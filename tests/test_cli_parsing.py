from __future__ import annotations
import pytest
from chess_game.chess.constants import (
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
    get_square_constant,
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


def test_parse_move_notation_e2e4_canonical() -> None:
    move = parse_move_notation("e2e4")
    assert move.start.row == ROW_2
    assert move.start.col == COL_E
    assert move.end.row == ROW_4
    assert move.end.col == COL_E
    assert move.promotion is None


def test_parse_move_notation_promotion_rook() -> None:
    move = parse_move_notation("e7e8r")
    assert move.promotion == PieceType.ROOK


def test_parse_move_notation_promotion_bishop() -> None:
    move = parse_move_notation("e7e8b")
    assert move.promotion == PieceType.BISHOP


def test_parse_move_notation_promotion_knight() -> None:
    move = parse_move_notation("e7e8n")
    assert move.promotion == PieceType.KNIGHT


def test_parse_move_notation_rejects_invalid_promotion() -> None:
    with pytest.raises(ValueError):
        parse_move_notation("e7e8k")
    with pytest.raises(ValueError):
        parse_move_notation("e7e8p")
    with pytest.raises(ValueError):
        parse_move_notation("e7e8x")
