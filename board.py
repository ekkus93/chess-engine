from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class Square:
    piece: Optional[str] = None

class Board:
    def __init__(self):
        self.grid: list[list[Square]] = [[Square() for _ in range(8)] for _ in range(8)]

    @staticmethod
    def _coord_to_index(coord: str) -> Tuple[int, int]:
        file, rank = coord[0], coord[1]
        return int(rank) - 1, ord(file) - ord("a")

    def get_piece(self, coord: str) -> Optional[str]:
        r, c = self._coord_to_index(coord)
        return self.grid[r][c].piece

    def set_piece(self, coord: str, piece: Optional[str]):
        r, c = self._coord_to_index(coord)
        self.grid[r][c].piece = piece

    @staticmethod
    def from_fen(fen: str) -> "Board":
        board = Board()
        placement = fen.split(" ")[0]
        rows = placement.split("/")
        for r, row in enumerate(rows):
            c = 0
            for ch in row:
                if ch.isdigit():
                    for _ in range(int(ch)):
                        board.grid[r][c] = Square()
                        c += 1
                else:
                    board.grid[r][c] = Square(ch)
                    c += 1
        return board

    def parse_fen(self, fen: str) -> "Board":
        return Board.from_fen(fen)

    def move_piece(self, from_sq: str, to_sq: str, promotion: Optional[str] = None):
        piece = self.get_piece(from_sq)
        if piece is None:
            raise ValueError("No piece at source")
        self.set_piece(to_sq, promotion if promotion else piece)
        self.set_piece(from_sq, None)

    def copy(self) -> "Board":
        new = Board()
        new.grid = [[Square(s.piece) for s in row] for row in self.grid]
        return new

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Board):
            return False
        return all(all(a.piece == b.piece for a, b in zip(row_a, row_b)) for row_a, row_b in zip(self.grid, other.grid))

    def __str__(self) -> str:
        rows = []
        for row in self.grid:
            rows.append("".join([s.piece if s.piece else "." for s in row]))
        return " ".join(rows)

# End of board module
