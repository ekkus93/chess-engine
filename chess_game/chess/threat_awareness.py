"""Shared threat-response heuristics for move ordering and root tie-breaks."""

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.constants import get_square_constant
from chess_game.chess.defensive_priorities import (
    DANGEROUS_KING_PRESSURE_THRESHOLD,
    KingDefenseProfile,
    king_defense_profile,
)
from chess_game.chess.move import Move
from chess_game.chess.opponent_plans import OpponentPlanProfile, opponent_plan_profile
from chess_game.chess.strategy_utils import (
    iter_color_pieces,
    legal_move_count,
    materially_ahead_color,
    non_king_piece_kinds,
    opposite_color,
    passed_pawns_for_color,
)
from chess_game.chess.types import Color, PieceType

_ORDER_PRESSURE_RELIEF_BONUS = 10
_ORDER_CHECK_RELIEF_BONUS = 20
_ORDER_PASSER_RELIEF_BONUS = 24
_ORDER_FLIGHT_BONUS = 22
_ORDER_BACK_RANK_FIX_BONUS = 34
_ORDER_PROMOTION_CONTEST_BONUS = 24
_ORDER_SPECULATIVE_FLANK_PAWN_PENALTY = 34
_ORDER_EMPTY_CHECK_PENALTY = 28

_ROOT_PRESSURE_RELIEF_BONUS = 14
_ROOT_CHECK_RELIEF_BONUS = 28
_ROOT_PASSER_RELIEF_BONUS = 32
_ROOT_FLIGHT_BONUS = 24
_ROOT_BACK_RANK_FIX_BONUS = 42
_ROOT_PROMOTION_CONTEST_BONUS = 32
_ROOT_REPLY_NARROW_BONUS = 3
_ROOT_SIMPLIFICATION_BONUS = 30
_ROOT_EMPTY_CHECK_PENALTY = 36
_HEAVY_MIDDLEGAME_THREAT_THRESHOLD = 9


@dataclass(frozen=True)
class ThreatState:
    """Compact summary of the opponent's current practical threats."""

    plan: OpponentPlanProfile
    defense: KingDefenseProfile
    urgent_enemy_passers: list[tuple[int, int]]


@dataclass(frozen=True)
class ThreatWeights:
    """Scoring weights for one threat-response context."""

    pressure_relief: int
    check_relief: int
    passer_relief: int
    flight_gain: int
    back_rank_fix: int


@dataclass(frozen=True)
class ThreatComparison:
    """Before/after threat state for one candidate move."""

    before: ThreatState
    after: ThreatState
    before_contest: int
    after_contest: int


def threat_response_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for moves that answer urgent enemy threats."""

    if kind not in {PieceType.KING, PieceType.QUEEN, PieceType.ROOK, PieceType.PAWN}:
        return 0
    if kind == PieceType.PAWN and {
        int(move.start.col),
        int(move.end.col),
    }.isdisjoint({0, 2, 6, 7}):
        return 0
    state = _threat_state(board, color)
    if not _should_score_threat_response(board, color, state):
        return 0
    if not _has_direct_threats(state) and kind != PieceType.PAWN:
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    child_state = _threat_state(child_board, color)
    comparison = _threat_comparison(board, child_board, color, state, child_state)
    score = _threat_delta_score(
        comparison,
        ThreatWeights(
            pressure_relief=_ORDER_PRESSURE_RELIEF_BONUS,
            check_relief=_ORDER_CHECK_RELIEF_BONUS,
            passer_relief=_ORDER_PASSER_RELIEF_BONUS,
            flight_gain=_ORDER_FLIGHT_BONUS,
            back_rank_fix=_ORDER_BACK_RANK_FIX_BONUS,
        ),
    )
    score += max(0, comparison.after_contest - comparison.before_contest) * (
        _ORDER_PROMOTION_CONTEST_BONUS
    )
    if _is_speculative_flank_pawn_push(kind, move) and not _is_meaningful_threat_response(
        comparison,
    ):
        score -= _ORDER_SPECULATIVE_FLANK_PAWN_PENALTY
    if _is_harmless_check(child_board, color, comparison):
        score -= _ORDER_EMPTY_CHECK_PENALTY
    return score


def threat_response_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
) -> int:
    """Return a root-only bonus for practical threat responses."""

    moving_kind = _moving_kind(board, move)
    if moving_kind not in {PieceType.KING, PieceType.QUEEN, PieceType.ROOK, PieceType.PAWN}:
        return 0
    state = _threat_state(board, moving_color)
    child_state = _threat_state(child_board, moving_color)
    comparison = _threat_comparison(
        board,
        child_board,
        moving_color,
        state,
        child_state,
    )
    score = 0
    if _should_score_threat_response(board, moving_color, state) and (
        _has_direct_threats(state) or moving_kind == PieceType.PAWN
    ):
        score += _threat_delta_score(
            comparison,
            ThreatWeights(
                pressure_relief=_ROOT_PRESSURE_RELIEF_BONUS,
                check_relief=_ROOT_CHECK_RELIEF_BONUS,
                passer_relief=_ROOT_PASSER_RELIEF_BONUS,
                flight_gain=_ROOT_FLIGHT_BONUS,
                back_rank_fix=_ROOT_BACK_RANK_FIX_BONUS,
            ),
        )
        score += max(0, comparison.after_contest - comparison.before_contest) * (
            _ROOT_PROMOTION_CONTEST_BONUS
        )
        if _is_harmless_check(child_board, moving_color, comparison):
            score -= _ROOT_EMPTY_CHECK_PENALTY
        if _is_meaningful_threat_response(comparison):
            reply_cap = 12
            enemy_color = opposite_color(moving_color)
            score += max(0, reply_cap - legal_move_count(child_board, enemy_color)) * (
                _ROOT_REPLY_NARROW_BONUS
            )
    if _is_speculative_flank_pawn_push(moving_kind, move) and score == 0:
        score -= _ROOT_REPLY_NARROW_BONUS
    score += _simplification_bonus(board, child_board, moving_color)
    return score


def _threat_state(board: Board, color: Color) -> ThreatState:
    enemy_color = opposite_color(color)
    urgent_enemy_passers = [
        pawn
        for pawn in passed_pawns_for_color(board, enemy_color)
        if _is_urgent_enemy_passer(enemy_color, pawn[0])
    ]
    return ThreatState(
        plan=opponent_plan_profile(board, color),
        defense=king_defense_profile(board, color),
        urgent_enemy_passers=urgent_enemy_passers,
    )


def _should_score_threat_response(board: Board, color: Color, state: ThreatState) -> bool:
    urgent = _has_direct_threats(state)
    if not urgent:
        return _has_heavy_middlegame_pressure(board, color, state)
    return not (
        state.urgent_enemy_passers
        and materially_ahead_color(board) == opposite_color(color)
    )


def _has_direct_threats(state: ThreatState) -> bool:
    return (
        bool(state.urgent_enemy_passers)
        or state.defense.danger >= DANGEROUS_KING_PRESSURE_THRESHOLD - 1
        or state.plan.checking_resources > 0
        or state.plan.invasion_lines > 0
    )


def _has_heavy_middlegame_pressure(
    board: Board,
    color: Color,
    state: ThreatState,
) -> bool:
    return (
        _enemy_heavy_count(board, color) > 0
        and len(non_king_piece_kinds(board)) > 5
        and state.plan.pressure >= _HEAVY_MIDDLEGAME_THREAT_THRESHOLD
    )


def _threat_comparison(
    board: Board,
    child_board: Board,
    color: Color,
    before: ThreatState,
    after: ThreatState,
) -> ThreatComparison:
    return ThreatComparison(
        before=before,
        after=after,
        before_contest=_promotion_contest_score(
            board,
            color,
            before.urgent_enemy_passers,
        ),
        after_contest=_promotion_contest_score(
            child_board,
            color,
            before.urgent_enemy_passers,
        ),
    )


def _threat_delta_score(comparison: ThreatComparison, weights: ThreatWeights) -> int:
    score = max(0, comparison.before.plan.pressure - comparison.after.plan.pressure)
    score *= weights.pressure_relief
    score += max(
        0,
        comparison.before.plan.checking_resources - comparison.after.plan.checking_resources,
    ) * weights.check_relief
    score += max(
        0,
        comparison.before.plan.passed_pawn_pushes - comparison.after.plan.passed_pawn_pushes,
    ) * weights.passer_relief
    score += max(
        0,
        comparison.after.defense.safe_king_moves - comparison.before.defense.safe_king_moves,
    ) * weights.flight_gain
    if comparison.before.defense.back_rank_weak and not comparison.after.defense.back_rank_weak:
        score += weights.back_rank_fix
    return score


def _promotion_contest_score(
    board: Board,
    color: Color,
    urgent_enemy_passers: list[tuple[int, int]],
) -> int:
    score = 0
    enemy_color = opposite_color(color)
    for pawn_row, pawn_col in urgent_enemy_passers:
        promotion_row = 7 if enemy_color == Color.BLACK else 0
        next_row = pawn_row + (-1 if enemy_color == Color.WHITE else 1)
        squares = {(promotion_row, pawn_col)}
        if 0 <= next_row < 8:
            squares.add((next_row, pawn_col))
        for row, col in squares:
            occupant = board.board[row][col]
            if occupant is not None and occupant.color == color:
                score += 2
                continue
            if _square_is_controlled_by_color(board, color, row, col):
                score += 1
    return score


def _square_is_controlled_by_color(
    board: Board,
    color: Color,
    row: int,
    col: int,
) -> bool:
    target = get_square_constant(row, col)
    return any(
        piece_attacks_square(piece, piece.square, target, board)
        for piece, _, _ in iter_color_pieces(board, color)
    )


def _is_meaningful_threat_response(comparison: ThreatComparison) -> bool:
    return (
        comparison.after.plan.pressure < comparison.before.plan.pressure
        or comparison.after.plan.checking_resources < comparison.before.plan.checking_resources
        or comparison.after.plan.passed_pawn_pushes < comparison.before.plan.passed_pawn_pushes
        or comparison.after.defense.safe_king_moves > comparison.before.defense.safe_king_moves
        or (
            comparison.before.defense.back_rank_weak
            and not comparison.after.defense.back_rank_weak
        )
        or comparison.after_contest > comparison.before_contest
    )


def _is_speculative_flank_pawn_push(kind: PieceType, move: Move) -> bool:
    return kind == PieceType.PAWN and int(move.start.col) in {0, 7} and int(move.end.col) in {0, 7}


def _is_harmless_check(
    child_board: Board,
    color: Color,
    comparison: ThreatComparison,
) -> bool:
    if not is_in_check(child_board, opposite_color(color)):
        return False
    return not _is_meaningful_threat_response(comparison)


def _simplification_bonus(board: Board, child_board: Board, color: Color) -> int:
    if materially_ahead_color(board) != color:
        return 0
    return max(0, _enemy_heavy_count(board, color) - _enemy_heavy_count(child_board, color)) * (
        _ROOT_SIMPLIFICATION_BONUS
    )


def _enemy_heavy_count(board: Board, color: Color) -> int:
    enemy_color = opposite_color(color)
    return sum(
        1
        for piece, _, _ in iter_color_pieces(board, enemy_color)
        if piece.kind in {PieceType.QUEEN, PieceType.ROOK}
    )


def _is_urgent_enemy_passer(color: Color, row: int) -> bool:
    return row <= 3 if color == Color.WHITE else row >= 4


def _moving_kind(board: Board, move: Move) -> PieceType | None:
    piece = board.get_piece(move.start)
    return None if piece is None else piece.kind
