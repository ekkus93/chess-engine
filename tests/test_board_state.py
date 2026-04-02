from __future__ import annotations
from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.chess.types import Color, PieceType
from chess_game.chess.constants import (
    COL_A,
    COL_B,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_G,
    COL_H,
    ROW_1,
    ROW_7,
    ROW_8,
)
from chess_game.chess.constants import get_row_constant, get_col_constant, get_square_constant


def clear_board(board: Board) -> None:
    for row in range(ROW_1, ROW_8 + 1):
        for col in range(COL_A, COL_H):
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )


def _setup_kings(board: Board) -> None:
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )


# =============================================================================
# Category 9: Board State Edge Cases
# =============================================================================
def test_board_handles_missing_white_king_gracefully() -> None:
    """T9.1: Engine handles board state with missing king gracefully."""
    board = Board()
    clear_board(board)
    # Only set black king, no white king
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK
    # Should not crash, just return no legal moves
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_extra_king_gracefully() -> None:
    """T9.1: Engine handles board state with extra king gracefully."""
    board = Board()
    clear_board(board)
    # Set both kings plus an extra white king
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.turn = Color.WHITE
    # Should not crash
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_missing_opponent_king() -> None:
    """T9.1: Engine handles board state with missing opponent king."""
    board = Board()
    clear_board(board)
    # Only white king present
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.turn = Color.WHITE
    # Should not crash
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_all_pieces_captured() -> None:
    """T9.2: Engine handles board state with minimal pieces."""
    board = Board()
    clear_board(board)
    # Only kings remain
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.turn = Color.WHITE
    # Should work normally
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_full_starting_position() -> None:
    """T9.3: Engine handles full board starting position."""
    board = Board()
    # Starting position is already set up by Board.__init__()
    board.turn = Color.WHITE
    # All pieces should be movable
    white_king_moves = board.get_legal_moves()
    assert len(white_king_moves) > 0
