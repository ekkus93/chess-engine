"""Tests for the end-to-end Texel tuning pipeline."""
from __future__ import annotations

from pathlib import Path

import pytest

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.spsa import SPSAOptions
from chess_game.texel.tune import TuningConfig, run_tuning
from chess_game.texel.weights_io import load_weights


@pytest.mark.slow
def test_run_tuning_produces_weights_file(tmp_path: Path) -> None:
    """run_tuning writes a valid weights file to the output path."""
    db_path = tmp_path / "test.jsonl"
    output_path = tmp_path / "tuned.json"

    config = TuningConfig(
        db_path=db_path,
        output_weights_path=output_path,
        collection_games=5,
        collection_depth=1,
        spsa_options=SPSAOptions(max_iterations=5, verbose=False),
        do_calibrate_k=True,
        verbose=False,
    )
    run_tuning(config)

    assert output_path.exists(), "Output weights file was not created"
    loaded = load_weights(output_path)
    assert isinstance(loaded, EvalWeights)


@pytest.mark.slow
def test_run_tuning_mse_does_not_increase(tmp_path: Path) -> None:
    """After tuning, the output weights file is a valid EvalWeights instance."""
    db_path = tmp_path / "test2.jsonl"
    output_path = tmp_path / "tuned2.json"

    config = TuningConfig(
        db_path=db_path,
        output_weights_path=output_path,
        collection_games=5,
        collection_depth=1,
        spsa_options=SPSAOptions(max_iterations=5, verbose=False),
        do_calibrate_k=False,
        verbose=False,
    )
    tuned = run_tuning(config)

    assert output_path.exists()
    loaded = load_weights(output_path)
    # The returned and loaded weights should match
    assert tuned.to_dict() == loaded.to_dict()
