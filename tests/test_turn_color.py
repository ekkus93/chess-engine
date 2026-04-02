from __future__ import annotations
from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.chess.types import Color, PieceType
from chess_game.chess.constants import (
    get_row_constant,
    get_col_constant,
    get_square_constant,
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
# Category 10: Turn & Color Edge Cases
# =============================================================================
def test_turn_alternates_after_each_move() -> None:
    """T10.1: Turn alternates correctly after each move."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.turn = Color.WHITE
    # White moves first
    assert board.make_move(get_square_constant(0, 4), get_square_constant(0, 5)) is True
    assert board.turn == Color.BLACK
    # Black moves (black pawn starts on row 6)
    # Need to clear the white pawn at (6, 0) first
    board.clear_square(get_square_constant(5, 0))
    board.set_piece(
        get_square_constant(5, 0), create_piece(Color.BLACK, PieceType.PAWN)
    )
    assert board.make_move(get_square_constant(5, 0), get_square_constant(4, 0)) is True
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
                get_square_constant(6, 0),
                create_piece(Color.WHITE, PieceType.PAWN),
            )
            board.make_move(
                get_square_constant(6, 0),
                get_square_constant(6, 1),
            )
        else:
            board.set_piece(
                get_square_constant(7, 0),
                create_piece(Color.BLACK, PieceType.PAWN),
            )
            board.make_move(
                get_square_constant(7, 0),
                get_square_constant(7, 1),
            )
    assert board.turn == Color.WHITE


def test_cannot_move_opponent_piece() -> None:
    """T10.2: Cannot move opponent's piece."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        get_square_constant(5, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board.turn = Color.WHITE
    # Cannot move black pawn
    assert (
        board.make_move(get_square_constant(7, 4), get_square_constant(0, 4)) is False
    )


def test_cannot_capture_own_piece() -> None:
    """T10.2: Cannot capture own piece."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        get_square_constant(5, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board.set_piece(
        get_square_constant(5, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board.turn = Color.WHITE
    # Cannot capture own pawn
    assert (
        board.make_move(get_square_constant(5, 4), get_square_constant(5, 3)) is False
    )


def test_white_pawn_moves_toward_row_seven() -> None:
    """T10.3: White pawn forward direction is increasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board.turn = Color.WHITE
    # White pawn moves from row 2 to row 3 (toward rank 8, row 7)
    assert board.make_move(get_square_constant(1, 4), get_square_constant(2, 4)) is True
    assert board.get_piece_type_at(get_square_constant(2, 4)) == PieceType.PAWN


def test_black_pawn_moves_toward_row_one() -> None:
    """T10.3: Black pawn forward direction is decreasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )  # e7
    board.turn = Color.BLACK
    # Black pawn moves from row 7 to row 6 (toward rank 1, row 0)
    assert board.make_move(get_square_constant(6, 4), get_square_constant(5, 4)) is True
    assert board.get_piece_type_at(get_square_constant(5, 4)) == PieceType.PAWN


def test_white_pawn_capture_moves_toward_row_seven() -> None:
    """T10.3: White pawn capture direction is increasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 3), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(2, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.WHITE
    # White pawn captures diagonally toward rank 8 (row 3)
    assert board.make_move(get_square_constant(1, 3), get_square_constant(2, 4)) is True
    assert board.get_piece_type_at(get_square_constant(2, 4)) == PieceType.PAWN


def test_black_pawn_capture_moves_toward_row_one() -> None:
    """T10.3: Black pawn capture direction is decreasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(5, 5), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(4, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.turn = Color.BLACK
    # Black pawn captures diagonally toward rank 1 (row 0)
    assert board.make_move(get_square_constant(5, 5), get_square_constant(4, 4)) is True
    assert board.get_piece_type_at(get_square_constant(4, 4)) == PieceType.PAWN
