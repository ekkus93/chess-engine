"""Helper functions for special moves tests."""

from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.chess.types import Color, PieceType
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


def clear_board(board: Board) -> None:
    """Clear all pieces from the board."""
    for row in range(8):
        for col in range(8):
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )


def _setup_kings(board: Board) -> None:
    """Set up kings in the center to test king safety scenarios."""
    clear_board(board)
    white_king = create_piece(Color.WHITE, PieceType.KING)
    black_king = create_piece(Color.BLACK, PieceType.KING)
    board.set_piece(ConstantSquare(row=ROW_7, col=COL_E), white_king)
    board.set_piece(ConstantSquare(row=ROW_8, col=COL_E), black_king)
