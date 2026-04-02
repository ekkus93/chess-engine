"""Castling validation logic."""

from __future__ import annotations

from chess_game.chess.board.board_state import BoardState
from chess_game.chess.color import Color
from chess_game.chess.constants import (
    ROW_1,
    ROW_8,
    COL_E,
    COL_F,
    COL_G,
    COL_C,
    COL_A,
    COL_D,
    COL_H,
    ConstantSquare,
    get_row_constant,
    get_col_constant,
)
from chess_game.chess.types import Piece
from chess_game.chess.types import PieceType


class CastlingValidator:
    """Validates castling moves."""

    @staticmethod
    def is_castling_move(start_pos: ConstantSquare, end_pos: ConstantSquare) -> bool:
        """Check if the move is a castling move."""
        # Kingside: E1 -> G1 (or E8 -> G8)
        if start_pos.col == 4 and end_pos.col == 6:  # E to G
            return start_pos.row == 0 or start_pos.row == 7  # Row 0 or 7

        # Queenside: E1 -> C1 (or E8 -> C8)
        if start_pos.col == 4 and end_pos.col == 2:  # E to C
            return start_pos.row == 0 or start_pos.row == 7  # Row 0 or 7

        return False

    @staticmethod
    def can_castle(
        board: BoardState,
        start_pos: ConstantSquare,
        end_pos: ConstantSquare,
        color: Color,
        _piece_color: Color,
    ) -> bool:
        """Check if castling is valid for the given move."""
        if not CastlingValidator.is_castling_move(start_pos, end_pos):
            return False

        # Determine which rook is involved based on direction
        if end_pos.col > start_pos.col:
            # Kingside
            rook_square = ConstantSquare(row=start_pos.row, col=COL_H)
        else:
            # Queenside
            rook_square = ConstantSquare(row=start_pos.row, col=COL_A)

        return CastlingValidator._can_complete_castle(
            board, start_pos, rook_square, end_pos, color, _piece_color
        )

    @staticmethod
    def can_castle_kingside(
        board: BoardState,
        color: Color,
    ) -> bool:
        """Check if kingside castling is possible."""
        home_row = ROW_1 if color == Color.WHITE else ROW_8
        king_square = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_E)
        rook_square = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_H)
        destination = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_G)

        return CastlingValidator._can_complete_castle(
            board, king_square, rook_square, destination, color, color
        )

    @staticmethod
    def can_castle_queenside(
        board: BoardState,
        color: Color,
    ) -> bool:
        """Check if queenside castling is possible."""
        home_row = ROW_1 if color == Color.WHITE else ROW_8
        king_square = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_E)
        rook_square = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_A)
        destination = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_C)

        return CastlingValidator._can_complete_castle(
            board, king_square, rook_square, destination, color, color
        )

    @staticmethod
    def _can_complete_castle(
        board: BoardState,
        king_square: ConstantSquare,
        rook_square: ConstantSquare,
        destination: ConstantSquare,
        color: Color,
        _piece_color: Color,
    ) -> bool:
        """Check if castling can be completed."""
        # Check rook is at original square
        if not CastlingValidator._rook_at_original_square(board, color, rook_square):
            return False

        # Check path is clear
        if not CastlingValidator._castling_path_is_clear(
            king_square, destination, board, _piece_color
        ):
            return False

        # Check king doesn't pass through attacked squares
        if not CastlingValidator._king_square_safe_during_castle(
            board, king_square, destination, color
        ):
            return False

        return True

    @staticmethod
    def _king_square_safe_during_castle(
        board: BoardState,
        king_square: ConstantSquare,
        destination: ConstantSquare,
        color: Color,
    ) -> bool:
        """Check if king's path and destination are not attacked."""
        enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE

        king_path = [
            king_square,
            ConstantSquare(row=king_square.row, col=COL_F),
            destination,
        ]

        for square in king_path:
            if CastlingValidator._is_square_attacked(board, square, enemy_color):
                return False

        return True

    @staticmethod
    def _rook_at_original_square(
        board: BoardState, color: Color, rook_square: ConstantSquare
    ) -> bool:
        """Check if rook is at original position and hasn't moved."""
        piece = board.get_piece(rook_square)
        return (
            piece is not None and piece.kind == PieceType.ROOK and piece.color == color
        )

    @staticmethod
    def _castling_path_is_clear(
        king_square: ConstantSquare,
        destination: ConstantSquare,
        board: BoardState,
        _piece_color: Color,
    ) -> bool:
        """Check if castling path is clear."""
        if king_square.col == COL_E and destination.col == COL_G:
            # Kingside: check f-file
            piece = board.get_piece(ConstantSquare(row=king_square.row, col=COL_F))
            if piece is not None:
                # Path blocked by any piece (friend or foe)
                return False
            return True
        elif king_square.col == COL_E and destination.col == COL_C:
            # Queenside: check d and c files
            piece_d = board.get_piece(ConstantSquare(row=king_square.row, col=COL_D))
            piece_c = board.get_piece(ConstantSquare(row=king_square.row, col=COL_C))
            if piece_d is not None:
                # Path blocked by any piece (friend or foe)
                return False
            if piece_c is not None:
                # Path blocked by any piece (friend or foe)
                return False
            return True
        return True

    @staticmethod
    def _is_square_attacked(
        board: BoardState, square: ConstantSquare, by_color: Color
    ) -> bool:
        """Check if a square is attacked by any piece of given color."""
        for row in range(8):
            for col in range(8):
                piece_square = ConstantSquare(
                    row=get_row_constant(row), col=get_col_constant(col)
                )
                piece = board.get_piece(piece_square)
                if piece is None or piece.color != by_color:
                    continue

                if CastlingValidator._piece_attacks_square(
                    piece, piece_square, square, board
                ):
                    return True
        return False

    @staticmethod
    def _piece_attacks_square(
        piece: Piece,
        from_square: ConstantSquare,
        to_square: ConstantSquare,
        board: BoardState,
    ) -> bool:
        """Check if a piece attacks a square."""
        row_diff = to_square.row - from_square.row
        col_diff = to_square.col - from_square.col

        if piece.kind == PieceType.PAWN:
            direction = 1 if piece.color == Color.WHITE else -1
            return row_diff == direction and abs(col_diff) == 1

        if piece.kind == PieceType.KNIGHT:
            return (abs(row_diff), abs(col_diff)) in {(2, 1), (1, 2)}

        if piece.kind == PieceType.BISHOP:
            if abs(row_diff) != abs(col_diff):
                return False
            return CastlingValidator._path_is_clear(from_square, to_square, board)

        if piece.kind == PieceType.ROOK:
            if from_square.row != to_square.row and from_square.col != to_square.col:
                return False
            return CastlingValidator._path_is_clear(from_square, to_square, board)

        if piece.kind == PieceType.QUEEN:
            if from_square.row != to_square.row and from_square.col != to_square.col:
                return False
            if abs(row_diff) != abs(col_diff):
                return False
            return CastlingValidator._path_is_clear(from_square, to_square, board)

        if piece.kind == PieceType.KING:
            return from_square != to_square and max(abs(row_diff), abs(col_diff)) == 1

        return False

    @staticmethod
    def _path_is_clear(
        from_square: ConstantSquare, to_square: ConstantSquare, board: BoardState
    ) -> bool:
        """Check if path between two squares is clear."""
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
