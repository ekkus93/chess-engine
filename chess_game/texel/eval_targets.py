"""Quiescence-search eval targets for Texel tuning.

Instead of using game outcomes (0/0.5/1) as training targets, this module
computes quiescence-search scores for each position.  These targets are on
the centipawn scale with a much higher dynamic range than outcome labels,
giving gradients that are orders of magnitude stronger.
"""
from __future__ import annotations

import multiprocessing as mp
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from chess_game.chess import Board
from chess_game.chess.ai import INF, SearchContext, quiescence
from chess_game.chess.color import Color
from chess_game.chess.eval_weights import EvalWeights

if TYPE_CHECKING:
    from chess_game.texel.position_db import PositionDB

_MAX_TARGET_CP: int = 2000


def _eval_chunk(args: tuple) -> list[float]:
    """Evaluate one chunk of FEN strings; returns centipawn scores (white-centric)."""
    fens: list[str]
    weights_flat: list[float]
    fens, weights_flat = args
    weights = EvalWeights.from_flat_list(weights_flat)
    context = SearchContext(weights=weights)
    scores: list[float] = []
    for fen in fens:
        board = Board.from_fen(fen)
        is_max = board.turn == Color.WHITE
        score = quiescence(board, -INF, INF, is_maximizing=is_max, context=context)
        scores.append(float(score))
    return scores


def compute_eval_targets(
    db: PositionDB,
    weights: EvalWeights,
    *,
    n_jobs: int = 14,
    clip_cp: int = _MAX_TARGET_CP,
) -> np.ndarray:
    """Compute quiescence eval for every position in *db* under *weights*.

    Args:
        db: Position database (FEN + outcome pairs; outcomes are ignored).
        weights: Evaluation weights used for the quiescence search.
        n_jobs: Number of worker processes.
        clip_cp: Clip targets to ±clip_cp centipawns to exclude forced-mate
            positions where the static eval cannot be expected to match.

    Returns:
        float32 array of shape (N,) in centipawns, white-centric (positive →
        white is winning).
    """
    fens = [fen for fen, _ in db.all_pairs()]
    weights_flat = weights.to_flat_list()
    n = len(fens)

    chunk_size = max(1, (n + n_jobs - 1) // n_jobs)
    chunks = [fens[i:i + chunk_size] for i in range(0, n, chunk_size)]

    with mp.Pool(n_jobs) as pool:
        results = pool.map(_eval_chunk, [(chunk, weights_flat) for chunk in chunks])

    scores = [s for chunk in results for s in chunk]
    arr = np.array(scores, dtype=np.float32)
    return np.clip(arr, -clip_cp, clip_cp)


def save_eval_targets(targets: np.ndarray, path: Path) -> None:
    """Save eval targets array to *.npy* file."""
    np.save(path, targets)


def load_eval_targets(path: Path) -> np.ndarray:
    """Load eval targets array from *.npy* file."""
    return np.asarray(np.load(path))
