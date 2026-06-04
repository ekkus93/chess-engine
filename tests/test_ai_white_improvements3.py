"""Regressions for WHITE_IMPROVEMENTS3: castling urgency — path-blocked scaling,
late-castling base, and flank-pawn-poke ordering penalty.

All positions are constructed directly (no transcript dependency).
"""

from __future__ import annotations

from chess_game.chess.ai import get_best_move
from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.move import Move, parse_move_notation
from chess_game.chess.opening_development import (
    castling_path_blocked_penalty,
    late_castling_urgency_penalty,
)
from chess_game.chess.opening_move_ordering import (
    QUIET_CLEARS_CASTLING_PATH_BONUS,
    QUIET_FLANK_PAWN_POKE_PENALTY,
    opening_discipline_order_score,
)
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def _m(notation: str) -> Move:
    p = parse_move_notation(notation)
    return Move(start=p.start, end=p.end, promotion=p.promotion)


def _pos_f1_bishop_blocking(fullmove: int = 5) -> Board:
    """White king at e1 (uncastled), f1 bishop still home blocking castling.

    Typical mid-opening position: White has Nf3 and d4 pawn but f1 bishop
    blocks kingside castling.  b2 is empty (b4 push is legal).
    """
    board = Board()
    board.clear_board()
    # White pieces
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.BISHOP))  # blocking!
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("c3"), create_piece(Color.WHITE, PieceType.PAWN))
    # Black pieces
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("c6"), create_piece(Color.BLACK, PieceType.KNIGHT))
    board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("e5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE
    board.fullmove_number = fullmove
    return board


def _pos_path_cleared(fullmove: int = 5) -> Board:
    """Same position but f1 bishop has moved to e2 — path is clear."""
    board = _pos_f1_bishop_blocking(fullmove)
    board.clear_square(sq("f1"))
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.BISHOP))
    return board


# ---------------------------------------------------------------------------
# Test 1: castling_path_blocked_penalty scales with fullmove
# ---------------------------------------------------------------------------


def test_castling_path_blocked_penalty_fires_at_fm5() -> None:
    """castling_path_blocked_penalty should fire when f1 bishop blocks castling."""
    board = _pos_f1_bishop_blocking(fullmove=5)
    penalty = castling_path_blocked_penalty(board, Color.WHITE)
    assert penalty > 0, f"Expected positive penalty at fullmove 5, got {penalty}"


def test_castling_path_blocked_penalty_grows_past_fm6() -> None:
    """castling_path_blocked_penalty should be larger at fullmove 10 than fullmove 5."""
    board_early = _pos_f1_bishop_blocking(fullmove=5)
    board_late = _pos_f1_bishop_blocking(fullmove=10)
    early = castling_path_blocked_penalty(board_early, Color.WHITE)
    late = castling_path_blocked_penalty(board_late, Color.WHITE)
    assert late > early, (
        f"Penalty should grow with fullmove: fm5={early}, fm10={late}"
    )


def test_castling_path_blocked_penalty_zero_when_cleared() -> None:
    """castling_path_blocked_penalty should be 0 when f1 bishop has moved."""
    board = _pos_path_cleared(fullmove=5)
    penalty = castling_path_blocked_penalty(board, Color.WHITE)
    assert penalty == 0, f"Expected 0 after bishop clears path, got {penalty}"


# ---------------------------------------------------------------------------
# Test 4: late_castling_urgency_penalty is meaningful at fullmove 5
# ---------------------------------------------------------------------------


def test_late_castling_urgency_at_fm5_significant() -> None:
    """late_castling_urgency_penalty at fullmove 5 should be ≥ 32 cp."""
    board = _pos_f1_bishop_blocking(fullmove=5)
    penalty = late_castling_urgency_penalty(board, Color.WHITE)
    assert penalty >= 32, (
        f"Expected late castling urgency ≥ 32 cp at fullmove 5, got {penalty}"
    )


# ---------------------------------------------------------------------------
# Test 2: Developing bishop to clear path scores higher than wing pawn push
# ---------------------------------------------------------------------------


def test_clears_path_bonus_constant_positive() -> None:
    """QUIET_CLEARS_CASTLING_PATH_BONUS should be positive and meaningful."""
    assert QUIET_CLEARS_CASTLING_PATH_BONUS >= 48, (
        f"Expected QUIET_CLEARS_CASTLING_PATH_BONUS >= 48, got {QUIET_CLEARS_CASTLING_PATH_BONUS}"
    )


def test_flank_pawn_poke_penalty_constant_large() -> None:
    """QUIET_FLANK_PAWN_POKE_PENALTY should be large enough to deter b4 while uncastled."""
    assert QUIET_FLANK_PAWN_POKE_PENALTY >= 32, (
        f"Expected QUIET_FLANK_PAWN_POKE_PENALTY >= 32, got {QUIET_FLANK_PAWN_POKE_PENALTY}"
    )


def test_bf1_development_scores_above_b4_when_path_blocked() -> None:
    """Developing Bf1 should score ≥ 40 cp higher in ordering than b2-b4."""
    board = _pos_f1_bishop_blocking(fullmove=5)
    bf1e2 = _m("f1e2")
    b4 = _m("b2b4")
    bf1_score = opening_discipline_order_score(board, PieceType.BISHOP, bf1e2)
    b4_score = opening_discipline_order_score(board, PieceType.PAWN, b4)
    gap = bf1_score - b4_score
    assert gap >= 40, (
        f"Bf1-e2 ({bf1_score}) should score ≥ 40 above b2-b4 ({b4_score}), got gap={gap}"
    )


# ---------------------------------------------------------------------------
# Test 5: Depth-3 search prefers castling/development over b4 when path blocked
# ---------------------------------------------------------------------------


def _pos_game2_opening() -> Board:
    """Approximate game-2 opening at fullmove 5, White to move.

    White has Nf3 + Nc3 developed; both bishops still home blocking castling.
    Black has played d5 and e5 with a c6 knight.
    """
    board = Board()
    board.clear_board()
    # White
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("d5"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
    # Black
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("f8"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.set_piece(sq("c8"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("c6"), create_piece(Color.BLACK, PieceType.KNIGHT))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KNIGHT))
    board.set_piece(sq("e5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("c5"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.turn = Color.WHITE
    board.fullmove_number = 5
    return board


def test_depth3_avoids_b4_when_path_blocked() -> None:
    """Depth-3 should NOT choose b2-b4 when f1/c1 bishops block castling."""
    board = _pos_game2_opening()
    best = get_best_move(board, depth=3)
    b4 = _m("b2b4")
    assert best is None or not (best.start == b4.start and best.end == b4.end), (
        "depth=3 should avoid b2-b4 when both bishops block castling path"
    )
