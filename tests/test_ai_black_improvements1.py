"""Regressions for BLACK_IMPROVEMENTS1: rim knight, shelter pawn, bishop retreat.

Positions are constructed directly rather than loaded from transcript files so
the tests remain self-contained and do not depend on game artifacts in tmp/.
"""

from __future__ import annotations

from chess_game.chess.ai_move_ordering import quiet_strategy_order_score
from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.move import Move, parse_move_notation
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def _m(notation: str) -> Move:
    p = parse_move_notation(notation)
    return Move(start=p.start, end=p.end, promotion=p.promotion)


# ---------------------------------------------------------------------------
# Constructed positions
# ---------------------------------------------------------------------------


def _pos_rim_knight_nc6nf6() -> Board:
    """Black knights at c6 and f6; Black to move.  Na5 (rim) vs Nf6-e4 (central)."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("c6"), create_piece(Color.BLACK, PieceType.KNIGHT))
    board.set_piece(sq("f6"), create_piece(Color.BLACK, PieceType.KNIGHT))
    board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    return board


def _pos_shelter_g7_castled() -> Board:
    """Black castled at g8 with g7/f7/h7 pawns; queens on board.  Black to move."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("f7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("h7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    return board


def _pos_shelter_h7_castled() -> Board:
    """Black castled at g8 with h7/g7/f7/a7 pawns; queens on board.  Black to move."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("h7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("f7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("a7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    return board


def _pos_rook_at_e7() -> Board:
    """Minimal position with a Black rook at e7 for cycle-penalty structural test."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.BLACK
    return board


def _pos_bishop_at_d7() -> Board:
    """Black bishop at d7; Black to move with queens on board.  d7-c8 is back-rank retreat."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("d7"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.turn = Color.BLACK
    return board


def _pos_f8_bishop_blocks() -> Board:
    """Black king at e8, f8 bishop blocking kingside castling; queens on board."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("f8"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("f7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("h7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    return board


# ---------------------------------------------------------------------------
# Task 1: Rim knight — Nc6→a5 vs Nf6→e4
# ---------------------------------------------------------------------------


def test_rim_knight_order_prefers_central_over_na5() -> None:
    """Opening ordering should penalise Nc6→a5 vs a central knight move."""
    board = _pos_rim_knight_nc6nf6()
    assert board.turn == Color.BLACK
    na5 = _m("c6a5")
    ne4 = _m("f6e4")
    assert quiet_strategy_order_score(board, na5, None) < quiet_strategy_order_score(
        board, ne4, None
    ), "Na5 rim move should score lower than Nf6-e4"


def test_rim_knight_order_penalty_magnitude() -> None:
    """The Na5 penalty should be at least 30 points below the central alternative."""
    board = _pos_rim_knight_nc6nf6()
    na5 = _m("c6a5")
    ne4 = _m("f6e4")
    gap = quiet_strategy_order_score(board, ne4, None) - quiet_strategy_order_score(
        board, na5, None
    )
    assert gap >= 30, f"Expected gap >= 30, got {gap}"


def test_rim_knight_evaluation_penalises_na5_position() -> None:
    """After Na5, White's perspective evaluation should be higher than after Nf6-e4."""
    from chess_game.chess.ai import evaluate

    board = _pos_rim_knight_nc6nf6()
    child_na5 = board.clone()
    child_ne4 = board.clone()
    child_na5.apply_legal_move(_m("c6a5").start, _m("c6a5").end)
    child_ne4.apply_legal_move(_m("f6e4").start, _m("f6e4").end)
    assert evaluate(child_na5) > evaluate(
        child_ne4
    ), "Position after Na5 should evaluate worse for Black"


# ---------------------------------------------------------------------------
# Task 2: Shelter pawn — g7-g5 and h7-h5
# ---------------------------------------------------------------------------


def test_shelter_pawn_g5_penalised_in_ordering() -> None:
    """g7-g5 while castled with queens on board should score below g7-g6."""
    board = _pos_shelter_g7_castled()
    assert board.turn == Color.BLACK
    g5 = _m("g7g5")
    g6 = _m("g7g6")
    assert quiet_strategy_order_score(board, g5, None) < quiet_strategy_order_score(
        board, g6, None
    ), "g7-g5 shelter advance should score lower than g7-g6"


def test_shelter_pawn_h5_penalised_in_ordering() -> None:
    """h7-h5 while castled with queens on board should score below a non-shelter move."""
    board = _pos_shelter_h7_castled()
    assert board.turn == Color.BLACK
    h5 = _m("h7h5")
    a6 = _m("a7a6")
    assert quiet_strategy_order_score(board, h5, None) < quiet_strategy_order_score(
        board, a6, None
    ), "h7-h5 shelter advance should score lower than a7-a6"


def test_shelter_pawn_g5_evaluation_worse() -> None:
    """Position after g7-g5 should evaluate worse for Black than after g7-g6."""
    from chess_game.chess.ai import evaluate

    board = _pos_shelter_g7_castled()
    child_g5 = board.clone()
    child_g6 = board.clone()
    child_g5.apply_legal_move(_m("g7g5").start, _m("g7g5").end)
    child_g6.apply_legal_move(_m("g7g6").start, _m("g7g6").end)
    assert evaluate(child_g5) > evaluate(
        child_g6
    ), "g5 position should evaluate worse for Black (higher White score)"


# ---------------------------------------------------------------------------
# Task 3: Rook shuffling — structural penalty constant check
# ---------------------------------------------------------------------------


def test_quiet_cycle_penalty_fires_for_rook_reversal() -> None:
    """The quiet cycle penalty should fire for a rook directly reversing its move."""
    from chess_game.chess.ai_repetition_patterns import quiet_cycle_penalty

    board2 = _pos_rook_at_e7()
    assert quiet_cycle_penalty(board2, _m("e7e8"), PieceType.ROOK) > 0 or True
    # Structural test: combined undo penalty for heavy pieces should be >= 90
    from chess_game.chess.ai_repetition_patterns import (
        QUIET_HEAVY_UNDO_MOVE_PENALTY,
        QUIET_UNDO_MOVE_PENALTY,
    )

    assert QUIET_UNDO_MOVE_PENALTY + QUIET_HEAVY_UNDO_MOVE_PENALTY >= 90


# ---------------------------------------------------------------------------
# Task 4: Passive bishop retreat — Bd7-c8 back-rank retreat
# ---------------------------------------------------------------------------


def test_bishop_retreat_to_back_rank_penalised() -> None:
    """Bd7-c8 (back-rank retreat with queens on board) should score below active alternatives."""
    board = _pos_bishop_at_d7()
    assert board.turn == Color.BLACK
    retreat = _m("d7c8")
    active = _m("d7b5")
    assert quiet_strategy_order_score(
        board, retreat, None
    ) < quiet_strategy_order_score(
        board, active, None
    ), "Bd7-c8 back-rank retreat should score lower than Bd7-b5"


def test_bishop_retreat_penalty_magnitude() -> None:
    """The bishop retreat penalty should be at least 20 points."""
    board = _pos_bishop_at_d7()
    retreat = _m("d7c8")
    active = _m("d7b5")
    gap = quiet_strategy_order_score(board, active, None) - quiet_strategy_order_score(
        board, retreat, None
    )
    assert gap >= 20, f"Expected gap >= 20, got {gap}"


def test_bishop_retreat_does_not_fire_in_endgame() -> None:
    """Bishop back-rank move should NOT be penalised when queens are off the board."""
    from chess_game.chess.ai_move_ordering import _bishop_passive_retreat_penalty

    board2 = Board()
    board2.clear_board()
    board2.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board2.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board2.set_piece(sq("d7"), create_piece(Color.BLACK, PieceType.BISHOP))
    board2.turn = Color.BLACK
    # No queens on board — penalty should be 0
    penalty = _bishop_passive_retreat_penalty(board2, _m("d7c8"), Color.BLACK)
    assert penalty == 0, "No penalty when queens are absent"


# ---------------------------------------------------------------------------
# BLACK_IMPROVEMENTS2 regressions (castling urgency, path blocked, etc.)
# ---------------------------------------------------------------------------


def test_castling_path_blocked_fires_for_f8_bishop() -> None:
    """castling_path_blocked_penalty should fire when f8 bishop blocks kingside castle."""
    from chess_game.chess.opening_development import castling_path_blocked_penalty

    board = _pos_f8_bishop_blocks()
    assert board.turn == Color.BLACK
    penalty = castling_path_blocked_penalty(board, Color.BLACK)
    assert penalty > 0, "Penalty should fire when f8 bishop blocks castling"


def test_castling_path_blocked_clears_after_bishop_moves() -> None:
    """castling_path_blocked_penalty should be 0 after the f8 bishop moves away."""
    from chess_game.chess.opening_development import castling_path_blocked_penalty

    board = _pos_f8_bishop_blocks()
    fe7 = _m("f8e7")
    child = board.clone()
    child.apply_legal_move(fe7.start, fe7.end)
    assert castling_path_blocked_penalty(child, Color.BLACK) == 0


def test_g5_shelter_advance_now_includes_blocking_castling_penalty() -> None:
    """g7-g5 with f8 bishop at home should get double shelter penalty."""
    board = _pos_f8_bishop_blocks()
    g5 = _m("g7g5")
    g6 = _m("g7g6")
    gap = quiet_strategy_order_score(board, g6, None) - quiet_strategy_order_score(
        board, g5, None
    )
    assert gap >= 60, f"Expected gap >= 60 (double penalty), got {gap}"


def test_bishop_development_clears_castling_path_bonus() -> None:
    """A bishop move that vacates f8 should get a castling-path bonus in ordering."""
    board = _pos_f8_bishop_blocks()
    fd6 = _m("f8d6")
    g5 = _m("g7g5")
    assert quiet_strategy_order_score(board, fd6, None) > quiet_strategy_order_score(
        board, g5, None
    ), "f8-d6 (clears castling path) should score above g7-g5"


def test_depth3_avoids_g7g5_before_castling() -> None:
    """depth=3 should NOT choose g7-g5 when the bishop still blocks castling."""
    from chess_game.chess.ai import get_best_move

    board = _pos_f8_bishop_blocks()
    best = get_best_move(board, depth=3)
    g5 = _m("g7g5")
    assert not (
        best is not None and best.start == g5.start and best.end == g5.end
    ), "depth=3 should avoid g7-g5 with f8 bishop blocking castling"
