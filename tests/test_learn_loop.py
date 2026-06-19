"""Tests for the persistent self-play learning loop.

These avoid real (slow) game collection by stubbing the collect/optimize/MSE
primitives, so they exercise the loop's control flow and — crucially — the
validation gate that decides whether to overwrite the engine's canonical weights.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel import learn_loop
from chess_game.texel.learn_loop import (
    LearnLoopConfig,
    RoundResult,
    _round_seed,
    _tune_round,
    run_learn_loop,
)
from chess_game.texel.position_db import PositionDB


def _toy_db() -> PositionDB:
    start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    after = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    return PositionDB.from_pairs([(start, 1.0), (after, 0.0)] * 5)


# --- config validation ------------------------------------------------------

@pytest.mark.parametrize(
    "kwargs",
    [
        {"rounds": 0},
        {"games_per_round": 0},
        {"validation_fraction": 0.0},
        {"validation_fraction": 1.0},
        {"min_validation_improvement": -0.1},
    ],
)
def test_config_rejects_bad_values(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        LearnLoopConfig(**kwargs)


def test_config_accepts_sensible_defaults() -> None:
    cfg = LearnLoopConfig()
    assert cfg.rounds >= 1 and 0.0 < cfg.validation_fraction < 1.0


# --- small helpers ----------------------------------------------------------

def test_round_seed_derivation() -> None:
    assert _round_seed(None, 3) is None
    assert _round_seed(100, 0) == 100
    assert _round_seed(100, 2) == 102


def test_round_result_improvement_sign() -> None:
    better = RoundResult(0, 10, 1.0, 0.09, 0.08, True)
    worse = RoundResult(0, 10, 1.0, 0.09, 0.10, False)
    assert better.improvement == pytest.approx(0.01)
    assert worse.improvement == pytest.approx(-0.01)


# --- validation gate --------------------------------------------------------

def _stub_tuning(
    monkeypatch: pytest.MonkeyPatch,
    *,
    baseline: float,
    candidate: float,
) -> EvalWeights:
    """Stub calibrate_k/optimize/MSE so the gate decision is deterministic."""
    candidate_weights = EvalWeights.default()
    monkeypatch.setattr(learn_loop, "calibrate_k", lambda pairs, w: 1.0)
    monkeypatch.setattr(learn_loop, "optimize", lambda w, db, opts: candidate_weights)

    def fake_mse(pairs, weights, opts=None):  # noqa: ANN001
        return candidate if weights is candidate_weights else baseline

    monkeypatch.setattr(learn_loop, "mean_squared_error", fake_mse)
    return candidate_weights


def test_tune_round_promotes_when_candidate_is_better(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate_weights = _stub_tuning(monkeypatch, baseline=0.090, candidate=0.080)
    saved: dict = {}
    monkeypatch.setattr(
        learn_loop, "save_weights", lambda w, p: saved.update(weights=w, path=p)
    )
    monkeypatch.setattr(learn_loop, "invalidate_weights_cache", lambda: saved.update(invalidated=True))

    cfg = LearnLoopConfig(weights_path=tmp_path / "tuned.json")
    result = _tune_round(cfg, _toy_db(), round_index=0)

    assert result.promoted is True
    assert saved["weights"] is candidate_weights
    assert saved["path"] == cfg.weights_path
    assert saved.get("invalidated") is True


def test_tune_round_keeps_existing_when_candidate_not_better(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_tuning(monkeypatch, baseline=0.080, candidate=0.085)
    saved: dict = {}
    monkeypatch.setattr(learn_loop, "save_weights", lambda w, p: saved.update(called=True))
    monkeypatch.setattr(learn_loop, "invalidate_weights_cache", lambda: None)

    cfg = LearnLoopConfig(weights_path=tmp_path / "tuned.json")
    result = _tune_round(cfg, _toy_db(), round_index=0)

    assert result.promoted is False
    assert "called" not in saved  # canonical weights left untouched


def test_min_improvement_threshold_blocks_marginal_gain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_tuning(monkeypatch, baseline=0.0900, candidate=0.0899)
    monkeypatch.setattr(learn_loop, "save_weights", lambda w, p: None)
    monkeypatch.setattr(learn_loop, "invalidate_weights_cache", lambda: None)

    cfg = LearnLoopConfig(
        weights_path=tmp_path / "tuned.json", min_validation_improvement=0.01
    )
    result = _tune_round(cfg, _toy_db(), round_index=0)
    assert result.promoted is False


# --- end-to-end loop with stubbed collection --------------------------------

def test_run_learn_loop_iterates_rounds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_tuning(monkeypatch, baseline=0.090, candidate=0.080)
    monkeypatch.setattr(learn_loop, "save_weights", lambda w, p: None)
    monkeypatch.setattr(learn_loop, "invalidate_weights_cache", lambda: None)
    monkeypatch.setattr(learn_loop, "_collect_round", lambda cfg, idx: _toy_db())

    cfg = LearnLoopConfig(rounds=3, weights_path=tmp_path / "tuned.json", verbose=False)
    results = run_learn_loop(cfg)

    assert [r.round_index for r in results] == [0, 1, 2]
    assert all(r.promoted for r in results)
