"""Search helper functions shared by the AI module."""

from dataclasses import dataclass
from typing import Any, Callable, Optional

from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import iter_color_pieces, path_clear_between
from chess_game.chess.types import Color, LegalMove, PieceType

DANGEROUS_KING_EXTENSION_THRESHOLD = 3


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


def record_selective_extension(context: Any) -> None:
    """Record a bounded selective extension when diagnostics are enabled."""

    if context is None or context.stats is None or context.stats.diagnostics is None:
        return
    context.stats.diagnostics.selective_extensions += 1


def root_stability_adjustment(
    board: Board,
    move: Move,
    child_board: Board,
) -> int:
    """Return a small root-only bonus for urgent threat-reducing moves."""

    moving_piece = board.get_piece(move.start)
    if moving_piece is None:
        return 0
    current_danger = king_danger_index(board, moving_piece.color)
    if current_danger < DANGEROUS_KING_EXTENSION_THRESHOLD:
        return 0
    danger_reduction = current_danger - king_danger_index(child_board, moving_piece.color)
    if danger_reduction <= 0:
        return 0
    signed_bonus = min(2, danger_reduction) * 36
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
    elif current_danger >= DANGEROUS_KING_EXTENSION_THRESHOLD:
        if king_danger_index(child_board, moving_color) < current_danger:
            bonus = 1
    elif not _king_needs_shelter(board, moving_color) and _is_forcing_attack_extension(
        board,
        move,
        child_board,
        moving_piece.kind,
        enemy_color,
    ):
        bonus = 1
    return bonus


def king_danger_index(board: Board, color: Color) -> int:
    """Return a simple attack-pressure score around one king."""

    king_square = board.find_king(color)
    if king_square is None:
        return 0
    king_row = int(king_square.row)
    king_col = int(king_square.col)
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    danger = 0
    if _king_lacks_luft(board, color, king_row):
        danger += 1
    if _is_central_king(king_row, king_col) and _queens_remain(board):
        danger += 1
    for piece, row_index, col_index in iter_color_pieces(board, enemy_color):
        if piece.kind in {PieceType.ROOK, PieceType.QUEEN} and (
            row_index == king_row or col_index == king_col
        ):
            if path_clear_between(board, (row_index, col_index), (king_row, king_col)):
                danger += 2
        distance = max(abs(row_index - king_row), abs(col_index - king_col))
        if piece.kind == PieceType.QUEEN and distance <= 3:
            danger += 2
        if piece.kind == PieceType.ROOK and distance <= 3:
            danger += 1
    return danger


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
        or enemy_danger_after < DANGEROUS_KING_EXTENSION_THRESHOLD
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


def _king_lacks_luft(board: Board, color: Color, king_row: int) -> bool:
    """Return True when the king sits on the home rank without a pawn escape square."""

    luft_row = 5 if color == Color.WHITE else 2
    home_row = 7 if color == Color.WHITE else 0
    if king_row != home_row:
        return False
    return not any(
        piece.kind == PieceType.PAWN and row_index == luft_row
        for piece, row_index, _ in iter_color_pieces(board, color)
    )


def _king_needs_shelter(board: Board, color: Color) -> bool:
    """Return True when the king is still parked in the center on its home rank."""

    king_square = board.find_king(color)
    home_row = 7 if color == Color.WHITE else 0
    return king_square is not None and int(king_square.row) == home_row and int(
        king_square.col
    ) in {3, 4, 5}


def _is_central_king(king_row: int, king_col: int) -> bool:
    """Return True when the king is not tucked near an edge."""

    return king_row in {2, 3, 4, 5} and king_col in {2, 3, 4, 5}


def _queens_remain(board: Board) -> bool:
    """Return True when at least one queen is still on the board."""

    return any(piece.kind == PieceType.QUEEN for row in board.board for piece in row if piece)
