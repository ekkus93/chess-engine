"""Promotion regression tests — Task 10.4

Covers:
  - White promotes on rank 8 (row 0) to Q/R/B/N
  - Black promotes on rank 1 (row 7) to Q/R/B/N
  - Illegal promotion pieces rejected
  - Default queen promotion when promotion=None
  - Pawn cannot promote from wrong rank
  - Promotion via capture
"""

from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.color import Color
from chess_game.chess.types import PieceType
from tests.helpers import sq


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


# ── White promotion to each piece type ──────────────────────────────────────

def test_white_promote_to_queen() -> None:
    """White pawn on rank 7 (row 1) promotes to queen on rank 8 (row 0)."""
    board = _setup_promotion_board(
        white_king_row=1,
        white_king_col=0,
        black_king_row=0,
        black_king_col=7,
        pawn_row=1,
        pawn_col=4,
        pawn_color=Color.WHITE,
    )
    assert (
        board.make_move(
            sq("e7"),
            sq("e8"),
            promotion=PieceType.QUEEN,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e8")) == PieceType.QUEEN
    assert board.get_color_at(sq("e8")) == Color.WHITE
    assert board.get_piece(sq("e7")) is None


def test_white_promote_to_rook() -> None:
    board = _setup_promotion_board(
        1, 0, 0, 7, 1, 4, Color.WHITE,
    )
    assert (
        board.make_move(
            sq("e7"),
            sq("e8"),
            promotion=PieceType.ROOK,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e8")) == PieceType.ROOK
    assert board.get_color_at(sq("e8")) == Color.WHITE


def test_white_promote_to_bishop() -> None:
    board = _setup_promotion_board(
        1, 0, 0, 7, 1, 4, Color.WHITE,
    )
    assert (
        board.make_move(
            sq("e7"),
            sq("e8"),
            promotion=PieceType.BISHOP,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e8")) == PieceType.BISHOP
    assert board.get_color_at(sq("e8")) == Color.WHITE


def test_white_promote_to_knight() -> None:
    board = _setup_promotion_board(
        1, 0, 0, 7, 1, 4, Color.WHITE,
    )
    assert (
        board.make_move(
            sq("e7"),
            sq("e8"),
            promotion=PieceType.KNIGHT,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e8")) == PieceType.KNIGHT
    assert board.get_color_at(sq("e8")) == Color.WHITE


# ── Black promotion to each piece type ──────────────────────────────────────

def test_black_promote_to_queen() -> None:
    """Black pawn on rank 2 (row 6) promotes to queen on rank 1 (row 7)."""
    board = _setup_promotion_board(
        white_king_row=7,
        white_king_col=0,
        black_king_row=6,
        black_king_col=7,
        pawn_row=6,
        pawn_col=4,
        pawn_color=Color.BLACK,
    )
    assert (
        board.make_move(
            sq("e2"),
            sq("e1"),
            promotion=PieceType.QUEEN,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e1")) == PieceType.QUEEN
    assert board.get_color_at(sq("e1")) == Color.BLACK
    assert board.get_piece(sq("e2")) is None


def test_black_promote_to_rook() -> None:
    board = _setup_promotion_board(
        7, 0, 6, 7, 6, 4, Color.BLACK,
    )
    assert (
        board.make_move(
            sq("e2"),
            sq("e1"),
            promotion=PieceType.ROOK,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e1")) == PieceType.ROOK
    assert board.get_color_at(sq("e1")) == Color.BLACK


def test_black_promote_to_bishop() -> None:
    board = _setup_promotion_board(
        7, 0, 6, 7, 6, 4, Color.BLACK,
    )
    assert (
        board.make_move(
            sq("e2"),
            sq("e1"),
            promotion=PieceType.BISHOP,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e1")) == PieceType.BISHOP
    assert board.get_color_at(sq("e1")) == Color.BLACK


def test_black_promote_to_knight() -> None:
    board = _setup_promotion_board(
        7, 0, 6, 7, 6, 4, Color.BLACK,
    )
    assert (
        board.make_move(
            sq("e2"),
            sq("e1"),
            promotion=PieceType.KNIGHT,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e1")) == PieceType.KNIGHT
    assert board.get_color_at(sq("e1")) == Color.BLACK


# ── Illegal promotion pieces ────────────────────────────────────────────────

def test_promotion_to_king_rejected() -> None:
    board = _setup_promotion_board(
        1, 0, 0, 7, 1, 4, Color.WHITE,
    )
    assert (
        board.make_move(
            sq("e7"),
            sq("e8"),
            promotion=PieceType.KING,
        )
        is False
    )


def test_promotion_to_pawn_rejected() -> None:
    board = _setup_promotion_board(
        1, 0, 0, 7, 1, 4, Color.WHITE,
    )
    assert (
        board.make_move(
            sq("e7"),
            sq("e8"),
            promotion=PieceType.PAWN,
        )
        is False
    )


# ── Default queen promotion ─────────────────────────────────────────────────

def test_default_queen_promotion_white() -> None:
    """When promotion=None, white pawn defaults to queen."""
    board = _setup_promotion_board(
        1, 0, 0, 7, 1, 4, Color.WHITE,
    )
    assert (
        board.make_move(
            sq("e7"),
            sq("e8"),
            promotion=None,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e8")) == PieceType.QUEEN


def test_default_queen_promotion_black() -> None:
    """When promotion=None, black pawn defaults to queen."""
    board = _setup_promotion_board(
        7, 0, 6, 7, 6, 4, Color.BLACK,
    )
    assert (
        board.make_move(
            sq("e2"),
            sq("e1"),
            promotion=None,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e1")) == PieceType.QUEEN


# ── Pawn cannot promote from wrong rank ─────────────────────────────────────

def test_pawn_cannot_promote_from_middle_rank() -> None:
    """A white pawn on rank 4 (row 3) cannot promote by jumping to rank 8."""
    board = _setup_promotion_board(
        1, 0, 0, 7, 3, 4, Color.WHITE,
    )
    assert (
        board.make_move(
            sq("e5"),
            sq("e8"),
            promotion=PieceType.QUEEN,
        )
        is False
    )


def test_black_pawn_cannot_promote_from_middle_rank() -> None:
    """A black pawn on rank 5 (row 4) cannot promote by jumping to rank 1."""
    board = _setup_promotion_board(
        7, 0, 6, 7, 4, 4, Color.BLACK,
    )
    assert (
        board.make_move(
            sq("e4"),
            sq("e1"),
            promotion=PieceType.QUEEN,
        )
        is False
    )


# ── Promotion via capture ───────────────────────────────────────────────────

def test_white_promotion_via_capture() -> None:
    """White pawn captures on promotion square."""
    board = _setup_promotion_board(
        1, 0, 0, 7, 1, 3,  # white pawn on d7 (row 1, col 3)
        Color.WHITE,
        extra_pieces=[(0, 4, Color.BLACK, PieceType.KNIGHT)],  # black knight on e8
    )
    assert (
        board.make_move(
            sq("d7"),
            sq("e8"),
            promotion=PieceType.QUEEN,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e8")) == PieceType.QUEEN
    assert board.get_color_at(sq("e8")) == Color.WHITE
    assert board.get_piece(sq("d7")) is None


def test_black_promotion_via_capture() -> None:
    """Black pawn captures on promotion square."""
    board = _setup_promotion_board(
        7, 0, 6, 7, 6, 3,  # black pawn on d2 (row 6, col 3)
        Color.BLACK,
        extra_pieces=[(7, 4, Color.WHITE, PieceType.KNIGHT)],  # white knight on e1
    )
    assert (
        board.make_move(
            sq("d2"),
            sq("e1"),
            promotion=PieceType.QUEEN,
        )
        is True
    )
    assert board.get_piece_type_at(sq("e1")) == PieceType.QUEEN
    assert board.get_color_at(sq("e1")) == Color.BLACK
    assert board.get_piece(sq("d2")) is None
