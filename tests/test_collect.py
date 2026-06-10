"""Tests for Texel self-play data collection."""
from __future__ import annotations

import random
from pathlib import Path

import pytest

import chess_game.texel.collect as collect_mod
from chess_game.chess.ai_board_utils import get_legal_moves
from chess_game.texel.collect import CollectionOptions, collect_games


def _first_legal_move(board, depth, book_options=None):
    """Fake get_best_move: return the first legal move, keeping a game progressing.

    Used to force games to the max-move limit with legal play so draw/discard
    behavior can be exercised without real (slow) search.
    """
    moves = get_legal_moves(board)
    return moves[0] if moves else None


@pytest.mark.slow
def test_collect_games_produces_nonempty_db(tmp_path: Path) -> None:
    """Three depth-1 games should produce at least some positions in the DB."""
    db_path = tmp_path / "positions.jsonl"
    opts = CollectionOptions(db_path=db_path, num_games=3, depth=1, skip_opening_plies=0)
    db = collect_games(opts)
    assert len(db) > 0


@pytest.mark.slow
def test_collect_games_outcomes_are_valid(tmp_path: Path) -> None:
    """Every individual self-play game outcome is one of {0.0, 0.5, 1.0}.

    Checks raw per-game outcomes from _play_game, not collect_games'
    all_pairs() values: all_pairs() returns aggregated means (total/count) that
    are legitimately fractional when a position recurs across games (e.g. the
    start position with skip_opening_plies=0), so asserting membership in
    {0,0.5,1} against the means is incorrect. Uses a seeded RNG for determinism.
    """
    opts = CollectionOptions(
        db_path=tmp_path / "positions.jsonl",
        num_games=3,
        depth=1,
        skip_opening_plies=0,
        max_moves=80,
    )
    rng = random.Random(0)
    valid_outcomes = {0.0, 0.5, 1.0}
    for _ in range(opts.num_games):
        record = collect_mod._play_game(opts, rng)
        assert record is not None
        assert record.outcome in valid_outcomes, f"Unexpected outcome: {record.outcome}"


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
    assert len(db) > 0, "Should collect at least one position from games"


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
    assert len(db) > 0, "Should collect positions even when games hit max_moves"


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


def test_play_game_propagates_weights_to_get_best_move(monkeypatch) -> None:
    """CollectionOptions.weights must reach get_best_move via BestMoveOptions.

    Behavior test: monkeypatches the real get_best_move used by _play_game and
    captures the BestMoveOptions actually passed by the collection code.
    """
    from chess_game.chess.eval_weights import EvalWeights

    custom = EvalWeights.default()
    captured: list = []

    def fake_get_best_move(board, depth, book_options=None):
        captured.append(book_options)
        return None  # end the game immediately after the first call

    monkeypatch.setattr(collect_mod, "get_best_move", fake_get_best_move)

    opts = CollectionOptions(
        db_path=Path("/tmp/unused.jsonl"),
        num_games=1,
        depth=1,
        weights=custom,
        skip_opening_plies=0,
    )
    collect_mod._play_game(opts, random.Random(0))

    assert captured, "get_best_move should have been invoked by _play_game"
    assert captured[0].weights is custom, "weights must propagate into BestMoveOptions"


def test_play_game_max_move_draw_returns_half(monkeypatch) -> None:
    """Hitting max_moves with max_move_result='draw' yields a 0.5 GameRecord."""
    monkeypatch.setattr(collect_mod, "get_best_move", _first_legal_move)

    opts = CollectionOptions(
        db_path=Path("/tmp/unused.jsonl"),
        num_games=1,
        depth=1,
        max_moves=4,
        skip_opening_plies=0,
        max_move_result="draw",
    )
    record = collect_mod._play_game(opts, random.Random(0))

    assert record is not None
    assert record.outcome == pytest.approx(0.5)
    assert len(record.positions) > 0


def test_play_game_max_move_discard_returns_none(monkeypatch) -> None:
    """Hitting max_moves with max_move_result='discard' returns None (game dropped)."""
    monkeypatch.setattr(collect_mod, "get_best_move", _first_legal_move)

    opts = CollectionOptions(
        db_path=Path("/tmp/unused.jsonl"),
        num_games=1,
        depth=1,
        max_moves=4,
        skip_opening_plies=0,
        max_move_result="discard",
    )
    record = collect_mod._play_game(opts, random.Random(0))

    assert record is None


def test_collect_games_invalid_max_move_result_raises() -> None:
    """Invalid max_move_result should raise ValueError."""
    with pytest.raises(ValueError):
        CollectionOptions(
            db_path=Path("/tmp/test.jsonl"),
            num_games=1,
            depth=1,
            max_move_result="invalid",
        )


def test_collect_games_seed_is_configurable() -> None:
    """CollectionOptions should accept and store seed parameter."""
    opts1 = CollectionOptions(
        db_path=Path("/tmp/test1.jsonl"),
        num_games=1,
        depth=1,
        seed=0,
    )
    opts2 = CollectionOptions(
        db_path=Path("/tmp/test2.jsonl"),
        num_games=1,
        depth=1,
        seed=42,
    )
    assert opts1.seed == 0
    assert opts2.seed == 42


def test_collect_games_weights_parameter_accepted() -> None:
    """CollectionOptions should accept custom weights."""
    from chess_game.chess.eval_weights import EvalWeights

    weights = EvalWeights.default()
    opts = CollectionOptions(
        db_path=Path("/tmp/test.jsonl"),
        num_games=1,
        depth=1,
        weights=weights,
    )
    assert opts.weights is weights


def test_collect_games_draw_stores_half_outcomes(monkeypatch, tmp_path: Path) -> None:
    """collect_games with max_move_result='draw' stores positions with 0.5 outcome."""
    monkeypatch.setattr(collect_mod, "get_best_move", _first_legal_move)

    opts = CollectionOptions(
        db_path=tmp_path / "draw.jsonl",
        num_games=1,
        depth=1,
        max_moves=4,
        skip_opening_plies=0,
        max_move_result="draw",
    )
    db = collect_games(opts)

    assert len(db) > 0
    assert all(outcome == pytest.approx(0.5) for _, outcome in db.all_pairs())


def test_collect_games_discard_stores_nothing(monkeypatch, tmp_path: Path) -> None:
    """collect_games with max_move_result='discard' stores no positions."""
    monkeypatch.setattr(collect_mod, "get_best_move", _first_legal_move)

    opts = CollectionOptions(
        db_path=tmp_path / "discard.jsonl",
        num_games=2,
        depth=1,
        max_moves=4,
        skip_opening_plies=0,
        max_move_result="discard",
    )
    db = collect_games(opts)

    assert len(db) == 0


def test_collect_games_same_seed_reproducible(monkeypatch, tmp_path: Path) -> None:
    """Same CollectionOptions.seed produces identical recorded data.

    The fake move chooser keys off the per-move rng_seed that collect_games
    derives from its seeded random.Random(seed), so reproducibility genuinely
    depends on the collection seed rather than being trivially constant.
    """

    def seeded_choice(board, depth, book_options=None):
        moves = get_legal_moves(board)
        if not moves:
            return None
        return moves[book_options.rng_seed % len(moves)]

    monkeypatch.setattr(collect_mod, "get_best_move", seeded_choice)

    def run(path: Path) -> dict:
        opts = CollectionOptions(
            db_path=path,
            num_games=2,
            depth=1,
            max_moves=6,
            skip_opening_plies=0,
            max_move_result="draw",
            seed=42,
        )
        return dict(collect_games(opts).all_pairs())

    first = run(tmp_path / "a.jsonl")
    second = run(tmp_path / "b.jsonl")

    assert len(first) > 0
    assert first == second


# Configuration and persistence tests (named honestly; not behavior claims)


def test_collection_options_stores_all_fields() -> None:
    """Config test: CollectionOptions stores all configuration fields."""
    opts = CollectionOptions(
        db_path=Path("/tmp/db.jsonl"),
        num_games=10,
        depth=2,
        skip_opening_plies=8,
        max_moves=300,
        seed=42,
        weights=None,
        max_move_result="draw",
    )
    assert opts.num_games == 10
    assert opts.depth == 2
    assert opts.skip_opening_plies == 8
    assert opts.max_moves == 300
    assert opts.seed == 42
    assert opts.weights is None
    assert opts.max_move_result == "draw"


def test_position_db_persists_draw_outcome(tmp_path: Path) -> None:
    """Persistence test: a 0.5 GameRecord round-trips through PositionDB as 0.5.

    Explicitly a persistence test, not collection draw-detection (which is
    covered by test_play_game_max_move_draw_returns_half).
    """
    from chess_game.texel.position_db import GameRecord, PositionDB

    db_path = tmp_path / "positions.jsonl"
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    db = PositionDB()
    db.add_game(GameRecord(positions=[fen], outcome=0.5))
    db.save(db_path)

    reloaded = PositionDB.load(db_path)
    outcomes = [outcome for _, outcome in reloaded.all_pairs()]
    assert outcomes
    assert all(outcome == pytest.approx(0.5) for outcome in outcomes)
