"""Search helper functions shared by the AI module."""

from collections.abc import Callable
from typing import Any

from chess_game.chess.ai_repetition_tracking import (
    RepetitionPolicy,
    position_occurrence_count,
    repetition_score,
    search_position_counts,
)
from chess_game.chess.ai_root_selection import (
    initial_root_window,
    prefer_root_move,
    rerun_full_window_if_needed,
    update_alpha_beta,
)
from chess_game.chess.ai_root_stability import (
    _high_danger_root_bonus,
    _ignore_near_promotion_passer_penalty,
    _opening_root_bonus,
    _pawn_structure_change_root_bonus,
    root_stability_adjustment,
)
from chess_game.chess.ai_selective_extensions import (
    check_extension,
    selective_extension_bonus,
)
from chess_game.chess.board import Board
from chess_game.chess.defensive_priorities import (
    DANGEROUS_KING_PRESSURE_THRESHOLD,
    king_defense_profile,
)
from chess_game.chess.move import Move
from chess_game.chess.types import LegalMove, PieceType

# Public facade: ai_search_helpers re-exports names that moved into the extracted
# ai_root_selection / ai_root_stability / ai_selective_extensions / repetition
# modules, so chess_game.chess.ai_search_helpers.<name> keeps resolving for the
# search core and tests. Declared for the linters as intentional re-exports.
__all__ = [
    "DANGEROUS_KING_PRESSURE_THRESHOLD",
    "RepetitionPolicy",
    "_high_danger_root_bonus",
    "_ignore_near_promotion_passer_penalty",
    "_opening_root_bonus",
    "_pawn_structure_change_root_bonus",
    "check_extension",
    "defensive_capture_bonus",
    "initial_root_window",
    "position_occurrence_count",
    "prefer_root_move",
    "promotion_order_score",
    "record_depth_timing",
    "record_root_research",
    "record_selective_extension",
    "repetition_score",
    "rerun_full_window_if_needed",
    "root_stability_adjustment",
    "same_legal_move",
    "search_position_counts",
    "selective_extension_bonus",
    "update_alpha_beta",
]


def record_root_research(context: Any) -> None:
    """Record a root re-search caused by aspiration failure."""

    if context.stats is not None:
        context.stats.root_researches += 1


def record_depth_timing(
    context: Any,
    depth: int,
    elapsed: float,
) -> None:
    """Store per-depth timing diagnostics."""

    if context.stats is None:
        return
    if context.stats.depth_timings is None:
        context.stats.depth_timings = {}
    context.stats.depth_timings[depth] = elapsed


def same_legal_move(move: Move, legal_move: LegalMove) -> bool:
    """Return True when two move objects represent the same move."""

    return (
        move.start == legal_move.start
        and move.end == legal_move.end
        and move.promotion == legal_move.promotion
    )


def record_selective_extension(context: Any) -> None:
    """Record a bounded selective extension when diagnostics are enabled."""

    if context is None or context.stats is None or context.stats.diagnostics is None:
        return
    context.stats.diagnostics.selective_extensions += 1


def promotion_order_score(move: Move) -> int:
    """Return a move-ordering bonus for promotions."""

    if move.promotion is None:
        return 0
    promotion_order_bonus = {
        PieceType.QUEEN: 900,
        PieceType.ROOK: 500,
        PieceType.BISHOP: 330,
        PieceType.KNIGHT: 320,
    }
    return promotion_order_bonus.get(move.promotion, 0)


def defensive_capture_bonus(
    board: Board,
    move: Move,
    captured_kind: PieceType,
    copy_with_move: Callable[[Board, Move], Board],
) -> int:
    """Prioritize danger-reducing heavy-piece trades when the king is under pressure."""

    if captured_kind not in {PieceType.QUEEN, PieceType.ROOK}:
        return 0
    before = king_defense_profile(board, board.turn)
    if before.danger < DANGEROUS_KING_PRESSURE_THRESHOLD:
        return 0
    child_board = copy_with_move(board, move)
    after = king_defense_profile(child_board, board.turn)
    score = max(0, before.danger - after.danger) * 250
    score += max(0, before.invasion_lines - after.invasion_lines) * 120
    if before.back_rank_weak and not after.back_rank_weak:
        score += 90
    return score
