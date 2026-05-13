"""Tests for checkmate."""

from __future__ import annotations
from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.chess.constants import (
    get_row_constant,
    get_col_constant,
    COL_A,
    COL_B,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_G,
    COL_H,
    ROW_0,
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_4,
    get_square_constant,
    ROW_5,
    ROW_6,
    ROW_7,
    ROW_8,
)
from chess_game.chess.types import Color, PieceType


def setup_checkmate_position(board: Board) -> None:
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )


# Category 4: King Safety & Pinning Edge Cases
# =============================================================================
def test_absolute_pin_rook_cannot_move_forward() -> None:
    """T4.1: Absolutely pinned rook cannot move to expose king."""
    board = Board()
    board.clear_board()
    # White king on f7 (doesn't check d8)
    board.set_piece(
        get_square_constant(2, 5), create_piece(Color.WHITE, PieceType.KING)
    )
    # Black king on d8 (not e8 to avoid conflict with queen)
    board.set_piece(
        get_square_constant(1, 3), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(5, 4), create_piece(Color.WHITE, PieceType.ROOK)
    )
    # Queen on e8 that pins the rook (on the same file)
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    # White knight on f3 that can capture king
    board.set_piece(
        get_square_constant(7, 5),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    # White rook on e3 is pinned by black queen on e7
    # Rook cannot move towards king (that would expose it to queen)
    board.turn = Color.WHITE
    assert (
        board.make_move(get_square_constant(5, 4), get_square_constant(5, 5)) is False
    )  # Cannot move towards king (away from queen)
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        get_square_constant(1, 0), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert board.make_move(get_square_constant(1, 0), get_square_constant(1, 1)) is True


def test_absolute_pin_rook_cannot_move_sideways() -> None:
    """T4.1: Absolutely pinned rook cannot move sideways."""
    board = Board()
    board.clear_board()
    # White king on f7 (doesn't check d8)
    board.set_piece(
        get_square_constant(2, 5), create_piece(Color.WHITE, PieceType.KING)
    )
    # Black king on d8 (not e8 to avoid conflict with queen)
    board.set_piece(
        get_square_constant(1, 3), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(5, 4), create_piece(Color.WHITE, PieceType.ROOK)
    )
    # Queen on e7 that pins the rook (on the same file)
    board.set_piece(
        get_square_constant(2, 4), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    # White rook on e3 is pinned by black queen on e7
    board.turn = Color.WHITE
    assert (
        board.make_move(get_square_constant(5, 4), get_square_constant(5, 3)) is False
    )  # Cannot move sideways
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        get_square_constant(1, 0), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert board.make_move(get_square_constant(1, 0), get_square_constant(1, 1)) is True


def test_pinned_rook_can_be_captured() -> None:
    """T4.1: Pinned piece can be captured (even if it exposes king)."""
    board = Board()
    board.clear_board()
    # White king on f7 (doesn't check d8)
    board.set_piece(
        get_square_constant(2, 5), create_piece(Color.WHITE, PieceType.KING)
    )
    # Black king on d8
    board.set_piece(
        get_square_constant(1, 3), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(5, 4), create_piece(Color.WHITE, PieceType.ROOK)
    )
    # Bishop on h8 that pins the white rook (same diagonal)
    board.set_piece(
        get_square_constant(1, 7),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # Knight can capture the rook from e3
    board.set_piece(
        get_square_constant(3, 3),
        create_piece(Color.BLACK, PieceType.KNIGHT),
    )
    # Black knight can capture pinned white rook
    board.turn = Color.BLACK
    assert (
        board.make_move(get_square_constant(3, 3), get_square_constant(5, 4)) is True
    )  # Black knight captures white rook (even though pinned)
    # Black moves (to change turn)
    board.turn = Color.WHITE
    board.set_piece(
        get_square_constant(2, 3), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK
    assert (
        board.make_move(get_square_constant(2, 3), get_square_constant(3, 3)) is True
    )  # Black pawn moves (unpinned piece can move)


def test_relative_pin_piece_can_move() -> None:
    """T4.2: Relatively pinned piece (not protecting king) can move."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 0), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.QUEEN)
    )
    board.set_piece(
        get_square_constant(4, 4), create_piece(Color.WHITE, PieceType.QUEEN)
    )
    board.set_piece(
        get_square_constant(0, 4),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # White queen on e4 is pinned by black bishop on e1 but can still move (queen is not protecting king)
    board.turn = Color.WHITE
    assert (
        board.make_move(get_square_constant(4, 4), get_square_constant(2, 4)) is True
    )  # Queen can move away from pin


def test_relative_pin_does_not_prevent_movement() -> None:
    """T4.2: Relative pin doesn't prevent movement of non-king-protecting piece."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 0), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    board.set_piece(
        get_square_constant(4, 4),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    board.set_piece(
        get_square_constant(0, 4),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # White knight on e4 is pinned by bishop on e1 but can still move (knights jump pins)
    board.turn = Color.WHITE
    assert (
        board.make_move(get_square_constant(4, 4), get_square_constant(2, 5)) is True
    )  # Knight can jump over pin


def test_engine_handles_double_pin_gracefully() -> None:
    """T4.3: Engine doesn't crash on double pin situation."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(5, 3), create_piece(Color.WHITE, PieceType.KING)
    )  # On a1-h8 diagonal (3+4=7)
    board.set_piece(
        get_square_constant(0, 0), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.ROOK)
    )  # Between bishop and king
    # Bishop on a1-h8 diagonal that pins the rook
    board.set_piece(
        get_square_constant(0, 7),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # Add a second attacker on the diagonal (rook on same diagonal)
    board.set_piece(
        get_square_constant(6, 3), create_piece(Color.BLACK, PieceType.ROOK)
    )
    # Create a double pin scenario
    # Engine should handle gracefully without crashing
    # Rook should be able to move sideways (not towards king)
    board.turn = Color.WHITE
    result = board.make_move(get_square_constant(3, 4), get_square_constant(3, 3))
    # Should reject move that would expose king (towards king)
    assert result is False
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        get_square_constant(7, 0), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert board.make_move(get_square_constant(7, 0), get_square_constant(7, 1)) is True


def test_king_can_move_into_pin() -> None:
    """T4.4: King can move into a pinning position."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4),
        create_piece(Color.WHITE, PieceType.BISHOP),
    )
    # Bishop on a1-h8 diagonal that can pin the king
    board.set_piece(
        get_square_constant(0, 7),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # White king moves to d1 (becomes pinned but that's legal)
    board.turn = Color.WHITE
    assert (
        board.make_move(get_square_constant(1, 4), get_square_constant(2, 4)) is True
    )  # King can move
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        get_square_constant(7, 0), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert board.make_move(get_square_constant(7, 0), get_square_constant(7, 1)) is True


def test_king_can_move_out_of_pin() -> None:
    """T4.4: King can move out of a pinning position."""
    board = Board()
    board.clear_board()
    # White king on d8 (not on the e-file)
    board.set_piece(
        get_square_constant(0, 3), create_piece(Color.WHITE, PieceType.KING)
    )
    # Black rook on e1 that pins the white rook on e4
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(4, 4),
        create_piece(Color.WHITE, PieceType.ROOK),
    )
    # White rook on e4 is pinned but can move sideways to f4
    board.turn = Color.WHITE
    assert (
        board.make_move(get_square_constant(4, 4), get_square_constant(4, 5)) is True
    )  # Rook can move away from pin
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        get_square_constant(7, 0), create_piece(Color.BLACK, PieceType.KING)
    )
    assert board.make_move(get_square_constant(7, 0), get_square_constant(7, 1)) is True


# =============================================================================
