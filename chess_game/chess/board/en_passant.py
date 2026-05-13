"""En passant validation logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from chess_game.chess.color import Color
from chess_game.chess.constants import (
    get_row_constant,
    get_col_constant,
    ConstantSquare,
)
from chess_game.chess.types import Piece, PieceType

if TYPE_CHECKING:
    from chess_game.chess.board.board import Board


class EnPassantValidator:
    """Validates en passant captures."""

    def __init__(self, board: Board):
        self.board = board

    def validate_en_passant_capture(
        self, from_square: ConstantSquare, to_square: ConstantSquare, piece: Piece
    ) -> bool:
        """Validate that an en passant capture is valid."""
        # En passant: one file over, one rank (diagonal move)
        if abs(int(from_square.col) - int(to_square.col)) != 1:
            return False

        if self.board.en_passant_target is None:
            return False

        if to_square != self.board.en_passant_target:
            return False

        # The captured piece is one rank beyond EP target in capturing pawn's direction
        direction = -1 if piece.color == Color.WHITE else 1
        captured_row = int(self.board.en_passant_target.row) - direction
        captured_square = ConstantSquare(
            row=get_row_constant(captured_row),
            col=get_col_constant(int(to_square.col)),
        )
        captured_piece = self.board.get_piece(captured_square)

        if captured_piece is None:
            return False
        if captured_piece.kind != PieceType.PAWN:
            return False
        if captured_piece.color == piece.color:
            return False

        # Check that en passant capture doesn't expose king to check
        temp_board = self.board.clone()
        temp_piece = Piece(color=piece.color, kind=piece.kind, _square=to_square)
        temp_board.set_piece(to_square, temp_piece)
        temp_board.clear_square(from_square)
        temp_board.clear_square(captured_square)

        if temp_board.is_in_check(piece.color):
            return False

        return True

    def clear_en_passant_target_if_needed(
        self, _from_square: ConstantSquare, _to_square: ConstantSquare, _piece: Piece
    ) -> None:
        """Clear en passant target after any non-two-square-pawn-advance move."""
        self.board.en_passant_target = None

    def set_en_passant_target_if_valid(
        self,
        from_square: ConstantSquare,
        to_square: ConstantSquare,
        piece: Piece,
    ) -> None:
        """Set en passant target for two-square pawn advances."""
        if piece.kind != PieceType.PAWN:
            return

        from_row = int(from_square.row)
        to_row = int(to_square.row)

        if abs(to_row - from_row) != 2:
            self.board.en_passant_target = None
            return

        # Verify correct direction
        direction = -1 if piece.color == Color.WHITE else 1
        expected_to_row = from_row + 2 * direction
        if to_row != expected_to_row:
            self.board.en_passant_target = None
            return

        # Target is the intermediate square between start and destination
        intermediate_row = (from_row + to_row) // 2
        self.board.en_passant_target = ConstantSquare(
            row=get_row_constant(intermediate_row),
            col=get_col_constant(int(to_square.col)),
        )
