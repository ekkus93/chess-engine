"""Search helper functions shared by the AI module."""

from dataclasses import dataclass
from typing import Any, Callable, Optional

from chess_game.chess.board import Board


@dataclass(frozen=True)
class RepetitionPolicy:
    """Configuration for repetition-aware draw scoring."""

    position_key: Callable[[Board], str]
    evaluate: Callable[[Board], int]
    progress: Callable[[Board], int]
    threshold: int
    progress_threshold: int
    penalty: int


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


def record_root_research(context: Any) -> None:
    """Record a root re-search caused by aspiration failure."""

    if context.stats is not None:
        context.stats.root_researches += 1


def record_depth_timing(
    context: Any,
    depth: int,
    elapsed: float,
) -> None:
    """Store per-depth timing diagnostics."""

    if context.stats is None:
        return
    if context.stats.depth_timings is None:
        context.stats.depth_timings = {}
    context.stats.depth_timings[depth] = elapsed


def search_position_counts(
    board: Board,
    position_counts: Optional[dict[str, int]],
    position_key: Callable[[Board], str],
) -> Optional[dict[str, int]]:
    """Return repetition counts adjusted so the current root is not double-counted."""

    if position_counts is None:
        return None
    adjusted_counts = dict(position_counts)
    current_key = position_key(board)
    if adjusted_counts.get(current_key, 0) > 0:
        adjusted_counts[current_key] -= 1
        if adjusted_counts[current_key] == 0:
            del adjusted_counts[current_key]
    return adjusted_counts


def position_occurrence_count(
    board: Board,
    context: Any,
    line_history: tuple[str, ...],
    position_key: Callable[[Board], str],
) -> int:
    """Return the number of times the current position has appeared in search/game history."""

    current_key = position_key(board)
    game_count = (
        0
        if context is None or context.position_counts is None
        else context.position_counts.get(current_key, 0)
    )
    return game_count + line_history.count(current_key)


def repetition_score(
    board: Board,
    context: Any,
    line_history: tuple[str, ...],
    policy: RepetitionPolicy,
) -> Optional[int]:
    """Return a repetition-draw score, biased against the side wasting an advantage."""

    if position_occurrence_count(board, context, line_history, policy.position_key) < 3:
        return None
    evaluation = policy.evaluate(board)
    if evaluation >= policy.threshold:
        return -policy.penalty
    if evaluation <= -policy.threshold:
        return policy.penalty
    progress = policy.progress(board)
    if progress >= policy.progress_threshold:
        return -policy.penalty
    if progress <= -policy.progress_threshold:
        return policy.penalty
    return 0
