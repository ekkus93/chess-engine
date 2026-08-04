"""Forced-win detection and move acceleration for trivial endgames."""

from __future__ import annotations

from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    iter_color_pieces,
    king_coordinates,
    opposite_color,
)
from chess_game.chess.types import Color, PieceType

# Material thresholds for forced-win detection
# _is_bare_king() already prevents false positives, so any modest material
# lead over a bare king is a genuine forced win.
_FORCED_WIN_MATERIAL_THRESHOLD = 50  # ~half a pawn

# Move prioritization bonuses — small enough not to override deeper guidance
_FORCED_WIN_PAWN_PUSH_BONUS = 60
_FORCED_WIN_KING_ATTACK_BONUS = 50

# Material values for internal scoring
_MATERIAL_VALUES = {
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 300,
    PieceType.BISHOP: 300,
    PieceType.ROOK: 500,
    PieceType.QUEEN: 900,
}


def is_forced_win_endgame(board: Board, color: Color) -> bool:
    """Return True if *color* is in a clearly won endgame (e.g. Q vs bare K).

    Criteria:
    - Material lead >= threshold (e.g. rook advantage).
    - Opponent has NO pieces AND NO pawns (bare king only).
    """
    own_material = _material_count(board, color)
    opp_material = _material_count(board, opposite_color(color))
    if own_material - opp_material < _FORCED_WIN_MATERIAL_THRESHOLD:
        return False
    return _is_bare_king(board, opposite_color(color))


def forced_win_move_bonus(board: Board, move: Move, color: Color) -> int:
    """Return a tiered bonus for moves that accelerate forced-win conversion.

    Only applies in pure K+piece(s) vs bare K endgames.
    Rewards: pawn pushes toward promotion, king moves toward the opponent king.
    Returns 0 when not in a forced-win position.
    """
    if not is_forced_win_endgame(board, color):
        return 0

    start_row, start_col = int(move.start.row), int(move.start.col)
    end_row, end_col = int(move.end.row), int(move.end.col)

    start_piece = board.board[start_row][start_col]
    if start_piece is None:
        return 0

    bonus = 0

    # Pawn advance toward promotion
    if start_piece.kind == PieceType.PAWN:
        if (color == Color.WHITE and end_row < start_row) or \
           (color == Color.BLACK and end_row > start_row):
            bonus += _FORCED_WIN_PAWN_PUSH_BONUS

    # King moves toward opponent king
    if start_piece.kind == PieceType.KING:
        opponent_king = king_coordinates(board, opposite_color(color))
        if opponent_king is not None:
            opp_row, opp_col = opponent_king
            old_dist = _chebyshev((start_row, start_col), (opp_row, opp_col))
            new_dist = _chebyshev((end_row, end_col), (opp_row, opp_col))
            if new_dist < old_dist:
                bonus += _FORCED_WIN_KING_ATTACK_BONUS

    return bonus


def forced_win_root_bonus(
    board: Board, move: Move, _child_board: Board, color: Color
) -> int:
    """Root-level tiebreak bonus that accelerates forced-win conversion.

    Uses the already-computed child_board (no extra clone needed).
    Returns 0 when not in a forced-win position.
    """
    if not is_forced_win_endgame(board, color):
        return 0

    start_row, start_col = int(move.start.row), int(move.start.col)
    end_row, end_col = int(move.end.row), int(move.end.col)

    start_piece = board.board[start_row][start_col]
    if start_piece is None:
        return 0

    bonus = 0

    # Pawn advance toward promotion
    if start_piece.kind == PieceType.PAWN:
        if (color == Color.WHITE and end_row < start_row) or \
           (color == Color.BLACK and end_row > start_row):
            bonus += _FORCED_WIN_PAWN_PUSH_BONUS

    # King moves toward opponent king
    if start_piece.kind == PieceType.KING:
        opponent_king = king_coordinates(board, opposite_color(color))
        if opponent_king is not None:
            opp_row, opp_col = opponent_king
            old_dist = _chebyshev((start_row, start_col), (opp_row, opp_col))
            new_dist = _chebyshev((end_row, end_col), (opp_row, opp_col))
            if new_dist < old_dist:
                bonus += _FORCED_WIN_KING_ATTACK_BONUS

    return bonus


def _is_bare_king(board: Board, color: Color) -> bool:
    """Return True if *color* has only a king (no pawns, no pieces)."""
    for piece, _, _ in iter_color_pieces(board, color):
        if piece.kind != PieceType.KING:
            return False
    return True


def _material_count(board: Board, color: Color) -> int:
    """Total material in centipawns for *color* (king excluded)."""
    return sum(
        _MATERIAL_VALUES.get(piece.kind, 0)
        for piece, _, _ in iter_color_pieces(board, color)
    )


def _chebyshev(pos1: tuple[int, int], pos2: tuple[int, int]) -> int:
    """Chebyshev (king) distance between two board positions."""
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))
