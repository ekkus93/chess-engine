"""Precompute the (position × weight) feature matrix for fast Texel tuning.

eval(board, w) is linear in w for fixed board state:
    eval(board, w) = F(board) · w

where F(board) is a row of feature counts (piece counts, PST occupancies, bonus
conditions) that depend only on the board, not on the weight values. This module
computes F via one-sided finite differences, parallelised across positions.

After a one-time extraction (~2 min on 14 cores), every loss evaluation and
gradient step reduces to a matrix-vector product — microseconds instead of seconds.
"""
from __future__ import annotations

import multiprocessing as mp
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, Optional

import numpy as np

from chess_game.chess import Board
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.evaluation import evaluate
from chess_game.texel.loss import sigmoid
from chess_game.texel.position_db import PositionDB

if TYPE_CHECKING:
    from chess_game.texel.annotated_position_db import AnnotatedPositionDB


class FeatureMatrix(NamedTuple):
    """Precomputed (N, D) feature matrix and aligned outcome vector."""

    F: np.ndarray       # (N, D) float32 — deval/dw_i per position
    outcomes: np.ndarray  # (N,)  float32 — game outcomes (1.0/0.5/0.0)


def save_features(matrix: FeatureMatrix, path: Path) -> None:
    """Save feature matrix and outcomes to a compressed .npz archive."""
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, F=matrix.F, outcomes=matrix.outcomes)


def load_features(path: Path) -> FeatureMatrix:
    """Load a previously saved feature matrix."""
    data = np.load(path)
    return FeatureMatrix(F=data["F"], outcomes=data["outcomes"])


# ---------------------------------------------------------------------------
# Internal worker (top-level so multiprocessing can pickle it)
# ---------------------------------------------------------------------------

def _extract_chunk(args: tuple) -> np.ndarray:
    """Compute rows of the feature matrix for a slice of positions.

    Returns F_chunk of shape (len(pairs), D) in float32.
    """
    pairs, weights_flat, eps = args
    d = len(weights_flat)
    chunk = np.zeros((len(pairs), d), dtype=np.float32)
    for row_idx, (fen, _) in enumerate(pairs):
        board = Board.from_fen(fen)
        base = float(evaluate(board, EvalWeights.from_flat_list(weights_flat)))
        for col_idx in range(d):
            w_plus = list(weights_flat)
            w_plus[col_idx] += eps
            score_plus = float(evaluate(board, EvalWeights.from_flat_list(w_plus)))
            chunk[row_idx, col_idx] = (score_plus - base) / eps
    return chunk


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_feature_matrix(
    db: PositionDB,
    weights: EvalWeights,
    *,
    eps: float = 1.0,
    n_jobs: int = 14,
) -> FeatureMatrix:
    """Compute F[n, i] = deval_n/dw_i via one-sided finite differences.

    The evaluation is linear in the weights at any fixed board state, so F is
    exact for PST / bonus weights and a close approximation for material weights
    (which affect the game-phase scalar non-linearly).

    Args:
        db: Position database with (FEN, outcome) records.
        weights: Current weights — F is valid for small deviations from these.
        eps: Perturbation size in centipawns (default 1.0).
        n_jobs: Parallel workers (default 14, one per physical core).

    Returns:
        FeatureMatrix with F of shape (N, D) and outcomes of shape (N,).
    """
    pairs = db.all_pairs()
    n = len(pairs)
    weights_flat = weights.to_flat_list()

    chunk_size = max(1, (n + n_jobs - 1) // n_jobs)
    chunks = [pairs[i : i + chunk_size] for i in range(0, n, chunk_size)]
    worker_args = [(chunk, weights_flat, eps) for chunk in chunks]

    with mp.Pool(n_jobs) as pool:
        results = pool.map(_extract_chunk, worker_args)

    f_matrix = np.vstack(results).astype(np.float32)
    outcomes_arr = np.array([o for _, o in pairs], dtype=np.float32)
    return FeatureMatrix(F=f_matrix, outcomes=outcomes_arr)


# ---------------------------------------------------------------------------
# Stockfish-targeted feature matrix
# ---------------------------------------------------------------------------


def outcomes_from_sf(
    annotated_pairs: list[tuple[str, int]],
    k: float,
) -> np.ndarray:
    """Convert Stockfish centipawn scores to sigmoid win-probability targets.

    Args:
        annotated_pairs: ``(fen, sf_score_cp)`` pairs — must not contain None scores.
        k: Sigmoid steepness (calibrated by ``calibrate_k_fast``).

    Returns:
        float32 array of shape (N,) with values in (0, 1).
    """
    return np.array(
        [sigmoid(float(cp), k) for _, cp in annotated_pairs], dtype=np.float32
    )


def compute_sf_feature_matrix(
    annotated_db: "AnnotatedPositionDB",
    weights: EvalWeights,
    k: float,
    *,
    eps: float = 1.0,
    n_jobs: int = 14,
) -> Optional[FeatureMatrix]:
    """Compute a FeatureMatrix using Stockfish scores as outcome targets.

    Filters to positions where ``sf_score_cp`` is not ``None`` (excludes mate
    positions).  Computes ``F`` via the same finite-difference method as
    ``compute_feature_matrix``, then sets ``outcomes`` to
    ``sigmoid(sf_score_cp, k)`` rather than game outcomes.

    Args:
        annotated_db: Annotated position database with ``sf_scores`` populated.
        weights: Current weights (F matrix is valid near these values).
        k: Sigmoid steepness for converting cp scores to win probabilities.
        eps: Perturbation size in centipawns (default 1.0).
        n_jobs: Parallel workers (default 14).

    Returns:
        FeatureMatrix, or None if no annotated positions are available.
    """
    annotated_pairs: list[tuple[str, int]] = [
        (fen, score)
        for fen, score in annotated_db.annotated_pairs()
        if score is not None
    ]
    if not annotated_pairs:
        return None

    # Reuse existing extraction logic by wrapping as (fen, dummy_outcome) pairs.
    dummy_pairs = [(fen, 0.0) for fen, _ in annotated_pairs]
    weights_flat = weights.to_flat_list()
    n = len(dummy_pairs)
    chunk_size = max(1, (n + n_jobs - 1) // n_jobs)
    chunks = [dummy_pairs[i: i + chunk_size] for i in range(0, n, chunk_size)]
    worker_args = [(chunk, weights_flat, eps) for chunk in chunks]

    with mp.Pool(n_jobs) as pool:
        results = pool.map(_extract_chunk, worker_args)

    f_matrix = np.vstack(results).astype(np.float32)
    sf_outcomes = outcomes_from_sf(annotated_pairs, k)
    return FeatureMatrix(F=f_matrix, outcomes=sf_outcomes)
