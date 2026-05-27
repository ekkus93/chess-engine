"""Practical guidance for low-material endgames that need king activity."""

from __future__ import annotations

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    center_distance,
    iter_color_pieces,
    king_coordinates,
    non_king_material_lead,
    opposite_color,
    passed_pawns_for_color,
    most_advanced_passer,
)
from chess_game.chess.types import Color, PieceType

_MAX_MINOR_PIECES = 2
_MAX_PAWNS = 6
_KING_FOCUS_BONUS = 18
_KING_CENTER_BONUS = 8
_KING_BLOCKADE_BONUS = 14
_KING_ESCORT_BONUS = 12
_PIECE_DRIFT_PENALTY = 26
_BISHOP_FOCUS_BONUS = 8
_ROOT_SCALE = 5
_ROOT_KING_ACTIVITY_BONUS = 16
_ROOT_PASSIVE_PIECE_PENALTY = 28
_EVAL_KING_FOCUS = 2
_EVAL_KING_CENTER = 1
_EVAL_KING_BLOCKADE = 3
_EVAL_KING_ESCORT = 2
_EVAL_BISHOP_FOCUS = 1
_OPPOSITION_BONUS = 8
_KING_CUTOFF_BONUS = 6


@dataclass(frozen=True)
class SimpleEndgameContext:
    """Compact context for one side in a low-material ending."""

    color: Color
    mode: str
    focus: tuple[int, int]
    own_passer: tuple[int, int] | None
    enemy_passer: tuple[int, int] | None


def simple_endgame_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for practical king-led endgame play."""

    if kind not in {PieceType.KING, PieceType.BISHOP}:
        return 0
    context = _simple_endgame_context(board, color)
    if context is None:
        return 0
    start = (int(move.start.row), int(move.start.col))
    end = (int(move.end.row), int(move.end.col))
    if kind == PieceType.KING:
        return _king_order_bonus(start, end, context)
    return _piece_order_bonus(board, start, end, kind, context)


def simple_endgame_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return a root bonus for low-material moves that improve the real plan."""

    piece = board.get_piece(move.start)
    if piece is None or piece.kind not in {PieceType.KING, PieceType.BISHOP}:
        return 0
    context = _simple_endgame_context(board, color)
    if context is None:
        return 0
    next_context = _simple_endgame_context(child_board, color) or context
    before = _side_score(board, context)
    after = _side_score(child_board, next_context)
    bonus = (after - before) * _ROOT_SCALE
    if piece.kind == PieceType.KING and after > before:
        bonus += _ROOT_KING_ACTIVITY_BONUS
    elif piece.kind != PieceType.KING and _king_is_passive(board, context):
        bonus -= _ROOT_PASSIVE_PIECE_PENALTY
    return bonus


def simple_endgame_evaluation_score(board: Board) -> int:
    """Return low-material king-geometry bonuses for both sides."""

    total = 0
    for color in (Color.WHITE, Color.BLACK):
        context = _simple_endgame_context(board, color)
        if context is None:
            continue
        color_score = _evaluation_side_score(board, context)
        color_score += _opposition_score(board, context)
        color_score += _king_cutoff_score(board, context)
        sign = 1 if color == Color.WHITE else -1
        total += sign * color_score
    return total


def _simple_endgame_context(board: Board, color: Color) -> SimpleEndgameContext | None:
    queens = 0
    rooks = 0
    minors = 0
    pawns = 0
    for row in board.board:
        for piece in row:
            if piece is None or piece.kind == PieceType.KING:
                continue
            if piece.kind == PieceType.QUEEN:
                queens += 1
            elif piece.kind == PieceType.ROOK:
                rooks += 1
            elif piece.kind in {PieceType.BISHOP, PieceType.KNIGHT}:
                minors += 1
            elif piece.kind == PieceType.PAWN:
                pawns += 1
    if queens > 0 or rooks > 0 or minors > _MAX_MINOR_PIECES or pawns > _MAX_PAWNS:
        return None
    own_passer = most_advanced_passer(color, passed_pawns_for_color(board, color))
    enemy_color = opposite_color(color)
    enemy_passer = most_advanced_passer(enemy_color, passed_pawns_for_color(board, enemy_color))
    if own_passer is None and enemy_passer is None:
        return None
    focus = _focus_square(board, color, own_passer, enemy_passer)
    if focus is None:
        return None
    lead = non_king_material_lead(board, color)
    mode = "better" if lead > 0 else "worse" if lead < 0 else "equal"
    return SimpleEndgameContext(
        color=color,
        mode=mode,
        focus=focus,
        own_passer=own_passer,
        enemy_passer=enemy_passer,
    )


def _focus_square(
    board: Board,
    color: Color,
    own_passer: tuple[int, int] | None,
    enemy_passer: tuple[int, int] | None,
) -> tuple[int, int] | None:
    enemy_color = opposite_color(color)
    if enemy_passer is not None:
        return _block_square(enemy_color, enemy_passer)
    if own_passer is not None:
        return own_passer
    enemy_king = king_coordinates(board, enemy_color)
    if enemy_king is not None:
        return enemy_king
    return None


def _king_order_bonus(
    start: tuple[int, int],
    end: tuple[int, int],
    context: SimpleEndgameContext,
) -> int:
    score = max(0, _distance(start, context.focus) - _distance(end, context.focus))
    score *= _KING_FOCUS_BONUS
    score += max(0, center_distance(*start) - center_distance(*end)) * _KING_CENTER_BONUS
    if context.enemy_passer is not None:
        block_square = _block_square(opposite_color(context.color), context.enemy_passer)
        score += max(0, _distance(start, block_square) - _distance(end, block_square))
        score *= _KING_BLOCKADE_BONUS // 2
    if context.own_passer is not None:
        score += (
            max(0, _distance(start, context.own_passer) - _distance(end, context.own_passer))
            * _KING_ESCORT_BONUS
        )
    return score


def _piece_order_bonus(
    board: Board,
    start: tuple[int, int],
    end: tuple[int, int],
    kind: PieceType,
    context: SimpleEndgameContext,
) -> int:
    score = 0
    if _king_is_passive(board, context) and _distance(end, context.focus) >= _distance(
        start, context.focus
    ):
        score -= _PIECE_DRIFT_PENALTY
    if kind == PieceType.BISHOP and _same_diagonal(end, context.focus):
        score += _BISHOP_FOCUS_BONUS
    return score


def _side_score(board: Board, context: SimpleEndgameContext) -> int:
    own_king = king_coordinates(board, context.color)
    if own_king is None:
        return 0
    score = max(0, 10 - _distance(own_king, context.focus)) * _KING_FOCUS_BONUS
    score += max(0, 6 - center_distance(*own_king)) * _KING_CENTER_BONUS
    if context.enemy_passer is not None:
        block_square = _block_square(opposite_color(context.color), context.enemy_passer)
        score += max(0, 8 - _distance(own_king, block_square)) * _KING_BLOCKADE_BONUS
    if context.own_passer is not None:
        score += max(0, 8 - _distance(own_king, context.own_passer)) * _KING_ESCORT_BONUS
    for piece, row, col in iter_color_pieces(board, context.color):
        if piece.kind == PieceType.BISHOP and _same_diagonal((row, col), context.focus):
            score += _BISHOP_FOCUS_BONUS
    return score


def _evaluation_side_score(board: Board, context: SimpleEndgameContext) -> int:
    own_king = king_coordinates(board, context.color)
    if own_king is None:
        return 0
    score = max(0, 8 - _distance(own_king, context.focus)) * _EVAL_KING_FOCUS
    score += max(0, 4 - center_distance(*own_king)) * _EVAL_KING_CENTER
    if context.enemy_passer is not None:
        block_square = _block_square(opposite_color(context.color), context.enemy_passer)
        score += max(0, 6 - _distance(own_king, block_square)) * _EVAL_KING_BLOCKADE
    if context.own_passer is not None:
        score += max(0, 5 - _distance(own_king, context.own_passer)) * _EVAL_KING_ESCORT
    for piece, row, col in iter_color_pieces(board, context.color):
        if piece.kind == PieceType.BISHOP and _same_diagonal((row, col), context.focus):
            score += _EVAL_BISHOP_FOCUS
    return score


def _opposition_score(board: Board, context: SimpleEndgameContext) -> int:
    score = 0
    if _has_minor_pieces(board):
        return score
    own_king = king_coordinates(board, context.color)
    enemy_king = king_coordinates(board, opposite_color(context.color))
    if own_king is None or enemy_king is None:
        return score
    if own_king[0] == enemy_king[0]:
        gap = abs(own_king[1] - enemy_king[1])
    elif own_king[1] == enemy_king[1]:
        gap = abs(own_king[0] - enemy_king[0])
    else:
        gap = 0
    if gap == 2:
        own_focus = _distance(own_king, context.focus)
        enemy_focus = _distance(enemy_king, context.focus)
        if own_focus <= enemy_focus:
            score = _OPPOSITION_BONUS
        else:
            score = -_OPPOSITION_BONUS
    return score


def _king_cutoff_score(board: Board, context: SimpleEndgameContext) -> int:
    own_king = king_coordinates(board, context.color)
    enemy_king = king_coordinates(board, opposite_color(context.color))
    if own_king is None or enemy_king is None:
        return 0
    if own_king[0] == enemy_king[0] and abs(own_king[1] - enemy_king[1]) >= 2:
        if abs(context.focus[1] - enemy_king[1]) > abs(context.focus[1] - own_king[1]):
            return _KING_CUTOFF_BONUS
    if own_king[1] == enemy_king[1] and abs(own_king[0] - enemy_king[0]) >= 2:
        if abs(context.focus[0] - enemy_king[0]) > abs(context.focus[0] - own_king[0]):
            return _KING_CUTOFF_BONUS
    return 0


def _king_is_passive(board: Board, context: SimpleEndgameContext) -> bool:
    own_king = king_coordinates(board, context.color)
    if own_king is None:
        return False
    return _distance(own_king, context.focus) >= 4


def _has_minor_pieces(board: Board) -> bool:
    for row in board.board:
        for piece in row:
            if piece is not None and piece.kind in {PieceType.BISHOP, PieceType.KNIGHT}:
                return True
    return False


def _block_square(color: Color, pawn: tuple[int, int]) -> tuple[int, int]:
    row_step = 1 if color == Color.BLACK else -1
    row = max(0, min(7, pawn[0] + row_step))
    return row, pawn[1]


def _distance(start: tuple[int, int], end: tuple[int, int]) -> int:
    return abs(start[0] - end[0]) + abs(start[1] - end[1])


def _same_diagonal(start: tuple[int, int], end: tuple[int, int]) -> bool:
    return abs(start[0] - end[0]) == abs(start[1] - end[1])
