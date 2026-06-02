"""Practical middlegame guidance for development, safety, and counterplay."""

from dataclasses import dataclass

from chess_game.chess.ai_repetition_patterns import move_undoes_last_own_move
from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.opening_development import (
    opening_central_control_bonus,
    opening_king_safety_score,
    opening_king_urgency_penalty,
    opening_piece_coordination_bonus,
    opening_rook_connection_bonus,
    undeveloped_minor_piece_count,
)
from chess_game.chess.evaluation_tables import MATERIAL_VALUES, STARTING_NON_PAWN_MATERIAL
from chess_game.chess.opponent_plans import opponent_plan_profile
from chess_game.chess.opening_development import minor_on_home_square
from chess_game.chess.strategy_utils import (
    clone_legal_child_board,
    iter_color_pieces as _iter_color_pieces,
    materially_behind_color,
    non_king_material_lead,
    non_king_piece_kinds,
    total_non_pawn_material,
    scale_signed,
)
from chess_game.chess.defensive_priorities import king_defense_profile
from chess_game.chess.types import Color, PieceType

_ORDER_SCALE = 4
_ROOT_SCALE = 6
_EXTENSION_DELTA = 18
_DEVELOPMENT_BONUS = 16
_KING_SAFETY_BONUS = 10
_COUNTERPLAY_BONUS = 8
_CENTRAL_BREAK_BONUS = 24
_CASTLED_KING_BONUS = 60
_UNCASTLED_KING_PENALTY = 40
_REPETITION_PENALTY = 20


@dataclass(frozen=True)
class MiddlegamePracticalityContext:
    """Shared middlegame summary for one side."""

    color: Color
    enemy_color: Color
    middlegame_phase: int
    undeveloped_minors: int
    threat_pressure: int
    enemy_pressure: int


def middlegame_practicality_evaluation_score(board: Board) -> int:
    """Return a signed score for practical middlegame plans."""

    context = _middlegame_context(board)
    if context is None:
        return 0
    total = 0
    for color in (Color.WHITE, Color.BLACK):
        side_context = _middlegame_context(board, color)
        if side_context is None:
            continue
        side_score = _side_score(board, side_context)
        total += side_score if color == Color.WHITE else -side_score
    return scale_signed(total, context.middlegame_phase)


def middlegame_practicality_order_bonus(
    board: Board,
    color: Color,
    move: Move,
) -> int:
    """Return a quiet-order bonus for practical middlegame play."""

    context = _middlegame_context(board, color)
    if context is None:
        return 0
    child_board = clone_legal_child_board(board, move)
    if child_board is None:
        return 0
    next_context = _middlegame_context(child_board, color) or context
    before = _side_score(board, context)
    after = _side_score(child_board, next_context)
    bonus = (after - before) * _ORDER_SCALE
    bonus += _direct_move_bonus(board, child_board, move, context)
    return bonus


def middlegame_practicality_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return a root tie-break bonus for practical middlegame play."""

    context = _middlegame_context(board, color)
    if context is None:
        return 0
    next_context = _middlegame_context(child_board, color) or context
    before = _side_score(board, context)
    after = _side_score(child_board, next_context)
    bonus = (after - before) * _ROOT_SCALE
    bonus += _direct_move_bonus(
        board,
        child_board,
        move,
        context,
    )
    return bonus


def middlegame_practicality_extension_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return 1 when a middlegame move needs a narrow extension."""

    context = _middlegame_context(board, color)
    if context is None:
        return 0
    next_context = _middlegame_context(child_board, color) or context
    before = _side_score(board, context)
    after = _side_score(child_board, next_context)
    if after - before >= _EXTENSION_DELTA:
        return 1
    if _is_central_break(move) and after >= before:
        return 1
    return 0


def _middlegame_context(
    board: Board,
    color: Color | None = None,
) -> MiddlegamePracticalityContext | None:
    phase = _middlegame_phase(board)
    if phase < 25 or phase > 95 or len(non_king_piece_kinds(board)) < 8:
        return None
    if not any(
        piece is not None and piece.kind == PieceType.QUEEN
        for row in board.board
        for piece in row
    ):
        return None
    if color is None:
        color = materially_behind_color(board) or Color.WHITE
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    return MiddlegamePracticalityContext(
        color=color,
        enemy_color=enemy_color,
        middlegame_phase=phase,
        undeveloped_minors=undeveloped_minor_piece_count(board, color),
        threat_pressure=opponent_plan_profile(board, color).pressure,
        enemy_pressure=opponent_plan_profile(board, enemy_color).pressure,
    )


def _side_score(board: Board, context: MiddlegamePracticalityContext) -> int:
    score = 0
    score -= context.undeveloped_minors * _DEVELOPMENT_BONUS
    score += opening_piece_coordination_bonus(
        board,
        context.color,
        context.undeveloped_minors,
    )
    score += opening_rook_connection_bonus(board, context.color, context.undeveloped_minors)
    score += opening_central_control_bonus(board, context.color) // 2
    score += opening_king_safety_score(board, context.color, context.undeveloped_minors)
    score -= opening_king_urgency_penalty(board, context.color, context.undeveloped_minors)
    defense = king_defense_profile(board, context.color)
    score += max(0, 6 - defense.danger) * _KING_SAFETY_BONUS
    score += defense.safe_king_moves * 2
    score += defense.king_zone_defenders * 2
    score += _castled_king_bonus(board, context.color)
    score -= _uncastled_king_penalty(board, context.color)
    score += context.enemy_pressure - context.threat_pressure
    score += _central_break_score(board, context.color)
    return score


def _direct_move_bonus(
    board: Board,
    child_board: Board,
    move: Move,
    before: MiddlegamePracticalityContext,
) -> int:
    bonus = 0
    moving_piece = board.get_piece(move.start)
    kind = moving_piece.kind if moving_piece is not None else PieceType.KING
    after = _middlegame_context(child_board, before.color) or before
    if kind in {PieceType.KNIGHT, PieceType.BISHOP} and _minor_leaves_home(
        board,
        move,
        before.color,
    ):
        bonus += _DEVELOPMENT_BONUS
    if kind == PieceType.KING:
        before_defense = king_defense_profile(board, before.color)
        after_defense = king_defense_profile(child_board, before.color)
        if after_defense.danger < before_defense.danger:
            bonus += _KING_SAFETY_BONUS * 2
        if after_defense.safe_king_moves > before_defense.safe_king_moves:
            bonus += _KING_SAFETY_BONUS
    if kind == PieceType.PAWN and _is_central_break(move):
        bonus += _CENTRAL_BREAK_BONUS
    if winning_side_consolidation_ready(board, before.color):
        bonus += _winning_side_consolidation_move_bonus(board, child_board, before)
    if defensive_hold_ready(board, before.color):
        bonus += _defensive_hold_move_bonus(board, child_board, before)
    if concrete_attack_ready(board, before.color):
        bonus += _concrete_attack_move_bonus(before, after)
    if move_undoes_last_own_move(board, move):
        bonus -= _REPETITION_PENALTY
    return bonus


def _is_central_break(move: Move) -> bool:
    start_col = int(move.start.col)
    end_col = int(move.end.col)
    return start_col in {2, 3, 4, 5} and end_col in {2, 3, 4, 5}


def _castled_king_bonus(board: Board, color: Color) -> int:
    king_square = board.find_king(color)
    if king_square is None:
        return 0
    row = int(king_square.row)
    col = int(king_square.col)
    home_row = 7 if color == Color.WHITE else 0
    if row == home_row and col in {2, 6}:
        return _CASTLED_KING_BONUS
    return 0


def _uncastled_king_penalty(board: Board, color: Color) -> int:
    king_square = board.find_king(color)
    if king_square is None:
        return 0
    row = int(king_square.row)
    col = int(king_square.col)
    home_row = 7 if color == Color.WHITE else 0
    if row == home_row and col == 4:
        return _UNCASTLED_KING_PENALTY
    return 0


def _central_break_score(board: Board, color: Color) -> int:
    score = 0
    for piece, row, col in _iter_color_pieces(board, color):
        if piece.kind != PieceType.PAWN or col not in {2, 3, 4, 5}:
            continue
        advancement = 6 - row if color == Color.WHITE else row - 1
        if advancement > 0:
            score += advancement * 4
    return score


def _minor_leaves_home(board: Board, move: Move, color: Color) -> bool:
    piece = board.get_piece(move.start)
    if piece is None or piece.kind not in {PieceType.KNIGHT, PieceType.BISHOP}:
        return False
    return minor_on_home_square(color, piece.kind, int(move.start.row), int(move.start.col))


def _middlegame_phase(board: Board) -> int:
    non_pawn_material = total_non_pawn_material(board)
    return min((non_pawn_material * 100) // STARTING_NON_PAWN_MATERIAL, 100)


def winning_side_consolidation_ready(board: Board, color: Color) -> bool:
    """Return True when this side is winning and should prioritize consolidation."""

    context = _middlegame_context(board, color)
    return (
        context is not None
        and non_king_material_lead(board, color) >= MATERIAL_VALUES[PieceType.ROOK]
    )


def defensive_hold_ready(board: Board, color: Color) -> bool:
    """Return True when this side should prioritize practical defense."""

    context = _middlegame_context(board, color)
    return context is not None and (
        materially_behind_color(board) == color
        or context.threat_pressure >= context.enemy_pressure
    )


def concrete_attack_ready(board: Board, color: Color) -> bool:
    """Return True when this side has a concrete attacking plan."""

    context = _middlegame_context(board, color)
    return context is not None and context.enemy_pressure >= context.threat_pressure


def _winning_side_consolidation_move_bonus(
    board: Board,
    child_board: Board,
    before: MiddlegamePracticalityContext,
) -> int:
    before_defense = king_defense_profile(board, before.color)
    after_defense = king_defense_profile(child_board, before.color)
    bonus = 0
    if after_defense.danger < before_defense.danger:
        bonus += _KING_SAFETY_BONUS * 2
    if after_defense.safe_king_moves > before_defense.safe_king_moves:
        bonus += _KING_SAFETY_BONUS
    return bonus


def _defensive_hold_move_bonus(
    board: Board,
    child_board: Board,
    before: MiddlegamePracticalityContext,
) -> int:
    before_defense = king_defense_profile(board, before.color)
    after_defense = king_defense_profile(child_board, before.color)
    bonus = 0
    if after_defense.danger < before_defense.danger:
        bonus += _KING_SAFETY_BONUS * 2
    if after_defense.king_zone_defenders > before_defense.king_zone_defenders:
        bonus += _KING_SAFETY_BONUS
    return bonus


def _concrete_attack_move_bonus(
    before: MiddlegamePracticalityContext,
    after: MiddlegamePracticalityContext,
) -> int:
    bonus = 0
    if after.enemy_pressure < before.enemy_pressure:
        bonus += _COUNTERPLAY_BONUS * 2
    if after.threat_pressure > before.threat_pressure:
        bonus += _COUNTERPLAY_BONUS
    return bonus
