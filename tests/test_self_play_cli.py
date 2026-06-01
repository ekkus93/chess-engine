"""Tests for self-play CLI argument behavior."""

from __future__ import annotations

import sys
from typing import Any, cast

from chess_game import self_play


def test_no_opening_book_wins_over_bad_custom_path(monkeypatch) -> None:
    """When both flags are passed, --no-opening-book must skip loading custom path."""
    called = {"from_file": False}
    captured: dict[str, object] = {}

    class DummyOpeningBook:
        """Stub opening book type for CLI loading tests."""

        @classmethod
        def from_file(cls, path: str):  # noqa: ANN206
            called["from_file"] = True
            raise AssertionError(f"OpeningBook.from_file should not be called: {path}")

    def fake_run_self_play(depth_white: int, depth_black: int, options: Any) -> None:
        captured["depth_white"] = depth_white
        captured["depth_black"] = depth_black
        captured["options"] = options

    monkeypatch.setattr(self_play, "OpeningBook", DummyOpeningBook)
    monkeypatch.setattr(self_play, "run_self_play", fake_run_self_play)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "self_play",
            "--no-opening-book",
            "--opening-book",
            "/no/such/file.json",
            "--max-moves",
            "1",
        ],
    )

    self_play.main()

    assert called["from_file"] is False
    options = cast(Any, captured["options"])
    assert options.use_opening_book is False
    assert options.opening_book is None
