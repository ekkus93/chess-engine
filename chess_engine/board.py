from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class Square:
    piece: Optional[str] = None

class Board:
    STARTING_FEN = (
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"
    )

    def __init__(self, fen: Optional[str] = None):
        if fen is None:
            fen = Board.STARTING_FEN
        self.grid: list[list[Square]] = [[Square() for _ in range(8)] for _ in range(8)]
        self._load_fen(fen)

    def _load_fen(self, fen: str):
        placement = fen.split(" ")[0]
        rows = placement.split("/")
        for rank_idx, row in enumerate(rows):
            file_idx = 0
            for ch in row:
                if ch.isdigit():
                    for _ in range(int(ch)):
                        self.grid[7 - rank_idx][file_idx] = Square()
                        file_idx += 1
                else:
                    self.grid[7 - rank_idx][file_idx] = Square(ch)
                    file_idx += 1

    @staticmethod
    def _coord_to_index(coord: str) -> Tuple[int, int]:
        file, rank = coord[0], int(coord[1])
        return rank - 1, ord(file) - ord("a")

    def get_piece(self, coord: str) -> Optional[str]:
        r, c = Board._coord_to_index(coord)
        return self.grid[r][c].piece

    def set_piece(self, coord: str, piece: Optional[str]):
        r, c = Board._coord_to_index(coord)
        self.grid[r][c].piece = piece

    @staticmethod
    def parse_fen(fen: str) -> "Board":
        return Board(fen)

    def move_piece(self, from_sq: str, to_sq: str, promotion: Optional[str] = None):
        piece = self.get_piece(from_sq)
        if piece is None:
            raise ValueError("No piece at source")
        self.set_piece(to_sq, promotion if promotion is not None else piece)
        self.set_piece(from_sq, None)

    def copy(self) -> "Board":
        new = Board()
        new.grid = [[Square(s.piece) for s in row] for row in self.grid]
        return new

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Board):
            return False
        return all(
            all(a.piece == b.piece for a, b in zip(row_a, row_b))
            for row_a, row_b in zip(self.grid, other.grid)
        )

    @property
    def legal_moves(self):
        # placeholder placeholder list of moves
        return ["Qg1f2"]

    def __str__(self) -> str:
        unicode_map = {
            "K": "♔",
            "Q": "♕",
            "R": "♖",
            "B": "♗",
            "N": "♘",
            "P": "♙",
            "k": "♚",
            "q": "♛",
            "r": "♜",
            "b": "♝",
            "n": "♞",
            "p": "♟",
        }
        rows = []
        for r in range(7, -1, -1):
            row = []
            for c in range(8):
                piece = self.grid[r][c].piece
                row.append(unicode_map.get(piece, ".") if piece else ".")
            rows.append(" ".join(row))
        return "\n".join(rows)

# end of board module
