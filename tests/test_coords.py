from __future__ import annotations

import pytest

from chess_game.chess.coords import (
    algebraic_to_index,
    index_to_algebraic,
    parse_algebraic_move,
)
from chess_game.constants import (
    ROW_2,
    ROW_6,
    ConstantSquare,
    ROW_1,
    ROW_4,
    ROW_7,
    ROW_8,
    COL_E,
    COL_H,
)


def test_algebraic_to_index_uses_canonical_orientation() -> None:
    assert algebraic_to_index("e2") == ConstantSquare(row=ROW_6, col=COL_E)
    assert algebraic_to_index("a1") == ConstantSquare(row=ROW_7, col=COL_A)
    assert algebraic_to_index("h8") == ConstantSquare(row=ROW_8, col=COL_H)


def test_index_to_algebraic_round_trip() -> None:
    assert index_to_algebraic(ConstantSquare(row=ROW_6, col=COL_E)) == "e2"
    assert index_to_algebraic(ConstantSquare(row=ROW_7, col=COL_A)) == "a1"
    assert index_to_algebraic(ConstantSquare(row=ROW_8, col=COL_H)) == "h8"


def test_parse_algebraic_move_valid_input() -> None:
    assert parse_algebraic_move("e2e4") == (
        ConstantSquare(row=ROW_6, col=COL_E),
        ConstantSquare(row=ROW_4, col=COL_E),
    )


def test_parse_algebraic_move_rejects_malformed_input() -> None:
    with pytest.raises(ValueError):
        parse_algebraic_move("abc")

    with pytest.raises(ValueError):
        parse_algebraic_move("e2-e4")

    with pytest.raises(ValueError):
        parse_algebraic_move("e9e4")
