"""Tests for chess_game.texel.features and chess_game.texel.fast_tune."""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.features import (
    FeatureMatrix,
    compute_feature_matrix,
    load_features,
    save_features,
)
from chess_game.texel.fast_tune import (
    AdamConfig,
    FastTuneConfig,
    calibrate_k_fast,
    fast_mse,
    fast_gradient,
    fast_tune,
    optimize_adam,
)
from chess_game.texel.learn_loop import RoundResult
from chess_game.texel.position_db import PositionDB


# ---------------------------------------------------------------------------
# Tiny synthetic dataset: two positions with known outcomes
# ---------------------------------------------------------------------------

_STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
_AFTER_E4_FEN = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"

_PAIRS = [
    (_STARTING_FEN, 0.5),
    (_AFTER_E4_FEN, 1.0),
]


def _tiny_db() -> PositionDB:
    return PositionDB.from_pairs(_PAIRS)


def _tiny_matrix(weights: EvalWeights | None = None) -> FeatureMatrix:
    db = _tiny_db()
    w = weights or EvalWeights()
    return compute_feature_matrix(db, w, n_jobs=1)


# ---------------------------------------------------------------------------
# features.py tests
# ---------------------------------------------------------------------------

class TestComputeFeatureMatrix:
    def test_shape(self) -> None:
        matrix = _tiny_matrix()
        assert matrix.F.shape == (2, 463)
        assert matrix.outcomes.shape == (2,)

    def test_outcomes_preserved(self) -> None:
        matrix = _tiny_matrix()
        # Outcomes must be 0.5 and 1.0 (order matches all_pairs order)
        assert set(matrix.outcomes.tolist()) == {0.5, 1.0}

    def test_dtype(self) -> None:
        matrix = _tiny_matrix()
        assert matrix.F.dtype == np.float32
        assert matrix.outcomes.dtype == np.float32

    def test_pst_features_nonzero(self) -> None:
        matrix = _tiny_matrix()
        # PST weights (indices 5–388) capture piece placement; at least one
        # column must be non-zero since pieces occupy different squares.
        pst_block = matrix.F[:, 5:389]
        assert not np.all(pst_block == 0)

    def test_save_load_roundtrip(self) -> None:
        matrix = _tiny_matrix()
        with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
            path = Path(f.name)
        try:
            save_features(matrix, path)
            loaded = load_features(path)
        finally:
            path.unlink(missing_ok=True)
        np.testing.assert_array_equal(matrix.F, loaded.F)
        np.testing.assert_array_equal(matrix.outcomes, loaded.outcomes)


# ---------------------------------------------------------------------------
# fast_tune.py helpers
# ---------------------------------------------------------------------------

class TestFastMse:
    def test_zero_loss_when_perfect(self) -> None:
        # If all outcomes are 0.5 and the eval is 0 (sigmoid=0.5), MSE=0
        feat = np.zeros((3, 5), dtype=np.float64)
        outcomes = np.full(3, 0.5, dtype=np.float64)
        w = np.zeros(5, dtype=np.float64)
        assert fast_mse(feat, outcomes, w, k=1.0) == pytest.approx(0.0)

    def test_mse_positive(self) -> None:
        feat = np.ones((4, 3), dtype=np.float64)
        outcomes = np.array([1.0, 0.0, 1.0, 0.0], dtype=np.float64)
        w = np.zeros(3, dtype=np.float64)
        mse = fast_mse(feat, outcomes, w, k=1.0)
        assert mse > 0.0


class TestFastGradient:
    def test_gradient_shape(self) -> None:
        feat = np.random.randn(10, 7).astype(np.float64)
        outcomes = np.random.uniform(0, 1, 10).astype(np.float64)
        w = np.zeros(7, dtype=np.float64)
        g = fast_gradient(feat, outcomes, w, k=1.0)
        assert g.shape == (7,)

    def test_gradient_direction_reduces_loss(self) -> None:
        np.random.seed(0)
        feat = np.random.randn(50, 5).astype(np.float64)
        outcomes = np.random.uniform(0, 1, 50).astype(np.float64)
        w = np.zeros(5, dtype=np.float64)
        g = fast_gradient(feat, outcomes, w, k=1.0)
        lr = 0.01
        w_new = w - lr * g
        assert fast_mse(feat, outcomes, w_new, k=1.0) < fast_mse(feat, outcomes, w, k=1.0)


class TestCalibrateKFast:
    def test_returns_float_in_range(self) -> None:
        matrix = _tiny_matrix()
        w = np.array(EvalWeights().to_flat_list(), dtype=np.float64)
        k = calibrate_k_fast(matrix.F.astype(np.float64), matrix.outcomes.astype(np.float64), w)
        assert 0.01 <= k <= 2.0

    def test_lower_bound_is_001(self) -> None:
        # Even with extreme scores the result stays >= 0.01
        feat = np.full((5, 3), 1e6, dtype=np.float64)
        outcomes = np.full(5, 0.5, dtype=np.float64)
        w = np.ones(3, dtype=np.float64)
        k = calibrate_k_fast(feat, outcomes, w)
        assert k >= 0.01


class TestOptimizeAdam:
    def test_reduces_loss(self) -> None:
        np.random.seed(42)
        feat = np.random.randn(30, 5).astype(np.float64)
        outcomes = np.random.uniform(0, 1, 30).astype(np.float64)
        w0 = np.zeros(5, dtype=np.float64)
        k = 1.0
        cfg = AdamConfig(n_iter=500, learning_rate=1.0)
        w_opt = optimize_adam(feat, outcomes, w0, k, cfg)
        assert fast_mse(feat, outcomes, w_opt, k) < fast_mse(feat, outcomes, w0, k)

    def test_output_shape(self) -> None:
        feat = np.zeros((10, 7), dtype=np.float64)
        outcomes = np.full(10, 0.5, dtype=np.float64)
        w0 = np.zeros(7, dtype=np.float64)
        w_out = optimize_adam(feat, outcomes, w0, k=1.0, config=AdamConfig(n_iter=5))
        assert w_out.shape == (7,)


# ---------------------------------------------------------------------------
# fast_tune integration
# ---------------------------------------------------------------------------

class TestFastTune:
    def test_returns_round_result(self) -> None:
        matrix = _tiny_matrix()
        weights = EvalWeights()
        cfg = FastTuneConfig(
            adam_config=AdamConfig(n_iter=50, learning_rate=1.0),
            verbose=False,
        )
        result = fast_tune(matrix, weights, cfg)
        assert isinstance(result, RoundResult)
        assert result.db_size == 2

    def test_result_fields_valid(self) -> None:
        matrix = _tiny_matrix()
        weights = EvalWeights()
        cfg = FastTuneConfig(
            adam_config=AdamConfig(n_iter=50, learning_rate=1.0),
            verbose=False,
        )
        result = fast_tune(matrix, weights, cfg)
        assert 0.01 <= result.calibrated_k <= 2.0
        assert result.baseline_val_mse >= 0.0
        assert result.candidate_val_mse >= 0.0

    def test_no_promotion_to_nonexistent_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            weights_path = Path(tmpdir) / "weights.json"
            matrix = _tiny_matrix()
            weights = EvalWeights()
            cfg = FastTuneConfig(
                adam_config=AdamConfig(n_iter=10, learning_rate=1.0),
                weights_path=weights_path,
                verbose=False,
            )
            result = fast_tune(matrix, weights, cfg)
            # Either promoted (file exists) or not (file absent)
            assert weights_path.exists() == result.promoted
