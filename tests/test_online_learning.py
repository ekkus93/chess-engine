"""Tests for incremental online learning after self-play games."""
from __future__ import annotations

from pathlib import Path

import chess_game.chess.ai as _ai_module
from chess_game.chess.ai import invalidate_weights_cache
from chess_game.texel.online_learning import OnlineLearningConfig, record_game_and_update_weights
from chess_game.texel.position_db import GameRecord, PositionDB

_STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def _make_record(n: int = 5, outcome: float = 0.5) -> GameRecord:
    """Return a GameRecord with *n* copies of the starting position."""
    return GameRecord(positions=[_STARTING_FEN] * n, outcome=outcome)


class TestRecordGameUpdatesDb:
    """record_game_and_update_weights must persist positions to disk."""

    def test_record_game_creates_db_file(self, tmp_path: Path) -> None:
        """Calling with a small record creates the DB file."""
        db_path = tmp_path / "positions.jsonl"
        weights_path = tmp_path / "weights.json"
        cfg = OnlineLearningConfig(
            db_path=db_path,
            weights_path=weights_path,
            min_positions=1_000_000,  # disable tuning
        )
        record_game_and_update_weights(_make_record(3), cfg)
        assert db_path.exists(), "DB file should be created"

    def test_record_game_accumulates_positions(self, tmp_path: Path) -> None:
        """Calling twice accumulates positions in the same DB."""
        db_path = tmp_path / "positions.jsonl"
        weights_path = tmp_path / "weights.json"
        cfg = OnlineLearningConfig(
            db_path=db_path,
            weights_path=weights_path,
            min_positions=1_000_000,
        )
        record_game_and_update_weights(_make_record(3, outcome=1.0), cfg)
        record_game_and_update_weights(_make_record(4, outcome=0.0), cfg)
        db = PositionDB.load(db_path)
        # At least one unique position stored (all FENs are the same so DB
        # may deduplicate — but the file must contain entries)
        assert len(db) >= 1


class TestNoTuningBelowMinPositions:
    """Online learning should skip tuning when DB is too small."""

    def test_returns_false_when_below_min_positions(self, tmp_path: Path) -> None:
        """With min_positions=1000 and only 2 positions, returns False."""
        db_path = tmp_path / "positions.jsonl"
        weights_path = tmp_path / "weights.json"
        cfg = OnlineLearningConfig(
            db_path=db_path,
            weights_path=weights_path,
            min_positions=1_000,
            spsa_iterations=2,
        )
        result = record_game_and_update_weights(_make_record(2), cfg)
        assert result is False

    def test_disabled_config_returns_false(self, tmp_path: Path) -> None:
        """When enabled=False, always returns False and does not write DB."""
        db_path = tmp_path / "positions.jsonl"
        weights_path = tmp_path / "weights.json"
        cfg = OnlineLearningConfig(
            db_path=db_path,
            weights_path=weights_path,
            enabled=False,
        )
        result = record_game_and_update_weights(_make_record(10), cfg)
        assert result is False
        assert not db_path.exists(), "DB should not be written when disabled"


class TestInvalidateWeightsCacheIsCallable:
    """invalidate_weights_cache must be importable and callable."""

    def test_invalidate_weights_cache_is_callable(self) -> None:
        """invalidate_weights_cache can be called without raising."""
        # Should not raise and should be a function
        assert callable(invalidate_weights_cache)
        invalidate_weights_cache()  # must not raise

    def test_invalidate_from_ai_module(self) -> None:
        """The function is re-exported from chess_game.chess.ai."""
        assert callable(getattr(_ai_module, "invalidate_weights_cache", None))


class TestOnlineLearningConfigValidationGate:
    """Test online learning validation gate configuration."""

    def test_default_config_has_validation_gate_defaults(self) -> None:
        """Default config should have sensible validation gate values."""
        cfg = OnlineLearningConfig()
        assert cfg.require_validation_improvement is True
        assert cfg.min_validation_mse_improvement == 0.0
        assert cfg.keep_rejected_candidate is False
        assert cfg.validation_fraction == 0.20
        assert cfg.validation_seed == 0

    def test_config_validation_gate_fields_are_settable(self) -> None:
        """Validation gate fields should be configurable."""
        cfg = OnlineLearningConfig(
            require_validation_improvement=False,
            min_validation_mse_improvement=0.001,
            keep_rejected_candidate=True,
            validation_fraction=0.25,
            validation_seed=42,
        )
        assert cfg.require_validation_improvement is False
        assert cfg.min_validation_mse_improvement == 0.001
        assert cfg.keep_rejected_candidate is True
        assert cfg.validation_fraction == 0.25
        assert cfg.validation_seed == 42
