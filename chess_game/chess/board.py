from typing import List, Tuple, Optional
from chess_game.chess.types import Piece, Color, PieceType


# Helper function to create pieces
def create_piece(color: Color, piece_type: PieceType) -> Piece:
    return Piece(color=color, kind=piece_type)


class Board:
    board: List[List[Optional[Piece]]]
    turn: Color

    def __init__(self):
        self.board = self.create_board()
        self.turn = Color.WHITE
        self.en_passant_target = None

    def create_board(self) -> List[List[Optional[Piece]]]:
        # Initialize board with pieces
        board = [[None for _ in range(8)] for _ in range(8)]

        # Place white pawns
        for i in range(8):
            board[6][i] = create_piece(Color.WHITE, PieceType.PAWN)

        # Place white back rank
        back_rank = [
            PieceType.ROOK,
            PieceType.KNIGHT,
            PieceType.BISHOP,
            PieceType.QUEEN,
            PieceType.KING,
            PieceType.BISHOP,
            PieceType.KNIGHT,
            PieceType.ROOK,
        ]
        for i in range(8):
            board[7][i] = create_piece(Color.WHITE, back_rank[i])

        # Place black pawns
        for i in range(8):
            board[1][i] = create_piece(Color.BLACK, PieceType.PAWN)

        # Place black back rank
        back_rank_black = [
            PieceType.ROOK,
            PieceType.KNIGHT,
            PieceType.BISHOP,
            PieceType.QUEEN,
            PieceType.KING,
            PieceType.BISHOP,
            PieceType.KNIGHT,
            PieceType.ROOK,
        ]
        for i in range(8):
            board[0][i] = create_piece(Color.BLACK, back_rank_black[i])

        return board

    def is_valid_position(self, row: int, col: int) -> bool:
        """Check if position is valid (within board boundaries)"""
        return 0 <= row < 8 and 0 <= col < 8

    def is_valid_rook_move(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Check if a rook move from start to end is valid."""
        if not self.is_valid_position(start[0], start[1]) or not self.is_valid_position(
            end[0], end[1]
        ):
            return False

        if start[0] == end[0] and start[1] == end[1]:
            return False

        # Check if it's moving in a straight line
        if start[0] != end[0] and start[1] != end[1]:
            return False

        # Check if path is clear
        row_step = 0 if start[0] == end[0] else (1 if end[0] > start[0] else -1)
        col_step = 0 if start[1] == end[1] else (1 if end[1] > start[1] else -1)

        current_row, current_col = start[0] + row_step, start[1] + col_step
        while (current_row, current_col) != end:
            if self.board[current_row][current_col] is not None:
                return False
            current_row += row_step
            current_col += col_step

        return True

    def is_valid_knight_move(
        self, start: Tuple[int, int], end: Tuple[int, int]
    ) -> bool:
        """Check if a knight move from start to end is valid."""
        if not self.is_valid_position(start[0], start[1]) or not self.is_valid_position(
            end[0], end[1]
        ):
            return False

        row_diff = abs(end[0] - start[0])
        col_diff = abs(end[1] - start[1])

        return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)

    def is_valid_bishop_move(
        self, start: Tuple[int, int], end: Tuple[int, int]
    ) -> bool:
        """Check if a bishop move from start to end is valid."""
        if not self.is_valid_position(start[0], start[1]) or not self.is_valid_position(
            end[0], end[1]
        ):
            return False

        if start[0] == end[0] and start[1] == end[1]:
            return False

        # Check if it's moving diagonally
        row_diff = abs(end[0] - start[0])
        col_diff = abs(end[1] - start[1])

        if row_diff != col_diff:
            return False

        # Check if path is clear
        row_step = 1 if end[0] > start[0] else -1
        col_step = 1 if end[1] > start[1] else -1

        current_row, current_col = start[0] + row_step, start[1] + col_step
        while (current_row, current_col) != end:
            if self.board[current_row][current_col] is not None:
                return False
            current_row += row_step
            current_col += col_step

        return True

    def is_valid_queen_move(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Check if a queen move from start to end is valid."""
        return self.is_valid_rook_move(start, end) or self.is_valid_bishop_move(
            start, end
        )

    def is_valid_king_move(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Check if a king move from start to end is valid."""
        if not self.is_valid_position(start[0], start[1]) or not self.is_valid_position(
            end[0], end[1]
        ):
            return False

        row_diff = abs(end[0] - start[0])
        col_diff = abs(end[1] - start[1])

        return row_diff <= 1 and col_diff <= 1

    def is_valid_pawn_move(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Check if a pawn move from start to end is valid."""
        if not self.is_valid_position(start[0], start[1]) or not self.is_valid_position(
            end[0], end[1]
        ):
            return False

        if start[0] == end[0] and start[1] == end[1]:
            return False

        start_piece = self.get_piece(*start)
        if start_piece is None or start_piece.kind != PieceType.PAWN:
            return False

        row_diff = end[0] - start[0]
        col_diff = end[1] - start[1]

        # Check for correct direction
        if start_piece.color == Color.WHITE:
            if row_diff <= 0:
                return False
            direction = 1
        else:
            if row_diff >= 0:
                return False
            direction = -1

        # Check for valid movement
        if col_diff == 0:  # Moving forward
            # Move one square
            if row_diff == direction:
                # Must not be blocked
                if self.board[end[0]][end[1]] is not None:
                    return False
                return True
            # Move two squares
            elif row_diff == 2 * direction:
                # Must be from starting position
                if (start_piece.color == Color.WHITE and start[0] != 6) or (
                    start_piece.color == Color.BLACK and start[0] != 1
                ):
                    return False
                # Must not be blocked
                if self.board[end[0]][end[1]] is not None:
                    return False
                # Middle square must not be blocked
                if start_piece.color == Color.WHITE:
                    if self.board[start[0] - direction][start[1]] is not None:
                        return False
                else:
                    if self.board[start[0] - direction][start[1]] is not None:
                        return False
                return True
            else:
                return False
        elif abs(col_diff) == 1 and row_diff == direction:  # Capturing diagonally
            # Must be capturing
            if self.board[end[0]][end[1]] is None:
                # Check for en passant capture
                if (
                    self.en_passant_target is not None
                    and end[0] == self.en_passant_target[0]
                    and end[1] == self.en_passant_target[1]
                ):
                    return True
                return False
            return True
        else:
            return False

    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        """Get piece at position (row, col)"""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None

    def is_empty(self, row: int, col: int) -> bool:
        """Check if position (row, col) is empty"""
        return self.get_piece(row, col) is None

    def get_color_at(self, row: int, col: int) -> Optional[Color]:
        """Get color of piece at position (row, col)"""
        piece = self.get_piece(row, col)
        return piece.color if piece else None

    def is_on_board(self, row: int, col: int) -> bool:
        """Check if position (row, col) is within board bounds"""
        return 0 <= row < 8 and 0 <= col < 8

    def get_piece_type_at(self, row: int, col: int) -> Optional[PieceType]:
        """Get piece type at position (row, col)"""
        piece = self.get_piece(row, col)
        return piece.kind if piece else None

    def is_same_color(self, row1: int, col1: int, row2: int, col2: int) -> bool:
        """Check if pieces at two positions have the same color"""
        piece1 = self.get_piece(row1, col1)
        piece2 = self.get_piece(row2, col2)

        if piece1 is None or piece2 is None:
            return False

        return piece1.color == piece2.color

    def is_opponent(self, row1: int, col1: int, row2: int, col2: int) -> bool:
        """Check if pieces at two positions are opponents (different colors)"""
        piece1 = self.get_piece(row1, col1)
        piece2 = self.get_piece(row2, col2)

        if piece1 is None or piece2 is None:
            return False

        return piece1.color != piece2.color

    def make_move(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> bool:
        """Make a move and return True if successful"""
        # Basic validation
        if not (0 <= start_pos[0] < 8 and 0 <= start_pos[1] < 8):
            return False
        if not (0 <= end_pos[0] < 8 and 0 <= end_pos[1] < 8):
            return False

        start_piece = self.get_piece(*start_pos)
        if start_piece is None:
            return False

        # Check turn - only allow moving own pieces
        if start_piece.color != self.turn:
            return False

        # For now, just perform the move
        # In a complete implementation, this would validate legal moves
        self.board[end_pos[0]][end_pos[1]] = start_piece
        self.board[start_pos[0]][start_pos[1]] = None

        # Switch turn
        self.turn = Color.BLACK if self.turn == Color.WHITE else Color.WHITE

        return True

    def display(self):
        """Display the board"""
        print("  a b c d e f g h")
        for i, row in enumerate(self.board):
            rank = 8 - i
            print(f"{rank} ", end="")
            for piece in row:
                if piece is None:
                    print(". ", end="")
                else:
                    # Show piece abbreviation
                    abbrev = piece.kind.value[0].upper()
                    if piece.color == Color.BLACK:
                        abbrev = abbrev.lower()
                    print(f"{abbrev} ", end="")
            print(f"{rank}")
        print("  a b c d e f g h")
        print(f"Turn: {self.turn.value}")
        if not (0 <= end_pos[0] < 8 and 0 <= end_pos[1] < 8):
            return False

        start_piece = self.get_piece(*start_pos)
        if start_piece is None:
            return False

        # Check turn - only allow moving own pieces
        if start_piece.color != self.turn:
            return False

        # For now, just perform the move
        # In a complete implementation, this would validate legal moves
        self.board[end_pos[0]][end_pos[1]] = start_piece
        self.board[start_pos[0]][start_pos[1]] = None

        # Switch turn
        self.turn = Color.BLACK if self.turn == Color.WHITE else Color.WHITE

        return True

    def display(self):
        """Display the board"""
        print("  a b c d e f g h")
        for i, row in enumerate(self.board):
            rank = 8 - i
            print(f"{rank} ", end="")
            for piece in row:
                if piece is None:
                    print(". ", end="")
                else:
                    # Show piece abbreviation
                    abbrev = piece.kind.value[0].upper()
                    if piece.color == Color.BLACK:
                        abbrev = abbrev.lower()
                    print(f"{abbrev} ", end="")
            print(f"{rank}")
        print("  a b c d e f g h")
        print(f"Turn: {self.turn.value}")
        if not (0 <= end_pos[0] < 8 and 0 <= end_pos[1] < 8):
            return False

        start_piece = self.get_piece(*start_pos)
        if start_piece is None:
            return False

        # Check turn
        if start_piece.color != self.turn:
            return False

        # Simple validation for demo - actual implementation will be more complex
        # This is just a placeholder that returns True for valid positions
        self.board[end_pos[0]][end_pos[1]] = start_piece
        self.board[start_pos[0]][start_pos[1]] = None

        # Switch turn
        self.turn = Color.BLACK if self.turn == Color.WHITE else Color.WHITE

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
