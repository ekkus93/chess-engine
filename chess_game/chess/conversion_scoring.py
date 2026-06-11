"""Conversion scoring layer: context types + the helper functions below the entry API.

Extracted from ``conversion_guidance``. Holds the ConversionContext/ConversionSideState/
LowMaterialMovePlan dataclasses plus the endgame-shape predicates, per-aspect scoring
helpers, geometry utilities and low-material move logic. This is the cycle-free layer
below the public entry points, so it never calls back into ``conversion_guidance``;
``conversion_guidance`` (the thin entry/hub layer) re-imports the names it uses.
"""

from __future__ import annotations

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.constants import get_square_constant
from chess_game.chess.defensive_priorities import (
    DANGEROUS_KING_PRESSURE_THRESHOLD,
    king_danger_index,
)
from chess_game.chess.evaluation_tables import MATERIAL_VALUES
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    heavy_piece_file_support_rows,
    is_advanced_passer,
    iter_color_pieces,
    materially_ahead_color,
    non_king_piece_count_at_most,
    non_king_piece_kinds,
    opposite_color,
)
from chess_game.chess.types import Color, PieceType

from chess_game.chess.conversion_guidance_constants import (
    _CONVERSION_DISTANCE_PRESSURE_BONUS,
    _COUNTERPLAY_LINE_PENALTY,
    _COUNTERPLAY_SUPPRESSION_BONUS,
    _ENEMY_PASSER_SUPPRESSION_BONUS,
    _HEAVY_SIDE_DRIFT_PENALTY,
    _KING_ACTIVATION_BONUS,
    _KING_CUTOFF_BONUS,
    _LOW_MATERIAL_CUTOFF_BONUS,
    _LOW_MATERIAL_KING_LEAD_BONUS,
    _LOW_MATERIAL_MAIN_PASSER_BONUS,
    _LOW_MATERIAL_MISSED_PROMOTION_PENALTY,
    _LOW_MATERIAL_PREMATURE_PUSH_PENALTY,
    _LOW_MATERIAL_PROMOTION_BONUS,
    _LOW_MATERIAL_SIDE_PAWN_PENALTY,
    _LOW_MATERIAL_TRADE_BONUS,
    _MAX_HEAVY_CONVERSION_NON_KING_PIECES,
    _MAX_NON_KING_PIECES,
    _MIN_HEAVY_CONVERSION_LEAD,
    _MINOR_EDGE_DRIFT_PENALTY,
    _MINOR_LANE_SUPPORT_BONUS,
    _PASSER_SUPPORT_BONUS,
    _PROMOTION_LANE_SUPPORT_BONUS,
    _PROMOTION_SQUARE_SUPPORT_BONUS,
    _SEVENTH_RANK_PRESSURE_BONUS,
    _TRADE_QUALITY_BONUS,
    _TRIVIAL_CONVERSION_TRANSITION_BONUS,
)


@dataclass(frozen=True)
class ConversionSideState:
    """Key conversion geometry for one side."""

    color: Color
    king: tuple[int, int]
    passers: list[tuple[int, int]]
    heavy: list[tuple[int, int, PieceType]]

@dataclass(frozen=True)
class ConversionContext:
    """Cached geometry for one side's practical conversion plan."""

    color: Color
    own: ConversionSideState
    enemy: ConversionSideState
    main_passer: tuple[int, int] | None
    is_heavy_conversion: bool
    is_low_material_conversion: bool

@dataclass(frozen=True)
class LowMaterialMovePlan:
    """Context needed to score one low-material conversion move."""

    board: Board
    move: Move
    child_board: Board
    context: ConversionContext
    child_context: ConversionContext

def _conversion_distance_pressure_score(board: Board, context: ConversionContext) -> int:
    if context.main_passer is None:
        return 0
    pawn_row, pawn_col = context.main_passer
    promotion_square = (
        (0, pawn_col) if context.color == Color.WHITE else (7, pawn_col)
    )
    block_square = (
        (pawn_row - 1, pawn_col) if context.color == Color.WHITE else (pawn_row + 1, pawn_col)
    )
    score = (8 - _promotion_distance(context.color, pawn_row)) * _CONVERSION_DISTANCE_PRESSURE_BONUS
    enemy_to_promo = _king_distance(context.enemy.king, promotion_square)
    own_to_promo = _king_distance(context.own.king, promotion_square)
    enemy_to_block = (
        _king_distance(context.enemy.king, block_square)
        if 0 <= block_square[0] < 8
        else enemy_to_promo
    )
    own_to_block = (
        _king_distance(context.own.king, block_square)
        if 0 <= block_square[0] < 8
        else own_to_promo
    )
    score += max(0, enemy_to_promo - own_to_promo) * (_CONVERSION_DISTANCE_PRESSURE_BONUS // 2)
    score += max(0, enemy_to_block - own_to_block) * (_CONVERSION_DISTANCE_PRESSURE_BONUS // 2)
    promotion_constant = _square_tuple_to_constant(*promotion_square)
    for piece, _, _ in iter_color_pieces(board, context.color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN, PieceType.BISHOP}:
            continue
        if piece_attacks_square(piece, piece.square, promotion_constant, board):
            score += _CONVERSION_DISTANCE_PRESSURE_BONUS
    return score

def _can_have_conversion_shape(board: Board) -> bool:
    return non_king_piece_count_at_most(board, _MAX_HEAVY_CONVERSION_NON_KING_PIECES)

def _leading_color(board: Board) -> Color | None:
    return materially_ahead_color(board)

def _is_simple_conversion_endgame(board: Board) -> bool:
    non_king_pieces = non_king_piece_kinds(board)
    return (
        len(non_king_pieces) <= _MAX_NON_KING_PIECES
        and any(kind in {PieceType.ROOK, PieceType.QUEEN} for kind in non_king_pieces)
    )

def _is_low_material_conversion_endgame(
    board: Board,
    color: Color,
    main_passer: tuple[int, int] | None,
    enemy_heavy: list[tuple[int, int, PieceType]],
) -> bool:
    non_king_pieces = non_king_piece_kinds(board)
    if len(non_king_pieces) > _MAX_NON_KING_PIECES:
        return False
    if any(kind == PieceType.QUEEN for kind in non_king_pieces):
        return False
    if enemy_heavy:
        return False
    if _material_lead(board, color) < MATERIAL_VALUES[PieceType.PAWN]:
        return False
    if main_passer is None:
        return False
    return _promotion_distance(color, main_passer[0]) <= 4

def _is_heavy_conversion_battle(
    board: Board,
    color: Color,
    main_passer: tuple[int, int] | None,
    own_heavy: list[tuple[int, int, PieceType]],
    enemy_heavy: list[tuple[int, int, PieceType]],
) -> bool:
    if not _has_heavy_conversion_passer(color, main_passer):
        return False
    if not own_heavy or not enemy_heavy:
        return False
    if _material_lead(board, color) < _MIN_HEAVY_CONVERSION_LEAD:
        return False
    return len(non_king_piece_kinds(board)) <= _MAX_HEAVY_CONVERSION_NON_KING_PIECES

def _has_meaningful_counterplay(
    enemy_heavy: list[tuple[int, int, PieceType]],
    enemy_passers: list[tuple[int, int]],
) -> bool:
    return bool(enemy_heavy or enemy_passers)

def _is_heavy_conversion_passer(color: Color, row: int) -> bool:
    return row <= 4 if color == Color.WHITE else row >= 3

def _has_heavy_conversion_passer(
    color: Color,
    main_passer: tuple[int, int] | None,
) -> bool:
    return (
        main_passer is not None
        and _is_heavy_conversion_passer(color, main_passer[0])
        and _is_outside_passer(main_passer[1])
    )

def _conversion_paused_for_king_danger(
    board: Board,
    context: ConversionContext,
) -> bool:
    return (
        king_danger_index(board, context.color) >= DANGEROUS_KING_PRESSURE_THRESHOLD
        or (context.is_heavy_conversion and board.turn != context.color)
    )

def _king_activation_score(context: ConversionContext) -> int:
    if context.own.passers:
        nearest = min(_king_distance(context.own.king, pawn) for pawn in context.own.passers)
        enemy_nearest = min(
            _king_distance(context.enemy.king, pawn)
            for pawn in context.own.passers
        )
        score = max(0, 8 - nearest) * _KING_ACTIVATION_BONUS
        if nearest + 1 < enemy_nearest:
            score += _KING_ACTIVATION_BONUS
        if (
            context.main_passer is not None
            and _king_is_behind_main_passer(
                context.color,
                context.own.king,
                context.main_passer,
            )
        ):
            score += _KING_ACTIVATION_BONUS
        return score
    return max(0, 8 - _king_distance(context.own.king, context.enemy.king)) * (
        _KING_ACTIVATION_BONUS // 2
    )

def _passer_support_score(board: Board, context: ConversionContext) -> int:
    score = 0
    for pawn_row, pawn_col in context.own.passers:
        if not is_advanced_passer(context.color, pawn_row):
            continue
        for row in heavy_piece_file_support_rows(board, context.color, (pawn_row, pawn_col)):
            if _is_behind_pawn(context.color, row, pawn_row):
                score += _PASSER_SUPPORT_BONUS
    return score

def _trade_quality_score(board: Board, context: ConversionContext) -> int:
    score = 0
    for piece, _, _ in iter_color_pieces(board, context.color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN}:
            continue
        for row, col, _ in context.enemy.heavy:
            if piece_attacks_square(
                piece,
                piece.square,
                _square_tuple_to_constant(row, col),
                board,
            ):
                score += _TRADE_QUALITY_BONUS
    return score

def _promotion_lane_support_score(board: Board, context: ConversionContext) -> int:
    lane_squares = _conversion_lane_squares(context)
    if not lane_squares:
        return 0
    score = 0
    promotion_square = lane_squares[-1]
    for piece, _, _ in iter_color_pieces(board, context.color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN, PieceType.BISHOP}:
            continue
        for square in lane_squares[:-1]:
            if piece_attacks_square(piece, piece.square, _square_tuple_to_constant(*square), board):
                score += _PROMOTION_LANE_SUPPORT_BONUS
        if piece_attacks_square(
            piece,
            piece.square,
            _square_tuple_to_constant(*promotion_square),
            board,
        ):
            score += _PROMOTION_SQUARE_SUPPORT_BONUS
    return score

def _minor_conversion_support_score(board: Board, context: ConversionContext) -> int:
    lane_squares = _conversion_lane_squares(context)
    if not lane_squares:
        return 0
    score = 0
    for piece, row, col in iter_color_pieces(board, context.color):
        if piece.kind not in {PieceType.BISHOP, PieceType.KNIGHT}:
            continue
        supports_lane = any(
            piece_attacks_square(piece, piece.square, _square_tuple_to_constant(*square), board)
            for square in lane_squares
        )
        if supports_lane:
            score += _MINOR_LANE_SUPPORT_BONUS
            continue
        if row in {0, 7} or col in {0, 7}:
            score -= _MINOR_EDGE_DRIFT_PENALTY
    return score

def _counterplay_suppression_score(board: Board, context: ConversionContext) -> int:
    score = 0
    own_passer_file = None if context.main_passer is None else context.main_passer[1]
    for piece, row, col in iter_color_pieces(board, context.enemy.color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN}:
            continue
        if row == context.own.king[0] or col == context.own.king[1]:
            score -= _COUNTERPLAY_SUPPRESSION_BONUS
        if own_passer_file is not None and col == own_passer_file:
            score -= _COUNTERPLAY_SUPPRESSION_BONUS + _COUNTERPLAY_LINE_PENALTY
    return score - _heavy_side_drift_penalty(context)

def _enemy_passer_suppression_score(context: ConversionContext) -> int:
    score = 0
    for pawn_row, pawn_col in context.enemy.passers:
        block_row = pawn_row + (-1 if context.enemy.color == Color.WHITE else 1)
        if context.own.king == (block_row, pawn_col):
            score += _ENEMY_PASSER_SUPPRESSION_BONUS
        for row, col, _ in context.own.heavy:
            if col == pawn_col and abs(row - pawn_row) >= 1:
                score += _ENEMY_PASSER_SUPPRESSION_BONUS // 2
    return score

def _king_cutoff_score(context: ConversionContext) -> int:
    score = 0
    for row, col, _ in context.own.heavy:
        if row == context.enemy.king[0] and abs(col - context.enemy.king[1]) >= 2:
            score += _KING_CUTOFF_BONUS
        if col == context.enemy.king[1] and abs(row - context.enemy.king[0]) >= 2:
            score += _KING_CUTOFF_BONUS
    return score

def _low_material_conversion_score(board: Board, context: ConversionContext) -> int:
    if context.main_passer is None:
        return 0
    score = _low_material_king_lead_score(context)
    score += _low_material_main_passer_score(context)
    score += _low_material_rook_cutoff_score(context)
    score += _low_material_minor_support_score(board, context)
    return score

def _low_material_king_lead_score(context: ConversionContext) -> int:
    if context.main_passer is None:
        return 0
    own_distance = _king_distance(context.own.king, context.main_passer)
    enemy_distance = _king_distance(context.enemy.king, context.main_passer)
    return max(0, enemy_distance - own_distance) * _LOW_MATERIAL_KING_LEAD_BONUS

def _low_material_main_passer_score(context: ConversionContext) -> int:
    if context.main_passer is None:
        return 0
    return (
        8 - _promotion_distance(context.color, context.main_passer[0])
    ) * _LOW_MATERIAL_MAIN_PASSER_BONUS

def _low_material_rook_cutoff_score(context: ConversionContext) -> int:
    return sum(
        _LOW_MATERIAL_CUTOFF_BONUS
        for row, col, kind in context.own.heavy
        if kind == PieceType.ROOK and _rook_cuts_off_enemy_king(row, col, context)
    )

def _low_material_minor_support_score(board: Board, context: ConversionContext) -> int:
    if context.main_passer is None:
        return 0
    score = 0
    for piece, _, _ in iter_color_pieces(board, context.color):
        if piece.kind != PieceType.BISHOP:
            continue
        if piece_attacks_square(
            piece,
            piece.square,
            _square_tuple_to_constant(*context.main_passer),
            board,
        ):
            score += _MINOR_LANE_SUPPORT_BONUS
    return score

def _seventh_rank_pressure_score(context: ConversionContext) -> int:
    if not any(is_advanced_passer(context.color, pawn_row) for pawn_row, _ in context.own.passers):
        return 0
    target_row = 1 if context.color == Color.WHITE else 6
    return sum(
        _SEVENTH_RANK_PRESSURE_BONUS
        for row, _, _ in context.own.heavy
        if row == target_row
    )

def _is_behind_pawn(color: Color, piece_row: int, pawn_row: int) -> bool:
    return piece_row > pawn_row if color == Color.WHITE else piece_row < pawn_row

def _king_is_behind_main_passer(
    color: Color,
    own_king: tuple[int, int],
    main_passer: tuple[int, int],
) -> bool:
    pawn_row, pawn_col = main_passer
    row_ok = own_king[0] >= pawn_row if color == Color.WHITE else own_king[0] <= pawn_row
    return row_ok and abs(own_king[1] - pawn_col) <= 1

def _move_checks_opponent(board: Board, color: Color) -> bool:
    return is_in_check(board, _opponent(color))

def _heavy_piece_positions(
    board: Board,
    color: Color,
) -> list[tuple[int, int, PieceType]]:
    return [
        (row, col, piece.kind)
        for piece, row, col in iter_color_pieces(board, color)
        if piece.kind in {PieceType.ROOK, PieceType.QUEEN}
    ]

def _main_passer(
    color: Color,
    passers: list[tuple[int, int]],
    enemy_king: tuple[int, int] | None = None,
) -> tuple[int, int] | None:
    if not passers:
        return None
    return min(
        passers,
        key=lambda pawn: (
            _promotion_distance(color, pawn[0]),
            -_outside_file_bonus(pawn[1]),
            0 if enemy_king is None else -_king_distance(enemy_king, pawn),
        ),
    )

def _conversion_lane_squares(context: ConversionContext) -> list[tuple[int, int]]:
    if context.main_passer is None:
        return []
    pawn_row, pawn_col = context.main_passer
    direction = -1 if context.color == Color.WHITE else 1
    promotion_row = 0 if context.color == Color.WHITE else 7
    squares: list[tuple[int, int]] = []
    current_row = pawn_row + direction
    while 0 <= current_row < 8:
        squares.append((current_row, pawn_col))
        if current_row == promotion_row:
            break
        current_row += direction
    return squares

def _heavy_side_drift_penalty(context: ConversionContext) -> int:
    if context.main_passer is None:
        return 0
    _, pawn_col = context.main_passer
    return sum(
        _HEAVY_SIDE_DRIFT_PENALTY
        for _, col, _ in context.own.heavy
        if abs(col - pawn_col) >= 4
    )

def _material_lead(board: Board, color: Color) -> int:
    own_material = 0
    enemy_material = 0
    for piece, _, _ in iter_color_pieces(board, color):
        if piece.kind != PieceType.KING:
            own_material += MATERIAL_VALUES[piece.kind]
    for piece, _, _ in iter_color_pieces(board, _opponent(color)):
        if piece.kind != PieceType.KING:
            enemy_material += MATERIAL_VALUES[piece.kind]
    return own_material - enemy_material

def _square_tuple_to_constant(row: int, col: int):
    return get_square_constant(row, col)

def _promotion_distance(color: Color, row: int) -> int:
    return row if color == Color.WHITE else 7 - row

def _outside_file_bonus(col: int) -> int:
    return max(col, 7 - col)

def _is_outside_passer(col: int) -> bool:
    return col in {0, 1, 6, 7}

def _king_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])

def _color_sign(color: Color) -> int:
    return 1 if color == Color.WHITE else -1

def _opponent(color: Color) -> Color:
    return opposite_color(color)

def _low_material_move_bonus(
    plan: LowMaterialMovePlan,
    kind: PieceType,
    scale: int,
) -> int:
    if not plan.context.is_low_material_conversion or plan.context.main_passer is None:
        return 0
    bonus = 0
    if _immediate_main_passer_promotion_available(plan.context):
        if _is_main_passer_promotion_move(plan.move, plan.context):
            bonus += _LOW_MATERIAL_PROMOTION_BONUS * scale
        else:
            bonus -= _LOW_MATERIAL_MISSED_PROMOTION_PENALTY * scale
    if kind == PieceType.KING:
        bonus += _king_lead_move_bonus(plan.context, plan.child_context) * scale
    if kind == PieceType.PAWN:
        bonus += _main_passer_move_bonus(plan.move, plan.context, plan.child_context) * scale
    if kind == PieceType.ROOK and _rook_move_creates_cutoff(plan.move, plan.child_context):
        bonus += _LOW_MATERIAL_CUTOFF_BONUS * scale
    if _trades_into_trivial_win(
        plan.board,
        plan.child_board,
        plan.context,
        plan.move,
    ):
        bonus += _LOW_MATERIAL_TRADE_BONUS * scale
    return bonus

def _trivial_conversion_transition_bonus(
    board: Board,
    child_board: Board,
    context: ConversionContext,
    child_context: ConversionContext,
) -> int:
    if context.color != child_context.color:
        return 0
    if not context.is_heavy_conversion:
        return 0
    before_pieces = len(non_king_piece_kinds(board))
    after_pieces = len(non_king_piece_kinds(child_board))
    if after_pieces >= before_pieces:
        return 0
    if not child_context.is_low_material_conversion:
        return 0
    if _material_lead(child_board, context.color) < MATERIAL_VALUES[PieceType.PAWN]:
        return 0
    return _TRIVIAL_CONVERSION_TRANSITION_BONUS + (before_pieces - after_pieces) * 8

def _king_lead_move_bonus(
    context: ConversionContext,
    child_context: ConversionContext,
) -> int:
    if context.main_passer is None or child_context.main_passer is None:
        return 0
    before = _king_distance(context.own.king, context.main_passer)
    after = _king_distance(child_context.own.king, child_context.main_passer)
    if after >= before:
        return 0
    return (before - after) * _LOW_MATERIAL_KING_LEAD_BONUS

def _main_passer_move_bonus(
    move: Move,
    context: ConversionContext,
    child_context: ConversionContext,
) -> int:
    start = (int(move.start.row), int(move.start.col))
    end = (int(move.end.row), int(move.end.col))
    if context.main_passer == start and move.promotion is not None:
        return 0
    if child_context.main_passer == end:
        if context.enemy.passers and _premature_main_passer_push(context):
            return -_LOW_MATERIAL_PREMATURE_PUSH_PENALTY
        return _LOW_MATERIAL_MAIN_PASSER_BONUS
    if context.main_passer is not None and context.main_passer != start:
        return -_LOW_MATERIAL_SIDE_PAWN_PENALTY
    return 0

def _rook_move_creates_cutoff(move: Move, context: ConversionContext) -> bool:
    row = int(move.end.row)
    col = int(move.end.col)
    return _rook_cuts_off_enemy_king(row, col, context)

def _rook_cuts_off_enemy_king(row: int, col: int, context: ConversionContext) -> bool:
    return (
        col == context.enemy.king[1] and abs(row - context.enemy.king[0]) >= 2
    ) or (
        row == context.enemy.king[0] and abs(col - context.enemy.king[1]) >= 2
    )

def _trades_into_trivial_win(
    board: Board,
    child_board: Board,
    context: ConversionContext,
    move: Move,
) -> bool:
    captured = board.get_piece(move.end)
    if captured is None or captured.color != context.enemy.color or captured.kind == PieceType.KING:
        return False
    return (
        _non_king_piece_count(board, context.enemy.color) > 0
        and _non_king_piece_count(child_board, context.enemy.color) == 0
        and context.main_passer is not None
    )

def _premature_main_passer_push(context: ConversionContext) -> bool:
    if context.main_passer is None:
        return False
    return _king_distance(context.own.king, context.main_passer) > _king_distance(
        context.enemy.king,
        context.main_passer,
    )

def _non_king_piece_count(board: Board, color: Color) -> int:
    return sum(
        1
        for piece, _, _ in iter_color_pieces(board, color)
        if piece.kind != PieceType.KING
    )

def _immediate_main_passer_promotion_available(context: ConversionContext) -> bool:
    if context.main_passer is None:
        return False
    return _promotion_distance(context.color, context.main_passer[0]) == 1

def _is_main_passer_promotion_move(
    move: Move,
    context: ConversionContext,
) -> bool:
    return (
        context.main_passer == (int(move.start.row), int(move.start.col))
        and move.promotion is not None
    )
