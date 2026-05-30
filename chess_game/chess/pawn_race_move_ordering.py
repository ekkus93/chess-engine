"""Quiet-order pawn-race tempo helpers."""

from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.passer_race_guidance import (
    explicit_pawn_race_tempo,
    is_pawn_race_tempo_position,
)
from chess_game.chess.strategy_utils import most_advanced_passer, passed_pawns_for_color
from chess_game.chess.types import Color, PieceType

_PAWN_RACE_MARGIN_BONUS = 16
_PAWN_RACE_PAWN_PUSH_BONUS = 14
_PAWN_RACE_BLOCK_BONUS = 18
_PAWN_RACE_KING_DRIFT_PENALTY = 14
_PAWN_RACE_KING_SUPPORT_BONUS = 9
_PAWN_RACE_KING_DISTANCE_PENALTY = 6


def pawn_race_move_bonus(board: Board, move: Move, side: Color) -> int:
    """Return a quiet-order bonus for side-to-move pawn-race tempo gains."""

    if not is_pawn_race_tempo_position(board):
        return 0
    piece = board.get_piece(move.start)
    if piece is None or piece.color != side:
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0

    before_margin = _tempo_margin_for_side(explicit_pawn_race_tempo(board), side)
    after_margin = _tempo_margin_for_side(explicit_pawn_race_tempo(child_board), side)
    if before_margin is None or after_margin is None:
        return 0

    bonus = (after_margin - before_margin) * _PAWN_RACE_MARGIN_BONUS
    if piece.kind == PieceType.PAWN and after_margin > before_margin:
        bonus += _PAWN_RACE_PAWN_PUSH_BONUS
    if piece.kind == PieceType.KING:
        bonus += _king_pawn_race_bonus(board, move, side, after_margin, before_margin)
    return bonus


def _king_pawn_race_bonus(
    board: Board,
    move: Move,
    side: Color,
    after_margin: int,
    before_margin: int,
) -> int:
    start = (int(move.start.row), int(move.start.col))
    end = (int(move.end.row), int(move.end.col))
    bonus = _own_pawn_support_bonus(board, side, start, end)
    bonus += _enemy_pawn_block_bonus(board, side, start, end)
    if after_margin > before_margin:
        bonus += _PAWN_RACE_BLOCK_BONUS
    elif after_margin < before_margin:
        bonus -= _PAWN_RACE_KING_DRIFT_PENALTY
    return bonus


def _own_pawn_support_bonus(
    board: Board,
    side: Color,
    start: tuple[int, int],
    end: tuple[int, int],
) -> int:
    own_passer = most_advanced_passer(side, passed_pawns_for_color(board, side))
    if own_passer is None:
        return 0
    own_promo = _promotion_square_for_side(side, own_passer[1])
    support_gain = _manhattan(start, own_promo) - _manhattan(end, own_promo)
    if support_gain > 0:
        return support_gain * _PAWN_RACE_KING_SUPPORT_BONUS
    if support_gain < 0:
        return support_gain * _PAWN_RACE_KING_DISTANCE_PENALTY
    return 0


def _enemy_pawn_block_bonus(
    board: Board,
    side: Color,
    start: tuple[int, int],
    end: tuple[int, int],
) -> int:
    enemy_side = Color.BLACK if side == Color.WHITE else Color.WHITE
    enemy_passer = most_advanced_passer(
        enemy_side,
        passed_pawns_for_color(board, enemy_side),
    )
    if enemy_passer is None:
        return 0
    enemy_block = _block_square_for_side(enemy_side, enemy_passer)
    block_gain = _manhattan(start, enemy_block) - _manhattan(end, enemy_block)
    if block_gain > 0:
        return block_gain * _PAWN_RACE_BLOCK_BONUS
    if block_gain < 0:
        return block_gain * _PAWN_RACE_KING_DISTANCE_PENALTY
    return 0


def _tempo_margin_for_side(
    tempo_pair: tuple[int | None, int | None],
    side: Color,
) -> int | None:
    white_tempo, black_tempo = tempo_pair
    own = white_tempo if side == Color.WHITE else black_tempo
    enemy = black_tempo if side == Color.WHITE else white_tempo
    if own is None or enemy is None:
        return None
    return enemy - own


def _promotion_square_for_side(side: Color, col: int) -> tuple[int, int]:
    return (0, col) if side == Color.WHITE else (7, col)


def _block_square_for_side(side: Color, pawn: tuple[int, int]) -> tuple[int, int]:
    row_delta = -1 if side == Color.WHITE else 1
    return (pawn[0] + row_delta, pawn[1])


def _manhattan(start: tuple[int, int], end: tuple[int, int]) -> int:
    return abs(start[0] - end[0]) + abs(start[1] - end[1])
