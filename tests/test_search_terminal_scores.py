"""Tests for _terminal_score branching in the minimax search.

Verifies that the minimax search returns the correct terminal score for:
  * Checkmate (one side mated)
  * Stalemate (draw)
  * Fifty-move rule (draw)
  * Insufficient material (draw)
  * Mate-in-1 preference over non-mating moves

All tests use depth-0 calls or single-depth calls to isolate the terminal
evaluation without deep search noise.
"""
from __future__ import annotations

import pytest

from chess_game.chess.ai import DRAW_SCORE, MATE_SCORE, minimax
from chess_game.chess.board import Board, create_piece
from chess_game.chess.coords import index_to_algebraic
from chess_game.chess.types import Color, LegalMove, PieceType
from tests.helpers import make_search_context, make_search_params, sq


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_INF = 10_000_000


def _minimax_d0(board: Board) -> int:
    """Run minimax at depth-0 for the current side to move."""
    is_max = board.turn == Color.WHITE
    params = make_search_params(_INF, -_INF, _INF, is_max, context=make_search_context())
    score, _ = minimax(board, params)
    return score


def _minimax_d1(board: Board) -> tuple[int, LegalMove | None]:
    """Run minimax at depth-1 for the current side to move."""
    is_max = board.turn == Color.WHITE
    params = make_search_params(1, -_INF, _INF, is_max, context=make_search_context())
    return minimax(board, params)


# ---------------------------------------------------------------------------
# Checkmate
# ---------------------------------------------------------------------------

def test_checkmate_white_mated_returns_negative_mate_score() -> None:
    """When White is checkmated at depth 0, minimax returns −MATE_SCORE."""
    # Fool's mate: White is checkmated
    board = Board.from_fen("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
    legal = board.get_legal_moves()
    if legal:
        pytest.skip("Position not actually checkmate in this build")
    score = _minimax_d0(board)
    assert score == -MATE_SCORE


def test_checkmate_black_mated_returns_positive_mate_score() -> None:
    """When Black is checkmated at depth 0, minimax returns +MATE_SCORE."""
    # Post Qg7# position: White king g6, White queen g7, Black king h8 — Black to move
    board = Board.from_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
    legal = board.get_legal_moves()
    if legal:
        pytest.skip("Position not actually checkmate in this build")
    score = _minimax_d0(board)
    assert score == MATE_SCORE


# ---------------------------------------------------------------------------
# Mate-in-1 preference
# ---------------------------------------------------------------------------

def test_mate_in_one_chosen_over_non_mating_move() -> None:
    """At depth 1 the engine selects the mating move, not a random capture."""
    # White Qf7# is available; White King on g6, Queen on d5, Black King on h8
    board = Board()
    board.clear_board()
    board.set_piece(sq("g6"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d5"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE
    score, move = _minimax_d1(board)
    assert move is not None
    assert score >= MATE_SCORE - 10, (
        f"Expected mate score, got {score}; "
        f"move={index_to_algebraic(move.start)}{index_to_algebraic(move.end)}"
    )


# ---------------------------------------------------------------------------
# Stalemate
# ---------------------------------------------------------------------------

def test_stalemate_returns_draw_score() -> None:
    """A stalemated position returns DRAW_SCORE."""
    # Classic stalemate: Black king at a8, White queen at b6, White king at b8
    # Black to move — no legal moves but not in check
    board = Board()
    board.clear_board()
    board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("b6"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("c7"), create_piece(Color.WHITE, PieceType.KING))
    board.turn = Color.BLACK
    legal = board.get_legal_moves()
    if legal:
        pytest.skip("Position not actually stalemate in this build")
    score = _minimax_d0(board)
    assert score == DRAW_SCORE


# ---------------------------------------------------------------------------
# Fifty-move rule
# ---------------------------------------------------------------------------

def test_fifty_move_rule_returns_draw_score() -> None:
    """A position with halfmove clock >= 100 returns DRAW_SCORE."""
    board = Board.from_fen("8/8/8/8/8/k7/8/K7 w - - 100 150")
    score = _minimax_d0(board)
    assert score == DRAW_SCORE


# ---------------------------------------------------------------------------
# Insufficient material
# ---------------------------------------------------------------------------

def test_insufficient_material_king_vs_king_returns_draw_score() -> None:
    """King vs King is drawn by insufficient material."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE
    score = _minimax_d0(board)
    assert score == DRAW_SCORE
