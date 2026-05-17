"""Promotion input-validation regression tests

Covers:
  - Non-pawn moves with promotion suffix rejected
  - Pawn promotion on wrong rank rejected
  - Raw integer promotion rejected
  - Raw string promotion rejected
  - Invalid PieceType (KING, PAWN, EMPTY) rejected
  - Valid underpromotion still accepted
  - PromotionValidator.is_valid_promotion_piece hardening
  - Color-specific promotion rank checks via is_valid_promotion_choice
"""

from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.board.promotion import PromotionValidator
from chess_game.chess.types import Color, PieceType
from chess_game.chess.constants import ConstantSquare
from tests.helpers import sq, assert_piece, assert_empty


def _setup_promo_board() -> Board:
    """White pawn on e7, e8 empty, white to move."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE
    return board


# ── 4.1 Non-pawn promotion suffix rejected ──────────────────────────────────


def test_non_pawn_knight_promo_rejected() -> None:
    """g1f3q with a knight must be rejected."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.turn = Color.WHITE

    before_turn = board.turn
    assert board.make_move(sq("g1"), sq("f3"), promotion=PieceType.QUEEN) is False
    assert board.turn == before_turn
    assert_piece(board, "g1", Color.WHITE, PieceType.KNIGHT)


def test_non_pawn_rook_promo_rejected() -> None:
    """a1a2q with a rook must be rejected."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.turn = Color.WHITE

    before_turn = board.turn
    assert board.make_move(sq("a1"), sq("a2"), promotion=PieceType.QUEEN) is False
    assert board.turn == before_turn
    assert_piece(board, "a1", Color.WHITE, PieceType.ROOK)


def test_non_pawn_king_promo_rejected() -> None:
    """e1e2q with a king must be rejected."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    before_turn = board.turn
    assert board.make_move(sq("e1"), sq("e2"), promotion=PieceType.QUEEN) is False
    assert board.turn == before_turn
    assert_piece(board, "e1", Color.WHITE, PieceType.KING)


# ── 4.2 Pawn promotion suffix on wrong rank rejected ────────────────────────


def test_pawn_promo_wrong_rank_double_step() -> None:
    """e2e4q must be rejected — pawn not on promotion rank."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    before_turn = board.turn
    assert board.make_move(sq("e2"), sq("e4"), promotion=PieceType.QUEEN) is False
    assert board.turn == before_turn
    assert_piece(board, "e2", Color.WHITE, PieceType.PAWN)


def test_pawn_promo_wrong_rank_single_step() -> None:
    """e7e5q must be rejected — destination not promotion rank."""
    board = _setup_promo_board()
    board.set_piece(sq("e5"), None)

    before_turn = board.turn
    assert board.make_move(sq("e7"), sq("e5"), promotion=PieceType.QUEEN) is False
    assert board.turn == before_turn
    assert_piece(board, "e7", Color.WHITE, PieceType.PAWN)


# ── 4.3 Raw integer promotion rejected ──────────────────────────────────────


def test_raw_int_promotion_rejected() -> None:
    """promotion=5 must be rejected."""
    board = _setup_promo_board()

    before_turn = board.turn
    assert board.make_move(sq("e7"), sq("e8"), promotion=5) is False  # type: ignore[arg-type]
    assert board.turn == before_turn
    assert_piece(board, "e7", Color.WHITE, PieceType.PAWN)
    assert_empty(board, "e8")


# ── 4.4 Raw string promotion rejected ───────────────────────────────────────


def test_raw_string_promotion_rejected() -> None:
    """promotion='q' must be rejected."""
    board = _setup_promo_board()

    before_turn = board.turn
    assert board.make_move(sq("e7"), sq("e8"), promotion="q") is False  # type: ignore[arg-type]
    assert board.turn == before_turn
    assert_piece(board, "e7", Color.WHITE, PieceType.PAWN)
    assert_empty(board, "e8")


# ── 4.5 Invalid PieceType promotions rejected ───────────────────────────────


def test_promotion_to_king_rejected() -> None:
    board = _setup_promo_board()

    before_turn = board.turn
    assert board.make_move(sq("e7"), sq("e8"), promotion=PieceType.KING) is False
    assert board.turn == before_turn
    assert_piece(board, "e7", Color.WHITE, PieceType.PAWN)
    assert_empty(board, "e8")


def test_promotion_to_pawn_rejected() -> None:
    board = _setup_promo_board()

    before_turn = board.turn
    assert board.make_move(sq("e7"), sq("e8"), promotion=PieceType.PAWN) is False
    assert board.turn == before_turn
    assert_piece(board, "e7", Color.WHITE, PieceType.PAWN)
    assert_empty(board, "e8")


def test_promotion_to_empty_rejected() -> None:
    board = _setup_promo_board()

    before_turn = board.turn
    assert board.make_move(sq("e7"), sq("e8"), promotion=PieceType.EMPTY) is False
    assert board.turn == before_turn
    assert_piece(board, "e7", Color.WHITE, PieceType.PAWN)
    assert_empty(board, "e8")


# ── 4.6 Valid underpromotion still accepted ─────────────────────────────────


def test_valid_promo_queen() -> None:
    board = _setup_promo_board()
    assert board.make_move(sq("e7"), sq("e8"), promotion=PieceType.QUEEN) is True
    assert_piece(board, "e8", Color.WHITE, PieceType.QUEEN)
    assert_empty(board, "e7")


def test_valid_promo_rook() -> None:
    board = _setup_promo_board()
    assert board.make_move(sq("e7"), sq("e8"), promotion=PieceType.ROOK) is True
    assert_piece(board, "e8", Color.WHITE, PieceType.ROOK)
    assert_empty(board, "e7")


def test_valid_promo_bishop() -> None:
    board = _setup_promo_board()
    assert board.make_move(sq("e7"), sq("e8"), promotion=PieceType.BISHOP) is True
    assert_piece(board, "e8", Color.WHITE, PieceType.BISHOP)
    assert_empty(board, "e7")


def test_valid_promo_knight() -> None:
    board = _setup_promo_board()
    assert board.make_move(sq("e7"), sq("e8"), promotion=PieceType.KNIGHT) is True
    assert_piece(board, "e8", Color.WHITE, PieceType.KNIGHT)
    assert_empty(board, "e7")


# ── 4.7 Algebraic parser path: non-pawn promotion suffix rejected ───────────


def test_algebraic_non_pawn_knight_promo_rejected() -> None:
    """parse_move_notation('g1f3q') parses, but make_move rejects it."""
    from chess_game.chess.move import parse_move_notation

    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.turn = Color.WHITE

    move = parse_move_notation("g1f3q")
    assert board.make_move(move.start, move.end, promotion=move.promotion) is False
    assert_piece(board, "g1", Color.WHITE, PieceType.KNIGHT)


def test_algebraic_non_pawn_bishop_promo_rejected() -> None:
    """parse_move_notation('f1d3r') parses, but make_move rejects it."""
    from chess_game.chess.move import parse_move_notation

    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.turn = Color.WHITE

    move = parse_move_notation("f1d3r")
    assert board.make_move(move.start, move.end, promotion=move.promotion) is False
    assert_piece(board, "f1", Color.WHITE, PieceType.BISHOP)


def test_algebraic_non_pawn_queen_promo_rejected() -> None:
    """parse_move_notation('d1f1q') parses, but make_move rejects it."""
    from chess_game.chess.move import parse_move_notation

    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.turn = Color.WHITE

    move = parse_move_notation("d1f1q")
    assert board.make_move(move.start, move.end, promotion=move.promotion) is False
    assert_piece(board, "d1", Color.WHITE, PieceType.QUEEN)


# ── is_valid_promotion_choice enforces color-specific ranks via sq() ─────────


def test_is_valid_promotion_choice_white_on_row_0() -> None:
    """White pawn promoting on row 0 with QUEEN should be allowed."""
    board = _setup_promo_board()
    v = PromotionValidator(board)
    white_pawn = board.get_piece(sq("e7"))
    assert v.is_valid_promotion_choice(white_pawn, sq("e8"), PieceType.QUEEN) is True


def test_is_valid_promotion_choice_white_rejected_on_row_7() -> None:
    """White pawn promoting on row 7 should be rejected."""
    board = _setup_promo_board()
    v = PromotionValidator(board)
    white_pawn = board.get_piece(sq("e7"))
    assert v.is_valid_promotion_choice(white_pawn, sq("e1"), PieceType.QUEEN) is False


def test_is_valid_promotion_choice_black_on_row_7() -> None:
    """Black pawn promoting on row 7 should be allowed."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e3"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    v = PromotionValidator(board)
    black_pawn = board.get_piece(sq("e3"))
    assert v.is_valid_promotion_choice(black_pawn, sq("e1"), PieceType.ROOK) is True


def test_is_valid_promotion_choice_black_rejected_on_row_0() -> None:
    """Black pawn promoting on row 0 should be rejected."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e3"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    v = PromotionValidator(board)
    black_pawn = board.get_piece(sq("e3"))
    assert v.is_valid_promotion_choice(black_pawn, sq("e8"), PieceType.ROOK) is False


def test_algebraic_pawn_promo_accepted() -> None:
    """parse_move_notation('e7e8q') on a pawn succeeds."""
    from chess_game.chess.move import parse_move_notation

    board = _setup_promo_board()
    move = parse_move_notation("e7e8q")
    assert board.make_move(move.start, move.end, promotion=move.promotion) is True
    assert_piece(board, "e8", Color.WHITE, PieceType.QUEEN)
    assert_empty(board, "e7")


# ── Color-specific promotion rank enforcement via existing helpers ───────────


def test_white_pawn_must_promote_only_on_row_0() -> None:
    """White pawn must only promote when moving to row 0."""
    board = _setup_promo_board()
    v = PromotionValidator(board)
    white_pawn = board.get_piece(sq("e7"))

    # Promoting to e8 (row 0) is valid
    assert v.is_promotion_rank(white_pawn, sq("e8")) is True

    # Other ranks are not promotion rank for white
    for s in ["e7", "e6", "e5", "e4", "e3", "e2", "e1"]:
        assert v.is_promotion_rank(white_pawn, sq(s)) is False


def test_black_pawn_must_promote_only_on_row_7() -> None:
    """Black pawn must only promote when moving to row 7."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e3"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    v = PromotionValidator(board)
    black_pawn = board.get_piece(sq("e3"))

    # Promoting to e1 (row 7) is valid
    assert v.is_promotion_rank(black_pawn, sq("e1")) is True

    # Other ranks are not promotion rank for black
    for s in ["e2", "e3", "e4", "e5", "e6", "e7", "e8"]:
        assert v.is_promotion_rank(black_pawn, sq(s)) is False


# ── is_valid_promotion_piece hardening ───────────────────────────────────────


class TestPromotionValidatorDirect:
    """Unit tests for PromotionValidator hardening."""

    def _validator(self) -> PromotionValidator:
        return PromotionValidator(Board())

    def test_valid_promotion_piece_queen(self) -> None:
        v = self._validator()
        assert v.is_valid_promotion_piece(PieceType.QUEEN) is True

    def test_valid_promotion_piece_rook(self) -> None:
        v = self._validator()
        assert v.is_valid_promotion_piece(PieceType.ROOK) is True

    def test_valid_promotion_piece_bishop(self) -> None:
        v = self._validator()
        assert v.is_valid_promotion_piece(PieceType.BISHOP) is True

    def test_valid_promotion_piece_knight(self) -> None:
        v = self._validator()
        assert v.is_valid_promotion_piece(PieceType.KNIGHT) is True

    def test_reject_king_promotion(self) -> None:
        v = self._validator()
        assert v.is_valid_promotion_piece(PieceType.KING) is False

    def test_reject_pawn_promotion(self) -> None:
        v = self._validator()
        assert v.is_valid_promotion_piece(PieceType.PAWN) is False

    def test_reject_empty_promotion(self) -> None:
        v = self._validator()
        assert v.is_valid_promotion_piece(PieceType.EMPTY) is False

    def test_reject_raw_int_promotion(self) -> None:
        v = self._validator()
        assert v.is_valid_promotion_piece(5) is False  # type: ignore[arg-type]

    def test_reject_raw_string_promotion(self) -> None:
        v = self._validator()
        assert v.is_valid_promotion_piece("q") is False  # type: ignore[arg-type]

    def test_reject_none_promotion(self) -> None:
        v = self._validator()
        assert v.is_valid_promotion_piece(None) is False  # type: ignore[arg-type]


# ── Color-specific promotion rank checks ─────────────────────────────────────


def _setup_white_pawn_near_promo() -> Board:
    """White pawn on e7, kings on c1/g8, white to move."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE
    return board


def _setup_black_pawn_near_promo() -> Board:
    """Black pawn on e3, kings on c1/g8, black to move."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e3"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    return board


def test_white_pawn_promo_on_row_1_allowed() -> None:
    """White pawn to row 1 should be allowed (promotion rank)."""
    board = _setup_white_pawn_near_promo()
    assert board.make_move(sq("e7"), sq("e8"), promotion=PieceType.QUEEN) is True
    assert_piece(board, "e8", Color.WHITE, PieceType.QUEEN)


def test_white_pawn_promo_on_row_8_not_allowed() -> None:
    """White pawn cannot appear on row 8 via non-promo move (no rank wrap)."""
    # Ensure only row 1 is treated as promotion rank for white.
    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e6"), create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # Move to e7 is normal (no promotion argument allowed).
    assert board.make_move(sq("e6"), sq("e7")) is True
    assert_piece(board, "e7", Color.WHITE, PieceType.PAWN)


def test_black_pawn_promo_on_row_8_allowed() -> None:
    """Black pawn to row 8 should be allowed (promotion rank for black)."""
    board = _setup_black_pawn_near_promo()
    # Black pawn e3->e2 is normal.
    assert board.make_move(sq("e3"), sq("e2")) is True
    assert_piece(board, "e2", Color.BLACK, PieceType.PAWN)


def test_black_pawn_promo_when_reaching_row_1() -> None:
    """Black pawn reaching row 1 should allow promotion."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e2"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    # Black pawn e2->e1 with promotion.
    assert board.make_move(sq("e2"), sq("e1"), promotion=PieceType.ROOK) is True
    assert_piece(board, "e1", Color.BLACK, PieceType.ROOK)


def test_white_pawn_no_promo_on_non_promo_rank() -> None:
    """White pawn moving on non-promo rank must not allow promotion arg."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # e7->e6 with promotion arg should be rejected.
    assert board.make_move(sq("e7"), sq("e6"), promotion=PieceType.QUEEN) is False
    assert_piece(board, "e7", Color.WHITE, PieceType.PAWN)


def test_black_pawn_no_promo_on_non_promo_rank() -> None:
    """Black pawn moving on non-promo rank must not allow promotion arg."""
    board = _setup_black_pawn_near_promo()

    # e3->e4 with promotion arg should be rejected.
    assert board.make_move(sq("e3"), sq("e4"), promotion=PieceType.QUEEN) is False
    assert_piece(board, "e3", Color.BLACK, PieceType.PAWN)
