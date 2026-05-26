"""Shared guidance for passed-pawn races and promotion urgency."""

from chess_game.chess.board import Board
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.constants import get_square_constant
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    heavy_piece_file_support_rows,
    iter_color_pieces,
    king_coordinates,
    non_king_piece_kinds,
    opposite_color,
    passed_pawns_for_color,
)
from chess_game.chess.types import Color, PieceType

_MAX_NON_KING_PIECES = 5
_EVAL_SCALE = 3
_ORDER_SCALE = 4
_PASSER_PROGRESS_BONUS = 20
_PROTECTED_PASSER_BONUS = 12
_CONNECTED_PASSER_BONUS = 14
_OUTSIDE_PASSER_BONUS = 12
_CLEAR_PATH_BONUS = 12
_KING_SUPPORT_BONUS = 8
_CRITICAL_ZONE_BONUS = 12
_HEAVY_SUPPORT_BONUS = 10
_ENEMY_PASSER_DANGER_BONUS = 18
_PROMOTION_SQUARE_PENALTY = 18
_BLOCKADE_PENALTY = 12
_DIRECT_PUSH_BONUS = 12
_HIGH_PRIORITY_PUSH_BONUS = 72
_ESCORT_BONUS = 16
_COSMETIC_CHECK_PENALTY = 96


def passer_race_evaluation_score(board: Board) -> int:
    """Return a signed score for passed-pawn urgency in simple endgames."""

    if not _is_relevant_passer_race(board):
        return 0
    return (
        _passer_race_side_score(board, Color.WHITE)
        - _passer_race_side_score(board, Color.BLACK)
    ) * _EVAL_SCALE


def passer_race_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for clearer passed-pawn race play."""

    if kind not in {PieceType.KING, PieceType.ROOK, PieceType.QUEEN, PieceType.PAWN}:
        return 0
    if not _is_relevant_passer_race(board):
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    before = _passer_race_side_score(board, color)
    after = _passer_race_side_score(child_board, color)
    bonus = (after - before) * _ORDER_SCALE
    if kind == PieceType.PAWN and after > before:
        bonus += _DIRECT_PUSH_BONUS
        bonus += _high_priority_push_bonus(child_board, color, move)
    if kind == PieceType.KING and after > before:
        bonus += _ESCORT_BONUS
    if (
        kind in {PieceType.ROOK, PieceType.QUEEN}
        and _move_checks_opponent(child_board, color)
        and after <= before
        and _has_relevant_race_targets(board, color)
    ):
        bonus -= _COSMETIC_CHECK_PENALTY
    return bonus


def passer_race_extension_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
) -> int:
    """Return 1 when a move deserves a narrow passer-race extension."""

    if not _is_relevant_passer_race(board):
        return 0
    if _is_near_promotion_passer_push(board, move, moving_color):
        return 1
    if _move_directly_stops_enemy_near_promotion_pawn(board, move, child_board, moving_color):
        return 1
    return 0


def _passer_race_side_score(board: Board, color: Color) -> int:
    own_passers = passed_pawns_for_color(board, color)
    enemy_passers = passed_pawns_for_color(board, _opponent(color))
    score = sum(
        _own_passer_score(board, color, pawn, own_passers)
        for pawn in own_passers
        if _is_high_priority_passer(board, color, pawn, own_passers)
    )
    score -= sum(
        _enemy_passer_danger_score(board, color, pawn)
        for pawn in enemy_passers
        if _is_high_priority_passer(board, _opponent(color), pawn, enemy_passers)
    )
    return score


def _own_passer_score(
    board: Board,
    color: Color,
    pawn: tuple[int, int],
    own_passers: list[tuple[int, int]],
) -> int:
    row, col = pawn
    score = _promotion_progress(color, row) * _PASSER_PROGRESS_BONUS
    if _is_protected_passer(board, color, pawn):
        score += _PROTECTED_PASSER_BONUS
    if _is_connected_passer(pawn, own_passers):
        score += _CONNECTED_PASSER_BONUS
    if _is_outside_passer(col):
        score += _OUTSIDE_PASSER_BONUS
    if _path_to_promotion_is_clear(board, color, pawn):
        score += _CLEAR_PATH_BONUS
    score += _king_support_score(board, color, pawn)
    score += _heavy_piece_support_score(board, color, pawn)
    return score


def _enemy_passer_danger_score(
    board: Board,
    color: Color,
    enemy_pawn: tuple[int, int],
) -> int:
    enemy_color = _opponent(color)
    row, _ = enemy_pawn
    score = _promotion_progress(enemy_color, row) * _ENEMY_PASSER_DANGER_BONUS
    if _path_to_promotion_is_clear(board, enemy_color, enemy_pawn):
        score += _CLEAR_PATH_BONUS
    if not _controls_promotion_square(board, color, enemy_pawn):
        score += _PROMOTION_SQUARE_PENALTY
    if not _blocks_enemy_pawn(board, color, enemy_pawn):
        score += _BLOCKADE_PENALTY
    return score


def _king_support_score(board: Board, color: Color, pawn: tuple[int, int]) -> int:
    own_king = king_coordinates(board, color)
    enemy_king = king_coordinates(board, _opponent(color))
    if own_king is None or enemy_king is None:
        return 0
    promotion_square = _promotion_square(color, pawn[1])
    score = max(0, _king_distance(enemy_king, pawn) - _king_distance(own_king, pawn))
    score *= _KING_SUPPORT_BONUS
    critical_gain = max(
        0,
        _king_distance(enemy_king, promotion_square)
        - _king_distance(own_king, promotion_square),
    )
    score += critical_gain * _CRITICAL_ZONE_BONUS
    return score


def _heavy_piece_support_score(
    board: Board,
    color: Color,
    pawn: tuple[int, int],
) -> int:
    score = 0
    pawn_row, _ = pawn
    for row in heavy_piece_file_support_rows(board, color, pawn):
        if color == Color.WHITE and row > pawn_row:
            score += _HEAVY_SUPPORT_BONUS
        if color == Color.BLACK and row < pawn_row:
            score += _HEAVY_SUPPORT_BONUS
    return score


def _is_protected_passer(board: Board, color: Color, pawn: tuple[int, int]) -> bool:
    row, col = pawn
    support_row = row + 1 if color == Color.WHITE else row - 1
    if not 0 <= support_row < 8:
        return False
    for support_col in (col - 1, col + 1):
        if not 0 <= support_col < 8:
            continue
        piece = board.board[support_row][support_col]
        if piece is not None and piece.color == color and piece.kind == PieceType.PAWN:
            return True
    return False


def _is_connected_passer(
    pawn: tuple[int, int],
    own_passers: list[tuple[int, int]],
) -> bool:
    row, col = pawn
    return any(
        other_col != col and abs(other_col - col) == 1 and abs(other_row - row) <= 1
        for other_row, other_col in own_passers
    )


def _path_to_promotion_is_clear(
    board: Board,
    color: Color,
    pawn: tuple[int, int],
) -> bool:
    row, col = pawn
    promotion_row = 0 if color == Color.WHITE else 7
    if row == promotion_row:
        return True
    step = -1 if color == Color.WHITE else 1
    current_row = row + step
    while current_row != promotion_row + step:
        if board.board[current_row][col] is not None:
            return False
        current_row += step
    return True


def _controls_promotion_square(
    board: Board,
    color: Color,
    enemy_pawn: tuple[int, int],
) -> bool:
    promotion_square = _square_tuple_to_constant(
        *_promotion_square(_opponent(color), enemy_pawn[1])
    )
    occupant = board.get_piece(promotion_square)
    if occupant is not None and occupant.color == color:
        return True
    return any(
        piece_attacks_square(piece, piece.square, promotion_square, board)
        for piece, _, _ in iter_color_pieces(board, color)
    )


def _blocks_enemy_pawn(
    board: Board,
    color: Color,
    enemy_pawn: tuple[int, int],
) -> bool:
    block_row, block_col = _block_square(_opponent(color), enemy_pawn)
    if not 0 <= block_row < 8:
        return False
    occupant = board.board[block_row][block_col]
    return occupant is not None and occupant.color == color


def _has_relevant_race_targets(board: Board, color: Color) -> bool:
    own_passers = passed_pawns_for_color(board, color)
    enemy_passers = passed_pawns_for_color(board, _opponent(color))
    return any(
        _is_high_priority_passer(board, color, pawn, own_passers)
        for pawn in own_passers
    ) or any(
        _is_high_priority_passer(board, _opponent(color), pawn, enemy_passers)
        for pawn in enemy_passers
    )


def _is_near_promotion_passer_push(board: Board, move: Move, color: Color) -> bool:
    piece = board.get_piece(move.start)
    if piece is None or piece.kind != PieceType.PAWN:
        return False
    start = (int(move.start.row), int(move.start.col))
    if start not in passed_pawns_for_color(board, color):
        return False
    end_row = int(move.end.row)
    return end_row == (1 if color == Color.WHITE else 6)


def _move_directly_stops_enemy_near_promotion_pawn(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> bool:
    enemy_color = _opponent(color)
    for pawn in passed_pawns_for_color(board, enemy_color):
        row, _ = pawn
        if row not in {2, 5, 1, 6}:
            continue
        promotion_square = _promotion_square(enemy_color, pawn[1])
        block_square = _block_square(enemy_color, pawn)
        move_end = (int(move.end.row), int(move.end.col))
        if move_end not in {promotion_square, block_square}:
            continue
        if _controls_promotion_square(child_board, color, pawn):
            return True
        if _blocks_enemy_pawn(child_board, color, pawn):
            return True
    return False


def _is_relevant_passer_race(board: Board) -> bool:
    non_king_pieces = non_king_piece_kinds(board)
    if len(non_king_pieces) > _MAX_NON_KING_PIECES:
        return False
    return _has_relevant_race_targets(board, Color.WHITE) or _has_relevant_race_targets(
        board,
        Color.BLACK,
    )


def _high_priority_push_bonus(board: Board, color: Color, move: Move) -> int:
    end_square = (int(move.end.row), int(move.end.col))
    own_passers = passed_pawns_for_color(board, color)
    if end_square not in own_passers:
        return 0
    if not _is_high_priority_passer(board, color, end_square, own_passers):
        return 0
    return _HIGH_PRIORITY_PUSH_BONUS


def _is_high_priority_passer(
    board: Board,
    color: Color,
    pawn: tuple[int, int],
    own_passers: list[tuple[int, int]],
) -> bool:
    row, col = pawn
    return (
        _promotion_progress(color, row) >= 4
        or _is_outside_passer(col)
        or _is_protected_passer(board, color, pawn)
        or _is_connected_passer(pawn, own_passers)
    )


def _promotion_progress(color: Color, row: int) -> int:
    return 6 - row if color == Color.WHITE else row - 1


def _promotion_square(color: Color, col: int) -> tuple[int, int]:
    return (0, col) if color == Color.WHITE else (7, col)


def _block_square(color: Color, pawn: tuple[int, int]) -> tuple[int, int]:
    row, col = pawn
    return (row - 1, col) if color == Color.WHITE else (row + 1, col)


def _is_outside_passer(col: int) -> bool:
    return col in {0, 1, 6, 7}


def _square_tuple_to_constant(row: int, col: int):
    return get_square_constant(row, col)


def _king_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _move_checks_opponent(board: Board, color: Color) -> bool:
    return is_in_check(board, _opponent(color))


def _opponent(color: Color) -> Color:
    return opposite_color(color)
