"""Shared guidance for defending difficult simple endgames."""

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.constants import get_square_constant
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    iter_color_pieces,
    materially_behind_color,
    most_advanced_passer,
    non_king_piece_count_at_most,
    non_king_piece_kinds,
    opposite_color,
    passed_pawns_for_color,
)
from chess_game.chess.types import Color, Piece, PieceType

_MAX_NON_KING_PIECES = 5
_EVAL_SCALE = 3
_ORDER_SCALE = 4
_ROOT_SCALE = 6
_CRITICAL_SQUARE_BONUS = 12
_BLOCKADE_BONUS = 20
_PURPOSEFUL_CHECK_BONUS = 14
_PASSER_PRESSURE_BONUS = 10
_FAKE_CHECK_PENALTY = 28
_KING_DRAW_ZONE_BONUS = 12
_LOW_MATERIAL_BLOCKADE_CONTROL_BONUS = 18
_LOW_MATERIAL_BISHOP_BLOCKADE_BONUS = 48
_LOW_MATERIAL_ACTIVE_KING_BONUS = 30
_LOW_MATERIAL_CHECK_HOLD_BONUS = 60
_LOW_MATERIAL_KEEP_ROOK_BONUS = 30
_LOW_MATERIAL_BAD_TRADE_PENALTY = 180
_LOW_MATERIAL_KING_SHOULD_LEAD_PENALTY = 42
_LOW_MATERIAL_THEATER_DRIFT_PENALTY = 36


@dataclass(frozen=True)
class LowMaterialDefenseContext:
    """Shared geometry for low-material defensive holds."""

    color: Color
    enemy_color: Color
    dangerous_pawn: tuple[int, int]
    own_king: tuple[int, int]
    enemy_king: tuple[int, int]
    block_square: tuple[int, int]
    promotion_square: tuple[int, int]


@dataclass(frozen=True)
class LowMaterialMovePlan:
    """Shared data for scoring one low-material defensive move."""

    board: Board
    context: LowMaterialDefenseContext
    child_context: LowMaterialDefenseContext | None
    move: Move
    child_board: Board


def defensive_endgame_evaluation_score(board: Board) -> int:
    """Return a signed score for practical drawing resources in simple endgames."""

    trailing_color = _trailing_color(board)
    if trailing_color is None:
        return 0
    score = 0
    if _is_relevant_defensive_evaluation(board, trailing_color):
        score += _defensive_side_score(board, trailing_color)
    context = None
    if not _both_sides_have_rooks(board):
        context = _low_material_defense_context(board, trailing_color)
    if context is not None:
        score += _low_material_evaluation_score(board, context)
    if score == 0:
        return 0
    return _color_sign(trailing_color) * score * _EVAL_SCALE


def defensive_endgame_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for purposeful defensive endgame play."""

    if kind not in {PieceType.KING, PieceType.ROOK, PieceType.QUEEN, PieceType.BISHOP}:
        return 0
    if _trailing_color(board) != color or not _is_relevant_defensive_context(board, color):
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    before = _defensive_side_score_total(board, color)
    after = _defensive_side_score_total(child_board, color)
    bonus = (after - before) * _ORDER_SCALE
    if kind == PieceType.KING and after > before:
        bonus += _KING_DRAW_ZONE_BONUS
    if kind in {PieceType.ROOK, PieceType.QUEEN}:
        bonus += _check_resource_bonus(board, child_board, color, before, after)
    bonus += _low_material_move_bonus(
        _low_material_move_plan(board, move, child_board, color),
        kind,
        scale=1,
    )
    return bonus


def defensive_endgame_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return a root-only bonus for stronger low-material defensive holds."""

    if _trailing_color(board) != color or not _is_relevant_defensive_context(board, color):
        return 0
    before = _defensive_side_score_total(board, color)
    after = _defensive_side_score_total(child_board, color)
    piece = board.get_piece(move.start)
    if piece is None:
        return 0
    bonus = (after - before) * _ROOT_SCALE
    return bonus + _low_material_move_bonus(
        _low_material_move_plan(
            board,
            move,
            child_board,
            color,
        ),
        piece.kind,
        scale=2,
    )


def _defensive_side_score(board: Board, color: Color) -> int:
    enemy_color = _opponent(color)
    dangerous_pawn = _most_dangerous_passer(board, enemy_color)
    score = _purposeful_check_score(board, color, dangerous_pawn)
    if dangerous_pawn is None:
        return score
    score += _king_draw_zone_score(board, color, enemy_color, dangerous_pawn)
    score += _blockade_score(board, color, enemy_color, dangerous_pawn)
    score += _passer_pressure_score(board, color, dangerous_pawn)
    return score


def _defensive_side_score_total(board: Board, color: Color) -> int:
    score = 0
    if _is_relevant_defensive_endgame(board, color):
        score += _defensive_side_score(board, color)
    context = _low_material_defense_context(board, color)
    if context is not None:
        score += _low_material_defense_score(board, context)
    return score


def _check_resource_bonus(
    board: Board,
    child_board: Board,
    color: Color,
    before: int,
    after: int,
) -> int:
    before_check = _purposeful_check_score(
        board,
        color,
        _most_dangerous_passer(board, _opponent(color)),
    )
    after_check = _purposeful_check_score(
        child_board,
        color,
        _most_dangerous_passer(child_board, _opponent(color)),
    )
    if not _move_checks_opponent(child_board, color):
        return 0
    if after_check > before_check:
        return _PURPOSEFUL_CHECK_BONUS
    if after <= before:
        return -_FAKE_CHECK_PENALTY
    return 0


def _king_draw_zone_score(
    board: Board,
    color: Color,
    enemy_color: Color,
    dangerous_pawn: tuple[int, int],
) -> int:
    own_king = board.find_king(color)
    if own_king is None:
        return 0
    block_square = _block_square(enemy_color, dangerous_pawn)
    distance = _king_distance((int(own_king.row), int(own_king.col)), block_square)
    return max(0, 8 - distance) * _CRITICAL_SQUARE_BONUS


def _blockade_score(
    board: Board,
    color: Color,
    enemy_color: Color,
    dangerous_pawn: tuple[int, int],
) -> int:
    block_row, block_col = _block_square(enemy_color, dangerous_pawn)
    occupant = board.board[block_row][block_col]
    if occupant is None or occupant.color != color:
        return 0
    if occupant.kind == PieceType.KING:
        return _BLOCKADE_BONUS
    if occupant.kind in {PieceType.ROOK, PieceType.QUEEN}:
        return _BLOCKADE_BONUS // 2
    return 0


def _passer_pressure_score(
    board: Board,
    color: Color,
    dangerous_pawn: tuple[int, int],
) -> int:
    pawn_square = _square_tuple_to_constant(*dangerous_pawn)
    score = 0
    for piece, _, _ in iter_color_pieces(board, color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN}:
            continue
        if piece_attacks_square(piece, piece.square, pawn_square, board):
            score += _PASSER_PRESSURE_BONUS
    return score


def _purposeful_check_score(
    board: Board,
    color: Color,
    dangerous_pawn: tuple[int, int] | None,
) -> int:
    enemy_color = _opponent(color)
    enemy_king = board.find_king(enemy_color)
    if enemy_king is None:
        return 0
    enemy_king_square = _square_tuple_to_constant(int(enemy_king.row), int(enemy_king.col))
    enemy_king_pos = (int(enemy_king.row), int(enemy_king.col))
    escorting_pawn = (
        dangerous_pawn is not None
        and _king_distance(enemy_king_pos, dangerous_pawn) <= 2
    )
    score = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN}:
            continue
        if not piece_attacks_square(piece, piece.square, enemy_king_square, board):
            continue
        if max(abs(row - enemy_king_pos[0]), abs(col - enemy_king_pos[1])) < 2:
            continue
        score += _PURPOSEFUL_CHECK_BONUS
        if escorting_pawn:
            score += _PURPOSEFUL_CHECK_BONUS
    return score


def _most_dangerous_passer(board: Board, color: Color) -> tuple[int, int] | None:
    return most_advanced_passer(color, passed_pawns_for_color(board, color))


def _is_relevant_defensive_endgame(board: Board, color: Color) -> bool:
    if not _is_small_defensive_endgame(board):
        return False
    non_king_pieces = non_king_piece_kinds(board)
    return (
        len(non_king_pieces) <= _MAX_NON_KING_PIECES
        and _most_dangerous_passer(board, _opponent(color)) is not None
    )


def _is_relevant_defensive_evaluation(board: Board, color: Color) -> bool:
    if not _is_relevant_defensive_endgame(board, color):
        return False
    return any(
        kind in {PieceType.ROOK, PieceType.QUEEN}
        for kind in non_king_piece_kinds(board)
    )


def _is_relevant_defensive_context(board: Board, color: Color) -> bool:
    if not _is_small_defensive_endgame(board):
        return False
    return _is_relevant_defensive_endgame(board, color) or _low_material_defense_context(
        board,
        color,
    ) is not None


def _low_material_defense_context(
    board: Board,
    color: Color,
) -> LowMaterialDefenseContext | None:
    if not _is_small_defensive_endgame(board):
        return None
    non_king_pieces = non_king_piece_kinds(board)
    enemy_color = _opponent(color)
    enemy_passers = passed_pawns_for_color(board, enemy_color)
    own_king = board.find_king(color)
    enemy_king = board.find_king(enemy_color)
    dangerous_pawn = most_advanced_passer(enemy_color, enemy_passers)
    context_ready = (
        non_king_piece_count_at_most(board, _MAX_NON_KING_PIECES)
        and not any(kind == PieceType.QUEEN for kind in non_king_pieces)
        and len(enemy_passers) == 1
        and dangerous_pawn is not None
        and _promotion_distance(enemy_color, dangerous_pawn[0]) <= 3
        and own_king is not None
        and enemy_king is not None
    )
    if not context_ready:
        return None
    assert dangerous_pawn is not None
    assert own_king is not None
    assert enemy_king is not None
    return _build_low_material_defense_context(
        color,
        enemy_color,
        dangerous_pawn,
        own_king,
        enemy_king,
    )


def _is_small_defensive_endgame(board: Board) -> bool:
    return non_king_piece_count_at_most(board, _MAX_NON_KING_PIECES)


def _build_low_material_defense_context(
    color: Color,
    enemy_color: Color,
    dangerous_pawn: tuple[int, int],
    own_king,
    enemy_king,
) -> LowMaterialDefenseContext:
    block_square = _block_square(enemy_color, dangerous_pawn)
    promotion_square = (
        0 if enemy_color == Color.WHITE else 7,
        dangerous_pawn[1],
    )
    return LowMaterialDefenseContext(
        color=color,
        enemy_color=enemy_color,
        dangerous_pawn=dangerous_pawn,
        own_king=(int(own_king.row), int(own_king.col)),
        enemy_king=(int(enemy_king.row), int(enemy_king.col)),
        block_square=block_square,
        promotion_square=promotion_square,
    )


def _low_material_defense_score(
    board: Board,
    context: LowMaterialDefenseContext,
) -> int:
    score = _low_material_king_score(context)
    score += _low_material_blockade_score(board, context)
    score += _low_material_blockade_control_score(board, context)
    score += _low_material_rook_resource_score(board, context)
    return score


def _low_material_evaluation_score(
    board: Board,
    context: LowMaterialDefenseContext,
) -> int:
    if _both_sides_have_rooks(board):
        return 0
    return _low_material_defense_score(board, context)


def _low_material_king_score(context: LowMaterialDefenseContext) -> int:
    block_distance = _king_distance(context.own_king, context.block_square)
    enemy_distance = _king_distance(context.enemy_king, context.dangerous_pawn)
    score = max(0, 8 - block_distance) * _CRITICAL_SQUARE_BONUS
    if block_distance <= enemy_distance:
        score += _KING_DRAW_ZONE_BONUS
    score += max(0, enemy_distance - block_distance) * _LOW_MATERIAL_ACTIVE_KING_BONUS
    return score


def _low_material_blockade_score(
    board: Board,
    context: LowMaterialDefenseContext,
) -> int:
    block_row, block_col = context.block_square
    score = 0
    if not 0 <= block_row < 8:
        return 0
    occupant = board.board[block_row][block_col]
    if occupant is not None and occupant.color == context.color:
        if occupant.kind == PieceType.KING:
            score += _BLOCKADE_BONUS + _KING_DRAW_ZONE_BONUS
        elif occupant.kind == PieceType.BISHOP:
            score += _LOW_MATERIAL_BISHOP_BLOCKADE_BONUS
        elif occupant.kind == PieceType.ROOK:
            score += _BLOCKADE_BONUS
    promotion_row, promotion_col = context.promotion_square
    promotion_occupant = board.board[promotion_row][promotion_col]
    if promotion_occupant is not None and promotion_occupant.color == context.color:
        if promotion_occupant.kind == PieceType.BISHOP:
            score += _LOW_MATERIAL_BISHOP_BLOCKADE_BONUS
        elif promotion_occupant.kind == PieceType.ROOK:
            score += _BLOCKADE_BONUS
    return score


def _low_material_blockade_control_score(
    board: Board,
    context: LowMaterialDefenseContext,
) -> int:
    score = 0
    block_square = _square_tuple_to_constant(*context.block_square)
    promotion_square = _square_tuple_to_constant(*context.promotion_square)
    for piece, _, col in iter_color_pieces(board, context.color):
        if piece.kind == PieceType.BISHOP:
            controls_key_square = False
            if piece_attacks_square(piece, piece.square, block_square, board):
                score += _LOW_MATERIAL_BISHOP_BLOCKADE_BONUS
                controls_key_square = True
            if piece_attacks_square(piece, piece.square, promotion_square, board):
                score += _LOW_MATERIAL_BLOCKADE_CONTROL_BONUS
                controls_key_square = True
            if not controls_key_square:
                score -= _LOW_MATERIAL_THEATER_DRIFT_PENALTY
        if piece.kind == PieceType.ROOK:
            controls_key_square = False
            if col == context.dangerous_pawn[1]:
                score += _PASSER_PRESSURE_BONUS
                controls_key_square = True
            if piece_attacks_square(piece, piece.square, block_square, board):
                score += _LOW_MATERIAL_BLOCKADE_CONTROL_BONUS
                controls_key_square = True
    return score


def _low_material_rook_resource_score(
    board: Board,
    context: LowMaterialDefenseContext,
) -> int:
    score = 0
    for piece, row, col in iter_color_pieces(board, context.color):
        if piece.kind != PieceType.ROOK:
            continue
        if col == context.dangerous_pawn[1]:
            score += _LOW_MATERIAL_KEEP_ROOK_BONUS
        if _move_checks_opponent(board, context.color):
            score += _LOW_MATERIAL_CHECK_HOLD_BONUS // 2
        if (
            piece_attacks_square(
                piece,
                piece.square,
                _square_tuple_to_constant(*context.enemy_king),
                board,
            )
            and _king_distance(context.enemy_king, context.dangerous_pawn) <= 2
        ):
            score += _LOW_MATERIAL_CHECK_HOLD_BONUS
        if (row, col) == context.promotion_square:
            score += _LOW_MATERIAL_BLOCKADE_CONTROL_BONUS
    return score


def _low_material_move_plan(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
 ) -> LowMaterialMovePlan | None:
    context = _low_material_defense_context(board, color)
    child_context = _low_material_defense_context(child_board, color)
    if context is None:
        return None
    return LowMaterialMovePlan(
        board=board,
        context=context,
        child_context=child_context,
        move=move,
        child_board=child_board,
    )


def _low_material_move_bonus(
    plan: LowMaterialMovePlan | None,
    kind: PieceType,
    scale: int,
) -> int:
    if plan is None:
        return 0
    bonus = 0
    if kind == PieceType.KING and plan.child_context is not None:
        bonus += _king_activation_move_bonus(plan.context, plan.child_context) * scale
    if kind == PieceType.BISHOP:
        bonus += _bishop_blockade_move_bonus(
            plan.board,
            plan.move,
            plan.context,
            plan.child_context,
        ) * scale
    if kind == PieceType.ROOK:
        bonus += _rook_holding_move_bonus(
            plan.child_board,
            plan.move,
            plan.context,
        ) * scale
    if _king_should_lead(plan.context) and kind != PieceType.KING and not _move_improves_blockade(
        plan.board,
        plan.move,
        plan.context,
    ):
        bonus -= _LOW_MATERIAL_KING_SHOULD_LEAD_PENALTY * scale
    if _move_trades_into_bad_pawn_race(
        plan.board,
        plan.child_board,
        plan.move,
        plan.context,
    ):
        bonus -= _LOW_MATERIAL_BAD_TRADE_PENALTY * scale
    return bonus


def _king_activation_move_bonus(
    context: LowMaterialDefenseContext,
    child_context: LowMaterialDefenseContext,
) -> int:
    before = _king_distance(context.own_king, context.block_square)
    after = _king_distance(child_context.own_king, child_context.block_square)
    if after >= before:
        return 0
    return (before - after) * _LOW_MATERIAL_ACTIVE_KING_BONUS


def _bishop_blockade_move_bonus(
    board: Board,
    move: Move,
    context: LowMaterialDefenseContext,
    child_context: LowMaterialDefenseContext | None,
) -> int:
    end = (int(move.end.row), int(move.end.col))
    bonus = 0
    if end == context.promotion_square:
        bonus += _LOW_MATERIAL_BISHOP_BLOCKADE_BONUS
    if child_context is not None and _move_improves_blockade(board, move, context):
        bonus += _LOW_MATERIAL_BLOCKADE_CONTROL_BONUS
    return bonus


def _rook_holding_move_bonus(
    child_board: Board,
    move: Move,
    context: LowMaterialDefenseContext,
) -> int:
    bonus = 0
    if _move_checks_opponent(child_board, context.color):
        bonus += _LOW_MATERIAL_CHECK_HOLD_BONUS
    if int(move.end.col) == context.dangerous_pawn[1]:
        bonus += _LOW_MATERIAL_KEEP_ROOK_BONUS
    return bonus


def _move_improves_blockade(
    board: Board,
    move: Move,
    context: LowMaterialDefenseContext,
) -> bool:
    end = (int(move.end.row), int(move.end.col))
    if end in (context.block_square, context.promotion_square):
        return True
    child_board, moved_piece = _child_board_piece(board, move)
    if child_board is None or moved_piece is None:
        return False
    target_block = _square_tuple_to_constant(*context.block_square)
    target_promotion = _square_tuple_to_constant(*context.promotion_square)
    return piece_attacks_square(
        moved_piece,
        move.end,
        target_block,
        child_board,
    ) or piece_attacks_square(
        moved_piece,
        move.end,
        target_promotion,
        child_board,
    )


def _king_should_lead(context: LowMaterialDefenseContext) -> bool:
    return _king_distance(context.own_king, context.block_square) > 1


def _move_trades_into_bad_pawn_race(
    board: Board,
    child_board: Board,
    move: Move,
    context: LowMaterialDefenseContext,
) -> bool:
    captured = board.get_piece(move.end)
    moving_piece = board.get_piece(move.start)
    if (
        captured is None
        or moving_piece is None
        or moving_piece.kind != PieceType.ROOK
        or captured.kind != PieceType.ROOK
    ):
        return False
    enemy_king_square = board.find_king(context.enemy_color)
    if enemy_king_square is None:
        return False
    if max(
        abs(int(enemy_king_square.row) - int(move.end.row)),
        abs(int(enemy_king_square.col) - int(move.end.col)),
    ) != 1:
        return False
    recapture_board = child_board.clone()
    if not recapture_board.apply_legal_move(enemy_king_square, move.end):
        return False
    recapture_context = _low_material_defense_context(recapture_board, context.color)
    if recapture_context is None:
        return False
    return _king_distance(
        recapture_context.own_king,
        recapture_context.block_square,
    ) > _king_distance(
        recapture_context.enemy_king,
        recapture_context.dangerous_pawn,
    )


def _trailing_color(board: Board) -> Color | None:
    return materially_behind_color(board)


def _move_checks_opponent(board: Board, color: Color) -> bool:
    return is_in_check(board, _opponent(color))


def _child_board_piece(board: Board, move: Move) -> tuple[Board | None, Piece | None]:
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return None, None
    return child_board, child_board.get_piece(move.end)


def _both_sides_have_rooks(board: Board) -> bool:
    return _has_rook(board, Color.WHITE) and _has_rook(board, Color.BLACK)


def _has_rook(board: Board, color: Color) -> bool:
    return any(
        piece.kind == PieceType.ROOK
        for piece, _, _ in iter_color_pieces(board, color)
    )


def _block_square(enemy_color: Color, dangerous_pawn: tuple[int, int]) -> tuple[int, int]:
    pawn_row, pawn_col = dangerous_pawn
    direction = -1 if enemy_color == Color.WHITE else 1
    return pawn_row + direction, pawn_col


def _promotion_distance(color: Color, row: int) -> int:
    return row if color == Color.WHITE else 7 - row


def _square_tuple_to_constant(row: int, col: int):
    return get_square_constant(row, col)


def _king_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _color_sign(color: Color) -> int:
    return 1 if color == Color.WHITE else -1


def _opponent(color: Color) -> Color:
    return opposite_color(color)
