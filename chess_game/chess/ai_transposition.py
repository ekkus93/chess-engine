"""Transposition-table access and position-key helpers for the AI search.

Extracted from ``ai.py``. Holds the position-key functions plus the TT
probe/store and TT-reuse diagnostics. Imports only lower-level modules
(``ai_search_types``, ``ai_search_helpers``, ``board``, ``position_utils``), so it
never depends back on ``ai.py``. ``ai.py`` re-exports the names callers rely on.
"""

from __future__ import annotations

from typing import Optional

from chess_game.chess.ai_search_helpers import (
    position_occurrence_count as _position_occurrence_count,
)
from chess_game.chess.ai_search_types import (
    MATE_SCORE,
    MATE_SCORE_MARGIN,
    MinimaxParams,
    SearchContext,
    TTEntry,
    TTFlag,
)
from chess_game.chess.board import Board
from chess_game.chess.position_utils import position_key as _shared_position_key
from chess_game.chess.types import LegalMove


def position_key(board: Board) -> str:
    """Generate a full position key including turn, castling rights, and en passant."""

    return _shared_position_key(board)


def _position_key(board: Board) -> str:
    """Backward-compatible internal alias for the full position key."""

    return position_key(board)


def _fen_key(board: Board) -> str:
    """Compatibility alias for older tests and scripts."""

    return position_key(board)


def _is_mate_score(score: int) -> bool:
    """Return true if score is close to a mate score.

    Mate scores are not stored in TT until proper ply-based normalization exists.
    """
    return abs(score) >= MATE_SCORE - MATE_SCORE_MARGIN


def _record_tt_hit(context: Optional[SearchContext]) -> None:
    """Record a transposition-table hit when stats are enabled."""

    if context is not None and context.stats is not None:
        context.stats.tt_hits += 1


def _record_tt_usage(context: Optional[SearchContext], entry: TTEntry) -> None:
    """Record the kind and depth of a TT reuse."""

    if context is None or context.stats is None:
        return
    if entry.flag == TTFlag.EXACT:
        context.stats.tt_exact_hits += 1
    else:
        context.stats.tt_bound_hits += 1
    assert context.stats.diagnostics is not None
    assert context.stats.diagnostics.tt is not None
    context.stats.diagnostics.tt.tt_depth_sum += entry.depth
    context.stats.diagnostics.tt.tt_depth_uses += 1


def _check_tt_cache(
    board: Board,
    params: MinimaxParams,
) -> Optional[tuple[int, LegalMove | None]]:
    """Check transposition table for a cached result.

    Mate-score entries are ignored until proper normalization exists.
    """

    if _position_occurrence_count(board, params.context, params.line_history, position_key) > 1:
        return None
    context = params.context
    if context is None or context.transposition_table is None:
        return None
    entry = context.transposition_table.get(position_key(board))
    if entry is None or entry.depth < params.depth or _is_mate_score(entry.score):
        return None
    if entry.flag == TTFlag.EXACT:
        _record_tt_usage(context, entry)
        return (entry.score, entry.best_move)
    lower_bound_hit = entry.flag == TTFlag.LOWERBOUND and entry.score >= params.beta
    upper_bound_hit = entry.flag == TTFlag.UPPERBOUND and entry.score <= params.alpha
    if lower_bound_hit or upper_bound_hit:
        _record_tt_usage(context, entry)
        return (entry.score, entry.best_move)
    return None


def _store_tt_cache(
    board: Board,
    params: MinimaxParams,
    score: int,
    move: LegalMove | None,
    original_window: tuple[int, int],
) -> None:
    """Store a result in the transposition table with the correct bound flag.

    Mate scores are skipped until proper TT mate-score normalization exists.
    """

    if _position_occurrence_count(board, params.context, params.line_history, position_key) > 1:
        return
    context = params.context
    if context is None or context.transposition_table is None:
        return
    if _is_mate_score(score):
        # TODO: Implement mate-score normalization for TT storage/retrieval.
        # Mate scores are ply-relative and corrupt when stored/retrieved without
        # proper adjustment. Skip storage until normalization is implemented.
        return
    alpha_orig, beta_orig = original_window
    if score <= alpha_orig:
        flag = TTFlag.UPPERBOUND
    elif score >= beta_orig:
        flag = TTFlag.LOWERBOUND
    else:
        flag = TTFlag.EXACT
    # TODO: Implement mate-score normalization for TT storage/retrieval.
    # Mate scores are currently not normalized on store/retrieve, which can corrupt
    # mate distance across different search plies. Full normalization is a separate patch.
    new_entry = TTEntry(
        depth=params.depth,
        score=score,
        best_move=move,
        flag=flag,
    )
    key = position_key(board)
    existing = context.transposition_table.get(key)
    if existing is None or params.depth >= existing.depth:
        context.transposition_table[key] = new_entry
