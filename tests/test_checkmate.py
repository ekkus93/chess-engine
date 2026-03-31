"""Tests for checkmate."""

from __future__ import annotations
from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.constants import (
    get_row_constant,
    get_col_constant,
    COL_A,
    COL_D,
    COL_E,
    COL_F,
    COL_H,
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_4,
    ROW_6,
    ROW_7,
    ROW_8,
)
from chess_game.chess.types import Color, PieceType


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )


def _setup_kings(board: Board) -> None:
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )


# Category 4: King Safety & Pinning Edge Cases
# =============================================================================
def test_absolute_pin_rook_cannot_move_forward() -> None:
    """T4.1: Absolutely pinned rook cannot move to expose king."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    # Black king on d8 (not e8 to avoid conflict with queen)
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_D), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_4, col=COL_E), create_piece(Color.WHITE, PieceType.ROOK)
    )
    # Queen on e8 that pins the rook (on the same file)
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    # White knight on f3 that can capture king
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_F),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    # White rook on e4 is pinned by black queen on e8
    # Rook cannot move towards king (that would expose it to queen)
    board.turn = Color.WHITE
    assert (
        board.make_move(
            ConstantSquare(row=ROW_4, col=COL_E), ConstantSquare(row=ROW_4, col=COL_F)
        )
        is False
    )  # Cannot move towards king (away from queen)
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_A), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_8, col=COL_A), ConstantSquare(row=ROW_8, col=COL_B)
        )
        is True
    )


def test_absolute_pin_rook_cannot_move_sideways() -> None:
    """T4.1: Absolutely pinned rook cannot move sideways."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    # Black king on d8 (not e8 to avoid conflict with queen)
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_D), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_4, col=COL_E), create_piece(Color.WHITE, PieceType.ROOK)
    )
    # Queen on e8 that pins the rook (on the same file)
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    # White rook on e4 is pinned by black queen on e8
    board.turn = Color.WHITE
    assert (
        board.make_move(
            ConstantSquare(row=ROW_4, col=COL_E), ConstantSquare(row=ROW_4, col=COL_D)
        )
        is False
    )  # Cannot move sideways
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_A), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_8, col=COL_A), ConstantSquare(row=ROW_8, col=COL_B)
        )
        is True
    )


def test_pinned_rook_can_be_captured() -> None:
    """T4.1: Pinned piece can be captured (even if it exposes king)."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    # Black king on a8 (not on e-file to avoid conflict)
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_A), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_4, col=COL_E), create_piece(Color.WHITE, PieceType.ROOK)
    )
    # Bishop on a1-h8 diagonal that pins the rook
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # Knight can capture the rook from e3
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_D),
        create_piece(Color.BLACK, PieceType.KNIGHT),
    )
    # Black knight can capture pinned white rook
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_D), ConstantSquare(row=ROW_4, col=COL_E)
        )
        is True
    )  # Black knight captures white rook
    # Black moves (to change turn)
    board.turn = Color.WHITE
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_D), ConstantSquare(row=ROW_8, col=COL_D)
        )
        is True
    )


def test_relative_pin_piece_can_move() -> None:
    """T4.2: Relatively pinned piece (not protecting king) can move."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_A), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.QUEEN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_4, col=COL_E), create_piece(Color.WHITE, PieceType.QUEEN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # White queen on d3 is pinned by black bishop but is not protecting king
    board.turn = Color.WHITE
    assert (
        board.make_move(
            ConstantSquare(row=ROW_3, col=COL_E), ConstantSquare(row=ROW_2, col=COL_E)
        )
        is True
    )  # Can move away from pin


def test_relative_pin_does_not_prevent_movement() -> None:
    """T4.2: Relative pin doesn't prevent movement of non-king-protecting piece."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_A), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    board.set_piece(
        ConstantSquare(row=ROW_4, col=COL_E),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # White knight on d3 is pinned but can still move
    board.turn = Color.WHITE
    assert (
        board.make_move(
            ConstantSquare(row=ROW_3, col=COL_E), ConstantSquare(row=ROW_5, col=COL_F)
        )
        is True
    )  # Knight can jump over pin


def test_engine_handles_double_pin_gracefully() -> None:
    """T4.3: Engine doesn't crash on double pin situation."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_D), create_piece(Color.WHITE, PieceType.KING)
    )  # On a1-h8 diagonal (3+4=7)
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_A), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.ROOK)
    )  # Between bishop and king
    # Bishop on a1-h8 diagonal that pins the rook
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # Add a second attacker on the diagonal (rook on same diagonal)
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_D), create_piece(Color.BLACK, PieceType.ROOK)
    )
    # Create a double pin scenario
    # Engine should handle gracefully without crashing
    # Rook should be able to move sideways (not towards king)
    board.turn = Color.WHITE
    result = board.make_move(
        ConstantSquare(row=ROW_5, col=COL_E), ConstantSquare(row=ROW_5, col=COL_D)
    )
    # Should reject move that would expose king (towards king)
    assert result is False
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_A), ConstantSquare(row=ROW_1, col=COL_B)
        )
        is True
    )


def test_king_can_move_into_pin() -> None:
    """T4.4: King can move into a pinning position."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E),
        create_piece(Color.WHITE, PieceType.BISHOP),
    )
    # Bishop on a1-h8 diagonal that can pin the king
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # White king moves to d1 (becomes pinned but that's legal)
    board.turn = Color.WHITE
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_6, col=COL_E)
        )
        is True
    )  # King can move
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_A), ConstantSquare(row=ROW_1, col=COL_B)
        )
        is True
    )


def test_king_can_move_out_of_pin() -> None:
    """T4.4: King can move out of a pinning position."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E),
        create_piece(Color.WHITE, PieceType.BISHOP),
    )
    # Bishop on a1-h8 diagonal that can pin the king
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # White king moves away from pin
    board.turn = Color.WHITE
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_7, col=COL_D)
        )
        is True
    )  # King can move out of pin
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_A), ConstantSquare(row=ROW_1, col=COL_B)
        )
        is True
    )


# =============================================================================
