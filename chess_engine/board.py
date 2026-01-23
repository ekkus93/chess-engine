# Board representation and state

from typing import List, Optional

class Board:
    PIECE_MAP = {
        "R": "♖",
        "N": "♘",
        "B": "♗",
        "Q": "♕",
        "K": "♔",
        "P": "♙",
        "r": "♜",
        "n": "♞",
        "b": "♝",
        "q": "♛",
        "k": "♚",
        "p": "♟",
    }

    def __init__(self):
        self.board: List[List[Optional[str]]] = self._starting_position()

    def _starting_position(self) -> List[List[Optional[str]]]:
        """Return a 8x8 board with pieces in starting positions."""
        empty = None
        return [
            ["r", "n", "b", "q", "k", "b", "n", "r"],
            ["p"] * 8,
            [empty] * 8,
            [empty] * 8,
            [empty] * 8,
            [empty] * 8,
            ["P"] * 8,
            ["R", "N", "B", "Q", "K", "B", "N", "R"],
        ]

    def _coord_to_index(self, coord: str) -> tuple[int, int]:
        file, rank = coord[0], coord[1]
        col = ord(file) - ord("a")
        row = 8 - int(rank)
        return row, col

    def get_piece(self, coord: str) -> Optional[str]:
        row, col = self._coord_to_index(coord)
        return self.board[row][col]

    def set_piece(self, coord: str, piece: Optional[str]) -> None:
        row, col = self._coord_to_index(coord)
        self.board[row][col] = piece

    def move_piece(self, start: str, end: str) -> None:
        piece = self.get_piece(start)
        if piece is None:
            raise ValueError(f"No piece at {start}")
        self.set_piece(end, piece)
        self.set_piece(start, None)

    def __repr__(self) -> str:
        rows = []
        for row in self.board:
            rows.append(" ".join(self.PIECE_MAP.get(p, ".") for p in row))
        return "\n".join(rows)
