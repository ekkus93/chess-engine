"""Move execution logic for the chess engine."""

from __future__ import annotations

from typing import Optional

from chess_game.chess.color import Color
from chess_game.chess.types import Piece, PieceType, ConstantSquare
from chess_game.chess.board.board_state import BoardState
from chess_game.chess.board.castling import CastlingValidator
from chess_game.chess.board.promotion import PromotionValidator
from chess_game.chess.constants import get_row_constant, get_col_constant


class MoveExecutor:
    """Executes moves on the board state."""

    def __init__(self, board: BoardState):
        """Initialize with board state."""
        self.board = board
        self.castling_validator = CastlingValidator()
        self.promotion_validator = PromotionValidator(board)

    def execute_move(
        self,
        from_square: ConstantSquare,
        to_square: ConstantSquare,
        promotion_piece: Optional[PieceType] = None,
        start_piece: Optional[Piece] = None,
    ) -> bool:
        """Execute a move on the board."""
        piece = self.board.get_piece(from_square)
        if piece is None:
            raise ValueError(f"No piece at {from_square}")

        # Handle promotion
        if piece.kind == PieceType.PAWN:
            # Only handle promotion if it's actually required or explicitly requested
            promotion_required = self.promotion_validator.is_promotion_required(
                piece, from_square, to_square
            )
            if promotion_required or promotion_piece is not None:
                self._handle_promotion(piece, from_square, to_square, promotion_piece)
            else:
                # Regular pawn move, no promotion
                self._execute_regular_move(piece, from_square, to_square)
        else:
            # Handle castling
            if self._is_castling_move(piece, from_square, to_square):
                self._execute_castling(piece, from_square, to_square)
            else:
                # Regular move
                self._execute_regular_move(piece, from_square, to_square)

        return True

    def _handle_promotion(
        self,
        piece: Piece,
        from_square: ConstantSquare,
        to_square: ConstantSquare,
        promotion_piece: Optional[PieceType],
    ) -> None:
        """Handle pawn promotion."""
        if promotion_piece is None:
            promotion_piece = self.promotion_validator.get_default_promotion_piece(
                piece.color
            )

        # Move the pawn
        self._move_piece(piece, from_square, to_square)

        # Replace with promoted piece
        new_piece = Piece(piece.color, promotion_piece, to_square)
        self.board.set_piece(to_square, new_piece)
        self.board.clear_square(from_square)

    def _is_castling_move(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Check if this is a castling move."""
        return self.castling_validator.is_castling_move(from_square, to_square)

    def _execute_castling(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> None:
        """Execute a castling move."""
        color = piece.color
        color_str = "white" if color == Color.WHITE else "black"

        if from_square.col == 4 and to_square.col == 6:
            # Kingside: move rook from h to f
            from_row = int(from_square.row)
            rook = self.board.get_piece(
                ConstantSquare(row=get_row_constant(from_row), col=get_col_constant(7))
            )  # COL_H
            if rook is not None:
                self.board.set_piece(
                    ConstantSquare(
                        row=get_row_constant(from_row), col=get_col_constant(5)
                    ),
                    rook,
                )  # COL_F
                self.board.clear_square(
                    ConstantSquare(
                        row=get_row_constant(from_row), col=get_col_constant(7)
                    )
                )
        elif from_square.col == 4 and to_square.col == 2:
            # Queenside: move rook from a to d
            from_row = int(from_square.row)
            rook = self.board.get_piece(
                ConstantSquare(row=get_row_constant(from_row), col=get_col_constant(0))
            )  # COL_A
            if rook is not None:
                self.board.set_piece(
                    ConstantSquare(
                        row=get_row_constant(from_row), col=get_col_constant(3)
                    ),
                    rook,
                )  # COL_D
                self.board.clear_square(
                    ConstantSquare(
                        row=get_row_constant(from_row), col=get_col_constant(0)
                    )
                )

        # Move the king
        self._move_piece(piece, from_square, to_square)

    def _execute_regular_move(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
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
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Check if this is an en passant capture."""
        return (
            self.board.en_passant_target is not None
            and to_square == self.board.en_passant_target
        )

    def _execute_en_passant_capture(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> None:
        """Execute an en passant capture."""
        # Remove the captured pawn (it's on the same row, opposite direction)
        capture_row = int(from_square.row)
        capture_col = int(to_square.col)
        captured_square = ConstantSquare(
            row=get_row_constant(capture_row), col=get_col_constant(capture_col)
        )
        self.board.clear_square(captured_square)

    def _move_piece(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> None:
        """Move a piece from one square to another."""
        self.board.set_piece(to_square, piece)
        piece._square = to_square

    def update_turn(self) -> None:
        """Update whose turn it is."""
        self.board.turn = Color.BLACK if self.board.turn == Color.WHITE else Color.WHITE
