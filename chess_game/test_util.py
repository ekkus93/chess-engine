"""Test utilities for chess engine tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from chess_game.chess.board import Board, create_piece
from chess_game.chess.constants import Color
from chess_game.chess.constants import ConstantSquare, get_col_constant, get_row_constant
from chess_game.chess.types import PieceType

if TYPE_CHECKING:
    pass


def _setup_kings(board: Board) -> None:
    """Setup kings on the board for testing."""
    board.set_piece(
        ConstantSquare(row=get_row_constant(0), col=get_col_constant(4)),
        create_piece(Color.WHITE, PieceType.KING),
    )
    board.set_piece(
        ConstantSquare(row=get_row_constant(7), col=get_col_constant(4)),
        create_piece(Color.BLACK, PieceType.KING),
    )


def setup_kings(board: Board) -> None:
    """Setup kings on the board for testing."""
    _setup_kings(board)


def get_piece(board: Board, square: tuple) -> Optional[object]:
    """Get a piece from the board."""
    return board.get_piece(ConstantSquare(row=get_row_constant(square[0]), col=get_col_constant(square[1])))
