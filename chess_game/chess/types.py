from dataclasses import dataclass
from typing import Optional

from chess_game.constants import ConstantSquare, Color, PieceType


@dataclass(frozen=True)
class Piece:
    color: Color
    kind: PieceType
    _square: ConstantSquare

    @property
    def row(self) -> ConstantSquare:
        return self._square.row

    @property
    def col(self) -> ConstantSquare:
        return self._square.col

    @property
    def square(self) -> ConstantSquare:
        return self._square


@dataclass
class LegalMove:
    start: ConstantSquare
    end: ConstantSquare
    promotion: Optional[PieceType] = None
