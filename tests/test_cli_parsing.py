from __future__ import annotations

import pytest

from chess_game.chess.move import parse_move_notation
from chess_game.chess.types import PieceType


def test_parse_move_notation_accepts_basic_coordinate_move() -> None:
    move = parse_move_notation("e2e4")

    assert move.start == (6, 4)
    assert move.end == (4, 4)
    assert move.promotion is None


def test_parse_move_notation_accepts_promotion_suffix() -> None:
    move = parse_move_notation("e7e8q")

    assert move.start == (1, 4)
    assert move.end == (0, 4)
    assert move.promotion == PieceType.QUEEN


def test_parse_move_notation_rejects_malformed_strings() -> None:
    with pytest.raises(ValueError):
        parse_move_notation("e2")

    with pytest.raises(ValueError):
        parse_move_notation("e2-e4")

    with pytest.raises(ValueError):
        parse_move_notation("hello")

    with pytest.raises(ValueError):
        parse_move_notation("e9e4")

    with pytest.raises(ValueError):
        parse_move_notation("a1a1x")
