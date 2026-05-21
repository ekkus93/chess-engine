"""Search helper functions shared by the AI module."""

from dataclasses import dataclass
from typing import Any, Callable, Optional

from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.defensive_priorities import (
    DANGEROUS_KING_PRESSURE_THRESHOLD,
    king_defense_profile,
    king_danger_index,
    king_needs_shelter,
)
from chess_game.chess.move import Move
from chess_game.chess.types import Color, LegalMove, PieceType


@dataclass(frozen=True)
class RepetitionPolicy:
    """Configuration for repetition-aware draw scoring."""

    position_key: Callable[[Board], str]
    evaluate: Callable[[Board], int]
    progress: Callable[[Board], int]
    threshold: int
    progress_threshold: int
    penalty: int


def initial_root_window(
    depth: int,
    previous_score: int,
    aspiration_window: int,
    inf: int,
) -> tuple[int, int]:
    """Return the initial alpha-beta window for one root search."""

    if depth == 1:
        return -inf, inf
    return previous_score - aspiration_window, previous_score + aspiration_window


def rerun_full_window_if_needed(
    score: int,
    alpha: int,
    beta: int,
    context: Any,
    inf: int,
) -> bool:
    """Return True when the root search must rerun with a full window."""

    if alpha == -inf and beta == inf:
        return False
    if score <= alpha:
        if context.stats is not None:
            context.stats.fail_low_retries += 1
        return True
    if score >= beta:
        if context.stats is not None:
            context.stats.fail_high_retries += 1
        return True
    return False


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


def search_position_counts(
    board: Board,
    position_counts: Optional[dict[str, int]],
    position_key: Callable[[Board], str],
) -> Optional[dict[str, int]]:
    """Return repetition counts adjusted so the current root is not double-counted."""

    if position_counts is None:
        return None
    adjusted_counts = dict(position_counts)
    current_key = position_key(board)
    if adjusted_counts.get(current_key, 0) > 0:
        adjusted_counts[current_key] -= 1
        if adjusted_counts[current_key] == 0:
            del adjusted_counts[current_key]
    return adjusted_counts


def position_occurrence_count(
    board: Board,
    context: Any,
    line_history: tuple[str, ...],
    position_key: Callable[[Board], str],
) -> int:
    """Return the number of times the current position has appeared in search/game history."""

    current_key = position_key(board)
    game_count = (
        0
        if context is None or context.position_counts is None
        else context.position_counts.get(current_key, 0)
    )
    return game_count + line_history.count(current_key)


def repetition_score(
    board: Board,
    context: Any,
    line_history: tuple[str, ...],
    policy: RepetitionPolicy,
) -> Optional[int]:
    """Return a repetition-draw score, biased against the side wasting an advantage."""

    if position_occurrence_count(board, context, line_history, policy.position_key) < 3:
        return None
    evaluation = policy.evaluate(board)
    if evaluation >= policy.threshold:
        return -policy.penalty
    if evaluation <= -policy.threshold:
        return policy.penalty
    progress = policy.progress(board)
    if progress >= policy.progress_threshold:
        return -policy.penalty
    if progress <= -policy.progress_threshold:
        return policy.penalty
    return 0


def update_best_result(
    is_maximizing: bool,
    move: Move,
    child_score: int,
    best_score: int,
    best_move: Optional[LegalMove],
) -> tuple[int, Optional[LegalMove]]:
    """Update the best move/score for the current node."""

    better_score = child_score > best_score if is_maximizing else child_score < best_score
    if not better_score:
        return best_score, best_move
    return child_score, LegalMove(move.start, move.end, move.promotion)


def update_alpha_beta(
    is_maximizing: bool,
    best_score: int,
    alpha: int,
    beta: int,
) -> tuple[int, int, bool]:
    """Update alpha/beta and report whether a cutoff occurred."""

    if is_maximizing:
        alpha = max(alpha, best_score)
        return alpha, beta, alpha >= beta
    beta = min(beta, best_score)
    return alpha, beta, beta <= alpha


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


def root_stability_adjustment(
    board: Board,
    move: Move,
    child_board: Board,
) -> int:
    """Return a small root-only bonus for urgent threat-reducing moves."""

    moving_piece = board.get_piece(move.start)
    if moving_piece is None:
        return 0
    before = king_defense_profile(board, moving_piece.color)
    if before.danger < DANGEROUS_KING_PRESSURE_THRESHOLD:
        return 0
    after = king_defense_profile(child_board, moving_piece.color)
    signed_bonus = max(0, before.danger - after.danger) * 36
    signed_bonus += max(0, before.invasion_lines - after.invasion_lines) * 24
    signed_bonus += max(0, after.king_zone_defenders - before.king_zone_defenders) * 16
    signed_bonus += max(0, after.heavy_connections - before.heavy_connections) * 12
    if before.back_rank_weak and not after.back_rank_weak:
        signed_bonus += 24
    if signed_bonus == 0:
        return 0
    return signed_bonus if moving_piece.color == Color.WHITE else -signed_bonus


def selective_extension_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    extension_budget: int,
) -> int:
    """Return a bounded one-ply extension for critical attack/defense moves."""

    bonus = 0
    moving_piece = board.get_piece(move.start)
    if extension_budget <= 0 or moving_piece is None:
        return bonus
    moving_color = moving_piece.color
    enemy_color = Color.BLACK if moving_color == Color.WHITE else Color.WHITE
    current_danger = king_danger_index(board, moving_color)
    if is_in_check(board, moving_color):
        bonus = 1
    elif current_danger >= DANGEROUS_KING_PRESSURE_THRESHOLD:
        if king_danger_index(child_board, moving_color) < current_danger:
            bonus = 1
    elif not king_needs_shelter(board, moving_color) and _is_forcing_attack_extension(
        board,
        move,
        child_board,
        moving_piece.kind,
        enemy_color,
    ):
        bonus = 1
    return bonus
def _is_forcing_attack_extension(
    board: Board,
    move: Move,
    child_board: Board,
    moving_kind: PieceType,
    enemy_color: Color,
) -> bool:
    """Return True for forcing attacking moves worth one extra search ply."""

    enemy_danger_before = king_danger_index(board, enemy_color)
    enemy_danger_after = king_danger_index(child_board, enemy_color)
    gives_check = is_in_check(child_board, enemy_color)
    if (
        not gives_check
        or enemy_danger_after < DANGEROUS_KING_PRESSURE_THRESHOLD
        or not _is_heavy_piece_invasion(move, moving_kind, enemy_color)
    ):
        return False
    return enemy_danger_after > enemy_danger_before


def _is_heavy_piece_invasion(
    move: Move,
    moving_kind: PieceType,
    enemy_color: Color,
) -> bool:
    """Return True when a rook or queen reaches the enemy back-rank zone."""

    if moving_kind not in {PieceType.ROOK, PieceType.QUEEN}:
        return False
    enemy_back_rank_zone = {0, 1} if enemy_color == Color.BLACK else {6, 7}
    return int(move.end.row) in enemy_back_rank_zone
