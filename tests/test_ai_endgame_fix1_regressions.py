"""Regression coverage for ENDGAME_FIX1 endgame-defense improvements."""

from __future__ import annotations

import pytest

from chess_game.chess import ai
from chess_game.chess.ai import (
    _root_stability_adjustment,
    get_best_move,
    get_evaluation_breakdown,
    position_key,
)
from chess_game.chess.ai_search_helpers import RepetitionPolicy, repetition_score
from chess_game.chess.board import Board, create_piece
from chess_game.chess.move import Move
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq
from tests.test_ai_quality import _move_order_score

pytestmark = pytest.mark.slow


def _board_from_transcript_snapshot(
    pieces: list[tuple[str, Color, PieceType]],
    turn: Color,
) -> Board:
    board = Board()
    board.clear_board()
    for square, color, kind in pieces:
        board.set_piece(sq(square), create_piece(color, kind))
    board.turn = turn
    return board


def _move_101_snapshot_board() -> Board:
    """Black to move from the late full-game snapshot after White promotes."""

    return _board_from_transcript_snapshot(
        [
            ("d8", Color.WHITE, PieceType.QUEEN),
            ("a7", Color.WHITE, PieceType.KNIGHT),
            ("c7", Color.WHITE, PieceType.PAWN),
            ("g6", Color.BLACK, PieceType.KING),
            ("a5", Color.WHITE, PieceType.PAWN),
            ("h4", Color.WHITE, PieceType.PAWN),
            ("f3", Color.BLACK, PieceType.PAWN),
            ("g3", Color.WHITE, PieceType.PAWN),
            ("f2", Color.WHITE, PieceType.PAWN),
            ("g1", Color.WHITE, PieceType.KING),
        ],
        turn=Color.BLACK,
    )


def _active_king_defense_board() -> Board:
    return _board_from_transcript_snapshot(
        [
            ("d5", Color.WHITE, PieceType.KING),
            ("g5", Color.WHITE, PieceType.PAWN),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("e7", Color.BLACK, PieceType.KING),
            ("d6", Color.BLACK, PieceType.BISHOP),
        ],
        turn=Color.BLACK,
    )


def _blockade_hold_board() -> Board:
    return _board_from_transcript_snapshot(
        [
            ("b6", Color.WHITE, PieceType.KING),
            ("a6", Color.WHITE, PieceType.PAWN),
            ("f1", Color.WHITE, PieceType.BISHOP),
            ("b8", Color.BLACK, PieceType.KING),
            ("c6", Color.BLACK, PieceType.BISHOP),
        ],
        turn=Color.BLACK,
    )


def _checking_hold_board() -> Board:
    return _board_from_transcript_snapshot(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("d5", Color.WHITE, PieceType.PAWN),
            ("f7", Color.BLACK, PieceType.KING),
            ("g8", Color.BLACK, PieceType.ROOK),
        ],
        turn=Color.BLACK,
    )


def _repeat_position_board() -> Board:
    return _board_from_transcript_snapshot(
        [
            ("f2", Color.WHITE, PieceType.KING),
            ("f4", Color.WHITE, PieceType.QUEEN),
            ("g8", Color.BLACK, PieceType.KING),
            ("g7", Color.BLACK, PieceType.ROOK),
        ],
        turn=Color.WHITE,
    )


def test_endgame_fix1_snapshot_helper_reconstructs_target_position() -> None:
    """Transcript snapshot helper should reconstruct the target endgame position."""
    board = _move_101_snapshot_board()

    assert board.turn == Color.BLACK
    assert board.get_piece(sq("d8")) is not None
    assert board.get_piece(sq("g6")) is not None


def test_endgame_fix1_prefers_snapshot_containment_step_over_shuffle() -> None:
    """Emergency heuristics should score containment king steps above h-file drift."""
    board = _move_101_snapshot_board()
    active_king = Move(start=sq("g6"), end=sq("f7"))
    bishop_shuffle = Move(start=sq("g6"), end=sq("h6"))
    active_child = board.clone()
    passive_child = board.clone()
    assert active_child.apply_legal_move(active_king.start, active_king.end) is True
    assert passive_child.apply_legal_move(bishop_shuffle.start, bishop_shuffle.end) is True

    assert _move_order_score(board, active_king, None) > _move_order_score(
        board,
        bishop_shuffle,
        None,
    )
    assert _root_stability_adjustment(
        board,
        active_king,
        active_child,
    ) < _root_stability_adjustment(
        board,
        bishop_shuffle,
        passive_child,
    )


def test_endgame_fix1_prefers_blockade_hold_over_bishop_drift() -> None:
    """Emergency heuristics should reward blockade plans over bishop theater drift."""
    board = _blockade_hold_board()
    hold = Move(start=sq("c6"), end=sq("a8"))
    drift = Move(start=sq("c6"), end=sq("e4"))
    hold_child = board.clone()
    drift_child = board.clone()
    assert hold_child.apply_legal_move(hold.start, hold.end) is True
    assert drift_child.apply_legal_move(drift.start, drift.end) is True

    assert _move_order_score(board, hold, None) > _move_order_score(board, drift, None)
    assert _root_stability_adjustment(board, hold, hold_child) < _root_stability_adjustment(
        board,
        drift,
        drift_child,
    )


def test_endgame_fix1_order_prefers_containment_king_step_over_shuffle() -> None:
    """Quiet ordering should prefer containment king steps over passive shuffles."""
    board = _move_101_snapshot_board()
    active_hold = Move(start=sq("g6"), end=sq("f7"))
    passive_shuffle = Move(start=sq("g6"), end=sq("h6"))

    assert _move_order_score(board, active_hold, None) > _move_order_score(
        board,
        passive_shuffle,
        None,
    )


def test_endgame_fix1_replaces_transcript_king_shuffle_with_active_hold() -> None:
    """Depth-3 search should avoid the old h-file king shuffle in the target snapshot."""
    board = _move_101_snapshot_board()

    best_move = get_best_move(board, depth=3)
    assert best_move.start == sq("g6")
    assert best_move.end in {sq("f7"), sq("g7"), sq("h7")}


def test_endgame_fix1_order_prefers_active_king_over_bishop_shuffle() -> None:
    """Move ordering should keep the snapshot containment step above king shuffle drift."""
    board = _move_101_snapshot_board()
    active_king = Move(start=sq("g6"), end=sq("f7"))
    bishop_shuffle = Move(start=sq("g6"), end=sq("h6"))

    assert _move_order_score(board, active_king, None) > _move_order_score(
        board,
        bishop_shuffle,
        None,
    )


def test_endgame_fix1_root_prefers_blockade_hold_over_drift() -> None:
    """Root tie-breaks should demote blockade drift in worse-side defensive holds."""
    board = _blockade_hold_board()
    hold = Move(start=sq("c6"), end=sq("a8"))
    drift = Move(start=sq("c6"), end=sq("e4"))
    hold_child = board.clone()
    drift_child = board.clone()
    assert hold_child.apply_legal_move(hold.start, hold.end) is True
    assert drift_child.apply_legal_move(drift.start, drift.end) is True

    assert _root_stability_adjustment(
        board,
        hold,
        hold_child,
    ) < _root_stability_adjustment(
        board,
        drift,
        drift_child,
    )


def test_endgame_fix1_breakdown_exposes_defensive_components() -> None:
    """Evaluation breakdown should expose and differentiate new defensive components."""
    board = _blockade_hold_board()
    active_child = board.clone()
    passive_child = board.clone()
    assert active_child.apply_legal_move(sq("c6"), sq("a8")) is True
    assert passive_child.apply_legal_move(sq("c6"), sq("e4")) is True

    active = get_evaluation_breakdown(active_child)
    passive = get_evaluation_breakdown(passive_child)
    assert "defensive_king_danger" in active
    assert "holdability" in active
    assert active["defensive_king_danger"] <= passive["defensive_king_danger"]
    assert active["holdability"] <= passive["holdability"]
    assert (
        active["defensive_king_danger"] != 0
        or active["holdability"] != 0
        or passive["defensive_king_danger"] != 0
        or passive["holdability"] != 0
    )


def test_endgame_fix1_repetition_penalizes_better_side_draw() -> None:
    """Repetition policy should still penalize draw loops for the better side."""
    board = _repeat_position_board()
    policy = RepetitionPolicy(
        position_key=position_key,
        evaluate=ai.evaluate,
        progress=lambda _board: 0,
        threshold=120,
        progress_threshold=24,
        penalty=32,
    )
    key = position_key(board)
    score = repetition_score(board, None, (key, key, key), policy)
    assert score is not None and score < 0


def test_endgame_fix1_repetition_favors_worse_side_draw() -> None:
    """Repetition policy should still reward draw loops for the worse side."""
    board = _repeat_position_board()
    policy = RepetitionPolicy(
        position_key=position_key,
        evaluate=ai.evaluate,
        progress=lambda _board: 0,
        threshold=120,
        progress_threshold=24,
        penalty=32,
    )
    board.turn = Color.BLACK
    key = position_key(board)
    score = repetition_score(board, None, (key, key, key), policy)
    assert score is not None and score > 0
