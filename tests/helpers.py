"""Helper functions for special moves tests."""

from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.chess.types import Color, PieceType


def clear_board(board: Board) -> None:
    """Clear all pieces from the board."""
    for row in range(8):
        for col in range(8):
            board.clear_square(ConstantSquare(row=row, col=col))


def _setup_kings(board: Board) -> None:
    """Set up kings in the center to test king safety scenarios."""
    clear_board(board)
    white_king = create_piece(Color.WHITE, PieceType.KING)
    black_king = create_piece(Color.BLACK, PieceType.KING)
    board.set_piece(ConstantSquare(row=ROW_7, col=COL_E), white_king)
    board.set_piece(ConstantSquare(row=ROW_8, col=COL_E), black_king)
