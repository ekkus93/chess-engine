"""Tests for the SPSA optimizer."""
from __future__ import annotations

from pathlib import Path

import pytest

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.position_db import GameRecord, PositionDB
from chess_game.texel.spsa import SPSAOptions, _clip_weights, optimize

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def _make_db_with_one_position() -> PositionDB:
    """Build a minimal PositionDB with a single known position."""
    db = PositionDB()
    record = GameRecord(positions=[STARTING_FEN], outcome=0.5)
    db.add_game(record)
    return db


class TestClipWeights:
    """Tests for the weight-clipping helper."""

    def test_clip_weights_keeps_material_positive(self) -> None:
        """Material values (first 5) must never fall below 1.0."""
        defaults = EvalWeights.default().to_flat_list()
        # Set first 5 weights to negative values
        bad = list(defaults)
        for i in range(5):
            bad[i] = -100.0
        clipped = _clip_weights(bad)
        for i in range(5):
            assert clipped[i] >= 1.0

    def test_clip_weights_caps_pst_values(self) -> None:
        """Piece-square table values (indices 5..388) must be within [-200, 200]."""
        defaults = EvalWeights.default().to_flat_list()
        extreme = list(defaults)
        for i in range(5, 5 + 384):
            extreme[i] = 9999.0
        clipped = _clip_weights(extreme)
        for i in range(5, 5 + 384):
            assert clipped[i] <= 200.0

    def test_clip_weights_caps_scalar_weights(self) -> None:
        """Scalar weights beyond index 389 must be within [-500, 500]."""
        defaults = EvalWeights.default().to_flat_list()
        extreme = list(defaults)
        for i in range(5 + 384, len(extreme)):
            extreme[i] = 9999.0
        clipped = _clip_weights(extreme)
        for i in range(5 + 384, len(clipped)):
            assert clipped[i] <= 500.0


class TestOptimize:
    """Tests for the SPSA optimize function."""

    def test_spsa_returns_eval_weights_instance(self) -> None:
        """optimize() must return an EvalWeights instance."""
        db = _make_db_with_one_position()
        weights = EvalWeights.default()
        opts = SPSAOptions(max_iterations=2, verbose=False)
        result = optimize(weights, db, opts)
        assert isinstance(result, EvalWeights)

    def test_spsa_checkpoint_written(self, tmp_path: Path) -> None:
        """A checkpoint file should be written at the specified interval."""
        db = _make_db_with_one_position()
        weights = EvalWeights.default()
        checkpoint = tmp_path / "checkpoints" / "weights.json"
        opts = SPSAOptions(
            max_iterations=10,
            checkpoint_every=5,
            checkpoint_path=checkpoint,
            verbose=False,
        )
        optimize(weights, db, opts)
        assert checkpoint.exists()

    @pytest.mark.slow
    def test_spsa_runs_without_error_on_small_db(self, tmp_path: Path) -> None:
        """SPSA should complete 20 iterations on a small DB without error."""
        db = _make_db_with_one_position()
        weights = EvalWeights.default()
        opts = SPSAOptions(max_iterations=20, verbose=False)
        result = optimize(weights, db, opts)
        assert isinstance(result, EvalWeights)
        flat = result.to_flat_list()
        assert len(flat) == len(weights.to_flat_list())
