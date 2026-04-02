"""Pawn promotion validation logic."""

from __future__ import annotations

from typing import List, Optional

from chess_game.chess.color import Color
from chess_game.chess.pieces.piece import Piece, PieceType, ConstantSquare
from chess_game.chess.board.board_state import BoardState


class PromotionValidator:
    """Validates pawn promotion moves."""

    def __init__(self, board: BoardState):
        """Initialize with board state."""
        self.board = board

    def get_default_promotion_piece(self, color: Color) -> PieceType:
        """Get the default promotion piece (queen)."""
        return PieceType.QUEEN

    def is_promotion_required(
        self, piece: Piece, from_square : ConstantSquare, to_square : ConstantSquare
    ) -> bool:
        """Check if promotion is required for this pawn move."""
        if piece.kind != PieceType.PAWN:
            return False

        # White pawns promote when reaching rank 8 (row 7)
        # Black pawns promote when reaching rank 1 (row 0)
        if piece.color == Color.WHITE:
            return int(to_square.row) == 7
        else:
            return int(to_square.row) == 0

    def get_promotion_options(self, piece: Piece, to_square : ConstantSquare) -> List[PieceType]:
        """Get all valid promotion pieces for a pawn."""
        if piece.kind != PieceType.PAWN:
            return []

        return [
            PieceType.QUEEN,
            PieceType.ROOK,
            PieceType.BISHOP,
            PieceType.KNIGHT,
        ]

    def is_valid_promotion_piece(self, piece_type: PieceType) -> bool:
        """Check if a piece type is valid for promotion."""
        return piece_type in [
            PieceType.QUEEN,
            PieceType.ROOK,
            PieceType.BISHOP,
            PieceType.KNIGHT,
        ]

    def is_valid_promotion_choice(
        self, piece: Piece, end_pos : ConstantSquare, promotion: Optional[PieceType]
    ) -> bool:
        """Check if a promotion choice is valid."""
        # Accept None (default promotion to queen) or explicit promotion type
        if promotion is None or piece.kind != PieceType.PAWN:
            return True

        # Check if pawn is on promotion rank (rank 1 = row 0, rank 8 = row 7)
        if int(end_pos.row) not in {0, 7}:
            return False

        return promotion in [
            PieceType.QUEEN,
            PieceType.ROOK,
            PieceType.BISHOP,
            PieceType.KNIGHT,
        ]

    def is_promotion_rank(self, piece: Piece, to_square : ConstantSquare) -> bool:
        """Check if the destination is a promotion rank."""
        if piece.kind != PieceType.PAWN:
            return False

        if piece.color == Color.WHITE:
            return int(to_square.row) == 7
        else:
            return int(to_square.row) == 0

    def get_promotion_rank_for_color(self, color: Color) -> int:
        """Get the row number for promotion rank."""
        if color == Color.WHITE:
            return ROW_8
        else:
            return ROW_1
