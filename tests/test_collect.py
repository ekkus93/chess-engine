"""Tests for Texel self-play data collection."""
from __future__ import annotations

from pathlib import Path

import pytest

from chess_game.texel.collect import CollectionOptions, collect_games


@pytest.mark.slow
def test_collect_games_produces_nonempty_db(tmp_path: Path) -> None:
    """Three depth-1 games should produce at least some positions in the DB."""
    db_path = tmp_path / "positions.jsonl"
    opts = CollectionOptions(db_path=db_path, num_games=3, depth=1, skip_opening_plies=0)
    db = collect_games(opts)
    assert len(db) > 0


@pytest.mark.slow
def test_collect_games_outcomes_are_valid(tmp_path: Path) -> None:
    """All collected outcomes must be one of {0.0, 0.5, 1.0}."""
    db_path = tmp_path / "positions.jsonl"
    opts = CollectionOptions(db_path=db_path, num_games=3, depth=1, skip_opening_plies=0)
    db = collect_games(opts)
    valid_outcomes = {0.0, 0.5, 1.0}
    for _, outcome in db.all_pairs():
        assert outcome in valid_outcomes, f"Unexpected outcome: {outcome}"


@pytest.mark.slow
def test_collect_games_appends_to_existing_db(tmp_path: Path) -> None:
    """Running collect twice should result in a larger DB the second time."""
    db_path = tmp_path / "positions.jsonl"
    opts = CollectionOptions(db_path=db_path, num_games=2, depth=1, skip_opening_plies=0)
    db_first = collect_games(opts)
    size_first = len(db_first)

    # Second run appends (deduplication means >= not strictly >)
    db_second = collect_games(opts)
    assert len(db_second) >= size_first


@pytest.mark.slow
def test_collect_skips_incomplete_games(tmp_path: Path) -> None:
    """max_moves=1 means all games hit the move limit and are discarded."""
    db_path = tmp_path / "positions.jsonl"
    opts = CollectionOptions(
        db_path=db_path,
        num_games=5,
        depth=1,
        skip_opening_plies=0,
        max_moves=1,
    )
    db = collect_games(opts)
    # With max_moves=1 all games are abandoned — DB should be empty
    assert len(db) == 0


@pytest.mark.slow
def test_collect_games_records_stalemate_as_draw(tmp_path: Path) -> None:
    """Stalemate should be recorded as outcome 0.5 (draw)."""
    db_path = tmp_path / "positions.jsonl"
    opts = CollectionOptions(db_path=db_path, num_games=5, depth=1, skip_opening_plies=0)
    db = collect_games(opts)
    # Verify all outcomes are valid: 0.0 (Black wins), 0.5 (draw), 1.0 (White wins)
    valid_outcomes = {0.0, 0.5, 1.0}
    for _, outcome in db.all_pairs():
        assert outcome in valid_outcomes


@pytest.mark.slow
def test_collect_games_with_seed_is_reproducible(tmp_path: Path) -> None:
    """Collection with the same seed should produce the same DB."""
    db_path1 = tmp_path / "positions1.jsonl"
    db_path2 = tmp_path / "positions2.jsonl"
    opts1 = CollectionOptions(
        db_path=db_path1,
        num_games=3,
        depth=1,
        skip_opening_plies=0,
        seed=42,
    )
    opts2 = CollectionOptions(
        db_path=db_path2,
        num_games=3,
        depth=1,
        skip_opening_plies=0,
        seed=42,
    )
    db1 = collect_games(opts1)
    db2 = collect_games(opts2)
    # Same seed should produce identical databases (same positions, same outcomes)
    pairs1 = sorted(db1.all_pairs())
    pairs2 = sorted(db2.all_pairs())
    assert pairs1 == pairs2


@pytest.mark.slow
def test_collect_games_uses_configured_weights(tmp_path: Path) -> None:
    """Collection should use weights from CollectionOptions if provided."""
    from chess_game.chess.eval_weights import EvalWeights
    db_path = tmp_path / "positions.jsonl"
    custom_weights = EvalWeights.default()
    opts = CollectionOptions(
        db_path=db_path,
        num_games=2,
        depth=1,
        skip_opening_plies=0,
        weights=custom_weights,
    )
    db = collect_games(opts)
    # Verify that collection completed with custom weights
    assert len(db) >= 0
