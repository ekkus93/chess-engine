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
        # "b" and "c" appear in both games; outcomes aggregate to mean
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

    def test_duplicate_aggregation(self) -> None:
        """Duplicate FENs should aggregate outcomes."""
        db = PositionDB()
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        db.add_game(GameRecord(positions=[fen], outcome=1.0))
        db.add_game(GameRecord(positions=[fen], outcome=0.5))
        db.add_game(GameRecord(positions=[fen], outcome=0.0))

        pairs = db.all_pairs()
        assert len(pairs) == 1
        assert pairs[0][0] == fen
        # Mean of 1.0, 0.5, 0.0 = 0.5
        assert abs(pairs[0][1] - 0.5) < 1e-9

    def test_old_jsonl_format_load(self, tmp_path: Path) -> None:
        """Loading old JSONL format {"pos": ..., "outcome": ...} should work."""
        save_path = tmp_path / "old_format.jsonl"
        old_format_line = '{"pos": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "outcome": 1.0}\n'
        save_path.write_text(old_format_line)

        db = PositionDB.load(save_path)
        assert len(db) == 1
        pairs = db.all_pairs()
        assert pairs[0][1] == 1.0  # outcome should be 1.0

    def test_new_jsonl_format_roundtrip(self, tmp_path: Path) -> None:
        """Saving and loading new JSONL format should preserve stats."""
        db = PositionDB()
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        db.add_game(GameRecord(positions=[fen], outcome=1.0))
        db.add_game(GameRecord(positions=[fen], outcome=0.5))

        save_path = tmp_path / "new_format.jsonl"
        db.save(save_path)

        loaded = PositionDB.load(save_path)
        assert len(loaded) == 1
        pairs = loaded.all_pairs()
        # Mean of 1.0 and 0.5 = 0.75
        assert abs(pairs[0][1] - 0.75) < 1e-9

    def test_old_jsonl_duplicate_aggregation(self, tmp_path: Path) -> None:
        """Old JSONL format with duplicate FENs should aggregate."""
        save_path = tmp_path / "old_duplicate.jsonl"
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        old_lines = (
            f'{{"pos": "{fen}", "outcome": 1.0}}\n'
            f'{{"pos": "{fen}", "outcome": 0.5}}\n'
            f'{{"pos": "{fen}", "outcome": 0.0}}\n'
        )
        save_path.write_text(old_lines)

        db = PositionDB.load(save_path)
        assert len(db) == 1
        pairs = db.all_pairs()
        # Mean of 1.0, 0.5, 0.0 = 0.5
        assert abs(pairs[0][1] - 0.5) < 1e-9

    def test_new_jsonl_format_with_explicit_counts(self, tmp_path: Path) -> None:
        """New JSONL format should preserve total and count separately."""
        db = PositionDB()
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        # Add 4 games: 3 wins + 1 draw = total 3.5, count 4, mean 0.875
        db.add_game(GameRecord(positions=[fen], outcome=1.0))
        db.add_game(GameRecord(positions=[fen], outcome=1.0))
        db.add_game(GameRecord(positions=[fen], outcome=1.0))
        db.add_game(GameRecord(positions=[fen], outcome=0.5))

        save_path = tmp_path / "counts.jsonl"
        db.save(save_path)

        loaded = PositionDB.load(save_path)
        assert len(loaded) == 1
        pairs = loaded.all_pairs()
        # Mean should be (1+1+1+0.5)/4 = 3.5/4 = 0.875
        assert abs(pairs[0][1] - 0.875) < 1e-9

    def test_get_stats_returns_none_for_missing_position(self) -> None:
        """get_stats should return None for a position not in the database."""
        db = PositionDB()
        db.add_game(GameRecord(positions=["pos1"], outcome=1.0))
        assert db.get_stats("pos_not_in_db") is None

    def test_get_stats_direct_access_to_stats(self) -> None:
        """get_stats should return PositionStats with correct total, count, mean."""
        db = PositionDB()
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        # Add duplicate outcomes: 1.0, 0.5, 0.0 → total=1.5, count=3, mean=0.5
        db.add_game(GameRecord(positions=[fen], outcome=1.0))
        db.add_game(GameRecord(positions=[fen], outcome=0.5))
        db.add_game(GameRecord(positions=[fen], outcome=0.0))

        stats = db.get_stats(fen)
        assert stats is not None
        assert stats.count == 3
        assert abs(stats.total - 1.5) < 1e-9
        assert abs(stats.mean - 0.5) < 1e-9

    def test_get_stats_round_trip_with_save_load(self, tmp_path: Path) -> None:
        """get_stats should work correctly after save/load round trip."""
        db = PositionDB()
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        db.add_game(GameRecord(positions=[fen], outcome=1.0))
        db.add_game(GameRecord(positions=[fen], outcome=1.0))
        db.add_game(GameRecord(positions=[fen], outcome=0.5))

        save_path = tmp_path / "round_trip.jsonl"
        db.save(save_path)

        loaded = PositionDB.load(save_path)
        stats = loaded.get_stats(fen)
        assert stats is not None
        assert stats.count == 3
        assert abs(stats.total - 2.5) < 1e-9
        assert abs(stats.mean - (2.5 / 3.0)) < 1e-9
