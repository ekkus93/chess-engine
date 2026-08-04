"""Fast gradient-based Texel tuner using a precomputed feature matrix.

Once the feature matrix (shape N × D) is available from
:mod:`chess_game.texel.features`, every loss evaluation reduces to a
matrix-vector product and every gradient to feat.T @ residual — operations
that numpy executes in microseconds. This allows hundreds of thousands of
Adam iterations in seconds rather than the hours SPSA would require.

Typical use::

    from chess_game.texel.features import compute_feature_matrix, save_features
    from chess_game.texel.fast_tune import fast_tune

    matrix = compute_feature_matrix(db, weights, n_jobs=14)
    save_features(matrix, cache_path)
    result = fast_tune(matrix, weights)
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np

from chess_game.chess.ai_weight_cache import invalidate_weights_cache
from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.features import FeatureMatrix
from chess_game.texel.learn_loop import RoundResult
from chess_game.texel.weights_io import TUNED_WEIGHTS_PATH, save_weights

_LN10 = float(np.log(10.0))


# ---------------------------------------------------------------------------
# Fast loss / gradient helpers
# ---------------------------------------------------------------------------

def _fast_sigmoid(scores: np.ndarray, k: float) -> np.ndarray:
    return 1.0 / (1.0 + 10.0 ** (-k * scores / 400.0))


def fast_mse(feat: np.ndarray, outcomes: np.ndarray, w: np.ndarray, k: float) -> float:
    """MSE of sigmoid(feat @ w) against outcomes, all in numpy."""
    preds = _fast_sigmoid(feat @ w, k)
    return float(np.mean((outcomes - preds) ** 2))


def fast_gradient(feat: np.ndarray, outcomes: np.ndarray, w: np.ndarray, k: float) -> np.ndarray:
    """Exact gradient dMSE/dw = feat.T @ (-2 * errors * dsigmoid) / N."""
    preds = _fast_sigmoid(feat @ w, k)
    errors = outcomes - preds
    dsigmoid = k * _LN10 / 400.0 * preds * (1.0 - preds)
    return np.asarray((feat.T @ (-2.0 * errors * dsigmoid)) / len(outcomes))


def calibrate_k_fast(
    feat: np.ndarray,
    outcomes: np.ndarray,
    w: np.ndarray,
    *,
    k_min: float = 0.01,
    k_max: float = 2.0,
    steps: int = 100,
) -> float:
    """Grid-search over k to minimise MSE using pre-computed feature matrix."""
    best_k, best_mse = k_min, float("inf")
    for i in range(steps + 1):
        k = k_min + (k_max - k_min) * i / steps
        mse = fast_mse(feat, outcomes, w, k)
        if mse < best_mse:
            best_mse = mse
            best_k = k
    return best_k


def _clip_w(w: np.ndarray) -> np.ndarray:
    """Absolute safety clip: material/bonus are frozen upstream; PST bounded at ±200."""
    result = w.copy()
    result[5:5 + 384] = np.clip(result[5:5 + 384], -200.0, 200.0)
    return result


# ---------------------------------------------------------------------------
# Adam optimiser
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class AdamConfig:
    """Hyper-parameters for the Adam optimiser used in fast Texel tuning."""

    n_iter: int = 200_000
    learning_rate: float = 0.05
    beta1: float = 0.9
    beta2: float = 0.999
    epsilon: float = 1e-8
    log_every: int = 0        # 0 = silent
    freeze_material: bool = True   # keep indices 0-4 (piece values) fixed
    freeze_bonus: bool = True      # keep indices 389+ (positional bonuses) fixed
    l2_lambda: float = 1e-6        # L2 reg toward w_init; 1e-6 → equilibrium ~20 cp from defaults


def optimize_adam(
    feat: np.ndarray,
    outcomes: np.ndarray,
    w_init: np.ndarray,
    k: float,
    config: AdamConfig | None = None,
) -> np.ndarray:
    """Run Adam gradient descent on the fast linearised Texel loss.

    Material weights (indices 0-4) are frozen when ``config.freeze_material``
    is True (default).  L2 regularisation toward ``w_init`` is applied with
    strength ``config.l2_lambda`` (default 0.001) to keep the candidate close
    to the starting point where the linear approximation is valid.

    Args:
        feat: Feature matrix (N, D) — rows are positions, columns are weights.
        outcomes: Game outcomes aligned with feat rows (1.0/0.5/0.0).
        w_init: Starting weight vector (D,).
        k: Calibrated sigmoid steepness.
        config: Adam hyper-parameters (defaults in AdamConfig).

    Returns:
        Optimised weight vector (D,).
    """
    cfg = config or AdamConfig()
    w_ref = w_init.astype(np.float64).copy()
    w = w_ref.copy()
    m = np.zeros_like(w)
    v = np.zeros_like(w)
    feat64 = feat.astype(np.float64)
    out64 = outcomes.astype(np.float64)

    for t in range(1, cfg.n_iter + 1):
        g = fast_gradient(feat64, out64, w, k)
        if cfg.l2_lambda:
            g = g + 2.0 * cfg.l2_lambda * (w - w_ref)
        if cfg.freeze_material:
            g[:5] = 0.0
        if cfg.freeze_bonus:
            g[5 + 384:] = 0.0
        m = cfg.beta1 * m + (1.0 - cfg.beta1) * g
        v = cfg.beta2 * v + (1.0 - cfg.beta2) * g ** 2
        m_hat = m / (1.0 - cfg.beta1 ** t)
        v_hat = v / (1.0 - cfg.beta2 ** t)
        w -= cfg.learning_rate * m_hat / (np.sqrt(v_hat) + cfg.epsilon)
        w = _clip_w(w)

        if cfg.log_every and t % cfg.log_every == 0:
            mse = fast_mse(feat64, out64, w, k)
            print(f"  iter {t:6d}: MSE={mse:.6f}", flush=True)

    return w


# ---------------------------------------------------------------------------
# High-level tuning entry point
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class FastTuneConfig:
    """Options for a single fast-tune run."""

    validation_fraction: float = 0.20
    validation_seed: int = 0
    adam_config: AdamConfig | None = None
    weights_path: Path = dataclasses.field(default_factory=lambda: TUNED_WEIGHTS_PATH)
    verbose: bool = True


def _train_val_split(
    matrix: FeatureMatrix, fraction: float, seed: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (feat_train, y_train, feat_val, y_val) as float64 arrays."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(matrix.outcomes))
    cut = max(1, int(len(matrix.outcomes) * fraction))
    val_idx, train_idx = idx[:cut], idx[cut:]
    return (
        matrix.F[train_idx].astype(np.float64),
        matrix.outcomes[train_idx].astype(np.float64),
        matrix.F[val_idx].astype(np.float64),
        matrix.outcomes[val_idx].astype(np.float64),
    )


def fast_tune(
    matrix: FeatureMatrix,
    weights: EvalWeights,
    config: FastTuneConfig | None = None,
) -> RoundResult:
    """Validation-gated fast Texel tune using pre-computed feature matrix.

    Splits the feature matrix into train/val, calibrates k, runs Adam on the
    training set, and promotes the candidate only when held-out val-MSE
    strictly improves.  Returns a :class:`RoundResult` with ``round_index=0``.

    Args:
        matrix: Pre-computed FeatureMatrix from :func:`compute_feature_matrix`.
        weights: Current weights (used only to compute the baseline val-MSE).
        config: Tuning options; defaults to FastTuneConfig().
    """
    cfg = config or FastTuneConfig()
    feat_train, y_train, feat_val, y_val = _train_val_split(
        matrix, cfg.validation_fraction, cfg.validation_seed
    )
    w0 = np.array(weights.to_flat_list(), dtype=np.float64)
    k = calibrate_k_fast(matrix.F.astype(np.float64), matrix.outcomes.astype(np.float64), w0)
    baseline_val_mse = fast_mse(feat_val, y_val, w0, k)

    if cfg.verbose:
        print(f"[fast_tune] k={k:.4f}  baseline_val_mse={baseline_val_mse:.6f}", flush=True)

    w_candidate = optimize_adam(feat_train, y_train, w0, k, cfg.adam_config)
    candidate_val_mse = fast_mse(feat_val, y_val, w_candidate, k)
    promoted = bool(candidate_val_mse < baseline_val_mse)

    if promoted:
        candidate_weights = EvalWeights.from_flat_list(
            [float(x) for x in w_candidate]
        )
        save_weights(candidate_weights, cfg.weights_path)
        invalidate_weights_cache()

    if cfg.verbose:
        status = "PROMOTED" if promoted else "kept existing"
        print(
            f"[fast_tune] candidate_val_mse={candidate_val_mse:.6f} "
            f"(improvement {baseline_val_mse - candidate_val_mse:+.6f}) -> {status}",
            flush=True,
        )

    return RoundResult(
        round_index=0,
        db_size=len(matrix.outcomes),
        calibrated_k=k,
        baseline_val_mse=baseline_val_mse,
        candidate_val_mse=candidate_val_mse,
        promoted=promoted,
    )
