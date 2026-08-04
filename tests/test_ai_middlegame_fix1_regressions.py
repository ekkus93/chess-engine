"""Regression coverage for MIDDLEGAME_FIX1 middlegame improvements."""

from __future__ import annotations

import pytest

from chess_game.chess.ai import get_evaluation_breakdown
from chess_game.chess.board import Board, create_piece
from chess_game.chess.middlegame_practicality_guidance import (
    middlegame_practicality_evaluation_score,
    middlegame_practicality_order_bonus,
    middlegame_practicality_root_bonus,
)
from chess_game.chess.move import Move
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq
from tests.test_ai_quality import _move_order_score

pytestmark = pytest.mark.slow


def _build_board(
    pieces: list[tuple[str, Color, PieceType]],
    turn: Color,
) -> Board:
    board = Board()
    board.clear_board()
    for square, color, kind in pieces:
        board.set_piece(sq(square), create_piece(color, kind))
    board.turn = turn
    return board


def _development_board() -> Board:
    return _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("c3", Color.WHITE, PieceType.KNIGHT),
            ("f3", Color.WHITE, PieceType.KNIGHT),
            ("a2", Color.WHITE, PieceType.PAWN),
            ("b2", Color.WHITE, PieceType.PAWN),
            ("c2", Color.WHITE, PieceType.PAWN),
            ("d4", Color.WHITE, PieceType.PAWN),
            ("e4", Color.WHITE, PieceType.PAWN),
            ("f2", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("a8", Color.BLACK, PieceType.ROOK),
            ("h8", Color.BLACK, PieceType.ROOK),
            ("c8", Color.BLACK, PieceType.BISHOP),
            ("b8", Color.BLACK, PieceType.KNIGHT),
            ("f6", Color.BLACK, PieceType.KNIGHT),
            ("a7", Color.BLACK, PieceType.PAWN),
            ("c7", Color.BLACK, PieceType.PAWN),
            ("d6", Color.BLACK, PieceType.PAWN),
            ("e6", Color.BLACK, PieceType.PAWN),
            ("f7", Color.BLACK, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.PAWN),
            ("h7", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )


def _castle_board() -> Board:
    return _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("c3", Color.WHITE, PieceType.KNIGHT),
            ("f3", Color.WHITE, PieceType.KNIGHT),
            ("a2", Color.WHITE, PieceType.PAWN),
            ("b2", Color.WHITE, PieceType.PAWN),
            ("c2", Color.WHITE, PieceType.PAWN),
            ("d4", Color.WHITE, PieceType.PAWN),
            ("e4", Color.WHITE, PieceType.PAWN),
            ("f2", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("e8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("a8", Color.BLACK, PieceType.ROOK),
            ("h8", Color.BLACK, PieceType.ROOK),
            ("c5", Color.BLACK, PieceType.BISHOP),
            ("c6", Color.BLACK, PieceType.KNIGHT),
            ("f6", Color.BLACK, PieceType.KNIGHT),
            ("a7", Color.BLACK, PieceType.PAWN),
            ("b7", Color.BLACK, PieceType.PAWN),
            ("c7", Color.BLACK, PieceType.PAWN),
            ("d6", Color.BLACK, PieceType.PAWN),
            ("e6", Color.BLACK, PieceType.PAWN),
            ("f7", Color.BLACK, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.PAWN),
            ("h7", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )


def _counterplay_board() -> Board:
    return _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("c3", Color.WHITE, PieceType.KNIGHT),
            ("f3", Color.WHITE, PieceType.KNIGHT),
            ("a2", Color.WHITE, PieceType.PAWN),
            ("b2", Color.WHITE, PieceType.PAWN),
            ("c2", Color.WHITE, PieceType.PAWN),
            ("d4", Color.WHITE, PieceType.PAWN),
            ("e4", Color.WHITE, PieceType.PAWN),
            ("f2", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("a8", Color.BLACK, PieceType.ROOK),
            ("h8", Color.BLACK, PieceType.ROOK),
            ("c5", Color.BLACK, PieceType.BISHOP),
            ("c6", Color.BLACK, PieceType.KNIGHT),
            ("f6", Color.BLACK, PieceType.KNIGHT),
            ("d6", Color.BLACK, PieceType.PAWN),
            ("e6", Color.BLACK, PieceType.PAWN),
            ("f7", Color.BLACK, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.PAWN),
            ("h7", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )


def test_middlegame_fix1_prefers_minor_development_over_rook_shuffle() -> None:
    """Practical middlegame ordering should finish development before drifting a rook."""

    board = _development_board()
    develop = Move(start=sq("b8"), end=sq("d7"))
    drift = Move(start=sq("a8"), end=sq("a6"))

    assert middlegame_practicality_order_bonus(board, Color.BLACK, develop) > middlegame_practicality_order_bonus(
        board,
        Color.BLACK,
        drift,
    )
    assert _move_order_score(board, develop, None) > _move_order_score(board, drift, None)


def test_middlegame_fix1_prefers_castling_over_queen_drift() -> None:
    """Middlegame king safety should reward castling over a quiet queen step."""

    board = _castle_board()
    castle = Move(start=sq("e8"), end=sq("g8"))
    drift = Move(start=sq("d8"), end=sq("d7"))

    assert middlegame_practicality_order_bonus(board, Color.BLACK, castle) > middlegame_practicality_order_bonus(
        board,
        Color.BLACK,
        drift,
    )
    assert _move_order_score(board, castle, None) > _move_order_score(board, drift, None)


def test_middlegame_fix1_prefers_central_break_over_waiting() -> None:
    """Counterplay should prefer a central pawn break over a quiet rook shuffle."""

    board = _counterplay_board()
    break_move = Move(start=sq("d6"), end=sq("d5"))
    waiting = Move(start=sq("a8"), end=sq("a6"))

    assert middlegame_practicality_order_bonus(board, Color.BLACK, break_move) > middlegame_practicality_order_bonus(
        board,
        Color.BLACK,
        waiting,
    )
    assert _move_order_score(board, break_move, None) > _move_order_score(board, waiting, None)


def test_middlegame_fix1_breakdown_exposes_middlegame_practicality() -> None:
    """Evaluation breakdown should surface the new middlegame signal."""

    board = _counterplay_board()
    active_child = board.clone()
    passive_child = board.clone()
    assert active_child.apply_legal_move(sq("d6"), sq("d5")) is True
    assert passive_child.apply_legal_move(sq("a8"), sq("a6")) is True

    active = get_evaluation_breakdown(active_child)
    passive = get_evaluation_breakdown(passive_child)
    assert "middlegame_practicality" in active
    assert active["middlegame_practicality"] < passive["middlegame_practicality"]


def test_middlegame_fix1_evaluation_scores_active_plan_higher() -> None:
    """The direct middlegame evaluator should prefer active development and king safety."""

    board = _castle_board()
    active_child = board.clone()
    passive_child = board.clone()
    assert active_child.apply_legal_move(sq("e8"), sq("g8")) is True
    assert passive_child.apply_legal_move(sq("d8"), sq("d7")) is True

    assert middlegame_practicality_evaluation_score(active_child) < middlegame_practicality_evaluation_score(
        passive_child,
    )


@pytest.mark.slow
def test_middlegame_fix1_root_prefers_castling_in_obvious_position() -> None:
    """A clear middlegame castle should outrank a passive queen drift at the root."""

    board = _castle_board()
    castle = Move(start=sq("e8"), end=sq("g8"))
    drift = Move(start=sq("d8"), end=sq("d7"))
    castle_child = board.clone()
    drift_child = board.clone()
    assert castle_child.apply_legal_move(castle.start, castle.end) is True
    assert drift_child.apply_legal_move(drift.start, drift.end) is True

    assert middlegame_practicality_root_bonus(board, castle, castle_child, Color.BLACK) > middlegame_practicality_root_bonus(
        board,
        drift,
        drift_child,
        Color.BLACK,
    )
