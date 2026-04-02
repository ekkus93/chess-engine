"""Piece data class."""

from __future__ import annotations

from typing import Optional

from chess_game.chess.color import Color
from chess_game.constants import PieceType


class Piece:
    """Represents a chess piece."""

    __slots__ = ("color", "kind", "_square")

    def __init__(
        self, color: Color, kind: PieceType, square: Optional["Square"] = None
    ) -> None:
        self.color = color
        self.kind = kind
        self._square = square

    @property
    def square(self) -> Optional["Square"]:
        """Get the piece's square position."""
        return self._square


class Square:
    """Represents a square on the board."""

    __slots__ = ("row", "col")

    def __init__(self, row: int, col: int) -> None:
        self.row = row
        self.col = col

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Square):
            return False
        return self.row == other.row and self.col == other.col

    def __hash__(self) -> int:
        return hash((self.row, self.col))

    def __repr__(self) -> str:
        return f"Square(row={self.row}, col={self.col})"
