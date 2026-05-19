"""AI promotion move-identity regression tests — Task 6

Covers:
  - AI correctly distinguishes promotion moves with different promotion types
  - No StopIteration from matching moves on start/end only
  - AI returns correct promotion field for the chosen move
"""

from chess_game.chess.ai import (
    MinimaxParams,
    get_legal_moves,
    minimax,
)
from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def _setup_promo_ai_board() -> Board:
    """White pawn on d7, d8 empty, white to move. Minimal board for AI test."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d7"), create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE
    return board


def test_ai_promotion_no_stopiteration() -> None:
    """AI search with promotion moves must not raise StopIteration."""
    board = _setup_promo_ai_board()
    params = MinimaxParams(
        depth=1,
        alpha=-100_000_000,
        beta=100_000_000,
        is_maximizing=True,
    )
    score, move = minimax(board, params)
    assert move is not None
    assert move.start == sq("d7")
    assert move.end == sq("d8")


def test_ai_promotion_move_identity_queen() -> None:
    """AI should return a move whose promotion field matches the played piece."""
    board = _setup_promo_ai_board()
    params = MinimaxParams(
        depth=1,
        alpha=-100_000_000,
        beta=100_000_000,
        is_maximizing=True,
    )
    score, move = minimax(board, params)
    assert move is not None
    # Play the returned move on a fresh board and verify the promotion matches
    board2 = _setup_promo_ai_board()
    ok = board2.make_move(move.start, move.end, promotion=move.promotion)
    assert ok is True
    promoted_piece = board2.get_piece_type_at(move.end)
    assert promoted_piece == move.promotion


def test_ai_all_four_promotions_legal() -> None:
    """Legal moves for a pawn on d7 must include all 4 promotion types."""
    board = _setup_promo_ai_board()
    moves = get_legal_moves(board)
    promo_moves = [m for m in moves if m.end == sq("d8")]
    promo_types = {m.promotion for m in promo_moves}
    assert PieceType.QUEEN in promo_types
    assert PieceType.ROOK in promo_types
    assert PieceType.BISHOP in promo_types
    assert PieceType.KNIGHT in promo_types


def test_ai_promotion_depth2_no_crash() -> None:
    """AI search at depth 2 with promotion must not crash."""
    board = _setup_promo_ai_board()
    params = MinimaxParams(
        depth=2,
        alpha=-100_000_000,
        beta=100_000_000,
        is_maximizing=True,
    )
    score, move = minimax(board, params)
    assert move is not None or score != 0  # At least something returned
