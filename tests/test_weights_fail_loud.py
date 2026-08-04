"""Texel fail-loud: explicit weight paths must not silently fall back to defaults.

Strict ``load_weights`` / ``load_optional_weights`` raise on a missing or malformed
explicit path; the lenient ``load_weights_or_default`` keeps its silent fallback only
for the engine's automatic tuned-weight cache.
"""

import json
from pathlib import Path

import pytest

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.position_db import GameRecord, PositionDB
from chess_game.texel.tune import TuningConfig, run_tuning
from chess_game.texel.weights_io import (
    load_optional_weights,
    load_weights,
    load_weights_or_default,
    save_weights,
)

_START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def _valid_weights_file(tmp_path: Path) -> Path:
    path = tmp_path / "w.json"
    save_weights(EvalWeights.default(), path)
    return path


def _non_empty_db_file(tmp_path: Path) -> Path:
    db = PositionDB()
    db.add_game(GameRecord(positions=[_START_FEN], outcome=0.5))
    path = tmp_path / "db.jsonl"
    db.save(path)
    return path


# ---- load_optional_weights: defaults only when path is None ----

def test_load_optional_weights_none_returns_default() -> None:
    assert isinstance(load_optional_weights(None), EvalWeights)


def test_load_optional_weights_missing_path_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_optional_weights(tmp_path / "does_not_exist.json")


def test_load_optional_weights_valid_path_loads(tmp_path: Path) -> None:
    path = _valid_weights_file(tmp_path)
    assert isinstance(load_optional_weights(path), EvalWeights)


# ---- strict load_weights ----

def test_load_weights_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_weights(tmp_path / "nope.json")


def test_load_weights_invalid_json_raises_with_path(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        load_weights(bad)
    assert str(bad) in str(exc.value)


def test_load_weights_non_dict_raises(tmp_path: Path) -> None:
    arr = tmp_path / "arr.json"
    arr.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(ValueError):
        load_weights(arr)


# ---- lenient auto-load fallback is intentionally preserved ----

def test_load_weights_or_default_keeps_silent_fallback(tmp_path: Path) -> None:
    """The auto tuned-weight cache loader still falls back silently (by design)."""
    assert isinstance(load_weights_or_default(None), EvalWeights)
    assert isinstance(load_weights_or_default(tmp_path / "missing.json"), EvalWeights)


# ---- run_tuning: explicit missing initial weights fails loudly, writes nothing ----

def test_run_tuning_missing_initial_weights_raises_and_writes_nothing(tmp_path: Path) -> None:
    db_path = _non_empty_db_file(tmp_path)
    output = tmp_path / "out.json"
    config = TuningConfig(
        db_path=db_path,
        output_weights_path=output,
        initial_weights_path=tmp_path / "typo_weights.json",
        do_calibrate_k=False,
        verbose=False,
    )
    with pytest.raises(FileNotFoundError):
        run_tuning(config)
    assert not output.exists(), "no tuned weights should be written when the run fails"
