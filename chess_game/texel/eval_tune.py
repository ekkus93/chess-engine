"""Least-squares Texel tuning using quiescence-search eval targets.

Instead of minimising sigmoid-MSE against game outcomes (which gives near-zero
gradients with k≈0.03), this module minimises squared centipawn error between
the *static* eval and *quiescence* eval targets.  The problem is linear in the
PST weights, so it is solved in closed form via :func:`numpy.linalg.lstsq` in
milliseconds.

Material weights (0–4) and positional-bonus weights (389–462) are frozen;
only PST weights (5–388) are optimised.

Typical use::

    from chess_game.texel.features import compute_feature_matrix
    from chess_game.texel.eval_targets import compute_eval_targets
    from chess_game.texel.eval_tune import eval_tune

    matrix = compute_feature_matrix(db, weights, n_jobs=14)
    targets = compute_eval_targets(db, weights, n_jobs=14)
    result = eval_tune(matrix, targets, weights)
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

_N_MATERIAL: int = 5
_N_PST: int = 384
_PST_START: int = _N_MATERIAL
_PST_END: int = _N_MATERIAL + _N_PST


@dataclasses.dataclass
class EvalTuneConfig:
    """Options for a single eval-tune run."""

    validation_fraction: float = 0.20
    validation_seed: int = 0
    ridge_lambda: float = 5000.0   # L2 penalty toward w0_pst; limits PST changes to ~10 cp
    weights_path: Path = dataclasses.field(default_factory=lambda: TUNED_WEIGHTS_PATH)
    verbose: bool = True


def _train_val_split(
    matrix: FeatureMatrix,
    targets: np.ndarray,
    fraction: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (F_train, y_train, F_val, y_val) as float64 arrays."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(targets))
    cut = max(1, int(len(targets) * fraction))
    val_idx, train_idx = idx[:cut], idx[cut:]
    return (
        matrix.F[train_idx].astype(np.float64),
        targets[train_idx].astype(np.float64),
        matrix.F[val_idx].astype(np.float64),
        targets[val_idx].astype(np.float64),
    )


def _mse(pred: np.ndarray, target: np.ndarray) -> float:
    return float(np.mean((pred - target) ** 2))


def _maybe_promote(
    w_cand: np.ndarray,
    baseline_val_mse: float,
    candidate_val_mse: float,
    cfg: EvalTuneConfig,
) -> bool:
    """Promote candidate weights if they improve val MSE; return promoted flag."""
    promoted = bool(candidate_val_mse < baseline_val_mse)
    if promoted:
        save_weights(
            EvalWeights.from_flat_list([float(x) for x in w_cand]),
            cfg.weights_path,
        )
        invalidate_weights_cache()
    if cfg.verbose:
        base_rmse = float(np.sqrt(baseline_val_mse))
        cand_rmse = float(np.sqrt(candidate_val_mse))
        status = "PROMOTED" if promoted else "kept existing"
        print(
            f"[eval_tune] baseline_val_rmse={base_rmse:.2f} cp "
            f"-> candidate_val_rmse={cand_rmse:.2f} cp "
            f"(improvement {base_rmse - cand_rmse:+.2f} cp) -> {status}",
            flush=True,
        )
    return promoted


def _solve_pst(
    f_pst: np.ndarray,
    y_adj: np.ndarray,
    w0_pst: np.ndarray,
    ridge_lambda: float,
) -> np.ndarray:
    """Ridge-regression solution for PST weights, clipped to [-200, 200].

    Solves min_w ||F_pst @ w - y_adj||² + ridge_lambda * ||w - w0_pst||²,
    which constrains the solution to stay close to the reference weights.
    The augmented system is: [F_pst; sqrt(λ)·I] @ w = [y_adj; sqrt(λ)·w0_pst].
    """
    n_pst = f_pst.shape[1]
    sqrt_lam = float(np.sqrt(ridge_lambda))
    f_aug = np.vstack([f_pst, sqrt_lam * np.eye(n_pst)])
    y_aug = np.concatenate([y_adj, sqrt_lam * w0_pst])
    w_pst, _, _, _ = np.linalg.lstsq(f_aug, y_aug, rcond=None)
    return np.asarray(np.clip(w_pst, -200.0, 200.0))


def _frozen_contrib(feat: np.ndarray, w0: np.ndarray) -> np.ndarray:
    """Contribution of frozen (material + bonus) weights to the static eval."""
    frozen_mask = np.ones(len(w0), dtype=bool)
    frozen_mask[_PST_START:_PST_END] = False
    return np.asarray(feat[:, frozen_mask] @ w0[frozen_mask])


def eval_tune(
    matrix: FeatureMatrix,
    targets: np.ndarray,
    weights: EvalWeights,
    config: EvalTuneConfig | None = None,
) -> RoundResult:
    """Least-squares PST tuning against quiescence-eval targets.

    Freezes material (indices 0–4) and bonus (indices 389+) weights.
    Solves ``min_w ||F_pst @ w_pst - y_adj||²`` in closed form, clips the
    result to PST bounds ([-200, 200]), and promotes only when held-out
    val-MSE strictly improves.

    The MSE values in the returned :class:`RoundResult` are in centipawns²
    (not sigmoid scale).  ``calibrated_k=0.0`` is a sentinel indicating
    eval-tuning mode.

    Args:
        matrix: Pre-computed :class:`~chess_game.texel.features.FeatureMatrix`.
        targets: Quiescence eval targets from
            :func:`~chess_game.texel.eval_targets.compute_eval_targets`
            (shape (N,), centipawns, white-centric).
        weights: Current weight vector (baseline reference).
        config: Tuning options; defaults to :class:`EvalTuneConfig`.
    """
    cfg = config or EvalTuneConfig()
    f_train, y_train, f_val, y_val = _train_val_split(
        matrix, targets, cfg.validation_fraction, cfg.validation_seed
    )
    w0 = np.array(weights.to_flat_list(), dtype=np.float64)

    # Baseline: how well does the current static eval approximate quiescence?
    baseline_val_mse = _mse(f_val @ w0, y_val)

    # Subtract frozen (material + bonus) contributions to isolate the PST term.
    fc_train = _frozen_contrib(f_train, w0)
    fc_val = _frozen_contrib(f_val, w0)

    # Ridge regression: w_pst* = argmin ||F_pst @ w - y_adj||² + λ||w - w0_pst||²
    w_pst_opt = _solve_pst(
        f_train[:, _PST_START:_PST_END],
        y_train - fc_train,
        w0[_PST_START:_PST_END],
        cfg.ridge_lambda,
    )

    w_cand = w0.copy()
    w_cand[_PST_START:_PST_END] = w_pst_opt

    # Evaluate candidate on validation set
    candidate_val_mse = _mse(
        f_val[:, _PST_START:_PST_END] @ w_pst_opt + fc_val,
        y_val,
    )

    promoted = _maybe_promote(w_cand, baseline_val_mse, candidate_val_mse, cfg)

    return RoundResult(
        round_index=0,
        db_size=len(targets),
        calibrated_k=0.0,
        baseline_val_mse=baseline_val_mse,
        candidate_val_mse=candidate_val_mse,
        promoted=promoted,
    )
