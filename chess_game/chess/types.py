from dataclasses import dataclass
from typing import Optional

from chess_game.chess.constants import ConstantSquare, Color, PieceType, RowConstant, ColConstant


@dataclass
class Piece:
    color: Color
    kind: PieceType
    _square: Optional[ConstantSquare] = None

    @property
    def row(self) -> Optional[RowConstant]:
        return self._square.row if self._square else None

    @property
    def col(self) -> Optional[ColConstant]:
        return self._square.col if self._square else None

    @property
    def square(self) -> Optional[ConstantSquare]:
        return self._square


@dataclass
class LegalMove:
    start: ConstantSquare
    end: ConstantSquare
    promotion: Optional[PieceType] = None
