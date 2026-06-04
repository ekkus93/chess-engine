"""Shared tactical-transition guidance for move ordering and root tie-breaks."""

from __future__ import annotations

from chess_game.chess.board import Board
from chess_game.chess.defensive_priorities import (
    DANGEROUS_KING_PRESSURE_THRESHOLD,
    king_defense_profile,
)
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    both_queens_on_board,
    exposed_shield_files,
    is_capture_move,
    is_castled_king,
)
from chess_game.chess.types import Color, PieceType

TACTICAL_TRANSITION_PRESSURE_RELIEF_BONUS = 12
TACTICAL_TRANSITION_SAFE_CAPTURE_BONUS = 14
TACTICAL_TRANSITION_CENTRAL_CAPTURE_BONUS = 10
TACTICAL_TRANSITION_SHELTER_LOOSENING_PENALTY = 96
TACTICAL_TRANSITION_ADVANCED_SHELTER_PENALTY = 28


def tactical_transition_order_bonus(board: Board, move: Move) -> int:
    """Return a quiet-order bonus for practical tactical-transition moves."""

    piece = board.get_piece(move.start)
    if (
        piece is None
        or move.promotion is not None
        or is_capture_move(board, move)
        or piece.kind != PieceType.PAWN
    ):
        return 0
    return (
        -(TACTICAL_TRANSITION_SHELTER_LOOSENING_PENALTY // 2)
        if _is_quiet_shelter_pawn_push(board, move, piece.color)
        else 0
    )


def tactical_transition_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
) -> int:
    """Return a root tie-break bonus for cleaner tactical transitions."""

    before = king_defense_profile(board, moving_color)
    after = king_defense_profile(child_board, moving_color)
    score = (
        max(0, before.danger - after.danger) * TACTICAL_TRANSITION_PRESSURE_RELIEF_BONUS
    )
    score += max(0, before.invasion_lines - after.invasion_lines) * (
        TACTICAL_TRANSITION_PRESSURE_RELIEF_BONUS // 2
    )
    score += _safe_capture_bonus(board, move, before, after)
    if _is_unforced_shelter_pawn_push(board, move, moving_color, before, after):
        score -= TACTICAL_TRANSITION_SHELTER_LOOSENING_PENALTY
    return score


def tactical_transition_king_penalty(board: Board, color: Color) -> int:
    """Return a middlegame penalty for fragile castled shelter during tactical play."""

    king_square = board.find_king(color)
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    if (
        king_square is None
        or not both_queens_on_board(board)
        or not is_castled_king(color, king_square)
        or king_defense_profile(board, enemy_color).danger
        >= DANGEROUS_KING_PRESSURE_THRESHOLD
    ):
        return 0
    penalty = 0
    for file_index in exposed_shield_files(board, color, int(king_square.col)):
        penalty += TACTICAL_TRANSITION_ADVANCED_SHELTER_PENALTY
        if file_index in {0, 7}:
            penalty += TACTICAL_TRANSITION_ADVANCED_SHELTER_PENALTY // 2
    return penalty


def _safe_capture_bonus(
    board: Board,
    move: Move,
    before,
    after,
) -> int:
    if not is_capture_move(board, move):
        return 0
    captured_piece = board.get_piece(move.end)
    if captured_piece is None:
        return 0
    score = 0
    if after.danger <= before.danger and after.invasion_lines <= before.invasion_lines:
        score += TACTICAL_TRANSITION_SAFE_CAPTURE_BONUS
    if captured_piece.kind == PieceType.PAWN and int(move.end.col) in {3, 4}:
        score += TACTICAL_TRANSITION_CENTRAL_CAPTURE_BONUS
    elif captured_piece.kind in {
        PieceType.KNIGHT,
        PieceType.BISHOP,
        PieceType.ROOK,
        PieceType.QUEEN,
    }:
        score += TACTICAL_TRANSITION_CENTRAL_CAPTURE_BONUS
    return score


def _is_unforced_shelter_pawn_push(
    board: Board,
    move: Move,
    color: Color,
    before,
    after,
) -> bool:
    moving_piece = board.get_piece(move.start)
    king_square = board.find_king(color)
    if (
        moving_piece is None
        or moving_piece.kind != PieceType.PAWN
        or king_square is None
        or not _supports_shelter_penalty(board, color, king_square)
        or is_capture_move(board, move)
    ):
        return False
    home_row = 6 if color == Color.WHITE else 1
    start_col = int(move.start.col)
    end_col = int(move.end.col)
    if int(move.start.row) != home_row or end_col != start_col:
        return False
    if abs(start_col - int(king_square.col)) > 1:
        return False
    if after.danger < before.danger or after.invasion_lines < before.invasion_lines:
        return False
    return True


def _is_quiet_shelter_pawn_push(board: Board, move: Move, color: Color) -> bool:
    king_square = board.find_king(color)
    if king_square is None or not _supports_shelter_penalty(board, color, king_square):
        return False
    home_row = 6 if color == Color.WHITE else 1
    start_col = int(move.start.col)
    advance = abs(int(move.end.row) - int(move.start.row))
    king_col = int(king_square.col)
    adjacent = -1 <= start_col - king_col <= 1
    return (
        int(move.start.row) == home_row
        and int(move.end.col) == start_col
        and adjacent
        and advance > 1
    )


def _supports_shelter_penalty(board: Board, color: Color, king_square) -> bool:
    return both_queens_on_board(board) and is_castled_king(color, king_square)
