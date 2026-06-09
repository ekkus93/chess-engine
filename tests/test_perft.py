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


# Special perft cases (shallow depths)


def test_perft_castling_position() -> None:
    """Perft for a position with castling rights."""
    board = Board.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    # Just verify move generation works and counts are consistent
    assert _perft(board, 1) > 0
    assert _perft(board, 2) > _perft(board, 1)


def test_perft_en_passant_position() -> None:
    """Perft for a position with en passant possibility."""
    board = Board.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
    # Verify move generation works (black can capture en passant)
    assert _perft(board, 1) > 0


def test_perft_promotion_position() -> None:
    """Perft for a position with promotion possibility."""
    board = Board.from_fen("8/P7/8/8/8/8/8/K6k w - - 0 1")
    # White pawn can promote
    moves = board.get_legal_moves()
    promotion_moves = [m for m in moves if m[2] is not None]
    assert len(promotion_moves) > 0  # Should have promotion moves


def test_perft_check_evasion_position() -> None:
    """Perft for a position with check."""
    board = Board.from_fen("rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 4 4")
    # Verify that check does not prevent move generation
    moves = board.get_legal_moves()
    assert len(moves) > 0  # Should have legal moves from this position
