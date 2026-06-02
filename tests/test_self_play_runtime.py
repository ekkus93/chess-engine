"""Unit tests for self-play runtime helpers."""

from __future__ import annotations

from typing import Callable

from chess_game import self_play
from chess_game.chess.board import Board
from chess_game.chess.types import LegalMove
from tests.helpers import sq


def test_get_best_move_with_timeout_without_timeout_forwards_book_options(
    monkeypatch,
) -> None:
    """No-timeout path should pass explicit opening-book options through to search."""

    captured: dict[str, object] = {}
    expected_move = LegalMove(start=sq("e2"), end=sq("e4"))

    def fake_get_best_move(
        board: Board,
        depth: int,
        position_counts=None,
        book_options=None,
    ):
        captured["board"] = board
        captured["depth"] = depth
        captured["position_counts"] = position_counts
        captured["book_options"] = book_options
        return expected_move

    monkeypatch.setattr(self_play, "get_best_move", fake_get_best_move)

    board = Board()
    params = self_play._MoveSelectionParams(
        board=board,
        depth=3,
        timeout=None,
        position_counts={"abc": 2},
        use_opening_book=False,
        opening_book=None,
    )
    move = self_play._get_best_move_with_timeout(params)

    assert move == expected_move
    assert captured["board"] is board
    assert captured["depth"] == 3
    assert captured["position_counts"] == {"abc": 2}
    assert isinstance(captured["book_options"], self_play.BestMoveOptions)
    assert captured["book_options"].use_opening_book is False


def test_get_best_move_with_timeout_returns_none_on_alarm_timeout(monkeypatch) -> None:
    """Timeout path should swallow internal timeout exception and return None."""

    handlers: list[Callable[[int, object], None]] = []
    alarms: list[int] = []

    def fake_signal(_sig: int, handler: Callable[[int, object], None]):
        previous = handlers[-1] if handlers else (lambda _signum, _frame: None)
        handlers.append(handler)
        return previous

    def fake_alarm(seconds: int) -> None:
        alarms.append(seconds)

    def fake_get_best_move(
        _board: Board,
        depth: int,
        position_counts=None,
        book_options=None,
    ):
        _ = depth
        _ = position_counts
        _ = book_options
        handlers[-1](0, object())
        raise AssertionError("Timeout handler should raise before this line")

    monkeypatch.setattr(self_play.signal, "signal", fake_signal)
    monkeypatch.setattr(self_play.signal, "alarm", fake_alarm)
    monkeypatch.setattr(self_play, "get_best_move", fake_get_best_move)

    params = self_play._MoveSelectionParams(
        board=Board(),
        depth=2,
        timeout=0.2,
        position_counts=None,
    )
    move = self_play._get_best_move_with_timeout(params)

    assert move is None
    assert alarms == [1, 0]
    assert len(handlers) == 2
