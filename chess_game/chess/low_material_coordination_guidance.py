"""Piece-specific coordination guidance for sparse bishop and rook endings."""

from __future__ import annotations

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.constants import ConstantSquare, get_square_constant
from chess_game.chess.move import Move
from chess_game.chess.pieces.piece_movers import PieceMovers
from chess_game.chess.strategy_utils import (
    is_advanced_passer,
    iter_color_pieces,
    king_coordinates,
    most_advanced_passer,
    non_king_piece_count_at_most,
    opposite_color,
    passed_pawns_for_color,
)
from chess_game.chess.types import Color, PieceType

_MAX_NON_KING_PIECES = 6
_BISHOP_CORRECT_COMPLEX_BONUS = 20
_WRONG_ROOK_PAWN_BISHOP_PENALTY = 44
_BISHOP_CRITICAL_CONTROL_BONUS = 18
_BISHOP_BLOCKADE_COMPLEX_BONUS = 14
_BISHOP_MOBILITY_BONUS = 2
_BISHOP_THEATER_BONUS = 5
_ROOK_FILE_ALIGNMENT_BONUS = 14
_ROOK_BEHIND_OWN_PASSER_BONUS = 26
_ROOK_BEHIND_ENEMY_PASSER_BONUS = 18
_ROOK_IN_FRONT_OF_ENEMY_PASSER_BONUS = 18
_ROOK_DRIFT_PENALTY = 16
_PIECE_THEATER_BONUS = 4
_KING_PIECE_COORDINATION_BONUS = 5
_KING_AND_PIECE_THEATER_BONUS = 12
_ORDER_SCALE = 4
_ROOT_SCALE = 5
_MOVE_CRITICAL_CONTROL_BONUS = 24
_MOVE_FOCUS_DISTANCE_BONUS = 16
_MOVE_COORDINATION_BONUS = 12
_MOVE_ROOK_ALIGNMENT_BONUS = 28
_AIMLESS_BISHOP_DRIFT_PENALTY = 72
_AIMLESS_ROOK_DRIFT_PENALTY = 44


@dataclass(frozen=True)
class LowMaterialCoordinationContext:
    """Compact sparse-ending coordination context for one side."""

    color: Color
    own_king: tuple[int, int] | None
    own_main_passer: tuple[int, int] | None
    enemy_main_passer: tuple[int, int] | None
    critical_squares: tuple[tuple[int, int], ...]
    focus: tuple[int, int] | None


def low_material_coordination_evaluation_score(board: Board) -> int:
    """Return a signed sparse-ending coordination score for both sides."""

    total = 0
    for color in (Color.WHITE, Color.BLACK):
        context = _coordination_context(board, color)
        if context is None:
            continue
        side_score = _side_score(board, context)
        total += side_score if color == Color.WHITE else -side_score
    return total


def low_material_coordination_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for coordinated bishop/rook sparse-endgame play."""

    if kind not in {PieceType.BISHOP, PieceType.ROOK}:
        return 0
    context = _coordination_context(board, color)
    if context is None:
        return 0
    child_board = _child_board_for_move(board, move)
    if child_board is None:
        return 0
    next_context = _coordination_context(child_board, color) or context
    bonus = (_side_score(child_board, next_context) - _side_score(board, context)) * _ORDER_SCALE
    bonus += _move_bonus(board, child_board, move, context, next_context)
    return bonus


def low_material_coordination_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return a root tie-break bonus for coordinated sparse-endgame plans."""

    piece = board.get_piece(move.start)
    if piece is None or piece.kind not in {PieceType.BISHOP, PieceType.ROOK}:
        return 0
    context = _coordination_context(board, color)
    if context is None:
        return 0
    next_context = _coordination_context(child_board, color) or context
    bonus = (_side_score(child_board, next_context) - _side_score(board, context)) * _ROOT_SCALE
    bonus += _move_bonus(board, child_board, move, context, next_context)
    return bonus


def _coordination_context(
    board: Board,
    color: Color,
) -> LowMaterialCoordinationContext | None:
    if not _is_relevant_board(board):
        return None
    own_main_passer = _critical_passer(board, color)
    enemy_color = opposite_color(color)
    enemy_main_passer = _critical_passer(board, enemy_color)
    if own_main_passer is None and enemy_main_passer is None:
        return None
    critical_squares = _critical_squares(color, own_main_passer, enemy_main_passer)
    if not critical_squares:
        return None
    focus = critical_squares[0]
    return LowMaterialCoordinationContext(
        color=color,
        own_king=king_coordinates(board, color),
        own_main_passer=own_main_passer,
        enemy_main_passer=enemy_main_passer,
        critical_squares=tuple(critical_squares),
        focus=focus,
    )


def _is_relevant_board(board: Board) -> bool:
    allowed = {PieceType.BISHOP, PieceType.ROOK, PieceType.PAWN}
    if not non_king_piece_count_at_most(board, _MAX_NON_KING_PIECES, allowed):
        return False
    counts = _piece_counts(board)
    if counts["rooks"] > 1:
        return False
    if counts["white_bishops"] == 0 and counts["black_bishops"] == 0:
        return False
    if (
        counts["white_bishops"] > 0
        and counts["black_bishops"] > 0
        and (counts["white_pawns"] == 0 or counts["black_pawns"] == 0)
    ):
        return False
    return any(
        piece.kind in {PieceType.BISHOP, PieceType.ROOK}
        for row in board.board
        for piece in row
        if piece is not None
    )


def _piece_counts(board: Board) -> dict[str, int]:
    counts = {
        "rooks": 0,
        "white_bishops": 0,
        "black_bishops": 0,
        "white_pawns": 0,
        "black_pawns": 0,
    }
    for row in board.board:
        for piece in row:
            if piece is None:
                continue
            if piece.kind == PieceType.ROOK:
                counts["rooks"] += 1
            elif piece.kind == PieceType.BISHOP:
                key = "white_bishops" if piece.color == Color.WHITE else "black_bishops"
                counts[key] += 1
            elif piece.kind == PieceType.PAWN:
                key = "white_pawns" if piece.color == Color.WHITE else "black_pawns"
                counts[key] += 1
    return counts


def _critical_passer(board: Board, color: Color) -> tuple[int, int] | None:
    passers = [
        pawn
        for pawn in passed_pawns_for_color(board, color)
        if is_advanced_passer(color, pawn[0])
    ]
    return most_advanced_passer(color, passers)


def _critical_squares(
    color: Color,
    own_main_passer: tuple[int, int] | None,
    enemy_main_passer: tuple[int, int] | None,
) -> list[tuple[int, int]]:
    squares: list[tuple[int, int]] = []
    if own_main_passer is not None:
        support_square = _advance_square(color, own_main_passer)
        if support_square is not None:
            squares.append(support_square)
        squares.append(_promotion_square(color, own_main_passer[1]))
    if enemy_main_passer is not None:
        enemy_color = opposite_color(color)
        block_square = _block_square(enemy_color, enemy_main_passer)
        if 0 <= block_square[0] < 8:
            squares.append(block_square)
        squares.append(_promotion_square(enemy_color, enemy_main_passer[1]))
    return squares


def _side_score(board: Board, context: LowMaterialCoordinationContext) -> int:
    score = 0
    for piece, row, col in iter_color_pieces(board, context.color):
        square = (row, col)
        if piece.kind == PieceType.BISHOP:
            score += _bishop_score(board, piece, square, context)
        elif piece.kind == PieceType.ROOK:
            score += _rook_score(board, square, context)
    return score


def _bishop_score(
    board: Board,
    piece,
    square: tuple[int, int],
    context: LowMaterialCoordinationContext,
) -> int:
    score = 0
    bishop_complex = _square_color(square)
    if context.own_main_passer is not None:
        own_promotion = _promotion_square(context.color, context.own_main_passer[1])
        if bishop_complex == _square_color(own_promotion):
            score += _BISHOP_CORRECT_COMPLEX_BONUS
        elif _is_rook_pawn(context.own_main_passer):
            score -= _WRONG_ROOK_PAWN_BISHOP_PENALTY
    if context.enemy_main_passer is not None:
        enemy_color = opposite_color(context.color)
        enemy_block = _block_square(enemy_color, context.enemy_main_passer)
        if 0 <= enemy_block[0] < 8 and bishop_complex == _square_color(enemy_block):
            score += _BISHOP_BLOCKADE_COMPLEX_BONUS
    score += _critical_control_score(
        board,
        piece,
        context.critical_squares,
        _BISHOP_CRITICAL_CONTROL_BONUS,
    )
    mobility = len(PieceMovers.get_valid_moves(piece, board))
    score += max(0, mobility - 4) * _BISHOP_MOBILITY_BONUS
    score += _piece_theater_score(square, context.critical_squares, _BISHOP_THEATER_BONUS)
    score += _king_piece_coordination_score(context.own_king, square, context.focus)
    return score


def _rook_score(
    board: Board,
    square: tuple[int, int],
    context: LowMaterialCoordinationContext,
) -> int:
    score = 0
    rook_row, rook_col = square
    if context.own_main_passer is not None and rook_col == context.own_main_passer[1]:
        score += _ROOK_FILE_ALIGNMENT_BONUS
        if _is_behind_pawn(context.color, rook_row, context.own_main_passer[0]):
            score += _ROOK_BEHIND_OWN_PASSER_BONUS
    if context.enemy_main_passer is not None and rook_col == context.enemy_main_passer[1]:
        enemy_color = opposite_color(context.color)
        score += _ROOK_FILE_ALIGNMENT_BONUS
        if _is_behind_pawn(enemy_color, rook_row, context.enemy_main_passer[0]):
            score += _ROOK_BEHIND_ENEMY_PASSER_BONUS
        elif _is_in_front_of_pawn(enemy_color, rook_row, context.enemy_main_passer[0]):
            score += _ROOK_IN_FRONT_OF_ENEMY_PASSER_BONUS
    if not _rook_on_critical_file(square, context):
        score -= _ROOK_DRIFT_PENALTY
    score += _piece_theater_score(square, context.critical_squares, _PIECE_THEATER_BONUS)
    score += _king_piece_coordination_score(context.own_king, square, context.focus)
    rook_piece = board.board[rook_row][rook_col]
    if rook_piece is not None:
        score += _critical_control_score(
            board,
            rook_piece,
            context.critical_squares,
            _ROOK_FILE_ALIGNMENT_BONUS,
        )
    return score


def _critical_control_score(
    board: Board,
    piece,
    critical_squares: tuple[tuple[int, int], ...],
    scale: int,
) -> int:
    if piece.square is None:
        return 0
    score = 0
    for square in critical_squares:
        if piece.square == _square_to_constant(square):
            score += scale
            continue
        if piece_attacks_square(piece, piece.square, _square_to_constant(square), board):
            score += scale
    return score


def _piece_theater_score(
    square: tuple[int, int],
    critical_squares: tuple[tuple[int, int], ...],
    scale: int,
) -> int:
    if not critical_squares:
        return 0
    nearest = min(_manhattan_distance(square, critical) for critical in critical_squares)
    return max(0, 7 - nearest) * scale


def _king_piece_coordination_score(
    own_king: tuple[int, int] | None,
    piece_square: tuple[int, int],
    focus: tuple[int, int] | None,
) -> int:
    if own_king is None or focus is None:
        return 0
    score = (
        max(0, 5 - _king_distance(own_king, piece_square))
        * _KING_PIECE_COORDINATION_BONUS
    )
    if _manhattan_distance(piece_square, focus) <= 2 and _manhattan_distance(own_king, focus) <= 3:
        score += _KING_AND_PIECE_THEATER_BONUS
    return score


def _move_bonus(
    board: Board,
    child_board: Board,
    move: Move,
    context: LowMaterialCoordinationContext,
    next_context: LowMaterialCoordinationContext,
) -> int:
    before_piece = board.get_piece(move.start)
    after_piece = child_board.get_piece(move.end)
    if before_piece is None or after_piece is None:
        return 0
    before_control = _critical_control_score(
        board,
        before_piece,
        context.critical_squares,
        1,
    )
    after_control = _critical_control_score(
        child_board,
        after_piece,
        next_context.critical_squares,
        1,
    )
    before_focus_distance = _nearest_focus_distance(
        (int(move.start.row), int(move.start.col)),
        context.critical_squares,
    )
    after_focus_distance = _nearest_focus_distance(
        (int(move.end.row), int(move.end.col)),
        next_context.critical_squares,
    )
    before_coordination = _king_piece_coordination_score(
        context.own_king,
        (int(move.start.row), int(move.start.col)),
        context.focus,
    )
    after_coordination = _king_piece_coordination_score(
        next_context.own_king,
        (int(move.end.row), int(move.end.col)),
        next_context.focus,
    )
    bonus = max(0, after_control - before_control) * _MOVE_CRITICAL_CONTROL_BONUS
    bonus += max(0, before_focus_distance - after_focus_distance) * _MOVE_FOCUS_DISTANCE_BONUS
    bonus += max(0, after_coordination - before_coordination) * _MOVE_COORDINATION_BONUS
    if before_piece.kind == PieceType.ROOK and _rook_on_critical_file(
        (int(move.end.row), int(move.end.col)),
        next_context,
    ):
        bonus += _MOVE_ROOK_ALIGNMENT_BONUS
    if (
        after_control <= before_control
        and after_focus_distance >= before_focus_distance
        and after_coordination <= before_coordination
    ):
        if before_piece.kind == PieceType.BISHOP:
            bonus -= _AIMLESS_BISHOP_DRIFT_PENALTY
        elif before_piece.kind == PieceType.ROOK:
            bonus -= _AIMLESS_ROOK_DRIFT_PENALTY
    return bonus


def _child_board_for_move(board: Board, move: Move) -> Board | None:
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return None
    return child_board


def _nearest_focus_distance(
    square: tuple[int, int],
    critical_squares: tuple[tuple[int, int], ...],
) -> int:
    if not critical_squares:
        return 0
    return min(_manhattan_distance(square, critical) for critical in critical_squares)


def _rook_on_critical_file(
    square: tuple[int, int],
    context: LowMaterialCoordinationContext,
) -> bool:
    col = square[1]
    return any(col == critical[1] for critical in context.critical_squares)


def _is_rook_pawn(pawn: tuple[int, int]) -> bool:
    return pawn[1] in {0, 7}


def _advance_square(color: Color, pawn: tuple[int, int]) -> tuple[int, int] | None:
    row, col = pawn
    next_row = row - 1 if color == Color.WHITE else row + 1
    if not 0 <= next_row < 8:
        return None
    return next_row, col


def _promotion_square(color: Color, col: int) -> tuple[int, int]:
    return (0, col) if color == Color.WHITE else (7, col)


def _block_square(color: Color, pawn: tuple[int, int]) -> tuple[int, int]:
    row, col = pawn
    return (row - 1, col) if color == Color.WHITE else (row + 1, col)


def _square_color(square: tuple[int, int]) -> int:
    return (square[0] + square[1]) % 2


def _square_to_constant(square: tuple[int, int]) -> ConstantSquare:
    return get_square_constant(square[0], square[1])


def _manhattan_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _king_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return max(abs(first[0] - second[0]), abs(first[1] - second[1]))


def _is_behind_pawn(color: Color, piece_row: int, pawn_row: int) -> bool:
    return piece_row > pawn_row if color == Color.WHITE else piece_row < pawn_row


def _is_in_front_of_pawn(color: Color, piece_row: int, pawn_row: int) -> bool:
    return piece_row < pawn_row if color == Color.WHITE else piece_row > pawn_row
