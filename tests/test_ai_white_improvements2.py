"""Regressions for WHITE_IMPROVEMENTS2: early luft, castling urgency, KQvKR, pawn race.

Positions are constructed directly rather than loaded from transcript files so
the tests remain self-contained and do not depend on game artifacts in tmp/.
"""

from __future__ import annotations

from chess_game.chess.ai_move_ordering import (
    is_prophylactic_h_luft,
    quiet_strategy_order_score,
    QUIET_PROPHYLACTIC_LUFT_BONUS,
)
from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.move import Move, parse_move_notation
from chess_game.chess.opening_development import late_castling_urgency_penalty
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def _pos_white_castled_g1() -> Board:
    """White king castled at g1 with h2 pawn; queens on board.  White to move."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.turn = Color.WHITE
    return board


def _pos_white_uncastled_midgame() -> Board:
    """White king at e1 (uncastled) at fullmove 15; queens on board.  White to move."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.fullmove_number = 15  # past move 4 so late_castling_urgency fires
    board.turn = Color.WHITE
    return board


def _m(notation: str) -> Move:
    p = parse_move_notation(notation)
    return Move(start=p.start, end=p.end, promotion=p.promotion)


def _kqvkr_board(queen_color: Color) -> Board:
    """Minimal KQvKR board with queen side to move."""
    board = Board()
    board.clear_board()
    if queen_color == Color.WHITE:
        board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.QUEEN))
        board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
        board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.ROOK))
    else:
        board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
        board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.QUEEN))
        board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.turn = queen_color
    return board


# ---------------------------------------------------------------------------
# Task 1: Prophylactic luft
# ---------------------------------------------------------------------------


def test_is_prophylactic_h_luft_fires_after_castling() -> None:
    """is_prophylactic_h_luft should return True when king is castled at g1."""
    board = _pos_white_castled_g1()
    assert board.find_king(Color.WHITE) is not None
    assert is_prophylactic_h_luft(board, Color.WHITE)


def test_h3_ordering_positive_after_castling() -> None:
    """h2-h3 should score positively after castling (not negative from old penalties)."""
    board = _pos_white_castled_g1()
    h3 = _m("h2h3")
    score = quiet_strategy_order_score(board, h3, None)
    assert score > 0, f"h2-h3 should score positively, got {score}"


def test_h3_competitive_with_other_moves_after_castling() -> None:
    """After castling h2-h3 should score at least +20 (prophylactic bonus active)."""
    board = _pos_white_castled_g1()
    h3 = _m("h2h3")
    score = quiet_strategy_order_score(board, h3, None)
    assert score >= 20, (
        f"h2-h3 should score >= 20 after castling (prophylactic bonus), got {score}"
    )


def test_prophylactic_luft_constant_positive() -> None:
    """QUIET_PROPHYLACTIC_LUFT_BONUS should be positive."""
    assert QUIET_PROPHYLACTIC_LUFT_BONUS > 0


def test_tactical_transition_does_not_penalise_h3() -> None:
    """h2-h3 (1-square advance) should not receive shelter-loosening penalty."""
    from chess_game.chess.tactical_transition_guidance import tactical_transition_order_bonus
    board = _pos_white_castled_g1()
    h3 = _m("h2h3")
    bonus = tactical_transition_order_bonus(board, h3)
    assert bonus >= 0, f"tactical_transition should not penalise h2-h3, got {bonus}"


# ---------------------------------------------------------------------------
# Task 2: Castling urgency
# ---------------------------------------------------------------------------


def test_late_castling_urgency_fires_when_uncastled_with_queens() -> None:
    """late_castling_urgency_penalty should fire when king is uncastled with queens on board."""
    board = _pos_white_uncastled_midgame()
    penalty = late_castling_urgency_penalty(board, Color.WHITE)
    assert penalty > 0, (
        f"Uncastled king with queens should have urgency penalty > 0, got {penalty}"
    )


def test_castling_urgency_bonus_increased() -> None:
    """QUIET_OPENING_CASTLING_URGENCY_BONUS should be at least 50."""
    from chess_game.chess.opening_move_ordering import QUIET_OPENING_CASTLING_URGENCY_BONUS
    assert QUIET_OPENING_CASTLING_URGENCY_BONUS >= 50


def test_late_castling_urgency_bonus_increased() -> None:
    """QUIET_LATE_CASTLING_URGENCY_BONUS should be at least 60."""
    from chess_game.chess.opening_move_ordering import QUIET_LATE_CASTLING_URGENCY_BONUS
    assert QUIET_LATE_CASTLING_URGENCY_BONUS >= 60


# ---------------------------------------------------------------------------
# Task 3: Queen-vs-rook endgame
# ---------------------------------------------------------------------------


def test_queen_vs_rook_evaluation_positive_for_queen_side() -> None:
    """evaluate_queen_vs_rook should give positive score to the queen side."""
    from chess_game.chess.ai import get_evaluation_breakdown
    board = _kqvkr_board(Color.WHITE)
    breakdown = get_evaluation_breakdown(board)
    assert "queen_vs_rook" in breakdown
    assert breakdown["queen_vs_rook"] > 0, (
        f"Queen side should get positive queen_vs_rook score, got {breakdown['queen_vs_rook']}"
    )


def test_queen_vs_rook_zero_in_non_kqvkr_position() -> None:
    """evaluate_queen_vs_rook should return 0 when not a KQvKR position."""
    from chess_game.chess.endgame_evaluation import evaluate_queen_vs_rook
    board = Board()
    assert evaluate_queen_vs_rook(board, 100) == 0


def test_passive_rook_penalised_in_kqvkr() -> None:
    """Rook on back rank in KQvKR should score worse than active rook."""
    from chess_game.chess.endgame_evaluation import evaluate_queen_vs_rook
    board_passive = _kqvkr_board(Color.WHITE)
    board_active = _kqvkr_board(Color.WHITE)
    board_active.clear_square(sq("a8"))
    board_active.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.ROOK))
    score_passive = evaluate_queen_vs_rook(board_passive, 100)
    score_active = evaluate_queen_vs_rook(board_active, 100)
    assert score_passive < score_active, (
        f"Passive rook on back rank ({score_passive}) should score below active rook ({score_active})"
    )


# ---------------------------------------------------------------------------
# Task 4: Pawn promotion race
# ---------------------------------------------------------------------------


def test_enemy_passer_danger_bonus_increased() -> None:
    """_ENEMY_PASSER_DANGER_BONUS should be at least 25 after increase."""
    import chess_game.chess.passer_race_guidance as prg
    assert prg._ENEMY_PASSER_DANGER_BONUS >= 25


def test_near_promotion_passer_penalty_fires_for_quiet_move() -> None:
    """_ignore_near_promotion_passer_penalty should penalise quiet non-pawn moves."""
    from chess_game.chess.ai_search_helpers import _ignore_near_promotion_passer_penalty
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("h3"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("a2"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE
    rook_move = _m("h3h4")
    penalty = _ignore_near_promotion_passer_penalty(board, rook_move, PieceType.ROOK, Color.WHITE)
    assert penalty > 0, f"Should penalise ignoring Black's near-promotion passer, got {penalty}"
