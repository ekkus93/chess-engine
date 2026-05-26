"""Shared guidance for defending difficult simple endgames."""

from chess_game.chess.board import Board
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.constants import get_square_constant
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    iter_color_pieces,
    materially_behind_color,
    non_king_piece_kinds,
    opposite_color,
    passed_pawns_for_color,
)
from chess_game.chess.types import Color, PieceType

_MAX_NON_KING_PIECES = 5
_EVAL_SCALE = 3
_ORDER_SCALE = 4
_CRITICAL_SQUARE_BONUS = 12
_BLOCKADE_BONUS = 20
_PURPOSEFUL_CHECK_BONUS = 14
_PASSER_PRESSURE_BONUS = 10
_FAKE_CHECK_PENALTY = 28
_KING_DRAW_ZONE_BONUS = 12


def defensive_endgame_evaluation_score(board: Board) -> int:
    """Return a signed score for practical drawing resources in simple endgames."""

    trailing_color = _trailing_color(board)
    if trailing_color is None or not _is_relevant_defensive_evaluation(board, trailing_color):
        return 0
    return _color_sign(trailing_color) * _defensive_side_score(board, trailing_color) * _EVAL_SCALE


def defensive_endgame_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for purposeful defensive endgame play."""

    if kind not in {PieceType.KING, PieceType.ROOK, PieceType.QUEEN}:
        return 0
    trailing_color = _trailing_color(board)
    if trailing_color != color or not _is_relevant_defensive_endgame(board, color):
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    before = _defensive_side_score(board, color)
    after = _defensive_side_score(child_board, color)
    bonus = (after - before) * _ORDER_SCALE
    if kind == PieceType.KING and after > before:
        bonus += _KING_DRAW_ZONE_BONUS
    if kind in {PieceType.ROOK, PieceType.QUEEN}:
        bonus += _check_resource_bonus(board, child_board, color, before, after)
    return bonus


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
    passers = passed_pawns_for_color(board, color)
    if not passers:
        return None
    if color == Color.WHITE:
        return min(passers, key=lambda pawn: pawn[0])
    return max(passers, key=lambda pawn: pawn[0])


def _is_relevant_defensive_endgame(board: Board, color: Color) -> bool:
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


def _trailing_color(board: Board) -> Color | None:
    return materially_behind_color(board)


def _move_checks_opponent(board: Board, color: Color) -> bool:
    return is_in_check(board, _opponent(color))


def _block_square(enemy_color: Color, dangerous_pawn: tuple[int, int]) -> tuple[int, int]:
    pawn_row, pawn_col = dangerous_pawn
    direction = -1 if enemy_color == Color.WHITE else 1
    return pawn_row + direction, pawn_col


def _square_tuple_to_constant(row: int, col: int):
    return get_square_constant(row, col)


def _king_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _color_sign(color: Color) -> int:
    return 1 if color == Color.WHITE else -1


def _opponent(color: Color) -> Color:
    return opposite_color(color)
