"""Tests for chess_game/texel/stockfish_annotate.py.

All tests require a working Stockfish binary and are marked slow.
"""
from __future__ import annotations

import pytest

from chess_game.texel.position_db import GameRecord, PositionDB
from chess_game.texel.stockfish_annotate import (
    StockfishProcess,
    annotate_db,
    annotate_fens,
)

pytestmark = pytest.mark.slow

_START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
_WHITE_UP_QUEEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
_WHITE_UP_ROOK = "4k3/8/8/8/8/8/8/R3K3 w Q - 0 1"   # White rook vs lone Black king
_BLACK_UP_ROOK = "r3k3/8/8/8/8/8/8/4K3 b q - 0 1"   # Black rook vs lone White king
_CHECKMATE = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"


def test_eval_fen_starting_position() -> None:
    with StockfishProcess(depth=5) as sf:
        score = sf.eval_fen(_START)
    assert score is not None
    assert -50 <= score <= 50


def test_eval_fen_white_winning() -> None:
    with StockfishProcess(depth=5) as sf:
        score = sf.eval_fen(_WHITE_UP_ROOK)
    assert score is not None
    assert score > 100


def test_eval_fen_black_winning() -> None:
    with StockfishProcess(depth=5) as sf:
        score = sf.eval_fen(_BLACK_UP_ROOK)
    assert score is not None
    assert score < -100


def test_eval_fen_returns_none_on_mate() -> None:
    with StockfishProcess(depth=5) as sf:
        score = sf.eval_fen(_CHECKMATE)
    assert score is None


def test_annotate_fens_multiple() -> None:
    fens = [_START, _WHITE_UP_ROOK, _BLACK_UP_ROOK]
    results = annotate_fens(fens, depth=5, n_workers=2)
    assert set(results.keys()) == set(fens)


def test_context_manager_closes_cleanly() -> None:
    with StockfishProcess(depth=3) as sf:
        score = sf.eval_fen(_START)
    assert score is not None


def test_white_relative_conversion() -> None:
    # White-to-move: score should be same sign as "White is slightly better".
    # Black-to-move mirror: from same material, score should be negative.
    fen_white = "4k3/8/8/8/8/8/8/R3K3 w Q - 0 1"   # White rook, White to move
    fen_black = "4k3/8/8/8/8/8/8/r3K3 b - - 0 1"   # Black rook, Black to move → score White-relative should be negative
    with StockfishProcess(depth=5) as sf:
        score_white = sf.eval_fen(fen_white)
        score_black = sf.eval_fen(fen_black)
    assert score_white is not None
    assert score_black is not None
    # White rook (White to move) → White winning → positive
    assert score_white > 0
    # Black rook (Black to move) → Black winning → White-relative negative
    assert score_black < 0


def test_annotate_db_returns_all_fens() -> None:
    db = PositionDB()
    record = GameRecord(positions=[_START, _WHITE_UP_ROOK], outcome=1.0)
    db.add_game(record)
    results = annotate_db(db, depth=5, n_workers=2)
    assert _START in results
    assert _WHITE_UP_ROOK in results
