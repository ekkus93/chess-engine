"""Tests for the truthful online-learning summary line in self-play.

Regression guard: the message must report the *actual* reason a candidate was or
was not promoted, instead of the old hard-coded "not enough positions" text.
"""
from __future__ import annotations

from chess_game.self_play import _format_learning_message
from chess_game.texel.online_learning import (
    REASON_CANDIDATE_BELOW_THRESHOLD,
    REASON_CANDIDATE_NOT_BETTER,
    REASON_DISABLED,
    REASON_EMPTY_TRAINING_SPLIT,
    REASON_EMPTY_VALIDATION_SPLIT,
    REASON_NOT_ENOUGH_POSITIONS,
    REASON_UPDATED,
    OnlineLearningConfig,
    OnlineLearningResult,
)


def _cfg() -> OnlineLearningConfig:
    return OnlineLearningConfig(min_positions=50)


def test_updated_message_reports_mse_and_path() -> None:
    cfg = _cfg()
    result = OnlineLearningResult(
        updated=True,
        reason=REASON_UPDATED,
        positions=120,
        baseline_val_mse=0.090000,
        candidate_val_mse=0.085000,
    )
    msg = _format_learning_message(result, cfg)
    assert "weights updated" in msg
    assert str(cfg.weights_path) in msg
    assert "0.090000" in msg and "0.085000" in msg
    assert "120 positions" in msg


def test_not_enough_positions_reports_progress_not_blame() -> None:
    cfg = _cfg()
    result = OnlineLearningResult(
        updated=False, reason=REASON_NOT_ENOUGH_POSITIONS, positions=12
    )
    msg = _format_learning_message(result, cfg)
    assert "12/50 positions" in msg


def test_candidate_not_better_is_not_called_not_enough_positions() -> None:
    """The core bug: a rejected candidate used to say 'not enough positions'."""
    cfg = _cfg()
    result = OnlineLearningResult(
        updated=False,
        reason=REASON_CANDIDATE_NOT_BETTER,
        positions=1330,
        baseline_val_mse=0.082000,
        candidate_val_mse=0.083000,
    )
    msg = _format_learning_message(result, cfg)
    assert "did not beat current weights" in msg
    assert "not enough positions" not in msg.lower()
    assert "0.083000" in msg and "0.082000" in msg


def test_candidate_below_threshold_message() -> None:
    cfg = _cfg()
    result = OnlineLearningResult(
        updated=False,
        reason=REASON_CANDIDATE_BELOW_THRESHOLD,
        positions=1330,
        baseline_val_mse=0.082000,
        candidate_val_mse=0.081999,
    )
    msg = _format_learning_message(result, cfg)
    assert "did not beat current weights" in msg


def test_empty_split_messages() -> None:
    cfg = _cfg()
    for reason in (REASON_EMPTY_TRAINING_SPLIT, REASON_EMPTY_VALIDATION_SPLIT):
        msg = _format_learning_message(
            OnlineLearningResult(updated=False, reason=reason, positions=3), cfg
        )
        assert "split was empty" in msg


def test_unknown_reason_falls_back_to_raw_reason() -> None:
    cfg = _cfg()
    msg = _format_learning_message(
        OnlineLearningResult(updated=False, reason=REASON_DISABLED), cfg
    )
    assert REASON_DISABLED in msg
