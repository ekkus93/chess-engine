"""Piece-specific move validation logic."""

from __future__ import annotations

from typing import List, Optional

from chess_game.chess.color import Color
from chess_game.constants import ROW_1, ROW_8
from chess_game.chess.pieces.piece import Piece, PieceType, Square


class PieceMovers:
    """Contains move validation logic for each piece type."""

    @staticmethod
    def get_valid_moves(
        piece: Piece, board
    ) -> List[Square]:
        """Get all valid moves for a piece."""
        if piece.kind == PieceType.PAWN:
            return PieceMovers._get_pawn_moves(piece, board)
        elif piece.kind == PieceType.KNIGHT:
            return PieceMovers._get_knight_moves(piece, board)
        elif piece.kind == PieceType.BISHOP:
            return PieceMovers._get_bishop_moves(piece, board)
        elif piece.kind == PieceType.ROOK:
            return PieceMovers._get_rook_moves(piece, board)
        elif piece.kind == PieceType.QUEEN:
            return PieceMovers._get_queen_moves(piece, board)
        elif piece.kind == PieceType.KING:
            return PieceMovers._get_king_moves(piece, board)
        return []

    @staticmethod
    def _get_pawn_moves(piece: Piece, board) -> List[Square]:
        """Get all valid pawn moves (forward, capture, 2-step)."""
        moves = []
        direction = 1 if piece.color == Color.WHITE else -1
        start_row = ROW_1 if piece.color == Color.WHITE else ROW_8

        current_row = int(piece.square.row)
        current_col = int(piece.square.col)

        # Forward 1 square
        if PieceMovers._is_valid_position(
            board, Square(current_row + direction, current_col)
        ):
            target_square = Square(current_row + direction, current_col)
            if board.is_empty(target_square):
                moves.append(target_square)

        # Forward 2 squares (only on first move)
        if current_row == int(start_row):
            target_square_2 = Square(current_row + 2 * direction, current_col)
            if PieceMovers._is_valid_position(board, target_square_2):
                square_between = Square(current_row + direction, current_col)
                if board.is_empty(square_between) and board.is_empty(target_square_2):
                    moves.append(target_square_2)

        # Captures
        for col_offset in [-1, 1]:
            target_col = current_col + col_offset
            target_square = Square(current_row + direction, target_col)
            
            if PieceMovers._is_valid_position(board, target_square):
                target_piece = board.get_piece(target_square)
                if target_piece is not None and target_piece.color != piece.color:
                    moves.append(target_square)

        return moves

    @staticmethod
    def _is_valid_position(board, square: Square) -> bool:
        """Check if a square is on the board."""
        return (
            0 <= int(square.row) < 8
            and 0 <= int(square.col) < 8
        )

    @staticmethod
    def _get_knight_moves(piece: Piece, board) -> List[Square]:
        """Get all valid knight moves (L-shaped)."""
        moves = []
        row_offsets = [-2, -1, 1, 2]
        col_offsets = [-2, -1, 1, 2]

        for row_offset, col_offset in [(ro, co) for ro in row_offsets for co in col_offsets]:
            if ro * co == 0:  # Skip adjacent squares
                continue

            target_square = Square(int(piece.square.row) + row_offset, int(piece.square.col) + col_offset)
            
            if PieceMovers._is_valid_position(board, target_square):
                if board.is_empty(target_square) or (
                    board.get_piece(target_square) is not None
                    and board.get_piece(target_square).color != piece.color
                ):
                    moves.append(target_square)

        return moves

    @staticmethod
    def _get_bishop_moves(piece: Piece, board) -> List[Square]:
        """Get all valid bishop moves (diagonal)."""
        moves = []
        diagonals = [
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        ]

        for row_offset, col_offset in diagonals:
            target_row = int(piece.square.row) + row_offset
            target_col = int(piece.square.col) + col_offset

            while (
                0 <= target_row < 8 and 0 <= target_col < 8
            ):
                target_square = Square(target_row, target_col)
                target_piece = board.get_piece(target_square)

                if target_piece is None:
                    moves.append(target_square)
                elif target_piece.color != piece.color:
                    moves.append(target_square)
                    break
                else:
                    break

                target_row += row_offset
                target_col += col_offset

        return moves

    @staticmethod
    def _get_rook_moves(piece: Piece, board) -> List[Square]:
        """Get all valid rook moves (straight lines)."""
        moves = []
        directions = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
        ]

        for row_offset, col_offset in directions:
            target_row = int(piece.square.row) + row_offset
            target_col = int(piece.square.col) + col_offset

            while (
                0 <= target_row < 8 and 0 <= target_col < 8
            ):
                target_square = Square(target_row, target_col)
                target_piece = board.get_piece(target_square)

                if target_piece is None:
                    moves.append(target_square)
                elif target_piece.color != piece.color:
                    moves.append(target_square)
                    break
                else:
                    break

                target_row += row_offset
                target_col += col_offset

        return moves

    @staticmethod
    def _get_queen_moves(piece: Piece, board) -> List[Square]:
        """Get all valid queen moves (rook + bishop combined)."""
        rook_moves = PieceMovers._get_rook_moves(piece, board)
        bishop_moves = PieceMovers._get_bishop_moves(piece, board)
        return rook_moves + bishop_moves

    @staticmethod
    def _get_king_moves(piece: Piece, board) -> List[Square]:
        """Get all valid king moves (one square in any direction)."""
        moves = []
        row_offsets = [-1, 0, 1]
        col_offsets = [-1, 0, 1]

        for row_offset, col_offset in [(ro, co) for ro in row_offsets for co in col_offsets]:
            if row_offset == 0 and col_offset == 0:
                continue

            target_square = Square(int(piece.square.row) + row_offset, int(piece.square.col) + col_offset)
            
            if PieceMovers._is_valid_position(board, target_square):
                if board.is_empty(target_square) or (
                    board.get_piece(target_square) is not None
                    and board.get_piece(target_square).color != piece.color
                ):
                    moves.append(target_square)

        return moves
