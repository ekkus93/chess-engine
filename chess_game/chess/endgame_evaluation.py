"""Helpers for endgame technique and conversion scoring."""

from chess_game.chess.board import Board
from chess_game.chess.conversion_guidance import winning_conversion_evaluation_score
from chess_game.chess.defensive_endgame_guidance import (
    defensive_endgame_evaluation_score,
)
from chess_game.chess.endgame_evaluation_helpers import (
    _ROOK_SEVENTH_RANK_ENDGAME_BONUS,
    _active_king_score,
    _blockaded_passed_pawn_score,
    _color_sign,
    _counterplay_reduction_score,
    _enemy_king_box_score,
    _has_conversion_assets,
    _has_queen,
    _has_rook,
    _heavy_endgame_king_activity_bonus,
    _heavy_endgame_king_activity_score,
    _heavy_piece_activity_score,
    _king_cutoff_score,
    _king_escort_passed_pawn_score,
    _material_advantage,
    _material_without_kings,
    _mating_material_score,
    _opponent,
    _passed_pawn_advancement_progress,
    _promotion_square_control_score,
    _queen_vs_rook_score,
    _rook_behind_passed_pawn_score,
    _rook_bishop_vs_rook_conversion_bonus,
    _rook_seventh_rank_endgame_score,
    _rook_vs_bishop_king_conversion_bonus,
    _total_non_pawn_material,
)
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.evaluation_tables import (
    STARTING_NON_PAWN_MATERIAL,
)
from chess_game.chess.heavy_piece_endgame_guidance import (
    heavy_piece_endgame_evaluation_score,
)
from chess_game.chess.low_material_coordination_guidance import (
    low_material_coordination_evaluation_score,
)
from chess_game.chess.low_material_race_guidance import (
    endgame_race_evaluation_score,
    low_material_race_evaluation_score,
)
from chess_game.chess.passer_race_guidance import passer_race_evaluation_score
from chess_game.chess.rook_endgame_guidance import rook_endgame_evaluation_score
from chess_game.chess.strategy_utils import (
    iter_board_pieces,
    scale_signed,
)
from chess_game.chess.types import Color, PieceType

# Public facade: the endgame helper layer moved into endgame_evaluation_helpers;
# re-export the names callers/tests import from chess_game.chess.endgame_evaluation.
__all__ = [
    "_ROOK_SEVENTH_RANK_ENDGAME_BONUS",
    "_heavy_endgame_king_activity_bonus",
    "_rook_bishop_vs_rook_conversion_bonus",
    "_rook_seventh_rank_endgame_score",
    "_rook_vs_bishop_king_conversion_bonus",
    "evaluate_conversion",
    "evaluate_endgame_races",
    "evaluate_endgame_technique",
    "evaluate_heavy_piece_endgames",
    "evaluate_low_material_coordination",
    "evaluate_passer_races",
    "evaluate_progress",
    "evaluate_queen_vs_rook",
    "evaluate_rook_endgames",
]


def evaluate_endgame_technique(
    board: Board, endgame_phase: int, weights: EvalWeights | None = None
) -> int:
    """Return endgame-technique bonuses such as king activity and mating method."""

    if endgame_phase == 0:
        return 0
    if weights is None:
        weights = EvalWeights.default()
    score = _active_king_score(board, endgame_phase, weights)
    score += _heavy_endgame_king_activity_score(board, endgame_phase)
    score += _blockaded_passed_pawn_score(board, endgame_phase, weights)
    score += _mating_material_score(board, weights)
    score += scale_signed(defensive_endgame_evaluation_score(board), endgame_phase)
    return score


def evaluate_conversion(
    board: Board, endgame_phase: int, weights: EvalWeights | None = None
) -> int:
    """Return simplification and conversion bonuses when materially ahead."""

    if weights is None:
        weights = EvalWeights.default()
    result = _material_advantage(board)
    if result is None:
        return 0
    lead_value, leading_color = result
    total_non_pawn_material = _total_non_pawn_material(board)
    simplification = max(0, STARTING_NON_PAWN_MATERIAL - total_non_pawn_material)
    bonus = (lead_value * simplification) // (STARTING_NON_PAWN_MATERIAL * 2)
    bonus *= weights.endgame.simplification_bonus_scale
    if not _has_queen(board, _opponent(leading_color)):
        bonus += weights.endgame.queens_off_when_ahead_bonus
    if not _has_rook(board, _opponent(leading_color)):
        bonus += weights.endgame.rooks_off_when_ahead_bonus
    if endgame_phase > 0:
        bonus = (bonus * (50 + endgame_phase)) // 100
    return _color_sign(leading_color) * bonus


def evaluate_progress(
    board: Board, endgame_phase: int, weights: EvalWeights | None = None
) -> int:
    """Return progress and restriction bonuses for practical endgame play."""

    if weights is None:
        weights = EvalWeights.default()
    material_without_kings = _material_without_kings(board)
    lead = material_without_kings[Color.WHITE] - material_without_kings[Color.BLACK]
    if lead == 0:
        return 0
    leading_color = Color.WHITE if lead > 0 else Color.BLACK
    if not _has_conversion_assets(board, leading_color):
        return 0
    bonus = 0
    bonus += _king_cutoff_score(board, leading_color, weights)
    bonus += _rook_behind_passed_pawn_score(board, leading_color, weights)
    bonus += _king_escort_passed_pawn_score(board, leading_color, weights)
    bonus += _promotion_square_control_score(board, leading_color, weights)
    bonus += _enemy_king_box_score(board, leading_color, weights)
    bonus += _counterplay_reduction_score(board, leading_color, weights)
    bonus += _heavy_piece_activity_score(board, leading_color, weights)
    bonus += _heavy_endgame_king_activity_bonus(board, leading_color)
    bonus += _passed_pawn_advancement_progress(board, leading_color)
    bonus += abs(winning_conversion_evaluation_score(board))
    bonus += _rook_vs_bishop_king_conversion_bonus(board, leading_color)
    bonus += _rook_bishop_vs_rook_conversion_bonus(board, leading_color)
    bonus += _rook_seventh_rank_endgame_score(board, leading_color)
    phase_scale = max(40, 40 + endgame_phase)
    return _color_sign(leading_color) * ((bonus * phase_scale) // 100)


def evaluate_rook_endgames(
    board: Board, endgame_phase: int, weights: EvalWeights | None = None
) -> int:
    """Return rook-endgame placement and defense bonuses.

    ``weights`` is accepted for API consistency with the other endgame
    evaluators; it is not yet used by this delegating function.
    """

    if weights is None:
        weights = EvalWeights.default()
    if endgame_phase == 0:
        return 0
    return scale_signed(rook_endgame_evaluation_score(board), endgame_phase)


def evaluate_heavy_piece_endgames(
    board: Board, endgame_phase: int, weights: EvalWeights | None = None
) -> int:
    """Return queen-and-rook ending guidance bonuses.

    ``weights`` is accepted for API consistency with the other endgame
    evaluators; it is not yet used by this delegating function.
    """

    if weights is None:
        weights = EvalWeights.default()
    if endgame_phase == 0:
        return 0
    return scale_signed(heavy_piece_endgame_evaluation_score(board), endgame_phase)


def evaluate_passer_races(
    board: Board, endgame_phase: int, weights: EvalWeights | None = None
) -> int:
    """Return passed-pawn race bonuses.

    ``weights`` is accepted for API consistency with the other endgame
    evaluators; it is not yet used by this delegating function.
    """

    if weights is None:
        weights = EvalWeights.default()
    if endgame_phase < 60:
        return 0
    score = passer_race_evaluation_score(board)
    score += low_material_race_evaluation_score(board)
    return scale_signed(score, endgame_phase)


def evaluate_endgame_races(
    board: Board, endgame_phase: int, weights: EvalWeights | None = None
) -> int:
    """Return exact must-converge and must-hold race bonuses.

    ``weights`` is accepted for API consistency with the other endgame
    evaluators; it is not yet used by this delegating function.
    """

    if weights is None:
        weights = EvalWeights.default()
    if endgame_phase < 40:
        return 0
    return scale_signed(endgame_race_evaluation_score(board), endgame_phase)


def evaluate_low_material_coordination(
    board: Board, endgame_phase: int, weights: EvalWeights | None = None
) -> int:
    """Return piece-specific sparse-endgame coordination bonuses.

    ``weights`` is accepted for API consistency with the other endgame
    evaluators; it is not yet used by this delegating function.
    """

    if weights is None:
        weights = EvalWeights.default()
    if endgame_phase < 60:
        return 0
    return scale_signed(low_material_coordination_evaluation_score(board), endgame_phase)


def evaluate_queen_vs_rook(
    board: Board, endgame_phase: int, weights: EvalWeights | None = None
) -> int:
    """Return a score adjustment for KQvKR positions.

    The queen side is generally winning but needs active king play.
    The rook side needs active rook play to avoid quick mate; passive
    back-rank rook shuffling accelerates the loss.

    ``weights`` is accepted for API consistency; it is not yet used by
    this function.
    """

    if weights is None:
        weights = EvalWeights.default()
    if endgame_phase < 60:
        return 0
    pieces = [
        (piece, row, col)
        for piece, row, col in iter_board_pieces(board)
        if piece.kind not in {PieceType.KING, PieceType.PAWN}
    ]
    kinds = {p.kind for p, _, _ in pieces}
    if kinds != {PieceType.QUEEN, PieceType.ROOK}:
        return 0
    queens = [(p.color, row, col) for p, row, col in pieces if p.kind == PieceType.QUEEN]
    rooks = [(p.color, row, col) for p, row, col in pieces if p.kind == PieceType.ROOK]
    if len(queens) != 1 or len(rooks) != 1:
        return 0
    queen_color = queens[0][0]
    rook_color, rook_row = rooks[0][0], rooks[0][1]
    if queen_color == rook_color:
        return 0
    score = _queen_vs_rook_score(board, queen_color, rook_color, rook_row)
    sign = 1 if queen_color == Color.WHITE else -1
    return scale_signed(sign * score, endgame_phase)
