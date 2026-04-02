"""Test utilities for chess engine tests."""

from chess_game.chess.board import Board, create_piece
from chess_game.chess.color import Color
from chess_game.chess.types import ConstantSquare
from chess_game.constants import (
    COL_A,
    COL_B,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_G,
    COL_H,
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_4,
    ROW_5,
    ROW_6,
    ROW_7,
    ROW_8,
    get_row_constant,
    get_col_constant,
)
from chess_game.chess.pieces.piece import PieceType
from typing import Optional


def _get_square(row: int, col: int) -> ConstantSquare:
    """Convert row/col integers to ConstantSquare objects."""
    return ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))


def clear_board(board: Board) -> None:
    """Clear all pieces from the board."""
    for row in range(8):
        for col in range(8):
            board.set_piece(_get_square(row, col), None)


def _setup_kings(
    board: Board, white_square: tuple = (0, 4), black_square: tuple = (7, 4)
) -> None:
    """Setup kings on the board for testing.

    Args:
        board: The board instance
        white_square: (row, col) position for white king
        black_square: (row, col) position for black king
    """
    board.set_piece(
        _get_square(white_square[0], white_square[1]),
        create_piece(Color.WHITE, PieceType.KING),
    )
    board.set_piece(
        _get_square(black_square[0], black_square[1]),
        create_piece(Color.BLACK, PieceType.KING),
    )


def setup_kings(board: Board) -> None:
    """Setup kings on the board for testing."""
    _setup_kings(board)


def get_piece(board: Board, square: tuple) -> Optional[object]:
    """Get a piece from the board."""
    return board.get_piece(_get_square(square[0], square[1]))
