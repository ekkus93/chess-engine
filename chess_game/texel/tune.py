"""End-to-end Texel tuning pipeline."""
from __future__ import annotations

import dataclasses
from pathlib import Path

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.collect import CollectionOptions, collect_games
from chess_game.texel.loss import LossOptions, calibrate_and_save_k, mean_squared_error
from chess_game.texel.position_db import PositionDB
from chess_game.texel.spsa import SPSAOptions, optimize
from chess_game.texel.weights_io import load_weights_or_default, save_weights


@dataclasses.dataclass
class TuningConfig:
    """Configuration for a full Texel tuning run."""

    db_path: Path
    output_weights_path: Path
    collection_games: int = 500
    collection_depth: int = 1
    initial_weights_path: Path | None = None
    spsa_options: SPSAOptions = dataclasses.field(default_factory=SPSAOptions)
    do_calibrate_k: bool = True
    k_path: Path | None = None
    verbose: bool = True


def run_tuning(config: TuningConfig) -> EvalWeights:
    """Full Texel tuning pipeline: collect → calibrate → optimize → save."""
    # Step 1: load or collect DB
    if config.db_path.exists():
        if config.verbose:
            print(f"Loading existing DB from {config.db_path}")
        db = PositionDB.load(config.db_path)
    else:
        if config.verbose:
            print(
                f"Collecting {config.collection_games} games "
                f"at depth {config.collection_depth}..."
            )
        opts = CollectionOptions(
            db_path=config.db_path,
            num_games=config.collection_games,
            depth=config.collection_depth,
            verbose=config.verbose,
        )
        db = collect_games(opts)
        db.save(config.db_path)
    if config.verbose:
        print(f"DB size: {len(db)} positions")

    # Step 2: load initial weights
    weights = load_weights_or_default(config.initial_weights_path)

    # Step 3: calibrate k and build LossOptions
    k = 1.13
    if config.do_calibrate_k and len(db) > 0:
        k_path = config.k_path or config.db_path.with_suffix(".k.json")
        k = calibrate_and_save_k(db, weights, k_path)
        if config.verbose:
            print(f"Calibrated k = {k:.4f}")
    loss_opts = LossOptions(k=k)

    # Step 4: compute initial MSE
    pairs = db.all_pairs()
    initial_mse = mean_squared_error(pairs, weights, opts=loss_opts) if pairs else 0.0
    if config.verbose:
        print(f"Initial MSE: {initial_mse:.6f}")

    # Step 5: run SPSA using the same calibrated loss options
    spsa_opts = dataclasses.replace(config.spsa_options, loss_options=loss_opts)
    tuned = optimize(weights, db, spsa_opts)

    # Step 6: compute final MSE with the same loss options and save
    final_mse = mean_squared_error(pairs, tuned, opts=loss_opts) if pairs else 0.0
    if config.verbose:
        improvement = (initial_mse - final_mse) / max(initial_mse, 1e-9) * 100
        print(f"Final MSE: {final_mse:.6f} (improvement: {improvement:.1f}%)")
    save_weights(tuned, config.output_weights_path)
    if config.verbose:
        print(f"Saved tuned weights to {config.output_weights_path}")
    return tuned


if __name__ == "__main__":
    import argparse

    _parser = argparse.ArgumentParser(description="Run Texel tuning pipeline")
    _parser.add_argument("--games", type=int, default=500)
    _parser.add_argument("--depth", type=int, default=1)
    _parser.add_argument("--db", required=True)
    _parser.add_argument("--output", required=True)
    _parser.add_argument("--initial-weights", default=None)
    _parser.add_argument("--iterations", type=int, default=5000)
    _parser.add_argument("--verbose", action="store_true")
    _args = _parser.parse_args()
    _config = TuningConfig(
        db_path=Path(_args.db),
        output_weights_path=Path(_args.output),
        collection_games=_args.games,
        collection_depth=_args.depth,
        initial_weights_path=Path(_args.initial_weights) if _args.initial_weights else None,
        spsa_options=SPSAOptions(max_iterations=_args.iterations, verbose=_args.verbose),
        verbose=_args.verbose,
    )
    run_tuning(_config)
