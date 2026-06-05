"""Regressions for BLACK_IMPROVEMENTS3: knight strong-square, knight threatens
minor, and rook on 7th rank endgame bonuses.

Positions are constructed directly so tests remain self-contained.
"""

from __future__ import annotations

from chess_game.chess.ai import evaluate
from chess_game.chess.ai_move_ordering import (
    _knight_threatens_minor_bonus,
    quiet_strategy_order_score,
)
from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.endgame_evaluation import (
    _ROOK_SEVENTH_RANK_ENDGAME_BONUS,
    _rook_seventh_rank_endgame_score,
)
from chess_game.chess.evaluation import _is_knight_strong_square
from chess_game.chess.evaluation_tables import (
    KNIGHT_OUTPOST_BONUS,
    KNIGHT_STRONG_SQUARE_BONUS,
)
from chess_game.chess.move import Move, parse_move_notation
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def _m(notation: str) -> Move:
    p = parse_move_notation(notation)
    return Move(start=p.start, end=p.end, promotion=p.promotion)


# ---------------------------------------------------------------------------
# Task 1 helpers: knight strong-square evaluation
# ---------------------------------------------------------------------------


def _pos_knight_at_e3() -> Board:
    """Minimal position with White knight at e3 and no special features."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("a7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("b7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE
    return board


def _pos_knight_at_f5() -> Board:
    """Same position but White knight has moved to f5 (strong square)."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f5"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("a7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("b7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE
    return board


# ---------------------------------------------------------------------------
# Task 1 tests: _is_knight_strong_square
# ---------------------------------------------------------------------------


def test_knight_strong_square_empty_enemy_pawns() -> None:
    """f5 with no Black pawns at all is a strong square."""
    assert _is_knight_strong_square(Color.WHITE, 3, 5, []) is True


def test_knight_strong_square_adjacent_file_blocks() -> None:
    """Black pawn on e5 (row=3, col=4) is adjacent to f5 (col=5), so not strong."""
    assert _is_knight_strong_square(Color.WHITE, 3, 5, [(3, 4)]) is False


def test_knight_strong_square_adjacent_g_file_blocks() -> None:
    """Black pawn on g5 (row=3, col=6) is adjacent to f5 (col=5), so not strong."""
    assert _is_knight_strong_square(Color.WHITE, 3, 5, [(3, 6)]) is False


def test_knight_strong_square_non_adjacent_file_ok() -> None:
    """Black pawn on d5 (col=3) is not adjacent to f5 (col=5), still strong."""
    assert _is_knight_strong_square(Color.WHITE, 3, 5, [(3, 3)]) is True


def test_knight_strong_square_game3_black_pawns() -> None:
    """Game-3 Black pawns a7/b7/d5 — none adjacent to f5's file, so f5 is strong."""
    black_pawns = [(1, 0), (1, 1), (3, 3)]  # a7, b7, d5
    assert _is_knight_strong_square(Color.WHITE, 3, 5, black_pawns) is True


def test_knight_strong_square_not_advanced_white() -> None:
    """White knight on e3 (row=5) is not advanced — not a strong square."""
    assert _is_knight_strong_square(Color.WHITE, 5, 4, []) is False


def test_knight_strong_square_black_perspective() -> None:
    """Black knight on d4 (row=4, col=3) is advanced from Black's perspective."""
    assert _is_knight_strong_square(Color.BLACK, 4, 3, []) is True


def test_knight_strong_square_black_not_advanced() -> None:
    """Black knight on d5 (row=3) is NOT advanced from Black's perspective (needs row>=4)."""
    assert _is_knight_strong_square(Color.BLACK, 3, 3, []) is False


# ---------------------------------------------------------------------------
# Task 1 tests: constant values
# ---------------------------------------------------------------------------


def test_knight_strong_square_bonus_positive() -> None:
    assert KNIGHT_STRONG_SQUARE_BONUS > 0


def test_knight_strong_square_bonus_less_than_outpost() -> None:
    """Strong square (no pawn support) should be weaker than a full outpost."""
    assert KNIGHT_STRONG_SQUARE_BONUS < KNIGHT_OUTPOST_BONUS


# ---------------------------------------------------------------------------
# Task 1 tests: evaluation impact
# ---------------------------------------------------------------------------


def test_knight_at_f5_evaluates_higher_than_e3() -> None:
    """With Black pawns a7/b7/d5, White knight at f5 should score higher than e3."""
    score_e3 = evaluate(_pos_knight_at_e3())
    score_f5 = evaluate(_pos_knight_at_f5())
    assert score_f5 > score_e3, (
        f"Expected knight at f5 to score higher than e3, "
        f"got e3={score_e3} f5={score_f5}"
    )


# ---------------------------------------------------------------------------
# Task 2 helpers: knight threatens enemy minor
# ---------------------------------------------------------------------------


def _pos_knight_threatens_bishop() -> Board:
    """White Nf3 about to jump to e5 where it attacks Black bishop on c6."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("c6"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.turn = Color.WHITE
    return board


def _pos_queen_threatens_bishop() -> Board:
    """White queen moving to e5 — bonus should NOT fire (wrong piece type)."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("c6"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.turn = Color.WHITE
    return board


# ---------------------------------------------------------------------------
# Task 2 tests: _knight_threatens_minor_bonus
# ---------------------------------------------------------------------------


def test_knight_threatens_minor_fires_for_bishop_target() -> None:
    """Ne5 attacks Black bishop on c6 — bonus should be positive."""
    board = _pos_knight_threatens_bishop()
    move = _m("f3e5")
    bonus = _knight_threatens_minor_bonus(board, move, Color.WHITE)
    assert bonus > 0, f"Expected positive bonus for Ne5 threatening Bc6, got {bonus}"


def test_knight_threatens_minor_fires_for_knight_target() -> None:
    """Knight move that attacks an enemy knight should also trigger the bonus."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("c6"), create_piece(Color.BLACK, PieceType.KNIGHT))
    board.turn = Color.WHITE
    move = _m("f3e5")
    bonus = _knight_threatens_minor_bonus(board, move, Color.WHITE)
    assert bonus > 0


def test_knight_threatens_minor_no_target() -> None:
    """Ne5 with no enemy piece on attacked squares — bonus should be 0."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE
    move = _m("f3e5")
    bonus = _knight_threatens_minor_bonus(board, move, Color.WHITE)
    assert bonus == 0


def test_knight_threatens_minor_not_for_queen_on_attacked_square() -> None:
    """Ne5 attacking Black queen on c6 — queen is NOT a minor, bonus should be 0."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("c6"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.turn = Color.WHITE
    move = _m("f3e5")
    bonus = _knight_threatens_minor_bonus(board, move, Color.WHITE)
    assert bonus == 0


def test_knight_threatens_minor_ordering_bonus_in_score() -> None:
    """Ne5 (threatens Bc6) should score higher in quiet ordering than a neutral move."""
    board = _pos_knight_threatens_bishop()
    score_threatens = quiet_strategy_order_score(board, _m("f3e5"))
    score_neutral = quiet_strategy_order_score(board, _m("f3h4"))
    assert score_threatens > score_neutral, (
        f"Ne5 (threatens bishop, score={score_threatens}) should beat "
        f"Nh4 (score={score_neutral})"
    )


# ---------------------------------------------------------------------------
# Task 3 helpers: rook on 7th rank
# ---------------------------------------------------------------------------


def _pos_rook_on_seventh_with_targets() -> Board:
    """White rook on e7 (row=1), Black pawns a7/b7 (also row=1 = rank 7)."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("a7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("b7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE
    return board


def _pos_rook_on_seventh_no_targets() -> Board:
    """White rook on e7, but all Black pawns are advanced past the 7th rank."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("a4"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE
    return board


def _pos_rook_not_on_seventh() -> Board:
    """White rook on e5 (not rank 7), Black pawns on 7th rank."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("a7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE
    return board


def _pos_black_rook_on_second_rank() -> Board:
    """Black rook on e2 (row=6, Black's 7th rank), White pawns on rows 5-7."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e2"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("a2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("b2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.BLACK
    return board


# ---------------------------------------------------------------------------
# Task 3 tests: _rook_seventh_rank_endgame_score
# ---------------------------------------------------------------------------


def test_rook_seventh_rank_bonus_constant_range() -> None:
    assert 18 <= _ROOK_SEVENTH_RANK_ENDGAME_BONUS <= 32


def test_rook_seventh_rank_fires_with_targets() -> None:
    """White rook on 7th rank with enemy pawns there → positive score."""
    board = _pos_rook_on_seventh_with_targets()
    score = _rook_seventh_rank_endgame_score(board, Color.WHITE)
    assert score > 0, f"Expected positive score for rook on 7th with targets, got {score}"


def test_rook_seventh_rank_zero_without_targets() -> None:
    """White rook on 7th rank but no Black pawns in first 3 ranks → 0."""
    board = _pos_rook_on_seventh_no_targets()
    score = _rook_seventh_rank_endgame_score(board, Color.WHITE)
    assert score == 0, f"Expected 0 without target pawns, got {score}"


def test_rook_seventh_rank_zero_when_not_on_seventh() -> None:
    """White rook NOT on 7th rank → 0 even with Black pawns."""
    board = _pos_rook_not_on_seventh()
    score = _rook_seventh_rank_endgame_score(board, Color.WHITE)
    assert score == 0


def test_rook_seventh_rank_black_perspective() -> None:
    """Black rook on 2nd rank (row=6) with White pawns → positive score for Black."""
    board = _pos_black_rook_on_second_rank()
    score = _rook_seventh_rank_endgame_score(board, Color.BLACK)
    assert score > 0, f"Expected positive score for Black rook on 2nd rank, got {score}"
