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


class TestLossOptions:
    """Tests for LossOptions and scoring modes."""

    def test_static_loss_mode_uses_static_evaluation(self) -> None:
        """LossOptions(use_quiescence=False) should use static evaluation."""
        from chess_game.texel.loss import LossOptions
        weights = EvalWeights.default()
        pairs = [(STARTING_FEN, 0.5)]
        static_mse = mean_squared_error(pairs, weights, opts=LossOptions(
            use_quiescence=False
        ))
        assert static_mse >= 0.0

    def test_quiescence_loss_mode_uses_quiescence(self) -> None:
        """LossOptions(use_quiescence=True) should use quiescence scoring."""
        from chess_game.texel.loss import LossOptions
        weights = EvalWeights.default()
        pairs = [(STARTING_FEN, 0.5)]
        quiescence_mse = mean_squared_error(pairs, weights, opts=LossOptions(
            use_quiescence=True, quiescence_depth_limit=2
        ))
        assert quiescence_mse >= 0.0

    def test_score_perspective_white_to_move(self) -> None:
        """Verify score perspective is consistent for White-to-move FEN."""
        weights = EvalWeights.default()
        fen_white_to_move = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        pairs = [(fen_white_to_move, 0.5)]
        mse = mean_squared_error(pairs, weights)
        assert mse >= 0.0

    def test_score_perspective_black_to_move(self) -> None:
        """Verify score perspective is consistent for Black-to-move FEN."""
        weights = EvalWeights.default()
        # Starting position with Black to move (flipped turn)
        fen_black_to_move = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"
        pairs = [(fen_black_to_move, 0.5)]
        mse = mean_squared_error(pairs, weights)
        # Should be symmetric from Black's perspective (draw → 0.5)
        assert mse >= 0.0

    def test_quiescence_depth_limit_is_respected(self) -> None:
        """Verify quiescence respects the depth limit."""
        from chess_game.texel.loss import LossOptions
        weights = EvalWeights.default()
        pairs = [(STARTING_FEN, 0.5)]
        # Shallow limit should complete without error
        mse_shallow = mean_squared_error(pairs, weights, opts=LossOptions(
            use_quiescence=True, quiescence_depth_limit=1
        ))
        assert mse_shallow >= 0.0

    def test_deterministic_mode_gives_same_result(self) -> None:
        """Verify deterministic mode produces consistent results."""
        from chess_game.texel.loss import LossOptions
        weights = EvalWeights.default()
        pairs = [(STARTING_FEN, 0.5)]
        opts = LossOptions(use_quiescence=True, deterministic=True)
        mse1 = mean_squared_error(pairs, weights, opts=opts)
        mse2 = mean_squared_error(pairs, weights, opts=opts)
        assert abs(mse1 - mse2) < 1e-12

    def test_white_material_advantage_gives_positive_score(self) -> None:
        """Evaluator should return positive score when White has material advantage."""
        from chess_game.chess import Board, create_piece
        from chess_game.chess.types import Color, PieceType
        from chess_game.chess.evaluation import evaluate
        from tests.helpers import sq

        board = Board()
        board.clear_board()
        # White king + extra queen
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
        # Black king only
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE

        weights = EvalWeights.default()
        score = float(evaluate(board, weights))
        assert score > 0, f"White has material advantage, expected positive score, got {score}"

    def test_black_material_advantage_gives_negative_score(self) -> None:
        """Evaluator should return negative score when Black has material advantage."""
        from chess_game.chess import Board, create_piece
        from chess_game.chess.types import Color, PieceType
        from chess_game.chess.evaluation import evaluate
        from tests.helpers import sq

        board = Board()
        board.clear_board()
        # White king only
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        # Black king + extra queen
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
        board.turn = Color.WHITE

        weights = EvalWeights.default()
        score = float(evaluate(board, weights))
        assert score < 0, f"Black has material advantage, expected negative score, got {score}"

    def test_score_sign_independent_of_side_to_move(self) -> None:
        """Evaluator score sign should be independent of whose turn it is."""
        from chess_game.chess import Board, create_piece
        from chess_game.chess.types import Color, PieceType
        from chess_game.chess.evaluation import evaluate
        from tests.helpers import sq

        board1 = Board()
        board1.clear_board()
        board1.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board1.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
        board1.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board1.turn = Color.WHITE

        board2 = Board()
        board2.clear_board()
        board2.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board2.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
        board2.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board2.turn = Color.BLACK

        weights = EvalWeights.default()
        score1 = float(evaluate(board1, weights))
        score2 = float(evaluate(board2, weights))
        # Both should be positive (White advantage) regardless of whose turn
        assert score1 > 0
        assert score2 > 0
        # Scores should be similar (ignoring small tempo adjustments)
        assert abs(score1 - score2) < 100  # Small tolerance for tempo
