"""Validate tuned weights by playing against baseline."""
from __future__ import annotations

import dataclasses
from pathlib import Path

from chess_game.chess import Board
from chess_game.chess.ai import BestMoveOptions, get_best_move
from chess_game.chess.board.game_state import (
    is_checkmate,
    is_fifty_move_rule,
    is_insufficient_material,
    is_stalemate,
    record_position,
)
from chess_game.chess.constants import Color
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.position_utils import position_key as _position_key_fn
from chess_game.texel.weights_io import load_weights_or_default


@dataclasses.dataclass
class ValidationResult:
    """Result of a validation match between tuned and baseline weights."""

    tuned_wins: int = 0
    baseline_wins: int = 0
    draws: int = 0

    @property
    def total_games(self) -> int:
        """Total number of games played."""
        return self.tuned_wins + self.baseline_wins + self.draws

    @property
    def tuned_win_rate(self) -> float:
        """Fraction of games won by the tuned engine."""
        if self.total_games == 0:
            return 0.0
        return self.tuned_wins / self.total_games


def _is_draw(board: Board, position_counts: dict[str, int]) -> bool:
    """Return True when the current position is a draw by rule."""
    if is_fifty_move_rule(board):
        return True
    if is_insufficient_material(board):
        return True
    if position_counts.get(_position_key(board), 0) >= 3:
        return True
    return False


def _position_key(board: Board) -> str:
    """Lightweight position key for repetition counting."""
    return _position_key_fn(board)


def _play_one_game(
    tuned_weights: EvalWeights,
    baseline: EvalWeights,
    tuned_is_white: bool,
    depth: int,
) -> str:
    """Play one game; return 'tuned', 'baseline', or 'draw'."""
    board = Board()
    position_counts: dict[str, int] = {}
    record_position(board, position_counts)

    for _ in range(400):
        is_white_turn = board.turn == Color.WHITE
        w = tuned_weights if (tuned_is_white == is_white_turn) else baseline
        move = get_best_move(
            board, depth=depth, book_options=BestMoveOptions(weights=w, use_opening_book=False)
        )
        if move is None:
            break
        board.make_move(move.start, move.end, move.promotion)
        record_position(board, position_counts)
        if is_checkmate(board):
            winner_was_white = board.turn != Color.WHITE
            return "tuned" if (winner_was_white == tuned_is_white) else "baseline"
        if is_stalemate(board) or _is_draw(board, position_counts):
            return "draw"
    return "draw"


def run_validation_match(
    tuned_weights: EvalWeights,
    num_games: int = 100,
    depth: int = 2,
    verbose: bool = False,
) -> ValidationResult:
    """Play tuned vs baseline; alternate which side uses tuned weights."""
    result = ValidationResult()
    baseline = EvalWeights.default()

    for game_idx in range(num_games):
        tuned_is_white = game_idx % 2 == 0
        outcome = _play_one_game(tuned_weights, baseline, tuned_is_white, depth)
        if outcome == "tuned":
            result.tuned_wins += 1
        elif outcome == "baseline":
            result.baseline_wins += 1
        else:
            result.draws += 1

        if verbose and (game_idx + 1) % 10 == 0:
            print(
                f"  Game {game_idx + 1}/{num_games}: "
                f"T={result.tuned_wins} B={result.baseline_wins} D={result.draws}"
            )

    return result


if __name__ == "__main__":
    import argparse

    _parser = argparse.ArgumentParser(description="Validate tuned weights")
    _parser.add_argument("--weights", required=True)
    _parser.add_argument("--games", type=int, default=100)
    _parser.add_argument("--depth", type=int, default=2)
    _args = _parser.parse_args()
    _weights = load_weights_or_default(Path(_args.weights))
    _result = run_validation_match(_weights, _args.games, _args.depth, verbose=True)
    print(
        f"\nResult: {_result.tuned_wins}W/{_result.baseline_wins}L/{_result.draws}D "
        f"({_result.tuned_win_rate:.1%} win rate)"
    )
    if _result.tuned_win_rate > 0.55:
        print("PASS: Tuned weights show meaningful improvement (>55% win rate)")
    else:
        print("NOTE: Win rate below 55% threshold — more tuning may be needed")
