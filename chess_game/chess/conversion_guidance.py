"""Shared guidance for converting materially winning endgames."""


from chess_game.chess.board import Board
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.conversion_guidance_constants import (
    _ANTI_QUEEN_TRADE_MIN_LEAD,
    _ANTI_QUEEN_TRADE_PENALTY,
    _BETTER_SIDE_PLAN_SWITCH_PENALTY,
    _CHECK_DRIFT_PENALTY,
    _EVAL_SCALE,
    _KING_ACTIVATION_BONUS,
    _MAIN_PASSER_ROOT_BONUS,
    _MIN_HEAVY_CONVERSION_LEAD,
    _ORDER_SCALE,
    _PASSER_ADVANCE_BONUS,
    _ROOT_SCALE,
)
from chess_game.chess.conversion_scoring import (
    ConversionContext,
    ConversionSideState,
    LowMaterialMovePlan,
    _can_have_conversion_shape,
    _color_sign,
    _conversion_distance_pressure_score,
    _conversion_paused_for_king_danger,
    _counterplay_suppression_score,
    _enemy_passer_suppression_score,
    _has_meaningful_counterplay,
    _heavy_piece_positions,
    _is_heavy_conversion_battle,
    _is_low_material_conversion_endgame,
    _is_simple_conversion_endgame,
    _king_activation_score,
    _king_cutoff_score,
    _leading_color,
    _low_material_conversion_score,
    _low_material_move_bonus,
    _main_passer,
    _material_lead,
    _minor_conversion_support_score,
    _move_checks_opponent,
    _opponent,
    _passer_support_score,
    _promotion_distance,
    _promotion_lane_support_score,
    _seventh_rank_pressure_score,
    _trade_quality_score,
    _trivial_conversion_transition_bonus,
)
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    is_capture_move,
    iter_color_pieces,
    passed_pawns_for_color,
)
from chess_game.chess.types import Color, PieceType

# Public facade: conversion_guidance re-exports names that moved into
# conversion_guidance_constants / conversion_scoring, so existing imports of
# chess_game.chess.conversion_guidance.<name> keep resolving for callers and tests.
__all__ = [
    "_anti_queen_trade_root_penalty",
    "_better_side_plan_switch_penalty",
    "_conversion_context",
    "_passer_advance_bonus",
    "low_material_conversion_root_bonus",
    "winning_conversion_evaluation_score",
    "winning_conversion_order_bonus",
    "winning_conversion_root_bonus",
]


def winning_conversion_evaluation_score(board: Board) -> int:
    """Return a signed score for materially winning conversion geometry."""

    if not _can_have_conversion_shape(board):
        return 0
    context = _conversion_context(board)
    if context is None:
        return 0
    if _conversion_paused_for_king_danger(board, context):
        return 0
    return _color_sign(context.color) * _conversion_side_score(board, context) * _EVAL_SCALE


def winning_conversion_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for clearer winning conversion plans."""

    if kind not in {
        PieceType.KING,
        PieceType.QUEEN,
        PieceType.ROOK,
        PieceType.BISHOP,
        PieceType.PAWN,
    }:
        return 0
    if not _can_have_conversion_shape(board):
        return 0
    context = _conversion_context(board)
    if (
        context is None
        or color != context.color
        or _conversion_paused_for_king_danger(board, context)
    ):
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    child_context = _conversion_context(child_board)
    if child_context is None:
        return 0
    before = _conversion_side_score(board, context)
    after = _conversion_side_score(child_board, child_context)
    pressure_before = _conversion_distance_pressure_score(board, context)
    pressure_after = _conversion_distance_pressure_score(child_board, child_context)
    bonus = (after - before) * _ORDER_SCALE
    bonus += (pressure_after - pressure_before) * (_ORDER_SCALE // 2)
    if kind == PieceType.KING and after > before:
        bonus += _KING_ACTIVATION_BONUS
    bonus += _low_material_move_bonus(
        LowMaterialMovePlan(
            board=board,
            move=move,
            child_board=child_board,
            context=context,
            child_context=child_context,
        ),
        kind,
        scale=1,
    )
    bonus += _passer_advance_bonus(board, move, context)
    if kind in {PieceType.ROOK, PieceType.QUEEN} and _move_checks_opponent(child_board, color):
        if after <= before:
            bonus -= _CHECK_DRIFT_PENALTY
    return bonus


def _passer_advance_bonus(
    board: Board,
    move: Move,
    context: ConversionContext,
) -> int:
    if context.main_passer is None:
        return 0
    if not context.own.heavy and not context.enemy.heavy:
        return 0
    piece = board.get_piece(move.start)
    if piece is None or piece.kind != PieceType.PAWN:
        return 0
    start_square = (int(move.start.row), int(move.start.col))
    if start_square != context.main_passer:
        return 0
    return _PASSER_ADVANCE_BONUS


def winning_conversion_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return a root-only bonus for cleaner winning conversion choices."""

    return _conversion_root_bonus(
        board,
        move,
        child_board,
        color,
        low_material_only=False,
    )


def low_material_conversion_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return a root-only bonus for low-material conversion choices."""

    return _conversion_root_bonus(
        board,
        move,
        child_board,
        color,
        low_material_only=True,
    )


def _conversion_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
    low_material_only: bool,
) -> int:
    if not _can_have_conversion_shape(board):
        return 0
    context = _conversion_context(board)
    child_context = _conversion_context(child_board)
    if (
        context is None
        or child_context is None
        or color != context.color
        or _conversion_paused_for_king_danger(board, context)
    ):
        return 0
    if low_material_only and not context.is_low_material_conversion:
        return 0
    before = _conversion_side_score(board, context)
    after = _conversion_side_score(child_board, child_context)
    pressure_before = _conversion_distance_pressure_score(board, context)
    pressure_after = _conversion_distance_pressure_score(child_board, child_context)
    bonus = (after - before) * _ROOT_SCALE
    bonus += (pressure_after - pressure_before) * (_ROOT_SCALE // 2)
    piece = board.get_piece(move.start)
    if piece is None:
        return bonus
    bonus += _main_passer_root_bonus(board, move, piece.kind, context)
    bonus -= _better_side_plan_switch_penalty(board, piece.kind, move, context)
    bonus -= _anti_queen_trade_root_penalty(board, move, piece.kind, context.color)
    bonus += _trivial_conversion_transition_bonus(
        board,
        child_board,
        context,
        child_context,
    )
    return bonus + _low_material_move_bonus(
        LowMaterialMovePlan(
            board=board,
            move=move,
            child_board=child_board,
            context=context,
            child_context=child_context,
        ),
        piece.kind,
        scale=2,
    )


def _anti_queen_trade_root_penalty(
    board: Board,
    move: Move,
    kind: PieceType,
    color: Color,
) -> int:
    """Penalize queen moves to squares attacked by enemy pieces when clearly ahead."""
    if kind != PieceType.QUEEN:
        return 0
    if is_capture_move(board, move):
        return 0
    if _material_lead(board, color) < _ANTI_QUEEN_TRADE_MIN_LEAD:
        return 0
    enemy_color = _opponent(color)
    for enemy_piece, _, _ in iter_color_pieces(board, enemy_color):
        if piece_attacks_square(enemy_piece, enemy_piece.square, move.end, board):
            return _ANTI_QUEEN_TRADE_PENALTY
    return 0


def _main_passer_root_bonus(
    board: Board,
    move: Move,
    kind: PieceType,
    context: ConversionContext,
) -> int:
    if context.main_passer is None or kind != PieceType.PAWN:
        return 0
    if (int(move.start.row), int(move.start.col)) != context.main_passer:
        return 0
    start_distance = _promotion_distance(context.color, int(move.start.row))
    end_distance = _promotion_distance(context.color, int(move.end.row))
    if end_distance >= start_distance:
        return 0
    if board.get_piece(move.start) is None:
        return 0
    return _MAIN_PASSER_ROOT_BONUS + (start_distance - end_distance) * 8


def _better_side_plan_switch_penalty(
    board: Board,
    kind: PieceType,
    move: Move,
    context: ConversionContext,
) -> int:
    if context.main_passer is None or kind not in {
        PieceType.BISHOP,
        PieceType.ROOK,
        PieceType.QUEEN,
    }:
        return 0
    if _material_lead(board, context.color) < _MIN_HEAVY_CONVERSION_LEAD:
        return 0
    start_distance = abs(int(move.start.col) - context.main_passer[1])
    end_distance = abs(int(move.end.col) - context.main_passer[1])
    return _BETTER_SIDE_PLAN_SWITCH_PENALTY if end_distance > start_distance else 0


def _conversion_side_score(board: Board, context: ConversionContext) -> int:
    score = 0
    score += _king_activation_score(context)
    score += _passer_support_score(board, context)
    score += _trade_quality_score(board, context)
    score += _promotion_lane_support_score(board, context)
    score += _minor_conversion_support_score(board, context)
    score += _counterplay_suppression_score(board, context)
    score += _enemy_passer_suppression_score(context)
    score += _king_cutoff_score(context)
    score += _seventh_rank_pressure_score(context)
    if context.is_low_material_conversion:
        score += _low_material_conversion_score(board, context)
    return score


def _conversion_context(board: Board) -> ConversionContext | None:
    color = _leading_color(board)
    if color is None:
        return None
    enemy_color = _opponent(color)
    own_king = board.find_king(color)
    enemy_king = board.find_king(enemy_color)
    if own_king is None or enemy_king is None:
        return None
    own_passers = passed_pawns_for_color(board, color)
    enemy_passers = passed_pawns_for_color(board, enemy_color)
    own_heavy = _heavy_piece_positions(board, color)
    enemy_heavy = _heavy_piece_positions(board, enemy_color)
    enemy_king_coords = (int(enemy_king.row), int(enemy_king.col))
    main_passer = _main_passer(color, own_passers, enemy_king_coords)
    is_heavy_conversion = _is_heavy_conversion_battle(
        board,
        color,
        main_passer,
        own_heavy,
        enemy_heavy,
    )
    is_low_material_conversion = _is_low_material_conversion_endgame(
        board,
        color,
        main_passer,
        enemy_heavy,
    )
    if not (
        _is_simple_conversion_endgame(board)
        or is_heavy_conversion
        or is_low_material_conversion
    ):
        return None
    if not (
        _has_meaningful_counterplay(enemy_heavy, enemy_passers)
        or is_low_material_conversion
    ):
        return None
    return ConversionContext(
        color=color,
        own=ConversionSideState(
            color=color,
            king=(int(own_king.row), int(own_king.col)),
            passers=own_passers,
            heavy=own_heavy,
        ),
        enemy=ConversionSideState(
            color=enemy_color,
            king=(int(enemy_king.row), int(enemy_king.col)),
            passers=enemy_passers,
            heavy=enemy_heavy,
        ),
        main_passer=main_passer,
        is_heavy_conversion=is_heavy_conversion,
        is_low_material_conversion=is_low_material_conversion,
    )
