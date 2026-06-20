"""SPSA optimizer for Texel tuning."""
from __future__ import annotations

import dataclasses
import json
import math
import random
from pathlib import Path
from typing import Callable, Optional

from chess_game.chess.eval_weights import EVAL_WEIGHTS_FLAT_LENGTH, EvalWeights
from chess_game.texel.loss import DEFAULT_K, LossOptions, mean_squared_error
from chess_game.texel.position_db import PositionDB

# EVAL_WEIGHTS_FLAT_LENGTH is re-exported as part of the public API so that
# callers can discover the flat-list dimension without importing eval_weights.
__all__ = [
    "SPSAOptions",
    "optimize",
    "_clip_weights",
    "EVAL_WEIGHTS_FLAT_LENGTH",
]

LossFn = Callable[[list[tuple[str, float]], EvalWeights], float]


def _require_finite_positive(name: str, value: float) -> None:
    """Raise unless *value* is a finite number strictly greater than zero."""
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"SPSAOptions.{name} must be a finite number > 0, got {value!r}")


@dataclasses.dataclass
class SPSAOptions:
    """Configuration for the SPSA optimiser.

    Invalid values that would silently no-op or crash later (zero iterations, zero
    perturbation size, zero checkpoint interval, empty batch) are rejected at
    construction. ``seed`` makes a run reproducible by seeding the perturbation RNG.
    """

    max_iterations: int = 5000
    initial_step_size: float = 5.0
    step_decay: float = 0.602
    perturbation_size: float = 1.0
    perturbation_decay: float = 0.101
    stability_constant: int = 100
    batch_size: Optional[int] = None
    checkpoint_every: int = 500
    checkpoint_path: Optional[Path] = None
    verbose: bool = True
    loss_options: Optional[LossOptions] = None
    seed: Optional[int] = None

    def __post_init__(self) -> None:
        """Reject unsafe option values at construction time."""
        if self.max_iterations < 1:
            raise ValueError(
                f"SPSAOptions.max_iterations must be >= 1, got {self.max_iterations}"
            )
        _require_finite_positive("initial_step_size", self.initial_step_size)
        _require_finite_positive("step_decay", self.step_decay)
        _require_finite_positive("perturbation_size", self.perturbation_size)
        _require_finite_positive("perturbation_decay", self.perturbation_decay)
        if not math.isfinite(self.stability_constant) or self.stability_constant < 0:
            raise ValueError(
                f"SPSAOptions.stability_constant must be finite >= 0, "
                f"got {self.stability_constant!r}"
            )
        if self.batch_size is not None and self.batch_size < 1:
            raise ValueError(
                f"SPSAOptions.batch_size must be None or >= 1, got {self.batch_size}"
            )
        if self.checkpoint_every < 1:
            raise ValueError(
                f"SPSAOptions.checkpoint_every must be >= 1, got {self.checkpoint_every}"
            )


def make_spsa_options(
    *,
    max_iterations: int,
    batch_size: int,
    loss_options: LossOptions,
    seed: Optional[int] = None,
) -> SPSAOptions:
    """Build SPSAOptions for an unattended tune: quiet, no checkpoint file.

    Shared by the online and batch learning loops so the "headless tune" option
    set lives in exactly one place.
    """
    return SPSAOptions(
        max_iterations=max_iterations,
        batch_size=batch_size,
        verbose=False,
        checkpoint_path=None,
        loss_options=loss_options,
        seed=seed,
    )


def _clip_weights(w: list[float]) -> list[float]:
    """Clip weights to sane bounds to prevent divergence."""
    result = list(w)
    # Material values (first 5) must be positive
    for i in range(5):
        result[i] = max(1.0, result[i])
    # Piece-square table values (next 384) capped at [-200, 200]
    for i in range(5, 5 + 384):
        result[i] = max(-200.0, min(200.0, result[i]))
    # All remaining scalar weights: cap at [-200, 200]
    for i in range(5 + 384, len(result)):
        result[i] = max(-200.0, min(200.0, result[i]))
    return result


def _make_loss_fn(opts: SPSAOptions) -> LossFn:
    """Build the loss callable used during optimization."""
    loss_opts = opts.loss_options or LossOptions(k=DEFAULT_K)
    def _loss(pairs: list[tuple[str, float]], weights: EvalWeights) -> float:
        return mean_squared_error(pairs, weights, opts=loss_opts)
    return _loss


def _spsa_step(
    w: list[float],
    pairs: list[tuple[str, float]],
    a_k: float,
    c_k: float,
    loss_fn: LossFn,
    *,
    rng: random.Random,
) -> list[float]:
    """Execute one SPSA gradient step; return the updated weight vector."""
    n = len(w)
    delta = [1.0 if rng.random() < 0.5 else -1.0 for _ in range(n)]
    w_plus = _clip_weights([w[i] + c_k * delta[i] for i in range(n)])
    w_minus = _clip_weights([w[i] - c_k * delta[i] for i in range(n)])
    loss_plus = loss_fn(pairs, EvalWeights.from_flat_list(w_plus))
    loss_minus = loss_fn(pairs, EvalWeights.from_flat_list(w_minus))
    grad_scale = (loss_plus - loss_minus) / (2.0 * c_k)
    return _clip_weights([w[i] - a_k * grad_scale / delta[i] for i in range(n)])


def _maybe_checkpoint(
    w: list[float],
    k: int,
    options: SPSAOptions,
) -> None:
    """Write a checkpoint file if the iteration count is due."""
    if options.checkpoint_path is None:
        return
    if k % options.checkpoint_every != 0:
        return
    checkpoint = EvalWeights.from_flat_list(w)
    options.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with options.checkpoint_path.open("w", encoding="utf-8") as fh:
        json.dump(checkpoint.to_dict(), fh, indent=2)


def optimize(
    weights: EvalWeights,
    db: PositionDB,
    options: SPSAOptions,
) -> EvalWeights:
    """Run SPSA optimization and return the tuned weights.

    Raises ``ValueError`` if the DB has no training positions, rather than silently
    returning the unchanged input weights.
    """
    if len(db) == 0:
        raise ValueError("SPSA optimize requires at least one training position")
    w = weights.to_flat_list()
    a = options.initial_step_size
    alpha = options.step_decay
    c = options.perturbation_size
    gamma = options.perturbation_decay
    cap_a = options.stability_constant
    loss_fn = _make_loss_fn(options)
    # Local RNG for perturbation deltas: seeded runs are reproducible, unseeded
    # (seed=None) still draws from system entropy as before.
    rng = random.Random(options.seed)

    for k in range(1, options.max_iterations + 1):
        a_k = a / (k + cap_a) ** alpha
        c_k = c / k ** gamma
        pairs = (
            db.sample(options.batch_size)
            if options.batch_size is not None
            else db.all_pairs()
        )
        if not pairs:
            break
        w = _spsa_step(w, pairs, a_k, c_k, loss_fn, rng=rng)
        if options.verbose and k % 100 == 0:
            mse = loss_fn(pairs, EvalWeights.from_flat_list(w))
            print(f"  iter {k:5d}: MSE={mse:.6f} a_k={a_k:.4f}")
        _maybe_checkpoint(w, k, options)

    return EvalWeights.from_flat_list(w)
