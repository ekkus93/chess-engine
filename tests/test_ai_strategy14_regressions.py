"""Regression coverage for STRATEGY14 middlegame stability work."""

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


def _attack_position_board() -> Board:
    """Middlegame where White's rook at d3 can invade to d8 (connecting with h8 rook).

    White: King g1, Queen d1, Rooks h8 and d3, Bishop c4, Knights c3/f3,
           Pawns a2/b2/c2/d4/e4/f2/g2/h2.

    White's h8 rook has already invaded Black's back rank.  Invading with
    the d3 rook to d8 connects the two White rooks on rank 8 (via the clear
    e8-f8-g8 path) and threatens the uncastled Black king on e8.  Retreating
    to d2 leaves the rooks unconnected and is positionally passive.

    Black: King e8 (uncastled), Queen c8, Rook a8, Bishops c5/f8,
           Knights c6/f6, standard pawn structure.
    """
    return _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("h8", Color.WHITE, PieceType.ROOK),
            ("d3", Color.WHITE, PieceType.ROOK),
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
            ("c8", Color.BLACK, PieceType.QUEEN),
            ("a8", Color.BLACK, PieceType.ROOK),
            ("c5", Color.BLACK, PieceType.BISHOP),
            ("f8", Color.BLACK, PieceType.BISHOP),
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
        turn=Color.WHITE,
    )


def _consolidation_position_board() -> Board:
    """Middlegame where Black's rook at f8 should consolidate to d8.

    The Black bishop at e8 blocks the a8-f8 connection along rank 8, but
    once the f8 rook moves to d8 (left of the bishop), the two rooks a8
    and d8 connect.  Moving the king from g8 to f7 instead leaves the rooks
    disconnected and exposes the king.

    White: same attacking setup as _attack_position_board with rook at d3.
    Black: King g8 (castled), Queen c8, Rooks a8/f8, Bishop e8 (critical
           blocker), Bishop c5, Knights c6/f6, standard pawn structure.
    """
    return _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("h8", Color.WHITE, PieceType.ROOK),
            ("d3", Color.WHITE, PieceType.ROOK),
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
            ("c8", Color.BLACK, PieceType.QUEEN),
            ("a8", Color.BLACK, PieceType.ROOK),
            ("f8", Color.BLACK, PieceType.ROOK),
            ("e8", Color.BLACK, PieceType.BISHOP),
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
    """White should prefer the rook invasion that connects rooks on the back rank."""

    board = _attack_position_board()
    invasion = Move(start=sq("d3"), end=sq("d8"))
    retreat = Move(start=sq("d3"), end=sq("d2"))
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
    """Black should prefer rook consolidation that connects rooks over an exposed king walk."""

    board = _consolidation_position_board()
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

    board = _attack_position_board()
    active_child = board.clone()
    passive_child = board.clone()
    assert active_child.apply_legal_move(sq("d3"), sq("d8")) is True
    assert passive_child.apply_legal_move(sq("d3"), sq("d2")) is True

    active = get_evaluation_breakdown(active_child)
    passive = get_evaluation_breakdown(passive_child)
    assert "middlegame_practicality" in active
    assert active["middlegame_practicality"] > passive["middlegame_practicality"]
