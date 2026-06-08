"""Perft (performance test) — node count verification from the starting position.

These tests verify that legal-move generation is correct by counting nodes at
fixed depths and comparing against the known-correct perft values:

  depth 1:      20
  depth 2:     400
  depth 3:   8 902
  depth 4: 197 281  (slow)
"""
from __future__ import annotations

import pytest

from chess_game.chess import Board
from chess_game.chess.board.board import Board as BoardImpl


def _perft(board: BoardImpl, depth: int) -> int:
    """Return the number of leaf nodes reachable at *depth* plies."""
    if depth == 0:
        return 1
    legal = board.get_legal_moves()
    if depth == 1:
        return len(legal)
    total = 0
    for start, end, promotion in legal:
        child = board.clone()
        child.make_move(start, end, promotion)
        total += _perft(child, depth - 1)
    return total


@pytest.fixture(name="start_board")
def _start_board() -> BoardImpl:
    return Board()


def test_perft_depth_1(start_board: BoardImpl) -> None:
    """Depth 1: 20 legal opening moves."""
    assert _perft(start_board, 1) == 20


def test_perft_depth_2(start_board: BoardImpl) -> None:
    """Depth 2: 400 positions after two half-moves."""
    assert _perft(start_board, 2) == 400


def test_perft_depth_3(start_board: BoardImpl) -> None:
    """Depth 3: 8 902 nodes."""
    assert _perft(start_board, 3) == 8902


@pytest.mark.slow
def test_perft_depth_4(start_board: BoardImpl) -> None:
    """Depth 4: 197 281 nodes (slow)."""
    assert _perft(start_board, 4) == 197281
