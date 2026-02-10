# Board representation and state

from typing import List, Optional, Dict


class Board:
    """Represents the chess board & state."""

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
        self.board: List[List[Optional[str]]] = self._starting_position_fen(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
        )
        self.castling_rights: Dict[str, bool] = {"K": True, "Q": True, "k": True, "q": True}
        self.ep_square: Optional[str] = None

    def _starting_position_fen(self, fen: str) -> List[List[Optional[str]]]:
        rows: List[List[Optional[str]]] = []
        fen_rows = fen.split(" ")[0].split("/")
        for fen_row in fen_rows:
            row: List[Optional[str]] = []
            for char in fen_row:
                if char.isdigit():
                    row.extend([None] * int(char))
                else:
                    row.append(char)
            rows.append(row)
        return rows

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

    def apply_move(self, move: "Move") -> None:
        from .move import Move

        piece = self.get_piece(move.start)
        if piece is None:
            raise ValueError(f"No piece at {move.start}")
        self.set_piece(move.end, piece)
        self.set_piece(move.start, None)
        # Update castling rights
        if piece in ("K", "k"):
            side = "K" if piece == "K" else "k"
            self.castling_rights["K"] = False
            self.castling_rights["Q"] = False
            self.castling_rights["k"] = False
            self.castling_rights["q"] = False
        if piece in ("R", "r"):
            if move.start == "h1":
                self.castling_rights["K"] = False
            elif move.start == "a1":
                self.castling_rights["Q"] = False
            elif move.start == "h8":
                self.castling_rights["k"] = False
            elif move.start == "a8":
                self.castling_rights["q"] = False
        # En‑passant square handling
        self.ep_square = None
        if piece.upper() == "P":
            start_row, _ = self._coord_to_index(move.start)
            end_row, _ = self._coord_to_index(move.end)
            if abs(start_row - end_row) == 2:
                file = move.start[0]
                between_rank = str((int(move.start[1]) + int(move.end[1])) // 2)
                self.ep_square = file + between_rank

    def in_check(self, color: str) -> bool:
        return False

    def __repr__(self) -> str:
        rows: List[str] = []
        for row in self.board:
            rows.append(" ".join(self.PIECE_MAP.get(p, ".") for p in row))
        return "\n".join(rows)

    # --- Immutable helpers ---
    def copy(self) -> "Board":
        new_board = Board()
        new_board.board = [row[:] for row in self.board]
        new_board.castling_rights = self.castling_rights.copy()
        new_board.ep_square = self.ep_square
        return new_board

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Board):
            return False
        return (
            self.board == other.board
            and self.castling_rights == other.castling_rights
            and self.ep_square == other.ep_square
        )

    def __hash__(self) -> int:
        return hash(
            (
                tuple(tuple(row) for row in self.board),
                frozenset(self.castling_rights.items()),
                self.ep_square,
            )
        )
