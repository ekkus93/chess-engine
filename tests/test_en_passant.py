"""Tests for en passant."""

from __future__ import annotations
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


# Category 1: Castling Edge Cases
# =============================================================================
def test_cannot_castle_if_rook_captured_on_original_square() -> None:
    """T1.1: Castling forbidden when rook is captured on original square."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.ROOK))
    # Black captures white's kingside rook
    board.turn = Color.BLACK
    assert (
        board.make_move(
            sq("h8"),
            sq("h1"),
        )
        is True
    )
    # White cannot castle kingside (rook captured)
    board.turn = Color.WHITE
    assert (
        board.make_move(
            sq("e1"),
            sq("g8"),
        )
        is False
    )


def test_castling_right_persists_after_rook_moved_then_returns() -> None:
    """T1.3: Castling right persists if rook moves and returns to original square."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.ROOK))
    # Move rook away
    board.turn = Color.WHITE
    assert (
        board.make_move(
            sq("h1"),
            sq("g1"),
        )
        is True
    )
    # Castling should be disabled (rook moved)
    assert (
        board.make_move(
            sq("e1"),
            sq("g8"),
        )
        is False
    )
    # Move rook back to original square
    board.turn = Color.WHITE
    assert (
        board.make_move(
            sq("g1"),
            sq("h1"),
        )
        is True
    )
    # Castling should still be disabled (original rook left)
    assert (
        board.make_move(
            sq("e1"),
            sq("g8"),
        )
        is False
    )


def test_cannot_castle_if_path_blocked_by_enemy_piece() -> None:
    """T1.2: Castling blocked if enemy piece occupies path or destination."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.ROOK))
    # Black pawn blocks kingside castling path
    board.turn = Color.BLACK
    board.set_piece(sq("g1"), create_piece(Color.BLACK, PieceType.PAWN))
    # White cannot castle (path blocked)
    board.turn = Color.WHITE
    assert (
        board.make_move(
            sq("e1"),
            sq("g8"),
        )
        is False
    )


def test_castling_with_opponent_piece_on_destination_square() -> None:
    """T1.2: Castling blocked if enemy piece on destination square."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.ROOK))
    # Black knight on kingside destination
    board.turn = Color.BLACK
    board.set_piece(sq("g1"), create_piece(Color.BLACK, PieceType.KNIGHT))
    # White cannot castle (enemy piece on destination)
    board.turn = Color.WHITE
    assert (
        board.make_move(
            sq("e1"),
            sq("g8"),
        )
        is False
    )


def test_castling_kingside_with_queenside_rook_only() -> None:
    """Kingside castling allowed if queenside rook moved but kingside rook remains."""
    board = Board()
    for row in range(8):
        for col in range(8):
            if not ((row == 0 and col == 4) or (row == 7 and col in {0, 4, 7})):
                board.clear_square(sq(f"{chr(ord('a')+col)}{8-row}"))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.ROOK))

    # Move queenside rook away (kingside rook remains)
    board.turn = Color.BLACK
    assert (
        board.make_move(
            sq("a8"),
            sq("a7"),
        )
        is True
    )

    # Kingside castling should be possible (kingside rook remains)
    board.turn = Color.BLACK
    assert (
        board.make_move(
            sq("e8"),
            sq("g8"),
        )
        is True
    )

    # Return rook
    board.turn = Color.BLACK
    assert (
        board.make_move(
            sq("a7"),
            sq("a8"),
        )
        is True
    )


def test_castling_queenside_with_kingside_rook_only() -> None:
    """T1.3: Queenside castling allowed if kingside rook moved but queenside rook remains."""
    board = Board()
    # Clear everything except the pieces we need
    for row in range(8):
        for col in range(8):
            if not ((row == 0 and col == 4) or (row == 7 and col in {0, 4, 7})):
                board.clear_square(sq(f"{chr(ord('a')+col)}{8-row}"))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.ROOK))

    # Move kingside rook away (queenside rook remains)
    board.turn = Color.BLACK
    assert (
        board.make_move(
            sq("h8"),
            sq("h7"),
        )
        is True
    )

    # Switch turn back to black for castling
    board.turn = Color.BLACK

    # Queenside castling should be possible (queenside rook remains)
    # Kingside castling should NOT be possible (kingside rook moved)
    assert (
        board.make_move(
            sq("e8"),
            sq("c8"),
        )
        is True
    )

    # Switch turn back to black for rook return
    board.turn = Color.BLACK
    assert (
        board.make_move(
            sq("h7"),
            sq("h8"),
        )
        is True
    )  # Return rook


def test_cannot_castle_if_king_squre_attacked_during_castle() -> None:
    """T8.1: Cannot castle if square behind king is attacked."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.ROOK))
    # Place black bishop on diagonal to attack g1 (square behind king on kingside)
    board.turn = Color.BLACK
    board.set_piece(sq("h1"), create_piece(Color.BLACK, PieceType.BISHOP))
    # White cannot castle kingside (path through attacked square)
    board.turn = Color.WHITE
    assert (
        board.make_move(
            sq("e1"),
            sq("g8"),
        )
        is False
    )
    # White cannot castle kingside (path through attacked square)
    board.turn = Color.WHITE
    assert (
        board.make_move(
            sq("e1"),
            sq("g8"),
        )
        is False
    )


# =============================================================================
