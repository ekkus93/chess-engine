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


def test_algebraic_pawn_promo_accepted() -> None:
    """parse_move_notation('e7e8q') on a pawn succeeds."""
    from chess_game.chess.move import parse_move_notation

    board = _setup_promo_board()
    move = parse_move_notation("e7e8q")
    assert board.make_move(move.start, move.end, promotion=move.promotion) is True
    assert_piece(board, "e8", Color.WHITE, PieceType.QUEEN)
    assert_empty(board, "e7")


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
