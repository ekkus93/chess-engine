"""Leaf-node scoring helpers for the AI search: evaluation glue and terminal scoring.

Extracted from ``ai.py``. Both the main search and quiescence need to (a) evaluate
a board through the weights carried on the search context and (b) detect terminal
draw/checkmate positions, so these helpers live in a low-level module that both can
import without depending back on ``ai.py``.
"""

from __future__ import annotations

from typing import Optional

from chess_game.chess.ai_search_helpers import RepetitionPolicy
from chess_game.chess.ai_search_types import DRAW_SCORE, MATE_SCORE, SearchContext
from chess_game.chess.ai_transposition import position_key
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import (
    is_dead_position as _gs_is_dead_position,
    is_fifty_move_rule as _gs_is_fifty_move_rule,
    is_fivefold_repetition as _gs_is_fivefold,
    is_in_check as _gs_is_in_check,
    is_insufficient_material as _gs_is_insufficient_material,
    is_seventy_five_move_rule as _gs_is_seventy_five_move_rule,
)
from chess_game.chess.evaluation import (
    evaluate,
    get_evaluation_breakdown as _get_evaluation_breakdown,
)
from chess_game.chess.evaluation_tables import (
    REPETITION_PROGRESS_ONLY_THRESHOLD,
    REPETITION_PROGRESS_THRESHOLD,
    VOLUNTARY_REPETITION_PENALTY,
)
from chess_game.chess.move import Move
from chess_game.chess.types import Color


def _progress_score(board: Board) -> int:
    """Return the progress component used to discourage empty repetitions."""

    return _get_evaluation_breakdown(board)["progress"]


def _ctx_evaluate(board: Board, context: Optional[SearchContext]) -> int:
    """Evaluate board using the weights stored in context (or defaults)."""
    weights = context.weights if context is not None else None
    return evaluate(board, weights)


def _make_evaluate_fn(context: Optional[SearchContext]):
    """Return an evaluate callable that captures context weights."""

    def _fn(board: Board) -> int:
        return _ctx_evaluate(board, context)

    return _fn


def make_repetition_policy(context: Optional[SearchContext]) -> RepetitionPolicy:
    """Build the repetition policy shared by the main search and quiescence."""

    return RepetitionPolicy(
        position_key=position_key,
        evaluate=_make_evaluate_fn(context),
        progress=_progress_score,
        threshold=REPETITION_PROGRESS_THRESHOLD,
        progress_threshold=REPETITION_PROGRESS_ONLY_THRESHOLD,
        penalty=VOLUNTARY_REPETITION_PENALTY,
    )


def _is_forced_draw(
    board: Board,
    position_counts: Optional[dict[str, int]],
) -> bool:
    return (
        _gs_is_fifty_move_rule(board)
        or _gs_is_seventy_five_move_rule(board)
        or _gs_is_insufficient_material(board)
        or _gs_is_dead_position(board)
        or (position_counts is not None and _gs_is_fivefold(board, position_counts))
    )


def _terminal_score(
    board: Board,
    legal_moves: list[Move],
    ply: int = 0,
    position_counts: Optional[dict[str, int]] = None,
) -> Optional[int]:
    """Return a terminal score for draws and checkmate; None when non-terminal.

    Covers all draw states supported by the board/game-state API:
    - fifty-move rule
    - seventy-five move rule
    - insufficient material
    - dead position
    - fivefold repetition (if position_counts provided)
    - stalemate
    - checkmate (via ply-adjusted mate score)
    """
    if _is_forced_draw(board, position_counts):
        return DRAW_SCORE
    if legal_moves:
        return None
    if _gs_is_in_check(board, board.turn):
        return -MATE_SCORE + ply if board.turn == Color.WHITE else MATE_SCORE - ply
    return DRAW_SCORE
