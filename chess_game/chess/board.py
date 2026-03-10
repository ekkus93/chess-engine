from __future__ import annotations

from typing import Optional

from chess_game.chess.types import Color, Piece, PieceType

Square = tuple[int, int]


def create_piece(color: Color, piece_type: PieceType) -> Piece:
    """Create a typed chess piece."""
    return Piece(color=color, kind=piece_type)


class Board:
    board: list[list[Optional[Piece]]]
    turn: Color
    en_passant_target: Optional[Square]

    def __init__(self) -> None:
        self.board = self.create_board()
        self.turn = Color.WHITE
        self.en_passant_target = None

    def create_board(self) -> list[list[Optional[Piece]]]:
        board: list[list[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
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

        for col, piece_type in enumerate(back_rank):
            board[7][col] = create_piece(Color.WHITE, piece_type)
            board[6][col] = create_piece(Color.WHITE, PieceType.PAWN)
            board[1][col] = create_piece(Color.BLACK, PieceType.PAWN)
            board[0][col] = create_piece(Color.BLACK, piece_type)

        return board

    def is_valid_position(self, row: int, col: int) -> bool:
        return 0 <= row < 8 and 0 <= col < 8

    def is_on_board(self, row: int, col: int) -> bool:
        return self.is_valid_position(row, col)

    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        if not self.is_valid_position(row, col):
            return None
        return self.board[row][col]

    def set_piece(self, row: int, col: int, piece: Optional[Piece]) -> None:
        if not self.is_valid_position(row, col):
            raise ValueError(f"Invalid position ({row}, {col})")
        self.board[row][col] = piece

    def clear_square(self, row: int, col: int) -> None:
        self.set_piece(row, col, None)

    def is_empty(self, row: int, col: int) -> bool:
        return self.get_piece(row, col) is None

    def get_color_at(self, row: int, col: int) -> Optional[Color]:
        piece = self.get_piece(row, col)
        return piece.color if piece else None

    def get_piece_type_at(self, row: int, col: int) -> Optional[PieceType]:
        piece = self.get_piece(row, col)
        return piece.kind if piece else None

    def is_same_color(self, row1: int, col1: int, row2: int, col2: int) -> bool:
        piece1 = self.get_piece(row1, col1)
        piece2 = self.get_piece(row2, col2)
        return piece1 is not None and piece2 is not None and piece1.color == piece2.color

    def is_opponent(self, row1: int, col1: int, row2: int, col2: int) -> bool:
        piece1 = self.get_piece(row1, col1)
        piece2 = self.get_piece(row2, col2)
        return piece1 is not None and piece2 is not None and piece1.color != piece2.color

    def _destination_occupiable(self, mover: Piece, end: Square) -> bool:
        end_piece = self.get_piece(*end)
        return end_piece is None or end_piece.color != mover.color

    def _path_is_clear(self, start: Square, end: Square) -> bool:
        row_diff = end[0] - start[0]
        col_diff = end[1] - start[1]

        step_row = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
        step_col = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)

        current_row = start[0] + step_row
        current_col = start[1] + step_col
        while (current_row, current_col) != end:
            if self.get_piece(current_row, current_col) is not None:
                return False
            current_row += step_row
            current_col += step_col
        return True

    def is_valid_rook_move(self, start: Square, end: Square) -> bool:
        piece = self.get_piece(*start)
        if piece is None or piece.kind != PieceType.ROOK:
            return False
        if not self.is_valid_position(*end) or start == end:
            return False
        if start[0] != end[0] and start[1] != end[1]:
            return False
        if not self._path_is_clear(start, end):
            return False
        return self._destination_occupiable(piece, end)

    def is_valid_bishop_move(self, start: Square, end: Square) -> bool:
        piece = self.get_piece(*start)
        if piece is None or piece.kind != PieceType.BISHOP:
            return False
        if not self.is_valid_position(*end) or start == end:
            return False
        if abs(end[0] - start[0]) != abs(end[1] - start[1]):
            return False
        if not self._path_is_clear(start, end):
            return False
        return self._destination_occupiable(piece, end)

    def is_valid_queen_move(self, start: Square, end: Square) -> bool:
        piece = self.get_piece(*start)
        if piece is None or piece.kind != PieceType.QUEEN:
            return False
        if not self.is_valid_position(*end) or start == end:
            return False

        is_straight = start[0] == end[0] or start[1] == end[1]
        is_diagonal = abs(end[0] - start[0]) == abs(end[1] - start[1])
        if not (is_straight or is_diagonal):
            return False
        if not self._path_is_clear(start, end):
            return False
        return self._destination_occupiable(piece, end)

    def is_valid_knight_move(self, start: Square, end: Square) -> bool:
        piece = self.get_piece(*start)
        if piece is None or piece.kind != PieceType.KNIGHT:
            return False
        if not self.is_valid_position(*end) or start == end:
            return False

        row_diff = abs(end[0] - start[0])
        col_diff = abs(end[1] - start[1])
        if (row_diff, col_diff) not in {(2, 1), (1, 2)}:
            return False
        return self._destination_occupiable(piece, end)

    def is_valid_king_move(self, start: Square, end: Square) -> bool:
        piece = self.get_piece(*start)
        if piece is None or piece.kind != PieceType.KING:
            return False
        if not self.is_valid_position(*end) or start == end:
            return False

        row_diff = abs(end[0] - start[0])
        col_diff = abs(end[1] - start[1])
        if max(row_diff, col_diff) != 1:
            return False
        return self._destination_occupiable(piece, end)

    def is_valid_pawn_move(self, start: Square, end: Square) -> bool:
        piece = self.get_piece(*start)
        if piece is None or piece.kind != PieceType.PAWN:
            return False
        if not self.is_valid_position(*end) or start == end:
            return False

        row_diff = end[0] - start[0]
        col_diff = end[1] - start[1]

        direction = -1 if piece.color == Color.WHITE else 1
        start_row = 6 if piece.color == Color.WHITE else 1

        if col_diff == 0:
            if row_diff == direction and self.is_empty(*end):
                return True
            if row_diff == 2 * direction and start[0] == start_row:
                middle = (start[0] + direction, start[1])
                return self.is_empty(*middle) and self.is_empty(*end)
            return False

        if abs(col_diff) == 1 and row_diff == direction:
            end_piece = self.get_piece(*end)
            if end_piece is not None:
                return end_piece.color != piece.color

            if self.en_passant_target == end:
                captured_row = end[0] + 1 if piece.color == Color.WHITE else end[0] - 1
                captured_piece = self.get_piece(captured_row, end[1])
                return (
                    captured_piece is not None
                    and captured_piece.kind == PieceType.PAWN
                    and captured_piece.color != piece.color
                )
        return False

    def _is_valid_piece_move(self, start: Square, end: Square) -> bool:
        piece = self.get_piece(*start)
        if piece is None:
            return False

        validators = {
            PieceType.ROOK: self.is_valid_rook_move,
            PieceType.BISHOP: self.is_valid_bishop_move,
            PieceType.QUEEN: self.is_valid_queen_move,
            PieceType.KNIGHT: self.is_valid_knight_move,
            PieceType.KING: self.is_valid_king_move,
            PieceType.PAWN: self.is_valid_pawn_move,
        }
        return validators[piece.kind](start, end)

    def make_move(self, start_pos: Square, end_pos: Square) -> bool:
        if not self.is_valid_position(*start_pos) or not self.is_valid_position(*end_pos):
            return False

        start_piece = self.get_piece(*start_pos)
        if start_piece is None or start_piece.color != self.turn:
            return False

        if not self._is_valid_piece_move(start_pos, end_pos):
            return False

        is_en_passant_capture = (
            start_piece.kind == PieceType.PAWN
            and self.en_passant_target == end_pos
            and self.get_piece(*end_pos) is None
            and start_pos[1] != end_pos[1]
        )

        if is_en_passant_capture:
            captured_row = end_pos[0] + 1 if start_piece.color == Color.WHITE else end_pos[0] - 1
            self.clear_square(captured_row, end_pos[1])

        self.set_piece(*end_pos, start_piece)
        self.clear_square(*start_pos)

        if start_piece.kind == PieceType.PAWN and abs(end_pos[0] - start_pos[0]) == 2:
            step = -1 if start_piece.color == Color.WHITE else 1
            self.en_passant_target = (start_pos[0] + step, start_pos[1])
        else:
            self.en_passant_target = None

        if start_piece.kind == PieceType.PAWN and end_pos[0] in {0, 7}:
            self.set_piece(end_pos[0], end_pos[1], create_piece(start_piece.color, PieceType.QUEEN))

        self.turn = Color.BLACK if self.turn == Color.WHITE else Color.WHITE
        return True

    def display(self) -> None:
        print("  a b c d e f g h")
        for row_index, row in enumerate(self.board):
            rank = 8 - row_index
            symbols: list[str] = []
            for piece in row:
                if piece is None:
                    symbols.append(".")
                    continue

                symbol_map = {
                    PieceType.PAWN: "P",
                    PieceType.KNIGHT: "N",
                    PieceType.BISHOP: "B",
                    PieceType.ROOK: "R",
                    PieceType.QUEEN: "Q",
                    PieceType.KING: "K",
                }
                symbol = symbol_map[piece.kind]
                symbols.append(symbol if piece.color == Color.WHITE else symbol.lower())
            print(f"{rank} {' '.join(symbols)} {rank}")
        print("  a b c d e f g h")
        print(f"Turn: {self.turn.value}")
