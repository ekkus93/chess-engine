"""Tests for king safety."""

from __future__ import annotations
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


# Category 3: Promotion Edge Cases
# =============================================================================
def test_promotion_to_queen_explicit() -> None:
    """T3.4: Promotion to queen with explicit choice."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("a7"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
    assert (
        board.make_move(
            sq("e7"),
            sq("e8"),
            promotion=PieceType.QUEEN,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e8")) == PieceType.QUEEN
    assert board.get_color_at(sq("e8")) == Color.WHITE


def test_promotion_to_rook() -> None:
    """T3.4: Promotion to rook."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("a7"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
    assert (
        board.make_move(
            sq("e7"),
            sq("e8"),
            promotion=PieceType.ROOK,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e8")) == PieceType.ROOK


def test_promotion_to_bishop() -> None:
    """T3.4: Promotion to bishop."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("a7"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
    assert (
        board.make_move(
            sq("e7"),
            sq("e8"),
            promotion=PieceType.BISHOP,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e8")) == PieceType.BISHOP


def test_promotion_to_knight() -> None:
    """T3.4: Promotion to knight."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("a7"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
    assert (
        board.make_move(
            sq("e7"),
            sq("e8"),
            promotion=PieceType.KNIGHT,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e8")) == PieceType.KNIGHT


def test_promotion_to_king_rejected() -> None:
    """T3.4: Promotion to king is rejected."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("a7"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
    assert (
        board.make_move(
            sq("e7"),
            sq("e8"),
            promotion=PieceType.KING,
        )
        is False
    )


def test_black_promotion_to_rook() -> None:
    """T3.4: Black promotion to rook."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("a7"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e2"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    assert (
        board.make_move(
            sq("e2"),
            sq("e1"),
            promotion=PieceType.ROOK,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e1")) == PieceType.ROOK
    assert board.get_color_at(sq("e1")) == Color.BLACK


def test_promotion_from_rank_7_forced() -> None:
    """T3.3: Pawn on rank 7 can promote (rank 1 for white, rank 8 for black)."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("a8"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
    # White pawn on rank 7 (row 1) can promote to rank 8 (row 0)
    assert (
        board.make_move(
            sq("e7"),
            sq("e8"),
            promotion=PieceType.QUEEN,
        )
        is True
    )


def test_promotion_from_rank_6_blocked() -> None:
    """T3.3: Pawn on rank 6 is blocked from moving forward."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("a7"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.PAWN))  # e4 (rank 4)
    # Place a piece blocking the e-file
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.ROOK))
    # White pawn on rank 4 cannot promote from rank 4
    assert board.make_move(sq("e5"), sq("e8")) is False


def test_validation_rejects_king_capture() -> None:
    """Validation must reject any move that targets the opponent king."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e1"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("b1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.turn = Color.WHITE

    assert board.make_move(sq("b1"), sq("e1")) is False


def test_validation_rejects_king_capture_by_knight() -> None:
    """Validation must reject knight moves that target the opponent king."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e1"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("c2"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.turn = Color.WHITE

    assert board.make_move(sq("c2"), sq("e1")) is False


# =============================================================================
