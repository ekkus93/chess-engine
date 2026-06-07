"""Tests for Texel loss functions."""
from __future__ import annotations

import math

from chess_game.chess import Board
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.evaluation import evaluate
from chess_game.texel.loss import calibrate_k, mean_squared_error, sigmoid


STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class TestSigmoid:
    """Tests for the sigmoid / win-probability function."""

    def test_sigmoid_at_zero_returns_half(self) -> None:
        """sigmoid(0) should be 0.5."""
        result = sigmoid(0.0)
        assert abs(result - 0.5) < 1e-9

    def test_sigmoid_large_positive_near_one(self) -> None:
        """sigmoid(very large positive) should approach 1."""
        result = sigmoid(100_000.0)
        assert result > 0.999

    def test_sigmoid_large_negative_near_zero(self) -> None:
        """sigmoid(very large negative) should approach 0."""
        result = sigmoid(-100_000.0)
        assert result < 0.001


class TestMeanSquaredError:
    """Tests for the MSE loss function."""

    def test_mse_perfect_prediction_is_zero(self) -> None:
        """MSE should be zero when outcome == sigmoid(eval) for every position."""
        weights = EvalWeights.default()
        board = Board.from_fen(STARTING_FEN)
        score = float(evaluate(board, weights))
        perfect_outcome = sigmoid(score)
        pairs = [(STARTING_FEN, perfect_outcome)]
        mse = mean_squared_error(pairs, weights)
        assert math.isclose(mse, 0.0, abs_tol=1e-12)

    def test_mse_worst_prediction(self) -> None:
        """MSE should be > 0 when the outcome is clearly wrong (0.0 for starting pos)."""
        weights = EvalWeights.default()
        # sigmoid(0) = 0.5; claiming black wins from the starting position is wrong
        pairs = [(STARTING_FEN, 0.0)]
        mse = mean_squared_error(pairs, weights)
        # Expected error is (0.0 - 0.5)^2 = 0.25
        assert mse > 0.0

    def test_mse_empty_pairs_returns_zero(self) -> None:
        """MSE with an empty list of pairs should return 0."""
        weights = EvalWeights.default()
        mse = mean_squared_error([], weights)
        assert mse == 0.0

    def test_calibrate_k_returns_float_in_range(self) -> None:
        """calibrate_k should return a float within [k_min, k_max]."""
        weights = EvalWeights.default()
        pairs = [(STARTING_FEN, 0.5)]
        k = calibrate_k(pairs, weights, k_min=0.5, k_max=2.0, steps=10)
        assert 0.5 <= k <= 2.0

    def test_calibrate_k_minimises_mse(self) -> None:
        """The returned k should give MSE <= every other k tested."""
        weights = EvalWeights.default()
        pairs = [(STARTING_FEN, 0.5)]
        best_k = calibrate_k(pairs, weights, k_min=0.5, k_max=2.0, steps=10)
        best_mse = mean_squared_error(pairs, weights, best_k)
        # Verify it's no worse than a random other k in the range
        for k in [0.5, 1.0, 1.5, 2.0]:
            assert mean_squared_error(pairs, weights, k) >= best_mse - 1e-12
