"""Tests for king safety."""

from __future__ import annotations

from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.constants import COL_A, COL_E, COL_F, COL_G, COL_H, ROW_1, ROW_7, ROW_8
from chess_game.chess.types import Color, PieceType


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(ConstantSquare(row=row, col=col))


def _setup_kings(board: Board) -> None:
    board.set_piece(
        ConstantSquare(row=ROW_7, col=4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=4), create_piece(Color.BLACK, PieceType.KING)
    )


# Category 3: Promotion Edge Cases
# =============================================================================


def test_promotion_to_queen_explicit() -> None:
    """T3.4: Promotion to queen with explicit choice."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=4), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=4),
            ConstantSquare(row=ROW_8, col=4),
            promotion=PieceType.QUEEN,
        )
        is True
    )
    assert board.get_piece_type_at(ConstantSquare(row=ROW_8, col=4)) == PieceType.QUEEN
    assert board.get_color_at(ConstantSquare(row=ROW_8, col=4)) == Color.WHITE


def test_promotion_to_rook() -> None:
    """T3.4: Promotion to rook."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=4), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=4),
            ConstantSquare(row=ROW_8, col=4),
            promotion=PieceType.ROOK,
        )
        is True
    )
    assert board.get_piece_type_at(ConstantSquare(row=ROW_8, col=4)) == PieceType.ROOK


def test_promotion_to_bishop() -> None:
    """T3.4: Promotion to bishop."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=4), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=4),
            ConstantSquare(row=ROW_8, col=4),
            promotion=PieceType.BISHOP,
        )
        is True
    )
    assert board.get_piece_type_at(ConstantSquare(row=ROW_8, col=4)) == PieceType.BISHOP


def test_promotion_to_knight() -> None:
    """T3.4: Promotion to knight."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=4), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=4),
            ConstantSquare(row=ROW_8, col=4),
            promotion=PieceType.KNIGHT,
        )
        is True
    )
    assert board.get_piece_type_at(ConstantSquare(row=ROW_8, col=4)) == PieceType.KNIGHT


def test_promotion_to_king_rejected() -> None:
    """T3.4: Promotion to king is rejected."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=4), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=4),
            ConstantSquare(row=ROW_8, col=4),
            promotion=PieceType.KING,
        )
        is False
    )


def test_black_promotion_to_rook() -> None:
    """T3.4: Black promotion to rook."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK

    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=4),
            ConstantSquare(row=ROW_7, col=4),
            promotion=PieceType.ROOK,
        )
        is True
    )
    assert board.get_piece_type_at(ConstantSquare(row=ROW_7, col=4)) == PieceType.ROOK
    assert board.get_color_at(ConstantSquare(row=ROW_7, col=4)) == Color.BLACK


def test_promotion_from_rank_7_forced() -> None:
    """T3.3: Pawn on rank 7 can promote (rank 1 for white, rank 8 for black)."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=4), create_piece(Color.WHITE, PieceType.PAWN)
    )

    # White pawn on rank 2 can promote to rank 8 (row 0)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=4),
            ConstantSquare(row=ROW_8, col=4),
            promotion=PieceType.QUEEN,
        )
        is True
    )


def test_promotion_from_rank_6_blocked() -> None:
    """T3.3: Pawn on rank 6 (row 2) cannot promote yet."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=4), create_piece(Color.WHITE, PieceType.PAWN)
    )

    # White pawn on rank 6 cannot promote yet
    assert (
        board.make_move(
            ConstantSquare(row=ROW_6, col=4), ConstantSquare(row=ROW_8, col=4)
        )
        is False
    )


# =============================================================================
