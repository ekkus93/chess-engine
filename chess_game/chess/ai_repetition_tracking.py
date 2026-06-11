"""Repetition / position-occurrence tracking and repetition-aware draw scoring.

Extracted from ``ai_search_helpers``. Pure helpers (board + stdlib only): the
RepetitionPolicy config, position-count bookkeeping, and the repetition-draw score
biased against the side wasting an advantage. ``ai_search_helpers`` re-exports the
public names so existing imports keep working.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from chess_game.chess.board import Board
from chess_game.chess.types import Color


@dataclass(frozen=True)
class RepetitionPolicy:
    """Configuration for repetition-aware draw scoring."""

    position_key: Callable[[Board], str]
    evaluate: Callable[[Board], int]
    progress: Callable[[Board], int]
    threshold: int
    progress_threshold: int
    penalty: int


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


def _side_to_move_score(board: Board, score: int) -> int:
    return score if board.turn == Color.WHITE else -score


def repetition_score(
    board: Board,
    context: Any,
    line_history: tuple[str, ...],
    policy: RepetitionPolicy,
) -> Optional[int]:
    """Return a repetition-draw score, biased against the side wasting an advantage."""

    if position_occurrence_count(board, context, line_history, policy.position_key) < 3:
        return None
    practical_evaluation = _side_to_move_score(board, policy.evaluate(board))
    practical_progress = _side_to_move_score(board, policy.progress(board))
    penalty = _repetition_penalty(policy, practical_evaluation, practical_progress)
    if practical_evaluation >= policy.threshold:
        return -penalty
    if practical_evaluation <= -policy.threshold:
        return penalty
    if practical_progress >= policy.progress_threshold:
        return -penalty
    if practical_progress <= -policy.progress_threshold:
        return penalty
    return 0


def _repetition_penalty(
    policy: RepetitionPolicy,
    evaluation: int,
    progress: int,
) -> int:
    scale = max(
        abs(evaluation) // max(policy.threshold, 1),
        abs(progress) // max(policy.progress_threshold, 1),
        1,
    )
    cap = 8 if evaluation >= policy.threshold * 2 else 5
    capped_scale = min(scale, cap)
    return policy.penalty * capped_scale
