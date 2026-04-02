"""Move validation logic for the chess engine."""

from __future__ import annotations

from typing import List, Optional, Tuple

from chess_game.chess.color import Color
from chess_game.chess.pieces.piece import Piece, PieceType, Square
from chess_game.chess.board.board_state import BoardState
from chess_game.chess.board.castling import CastlingValidator
from chess_game.chess.board.path_validator import PathValidator
from chess_game.chess.pieces.piece_movers import PieceMovers


class MoveValidator:
    """Validates whether a move is legal according to chess rules."""

    def __init__(self, board: BoardState):
        """Initialize with board state."""
        self.board = board
        self.path_validator = PathValidator()
        self.piece_movers = PieceMovers()

    def is_valid_move(
        self, from_square: Square, to_square: Square
    ) -> bool:
        """Check if a move is valid."""
        piece = self.board.get_piece(from_square)
        if piece is None:
            return False

        # Check if piece can move to destination
        if to_square not in self.piece_movers.get_valid_moves(piece, self.board):
            return False

        # Check for special moves
        if self._is_castling_move(piece, from_square, to_square):
            return self._validate_castling(piece, from_square, to_square)

        if self._is_en_passant_move(piece, from_square, to_square):
            return self._validate_en_passant(piece, from_square, to_square)

        # Regular move: check if destination is valid (not own piece)
        if self.board.get_piece(to_square) is not None:
            if self.board.get_piece(to_square).color == piece.color:
                return False

        return True

    def _is_castling_move(
        self, piece: Piece, from_square: Square, to_square: Square
    ) -> bool:
        """Check if this is a castling move."""
        if piece.kind != PieceType.KING:
            return False

        # Kingside castling
        if (
            from_square == Square(int(piece.square.row), 4)  # COL_E
            and to_square == Square(int(piece.square.row), 6)  # COL_G
        ):
            return True

        # Queenside castling
        if (
            from_square == Square(int(piece.square.row), 4)  # COL_E
            and to_square == Square(int(piece.square.row), 2)  # COL_C
        ):
            return True

        return False

    def _is_en_passant_move(
        self, piece: Piece, from_square: Square, to_square: Square
    ) -> bool:
        """Check if this is an en passant capture."""
        if piece.kind != PieceType.PAWN:
            return False

        # En passant captures diagonal
        col_diff = abs(int(to_square.col) - int(from_square.col))
        row_diff = abs(int(to_square.row) - int(from_square.row))

        return col_diff == 1 and row_diff == 1

    def _validate_castling(
        self, piece: Piece, from_square: Square, to_square: Square
    ) -> bool:
        """Validate castling move."""
        color = piece.color
        color_str = "white" if color == Color.WHITE else "black"

        if from_square.row != to_square.row:
            return False

        # Check castling rights
        if color == Color.WHITE:
            kingside = self.board.white_kingside
            queenside = self.board.white_queenside
        else:
            kingside = self.board.black_kingside
            queenside = self.board.black_queenside

        if not kingside and not queenside:
            return False

        # Check path is clear
        if not self._is_castling_path_clear(from_square, to_square):
            return False

        # Check king doesn't pass through attacked squares
        enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
        king_path = [
            from_square,
            Square(int(from_square.row), int(from_square.col) + 1),
            to_square,
        ]

        for square in king_path:
            if CastlingValidator.is_square_attacked(
                self.board, square, enemy_color
            ):
                return False

        return True

    def _is_castling_path_clear(
        self, from_square: Square, to_square: Square
    ) -> bool:
        """Check if castling path is clear."""
        from_col = int(from_square.col)
        to_col = int(to_square.col)

        # Kingside: check f-file
        if to_col == 6:  # COL_G
            return self.path_validator.is_path_clear(
                self.board, from_square, Square(int(from_square.row), 5)
            )  # COL_F

        # Queenside: check d and c files
        if to_col == 2:  # COL_C
            return (
                self.path_validator.is_path_clear(
                    self.board, from_square, Square(int(from_square.row), 3)
                )  # COL_D
                and self.path_validator.is_path_clear(
                    self.board, from_square, Square(int(from_square.row), 2)
                )  # COL_C
            )

        return True

    def _validate_en_passant(
        self, piece: Piece, from_square: Square, to_square: Square
    ) -> bool:
        """Validate en passant capture."""
        if self.board.en_passant_target is None:
            return False

        target_square = self.board.en_passant_target

        # En passant capture lands on the same row as the en passant target
        if int(to_square.row) != int(target_square.row):
            return False

        # Must be capturing on the en passant square
        if to_square != target_square:
            return False

        return True

    def get_legal_moves(self, from_square: Optional[Square] = None) -> List[Square]:
        """Get all legal moves (with check validation)."""
        all_moves = []

        if from_square is not None:
            piece = self.board.get_piece(from_square)
            if piece is None:
                return []

            for to_square in self.piece_movers.get_valid_moves(piece, self.board):
                if self.is_valid_move(from_square, to_square):
                    all_moves.append(to_square)
        else:
            # Get all legal moves for the current turn
            for row in range(8):
                for col in range(8):
                    from_square = Square(row, col)
                    piece = self.board.get_piece(from_square)
                    if piece is not None:
                        for to_square in self.piece_movers.get_valid_moves(
                            piece, self.board
                        ):
                            if self.is_valid_move(from_square, to_square):
                                all_moves.append(to_square)

        return all_moves
