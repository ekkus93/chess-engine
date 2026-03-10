from __future__ import annotations

import pytest

from chess_game.chess.coords import algebraic_to_index, index_to_algebraic, parse_algebraic_move


def test_algebraic_to_index_uses_canonical_orientation() -> None:
    assert algebraic_to_index("e2") == (6, 4)
    assert algebraic_to_index("a1") == (7, 0)
    assert algebraic_to_index("h8") == (0, 7)


def test_index_to_algebraic_round_trip() -> None:
    assert index_to_algebraic(6, 4) == "e2"
    assert index_to_algebraic(7, 0) == "a1"
    assert index_to_algebraic(0, 7) == "h8"


def test_parse_algebraic_move_valid_input() -> None:
    assert parse_algebraic_move("e2e4") == ((6, 4), (4, 4))


def test_parse_algebraic_move_rejects_malformed_input() -> None:
    with pytest.raises(ValueError):
        parse_algebraic_move("abc")

    with pytest.raises(ValueError):
        parse_algebraic_move("e2-e4")

    with pytest.raises(ValueError):
        parse_algebraic_move("e9e4")
