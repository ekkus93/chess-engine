"""Narrow emergency-defense guidance for practical low-material endgames."""

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.constants import get_square_constant
from chess_game.chess.low_material_race_guidance import endgame_race_context
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    ENDGAME_PRINCIPAL_PIECE_KINDS,
    iter_color_pieces,
    king_coordinates,
    materially_behind_color,
    most_advanced_passer,
    non_king_material_lead,
    non_king_piece_count_at_most,
    opposite_color,
    passed_pawns_for_color,
)
from chess_game.chess.types import Color, PieceType

_MAX_NON_KING_PIECES = 8
_CRITICAL_PUSHES = 2
_KING_DANGER_EVAL_SCALE = 3
_HOLDABILITY_EVAL_SCALE = 2
_ORDER_SCALE = 8
_ROOT_SCALE = 12
_DISTANCE_WEIGHT = 10
_BLOCKADE_OCCUPANCY_BONUS = 36
_PROMOTION_CONTROL_BONUS = 24
_THEATER_DRIFT_PENALTY = 80
_CHECK_RESOURCE_BONUS = 14
_PIECE_RETENTION_BONUS = 12
_BAD_TRADE_PENALTY = 22
_EMERGENCY_EXTENSION_DELTA = 20
_KING_SHOULD_LEAD_PENALTY = 64


@dataclass(frozen=True)
class EmergencyDefenseContext:
    """Emergency geometry for containing one critical enemy passer."""

    color: Color
    enemy_color: Color
    dangerous_pawn: tuple[int, int]
    block_square: tuple[int, int]
    promotion_square: tuple[int, int]
    pushes_remaining: int


def defensive_king_danger_evaluation_score(board: Board) -> int:
    """Return a signed king-danger score for the materially trailing side."""

    trailing = materially_behind_color(board)
    if trailing is None:
        return 0
    context = _emergency_context(board, trailing)
    if context is None or not _is_low_material_king_danger_position(board):
        return 0
    return _color_sign(trailing) * _king_danger_score(board, context) * _KING_DANGER_EVAL_SCALE


def endgame_holdability_evaluation_score(board: Board) -> int:
    """Return a signed practical holdability score for the trailing side."""

    trailing = materially_behind_color(board)
    if trailing is None:
        return 0
    context = _emergency_context(board, trailing)
    if context is None:
        return 0
    return _color_sign(trailing) * _holdability_score(board, context) * _HOLDABILITY_EVAL_SCALE


def endgame_emergency_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for emergency containment and active holds."""

    if kind not in ENDGAME_PRINCIPAL_PIECE_KINDS:
        return 0
    context = _emergency_context(board, color)
    if context is None:
        return 0
    child_board = _child_board_after_move(board, move)
    if child_board is None:
        return 0
    next_context = _emergency_context(child_board, color) or context
    before = _king_danger_score(board, context) + _holdability_score(board, context)
    after = _king_danger_score(
        child_board,
        next_context,
    ) + _holdability_score(child_board, next_context)
    bonus = (after - before) * _ORDER_SCALE
    bonus += _direct_emergency_move_bonus(board, child_board, move, next_context)
    return bonus


def endgame_emergency_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return a root tie-break bonus for emergency defensive containment."""

    context = _emergency_context(board, color)
    if context is None:
        return 0
    next_context = _emergency_context(child_board, color) or context
    before = _king_danger_score(board, context) + _holdability_score(board, context)
    after = _king_danger_score(
        child_board,
        next_context,
    ) + _holdability_score(child_board, next_context)
    bonus = (after - before) * _ROOT_SCALE
    bonus += _direct_emergency_move_bonus(board, child_board, move, next_context)
    return bonus


def endgame_emergency_extension_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return 1 for tightly-gated emergency containment moves."""

    context = _emergency_context(board, color)
    if context is None:
        return 0
    next_context = _emergency_context(child_board, color) or context
    before = _king_danger_score(board, context) + _holdability_score(board, context)
    after = _king_danger_score(
        child_board,
        next_context,
    ) + _holdability_score(child_board, next_context)
    if after - before >= _EMERGENCY_EXTENSION_DELTA:
        return 1
    if _move_directly_controls_promotion(move, child_board, next_context):
        return 1
    return 0


def _is_low_material_king_danger_position(board: Board) -> bool:
    return non_king_piece_count_at_most(
        board,
        _MAX_NON_KING_PIECES,
        allowed_kinds={
            PieceType.PAWN,
            PieceType.BISHOP,
            PieceType.KNIGHT,
            PieceType.ROOK,
        },
    )


def _emergency_context(board: Board, color: Color) -> EmergencyDefenseContext | None:
    if materially_behind_color(board) != color or not non_king_piece_count_at_most(
        board,
        _MAX_NON_KING_PIECES,
    ):
        return None
    if not _has_non_king_piece(board, color):
        return None
    race_context = endgame_race_context(board, color)
    if race_context is None or race_context.mode != "must_hold":
        return None
    enemy = opposite_color(color)
    dangerous = _critical_enemy_passer(board, enemy)
    if dangerous is None:
        return None
    return EmergencyDefenseContext(
        color=color,
        enemy_color=enemy,
        dangerous_pawn=dangerous,
        block_square=_block_square(enemy, dangerous),
        promotion_square=_promotion_square(enemy, dangerous[1]),
        pushes_remaining=_promotion_pushes_remaining(enemy, dangerous[0]),
    )


def _critical_enemy_passer(board: Board, enemy_color: Color) -> tuple[int, int] | None:
    passers = passed_pawns_for_color(board, enemy_color)
    critical = [
        pawn
        for pawn in passers
        if _promotion_pushes_remaining(enemy_color, pawn[0]) <= _CRITICAL_PUSHES
    ]
    return most_advanced_passer(enemy_color, critical)


def _has_non_king_piece(board: Board, color: Color) -> bool:
    for piece, _, _ in iter_color_pieces(board, color):
        if piece.kind != PieceType.KING:
            return True
    return False


def _child_board_after_move(board: Board, move: Move) -> Board | None:
    child_board = board.clone()
    if child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return child_board
    return None


def _king_danger_score(board: Board, context: EmergencyDefenseContext) -> int:
    own_king = king_coordinates(board, context.color)
    enemy_king = king_coordinates(board, context.enemy_color)
    if own_king is None or enemy_king is None:
        return 0
    block_distance = _king_distance(own_king, context.block_square)
    promotion_distance = _king_distance(own_king, context.promotion_square)
    enemy_escort = _king_distance(enemy_king, context.dangerous_pawn)
    urgency = 3 - min(3, context.pushes_remaining)
    score = max(0, 10 - block_distance) * _DISTANCE_WEIGHT
    score += max(0, 9 - promotion_distance) * (_DISTANCE_WEIGHT // 2)
    score += max(0, enemy_escort - block_distance) * _DISTANCE_WEIGHT
    score += urgency * _DISTANCE_WEIGHT
    block_row, block_col = context.block_square
    if 0 <= block_row < 8:
        occupant = board.board[block_row][block_col]
        if occupant is not None and occupant.color == context.color:
            score += _BLOCKADE_OCCUPANCY_BONUS
    promotion_square = get_square_constant(*context.promotion_square)
    for piece, _, _ in iter_color_pieces(board, context.color):
        if piece.kind not in {
            PieceType.BISHOP,
            PieceType.KNIGHT,
            PieceType.ROOK,
            PieceType.QUEEN,
        }:
            continue
        if piece_attacks_square(piece, piece.square, promotion_square, board):
            score += _PROMOTION_CONTROL_BONUS
    return score


def _holdability_score(board: Board, context: EmergencyDefenseContext) -> int:
    score = 0
    enemy_king_square = board.find_king(context.enemy_color)
    if enemy_king_square is not None:
        enemy_constant = get_square_constant(
            int(enemy_king_square.row),
            int(enemy_king_square.col),
        )
        for piece, _, _ in iter_color_pieces(board, context.color):
            if piece.kind not in {PieceType.ROOK, PieceType.QUEEN, PieceType.BISHOP}:
                continue
            if piece_attacks_square(piece, piece.square, enemy_constant, board):
                score += _CHECK_RESOURCE_BONUS
    if non_king_material_lead(board, context.color) < 0:
        score += _PIECE_RETENTION_BONUS
    return score


def _direct_emergency_move_bonus(
    board: Board,
    child_board: Board,
    move: Move,
    context: EmergencyDefenseContext,
) -> int:
    end = (int(move.end.row), int(move.end.col))
    start = (int(move.start.row), int(move.start.col))
    bonus = 0
    moving_piece = board.get_piece(move.start)
    if moving_piece is None:
        return 0
    if end in {context.block_square, context.promotion_square}:
        bonus += _BLOCKADE_OCCUPANCY_BONUS
    if _move_directly_controls_promotion(move, child_board, context):
        bonus += _PROMOTION_CONTROL_BONUS
    if moving_piece.kind == PieceType.KING:
        start_block_distance = _king_distance(start, context.block_square)
        end_block_distance = _king_distance(end, context.block_square)
        start_promo_distance = _king_distance(start, context.promotion_square)
        end_promo_distance = _king_distance(end, context.promotion_square)
        if end_block_distance < start_block_distance:
            bonus += _CHECK_RESOURCE_BONUS
        if end_promo_distance < start_promo_distance:
            bonus += _CHECK_RESOURCE_BONUS // 2
    if _drifts_from_emergency_theater(context, move):
        bonus -= _THEATER_DRIFT_PENALTY
    if is_in_check(child_board, context.enemy_color):
        bonus += _CHECK_RESOURCE_BONUS * 4
    if (
        moving_piece.kind != PieceType.KING
        and _king_should_lead(board, context)
        and not _move_directly_controls_promotion(move, child_board, context)
    ):
        bonus -= _KING_SHOULD_LEAD_PENALTY
    if _is_bad_trade_when_worse(board, move, context.color):
        bonus -= _BAD_TRADE_PENALTY
    return bonus


def _move_directly_controls_promotion(
    move: Move,
    child_board: Board,
    context: EmergencyDefenseContext,
) -> bool:
    moved_piece = child_board.get_piece(move.end)
    if moved_piece is None or moved_piece.color != context.color:
        return False
    target = get_square_constant(*context.promotion_square)
    return piece_attacks_square(moved_piece, move.end, target, child_board)


def _drifts_from_emergency_theater(context: EmergencyDefenseContext, move: Move) -> bool:
    start = (int(move.start.row), int(move.start.col))
    end = (int(move.end.row), int(move.end.col))
    start_distance = _king_distance(start, context.block_square)
    end_distance = _king_distance(end, context.block_square)
    if end_distance > start_distance:
        return True
    start_promotion_distance = _king_distance(start, context.promotion_square)
    end_promotion_distance = _king_distance(end, context.promotion_square)
    return end_promotion_distance > start_promotion_distance


def _is_bad_trade_when_worse(board: Board, move: Move, color: Color) -> bool:
    moving_piece = board.get_piece(move.start)
    captured_piece = board.get_piece(move.end)
    if moving_piece is None or captured_piece is None:
        return False
    if moving_piece.color != color:
        return False
    return (
        moving_piece.kind in {PieceType.ROOK, PieceType.QUEEN}
        and captured_piece.kind in {PieceType.ROOK, PieceType.QUEEN}
    )


def _king_should_lead(board: Board, context: EmergencyDefenseContext) -> bool:
    own_king = king_coordinates(board, context.color)
    if own_king is None:
        return False
    return _king_distance(own_king, context.block_square) > 2


def _promotion_pushes_remaining(color: Color, row: int) -> int:
    return row if color == Color.WHITE else 7 - row


def _promotion_square(color: Color, col: int) -> tuple[int, int]:
    return (0, col) if color == Color.WHITE else (7, col)


def _block_square(color: Color, pawn: tuple[int, int]) -> tuple[int, int]:
    row, col = pawn
    return (row - 1, col) if color == Color.WHITE else (row + 1, col)


def _king_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _color_sign(color: Color) -> int:
    return 1 if color == Color.WHITE else -1
