"""Capture-order helpers shared by the main search module."""

from __future__ import annotations

from chess_game.chess.ai_search_helpers import defensive_capture_bonus
from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import is_capture_move
from chess_game.chess.structure_recognition import structure_capture_bonus
from chess_game.chess.types import Piece, PieceType

_VICTIM_VALUES = {
    PieceType.PAWN: 10,
    PieceType.KNIGHT: 30,
    PieceType.BISHOP: 32,
    PieceType.ROOK: 35,
    PieceType.QUEEN: 90,
}

_ATTACKER_VALUES = {
    PieceType.PAWN: 10,
    PieceType.KNIGHT: 30,
    PieceType.BISHOP: 32,
    PieceType.ROOK: 35,
    PieceType.QUEEN: 90,
}


def capture_order_score(
    board: Board,
    move: Move,
    make_copy_with_move,
) -> int:
    """Return capture ordering score using MVV/LVA plus structural priorities."""

    captured_piece = board.get_piece(move.end)
    attacker = board.get_piece(move.start)
    if attacker is None or captured_piece is None:
        return 900 if is_capture_move(board, move) else 0
    return (
        _mvv_lva_capture_score(attacker, captured_piece)
        + defensive_capture_bonus(
            board,
            move,
            captured_piece.kind,
            make_copy_with_move,
        )
        + structure_capture_bonus(
            board,
            attacker.color,
            attacker.kind,
            captured_piece.kind,
            move.end,
        )
    )


def _mvv_lva_capture_score(attacker: Piece, victim: Piece) -> int:
    """MVV/LVA score for a capture."""

    return (victim_value(victim.kind) * 1_000) - attacker_value(attacker.kind)


def victim_value(kind: PieceType) -> int:
    """Return the MVV/LVA victim priority value."""

    return _VICTIM_VALUES.get(kind, 0)


def attacker_value(kind: PieceType) -> int:
    """Return the MVV/LVA attacker priority value."""

    return _ATTACKER_VALUES.get(kind, 0)
