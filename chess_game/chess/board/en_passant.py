"""En passant validation logic."""

from __future__ import annotations

from typing import Optional

from chess_game.chess.constants import (
    ROW_1,
    ROW_8,
    Color,
    get_row_constant,
    ConstantSquare,
)
from chess_game.chess.board.board_state import BoardState
from chess_game.chess.types import PieceType


class EnPassantValidator:
    """Validates en passant captures."""

    def __init__(self, board_state: BoardState):
        self.board_state = board_state

    def is_en_passant_valid(
        self, from_square: "ConstantSquare", to_square: "ConstantSquare"
    ) -> bool:
        """
        Check if an en passant capture is valid.

        Args:
            from_square: Capturing pawn's square (row, col)
            to_square: Target square (row, col)

        Returns:
            True if en passant is valid
        """
        # En passant must be one file over and one rank forward
        if abs(int(from_square.col) - int(to_square.col)) != 1:
            return False
        if abs(int(from_square.row) - int(to_square.row)) != 1:
            return False

        # Check if there's an en passant target set
        if self.board_state.en_passant_target is None:
            return False

        # The target must be the square the pawn would pass through
        ep_target = ConstantSquare(
            row=int(to_square.row), col=int(from_square.col)
        )  # The square directly behind the capturing pawn
        if self.board_state.en_passant_target != ep_target:
            return False

        return True

    def can_en_passant_capture(
        self, from_square: "ConstantSquare", to_square: "ConstantSquare"
    ) -> bool:
        """
        Check if a pawn can make an en passant capture.

        Args:
            from_square: Capturing pawn's square
            to_square: Target square

        Returns:
            True if en passant capture is available
        """
        # En passant must be one file over and one rank forward
        if abs(int(from_square.col) - int(to_square.col)) != 1:
            return False
        if abs(int(from_square.row) - int(to_square.row)) != 1:
            return False

        # Check if there's an en passant target set
        if self.board_state.en_passant_target is None:
            return False

        # The target must be the square the captured pawn would be on
        ep_target = ConstantSquare(
            row=int(to_square.row), col=int(from_square.col)
        )  # The square directly behind the capturing pawn
        if self.board_state.en_passant_target != ep_target:
            return False

        # Check if there's actually an enemy pawn on the target square
        captured_piece = self.board_state.get_piece(ep_target)
        if captured_piece is None:
            return False

        # Check piece type and color
        capturing_piece = self.board_state.get_piece(from_square)
        if captured_piece.piece_type != PieceType.PAWN:
            return False
        if capturing_piece.color == captured_piece.color:
            return False

        return True

    def update_en_passant_target(
        self, from_square: "ConstantSquare", to_square: "ConstantSquare"
    ):
        """
        Set the en passant target square.

        Args:
            from_square: Moving pawn's square
            to_square: Target square
        """
        # Only set en passant target for two-square pawn advances
        color = self.board_state.pieces[from_square].color
        direction = 1 if color == Color.WHITE else -1
        start_row = (
            get_row_constant(ROW_1) if color == Color.WHITE else get_row_constant(ROW_8)
        )

        if (
            int(from_square.row) == int(start_row)
            and int(to_square.row) == int(from_square.row) + 2 * direction
        ):
            self.board_state.set_en_passant_target(
                ConstantSquare(row=int(to_square.row), col=int(from_square.col))
            )
        else:
            self.board_state.set_en_passant_target(None)

    def reset_en_passant_target(self):
        """Reset the en passant target after a move."""
        self.board_state.set_en_passant_target(None)
