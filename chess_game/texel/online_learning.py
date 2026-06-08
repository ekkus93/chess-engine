"""Incremental learning: update weights after each self-play game."""
from __future__ import annotations

import dataclasses
import shutil
from pathlib import Path

from chess_game.chess.ai_weight_cache import invalidate_weights_cache
from chess_game.texel.loss import LossOptions, mean_squared_error
from chess_game.texel.position_db import GameRecord, PositionDB
from chess_game.texel.spsa import SPSAOptions, optimize
from chess_game.texel.weights_io import (
    TUNED_WEIGHTS_PATH,
    load_weights_or_default,
    save_weights,
)

_DEFAULT_DB_PATH = Path("chess_game/chess/data/positions.jsonl")
_VALIDATION_FRACTION = 0.20
_VALIDATION_SEED = 0


@dataclasses.dataclass
class OnlineLearningConfig:
    """Configuration for incremental self-play learning."""

    db_path: Path = dataclasses.field(default_factory=lambda: _DEFAULT_DB_PATH)
    weights_path: Path = dataclasses.field(default_factory=lambda: TUNED_WEIGHTS_PATH)
    spsa_iterations: int = 200
    spsa_batch_size: int = 256
    min_positions: int = 50
    enabled: bool = True
    loss_options: LossOptions = dataclasses.field(default_factory=LossOptions)
    # Validation gate configuration
    require_validation_improvement: bool = True
    min_validation_mse_improvement: float = 0.0
    keep_rejected_candidate: bool = False
    validation_fraction: float = 0.20
    validation_seed: int = 0


def _backup_path(weights_path: Path) -> Path:
    return weights_path.with_suffix(".backup" + weights_path.suffix)


def record_game_and_update_weights(
    record: GameRecord,
    config: OnlineLearningConfig | None = None,
) -> bool:
    """Add game positions to the DB and run a mini SPSA pass.

    Uses an 80/20 train/validation split. The candidate weights are only
    promoted if they achieve lower MSE than the current weights on the
    held-out validation set. Saves a backup of the current weights before
    any update and rolls back if the candidate does not improve.

    Returns True if weights were updated, False otherwise (not enough data,
    disabled, or candidate did not improve).
    """
    if config is None:
        config = OnlineLearningConfig()
    if not config.enabled:
        return False

    config.db_path.parent.mkdir(parents=True, exist_ok=True)

    if config.db_path.exists():
        db = PositionDB.load(config.db_path)
    else:
        db = PositionDB()

    db.add_game(record)
    db.save(config.db_path)

    if len(db) < config.min_positions:
        return False

    train_pairs, val_pairs = db.split(
        validation_fraction=_VALIDATION_FRACTION,
        seed=_VALIDATION_SEED,
    )
    if not val_pairs:
        return False

    weights = load_weights_or_default(config.weights_path)
    baseline_val_mse = mean_squared_error(val_pairs, weights, opts=config.loss_options)

    spsa_opts = SPSAOptions(
        max_iterations=config.spsa_iterations,
        batch_size=config.spsa_batch_size,
        verbose=False,
        checkpoint_path=None,
        loss_options=config.loss_options,
    )
    # Use only training pairs for optimisation
    train_db = PositionDB()
    for pos, outcome in train_pairs:
        train_db.add_game(GameRecord(positions=[pos], outcome=outcome))

    candidate = optimize(weights, train_db, spsa_opts)
    candidate_val_mse = mean_squared_error(val_pairs, candidate, opts=config.loss_options)

    if candidate_val_mse >= baseline_val_mse:
        return False

    if config.weights_path.exists():
        shutil.copy2(config.weights_path, _backup_path(config.weights_path))
    save_weights(candidate, config.weights_path)
    invalidate_weights_cache()
    return True


__all__ = ["OnlineLearningConfig", "record_game_and_update_weights"]
