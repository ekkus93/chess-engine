"""Universal Chess Interface (UCI) protocol implementation.

Run as a module::

    uv run python -m chess_game.uci

Or via the console script::

    chess-uci

The engine responds to the standard UCI command set: ``uci``, ``isready``,
``ucinewgame``, ``position``, ``go``, ``stop``, ``debug``, and ``quit``.
"""
from __future__ import annotations

import sys
import threading
import time
from dataclasses import dataclass, field
from typing import IO

from chess_game.chess.ai import get_legal_moves, search_root_depth
from chess_game.chess.ai_search_types import SearchContext, SearchStats
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import record_position
from chess_game.chess.constants import PieceType
from chess_game.chess.coords import index_to_algebraic
from chess_game.chess.move import parse_move_notation
from chess_game.chess.opening_book import get_bundled_opening_book
from chess_game.chess.types import Color, LegalMove

_ENGINE_NAME = "ChessEngine"
_ENGINE_AUTHOR = "Phillip Chin"

_PROMO_CHAR: dict[PieceType, str] = {
    PieceType.QUEEN: "q",
    PieceType.ROOK: "r",
    PieceType.BISHOP: "b",
    PieceType.KNIGHT: "n",
}

# Time (ms) thresholds → depth mapping for wtime/btime allocation.
_TIME_TO_DEPTH_TABLE: list[tuple[int, int]] = [
    (500, 2),
    (2000, 3),
    (8000, 4),
]
_DEPTH_HIGH = 5
_DEPTH_DEFAULT = 3


# ---------------------------------------------------------------------------
# Async search control (replaces module-level globals)
# ---------------------------------------------------------------------------


@dataclass
class _SearchControl:
    """Mutable container for the active search thread and stop signal."""

    stop_event: threading.Event = field(default_factory=threading.Event)
    thread: threading.Thread | None = None


_ctrl = _SearchControl()


# ---------------------------------------------------------------------------
# Public utility
# ---------------------------------------------------------------------------


def legal_move_to_uci(move: LegalMove) -> str:
    """Return the UCI string for *move*, e.g. ``"e2e4"`` or ``"e7e8q"``."""
    result = index_to_algebraic(move.start) + index_to_algebraic(move.end)
    if move.promotion is not None:
        result += _PROMO_CHAR[move.promotion]
    return result


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------


@dataclass
class UciState:
    """Mutable per-session UCI state."""

    board: Board = field(default_factory=Board)
    position_counts: dict[str, int] = field(default_factory=dict)
    debug: bool = False


def _reset(state: UciState) -> None:
    """Reset board to the starting position and clear position counts."""
    state.board = Board()
    state.position_counts = {}
    record_position(state.board, state.position_counts)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _out(message: str) -> None:
    """Write *message* to the current stdout with a flush."""
    print(message, flush=True)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def handle_uci(state: UciState, tokens: list[str]) -> None:
    """Respond to the ``uci`` handshake."""
    del state, tokens
    _out(f"id name {_ENGINE_NAME}")
    _out(f"id author {_ENGINE_AUTHOR}")
    _out("uciok")


def handle_isready(state: UciState, tokens: list[str]) -> None:
    """Respond to ``isready``."""
    del state, tokens
    _out("readyok")


def handle_ucinewgame(state: UciState, tokens: list[str]) -> None:
    """Reset internal state for a new game."""
    del tokens
    _reset(state)


def handle_quit(state: UciState, tokens: list[str]) -> None:
    """Exit the process."""
    del state, tokens
    sys.exit(0)


def handle_debug(state: UciState, tokens: list[str]) -> None:
    """Toggle debug mode (``debug on`` / ``debug off``)."""
    if len(tokens) >= 2:
        state.debug = tokens[1] == "on"


def handle_stop(state: UciState, tokens: list[str] | None = None) -> None:
    """Signal any running search to stop and wait for it to finish."""
    del state, tokens
    _ctrl.stop_event.set()
    if _ctrl.thread is not None and _ctrl.thread.is_alive():
        _ctrl.thread.join(timeout=5.0)


# ---------------------------------------------------------------------------
# position command
# ---------------------------------------------------------------------------


def handle_position(state: UciState, tokens: list[str]) -> None:
    """Set up the board from ``position startpos …`` or ``position fen … …``."""
    if len(tokens) < 2:
        return

    moves_idx: int | None = None
    try:
        moves_idx = tokens.index("moves")
    except ValueError:
        pass

    subcommand = tokens[1]
    move_tokens: list[str] = []

    if subcommand == "startpos":
        state.board = Board()
        state.position_counts = {}
        record_position(state.board, state.position_counts)
        move_tokens = tokens[moves_idx + 1:] if moves_idx is not None else []

    elif subcommand == "fen":
        fen_end = moves_idx if moves_idx is not None else len(tokens)
        fen_str = " ".join(tokens[2:fen_end])
        try:
            state.board = Board.from_fen(fen_str)
        except ValueError as exc:
            if state.debug:
                _out(f"info string error loading fen: {exc}")
            return
        state.position_counts = {}
        record_position(state.board, state.position_counts)
        move_tokens = tokens[moves_idx + 1:] if moves_idx is not None else []

    _replay_moves(state, move_tokens)


def _replay_moves(state: UciState, move_tokens: list[str]) -> None:
    """Apply each UCI move string in *move_tokens* to *state.board* in order."""
    for move_str in move_tokens:
        try:
            move = parse_move_notation(move_str)
        except ValueError:
            if state.debug:
                _out(f"info string illegal move notation: {move_str}")
            break
        success = state.board.make_move(move.start, move.end, promotion=move.promotion)
        if not success:
            if state.debug:
                _out(f"info string illegal move: {move_str}")
            break
        record_position(state.board, state.position_counts)


# ---------------------------------------------------------------------------
# go command — search
# ---------------------------------------------------------------------------


@dataclass
class _GoParams:
    """Parsed parameters from a ``go`` command."""

    depth: int | None = None
    movetime_ms: int | None = None
    wtime_ms: int | None = None
    btime_ms: int | None = None
    winc_ms: int = 0
    binc_ms: int = 0
    movestogo: int | None = None
    infinite: bool = False


def _parse_go_tokens(tokens: list[str]) -> _GoParams:
    """Parse ``go`` subcommand tokens into a :class:`_GoParams`."""
    params = _GoParams()
    i = 1
    while i < len(tokens):
        tok = tokens[i]
        has_next = i + 1 < len(tokens)
        if tok == "depth" and has_next:
            params.depth = int(tokens[i + 1])
            i += 2
        elif tok == "movetime" and has_next:
            params.movetime_ms = int(tokens[i + 1])
            i += 2
        elif tok == "wtime" and has_next:
            params.wtime_ms = int(tokens[i + 1])
            i += 2
        elif tok == "btime" and has_next:
            params.btime_ms = int(tokens[i + 1])
            i += 2
        elif tok == "winc" and has_next:
            params.winc_ms = int(tokens[i + 1])
            i += 2
        elif tok == "binc" and has_next:
            params.binc_ms = int(tokens[i + 1])
            i += 2
        elif tok == "movestogo" and has_next:
            params.movestogo = int(tokens[i + 1])
            i += 2
        elif tok == "infinite":
            params.infinite = True
            i += 1
        else:
            i += 1
    return params


def _uci_search(
    board: Board,
    depth: int,
    position_counts: dict[str, int],
) -> LegalMove | None:
    """Run iterative-deepening search and emit ``info`` lines per depth."""
    book_move = get_bundled_opening_book().find_book_move(board)
    if book_move is not None:
        pv_str = f" pv {legal_move_to_uci(book_move)}"
        _out(f"info depth 1 score cp 0 nodes 0 time 0{pv_str}")
        return book_move

    if not get_legal_moves(board):
        return None

    is_maximizing = board.turn == Color.WHITE
    stats = SearchStats()
    context = SearchContext(
        transposition_table={},
        stats=stats,
        killer_moves=[],
        position_counts=dict(position_counts),
        deterministic=False,
    )

    best_move: LegalMove | None = None
    previous_score = 0
    t0 = time.monotonic()

    for current_depth in range(1, depth + 1):
        if _ctrl.stop_event.is_set():
            break
        score, move = search_root_depth(
            board, current_depth, is_maximizing, previous_score, context
        )
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        pv_str = f" pv {legal_move_to_uci(move)}" if move is not None else ""
        _out(
            f"info depth {current_depth} score cp {score}"
            f" nodes {stats.nodes} time {elapsed_ms}{pv_str}"
        )
        previous_score = score
        if move is not None:
            best_move = move

    return best_move


def _run_go(state: UciState, depth: int) -> None:
    """Execute search and emit ``bestmove``."""
    move = _uci_search(state.board, depth, state.position_counts)
    _out(f"bestmove {legal_move_to_uci(move)}" if move is not None else "bestmove (none)")


def handle_go(state: UciState, tokens: list[str]) -> None:
    """Handle ``go depth``, ``go movetime``, ``go wtime/btime``, or ``go infinite``."""
    _ctrl.stop_event = threading.Event()

    params = _parse_go_tokens(tokens)

    if params.depth is not None:
        _run_go(state, params.depth)
        return

    search_depth, movetime_ms = _resolve_search_depth(params, state.board.turn)

    _ctrl.thread = threading.Thread(
        target=_run_go, args=(state, search_depth), daemon=True
    )
    _ctrl.thread.start()

    timer: threading.Thread | None = None
    if movetime_ms is not None:
        timer = threading.Thread(
            target=_stop_after, args=(movetime_ms,), daemon=True
        )
        timer.start()

    if not params.infinite:
        _ctrl.thread.join()
        if timer is not None:
            timer.join(timeout=0)


def _resolve_search_depth(params: _GoParams, color: Color) -> tuple[int, int | None]:
    """Return (search_depth, movetime_ms) for the given go parameters."""
    if params.movetime_ms is not None:
        return _DEPTH_HIGH, params.movetime_ms
    if params.infinite:
        return 99, None
    if params.wtime_ms is not None or params.btime_ms is not None:
        allocated = _allocate_time(params, color)
        return _time_to_depth(allocated), allocated
    return _DEPTH_DEFAULT, None


def _stop_after(delay_ms: int) -> None:
    """Set the stop event after *delay_ms* milliseconds."""
    time.sleep(delay_ms / 1000.0)
    _ctrl.stop_event.set()


# ---------------------------------------------------------------------------
# Time management
# ---------------------------------------------------------------------------


@dataclass
class _TimeControl:
    """Side-to-move time parameters extracted from a ``go`` command."""

    remaining_ms: int
    increment_ms: int
    movestogo: int | None


def _allocate_time(params: _GoParams, color: Color) -> int:
    """Return milliseconds to spend on this move given *params* and *color*."""
    tc = _TimeControl(
        remaining_ms=(params.wtime_ms or 0) if color == Color.WHITE else (params.btime_ms or 0),
        increment_ms=params.winc_ms if color == Color.WHITE else params.binc_ms,
        movestogo=params.movestogo,
    )
    divisor = tc.movestogo if tc.movestogo is not None else 30
    allocated = tc.remaining_ms // divisor + tc.increment_ms
    allocated = max(allocated, 100)
    allocated = min(allocated, int(tc.remaining_ms * 0.8))
    return allocated


def _time_to_depth(allocated_ms: int) -> int:
    """Map allocated milliseconds to a search depth."""
    for threshold, depth in _TIME_TO_DEPTH_TABLE:
        if allocated_ms < threshold:
            return depth
    return _DEPTH_HIGH


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


_HANDLERS = {
    "uci": handle_uci,
    "isready": handle_isready,
    "ucinewgame": handle_ucinewgame,
    "position": handle_position,
    "go": handle_go,
    "stop": handle_stop,
    "debug": handle_debug,
    "quit": handle_quit,
}


def uci_loop(
    input_stream: IO[str] = sys.stdin,
    output_stream: IO[str] = sys.stdout,
) -> None:
    """Read UCI commands from *input_stream* and write responses to *output_stream*.

    Runs until ``quit`` is received or input is exhausted.
    """
    _ctrl.stop_event = threading.Event()
    state = UciState()
    record_position(state.board, state.position_counts)

    original_stdout = sys.stdout
    sys.stdout = output_stream
    try:
        for raw_line in input_stream:
            line = raw_line.strip()
            if not line:
                continue
            tokens = line.split()
            handler = _HANDLERS.get(tokens[0])
            if handler is None:
                continue
            handler(state, tokens)
    finally:
        sys.stdout = original_stdout


if __name__ == "__main__":
    uci_loop()
