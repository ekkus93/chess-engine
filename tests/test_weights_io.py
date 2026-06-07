"""Unit tests for chess_game.texel.weights_io."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.weights_io import (
    load_weights,
    load_weights_or_default,
    save_weights,
)


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    """Saved weights can be loaded and are equal to the original."""
    weights = EvalWeights.default()
    path = tmp_path / "weights.json"
    save_weights(weights, path)
    loaded = load_weights(path)
    assert loaded.to_dict() == weights.to_dict()


def test_load_nonexistent_raises(tmp_path: Path) -> None:
    """Loading a file that does not exist raises FileNotFoundError."""
    path = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError):
        load_weights(path)


def test_load_malformed_json_raises(tmp_path: Path) -> None:
    """Loading a file with non-dict JSON content raises ValueError."""
    path = tmp_path / "bad.json"
    # Write a JSON file that is not a dict — from_dict will fail with TypeError.
    path.write_text('"just a string"', encoding="utf-8")
    with pytest.raises(ValueError):
        load_weights(path)


def test_load_or_default_returns_default_when_no_file(tmp_path: Path) -> None:
    """load_weights_or_default returns default weights when the path is absent."""
    missing = tmp_path / "nope.json"
    result_none = load_weights_or_default(None)
    result_missing = load_weights_or_default(missing)
    default = EvalWeights.default()
    assert result_none.to_dict() == default.to_dict()
    assert result_missing.to_dict() == default.to_dict()


def test_save_creates_parent_dirs(tmp_path: Path) -> None:
    """save_weights creates nested parent directories if they don't exist."""
    path = tmp_path / "nested" / "dir" / "weights.json"
    save_weights(EvalWeights.default(), path)
    assert path.exists()


def test_saved_file_is_valid_json(tmp_path: Path) -> None:
    """The saved weights file is well-formed JSON."""
    path = tmp_path / "weights.json"
    save_weights(EvalWeights.default(), path)
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)
