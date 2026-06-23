"""Tests for Stockfish-targeted feature matrix and tuning helpers."""
from __future__ import annotations

import numpy as np

from chess_game.chess.eval_weights import EvalWeights
from chess_game.texel.annotated_position_db import AnnotatedPositionDB
from chess_game.texel.features import compute_sf_feature_matrix, outcomes_from_sf
from chess_game.texel.position_db import GameRecord

_FEN_A = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
_FEN_B = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
_FEN_C = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"

_K = 1.13


def test_outcomes_from_sf_zero_score() -> None:
    pairs = [(_FEN_A, 0)]
    outcomes = outcomes_from_sf(pairs, _K)
    assert abs(float(outcomes[0]) - 0.5) < 0.01


def test_outcomes_from_sf_large_positive() -> None:
    pairs = [(_FEN_A, 900)]
    outcomes = outcomes_from_sf(pairs, _K)
    assert float(outcomes[0]) > 0.9


def test_outcomes_from_sf_large_negative() -> None:
    pairs = [(_FEN_A, -900)]
    outcomes = outcomes_from_sf(pairs, _K)
    assert float(outcomes[0]) < 0.1


def test_compute_sf_feature_matrix_shape() -> None:
    db = AnnotatedPositionDB()
    for fen in [_FEN_A, _FEN_B, _FEN_C]:
        db.add_game(GameRecord(positions=[fen], outcome=0.5))
    db.sf_scores = {_FEN_A: 30, _FEN_B: -20, _FEN_C: 10}

    weights = EvalWeights()
    d = len(weights.to_flat_list())
    matrix = compute_sf_feature_matrix(db, weights, k=_K, n_jobs=1)
    assert matrix is not None
    assert matrix.F.shape == (3, d)
    assert matrix.outcomes.shape == (3,)


def test_compute_sf_feature_matrix_excludes_none() -> None:
    db = AnnotatedPositionDB()
    for fen in [_FEN_A, _FEN_B, _FEN_C]:
        db.add_game(GameRecord(positions=[fen], outcome=0.5))
    # Only two are annotated; one is None (mate)
    db.sf_scores = {_FEN_A: 30, _FEN_B: None, _FEN_C: 10}

    weights = EvalWeights()
    matrix = compute_sf_feature_matrix(db, weights, k=_K, n_jobs=1)
    assert matrix is not None
    assert matrix.F.shape[0] == 2


def test_compute_sf_feature_matrix_all_none_returns_none() -> None:
    db = AnnotatedPositionDB()
    db.add_game(GameRecord(positions=[_FEN_A], outcome=0.5))
    db.sf_scores = {_FEN_A: None}

    weights = EvalWeights()
    matrix = compute_sf_feature_matrix(db, weights, k=_K, n_jobs=1)
    assert matrix is None


def test_compute_sf_feature_matrix_outcomes_in_range() -> None:
    db = AnnotatedPositionDB()
    for fen in [_FEN_A, _FEN_B]:
        db.add_game(GameRecord(positions=[fen], outcome=0.5))
    db.sf_scores = {_FEN_A: 200, _FEN_B: -200}

    weights = EvalWeights()
    matrix = compute_sf_feature_matrix(db, weights, k=_K, n_jobs=1)
    assert matrix is not None
    assert np.all(matrix.outcomes > 0)
    assert np.all(matrix.outcomes < 1)
