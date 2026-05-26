"""Transcript-driven regressions for STRATEGY7 practical defense cleanup."""

from chess_game.chess import ai
from chess_game.chess.ai import get_best_move, get_evaluation_breakdown
from chess_game.chess.board import Board
from chess_game.chess.types import LegalMove
from tests.helpers import sq
from tests.test_ai_quality import _move_order_score


def _board_from_moves(moves: list[tuple[str, str]]) -> Board:
    board = Board()
    for start, end in moves:
        board.make_move(sq(start), sq(end))
    return board


def _task1_passer_containment_board() -> Board:
    return _board_from_moves(
        [
            ("b1", "c3"),
            ("e7", "e5"),
            ("g1", "f3"),
            ("b8", "c6"),
            ("c3", "e4"),
            ("d7", "d5"),
            ("e4", "g5"),
            ("e5", "e4"),
            ("g5", "e4"),
            ("c8", "f5"),
            ("e4", "c3"),
            ("f8", "c5"),
            ("g2", "g3"),
            ("g8", "f6"),
            ("d2", "d4"),
            ("c6", "d4"),
            ("f3", "d4"),
            ("f5", "d7"),
            ("c1", "g5"),
            ("e8", "g8"),
            ("c3", "d5"),
            ("h7", "h5"),
            ("g5", "f6"),
            ("g7", "f6"),
            ("e2", "e4"),
            ("f8", "e8"),
            ("d1", "d3"),
            ("h5", "h4"),
            ("e1", "c1"),
            ("e8", "e5"),
            ("f2", "f4"),
            ("e5", "d5"),
            ("e4", "d5"),
            ("c5", "b6"),
            ("g3", "h4"),
            ("g8", "h8"),
            ("f1", "h3"),
            ("d7", "h3"),
            ("d3", "h3"),
            ("c7", "c6"),
            ("d5", "c6"),
            ("b6", "d4"),
            ("c6", "b7"),
            ("a8", "b8"),
            ("h3", "b3"),
        ]
    )


def _task1_heavy_piece_threat_board() -> Board:
    board = _task1_passer_containment_board()
    for start, end in [("a7", "a5"), ("a2", "a4"), ("d8", "d6"), ("h1", "f1")]:
        board.make_move(sq(start), sq(end))
    return board


def test_strategy7_order_prefers_capturing_b7_passer_over_a5() -> None:
    """The defending side should tie its rook to the passer instead of drifting on the wing."""

    board = _task1_passer_containment_board()
    contain = ai.Move(start=sq("b8"), end=sq("b7"))
    side_play = ai.Move(start=sq("a7"), end=sq("a5"))

    assert _move_order_score(board, contain, None) > _move_order_score(board, side_play, None)


def test_strategy7_search_rejects_a5_and_stays_on_b_file() -> None:
    """The baseline defense should stay focused on the passer instead of drifting with ...a5."""

    board = _task1_passer_containment_board()
    best_move = get_best_move(board, depth=3)

    assert best_move != LegalMove(start=sq("a7"), end=sq("a5"))
    assert best_move in [
        LegalMove(start=sq("b8"), end=sq("b7")),
        LegalMove(start=sq("d8"), end=sq("d7")),
        LegalMove(start=sq("d8"), end=sq("e7")),
        LegalMove(start=sq("d8"), end=sq("c7")),
    ]


def test_strategy7_order_prefers_rook_containment_over_queen_drift() -> None:
    """Heavy-piece defense should keep the rook tied to the passer over Qa6 drift."""

    board = _task1_heavy_piece_threat_board()
    contain = ai.Move(start=sq("b8"), end=sq("b7"))
    queen_drift = ai.Move(start=sq("d6"), end=sq("a6"))

    assert _move_order_score(board, contain, None) > _move_order_score(board, queen_drift, None)


def test_strategy7_order_prefers_queen_reinforcement_over_a5_panic() -> None:
    """Even non-capturing defense should beat the old side-pawn panic in the baseline."""

    board = _task1_passer_containment_board()
    reinforce = ai.Move(start=sq("d8"), end=sq("d7"))
    side_play = ai.Move(start=sq("a7"), end=sq("a5"))

    assert _move_order_score(board, reinforce, None) > _move_order_score(board, side_play, None)


def test_strategy7_search_rejects_qa6_in_later_heavy_piece_defense() -> None:
    """Later heavy-piece defense should no longer drift into the old Qa6 side line."""

    board = _task1_heavy_piece_threat_board()

    assert get_best_move(board, depth=3) != LegalMove(start=sq("d6"), end=sq("a6"))


def test_strategy7_breakdown_prefers_covering_key_defenders_over_qa6_drift() -> None:
    """Containment should reward covering overloaded defenders over the old queen drift."""

    drift_board = _task1_heavy_piece_threat_board()
    support_board = drift_board.clone()
    support_board.make_move(sq("d6"), sq("d7"))
    drift_board.make_move(sq("d6"), sq("a6"))

    assert (
        get_evaluation_breakdown(support_board)["defensive_containment"]
        < get_evaluation_breakdown(drift_board)["defensive_containment"]
    )
