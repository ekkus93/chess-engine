"""Unit tests for PositionDB."""
from __future__ import annotations

from pathlib import Path

from chess_game.texel.position_db import GameRecord, PositionDB


class TestPositionDB:
    """Tests for PositionDB storage and retrieval."""

    def test_add_game_stores_correct_outcome(self) -> None:
        """add_game should store each position with the game's outcome."""
        db = PositionDB()
        record = GameRecord(positions=["pos1", "pos2", "pos3"], outcome=1.0)
        db.add_game(record)
        pairs = dict(db.all_pairs())
        assert pairs["pos1"] == 1.0
        assert pairs["pos2"] == 1.0
        assert pairs["pos3"] == 1.0

    def test_save_and_load_round_trip(self, tmp_path: Path) -> None:
        """Saving and loading a PositionDB should preserve all data."""
        db = PositionDB()
        db.add_game(GameRecord(positions=["alpha", "beta"], outcome=0.5))
        db.add_game(GameRecord(positions=["gamma"], outcome=0.0))

        save_path = tmp_path / "test_db.jsonl"
        db.save(save_path)

        loaded = PositionDB.load(save_path)
        assert len(loaded) == 3
        pairs = dict(loaded.all_pairs())
        assert pairs["alpha"] == 0.5
        assert pairs["beta"] == 0.5
        assert pairs["gamma"] == 0.0

    def test_len_returns_unique_position_count(self) -> None:
        """__len__ should return number of unique positions (deduplication)."""
        db = PositionDB()
        db.add_game(GameRecord(positions=["a", "b", "c"], outcome=1.0))
        db.add_game(GameRecord(positions=["b", "c", "d"], outcome=0.0))
        # "b" and "c" appear in both games; last outcome wins
        assert len(db) == 4

    def test_sample_respects_size(self) -> None:
        """sample(n) should return at most n items."""
        db = PositionDB()
        positions = [f"pos{i}" for i in range(20)]
        db.add_game(GameRecord(positions=positions, outcome=0.5))
        assert len(db.sample(5)) == 5
        assert len(db.sample(20)) == 20
        assert len(db.sample(100)) == 20  # capped at actual size

    def test_empty_db_save_load(self, tmp_path: Path) -> None:
        """Saving and loading an empty PositionDB should work without error."""
        db = PositionDB()
        save_path = tmp_path / "empty_db.jsonl"
        db.save(save_path)

        loaded = PositionDB.load(save_path)
        assert len(loaded) == 0
        assert loaded.all_pairs() == []
