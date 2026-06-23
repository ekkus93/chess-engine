"""Tests for AnnotatedPositionDB and save_annotated."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from chess_game.texel.annotated_position_db import AnnotatedPositionDB, save_annotated
from chess_game.texel.position_db import GameRecord, PositionDB

_FEN_A = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
_FEN_B = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
_FEN_C = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"


def _make_annotated_db(scores: dict) -> AnnotatedPositionDB:
    db = AnnotatedPositionDB()
    for fen in scores:
        db.add_game(GameRecord(positions=[fen], outcome=0.5))
    db.sf_scores = dict(scores)
    return db


def test_round_trip_with_scores() -> None:
    db = _make_annotated_db({_FEN_A: 42, _FEN_B: -100})
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = Path(f.name)
    db.save(path)
    loaded = AnnotatedPositionDB.load(path)
    assert loaded.sf_scores.get(_FEN_A) == 42
    assert loaded.sf_scores.get(_FEN_B) == -100


def test_round_trip_null_score() -> None:
    db = _make_annotated_db({_FEN_A: None})
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = Path(f.name)
    db.save(path)
    loaded = AnnotatedPositionDB.load(path)
    assert _FEN_A in loaded.sf_scores
    assert loaded.sf_scores[_FEN_A] is None


def test_backward_compat_no_sf_score() -> None:
    """Old-format JSONL without sf_score_cp loads without error."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w", delete=False) as f:
        f.write(json.dumps({"pos": _FEN_A, "total": 0.5, "count": 1}) + "\n")
        path = Path(f.name)
    loaded = AnnotatedPositionDB.load(path)
    assert not loaded.has_annotations()
    assert len(loaded) == 1


def test_has_annotations_true() -> None:
    db = _make_annotated_db({_FEN_A: 30})
    assert db.has_annotations()


def test_has_annotations_false_all_none() -> None:
    db = _make_annotated_db({_FEN_A: None})
    assert not db.has_annotations()


def test_has_annotations_false_empty() -> None:
    db = AnnotatedPositionDB()
    assert not db.has_annotations()


def test_save_annotated_merges_correctly() -> None:
    plain_db = PositionDB()
    plain_db.add_game(GameRecord(positions=[_FEN_A, _FEN_B], outcome=1.0))
    scores = {_FEN_A: 55, _FEN_B: -30}
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = Path(f.name)
    save_annotated(plain_db, scores, path)
    loaded = AnnotatedPositionDB.load(path)
    assert loaded.sf_scores.get(_FEN_A) == 55
    assert loaded.sf_scores.get(_FEN_B) == -30


def test_save_annotated_none_written_as_null() -> None:
    plain_db = PositionDB()
    plain_db.add_game(GameRecord(positions=[_FEN_A], outcome=0.5))
    scores = {_FEN_A: None}
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = Path(f.name)
    save_annotated(plain_db, scores, path)
    with path.open() as f:
        row = json.loads(f.read().strip())
    assert row["sf_score_cp"] is None


def test_mixed_rows_load_without_error() -> None:
    with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w", delete=False) as f:
        f.write(json.dumps({"pos": _FEN_A, "total": 0.5, "count": 1, "sf_score_cp": 10}) + "\n")
        f.write(json.dumps({"pos": _FEN_B, "total": 1.0, "count": 1}) + "\n")
        path = Path(f.name)
    loaded = AnnotatedPositionDB.load(path)
    assert len(loaded) == 2
    assert loaded.sf_scores.get(_FEN_A) == 10
    assert _FEN_B not in loaded.sf_scores


def test_annotated_pairs_returns_all() -> None:
    db = _make_annotated_db({_FEN_A: 42, _FEN_B: None})
    pairs = dict(db.annotated_pairs())
    assert pairs[_FEN_A] == 42
    assert pairs[_FEN_B] is None
