"""Tests for king safety."""

from __future__ import annotations
from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.chess.constants import (
    get_row_constant,
    get_col_constant,
    get_square_constant,
    COL_A,
    COL_E,
    COL_F,
    COL_G,
    COL_H,
    ROW_1,
    ROW_7,
    ROW_8,
    ROW_2,
    ROW_3,
    ROW_4,
    ROW_5,
    ROW_6,
)
from chess_game.chess.types import Color, PieceType


def setup_king_safety_position(board: Board) -> None:
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )


# Category 3: Promotion Edge Cases
# =============================================================================
def test_promotion_to_queen_explicit() -> None:
    """T3.4: Promotion to queen with explicit choice."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(6, 0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    assert (
        board.make_move(
            get_square_constant(6, 4),
            get_square_constant(7, 4),
            promotion=PieceType.QUEEN,
        )
        is True
    )
    assert board.get_piece_type_at(get_square_constant(7, 4)) == PieceType.QUEEN
    assert board.get_color_at(get_square_constant(7, 4)) == Color.WHITE


def test_promotion_to_rook() -> None:
    """T3.4: Promotion to rook."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(6, 0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    assert (
        board.make_move(
            get_square_constant(6, 4),
            get_square_constant(7, 4),
            promotion=PieceType.ROOK,
        )
        is True
    )
    assert board.get_piece_type_at(get_square_constant(7, 4)) == PieceType.ROOK


def test_promotion_to_bishop() -> None:
    """T3.4: Promotion to bishop."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(6, 0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    assert (
        board.make_move(
            get_square_constant(6, 4),
            get_square_constant(7, 4),
            promotion=PieceType.BISHOP,
        )
        is True
    )
    assert board.get_piece_type_at(get_square_constant(7, 4)) == PieceType.BISHOP


def test_promotion_to_knight() -> None:
    """T3.4: Promotion to knight."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(6, 0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    assert (
        board.make_move(
            get_square_constant(6, 4),
            get_square_constant(7, 4),
            promotion=PieceType.KNIGHT,
        )
        is True
    )
    assert board.get_piece_type_at(get_square_constant(7, 4)) == PieceType.KNIGHT


def test_promotion_to_king_rejected() -> None:
    """T3.4: Promotion to king is rejected."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(6, 0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    assert (
        board.make_move(
            get_square_constant(6, 4),
            get_square_constant(7, 4),
            promotion=PieceType.KING,
        )
        is False
    )


def test_black_promotion_to_rook() -> None:
    """T3.4: Black promotion to rook."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(6, 0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK
    assert (
        board.make_move(
            get_square_constant(1, 4),
            get_square_constant(0, 4),
            promotion=PieceType.ROOK,
        )
        is True
    )
    assert board.get_piece_type_at(get_square_constant(0, 4)) == PieceType.ROOK
    assert board.get_color_at(get_square_constant(0, 4)) == Color.BLACK


def test_promotion_from_rank_7_forced() -> None:
    """T3.3: Pawn on rank 7 can promote (rank 1 for white, rank 8 for black)."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(7, 0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    # White pawn on rank 2 can promote to rank 8 (row 7)
    assert (
        board.make_move(
            get_square_constant(1, 4),
            get_square_constant(7, 4),
            promotion=PieceType.QUEEN,
        )
        is True
    )


def test_promotion_from_rank_6_blocked() -> None:
    """T3.3: Pawn on rank 6 is blocked from moving forward."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(6, 0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(4, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e4 (rank 4)
    # Place a piece blocking the e-file
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )
    # White pawn on rank 4 cannot promote from rank 4
    assert (
        board.make_move(get_square_constant(4, 4), get_square_constant(7, 4)) is False
    )


# =============================================================================
