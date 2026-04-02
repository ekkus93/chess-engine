"""En passant validation logic."""

from __future__ import annotations

from typing import Optional

from chess_game.chess.constants import (
    ROW_1,
    ROW_8,
    Color,
    get_row_constant,
    get_col_constant,
    ConstantSquare,
)
from chess_game.chess.board.board_state import BoardState
from chess_game.chess.types import Piece, PieceType


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
        # En passant must be one file over and two ranks (from capturing pawn to destination)
        if abs(int(from_square.col) - int(to_square.col)) != 1:
            return False
        if abs(int(from_square.row) - int(to_square.row)) != 2:
            return False

        # Check if there's an en passant target set
        if self.board_state.en_passant_target is None:
            return False

        # The target must be the square the pawn would pass through
        ep_target = ConstantSquare(
            row=get_row_constant(int(to_square.row)),
            col=get_col_constant(int(from_square.col)),
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
        # En passant must be one file over and two ranks (from capturing pawn to destination)
        if abs(int(from_square.col) - int(to_square.col)) != 1:
            return False
        if abs(int(from_square.row) - int(to_square.row)) != 1:
            return False

        # Check if there's an en passant target set
        if self.board_state.en_passant_target is None:
            return False

        # Calculate where the captured piece is
        # The captured piece is on the square between the capturing pawn and the en passant target
        capturing_row = int(from_square.row)
        capturing_col = int(from_square.col)

        # Find the en passant target square
        ep_target_row = int(self.board_state.en_passant_target.row)
        ep_target_col = int(self.board_state.en_passant_target.col)

        # The captured piece is on the same column as the en passant target
        # and on the row between the capturing pawn and the en passant target
        captured_row = (capturing_row + ep_target_row) // 2
        captured_col = ep_target_col

        # Check if en passant target matches expected
        expected_ep_target = ConstantSquare(
            row=get_row_constant(int(to_square.row)),
            col=get_col_constant(int(to_square.col)),
        )
        if self.board_state.en_passant_target != expected_ep_target:
            return False

        # Check if there's actually an enemy pawn on the captured piece square
        captured_piece = self.board_state.get_piece(
            ConstantSquare(
                row=get_row_constant(captured_row),
                col=get_col_constant(captured_col),
            )
        )
        print(f"DEBUG validate: captured_piece={captured_piece}")
        if captured_piece is None:
            print("DEBUG validate: no piece on target square")
            return False

        # Check piece type and color
        if captured_piece.kind != PieceType.PAWN:
            print(f"DEBUG validate: not a pawn on target")
            return False
        if piece.color == captured_piece.color:
            print("DEBUG validate: same color as capturing piece")
            return False

        return True

    def update_en_passant_target(
        self, from_square: "ConstantSquare", to_square: "ConstantSquare", piece: Piece
    ):
        """
        Set the en passant target square.

        Args:
            from_square: Moving pawn's square
            to_square: Target square
        """
        color = piece.color
        # Only set en passant target for two-square pawn advances
        # Detect starting row from the pawn's current position
        direction = 1 if color == Color.WHITE else -1
        from_row = int(from_square.row)
        to_row = int(to_square.row)

        print(
            f"DEBUG update: color={color}, from_row={from_row}, to_row={to_row}, direction={direction}"
        )
        print(f"DEBUG update: move is 2 squares: {abs(to_row - from_row) == 2}")

        if abs(to_row - from_row) == 2:
            # Target is where the capturing pawn would land
            # For white pawns (moving forward): destination is to_row
            # For black pawns (moving backward): destination is to_row
            destination_row = to_row
            print(
                f"DEBUG update: setting en passant target at row={destination_row}, col={int(to_square.col)}"
            )
            self.board_state.set_en_passant_target(
                ConstantSquare(
                    row=get_row_constant(destination_row),
                    col=get_col_constant(int(to_square.col)),
                )
            )
        else:
            self.board_state.set_en_passant_target(None)

    def validate_en_passant_capture(
        self, from_square: "ConstantSquare", to_square: "ConstantSquare", piece: Piece
    ) -> bool:
        """
        Validate that an en passant capture is valid.

        Args:
            from_square: Capturing pawn's square
            to_square: Target square (where the pawn lands)
            piece: The capturing pawn

        Returns:
            True if the en passant capture is valid
        """
        print(
            f"DEBUG validate: from={from_square}, to={to_square}, piece_color={piece.color}"
        )
        print(f"DEBUG validate: ep_target={self.board_state.en_passant_target}")

        # En passant capture: one file over and two ranks (diagonal jump)
        if abs(int(from_square.col) - int(to_square.col)) != 1:
            print("DEBUG validate: wrong column offset")
            return False
        if abs(int(from_square.row) - int(to_square.row)) != 2:
            print("DEBUG validate: wrong row offset (should be 2)")
            return False

        # Check if there's an en passant target set
        if self.board_state.en_passant_target is None:
            print("DEBUG validate: no en passant target set")
            return False

        # Calculate where the captured piece is
        # The captured piece is on the square between the capturing pawn and the en passant target
        capturing_row = int(from_square.row)
        capturing_col = int(from_square.col)

        # Find the en passant target square
        ep_target_row = int(self.board_state.en_passant_target.row)
        ep_target_col = int(self.board_state.en_passant_target.col)

        # The captured piece is at the intersection of:
        # - The row between the capturing pawn and en passant target
        # - The column of the en passant target (where the pawn moved past)
        # For en passant: captured piece is at ((capturing_row + ep_target_row) // 2, ep_target_col)
        captured_row = (capturing_row + ep_target_row) // 2
        captured_col = ep_target_col

        expected_ep_target = ConstantSquare(
            row=get_row_constant(captured_row),
            col=get_col_constant(captured_col),
        )
        print(f"DEBUG validate: calculated captured square={expected_ep_target}")

        # Check if there's actually an enemy pawn on the captured piece square
        captured_piece = self.board_state.get_piece(expected_ep_target)
        print(f"DEBUG validate: captured_piece={captured_piece}")
        if captured_piece is None:
            print("DEBUG validate: no piece on target square")
            return False

        # Check piece type and color
        if captured_piece.kind != PieceType.PAWN:
            print("DEBUG validate: captured piece is not a pawn")
            return False
        if captured_piece.color == piece.color:
            print("DEBUG validate: same color as capturing piece")
            return False

        return True

    def reset_en_passant_target(self):
        """Reset the en passant target after a move."""
        self.board_state.set_en_passant_target(None)

    def clear_en_passant_target_if_needed(
        self, from_square: ConstantSquare, to_square: ConstantSquare, piece: Piece
    ) -> None:
        """Clear en passant target if not a pawn move or not a two-square advance."""
        if piece.kind != PieceType.PAWN:
            self.board_state.set_en_passant_target(None)
        else:
            # Check if this is a two-square advance (not an en passant capture)
            from_row = int(from_square.row)
            to_row = int(to_square.row)

            # If the move is exactly 2 squares forward, clear the target
            # (the pawn advanced 2 squares, so the en passant opportunity is gone)
            if abs(to_row - from_row) == 2:
                self.board_state.set_en_passant_target(None)

    def set_en_passant_target_if_valid(
        self,
        from_square: ConstantSquare,
        to_square: ConstantSquare,
        piece: Piece,
    ) -> None:
        """Set en passant target for two-square pawn advances."""
        # Only set en passant target for two-square pawn advances
        if piece.kind != PieceType.PAWN:
            return

        # Check if this is a two-square advance in the correct direction
        from_row = int(from_square.row)
        to_row = int(to_square.row)

        if abs(to_row - from_row) == 2:
            # Verify the move is in the correct direction for the pawn color
            direction = 1 if piece.color == Color.WHITE else -1
            expected_to_row = from_row + 2 * direction
            if to_row == expected_to_row:
                # Target is where the capturing pawn will land (the square between start and destination)
                # The capturing pawn lands on the square between start and destination
                intermediate_row = (from_row + to_row) // 2
                print()
                self.board_state.set_en_passant_target(
                    ConstantSquare(
                        row=get_row_constant(intermediate_row),
                        col=get_col_constant(int(to_square.col)),
                    )
                )
            else:
                self.board_state.set_en_passant_target(None)
        else:
            self.board_state.set_en_passant_target(None)
