"""Tests for the UCI protocol implementation (chess_game/uci.py)."""
from __future__ import annotations

import io
import sys
from typing import Optional
import pytest

from chess_game.chess.board import Board
from chess_game.chess.constants import PieceType
from chess_game.chess.types import Color, LegalMove
from chess_game.uci import (
    UciState,
    _GoParams,
    _allocate_time,
    _time_to_depth,
    handle_debug,
    handle_go,
    handle_isready,
    handle_position,
    handle_uci,
    handle_ucinewgame,
    legal_move_to_uci,
    uci_loop,
)

# ---------------------------------------------------------------------------
# Phase 1: legal_move_to_uci
# ---------------------------------------------------------------------------


def _make_move(
    start_row: int,
    start_col: int,
    end_row: int,
    end_col: int,
    promotion: Optional[PieceType] = None,
) -> LegalMove:
    from chess_game.chess.constants import ConstantSquare

    class _Sq(ConstantSquare):
        def __init__(self, row: int, col: int) -> None:
            self._row = row
            self._col = col

        @property
        def row(self) -> int:
            return self._row

        @property
        def col(self) -> int:
            return self._col

    # We need real ConstantSquare instances sourced from the board's coords.
    from chess_game.chess.coords import algebraic_to_index

    files = "abcdefgh"
    start_alg = f"{files[start_col]}{8 - start_row}"
    end_alg = f"{files[end_col]}{8 - end_row}"
    start_sq = algebraic_to_index(start_alg)
    end_sq = algebraic_to_index(end_alg)
    return LegalMove(start=start_sq, end=end_sq, promotion=promotion)


def test_legal_move_to_uci_normal() -> None:
    move = _make_move(6, 4, 4, 4)  # e2e4
    assert legal_move_to_uci(move) == "e2e4"


def test_legal_move_to_uci_promotion_queen() -> None:
    move = _make_move(1, 4, 0, 4, PieceType.QUEEN)  # e7e8q
    assert legal_move_to_uci(move) == "e7e8q"


def test_legal_move_to_uci_promotion_knight() -> None:
    move = _make_move(1, 4, 0, 4, PieceType.KNIGHT)
    assert legal_move_to_uci(move) == "e7e8n"


def test_legal_move_to_uci_promotion_rook() -> None:
    move = _make_move(1, 4, 0, 4, PieceType.ROOK)
    assert legal_move_to_uci(move) == "e7e8r"


def test_legal_move_to_uci_promotion_bishop() -> None:
    move = _make_move(1, 4, 0, 4, PieceType.BISHOP)
    assert legal_move_to_uci(move) == "e7e8b"


def test_legal_move_to_uci_no_promotion() -> None:
    move = _make_move(6, 4, 4, 4)
    result = legal_move_to_uci(move)
    assert len(result) == 4


def test_legal_move_to_uci_corner_a1() -> None:
    move = _make_move(7, 0, 6, 0)  # a1a2
    assert legal_move_to_uci(move) == "a1a2"


def test_legal_move_to_uci_corner_h8() -> None:
    move = _make_move(0, 7, 1, 7)  # h8h7
    assert legal_move_to_uci(move) == "h8h7"


# ---------------------------------------------------------------------------
# Phase 3: command handlers
# ---------------------------------------------------------------------------


def _capture(func, state: UciState, tokens: list[str]) -> str:
    """Call handler with sys.stdout redirected; return captured output."""
    buf = io.StringIO()
    orig = sys.stdout
    sys.stdout = buf
    try:
        func(state, tokens)
    finally:
        sys.stdout = orig
    # Also collect anything pytest captured on the real stdout during the call
    return buf.getvalue()


def test_handle_uci_output() -> None:
    state = UciState()
    out = _capture(handle_uci, state, ["uci"])
    lines = out.strip().splitlines()
    assert any(l.startswith("id name") for l in lines)
    assert any(l.startswith("id author") for l in lines)
    assert lines[-1] == "uciok"


def test_handle_isready() -> None:
    state = UciState()
    out = _capture(handle_isready, state, ["isready"])
    assert out.strip() == "readyok"


def test_handle_ucinewgame_resets_board() -> None:
    state = UciState()
    # Move a pawn so the board is not in starting position.
    # Board.get_legal_moves() returns (start, end, promotion) tuples.
    first = state.board.get_legal_moves()[0]
    state.board.make_move(first[0], first[1], first[2])
    handle_ucinewgame(state, ["ucinewgame"])
    assert state.board.to_fen().startswith(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
    )


def test_handle_quit_exits() -> None:
    from chess_game.uci import handle_quit

    state = UciState()
    with pytest.raises(SystemExit):
        handle_quit(state, ["quit"])


def test_handle_debug_on() -> None:
    state = UciState()
    handle_debug(state, ["debug", "on"])
    assert state.debug is True


def test_handle_debug_off() -> None:
    state = UciState()
    state.debug = True
    handle_debug(state, ["debug", "off"])
    assert state.debug is False


def test_handle_debug_unknown_ignored() -> None:
    state = UciState()
    handle_debug(state, ["debug", "maybe"])
    assert state.debug is False


# ---------------------------------------------------------------------------
# Phase 4: position command
# ---------------------------------------------------------------------------


def test_position_startpos() -> None:
    state = UciState()
    handle_position(state, ["position", "startpos"])
    expected = Board().to_fen()
    assert state.board.to_fen() == expected


def test_position_startpos_move_e2e4() -> None:
    state = UciState()
    handle_position(state, ["position", "startpos", "moves", "e2e4"])
    assert state.board.turn == Color.BLACK
    # White pawn should be on e4 (row 4, col 4).
    # Board.get_piece() takes a ConstantSquare.
    from chess_game.chess.coords import algebraic_to_index

    e4 = algebraic_to_index("e4")
    piece = state.board.get_piece(e4)
    assert piece is not None
    assert piece.kind == PieceType.PAWN
    assert piece.color == Color.WHITE


def test_position_startpos_three_moves() -> None:
    state = UciState()
    handle_position(
        state,
        ["position", "startpos", "moves", "e2e4", "e7e5", "g1f3"],
    )
    assert state.board.turn == Color.BLACK
    assert len(state.position_counts) == 4  # start + 3 moves


def test_position_fen_starting_position() -> None:
    state = UciState()
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    handle_position(state, ["position", "fen"] + starting_fen.split())
    assert state.board.to_fen() == Board().to_fen()


def test_position_fen_custom() -> None:
    state = UciState()
    # Position after 1.e4
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    handle_position(state, ["position", "fen"] + fen.split())
    assert state.board.turn == Color.BLACK


def test_position_fen_with_move() -> None:
    state = UciState()
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    handle_position(state, ["position", "fen"] + fen.split() + ["moves", "e7e5"])
    assert state.board.turn == Color.WHITE


def test_position_illegal_move_no_crash() -> None:
    state = UciState()
    # a1a1 is always illegal
    handle_position(state, ["position", "startpos", "moves", "a1a1"])
    # board should still be in starting position (move was rejected)
    assert state.board.turn == Color.WHITE


# ---------------------------------------------------------------------------
# Phase 5 & 6: go command
# ---------------------------------------------------------------------------


def _run_go_capture(tokens: list[str], fen: str | None = None) -> str:
    """Run handle_go on a fresh state and capture all stdout output."""
    state = UciState()
    if fen is not None:
        handle_position(state, ["position", "fen"] + fen.split())
    buf = io.StringIO()
    orig = sys.stdout
    # Redirect sys.stdout so both the main thread and any search thread write
    # to buf (threads share sys.stdout since it is a module global).
    sys.stdout = buf
    try:
        handle_go(state, tokens)
    finally:
        sys.stdout = orig
    return buf.getvalue()


def test_go_depth1_returns_bestmove() -> None:
    out = _run_go_capture(["go", "depth", "1"])
    lines = out.strip().splitlines()
    assert any(l.startswith("bestmove") for l in lines)


def test_go_depth1_bestmove_is_valid_uci() -> None:
    out = _run_go_capture(["go", "depth", "1"])
    bestmove_line = next(l for l in out.splitlines() if l.startswith("bestmove"))
    move_str = bestmove_line.split()[1]
    assert len(move_str) in (4, 5)
    assert move_str[0] in "abcdefgh"
    assert move_str[1] in "12345678"
    assert move_str[2] in "abcdefgh"
    assert move_str[3] in "12345678"


def test_go_depth2_emits_info_lines() -> None:
    # Starting position hits the opening book, so we get 1 synthetic info line.
    # A position outside the book would produce 2 (one per depth).
    out = _run_go_capture(["go", "depth", "2"])
    info_lines = [l for l in out.splitlines() if l.startswith("info depth")]
    assert len(info_lines) >= 1


def test_go_depth2_emits_two_info_lines_out_of_book() -> None:
    # Use a late-game position that is outside the opening book.
    fen = "8/8/8/8/8/8/4K3/4k3 w - - 0 1"
    out = _run_go_capture(["go", "depth", "2"], fen=fen)
    info_lines = [l for l in out.splitlines() if l.startswith("info depth")]
    assert len(info_lines) >= 2


def test_go_depth1_info_has_score_and_nodes() -> None:
    out = _run_go_capture(["go", "depth", "1"])
    info_line = next((l for l in out.splitlines() if l.startswith("info depth")), None)
    assert info_line is not None
    assert "score cp" in info_line
    assert "nodes" in info_line


def test_go_depth1_checkmate_position() -> None:
    # Fool's mate: White is checkmated
    fen = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
    out = _run_go_capture(["go", "depth", "1"], fen=fen)
    assert "bestmove (none)" in out


def test_go_depth1_stalemate_position() -> None:
    # Classic stalemate: Black king only legal move is into check
    fen = "k7/8/1Q6/8/8/8/8/K7 b - - 0 1"
    out = _run_go_capture(["go", "depth", "1"], fen=fen)
    assert "bestmove (none)" in out


def test_go_movetime_returns_bestmove() -> None:
    out = _run_go_capture(["go", "movetime", "500"])
    assert any(l.startswith("bestmove") for l in out.splitlines())


def test_go_movetime_within_time() -> None:
    import time as _time

    state = UciState()
    buf = io.StringIO()
    orig = sys.stdout
    sys.stdout = buf
    t0 = _time.monotonic()
    try:
        handle_go(state, ["go", "movetime", "800"])
    finally:
        sys.stdout = orig
    elapsed = _time.monotonic() - t0
    # Allow 3× overshoot since we only check after each full depth
    assert elapsed < 30.0


def test_go_movetime_emits_info() -> None:
    out = _run_go_capture(["go", "movetime", "500"])
    assert any(l.startswith("info depth") for l in out.splitlines())


# ---------------------------------------------------------------------------
# Phase 7: time allocation
# ---------------------------------------------------------------------------


def _tc(
    wtime: int,
    btime: int,
    winc: int = 0,
    binc: int = 0,
    movestogo: Optional[int] = None,
) -> _GoParams:
    return _GoParams(wtime_ms=wtime, btime_ms=btime, winc_ms=winc, binc_ms=binc, movestogo=movestogo)


def test_allocate_time_equal_times() -> None:
    ms = _allocate_time(_tc(60_000, 60_000), Color.WHITE)
    assert ms == pytest.approx(2000, rel=0.1)


def test_allocate_time_with_increment() -> None:
    ms = _allocate_time(_tc(60_000, 60_000, winc=1000, binc=1000), Color.WHITE)
    assert ms > 2000


def test_allocate_time_low_time_floor() -> None:
    ms = _allocate_time(_tc(500, 500), Color.WHITE)
    assert ms >= 100


def test_allocate_time_movestogo() -> None:
    ms = _allocate_time(_tc(60_000, 60_000, movestogo=20), Color.WHITE)
    assert ms == pytest.approx(3000, rel=0.1)


def test_allocate_time_black() -> None:
    ms = _allocate_time(_tc(60_000, 30_000), Color.BLACK)
    assert ms == pytest.approx(1000, rel=0.1)


def test_time_to_depth_under_500() -> None:
    assert _time_to_depth(300) == 2


def test_time_to_depth_under_2000() -> None:
    assert _time_to_depth(1000) == 3


def test_time_to_depth_under_8000() -> None:
    assert _time_to_depth(5000) == 4


def test_time_to_depth_over_8000() -> None:
    assert _time_to_depth(10_000) == 5


# ---------------------------------------------------------------------------
# Phase 8: uci_loop
# ---------------------------------------------------------------------------


def _loop(commands: str) -> str:
    """Feed *commands* to uci_loop and return captured output."""
    inp = io.StringIO(commands)
    out = io.StringIO()
    try:
        uci_loop(input_stream=inp, output_stream=out)
    except SystemExit:
        pass
    return out.getvalue()


def test_loop_uci_handshake() -> None:
    out = _loop("uci\nquit\n")
    assert "uciok" in out


def test_loop_isready() -> None:
    out = _loop("isready\nquit\n")
    assert "readyok" in out


def test_loop_full_handshake_and_quit() -> None:
    out = _loop("uci\nisready\nquit\n")
    assert "uciok" in out
    assert "readyok" in out


def test_loop_unknown_command_no_crash() -> None:
    out = _loop("xyzzy\nquit\n")
    # No crash; no output for unknown command
    assert "xyzzy" not in out


def test_loop_sequential_commands() -> None:
    out = _loop("uci\nisready\nucinewgame\nisready\nquit\n")
    assert out.count("readyok") == 2
