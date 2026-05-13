"""Helper functions for tests."""

from chess_game.chess.board import Board, ConstantSquare
from chess_game.chess.coords import algebraic_to_index
from chess_game.chess.types import Color, PieceType


def sq(name: str) -> ConstantSquare:
    """Convert algebraic notation (e.g. 'e4') to a ConstantSquare."""
    return algebraic_to_index(name)


def assert_piece(
    board: Board,
    square_name: str,
    color: Color,
    kind: PieceType,
) -> None:
    """Assert that the given square contains a piece of the given color and type."""
    square = algebraic_to_index(square_name)
    piece = board.get_piece(square)
    assert piece is not None, f"Expected piece at {square_name}, found empty square"
    assert piece.color == color, (
        f"Expected {color.name} piece at {square_name}, "
        f"got {piece.color.name}"
    )
    assert piece.kind == kind, (
        f"Expected {kind.name} at {square_name}, got {piece.kind.name}"
    )


def assert_empty(board: Board, square_name: str) -> None:
    """Assert that the given square is empty."""
    square = algebraic_to_index(square_name)
    piece = board.get_piece(square)
    assert piece is None, (
        f"Expected empty square at {square_name}, "
        f"found {piece.color.name} {piece.kind.name}"
    )
