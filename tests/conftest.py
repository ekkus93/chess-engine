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
