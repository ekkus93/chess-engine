"""Transcript-driven regressions for STRATEGY6 opening-discipline cleanup."""

from chess_game.chess import ai
from chess_game.chess.ai import get_best_move
from chess_game.chess.board import Board
from chess_game.chess.types import LegalMove
from tests.helpers import sq
from tests.test_ai_quality import _move_order_score


def _board_from_moves(moves: list[tuple[str, str]]) -> Board:
    board = Board()
    for start, end in moves:
        board.make_move(sq(start), sq(end))
    return board


def test_strategy6_order_prefers_development_over_early_rc1_from_transcript() -> None:
    """The opening should score a normal kingside setup above the move-11 rook drift."""

    board = _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
        ]
    )

    develop = ai.Move(start=sq("g2"), end=sq("g3"))
    rook_drift = ai.Move(start=sq("a1"), end=sq("c1"))

    assert _move_order_score(board, develop, None) > _move_order_score(
        board,
        rook_drift,
        None,
    )


def test_strategy6_search_rejects_early_rc1_from_transcript() -> None:
    """The transcript opening should no longer choose Rc1 before king safety."""

    board = _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
        ]
    )

    assert get_best_move(board, depth=3) != LegalMove(start=sq("a1"), end=sq("c1"))


def test_strategy6_search_rejects_early_a_pawn_drift_after_rook_probe() -> None:
    """The same baseline opening should not replace Rc1 with aimless a-pawn drift."""

    board = _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
        ]
    )

    best_move = get_best_move(board, depth=3)

    assert best_move not in [
        LegalMove(start=sq("a2"), end=sq("a3")),
        LegalMove(start=sq("a2"), end=sq("a4")),
    ]


def test_strategy6_order_prefers_bg2_over_h4_from_transcript() -> None:
    """The transcript position should finish kingside development before h4."""

    board = _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
            ("a1", "c1"),
            ("f8", "e7"),
            ("g2", "g3"),
            ("g8", "h6"),
        ]
    )

    develop = ai.Move(start=sq("f1"), end=sq("g2"))
    pawn_lunge = ai.Move(start=sq("h2"), end=sq("h4"))

    assert _move_order_score(board, develop, None) > _move_order_score(
        board,
        pawn_lunge,
        None,
    )


def test_strategy6_search_rejects_h4_before_king_safety_from_transcript() -> None:
    """The transcript position should no longer choose h4 before kingside setup."""

    board = _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
            ("a1", "c1"),
            ("f8", "e7"),
            ("g2", "g3"),
            ("g8", "h6"),
        ]
    )

    assert get_best_move(board, depth=3) != LegalMove(start=sq("h2"), end=sq("h4"))


def test_strategy6_prefers_central_knight_development_over_nh6_from_transcript() -> None:
    """Black should score and search normal knight development above the rim hop."""

    board = _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
            ("a1", "c1"),
            ("f8", "e7"),
            ("g2", "g3"),
        ]
    )

    central_development = ai.Move(start=sq("g8"), end=sq("f6"))
    rim_development = ai.Move(start=sq("g8"), end=sq("h6"))

    assert _move_order_score(board, central_development, None) > _move_order_score(
        board,
        rim_development,
        None,
    )
    assert get_best_move(board, depth=3) != LegalMove(start=sq("g8"), end=sq("h6"))
