from dataclasses import dataclass
from enum import Enum


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
