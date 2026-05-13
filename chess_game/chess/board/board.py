"""Main Board class - orchestrator for chess game logic.

This module provides the Board class which owns all game state and delegates
to specialized modules for validation, execution, and special rules.
"""

from __future__ import annotations

import copy
from typing import List, Optional, Tuple

from chess_game.chess.color import Color
from chess_game.chess.types import PieceType, Piece
from chess_game.chess.board.move_validation import MoveValidator
from chess_game.chess.board.move_execution import MoveExecutor
from chess_game.chess.board.castling import CastlingValidator
from chess_game.chess.board.promotion import PromotionValidator
from chess_game.chess.board.en_passant import EnPassantValidator
from chess_game.chess.constants import (
    ROW_1,
    ROW_2,
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
    ConstantSquare,
    get_row_constant,
    get_col_constant,
    get_square_constant,
)

LegalMove = tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]


def create_piece(
    color: Color, piece_type: PieceType, square: Optional[ConstantSquare] = None
) -> Piece:
    """Create a typed chess piece."""
    if isinstance(square, tuple):
        square = ConstantSquare(
            row=get_row_constant(square[0]), col=get_col_constant(square[1])
        )
    piece = Piece(color=color, kind=piece_type)
    if square is not None:
        piece._square = square
    return piece


def offset_square(s: ConstantSquare, dr: int, dc: int) -> ConstantSquare:
    """Offset square by delta row and column."""
    if isinstance(s, tuple):
        s = ConstantSquare(row=get_row_constant(s[0]), col=get_col_constant(s[1]))
    new_row = int(s.row) + dr
    new_col = int(s.col) + dc
    return ConstantSquare(row=get_row_constant(new_row), col=get_col_constant(new_col))


def forward_one(s: ConstantSquare, color: Color) -> ConstantSquare:
    """Move one square forward for a pawn."""
    if color == Color.WHITE:
        return offset_square(s, -1, 0)  # White moves toward rank 8 (row 0)
    else:
        return offset_square(s, 1, 0)  # Black moves toward rank 1 (row 7)


class Board:
    """Main Board class owning all game state.

    State attributes:
        board: 8x8 list of Piece or None
        turn: Color whose turn it is
        en_passant_target: Optional en passant square
        white_kingside / white_queenside / black_kingside / black_queenside: castling rights
    """

    def __init__(self) -> None:
        self.board: List[List[Optional[Piece]]] = self._create_board()
        self.turn = Color.WHITE
        self.en_passant_target: Optional[ConstantSquare] = None
        self.white_kingside = True
        self.white_queenside = True
        self.black_kingside = True
        self.black_queenside = True

        self._move_validator = MoveValidator(self)
        self._move_executor = MoveExecutor(self)
        self._promotion_validator = PromotionValidator(self)
        self._en_passant_validator = EnPassantValidator(self)

    # ---- board accessors ----

    def get_piece(self, square: ConstantSquare) -> Optional[Piece]:
        """Get piece at square."""
        if isinstance(square, tuple):
            square = ConstantSquare(
                row=get_row_constant(square[0]), col=get_col_constant(square[1])
            )
        if not (0 <= int(square.row) < 8 and 0 <= int(square.col) < 8):
            return None
        return self.board[int(square.row)][int(square.col)]

    def set_piece(self, square: ConstantSquare, piece: Optional[Piece]) -> None:
        """Set piece at square."""
        if isinstance(square, tuple):
            square = ConstantSquare(
                row=get_row_constant(square[0]), col=get_col_constant(square[1])
            )
        if not (0 <= int(square.row) < 8 and 0 <= int(square.col) < 8):
            raise ValueError(f"Invalid square: {square}")
        if piece is not None:
            piece._square = square
        self.board[int(square.row)][int(square.col)] = piece

    def clear_square(self, square: ConstantSquare) -> None:
        """Clear square."""
        self.set_piece(square, None)

    def is_empty(self, square: ConstantSquare) -> bool:
        """Check if square is empty."""
        return self.get_piece(square) is None

    def get_color_at(self, square: ConstantSquare) -> Optional[Color]:
        """Get color of piece at square."""
        piece = self.get_piece(square)
        return piece.color if piece else None

    def get_piece_type_at(self, square: ConstantSquare) -> Optional[PieceType]:
        """Get piece type at square."""
        piece = self.get_piece(square)
        return piece.kind if piece else None

    def find_king(self, color: Color) -> Optional[ConstantSquare]:
        """Find king of given color."""
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

    def is_valid_position(self, square: ConstantSquare) -> bool:
        """Validate square coordinates."""
        return 0 <= int(square.row) < 8 and 0 <= int(square.col) < 8

    def is_on_board(self, square: ConstantSquare) -> bool:
        """Check if square is on board."""
        return self.is_valid_position(square)

    def is_same_color(self, square1: ConstantSquare, square2: ConstantSquare) -> bool:
        """Check if pieces at both squares have same color."""
        piece1 = self.get_piece(square1)
        piece2 = self.get_piece(square2)
        return (
            piece1 is not None and piece2 is not None and piece1.color == piece2.color
        )

    def is_opponent(self, square1: ConstantSquare, square2: ConstantSquare) -> bool:
        """Check if pieces at both squares are opponents."""
        piece1 = self.get_piece(square1)
        piece2 = self.get_piece(square2)
        return (
            piece1 is not None and piece2 is not None and piece1.color != piece2.color
        )

    # ---- board creation ----

    def _create_board(self) -> List[List[Optional[Piece]]]:
        """Create a standard chess board with starting position.

        Canonical layout: row 0 = rank 8 (black), row 7 = rank 1 (white).
        """
        board: List[List[Optional[Piece]]] = [
            [None for _ in range(8)] for _ in range(8)
        ]

        # Black pieces (rows 0-1 = ranks 8-7)
        board[0] = [
            create_piece(Color.BLACK, PieceType.ROOK, ConstantSquare(row=ROW_8, col=COL_A)),
            create_piece(Color.BLACK, PieceType.KNIGHT, ConstantSquare(row=ROW_8, col=COL_B)),
            create_piece(Color.BLACK, PieceType.BISHOP, ConstantSquare(row=ROW_8, col=COL_C)),
            create_piece(Color.BLACK, PieceType.QUEEN, ConstantSquare(row=ROW_8, col=COL_D)),
            create_piece(Color.BLACK, PieceType.KING, ConstantSquare(row=ROW_8, col=COL_E)),
            create_piece(Color.BLACK, PieceType.BISHOP, ConstantSquare(row=ROW_8, col=COL_F)),
            create_piece(Color.BLACK, PieceType.KNIGHT, ConstantSquare(row=ROW_8, col=COL_G)),
            create_piece(Color.BLACK, PieceType.ROOK, ConstantSquare(row=ROW_8, col=COL_H)),
        ]
        board[1] = [
            create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_A)),
            create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_B)),
            create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_C)),
            create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_D)),
            create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_E)),
            create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_F)),
            create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_G)),
            create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_H)),
        ]

        # White pieces (rows 6-7 = ranks 2-1)
        board[6] = [
            create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_A)),
            create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_B)),
            create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_C)),
            create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_D)),
            create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_E)),
            create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_F)),
            create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_G)),
            create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_H)),
        ]
        board[7] = [
            create_piece(Color.WHITE, PieceType.ROOK, ConstantSquare(row=ROW_1, col=COL_A)),
            create_piece(Color.WHITE, PieceType.KNIGHT, ConstantSquare(row=ROW_1, col=COL_B)),
            create_piece(Color.WHITE, PieceType.BISHOP, ConstantSquare(row=ROW_1, col=COL_C)),
            create_piece(Color.WHITE, PieceType.QUEEN, ConstantSquare(row=ROW_1, col=COL_D)),
            create_piece(Color.WHITE, PieceType.KING, ConstantSquare(row=ROW_1, col=COL_E)),
            create_piece(Color.WHITE, PieceType.BISHOP, ConstantSquare(row=ROW_1, col=COL_F)),
            create_piece(Color.WHITE, PieceType.KNIGHT, ConstantSquare(row=ROW_1, col=COL_G)),
            create_piece(Color.WHITE, PieceType.ROOK, ConstantSquare(row=ROW_1, col=COL_H)),
        ]

        return board

    def clear_board(self) -> None:
        """Clear all pieces from the board."""
        for row in range(8):
            for col in range(8):
                self.clear_square(get_square_constant(row, col))

    # ---- piece-specific move validation (delegates to MoveValidator) ----

    def is_valid_rook_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate rook move (straight line)."""
        piece = self.get_piece(from_square)
        if piece is None or piece.kind != PieceType.ROOK:
            return False
        return self._move_validator.is_valid_move(from_square, to_square)

    def is_valid_bishop_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate bishop move (diagonal)."""
        piece = self.get_piece(from_square)
        if piece is None or piece.kind != PieceType.BISHOP:
            return False
        return self._move_validator.is_valid_move(from_square, to_square)

    def is_valid_queen_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate queen move (straight or diagonal)."""
        piece = self.get_piece(from_square)
        if piece is None or piece.kind != PieceType.QUEEN:
            return False
        return self._move_validator.is_valid_move(from_square, to_square)

    def is_valid_knight_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate knight move (L-shape)."""
        piece = self.get_piece(from_square)
        if piece is None or piece.kind != PieceType.KNIGHT:
            return False
        return self._move_validator.is_valid_move(from_square, to_square)

    def is_valid_king_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate king move (one square in any direction)."""
        piece = self.get_piece(from_square)
        if piece is None or piece.kind != PieceType.KING:
            return False
        return self._move_validator.is_valid_move(from_square, to_square)

    def is_valid_pawn_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate pawn move."""
        piece = self.get_piece(from_square)
        if piece is None or piece.kind != PieceType.PAWN:
            return False
        return self._move_validator.is_valid_move(from_square, to_square)

    # ---- check / checkmate / stalemate ----

    def is_in_check(self, color: Color) -> bool:
        """Check if specified color's king is in check."""
        king_sq = self.find_king(color)
        if king_sq is None:
            return False
        enemy = Color.BLACK if color == Color.WHITE else Color.WHITE
        return CastlingValidator._is_square_attacked(self, king_sq, enemy)

    def is_checkmate(self) -> bool:
        """Check if current side-to-move is in checkmate."""
        if not self.is_in_check(self.turn):
            return False
        return len(self.get_legal_moves()) == 0

    def is_stalemate(self) -> bool:
        """Check if current side-to-move is in stalemate."""
        if self.is_in_check(self.turn):
            return False
        return len(self.get_legal_moves()) == 0

    # ---- clone ----

    def clone(self) -> Board:
        """Create a deep copy of the board."""
        cloned = Board.__new__(Board)
        cloned.board = [row[:] for row in self.board]
        # Deep copy pieces so they're independent
        cloned.board = [
            [copy.deepcopy(p) if p is not None else None for p in row]
            for row in cloned.board
        ]
        cloned.turn = self.turn
        cloned.en_passant_target = self.en_passant_target
        cloned.white_kingside = self.white_kingside
        cloned.white_queenside = self.white_queenside
        cloned.black_kingside = self.black_kingside
        cloned.black_queenside = self.black_queenside
        cloned._move_validator = MoveValidator(cloned)
        cloned._move_executor = MoveExecutor(cloned)
        cloned._promotion_validator = PromotionValidator(cloned)
        cloned._en_passant_validator = EnPassantValidator(cloned)
        return cloned

    # ---- legal moves ----

    def get_legal_moves(
        self, square: Optional[ConstantSquare] = None
    ) -> List[Tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]]:
        """Get all legal moves from the specified square, or all side-to-move legal moves."""
        if square is None:
            return self._move_validator.get_legal_moves()
        piece = self.get_piece(square)
        if piece is None:
            return []
        return self._move_validator.get_legal_moves(square, piece.kind)

    # ---- make_move ----

    def make_move(
        self,
        start_pos: ConstantSquare,
        end_pos: ConstantSquare,
        promotion: Optional[PieceType] = None,
    ) -> bool:
        """Make a move on the board."""
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

        if not self._promotion_validator.is_valid_promotion_choice(
            start_piece, end_pos, promotion
        ):
            return False

        # Castling
        if (
            start_piece.kind == PieceType.KING
            and CastlingValidator.is_castling_move(start_pos, end_pos)
        ):
            if not CastlingValidator.can_castle(
                self, start_pos, end_pos, start_piece.color, start_piece.color
            ):
                return False

        # En passant
        is_en_passant = (
            start_piece.kind == PieceType.PAWN
            and self.en_passant_target == end_pos
            and start_pos.col != end_pos.col
        )

        if is_en_passant:
            if not self._en_passant_validator.validate_en_passant_capture(
                start_pos, end_pos, start_piece
            ):
                return False
        else:
            if not self._move_validator.is_move_legal(start_pos, end_pos):
                return False

        # Execute
        success = self._move_executor.execute_move(
            start_pos, end_pos, promotion, start_piece
        )
        if not success:
            return False

        # Update en passant target
        self._en_passant_validator.clear_en_passant_target_if_needed(
            start_pos, end_pos, start_piece
        )
        self._en_passant_validator.set_en_passant_target_if_valid(
            start_pos, end_pos, start_piece
        )

        # Switch turn
        self.turn = Color.BLACK if self.turn == Color.WHITE else Color.WHITE

        return True

    # ---- display ----

    def display(self) -> None:
        """Display the board to console."""
        print("  a b c d e f g h")
        for row_index, row in enumerate(self.board):
            rank = 8 - row_index
            symbols = []
            for piece in row:
                if piece is None:
                    symbols.append(".")
                elif piece.color == Color.WHITE:
                    symbols.append(piece.kind.name.upper())
                else:
                    symbols.append(piece.kind.name.lower())
            print(f"{rank}  {''.join(symbols)}")
        print(f"{' ' * 10}{self.turn.name}")
