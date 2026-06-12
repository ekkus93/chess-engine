"""Texel fail-loud: SPSAOptions rejects unsafe values; seed makes runs reproducible."""

from __future__ import annotations

import pytest

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.position_db import GameRecord, PositionDB
from chess_game.texel.spsa import SPSAOptions, optimize

_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def _one_position_db() -> PositionDB:
    db = PositionDB()
    db.add_game(GameRecord(positions=[_FEN], outcome=0.5))
    return db


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_iterations": 0},
        {"initial_step_size": 0},
        {"step_decay": 0},
        {"perturbation_size": 0},
        {"perturbation_decay": 0},
        {"stability_constant": -1},
        {"batch_size": 0},
        {"checkpoint_every": 0},
        {"initial_step_size": float("nan")},
        {"perturbation_size": float("inf")},
    ],
)
def test_invalid_spsa_options_raise(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        SPSAOptions(**kwargs)


def test_valid_default_options_construct() -> None:
    assert SPSAOptions().max_iterations == 5000


def test_valid_custom_options_construct() -> None:
    opts = SPSAOptions(max_iterations=10, batch_size=None, checkpoint_every=5, seed=1)
    assert opts.seed == 1


def test_same_seed_same_db_same_options_is_reproducible() -> None:
    """The key guarantee: a seeded run is deterministic given the same DB/options."""
    db = _one_position_db()
    weights = EvalWeights.default()
    opts = SPSAOptions(max_iterations=5, seed=42, verbose=False)
    first = optimize(weights, db, opts).to_flat_list()
    second = optimize(weights, db, opts).to_flat_list()
    assert first == second
