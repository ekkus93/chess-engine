"""Self-play data collection for Texel tuning."""
from __future__ import annotations

import argparse
import dataclasses
import random
from pathlib import Path
from typing import Optional

from chess_game.chess import Board
from chess_game.chess.ai import BestMoveOptions, get_best_move
from chess_game.chess.board.game_state import (
    is_checkmate,
    is_fifty_move_rule,
    is_insufficient_material,
    is_stalemate,
)
from chess_game.chess.constants import Color
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.position_utils import position_key as _position_key_fn
from chess_game.texel.position_db import GameRecord, PositionDB


@dataclasses.dataclass
class CollectionOptions:
    """Options controlling self-play game collection."""

    db_path: Path
    num_games: int = 200
    depth: int = 1
    weights: Optional[EvalWeights] = None
    verbose: bool = False
    skip_opening_plies: int = 10
    max_moves: int = 200
    seed: Optional[int] = None
    max_move_result: str = "draw"


def _is_draw_by_rule(
    board: Board,
    position_counts: dict[str, int],
) -> bool:
    """Return True when the current position is drawn by a game rule."""
    if is_fifty_move_rule(board):
        return True
    if is_insufficient_material(board):
        return True
    pos = _position_key_fn(board)
    return position_counts.get(pos, 0) >= 3


def _play_game(
    options: CollectionOptions,
    rng: random.Random,
) -> Optional[GameRecord]:
    """Play one self-play game and return a GameRecord, or None if discarded."""
    board = Board()
    positions: list[str] = []
    outcome: Optional[float] = None
    position_counts: dict[str, int] = {}

    for ply in range(options.max_moves):
        current_color = board.turn
        pos = _position_key_fn(board)
        position_counts[pos] = position_counts.get(pos, 0) + 1

        if is_checkmate(board):
            outcome = 0.0 if current_color == Color.WHITE else 1.0
            break
        if is_stalemate(board) or _is_draw_by_rule(board, position_counts):
            outcome = 0.5
            break

        book_opts = BestMoveOptions(
            use_opening_book=True,
            random_opening_book=True,
            weights=options.weights,
            rng_seed=rng.randint(0, 2**31),
        )
        move = get_best_move(board, options.depth, book_options=book_opts)
        if move is None:
            outcome = 0.5
            break

        if ply >= options.skip_opening_plies:
            positions.append(board.to_fen())

        board.make_move(move.start, move.end, move.promotion)

    if outcome is None:
        if options.max_move_result == "draw":
            outcome = 0.5
        else:
            return None

    return GameRecord(positions=positions, outcome=outcome)


def collect_games(options: CollectionOptions) -> PositionDB:
    """Run self-play games and return a PositionDB with the collected positions."""
    rng = random.Random(options.seed)

    if options.db_path.exists():
        db = PositionDB.load(options.db_path)
    else:
        db = PositionDB()

    for game_idx in range(options.num_games):
        record = _play_game(options, rng)
        if record is None:
            if options.verbose:
                print(f"  game {game_idx + 1}: max_moves reached — discarded")
            continue
        db.add_game(record)
        if options.verbose:
            print(
                f"  game {game_idx + 1}: outcome={record.outcome:.1f}"
                f" positions={len(record.positions)}"
            )

    db.save(options.db_path)
    return db


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect self-play positions for Texel tuning.")
    parser.add_argument("--games", type=int, default=200, help="Number of games to play")
    parser.add_argument("--depth", type=int, default=1, help="Search depth per move")
    parser.add_argument("--db", type=Path, default=Path("texel_positions.jsonl"), help="DB path")
    parser.add_argument("--verbose", action="store_true", help="Print per-game info")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()

    collected_db = collect_games(
        CollectionOptions(
            db_path=args.db,
            num_games=args.games,
            depth=args.depth,
            verbose=args.verbose,
            seed=args.seed,
        )
    )
    print(f"DB size: {len(collected_db)} positions")
