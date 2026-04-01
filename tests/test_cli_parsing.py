from __future__ import annotations
import pytest
from chess_game.constants import (
    ConstantSquare,
    ROW_1,
    ROW_2,
    ROW_4,
    ROW_7,
    ROW_8,
    COL_E,
    COL_H,
    get_row_constant,
    get_col_constant,
)
from chess_game.chess.move import parse_move_notation
from chess_game.chess.types import PieceType


def test_parse_move_notation_accepts_basic_coordinate_move() -> None:
    move = parse_move_notation("e7e8")
    assert isinstance(move.start, ConstantSquare)
    assert move.start.row == ROW_7
    assert move.start.col == COL_E
    assert move.end.row == ROW_8
    assert move.end.col == COL_E
    assert move.promotion is None


def test_parse_move_notation_accepts_promotion_suffix() -> None:
    move = parse_move_notation("e7e8q")
    assert isinstance(move.start, ConstantSquare)
    assert move.start.row == ROW_7
    assert move.start.col == COL_E
    assert move.end.row == ROW_8
    assert move.end.col == COL_E
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
