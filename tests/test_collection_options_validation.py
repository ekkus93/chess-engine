"""Texel fail-loud: CollectionOptions rejects values that would collect nothing or crash."""
from __future__ import annotations

from pathlib import Path

import pytest

from chess_game.texel.collect import CollectionOptions

_DB = Path("unused.jsonl")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"num_games": 0},
        {"depth": 0},
        {"max_moves": 0},
        {"skip_opening_plies": -1},
        {"max_move_result": "bogus"},
        # skip_opening_plies >= max_moves means every game is skipped.
        {"skip_opening_plies": 200, "max_moves": 200},
        {"skip_opening_plies": 10, "max_moves": 5},
    ],
)
def test_invalid_collection_options_raise(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        CollectionOptions(db_path=_DB, **kwargs)


def test_valid_collection_options_construct() -> None:
    opts = CollectionOptions(db_path=_DB, num_games=1, depth=1, skip_opening_plies=0, max_moves=1)
    assert opts.num_games == 1


def test_default_collection_options_construct() -> None:
    opts = CollectionOptions(db_path=_DB)
    assert opts.skip_opening_plies < opts.max_moves
