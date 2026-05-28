"""Guidance for practical heavy-piece defense against dangerous enemy passers."""

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.constants import ConstantSquare, get_square_constant
from chess_game.chess.move import Move
from chess_game.chess.opponent_plans import opponent_plan_profile
from chess_game.chess.strategy_utils import (
    is_advanced_passer,
    iter_color_pieces,
    materially_behind_color,
    opposite_color,
    passed_pawns_for_color,
)
from chess_game.chess.types import Color, PieceType

_ROOT_SCALE = 6
_EVAL_SCALE = 4
_ORDER_SCALE = 4
_PASSER_NEUTRALIZED_SCORE = 100
_BLOCKADE_BONUS = 20
_CAPTURE_PRESSURE_BONUS = 18
_PROMOTION_CONTROL_BONUS = 14
_FILE_CONTEST_BONUS = 10
_KING_DISTANCE_BONUS = 4
_FRONT_CONTAINMENT_BONUS = 20
_BEHIND_CONTAINMENT_BONUS = 12
_SIDE_CONTAINMENT_BONUS = 8
_SUPPORTED_KEY_DEFENDER_BONUS = 12
_OVERLOADED_KEY_DEFENDER_PENALTY = 18
_KING_MATING_PRESSURE_WEIGHT = 18
_CHECKING_RESOURCE_BONUS = 12
_HEAVY_TRADE_RESOURCE_BONUS = 10
_DRIFT_PENALTY = 18


@dataclass(frozen=True)
class ContainmentContext:
    """Shared geometry for one dangerous enemy passer."""

    enemy_color: Color
    dangerous_pawn: tuple[int, int]
    pawn_square: ConstantSquare
    promotion_square: ConstantSquare
    block_square: tuple[int, int]


def heavy_piece_defense_evaluation_score(board: Board) -> int:
    """Return a signed score for practical heavy-piece passer containment."""

    trailing_color = materially_behind_color(board)
    if trailing_color is None or not _has_heavy_piece_context(board):
        return 0
    enemy_color = opposite_color(trailing_color)
    dangerous_pawn = _most_dangerous_advanced_passer(board, enemy_color)
    if dangerous_pawn is None:
        return 0
    return _color_sign(trailing_color) * _containment_score(
        board, trailing_color, dangerous_pawn
    ) * _EVAL_SCALE


def heavy_piece_defense_root_bonus(board: Board, child_board: Board, color: Color) -> int:
    """Return a root-only bonus for practical passer containment while worse."""

    if materially_behind_color(board) != color or not _has_heavy_piece_context(board):
        return 0
    enemy_color = opposite_color(color)
    dangerous_before = _most_dangerous_advanced_passer(board, enemy_color)
    if dangerous_before is None:
        return 0
    before = _containment_score(board, color, dangerous_before)
    after = _containment_score(
        child_board,
        color,
        _most_dangerous_advanced_passer(child_board, enemy_color),
    )
    score = (after - before) * _ROOT_SCALE
    score += max(
        0,
        _checking_resource_score(
            child_board,
            color,
            _most_dangerous_advanced_passer(child_board, enemy_color),
        )
        - _checking_resource_score(board, color, dangerous_before),
    )
    score += max(
        0,
        _heavy_trade_resource_score(child_board, color)
        - _heavy_trade_resource_score(board, color),
    )
    return score


def heavy_piece_defense_extension_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return 1 when a move deserves a narrow containment extension."""

    if materially_behind_color(board) != color or not _has_heavy_piece_context(board):
        return 0
    enemy_color = opposite_color(color)
    dangerous_pawn = _most_dangerous_advanced_passer(board, enemy_color)
    if dangerous_pawn is None:
        return 0
    if _move_neutralizes_passer(board, move, child_board, color, dangerous_pawn):
        return 1
    return 0


def heavy_piece_defense_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for heavy-piece defensive containment."""

    if kind not in {PieceType.KING, PieceType.ROOK, PieceType.QUEEN, PieceType.BISHOP}:
        return 0
    if materially_behind_color(board) != color or not _has_heavy_piece_context(board):
        return 0
    enemy_color = opposite_color(color)
    dangerous_before = _most_dangerous_advanced_passer(board, enemy_color)
    if dangerous_before is None:
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    after_pawn = _most_dangerous_advanced_passer(child_board, enemy_color)
    before = _containment_score(board, color, dangerous_before)
    after = _containment_score(child_board, color, after_pawn)
    bonus = (after - before) * _ORDER_SCALE
    if _checking_resource_score(child_board, color, after_pawn) > _checking_resource_score(
        board,
        color,
        dangerous_before,
    ):
        bonus += _CHECKING_RESOURCE_BONUS
    if _heavy_trade_resource_score(child_board, color) > _heavy_trade_resource_score(board, color):
        bonus += _HEAVY_TRADE_RESOURCE_BONUS
    if _drifts_from_main_theater(dangerous_before, move):
        bonus -= _DRIFT_PENALTY
    return bonus


def _has_heavy_piece_context(board: Board) -> bool:
    heavy_piece_count = 0
    for piece, _, _ in iter_color_pieces(board, Color.WHITE):
        if piece.kind in {PieceType.ROOK, PieceType.QUEEN}:
            heavy_piece_count += 1
    for piece, _, _ in iter_color_pieces(board, Color.BLACK):
        if piece.kind in {PieceType.ROOK, PieceType.QUEEN}:
            heavy_piece_count += 1
    return heavy_piece_count >= 2


def _most_dangerous_advanced_passer(
    board: Board, color: Color
) -> tuple[int, int] | None:
    advanced_passers = [
        pawn
        for pawn in passed_pawns_for_color(board, color)
        if is_advanced_passer(color, pawn[0]) and _is_critical_passer(color, pawn[0])
    ]
    if not advanced_passers:
        return None
    if color == Color.WHITE:
        return min(advanced_passers, key=lambda pawn: pawn[0])
    return max(advanced_passers, key=lambda pawn: pawn[0])


def _containment_score(
    board: Board,
    color: Color,
    dangerous_pawn: tuple[int, int] | None,
) -> int:
    if dangerous_pawn is None:
        return _PASSER_NEUTRALIZED_SCORE
    context = _containment_context(color, dangerous_pawn)
    score = _blockade_score(board, color, context.block_square)
    score += _heavy_piece_pressure_score(
        board,
        color,
        context.pawn_square,
        context.promotion_square,
        context.dangerous_pawn[1],
    )
    score += _king_distance_score(board, color, context.block_square)
    score += _heavy_piece_alignment_score(
        board,
        color,
        context.enemy_color,
        context.dangerous_pawn,
    )
    score += _key_defender_support_score(board, color, context)
    score += _checking_resource_score(board, color, dangerous_pawn)
    score += _heavy_trade_resource_score(board, color)
    score -= _immediate_king_danger_penalty(board, color)
    return score


def _blockade_score(board: Board, color: Color, block_square: tuple[int, int]) -> int:
    block_row, block_col = block_square
    if not 0 <= block_row < 8:
        return 0
    occupant = board.board[block_row][block_col]
    if occupant is None or occupant.color != color:
        return 0
    if occupant.kind in {PieceType.KING, PieceType.ROOK, PieceType.QUEEN}:
        return _BLOCKADE_BONUS
    return _BLOCKADE_BONUS // 2


def _heavy_piece_pressure_score(
    board: Board,
    color: Color,
    pawn_square,
    promotion_square,
    pawn_col: int,
) -> int:
    score = 0
    for piece, _, col in iter_color_pieces(board, color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN}:
            continue
        if piece_attacks_square(piece, piece.square, pawn_square, board):
            score += _CAPTURE_PRESSURE_BONUS
        if piece_attacks_square(piece, piece.square, promotion_square, board):
            score += _PROMOTION_CONTROL_BONUS
        if col == pawn_col:
            score += _FILE_CONTEST_BONUS
    return score


def _king_distance_score(board: Board, color: Color, block_square: tuple[int, int]) -> int:
    own_king = board.find_king(color)
    if own_king is None:
        return 0
    distance = abs(int(own_king.row) - block_square[0]) + abs(int(own_king.col) - block_square[1])
    return max(0, 6 - distance) * _KING_DISTANCE_BONUS


def _heavy_piece_alignment_score(
    board: Board,
    color: Color,
    enemy_color: Color,
    dangerous_pawn: tuple[int, int],
) -> int:
    pawn_row, pawn_col = dangerous_pawn
    score = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN}:
            continue
        if col == pawn_col:
            if _is_in_front_of_enemy_pawn(enemy_color, row, pawn_row):
                score += _FRONT_CONTAINMENT_BONUS
            elif _is_behind_enemy_pawn(enemy_color, row, pawn_row):
                score += _BEHIND_CONTAINMENT_BONUS
        elif abs(col - pawn_col) == 1 and abs(row - pawn_row) <= 2:
            score += _SIDE_CONTAINMENT_BONUS
    return score


def _key_defender_support_score(
    board: Board,
    color: Color,
    context: ContainmentContext,
) -> int:
    score = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind == PieceType.PAWN:
            continue
        if not _is_key_defender(
            board,
            piece.kind,
            row,
            col,
            context,
        ):
            continue
        piece_square = get_square_constant(row, col)
        enemy_attackers = _attacker_count(board, opposite_color(color), piece_square)
        if enemy_attackers == 0:
            continue
        friendly_support = _defender_count(board, color, piece_square, exclude=(row, col))
        if friendly_support >= enemy_attackers:
            score += _SUPPORTED_KEY_DEFENDER_BONUS * friendly_support
        else:
            score -= _OVERLOADED_KEY_DEFENDER_PENALTY * (enemy_attackers - friendly_support)
    return score


def _checking_resource_score(
    board: Board,
    color: Color,
    dangerous_pawn: tuple[int, int] | None,
) -> int:
    enemy_king = board.find_king(opposite_color(color))
    if enemy_king is None:
        return 0
    enemy_king_square = enemy_king
    score = 0
    for piece, _, _ in iter_color_pieces(board, color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN, PieceType.BISHOP}:
            continue
        if piece_attacks_square(piece, piece.square, enemy_king_square, board):
            score += _CHECKING_RESOURCE_BONUS
            if dangerous_pawn is not None:
                score += _CHECKING_RESOURCE_BONUS // 2
    if is_in_check(board, opposite_color(color)):
        score += _CHECKING_RESOURCE_BONUS
    return score


def _heavy_trade_resource_score(board: Board, color: Color) -> int:
    score = 0
    enemy_heavy = [
        get_square_constant(row, col)
        for piece, row, col in iter_color_pieces(board, opposite_color(color))
        if piece.kind in {PieceType.ROOK, PieceType.QUEEN}
    ]
    for piece, _, _ in iter_color_pieces(board, color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN}:
            continue
        if any(
            piece_attacks_square(piece, piece.square, target_square, board)
            for target_square in enemy_heavy
        ):
            score += _HEAVY_TRADE_RESOURCE_BONUS
    return score


def _immediate_king_danger_penalty(board: Board, color: Color) -> int:
    profile = opponent_plan_profile(board, color)
    danger = profile.invasion_lines * 2 + profile.checking_resources * 3
    return danger * _KING_MATING_PRESSURE_WEIGHT


def _containment_context(
    color: Color,
    dangerous_pawn: tuple[int, int],
) -> ContainmentContext:
    enemy_color = opposite_color(color)
    pawn_row, pawn_col = dangerous_pawn
    promotion_row = 0 if enemy_color == Color.WHITE else 7
    return ContainmentContext(
        enemy_color=enemy_color,
        dangerous_pawn=dangerous_pawn,
        pawn_square=get_square_constant(pawn_row, pawn_col),
        promotion_square=get_square_constant(promotion_row, pawn_col),
        block_square=_block_square(enemy_color, dangerous_pawn),
    )


def _block_square(enemy_color: Color, dangerous_pawn: tuple[int, int]) -> tuple[int, int]:
    pawn_row, pawn_col = dangerous_pawn
    direction = -1 if enemy_color == Color.WHITE else 1
    return pawn_row + direction, pawn_col


def _is_critical_passer(color: Color, row: int) -> bool:
    return row <= 1 if color == Color.WHITE else row >= 6


def _is_key_defender(
    board: Board,
    kind: PieceType,
    row: int,
    col: int,
    context: ContainmentContext,
) -> bool:
    piece_square = get_square_constant(row, col)
    if (row, col) == context.block_square:
        return True
    piece = board.board[row][col]
    if piece is None:
        return False
    if kind in {PieceType.ROOK, PieceType.QUEEN} and (
        piece_attacks_square(piece, piece_square, context.pawn_square, board)
        or piece_attacks_square(piece, piece_square, context.promotion_square, board)
    ):
        return True
    if kind in {PieceType.BISHOP, PieceType.KNIGHT, PieceType.QUEEN, PieceType.ROOK}:
        center_rows = {2, 3, 4, 5}
        center_cols = {2, 3, 4, 5}
        if row in center_rows and col in center_cols:
            return True
    return abs(col - context.dangerous_pawn[1]) <= 1


def _attacker_count(board: Board, color: Color, target_square) -> int:
    return sum(
        1
        for piece, _, _ in iter_color_pieces(board, color)
        if piece_attacks_square(piece, piece.square, target_square, board)
    )


def _defender_count(
    board: Board,
    color: Color,
    target_square,
    exclude: tuple[int, int] | None = None,
) -> int:
    count = 0
    for piece, row, col in iter_color_pieces(board, color):
        if exclude is not None and (row, col) == exclude:
            continue
        if piece_attacks_square(piece, piece.square, target_square, board):
            count += 1
    return count


def _is_in_front_of_enemy_pawn(enemy_color: Color, piece_row: int, pawn_row: int) -> bool:
    return piece_row < pawn_row if enemy_color == Color.WHITE else piece_row > pawn_row


def _is_behind_enemy_pawn(enemy_color: Color, piece_row: int, pawn_row: int) -> bool:
    return piece_row > pawn_row if enemy_color == Color.WHITE else piece_row < pawn_row


def _drifts_from_main_theater(dangerous_pawn: tuple[int, int], move: Move) -> bool:
    start_file_distance = abs(int(move.start.col) - dangerous_pawn[1])
    end_file_distance = abs(int(move.end.col) - dangerous_pawn[1])
    return end_file_distance > start_file_distance and end_file_distance >= 2


def _move_neutralizes_passer(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
    dangerous_pawn: tuple[int, int],
) -> bool:
    enemy_color = opposite_color(color)
    moving_piece = board.get_piece(move.start)
    if moving_piece is None or moving_piece.kind not in {
        PieceType.ROOK,
        PieceType.QUEEN,
        PieceType.KING,
    }:
        return False
    if _most_dangerous_advanced_passer(child_board, enemy_color) is None:
        return True
    return (
        (int(move.end.row), int(move.end.col)) == _block_square(enemy_color, dangerous_pawn)
        or int(move.end.col) == dangerous_pawn[1]
    )


def _color_sign(color: Color) -> int:
    return 1 if color == Color.WHITE else -1
