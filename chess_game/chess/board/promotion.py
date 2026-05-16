"""Pawn promotion validation logic."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from chess_game.chess.constants import Color
from chess_game.chess.types import Piece, PieceType
from chess_game.chess.constants import ConstantSquare

if TYPE_CHECKING:
    from chess_game.chess.board.board import Board


class PromotionValidator:
    """Validates pawn promotion moves."""

    def __init__(self, board: Board):
        self.board = board

    def get_default_promotion_piece(self, _color: Color) -> PieceType:
        """Return the default promotion piece type."""
        return PieceType.QUEEN

    def is_promotion_required(
        self, piece: Piece, _from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Return True if moving the piece to to_square triggers promotion."""
        if piece.kind != PieceType.PAWN:
            return False

        # White promotes at row 0 (rank 8), Black at row 7 (rank 1)
        if piece.color == Color.WHITE:
            return int(to_square.row) == 0
        return int(to_square.row) == 7

    def get_promotion_options(
        self, piece: Piece, _to_square: ConstantSquare
    ) -> List[PieceType]:
        """Return all valid promotion piece types for a pawn."""
        if piece.kind != PieceType.PAWN:
            return []

        return [
            PieceType.QUEEN,
            PieceType.ROOK,
            PieceType.BISHOP,
            PieceType.KNIGHT,
        ]

    def is_valid_promotion_piece(self, piece_type: PieceType) -> bool:
        """Return True if piece_type is a valid promotion target."""
        return piece_type in [
            PieceType.QUEEN,
            PieceType.ROOK,
            PieceType.BISHOP,
            PieceType.KNIGHT,
        ]

    def is_valid_promotion_choice(
        self, piece: Piece, end_pos: ConstantSquare, promotion: Optional[PieceType]
    ) -> bool:
        """Return True if the promotion choice is valid for this move."""
        if promotion is None:
            return True
        if piece.kind != PieceType.PAWN:
            return False

        if not isinstance(promotion, PieceType):
            return False

        if int(end_pos.row) not in {0, 7}:
            return False

        return promotion in [
            PieceType.QUEEN,
            PieceType.ROOK,
            PieceType.BISHOP,
            PieceType.KNIGHT,
        ]

    def is_promotion_rank(self, piece: Piece, to_square: ConstantSquare) -> bool:
        """Return True if to_square is on the promotion rank for piece's color."""
        if piece.kind != PieceType.PAWN:
            return False

        if piece.color == Color.WHITE:
            return int(to_square.row) == 0
        return int(to_square.row) == 7

    def get_promotion_rank_for_color(self, color: Color) -> int:
        """Return the promotion row index for the given color."""
        if color == Color.WHITE:
            return 0
        return 7
