"""Texel fail-loud: online learning reports a distinct reason instead of a bare False.

``record_game_and_update_weights_result`` returns an ``OnlineLearningResult`` whose
``reason`` names exactly which guard path was taken; the legacy bool wrapper stays
consistent with ``result.updated``.
"""
from __future__ import annotations

from pathlib import Path
from unittest import mock

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.online_learning import (
    REASON_CANDIDATE_NOT_BETTER,
    REASON_DISABLED,
    REASON_EMPTY_TRAINING_SPLIT,
    REASON_EMPTY_VALIDATION_SPLIT,
    REASON_NOT_ENOUGH_POSITIONS,
    OnlineLearningConfig,
    OnlineLearningResult,
    record_game_and_update_weights,
    record_game_and_update_weights_result,
)
from chess_game.texel.position_db import GameRecord

_FEN_A = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
_FEN_B = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"


def _cfg(tmp_path: Path, **kw: object) -> OnlineLearningConfig:
    return OnlineLearningConfig(
        db_path=tmp_path / "positions.jsonl",
        weights_path=tmp_path / "weights.json",
        **kw,  # type: ignore[arg-type]
    )


def test_disabled_reports_disabled(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path, enabled=False)
    result = record_game_and_update_weights_result(_make(_FEN_A), cfg)
    assert result == OnlineLearningResult(updated=False, reason=REASON_DISABLED)


def test_not_enough_positions_reports_reason(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path, min_positions=1_000)
    result = record_game_and_update_weights_result(_make(_FEN_A), cfg)
    assert result.updated is False
    assert result.reason == REASON_NOT_ENOUGH_POSITIONS
    assert result.positions == 1


def test_empty_validation_split_reports_reason(tmp_path: Path) -> None:
    """A single unique FEN leaves the held-out validation split empty."""
    cfg = _cfg(tmp_path, min_positions=1, require_validation_improvement=True)
    result = record_game_and_update_weights_result(_make(_FEN_A), cfg)
    assert result.updated is False
    assert result.reason == REASON_EMPTY_VALIDATION_SPLIT


def test_empty_training_split_reports_reason(tmp_path: Path) -> None:
    """An empty game (no positions) with validation off yields no training pairs."""
    cfg = _cfg(tmp_path, min_positions=0, require_validation_improvement=False)
    result = record_game_and_update_weights_result(GameRecord(positions=[]), cfg)
    assert result.updated is False
    assert result.reason == REASON_EMPTY_TRAINING_SPLIT


def test_candidate_not_better_reports_reason(tmp_path: Path) -> None:
    """A candidate identical to the baseline does not lower validation MSE."""
    cfg = _cfg(tmp_path, min_positions=1, require_validation_improvement=True)
    record = GameRecord(positions=[_FEN_A, _FEN_B], outcome=1.0)
    with mock.patch(
        "chess_game.texel.online_learning.optimize",
        return_value=EvalWeights.default(),
    ):
        result = record_game_and_update_weights_result(record, cfg)
    assert result.updated is False
    assert result.reason == REASON_CANDIDATE_NOT_BETTER
    assert result.baseline_val_mse is not None
    assert result.candidate_val_mse == result.baseline_val_mse


def test_bool_wrapper_matches_result_updated(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path, min_positions=1_000)
    record = _make(_FEN_A)
    structured = record_game_and_update_weights_result(record, _cfg(tmp_path, min_positions=1_000))
    assert record_game_and_update_weights(record, cfg) is structured.updated is False


def _make(fen: str) -> GameRecord:
    return GameRecord(positions=[fen], outcome=0.5)
