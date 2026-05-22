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
from chess_game.chess.strategy_utils import is_capture_move
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
    penalty = _repetition_penalty(policy, evaluation, policy.progress(board))
    if evaluation >= policy.threshold:
        return -penalty
    if evaluation <= -policy.threshold:
        return penalty
    progress = policy.progress(board)
    if progress >= policy.progress_threshold:
        return -penalty
    if progress <= -policy.progress_threshold:
        return penalty
    return 0


def _repetition_penalty(
    policy: RepetitionPolicy,
    evaluation: int,
    progress: int,
) -> int:
    scale = max(
        abs(evaluation) // max(policy.threshold, 1),
        abs(progress) // max(policy.progress_threshold, 1),
        1,
    )
    capped_scale = min(scale, 5)
    return policy.penalty * capped_scale


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
    context: Any = None,
    position_key: Callable[[Board], str] | None = None,
) -> int:
    """Return a root-only tie-break bonus for stable attack/defense moves.

    This intentionally stays out of static evaluation and quiescence: it only
    nudges near-equal root choices toward lines that either reduce urgent king
    danger or create fresh tactical pressure without drifting into repetition.
    """

    moving_piece = board.get_piece(move.start)
    if moving_piece is None:
        return 0
    moving_color = moving_piece.color
    enemy_color = Color.BLACK if moving_color == Color.WHITE else Color.WHITE
    signed_bonus = _defensive_root_bonus(board, child_board, moving_color)
    signed_bonus += _attacking_root_bonus(
        board,
        move,
        child_board,
        moving_color,
        enemy_color,
    )
    signed_bonus -= _repetition_root_penalty(
        board,
        move,
        child_board,
        context,
        position_key,
    )
    if signed_bonus == 0:
        return 0
    return signed_bonus if moving_color == Color.WHITE else -signed_bonus


def selective_extension_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    extension_budget: int,
) -> int:
    """Return a bounded one-ply extension for critical attack/defense moves.

    Extensions stay binary and narrow on purpose so king-danger signals do not
    double-count with static evaluation or root tie-break logic.
    """

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
    elif _is_danger_opening_capture(board, move, child_board, enemy_color):
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


def _is_danger_opening_capture(
    board: Board,
    move: Move,
    child_board: Board,
    enemy_color: Color,
) -> bool:
    """Return True for captures that clearly increase pressure on the enemy king."""

    if not is_capture_move(board, move):
        return False
    before = king_defense_profile(board, enemy_color)
    after = king_defense_profile(child_board, enemy_color)
    if after.danger < DANGEROUS_KING_PRESSURE_THRESHOLD:
        return False
    return after.danger > before.danger or after.invasion_lines > before.invasion_lines


def _defensive_root_bonus(board: Board, child_board: Board, moving_color: Color) -> int:
    """Return a small bonus for root moves that clearly stabilize the king."""

    before = king_defense_profile(board, moving_color)
    if before.danger < DANGEROUS_KING_PRESSURE_THRESHOLD:
        return 0
    after = king_defense_profile(child_board, moving_color)
    score = max(0, before.danger - after.danger) * 36
    score += max(0, before.invasion_lines - after.invasion_lines) * 24
    score += max(0, after.king_zone_defenders - before.king_zone_defenders) * 16
    score += max(0, after.heavy_connections - before.heavy_connections) * 12
    score += max(0, after.safe_king_moves - before.safe_king_moves) * 12
    if before.back_rank_weak and not after.back_rank_weak:
        score += 24
    return score


def _attacking_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
    enemy_color: Color,
) -> int:
    """Return a bonus for fresh tactical lines that keep real pressure alive."""

    if (
        king_danger_index(board, moving_color) >= DANGEROUS_KING_PRESSURE_THRESHOLD
        or king_needs_shelter(board, moving_color)
    ):
        return 0
    before = king_defense_profile(board, enemy_color)
    after = king_defense_profile(child_board, enemy_color)
    danger_gain = max(0, after.danger - before.danger)
    invasion_gain = max(0, after.invasion_lines - before.invasion_lines)
    score = danger_gain * 16
    score += invasion_gain * 18
    if (
        is_in_check(child_board, enemy_color)
        and after.danger >= DANGEROUS_KING_PRESSURE_THRESHOLD
        and (danger_gain > 0 or invasion_gain > 0)
    ):
        score += 14
    if is_capture_move(board, move):
        score += 10
    return score


def _repetition_root_penalty(
    board: Board,
    move: Move,
    child_board: Board,
    context: Any,
    position_key: Callable[[Board], str] | None,
) -> int:
    """Penalize repeated root tactics unless they clearly improve the position."""

    if context is None or position_key is None:
        return 0
    occurrence_count = position_occurrence_count(
        child_board,
        context,
        (),
        position_key,
    )
    if occurrence_count <= 0:
        return 0
    moving_piece = board.get_piece(move.start)
    if moving_piece is None:
        return 0
    moving_color = moving_piece.color
    enemy_color = Color.BLACK if moving_color == Color.WHITE else Color.WHITE
    if _has_genuine_tactical_payoff(board, move, child_board, moving_color, enemy_color):
        return 0
    return 48 * occurrence_count


def _has_genuine_tactical_payoff(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
    enemy_color: Color,
) -> bool:
    """Return True when a repeated tactical line still improves attack or defense."""

    before_enemy = king_defense_profile(board, enemy_color)
    after_enemy = king_defense_profile(child_board, enemy_color)
    before_self = king_defense_profile(board, moving_color)
    after_self = king_defense_profile(child_board, moving_color)
    return (
        is_capture_move(board, move)
        or after_enemy.danger > before_enemy.danger
        or after_enemy.invasion_lines > before_enemy.invasion_lines
        or after_self.danger < before_self.danger
    )


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
