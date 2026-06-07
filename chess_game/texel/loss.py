"""Loss function for Texel tuning."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from chess_game.chess import Board
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.evaluation import evaluate

if TYPE_CHECKING:
    from chess_game.texel.position_db import PositionDB


def sigmoid(score: float, k: float = 1.13) -> float:
    """Win-probability sigmoid. score is in centipawns from white's perspective."""
    return float(1.0 / (1.0 + 10.0 ** (-k * score / 400.0)))


def mean_squared_error(
    pairs: list[tuple[str, float]],
    weights: EvalWeights,
    k: float = 1.13,
) -> float:
    """MSE between sigmoid(eval) and game outcome over a list of (fen, outcome) pairs."""
    if not pairs:
        return 0.0
    total = 0.0
    for fen, outcome in pairs:
        board = Board.from_fen(fen)
        score = evaluate(board, weights)
        predicted = sigmoid(float(score), k)
        total += (outcome - predicted) ** 2
    return total / len(pairs)


def calibrate_k(
    pairs: list[tuple[str, float]],
    weights: EvalWeights,
    k_min: float = 0.5,
    k_max: float = 2.0,
    steps: int = 30,
) -> float:
    """Find the k value that minimises MSE via grid search."""
    best_k = k_min
    best_mse = float("inf")
    for i in range(steps + 1):
        k = k_min + (k_max - k_min) * i / steps
        mse = mean_squared_error(pairs, weights, k)
        if mse < best_mse:
            best_mse = mse
            best_k = k
    return best_k


def calibrate_and_save_k(
    db: PositionDB,
    weights: EvalWeights,
    path: Path,
) -> float:
    """Calibrate k on the given DB and save the result to *path*.

    Returns the calibrated k value.
    """
    pairs = db.all_pairs()
    best_k = calibrate_k(pairs, weights)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump({"k": best_k}, fh)
    return best_k


if __name__ == "__main__":
    import argparse

    from chess_game.texel.position_db import PositionDB
    from chess_game.texel.weights_io import load_weights_or_default

    _parser = argparse.ArgumentParser(description="Calibrate Texel tuning K constant")
    _parser.add_argument("--db", required=True, help="Path to position DB")
    _parser.add_argument("--weights", default=None, help="Path to weights JSON")
    _parser.add_argument("--output", required=True, help="Output path for K value")
    _args = _parser.parse_args()
    _db = PositionDB.load(Path(_args.db))
    _weights = load_weights_or_default(Path(_args.weights) if _args.weights else None)
    _k = calibrate_and_save_k(_db, _weights, Path(_args.output))
    print(f"Calibrated k = {_k:.4f}")
