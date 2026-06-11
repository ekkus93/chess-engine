"""Root move-selection helpers: aspiration window, tie-break, alpha-beta update.

Extracted from ``ai_search_helpers.py``. These are pure scoring/selection helpers
(no board or guidance dependencies) used by the root search loop in ``ai.py``.
``ai_search_helpers`` re-exports the public names so existing imports keep working.
"""

from __future__ import annotations

from typing import Any, Optional

from chess_game.chess.move import Move
from chess_game.chess.types import LegalMove

ROOT_TIEBREAK_MARGIN, ROOT_TIEBREAK_OVERRIDE = 50, 24
ROOT_TIEBREAK_MAX_SCORE_GAP, ROOT_TIEBREAK_WINNING_SCORE = 96, 1000


def initial_root_window(
    depth: int,
    previous_score: int,
    aspiration_window: int,
    inf: int,
) -> tuple[int, int]:
    """Return the initial alpha-beta window for one root search."""

    if depth == 1:
        return -inf, inf
    return previous_score - aspiration_window, previous_score + aspiration_window


def rerun_full_window_if_needed(
    score: int,
    alpha: int,
    beta: int,
    context: Any,
    inf: int,
) -> bool:
    """Return True when the root search must rerun with a full window."""

    if alpha == -inf and beta == inf:
        return False
    if score <= alpha:
        if context.stats is not None:
            context.stats.fail_low_retries += 1
        return True
    if score >= beta:
        if context.stats is not None:
            context.stats.fail_high_retries += 1
        return True
    return False


def prefer_root_move(
    is_maximizing: bool,
    child_score: int,
    root_tiebreak: int,
    selected_score: int,
    best_root_tiebreak: int,
) -> bool:
    """Return True when a near-equal root move should replace the current pick."""

    score_gap = child_score - selected_score
    if not is_maximizing:
        score_gap = -score_gap
    tiebreak_gap = (
        root_tiebreak - best_root_tiebreak
        if is_maximizing
        else best_root_tiebreak - root_tiebreak
    )
    if score_gap > ROOT_TIEBREAK_MARGIN:
        return True
    if score_gap < -ROOT_TIEBREAK_MARGIN:
        return _strong_root_tiebreak_override(
            is_maximizing,
            child_score,
            selected_score,
            score_gap,
            tiebreak_gap,
        )
    if root_tiebreak != best_root_tiebreak:
        if score_gap > 0:
            return not (
                -tiebreak_gap >= ROOT_TIEBREAK_OVERRIDE and -tiebreak_gap > score_gap
            )
        if score_gap < 0:
            return tiebreak_gap >= ROOT_TIEBREAK_OVERRIDE and tiebreak_gap > -score_gap
        return tiebreak_gap > 0
    return score_gap > 0


def _strong_root_tiebreak_override(
    is_maximizing: bool,
    child_score: int,
    selected_score: int,
    score_gap: int,
    tiebreak_gap: int,
) -> bool:
    if not _is_clearly_winning_choice(is_maximizing, child_score, selected_score):
        return False
    return (
        tiebreak_gap >= -score_gap + ROOT_TIEBREAK_OVERRIDE
        and -score_gap <= ROOT_TIEBREAK_MAX_SCORE_GAP
    )


def _is_clearly_winning_choice(
    is_maximizing: bool,
    child_score: int,
    selected_score: int,
) -> bool:
    threshold = ROOT_TIEBREAK_WINNING_SCORE
    if is_maximizing:
        return child_score >= threshold and selected_score >= threshold
    return child_score <= -threshold and selected_score <= -threshold


def update_best_result(
    is_maximizing: bool,
    move: Move,
    child_score: int,
    best_score: int,
    best_move: Optional[LegalMove],
) -> tuple[int, Optional[LegalMove]]:
    """Update the best move/score for the current node."""

    better_score = child_score > best_score if is_maximizing else child_score < best_score
    if not better_score:
        return best_score, best_move
    return child_score, LegalMove(move.start, move.end, move.promotion)


def update_alpha_beta(
    is_maximizing: bool,
    best_score: int,
    alpha: int,
    beta: int,
) -> tuple[int, int, bool]:
    """Update alpha/beta and report whether a cutoff occurred."""

    if is_maximizing:
        alpha = max(alpha, best_score)
        return alpha, beta, alpha >= beta
    beta = min(beta, best_score)
    return alpha, beta, beta <= alpha
