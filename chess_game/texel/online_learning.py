"""Incremental learning: update weights after each self-play game."""
from __future__ import annotations

import dataclasses
from pathlib import Path

from chess_game.chess.ai_weight_cache import invalidate_weights_cache
from chess_game.texel.position_db import GameRecord, PositionDB
from chess_game.texel.spsa import SPSAOptions, optimize
from chess_game.texel.weights_io import (
    TUNED_WEIGHTS_PATH,
    load_weights_or_default,
    save_weights,
)

_DEFAULT_DB_PATH = Path("chess_game/chess/data/positions.jsonl")


@dataclasses.dataclass
class OnlineLearningConfig:
    """Configuration for incremental self-play learning."""

    db_path: Path = dataclasses.field(default_factory=lambda: _DEFAULT_DB_PATH)
    weights_path: Path = dataclasses.field(default_factory=lambda: TUNED_WEIGHTS_PATH)
    spsa_iterations: int = 200
    spsa_batch_size: int = 256
    min_positions: int = 50
    enabled: bool = True


def record_game_and_update_weights(
    record: GameRecord,
    config: OnlineLearningConfig | None = None,
) -> bool:
    """Add game positions to the DB and run a mini SPSA pass.

    Returns True if weights were updated, False otherwise (not enough data,
    or learning is disabled).
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

    weights = load_weights_or_default(config.weights_path)
    spsa_opts = SPSAOptions(
        max_iterations=config.spsa_iterations,
        batch_size=config.spsa_batch_size,
        verbose=False,
        checkpoint_path=None,
    )
    tuned = optimize(weights, db, spsa_opts)
    save_weights(tuned, config.weights_path)
    invalidate_weights_cache()

    return True


__all__ = ["OnlineLearningConfig", "record_game_and_update_weights"]
