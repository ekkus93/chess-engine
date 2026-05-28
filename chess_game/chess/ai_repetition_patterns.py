"""Helpers for discouraging low-value repetition and quiet shuffling."""

from __future__ import annotations
from typing import cast

from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import is_capture_move
from chess_game.chess.types import PieceType

QUIET_UNDO_MOVE_PENALTY = 64
QUIET_HEAVY_UNDO_MOVE_PENALTY = 28
ROOT_UNDO_MOVE_PENALTY = 96
ROOT_HEAVY_UNDO_MOVE_PENALTY = 48
ROOT_REPEATED_POSITION_PENALTY = 72
ROOT_SIMPLE_ENDGAME_REPEAT_PENALTY = 128


def quiet_cycle_penalty(board: Board, move: Move, kind: PieceType) -> int:
    """Return a quiet-order penalty for immediate short-cycle reversals."""

    if move.promotion is not None or is_capture_move(board, move):
        return 0
    if not move_undoes_last_own_move(board, move):
        return 0
    penalty = QUIET_UNDO_MOVE_PENALTY
    if kind in {PieceType.KING, PieceType.ROOK, PieceType.QUEEN}:
        penalty += QUIET_HEAVY_UNDO_MOVE_PENALTY
    return penalty


def root_cycle_penalty(
    board: Board,
    move: Move,
    kind: PieceType,
    repeated_position_count: int,
    simple_endgame: bool,
) -> int:
    """Return a root tie-break penalty for repetition-prone moves."""

    penalty = 0
    if repeated_position_count > 0:
        penalty += ROOT_REPEATED_POSITION_PENALTY * repeated_position_count
    if move_undoes_last_own_move(board, move):
        penalty += ROOT_UNDO_MOVE_PENALTY
        if kind in {PieceType.KING, PieceType.ROOK, PieceType.QUEEN}:
            penalty += ROOT_HEAVY_UNDO_MOVE_PENALTY
    if penalty > 0 and simple_endgame:
        penalty += ROOT_SIMPLE_ENDGAME_REPEAT_PENALTY
    return penalty


def move_undoes_last_own_move(board: Board, move: Move) -> bool:
    """Return True when the candidate directly reverses the side's last move."""

    last_own_move = _last_own_move(board)
    if last_own_move is None:
        return False
    start, end, promotion = last_own_move
    return (
        move.start == end
        and move.end == start
        and move.promotion == promotion
    )


def _last_own_move(board: Board) -> tuple[object, object, PieceType | None] | None:
    history = _move_history(board)
    if len(history) < 2:
        return None
    return history[-2]


def _move_history(board: Board) -> list[tuple[object, object, PieceType | None]]:
    history_copy = getattr(board, "_move_history_copy", None)
    if callable(history_copy):
        return cast(list[tuple[object, object, PieceType | None]], history_copy())
    return []
