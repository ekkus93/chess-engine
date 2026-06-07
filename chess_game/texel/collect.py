"""Self-play data collection for Texel tuning."""
from __future__ import annotations

import argparse
import dataclasses
from pathlib import Path
from typing import Optional

from chess_game.chess import Board
from chess_game.chess.ai import BestMoveOptions, get_best_move
from chess_game.chess.board.game_state import is_checkmate, is_stalemate
from chess_game.chess.constants import Color
from chess_game.chess.eval_weights import EvalWeights
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


def _play_game(options: CollectionOptions) -> Optional[GameRecord]:
    """Play one self-play game and return a GameRecord, or None if incomplete."""
    board = Board()
    positions: list[str] = []
    outcome: Optional[float] = None

    for ply in range(options.max_moves):
        current_color = board.turn

        if is_checkmate(board):
            outcome = 0.0 if current_color == Color.WHITE else 1.0
            break
        if is_stalemate(board):
            outcome = 0.5
            break

        book_opts = BestMoveOptions(
            use_opening_book=True,
            random_opening_book=True,
        )
        move = get_best_move(board, options.depth, book_options=book_opts)
        if move is None:
            outcome = 0.5
            break

        if ply >= options.skip_opening_plies:
            positions.append(board.to_fen())

        board.make_move(move.start, move.end, move.promotion)

    if outcome is None:
        return None

    return GameRecord(positions=positions, outcome=outcome)


def collect_games(options: CollectionOptions) -> PositionDB:
    """Run self-play games and return a PositionDB with the collected positions."""
    if options.db_path.exists():
        db = PositionDB.load(options.db_path)
    else:
        db = PositionDB()

    for game_idx in range(options.num_games):
        record = _play_game(options)
        if record is None:
            if options.verbose:
                print(f"  game {game_idx + 1}: max_moves reached — skipped")
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
    args = parser.parse_args()

    collected_db = collect_games(
        CollectionOptions(
            db_path=args.db,
            num_games=args.games,
            depth=args.depth,
            verbose=args.verbose,
        )
    )
    print(f"DB size: {len(collected_db)} positions")
