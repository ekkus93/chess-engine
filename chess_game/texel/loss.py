"""Loss function for Texel tuning."""
from __future__ import annotations

from chess_game.chess import Board
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.evaluation import evaluate


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
