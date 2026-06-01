"""Shared guidance for converting materially winning endgames."""

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
    is_capture_move,
    iter_color_pieces,
    materially_ahead_color,
    non_king_piece_count_at_most,
    non_king_piece_kinds,
    opposite_color,
    passed_pawns_for_color,
)
from chess_game.chess.types import Color, PieceType

_MAX_NON_KING_PIECES = 5
_MAX_HEAVY_CONVERSION_NON_KING_PIECES = 22
_MIN_HEAVY_CONVERSION_LEAD = MATERIAL_VALUES[PieceType.BISHOP]
_EVAL_SCALE = 3
_ORDER_SCALE = 4
_ROOT_SCALE = 6
_CHECK_DRIFT_PENALTY = 36
_KING_ACTIVATION_BONUS = 10
_PASSER_ADVANCE_BONUS = 30
_MAIN_PASSER_ROOT_BONUS = 34
_TRADE_QUALITY_BONUS = 18
_PASSER_SUPPORT_BONUS = 10
_PROMOTION_LANE_SUPPORT_BONUS = 12
_PROMOTION_SQUARE_SUPPORT_BONUS = 18
_COUNTERPLAY_SUPPRESSION_BONUS = 8
_COUNTERPLAY_LINE_PENALTY = 10
_KING_CUTOFF_BONUS = 10
_ENEMY_PASSER_SUPPRESSION_BONUS = 12
_SEVENTH_RANK_PRESSURE_BONUS = 30
_MINOR_LANE_SUPPORT_BONUS = 12
_MINOR_EDGE_DRIFT_PENALTY = 12
_HEAVY_SIDE_DRIFT_PENALTY = 12
_BETTER_SIDE_PLAN_SWITCH_PENALTY = 24
_ANTI_QUEEN_TRADE_PENALTY = 50
_ANTI_QUEEN_TRADE_MIN_LEAD = 400  # 4 pawns
_LOW_MATERIAL_KING_LEAD_BONUS = 14
_LOW_MATERIAL_MAIN_PASSER_BONUS = 24
_LOW_MATERIAL_PROMOTION_BONUS = 96
_LOW_MATERIAL_MISSED_PROMOTION_PENALTY = 120
_LOW_MATERIAL_SIDE_PAWN_PENALTY = 18
_LOW_MATERIAL_PREMATURE_PUSH_PENALTY = 64
_LOW_MATERIAL_TRADE_BONUS = 240
_LOW_MATERIAL_CUTOFF_BONUS = 42
_CONVERSION_DISTANCE_PRESSURE_BONUS = 12
_TRIVIAL_CONVERSION_TRANSITION_BONUS = 54


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
