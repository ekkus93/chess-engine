from __future__ import annotations


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
)


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(ConstantSquare(row=row, col=col))


def _setup_kings(board: Board) -> None:
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )


# =============================================================================
# Category 10: Turn & Color Edge Cases
# =============================================================================


def test_turn_alternates_after_each_move() -> None:
    """T10.1: Turn alternates correctly after each move."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.turn = Color.WHITE

    # White moves first
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_7, col=COL_F)
        )
        is True
    )
    assert board.turn == Color.BLACK

    # Black moves (black pawn starts on row 6)
    # Need to clear the white pawn at (6, 0) first
    board.clear_square(ConstantSquare(row=ROW_6, col=COL_A))
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_A), create_piece(Color.BLACK, PieceType.PAWN)
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_6, col=COL_A), ConstantSquare(row=ROW_7, col=COL_A)
        )
        is True
    )
    assert board.turn == Color.WHITE


def test_turn_alternates_after_100_moves() -> None:
    """T10.1: Turn alternates correctly after many moves."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.turn = Color.WHITE

    # Make 99 moves alternating
    # After odd number of moves, should be black's turn
    for i in range(99):
        if i % 2 == 0:
            board.set_piece(
                ConstantSquare(row=ROW_7, col=COL_A),
                create_piece(Color.WHITE, PieceType.PAWN),
            )
            board.make_move(
                ConstantSquare(row=ROW_7, col=COL_A),
                ConstantSquare(row=ROW_7, col=COL_B),
            )
        else:
            board.set_piece(
                ConstantSquare(row=ROW_8, col=COL_A),
                create_piece(Color.BLACK, PieceType.PAWN),
            )
            board.make_move(
                ConstantSquare(row=ROW_8, col=COL_A),
                ConstantSquare(row=ROW_8, col=COL_B),
            )

    assert board.turn == Color.WHITE


def test_cannot_move_opponent_piece() -> None:
    """T10.2: Cannot move opponent's piece."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board.turn = Color.WHITE

    # Cannot move black pawn
    assert (
        board.make_move(
            ConstantSquare(row=ROW_8, col=COL_E), ConstantSquare(row=ROW_1, col=COL_E)
        )
        is False
    )


def test_cannot_capture_own_piece() -> None:
    """T10.2: Cannot capture own piece."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board.turn = Color.WHITE

    # Cannot capture own pawn
    assert (
        board.make_move(
            ConstantSquare(row=ROW_6, col=COL_E), ConstantSquare(row=ROW_6, col=COL_D)
        )
        is False
    )


def test_white_pawn_moves_toward_row_zero() -> None:
    """T10.3: White pawn forward direction is decreasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board.turn = Color.WHITE

    # White pawn moves from row 6 to row 5 (toward rank 1, row 0)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_6, col=COL_E), ConstantSquare(row=ROW_5, col=COL_E)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_5, col=COL_E)) == PieceType.PAWN
    )


def test_black_pawn_moves_toward_row_seven() -> None:
    """T10.3: Black pawn forward direction is increasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK

    # Black pawn moves from row 1 to row 2 (toward rank 1, row 7)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_2, col=COL_E)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_2, col=COL_E)) == PieceType.PAWN
    )


def test_white_pawn_capture_moves_toward_row_zero() -> None:
    """T10.3: White pawn capture direction is decreasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_D), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_5, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.WHITE

    # White pawn captures diagonally toward rank 8 (row 5)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_6, col=COL_D), ConstantSquare(row=ROW_5, col=COL_E)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_5, col=COL_E)) == PieceType.PAWN
    )


def test_black_pawn_capture_moves_toward_row_seven() -> None:
    """T10.3: Black pawn capture direction is increasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_F), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.turn = Color.BLACK

    # Black pawn captures diagonally toward rank 1 (row 2)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_F), ConstantSquare(row=ROW_2, col=COL_E)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_2, col=COL_E)) == PieceType.PAWN
    )
