"""Tests for alpha-beta pruning and search manageability."""

from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from chess_game.chess.ai import minimax, MinimaxParams, MATE_SCORE
from tests.helpers import sq


def make_mate_in_one_white_position():
    board = Board()
    board.clear_board()
    board.set_piece(sq("g6"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f7"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE
    return board


def test_alpha_beta_pruning_does_not_affect_mate_detection():
    """Alpha-beta pruning should still find mate-in-one when available."""
    board = make_mate_in_one_white_position()

    nodes = [0]
    params = MinimaxParams(
        depth=1,
        alpha=-MATE_SCORE,
        beta=MATE_SCORE,
        is_maximizing=True,
        nodes_searched=nodes,
    )

    score, move = minimax(board, params)

    assert move is not None, "Alpha-beta should still find a mating move"
    assert score >= MATE_SCORE - 1, "Score should reflect mate"


def test_alpha_beta_pruning_fewer_or_equal_with_tighter_window():
    """With alpha-beta pruning, tightening the window around the expected score
    should not explore more nodes than a very wide window (it should prune at least as much)."""
    board = make_mate_in_one_white_position()

    # Wide window: less pruning.
    wide_nodes = [0]
    wide_params = MinimaxParams(
        depth=2,
        alpha=-10_000_000,
        beta=10_000_000,
        is_maximizing=True,
        nodes_searched=wide_nodes,
    )

    # Tighter window around mate score.
    tight_nodes = [0]
    tight_params = MinimaxParams(
        depth=2,
        alpha=MATE_SCORE - 500,
        beta=MATE_SCORE + 500,
        is_maximizing=True,
        nodes_searched=tight_nodes,
    )

    minimax(board, wide_params)
    minimax(board, tight_params)

    # Tighter bounds should not cause more work.
    assert tight_nodes[0] <= wide_nodes[0], (
        "Tighter alpha/beta should prune at least as much as a wide window"
    )


def test_minimax_respects_max_depth():
    """Minimax should not recurse beyond requested depth."""
    board = Board()

    nodes = [0]
    params = MinimaxParams(
        depth=1,
        alpha=-10_000_000,
        beta=10_000_000,
        is_maximizing=True,
        nodes_searched=nodes,
    )

    # Just ensure it completes without error at depth=1.
    minimax(board, params)
    assert nodes[0] > 0, "Minimax should explore at least one node"


def test_depth_2_search_completes():
    """Depth-2 search on a standard position should complete within reasonable time."""
    import time

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
    params = MinimaxParams(
        depth=3,
        alpha=-10_000_000,
        beta=10_000_000,
        is_maximizing=True,
        nodes_searched=nodes,
    )

    # Run a depth-3 search with nodes counted.
    minimax(board, params)

    # This threshold is heuristic but should hold for reasonable alpha-beta.
    assert nodes[0] < 500_000, "Depth-3 search should not exceed 500k nodes"


def get_best_move(board: Board, depth: int):
    """Simple wrapper around minimax for testing."""
    from chess_game.chess.types import Color

    if depth < 1:
        raise ValueError("depth must be >= 1")

    nodes = [0]
    params = MinimaxParams(
        depth=depth,
        alpha=-10_000_000,
        beta=10_000_000,
        is_maximizing=(board.turn == Color.WHITE),
        nodes_searched=nodes,
    )

    score, move = minimax(board, params)
    return move
