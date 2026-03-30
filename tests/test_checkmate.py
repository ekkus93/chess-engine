"""Tests for checkmate."""

from __future__ import annotations

from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType

def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)

def _setup_kings(board: Board) -> None:
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))

# Category 4: King Safety & Pinning Edge Cases
# =============================================================================


def test_absolute_pin_rook_cannot_move_forward() -> None:
    """T4.1: Absolutely pinned rook cannot move to expose king."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    # Black king on d8 (not e8 to avoid conflict with queen)
    board.set_piece(0, 3, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.ROOK))
    # Queen on e8 that pins the rook (on the same file)
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.QUEEN))
    # White knight on f3 that can capture king
    board.set_piece(6, 5, create_piece(Color.WHITE, PieceType.KNIGHT))

    # White rook on e4 is pinned by black queen on e8
    # Rook cannot move towards king (that would expose it to queen)
    board.turn = Color.WHITE
    assert (
        board.make_move((3, 4), (3, 5)) is False
    )  # Cannot move towards king (away from queen)

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


def test_absolute_pin_rook_cannot_move_sideways() -> None:
    """T4.1: Absolutely pinned rook cannot move sideways."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    # Black king on d8 (not e8 to avoid conflict with queen)
    board.set_piece(0, 3, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.ROOK))
    # Queen on e8 that pins the rook (on the same file)
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.QUEEN))

    # White rook on e4 is pinned by black queen on e8
    board.turn = Color.WHITE
    assert board.make_move((3, 4), (3, 3)) is False  # Cannot move sideways

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


def test_pinned_rook_can_be_captured() -> None:
    """T4.1: Pinned piece can be captured (even if it exposes king)."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    # Black king on a8 (not on e-file to avoid conflict)
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.ROOK))
    # Bishop on a1-h8 diagonal that pins the rook
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.BISHOP))
    # Knight can capture the rook from e3
    board.set_piece(1, 3, create_piece(Color.BLACK, PieceType.KNIGHT))

    # Black knight can capture pinned white rook
    board.turn = Color.BLACK
    assert board.make_move((1, 3), (3, 4)) is True  # Black knight captures white rook

    # Black moves (to change turn)
    board.turn = Color.WHITE
    board.set_piece(6, 3, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    assert board.make_move((6, 3), (7, 3)) is True


def test_relative_pin_piece_can_move() -> None:
    """T4.2: Relatively pinned piece (not protecting king) can move."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(5, 4, create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.BISHOP))

    # White queen on d3 is pinned by black bishop but is not protecting king
    board.turn = Color.WHITE
    assert board.make_move((3, 4), (2, 4)) is True  # Can move away from pin


def test_relative_pin_does_not_prevent_movement() -> None:
    """T4.2: Relative pin doesn't prevent movement of non-king-protecting piece."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(5, 4, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.BISHOP))

    # White knight on d3 is pinned but can still move
    board.turn = Color.WHITE
    assert board.make_move((3, 4), (5, 5)) is True  # Knight can jump over pin


def test_engine_handles_double_pin_gracefully() -> None:
    """T4.3: Engine doesn't crash on double pin situation."""
    board = Board()
    clear_board(board)
    board.set_piece(
        3, 4, create_piece(Color.WHITE, PieceType.KING)
    )  # On a1-h8 diagonal (3+4=7)
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(
        5, 4, create_piece(Color.WHITE, PieceType.ROOK)
    )  # Between bishop and king
    # Bishop on a1-h8 diagonal that pins the rook
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.BISHOP))
    # Add a second attacker on the diagonal (rook on same diagonal)
    board.set_piece(6, 3, create_piece(Color.BLACK, PieceType.ROOK))

    # Create a double pin scenario
    # Engine should handle gracefully without crashing
    # Rook should be able to move sideways (not towards king)
    board.turn = Color.WHITE
    result = board.make_move((5, 4), (5, 3))
    # Should reject move that would expose king (towards king)
    assert result is False

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


def test_king_can_move_into_pin() -> None:
    """T4.4: King can move into a pinning position."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(5, 4, create_piece(Color.WHITE, PieceType.BISHOP))
    # Bishop on a1-h8 diagonal that can pin the king
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.BISHOP))

    # White king moves to d1 (becomes pinned but that's legal)
    board.turn = Color.WHITE
    assert board.make_move((7, 4), (6, 4)) is True  # King can move

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


def test_king_can_move_out_of_pin() -> None:
    """T4.4: King can move out of a pinning position."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(5, 4, create_piece(Color.WHITE, PieceType.BISHOP))
    # Bishop on a1-h8 diagonal that can pin the king
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.BISHOP))

    # White king moves away from pin
    board.turn = Color.WHITE
    assert board.make_move((7, 4), (7, 3)) is True  # King can move out of pin

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


# =============================================================================
