"""Piece data class."""

from __future__ import annotations

from typing import Optional

from chess_game.chess.color import Color
from chess_game.chess.constants import PieceType, ConstantSquare


class Piece:
    """Represents a chess piece."""

    __slots__ = ("color", "kind", "_square")

    def __init__(
        self, color: Color, kind: PieceType, square: Optional[ConstantSquare] = None
    ) -> None:
        self.color = color
        self.kind = kind
        self._square = square

    def __eq__(self, other):
        if isinstance(other, Piece):
            return (
                self.color == other.color
                and self.kind == other.kind
                and self._square == other._square
            )
        return False

    def __hash__(self):
        return hash((self.color, self.kind, self._square))

    @property
    def square(self) -> Optional[ConstantSquare]:
        """Get the piece's square position."""
        return self._square
