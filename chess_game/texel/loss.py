"""Loss function for Texel tuning."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from chess_game.chess import Board
from chess_game.chess.ai import INF as _INF, SearchContext, quiescence
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.evaluation import evaluate
from chess_game.chess.types import Color

if TYPE_CHECKING:
    from chess_game.texel.position_db import PositionDB

DEFAULT_K: float = 1.13


@dataclass(frozen=True)
class LossOptions:
    """Options controlling Texel loss computation."""

    k: float = DEFAULT_K
    use_quiescence: bool = False
    quiescence_depth_limit: int = 4
    deterministic: bool = True


def sigmoid(score: float, k: float = DEFAULT_K) -> float:
    """Win-probability sigmoid. score is in centipawns, White-relative."""
    return float(1.0 / (1.0 + 10.0 ** (-k * score / 400.0)))


def _score_position(
    board: Board,
    weights: EvalWeights,
    opts: LossOptions,
) -> float:
    """Return a White-relative score for a position, static or via quiescence."""
    if not opts.use_quiescence:
        return float(evaluate(board, weights))
    ctx = SearchContext(weights=weights, deterministic=opts.deterministic)
    is_max = board.turn == Color.WHITE
    return float(quiescence(
        board, -_INF, _INF, is_max,
        context=ctx, depth_remaining=opts.quiescence_depth_limit,
    ))


def mean_squared_error(
    pairs: list[tuple[str, float]],
    weights: EvalWeights,
    k: float = DEFAULT_K,
    opts: Optional[LossOptions] = None,
) -> float:
    """MSE between sigmoid(eval) and game outcome over (fen, outcome) pairs.

    Outcome labels are White-relative: 1.0 = White wins, 0.5 = draw, 0.0 = Black wins.
    evaluate() returns a White-relative score, so no perspective conversion is needed.
    """
    if not pairs:
        return 0.0
    effective_k = opts.k if opts is not None else k
    total = 0.0
    for fen, outcome in pairs:
        board = Board.from_fen(fen)
        if opts is not None:
            score = _score_position(board, weights, opts)
        else:
            score = float(evaluate(board, weights))
        predicted = sigmoid(score, effective_k)
        total += (outcome - predicted) ** 2
    return total / len(pairs)


def calibrate_k(
    pairs: list[tuple[str, float]],
    weights: EvalWeights,
    k_min: float = 0.5,
    k_max: float = 2.0,
    steps: int = 30,
) -> float:
    """Find the k value that minimises MSE via grid search.

    Raises ``ValueError`` on empty input rather than silently returning ``k_min``.
    """
    if not pairs:
        raise ValueError("Cannot calibrate Texel k with no positions")
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
    from chess_game.texel.weights_io import load_optional_weights

    _parser = argparse.ArgumentParser(description="Calibrate Texel tuning K constant")
    _parser.add_argument("--db", required=True, help="Path to position DB")
    _parser.add_argument("--weights", default=None, help="Path to weights JSON")
    _parser.add_argument("--output", required=True, help="Output path for K value")
    _args = _parser.parse_args()
    _db = PositionDB.load(Path(_args.db))
    # --weights is optional (None -> defaults), but if supplied it must exist (fail loud).
    _weights = load_optional_weights(Path(_args.weights) if _args.weights else None)
    _k = calibrate_and_save_k(_db, _weights, Path(_args.output))
    print(f"Calibrated k = {_k:.4f}")
