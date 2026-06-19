"""Persistent self-play learning loop: collect -> tune -> promote-on-improvement.

Each round (1) plays self-play games into a growing on-disk position DB, then
(2) runs an SPSA tune starting from the engine's *current* canonical weights and
overwrites those weights only when the candidate lowers held-out validation MSE.

Because every round starts from the current canonical weights and the DB persists
on disk, real improvements compound across rounds and across sessions, while a
noisy round can never make the engine worse: a candidate that fails the validation
gate is discarded and the canonical weights are left untouched.

This is the durable counterpart to :mod:`chess_game.texel.online_learning`, which
tunes after every single game. Here data is accumulated and tuned in batches.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

from chess_game.chess.ai_weight_cache import invalidate_weights_cache
from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.collect import CollectionOptions, collect_games
from chess_game.texel.loss import LossOptions, calibrate_k, mean_squared_error
from chess_game.texel.position_db import PositionDB
from chess_game.texel.spsa import make_spsa_options, optimize
from chess_game.texel.weights_io import (
    TUNED_WEIGHTS_PATH,
    load_weights_or_default,
    save_weights,
)

_DEFAULT_DB_PATH = Path("chess_game/chess/data/positions.jsonl")


@dataclasses.dataclass
class LearnLoopConfig:
    """Configuration for a persistent learning loop.

    Defaults point at the engine's canonical DB and weights cache, so a run with
    defaults genuinely improves the engine that ``get_best_move`` plays with.
    """

    rounds: int = 5
    games_per_round: int = 50
    depth: int = 1
    db_path: Path = dataclasses.field(default_factory=lambda: _DEFAULT_DB_PATH)
    weights_path: Path = dataclasses.field(default_factory=lambda: TUNED_WEIGHTS_PATH)
    spsa_iterations: int = 1000
    spsa_batch_size: int = 256
    validation_fraction: float = 0.20
    validation_seed: int = 0
    min_validation_improvement: float = 0.0
    collect_seed: int | None = None
    max_moves: int = 200
    verbose: bool = True

    def __post_init__(self) -> None:
        """Reject configurations that would loop without ever learning."""
        if self.rounds < 1:
            raise ValueError(f"rounds must be >= 1, got {self.rounds}")
        if self.games_per_round < 1:
            raise ValueError(f"games_per_round must be >= 1, got {self.games_per_round}")
        if not 0.0 < self.validation_fraction < 1.0:
            raise ValueError(
                "validation_fraction must satisfy 0.0 < validation_fraction < 1.0, "
                f"got {self.validation_fraction}"
            )
        if self.min_validation_improvement < 0.0:
            raise ValueError(
                "min_validation_improvement must be >= 0.0, got "
                f"{self.min_validation_improvement}"
            )


@dataclasses.dataclass(frozen=True)
class RoundResult:
    """Outcome of a single learning round."""

    round_index: int
    db_size: int
    calibrated_k: float
    baseline_val_mse: float
    candidate_val_mse: float
    promoted: bool

    @property
    def improvement(self) -> float:
        """Absolute validation-MSE reduction (positive means the candidate is better)."""
        return self.baseline_val_mse - self.candidate_val_mse


def _round_seed(base: int | None, round_index: int) -> int | None:
    """Derive a distinct per-round collection seed so rounds explore new games."""
    if base is None:
        return None
    return base + round_index


def _collect_round(config: LearnLoopConfig, round_index: int) -> PositionDB:
    """Play this round's games into the growing on-disk DB and return it loaded."""
    opts = CollectionOptions(
        db_path=config.db_path,
        num_games=config.games_per_round,
        depth=config.depth,
        max_moves=config.max_moves,
        seed=_round_seed(config.collect_seed, round_index),
        verbose=False,
    )
    return collect_games(opts)


def _tune_round(
    config: LearnLoopConfig,
    db: PositionDB,
    round_index: int,
) -> RoundResult:
    """Run one validation-gated tune over *db*, promoting on improvement only."""
    weights = load_weights_or_default(config.weights_path)
    pairs = db.all_pairs()
    k = calibrate_k(pairs, weights)
    loss_opts = LossOptions(k=k)

    train_pairs, val_pairs = db.split(
        validation_fraction=config.validation_fraction,
        seed=config.validation_seed,
    )
    baseline = mean_squared_error(val_pairs, weights, opts=loss_opts)
    spsa_opts = make_spsa_options(
        max_iterations=config.spsa_iterations,
        batch_size=config.spsa_batch_size,
        loss_options=loss_opts,
        seed=config.validation_seed,
    )
    candidate = optimize(weights, PositionDB.from_pairs(train_pairs), spsa_opts)
    candidate_mse = mean_squared_error(val_pairs, candidate, opts=loss_opts)

    promoted = candidate_mse < baseline - config.min_validation_improvement
    if promoted:
        _promote(candidate, config.weights_path)

    return RoundResult(
        round_index=round_index,
        db_size=len(db),
        calibrated_k=k,
        baseline_val_mse=baseline,
        candidate_val_mse=candidate_mse,
        promoted=promoted,
    )


def _promote(weights: EvalWeights, weights_path: Path) -> None:
    """Save accepted weights to the canonical cache and force the engine to reload."""
    save_weights(weights, weights_path)
    invalidate_weights_cache()


def _log_round(config: LearnLoopConfig, result: RoundResult) -> None:
    if not config.verbose:
        return
    status = "PROMOTED" if result.promoted else "kept existing"
    print(
        f"[round {result.round_index + 1}/{config.rounds}] "
        f"db={result.db_size} k={result.calibrated_k:.4f} "
        f"val_mse {result.baseline_val_mse:.6f} -> {result.candidate_val_mse:.6f} "
        f"(improvement {result.improvement:+.6f}) -> {status}"
    )


def run_learn_loop(config: LearnLoopConfig | None = None) -> list[RoundResult]:
    """Run the persistent learning loop and return per-round results.

    Each round collects games into the growing DB, then tunes from the current
    canonical weights and promotes the candidate only when held-out validation MSE
    improves.
    """
    if config is None:
        config = LearnLoopConfig()
    results: list[RoundResult] = []
    for round_index in range(config.rounds):
        if config.verbose:
            print(
                f"== Round {round_index + 1}/{config.rounds}: "
                f"collecting {config.games_per_round} games at depth {config.depth} =="
            )
        db = _collect_round(config, round_index)
        result = _tune_round(config, db, round_index)
        _log_round(config, result)
        results.append(result)
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Persistent self-play learning loop (collect -> tune -> promote)."
    )
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--games-per-round", type=int, default=50)
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--db", type=Path, default=_DEFAULT_DB_PATH)
    parser.add_argument("--weights", type=Path, default=TUNED_WEIGHTS_PATH)
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--seed", type=int, default=None)
    _args = parser.parse_args()

    _cfg = LearnLoopConfig(
        rounds=_args.rounds,
        games_per_round=_args.games_per_round,
        depth=_args.depth,
        db_path=_args.db,
        weights_path=_args.weights,
        spsa_iterations=_args.iterations,
        spsa_batch_size=_args.batch_size,
        collect_seed=_args.seed,
    )
    _round_results = run_learn_loop(_cfg)
    _promotions = sum(1 for r in _round_results if r.promoted)
    print(f"\nDone: {_promotions}/{len(_round_results)} rounds promoted new weights.")
