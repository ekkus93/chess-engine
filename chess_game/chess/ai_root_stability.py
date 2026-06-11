"""Root-stability tie-break bonuses for the AI search.

Extracted from ``ai_search_helpers``. ``root_stability_adjustment`` and its bonus/
penalty helpers nudge near-equal root choices toward stable attack/defense lines;
they pull in the bulk of the guidance modules. ``ai_search_helpers`` re-exports the
public names so existing imports keep working.
"""

from __future__ import annotations

from typing import Any, Callable

from chess_game.chess.ai_board_utils import move_colors
from chess_game.chess.ai_repetition_patterns import (
    move_undoes_last_own_move,
    root_cycle_penalty,
)
from chess_game.chess.anti_drift_guidance import anti_drift_root_bonus
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.conversion_guidance import (
    low_material_conversion_root_bonus, winning_conversion_root_bonus,
)
from chess_game.chess.defensive_containment_guidance import (
    heavy_piece_defense_root_bonus,
)
from chess_game.chess.defensive_endgame_guidance import defensive_endgame_root_bonus
from chess_game.chess.ai_plan_guidance import (
    plan_continuity_bonus,
    practical_options_bonus,
)
from chess_game.chess.heavy_piece_endgame_guidance import heavy_piece_endgame_root_bonus
from chess_game.chess.low_material_race_guidance import low_material_race_root_bonus
from chess_game.chess.low_material_race_guidance import endgame_race_root_bonus
from chess_game.chess.middlegame_practicality_guidance import (
    middlegame_practicality_root_bonus,
)
from chess_game.chess.defensive_priorities import (
    DANGEROUS_KING_PRESSURE_THRESHOLD,
    king_defense_profile,
    king_danger_index,
    king_needs_shelter,
    h_pawn_exposure_penalty as _h_pawn_exposure,
)
from chess_game.chess.move import Move
from chess_game.chess.opening_move_ordering import (
    opening_discipline_order_score,
    undeveloped_minor_count,
    _is_castled_shelter_pawn_advance,
    _is_late_castling_move,
)
from chess_game.chess.opening_development import (
    middlegame_rim_knight_penalty as _rim_knight_penalty,
)
from chess_game.chess.opening_guidance import opening_guidance_bonus
from chess_game.chess.ai_move_ordering import (
    is_prophylactic_h_luft as _is_prophylactic_h_luft,
)
from chess_game.chess.passer_race_guidance import (
    passer_race_root_bonus,
)
from chess_game.chess.pawn_structure_evaluation import evaluate_pawn_structure
from chess_game.chess.review_loop_guidance import review_loop_root_bonus
from chess_game.chess.endgame_choice_guidance import (
    endgame_choice_king_activity_root_bonus, endgame_choice_root_bonus,
)
from chess_game.chess.endgame_emergency_defense import (
    endgame_emergency_root_bonus,
)
from chess_game.chess.low_material_coordination_guidance import low_material_coordination_root_bonus
from chess_game.chess.simple_endgame_guidance import simple_endgame_root_bonus
from chess_game.chess.threat_awareness import threat_response_root_bonus
from chess_game.chess.tactical_transition_guidance import tactical_transition_root_bonus
from chess_game.chess.forced_win_guidance import forced_win_root_bonus
from chess_game.chess.strategy_utils import (
    is_capture_move,
    non_king_material_lead,
    non_king_piece_kinds,
    passed_pawns_for_color,
    total_non_pawn_material,
)
from chess_game.chess.types import Color, PieceType
from chess_game.chess.evaluation_tables import MATERIAL_VALUES, STARTING_NON_PAWN_MATERIAL
from chess_game.chess.ai_repetition_tracking import (
    position_occurrence_count,
)

_PAWN_STRUCTURE_CHANGE_ROOT_BONUS, _OPENING_CENTRAL_PAWN_ROOT_BONUS = 18, 14
_MOVE1_CENTRAL_PAWN_BONUS = 320
# Capped just under the root tie-break margin: a concrete material capture dominates
# the speculative attack/strategic root nudges at (near-)equal search scores, but
# still cannot override a score difference the search judged larger than the tie
# band.
_MATERIAL_REALIZATION_CAP = 49


def _material_realization_bonus(board: Board, move: Move) -> int:
    """Mover-relative root tie-break nudge toward realizing material immediately.

    Among root moves the search scores equally, prefer the one that captures
    material now (a concrete gain) over deferring it to a later ply. Scaled by
    captured value and capped at _MATERIAL_REALIZATION_CAP so a real capture
    outranks the speculative attack/strategic nudges without overriding score
    differences the search judged larger than the tie band.
    """
    captured = board.get_piece(move.end)
    if captured is None:
        return 0
    return min(MATERIAL_VALUES[captured.kind] // 10, _MATERIAL_REALIZATION_CAP)

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
    colors = move_colors(board, move)
    if colors is None:
        return 0
    moving_color, enemy_color = colors
    signed_bonus = _defensive_root_bonus(board, child_board, moving_color)
    signed_bonus += _attacking_root_bonus(
        board,
        move,
        child_board,
        moving_color,
        enemy_color,
    )
    signed_bonus += _strategic_root_bonus(
        board,
        move,
        child_board,
        moving_piece.kind,
        moving_color,
    )
    signed_bonus += _material_realization_bonus(board, move)
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
    score -= max(0, before.safe_king_moves - after.safe_king_moves) * 24
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
    score += invasion_gain * 22
    if (
        is_in_check(child_board, enemy_color)
        and after.danger >= DANGEROUS_KING_PRESSURE_THRESHOLD
        and (danger_gain > 0 or invasion_gain > 0)
    ):
        score += 14
    if is_capture_move(board, move):
        score += 10
    return score

def _strategic_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    moving_kind: PieceType,
    moving_color: Color,
) -> int:
    score = heavy_piece_endgame_root_bonus(board, move, child_board, moving_color)
    score += endgame_choice_root_bonus(board, move, child_board, moving_color)
    score += low_material_coordination_root_bonus(board, move, child_board, moving_color)
    score += low_material_race_root_bonus(board, move, child_board, moving_color)
    score += passer_race_root_bonus(board, move, child_board, moving_color)
    score += anti_drift_root_bonus(board, move, child_board, moving_color)
    score += simple_endgame_root_bonus(board, move, child_board, moving_color)
    score += defensive_endgame_root_bonus(board, move, child_board, moving_color)
    score += low_material_conversion_root_bonus(board, move, child_board, moving_color)
    score += forced_win_root_bonus(board, move, child_board, moving_color)
    score += review_loop_root_bonus(board, child_board, moving_color)
    score += endgame_choice_king_activity_root_bonus(board, child_board, moving_color)
    score += endgame_emergency_root_bonus(board, move, child_board, moving_color)
    if king_danger_index(board, moving_color) >= DANGEROUS_KING_PRESSURE_THRESHOLD:
        return score + _high_danger_root_bonus(board, move, child_board, moving_color)
    if _is_simple_endgame(board):
        return score
    score += _pawn_structure_change_root_bonus(board, move, moving_color)
    score += _pawn_structure_root_bonus(board, move, child_board)
    score += practical_options_bonus(board, child_board, moving_color)
    score += _opening_root_bonus(board, move, moving_kind)
    score += heavy_piece_defense_root_bonus(board, child_board, moving_color)
    score += winning_conversion_root_bonus(board, move, child_board, moving_color)
    score += threat_response_root_bonus(board, move, child_board, moving_color)
    score += tactical_transition_root_bonus(board, move, child_board, moving_color)
    score += endgame_race_root_bonus(board, move, child_board, moving_color)
    score += middlegame_practicality_root_bonus(board, move, child_board, moving_color)
    score -= _rim_knight_root_penalty(child_board, moving_color)
    score -= _shelter_pawn_advance_root_penalty(board, move, moving_kind, moving_color)
    score += _late_castling_root_bonus(board, move, moving_kind, moving_color)
    score += _h_pawn_luft_root_bonus(board, move, moving_kind, moving_color)
    score -= _ignore_near_promotion_passer_penalty(board, move, moving_kind, moving_color)
    score += plan_continuity_bonus(
        board,
        move,
        child_board,
        moving_kind,
        moving_color,
    )
    return score

def _pawn_structure_change_root_bonus(
    board: Board,
    move: Move,
    moving_color: Color,
) -> int:
    if non_king_material_lead(board, moving_color) < MATERIAL_VALUES[PieceType.ROOK]:
        return 0
    moving_piece = board.get_piece(move.start)
    if moving_piece is not None and moving_piece.kind == PieceType.PAWN:
        own_passers = passed_pawns_for_color(board, moving_color)
        start_square = (int(move.start.row), int(move.start.col))
        if start_square in own_passers:
            return _PAWN_STRUCTURE_CHANGE_ROOT_BONUS
        return _PAWN_STRUCTURE_CHANGE_ROOT_BONUS // 2
    if is_capture_move(board, move):
        return _PAWN_STRUCTURE_CHANGE_ROOT_BONUS
    return 0

def _rim_knight_root_penalty(child_board: Board, moving_color: Color) -> int:
    """Root penalty for lines that leave a friendly knight on the rim with queens on board."""

    if _is_simple_endgame(child_board):
        return 0
    return _rim_knight_penalty(child_board, moving_color)

def _shelter_pawn_advance_root_penalty(
    board: Board,
    move: Move,
    moving_kind: PieceType,
    moving_color: Color,
) -> int:
    """Root penalty for castled-shelter pawn advances while the opponent has a queen."""

    if moving_kind != PieceType.PAWN:
        return 0
    if _is_simple_endgame(board):
        return 0
    if not _is_castled_shelter_pawn_advance(board, move):
        return 0
    _ = moving_color
    return 24

def _ignore_near_promotion_passer_penalty(
    board: Board,
    move: Move,
    moving_kind: PieceType,
    moving_color: Color,
) -> int:
    """Root penalty for ignoring an enemy passer within 2 squares of promotion."""

    if not _is_simple_endgame(board):
        return 0
    enemy_color = Color.BLACK if moving_color == Color.WHITE else Color.WHITE
    has_critical = any(
        _promotion_progress_raw(enemy_color, pawn[0]) >= 4
        for pawn in passed_pawns_for_color(board, enemy_color)
    )
    responds = has_critical and (
        is_capture_move(board, move) or moving_kind == PieceType.PAWN
    )
    return 0 if not has_critical or responds else 24

def _promotion_progress_raw(color: Color, row: int) -> int:
    return 6 - row if color == Color.WHITE else row - 1

def _h_pawn_luft_root_bonus(
    board: Board,
    move: Move,
    moving_kind: PieceType,
    moving_color: Color,
) -> int:
    """Root bonus for h-pawn luft moves — reactive (bishop threat) or prophylactic."""

    home_row = 6 if moving_color == Color.WHITE else 1
    is_h_luft = (
        moving_kind == PieceType.PAWN
        and not _is_simple_endgame(board)
        and int(move.start.row) == home_row
        and int(move.start.col) == 7
        and abs(int(move.end.row) - int(move.start.row)) == 1
    )
    if not is_h_luft:
        return 0
    if _h_pawn_exposure(board, moving_color) >= 15:
        return 36
    return 28 if _is_prophylactic_h_luft(board, moving_color) else 0

def _late_castling_root_bonus(
    board: Board,
    move: Move,
    moving_kind: PieceType,
    moving_color: Color,
) -> int:
    """Root-only bonus for castling moves when the king has been uncastled past move 10.

    Compensates for the search horizon: even when evaluation penalises the uncastled
    king, the root tiebreak needs an explicit nudge to prefer castling over near-equal
    tactical alternatives.
    """

    if moving_kind != PieceType.KING:
        return 0
    if _is_simple_endgame(board):
        return 0
    if not _is_late_castling_move(board, move):
        return 0
    _ = moving_color
    return 40

def _opening_root_bonus(board: Board, move: Move, moving_kind: PieceType) -> int:
    """Return a root-only tiebreak bonus for better opening discipline."""

    if is_capture_move(board, move):
        return 0
    if len(non_king_piece_kinds(board)) <= 10:
        return 0
    score = opening_discipline_order_score(board, moving_kind, move) * 4
    score += _opening_central_pawn_root_bonus(board, move, moving_kind)
    return score

def _opening_central_pawn_root_bonus(
    board: Board,
    move: Move,
    moving_kind: PieceType,
) -> int:
    if moving_kind != PieceType.PAWN:
        return 0
    if int(move.start.col) not in {3, 4} or int(move.end.col) not in {3, 4}:
        return 0
    if opening_guidance_bonus(board, board.turn, moving_kind, move) == 0:
        return 0
    if undeveloped_minor_count(board) == 4:
        return _MOVE1_CENTRAL_PAWN_BONUS
    return _OPENING_CENTRAL_PAWN_ROOT_BONUS

def _high_danger_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
) -> int:
    """Keep defense-first tie-breaks active when the moving king is under pressure."""

    score = heavy_piece_defense_root_bonus(board, child_board, moving_color)
    score += threat_response_root_bonus(board, move, child_board, moving_color)
    score += tactical_transition_root_bonus(board, move, child_board, moving_color)
    return score

def _pawn_structure_root_bonus(board: Board, move: Move, child_board: Board) -> int:
    moving_piece = board.get_piece(move.start)
    if moving_piece is None or moving_piece.kind != PieceType.PAWN:
        return 0
    if undeveloped_minor_count(board) == 4:
        return 0
    endgame_phase = _endgame_phase(board)
    before = evaluate_pawn_structure(board, endgame_phase)
    after = evaluate_pawn_structure(child_board, endgame_phase)
    delta = after - before
    if delta == 0:
        return 0
    return delta * 8

def _endgame_phase(board: Board) -> int:
    non_pawn_material = total_non_pawn_material(board)
    middlegame_phase = min((non_pawn_material * 100) // STARTING_NON_PAWN_MATERIAL, 100)
    return 100 - middlegame_phase

def _is_simple_endgame(board: Board) -> bool:
    non_king_pieces = [
        piece
        for row in board.board
        for piece in row
        if piece is not None and piece.kind != PieceType.KING
    ]
    return len(non_king_pieces) <= 4

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
    moving_piece = board.get_piece(move.start)
    if moving_piece is None:
        return 0
    moving_color = moving_piece.color
    enemy_color = Color.BLACK if moving_color == Color.WHITE else Color.WHITE
    has_tactical_payoff = _has_genuine_tactical_payoff(
        board,
        move,
        child_board,
        moving_color,
        enemy_color,
    )
    penalty = root_cycle_penalty(
        board,
        move,
        moving_piece.kind,
        occurrence_count,
        _is_simple_endgame(board),
    )
    repeated_position_penalty = 48 * occurrence_count if occurrence_count > 0 else 0
    if has_tactical_payoff:
        return 0
    if penalty > 0:
        return penalty
    return repeated_position_penalty

def _has_genuine_tactical_payoff(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
    enemy_color: Color,
) -> bool:
    """Return True when a repeated tactical line still improves attack or defense."""

    if move_undoes_last_own_move(board, move) and not is_capture_move(board, move):
        return False
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
