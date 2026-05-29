"""Endgame-only quiet-order and root tie-break guidance."""

from __future__ import annotations

from dataclasses import dataclass

from chess_game.chess.ai_repetition_patterns import move_undoes_last_own_move
from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    both_queens_on_board,
    is_capture_move,
    iter_color_pieces,
    king_coordinates,
    legal_move_count,
    most_advanced_passer,
    non_king_piece_count_at_most,
    opposite_color,
    passed_pawns_for_color,
    path_clear_between,
)
from chess_game.chess.evaluation import evaluate
from chess_game.chess.types import Color, PieceType

_MAX_NON_KING_PIECES = 8
_PRACTICAL_REPEAT_THRESHOLD = 120
_ORDER_SCALE = 4
_ROOT_SCALE = 5
_KING_ACTIVATION_SCORE = 10
_PASSER_SUPPORT_SCORE = 14
_PASSER_BLOCKADE_SCORE = 18
_CUTOFF_SCORE = 18
_SIMPLIFICATION_SCORE = 16
_REPLY_NARROW_SCORE = 10
_BETTER_SIDE_REPEAT_PENALTY = 96
_WORSE_SIDE_REPEAT_BONUS = 64
_MOVE_CUTOFF_BONUS = 96
_ROOT_CUTOFF_BONUS = 120
_WORSE_SIDE_BAD_SIMPLIFICATION_PENALTY = 220
_BETTER_SIDE_THEATER_SWITCH_PENALTY = 28


@dataclass(frozen=True)
class EndgameChoiceContext:
    """Minimal endgame context for one side's practical choice signals."""

    color: Color
    practical_score: int
    own_king: tuple[int, int] | None
    enemy_king: tuple[int, int] | None
    own_passer: tuple[int, int] | None
    enemy_passer: tuple[int, int] | None


def endgame_choice_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for practical endgame choice."""

    if not _is_relevant_endgame(board):
        return 0
    context = _choice_context(board, color)
    child_board = None if context is None else _child_board_for_move(board, move)
    if context is None or child_board is None:
        return 0
    next_context = _choice_context(child_board, color) or context
    bonus = (_side_score(child_board, next_context) - _side_score(board, context)) * _ORDER_SCALE
    bonus += _repeat_adjustment(context.practical_score, board, move)
    bonus += _direct_cutoff_bonus(board, child_board, move, context, next_context)
    bonus -= _theater_switch_penalty(move, context)
    if kind == PieceType.KING:
        bonus += _king_move_bonus(context, next_context)
    return bonus


def endgame_choice_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return a root tie-break bonus for practical endgame choice."""

    if not _is_relevant_endgame(board):
        return 0
    context = _choice_context(board, color)
    if context is None:
        return 0
    next_context = _choice_context(child_board, color) or context
    bonus = (_side_score(child_board, next_context) - _side_score(board, context)) * _ROOT_SCALE
    bonus += _reply_narrowing_bonus(board, child_board, color)
    bonus += _simplification_bonus(board, child_board, context.practical_score)
    bonus += _repeat_adjustment(context.practical_score, board, move)
    bonus += _direct_cutoff_bonus(board, child_board, move, context, next_context) * (
        _ROOT_CUTOFF_BONUS // max(_MOVE_CUTOFF_BONUS, 1)
    )
    bonus -= _theater_switch_penalty(move, context)
    if (
        is_capture_move(board, move)
        and context.practical_score <= -_PRACTICAL_REPEAT_THRESHOLD
    ):
        bonus -= _WORSE_SIDE_BAD_SIMPLIFICATION_PENALTY
    return bonus


def _choice_context(board: Board, color: Color) -> EndgameChoiceContext | None:
    if not _is_relevant_endgame(board):
        return None
    return EndgameChoiceContext(
        color=color,
        practical_score=_practical_score(board, color),
        own_king=king_coordinates(board, color),
        enemy_king=king_coordinates(board, opposite_color(color)),
        own_passer=most_advanced_passer(color, passed_pawns_for_color(board, color)),
        enemy_passer=most_advanced_passer(
            opposite_color(color),
            passed_pawns_for_color(board, opposite_color(color)),
        ),
    )


def _is_relevant_endgame(board: Board) -> bool:
    if both_queens_on_board(board):
        return False
    if not non_king_piece_count_at_most(board, _MAX_NON_KING_PIECES):
        return False
    rooks = 0
    for row in board.board:
        for piece in row:
            if piece is None or piece.kind == PieceType.KING:
                continue
            if piece.kind in {PieceType.QUEEN, PieceType.KNIGHT}:
                return False
            if piece.kind == PieceType.ROOK:
                rooks += 1
                if rooks > 1:
                    return False
    return True


def _practical_score(board: Board, color: Color) -> int:
    score = evaluate(board)
    return score if color == Color.WHITE else -score


def _side_score(board: Board, context: EndgameChoiceContext) -> int:
    score = 0
    score += _king_focus_score(context)
    score += _passer_support_score(board, context)
    score += _passer_blockade_score(board, context)
    score += _cutoff_score(board, context)
    return score


def _king_focus_score(context: EndgameChoiceContext) -> int:
    own_king = context.own_king
    if own_king is None:
        return 0
    targets: list[tuple[int, int]] = []
    if context.own_passer is not None:
        targets.append(context.own_passer)
    if context.enemy_passer is not None:
        block_square = _block_square(opposite_color(context.color), context.enemy_passer)
        if 0 <= block_square[0] < 8:
            targets.append(block_square)
    if not targets:
        return 0
    distance = min(_manhattan_distance(own_king, target) for target in targets)
    return max(0, 8 - distance) * _KING_ACTIVATION_SCORE


def _passer_support_score(board: Board, context: EndgameChoiceContext) -> int:
    if context.own_passer is None:
        return 0
    score = 0
    for piece, row, col in iter_color_pieces(board, context.color):
        if piece.kind not in {PieceType.ROOK, PieceType.BISHOP, PieceType.KING}:
            continue
        if piece.kind == PieceType.ROOK and col == context.own_passer[1]:
            score += _PASSER_SUPPORT_SCORE
        if piece.kind == PieceType.BISHOP and _same_diagonal(
            (row, col),
            context.own_passer,
        ):
            score += _PASSER_SUPPORT_SCORE // 2
    return score


def _passer_blockade_score(board: Board, context: EndgameChoiceContext) -> int:
    if context.enemy_passer is None:
        return 0
    block_square = _block_square(opposite_color(context.color), context.enemy_passer)
    if not 0 <= block_square[0] < 8:
        return 0
    score = 0
    for piece, row, col in iter_color_pieces(board, context.color):
        if piece.kind == PieceType.KING and (row, col) == block_square:
            score += _PASSER_BLOCKADE_SCORE
        elif piece.kind == PieceType.ROOK and col == context.enemy_passer[1]:
            score += _PASSER_BLOCKADE_SCORE // 2
        elif piece.kind == PieceType.BISHOP and _same_diagonal((row, col), block_square):
            score += _PASSER_BLOCKADE_SCORE // 3
    return score


def _cutoff_score(board: Board, context: EndgameChoiceContext) -> int:
    enemy_king = context.enemy_king
    if enemy_king is None:
        return 0
    score = 0
    for piece, row, col in iter_color_pieces(board, context.color):
        if piece.kind != PieceType.ROOK:
            continue
        same_line = row == enemy_king[0] or col == enemy_king[1]
        if same_line and path_clear_between(board, (row, col), enemy_king):
            score += _CUTOFF_SCORE
    return score


def _reply_narrowing_bonus(board: Board, child_board: Board, color: Color) -> int:
    enemy_color = opposite_color(color)
    before = legal_move_count(board, enemy_color)
    after = legal_move_count(child_board, enemy_color)
    return max(0, before - after) * _REPLY_NARROW_SCORE


def _direct_cutoff_bonus(
    board: Board,
    child_board: Board,
    move: Move,
    context: EndgameChoiceContext,
    next_context: EndgameChoiceContext,
) -> int:
    before_piece = board.get_piece(move.start)
    after_piece = child_board.get_piece(move.end)
    if (
        before_piece is None
        or before_piece.kind != PieceType.ROOK
        or after_piece is None
        or context.enemy_king is None
        or next_context.enemy_king is None
    ):
        return 0
    before_cutoff = _rook_cuts_enemy_king(
        board,
        (int(move.start.row), int(move.start.col)),
        context.enemy_king,
    )
    after_cutoff = _rook_cuts_enemy_king(
        child_board,
        (int(move.end.row), int(move.end.col)),
        next_context.enemy_king,
    )
    if after_cutoff and not before_cutoff:
        return _MOVE_CUTOFF_BONUS
    return 0


def _simplification_bonus(board: Board, child_board: Board, practical_score: int) -> int:
    before = _non_king_count(board)
    after = _non_king_count(child_board)
    if after >= before:
        return 0
    if practical_score >= _PRACTICAL_REPEAT_THRESHOLD:
        return _SIMPLIFICATION_SCORE * (before - after)
    if practical_score <= -_PRACTICAL_REPEAT_THRESHOLD:
        return -_SIMPLIFICATION_SCORE * (before - after)
    return 0


def _repeat_adjustment(practical_score: int, board: Board, move: Move) -> int:
    if not move_undoes_last_own_move(board, move):
        return 0
    if practical_score >= _PRACTICAL_REPEAT_THRESHOLD:
        return -_BETTER_SIDE_REPEAT_PENALTY
    if practical_score <= -_PRACTICAL_REPEAT_THRESHOLD:
        return _WORSE_SIDE_REPEAT_BONUS
    return 0


def _king_move_bonus(
    context: EndgameChoiceContext,
    next_context: EndgameChoiceContext,
) -> int:
    if context.own_king is None or next_context.own_king is None:
        return 0
    before = _king_focus_score(context)
    after = _king_focus_score(next_context)
    return max(0, after - before)


def _theater_switch_penalty(move: Move, context: EndgameChoiceContext) -> int:
    if context.practical_score < _PRACTICAL_REPEAT_THRESHOLD or context.own_passer is None:
        return 0
    start_file_distance = abs(int(move.start.col) - context.own_passer[1])
    end_file_distance = abs(int(move.end.col) - context.own_passer[1])
    if end_file_distance <= start_file_distance:
        return 0
    if end_file_distance == start_file_distance + 1:
        return _BETTER_SIDE_THEATER_SWITCH_PENALTY // 2
    return _BETTER_SIDE_THEATER_SWITCH_PENALTY


def _child_board_for_move(board: Board, move: Move) -> Board | None:
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return None
    return child_board


def _non_king_count(board: Board) -> int:
    return sum(
        1
        for row in board.board
        for piece in row
        if piece is not None and piece.kind != PieceType.KING
    )


def _block_square(color: Color, pawn: tuple[int, int]) -> tuple[int, int]:
    row, col = pawn
    return (row - 1, col) if color == Color.WHITE else (row + 1, col)


def _manhattan_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _same_diagonal(first: tuple[int, int], second: tuple[int, int]) -> bool:
    return abs(first[0] - second[0]) == abs(first[1] - second[1])


def _rook_cuts_enemy_king(
    board: Board,
    rook_square: tuple[int, int],
    enemy_king: tuple[int, int],
) -> bool:
    same_line = rook_square[0] == enemy_king[0] or rook_square[1] == enemy_king[1]
    return same_line and path_clear_between(board, rook_square, enemy_king)
