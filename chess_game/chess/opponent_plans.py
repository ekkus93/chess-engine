"""Lightweight heuristics for the opponent's most dangerous near-term plan."""

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.constants import KNIGHT_MOVE_OFFSETS
from chess_game.chess.defensive_priorities import open_heavy_invasion_lines
from chess_game.chess.strategy_utils import (
    is_passed_pawn,
    iter_color_pieces,
    king_coordinates,
    path_clear_between,
)
from chess_game.chess.types import Color, PieceType


@dataclass(frozen=True)
class OpponentPlanProfile:
    """Summarize the opponent's immediate strategic threats against one side."""

    invasion_lines: int
    knight_jumps: int
    pawn_breaks: int
    checking_resources: int
    passed_pawn_pushes: int

    @property
    def pressure(self) -> int:
        """Return a weighted pressure score for near-term enemy plans."""

        return (
            self.invasion_lines * 3
            + self.knight_jumps * 2
            + self.pawn_breaks * 3
            + self.checking_resources * 2
            + self.passed_pawn_pushes * 2
        )


def opponent_plan_profile(board: Board, color: Color) -> OpponentPlanProfile:
    """Return the enemy's near-term plan pressure against one color."""

    return OpponentPlanProfile(
        invasion_lines=open_heavy_invasion_lines(board, color),
        knight_jumps=_knight_jump_threats(board, color),
        pawn_breaks=_pawn_break_threats(board, color),
        checking_resources=_checking_resources(board, color),
        passed_pawn_pushes=_passed_pawn_push_threats(board, color),
    )


def _knight_jump_threats(board: Board, color: Color) -> int:
    king_position = king_coordinates(board, color)
    if king_position is None:
        return 0
    king_row, king_col = king_position
    enemy_color = _opponent(color)
    return sum(
        1
        for _, row_index, col_index in iter_color_pieces(board, enemy_color)
        for target_row, target_col in _knight_targets(row_index, col_index)
        if 0 <= target_row < 8
        and 0 <= target_col < 8
        and board.board[target_row][target_col] is None
        and max(abs(target_row - king_row), abs(target_col - king_col)) <= 2
    )


def _pawn_break_threats(board: Board, color: Color) -> int:
    enemy_color = _opponent(color)
    friendly_pawns = [
        (row_index, col_index)
        for piece, row_index, col_index in iter_color_pieces(board, color)
        if piece.kind == PieceType.PAWN
    ]
    king_position = king_coordinates(board, color)
    king_row = -10 if king_position is None else king_position[0]
    king_col = -10 if king_position is None else king_position[1]
    threats = 0
    for _, row_index, col_index in iter_color_pieces(board, enemy_color):
        if col_index not in {2, 3, 4, 5}:
            continue
        next_row = row_index + _pawn_direction(enemy_color)
        if not 0 <= next_row < 8 or board.board[next_row][col_index] is not None:
            continue
        destination = (next_row, col_index)
        if _push_hits_pawn_chain(destination, friendly_pawns) or max(
            abs(next_row - king_row),
            abs(col_index - king_col),
        ) <= 3:
            threats += 1
    return threats


def _checking_resources(board: Board, color: Color) -> int:
    king_position = king_coordinates(board, color)
    if king_position is None:
        return 0
    king_row, king_col = king_position
    enemy_color = _opponent(color)
    checks = 0
    for piece, row_index, col_index in iter_color_pieces(board, enemy_color):
        if piece.kind in {PieceType.QUEEN, PieceType.ROOK} and (
            row_index == king_row or col_index == king_col
        ):
            if path_clear_between(board, (row_index, col_index), (king_row, king_col)):
                checks += 1
        if piece.kind == PieceType.QUEEN and max(
            abs(row_index - king_row),
            abs(col_index - king_col),
        ) <= 2:
            checks += 1
    return checks


def _passed_pawn_push_threats(board: Board, color: Color) -> int:
    enemy_color = _opponent(color)
    friendly_pawns = [
        (row_index, col_index)
        for piece, row_index, col_index in iter_color_pieces(board, color)
        if piece.kind == PieceType.PAWN
    ]
    threats = 0
    for _, row_index, col_index in iter_color_pieces(board, enemy_color):
        if not is_passed_pawn(enemy_color, row_index, col_index, friendly_pawns):
            continue
        next_row = row_index + _pawn_direction(enemy_color)
        if 0 <= next_row < 8 and board.board[next_row][col_index] is None:
            threats += 1
    return threats


def _push_hits_pawn_chain(
    destination: tuple[int, int],
    friendly_pawns: list[tuple[int, int]],
) -> bool:
    target_row, target_col = destination
    return any(
        abs(friendly_row - target_row) <= 1 and abs(friendly_col - target_col) <= 1
        for friendly_row, friendly_col in friendly_pawns
    )


def _knight_targets(row: int, col: int) -> list[tuple[int, int]]:
    return [
        (row + row_delta, col + col_delta)
        for row_delta, col_delta in KNIGHT_MOVE_OFFSETS
    ]


def _opponent(color: Color) -> Color:
    return Color.BLACK if color == Color.WHITE else Color.WHITE


def _pawn_direction(color: Color) -> int:
    return -1 if color == Color.WHITE else 1
