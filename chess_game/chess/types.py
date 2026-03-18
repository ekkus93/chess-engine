from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Color(Enum):
    WHITE = "white"
    BLACK = "black"


class PieceType(Enum):
    PAWN = "pawn"
    KNIGHT = "knight"
    BISHOP = "bishop"
    ROOK = "rook"
    QUEEN = "queen"
    KING = "king"


@dataclass(frozen=True)
class Piece:
    color: Color
    kind: PieceType


LegalMove = tuple[tuple[int, int], tuple[int, int], Optional[PieceType]]
