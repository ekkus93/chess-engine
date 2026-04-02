from __future__ import annotations
from collections.abc import Callable
import pytest
from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.chess.constants import (
    get_row_constant,
    get_col_constant,
    get_square_constant,
    COL_A,
    COL_B,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_H,
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_5,
    ROW_6,
    ROW_7,
    ROW_8,
)
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


@pytest.fixture
def empty_board() -> Board:
    """Provide an empty board (no pieces, no kings) for isolated tests."""
    board = Board()
    board.clear_board()
    return board


@pytest.fixture
def simple_opening_position() -> Board:
    """Provide a standard Italian game opening position for AI testing."""
    board = Board()
    # Make some standard opening moves to set up a position
    board.make_move(
        ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_3, col=COL_D)
    )  # e4
    board.make_move(
        ConstantSquare(row=ROW_8, col=COL_B), ConstantSquare(row=ROW_6, col=COL_C)
    )  # Nc6 (Black knight)
    board.make_move(
        ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_3, col=COL_F)
    )  # Bc4 (White bishop to center)
    board.make_move(
        ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_5, col=COL_H)
    )  # ...e6
    return board


@pytest.fixture
def board_with_kings() -> Board:
    """Provide an otherwise-empty board with both kings placed legally."""
    board = Board()
    board.clear_board()
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    return board


@pytest.fixture
def board_with_material() -> Board:
    """Provide a board with material for evaluation testing."""
    board = Board()
    # Clear and set up a simple position: White has queen vs Black knight
    board.clear_board()
    # Set up kings (required by board state but not used in evaluation)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    # Add material: White queen at d1, Black knight at f8 (worse position)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_D), create_piece(Color.WHITE, PieceType.QUEEN)
    )  # d1 square
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_F),
        create_piece(Color.BLACK, PieceType.KNIGHT),
    )  # f8 square (rank 8 = row 0, worse position for knights)
    return board


@pytest.fixture
def simple_opening_position() -> Board:
    """Provide a standard Italian game opening position for AI testing."""
    board = Board()
    # Make some standard opening moves to set up a position
    board.make_move(
        ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_3, col=COL_D)
    )  # e4
    board.make_move(
        ConstantSquare(row=ROW_8, col=COL_B), ConstantSquare(row=ROW_6, col=COL_C)
    )  # Nc6 (Black knight)
    board.make_move(
        ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_3, col=COL_F)
    )  # Bc4 (White bishop to center)
    board.make_move(
        ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_5, col=COL_H)
    )  # ...e6
    return board


def is_piece_in_position(piece_type: PieceType, square: ConstantSquare) -> bool:
    """Check if a piece of given type exists at position."""
    piece = Board().get_piece(square)
    return piece is not None and piece.kind == piece_type
