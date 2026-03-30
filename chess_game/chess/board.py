from __future__ import annotations

from typing import Optional

from chess_game.chess.types import Color, Piece, PieceType

Square = tuple[int, int]
LegalMove = tuple[Square, Square, Optional[PieceType]]


def create_piece(color: Color, piece_type: PieceType) -> Piece:
    """Create a typed chess piece."""
    return Piece(color=color, kind=piece_type)


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
        board: list[list[Optional[Piece]]] = [
            [None for _ in range(8)] for _ in range(8)
        ]
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
        return (
            piece1 is not None and piece2 is not None and piece1.color == piece2.color
        )

    def is_opponent(self, row1: int, col1: int, row2: int, col2: int) -> bool:
        piece1 = self.get_piece(row1, col1)
        piece2 = self.get_piece(row2, col2)
        return (
            piece1 is not None and piece2 is not None and piece1.color != piece2.color
        )

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

        if self._is_castling_move(start, end):
            return self._can_castle(start, end, piece.color)

        row_diff = abs(end[0] - start[0])
        col_diff = abs(end[1] - start[1])
        if max(row_diff, col_diff) != 1:
            return False
        return self._destination_occupiable(piece, end)

    def _is_castling_move(self, start: Square, end: Square) -> bool:
        return start[0] == end[0] and start[1] == 4 and end[1] in {2, 6}

    def _rook_at_original_square(self, color: Color, rook_square: Square) -> bool:
        """Check if the rook is still at its original square."""
        piece = self.get_piece(*rook_square)
        return (
            piece is not None and piece.kind == PieceType.ROOK and piece.color == color
        )

    def _can_castle(self, start: Square, end: Square, color: Color) -> bool:
        home_row = 7 if color == Color.WHITE else 0
        if start != (home_row, 4):
            return False

        # Check if castling rights are still valid
        if color == Color.WHITE:
            if not self.white_kingside and end == (home_row, 6):
                return False
            if not self.white_queenside and end == (home_row, 2):
                return False
        else:
            if not self.black_kingside and end == (home_row, 6):
                return False
            if not self.black_queenside and end == (home_row, 2):
                return False

        enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE

        if end == (home_row, 6):
            rook_square = (home_row, 7)
            between = [(home_row, 5)]  # Only check f1, the square king passes through
            king_path = [
                (home_row, 5)
            ]  # King moves e1->f1->g1, attackable square is f1
            destination = (home_row, 6)  # g1
            if not self._rook_at_original_square(color, rook_square):
                return False
        elif end == (home_row, 2):
            rook_square = (home_row, 0)
            between = [(home_row, 3), (home_row, 2)]  # Check d1 and c1 for attacks
            king_path = [
                (home_row, 3),
                (home_row, 2),
            ]  # King passes through d1 to c1, attackable squares are d1,c1
            destination = (home_row, 2)  # c1
            if not self._rook_at_original_square(color, rook_square):
                return False
        else:
            return False

        rook_piece = self.get_piece(*rook_square)
        if (
            rook_piece is None
            or rook_piece.kind != PieceType.ROOK
            or rook_piece.color != color
        ):
            return False

        if any(not self.is_empty(*square) for square in between):
            return False

        if not self.is_empty(*destination):
            return False

        if self.is_in_check(color):
            return False

        if any(self.is_square_attacked(square, enemy_color) for square in king_path):
            return False

        return True

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
            # Straight move (forward)
            if row_diff == direction and self.is_empty(*end):
                return True
            if row_diff == 2 * direction and start[0] == start_row:
                middle = (start[0] + direction, start[1])
                return self.is_empty(*middle) and self.is_empty(*end)
            # Promotion move: can move to promotion rank (row 0 for white, row 7 for black)
            if start[0] == start_row and self.is_empty(*end):
                # Check if destination is on promotion rank
                if piece.color == Color.WHITE and end[0] == 0:
                    # White promotion: from rank 2 (row 6) to rank 8 (row 0)
                    # Either 2-square move or 1-square move from rank 7
                    if start[0] == 6:
                        # Two-square move (row_diff = -6 for white, +6 for black)
                        if abs(row_diff) == 6:
                            middle = (start[0] + direction, start[1])
                            return self.is_empty(*middle)
                    # One-square move from rank 7 (already on rank 7, moving to rank 8)
                    elif start[0] == 1:
                        return True
                elif piece.color == Color.BLACK and end[0] == 7:
                    # Black promotion: from rank 7 (row 1) to rank 1 (row 7)
                    # Either 2-square move or 1-square move from rank 2
                    if start[0] == 1:
                        # Two-square move (row_diff = -6 for white, +6 for black)
                        if abs(row_diff) == 6:
                            middle = (start[0] + direction, start[1])
                            return self.is_empty(*middle)
                    # One-square move from rank 2 (already on rank 2, moving to rank 1)
                    elif start[0] == 6:
                        return True
                return False
            return False

        if abs(col_diff) == 1:
            # En passant capture (horizontal move, same row)
            if self.en_passant_target == end and row_diff == 0:
                captured_row = end[0] + 1 if piece.color == Color.WHITE else end[0] - 1
                captured_piece = self.get_piece(captured_row, end[1])
                return (
                    captured_piece is not None
                    and captured_piece.kind == PieceType.PAWN
                    and captured_piece.color != piece.color
                )
            # Regular capture (diagonal forward)
            if row_diff == direction:
                end_piece = self.get_piece(*end)
                if end_piece is not None:
                    return end_piece.color != piece.color
                # En passant capture (diagonal, target is the empty square)
                if self.en_passant_target == end:
                    captured_row = (
                        end[0] + 1 if piece.color == Color.WHITE else end[0] - 1
                    )
                    captured_piece = self.get_piece(captured_row, end[1])
                    return (
                        captured_piece is not None
                        and captured_piece.kind == PieceType.PAWN
                        and captured_piece.color != piece.color
                    )
            return False
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

    def find_king(self, color: Color) -> Optional[Square]:
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if (
                    piece is not None
                    and piece.color == color
                    and piece.kind == PieceType.KING
                ):
                    return (row, col)
        return None

    def _piece_attacks_square(
        self, start: Square, piece: Piece, target: Square
    ) -> bool:
        row_diff = target[0] - start[0]
        col_diff = target[1] - start[1]

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
            if start[0] != target[0] and start[1] != target[1]:
                return False
            return self._path_is_clear(start, target)

        if piece.kind == PieceType.QUEEN:
            if start == target:
                return False
            is_straight = start[0] == target[0] or start[1] == target[1]
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
                enemy_piece = self.get_piece(row, col)
                if enemy_piece is None or enemy_piece.color != enemy_color:
                    continue

                # Check if enemy piece attacks along a straight or diagonal line
                if enemy_piece.kind == PieceType.ROOK:
                    # Rook attacks on rank or file
                    if row == king_square[0] or col == king_square[1]:
                        # Check if piece is between enemy piece and king
                        if self._is_piece_between_enemy_and_king(
                            (row, col), piece_square, king_square
                        ):
                            return True

                elif enemy_piece.kind == PieceType.BISHOP:
                    # Bishop attacks on diagonal
                    if abs(row - king_square[0]) == abs(col - king_square[1]):
                        # Check if piece is between enemy piece and king
                        if self._is_piece_between_enemy_and_king(
                            (row, col), piece_square, king_square
                        ):
                            return True

                elif enemy_piece.kind == PieceType.QUEEN:
                    # Queen attacks on rank, file, or diagonal
                    if row == king_square[0] or col == king_square[1]:
                        # Check if piece is between enemy piece and king
                        if self._is_piece_between_enemy_and_king(
                            (row, col), piece_square, king_square
                        ):
                            return True
                    if abs(row - king_square[0]) == abs(col - king_square[1]):
                        # Check if piece is between enemy piece and king
                        if self._is_piece_between_enemy_and_king(
                            (row, col), piece_square, king_square
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
        if enemy_pos[0] != piece_pos[0] or piece_pos[0] != king_pos[0]:
            # Not on same rank
            if enemy_pos[1] != piece_pos[1] or piece_pos[1] != king_pos[1]:
                # Not on same file
                if abs(enemy_pos[0] - king_pos[0]) != abs(enemy_pos[1] - king_pos[1]):
                    # Not on same diagonal
                    return False

        # Check if piece is geometrically between enemy and king (exclusive)
        # For rank: enemy_row < piece_row < king_row or king_row < piece_row < enemy_row
        # For file: enemy_col < piece_col < king_col or king_col < piece_col < enemy_col
        # For diagonal: check both row and col ordering
        if enemy_pos[0] == piece_pos[0] == king_pos[0]:
            # Same rank
            return (enemy_pos[1] < piece_pos[1] < king_pos[1]) or (
                king_pos[1] < piece_pos[1] < enemy_pos[1]
            )
        elif enemy_pos[1] == piece_pos[1] == king_pos[1]:
            # Same file
            return (enemy_pos[0] < piece_pos[0] < king_pos[0]) or (
                king_pos[0] < piece_pos[0] < enemy_pos[0]
            )
        else:
            # Diagonal
            row_diff = enemy_pos[0] - piece_pos[0]
            col_diff = enemy_pos[1] - piece_pos[1]
            king_row_diff = king_pos[0] - piece_pos[0]
            king_col_diff = king_pos[1] - piece_pos[1]
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

    def is_square_attacked(self, square: Square, by_color: Color) -> bool:
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece is None or piece.color != by_color:
                    continue
                if self._piece_attacks_square((row, col), piece, square):
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
        if piece.kind == PieceType.PAWN and end_pos[0] in {0, 7}:
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
                piece = self.get_piece(start_row, start_col)
                if piece is None or piece.color != side:
                    continue

                start = (start_row, start_col)
                for end_row in range(8):
                    for end_col in range(8):
                        end = (end_row, end_col)
                        for promotion in self._promotion_options_for_move(piece, end):
                            # Check if this move would expose the king (pin)
                            if piece.kind != PieceType.KNIGHT:  # Knights can jump pins
                                if self._is_piece_pinned(start, piece.color):
                                    # Check if this move would leave the king in check
                                    simulated = self.clone()
                                    simulated._apply_move_unchecked(start, end)
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

    def _apply_move_unchecked(self, start_pos: Square, end_pos: Square) -> None:
        start_piece = self.get_piece(*start_pos)
        if start_piece is None:
            return

        captured_piece = self.get_piece(*end_pos)
        self._update_castling_rights_for_move(
            start_pos, end_pos, start_piece, captured_piece
        )

        is_en_passant_capture = (
            start_piece.kind == PieceType.PAWN
            and self.en_passant_target == end_pos
            and self.get_piece(*end_pos) is None
            and start_pos[1] != end_pos[1]
        )

        if is_en_passant_capture:
            captured_row = (
                end_pos[0] + 1 if start_piece.color == Color.WHITE else end_pos[0] - 1
            )
            captured_piece = self.get_piece(captured_row, end_pos[1])
            self.clear_square(captured_row, end_pos[1])
            if (
                captured_piece is not None
                and captured_piece.kind == PieceType.ROOK
                and captured_piece.color != start_piece.color
            ):
                self._clear_castling_right_for_captured_rook((captured_row, end_pos[1]))

        self.set_piece(*end_pos, start_piece)
        self.clear_square(*start_pos)

        if start_piece.kind == PieceType.KING and self._is_castling_move(
            start_pos, end_pos
        ):
            home_row = start_pos[0]
            if end_pos[1] == 6:
                rook_from = (home_row, 7)
                rook_to = (home_row, 5)
            else:
                rook_from = (home_row, 0)
                rook_to = (home_row, 3)

            rook_piece = self.get_piece(*rook_from)
            self.clear_square(*rook_from)
            self.set_piece(*rook_to, rook_piece)

        if start_piece.kind == PieceType.PAWN and abs(end_pos[0] - start_pos[0]) == 2:
            self.en_passant_target = ((start_pos[0] + end_pos[0]) // 2, end_pos[1])
        else:
            self.en_passant_target = None

        if start_piece.kind == PieceType.PAWN and end_pos[0] in {0, 7}:
            self.set_piece(
                end_pos[0], end_pos[1], create_piece(start_piece.color, PieceType.QUEEN)
            )

    def _clear_castling_right_for_captured_rook(self, square: Square) -> None:
        if square == (7, 0):
            self.white_queenside = False
        elif square == (7, 7):
            self.white_kingside = False
        elif square == (0, 0):
            self.black_queenside = False
        elif square == (0, 7):
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
            if start_pos == (7, 0):
                self.white_queenside = False
            elif start_pos == (7, 7):
                self.white_kingside = False
            elif start_pos == (0, 0):
                self.black_queenside = False
            elif start_pos == (0, 7):
                self.black_kingside = False

        if captured_piece is not None and captured_piece.kind == PieceType.ROOK:
            self._clear_castling_right_for_captured_rook(end_pos)

    def _is_valid_promotion_choice(
        self,
        piece: Piece,
        end_pos: Square,
        promotion: Optional[PieceType],
    ) -> bool:
        if promotion is None:
            return True

        if piece.kind != PieceType.PAWN:
            return False

        if end_pos[0] not in {0, 7}:
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
        if not self.is_valid_position(*start_pos) or not self.is_valid_position(
            *end_pos
        ):
            return False

        start_piece = self.get_piece(*start_pos)
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
                simulated._apply_move_unchecked(start_pos, end_pos)
                if simulated.is_in_check(start_piece.color):
                    return False

        simulated = self.clone()
        simulated._apply_move_unchecked(start_pos, end_pos)

        if (
            start_piece.kind == PieceType.PAWN
            and end_pos[0] in {0, 7}
            and promotion is not None
        ):
            simulated.set_piece(
                end_pos[0],
                end_pos[1],
                create_piece(start_piece.color, promotion),
            )

        if simulated.is_in_check(start_piece.color):
            return False

        self._apply_move_unchecked(start_pos, end_pos)

        if (
            start_piece.kind == PieceType.PAWN
            and end_pos[0] in {0, 7}
            and promotion is not None
        ):
            self.set_piece(
                end_pos[0], end_pos[1], create_piece(start_piece.color, promotion)
            )

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
