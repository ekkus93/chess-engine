"""Regression coverage for STRATEGY14 middlegame stability work."""

from __future__ import annotations

from pathlib import Path

import pytest

from chess_game.chess.ai import get_evaluation_breakdown
from chess_game.chess.board import Board, create_piece
from chess_game.chess.middlegame_practicality_guidance import (
    middlegame_practicality_evaluation_score,
    middlegame_practicality_order_bonus,
    middlegame_practicality_root_bonus,
)
from chess_game.chess.move import Move, parse_move_notation
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


pytestmark = pytest.mark.slow

_TRANSCRIPT = Path(__file__).resolve().parents[1] / "tmp" / "middlegame_fix1_depth3_20260602T092000Z.txt"


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


def _transcript_board(move_number: int) -> Board:
    board = Board()
    for line in _TRANSCRIPT.read_text().splitlines():
        if not line.startswith("Move ") or " plays " not in line:
            continue
        current_move = int(line.split(":", 1)[0].split()[1])
        move = parse_move_notation(line.split(" plays ", 1)[1].strip())
        assert board.make_move(move.start, move.end, promotion=move.promotion) is True
        if current_move == move_number:
            return board
    raise AssertionError(f"Move {move_number} not found in {_TRANSCRIPT}")


def _full_middlegame_board() -> Board:
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


def test_strategy14_white_prefers_rook_invasion_over_retreat_in_transcript_position() -> None:
    """White should prefer the rook invasion from the actual winning attack position."""

    board = _transcript_board(44)
    invasion = Move(start=sq("d3"), end=sq("d8"))
    retreat = Move(start=sq("d3"), end=sq("d1"))
    invasion_child = board.clone()
    retreat_child = board.clone()
    assert invasion_child.apply_legal_move(invasion.start, invasion.end) is True
    assert retreat_child.apply_legal_move(retreat.start, retreat.end) is True

    assert middlegame_practicality_order_bonus(board, Color.WHITE, invasion) > middlegame_practicality_order_bonus(
        board,
        Color.WHITE,
        retreat,
    )
    assert middlegame_practicality_root_bonus(board, invasion, invasion_child, Color.WHITE) > middlegame_practicality_root_bonus(
        board,
        retreat,
        retreat_child,
        Color.WHITE,
    )
    assert middlegame_practicality_evaluation_score(invasion_child) > middlegame_practicality_evaluation_score(
        retreat_child,
    )
    assert get_evaluation_breakdown(invasion_child)["middlegame_practicality"] > get_evaluation_breakdown(
        retreat_child,
    )["middlegame_practicality"]


def test_strategy14_black_prefers_consolidation_over_king_walk_in_transcript_position() -> None:
    """Black should prefer practical consolidation after White's invasion appears."""

    board = _transcript_board(45)
    rook_consolidation = Move(start=sq("f8"), end=sq("d8"))
    king_walk = Move(start=sq("g8"), end=sq("f7"))
    consolidation_child = board.clone()
    king_walk_child = board.clone()
    assert consolidation_child.apply_legal_move(rook_consolidation.start, rook_consolidation.end) is True
    assert king_walk_child.apply_legal_move(king_walk.start, king_walk.end) is True

    assert middlegame_practicality_order_bonus(board, Color.BLACK, rook_consolidation) > middlegame_practicality_order_bonus(
        board,
        Color.BLACK,
        king_walk,
    )
    assert middlegame_practicality_root_bonus(
        board,
        rook_consolidation,
        consolidation_child,
        Color.BLACK,
    ) > middlegame_practicality_root_bonus(
        board,
        king_walk,
        king_walk_child,
        Color.BLACK,
    )
    assert middlegame_practicality_evaluation_score(consolidation_child) < middlegame_practicality_evaluation_score(
        king_walk_child,
    )


def test_strategy14_black_prefers_castling_over_queen_drift_in_full_middlegame_board() -> None:
    """Black should prefer castling over a passive queen step in a full middlegame."""

    board = _full_middlegame_board()
    castle = Move(start=sq("e8"), end=sq("g8"))
    drift = Move(start=sq("d8"), end=sq("d7"))
    castle_child = board.clone()
    drift_child = board.clone()
    assert castle_child.apply_legal_move(castle.start, castle.end) is True
    assert drift_child.apply_legal_move(drift.start, drift.end) is True

    assert middlegame_practicality_order_bonus(board, Color.BLACK, castle) > middlegame_practicality_order_bonus(
        board,
        Color.BLACK,
        drift,
    )
    assert middlegame_practicality_root_bonus(board, castle, castle_child, Color.BLACK) > middlegame_practicality_root_bonus(
        board,
        drift,
        drift_child,
        Color.BLACK,
    )


def test_strategy14_white_prefers_king_safety_over_waiting_in_full_middlegame_board() -> None:
    """White should choose king safety over a waiting pawn move when under pressure."""

    board = _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("h2", Color.WHITE, PieceType.ROOK),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("c3", Color.WHITE, PieceType.KNIGHT),
            ("f3", Color.WHITE, PieceType.KNIGHT),
            ("a2", Color.WHITE, PieceType.PAWN),
            ("b2", Color.WHITE, PieceType.PAWN),
            ("c2", Color.WHITE, PieceType.PAWN),
            ("d4", Color.WHITE, PieceType.PAWN),
            ("e4", Color.WHITE, PieceType.PAWN),
            ("f2", Color.WHITE, PieceType.PAWN),
            ("g3", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("e5", Color.BLACK, PieceType.KING),
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
        turn=Color.WHITE,
    )
    king_step = Move(start=sq("g2"), end=sq("f2"))
    waiting = Move(start=sq("a2"), end=sq("a3"))

    assert middlegame_practicality_order_bonus(board, Color.WHITE, king_step) > middlegame_practicality_order_bonus(
        board,
        Color.WHITE,
        waiting,
    )


def test_strategy14_breakdown_surfaces_middlegame_practicality_in_attack_position() -> None:
    """The evaluation breakdown should surface the new practical middlegame signal."""

    board = _transcript_board(44)
    active_child = board.clone()
    passive_child = board.clone()
    assert active_child.apply_legal_move(sq("d3"), sq("d8")) is True
    assert passive_child.apply_legal_move(sq("d3"), sq("d1")) is True

    active = get_evaluation_breakdown(active_child)
    passive = get_evaluation_breakdown(passive_child)
    assert "middlegame_practicality" in active
    assert active["middlegame_practicality"] > passive["middlegame_practicality"]
