"""Generate diverse chess positions via Stockfish self-play.

Each game starts from a randomly selected opening FEN and plays at the given
depth until a terminal condition is reached or *max_ply* moves have been made.
Positions at plies in [min_ply, max_ply] are collected and deduplicated.

Typical use::

    uv run python -m chess_game.texel.stockfish_generate \\
        --games 500 --depth 8 --output positions.jsonl
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Optional

from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_checkmate, is_stalemate
from chess_game.chess.move import parse_move_notation
from chess_game.texel.stockfish_annotate import StockfishProcess

_STOCKFISH_PATH = "stockfish"

# A short list of common opening FENs used to diversify self-play.
_OPENING_FENS: list[str] = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1",
    "rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq c3 0 1",
    "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1",
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
    "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2",
    "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq d6 0 2",
    "rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
    "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
]


def _play_game(
    white: StockfishProcess,
    black: StockfishProcess,
    start_fen: str,
    *,
    min_ply: int,
    max_ply: int,
) -> list[str]:
    """Play one game and return FENs collected at plies in [min_ply, max_ply]."""
    board = Board.from_fen(start_fen)
    move_history: list[str] = []
    collected: list[str] = []

    for ply in range(max_ply):
        if is_checkmate(board) or is_stalemate(board):
            break

        current_sf = white if ply % 2 == 0 else black
        best_move_uci: Optional[str] = current_sf.find_best_move(start_fen, move_history)

        if best_move_uci is None:
            break

        move_history.append(best_move_uci)

        try:
            move = parse_move_notation(best_move_uci)
        except ValueError:
            break

        if not board.make_move(move.start, move.end, promotion=move.promotion):
            break

        if ply >= min_ply:
            collected.append(board.to_fen())

    return collected


def generate_positions(
    n_games: int,
    *,
    depth: int = 8,
    stockfish_path: str = _STOCKFISH_PATH,
    min_ply: int = 16,
    max_ply: int = 60,
    seed: int = 0,
) -> list[str]:
    """Generate diverse positions via Stockfish self-play.

    Args:
        n_games: Number of games to play.
        depth: Stockfish search depth per move (higher → stronger, slower).
        stockfish_path: Path to the Stockfish binary.
        min_ply: First ply from which positions are collected.
        max_ply: Last ply at which positions are collected.
        seed: Random seed for opening selection.

    Returns:
        Deduplicated list of FEN strings.
    """
    rng = random.Random(seed)
    all_fens: set[str] = set()

    with (
        StockfishProcess(stockfish_path=stockfish_path, depth=depth) as white,
        StockfishProcess(stockfish_path=stockfish_path, depth=depth) as black,
    ):
        for game_idx in range(n_games):
            opening = rng.choice(_OPENING_FENS)
            game_fens = _play_game(white, black, opening, min_ply=min_ply, max_ply=max_ply)
            all_fens.update(game_fens)

            if (game_idx + 1) % 10 == 0:
                print(
                    f"  game {game_idx + 1}/{n_games}:"
                    f" {len(all_fens)} unique positions",
                    flush=True,
                )

    return list(all_fens)


if __name__ == "__main__":
    import argparse

    from chess_game.texel.position_db import GameRecord, PositionDB

    _parser = argparse.ArgumentParser(
        description="Generate positions via Stockfish self-play."
    )
    _parser.add_argument("--games", type=int, default=200, help="Number of games.")
    _parser.add_argument("--depth", type=int, default=8, help="Stockfish search depth.")
    _parser.add_argument(
        "--output", required=True, type=Path, help="Output PositionDB JSONL path."
    )
    _parser.add_argument("--min-ply", type=int, default=16, help="First ply to collect.")
    _parser.add_argument("--max-ply", type=int, default=60, help="Last ply to collect.")
    _parser.add_argument("--seed", type=int, default=0, help="Random seed.")
    _parser.add_argument(
        "--stockfish", type=str, default=_STOCKFISH_PATH, help="Path to Stockfish binary."
    )
    _args = _parser.parse_args()

    print(f"Generating positions from {_args.games} Stockfish self-play games …")
    _fens = generate_positions(
        _args.games,
        depth=_args.depth,
        stockfish_path=_args.stockfish,
        min_ply=_args.min_ply,
        max_ply=_args.max_ply,
        seed=_args.seed,
    )
    print(f"Collected {len(_fens)} unique FENs")

    _db = PositionDB()
    for _fen in _fens:
        _db.add_game(GameRecord(positions=[_fen], outcome=0.5))
    _db.save(_args.output)
    print(f"Saved to {_args.output}")
