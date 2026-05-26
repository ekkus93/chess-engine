"""Shared rook-endgame guidance for evaluation and move ordering."""

from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.move import Move
from chess_game.chess.structure_recognition import structure_profile
from chess_game.chess.strategy_utils import (
    is_advanced_passer,
    iter_color_pieces,
    non_king_piece_kinds,
    opposite_color,
    passed_pawns_for_color,
    path_clear_between,
)
from chess_game.chess.types import Color, PieceType

_ROOK_BEHIND_OWN_PASSER_BONUS = 18
_ROOK_BEHIND_ENEMY_PASSER_BONUS = 24
_ROOK_IN_FRONT_OF_ENEMY_PASSER_BONUS = 24
_ROOK_IN_FRONT_OF_PASSER_PENALTY = 16
_KING_SUPPORTS_PASSER_BONUS = 12
_OUTSIDE_PASSER_ACTIVITY_BONUS = 10
_PASSIVE_ROOK_PENALTY = 10
_WORSE_SIDE_CHECK_DRIFT_PENALTY = 48
_ORDER_SCORE_SCALE = 4


def rook_endgame_evaluation_score(board: Board) -> int:
    """Return a signed score for rook-endgame placement and defense."""

    if not _is_relevant_rook_endgame(board):
        return 0
    score = 0
    for color in (Color.WHITE, Color.BLACK):
        side_score = _rook_endgame_side_score(board, color)
        score += side_score if color == Color.WHITE else -side_score
    return score


def rook_endgame_order_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a quiet-order bonus for improving rook-endgame technique."""

    if kind not in {PieceType.KING, PieceType.ROOK, PieceType.PAWN}:
        return 0
    if not _is_relevant_rook_endgame(board):
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    before = _rook_endgame_side_score(board, color)
    after = _rook_endgame_side_score(child_board, color)
    bonus = (after - before) * _ORDER_SCORE_SCALE
    if (
        kind == PieceType.ROOK
        and _is_materially_down(board, color)
        and _move_checks_opponent(child_board, color)
        and not _move_targets_enemy_passer_file(board, color, move)
    ):
        bonus -= _WORSE_SIDE_CHECK_DRIFT_PENALTY
    return bonus


def _rook_endgame_side_score(board: Board, color: Color) -> int:
    rooks = rook_positions(board, color)
    if not rooks:
        return 0
    own_passers = passed_pawns_for_color(board, color)
    enemy_color = _opponent(color)
    enemy_passers = passed_pawns_for_color(board, enemy_color)
    if not own_passers and not enemy_passers:
        return 0
    score = 0
    for rook in rooks:
        score += _rook_passer_alignment_score(board, color, rook, own_passers)
        score += _rook_defensive_alignment_score(board, color, rook, enemy_passers)
        if _rook_is_passive(rook, own_passers, enemy_passers):
            score -= _PASSIVE_ROOK_PENALTY
    score += _king_support_score(board, color, own_passers)
    score += _outside_passer_activity_score(board, color, rooks)
    return score


def _rook_passer_alignment_score(
    board: Board,
    color: Color,
    rook: tuple[int, int],
    own_passers: list[tuple[int, int]],
) -> int:
    rook_row, rook_col = rook
    score = 0
    for pawn_row, pawn_col in own_passers:
        if not is_advanced_passer(color, pawn_row) or rook_col != pawn_col:
            continue
        if not path_clear_between(board, rook, (pawn_row, pawn_col)):
            continue
        if _is_behind_pawn(color, rook_row, pawn_row):
            score += _ROOK_BEHIND_OWN_PASSER_BONUS
        else:
            score -= _ROOK_IN_FRONT_OF_PASSER_PENALTY
    return score


def _rook_defensive_alignment_score(
    board: Board,
    color: Color,
    rook: tuple[int, int],
    enemy_passers: list[tuple[int, int]],
) -> int:
    rook_row, rook_col = rook
    score = 0
    for pawn_row, pawn_col in enemy_passers:
        enemy_color = _opponent(color)
        if not is_advanced_passer(enemy_color, pawn_row) or rook_col != pawn_col:
            continue
        if not path_clear_between(board, rook, (pawn_row, pawn_col)):
            continue
        if _is_in_front_of_pawn(enemy_color, rook_row, pawn_row):
            score += _ROOK_IN_FRONT_OF_ENEMY_PASSER_BONUS
        elif _is_behind_pawn(enemy_color, rook_row, pawn_row):
            score += _ROOK_BEHIND_ENEMY_PASSER_BONUS
        else:
            score -= _ROOK_IN_FRONT_OF_PASSER_PENALTY
    return score


def _king_support_score(board: Board, color: Color, own_passers: list[tuple[int, int]]) -> int:
    if not own_passers:
        return 0
    own_king = board.find_king(color)
    enemy_king = board.find_king(_opponent(color))
    if own_king is None or enemy_king is None:
        return 0
    own_position = (int(own_king.row), int(own_king.col))
    enemy_position = (int(enemy_king.row), int(enemy_king.col))
    score = 0
    for pawn_row, pawn_col in own_passers:
        if not is_advanced_passer(color, pawn_row):
            continue
        own_distance = _king_distance(own_position, (pawn_row, pawn_col))
        enemy_distance = _king_distance(enemy_position, (pawn_row, pawn_col))
        if own_distance + 1 < enemy_distance:
            score += _KING_SUPPORTS_PASSER_BONUS
    return score


def _outside_passer_activity_score(
    board: Board,
    color: Color,
    rooks: list[tuple[int, int]],
) -> int:
    profile = structure_profile(board).side(color)
    if not profile.outside_passed_files:
        return 0
    enemy_king = board.find_king(_opponent(color))
    if enemy_king is None:
        return 0
    enemy_position = (int(enemy_king.row), int(enemy_king.col))
    for rook in rooks:
        if rook[1] in profile.outside_passed_files:
            return _OUTSIDE_PASSER_ACTIVITY_BONUS
        if _king_distance(rook, enemy_position) <= 3:
            return _OUTSIDE_PASSER_ACTIVITY_BONUS
    return 0


def _rook_is_passive(
    rook: tuple[int, int],
    own_passers: list[tuple[int, int]],
    enemy_passers: list[tuple[int, int]],
) -> bool:
    rook_row, rook_col = rook
    advanced_files = {
        pawn_col
        for pawn_row, pawn_col in own_passers + enemy_passers
        if pawn_row <= 3 or pawn_row >= 4
    }
    if not advanced_files:
        return False
    return rook_col not in advanced_files and rook_row in {0, 7}


def _is_relevant_rook_endgame(board: Board) -> bool:
    non_king_pieces = non_king_piece_kinds(board)
    if not non_king_pieces or any(
        kind not in {PieceType.ROOK, PieceType.PAWN} for kind in non_king_pieces
    ):
        return False
    return any(kind == PieceType.ROOK for kind in non_king_pieces)


def _is_behind_pawn(color: Color, rook_row: int, pawn_row: int) -> bool:
    return rook_row > pawn_row if color == Color.WHITE else rook_row < pawn_row


def _is_in_front_of_pawn(color: Color, rook_row: int, pawn_row: int) -> bool:
    return rook_row < pawn_row if color == Color.WHITE else rook_row > pawn_row


def _king_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _is_materially_down(board: Board, color: Color) -> bool:
    return simple_material_balance(board, color) < 0


def _move_checks_opponent(board: Board, color: Color) -> bool:
    return is_in_check(board, _opponent(color))


def _move_targets_enemy_passer_file(board: Board, color: Color, move: Move) -> bool:
    enemy_passers = passed_pawns_for_color(board, _opponent(color))
    return any(int(move.end.col) == pawn_col for _, pawn_col in enemy_passers)


def rook_positions(board: Board, color: Color) -> list[tuple[int, int]]:
    """Return rook coordinates for the given color."""

    return [
        (row, col)
        for piece, row, col in iter_color_pieces(board, color)
        if piece.kind == PieceType.ROOK
    ]

def simple_material_balance(board: Board, color: Color) -> int:
    """Return a simple rook+pawn material balance from the given side's view."""

    weighted_pieces = [
        (piece.color, 5 if piece.kind == PieceType.ROOK else 1)
        for row in board.board
        for piece in row
        if piece is not None and piece.kind != PieceType.KING
    ]
    own_material = sum(value for piece_color, value in weighted_pieces if piece_color == color)
    enemy_material = sum(value for piece_color, value in weighted_pieces if piece_color != color)
    return own_material - enemy_material


def _opponent(color: Color) -> Color:
    return opposite_color(color)
