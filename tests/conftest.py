from __future__ import annotations

from collections.abc import Callable

import pytest

from chess_game.chess.board import Board, create_piece
from chess_game.chess.coords import algebraic_to_index
from chess_game.chess.types import Color, PieceType


@pytest.fixture
def record_xml_attribute() -> Callable[[str, object], None]:
    """Provide a stable no-op xml attribute recorder for local test runs."""

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
    """Provide a standard opening position for testing.

    Canonical coordinates: row 0 = rank 8, row 7 = rank 1.
    """
    board = Board()
    # e2e4 (White pawn from row 6 to row 4)
    board.make_move(
        algebraic_to_index("e2"), algebraic_to_index("e4")
    )
    # e7e5 (Black pawn from row 1 to row 3)
    board.make_move(
        algebraic_to_index("e7"), algebraic_to_index("e5")
    )
    # g1f3 (White knight)
    board.make_move(
        algebraic_to_index("g1"), algebraic_to_index("f3")
    )
    # b8c6 (Black knight)
    board.make_move(
        algebraic_to_index("b8"), algebraic_to_index("c6")
    )
    return board


@pytest.fixture
def board_with_kings() -> Board:
    """Provide an otherwise-empty board with both kings placed legally.

    White king on e1 (row 7), black king on e8 (row 0).
    """
    board = Board()
    board.clear_board()
    board.set_piece(
        algebraic_to_index("e1"), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        algebraic_to_index("e8"), create_piece(Color.BLACK, PieceType.KING)
    )
    return board


@pytest.fixture
def board_with_material() -> Board:
    """Provide a board with material for evaluation testing."""
    board = Board()
    board.clear_board()
    board.set_piece(
        algebraic_to_index("e1"), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        algebraic_to_index("e8"), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        algebraic_to_index("d1"), create_piece(Color.WHITE, PieceType.QUEEN)
    )
    board.set_piece(
        algebraic_to_index("f8"), create_piece(Color.BLACK, PieceType.KNIGHT)
    )
    return board
