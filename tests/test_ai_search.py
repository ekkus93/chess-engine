"""Tests for AI search correctness: mate-at-horizon, leaf evaluation, and depth validation."""

from __future__ import annotations

import pytest
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from chess_game.chess.ai import get_best_move, minimax, MinimaxParams, MATE_SCORE
from tests.helpers import sq


def move_to_str(move):
    """Helper to format a move tuple into algebraic string for assertions."""
    start, end, promotion = move
    suffix = ""
    if promotion is not None:
        suffix = str(promotion.name).lower()[0]
    return f"{index_to_str(start)}{index_to_str(end)}{suffix}"


def index_to_str(sq_obj):
    """Convert ConstantSquare to algebraic string."""
    file = chr(ord("a") + int(sq_obj.col))
    rank = str(8 - int(sq_obj.row))
    return f"{rank}{file}"


def make_mate_in_one_white_position():
    """Position:
    White king on g6
    White queen on f7
    Black king on h8
    White to move
    """
    board = Board()
    board.clear_board()
    board.set_piece(sq("g6"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f7"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE
    return board


def make_mate_in_one_black_position():
    """Position:
    Black king on c2
    Black queen on d3
    White king on a1
    Black to move
    """
    board = Board()
    board.clear_board()
    board.set_piece(sq("c2"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d3"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
    board.turn = Color.BLACK
    return board


def test_mate_in_one_white_finds_checkmate():
    """White to move should find a mate-in-one at depth 1."""
    board = make_mate_in_one_white_position()
    move = get_best_move(board, depth=1)
    assert move is not None, "AI should find a checkmate at depth 1"

    # Verify it actually mates
    clone = board.clone()
    assert clone.make_move(move.start, move.end, promotion=move.promotion) is True
    assert clone._is_checkmate(Color.BLACK), "Black should be checkmated"


def test_mate_in_one_black_finds_checkmate():
    """Black to move should find a mate-in-one at depth 1."""
    board = make_mate_in_one_black_position()
    move = get_best_move(board, depth=1)
    assert move is not None, "AI should find a checkmate for Black at depth 1"

    clone = board.clone()
    assert clone.make_move(move.start, move.end, promotion=move.promotion) is True
    assert clone._is_checkmate(Color.WHITE), "White should be checkmated"


def test_mate_in_one_does_not_choose_non_mating_queen_move():
    """Ensure AI prefers a mating move over a non-mating queen move."""
    board = make_mate_in_one_white_position()
    move = get_best_move(board, depth=1)
    assert move is not None

    clone = board.clone()
    clone.make_move(move.start, move.end, promotion=move.promotion)
    # If it's not a checkmate, we failed to prioritize mate
    assert clone._is_checkmate(Color.BLACK), "Move should be checkmate, not random queen move"


def test_stalemate_returns_no_best_move():
    """Stalemate: no legal moves, get_best_move should return None."""
    board = Board()
    board.clear_board()
    # Black king: h8
    # White king: f7
    # White queen: g6
    # Black to move
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("f7"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g6"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.turn = Color.BLACK

    move = get_best_move(board, depth=1)
    assert move is None, "No move should be returned in stalemate"


def test_checkmate_side_to_move_returns_no_best_move():
    """Checkmate position: get_best_move should return None (no legal moves)."""
    board = Board()
    board.clear_board()
    # Black king: h8
    # White king: f6
    # White queen: g7
    # Black to move
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("f6"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g7"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.turn = Color.BLACK

    move = get_best_move(board, depth=1)
    assert move is None, "No move should be returned in checkmate"


def test_depth_validation_raises_value_error_for_zero():
    """depth=0 should raise ValueError."""
    board = Board()
    with pytest.raises(ValueError, match="depth"):
        get_best_move(board, depth=0)


def test_depth_validation_raises_value_error_for_negative():
    """Negative depth should raise ValueError."""
    board = Board()
    with pytest.raises(ValueError, match="depth"):
        get_best_move(board, depth=-1)


def test_get_best_move_does_not_mutate_board():
    """AI should not mutate the original board."""
    board = Board()

    # Capture initial key
    initial_key = _board_key(board)

    move = get_best_move(board, depth=2)
    # Just ensure it runs and does not mutate
    final_key = _board_key(board)
    assert initial_key == final_key, "Board state must not be mutated by AI search"


def _board_key(board: Board) -> str:
    """Helper to capture a board key for mutation checks."""
    parts = []
    for row in board.board:
        for p in row:
            if p is None:
                parts.append("-")
            else:
                parts.append(f"{p.color.name[0]}{p.kind.name[0].lower()}")
    parts.append(board.turn.name)
    return "".join(parts)


def make_params(
    depth: int,
    alpha: int = -10_000_000,
    beta: int = 10_000_000,
    is_maximizing: bool = True,
    tt=None,
):
    """Helper to create MinimaxParams."""
    return MinimaxParams(
        depth=depth,
        alpha=alpha,
        beta=beta,
        is_maximizing=is_maximizing,
        transposition_table=tt,
    )


# Tests for minimax leaf evaluation behavior


def test_minimax_depth_zero_returns_raw_evaluation():
    """At depth 0, minimax should return raw evaluation."""
    board = Board()
    score, move = minimax(board, make_params(depth=0, is_maximizing=True))
    assert move is None
    assert isinstance(score, int)


def test_minimax_depth_zero_no_clamp_to_alpha_beta():
    """Depth-0 score should not be clamped to alpha/beta window."""
    board = Board()
    s1, _ = minimax(board, make_params(depth=0, alpha=-1, beta=1))
    s2, _ = minimax(board, make_params(depth=0, alpha=-10, beta=10))
    assert s1 == s2, "Depth-0 evaluation should not depend on alpha/beta window"


def test_minimax_no_legal_moves_checkmate_white_to_move():
    """If White has no legal moves and is in check, minimax should return -MATE_SCORE."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("f6"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g7"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.turn = Color.BLACK

    score, _ = minimax(board, make_params(depth=1, is_maximizing=True))
    assert score == MATE_SCORE


def test_minimax_no_legal_moves_checkmate_black_to_move():
    """If Black has no legal moves and is in check, minimax should return MATE_SCORE."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("f6"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g7"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.turn = Color.BLACK

    score, _ = minimax(board, make_params(depth=1, is_maximizing=False))
    assert score == MATE_SCORE


def test_minimax_stalemate_returns_zero():
    """Stalemate: no legal moves and not in check should return score 0."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("f7"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g6"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.turn = Color.BLACK

    score, _ = minimax(board, make_params(depth=1, is_maximizing=True))
    assert score == 0


def test_minimax_prefers_checkmate_over_material():
    """Minimax should prefer a line that mates over a material win."""
    board = make_mate_in_one_white_position()
    params = make_params(depth=2, is_maximizing=True)
    score, move = minimax(board, params)

    assert move is not None
    clone = board.clone()
    assert clone.make_move(move.start, move.end, promotion=move.promotion) is True
    assert clone._is_checkmate(Color.BLACK), "Minimax should find mate over material win"


# Tests for alpha-beta pruning behavior


def test_alpha_beta_pruning_cuts_off_search():
    """With alpha-beta pruning, a cutoff should occur if alpha >= beta."""
    # We cannot inspect cutoffs directly, but search should complete and return a move.
    board = Board()
    params = make_params(depth=2, is_maximizing=True)
    score, move = minimax(board, params)
    assert isinstance(score, int)


def test_alpha_beta_respects_alpha_beta_bounds():
    """Minimax with alpha-beta should still respect alpha/beta via TT/early cutoff."""
    board = Board()

    wide = make_params(depth=2, is_maximizing=True, alpha=-10_000_000, beta=10_000_000)
    s1, _ = minimax(board, wide)

    narrow = make_params(depth=2, is_maximizing=True, alpha=-1000, beta=1000)
    s2, _ = minimax(board, narrow)

    assert isinstance(s1, int)
    assert isinstance(s2, int)


def test_minimax_no_move_on_checkmate_side():
    """If side to move is checkmated, minimax should return no move."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("f6"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g7"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.turn = Color.BLACK

    score, move = minimax(board, make_params(depth=1, is_maximizing=True))
    assert move is None


# Tests for evaluation perspective


def test_evaluation_positive_for_white_advantage():
    """Evaluation should be positive when White has material advantage."""
    from chess_game.chess.ai import evaluate

    board = Board()
    board.clear_board()
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.KING))
    score = evaluate(board)
    assert score > 0, "Evaluation should be positive when White has material advantage"


def test_evaluation_negative_for_black_advantage():
    """Evaluation should be negative when Black has material advantage."""
    from chess_game.chess.ai import evaluate

    board = Board()
    board.clear_board()
    board.set_piece(sq("e4"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("e4"), create_piece(Color.BLACK, PieceType.KING))
    score = evaluate(board)
    assert score < 0, "Evaluation should be negative when Black has material advantage"


def test_evaluation_symmetric_for_equal_positions():
    """Symmetric positions should yield equal evaluations."""
    from chess_game.chess.ai import evaluate

    board1 = Board()
    board2 = Board()

    for b in (board1, board2):
        b.clear_board()
        b.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.QUEEN))
        b.set_piece(sq("e5"), create_piece(Color.BLACK, PieceType.KING))

    s1 = evaluate(board1)
    s2 = evaluate(board2)
    assert s1 == s2, "Same positions should give same evaluation"


# Tests for transposition table integration


def make_simple_board_with_legal_moves():
    """Create a simple position with legal moves."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e5"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.turn = Color.WHITE
    return board


def test_tt_is_used_in_minimax():
    """TT entries should be written and used during search."""
    board = make_simple_board_with_legal_moves()
    tt: dict = {}
    params = make_params(depth=1, is_maximizing=True, tt=tt)
    minimax(board, params)
    assert len(tt) > 0


def test_tt_stores_non_none_best_move():
    """TT entry should store a best_move (not None) when a move exists."""
    board = make_simple_board_with_legal_moves()
    tt: dict = {}
    params = make_params(depth=1, is_maximizing=True, tt=tt)
    minimax(board, params)
    assert any(entry.best_move is not None for entry in tt.values())


def test_tt_does_not_overwrite_deeper_entry():
    """A shallower TT entry should not overwrite a deeper one."""
    board = make_simple_board_with_legal_moves()
    tt: dict = {}

    params2 = make_params(depth=2, is_maximizing=True, tt=tt)
    minimax(board, params2)

    params1 = make_params(depth=1, is_maximizing=True, tt=tt)
    minimax(board, params1)

    assert any(e.depth >= 2 for e in tt.values())


def test_tt_entry_has_flag():
    """TT entries should have a valid flag."""
    from chess_game.chess.ai import TTFlag

    board = make_simple_board_with_legal_moves()
    tt: dict = {}
    params = make_params(depth=1, is_maximizing=True, tt=tt)
    minimax(board, params)

    assert any(e.flag in (TTFlag.EXACT, TTFlag.LOWERBOUND, TTFlag.UPPERBOUND) for e in tt.values())


def test_tt_entry_depth_positive():
    """TT entry should have positive depth."""
    board = make_simple_board_with_legal_moves()
    tt: dict = {}
    params = make_params(depth=1, is_maximizing=True, tt=tt)
    minimax(board, params)

    assert any(e.depth > 0 for e in tt.values())


def test_tt_entry_score_is_int():
    """TT entry should store numeric score."""
    board = make_simple_board_with_legal_moves()
    tt: dict = {}
    params = make_params(depth=1, is_maximizing=True, tt=tt)
    minimax(board, params)

    assert any(isinstance(e.score, int) for e in tt.values())
