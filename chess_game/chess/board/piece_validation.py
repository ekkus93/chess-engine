"""Piece-specific move validation delegate.

Holds the six `is_valid_*_move` methods extracted from Board to reduce
Board's public method count.
"""

from __future__ import annotations

from chess_game.chess.types import PieceType
from chess_game.chess.constants import ConstantSquare

_PIECE_CHECKERS = {
    PieceType.ROOK: "rook",
    PieceType.BISHOP: "bishop",
    PieceType.QUEEN: "queen",
    PieceType.KNIGHT: "knight",
    PieceType.KING: "king",
    PieceType.PAWN: "pawn",
}


class PieceMoveChecker:
    """Validates moves for specific piece types by delegating to MoveValidator."""

    def __init__(self, board: "Board") -> None:  # noqa: F821
        self._board = board

    def _check_piece_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare, expected_kind: PieceType
    ) -> bool:
        """Check that the piece on from_square matches expected_kind, then validate."""
        piece = self._board.get_piece(from_square)
        if piece is None or piece.kind != expected_kind:
            return False
        return self._board.is_valid_move(from_square, to_square)

    def is_valid_rook_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate rook move (straight line)."""
        return self._check_piece_move(from_square, to_square, PieceType.ROOK)

    def is_valid_bishop_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate bishop move (diagonal)."""
        return self._check_piece_move(from_square, to_square, PieceType.BISHOP)

    def is_valid_queen_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate queen move (straight or diagonal)."""
        return self._check_piece_move(from_square, to_square, PieceType.QUEEN)

    def is_valid_knight_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate knight move (L-shape)."""
        return self._check_piece_move(from_square, to_square, PieceType.KNIGHT)

    def is_valid_king_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate king move (one square in any direction)."""
        return self._check_piece_move(from_square, to_square, PieceType.KING)

    def is_valid_pawn_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate pawn move."""
        return self._check_piece_move(from_square, to_square, PieceType.PAWN)
