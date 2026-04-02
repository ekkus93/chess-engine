"""Test utilities for chess engine tests."""

from chess_game.chess.board import Board, create_piece
from chess_game.chess.color import Color
from chess_game.chess.types import ConstantSquare
from chess_game.chess.pieces.piece import PieceType
from typing import Optional


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
        ConstantSquare(row=0, col=4),
        create_piece(Color.WHITE, PieceType.KING),
    )
    board.set_piece(
        ConstantSquare(row=7, col=4),
        create_piece(Color.BLACK, PieceType.KING),
    )


def setup_kings(board: Board) -> None:
    """Setup kings on the board for testing."""
    _setup_kings(board)


def get_piece(board: Board, square: tuple) -> Optional[object]:
    """Get a piece from the board."""
    return board.get_piece(ConstantSquare(row=square[0], col=square[1]))
