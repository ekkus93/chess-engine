from dataclasses import dataclass
from typing import Optional

from chess_game.chess.coords import algebraic_to_index
from chess_game.chess.types import PieceType


@dataclass(frozen=True)
class Move:
    start: tuple[int, int]  # (row, col)
    end: tuple[int, int]  # (row, col)
    promotion: Optional[PieceType] = None


def parse_move_notation(move_str: str) -> Move:
    """Parse coordinate notation like e2e4 or e7e8q into a Move.

    Accepted promotion suffix letters are: q, r, b, n.
    """
    if len(move_str) not in {4, 5}:
        raise ValueError(
            f"Invalid move format: {move_str}. Expected e2e4 or e7e8q"
        )

    start = algebraic_to_index(move_str[0:2])
    end = algebraic_to_index(move_str[2:4])

    promotion: Optional[PieceType] = None
    if len(move_str) == 5:
        promo_map = {
            "q": PieceType.QUEEN,
            "r": PieceType.ROOK,
            "b": PieceType.BISHOP,
            "n": PieceType.KNIGHT,
        }
        promo_char = move_str[4].lower()
        if promo_char not in promo_map:
            raise ValueError(
                f"Invalid promotion piece '{move_str[4]}'. Use q, r, b, or n."
            )
        promotion = promo_map[promo_char]

    return Move(start=start, end=end, promotion=promotion)
