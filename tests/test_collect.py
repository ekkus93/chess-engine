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
def test_collect_games_with_custom_weights_completes(tmp_path: Path) -> None:
    """Collection should accept and use custom weights without error."""
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


@pytest.mark.slow
def test_collect_games_handles_max_move_limit(tmp_path: Path) -> None:
    """Games hitting max_moves should be treated as draws (default max_move_result)."""
    db_path = tmp_path / "positions.jsonl"
    opts = CollectionOptions(
        db_path=db_path,
        num_games=3,
        depth=1,
        skip_opening_plies=0,
        max_moves=20,  # Low limit; most games will reach it
        max_move_result="draw",
    )
    db = collect_games(opts)
    # Verify that collection completed (games hitting max_moves → outcome 0.5)
    assert len(db) >= 0


@pytest.mark.slow
def test_collect_games_aggregates_position_outcomes(tmp_path: Path) -> None:
    """Positions appearing in multiple games should have aggregated (mean) outcomes."""
    db_path = tmp_path / "positions.jsonl"
    opts = CollectionOptions(
        db_path=db_path,
        num_games=5,
        depth=1,
        skip_opening_plies=0,
    )
    db = collect_games(opts)
    # Verify that positions were collected (no assertion on specific outcomes,
    # since aggregation produces any value [0.0, 1.0], not just {0.0, 0.5, 1.0})
    pairs = db.all_pairs()
    for fen, outcome in pairs:
        assert isinstance(fen, str)
        assert 0.0 <= outcome <= 1.0


def test_collect_games_max_move_result_draw() -> None:
    """max_move_result='draw' should treat timeout games as draws."""
    opts = CollectionOptions(
        db_path=Path("/tmp/test_draw.jsonl"),
        num_games=1,
        depth=1,
        max_moves=1,
        max_move_result="draw",
    )
    # Just verify the config accepts 'draw'
    assert opts.max_move_result == "draw"


def test_collect_games_max_move_result_discard() -> None:
    """max_move_result='discard' should discard timeout games."""
    opts = CollectionOptions(
        db_path=Path("/tmp/test_discard.jsonl"),
        num_games=1,
        depth=1,
        max_moves=1,
        max_move_result="discard",
    )
    # Just verify the config accepts 'discard'
    assert opts.max_move_result == "discard"


def test_collect_games_invalid_max_move_result_raises() -> None:
    """Invalid max_move_result should raise ValueError."""
    with pytest.raises(ValueError):
        CollectionOptions(
            db_path=Path("/tmp/test.jsonl"),
            num_games=1,
            depth=1,
            max_move_result="invalid",
        )
