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
        def from_file(cls, path: str):
            called["from_file"] = True
            raise AssertionError(f"OpeningBook.from_file should not be called: {path}")

    def fake_run_multi_game(config: Any) -> None:
        captured["config"] = config

    monkeypatch.setattr(self_play, "OpeningBook", DummyOpeningBook)
    monkeypatch.setattr(self_play, "_run_multi_game", fake_run_multi_game)
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
    config = cast(Any, captured["config"])
    assert config.play_options.use_opening_book is False
    assert config.play_options.opening_book is None
