from typing import List, Tuple, Optional


class Board:
    board: List[List[str]]
    turn: str

    def __init__(self):
        self.board = self.create_board()
        self.turn = "white"

    def create_board(self) -> List[List[str]]:
        # Initialize board with pieces
        board = [["" for _ in range(8)] for _ in range(8)]

        # Place white pawns
        for i in range(8):
            board[1][i] = "Pawn"

        # Place white back rank
        back_rank = [
            "Rook",
            "Knight",
            "Bishop",
            "Queen",
            "King",
            "Bishop",
            "Knight",
            "Rook",
        ]
        for i in range(8):
            board[0][i] = back_rank[i]

        # Place black pawns
        for i in range(8):
            board[6][i] = "Pawn"

        # Place black back rank
        back_rank_black = [
            "Rook",
            "Knight",
            "Bishop",
            "Queen",
            "King",
            "Bishop",
            "Knight",
            "Rook",
        ]
        for i in range(8):
            board[7][i] = back_rank_black[i]

        return board

    def make_move(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        piece = self.board[start[0]][start[1]]
        # Check if it's a valid move for this piece type
        if piece == "Rook":
            if not self.move_rook(start, end):
                return False
        elif piece == "Knight":
            if not self.move_knight(start, end):
                return False
        elif piece == "Bishop":
            if not self.move_bishop(start, end):
                return False
        elif piece == "Queen":
            if not self.move_queen(start, end):
                return False
        elif piece == "King":
            if not self.move_king(start, end):
                return False
        elif piece == "Pawn":
            if not self.move_pawn(start, end):
                return False

        self.board[end[0]][end[1]] = piece
        self.board[start[0]][start[1]] = ""
        self.turn = "black" if self.turn == "white" else "white"
        return True

    def move_rook(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        row_from, col_from = start
        row_to, col_to = end
        # Check if path is clear
        if row_from == row_to:
            step = 1 if col_to > col_from else -1
            for i in range(1, abs(col_to - col_from)):
                if self.board[row_from][col_from + i * step] != "":
                    return False
        elif col_from == col_to:
            step = 1 if row_to > row_from else -1
            for i in range(1, abs(row_to - row_from)):
                if self.board[row_from + i * step][col_from] != "":
                    return False
        else:
            return False
        return True

    def move_knight(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        row_from, col_from = start
        row_to, col_to = end
        # Knight moves in L-shape
        delta_row = abs(row_to - row_from)
        delta_col = abs(col_to - col_from)
        if (delta_row == 2 and delta_col == 1) or (delta_row == 1 and delta_col == 2):
            return True
        return False

    def move_bishop(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        row_from, col_from = start
        row_to, col_to = end
        delta_row = abs(row_to - row_from)
        delta_col = abs(col_to - col_from)
        if delta_row == delta_col:
            step_row = 1 if row_to > row_from else -1
            step_col = 1 if col_to > col_from else -1
            for i in range(1, delta_row):
                if self.board[row_from + i * step_row][col_from + i * step_col] != "":
                    return False
            return True
        return False

    def move_queen(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        # Queen can move like a rook or bishop
        if self.move_rook(start, end) or self.move_bishop(start, end):
            return True
        return False

    def move_king(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        row_from, col_from = start
        row_to, col_to = end
        delta_row = abs(row_to - row_from)
        delta_col = abs(col_to - col_from)
        if delta_row <= 1 and delta_col <= 1:
            return True
        return False

    def move_pawn(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        row_from, col_from = start
        row_to, col_to = end
        piece = self.board[row_from][col_from]
        if piece == "Pawn" and self.turn == "white":
            # White pawn moves
            if col_to == col_from:
                if row_to == row_from + 1 and self.board[row_to][col_to] == "":
                    return True
                elif (
                    row_to == row_from + 2
                    and row_from == 1
                    and self.board[row_to][col_to] == ""
                ):
                    return True
            elif col_to == col_from + 1 or col_to == col_from - 1:
                if row_to == row_from + 1 and self.board[row_to][col_to] != "":
                    return True
            return False
        elif piece == "Pawn" and self.turn == "black":
            # Black pawn moves
            if col_to == col_from:
                if row_to == row_from - 1 and self.board[row_to][col_to] == "":
                    return True
                elif (
                    row_to == row_from - 2
                    and row_from == 6
                    and self.board[row_to][col_to] == ""
                ):
                    return True
            elif col_to == col_from + 1 or col_to == col_from - 1:
                if row_to == row_from - 1 and self.board[row_to][col_to] != "":
                    return True
            return False
        return False

    def __str__(self) -> str:
        return "\n".join([" ".join(row) for row in self.board])

    def display(self) -> None:
        # Display the board with row and column labels
        # Columns a-h
        print("  a b c d e f g h")
        for i, row in enumerate(reversed(self.board)):
            row_str = f"{i + 1} " + " ".join(row)
            print(row_str)
        print(f"\nTurn: {self.turn}")
