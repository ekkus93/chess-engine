from __future__ import annotations

from typing import Optional, Union

from chess_game.chess.types import Color, Piece, PieceType
from chess_game.constants import (
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_4,
    ROW_5,
    ROW_6,
    ROW_7,
    ROW_8,
    COL_A,
    COL_B,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_G,
    COL_H,
)
from chess_game.constants import (
    ConstantSquare,
    get_row_constant,
    get_col_constant,
)

Square = ConstantSquare
LegalMove = tuple[Square, Square, Optional[PieceType]]


def create_piece(
    color: Color, piece_type: PieceType, square: Optional[Square] = None
) -> Piece:
    """Create a typed chess piece."""
    return Piece(color=color, kind=piece_type, _square=square)


def offset_square(s: Square, dr: int, dc: int) -> Square:
    """Offset a square position by delta row and delta column.

    This helper function prevents direct arithmetic on Square tuples,
    which can introduce subtle bugs. Use this instead of manual coordinate math.

    Args:
        s: The starting square as (row, col) tuple or ConstantSquare
        dr: Row delta (negative for upward, positive for downward)
        dc: Column delta (negative for leftward, positive for rightward)

    Returns:
        New square position as (row + dr, col + dc)
    """
    if isinstance(s, tuple):
        s = ConstantSquare(row=get_row_constant(s[0]), col=get_col_constant(s[1]))
    new_row = int(s.row) + dr
    new_col = int(s.col) + dc
    return ConstantSquare(row=get_row_constant(new_row), col=get_col_constant(new_col))


def forward_one(s: Square, color: Color) -> Square:
    """Move one square forward for a pawn.

    White moves toward row 7 (increasing), black moves toward row 0 (decreasing).

    Args:
        s: The pawn's current position
        color: The pawn's color

    Returns:
        Position one square forward
    """
    if color == Color.WHITE:
        return offset_square(s, 1, 0)
    else:
        return offset_square(s, -1, 0)


class Board:
    board: list[list[Optional[Piece]]]
    turn: Color
    en_passant_target: Optional[Square]
    white_kingside: bool
    white_queenside: bool
    black_kingside: bool
    black_queenside: bool

    def __init__(self) -> None:
        super().__init__()
        self.board = self.create_board()
        self.turn = Color.WHITE
        self.en_passant_target = None
        self.white_kingside = True
        self.white_queenside = True
        self.black_kingside = True
        self.black_queenside = True

    def create_board(self) -> list[list[Optional[Piece]]]:
        """Create a standard chess board."""
        board: list[list[Optional[Piece]]] = [
            [None for _ in range(8)] for _ in range(8)
        ]

        # White pieces at rows 0-1 (ranks 1-2) - array row 0 = ROW_1 = rank 1
        # White pawns at row 1 (rank 2), white pieces at row 0 (rank 1)
        board[0] = [
            create_piece(Color.WHITE, PieceType.ROOK),  # a1
            create_piece(Color.WHITE, PieceType.KNIGHT),  # b1
            create_piece(Color.WHITE, PieceType.BISHOP),  # c1
            create_piece(Color.WHITE, PieceType.QUEEN),  # d1
            create_piece(Color.WHITE, PieceType.KING),  # e1
            create_piece(Color.WHITE, PieceType.BISHOP),  # f1
            create_piece(Color.WHITE, PieceType.KNIGHT),  # g1
            create_piece(Color.WHITE, PieceType.ROOK),  # h1
        ]

        board[1] = [create_piece(Color.WHITE, PieceType.PAWN) for _ in range(8)]

        # Black pieces at rows 6-7 (ranks 7-8) - array row 6 = ROW_7 = rank 7
        # Black pawns at row 6 (rank 7), black pieces at row 7 (rank 8)
        board[6] = [create_piece(Color.BLACK, PieceType.PAWN) for _ in range(8)]
        board[7] = [
            create_piece(Color.BLACK, PieceType.ROOK),  # a8
            create_piece(Color.BLACK, PieceType.KNIGHT),  # b8
            create_piece(Color.BLACK, PieceType.BISHOP),  # c8
            create_piece(Color.BLACK, PieceType.QUEEN),  # d8
            create_piece(Color.BLACK, PieceType.KING),  # e8
            create_piece(Color.BLACK, PieceType.BISHOP),  # f8
            create_piece(Color.BLACK, PieceType.KNIGHT),  # g8
            create_piece(Color.BLACK, PieceType.ROOK),  # h8
        ]

        return board

    def _validate_coordinates(self, row: int, col: int) -> None:
        """Validate coordinates using Pydantic type checking.

        This enforces the use of ROW_* and COL_* constants instead of raw values.
        Raises a ValueError with a helpful message if invalid coordinates are used.
        """
        try:
            ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
        except ValueError as e:
            raise ValueError(f"Invalid coordinates ({row}, {col}): {e}") from e

    def is_valid_position(self, square: Square) -> bool:
        return 0 <= int(square.row) < 8 and 0 <= int(square.col) < 8

    def is_on_board(self, square: Square) -> bool:
        return 0 <= int(square.row) < 8 and 0 <= int(square.col) < 8

    def get_piece(self, square: Square) -> Optional[Piece]:
        return self.board[int(square.row)][int(square.col)]

    def set_piece(self, square: Square, piece: Optional[Piece]) -> None:
        if piece is not None:
            # Create a new piece with updated square since Piece is frozen
            piece = create_piece(piece.color, piece.kind, square)
        self.board[int(square.row)][int(square.col)] = piece

    def clear_square(self, square: Square) -> None:
        self.set_piece(square, None)

    def clone(self) -> Board:
        cloned = Board()
        cloned.board = [row.copy() for row in self.board]
        cloned.turn = self.turn
        cloned.en_passant_target = self.en_passant_target
        cloned.white_kingside = self.white_kingside
        cloned.white_queenside = self.white_queenside
        cloned.black_kingside = self.black_kingside
        cloned.black_queenside = self.black_queenside
        return cloned

    def is_empty(self, square: Square) -> bool:
        return self.get_piece(square) is None

    def get_color_at(self, square: Square) -> Optional[Color]:
        piece = self.get_piece(square)
        return piece.color if piece else None

    def get_piece_type_at(self, square: Square) -> Optional[PieceType]:
        piece = self.get_piece(square)
        return piece.kind if piece else None

    def is_same_color(self, square1: Square, square2: Square) -> bool:
        piece1 = self.get_piece(square1)
        piece2 = self.get_piece(square2)
        return (
            piece1 is not None and piece2 is not None and piece1.color == piece2.color
        )

    def is_opponent(self, row1: int, col1: int, row2: int, col2: int) -> bool:
        piece1 = self.get_piece(
            ConstantSquare(row=get_row_constant(row1), col=get_col_constant(col1))
        )
        piece2 = self.get_piece(
            ConstantSquare(row=get_row_constant(row2), col=get_col_constant(col2))
        )
        return (
            piece1 is not None and piece2 is not None and piece1.color != piece2.color
        )

    def _destination_occupiable(self, mover: Piece, end: Square) -> bool:
        if not self.is_valid_position(end):
            return False
        end_piece = self.get_piece(end)
        return end_piece is None or end_piece.color != mover.color

    def _path_is_clear(self, start: Square, end: Square) -> bool:
        row_diff = end.row - start.row
        col_diff = end.col - start.col

        step_row = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
        step_col = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)

        current_row = int(start.row) + step_row
        current_col = int(start.col) + step_col
        while (current_row, current_col) != (int(end.row), int(end.col)):
            if (
                self.get_piece(
                    ConstantSquare(
                        row=get_row_constant(current_row),
                        col=get_col_constant(current_col),
                    )
                )
                is not None
            ):
                return False
            current_row += step_row
            current_col += step_col
        return True

    def is_valid_rook_move(self, start: Square, end: Square) -> bool:
        if isinstance(start, tuple):
            start = ConstantSquare(
                row=get_row_constant(start[0]), col=get_col_constant(start[1])
            )
        if isinstance(end, tuple):
            end = ConstantSquare(
                row=get_row_constant(end[0]), col=get_col_constant(end[1])
            )
        piece = self.get_piece(start)
        if piece is None or piece.kind != PieceType.ROOK:
            return False
        if not self.is_valid_position(end) or start == end:
            return False
        if start.row != end.row and start.col != end.col:
            return False
        if not self._path_is_clear(start, end):
            return False
        return self._destination_occupiable(piece, end)

    def is_valid_bishop_move(self, start: Square, end: Square) -> bool:
        if isinstance(start, tuple):
            start = ConstantSquare(
                row=get_row_constant(start[0]), col=get_col_constant(start[1])
            )
        if isinstance(end, tuple):
            end = ConstantSquare(
                row=get_row_constant(end[0]), col=get_col_constant(end[1])
            )
        piece = self.get_piece(start)
        if piece is None or piece.kind != PieceType.BISHOP:
            return False
        if not self.is_valid_position(end) or start == end:
            return False
        if abs(end.row - start.row) != abs(end.col - start.col):
            return False
        if not self._path_is_clear(start, end):
            return False
        return self._destination_occupiable(piece, end)

    def is_valid_queen_move(self, start: Square, end: Square) -> bool:
        if isinstance(start, tuple):
            start = ConstantSquare(
                row=get_row_constant(start[0]), col=get_col_constant(start[1])
            )
        if isinstance(end, tuple):
            end = ConstantSquare(
                row=get_row_constant(end[0]), col=get_col_constant(end[1])
            )
        piece = self.get_piece(start)
        if piece is None or piece.kind != PieceType.QUEEN:
            return False
        if not self.is_valid_position(end) or start == end:
            return False

        is_straight = start.row == end.row or start.col == end.col
        is_diagonal = abs(end.row - start.row) == abs(end.col - start.col)
        if not (is_straight or is_diagonal):
            return False
        if not self._path_is_clear(start, end):
            return False
        return self._destination_occupiable(piece, end)

    def is_valid_knight_move(self, start: Square, end: Square) -> bool:
        if isinstance(start, tuple):
            start = ConstantSquare(
                row=get_row_constant(start[0]), col=get_col_constant(start[1])
            )
        if isinstance(end, tuple):
            end = ConstantSquare(
                row=get_row_constant(end[0]), col=get_col_constant(end[1])
            )
        piece = self.get_piece(start)
        if piece is None or piece.kind != PieceType.KNIGHT:
            return False
        if not self.is_valid_position(end) or start == end:
            return False

        row_diff = abs(end.row - start.row)
        col_diff = abs(end.col - start.col)
        if (row_diff, col_diff) not in {(2, 1), (1, 2)}:
            return False
        return self._destination_occupiable(piece, end)

    def is_valid_king_move(self, start: Square, end: Square) -> bool:
        piece = self.get_piece(start)
        if piece is None or piece.kind != PieceType.KING:
            return False
        if not self.is_valid_position(end) or start == end:
            return False

        if self._is_castling_move(start, end):
            return self._can_castle(start, end, piece.color)

        row_diff = abs(end.row - start.row)
        col_diff = abs(end.col - start.col)
        if max(row_diff, col_diff) != 1:
            return False
        return self._destination_occupiable(piece, end)

    def _is_castling_move(self, start: Square, end: Square) -> bool:
        return start.row == end.row and start.col == COL_E and end.col in {COL_C, COL_G}

    def _rook_at_original_square(self, color: Color, rook_square: Square) -> bool:
        """Check if the rook is still at its original square."""
        piece = self.get_piece(rook_square)
        return (
            piece is not None and piece.kind == PieceType.ROOK and piece.color == color
        )

    def _can_castle(self, start: Square, end: Square, color: Color) -> bool:
        home_row = ROW_1 if color == Color.WHITE else ROW_8
        if start != ConstantSquare(row=home_row, col=COL_E):
            return False

        # Check if castling rights are still valid
        if color == Color.WHITE:
            if not self.white_kingside and end == ConstantSquare(
                row=home_row, col=COL_F
            ):
                return False
            if not self.white_queenside and end == ConstantSquare(
                row=home_row, col=get_col_constant(int(COL_B))
            ):
                return False
        else:
            if not self.black_kingside and end == ConstantSquare(
                row=home_row, col=COL_F
            ):
                return False
            if not self.black_queenside and end == ConstantSquare(
                row=home_row, col=get_col_constant(int(COL_B))
            ):
                return False

        enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE

        if end == ConstantSquare(row=home_row, col=COL_G):
            rook_square = ConstantSquare(row=home_row, col=COL_H)
            between = [
                ConstantSquare(row=home_row, col=COL_F)
            ]  # Only check f1, the square king passes through
            king_path = [
                ConstantSquare(row=home_row, col=COL_F)
            ]  # King moves e1->f1->g1, attackable square is f1
            destination = ConstantSquare(row=home_row, col=COL_G)  # g1
            if not self._rook_at_original_square(color, rook_square):
                return False
        elif end == ConstantSquare(row=home_row, col=get_col_constant(int(COL_C))):
            rook_square = ConstantSquare(row=home_row, col=COL_A)
            between = [
                ConstantSquare(row=home_row, col=get_col_constant(int(COL_D))),
                ConstantSquare(row=home_row, col=get_col_constant(int(COL_C))),
            ]  # Check d1 and c1 for attacks
            king_path = [
                ConstantSquare(row=home_row, col=get_col_constant(int(COL_D))),
                ConstantSquare(row=home_row, col=get_col_constant(int(COL_C))),
            ]  # King passes through d1 to c1, attackable squares are d1,c1
            destination = ConstantSquare(
                row=home_row, col=get_col_constant(int(COL_C))
            )  # c1
            if not self._rook_at_original_square(color, rook_square):
                return False
        else:
            return False

        rook_piece = self.get_piece(rook_square)
        if (
            rook_piece is None
            or rook_piece.kind != PieceType.ROOK
            or rook_piece.color != color
        ):
            return False

        if any(not self.is_empty(square) for square in between):
            return False

        if not self.is_empty(destination):
            return False

        if self.is_in_check(color):
            return False

        if any(self.is_square_attacked(square, enemy_color) for square in king_path):
            return False

        # Check if the destination square is attacked (king would be in check)
        if self.is_square_attacked(destination, enemy_color):
            return False

        return True

    def is_valid_pawn_move(self, start: Square, end: Square) -> bool:
        """Check if a pawn move is valid."""
        if isinstance(start, tuple):
            start = ConstantSquare(
                row=get_row_constant(start[0]), col=get_col_constant(start[1])
            )
        if isinstance(end, tuple):
            end = ConstantSquare(
                row=get_row_constant(end[0]), col=get_col_constant(end[1])
            )
        piece = self.get_piece(start)
        if piece is None or piece.color != self.turn:
            return False

        start_row = int(start.row)
        end_row = int(end.row)

        # Pawns can move forward 1, 2, or 6 squares from starting position
        if piece.color == Color.WHITE:
            # White moves toward row 7 (increasing) - from rank 1 to rank 8
            if end_row <= start_row:
                return False
            col_diff = abs(int(end.col) - int(start.col))

            # Diagonal capture (must be adjacent diagonal)
            if end.col != start.col:
                is_en_passant_capture = end == self.en_passant_target
                is_capture = self.get_piece(end) is not None
                # Regular capture must be adjacent diagonal (row diff = 1, col diff = 1)
                if is_en_passant_capture:
                    # En passant capture: 1 row difference (diagonal) and 1 column
                    return abs(end_row - start_row) == 1 and col_diff == 1
                # Regular capture: must be adjacent diagonal and enemy piece at destination
                if is_capture and abs(end_row - start_row) == 1 and col_diff == 1:
                    return True
                # Not a valid capture, so this diagonal move is invalid
                return False

            # Validate move distance (white moves toward increasing row)
            distance = end_row - start_row  # White moves toward row 7 (increasing)

            # 6-square move for promotion (ROW_2 to ROW_8, i.e., rank 2 to rank 8)
            if start_row == int(ROW_2) and end_row == int(ROW_8):
                # Check ALL intermediate squares are empty (rows 2, 3, 4, 5, 6)
                all_clear = self.get_piece(end) is None
                for row_idx in range(int(start_row) + 1, int(end_row)):
                    intermediate = ConstantSquare(
                        row=get_row_constant(row_idx),
                        col=get_col_constant(int(start.col)),
                    )
                    all_clear = all_clear and self.get_piece(intermediate) is None
                return all_clear and distance == 6

            # 2-square move from starting position (ROW_2 to ROW_4, i.e., rank 2 to rank 4)
            if start_row == int(ROW_2) and end_row == int(ROW_4):
                intermediate = ConstantSquare(
                    row=get_row_constant(int(start_row) + 1),
                    col=get_col_constant(int(start.col)),
                )
                return (
                    self.get_piece(end) is None
                    and self.get_piece(intermediate) is None
                    and distance == 2
                )

            # Check if pawn reached promotion rank (row 7 = rank 8)
            if end_row == int(ROW_8):
                # Pawn needs to promote - must be valid 1-step move
                # Pawn can promote from any rank when reaching row 7 (rank 8)
                return self.get_piece(end) is None and distance == 1

            # Normal 1-step move (non-promotion)
            return self.get_piece(end) is None and distance == 1

        else:
            # Black moves toward row 0 (decreasing) - from rank 8 to rank 1
            if end_row >= start_row:
                return False
            col_diff = abs(int(end.col) - int(start.col))

            # Diagonal capture (must be adjacent diagonal)
            if end.col != start.col:
                is_en_passant_capture = end == self.en_passant_target
                is_capture = self.get_piece(end) is not None
                # Regular capture must be adjacent diagonal (row diff = 1, col diff = 1)
                if is_en_passant_capture:
                    # En passant capture: 1 row difference (diagonal) and 1 column
                    return abs(end_row - start_row) == 1 and col_diff == 1
                # Regular capture: must be adjacent diagonal and enemy piece at destination
                if is_capture and abs(end_row - start_row) == 1 and col_diff == 1:
                    return True
                # Not a valid capture, so this diagonal move is invalid
                return False

            # Validate move distance (black moves toward decreasing row)
            distance = start_row - end_row  # Black moves toward row 0 (decreasing)

            # 6-square move for promotion (ROW_7 to ROW_1, i.e., rank 7 to rank 1)
            if start_row == int(ROW_7) and end_row == int(ROW_1):
                # Check ALL intermediate squares are empty (rows 6, 5, 4, 3, 2)
                all_clear = self.get_piece(end) is None
                for row_idx in range(int(end_row) + 1, int(start_row)):
                    intermediate = ConstantSquare(
                        row=get_row_constant(row_idx),
                        col=get_col_constant(int(start.col)),
                    )
                    all_clear = all_clear and self.get_piece(intermediate) is None
                return all_clear and distance == 6

            # 2-square move from starting position (ROW_8 to ROW_6, i.e., rank 8 to rank 6)
            if start_row == int(ROW_8) and end_row == int(ROW_6):
                intermediate = ConstantSquare(
                    row=get_row_constant(int(start_row) - 1),
                    col=get_col_constant(int(start.col)),
                )
                return (
                    self.get_piece(end) is None
                    and self.get_piece(intermediate) is None
                    and distance == 2
                )

            # Check if pawn reached promotion rank (row 0 = rank 1)
            if end_row == int(ROW_1):
                # Pawn needs to promote - must be valid 1-step move
                # Pawn can promote from any rank when reaching row 0 (rank 1)
                return self.get_piece(end) is None and distance == 1

            # Normal 1-step move (non-promotion)
            return self.get_piece(end) is None and distance == 1

    def _is_valid_piece_move(self, start: Square, end: Square) -> bool:
        print()
        if isinstance(start, tuple):
            start = ConstantSquare(
                row=get_row_constant(start[0]), col=get_col_constant(start[1])
            )
        if isinstance(end, tuple):
            end = ConstantSquare(
                row=get_row_constant(end[0]), col=get_col_constant(end[1])
            )
        piece = self.get_piece(start)
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

    def find_king(self, color: Color) -> Optional[Square]:
        for row in range(8):
            for col in range(8):
                square = ConstantSquare(
                    row=get_row_constant(row), col=get_col_constant(col)
                )
                piece = self.get_piece(square)
                if (
                    piece is not None
                    and piece.color == color
                    and piece.kind == PieceType.KING
                ):
                    return square
        return None

    def _piece_attacks_square(
        self, start: Square, piece: Piece, target: Square
    ) -> bool:
        row_diff = target.row - start.row
        col_diff = target.col - start.col

        if piece.kind == PieceType.PAWN:
            direction = 1 if piece.color == Color.WHITE else -1
            return row_diff == direction and abs(col_diff) == 1

        if piece.kind == PieceType.KNIGHT:
            return (abs(row_diff), abs(col_diff)) in {(2, 1), (1, 2)}

        if piece.kind == PieceType.BISHOP:
            if abs(row_diff) != abs(col_diff) or start == target:
                return False
            return self._path_is_clear(start, target)

        if piece.kind == PieceType.ROOK:
            if start == target:
                return False
            if start.row != target.row and start.col != target.col:
                return False
            return self._path_is_clear(start, target)

        if piece.kind == PieceType.QUEEN:
            if start == target:
                return False
            is_straight = start.row == target.row or start.col == target.col
            is_diagonal = abs(row_diff) == abs(col_diff)
            if not (is_straight or is_diagonal):
                return False
            return self._path_is_clear(start, target)

        if piece.kind == PieceType.KING:
            return start != target and max(abs(row_diff), abs(col_diff)) == 1

        return False

    def _is_piece_pinned(self, piece_square: Square, piece_color: Color) -> bool:
        """Check if a piece is absolutely pinned (moving would expose king to check)."""
        king_square = self.find_king(piece_color)
        if king_square is None:
            return False

        enemy_color = Color.BLACK if piece_color == Color.WHITE else Color.WHITE

        # Find if there's a line of attack from enemy to king through this piece
        for row in range(8):
            for col in range(8):
                enemy_piece = self.get_piece(
                    ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
                )
                if enemy_piece is None or enemy_piece.color != enemy_color:
                    continue

                enemy_square = ConstantSquare(
                    row=get_row_constant(row), col=get_col_constant(col)
                )

                # Check if enemy piece attacks along a straight or diagonal line
                is_enemy_on_line = False
                if enemy_piece.kind == PieceType.ROOK:
                    # Rook attacks on rank or file
                    if row == king_square.row or col == king_square.col:
                        is_enemy_on_line = True
                elif enemy_piece.kind == PieceType.BISHOP:
                    # Bishop attacks on diagonal
                    if abs(row - king_square.row) == abs(col - king_square.col):
                        is_enemy_on_line = True
                elif enemy_piece.kind == PieceType.QUEEN:
                    # Queen attacks on rank, file, or diagonal
                    if row == king_square.row or col == king_square.col:
                        is_enemy_on_line = True
                    if abs(row - king_square.row) == abs(col - king_square.col):
                        is_enemy_on_line = True

                if is_enemy_on_line and self._is_piece_between_enemy_and_king(
                    enemy_square, piece_square, king_square
                ):
                    return True

        return False

    def _is_piece_between_enemy_and_king(
        self, enemy_pos: Square, piece_pos: Square, king_pos: Square
    ) -> bool:
        """Check if the piece is geometrically between the enemy piece and king."""
        # Check if all three are on the same line (rank, file, or diagonal)
        if enemy_pos.row != piece_pos.row or piece_pos.row != king_pos.row:
            # Not on same rank
            if enemy_pos.col != piece_pos.col or piece_pos.col != king_pos.col:
                # Not on same file
                if abs(enemy_pos.row - king_pos.row) != abs(
                    enemy_pos.col - king_pos.col
                ):
                    # Not on same diagonal
                    return False

        # Check if piece is geometrically between enemy and king (exclusive)
        # For rank: enemy_row < piece_row < king_row or king_row < piece_row < enemy_row
        # For file: enemy_col < piece_col < king_col or king_col < piece_col < enemy_col
        # For diagonal: check both row and col ordering
        if enemy_pos.row == piece_pos.row == king_pos.row:
            # Same rank
            return (int(enemy_pos.col) < int(piece_pos.col) < int(king_pos.col)) or (
                int(king_pos.col) < int(piece_pos.col) < int(enemy_pos.col)
            )
        elif enemy_pos.col == piece_pos.col == king_pos.col:
            # Same file
            return (int(enemy_pos.row) < int(piece_pos.row) < int(king_pos.row)) or (
                int(king_pos.row) < int(piece_pos.row) < int(enemy_pos.row)
            )
        else:
            # Diagonal
            row_diff = int(enemy_pos.row) - int(piece_pos.row)
            col_diff = int(enemy_pos.col) - int(piece_pos.col)
            king_row_diff = int(king_pos.row) - int(piece_pos.row)
            king_col_diff = int(king_pos.col) - int(piece_pos.col)
            return (
                (row_diff < 0 and king_row_diff < 0)
                or (row_diff > 0 and king_row_diff > 0)
            ) and (
                (col_diff < 0 and king_col_diff < 0)
                or (col_diff > 0 and king_col_diff > 0)
            )

    def _is_square_between(self, start: Square, end: Square) -> bool:
        """Check if there's any square between two positions (exclusive)."""
        if start == end:
            return False

        row_diff = end.row - start.row
        col_diff = end.col - start.col

        step_row = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
        step_col = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)

        current_row = start.row + step_row
        current_col = start.col + step_col

        while (current_row, current_col) != (end.row, end.col):
            if (
                self.get_piece(
                    ConstantSquare(
                        row=get_row_constant(current_row),
                        col=get_col_constant(current_col),
                    )
                )
                is not None
            ):
                return False
            current_row += step_row
            current_col += step_col

        return True

    def is_square_attacked(self, square: Square, by_color: Color) -> bool:
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(
                    ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
                )
                if piece is None or piece.color != by_color:
                    continue
                if self._piece_attacks_square(
                    ConstantSquare(
                        row=get_row_constant(row), col=get_col_constant(col)
                    ),
                    piece,
                    square,
                ):
                    return True
        return False

    def is_in_check(self, color: Color) -> bool:
        king_square = self.find_king(color)
        if king_square is None:
            return False

        enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
        return self.is_square_attacked(king_square, enemy_color)

    def _promotion_options_for_move(
        self, piece: Piece, end_pos: Square
    ) -> list[Optional[PieceType]]:
        if piece.kind == PieceType.PAWN and int(end_pos.row) in {0, 7}:
            return [
                PieceType.QUEEN,
                PieceType.ROOK,
                PieceType.BISHOP,
                PieceType.KNIGHT,
            ]
        return [None]

    def get_legal_moves(self, color: Optional[Color] = None) -> list[LegalMove]:
        side = self.turn if color is None else color
        legal_moves: list[LegalMove] = []

        for start_row in range(8):
            for start_col in range(8):
                piece = self.get_piece(
                    ConstantSquare(
                        row=get_row_constant(start_row), col=get_col_constant(start_col)
                    )
                )
                if piece is None or piece.color != side:
                    continue

                start = ConstantSquare(
                    row=get_row_constant(start_row), col=get_col_constant(start_col)
                )
                for end_row in range(8):
                    for end_col in range(8):
                        end = ConstantSquare(
                            row=get_row_constant(end_row), col=get_col_constant(end_col)
                        )
                        for promotion in self._promotion_options_for_move(piece, end):
                            simulated = self.clone()
                            simulated.turn = side
                            if simulated.make_move(start, end, promotion=promotion):
                                # Check that the move doesn't leave the player's king in check
                                if not simulated.is_in_check(side):
                                    legal_moves.append((start, end, promotion))

        return legal_moves

    def is_checkmate(self, color: Optional[Color] = None) -> bool:
        side = self.turn if color is None else color
        return self.is_in_check(side) and len(self.get_legal_moves(side)) == 0

    def is_stalemate(self, color: Optional[Color] = None) -> bool:
        side = self.turn if color is None else color
        return not self.is_in_check(side) and len(self.get_legal_moves(color)) == 0

    def _apply_move_unchecked(
        self, start_pos: Square, end_pos: Square, promotion: Optional[PieceType] = None
    ) -> None:
        start_piece = self.get_piece(start_pos)
        if start_piece is None:
            return

        captured_piece = self.get_piece(end_pos)
        self._update_castling_rights_for_move(
            start_pos, end_pos, start_piece, captured_piece
        )

        is_en_passant_capture = (
            start_piece.kind == PieceType.PAWN
            and self.en_passant_target == end_pos
            and self.get_piece(end_pos) is None
            and start_pos.col != end_pos.col
        )

        if is_en_passant_capture:
            # For en passant capture, the captured pawn is on the destination square
            # but needs to be moved up one square (in its original direction)
            captured_row = int(end_pos.row)
            captured_col = int(end_pos.col)

            # Determine the square where the captured pawn should be removed from
            # White moves toward increasing row, so captured black pawn is at end_pos - 1
            # Black moves toward decreasing row, so captured white pawn is at end_pos + 1
            captured_row_from = (
                captured_row - 1
                if start_piece.color == Color.WHITE
                else captured_row + 1
            )

            captured_piece = self.get_piece(
                ConstantSquare(
                    row=get_row_constant(captured_row_from),
                    col=get_col_constant(captured_col),
                )
            )
            self.clear_square(
                ConstantSquare(
                    row=get_row_constant(captured_row_from),
                    col=get_col_constant(captured_col),
                )
            )
            if (
                captured_piece is not None
                and captured_piece.kind == PieceType.ROOK
                and captured_piece.color != start_piece.color
            ):
                self._clear_castling_right_for_captured_rook(
                    ConstantSquare(
                        row=get_row_constant(captured_row),
                        col=get_col_constant(int(end_pos.col)),
                    )
                )

        self.set_piece(end_pos, start_piece)
        self.clear_square(start_pos)

        if start_piece.kind == PieceType.KING and self._is_castling_move(
            start_pos, end_pos
        ):
            home_row = start_pos.row
            if end_pos.col == COL_G:  # Kingside: e1->g1, rook h1->f1
                rook_from = ConstantSquare(row=home_row, col=COL_H)
                rook_to = ConstantSquare(row=home_row, col=COL_F)
            else:  # Queenside: e1->c1, rook a1->d1
                rook_from = ConstantSquare(row=home_row, col=COL_A)
                rook_to = ConstantSquare(row=home_row, col=COL_D)

            rook_piece = self.get_piece(rook_from)
            self.clear_square(rook_from)
            self.set_piece(rook_to, rook_piece)

        if start_piece.kind == PieceType.PAWN and abs(end_pos.row - start_pos.row) == 2:
            # Set en_passant_target to the midpoint between start and end
            # White: start=ROW_2(1), end=ROW_4(3), target=ROW_3(2)
            # Black: start=ROW_7(6), end=ROW_5(4), target=ROW_6(5)
            midpoint_row = (int(start_pos.row) + int(end_pos.row)) // 2
            self.en_passant_target = ConstantSquare(
                row=get_row_constant(midpoint_row),
                col=get_col_constant(int(end_pos.col)),
            )
        else:
            # Clear en_passant_target for all other moves
            self.en_passant_target = None

        if start_piece.kind == PieceType.PAWN and end_pos.row in {
            int(ROW_1),
            int(ROW_8),
        }:
            self.set_piece(
                end_pos,
                create_piece(
                    start_piece.color,
                    promotion if promotion is not None else PieceType.QUEEN,
                ),
            )

    def _clear_castling_right_for_captured_rook(self, square: Square) -> None:
        if square == ConstantSquare(row=get_row_constant(int(ROW_1)), col=COL_A):
            self.white_queenside = False
        elif square == ConstantSquare(row=get_row_constant(int(ROW_1)), col=COL_H):
            self.white_kingside = False
        elif square == ConstantSquare(row=get_row_constant(int(ROW_8)), col=COL_A):
            self.black_queenside = False
        elif square == ConstantSquare(row=get_row_constant(int(ROW_8)), col=COL_H):
            self.black_kingside = False

    def _update_castling_rights_for_move(
        self,
        start_pos: Square,
        end_pos: Square,
        moving_piece: Piece,
        captured_piece: Optional[Piece],
    ) -> None:
        if moving_piece.kind == PieceType.KING:
            home_row = start_pos.row
            if moving_piece.color == Color.WHITE:
                if end_pos.row == home_row and end_pos.col in {COL_C, COL_G}:
                    self.white_kingside = False
                    self.white_queenside = False
            else:
                if end_pos.row == home_row and end_pos.col in {COL_C, COL_G}:
                    self.black_kingside = False
                    self.black_queenside = False

        if moving_piece.kind == PieceType.ROOK:
            if start_pos == ConstantSquare(row=get_row_constant(int(ROW_1)), col=COL_A):
                self.white_queenside = False
            elif start_pos == ConstantSquare(
                row=get_row_constant(int(ROW_1)), col=COL_H
            ):
                self.white_kingside = False
            elif start_pos == ConstantSquare(
                row=get_row_constant(int(ROW_8)), col=COL_A
            ):
                self.black_queenside = False
            elif start_pos == ConstantSquare(
                row=get_row_constant(int(ROW_8)), col=COL_H
            ):
                self.black_kingside = False

        if captured_piece is not None and captured_piece.kind == PieceType.ROOK:
            self._clear_castling_right_for_captured_rook(end_pos)

    def _is_valid_promotion_choice(
        self,
        piece: Piece,
        end_pos: Square,
        promotion: Optional[PieceType],
    ) -> bool:
        # Accept None (default promotion to queen) or explicit promotion type
        if promotion is None or piece.kind != PieceType.PAWN:
            return True

        # Check if pawn is on promotion rank (rank 1 = row 0, rank 8 = row 7)
        # The destination must be on the promotion rank
        if int(end_pos.row) not in {0, 7}:
            return False

        return promotion in {
            PieceType.QUEEN,
            PieceType.ROOK,
            PieceType.BISHOP,
            PieceType.KNIGHT,
        }

    def make_move(
        self,
        start_pos: Square,
        end_pos: Square,
        promotion: Optional[PieceType] = None,
    ) -> bool:
        if isinstance(start_pos, tuple):
            start_pos = ConstantSquare(
                row=get_row_constant(start_pos[0]), col=get_col_constant(start_pos[1])
            )
        if isinstance(end_pos, tuple):
            end_pos = ConstantSquare(
                row=get_row_constant(end_pos[0]), col=get_col_constant(end_pos[1])
            )
        start_piece = self.get_piece(start_pos)
        if start_piece is None or start_piece.color != self.turn:
            return False

        if not self._is_valid_promotion_choice(start_piece, end_pos, promotion):
            return False

        # Check if this is a castling move
        if start_piece.kind == PieceType.KING and self._is_castling_move(
            start_pos, end_pos
        ):
            if not self._can_castle(start_pos, end_pos, start_piece.color):
                return False

        # Special case: en passant capture
        # En passant captures must be validated before standard piece move validation
        # because the destination square appears empty (pawn is in transit)
        is_en_passant_capture = (
            start_piece.kind == PieceType.PAWN
            and self.en_passant_target == end_pos
            and start_pos.col != end_pos.col
        )

        if is_en_passant_capture:
            # Validate that this is a valid en passant capture
            # Destination must be diagonally adjacent to source (column diff = 1)
            # Row diff is not checked because the destination is the en_passant_target
            col_diff = abs(int(end_pos.col) - int(start_pos.col))
            if col_diff != 1:
                return False
        else:
            if not self._is_valid_piece_move(start_pos, end_pos):
                return False

        # Check if piece is pinned (moving it would expose king to check)
        if (
            start_piece.kind != PieceType.KNIGHT and start_piece.kind != PieceType.KING
        ):  # Knights and kings can move out of pin
            if self._is_piece_pinned(start_pos, start_piece.color):
                simulated = self.clone()
                simulated._apply_move_unchecked(start_pos, end_pos, promotion=promotion)
                if simulated.is_in_check(start_piece.color):
                    return False

        simulated = self.clone()
        simulated._apply_move_unchecked(start_pos, end_pos, promotion=promotion)

        # Determine promotion piece (default to QUEEN if None)
        promotion_piece = promotion if promotion is not None else PieceType.QUEEN

        if start_piece.kind == PieceType.PAWN and int(end_pos.row) in {0, 7}:
            simulated.set_piece(
                end_pos,
                create_piece(start_piece.color, promotion_piece),
            )

        if simulated.is_in_check(start_piece.color):
            return False

        self._apply_move_unchecked(start_pos, end_pos, promotion=promotion)

        self.turn = Color.BLACK if self.turn == Color.WHITE else Color.WHITE
        return True

    @staticmethod
    def clear_board(board: "Board") -> None:
        """Clear all pieces from the board."""
        for row in board.board:
            for i, piece in enumerate(row):
                if piece is not None:
                    row[i] = None

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
