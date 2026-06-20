"""Tests for chess_game.texel.eval_targets and chess_game.texel.eval_tune."""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.eval_targets import (
    compute_eval_targets,
    load_eval_targets,
    save_eval_targets,
)
from chess_game.texel.eval_tune import EvalTuneConfig, eval_tune
from chess_game.texel.features import FeatureMatrix
from chess_game.texel.learn_loop import RoundResult
from chess_game.texel.position_db import PositionDB

_STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
_AFTER_E4_FEN = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"

_PAIRS = [
    (_STARTING_FEN, 0.5),
    (_AFTER_E4_FEN, 1.0),
]


def _tiny_db() -> PositionDB:
    return PositionDB.from_pairs(_PAIRS)


# ---------------------------------------------------------------------------
# eval_targets tests
# ---------------------------------------------------------------------------

class TestComputeEvalTargets:
    def test_shape(self) -> None:
        db = _tiny_db()
        targets = compute_eval_targets(db, EvalWeights(), n_jobs=1)
        assert targets.shape == (2,)

    def test_dtype(self) -> None:
        db = _tiny_db()
        targets = compute_eval_targets(db, EvalWeights(), n_jobs=1)
        assert targets.dtype == np.float32

    def test_values_within_clip(self) -> None:
        db = _tiny_db()
        targets = compute_eval_targets(db, EvalWeights(), n_jobs=1, clip_cp=2000)
        assert np.all(targets >= -2000)
        assert np.all(targets <= 2000)

    def test_starting_position_near_zero(self) -> None:
        db = PositionDB.from_pairs([(_STARTING_FEN, 0.5)])
        targets = compute_eval_targets(db, EvalWeights(), n_jobs=1)
        assert abs(float(targets[0])) < 200

    def test_save_load_roundtrip(self) -> None:
        db = _tiny_db()
        targets = compute_eval_targets(db, EvalWeights(), n_jobs=1)
        with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
            path = Path(f.name)
        try:
            save_eval_targets(targets, path)
            loaded = load_eval_targets(path)
        finally:
            path.unlink(missing_ok=True)
        np.testing.assert_array_equal(targets, loaded)


# ---------------------------------------------------------------------------
# eval_tune tests — use synthetic feature matrix to avoid quiescence overhead
# ---------------------------------------------------------------------------

_D = 463   # total weight dimensions matching EvalWeights


def _synthetic_matrix(n: int = 60) -> FeatureMatrix:
    """Synthetic feature matrix with realistic shape (N, 463)."""
    rng = np.random.default_rng(0)
    F = rng.standard_normal((n, _D)).astype(np.float32)
    outcomes = rng.uniform(0, 1, n).astype(np.float32)
    return FeatureMatrix(F=F, outcomes=outcomes)


def _synthetic_targets(matrix: FeatureMatrix, w_true: np.ndarray) -> np.ndarray:
    """Targets consistent with w_true (exact linear relationship)."""
    return (matrix.F.astype(np.float64) @ w_true).astype(np.float32)


def _w_true_from_defaults(seed: int, pst_scale: float = 20.0) -> np.ndarray:
    """Start from default weights and perturb only PST (5-388).

    The frozen weights (material/bonus) stay at their defaults so that
    eval_tune's frozen-contribution subtraction cancels exactly, leaving a
    clean least-squares problem over the PST block only.
    """
    w = np.array(EvalWeights().to_flat_list(), dtype=np.float64)
    rng = np.random.default_rng(seed)
    w[5:389] = rng.standard_normal(384) * pst_scale
    return w


class TestEvalTune:
    def test_returns_round_result(self) -> None:
        matrix = _synthetic_matrix()
        targets = np.zeros(_D, dtype=np.float32)[:60]
        targets = np.random.default_rng(1).standard_normal(60).astype(np.float32)
        result = eval_tune(matrix, targets, EvalWeights(), EvalTuneConfig(verbose=False))
        assert isinstance(result, RoundResult)

    def test_calibrated_k_is_zero(self) -> None:
        matrix = _synthetic_matrix()
        targets = np.zeros(60, dtype=np.float32)
        result = eval_tune(matrix, targets, EvalWeights(), EvalTuneConfig(verbose=False))
        assert result.calibrated_k == 0.0

    def test_db_size(self) -> None:
        matrix = _synthetic_matrix(n=60)
        targets = np.zeros(60, dtype=np.float32)
        result = eval_tune(matrix, targets, EvalWeights(), EvalTuneConfig(verbose=False))
        assert result.db_size == 60

    def test_val_mse_non_negative(self) -> None:
        matrix = _synthetic_matrix()
        targets = np.random.default_rng(2).standard_normal(60).astype(np.float32)
        result = eval_tune(matrix, targets, EvalWeights(), EvalTuneConfig(verbose=False))
        assert result.baseline_val_mse >= 0.0
        assert result.candidate_val_mse >= 0.0

    def test_least_squares_reduces_val_mse(self) -> None:
        """With a consistent linear target the solver should improve val MSE.

        n=600 > 384 PST weights ensures the training system is overdetermined
        and the solution generalises to the held-out validation rows.
        """
        w_true = _w_true_from_defaults(seed=42, pst_scale=20.0)
        matrix = _synthetic_matrix(n=600)
        targets = _synthetic_targets(matrix, w_true)
        result = eval_tune(matrix, targets, EvalWeights(), EvalTuneConfig(verbose=False))
        assert result.candidate_val_mse < result.baseline_val_mse

    def test_no_promotion_writes_no_file(self) -> None:
        """If val MSE doesn't improve, no weights file is written."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "weights.json"
            matrix = _synthetic_matrix(n=4)
            targets = np.zeros(4, dtype=np.float32)
            cfg = EvalTuneConfig(
                weights_path=path,
                verbose=False,
                validation_fraction=0.5,
            )
            result = eval_tune(matrix, targets, EvalWeights(), cfg)
            assert path.exists() == result.promoted

    def test_promotion_writes_file(self) -> None:
        """With a consistent linear target the solver promotes and writes weights."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "weights.json"
            w_true = _w_true_from_defaults(seed=7, pst_scale=30.0)
            matrix = _synthetic_matrix(n=600)
            targets = _synthetic_targets(matrix, w_true)
            cfg = EvalTuneConfig(weights_path=path, verbose=False)
            result = eval_tune(matrix, targets, EvalWeights(), cfg)
            assert result.promoted
            assert path.exists()

    def test_material_weights_unchanged_after_promotion(self) -> None:
        """Promoted weights must have identical material values to defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "weights.json"
            w_true = _w_true_from_defaults(seed=9, pst_scale=30.0)
            matrix = _synthetic_matrix(n=600)
            targets = _synthetic_targets(matrix, w_true)
            cfg = EvalTuneConfig(weights_path=path, verbose=False)
            result = eval_tune(matrix, targets, EvalWeights(), cfg)
            if result.promoted:
                from chess_game.texel.weights_io import load_weights_or_default
                promoted = load_weights_or_default(path)
                defaults = EvalWeights()
                assert promoted.to_flat_list()[:5] == pytest.approx(
                    defaults.to_flat_list()[:5]
                )
