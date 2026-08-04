"""Unit tests for loss function calibration."""
from __future__ import annotations

from pathlib import Path

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.loss import calibrate_k, mean_squared_error

# A minimal set of (fen, outcome) pairs using the starting position FEN.
_START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

_FAKE_PAIRS: list[tuple[str, float]] = [
    (_START_FEN, 1.0),
    (_START_FEN, 0.5),
    (_START_FEN, 0.0),
]


def test_calibrate_k_returns_positive_float() -> None:
    """calibrate_k should return a positive float in a reasonable range."""
    weights = EvalWeights.default()
    k = calibrate_k(_FAKE_PAIRS, weights)
    assert isinstance(k, float)
    assert k > 0.0
    assert k <= 2.0


def test_calibrate_k_reduces_mse_vs_default_k() -> None:
    """Calibrated k should give MSE <= MSE with the default k=1.13."""
    weights = EvalWeights.default()
    default_k = 1.13
    calibrated_k = calibrate_k(_FAKE_PAIRS, weights)
    mse_default = mean_squared_error(_FAKE_PAIRS, weights, default_k)
    mse_calibrated = mean_squared_error(_FAKE_PAIRS, weights, calibrated_k)
    # Calibrated k should not be worse than the hard-coded default.
    assert mse_calibrated <= mse_default + 1e-9


def test_calibrate_and_save_k_writes_file(tmp_path: Path) -> None:
    """calibrate_and_save_k writes a JSON file with the 'k' key."""
    import json

    from chess_game.texel.loss import calibrate_and_save_k
    from chess_game.texel.position_db import PositionDB

    db = PositionDB()
    from chess_game.texel.position_db import GameRecord
    db.add_game(GameRecord(positions=[_START_FEN], outcome=1.0))
    db.add_game(GameRecord(positions=[_START_FEN], outcome=0.0))

    out = tmp_path / "k.json"
    k = calibrate_and_save_k(db, EvalWeights.default(), out)

    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "k" in data
    assert abs(data["k"] - k) < 1e-9
