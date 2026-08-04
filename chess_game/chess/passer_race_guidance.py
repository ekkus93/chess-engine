"""Shared guidance for passed-pawn races and promotion urgency."""

from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.passer_race_helpers import (
    _ACTIVE_ENEMY_HEAVY_PENALTY,
    _ALLOWED_RACE_KINDS,
    _BLOCKADE_PENALTY,
    _CHECK_DISRUPTION_PENALTY,
    _CHECKMATE_RESOLUTION_BONUS,
    _CLEAR_PATH_BONUS,
    _CONNECTED_PASSER_BONUS,
    _COSMETIC_CHECK_PENALTY,
    _CRITICAL_ZONE_BONUS,
    _DIRECT_PUSH_BONUS,
    _ENEMY_PASSER_DANGER_BONUS,
    _ESCORT_BONUS,
    _EVAL_SCALE,
    _EXPLICIT_TEMPO_MARGIN_BONUS,
    _HEAVY_SUPPORT_BONUS,
    _HIGH_PRIORITY_PUSH_BONUS,
    _KING_SUPPORT_BONUS,
    _LOSING_SIDE_BAD_RACE_PENALTY,
    _LOSING_SIDE_IRRELEVANT_ACTIVITY_PENALTY,
    _MAX_NON_KING_PIECES,
    _ORDER_SCALE,
    _OUTSIDE_PASSER_BONUS,
    _PASSER_PROGRESS_BONUS,
    _PROMOTION_RESOLUTION_BONUS,
    _PROMOTION_SQUARE_PENALTY,
    _PROTECTED_PASSER_BONUS,
    _RACE_TEMPO_BONUS,
    _ROOT_SCALE,
    _STALEMATE_RESOLUTION_PENALTY,
    _TIED_DOWN_DEFENDER_BONUS,
    _UNSTOPPABLE_PASSER_BONUS,
    _defender_escape_bonus,
    _explicit_pawn_race_tempo,
    _has_relevant_race_targets,
    _high_priority_push_bonus,
    _is_near_promotion_passer_push,
    _is_pawn_race_tempo_position,
    _is_relevant_passer_race,
    _is_relevant_passer_race_evaluation,
    _losing_side_bad_race_penalty,
    _losing_side_urgent_defense_penalty,
    _move_checks_opponent,
    _move_directly_stops_enemy_near_promotion_pawn,
    _passer_race_side_score,
    _passes_material_gate,
    _relative_race_score,
)
from chess_game.chess.types import Color, PieceType

# Public facade: helper layer moved to passer_race_helpers; re-export the names
# callers/tests import from chess_game.chess.passer_race_guidance.
__all__ = [
    "_ACTIVE_ENEMY_HEAVY_PENALTY",
    "_ALLOWED_RACE_KINDS",
    "_BLOCKADE_PENALTY",
    "_CHECKMATE_RESOLUTION_BONUS",
    "_CHECK_DISRUPTION_PENALTY",
    "_CLEAR_PATH_BONUS",
    "_CONNECTED_PASSER_BONUS",
    "_COSMETIC_CHECK_PENALTY",
    "_CRITICAL_ZONE_BONUS",
    "_DIRECT_PUSH_BONUS",
    "_ENEMY_PASSER_DANGER_BONUS",
    "_ESCORT_BONUS",
    "_EVAL_SCALE",
    "_EXPLICIT_TEMPO_MARGIN_BONUS",
    "_HEAVY_SUPPORT_BONUS",
    "_HIGH_PRIORITY_PUSH_BONUS",
    "_KING_SUPPORT_BONUS",
    "_LOSING_SIDE_BAD_RACE_PENALTY",
    "_LOSING_SIDE_IRRELEVANT_ACTIVITY_PENALTY",
    "_MAX_NON_KING_PIECES",
    "_ORDER_SCALE",
    "_OUTSIDE_PASSER_BONUS",
    "_PASSER_PROGRESS_BONUS",
    "_PROMOTION_RESOLUTION_BONUS",
    "_PROMOTION_SQUARE_PENALTY",
    "_PROTECTED_PASSER_BONUS",
    "_RACE_TEMPO_BONUS",
    "_ROOT_SCALE",
    "_STALEMATE_RESOLUTION_PENALTY",
    "_TIED_DOWN_DEFENDER_BONUS",
    "_UNSTOPPABLE_PASSER_BONUS",
    "_passes_material_gate",
    "explicit_pawn_race_tempo",
    "is_pawn_race_tempo_position",
    "passer_race_evaluation_score",
    "passer_race_extension_bonus",
    "passer_race_order_bonus",
    "passer_race_root_bonus",
]


def passer_race_evaluation_score(board: Board) -> int:
    """Return a signed score for passed-pawn urgency in simple endgames."""

    if not _is_relevant_passer_race_evaluation(board):
        return 0
    return (
        _passer_race_side_score(board, Color.WHITE)
        - _passer_race_side_score(board, Color.BLACK)
    ) * _EVAL_SCALE


def explicit_pawn_race_tempo(board: Board) -> tuple[int | None, int | None]:
    """Return side-to-move-adjusted promotion tempos for white and black."""

    return _explicit_pawn_race_tempo(board)


def is_pawn_race_tempo_position(board: Board) -> bool:
    """Return True for pawn-only races where tempo calculation is decisive."""

    return _is_pawn_race_tempo_position(board)


def passer_race_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for clearer passed-pawn race play."""

    if kind not in {PieceType.KING, PieceType.ROOK, PieceType.QUEEN, PieceType.PAWN}:
        return 0
    if not _is_relevant_passer_race(board):
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    before = _passer_race_side_score(board, color)
    after = _passer_race_side_score(child_board, color)
    bonus = (after - before) * _ORDER_SCALE
    if kind == PieceType.PAWN and after > before:
        bonus += _DIRECT_PUSH_BONUS
        bonus += _high_priority_push_bonus(child_board, color, move)
    if kind == PieceType.KING and after > before:
        bonus += _ESCORT_BONUS
    if (
        kind in {PieceType.ROOK, PieceType.QUEEN}
        and _move_checks_opponent(child_board, color)
        and after <= before
        and _has_relevant_race_targets(board, color)
    ):
        bonus -= _COSMETIC_CHECK_PENALTY
    bonus += _defender_escape_bonus(child_board, color)
    bonus -= _losing_side_urgent_defense_penalty(board, child_board, color, move)
    bonus -= _losing_side_bad_race_penalty(board, color, kind, move)
    return bonus


def passer_race_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return a root-only bonus for clearer passed-pawn race choices."""

    if not _is_relevant_passer_race(board):
        return 0
    piece = board.get_piece(move.start)
    if move.promotion is not None and piece is not None and piece.kind == PieceType.PAWN:
        return _PROMOTION_RESOLUTION_BONUS
    before = _relative_race_score(board, color)
    after = _relative_race_score(child_board, color)
    bonus = (after - before) * _ROOT_SCALE
    if (
        piece is not None
        and piece.kind in {PieceType.ROOK, PieceType.QUEEN}
        and _move_checks_opponent(child_board, color)
        and after <= before
        and _has_relevant_race_targets(board, color)
    ):
        bonus -= _COSMETIC_CHECK_PENALTY
    bonus += _defender_escape_bonus(child_board, color)
    bonus -= _losing_side_urgent_defense_penalty(board, child_board, color, move)
    if piece is not None:
        bonus -= _losing_side_bad_race_penalty(board, color, piece.kind, move)
    return bonus


def passer_race_extension_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
) -> int:
    """Return 1 when a move deserves a narrow passer-race extension."""

    if not _is_relevant_passer_race(board):
        return 0
    if _is_near_promotion_passer_push(board, move, moving_color):
        return 1
    if _move_directly_stops_enemy_near_promotion_pawn(board, move, child_board, moving_color):
        return 1
    return 0
