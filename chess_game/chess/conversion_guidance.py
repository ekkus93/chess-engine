"""Shared guidance for converting materially winning simple endgames."""

from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.move import Move
from chess_game.chess.constants import get_square_constant
from chess_game.chess.strategy_utils import (
    heavy_piece_file_support_rows,
    is_advanced_passer,
    iter_color_pieces,
    materially_ahead_color,
    non_king_piece_kinds,
    opposite_color,
    passed_pawns_for_color,
)
from chess_game.chess.types import Color, PieceType

_MAX_NON_KING_PIECES = 5
_EVAL_SCALE = 3
_ORDER_SCALE = 4
_CHECK_DRIFT_PENALTY = 28
_KING_ACTIVATION_BONUS = 10
_DEFENDER_PRESSURE_BONUS = 12
_PASSER_SUPPORT_BONUS = 10
_COUNTERPLAY_SUPPRESSION_BONUS = 8
_KING_CUTOFF_BONUS = 10
_ENEMY_PASSER_SUPPRESSION_BONUS = 12
_SEVENTH_RANK_PRESSURE_BONUS = 30


def winning_conversion_evaluation_score(board: Board) -> int:
    """Return a signed score for simple materially winning conversion geometry."""

    leading_color = _leading_color(board)
    if (
        leading_color is None
        or not _is_simple_conversion_endgame(board)
        or not _has_meaningful_counterplay(board, leading_color)
    ):
        return 0
    return _color_sign(leading_color) * _conversion_side_score(board, leading_color) * _EVAL_SCALE


def winning_conversion_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for clearer winning conversion plans."""

    if (
        kind not in {PieceType.KING, PieceType.QUEEN, PieceType.ROOK, PieceType.PAWN}
        or color != _leading_color(board)
        or not _is_simple_conversion_endgame(board)
        or not _has_meaningful_counterplay(board, color)
    ):
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    before = _conversion_side_score(board, color)
    after = _conversion_side_score(child_board, color)
    bonus = (after - before) * _ORDER_SCALE
    if kind == PieceType.KING and after > before:
        bonus += _KING_ACTIVATION_BONUS
    if kind in {PieceType.ROOK, PieceType.QUEEN} and _move_checks_opponent(child_board, color):
        if after <= before:
            bonus -= _CHECK_DRIFT_PENALTY
    return bonus


def _conversion_side_score(board: Board, color: Color) -> int:
    own_king = board.find_king(color)
    enemy_color = _opponent(color)
    enemy_king = board.find_king(enemy_color)
    if own_king is None or enemy_king is None:
        return 0
    own_king_pos = (int(own_king.row), int(own_king.col))
    enemy_king_pos = (int(enemy_king.row), int(enemy_king.col))
    own_passers = passed_pawns_for_color(board, color)
    enemy_passers = passed_pawns_for_color(board, enemy_color)
    enemy_heavy = [
        (row, col, piece.kind)
        for piece, row, col in iter_color_pieces(board, enemy_color)
        if piece.kind in {PieceType.ROOK, PieceType.QUEEN}
    ]
    score = 0
    score += _king_activation_score(own_king_pos, enemy_king_pos, own_passers)
    score += _passer_support_score(board, color, own_passers)
    score += _defender_pressure_score(board, color, enemy_heavy)
    score += _counterplay_suppression_score(board, color, own_king_pos, own_passers)
    score += _enemy_passer_suppression_score(board, color, enemy_passers)
    score += _king_cutoff_score(board, color, enemy_king_pos)
    score += _seventh_rank_pressure_score(board, color, own_passers)
    return score


def _leading_color(board: Board) -> Color | None:
    return materially_ahead_color(board)


def _is_simple_conversion_endgame(board: Board) -> bool:
    non_king_pieces = non_king_piece_kinds(board)
    return (
        len(non_king_pieces) <= _MAX_NON_KING_PIECES
        and any(kind in {PieceType.ROOK, PieceType.QUEEN} for kind in non_king_pieces)
    )


def _has_meaningful_counterplay(board: Board, color: Color) -> bool:
    enemy_color = _opponent(color)
    enemy_heavy = any(
        piece.kind in {PieceType.ROOK, PieceType.QUEEN}
        for piece, _, _ in iter_color_pieces(board, enemy_color)
    )
    return enemy_heavy or bool(passed_pawns_for_color(board, enemy_color))


def _king_activation_score(
    own_king: tuple[int, int],
    enemy_king: tuple[int, int],
    own_passers: list[tuple[int, int]],
) -> int:
    if own_passers:
        nearest = min(_king_distance(own_king, pawn) for pawn in own_passers)
        enemy_nearest = min(_king_distance(enemy_king, pawn) for pawn in own_passers)
        score = max(0, 8 - nearest) * _KING_ACTIVATION_BONUS
        if nearest + 1 < enemy_nearest:
            score += _KING_ACTIVATION_BONUS
        return score
    return max(0, 8 - _king_distance(own_king, enemy_king)) * (_KING_ACTIVATION_BONUS // 2)


def _passer_support_score(
    board: Board,
    color: Color,
    own_passers: list[tuple[int, int]],
) -> int:
    score = 0
    for pawn_row, pawn_col in own_passers:
        if not is_advanced_passer(color, pawn_row):
            continue
        for row in heavy_piece_file_support_rows(board, color, (pawn_row, pawn_col)):
            if _is_behind_pawn(color, row, pawn_row):
                score += _PASSER_SUPPORT_BONUS
    return score


def _defender_pressure_score(
    board: Board,
    color: Color,
    enemy_heavy: list[tuple[int, int, PieceType]],
) -> int:
    score = 0
    for piece, _, _ in iter_color_pieces(board, color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN}:
            continue
        for row, col, _ in enemy_heavy:
            if piece_attacks_square(
                piece,
                piece.square,
                _square_tuple_to_constant(row, col),
                board,
            ):
                score += _DEFENDER_PRESSURE_BONUS
    return score


def _counterplay_suppression_score(
    board: Board,
    color: Color,
    own_king: tuple[int, int],
    own_passers: list[tuple[int, int]],
) -> int:
    enemy_color = _opponent(color)
    score = 0
    for piece, row, col in iter_color_pieces(board, enemy_color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN}:
            continue
        if row == own_king[0] or col == own_king[1]:
            score -= _COUNTERPLAY_SUPPRESSION_BONUS
        if any(col == pawn_col for _, pawn_col in own_passers):
            score -= _COUNTERPLAY_SUPPRESSION_BONUS
    return score


def _enemy_passer_suppression_score(
    board: Board,
    color: Color,
    enemy_passers: list[tuple[int, int]],
) -> int:
    score = 0
    own_king = board.find_king(color)
    if own_king is None:
        return 0
    own_king_pos = (int(own_king.row), int(own_king.col))
    enemy_color = _opponent(color)
    for pawn_row, pawn_col in enemy_passers:
        block_row = pawn_row + (-1 if enemy_color == Color.WHITE else 1)
        block_square = (block_row, pawn_col)
        if own_king_pos == block_square:
            score += _ENEMY_PASSER_SUPPRESSION_BONUS
        for piece, row, col in iter_color_pieces(board, color):
            if piece.kind not in {PieceType.ROOK, PieceType.QUEEN}:
                continue
            if col == pawn_col and abs(row - pawn_row) >= 1:
                score += _ENEMY_PASSER_SUPPRESSION_BONUS // 2
    return score


def _king_cutoff_score(
    board: Board,
    color: Color,
    enemy_king: tuple[int, int],
) -> int:
    score = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN}:
            continue
        if row == enemy_king[0] and abs(col - enemy_king[1]) >= 2:
            score += _KING_CUTOFF_BONUS
        if col == enemy_king[1] and abs(row - enemy_king[0]) >= 2:
            score += _KING_CUTOFF_BONUS
    return score


def _seventh_rank_pressure_score(
    board: Board,
    color: Color,
    own_passers: list[tuple[int, int]],
) -> int:
    if not any(is_advanced_passer(color, pawn_row) for pawn_row, _ in own_passers):
        return 0
    target_row = 1 if color == Color.WHITE else 6
    return sum(
        _SEVENTH_RANK_PRESSURE_BONUS
        for piece, row, _ in iter_color_pieces(board, color)
        if piece.kind in {PieceType.ROOK, PieceType.QUEEN} and row == target_row
    )


def _is_behind_pawn(color: Color, piece_row: int, pawn_row: int) -> bool:
    return piece_row > pawn_row if color == Color.WHITE else piece_row < pawn_row


def _move_checks_opponent(board: Board, color: Color) -> bool:
    return is_in_check(board, _opponent(color))


def _square_tuple_to_constant(row: int, col: int):
    return get_square_constant(row, col)


def _king_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _color_sign(color: Color) -> int:
    return 1 if color == Color.WHITE else -1


def _opponent(color: Color) -> Color:
    return opposite_color(color)
