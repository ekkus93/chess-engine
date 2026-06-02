"""Guidance for passed-pawn races in true low-material endgames."""

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.constants import ConstantSquare, get_square_constant
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    ENDGAME_PRINCIPAL_PIECE_KINDS,
    is_endgame_race_piece_kind,
    iter_color_pieces,
    king_coordinates,
    materially_behind_color,
    most_advanced_passer,
    non_king_piece_kinds,
    opposite_color,
    pawn_path_to_promotion_is_clear,
    passed_pawns_for_color,
)
from chess_game.chess.types import Color, PieceType

_MAX_NON_KING_PIECES = 4
_ORDER_SCALE = 4
_ROOT_SCALE = 5
_PROMOTION_PUSH_BONUS = 84
_READY_TO_QUEEN_BONUS = 120
_DIRECT_STOP_BONUS = 220
_ROOT_DIRECT_STOP_BONUS = 280
_KING_ACTIVATION_BONUS = 72
_TEMPO_BONUS = 24
_CRITICAL_CONTROL_BONUS = 20
_TIED_DOWN_BONUS = 18
_CLEAR_PATH_BONUS = 18
_KING_GEOMETRY_BONUS = 10
_ENDGAME_RACE_MAX_NON_KING_PIECES = 8
_ENDGAME_RACE_ORDER_SCALE = 4
_ENDGAME_RACE_ROOT_SCALE = 6
_ENDGAME_RACE_EXTENSION_DELTA = 18
_ENDGAME_RACE_BLOCKADE_BONUS = 40
_ENDGAME_RACE_PROMOTION_CONTROL_BONUS = 20
_ENDGAME_RACE_KING_APPROACH_BONUS = 8
_ENDGAME_RACE_DRIFT_PENALTY = 28


@dataclass(frozen=True)
class LowMaterialRaceContext:
    """The critical passers for one side in a low-material race."""

    color: Color
    own_passer: tuple[int, int] | None
    enemy_passer: tuple[int, int] | None


@dataclass(frozen=True)
class EndgameRaceContext:
    """The critical passers and race mode for a true endgame race."""

    color: Color
    enemy_color: Color
    mode: str
    own_passer: tuple[int, int] | None
    enemy_passer: tuple[int, int] | None


def low_material_race_evaluation_score(board: Board) -> int:
    """Return low-material race bonuses for both sides."""

    total = 0
    for color in (Color.WHITE, Color.BLACK):
        context = _race_context(board, color)
        if context is None:
            continue
        sign = 1 if color == Color.WHITE else -1
        total += sign * _side_score(board, context)
    return total


def endgame_race_context(board: Board, color: Color) -> EndgameRaceContext | None:
    """Return the must-converge or must-hold race context for one side."""

    if not _is_relevant_endgame_race(board):
        return None
    own_passer = _critical_passer(board, color)
    enemy_color = opposite_color(color)
    enemy_passer = _critical_passer(board, enemy_color)
    if own_passer is None and enemy_passer is None:
        return None
    mode = (
        "must_hold"
        if materially_behind_color(board) == color and enemy_passer is not None
        else "must_converge"
    )
    return EndgameRaceContext(
        color=color,
        enemy_color=enemy_color,
        mode=mode,
        own_passer=own_passer,
        enemy_passer=enemy_passer,
    )


def endgame_race_evaluation_score(board: Board) -> int:
    """Return a signed score for true must-converge and must-hold races."""

    if not _is_relevant_endgame_race(board):
        return 0
    total = low_material_race_evaluation_score(board)
    for color in (Color.WHITE, Color.BLACK):
        context = endgame_race_context(board, color)
        if context is None:
            continue
        sign = 1 if color == Color.WHITE else -1
        total += sign * _endgame_race_side_score(board, context)
    return total


def endgame_race_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for exact race-converging or race-holding moves."""

    if not is_endgame_race_piece_kind(kind):
        return 0
    context = endgame_race_context(board, color)
    if context is None:
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    next_context = endgame_race_context(child_board, color) or context
    before = _endgame_race_side_score(board, context)
    after = _endgame_race_side_score(child_board, next_context)
    bonus = (after - before) * _ENDGAME_RACE_ORDER_SCALE
    bonus += _endgame_race_direct_bonus(board, child_board, move, next_context)
    return bonus


def endgame_race_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return a root tie-break bonus for exact race preservation."""

    context = endgame_race_context(board, color)
    if context is None:
        return 0
    next_context = endgame_race_context(child_board, color) or context
    before = _endgame_race_side_score(board, context)
    after = _endgame_race_side_score(child_board, next_context)
    bonus = (after - before) * _ENDGAME_RACE_ROOT_SCALE
    bonus += _endgame_race_direct_bonus(board, child_board, move, next_context)
    return bonus


def endgame_race_extension_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return 1 for narrow must-converge or must-hold race moves."""

    context = endgame_race_context(board, color)
    if context is None:
        return 0
    next_context = endgame_race_context(child_board, color) or context
    before = _endgame_race_side_score(board, context)
    after = _endgame_race_side_score(child_board, next_context)
    if after - before >= _ENDGAME_RACE_EXTENSION_DELTA:
        return 1
    if (
        _endgame_race_direct_bonus(board, child_board, move, next_context)
        >= _ENDGAME_RACE_EXTENSION_DELTA
    ):
        return 1
    return 0


def low_material_race_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for critical low-material pawn races."""

    if kind not in {PieceType.KING, PieceType.BISHOP, PieceType.KNIGHT, PieceType.PAWN}:
        return 0
    context = _race_context(board, color)
    if context is None:
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    next_context = _race_context(child_board, color) or context
    bonus = (_side_score(child_board, next_context) - _side_score(board, context)) * _ORDER_SCALE
    bonus += _direct_move_bonus(
        board,
        child_board,
        kind,
        move,
        (context, next_context),
    )
    return bonus


def low_material_race_root_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return a root tie-break bonus for critical low-material pawn races."""

    piece = board.get_piece(move.start)
    if piece is None or piece.kind not in {
        PieceType.KING,
        PieceType.BISHOP,
        PieceType.KNIGHT,
        PieceType.PAWN,
    }:
        return 0
    context = _race_context(board, color)
    if context is None:
        return 0
    next_context = _race_context(child_board, color) or context
    bonus = (_side_score(child_board, next_context) - _side_score(board, context)) * _ROOT_SCALE
    bonus += _direct_move_bonus(
        board,
        child_board,
        piece.kind,
        move,
        (context, next_context),
    )
    if piece.kind in {PieceType.BISHOP, PieceType.KNIGHT, PieceType.KING} and _stops_enemy_passer(
        child_board,
        color,
        next_context.enemy_passer,
        move,
    ):
        bonus += _ROOT_DIRECT_STOP_BONUS
    return bonus


def _race_context(board: Board, color: Color) -> LowMaterialRaceContext | None:
    if not _is_low_material_board(board):
        return None
    own_passer = _critical_passer(board, color)
    enemy_color = opposite_color(color)
    enemy_passer = _critical_passer(board, enemy_color)
    if own_passer is None and enemy_passer is None:
        return None
    return LowMaterialRaceContext(
        color=color,
        own_passer=own_passer,
        enemy_passer=enemy_passer,
    )


def _is_low_material_board(board: Board) -> bool:
    kinds = non_king_piece_kinds(board)
    return len(kinds) <= _MAX_NON_KING_PIECES and not any(
        kind in {PieceType.QUEEN, PieceType.ROOK}
        for kind in kinds
    )


def _critical_passer(board: Board, color: Color) -> tuple[int, int] | None:
    passers = passed_pawns_for_color(board, color)
    critical = [
        pawn
        for pawn in passers
        if _promotion_pushes_remaining(color, pawn[0]) <= 3
    ]
    return most_advanced_passer(color, critical)


def _is_relevant_endgame_race(board: Board) -> bool:
    kinds = non_king_piece_kinds(board)
    return len(kinds) <= _ENDGAME_RACE_MAX_NON_KING_PIECES


def _side_score(board: Board, context: LowMaterialRaceContext) -> int:
    score = 0
    if context.own_passer is not None:
        score += _passer_score(board, context.color, context.own_passer)
    if context.enemy_passer is not None:
        score -= _passer_score(board, opposite_color(context.color), context.enemy_passer)
    return score


def _endgame_race_side_score(board: Board, context: EndgameRaceContext) -> int:
    score = 0
    if context.own_passer is not None:
        score += _passer_score(board, context.color, context.own_passer)
        score += _endgame_race_anchor_score(
            board,
            context.color,
            context.own_passer,
            hold=False,
        )
    if context.enemy_passer is not None:
        score -= _passer_score(board, context.enemy_color, context.enemy_passer)
        score -= _endgame_race_anchor_score(
            board,
            context.color,
            context.enemy_passer,
            hold=True,
        )
    if context.mode == "must_hold" and context.enemy_passer is not None:
        score += _must_hold_escape_score(board, context)
    if context.mode == "must_converge" and context.own_passer is not None:
        score += _must_converge_escape_score(board, context)
    return score


def _endgame_race_anchor_score(
    board: Board,
    defender_color: Color,
    pawn: tuple[int, int],
    *,
    hold: bool,
) -> int:
    score = 0
    block_square = _block_square(opposite_color(defender_color) if hold else defender_color, pawn)
    promotion_square = _promotion_square(
        opposite_color(defender_color) if hold else defender_color,
        pawn[1],
    )
    own_king = king_coordinates(board, defender_color)
    if own_king is not None:
        distance = _king_distance((int(own_king[0]), int(own_king[1])), block_square)
        score += max(0, 6 - distance) * _ENDGAME_RACE_KING_APPROACH_BONUS
        if distance <= 2:
            score += _ENDGAME_RACE_BLOCKADE_BONUS // 2
        if distance == 0:
            score += _ENDGAME_RACE_BLOCKADE_BONUS
    for piece, _, _ in iter_color_pieces(board, defender_color):
        if piece.kind not in ENDGAME_PRINCIPAL_PIECE_KINDS:
            continue
        if piece_attacks_square(piece, piece.square, get_square_constant(*promotion_square), board):
            score += _ENDGAME_RACE_PROMOTION_CONTROL_BONUS
    block_row, block_col = block_square
    if 0 <= block_row < 8 and board.board[block_row][block_col] is not None:
        occupant = board.board[block_row][block_col]
        if occupant is not None and occupant.color == defender_color:
            score += _ENDGAME_RACE_BLOCKADE_BONUS
    return score


def _must_hold_escape_score(board: Board, context: EndgameRaceContext) -> int:
    if context.enemy_passer is None:
        return 0
    own_king = king_coordinates(board, context.color)
    if own_king is None:
        return 0
    block_square = _block_square(context.enemy_color, context.enemy_passer)
    distance = _king_distance((int(own_king[0]), int(own_king[1])), block_square)
    return max(0, 4 - distance) * _ENDGAME_RACE_KING_APPROACH_BONUS


def _must_converge_escape_score(board: Board, context: EndgameRaceContext) -> int:
    if context.own_passer is None:
        return 0
    own_king = king_coordinates(board, context.color)
    if own_king is None:
        return 0
    promotion_square = _promotion_square(context.color, context.own_passer[1])
    distance = _king_distance((int(own_king[0]), int(own_king[1])), promotion_square)
    return max(0, 4 - distance) * _ENDGAME_RACE_KING_APPROACH_BONUS


def _passer_score(board: Board, color: Color, pawn: tuple[int, int]) -> int:
    enemy_color = opposite_color(color)
    own_king = king_coordinates(board, color)
    enemy_king = king_coordinates(board, enemy_color)
    remaining = _promotion_pushes_remaining(color, pawn[0])
    score = (4 - remaining) * _TEMPO_BONUS
    if remaining <= 1:
        score += _READY_TO_QUEEN_BONUS
    if pawn_path_to_promotion_is_clear(board, color, pawn):
        score += _CLEAR_PATH_BONUS
    if own_king is not None:
        score += max(0, 8 - _king_distance(own_king, pawn)) * _KING_GEOMETRY_BONUS
    if enemy_king is not None:
        score += max(0, _king_stop_margin(color, pawn, enemy_king)) * _KING_GEOMETRY_BONUS
    score += _critical_square_control_score(board, color, pawn)
    score += _tied_down_score(board, color, pawn)
    return score


def _direct_move_bonus(
    board: Board,
    child_board: Board,
    kind: PieceType,
    move: Move,
    contexts: tuple[LowMaterialRaceContext, LowMaterialRaceContext],
) -> int:
    context, next_context = contexts
    color = context.color
    bonus = 0
    if kind == PieceType.PAWN and _advances_primary_passer(next_context.own_passer, move):
        remaining = _promotion_pushes_remaining(color, int(move.end.row))
        bonus += _PROMOTION_PUSH_BONUS
        if remaining <= 1:
            bonus += _READY_TO_QUEEN_BONUS
    if kind == PieceType.KING:
        bonus += _king_activation_bonus(board, child_board, color, context, next_context)
    if kind in {PieceType.BISHOP, PieceType.KNIGHT, PieceType.KING} and _stops_enemy_passer(
        child_board,
        color,
        context.enemy_passer,
        move,
    ):
        bonus += _DIRECT_STOP_BONUS
    return bonus


def _advances_primary_passer(primary_passer: tuple[int, int] | None, move: Move) -> bool:
    if primary_passer is None:
        return False
    return primary_passer == (int(move.end.row), int(move.end.col))


def _stops_enemy_passer(
    board: Board,
    color: Color,
    enemy_passer: tuple[int, int] | None,
    move: Move,
) -> bool:
    if enemy_passer is None:
        return False
    promotion_square = _square_to_constant(
        *_promotion_square(opposite_color(color), enemy_passer[1])
    )
    block_square = _block_square(opposite_color(color), enemy_passer)
    moved_piece = board.get_piece(move.end)
    if moved_piece is None or moved_piece.color != color:
        return False
    end_square = (int(move.end.row), int(move.end.col))
    if end_square in {
        _promotion_square(opposite_color(color), enemy_passer[1]),
        block_square,
    }:
        return True
    return piece_attacks_square(moved_piece, move.end, promotion_square, board)


def _king_activation_bonus(
    board: Board,
    child_board: Board,
    color: Color,
    context: LowMaterialRaceContext,
    next_context: LowMaterialRaceContext,
) -> int:
    before = _king_race_distance(board, color, context)
    after = _king_race_distance(child_board, color, next_context)
    if before is None or after is None or after >= before:
        return 0
    return (before - after) * _KING_ACTIVATION_BONUS


def _king_race_distance(
    board: Board,
    color: Color,
    context: LowMaterialRaceContext,
) -> int | None:
    king = king_coordinates(board, color)
    if king is None:
        return None
    targets: list[tuple[int, int]] = []
    if context.own_passer is not None:
        targets.append(context.own_passer)
        targets.append(_promotion_square(color, context.own_passer[1]))
    if context.enemy_passer is not None:
        targets.append(_block_square(opposite_color(color), context.enemy_passer))
    if not targets:
        return None
    return min(_king_distance(king, target) for target in targets)


def _critical_square_control_score(
    board: Board,
    color: Color,
    pawn: tuple[int, int],
) -> int:
    promotion_square = _square_to_constant(*_promotion_square(color, pawn[1]))
    block_square = _block_square(color, pawn)
    block_constant = (
        _square_to_constant(*block_square) if 0 <= block_square[0] < 8 else None
    )
    score = 0
    for piece, _, _ in iter_color_pieces(board, color):
        if piece.kind not in {PieceType.BISHOP, PieceType.KNIGHT}:
            continue
        if piece_attacks_square(piece, piece.square, promotion_square, board):
            score += _CRITICAL_CONTROL_BONUS
        if (
            block_constant is not None
            and piece_attacks_square(piece, piece.square, block_constant, board)
        ):
            score += _CRITICAL_CONTROL_BONUS // 2
    return score


def _tied_down_score(board: Board, color: Color, pawn: tuple[int, int]) -> int:
    enemy_color = opposite_color(color)
    block_row, block_col = _block_square(color, pawn)
    promotion_row, promotion_col = _promotion_square(color, pawn[1])
    score = 0
    if 0 <= block_row < 8:
        block_piece = board.board[block_row][block_col]
        if block_piece is not None and block_piece.color == enemy_color:
            score += _TIED_DOWN_BONUS
    promotion_piece = board.board[promotion_row][promotion_col]
    if promotion_piece is not None and promotion_piece.color == enemy_color:
        score += _TIED_DOWN_BONUS
    return score


def _king_stop_margin(
    color: Color,
    pawn: tuple[int, int],
    enemy_king: tuple[int, int],
) -> int:
    remaining = _promotion_pushes_remaining(color, pawn[0])
    return min(
        _king_distance(enemy_king, _promotion_square(color, pawn[1])),
        _king_distance(enemy_king, _block_square(color, pawn)),
    ) - remaining


def _promotion_pushes_remaining(color: Color, row: int) -> int:
    return row if color == Color.WHITE else 7 - row


def _promotion_square(color: Color, col: int) -> tuple[int, int]:
    return (0, col) if color == Color.WHITE else (7, col)


def _block_square(color: Color, pawn: tuple[int, int]) -> tuple[int, int]:
    row, col = pawn
    return (row - 1, col) if color == Color.WHITE else (row + 1, col)


def _square_to_constant(row: int, col: int) -> ConstantSquare:
    return get_square_constant(row, col)


def _king_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _endgame_race_direct_bonus(
    board: Board,
    child_board: Board,
    move: Move,
    context: EndgameRaceContext,
) -> int:
    moving_piece = board.get_piece(move.start)
    if moving_piece is None:
        return 0
    bonus = 0
    end = (int(move.end.row), int(move.end.col))
    if context.own_passer is not None and moving_piece.kind == PieceType.PAWN:
        if end == context.own_passer:
            bonus += _ENDGAME_RACE_PROMOTION_CONTROL_BONUS
    if context.enemy_passer is not None and moving_piece.kind in {
        PieceType.KING,
        PieceType.ROOK,
        PieceType.QUEEN,
        PieceType.BISHOP,
        PieceType.KNIGHT,
    }:
        block_square = _block_square(context.enemy_color, context.enemy_passer)
        promotion_square = _promotion_square(context.enemy_color, context.enemy_passer[1])
        if end in {block_square, promotion_square}:
            bonus += _ENDGAME_RACE_BLOCKADE_BONUS
        if _move_directly_controls_promotion(move, child_board, context):
            bonus += _ENDGAME_RACE_PROMOTION_CONTROL_BONUS
        start_distance = _king_distance((int(move.start.row), int(move.start.col)), block_square)
        end_distance = _king_distance(end, block_square)
        if end_distance > start_distance:
            bonus -= _ENDGAME_RACE_DRIFT_PENALTY
        if moving_piece.kind == PieceType.KING and end_distance < start_distance:
            bonus += _ENDGAME_RACE_BLOCKADE_BONUS
        if moving_piece.kind == PieceType.KING and end_distance <= 2:
            bonus += _ENDGAME_RACE_BLOCKADE_BONUS // 2
        if (
            moving_piece.kind != PieceType.KING
            and end not in {block_square, promotion_square}
            and not _move_directly_controls_promotion(move, child_board, context)
        ):
            bonus -= _ENDGAME_RACE_DRIFT_PENALTY
    return bonus


def _move_directly_controls_promotion(
    move: Move,
    child_board: Board,
    context: EndgameRaceContext,
) -> bool:
    moved_piece = child_board.get_piece(move.end)
    if moved_piece is None or moved_piece.color != context.color:
        return False
    if context.enemy_passer is None:
        return False
    target = get_square_constant(*_promotion_square(context.enemy_color, context.enemy_passer[1]))
    return piece_attacks_square(moved_piece, move.end, target, child_board)
