"""Move execution logic for the chess engine."""

from __future__ import annotations

from typing import Optional

from chess_game.chess.color import Color
from chess_game.chess.pieces.piece import Piece, PieceType, Square
from chess_game.chess.board.board_state import BoardState
from chess_game.chess.board.castling import CastlingValidator
from chess_game.chess.board.promotion import PromotionValidator


class MoveExecutor:
    """Executes moves on the board state."""

    def __init__(self, board: BoardState):
        """Initialize with board state."""
        self.board = board
        self.castling_validator = CastlingValidator()
        self.promotion_validator = PromotionValidator()

    def execute_move(
        self,
        from_square: Square,
        to_square: Square,
        promotion_piece: Optional[PieceType] = None,
    ) -> None:
        """Execute a move on the board."""
        piece = self.board.get_piece(from_square)
        if piece is None:
            raise ValueError(f"No piece at {from_square}")

        # Handle promotion
        if piece.kind == PieceType.PAWN:
            self._handle_promotion(piece, to_square, promotion_piece)
        else:
            # Handle castling
            if self._is_castling_move(piece, from_square, to_square):
                self._execute_castling(piece, from_square, to_square)
            else:
                # Regular move
                self._execute_regular_move(piece, from_square, to_square)

    def _handle_promotion(
        self,
        piece: Piece,
        to_square: Square,
        promotion_piece: Optional[PieceType],
    ) -> None:
        """Handle pawn promotion."""
        if promotion_piece is None:
            promotion_piece = self.promotion_validator.get_default_promotion_piece(piece.color)

        # Move the pawn
        self._move_piece(piece, from_square, to_square)

        # Replace with promoted piece
        new_piece = Piece(piece.color, promotion_piece, to_square)
        self.board.set_piece(to_square, new_piece)
        self.board.clear_square(from_square)

    def _is_castling_move(
        self, piece: Piece, from_square: Square, to_square: Square
    ) -> bool:
        """Check if this is a castling move."""
        return CastlingValidator.is_castling_move(piece, from_square, to_square)

    def _execute_castling(
        self, piece: Piece, from_square: Square, to_square: Square
    ) -> None:
        """Execute a castling move."""
        color = piece.color
        color_str = "white" if color == Color.WHITE else "black"

        if from_square.col == 4 and to_square.col == 6:
            # Kingside: move rook from h to f
            rook = self.board.get_piece(Square(int(from_square.row), 7))  # COL_H
            if rook is not None:
                self.board.set_piece(Square(int(from_square.row), 5), rook)  # COL_F
                self.board.clear_square(Square(int(from_square.row), 7))
        elif from_square.col == 4 and to_square.col == 2:
            # Queenside: move rook from a to d
            rook = self.board.get_piece(Square(int(from_square.row), 0))  # COL_A
            if rook is not None:
                self.board.set_piece(Square(int(from_square.row), 3), rook)  # COL_D
                self.board.clear_square(Square(int(from_square.row), 0))

        # Move the king
        self._move_piece(piece, from_square, to_square)

    def _execute_regular_move(
        self, piece: Piece, from_square: Square, to_square: Square
    ) -> None:
        """Execute a regular move."""
        # Move the piece
        self._move_piece(piece, from_square, to_square)

        # Handle en passant capture
        if self._is_en_passant_capture(piece, from_square, to_square):
            self._execute_en_passant_capture(from_square, to_square)

        # Clear the original square
        self.board.clear_square(from_square)

    def _is_en_passant_capture(
        self, piece: Piece, from_square: Square, to_square: Square
    ) -> bool:
        """Check if this is an en passant capture."""
        return self.board.en_passant_target is not None and to_square == self.board.en_passant_target

    def _execute_en_passant_capture(
        self, from_square: Square, to_square: Square
    ) -> None:
        """Execute an en passant capture."""
        # Remove the captured pawn (it's on the same row, opposite direction)
        capture_row = int(from_square.row)
        capture_col = int(to_square.col)
        captured_square = Square(capture_row, capture_col)
        self.board.clear_square(captured_square)

    def _move_piece(self, piece: Piece, from_square: Square, to_square: Square) -> None:
        """Move a piece from one square to another."""
        self.board.set_piece(to_square, piece)
        piece._square = to_square

    def update_turn(self) -> None:
        """Update whose turn it is."""
        self.board.turn = Color.BLACK if self.board.turn == Color.WHITE else Color.WHITE
