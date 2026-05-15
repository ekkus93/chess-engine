"""Module-level game-state predicates extracted from Board.

Provides `is_in_check`, `is_checkmate`, and `is_stalemate` so that Board
doesn't have to carry them as instance methods.
"""

from __future__ import annotations

from typing import Optional

from chess_game.chess.board.castling import CastlingValidator
from chess_game.chess.types import Color


def is_in_check(board: "Board", color: Color) -> bool:  # noqa: F821
    """Check if the given color's king is currently in check."""
    king_sq = board.find_king(color)
    if king_sq is None:
        return False
    enemy = Color.BLACK if color == Color.WHITE else Color.WHITE
    return CastlingValidator.is_square_attacked(board, king_sq, enemy)


def is_checkmate(board: "Board", color: Optional[Color] = None) -> bool:  # noqa: F821
    """Check if the given color (or side-to-move) is in checkmate."""
    c = color if color is not None else board.turn
    if not is_in_check(board, c):
        return False
    return len(board.get_legal_moves_for_color(c)) == 0


def is_stalemate(board: "Board", color: Optional[Color] = None) -> bool:  # noqa: F821
    """Check if the given color (or side-to-move) is in stalemate."""
    c = color if color is not None else board.turn
    if is_in_check(board, c):
        return False
    return len(board.get_legal_moves_for_color(c)) == 0
