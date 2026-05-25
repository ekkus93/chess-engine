"""Helpers for quiescence move selection."""

from __future__ import annotations

from typing import Callable

from chess_game.chess.ai_search_helpers import promotion_order_score
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_in_check as _gs_is_in_check
from chess_game.chess.defensive_priorities import king_defense_profile
from chess_game.chess.move import Move
from chess_game.chess.structure_recognition import (
    structure_capture_bonus,
    structure_profile,
)
from chess_game.chess.strategy_utils import is_capture_move
from chess_game.chess.types import Color, PieceType
from chess_game.chess.evaluation import MATERIAL_VALUES

_MVV_OFFSET = 100_000


def select_quiescence_moves(
    board: Board,
    legal_moves: list[Move],
    move_order_score: Callable[[Board, Move], int],
    max_moves: int,
) -> list[Move]:
    """Return the most relevant tactical moves for quiescence search.

    Uses cheap static analysis only (no board simulation) so it stays within
    performance budgets at depth 4 and 5.
    """

    in_check = _gs_is_in_check(board, board.turn)
    has_forcing_move = any(
        move.promotion is not None or is_capture_move(board, move)
        for move in legal_moves
    )
    if not has_forcing_move and not in_check:
        return []

    scored_moves: list[tuple[int, int, Move]] = []
    for move in legal_moves:
        score = _quiescence_move_static_score(board, move)
        if score > 0:
            scored_moves.append((score, move_order_score(board, move), move))
    scored_moves.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [move for _, _, move in scored_moves[:max_moves]]


def _quiescence_move_static_score(board: Board, move: Move) -> int:
    """Cheap static selectivity score — no board simulation.

    Returns 0 to exclude the move from quiescence search.
    """

    if move.promotion is not None:
        return _MVV_OFFSET + 5_000 + promotion_order_score(move)
    if is_capture_move(board, move):
        return _quiescence_capture_mvv_lva(board, move)
    return 0


def _quiescence_capture_mvv_lva(board: Board, move: Move) -> int:
    """MVV-LVA capture score, filtering clearly losing low-value captures."""

    captured = board.get_piece(move.end)
    attacker = board.get_piece(move.start)
    if captured is None or attacker is None:
        return _MVV_OFFSET + MATERIAL_VALUES[PieceType.PAWN] * 10
    cap_val = MATERIAL_VALUES[captured.kind]
    atk_val = MATERIAL_VALUES[attacker.kind]
    if cap_val < MATERIAL_VALUES[PieceType.BISHOP] and atk_val > cap_val:
        return 0
    return _MVV_OFFSET + cap_val * 10 - atk_val


def _get_tactical_moves(
    board: Board,
    legal_moves: tuple[Move, ...] | list[Move] | None = None,
    move_order_score: Callable[[Board, Move], int] | None = None,
    max_moves: int = 4,
) -> list[Move]:
    """Compatibility wrapper used by the main AI module."""

    if legal_moves is None or move_order_score is None:
        return []
    return select_quiescence_moves(board, list(legal_moves), move_order_score, max_moves)


# ---------------------------------------------------------------------------
# Analysis functions — not in the selection hot path; exported for tests
# ---------------------------------------------------------------------------


def _quiescence_tactical_score(board: Board, move: Move) -> int:
    """Return a simulation-based quality score for quiescence move selection.

    Uses board simulation for higher-quality scoring.  Not used in the search
    hot path; exported for regression tests.
    """

    moving_piece = board.get_piece(move.start)
    if moving_piece is None:
        return 0
    moving_color = moving_piece.color
    enemy_color = Color.BLACK if moving_color == Color.WHITE else Color.WHITE
    score = 0
    if move.promotion is not None:
        score += 1_000 + promotion_order_score(move)
    if is_capture_move(board, move):
        base_capture_score = _quiescence_capture_base_score(board, move, moving_color)
        if base_capture_score < 1_200:
            return 0
        child_board = _make_copy_with_move(board, move)
        score += _quiescence_capture_score(board, move, child_board, moving_color)
    else:
        if not _gs_is_in_check(board, board.turn):
            return score
        child_board = _make_copy_with_move(board, move)
    if _gs_is_in_check(child_board, enemy_color):
        score += _quiescence_check_score(board, child_board, enemy_color)
    if score > 0 and (board.get_piece(move.end) is not None or move.promotion is not None):
        structure_follow_up_score = _quiescence_structure_follow_up_score(board, child_board)
        if structure_follow_up_score > 0:
            score += structure_follow_up_score
    return score


def _quiescence_capture_base_score(
    board: Board,
    move: Move,
    moving_color: Color,
) -> int:
    """Return a cheap capture score before simulating the move."""

    captured_piece = board.get_piece(move.end)
    moving_piece = board.get_piece(move.start)
    if captured_piece is None or moving_piece is None:
        return 0
    score = MATERIAL_VALUES[captured_piece.kind] * 100
    score += structure_capture_bonus(
        board,
        moving_color,
        moving_piece.kind,
        captured_piece.kind,
        move.end,
    )
    if captured_piece.kind in {PieceType.ROOK, PieceType.QUEEN}:
        score += 220
    elif captured_piece.kind in {PieceType.BISHOP, PieceType.KNIGHT}:
        score += 90
    return score


def _quiescence_capture_score(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
) -> int:
    """Return a quiescence score for a capture that changes the position."""

    captured_piece = board.get_piece(move.end)
    if captured_piece is None:
        return 0
    moving_piece = board.get_piece(move.start)
    score = MATERIAL_VALUES[captured_piece.kind] * 100
    score += structure_capture_bonus(
        board,
        moving_color,
        moving_piece.kind if moving_piece is not None else captured_piece.kind,
        captured_piece.kind,
        move.end,
    )
    before_profile = king_defense_profile(board, moving_color)
    after_profile = king_defense_profile(child_board, moving_color)
    score += max(0, before_profile.danger - after_profile.danger) * 250
    score += max(0, before_profile.invasion_lines - after_profile.invasion_lines) * 140
    score += max(0, after_profile.safe_king_moves - before_profile.safe_king_moves) * 60
    if before_profile.back_rank_weak and not after_profile.back_rank_weak:
        score += 180
    if captured_piece.kind in {PieceType.ROOK, PieceType.QUEEN}:
        score += 220
    elif captured_piece.kind in {PieceType.BISHOP, PieceType.KNIGHT}:
        score += 90
    return score if score >= 1_200 else 0


def _quiescence_check_score(
    board: Board,
    child_board: Board,
    enemy_color: Color,
) -> int:
    """Return a quiescence score for a checking move that matters materially."""

    before_profile = king_defense_profile(board, enemy_color)
    after_profile = king_defense_profile(child_board, enemy_color)
    score = max(0, before_profile.safe_king_moves - after_profile.safe_king_moves) * 120
    score += max(0, after_profile.danger - before_profile.danger) * 160
    score += max(0, after_profile.invasion_lines - before_profile.invasion_lines) * 100
    if not before_profile.back_rank_weak and after_profile.back_rank_weak:
        score += 180
    return score if score >= 180 else 0


def _quiescence_structure_follow_up_score(board: Board, child_board: Board) -> int:
    """Return a bonus for moves that materially alter pawn structure."""

    before_profile = structure_profile(board)
    after_profile = structure_profile(child_board)
    if before_profile == after_profile:
        return 0
    score = 0
    if before_profile.open_center != after_profile.open_center:
        score += 180
    if before_profile.closed_center != after_profile.closed_center:
        score += 180
    if before_profile.opposite_side_castling != after_profile.opposite_side_castling:
        score += 120
    if before_profile.rook_endgame_with_passer_plan != after_profile.rook_endgame_with_passer_plan:
        score += 120
    if before_profile.white != after_profile.white:
        score += 80
    if before_profile.black != after_profile.black:
        score += 80
    return score


def _make_copy_with_move(board: Board, move: Move) -> Board:
    """Create a new board state after making a move."""

    simulated = board.clone()
    if not simulated.apply_legal_move(
        move.start,
        move.end,
        promotion=move.promotion,
    ):
        raise RuntimeError("Simulated move failed legality check")
    return simulated
