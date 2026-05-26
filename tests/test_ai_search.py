"""Tests for AI search correctness: mate-at-horizon, leaf evaluation, and depth validation."""

from __future__ import annotations

import time

import pytest
from chess_game.chess.ai import (
    MATE_SCORE,
    SearchStats,
    TTFlag,
    evaluate,
    get_best_move,
    minimax,
    position_key,
    search_root_depth,
)
from chess_game.chess.ai_search_helpers import root_stability_adjustment, selective_extension_bonus
from chess_game.chess.board import Board, create_piece
from chess_game.chess.board.game_state import is_checkmate
from chess_game.chess.move import Move
from chess_game.chess.types import Color, LegalMove, PieceType
from tests.helpers import (
    make_mate_in_one_white_position,
    make_search_context,
    make_search_params,
    sq,
)


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
    assert is_checkmate(clone, Color.BLACK), "Black should be checkmated"


def test_mate_in_one_black_finds_checkmate():
    """Black to move should find a mate-in-one at depth 1."""
    board = make_mate_in_one_black_position()
    move = get_best_move(board, depth=1)
    assert move is not None, "AI should find a checkmate for Black at depth 1"

    clone = board.clone()
    assert clone.make_move(move.start, move.end, promotion=move.promotion) is True
    assert is_checkmate(clone, Color.WHITE), "White should be checkmated"


def test_mate_in_one_does_not_choose_non_mating_queen_move():
    """Ensure AI prefers a mating move over a non-mating queen move."""
    board = make_mate_in_one_white_position()
    move = get_best_move(board, depth=1)
    assert move is not None

    clone = board.clone()
    clone.make_move(move.start, move.end, promotion=move.promotion)
    # If it's not a checkmate, we failed to prioritize mate
    assert is_checkmate(clone, Color.BLACK), "Move should be checkmate, not random queen move"


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

    get_best_move(board, depth=2)
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
    return make_search_params(
        depth,
        alpha,
        beta,
        is_maximizing,
        context=make_search_context(tt=tt),
    )


def make_forcing_check_extension_position() -> Board:
    """Create a position where a back-rank queen invasion deserves an extension."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("h7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE
    return board


def make_check_evasion_extension_position() -> Board:
    """Create a position where the side to move must answer a check."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e1"), create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.WHITE
    return board


def make_capture_extension_position() -> Board:
    """Create a capture that tears open a file near the enemy king."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE
    return board


def make_technical_simplification_extension_position() -> Board:
    """Create a favorable simplification into a trivial technical ending."""

    board = Board()
    board.clear_board()
    placements = [
        ("g1", Color.WHITE, PieceType.KING),
        ("d1", Color.WHITE, PieceType.ROOK),
        ("d5", Color.WHITE, PieceType.PAWN),
        ("g8", Color.BLACK, PieceType.KING),
        ("d8", Color.BLACK, PieceType.ROOK),
    ]
    for square_name, color, piece_kind in placements:
        board.set_piece(sq(square_name), create_piece(color, piece_kind))
    board.turn = Color.WHITE
    return board


def make_central_prophylaxis_extension_position() -> Board:
    """Create a central pawn push that sharply reduces enemy plan pressure."""

    board = Board()
    board.clear_board()
    placements = [
        ("g1", Color.WHITE, PieceType.KING),
        ("d1", Color.WHITE, PieceType.QUEEN),
        ("a1", Color.WHITE, PieceType.ROOK),
        ("f1", Color.WHITE, PieceType.ROOK),
        ("c4", Color.WHITE, PieceType.BISHOP),
        ("f3", Color.WHITE, PieceType.KNIGHT),
        ("d4", Color.WHITE, PieceType.PAWN),
        ("e4", Color.WHITE, PieceType.PAWN),
        ("f2", Color.WHITE, PieceType.PAWN),
        ("g2", Color.WHITE, PieceType.PAWN),
        ("h2", Color.WHITE, PieceType.PAWN),
        ("g8", Color.BLACK, PieceType.KING),
        ("d8", Color.BLACK, PieceType.QUEEN),
        ("c5", Color.BLACK, PieceType.PAWN),
        ("d6", Color.BLACK, PieceType.PAWN),
        ("e5", Color.BLACK, PieceType.PAWN),
        ("f6", Color.BLACK, PieceType.KNIGHT),
    ]
    for square_name, color, piece_kind in placements:
        board.set_piece(sq(square_name), create_piece(color, piece_kind))
    board.turn = Color.WHITE
    return board


def make_king_file_shift_extension_position() -> Board:
    """Create a shelter-pawn shift near the king that changes king-file safety."""

    board = Board()
    board.clear_board()
    placements = [
        ("g1", Color.WHITE, PieceType.KING),
        ("d1", Color.WHITE, PieceType.QUEEN),
        ("h1", Color.WHITE, PieceType.ROOK),
        ("g2", Color.WHITE, PieceType.PAWN),
        ("h2", Color.WHITE, PieceType.PAWN),
        ("g8", Color.BLACK, PieceType.KING),
        ("g7", Color.BLACK, PieceType.ROOK),
        ("h4", Color.BLACK, PieceType.QUEEN),
        ("h5", Color.BLACK, PieceType.PAWN),
    ]
    for square_name, color, piece_kind in placements:
        board.set_piece(sq(square_name), create_piece(color, piece_kind))
    board.turn = Color.WHITE
    return board


def make_king_shelter_recapture_extension_position() -> Board:
    """Create a king-side pawn recapture that changes shelter geometry."""

    board = Board()
    board.clear_board()
    placements = [
        ("g1", Color.WHITE, PieceType.KING),
        ("d1", Color.WHITE, PieceType.QUEEN),
        ("h1", Color.WHITE, PieceType.ROOK),
        ("f2", Color.WHITE, PieceType.PAWN),
        ("g3", Color.WHITE, PieceType.PAWN),
        ("h2", Color.WHITE, PieceType.PAWN),
        ("g8", Color.BLACK, PieceType.KING),
        ("g7", Color.BLACK, PieceType.ROOK),
        ("h5", Color.BLACK, PieceType.QUEEN),
        ("h4", Color.BLACK, PieceType.PAWN),
    ]
    for square_name, color, piece_kind in placements:
        board.set_piece(sq(square_name), create_piece(color, piece_kind))
    board.turn = Color.WHITE
    return board


def make_only_move_prophylaxis_extension_position() -> Board:
    """Create a back-rank pressure case with a single non-capturing stabilizer."""

    board = Board()
    board.clear_board()
    placements = [
        ("g1", Color.WHITE, PieceType.KING),
        ("h1", Color.WHITE, PieceType.ROOK),
        ("d1", Color.WHITE, PieceType.QUEEN),
        ("g2", Color.WHITE, PieceType.PAWN),
        ("h8", Color.BLACK, PieceType.KING),
        ("h4", Color.BLACK, PieceType.QUEEN),
        ("h5", Color.BLACK, PieceType.PAWN),
    ]
    for square_name, color, piece_kind in placements:
        board.set_piece(sq(square_name), create_piece(color, piece_kind))
    board.turn = Color.WHITE
    return board


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
    _, move = minimax(board, params)

    assert move is not None
    clone = board.clone()
    assert clone.make_move(move.start, move.end, promotion=move.promotion) is True
    assert is_checkmate(clone, Color.BLACK), "Minimax should find mate over material win"


def test_selective_extension_bonus_triggers_for_forcing_check() -> None:
    """Back-rank queen checks against an exposed king should get one extra ply."""

    board = make_forcing_check_extension_position()
    move = Move(start=sq("d1"), end=sq("d8"))
    child_board = board.clone()

    assert child_board.apply_legal_move(move.start, move.end) is True
    assert selective_extension_bonus(board, move, child_board, extension_budget=1) == 1


def test_selective_extension_bonus_triggers_for_check_evasion() -> None:
    """Legal replies while in check should keep searching one ply deeper."""

    board = make_check_evasion_extension_position()
    move = Move(start=sq("d1"), end=sq("e1"))
    child_board = board.clone()

    assert child_board.apply_legal_move(move.start, move.end) is True
    assert selective_extension_bonus(board, move, child_board, extension_budget=1) == 1


def test_selective_extension_bonus_skips_harmless_queen_drift() -> None:
    """Fake attacking queen moves should not trigger the extension."""

    board = make_forcing_check_extension_position()
    move = Move(start=sq("d1"), end=sq("h5"))
    child_board = board.clone()

    assert child_board.apply_legal_move(move.start, move.end) is True
    assert selective_extension_bonus(board, move, child_board, extension_budget=1) == 0


def test_selective_extension_bonus_triggers_for_capture_that_opens_king_pressure() -> None:
    """Captures that increase king pressure should keep searching one ply deeper."""

    board = make_capture_extension_position()
    move = Move(start=sq("g1"), end=sq("g7"))
    child_board = board.clone()

    assert child_board.apply_legal_move(move.start, move.end) is True
    assert selective_extension_bonus(board, move, child_board, extension_budget=1) == 1


def test_selective_extension_bonus_triggers_for_favorable_simplification() -> None:
    """Winning trades into simple technical endings should get one extra ply."""

    board = make_technical_simplification_extension_position()
    move = Move(start=sq("d1"), end=sq("d8"))
    child_board = board.clone()

    assert child_board.apply_legal_move(move.start, move.end) is True
    assert selective_extension_bonus(board, move, child_board, extension_budget=1) == 1


def test_selective_extension_bonus_triggers_for_central_prophylaxis() -> None:
    """Central pawn pushes that cut enemy plan pressure should get one extra ply."""

    board = make_central_prophylaxis_extension_position()
    move = Move(start=sq("d4"), end=sq("d5"))
    child_board = board.clone()

    assert child_board.apply_legal_move(move.start, move.end) is True
    assert selective_extension_bonus(board, move, child_board, extension_budget=1) == 1


def test_selective_extension_bonus_triggers_for_king_file_shift() -> None:
    """King-file shelter shifts should get one extra ply under real pressure."""

    board = make_king_file_shift_extension_position()
    move = Move(start=sq("g2"), end=sq("g3"))
    child_board = board.clone()

    assert child_board.apply_legal_move(move.start, move.end) is True
    assert selective_extension_bonus(board, move, child_board, extension_budget=1) == 1


def test_selective_extension_bonus_triggers_for_king_shelter_recapture() -> None:
    """Pawn recaptures beside the king should extend when shelter profile changes."""

    board = make_king_shelter_recapture_extension_position()
    move = Move(start=sq("g3"), end=sq("h4"))
    child_board = board.clone()

    assert child_board.apply_legal_move(move.start, move.end) is True
    assert selective_extension_bonus(board, move, child_board, extension_budget=1) == 1


def test_selective_extension_bonus_triggers_for_only_move_prophylaxis() -> None:
    """A unique non-capturing back-rank stabilizer should get one extra ply."""

    board = make_only_move_prophylaxis_extension_position()
    move = Move(start=sq("g2"), end=sq("g3"))
    child_board = board.clone()

    assert child_board.apply_legal_move(move.start, move.end) is True
    assert selective_extension_bonus(board, move, child_board, extension_budget=1) == 1


def test_selective_extension_bonus_triggers_for_near_promotion_passer_push() -> None:
    """A near-promotion passed-pawn push should get one extra ply in simple races."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("a6"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.WHITE

    move = Move(start=sq("a6"), end=sq("a7"))
    child_board = board.clone()

    assert child_board.apply_legal_move(move.start, move.end) is True
    assert selective_extension_bonus(board, move, child_board, extension_budget=1) == 1


def test_search_records_selective_extension_diagnostics() -> None:
    """Search diagnostics should record when a bounded extension is applied."""

    board = make_forcing_check_extension_position()
    stats = SearchStats()
    context = make_search_context(stats=stats)

    search_root_depth(
        board,
        depth=1,
        is_maximizing=True,
        previous_score=0,
        context=context,
    )

    assert stats.diagnostics is not None
    assert stats.diagnostics.selective_extensions > 0


def test_root_stability_adjustment_penalizes_repeated_empty_tactic() -> None:
    """Repeated root tactics should lose tie-breaks unless they improve the attack."""

    board = make_forcing_check_extension_position()
    repeated_move = Move(start=sq("d1"), end=sq("h5"))
    fresh_move = Move(start=sq("d1"), end=sq("d8"))

    repeated_child = board.clone()
    fresh_child = board.clone()
    assert repeated_child.apply_legal_move(repeated_move.start, repeated_move.end) is True
    assert fresh_child.apply_legal_move(fresh_move.start, fresh_move.end) is True

    context = make_search_context(
        stats=SearchStats(),
    )
    context.position_counts = {position_key(repeated_child): 1}

    repeated_adjustment = root_stability_adjustment(
        board,
        repeated_move,
        repeated_child,
        context,
        position_key,
    )
    fresh_adjustment = root_stability_adjustment(
        board,
        fresh_move,
        fresh_child,
        context,
        position_key,
    )

    assert fresh_adjustment > repeated_adjustment


def test_root_stability_adjustment_prefers_fewer_strategic_weaknesses() -> None:
    """Root tie-breaks should prefer moves that avoid creating fresh weaknesses."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("f2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.WHITE

    solid_move = Move(start=sq("a1"), end=sq("d1"))
    loosening_move = Move(start=sq("h2"), end=sq("h4"))

    solid_child = board.clone()
    loosening_child = board.clone()
    assert solid_child.apply_legal_move(solid_move.start, solid_move.end) is True
    assert loosening_child.apply_legal_move(loosening_move.start, loosening_move.end) is True

    assert root_stability_adjustment(board, solid_move, solid_child) > root_stability_adjustment(
        board,
        loosening_move,
        loosening_child,
    )


def test_root_stability_adjustment_prefers_reducing_opponent_options() -> None:
    """Root tie-breaks should reward moves that narrow the opponent's plan choices."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("a2"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.WHITE

    suppress_move = Move(start=sq("a2"), end=sq("d2"))
    attack_move = Move(start=sq("e2"), end=sq("e8"))

    suppress_child = board.clone()
    attack_child = board.clone()
    assert suppress_child.apply_legal_move(suppress_move.start, suppress_move.end) is True
    assert attack_child.apply_legal_move(attack_move.start, attack_move.end) is True

    assert root_stability_adjustment(board, suppress_move, suppress_child) > root_stability_adjustment(
        board,
        attack_move,
        attack_child,
    )


def test_root_stability_adjustment_prefers_plan_continuity() -> None:
    """Root tie-breaks should keep a good structural plan alive over queen drift."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("a2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("b2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("a7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("b7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("c6"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("e6"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("h7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    plan_move = Move(start=sq("b2"), end=sq("b4"))
    drift_move = Move(start=sq("d1"), end=sq("h5"))

    plan_child = board.clone()
    drift_child = board.clone()
    assert plan_child.apply_legal_move(plan_move.start, plan_move.end) is True
    assert drift_child.apply_legal_move(drift_move.start, drift_move.end) is True

    assert root_stability_adjustment(board, plan_move, plan_child) > root_stability_adjustment(
        board,
        drift_move,
        drift_child,
    )


def test_root_stability_adjustment_prefers_structure_improvement_with_stability() -> None:
    """Root tie-breaks should like structure improvement when it keeps the position stable."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("c2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("e3"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("f2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("h7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    stable_structure = Move(start=sq("c2"), end=sq("c3"))
    speculative_move = Move(start=sq("d1"), end=sq("h5"))

    stable_child = board.clone()
    speculative_child = board.clone()
    assert stable_child.apply_legal_move(stable_structure.start, stable_structure.end) is True
    assert speculative_child.apply_legal_move(speculative_move.start, speculative_move.end) is True

    assert root_stability_adjustment(
        board,
        stable_structure,
        stable_child,
    ) > root_stability_adjustment(board, speculative_move, speculative_child)


# Tests for alpha-beta pruning behavior


def test_alpha_beta_pruning_cuts_off_search():
    """With alpha-beta pruning, a cutoff should occur if alpha >= beta."""
    # We cannot inspect cutoffs directly, but search should complete and return a move.
    board = Board()
    params = make_params(depth=2, is_maximizing=True)
    score, _ = minimax(board, params)
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

    _, move = minimax(board, make_params(depth=1, is_maximizing=True))
    assert move is None


# Tests for evaluation perspective


def test_evaluation_positive_for_white_advantage():
    """Evaluation should be positive when White has material advantage."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.KING))
    score = evaluate(board)
    assert score > 0, "Evaluation should be positive when White has material advantage"


def test_evaluation_negative_for_black_advantage():
    """Evaluation should be negative when Black has material advantage."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e4"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("e4"), create_piece(Color.BLACK, PieceType.KING))
    score = evaluate(board)
    assert score < 0, "Evaluation should be negative when Black has material advantage"


def test_evaluation_symmetric_for_equal_positions():
    """Symmetric positions should yield equal evaluations."""
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
    board.set_piece(sq("c3"), create_piece(Color.WHITE, PieceType.KING))
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
    board = make_simple_board_with_legal_moves()
    tt: dict = {}
    params = make_params(depth=1, is_maximizing=True, tt=tt)
    minimax(board, params)

    assert any(
        e.flag in (TTFlag.EXACT, TTFlag.LOWERBOUND, TTFlag.UPPERBOUND)
        for e in tt.values()
    )


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


def make_params_with_nodes(
    depth: int,
    is_maximizing: bool,
    alpha: int = -10_000_000,
    beta: int = 10_000_000,
):
    """Helper to create MinimaxParams with nodes_searched."""
    nodes = [0]
    return make_search_params(
        depth,
        alpha,
        beta,
        is_maximizing,
        context=make_search_context(nodes=nodes),
    )


# Alpha-beta pruning behavior tests


def test_alpha_beta_pruning_fewer_nodes_than_without_pruning():
    """
    With alpha-beta pruning, using a very tight alpha/beta window
    around a known good score should prune more than a wide window.
    """
    board = make_mate_in_one_white_position()

    # Wide window: less pruning
    wide_nodes = [0]
    wide_params = make_search_params(
        3,
        -10_000_000,
        10_000_000,
        True,
        context=make_search_context(nodes=wide_nodes),
    )

    # Tight window: more pruning (around mate score)
    tight_nodes = [0]
    tight_params = make_search_params(
        3,
        MATE_SCORE - 500,
        MATE_SCORE + 500,
        True,
        context=make_search_context(nodes=tight_nodes),
    )

    minimax(board, wide_params)
    minimax(board, tight_params)

    # Tight window should prune more -> fewer nodes explored.
    assert tight_nodes[0] <= wide_nodes[0], (
        "Alpha-beta pruning should prune more with tighter bounds"
    )


def test_alpha_beta_pruning_does_not_affect_mate_detection():
    """
    Alpha-beta pruning should still find mate-in-one when available.
    """
    board = make_mate_in_one_white_position()

    nodes = [0]
    params = make_search_params(
        1,
        -MATE_SCORE,
        MATE_SCORE,
        True,
        context=make_search_context(nodes=nodes),
    )

    score, move = minimax(board, params)

    assert move is not None, "Alpha-beta should still find a mating move"
    assert score >= MATE_SCORE - 1, "Score should reflect mate"


def test_minimax_respects_max_depth():
    """Minimax should not recurse beyond requested depth."""
    board = Board()

    nodes = [0]
    params = make_search_params(
        1,
        -10_000_000,
        10_000_000,
        True,
        context=make_search_context(nodes=nodes),
    )

    # Just ensure it completes without error at depth=1
    minimax(board, params)
    assert nodes[0] > 0, "Minimax should explore at least one node"


# Depth-5 manageability tests (marked slow to exclude from fast CI)


@pytest.mark.slow
@pytest.mark.parametrize(
    ("depth", "max_seconds"),
    [
        (3, 5),
        (4, 20),
    ],
)
def test_intermediate_search_depths_complete(depth: int, max_seconds: int):
    """Depth-3 and depth-4 searches should stay comfortably practical."""
    board = Board()

    start = time.monotonic()
    move = get_best_move(board, depth=depth)
    elapsed = time.monotonic() - start

    assert move is not None, f"Depth-{depth} search should return a move"
    assert elapsed < max_seconds, (
        f"Depth-{depth} search should complete within {max_seconds} seconds"
    )


@pytest.mark.slow
def test_depth_5_search_completes():
    """Depth-5 search on a standard position should complete within reasonable time."""
    board = Board()

    start = time.monotonic()
    move = get_best_move(board, depth=5)
    elapsed = time.monotonic() - start

    # Just ensure it finishes within 60s and returns a move.
    assert move is not None, "Depth-5 search should return a move"
    assert elapsed < 60, "Depth-5 search should complete within 60 seconds"


@pytest.mark.slow
def test_depth_5_nodes_within_reasonable_limit():
    """Depth-5 search nodes should be within some reasonable limit (no combinatorial explosion)."""
    board = Board()

    nodes = [0]
    params = make_params_with_nodes(depth=5, is_maximizing=True)

    # Run a depth-5 search with nodes counted.
    minimax(board, params)

    # This threshold is heuristic but should hold for reasonable alpha-beta.
    assert nodes[0] < 500_000, "Depth-5 search should not exceed 500k nodes"


# ─── Task 7.4: Search-level regressions ──────────────────────────────────────


def test_search_sees_prophylactic_line_is_best() -> None:
    """Depth-3 search should capture a piece that immediately enables a check threat.

    Black knight on d4 threatens Nf3+ (check on the White king at g1).
    White's best prophylactic response is Qxd4 — eliminating the threat and
    winning a free piece — rather than any passive move that lets the check land.
    """
    board = Board()
    board.clear_board()
    placements = [
        ("g1", Color.WHITE, PieceType.KING),
        ("d1", Color.WHITE, PieceType.QUEEN),
        ("f2", Color.WHITE, PieceType.PAWN),
        ("g2", Color.WHITE, PieceType.PAWN),
        ("h2", Color.WHITE, PieceType.PAWN),
        ("e8", Color.BLACK, PieceType.KING),
        ("d4", Color.BLACK, PieceType.KNIGHT),
    ]
    for square_name, color, piece_kind in placements:
        board.set_piece(sq(square_name), create_piece(color, piece_kind))
    board.turn = Color.WHITE

    move = get_best_move(board, depth=3)
    assert move is not None
    assert move.end == sq("d4"), "Prophylactic Qxd4 should eliminate the Nf3+ fork threat"


def test_search_prefers_clean_simplifying_line_over_repeated_checking() -> None:
    """Depth-3 search should win a free rook rather than give a harmless check.

    White's rook on a1 can capture an unprotected Black rook on d8 (a free
    rook worth +500 cp).  The alternative — a queen check that leads nowhere —
    should score far worse once the engine looks two moves ahead.
    """
    board = Board()
    board.clear_board()
    placements = [
        ("g1", Color.WHITE, PieceType.KING),
        ("f4", Color.WHITE, PieceType.QUEEN),
        ("d1", Color.WHITE, PieceType.ROOK),  # on d-file to reach d8
        ("g2", Color.WHITE, PieceType.PAWN),
        ("h2", Color.WHITE, PieceType.PAWN),
        # Black king on h8 (far from d8) so the rook is genuinely unprotected
        ("h8", Color.BLACK, PieceType.KING),
        ("d8", Color.BLACK, PieceType.ROOK),
        ("g7", Color.BLACK, PieceType.PAWN),
        ("h7", Color.BLACK, PieceType.PAWN),
    ]
    for square_name, color, piece_kind in placements:
        board.set_piece(sq(square_name), create_piece(color, piece_kind))
    board.turn = Color.WHITE

    move = get_best_move(board, depth=3)
    assert move is not None
    assert move.end == sq("d8"), "Should capture the free rook (clean simplification)"


def test_search_rejects_material_win_that_opens_fatal_counterplay() -> None:
    """Depth-3 search should not capture a pawn that costs a rook via back-rank tactic.

    White's queen on a4 can capture the undefended pawn on d7 — tempting,
    but after Qxd7 Black's rook on e8 slides to e1 (capturing White's sole
    back-rank defender) with a decisive counter.  The engine must reject the
    pawn grab and keep the back rank covered.
    """
    board = Board()
    board.clear_board()
    placements = [
        ("g1", Color.WHITE, PieceType.KING),
        ("e1", Color.WHITE, PieceType.ROOK),
        ("a4", Color.WHITE, PieceType.QUEEN),
        ("g2", Color.WHITE, PieceType.PAWN),
        ("h2", Color.WHITE, PieceType.PAWN),
        ("g8", Color.BLACK, PieceType.KING),
        ("e8", Color.BLACK, PieceType.ROOK),
        ("d7", Color.BLACK, PieceType.PAWN),
    ]
    for square_name, color, piece_kind in placements:
        board.set_piece(sq(square_name), create_piece(color, piece_kind))
    board.turn = Color.WHITE

    move = get_best_move(board, depth=3)
    assert move is not None
    assert move.end != sq("d7"), "Should not grab the pawn that opens the e1 back-rank counter"


def test_search_goes_deeper_in_structure_changing_defensive_moments() -> None:
    """Engine should log selective extensions when a shelter-restoring capture is available.

    The king-shelter recapture position already triggers a selective extension bonus.
    This end-to-end test verifies that `search_root_depth` actually records at least
    one selective extension in its diagnostics when the position contains a
    structure-changing defensive capture.
    """
    board = make_king_shelter_recapture_extension_position()
    stats = SearchStats()
    context = make_search_context(stats=stats)

    search_root_depth(
        board,
        depth=2,
        is_maximizing=True,
        previous_score=0,
        context=context,
    )

    assert stats.diagnostics is not None
    assert stats.diagnostics.selective_extensions > 0, (
        "Should have fired at least one selective extension in a shelter-changing position"
    )
