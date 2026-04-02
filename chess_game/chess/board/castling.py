"""Castling validation logic."""

from __future__ import annotations

from chess_game.chess.board.board_state import BoardState
from chess_game.chess.color import Color
from chess_game.constants import (
    ROW_1,
    ROW_8,
    COL_E,
    COL_F,
    COL_G,
    COL_C,
    COL_A,
    COL_D,
    COL_H,
)
from chess_game.chess.pieces.piece import Piece
from chess_game.chess.pieces.piece import PieceType
from chess_game.chess.pieces.piece import Square

SquareLike = Square | tuple[int, int]


class CastlingValidator:
    """Validates castling moves."""

    @staticmethod
    def can_castle_kingside(
        board: BoardState,
        color: Color,
    ) -> bool:
        """Check if kingside castling is possible."""
        home_row = ROW_1 if color == Color.WHITE else ROW_8
        king_square = Square(home_row, COL_E)
        rook_square = Square(home_row, COL_H)
        destination = Square(home_row, COL_G)

        return CastlingValidator._can_complete_castle(
            board, king_square, rook_square, destination, color
        )

    @staticmethod
    def can_castle_queenside(
        board: BoardState,
        color: Color,
    ) -> bool:
        """Check if queenside castling is possible."""
        home_row = ROW_1 if color == Color.WHITE else ROW_8
        king_square = Square(home_row, COL_E)
        rook_square = Square(home_row, COL_A)
        destination = Square(home_row, COL_C)

        return CastlingValidator._can_complete_castle(
            board, king_square, rook_square, destination, color
        )

    @staticmethod
    def _can_complete_castle(
        board: BoardState,
        king_square: Square,
        rook_square: Square,
        destination: Square,
        color: Color,
    ) -> bool:
        """Check if castling can be completed."""
        # Check rook is at original square
        if not CastlingValidator._rook_at_original_square(board, color, rook_square):
            return False

        # Check path is clear
        if not CastlingValidator._castling_path_is_clear(
            board, king_square, destination
        ):
            return False

        # Check king doesn't pass through attacked squares
        if not CastlingValidator._king_square_safe_during_castle(
            board, king_square, destination, color
        ):
            return False

        return True

    @staticmethod
    def _rook_at_original_square(
        board: BoardState, color: Color, rook_square: Square
    ) -> bool:
        """Check if rook is at original position and hasn't moved."""
        piece = board.get_piece(rook_square)
        return (
            piece is not None and piece.kind == PieceType.ROOK and piece.color == color
        )

    @staticmethod
    def _castling_path_is_clear(
        board: BoardState,
        king_square: Square,
        destination: Square,
    ) -> bool:
        """Check if castling path is clear."""
        if king_square.col == COL_E and destination.col == COL_G:
            # Kingside: check f-file
            return not board.get_piece(Square(king_square.row, COL_F))
        elif king_square.col == COL_E and destination.col == COL_C:
            # Queenside: check d and c files
            return not board.get_piece(
                Square(king_square.row, COL_D)
            ) and not board.get_piece(Square(king_square.row, COL_C))
        return True

    @staticmethod
    def _king_square_safe_during_castle(
        board: BoardState,
        king_square: Square,
        destination: Square,
        color: Color,
    ) -> bool:
        """Check if king's path and destination are not attacked."""
        enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE

        king_path = [
            king_square,
            Square(king_square.row, COL_F),
            destination,
        ]

        for square in king_path:
            if CastlingValidator._is_square_attacked(board, square, enemy_color):
                return False

        return True

    @staticmethod
    def _is_square_attacked(board: BoardState, square: Square, by_color: Color) -> bool:
        """Check if a square is attacked by any piece of given color."""
        for row in range(8):
            for col in range(8):
                piece_square = Square(row, col)
                piece = board.get_piece(piece_square)
                if piece is None or piece.color != by_color:
                    continue

                if CastlingValidator._piece_attacks_square(piece, piece_square, square):
                    return True
        return False

    @staticmethod
    def _piece_attacks_square(
        piece: Piece, from_square: Square, to_square: Square
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
            return CastlingValidator._path_is_clear(from_square, to_square)

        if piece.kind == PieceType.ROOK:
            if from_square.row != to_square.row and from_square.col != to_square.col:
                return False
            return CastlingValidator._path_is_clear(from_square, to_square)

        if piece.kind == PieceType.QUEEN:
            if from_square.row != to_square.row and from_square.col != to_square.col:
                return False
            if abs(row_diff) != abs(col_diff):
                return False
            return CastlingValidator._path_is_clear(from_square, to_square)

        if piece.kind == PieceType.KING:
            return from_square != to_square and max(abs(row_diff), abs(col_diff)) == 1

        return False

    @staticmethod
    def _path_is_clear(from_square: Square, to_square: Square) -> bool:
        """Check if path between two squares is clear."""
        if from_square == to_square:
            return False

        row_diff = to_square.row - from_square.row
        col_diff = to_square.col - from_square.col

        step_row = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
        step_col = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)

        current_row = int(from_square.row) + step_row
        current_col = int(from_square.col) + step_col

        while (current_row, current_col) != (int(to_square.row), int(to_square.col)):
            if board.get_piece(Square(current_row, current_col)) is not None:
                return False
            current_row += step_row
            current_col += step_col

        return True
