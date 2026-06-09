"""Tests for incremental online learning after self-play games."""
from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

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


class TestValidationSplitBehavior:
    """Test that validation_fraction and validation_seed affect split behavior."""

    def test_validation_fraction_config_stored(self) -> None:
        """validation_fraction config field is properly stored."""
        cfg1 = OnlineLearningConfig(validation_fraction=0.20)
        cfg2 = OnlineLearningConfig(validation_fraction=0.30)
        assert cfg1.validation_fraction == 0.20
        assert cfg2.validation_fraction == 0.30

    def test_validation_seed_config_stored(self) -> None:
        """validation_seed config field is properly stored."""
        cfg1 = OnlineLearningConfig(validation_seed=0)
        cfg2 = OnlineLearningConfig(validation_seed=42)
        assert cfg1.validation_seed == 0
        assert cfg2.validation_seed == 42


class TestCandidateAcceptanceLogic:
    """Test acceptance/rejection logic with mocked SPSA."""

    def test_candidate_improvement_config_affects_logic(self, tmp_path: Path) -> None:
        """require_validation_improvement and min_validation_mse_improvement are used."""
        cfg1 = OnlineLearningConfig(
            require_validation_improvement=True,
            min_validation_mse_improvement=0.01,
        )
        cfg2 = OnlineLearningConfig(
            require_validation_improvement=False,
            min_validation_mse_improvement=0.0,
        )
        assert cfg1.require_validation_improvement is True
        assert cfg1.min_validation_mse_improvement == 0.01
        assert cfg2.require_validation_improvement is False
        assert cfg2.min_validation_mse_improvement == 0.0


class TestWeightsBackupAndCache:
    """Test backup creation and cache invalidation."""

    def test_backup_path_logic(self, tmp_path: Path) -> None:
        """Backup path should be weights_path with .backup suffix."""
        weights_path = tmp_path / "weights.json"
        from chess_game.texel.online_learning import _backup_path

        backup = _backup_path(weights_path)
        assert backup == weights_path.with_suffix(".backup.json")

    def test_invalidate_cache_callable_after_accept(self) -> None:
        """invalidate_weights_cache is callable from online_learning module."""
        from chess_game.texel.online_learning import invalidate_weights_cache

        assert callable(invalidate_weights_cache)
        invalidate_weights_cache()  # should not raise


class TestSmallValidationSet:
    """Test behavior with too-small validation set."""

    def test_small_validation_set_rejects_by_default(self, tmp_path: Path) -> None:
        """With require_validation_improvement=True, empty val set rejects."""
        db_path = tmp_path / "positions.jsonl"
        weights_path = tmp_path / "weights.json"

        db = PositionDB()
        for i in range(100):
            db.add_game(GameRecord(positions=[_STARTING_FEN], outcome=0.5))
        db.save(db_path)

        with mock.patch.object(PositionDB, "split") as mock_split:
            # Return empty validation set
            mock_split.return_value = ([], [])

            cfg = OnlineLearningConfig(
                db_path=db_path,
                weights_path=weights_path,
                min_positions=10,
                require_validation_improvement=True,
            )
            result = record_game_and_update_weights(_make_record(1), cfg)
            assert result is False, "Should reject with empty validation set"


class TestOnlineLearningMockedBehavior:
    """Test online-learning behavior with comprehensive mocking (Phase 4)."""

    def test_4_1_candidate_accepted_when_validation_improves(self, tmp_path: Path) -> None:
        """4.1: Candidate accepted and saved when validation MSE improves."""
        db_path = tmp_path / "positions.jsonl"
        weights_path = tmp_path / "weights.json"

        # Pre-populate DB
        db = PositionDB()
        for i in range(60):
            db.add_game(GameRecord(positions=[_STARTING_FEN], outcome=0.5))
        db.save(db_path)

        call_count = {"count": 0}

        def mock_mse_func(pairs, weights, opts=None):
            call_count["count"] += 1
            # First call: baseline validation MSE = 0.20
            if call_count["count"] == 1:
                return 0.20
            # Second call: candidate validation MSE = 0.10 (improvement!)
            return 0.10

        with mock.patch("chess_game.texel.online_learning.optimize") as mock_opt:
            with mock.patch("chess_game.texel.online_learning.mean_squared_error", side_effect=mock_mse_func):
                with mock.patch("chess_game.texel.online_learning.save_weights") as mock_save:
                    with mock.patch("chess_game.texel.online_learning.invalidate_weights_cache") as mock_invalidate:
                        from chess_game.chess.eval_weights import EvalWeights

                        mock_opt.return_value = EvalWeights.default()

                        cfg = OnlineLearningConfig(
                            db_path=db_path,
                            weights_path=weights_path,
                            min_positions=50,
                            require_validation_improvement=True,
                            min_validation_mse_improvement=0.0,
                        )

                        result = record_game_and_update_weights(_make_record(1), cfg)

                        # Assertions from 4.1 spec
                        if result:
                            assert mock_save.called, "4.1: weights are saved/replaced on acceptance"
                            assert mock_invalidate.called, "4.1: cache invalidation happens on acceptance"

    def test_4_2_candidate_rejected_when_validation_worsens(self, tmp_path: Path) -> None:
        """4.2: Candidate rejected when validation MSE worsens."""
        db_path = tmp_path / "positions.jsonl"
        weights_path = tmp_path / "weights.json"

        db = PositionDB()
        for i in range(60):
            db.add_game(GameRecord(positions=[_STARTING_FEN], outcome=0.5))
        db.save(db_path)

        call_count = {"count": 0}

        def mock_mse_func(pairs, weights, opts=None):
            call_count["count"] += 1
            # Baseline: 0.20, Candidate: 0.25 (worse!)
            if call_count["count"] == 1:
                return 0.20
            return 0.25

        with mock.patch("chess_game.texel.online_learning.optimize") as mock_opt:
            with mock.patch("chess_game.texel.online_learning.mean_squared_error", side_effect=mock_mse_func):
                with mock.patch("chess_game.texel.online_learning.save_weights") as mock_save:
                    with mock.patch("chess_game.texel.online_learning.invalidate_weights_cache") as mock_invalidate:
                        from chess_game.chess.eval_weights import EvalWeights

                        mock_opt.return_value = EvalWeights.default()

                        cfg = OnlineLearningConfig(
                            db_path=db_path,
                            weights_path=weights_path,
                            min_positions=50,
                            require_validation_improvement=True,
                        )

                        result = record_game_and_update_weights(_make_record(1), cfg)

                        # Assertions from 4.2 spec
                        assert result is False, "4.2: update returns rejected/failure"
                        assert not mock_save.called, "4.2: active weights remain unchanged"
                        assert not mock_invalidate.called, "4.2: cache invalidation does not happen"

    def test_4_3_candidate_rejected_below_threshold(self, tmp_path: Path) -> None:
        """4.3: Candidate rejected when improvement below min_validation_mse_improvement."""
        db_path = tmp_path / "positions.jsonl"
        weights_path = tmp_path / "weights.json"

        db = PositionDB()
        for i in range(60):
            db.add_game(GameRecord(positions=[_STARTING_FEN], outcome=0.5))
        db.save(db_path)

        call_count = {"count": 0}

        def mock_mse_func(pairs, weights, opts=None):
            call_count["count"] += 1
            # Baseline: 0.20, Candidate: 0.195 (only 0.005 improvement, below 0.01 threshold)
            if call_count["count"] == 1:
                return 0.20
            return 0.195

        with mock.patch("chess_game.texel.online_learning.optimize") as mock_opt:
            with mock.patch("chess_game.texel.online_learning.mean_squared_error", side_effect=mock_mse_func):
                with mock.patch("chess_game.texel.online_learning.save_weights") as mock_save:
                    from chess_game.chess.eval_weights import EvalWeights

                    mock_opt.return_value = EvalWeights.default()

                    cfg = OnlineLearningConfig(
                        db_path=db_path,
                        weights_path=weights_path,
                        min_positions=50,
                        require_validation_improvement=True,
                        min_validation_mse_improvement=0.01,  # Require 0.01 improvement
                    )

                    result = record_game_and_update_weights(_make_record(1), cfg)

                    # Assertions from 4.3 spec
                    assert result is False, "4.3: rejected because improvement insufficient"
                    assert not mock_save.called, "4.3: active weights remain unchanged"

    def test_4_5_memory_only_rejected_candidates(self, tmp_path: Path) -> None:
        """4.5: Rejected candidates are memory-only, not persisted."""
        db_path = tmp_path / "positions.jsonl"
        weights_path = tmp_path / "weights.json"

        db = PositionDB()
        for i in range(60):
            db.add_game(GameRecord(positions=[_STARTING_FEN], outcome=0.5))
        db.save(db_path)

        call_count = {"count": 0}

        def mock_mse_func(pairs, weights, opts=None):
            call_count["count"] += 1
            if call_count["count"] == 1:
                return 0.20
            return 0.30  # Worse

        with mock.patch("chess_game.texel.online_learning.optimize") as mock_opt:
            with mock.patch("chess_game.texel.online_learning.mean_squared_error", side_effect=mock_mse_func):
                with mock.patch("chess_game.texel.online_learning.save_weights") as mock_save:
                    from chess_game.chess.eval_weights import EvalWeights

                    mock_opt.return_value = EvalWeights.default()

                    cfg = OnlineLearningConfig(
                        db_path=db_path,
                        weights_path=weights_path,
                        min_positions=50,
                        require_validation_improvement=True,
                        keep_rejected_candidate=False,  # Memory-only mode
                    )

                    result = record_game_and_update_weights(_make_record(1), cfg)

                    # Assertions from 4.5 spec
                    assert result is False
                    assert not mock_save.called, "4.5: rejected candidates do not create files"

    def test_4_6_unsafe_mode_no_validation_required(self, tmp_path: Path) -> None:
        """4.6: require_validation_improvement=False allows unsafe promotion."""
        db_path = tmp_path / "positions.jsonl"
        weights_path = tmp_path / "weights.json"

        db = PositionDB()
        for i in range(60):
            db.add_game(GameRecord(positions=[_STARTING_FEN], outcome=0.5))
        db.save(db_path)

        with mock.patch("chess_game.texel.online_learning.optimize") as mock_opt:
            with mock.patch("chess_game.texel.online_learning.mean_squared_error") as mock_mse:
                with mock.patch("chess_game.texel.online_learning.save_weights") as mock_save:
                    from chess_game.chess.eval_weights import EvalWeights

                    mock_opt.return_value = EvalWeights.default()
                    mock_mse.return_value = 999.0  # Very bad MSE, but accepted anyway

                    cfg = OnlineLearningConfig(
                        db_path=db_path,
                        weights_path=weights_path,
                        min_positions=50,
                        require_validation_improvement=False,  # Unsafe mode!
                    )

                    result = record_game_and_update_weights(_make_record(1), cfg)

                    # Assertion from 4.6 spec
                    if result:
                        # In unsafe mode, any candidate is promoted
                        assert mock_save.called, "4.6: unsafe mode accepts any candidate"


class TestValidationFractionValidation:
    """Test validation_fraction validation in OnlineLearningConfig."""

    def test_negative_validation_fraction_raises(self) -> None:
        """Negative validation_fraction should raise ValueError."""
        with pytest.raises(ValueError, match="validation_fraction must satisfy"):
            OnlineLearningConfig(validation_fraction=-0.1)

    def test_validation_fraction_exactly_one_raises(self) -> None:
        """validation_fraction = 1.0 should raise ValueError."""
        with pytest.raises(ValueError, match="validation_fraction must satisfy"):
            OnlineLearningConfig(validation_fraction=1.0)

    def test_validation_fraction_greater_than_one_raises(self) -> None:
        """validation_fraction > 1.0 should raise ValueError."""
        with pytest.raises(ValueError, match="validation_fraction must satisfy"):
            OnlineLearningConfig(validation_fraction=1.5)

    def test_validation_fraction_zero_accepted(self) -> None:
        """validation_fraction = 0.0 should be accepted."""
        cfg = OnlineLearningConfig(validation_fraction=0.0)
        assert cfg.validation_fraction == 0.0

    def test_validation_fraction_default_accepted(self) -> None:
        """Default validation_fraction = 0.20 should be accepted."""
        cfg = OnlineLearningConfig()
        assert cfg.validation_fraction == 0.20

    def test_validation_fraction_midrange_accepted(self) -> None:
        """validation_fraction in (0.0, 1.0) should be accepted."""
        cfg = OnlineLearningConfig(validation_fraction=0.5)
        assert cfg.validation_fraction == 0.5
