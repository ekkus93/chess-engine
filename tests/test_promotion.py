"""Tests for promotion."""

from __future__ import annotations
from chess_game.chess.board import Board, ConstantSquare, create_piece
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
from chess_game.chess.types import Color, PieceType


def clear_board(board: Board) -> None:
    for row_const in [ROW_1, ROW_2, ROW_3, ROW_4, ROW_5, ROW_6, ROW_7, ROW_8]:
        for col_const in [COL_A, COL_B, COL_C, COL_D, COL_E, COL_F, COL_G, COL_H]:
            board.clear_square(ConstantSquare(row=row_const, col=col_const))


def _setup_kings(board: Board) -> None:
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )


# Category 2: En Passant Edge Cases
# =============================================================================
def test_en_passant_white_captures_black_pawn() -> None:
    """T2.2: Standard en passant capture - white pawn captures black pawn."""
    board = Board()
    # Clear entire board first
    for row in range(8):
        for col in range(8):
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # Row 6 = rank 2
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK
    # Black moves pawn two squares (from rank 7 to rank 5)
    assert (
        board.make_move(
            get_square_constant(6, 4), get_square_constant(4, 4)
        )
        is True
    )
    assert board.en_passant_target == get_square_constant(5, 4)
    # White moves knight (non-pawn move)
    board.turn = Color.WHITE
    board.set_piece(
        get_square_constant(0, 0),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    # Knight from a1 to b3 (row diff 2, col diff 1)
    assert (
        board.make_move(
            get_square_constant(0, 0), get_square_constant(2, 1)
        )
        is True
    )
    # En passant target should be cleared
    assert board.en_passant_target is None
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        get_square_constant(7, 0), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(
            get_square_constant(7, 0), get_square_constant(7, 1)
        )
        is True
    )


def test_en_passant_cannot_capture_own_pawn() -> None:
    """T2.5: Cannot capture own pawn en passant."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK
    # Black moves pawn two squares
    assert (
        board.make_move(
            get_square_constant(6, 4), get_square_constant(4, 4)
        )
        is True
    )
    assert board.en_passant_target == get_square_constant(5, 4)
    # White tries to capture its own pawn en passant (should fail)
    board.turn = Color.WHITE
    assert (
        board.make_move(
            get_square_constant(5, 4), get_square_constant(4, 3)
        )
        is False
    )
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        get_square_constant(7, 0), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(
            get_square_constant(7, 0), get_square_constant(7, 1)
        )
        is True
    )


def test_en_passant_expires_after_white_move() -> None:
    """T2.3: En passant expires after white's move."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK
    # Black moves pawn two squares
    assert (
        board.make_move(
            get_square_constant(6, 4), get_square_constant(4, 4)
        )
        is True
    )
    assert board.en_passant_target == get_square_constant(5, 4)
    # White makes any move
    board.turn = Color.WHITE
    board.set_piece(
        get_square_constant(0, 0),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    # Knight from a1 to b3 (row diff 2, col diff 1)
    assert (
        board.make_move(
            get_square_constant(0, 0), get_square_constant(2, 1)
        )
        is True
    )
    # En passant target should be cleared
    assert board.en_passant_target is None
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        get_square_constant(7, 0), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(
            get_square_constant(7, 0), get_square_constant(7, 1)
        )
        is True
    )


# =============================================================================
