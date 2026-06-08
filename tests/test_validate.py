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


def test_validation_result_tuned_score_rate_formula() -> None:
    """tuned_score_rate = (wins + 0.5 * draws) / total_games."""
    result = ValidationResult(tuned_wins=2, baseline_wins=1, draws=4)
    assert result.total_games == 7
    expected = (2 + 0.5 * 4) / 7
    assert abs(result.tuned_score_rate - expected) < 1e-9


def test_validation_result_baseline_score_rate_formula() -> None:
    """baseline_score_rate = (baseline_wins + 0.5 * draws) / total_games."""
    result = ValidationResult(tuned_wins=2, baseline_wins=3, draws=2)
    assert result.total_games == 7
    expected = (3 + 0.5 * 2) / 7
    assert abs(result.baseline_score_rate - expected) < 1e-9


def test_validation_result_zero_games_baseline_score_rate() -> None:
    """baseline_score_rate is 0.0 when no games have been played."""
    result = ValidationResult()
    assert result.baseline_score_rate == 0.0


def test_validation_result_all_tuned_wins() -> None:
    """All tuned wins: tuned_score_rate should be 1.0."""
    result = ValidationResult(tuned_wins=10, baseline_wins=0, draws=0)
    assert result.tuned_score_rate == 1.0


def test_validation_result_all_baseline_wins() -> None:
    """All baseline wins: tuned_score_rate should be 0.0."""
    result = ValidationResult(tuned_wins=0, baseline_wins=10, draws=0)
    assert result.tuned_score_rate == 0.0


def test_validation_result_all_draws() -> None:
    """All draws: both score_rates should be 0.5."""
    result = ValidationResult(tuned_wins=0, baseline_wins=0, draws=10)
    assert result.tuned_score_rate == 0.5
    assert result.baseline_score_rate == 0.5


@pytest.mark.slow
def test_run_validation_small() -> None:
    """A small validation match returns a ValidationResult with the right game count."""
    weights = EvalWeights.default()
    result = run_validation_match(weights, num_games=4, depth=1, verbose=False)
    assert isinstance(result, ValidationResult)
    assert result.total_games == 4
    assert result.tuned_wins + result.baseline_wins + result.draws == 4
