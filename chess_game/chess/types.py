from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class Color(IntEnum):
    WHITE = 1
    BLACK = 0


class PieceType(IntEnum):
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6


@dataclass(frozen=True)
class Piece:
    color: Color
    kind: PieceType


LegalMove = tuple[tuple[int, int], tuple[int, int], Optional[PieceType]]
