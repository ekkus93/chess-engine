"""Shared anti-drift guidance for clearly won or clearly worse practical endings."""

from dataclasses import dataclass

from chess_game.chess.ai_repetition_patterns import move_undoes_last_own_move
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.defensive_priorities import king_danger_index
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    is_advanced_passer,
    is_capture_move,
    iter_color_pieces,
    king_coordinates,
    materially_ahead_color,
    most_advanced_passer,
    non_king_material_lead,
    non_king_piece_kinds,
    opposite_color,
    passed_pawns_for_color,
)
from chess_game.chess.types import Color, PieceType

_ANTI_DRIFT_KINDS = frozenset(
    {PieceType.KING, PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.PAWN}
)
_MAX_NON_KING_PIECES = 6
_MIN_NON_KING_PIECES = 5
_MIN_CLEAR_LEAD = 3
_ORDER_SCALE = 4
_ROOT_SCALE = 6
_SIMPLIFY_BONUS = 18
_RELIEF_BONUS = 14
_FOCUS_BONUS = 3
_KING_FOCUS_BONUS = 4
_FILE_SUPPORT_BONUS = 10
_BLOCKADE_BONUS = 18
_QUEEN_DRIFT_PENALTY = 20
_BISHOP_DRIFT_PENALTY = 16
_ROOK_DRIFT_PENALTY = 18
_PAWN_DRIFT_PENALTY = 18
_WINNING_UNDO_ORDER_PENALTY = 32
_WINNING_UNDO_ROOT_PENALTY = 72


@dataclass(frozen=True)
class DriftContext:
    """Compact anti-drift context for one side."""

    color: Color
    mode: str
    anchor: tuple[int, int] | None
    focus: tuple[int, int] | None


def anti_drift_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus that rejects fake activity in practical endings."""

    if kind not in _ANTI_DRIFT_KINDS:
        return 0
    context = _drift_context(board, color)
    if context is None:
        return 0
    bonus = _static_order_bonus(move, kind, context)
    return bonus - _winning_undo_penalty(board, move, context, _WINNING_UNDO_ORDER_PENALTY)


def anti_drift_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return a root-only bonus for moves that avoid low-value ending drift."""

    piece = board.get_piece(move.start)
    if piece is None:
        return 0
    context = _drift_context(board, color)
    if context is None:
        return 0
    before = _side_score(board, context)
    after = _side_score(child_board, _next_context(child_board, context))
    bonus = (after - before) * _ROOT_SCALE
    bonus += _trade_or_relief_bonus(board, child_board, context) * 2
    bonus += _static_order_bonus(move, piece.kind, context)
    bonus -= _winning_root_undo_penalty(board, child_board, move, context)
    return bonus + _drift_adjustment(
        child_board,
        move,
        piece.kind,
        context,
        after > before,
    )


def _winning_undo_penalty(
    board: Board,
    move: Move,
    context: DriftContext,
    penalty: int,
) -> int:
    if context.mode != "won":
        return 0
    if move.promotion is not None or is_capture_move(board, move):
        return 0
    if not move_undoes_last_own_move(board, move):
        return 0
    return penalty


def _winning_root_undo_penalty(
    board: Board,
    child_board: Board,
    move: Move,
    context: DriftContext,
) -> int:
    penalty = _winning_undo_penalty(board, move, context, _WINNING_UNDO_ROOT_PENALTY)
    if penalty == 0:
        return 0
    enemy_color = opposite_color(context.color)
    if is_in_check(child_board, enemy_color):
        return 0
    return penalty


def _drift_context(board: Board, color: Color) -> DriftContext | None:
    piece_kinds = non_king_piece_kinds(board)
    piece_count = len(piece_kinds)
    lead = _signed_material_lead(board, color)
    if (
        abs(lead) < _MIN_CLEAR_LEAD
        or piece_count < _MIN_NON_KING_PIECES
        or piece_count > _MAX_NON_KING_PIECES
        or king_danger_index(board, color) >= 2
        or not _has_required_piece_mix(piece_kinds)
    ):
        return None
    enemy_color = opposite_color(color)
    own_passers = passed_pawns_for_color(board, color)
    enemy_passers = passed_pawns_for_color(board, enemy_color)
    if len(own_passers) + len(enemy_passers) != 1:
        return None
    if lead > 0:
        anchor = most_advanced_passer(color, own_passers)
        if anchor is None or not is_advanced_passer(color, anchor[0]):
            return None
        return DriftContext(
            color=color,
            mode="won",
            anchor=anchor,
            focus=anchor if anchor is not None else king_coordinates(board, enemy_color),
        )
    anchor = most_advanced_passer(enemy_color, enemy_passers)
    if anchor is None or not is_advanced_passer(enemy_color, anchor[0]):
        return None
    return DriftContext(
        color=color,
        mode="worse",
        anchor=anchor,
        focus=None if anchor is None else _block_square(enemy_color, anchor),
    )


def _next_context(board: Board, fallback: DriftContext) -> DriftContext:
    return _drift_context(board, fallback.color) or fallback


def _side_score(board: Board, context: DriftContext) -> int:
    if context.focus is None:
        return 0
    score = _piece_focus_score(board, context)
    own_king = king_coordinates(board, context.color)
    if own_king is not None:
        score += max(0, 8 - _distance(own_king, context.focus)) * _KING_FOCUS_BONUS
    score -= king_danger_index(board, context.color) * _KING_FOCUS_BONUS
    if context.anchor is None:
        return score
    if context.mode == "won":
        score += _winning_support_score(board, context)
        return score
    return score + _defensive_blockade_score(board, context)


def _piece_focus_score(board: Board, context: DriftContext) -> int:
    if context.focus is None:
        return 0
    score = 0
    for piece, row, col in iter_color_pieces(board, context.color):
        if piece.kind == PieceType.KING:
            continue
        focus_gain = max(0, 8 - _distance((row, col), context.focus))
        if piece.kind in {PieceType.QUEEN, PieceType.ROOK}:
            score += focus_gain * _FOCUS_BONUS
        elif piece.kind == PieceType.BISHOP:
            score += focus_gain * (_FOCUS_BONUS // 2)
            if _same_diagonal((row, col), context.focus):
                score += _FOCUS_BONUS
        elif piece.kind == PieceType.PAWN and context.mode == "won":
            score += focus_gain
    return score


def _winning_support_score(board: Board, context: DriftContext) -> int:
    if context.anchor is None:
        return 0
    score = 0
    for piece, row, col in iter_color_pieces(board, context.color):
        if piece.kind in {PieceType.ROOK, PieceType.QUEEN} and col == context.anchor[1]:
            if (context.color == Color.WHITE and row > context.anchor[0]) or (
                context.color == Color.BLACK and row < context.anchor[0]
            ):
                score += _FILE_SUPPORT_BONUS
    enemy_king = king_coordinates(board, opposite_color(context.color))
    own_king = king_coordinates(board, context.color)
    if own_king is not None and enemy_king is not None:
        score += max(0, _distance(enemy_king, context.anchor) - _distance(own_king, context.anchor))
        score *= _FOCUS_BONUS
    return score


def _defensive_blockade_score(board: Board, context: DriftContext) -> int:
    if context.anchor is None or context.focus is None:
        return 0
    score = 0
    occupant = board.board[context.focus[0]][context.focus[1]]
    if occupant is not None and occupant.color == context.color:
        score += _BLOCKADE_BONUS
    for piece, _, col in iter_color_pieces(board, context.color):
        if piece.kind in {PieceType.ROOK, PieceType.QUEEN} and col == context.anchor[1]:
            score += _FILE_SUPPORT_BONUS // 2
    return score


def _trade_or_relief_bonus(board: Board, child_board: Board, context: DriftContext) -> int:
    before_count = len(non_king_piece_kinds(board))
    after_count = len(non_king_piece_kinds(child_board))
    if after_count < before_count:
        return _SIMPLIFY_BONUS if context.mode == "won" else _RELIEF_BONUS
    if king_danger_index(child_board, context.color) < king_danger_index(board, context.color):
        return _RELIEF_BONUS
    return 0


def _static_order_bonus(move: Move, kind: PieceType, context: DriftContext) -> int:
    if context.focus is None:
        return 0
    start = (int(move.start.row), int(move.start.col))
    end = (int(move.end.row), int(move.end.col))
    if end == start:
        return 0
    score = 0
    toward_focus = _distance(end, context.focus) < _distance(start, context.focus)
    if toward_focus:
        score += _focus_reward(kind)
    else:
        score -= _drift_penalty(kind)
    if context.anchor is None:
        return score
    if context.mode == "won":
        return score + _winning_order_bonus(move, end, kind, context)
    return score + _defensive_order_bonus(end, kind, context)


def _drift_adjustment(
    child_board: Board,
    move: Move,
    kind: PieceType,
    context: DriftContext,
    improved_focus: bool,
) -> int:
    if context.focus is None or improved_focus or _changes_main_theater(child_board, context):
        return 0
    if kind == PieceType.QUEEN and _moves_away(move, context.focus):
        return -_QUEEN_DRIFT_PENALTY
    if kind == PieceType.BISHOP and _moves_away(move, context.focus):
        return -_BISHOP_DRIFT_PENALTY
    if kind == PieceType.ROOK and _moves_away(move, context.focus):
        return -_ROOK_DRIFT_PENALTY
    if kind == PieceType.PAWN and not _pawn_supports_plan(move, context):
        return -_PAWN_DRIFT_PENALTY
    return 0


def _winning_order_bonus(
    move: Move,
    end: tuple[int, int],
    kind: PieceType,
    context: DriftContext,
) -> int:
    if context.anchor is None:
        return 0
    score = 0
    if kind in {PieceType.QUEEN, PieceType.ROOK} and end[1] == context.anchor[1]:
        score += _FILE_SUPPORT_BONUS
    if kind == PieceType.BISHOP and _same_diagonal(end, context.anchor):
        score += _FOCUS_BONUS * 2
    if kind == PieceType.PAWN and _pawn_supports_plan(move, context):
        score += _BLOCKADE_BONUS
    if move.promotion is not None:
        score += _SIMPLIFY_BONUS
    return score


def _defensive_order_bonus(
    end: tuple[int, int],
    kind: PieceType,
    context: DriftContext,
) -> int:
    if context.focus is None or context.anchor is None:
        return 0
    if kind in {PieceType.ROOK, PieceType.QUEEN, PieceType.KING} and end == context.focus:
        return _BLOCKADE_BONUS
    if kind in {PieceType.ROOK, PieceType.QUEEN} and end[1] == context.anchor[1]:
        return _FILE_SUPPORT_BONUS // 2
    return 0


def _changes_main_theater(child_board: Board, context: DriftContext) -> bool:
    enemy_color = opposite_color(context.color)
    next_context = _drift_context(child_board, context.color)
    if next_context is None:
        return True
    return next_context.focus != context.focus or king_danger_index(child_board, enemy_color) >= 3


def _pawn_supports_plan(move: Move, context: DriftContext) -> bool:
    if context.anchor is None:
        return False
    end = (int(move.end.row), int(move.end.col))
    if context.mode == "won":
        return end[1] == context.anchor[1] and _closer_to_promotion(context.color, move)
    return end == context.focus


def _signed_material_lead(board: Board, color: Color) -> int:
    leading_color = materially_ahead_color(board)
    if leading_color is None:
        return 0
    return non_king_material_lead(board, color)


def _block_square(color: Color, pawn: tuple[int, int]) -> tuple[int, int]:
    row, col = pawn
    return (row - 1, col) if color == Color.WHITE else (row + 1, col)


def _moves_away(move: Move, focus: tuple[int, int]) -> bool:
    start = (int(move.start.row), int(move.start.col))
    end = (int(move.end.row), int(move.end.col))
    return _distance(end, focus) >= _distance(start, focus)


def _closer_to_promotion(color: Color, move: Move) -> bool:
    if color == Color.WHITE:
        return int(move.end.row) < int(move.start.row)
    return int(move.end.row) > int(move.start.row)


def _distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _has_required_piece_mix(piece_kinds: list[PieceType]) -> bool:
    return (
        PieceType.QUEEN in piece_kinds
        and PieceType.ROOK in piece_kinds
        and PieceType.PAWN in piece_kinds
    )


def _focus_reward(kind: PieceType) -> int:
    return {
        PieceType.KING: _KING_FOCUS_BONUS,
        PieceType.QUEEN: _FOCUS_BONUS * 4,
        PieceType.ROOK: _FOCUS_BONUS * 4,
        PieceType.BISHOP: _FOCUS_BONUS * 2,
        PieceType.PAWN: _FOCUS_BONUS * 3,
    }.get(kind, 0)


def _drift_penalty(kind: PieceType) -> int:
    return {
        PieceType.KING: _FOCUS_BONUS,
        PieceType.QUEEN: _QUEEN_DRIFT_PENALTY,
        PieceType.ROOK: _ROOK_DRIFT_PENALTY,
        PieceType.BISHOP: _BISHOP_DRIFT_PENALTY,
        PieceType.PAWN: _PAWN_DRIFT_PENALTY,
    }.get(kind, 0)


def _same_diagonal(first: tuple[int, int], second: tuple[int, int]) -> bool:
    return abs(first[0] - second[0]) == abs(first[1] - second[1])
