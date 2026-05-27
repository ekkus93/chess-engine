"""Shared guidance for practical queen-and-rook endings."""

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.defensive_priorities import (
    KingDefenseProfile,
    king_danger_index,
    king_defense_profile,
)
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    heavy_piece_file_support_rows,
    is_advanced_passer,
    iter_color_pieces,
    king_coordinates,
    materially_ahead_color,
    most_advanced_passer,
    opposite_color,
    passed_pawns_for_color,
    path_clear_between,
)
from chess_game.chess.types import Color, PieceType

_MAX_NON_KING_PIECES = 6
_EVAL_SCALE = 2
_ORDER_SCALE = 3
_ROOT_SCALE = 5

_ROOK_BEHIND_PASSER_BONUS = 36
_QUEEN_FILE_ESCORT_BONUS = 26
_QUEEN_RANK_ESCORT_BONUS = 24
_PROMOTION_CONTROL_BONUS = 24
_NEAR_PROMOTION_SUPPORT_BONUS = 18
_UNSUPPORTED_NEAR_PROMOTION_PENALTY = 14
_KING_SUPPORT_BONUS = 14
_KING_STEP_TO_PASSER_BONUS = 96
_DANGER_PENALTY = 14
_ZONE_DEFENDER_BONUS = 6
_HEAVY_CONNECTION_BONUS = 8
_BACK_RANK_PENALTY = 10
_TRADE_WHEN_AHEAD_BONUS = 18
_TRADE_FOR_RELIEF_BONUS = 14
_ROOT_SHELTER_BONUS = 40
_ROOT_NEGLECT_SHELTER_PENALTY = 56

_ALLOWED_KINDS = {PieceType.QUEEN, PieceType.ROOK, PieceType.PAWN}


@dataclass(frozen=True)
class HeavyPieceSideState:
    """Cached queen-and-rook ending geometry for one side."""

    color: Color
    king: tuple[int, int]
    queen: tuple[int, int] | None
    rooks: list[tuple[int, int]]
    passers: list[tuple[int, int]]
    defense: KingDefenseProfile


def heavy_piece_endgame_evaluation_score(board: Board) -> int:
    """Return a signed score for practical queen-and-rook ending play."""

    if not _is_relevant_heavy_piece_endgame(board):
        return 0
    white = _side_state(board, Color.WHITE)
    black = _side_state(board, Color.BLACK)
    score = _side_score(board, white, black) - _side_score(board, black, white)
    return score * _EVAL_SCALE


def heavy_piece_endgame_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for practical heavy-piece ending moves."""

    if kind not in {PieceType.KING, PieceType.QUEEN, PieceType.ROOK, PieceType.PAWN}:
        return 0
    if not _is_relevant_heavy_piece_endgame(board) or not _side_has_advanced_passer(board, color):
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    before = _relative_side_score(board, color)
    after = _relative_side_score(child_board, color)
    bonus = (after - before) * _ORDER_SCALE + _trade_bonus(board, child_board, color)
    if kind == PieceType.KING:
        bonus += _king_support_move_bonus(board, child_board, color)
    return bonus + _neglect_shelter_penalty(board, move, child_board, color)


def heavy_piece_endgame_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return a root-only bonus for practical heavy-piece ending choices."""

    if not _is_relevant_heavy_piece_endgame(board) or not _side_has_advanced_passer(board, color):
        return 0
    before = _relative_side_score(board, color)
    after = _relative_side_score(child_board, color)
    bonus = (after - before) * _ROOT_SCALE + _trade_bonus(board, child_board, color)
    bonus += _root_shelter_bonus(board, child_board, color)
    return bonus + _neglect_shelter_penalty(board, move, child_board, color)


def _relative_side_score(board: Board, color: Color) -> int:
    own = _side_state(board, color)
    enemy = _side_state(board, opposite_color(color))
    return _side_score(board=board, own=own, enemy=enemy) - _side_score(
        board=board,
        own=enemy,
        enemy=own,
    )


def _side_score(
    board: Board,
    own: HeavyPieceSideState,
    enemy: HeavyPieceSideState,
) -> int:
    score = _rook_behind_passer_score(board, own)
    score += _queen_escort_score(board, own)
    score += _promotion_control_score(board, own)
    score += _near_promotion_support_score(board, own)
    score += _king_support_score(own, enemy)
    score += _king_shelter_score(own, enemy)
    return score


def _side_state(board: Board, color: Color) -> HeavyPieceSideState:
    queen: tuple[int, int] | None = None
    rooks: list[tuple[int, int]] = []
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind == PieceType.QUEEN:
            queen = (row, col)
        elif piece.kind == PieceType.ROOK:
            rooks.append((row, col))
    king = king_coordinates(board, color)
    if king is None:
        king = (-1, -1)
    defense = king_defense_profile(board, color)
    return HeavyPieceSideState(
        color=color,
        king=king,
        queen=queen,
        rooks=rooks,
        passers=passed_pawns_for_color(board, color),
        defense=defense,
    )


def _is_relevant_heavy_piece_endgame(board: Board) -> bool:
    non_king_count = 0
    heavy_count = 0
    has_queen = False
    white_rook = False
    black_rook = False
    for row in board.board:
        for piece in row:
            if piece is None or piece.kind == PieceType.KING:
                continue
            if piece.kind not in _ALLOWED_KINDS:
                return False
            non_king_count += 1
            if non_king_count > _MAX_NON_KING_PIECES:
                return False
            if piece.kind == PieceType.QUEEN:
                has_queen = True
                heavy_count += 1
            elif piece.kind == PieceType.ROOK:
                heavy_count += 1
                if piece.color == Color.WHITE:
                    white_rook = True
                else:
                    black_rook = True
    if heavy_count < 2 or not has_queen:
        return False
    return (white_rook and black_rook) or _has_advanced_passer(board)


def _rook_behind_passer_score(
    board: Board,
    state: HeavyPieceSideState,
) -> int:
    passer = most_advanced_passer(state.color, state.passers)
    if passer is None:
        return 0
    file_support_rows = heavy_piece_file_support_rows(board, state.color, passer)
    score = 0
    for rook_row, rook_col in state.rooks:
        if rook_col != passer[1] or rook_row not in file_support_rows:
            continue
        if _is_behind_pawn(state.color, rook_row, passer[0]):
            score += _ROOK_BEHIND_PASSER_BONUS
    return score


def _queen_escort_score(
    board: Board,
    state: HeavyPieceSideState,
) -> int:
    passer = most_advanced_passer(state.color, state.passers)
    if passer is None or state.queen is None:
        return 0
    queen_row, queen_col = state.queen
    score = 0
    if queen_col == passer[1] and path_clear_between(board, state.queen, passer):
        if _is_behind_pawn(state.color, queen_row, passer[0]):
            score += _QUEEN_FILE_ESCORT_BONUS
    if queen_row == passer[0] and path_clear_between(board, state.queen, passer):
        score += _QUEEN_RANK_ESCORT_BONUS
    if abs(queen_row - passer[0]) == abs(queen_col - passer[1]) and path_clear_between(
        board,
        state.queen,
        passer,
    ):
        score += _QUEEN_RANK_ESCORT_BONUS // 2
    return score


def _promotion_control_score(
    board: Board,
    state: HeavyPieceSideState,
) -> int:
    passer = most_advanced_passer(state.color, state.passers)
    if passer is None:
        return 0
    promotion_square = _promotion_square(state.color, passer[1])
    score = 0
    for rook in state.rooks:
        if _controls_square(board, rook, promotion_square):
            score += _PROMOTION_CONTROL_BONUS
    if state.queen is not None and _controls_square(board, state.queen, promotion_square):
        score += _PROMOTION_CONTROL_BONUS
    return score


def _near_promotion_support_score(
    board: Board,
    state: HeavyPieceSideState,
) -> int:
    passer = most_advanced_passer(state.color, state.passers)
    if passer is None or not _is_near_promotion(state.color, passer[0]):
        return 0
    score = 0
    if _rook_behind_passer_score(board, state) > 0:
        score += _NEAR_PROMOTION_SUPPORT_BONUS
    if _queen_escort_score(board, state) > 0:
        score += _NEAR_PROMOTION_SUPPORT_BONUS
    if _promotion_control_score(board, state) > 0:
        score += _NEAR_PROMOTION_SUPPORT_BONUS
    if score == 0:
        return -_UNSUPPORTED_NEAR_PROMOTION_PENALTY
    return score


def _king_shelter_score(
    own: HeavyPieceSideState,
    enemy: HeavyPieceSideState,
) -> int:
    if enemy.queen is None and not enemy.rooks:
        return 0
    score = own.defense.king_zone_defenders * _ZONE_DEFENDER_BONUS
    score += own.defense.heavy_connections * _HEAVY_CONNECTION_BONUS
    score -= _state_danger(own) * _DANGER_PENALTY
    if own.defense.back_rank_weak:
        score -= _BACK_RANK_PENALTY
    return score


def _king_support_score(
    own: HeavyPieceSideState,
    enemy: HeavyPieceSideState,
) -> int:
    passer = most_advanced_passer(own.color, own.passers)
    if passer is None:
        return 0
    own_distance = _king_distance(own.king, passer)
    enemy_distance = _king_distance(enemy.king, passer)
    score = 0
    if own_distance + 1 < enemy_distance:
        score += _KING_SUPPORT_BONUS
    if _is_behind_pawn(own.color, own.king[0], passer[0]):
        score += _KING_SUPPORT_BONUS
    return score


def _king_support_move_bonus(
    board: Board,
    child_board: Board,
    color: Color,
) -> int:
    passer = most_advanced_passer(color, passed_pawns_for_color(board, color))
    before_king = king_coordinates(board, color)
    after_king = king_coordinates(child_board, color)
    if passer is None or before_king is None or after_king is None:
        return 0
    improvement = max(0, _king_distance(before_king, passer) - _king_distance(after_king, passer))
    return improvement * _KING_STEP_TO_PASSER_BONUS


def _trade_bonus(board: Board, child_board: Board, color: Color) -> int:
    if _queen_count(board, opposite_color(color)) <= _queen_count(
        child_board,
        opposite_color(color),
    ):
        return 0
    if materially_ahead_color(board) == color:
        return _TRADE_WHEN_AHEAD_BONUS
    if king_danger_index(child_board, color) < king_danger_index(board, color):
        return _TRADE_FOR_RELIEF_BONUS
    return 0


def _root_shelter_bonus(board: Board, child_board: Board, color: Color) -> int:
    before = _side_state(board, color)
    after = _side_state(child_board, color)
    score = max(0, _state_danger(before) - _state_danger(after)) * _ROOT_SHELTER_BONUS
    score += max(
        0,
        after.defense.king_zone_defenders - before.defense.king_zone_defenders,
    ) * (_ROOT_SHELTER_BONUS // 2)
    score += max(
        0,
        after.defense.heavy_connections - before.defense.heavy_connections,
    ) * (
        _ROOT_SHELTER_BONUS // 2
    )
    return score


def _neglect_shelter_penalty(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    piece = board.get_piece(move.start)
    if piece is None or piece.kind != PieceType.PAWN:
        return 0
    before = _side_state(board, color)
    after = _side_state(child_board, color)
    if _state_danger(before) < 3 or _state_danger(after) < _state_danger(before):
        return 0
    return -_ROOT_NEGLECT_SHELTER_PENALTY


def _queen_count(board: Board, color: Color) -> int:
    return sum(
        1
        for piece, _, _ in iter_color_pieces(board, color)
        if piece.kind == PieceType.QUEEN
    )


def _controls_square(
    board: Board,
    start: tuple[int, int],
    target: tuple[int, int],
) -> bool:
    same_row = start[0] == target[0]
    same_col = start[1] == target[1]
    same_diag = abs(start[0] - target[0]) == abs(start[1] - target[1])
    return (same_row or same_col or same_diag) and path_clear_between(board, start, target)


def _promotion_square(color: Color, file_index: int) -> tuple[int, int]:
    return (0, file_index) if color == Color.WHITE else (7, file_index)


def _is_behind_pawn(color: Color, piece_row: int, pawn_row: int) -> bool:
    return piece_row > pawn_row if color == Color.WHITE else piece_row < pawn_row


def _is_near_promotion(color: Color, row: int) -> bool:
    return row <= 2 if color == Color.WHITE else row >= 5


def _has_advanced_passer(board: Board) -> bool:
    return any(
        is_advanced_passer(Color.WHITE, row)
        for row, _ in passed_pawns_for_color(board, Color.WHITE)
    ) or any(
        is_advanced_passer(Color.BLACK, row)
        for row, _ in passed_pawns_for_color(board, Color.BLACK)
    )


def _side_has_advanced_passer(board: Board, color: Color) -> bool:
    return any(
        is_advanced_passer(color, row)
        for row, _ in passed_pawns_for_color(board, color)
    )
def _state_danger(state: HeavyPieceSideState) -> int:
    return state.defense.danger


def _king_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])
