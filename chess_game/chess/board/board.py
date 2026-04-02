"""Main Board class - orchestrator for chess game logic.

This module provides the Board class which orchestrates all chess game logic
by delegating to specialized modules for validation, execution, and special rules.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from chess_game.chess.color import Color
from chess_game.chess.types import PieceType
from chess_game.chess.types import Piece
from chess_game.chess.board.board_state import BoardState as BoardState
from chess_game.chess.board.move_validation import MoveValidator
from chess_game.chess.board.move_execution import MoveExecutor
from chess_game.chess.board.castling import CastlingValidator
from chess_game.chess.board.promotion import PromotionValidator
from chess_game.chess.board.en_passant import EnPassantValidator
from chess_game.chess.constants import (
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
        return offset_square(s, 1, 0)
    else:
        return offset_square(s, -1, 0)


class Board:
    """Main Board class - orchestrator for chess game logic.

    Delegates all logic to specialized modules:
    - MoveValidator: Validates move legality
    - MoveExecutor: Executes moves on board state
    - CastlingValidator: Castling rules
    - PromotionValidator: Promotion rules
    - EnPassantValidator: En passant rules
    """

    def __init__(self) -> None:
        """Initialize the board with all components."""
        self.board: List[List[Optional[Piece]]] = self._create_board()
        self.turn = Color.WHITE
        self.white_kingside = True
        self.white_queenside = True
        self.black_kingside = True
        self.black_queenside = True

        # Create component instances
        self._board_state = BoardState(
            board=self.board,
            turn=self.turn,
            en_passant_target=None,
            white_kingside=self.white_kingside,
            white_queenside=self.white_queenside,
            black_kingside=self.black_kingside,
            black_queenside=self.black_queenside,
        )
        self._move_validator = MoveValidator(self._board_state)
        self._move_executor = MoveExecutor(self._board_state)
        self._castling_validator = CastlingValidator()
        self._promotion_validator = PromotionValidator(self._board_state)
        self._en_passant_validator = EnPassantValidator(self._board_state)

    @property
    def en_passant_target(self) -> Optional[ConstantSquare]:
        """Get the en passant target square."""
        return self._board_state.en_passant_target

    @en_passant_target.setter
    def en_passant_target(self, value: Optional[ConstantSquare]) -> None:
        """Set the en passant target square."""
        if hasattr(self, "_board_state"):
            self._board_state.en_passant_target = value
        else:
            object.__setattr__(self, "en_passant_target", value)

    def _create_board(self) -> List[List[Optional[Piece]]]:
        """Create a standard chess board."""
        board: List[List[Optional[Piece]]] = [
            [None for _ in range(8)] for _ in range(8)
        ]

        # Black pieces (rows 0-1, ranks 8-7)
        for col in range(8):
            piece_type = (
                PieceType.ROOK
                if col == 0 or col == 7
                else PieceType.KNIGHT
                if col == 1 or col == 6
                else PieceType.BISHOP
                if col == 2 or col == 5
                else PieceType.QUEEN
                if col == 3
                else PieceType.KING
                if col == 4
                else None
            )
            board[0][col] = create_piece(Color.BLACK, piece_type, square=(0, col))

        for col in range(8):
            board[1][col] = create_piece(Color.BLACK, PieceType.PAWN, square=(1, col))

        # White pieces (rows 6-7, ranks 2-1)
        for col in range(8):
            board[6][col] = create_piece(Color.WHITE, PieceType.PAWN, square=(6, col))

        for col in range(8):
            piece_type = (
                PieceType.ROOK
                if col == 0 or col == 7
                else PieceType.KNIGHT
                if col == 1 or col == 6
                else PieceType.BISHOP
                if col == 2 or col == 5
                else PieceType.QUEEN
                if col == 3
                else PieceType.KING
                if col == 4
                else None
            )
            board[7][col] = create_piece(Color.WHITE, piece_type, square=(7, col))

        return board

    def _get_square_from_tuple(self, s: ConstantSquare) -> ConstantSquare:
        """Convert tuple or Square to ConstantSquare."""
        if isinstance(s, tuple):
            return ConstantSquare(
                row=get_row_constant(s[0]), col=get_col_constant(s[1])
            )
        return s

    def get_piece(self, square: ConstantSquare) -> Optional[Piece]:
        """Get piece at square."""
        return self._board_state.get_piece(square)

    def set_piece(self, square: ConstantSquare, piece: Optional[Piece]) -> None:
        """Set piece at square."""
        self._board_state.set_piece(square, piece)

    def clear_square(self, square: ConstantSquare) -> None:
        """Clear square."""
        self.set_piece(square, None)

    def clear_board(self) -> None:
        """Clear all pieces from the board."""
        for row in range(8):
            for col in range(8):
                self.clear_square(ConstantSquare(row=row, col=col))

    def is_empty(self, square: ConstantSquare) -> bool:
        """Check if square is empty."""
        return self._board_state.is_empty(square)

    def get_color_at(self, square: ConstantSquare) -> Optional[Color]:
        """Get color at square."""
        return self._board_state.get_color_at(square)

    def get_piece_type_at(self, square: ConstantSquare) -> Optional[PieceType]:
        """Get piece type at square."""
        return self._board_state.get_piece_type_at(square)

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

    def is_valid_position(self, square: ConstantSquare) -> bool:
        """Validate square coordinates."""
        return 0 <= int(square.row) < 8 and 0 <= int(square.col) < 8

    def is_valid_rook_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate rook move (straight line)."""
        piece = self._board_state.get_piece(from_square)
        if piece is None or piece.kind != PieceType.ROOK:
            return False
        return self._move_validator.is_valid_move(from_square, to_square)

    def is_valid_bishop_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate bishop move (diagonal)."""
        piece = self._board_state.get_piece(from_square)
        if piece is None or piece.kind != PieceType.BISHOP:
            return False
        return self._move_validator.is_valid_move(from_square, to_square)

    def is_valid_queen_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate queen move (straight or diagonal)."""
        piece = self._board_state.get_piece(from_square)
        if piece is None or piece.kind != PieceType.QUEEN:
            return False
        return self._move_validator.is_valid_move(from_square, to_square)

    def is_valid_knight_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate knight move (L-shape)."""
        piece = self._board_state.get_piece(from_square)
        if piece is None or piece.kind != PieceType.KNIGHT:
            return False
        return self._move_validator.is_valid_move(from_square, to_square)

    def is_valid_king_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate king move (one square in any direction)."""
        piece = self._board_state.get_piece(from_square)
        if piece is None or piece.kind != PieceType.KING:
            return False
        return self._move_validator.is_valid_move(from_square, to_square)

    def is_valid_pawn_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate pawn move."""
        piece = self._board_state.get_piece(from_square)
        if piece is None or piece.kind != PieceType.PAWN:
            return False
        return self._move_validator.is_valid_move(from_square, to_square)

    def is_on_board(self, square: ConstantSquare) -> bool:
        """Check if square is on board."""
        return self.is_valid_position(square)

    def is_in_check(self, color: Color) -> bool:
        """Check if specified color's king is in check."""
        return self._board_state.is_in_check(color)

    def is_checkmate(self, color: Color) -> bool:
        """Check if game is checkmate."""
        return self._board_state.is_checkmate(color)

    def is_stalemate(self, color: Color) -> bool:
        """Check if game is stalemate."""
        return self._board_state.is_stalemate(color)

    def clone(self) -> Board:
        """Create a deep copy of the board."""
        cloned = Board()
        cloned.board = [row.copy() for row in self.board]
        cloned.turn = self.turn
        cloned._board_state.en_passant_target = self._board_state.en_passant_target
        cloned.white_kingside = self.white_kingside
        cloned.white_queenside = self.white_queenside
        cloned.black_kingside = self.black_kingside
        cloned.black_queenside = self.black_queenside
        return cloned

    def clear_board(self):
        """Clear all pieces from the board."""
        for row in range(8):
            for col in range(8):
                self.clear_square(get_square_constant(row, col))

    def get_legal_moves(
        self, square: Optional[ConstantSquare] = None
    ) -> List[Tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]]:
        """Get all legal moves from the specified square, or all moves on board if none specified."""
        if square is None:
            # Return all legal moves on the board
            all_moves = []
            for row in range(8):
                for col in range(8):
                    sq = ConstantSquare(
                        row=get_row_constant(row), col=get_col_constant(col)
                    )
                    piece = self.get_piece(sq)
                    if piece is not None:
                        all_moves.extend(
                            self._move_validator.get_legal_moves(sq, piece.kind)
                        )
            return all_moves
        piece = self.get_piece(square)
        if piece is None:
            return []
        return self._move_validator.get_legal_moves(square, piece.kind)

    def make_move(
        self,
        start_pos: ConstantSquare,
        end_pos: ConstantSquare,
        promotion: Optional[PieceType] = None,
    ) -> bool:
        """Make a move on the board.

        Args:
            start_pos: Starting square
            end_pos: Destination square
            promotion: Promotion piece type (optional)

        Returns:
            True if move was successful, False otherwise
        """
        # Convert to ConstantSquare if needed
        if isinstance(start_pos, tuple):
            start_pos = ConstantSquare(
                row=get_row_constant(start_pos[0]), col=get_col_constant(start_pos[1])
            )
        if isinstance(end_pos, tuple):
            end_pos = ConstantSquare(
                row=get_row_constant(end_pos[0]), col=get_col_constant(end_pos[1])
            )

        # Get the moving piece
        start_piece = self.get_piece(start_pos)
        if start_piece is None or start_piece.color != self.turn:
            return False

        # Check promotion validity
        if not self._promotion_validator.is_valid_promotion_choice(
            start_piece, end_pos, promotion
        ):
            return False

        # Check for castling
        if (
            start_piece.kind == PieceType.KING
            and self._castling_validator.is_castling_move(start_pos, end_pos)
        ):
            if not self._castling_validator.can_castle(
                self._board_state, start_pos, end_pos, start_piece.color
            ):
                return False

        # Check for en passant capture
        is_en_passant = (
            start_piece.kind == PieceType.PAWN
            and self._board_state.en_passant_target == end_pos
            and start_pos.col != end_pos.col
        )

        if is_en_passant:
            # Validate en passant capture
            if not self._en_passant_validator.validate_en_passant_capture(
                start_pos, end_pos, start_piece
            ):
                return False
        else:
            # Validate regular move
            if not self._move_validator.is_move_legal(start_pos, end_pos):
                return False

        # Check for pinned pieces
        if start_piece.kind not in (PieceType.KNIGHT, PieceType.KING):
            if self._move_validator.is_piece_pinned(start_pos, start_piece.color):
                return False

        # Execute the move
        success = self._move_executor.execute_move(
            start_pos, end_pos, promotion, start_piece
        )

        if not success:
            return False

        # Clear en passant target if needed
        self._en_passant_validator.clear_en_passant_target_if_needed(
            start_pos, end_pos, start_piece
        )

        # Set en passant target if pawn moved 2 squares
        self._en_passant_validator.set_en_passant_target_if_valid(
            start_pos, end_pos, start_piece
        )

        # Switch turn
        self.turn = Color.BLACK if self.turn == Color.WHITE else Color.WHITE

        return True

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
