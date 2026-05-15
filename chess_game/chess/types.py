"""Chess piece and move data types."""

from dataclasses import dataclass
from typing import Optional

from chess_game.chess.constants import (
    ConstantSquare,
    Color,
    PieceType,
    RowConstant,
    ColConstant,
)


@dataclass
class Piece:
    """A chess piece with its color, kind, and current board square."""

    color: Color
    kind: PieceType
    _square: Optional[ConstantSquare] = None

    @property
    def row(self) -> Optional[RowConstant]:
        """The row constant of the piece's current square, or None if unplaced."""
        return self._square.row if self._square else None

    @property
    def col(self) -> Optional[ColConstant]:
        """The column constant of the piece's current square, or None if unplaced."""
        return self._square.col if self._square else None

    @property
    def square(self) -> Optional[ConstantSquare]:
        """The ConstantSquare of the piece's current position, or None if unplaced."""
        return self._square


@dataclass
class LegalMove:
    """A legal move from one square to another, optionally with promotion."""

    start: ConstantSquare
    end: ConstantSquare
    promotion: Optional[PieceType] = None
