"""Fast unit tests for ai_search_helpers utility functions."""

from __future__ import annotations

from types import SimpleNamespace

from chess_game.chess.ai import SearchStats
from chess_game.chess.ai_search_helpers import (
    initial_root_window,
    position_occurrence_count,
    promotion_order_score,
    rerun_full_window_if_needed,
    search_position_counts,
    update_alpha_beta,
)
from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.types import PieceType
from tests.helpers import sq


def test_initial_root_window_depth_one_uses_full_window() -> None:
    """Depth-1 root search should not use aspiration bounds."""

    assert initial_root_window(1, previous_score=120, aspiration_window=50, inf=10_000) == (
        -10_000,
        10_000,
    )


def test_initial_root_window_depth_gt_one_uses_aspiration_bounds() -> None:
    """Deeper root search should center around the previous score."""

    assert initial_root_window(3, previous_score=120, aspiration_window=50, inf=10_000) == (
        70,
        170,
    )


def test_rerun_full_window_if_needed_detects_fail_low_and_increments_stat() -> None:
    """Fail-low inside an aspiration window should trigger a rerun."""

    stats = SearchStats()
    context = SimpleNamespace(stats=stats)

    assert rerun_full_window_if_needed(score=-200, alpha=-150, beta=150, context=context, inf=10_000)
    assert stats.fail_low_retries == 1
    assert stats.fail_high_retries == 0


def test_rerun_full_window_if_needed_detects_fail_high_and_increments_stat() -> None:
    """Fail-high inside an aspiration window should trigger a rerun."""

    stats = SearchStats()
    context = SimpleNamespace(stats=stats)

    assert rerun_full_window_if_needed(score=220, alpha=-150, beta=200, context=context, inf=10_000)
    assert stats.fail_low_retries == 0
    assert stats.fail_high_retries == 1


def test_rerun_full_window_if_needed_skips_rerun_on_full_window() -> None:
    """A full-width search window should not rerun, even when score is extreme."""

    stats = SearchStats()
    context = SimpleNamespace(stats=stats)

    assert not rerun_full_window_if_needed(
        score=9999,
        alpha=-10_000,
        beta=10_000,
        context=context,
        inf=10_000,
    )
    assert stats.fail_low_retries == 0
    assert stats.fail_high_retries == 0


def test_search_position_counts_decrements_current_root_position_once() -> None:
    """Current root key should be decremented to avoid double-counting."""

    board = Board()
    adjusted = search_position_counts(
        board,
        {"root-key": 2, "other-key": 3},
        position_key=lambda _board: "root-key",
    )

    assert adjusted == {"root-key": 1, "other-key": 3}


def test_search_position_counts_removes_key_when_decrement_reaches_zero() -> None:
    """Current key should be removed if decrement reaches zero."""

    board = Board()
    adjusted = search_position_counts(
        board,
        {"root-key": 1},
        position_key=lambda _board: "root-key",
    )

    assert adjusted == {}


def test_position_occurrence_count_combines_game_and_line_history() -> None:
    """Occurrence count should include both recorded game counts and line history."""

    board = Board()
    context = SimpleNamespace(position_counts={"root-key": 2})
    line_history = ("x", "root-key", "y", "root-key")

    assert position_occurrence_count(board, context, line_history, lambda _board: "root-key") == 4


def test_update_alpha_beta_maximizing_path_reports_cutoff() -> None:
    """Maximizing branch should raise alpha and report cutoff when alpha >= beta."""

    alpha, beta, cutoff = update_alpha_beta(
        is_maximizing=True,
        best_score=40,
        alpha=10,
        beta=30,
    )

    assert (alpha, beta, cutoff) == (40, 30, True)


def test_update_alpha_beta_minimizing_path_reports_cutoff() -> None:
    """Minimizing branch should lower beta and report cutoff when beta <= alpha."""

    alpha, beta, cutoff = update_alpha_beta(
        is_maximizing=False,
        best_score=-40,
        alpha=-20,
        beta=10,
    )

    assert (alpha, beta, cutoff) == (-20, -40, True)


def test_promotion_order_score_matches_piece_priority() -> None:
    """Promotion order should prefer queen over rook/bishop/knight and none for non-promo."""

    queen_promo = Move(start=sq("a7"), end=sq("a8"), promotion=PieceType.QUEEN)
    rook_promo = Move(start=sq("a7"), end=sq("a8"), promotion=PieceType.ROOK)
    bishop_promo = Move(start=sq("a7"), end=sq("a8"), promotion=PieceType.BISHOP)
    knight_promo = Move(start=sq("a7"), end=sq("a8"), promotion=PieceType.KNIGHT)
    quiet_move = Move(start=sq("a2"), end=sq("a3"), promotion=None)

    assert promotion_order_score(queen_promo) > promotion_order_score(rook_promo)
    assert promotion_order_score(rook_promo) > promotion_order_score(bishop_promo)
    assert promotion_order_score(bishop_promo) > promotion_order_score(knight_promo)
    assert promotion_order_score(quiet_move) == 0
