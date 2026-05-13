"""Path validation for piece moves."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from chess_game.chess.constants import get_row_constant, get_col_constant
from chess_game.chess.types import Piece
from chess_game.chess.constants import ConstantSquare

if TYPE_CHECKING:
    from chess_game.chess.board.board import Board


class PathValidator:
    """Validates paths between squares on the board."""

    @staticmethod
    def is_path_clear(
        board: "Board",
        from_square: ConstantSquare,
        to_square: ConstantSquare,
        _ignore_color: Optional[int] = None,
    ) -> bool:
        """Check if the path between two squares is clear (no pieces blocking)."""
        if from_square == to_square:
            return True

        row_diff = to_square.row - from_square.row
        col_diff = to_square.col - from_square.col

        step_row = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
        step_col = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)

        current_row = int(from_square.row) + step_row
        current_col = int(from_square.col) + step_col

        while (current_row, current_col) != (int(to_square.row), int(to_square.col)):
            if (
                board.get_piece(
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

    @staticmethod
    def is_piece_between(
        board: "Board", from_square: ConstantSquare, to_square: ConstantSquare
    ) -> Optional[Piece]:
        """Get the piece between two squares if any."""
        if from_square == to_square:
            return None

        row_diff = to_square.row - from_square.row
        col_diff = to_square.col - from_square.col

        step_row = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
        step_col = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)

        current_row = int(from_square.row) + step_row
        current_col = int(from_square.col) + step_col

        while (current_row, current_col) != (int(to_square.row), int(to_square.col)):
            piece = board.get_piece(
                ConstantSquare(
                    row=get_row_constant(current_row),
                    col=get_col_constant(current_col),
                )
            )
            if piece is not None:
                return piece
            current_row += step_row
            current_col += step_col

        return None
