"""Annotate chess positions with Stockfish centipawn evaluations.

Communicates with a Stockfish subprocess via UCI to produce White-relative
centipawn scores for a list of FEN positions.  These scores replace the noisy
game-outcome labels used by default Texel tuning.

Typical use::

    from chess_game.texel.stockfish_annotate import annotate_db
    from chess_game.texel.position_db import PositionDB
    from pathlib import Path

    db = PositionDB.load(Path("texel_positions.jsonl"))
    scores = annotate_db(db, depth=10, n_workers=4)
    # scores: {fen: score_cp_or_none}
"""
from __future__ import annotations

import contextlib
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from chess_game.chess.board import Board
from chess_game.chess.types import Color
from chess_game.texel.position_db import PositionDB

_NONE_MOVE = "(none)"

_STOCKFISH_PATH = "stockfish"


class StockfishProcess:
    """A single Stockfish subprocess communicating over UCI.

    Must be used as a context manager::

        with StockfishProcess(depth=10) as sf:
            score = sf.eval_fen(fen)
    """

    def __init__(
        self,
        stockfish_path: str = _STOCKFISH_PATH,
        depth: int = 10,
    ) -> None:
        self._depth = depth
        self._stockfish_path = stockfish_path
        self._stack = contextlib.ExitStack()
        self._proc: subprocess.Popen | None = None

    def __enter__(self) -> StockfishProcess:
        self._proc = self._stack.enter_context(
            subprocess.Popen(
                [self._stockfish_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
            )
        )
        self._send("uci")
        self._wait_for("uciok")
        self._send("isready")
        self._wait_for("readyok")
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Send quit and wait for the process to exit."""
        try:
            self._send("quit")
        except (OSError, BrokenPipeError):
            pass
        self._stack.close()

    def _send(self, command: str) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise RuntimeError("StockfishProcess must be used as a context manager")
        self._proc.stdin.write(command + "\n")
        self._proc.stdin.flush()

    def _readline(self) -> str:
        if self._proc is None or self._proc.stdout is None:
            raise RuntimeError("StockfishProcess must be used as a context manager")
        return str(self._proc.stdout.readline())

    def _wait_for(self, token: str) -> None:
        """Read lines until one starts with *token*."""
        while True:
            line = self._readline()
            if not line or line.startswith(token):
                break

    def eval_fen(self, fen: str) -> int | None:
        """Return the White-relative centipawn score for *fen*, or None for mate.

        Sends ``position fen <fen>`` then ``go depth <depth>`` and reads until
        ``bestmove``.  Parses the last ``info depth … score cp N`` line.
        Returns ``None`` if the score is a mate distance or the position has no
        legal moves.
        """
        self._send(f"position fen {fen}")
        self._send(f"go depth {self._depth}")

        last_score_cp: int | None = None
        is_mate = False

        while True:
            line = self._readline().strip()
            if not line:
                continue
            if line.startswith("info") and "score" in line:
                parts = line.split()
                try:
                    score_idx = parts.index("score")
                    score_type = parts[score_idx + 1]
                    if score_type == "cp":
                        last_score_cp = int(parts[score_idx + 2])
                        is_mate = False
                    elif score_type == "mate":
                        is_mate = True
                except (ValueError, IndexError):
                    pass
            if line.startswith("bestmove"):
                break

        if is_mate or last_score_cp is None:
            return None

        # Score from Stockfish is from the perspective of the side to move.
        # Convert to White-relative.
        board = Board.from_fen(fen)
        if board.turn == Color.BLACK:
            last_score_cp = -last_score_cp
        return last_score_cp

    def find_best_move(
        self, start_fen: str, move_history: list[str]
    ) -> str | None:
        """Return the best-move UCI string from *start_fen* after *move_history*.

        Returns ``None`` if the position has no legal moves.
        """
        if move_history:
            position_cmd = f"position fen {start_fen} moves {' '.join(move_history)}"
        else:
            position_cmd = f"position fen {start_fen}"
        self._send(position_cmd)
        self._send(f"go depth {self._depth}")
        while True:
            line = self._readline().strip()
            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) >= 2 and parts[1] != _NONE_MOVE:
                    return parts[1]
                return None

    @property
    def depth(self) -> int:
        """Search depth configured for this process."""
        return self._depth


def annotate_fens(
    fens: list[str],
    *,
    depth: int = 10,
    n_workers: int = 4,
    stockfish_path: str = _STOCKFISH_PATH,
) -> dict[str, int | None]:
    """Annotate a list of FEN strings with Stockfish centipawn evaluations.

    Launches *n_workers* Stockfish processes and distributes FENs across them
    using a thread pool.  Each worker owns one ``StockfishProcess`` and calls
    ``eval_fen`` sequentially within its thread.

    Args:
        fens: List of FEN strings to annotate.
        depth: Stockfish search depth (default 10).
        n_workers: Number of parallel Stockfish processes (default 4).
        stockfish_path: Path to the Stockfish binary (default ``"stockfish"``).

    Returns:
        Dict mapping each input FEN to its White-relative centipawn score,
        or ``None`` for positions with mate scores or no legal moves.
    """
    if not fens:
        return {}

    slices: list[list[str]] = [[] for _ in range(n_workers)]
    for i, fen in enumerate(fens):
        slices[i % n_workers].append(fen)

    results: dict[str, int | None] = {}

    def _worker(worker_fens: list[str]) -> dict[str, int | None]:
        partial: dict[str, int | None] = {}
        with StockfishProcess(stockfish_path=stockfish_path, depth=depth) as sf:
            for fen in worker_fens:
                partial[fen] = sf.eval_fen(fen)
        return partial

    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = {
            executor.submit(_worker, worker_fens): worker_fens
            for worker_fens in slices
            if worker_fens
        }
        for future in as_completed(futures):
            results.update(future.result())

    return results


def annotate_db(
    db: PositionDB,
    *,
    depth: int = 10,
    n_workers: int = 4,
    stockfish_path: str = _STOCKFISH_PATH,
) -> dict[str, int | None]:
    """Annotate all positions in *db* with Stockfish centipawn evaluations.

    Args:
        db: Position database; outcomes are ignored, only FENs are used.
        depth: Stockfish search depth (default 10).
        n_workers: Number of parallel Stockfish processes (default 4).
        stockfish_path: Path to the Stockfish binary (default ``"stockfish"``).

    Returns:
        Dict mapping each FEN in *db* to its White-relative centipawn score,
        or ``None`` for mate/no-legal-moves positions.
    """
    fens = [fen for fen, _ in db.all_pairs()]
    return annotate_fens(
        fens, depth=depth, n_workers=n_workers, stockfish_path=stockfish_path
    )


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    from chess_game.texel.annotated_position_db import save_annotated

    _parser = argparse.ArgumentParser(
        description="Annotate a PositionDB with Stockfish centipawn scores."
    )
    _parser.add_argument(
        "--db", required=True, type=Path, help="Input PositionDB JSONL path."
    )
    _parser.add_argument(
        "--output", required=True, type=Path, help="Output annotated JSONL path."
    )
    _parser.add_argument(
        "--depth", type=int, default=10, help="Stockfish search depth."
    )
    _parser.add_argument(
        "--workers", type=int, default=4,
        help="Number of parallel Stockfish processes."
    )
    _parser.add_argument(
        "--stockfish", type=str, default=_STOCKFISH_PATH,
        help="Path to Stockfish binary."
    )
    _args = _parser.parse_args()

    _input_db = PositionDB.load(_args.db)
    print(f"Loaded {len(_input_db)} positions from {_args.db}")

    _scores = annotate_db(
        _input_db,
        depth=_args.depth,
        n_workers=_args.workers,
        stockfish_path=_args.stockfish,
    )
    _annotated = sum(1 for v in _scores.values() if v is not None)
    print(f"Annotated {_annotated}/{len(_scores)} positions (rest are mate scores)")

    save_annotated(_input_db, _scores, _args.output)
    print(f"Saved annotated DB to {_args.output}")
