"""Piece-specific move validation delegate.

Holds the six `is_valid_*_move` methods extracted from Board to reduce
Board's public method count.
"""

from __future__ import annotations

from chess_game.chess.types import PieceType
from chess_game.chess.constants import ConstantSquare


class PieceMoveChecker:
    """Validates moves for specific piece types by delegating to MoveValidator."""

    def __init__(self, board: "Board") -> None:  # noqa: F821
        self._board = board

    def is_valid_rook_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate rook move (straight line)."""
        piece = self._board.get_piece(from_square)
        if piece is None or piece.kind != PieceType.ROOK:
            return False
        return self._board._move_validator.is_valid_move(
            from_square, to_square
        )

    def is_valid_bishop_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate bishop move (diagonal)."""
        piece = self._board.get_piece(from_square)
        if piece is None or piece.kind != PieceType.BISHOP:
            return False
        return self._board._move_validator.is_valid_move(
            from_square, to_square
        )

    def is_valid_queen_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate queen move (straight or diagonal)."""
        piece = self._board.get_piece(from_square)
        if piece is None or piece.kind != PieceType.QUEEN:
            return False
        return self._board._move_validator.is_valid_move(
            from_square, to_square
        )

    def is_valid_knight_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate knight move (L-shape)."""
        piece = self._board.get_piece(from_square)
        if piece is None or piece.kind != PieceType.KNIGHT:
            return False
        return self._board._move_validator.is_valid_move(
            from_square, to_square
        )

    def is_valid_king_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate king move (one square in any direction)."""
        piece = self._board.get_piece(from_square)
        if piece is None or piece.kind != PieceType.KING:
            return False
        return self._board._move_validator.is_valid_move(
            from_square, to_square
        )

    def is_valid_pawn_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate pawn move."""
        piece = self._board.get_piece(from_square)
        if piece is None or piece.kind != PieceType.PAWN:
            return False
        return self._board._move_validator.is_valid_move(
            from_square, to_square
        )
