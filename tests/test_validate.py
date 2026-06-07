"""Tests for the Texel validation match module."""
from __future__ import annotations

import pytest

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.validate import ValidationResult, run_validation_match


def test_validation_result_game_count_sums_correctly() -> None:
    """total_games is the sum of wins, losses, and draws."""
    result = ValidationResult(tuned_wins=3, baseline_wins=2, draws=5)
    assert result.total_games == 10


def test_validation_result_win_rate_formula() -> None:
    """tuned_win_rate returns wins / total_games."""
    result = ValidationResult(tuned_wins=3, baseline_wins=1, draws=0)
    assert result.total_games == 4
    assert abs(result.tuned_win_rate - 0.75) < 1e-9


def test_validation_result_zero_games_win_rate() -> None:
    """tuned_win_rate is 0.0 when no games have been played."""
    result = ValidationResult()
    assert result.tuned_win_rate == 0.0


@pytest.mark.slow
def test_run_validation_small() -> None:
    """A small validation match returns a ValidationResult with the right game count."""
    weights = EvalWeights.default()
    result = run_validation_match(weights, num_games=4, depth=1, verbose=False)
    assert isinstance(result, ValidationResult)
    assert result.total_games == 4
    assert result.tuned_wins + result.baseline_wins + result.draws == 4
