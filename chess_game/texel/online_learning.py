"""Incremental learning: update weights after each self-play game."""
from __future__ import annotations

import dataclasses
import shutil
from pathlib import Path

from chess_game.chess.ai_weight_cache import invalidate_weights_cache
from chess_game.texel.loss import LossOptions, mean_squared_error
from chess_game.texel.position_db import GameRecord, PositionDB
from chess_game.texel.spsa import SPSAOptions, make_spsa_options, optimize
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
    validation_fraction: float = 0.20
    validation_seed: int = 0

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if not 0.0 <= self.validation_fraction < 1.0:
            raise ValueError(
                f"validation_fraction must satisfy 0.0 <= validation_fraction < 1.0, "
                f"got {self.validation_fraction}"
            )


# Stable reason strings reported by record_game_and_update_weights_result(). A bare
# False no longer hides which guard path was taken.
REASON_DISABLED = "disabled"
REASON_NOT_ENOUGH_POSITIONS = "not_enough_positions"
REASON_EMPTY_TRAINING_SPLIT = "empty_training_split"
REASON_EMPTY_VALIDATION_SPLIT = "empty_validation_split"
REASON_CANDIDATE_NOT_BETTER = "candidate_not_better"
REASON_CANDIDATE_BELOW_THRESHOLD = "candidate_below_threshold"
REASON_UPDATED = "updated"


@dataclasses.dataclass(frozen=True)
class OnlineLearningResult:
    """Structured outcome of an online-learning attempt.

    ``reason`` is one of the ``REASON_*`` constants; ``updated`` is True only when
    ``reason == REASON_UPDATED``. ``candidate_path`` is always None today (rejected
    candidates are in-memory and never written to disk).
    """

    updated: bool
    reason: str
    positions: int = 0
    baseline_val_mse: float | None = None
    candidate_val_mse: float | None = None
    candidate_path: Path | None = None


def _backup_path(weights_path: Path) -> Path:
    return weights_path.with_suffix(".backup" + weights_path.suffix)


def _load_or_create_db(db_path: Path) -> PositionDB:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return PositionDB.load(db_path) if db_path.exists() else PositionDB()


def _spsa_options(config: OnlineLearningConfig) -> SPSAOptions:
    return make_spsa_options(
        max_iterations=config.spsa_iterations,
        batch_size=config.spsa_batch_size,
        loss_options=config.loss_options,
    )


def _acceptance_reason(
    config: OnlineLearningConfig,
    baseline_val_mse: float | None,
    candidate_val_mse: float | None,
) -> str:
    """Decide whether a candidate is accepted, and why not when rejected."""
    if not config.require_validation_improvement:
        return REASON_UPDATED
    # require_validation_improvement is True only reaches here with a non-empty
    # validation split, so both MSEs are concrete floats.
    assert baseline_val_mse is not None and candidate_val_mse is not None
    if candidate_val_mse >= baseline_val_mse:
        return REASON_CANDIDATE_NOT_BETTER
    if candidate_val_mse >= baseline_val_mse - config.min_validation_mse_improvement:
        return REASON_CANDIDATE_BELOW_THRESHOLD
    return REASON_UPDATED


def _promote_candidate(config: OnlineLearningConfig, candidate) -> None:
    if config.weights_path.exists():
        shutil.copy2(config.weights_path, _backup_path(config.weights_path))
    save_weights(candidate, config.weights_path)
    invalidate_weights_cache()


def record_game_and_update_weights_result(
    record: GameRecord,
    config: OnlineLearningConfig | None = None,
) -> OnlineLearningResult:
    """Add game positions to the DB and run a mini SPSA pass, reporting the outcome.

    Uses an 80/20 train/validation split. The candidate weights are only promoted if
    they beat the current weights on the held-out validation set; a backup of the
    current weights is saved before any update. Every non-update path returns a
    distinct ``reason`` rather than a bare False, so callers can tell *why* no update
    happened.
    """
    if config is None:
        config = OnlineLearningConfig()
    if not config.enabled:
        return OnlineLearningResult(updated=False, reason=REASON_DISABLED)

    db = _load_or_create_db(config.db_path)
    db.add_game(record)
    db.save(config.db_path)
    positions = len(db)
    if positions < config.min_positions:
        return OnlineLearningResult(False, REASON_NOT_ENOUGH_POSITIONS, positions)

    train_pairs, val_pairs = db.split(
        validation_fraction=config.validation_fraction,
        seed=config.validation_seed,
    )
    if config.require_validation_improvement and not val_pairs:
        return OnlineLearningResult(False, REASON_EMPTY_VALIDATION_SPLIT, positions)
    if not train_pairs:
        return OnlineLearningResult(False, REASON_EMPTY_TRAINING_SPLIT, positions)

    weights = load_weights_or_default(config.weights_path)
    baseline = (
        mean_squared_error(val_pairs, weights, opts=config.loss_options)
        if val_pairs
        else None
    )
    candidate = optimize(weights, PositionDB.from_pairs(train_pairs), _spsa_options(config))
    candidate_mse = (
        mean_squared_error(val_pairs, candidate, opts=config.loss_options)
        if val_pairs
        else None
    )

    reason = _acceptance_reason(config, baseline, candidate_mse)
    if reason != REASON_UPDATED:
        return OnlineLearningResult(False, reason, positions, baseline, candidate_mse)

    _promote_candidate(config, candidate)
    return OnlineLearningResult(True, REASON_UPDATED, positions, baseline, candidate_mse)


def record_game_and_update_weights(
    record: GameRecord,
    config: OnlineLearningConfig | None = None,
) -> bool:
    """Backward-compatible wrapper: True iff weights were updated.

    Prefer :func:`record_game_and_update_weights_result` for the structured reason.
    """
    return record_game_and_update_weights_result(record, config).updated


__all__ = [
    "OnlineLearningConfig",
    "OnlineLearningResult",
    "record_game_and_update_weights",
    "record_game_and_update_weights_result",
]
