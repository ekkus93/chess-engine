from __future__ import annotations

from collections.abc import Callable

import pytest

from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType


@pytest.fixture
def record_xml_attribute() -> Callable[[str, object], None]:
    """Provide a stable no-op xml attribute recorder for local test runs.

    Some globally installed plugins request the experimental pytest fixture of the
    same name. Defining this local fixture avoids the experimental API warning
    without suppressing warnings globally.
    """

    def _record(_name: str, _value: object) -> None:
        return None

    return _record


def clear_board(board: Board) -> None:
    """Clear all pieces from a board for focused rule tests."""
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)


@pytest.fixture
def empty_board() -> Board:
    """Provide an empty board (no kings) for piece-pattern tests."""
    board = Board()
    clear_board(board)
    return board


@pytest.fixture
def board_with_kings() -> Board:
    """Provide an otherwise-empty board with both kings placed legally."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    return board


@pytest.fixture
def board_with_material() -> Board:
    """Provide a board with material for evaluation testing."""
    board = Board()
    # Clear and set up a simple position: White has queen vs Black knight
    clear_board(board)
    # Set up kings (required by board state but not used in evaluation)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    # Add material: White queen at d1, Black knight at f6
    board.set_piece(3, 3, create_piece(Color.WHITE, PieceType.QUEEN))  # d4 square (rank 5 = row 3)
    board.set_piece(0, 5, create_piece(Color.BLACK, PieceType.KNIGHT))  # e1 rank (Black knight at back rank edge)
    return board


@pytest.fixture
def simple_opening_position() -> Board:
    """Provide a standard Italian game opening position for AI testing."""
    board = Board()
    # Make some standard opening moves to set up a position
    board.make_move((7, 2), (5, 3))  # e4
    board.make_move((0, 1), (2, 2))  # Nc6 (Black knight)
    board.make_move((7, 4), (6, 5))  # Bc4 (White bishop to center)
    board.make_move((0, 8), (2, 7))  # ...e6
    return board


def is_piece_in_position(piece_type: PieceType, row: int, col: int) -> bool:
    """Check if a piece of given type exists at position."""
    piece = Board().get_piece(row, col)
    return piece is not None and piece.kind == piece_type
