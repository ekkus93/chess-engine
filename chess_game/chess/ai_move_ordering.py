"""Helpers for scoring quiet strategic moves during search ordering."""


from chess_game.chess.ai_check_ordering import (
    _check_quality_bonus,
)
from chess_game.chess.ai_quiet_ordering_constants import (
    QUIET_PROPHYLACTIC_LUFT_BONUS,
    QUIET_WORST_PIECE_BONUS,
)
from chess_game.chess.ai_quiet_scoring import (
    QuietOrderContext,
    _advantage_preservation_penalty,
    _bishop_passive_retreat_penalty,
    _centralization_bonus,
    _defensive_priority_bonus,
    _heavy_piece_bonus,
    _king_move_bonus,
    _knight_threatens_minor_bonus,
    _pawn_bonus,
    _piece_coordination_bonus,
    is_prophylactic_h_luft,
    make_quiet_order_context,
)
from chess_game.chess.ai_repetition_patterns import quiet_cycle_penalty
from chess_game.chess.anti_drift_guidance import anti_drift_order_bonus
from chess_game.chess.board import Board
from chess_game.chess.conversion_guidance import winning_conversion_order_bonus
from chess_game.chess.defensive_containment_guidance import (
    heavy_piece_defense_order_bonus,
)
from chess_game.chess.defensive_endgame_guidance import defensive_endgame_order_bonus
from chess_game.chess.endgame_choice_guidance import endgame_choice_order_bonus
from chess_game.chess.endgame_emergency_defense import endgame_emergency_order_bonus
from chess_game.chess.heavy_piece_endgame_guidance import (
    heavy_piece_endgame_order_bonus,
)
from chess_game.chess.low_material_coordination_guidance import (
    low_material_coordination_order_bonus,
)
from chess_game.chess.low_material_race_guidance import (
    endgame_race_order_bonus,
    low_material_race_order_bonus,
)
from chess_game.chess.middlegame_practicality_guidance import (
    middlegame_practicality_order_bonus,
)
from chess_game.chess.move import Move
from chess_game.chess.opening_move_ordering import (
    opening_discipline_order_score,
)
from chess_game.chess.passer_race_guidance import passer_race_order_bonus
from chess_game.chess.pawn_race_move_ordering import pawn_race_move_bonus
from chess_game.chess.piece_coordination import (
    improves_worst_piece,
)
from chess_game.chess.rook_endgame_guidance import rook_endgame_order_bonus
from chess_game.chess.simple_endgame_guidance import simple_endgame_order_bonus
from chess_game.chess.strategy_utils import (
    is_capture_move,
)
from chess_game.chess.structure_recognition import structure_plan_bonus
from chess_game.chess.tactical_transition_guidance import (
    tactical_transition_order_bonus,
)
from chess_game.chess.threat_awareness import threat_response_order_bonus
from chess_game.chess.types import PieceType

# Public facade: ai_move_ordering re-exports names that moved into
# ai_quiet_ordering_constants / ai_check_ordering, so existing imports of
# chess_game.chess.ai_move_ordering.<name> keep resolving for callers and tests.
__all__ = [
    "QUIET_PROPHYLACTIC_LUFT_BONUS",
    "_bishop_passive_retreat_penalty",
    "_knight_threatens_minor_bonus",
    "is_prophylactic_h_luft",
    "make_quiet_order_context",
    "quiet_strategy_order_score",
]


def quiet_strategy_order_score(
    board: Board,
    move: Move,
    order_context: QuietOrderContext | None = None,
) -> int:
    """Return a bonus for strong quiet strategic moves.

    Placement audit: this file scores only quiet candidates. It intentionally
    avoids capture-ordering and root-only tie-break work so king-danger signals
    are not rewarded the same way in every search stage.
    """

    if move.promotion is not None or is_capture_move(board, move):
        return 0
    piece = board.get_piece(move.start)
    if piece is None:
        return 0
    quiet_context = order_context or make_quiet_order_context(board)
    score = _centralization_bonus(piece.kind, move)
    score += opening_discipline_order_score(board, piece.kind, move)
    score += _defensive_priority_bonus(board, move, quiet_context)
    score += _king_move_bonus(board, piece.kind, move, quiet_context.heavy_piece_endgame)
    score += _heavy_piece_bonus(board, piece.kind, piece.color, move)
    score += _pawn_bonus(board, piece.color, piece.kind, move)
    if quiet_context.endgame_order_position:
        score += endgame_choice_order_bonus(board, piece.color, piece.kind, move)
        score += winning_conversion_order_bonus(board, piece.color, piece.kind, move)
        score += heavy_piece_defense_order_bonus(board, piece.color, piece.kind, move)
        score += heavy_piece_endgame_order_bonus(board, piece.color, piece.kind, move)
        score += simple_endgame_order_bonus(board, piece.color, piece.kind, move)
        score += low_material_coordination_order_bonus(board, piece.color, piece.kind, move)
        score += low_material_race_order_bonus(board, piece.color, piece.kind, move)
        score += endgame_race_order_bonus(board, piece.color, piece.kind, move)
        score += middlegame_practicality_order_bonus(board, piece.color, move)
        score += defensive_endgame_order_bonus(board, piece.color, piece.kind, move)
        score += endgame_emergency_order_bonus(board, piece.color, piece.kind, move)
        score += passer_race_order_bonus(board, piece.color, piece.kind, move)
        score += anti_drift_order_bonus(board, piece.color, piece.kind, move)
        score += pawn_race_move_bonus(board, move, piece.color)
    score += threat_response_order_bonus(board, piece.color, piece.kind, move)
    score += tactical_transition_order_bonus(board, move)
    score += _piece_coordination_bonus(board, piece.color, piece.kind, move)
    score += structure_plan_bonus(board, piece.color, piece.kind, move)
    if quiet_context.endgame_order_position:
        score += rook_endgame_order_bonus(board, piece.color, piece.kind, move)
    score -= quiet_cycle_penalty(board, move, piece.kind)
    if improves_worst_piece(board, move):
        score += QUIET_WORST_PIECE_BONUS
    score += _check_quality_bonus(board, piece.kind, move)
    score -= _advantage_preservation_penalty(board, piece, move, quiet_context)
    if piece.kind == PieceType.BISHOP:
        score -= _bishop_passive_retreat_penalty(board, move, piece.color)
    if piece.kind == PieceType.KNIGHT:
        score += _knight_threatens_minor_bonus(board, move, piece.color)
    return score
