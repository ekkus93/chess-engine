"""Stockfish-targeted Texel tuning pipeline.

Replaces noisy game-outcome labels with Stockfish centipawn evaluations as
training targets.  The loss function and Adam optimiser in ``fast_tune.py``
are unchanged; only the ``outcomes`` vector in the ``FeatureMatrix`` changes.

Typical use::

    uv run python -m chess_game.texel.eval_tune_sf \\
        --db annotated_positions.jsonl \\
        --features sf_features.npz \\
        --output tuned_weights.json
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.annotated_position_db import AnnotatedPositionDB
from chess_game.texel.fast_tune import AdamConfig, FastTuneConfig, calibrate_k_fast, fast_tune
from chess_game.texel.features import (
    FeatureMatrix,
    compute_sf_feature_matrix,
    load_features,
    save_features,
)
from chess_game.texel.weights_io import TUNED_WEIGHTS_PATH, load_optional_weights


def _load_or_compute_matrix(
    db: AnnotatedPositionDB,
    weights: EvalWeights,
    features_path: Path | None,
    *,
    n_jobs: int,
    verbose: bool,
) -> FeatureMatrix | None:
    """Load a cached SF feature matrix or compute and optionally cache it."""
    if features_path is not None and features_path.exists():
        if verbose:
            print(f"Loading cached SF feature matrix from {features_path} …")
        return load_features(features_path)

    annotated = sum(1 for _, s in db.annotated_pairs() if s is not None)
    if verbose:
        print(f"Computing SF feature matrix ({annotated} positions, {n_jobs} workers) …")

    # SF outcomes are converted with a fixed k=1.13.  The k returned by
    # calibrate_k_fast is for our engine's sigmoid vs these targets, not for
    # re-converting SF scores — so we must NOT recompute outcomes with it.
    result = compute_sf_feature_matrix(db, weights, k=1.13, n_jobs=n_jobs)
    if result is None:
        return None

    matrix = result

    if features_path is not None:
        save_features(matrix, features_path)
        if verbose:
            print(f"  Cached to {features_path}")

    return matrix


def run_sf_tuning(
    db_path: Path,
    weights_path: Path | None = None,
    features_path: Path | None = None,
    config: FastTuneConfig | None = None,
    *,
    n_jobs: int = 14,
) -> None:
    """End-to-end Stockfish-targeted tuning run.

    Args:
        db_path: Path to an annotated JSONL file (produced by
            ``chess_game.texel.stockfish_annotate``).
        weights_path: Optional path to initial weights JSON; defaults to
            the project's committed tuned weights.
        features_path: Optional path to cache the SF feature matrix (.npz).
            If the file already exists it is loaded instead of recomputed.
        config: Tuning options (output path, verbose, l2_lambda via adam_config).
            Defaults to ``FastTuneConfig()``.
        n_jobs: Parallel workers for feature-matrix computation.
    """
    cfg = config or FastTuneConfig()
    verbose = cfg.verbose

    if verbose:
        print(f"Loading annotated DB from {db_path} …")
    db: AnnotatedPositionDB = AnnotatedPositionDB.load(db_path)
    total = len(db)
    annotated = sum(1 for _, s in db.annotated_pairs() if s is not None)
    if verbose:
        print(f"  {total} positions total, {annotated} annotated (non-mate)")

    if annotated == 0:
        print("No annotated positions found. Run stockfish_annotate first.")
        return

    weights = load_optional_weights(weights_path)
    w0 = np.array(weights.to_flat_list(), dtype=np.float64)

    matrix = _load_or_compute_matrix(db, weights, features_path, n_jobs=n_jobs, verbose=verbose)
    if matrix is None:
        print("No annotated positions available after filtering mate scores.")
        return

    if verbose:
        print(f"Feature matrix: {matrix.F.shape}, outcomes mean={matrix.outcomes.mean():.4f}")

    # Calibrate k for our engine's sigmoid against the fixed SF-based outcomes.
    k = calibrate_k_fast(matrix.F.astype(np.float64), matrix.outcomes.astype(np.float64), w0)
    if verbose:
        print(f"Calibrated k (engine sigmoid vs SF outcomes) = {k:.4f}")

    result_r = fast_tune(matrix, weights, cfg)

    if verbose:
        status = "PROMOTED" if result_r.promoted else "not promoted (kept existing)"
        print(
            f"Result: baseline_val_mse={result_r.baseline_val_mse:.6f}"
            f"  candidate_val_mse={result_r.candidate_val_mse:.6f}"
            f"  → {status}"
        )


if __name__ == "__main__":
    _parser = argparse.ArgumentParser(description="Stockfish-targeted Texel tuning.")
    _parser.add_argument(
        "--db", required=True, type=Path, help="Annotated PositionDB JSONL path."
    )
    _parser.add_argument(
        "--weights", default=None, type=Path,
        help="Initial weights JSON (default: committed tuned weights).",
    )
    _parser.add_argument(
        "--features", default=None, type=Path,
        help="Cache path for SF feature matrix (.npz).",
    )
    _parser.add_argument(
        "--output", default=TUNED_WEIGHTS_PATH, type=Path,
        help="Output path for promoted weights.",
    )
    _parser.add_argument(
        "--jobs", type=int, default=14, help="Parallel workers for feature computation."
    )
    _parser.add_argument(
        "--l2-lambda", type=float, default=1e-6,
        help="L2 regularisation strength (default 1e-6).",
    )
    _parser.add_argument("--verbose", action="store_true")
    _args = _parser.parse_args()

    _adam_cfg = AdamConfig(l2_lambda=_args.l2_lambda)
    _config = FastTuneConfig(
        weights_path=_args.output,
        verbose=_args.verbose,
        adam_config=_adam_cfg,
    )
    run_sf_tuning(
        db_path=_args.db,
        weights_path=_args.weights,
        features_path=_args.features,
        config=_config,
        n_jobs=_args.jobs,
    )
