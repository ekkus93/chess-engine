"""Tests for alpha-beta pruning and search manageability."""

import time

from chess_game import self_play
from chess_game.self_play import run_self_play
from chess_game.chess.ai import SearchStats, minimax, minimax_no_prune
from chess_game.chess.board import Board
from chess_game.chess.types import Color, LegalMove
from tests.helpers import (
    make_search_context,
    make_search_params,
)

def test_depth_2_search_completes():
    """Depth-2 search on a standard position should complete within reasonable time."""
    board = Board()

    start = time.monotonic()
    move = get_best_move(board, depth=2)
    elapsed = time.monotonic() - start

    # Just ensure it finishes within 20s and returns a move.
    assert move is not None, "Depth-2 search should return a move"
    assert elapsed < 20, "Depth-2 search should complete within 20 seconds"


def test_depth_3_nodes_within_reasonable_limit():
    """Depth-3 search nodes should be within some reasonable limit (no combinatorial explosion)."""
    board = Board()

    nodes = [0]
    params = make_search_params(
        3,
        -10_000_000,
        10_000_000,
        True,
        context=make_search_context(nodes=nodes),
    )

    # Run a depth-3 search with nodes counted.
    minimax(board, params)

    # This threshold is heuristic but should hold for reasonable alpha-beta.
    assert nodes[0] < 500_000, "Depth-3 search should not exceed 500k nodes"


def get_best_move(board: Board, depth: int):
    """Simple wrapper around minimax for testing."""
    if depth < 1:
        raise ValueError("depth must be >= 1")

    nodes = [0]
    params = make_search_params(
        depth,
        -10_000_000,
        10_000_000,
        board.turn == Color.WHITE,
        context=make_search_context(nodes=nodes),
    )

    _, move = minimax(board, params)
    return move


def test_alpha_beta_prunes_fewer_nodes_than_no_prune():
    """Alpha-beta minimax should explore fewer nodes than pure minimax on the same position."""
    board = Board()

    # Alpha-beta minimax with nodes counter
    nodes_ab = [0]
    params_ab = make_search_params(
        2,
        -10_000_000,
        10_000_000,
        True,
        context=make_search_context(nodes=nodes_ab),
    )
    score_ab, _ = minimax(board, params_ab)

    # Pure minimax (no pruning) with nodes counter
    nodes_nop = [0]
    score_nop = minimax_no_prune(board, 2, True, nodes_nop)

    # Both should agree on score.
    assert score_ab == score_nop

    # Alpha-beta should explore fewer nodes.
    assert nodes_ab[0] < nodes_nop[0], "Alpha-beta should prune nodes compared to pure minimax"


def test_alpha_beta_cutoffs_occurred():
    """Alpha-beta search should record cutoffs at moderate depth."""
    board = Board()
    stats = SearchStats()

    params = make_search_params(
        3,
        -10_000_000,
        10_000_000,
        True,
        context=make_search_context(stats=stats),
    )

    minimax(board, params)

    assert stats.cutoffs > 0, "Alpha-beta should trigger cutoffs at depth 3"


def test_self_play_depth_3_terminates():
    """Self-play with depth 3 should terminate for a single move quickly."""
    start = time.monotonic()
    run_self_play(
        depth_white=3,
        depth_black=3,
        max_moves=1,
        verbose=False,
    )
    elapsed = time.monotonic() - start

    assert elapsed < 60, "Self-play with depth 3, 1 move should complete within 60s"


def test_self_play_honors_requested_depth(monkeypatch):
    """Self-play should use the exact requested depth for both sides."""
    requested_depths = []

    def fake_get_best_move(board: Board, depth: int):
        requested_depths.append(depth)
        start, end, promotion = board.get_legal_moves()[0]
        return LegalMove(start, end, promotion)

    monkeypatch.setattr(self_play, "get_best_move", fake_get_best_move)

    run_self_play(
        depth_white=7,
        depth_black=7,
        max_moves=2,
        verbose=False,
    )

    assert requested_depths == [7, 7]
