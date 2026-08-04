"""Promotion move-generation regression tests — Task 2

Covers:
  - get_legal_moves() emits all 4 promotion choices (q/r/b/n) for white/black
  - Quiet and capture promotion destinations each produce 4 moves
  - No duplicate (start, end, promotion) entries
"""

from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.color import Color
from chess_game.chess.types import PieceType
from tests.helpers import sq

# ── Helpers ──────────────────────────────────────────────────────────────────

def _setup_promotion_board(
    white_king_row: int,
    white_king_col: int,
    black_king_row: int,
    black_king_col: int,
    pawn_row: int,
    pawn_col: int,
    pawn_color: Color,
    extra_pieces: list = None,
) -> Board:
    """Create an empty board with kings and a pawn ready to promote."""
    board = Board()
    board.clear_board()
    board.set_piece(
        sq(f"{chr(ord('a') + white_king_col)}{8 - white_king_row}"),
        create_piece(Color.WHITE, PieceType.KING),
    )
    board.set_piece(
        sq(f"{chr(ord('a') + black_king_col)}{8 - black_king_row}"),
        create_piece(Color.BLACK, PieceType.KING),
    )
    board.set_piece(
        sq(f"{chr(ord('a') + pawn_col)}{8 - pawn_row}"),
        create_piece(pawn_color, PieceType.PAWN),
    )
    board.turn = pawn_color
    if extra_pieces:
        for (pr, pc, color, kind) in extra_pieces:
            board.set_piece(
                sq(f"{chr(ord('a') + pc)}{8 - pr}"),
                create_piece(color, kind),
            )
    return board


def promotions_for(board: Board, start: str, end: str) -> set[PieceType]:
    """Return the set of promotion piece types for moves from start to end."""
    start_sq = sq(start)
    end_sq = sq(end)
    return {
        promotion
        for move_start, move_end, promotion in board.get_legal_moves()
        if move_start == start_sq and move_end == end_sq and promotion is not None
    }


# ── 2.2 White quiet promotion generation ─────────────────────────────────────

def test_white_quiet_promotion_all_four() -> None:
    """White pawn on e7 → e8 (empty) must generate q/r/b/n."""
    board = _setup_promotion_board(
        1, 0, 0, 7, 1, 4, Color.WHITE,
    )
    assert promotions_for(board, "e7", "e8") == {
        PieceType.QUEEN,
        PieceType.ROOK,
        PieceType.BISHOP,
        PieceType.KNIGHT,
    }


# ── 2.3 White capture promotion generation ───────────────────────────────────

def test_white_capture_promotion_all_four() -> None:
    """White pawn on e7 captures on d8, generating q/r/b/n."""
    board = _setup_promotion_board(
        1, 0, 0, 7, 1, 4, Color.WHITE,
        extra_pieces=[(0, 3, Color.BLACK, PieceType.KNIGHT)],  # black knight on d8
    )
    assert promotions_for(board, "e7", "d8") == {
        PieceType.QUEEN,
        PieceType.ROOK,
        PieceType.BISHOP,
        PieceType.KNIGHT,
    }


# ── 2.4 Black quiet promotion generation ─────────────────────────────────────

def test_black_quiet_promotion_all_four() -> None:
    """Black pawn on e2 → e1 (empty) must generate q/r/b/n."""
    board = _setup_promotion_board(
        7, 0, 6, 7, 6, 4, Color.BLACK,
    )
    assert promotions_for(board, "e2", "e1") == {
        PieceType.QUEEN,
        PieceType.ROOK,
        PieceType.BISHOP,
        PieceType.KNIGHT,
    }


# ── 2.5 Black capture promotion generation ───────────────────────────────────

def test_black_capture_promotion_all_four() -> None:
    """Black pawn on e2 captures on d1, generating q/r/b/n."""
    board = _setup_promotion_board(
        7, 0, 6, 7, 6, 4, Color.BLACK,
        extra_pieces=[(7, 3, Color.WHITE, PieceType.KNIGHT)],  # white knight on d1
    )
    assert promotions_for(board, "e2", "d1") == {
        PieceType.QUEEN,
        PieceType.ROOK,
        PieceType.BISHOP,
        PieceType.KNIGHT,
    }


# ── 2.6 No duplicate identical promotion moves ──────────────────────────────

def test_no_duplicate_promotion_moves() -> None:
    """Legal promotion moves must not contain duplicate (start, end, promotion)."""
    board = _setup_promotion_board(
        1, 0, 0, 7, 1, 4, Color.WHITE,
        extra_pieces=[
            (0, 3, Color.BLACK, PieceType.KNIGHT),  # d8
            (0, 5, Color.BLACK, PieceType.BISHOP),  # f8
        ],
    )
    moves = board.get_legal_moves()
    move_set = set(moves)
    assert len(moves) == len(move_set), "Duplicate promotion moves found"
