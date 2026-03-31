from __future__ import annotations

from typing import Optional

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
    ALLOWED_ROW_VALUES,
    ALLOWED_COL_VALUES,
    RowType,
    ColType,
)

Square = ConstantSquare
LegalMove = tuple[Square, Square, Optional[PieceType]]


def create_piece(color: Color, piece_type: PieceType) -> Piece:
    """Create a typed chess piece."""
    return Piece(color=color, kind=piece_type)


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
        s = ConstantSquare(row=s[0], col=s[1])
    new_row = s.row + dr
    new_col = s.col + dc
    return ConstantSquare(row=new_row, col=new_col)


def forward_one(s: Square, color: Color) -> Square:
    """Move one square forward for a pawn.

    White moves toward row 0 (decreasing), black moves toward row 7 (increasing).

    Args:
        s: The pawn's current position
        color: The pawn's color

    Returns:
        Position one square forward
    """
    if color == Color.WHITE:
        return offset_square(s, -1, 0)
    else:
        return offset_square(s, 1, 0)


class Board:
    board: list[list[Optional[Piece]]]
    turn: Color
    en_passant_target: Optional[Square]
    white_kingside: bool
    white_queenside: bool
    black_kingside: bool
    black_queenside: bool

    def __init__(self) -> None:
        self.board = self.create_board()
        self.turn = Color.WHITE
        self.en_passant_target = None
        self.white_kingside = True
        self.white_queenside = True
        self.black_kingside = True
        self.black_queenside = True

    def create_board(self) -> list[list[Optional[Piece]]]:
        """Create a standard chess board."""
        board = [[None for _ in range(8)] for _ in range(8)]

        # Black pieces (rows 0-1, rank 8-7)
        self._validate_coordinates(ROW_8, COL_A)
        self._validate_coordinates(ROW_7, COL_A)

        # White pieces (rows 6-7, rank 2-1)
        self._validate_coordinates(ROW_2, COL_A)
        self._validate_coordinates(ROW_1, COL_A)

        board[ROW_8] = [
            create_piece(Color.BLACK, PieceType.ROOK),  # a8
            create_piece(Color.BLACK, PieceType.KNIGHT),  # b8
            create_piece(Color.BLACK, PieceType.BISHOP),  # c8
            create_piece(Color.BLACK, PieceType.QUEEN),  # d8
            create_piece(Color.BLACK, PieceType.KING),  # e8
            create_piece(Color.BLACK, PieceType.BISHOP),  # f8
            create_piece(Color.BLACK, PieceType.KNIGHT),  # g8
            create_piece(Color.BLACK, PieceType.ROOK),  # h8
        ]
        board[ROW_7] = [create_piece(Color.BLACK, PieceType.PAWN) for _ in range(8)]

        # White pieces (rows 6-7, rank 2-1)
        board[ROW_2] = [create_piece(Color.WHITE, PieceType.PAWN) for _ in range(8)]
        board[ROW_1] = [
            create_piece(Color.WHITE, PieceType.ROOK),
            create_piece(Color.WHITE, PieceType.KNIGHT),
            create_piece(Color.WHITE, PieceType.BISHOP),
            create_piece(Color.WHITE, PieceType.QUEEN),
            create_piece(Color.WHITE, PieceType.KING),
            create_piece(Color.WHITE, PieceType.BISHOP),
            create_piece(Color.WHITE, PieceType.KNIGHT),
            create_piece(Color.WHITE, PieceType.ROOK),
        ]

        return board

    def _validate_coordinates(self, row: int, col: int) -> None:
        """Validate coordinates using Pydantic type checking.

        This enforces the use of ROW_* and COL_* constants instead of raw values.
        Raises a ValueError with a helpful message if invalid coordinates are used.
        """
        try:
            ConstantSquare(row=row, col=col)
        except ValueError as e:
            raise ValueError(f"Invalid coordinates ({row}, {col}): {e}") from e

    def is_valid_position(self, row: RowType, col: ColType) -> bool:
        return 0 <= row < 8 and 0 <= col < 8

    def is_on_board(self, row: RowType, col: ColType) -> bool:
        return self.is_valid_position(row, col)

    def get_piece(self, square: Square) -> Optional[Piece]:
        return self.board[square.row][square.col]

    def set_piece(self, square: Square, piece: Optional[Piece]) -> None:
        self.board[square.row][square.col] = piece

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

    def is_same_color(self, row1: int, col1: int, row2: int, col2: int) -> bool:
        piece1 = self.get_piece(ConstantSquare(row=row1, col=col1))
        piece2 = self.get_piece(ConstantSquare(row=row2, col=col2))
        return (
            piece1 is not None and piece2 is not None and piece1.color == piece2.color
        )

    def is_opponent(self, row1: int, col1: int, row2: int, col2: int) -> bool:
        piece1 = self.get_piece(ConstantSquare(row=row1, col=col1))
        piece2 = self.get_piece(ConstantSquare(row=row2, col=col2))
        return (
            piece1 is not None and piece2 is not None and piece1.color != piece2.color
        )

    def _destination_occupiable(self, mover: Piece, end: Square) -> bool:
        end_piece = self.get_piece(end)
        return end_piece is None or end_piece.color != mover.color

    def _path_is_clear(self, start: Square, end: Square) -> bool:
        row_diff = end.row - start.row
        col_diff = end.col - start.col

        step_row = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
        step_col = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)

        current_row = start.row + step_row
        current_col = start.col + step_col
        while (current_row, current_col) != (end.row, end.col):
            if (
                self.get_piece(ConstantSquare(row=current_row, col=current_col))
                is not None
            ):
                return False
            current_row += step_row
            current_col += step_col
        return True

    def is_valid_rook_move(self, start: Square, end: Square) -> bool:
        if isinstance(start, tuple):
            start = ConstantSquare(row=start[0], col=start[1])
        if isinstance(end, tuple):
            end = ConstantSquare(row=end[0], col=end[1])
        piece = self.get_piece(start)
        if piece is None or piece.kind != PieceType.ROOK:
            return False
        if not self.is_valid_position(end.row, end.col) or start == end:
            return False
        if start.row != end.row and start.col != end.col:
            return False
        if not self._path_is_clear(start, end):
            return False
        return self._destination_occupiable(piece, end)

    def is_valid_bishop_move(self, start: Square, end: Square) -> bool:
        if isinstance(start, tuple):
            start = ConstantSquare(row=start[0], col=start[1])
        if isinstance(end, tuple):
            end = ConstantSquare(row=end[0], col=end[1])
        piece = self.get_piece(start)
        if piece is None or piece.kind != PieceType.BISHOP:
            return False
        if not self.is_valid_position(end.row, end.col) or start == end:
            return False
        if abs(end.row - start.row) != abs(end.col - start.col):
            return False
        if not self._path_is_clear(start, end):
            return False
        return self._destination_occupiable(piece, end)

    def is_valid_queen_move(self, start: Square, end: Square) -> bool:
        if isinstance(start, tuple):
            start = ConstantSquare(row=start[0], col=start[1])
        if isinstance(end, tuple):
            end = ConstantSquare(row=end[0], col=end[1])
        piece = self.get_piece(start)
        if piece is None or piece.kind != PieceType.QUEEN:
            return False
        if not self.is_valid_position(end.row, end.col) or start == end:
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
            start = ConstantSquare(row=start[0], col=start[1])
        if isinstance(end, tuple):
            end = ConstantSquare(row=end[0], col=end[1])
        piece = self.get_piece(start)
        if piece is None or piece.kind != PieceType.KNIGHT:
            return False
        if not self.is_valid_position(end.row, end.col) or start == end:
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
        if not self.is_valid_position(end.row, end.col) or start == end:
            return False

        if self._is_castling_move(start, end):
            return self._can_castle(start, end, piece.color)

        row_diff = abs(end.row - start.row)
        col_diff = abs(end.col - start.col)
        if max(row_diff, col_diff) != 1:
            return False
        return self._destination_occupiable(piece, end)

    def _is_castling_move(self, start: Square, end: Square) -> bool:
        return start.row == end.row and start.col == 4 and end.col in {2, 6}

    def _rook_at_original_square(self, color: Color, rook_square: Square) -> bool:
        """Check if the rook is still at its original square."""
        piece = self.get_piece(rook_square)
        return (
            piece is not None and piece.kind == PieceType.ROOK and piece.color == color
        )

    def _can_castle(self, start: Square, end: Square, color: Color) -> bool:
        home_row = 7 if color == Color.WHITE else 0
        if start != ConstantSquare(row=home_row, col=COL_D):
            return False

        # Check if castling rights are still valid
        if color == Color.WHITE:
            if not self.white_kingside and end == ConstantSquare(row=home_row, col=COL_F):
                return False
            if not self.white_queenside and end == ConstantSquare(row=home_row, col=COL_B):
                return False
        else:
            if not self.black_kingside and end == ConstantSquare(row=home_row, col=COL_F):
                return False
            if not self.black_queenside and end == ConstantSquare(row=home_row, col=COL_B):
                return False

        enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE

        if end == ConstantSquare(row=home_row, col=COL_F):
            rook_square = ConstantSquare(row=home_row, col=COL_H)
            between = [
                ConstantSquare(row=home_row, col=COL_E)
            ]  # Only check f1, the square king passes through
            king_path = [
                ConstantSquare(row=home_row, col=COL_E)
            ]  # King moves e1->f1->g1, attackable square is f1
            destination = ConstantSquare(row=home_row, col=COL_F)  # g1
            if not self._rook_at_original_square(color, rook_square):
                return False
        elif end == ConstantSquare(row=home_row, col=COL_B):
            rook_square = ConstantSquare(row=home_row, col=COL_A)
            between = [
                ConstantSquare(row=home_row, col=COL_C),
                ConstantSquare(row=home_row, col=COL_B),
            ]  # Check d1 and c1 for attacks
            king_path = [
                ConstantSquare(row=home_row, col=COL_C),
                ConstantSquare(row=home_row, col=COL_B),
            ]  # King passes through d1 to c1, attackable squares are d1,c1
            destination = ConstantSquare(row=home_row, col=COL_B)  # c1
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

        return True

    def is_valid_pawn_move(self, start: Square, end: Square) -> bool:
        """Check if a pawn move is valid."""
        piece = self.get_piece(start)
        if piece is None or piece.color != self.turn:
            return False

        start_row = start.row
        end_row = end.row

        # Pawns can move forward 1 or 2 squares from starting position
        if piece.color == Color.WHITE:
            if end_row > start_row:
                return False
            col_diff = abs(end.col - start.col)

            # Diagonal capture (must be adjacent diagonal)
            if end.col != start.col:
                is_en_passant_capture = end == self.en_passant_target
                is_capture = self.get_piece(end) is not None
                # Regular capture must be adjacent diagonal (row diff = 1, col diff = 1)
                # En passant has row diff = 2 but is handled by is_en_passant_capture check
                if is_en_passant_capture:
                    return col_diff == 1
                return abs(end_row - start_row) == 1 and col_diff == 1 and is_capture

            # Validate move distance
            distance = start_row - end_row  # White moves toward row 0 (decreasing)

            # 2-square move from starting position (ROW_2 to ROW_4)
            if start_row == ROW_2 and end_row == ROW_4:
                intermediate = offset_square(
                    ConstantSquare(row=start_row, col=end.col), -1, 0
                )
                return (
                    self.get_piece(end) is None
                    and self.get_piece(intermediate) is None
                    and distance == 2
                )

            # 1-square move from any position - must be exactly 1 square
            if distance == 1:
                return self.get_piece(end) is None
            return False
        else:
            if end_row < start_row:
                return False
            col_diff = abs(end.col - start.col)

            # Diagonal capture (must be adjacent diagonal)
            if end.col != start.col:
                is_en_passant_capture = end == self.en_passant_target
                is_capture = self.get_piece(end) is not None
                # Regular capture must be adjacent diagonal (row diff = 1, col diff = 1)
                # En passant has row diff = 2 but is handled by is_en_passant_capture check
                if is_en_passant_capture:
                    return col_diff == 1
                return abs(end_row - start_row) == 1 and col_diff == 1 and is_capture

            # Validate move distance
            distance = end_row - start_row  # Black moves toward row 7 (increasing)

            # 2-square move from starting position (ROW_7 to ROW_5)
            if start_row == ROW_7 and end_row == ROW_5:
                intermediate = offset_square(
                    ConstantSquare(row=start_row, col=end.col), 1, 0
                )
                return (
                    self.get_piece(end) is None
                    and self.get_piece(intermediate) is None
                    and distance == 2
                )

            # 1-square move from any position - must be exactly 1 square
            if distance == 1:
                return self.get_piece(end) is None
            return False

    def _is_valid_piece_move(self, start: Square, end: Square) -> bool:
        if isinstance(start, tuple):
            start = ConstantSquare(row=start[0], col=start[1])
        if isinstance(end, tuple):
            end = ConstantSquare(row=end[0], col=end[1])
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
                square = ConstantSquare(row=row, col=col)
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
            direction = -1 if piece.color == Color.WHITE else 1
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
                enemy_piece = self.get_piece(ConstantSquare(row=row, col=col))
                if enemy_piece is None or enemy_piece.color != enemy_color:
                    continue

                enemy_square = ConstantSquare(row=row, col=col)

                # Check if enemy piece attacks along a straight or diagonal line
                if enemy_piece.kind == PieceType.ROOK:
                    # Rook attacks on rank or file
                    if row == king_square.row or col == king_square.col:
                        # Check if piece is between enemy piece and king
                        if self._is_piece_between_enemy_and_king(
                            enemy_square, piece_square, king_square
                        ):
                            return True

                elif enemy_piece.kind == PieceType.BISHOP:
                    # Bishop attacks on diagonal
                    if abs(row - king_square.row) == abs(col - king_square.col):
                        # Check if piece is between enemy piece and king
                        if self._is_piece_between_enemy_and_king(
                            enemy_square, piece_square, king_square
                        ):
                            return True

                elif enemy_piece.kind == PieceType.QUEEN:
                    # Queen attacks on rank, file, or diagonal
                    if row == king_square.row or col == king_square.col:
                        # Check if piece is between enemy piece and king
                        if self._is_piece_between_enemy_and_king(
                            enemy_square, piece_square, king_square
                        ):
                            return True
                    if abs(row - king_square.row) == abs(col - king_square.col):
                        # Check if piece is between enemy piece and king
                        if self._is_piece_between_enemy_and_king(
                            enemy_square, piece_square, king_square
                        ):
                            return True

                elif enemy_piece.kind == PieceType.KNIGHT:
                    # Knight attacks are not pins (jumps over pieces)
                    pass

                elif enemy_piece.kind == PieceType.KING:
                    pass

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
            return (enemy_pos.col < piece_pos.col < king_pos.col) or (
                king_pos.col < piece_pos.col < enemy_pos.col
            )
        elif enemy_pos.col == piece_pos.col == king_pos.col:
            # Same file
            return (enemy_pos.row < piece_pos.row < king_pos.row) or (
                king_pos.row < piece_pos.row < enemy_pos.row
            )
        else:
            # Diagonal
            row_diff = enemy_pos.row - piece_pos.row
            col_diff = enemy_pos.col - piece_pos.col
            king_row_diff = king_pos.row - piece_pos.row
            king_col_diff = king_pos.col - piece_pos.col
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
                self.get_piece(ConstantSquare(row=current_row, col=current_col))
                is not None
            ):
                return False
            current_row += step_row
            current_col += step_col

        return True

    def is_square_attacked(self, square: Square, by_color: Color) -> bool:
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(square)
                if piece is None or piece.color != by_color:
                    continue
                if self._piece_attacks_square(
                    ConstantSquare(row=row, col=col), piece, square
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
        if piece.kind == PieceType.PAWN and end_pos.row in {0, 7}:
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
                piece = self.get_piece(ConstantSquare(row=start_row, col=start_col))
                if piece is None or piece.color != side:
                    continue

                start = ConstantSquare(row=start_row, col=start_col)
                for end_row in range(8):
                    for end_col in range(8):
                        end = ConstantSquare(row=end_row, col=end_col)
                        for promotion in self._promotion_options_for_move(piece, end):
                            # Check if this move would expose the king (pin)
                            if piece.kind != PieceType.KNIGHT:  # Knights can jump pins
                                if self._is_piece_pinned(start, piece.color):
                                    # Check if this move would leave the king in check
                                    simulated = self.clone()
                                    simulated._apply_move_unchecked(
                                        start, end, promotion=promotion
                                    )
                                    if simulated.is_in_check(piece.color):
                                        continue

                            simulated = self.clone()
                            simulated.turn = side
                            if simulated.make_move(start, end, promotion=promotion):
                                legal_moves.append((start, end, promotion))

        return legal_moves

    def is_checkmate(self, color: Optional[Color] = None) -> bool:
        side = self.turn if color is None else color
        return self.is_in_check(side) and len(self.get_legal_moves(side)) == 0

    def is_stalemate(self, color: Optional[Color] = None) -> bool:
        side = self.turn if color is None else color
        return not self.is_in_check(side) and len(self.get_legal_moves(side)) == 0

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
            captured_row = (
                end_pos.row + 1 if start_piece.color == Color.WHITE else end_pos.row - 1
            )
            captured_piece = self.get_piece(
                ConstantSquare(row=captured_row, col=end_pos.col)
            )
            self.clear_square(ConstantSquare(row=captured_row, col=end_pos.col))
            if (
                captured_piece is not None
                and captured_piece.kind == PieceType.ROOK
                and captured_piece.color != start_piece.color
            ):
                self._clear_castling_right_for_captured_rook(
                    ConstantSquare(row=captured_row, col=end_pos.col)
                )

        self.set_piece(end_pos, start_piece)
        self.clear_square(start_pos)

        if start_piece.kind == PieceType.KING and self._is_castling_move(
            start_pos, end_pos
        ):
            home_row = start_pos.row
            if end_pos.col == 6:
                rook_from = ConstantSquare(row=home_row, col=COL_H)
                rook_to = ConstantSquare(row=home_row, col=COL_E)
            else:
                rook_from = ConstantSquare(row=home_row, col=COL_A)
                rook_to = ConstantSquare(row=home_row, col=COL_C)

            rook_piece = self.get_piece(rook_from)
            self.clear_square(rook_from)
            self.set_piece(rook_to, rook_piece)

        if start_piece.kind == PieceType.PAWN and abs(end_pos.row - start_pos.row) == 2:
            self.en_passant_target = ConstantSquare(
                row=(start_pos.row + end_pos.row) // 2, col=end_pos.col
            )
        else:
            self.en_passant_target = None

        if start_piece.kind == PieceType.PAWN and end_pos.row in {0, 7}:
            self.set_piece(
                end_pos,
                create_piece(
                    start_piece.color,
                    promotion if promotion is not None else PieceType.QUEEN,
                ),
            )

    def _clear_castling_right_for_captured_rook(self, square: Square) -> None:
        if square == ConstantSquare(row=ROW_8, col=COL_A):
            self.white_queenside = False
        elif square == ConstantSquare(row=ROW_8, col=COL_H):
            self.white_kingside = False
        elif square == ConstantSquare(row=ROW_7, col=COL_A):
            self.black_queenside = False
        elif square == ConstantSquare(row=ROW_7, col=COL_H):
            self.black_kingside = False

    def _update_castling_rights_for_move(
        self,
        start_pos: Square,
        end_pos: Square,
        moving_piece: Piece,
        captured_piece: Optional[Piece],
    ) -> None:
        if moving_piece.kind == PieceType.KING:
            if moving_piece.color == Color.WHITE:
                self.white_kingside = False
                self.white_queenside = False
            else:
                self.black_kingside = False
                self.black_queenside = False

        if moving_piece.kind == PieceType.ROOK:
            if start_pos == ConstantSquare(row=ROW_8, col=COL_A):
                self.white_queenside = False
            elif start_pos == ConstantSquare(row=ROW_8, col=COL_H):
                self.white_kingside = False
            elif start_pos == ConstantSquare(row=ROW_7, col=COL_A):
                self.black_queenside = False
            elif start_pos == ConstantSquare(row=ROW_7, col=COL_H):
                self.white_kingside = False
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

        if end_pos.row not in {ROW_1, ROW_8}:
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
            start_pos = ConstantSquare(row=start_pos[0], col=start_pos[1])
        if isinstance(end_pos, tuple):
            end_pos = ConstantSquare(row=end_pos[0], col=end_pos[1])
        start_piece = self.get_piece(start_pos)
        if start_piece is None or start_piece.color != self.turn:
            return False

        if not self._is_valid_promotion_choice(start_piece, end_pos, promotion):
            return False

        if not self._is_valid_piece_move(start_pos, end_pos):
            return False

        # Check if piece is pinned (moving it would expose king to check)
        if start_piece.kind != PieceType.KNIGHT:  # Knights can jump pins
            if self._is_piece_pinned(start_pos, start_piece.color):
                simulated = self.clone()
                simulated._apply_move_unchecked(start_pos, end_pos, promotion=promotion)
                if simulated.is_in_check(start_piece.color):
                    return False

        simulated = self.clone()
        simulated._apply_move_unchecked(start_pos, end_pos, promotion=promotion)

        # Determine promotion piece (default to QUEEN if None)
        promotion_piece = promotion if promotion is not None else PieceType.QUEEN

        if start_piece.kind == PieceType.PAWN and end_pos.row in {ROW_1, ROW_8}:
            simulated.set_piece(
                end_pos,
                create_piece(start_piece.color, promotion_piece),
            )

        if simulated.is_in_check(start_piece.color):
            return False

        self._apply_move_unchecked(start_pos, end_pos, promotion=promotion)

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
