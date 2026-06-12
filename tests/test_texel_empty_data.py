"""Texel fail-loud: empty training data must raise, not silently no-op or write output.

Covers SPSA ``optimize``, k calibration, and the ``run_tuning`` pipeline (both an
empty existing DB and a collection run that produced zero positions).
"""

from pathlib import Path

import pytest

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel import tune as tune_module
from chess_game.texel.loss import calibrate_k
from chess_game.texel.position_db import PositionDB
from chess_game.texel.spsa import SPSAOptions, optimize
from chess_game.texel.tune import TuningConfig, run_tuning


def test_optimize_empty_db_raises() -> None:
    with pytest.raises(ValueError, match="at least one training position"):
        optimize(EvalWeights.default(), PositionDB(), SPSAOptions(max_iterations=1))


def test_calibrate_k_empty_raises() -> None:
    with pytest.raises(ValueError, match="no positions"):
        calibrate_k([], EvalWeights.default())


def test_run_tuning_empty_existing_db_raises_and_writes_nothing(tmp_path: Path) -> None:
    db_path = tmp_path / "empty_db.jsonl"
    PositionDB().save(db_path)  # valid but empty
    output = tmp_path / "out.json"
    config = TuningConfig(
        db_path=db_path,
        output_weights_path=output,
        do_calibrate_k=False,
        verbose=False,
    )
    with pytest.raises(ValueError, match="no positions"):
        run_tuning(config)
    assert not output.exists()


def test_run_tuning_empty_collection_raises_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A collection run that produces zero positions must fail, not write weights."""
    monkeypatch.setattr(tune_module, "collect_games", lambda _opts: PositionDB())
    db_path = tmp_path / "fresh_db.jsonl"  # does not exist -> triggers collection
    output = tmp_path / "out.json"
    config = TuningConfig(
        db_path=db_path,
        output_weights_path=output,
        do_calibrate_k=False,
        verbose=False,
    )
    with pytest.raises(ValueError, match="no positions"):
        run_tuning(config)
    assert not output.exists()
