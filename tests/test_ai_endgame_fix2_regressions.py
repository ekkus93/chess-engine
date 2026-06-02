"""Regression coverage for ENDGAME_FIX2 endgame-defense refinements."""

from chess_game.chess.ai import get_evaluation_breakdown
from chess_game.chess import ai
from chess_game.chess.ai import position_key
from chess_game.chess.ai_search_helpers import RepetitionPolicy, repetition_score
from chess_game.chess.board import Board, create_piece
from chess_game.chess.endgame_emergency_defense import _emergency_context
from chess_game.chess.low_material_race_guidance import (
    endgame_race_context,
    endgame_race_order_bonus,
)
from chess_game.chess.rook_endgame_guidance import rook_endgame_order_bonus
from chess_game.chess.move import Move
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq
from tests.test_ai_quality import _move_order_score


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


def _rook_blockade_board() -> Board:
    return _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("d5", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
        ],
        turn=Color.BLACK,
    )


def _must_hold_board() -> Board:
    return _build_board(
        [
            ("e5", Color.WHITE, PieceType.KING),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("d7", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
        ],
        turn=Color.BLACK,
    )


def test_endgame_fix2_race_context_distinguishes_endgame_modes() -> None:
    """Race context should classify a winning race and a must-hold race."""

    converge_board = _rook_blockade_board()
    hold_board = _must_hold_board()

    converge_context = endgame_race_context(converge_board, Color.BLACK)
    hold_context = endgame_race_context(hold_board, Color.BLACK)

    assert converge_context is not None
    assert converge_context.mode == "must_converge"
    assert hold_context is not None
    assert hold_context.mode == "must_hold"


def test_endgame_fix2_prefers_exact_blockade_over_lateral_rook_drift() -> None:
    """The race evaluator should prefer file blockade over cosmetic rook drift."""

    board = _rook_blockade_board()
    exact_blockade = Move(start=sq("a8"), end=sq("d8"))
    lateral_drift = Move(start=sq("a8"), end=sq("a4"))

    assert endgame_race_order_bonus(board, Color.BLACK, PieceType.ROOK, exact_blockade) > endgame_race_order_bonus(
        board,
        Color.BLACK,
        PieceType.ROOK,
        lateral_drift,
    )
    assert rook_endgame_order_bonus(board, Color.BLACK, PieceType.ROOK, exact_blockade) > rook_endgame_order_bonus(
        board,
        Color.BLACK,
        PieceType.ROOK,
        lateral_drift,
    )


def test_endgame_fix2_exposes_race_score_in_evaluation_breakdown() -> None:
    """The evaluation breakdown should surface the new race signal."""

    board = _rook_blockade_board()
    exact_child = board.clone()
    drift_child = board.clone()
    assert exact_child.apply_legal_move(sq("a8"), sq("d8")) is True
    assert drift_child.apply_legal_move(sq("a8"), sq("a4")) is True

    exact = get_evaluation_breakdown(exact_child)
    drift = get_evaluation_breakdown(drift_child)
    assert "endgame_race" in exact
    assert exact["endgame_race"] > drift["endgame_race"]


def test_endgame_fix2_emergency_defense_prefers_blockade_king_step() -> None:
    """Emergency defense should activate only for a real must-hold promotion race."""

    board = _must_hold_board()
    hold_step = Move(start=sq("g7"), end=sq("f8"))
    drift_step = Move(start=sq("g7"), end=sq("h8"))
    hold_child = board.clone()
    drift_child = board.clone()
    assert hold_child.apply_legal_move(hold_step.start, hold_step.end) is True
    assert drift_child.apply_legal_move(drift_step.start, drift_step.end) is True

    assert _emergency_context(board, Color.BLACK) is not None
    assert _move_order_score(board, hold_step, None) > _move_order_score(
        board,
        drift_step,
        None,
    )
    assert get_evaluation_breakdown(hold_child)["endgame_race"] >= 0
    assert get_evaluation_breakdown(drift_child)["endgame_race"] >= 0


def test_endgame_fix2_repetition_keeps_a_practical_hold() -> None:
    """Repetition should still be a valid practical hold when the race is critical."""

    board = _must_hold_board()
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
    assert score is not None and score > 0
