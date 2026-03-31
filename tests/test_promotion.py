"""Tests for promotion."""

from __future__ import annotations

from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.constants import COL_A, COL_E, COL_H, ROW_1, ROW_7
from chess_game.chess.types import Color, PieceType


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(ConstantSquare(row=row, col=col))


def _setup_kings(board: Board) -> None:
    board.set_piece(
        ConstantSquare(row=ROW_1, col=4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=4), create_piece(Color.BLACK, PieceType.KING)
    )


# Category 2: En Passant Edge Cases
# =============================================================================


def test_en_passant_white_captures_black_pawn() -> None:
    """T2.2: Standard en passant capture - white pawn captures black pawn."""
    board = Board()
    # Clear entire board first
    for row in range(8):
        for col in range(8):
            board.clear_square(ConstantSquare(row=row, col=col))
    board.set_piece(
        ConstantSquare(row=ROW_1, col=4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # Row 6 = rank 2
    board.set_piece(
        ConstantSquare(row=ROW_7, col=4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK

    # Black moves pawn two squares (from rank 7 to rank 5)
    assert (
        board.make_move(ConstantSquare(row=ROW_7, col=4), ConstantSquare(row=ROW_5, col=4))
        is True
    )
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=4)

    # White moves knight (non-pawn move)
    board.turn = Color.WHITE
    board.set_piece(
        ConstantSquare(row=ROW_1, col=1), create_piece(Color.WHITE, PieceType.KNIGHT)
    )
    assert board.make_move(ConstantSquare(row=ROW_1, col=1), (5, 2)) is True

    # En passant target should be cleared
    assert board.en_passant_target is None

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_8, col=0), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(ConstantSquare(row=ROW_8, col=0), ConstantSquare(row=ROW_8, col=1))
        is True
    )


def test_en_passant_cannot_capture_own_pawn() -> None:
    """T2.5: Cannot capture own pawn en passant."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK

    # Black moves pawn two squares
    assert (
        board.make_move(ConstantSquare(row=ROW_7, col=4), ConstantSquare(row=ROW_5, col=4))
        is True
    )
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=4)

    # White tries to capture its own pawn en passant (should fail)
    board.turn = Color.WHITE
    assert (
        board.make_move(ConstantSquare(row=ROW_6, col=4), ConstantSquare(row=ROW_5, col=3))
        is False
    )

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_8, col=0), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(ConstantSquare(row=ROW_8, col=0), ConstantSquare(row=ROW_8, col=1))
        is True
    )


def test_en_passant_expires_after_white_move() -> None:
    """T2.3: En passant expires after white's move."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK

    # Black moves pawn two squares
    assert (
        board.make_move(ConstantSquare(row=ROW_7, col=4), ConstantSquare(row=ROW_5, col=4))
        is True
    )
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=4)

    # White makes any move
    board.turn = Color.WHITE
    board.set_piece(
        ConstantSquare(row=ROW_1, col=1), create_piece(Color.WHITE, PieceType.KNIGHT)
    )
    assert (
        board.make_move(ConstantSquare(row=ROW_1, col=1), ConstantSquare(row=ROW_3, col=2))
        is True
    )

    # En passant target should be cleared
    assert board.en_passant_target is None

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_8, col=0), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(ConstantSquare(row=ROW_8, col=0), ConstantSquare(row=ROW_8, col=1))
        is True
    )


# =============================================================================
