"""Board API tests (Task 1–6 of BIG_FIX1_TODO)."""

from chess_game.chess.board import Board, create_piece, ConstantSquare
from chess_game.chess.constants import RowConstant, ColConstant
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


class TestIsValidPosition:
    """Task 2: API tests for Board.is_valid_position."""

    def test_is_valid_position_corners(self):
        board = Board()
        for name in ("a1", "a8", "h1", "h8"):
            assert board.is_valid_position(sq(name)) is True

    def test_is_valid_position_center(self):
        board = Board()
        for name in ("e4", "d5"):
            assert board.is_valid_position(sq(name)) is True

    def test_is_valid_position_column_out_of_bounds(self):
        board = Board()
        bad_left = ConstantSquare(row=RowConstant(0), col=ColConstant(-1))
        bad_right = ConstantSquare(row=RowConstant(0), col=ColConstant(8))
        assert board.is_valid_position(bad_left) is False
        assert board.is_valid_position(bad_right) is False

    def test_is_valid_position_row_out_of_bounds(self):
        board = Board()
        bad_up = ConstantSquare(row=RowConstant(-1), col=ColConstant(0))
        bad_down = ConstantSquare(row=RowConstant(8), col=ColConstant(0))
        assert board.is_valid_position(bad_up) is False
        assert board.is_valid_position(bad_down) is False

    def test_is_valid_position_both_negative(self):
        board = Board()
        bad = ConstantSquare(row=RowConstant(-1), col=ColConstant(-1))
        assert board.is_valid_position(bad) is False


class TestIsSameColor:
    """Task 3: API tests for Board.is_same_color."""

    def test_is_same_color_two_white_pieces(self):
        board = Board()
        assert board.is_same_color(sq("a1"), sq("e1")) is True

    def test_is_same_color_two_black_pieces(self):
        board = Board()
        assert board.is_same_color(sq("a8"), sq("e8")) is True

    def test_is_same_color_white_vs_black(self):
        board = Board()
        assert board.is_same_color(sq("a1"), sq("a8")) is False

    def test_is_same_color_same_square(self):
        board = Board()
        assert board.is_same_color(sq("e1"), sq("e1")) is True

    def test_is_same_color_one_occupied_one_empty(self):
        board = Board()
        assert board.is_same_color(sq("e1"), sq("e4")) is False

    def test_is_same_color_both_empty(self):
        board = Board()
        assert board.is_same_color(sq("e4"), sq("d4")) is False


class TestIsOpponent:
    """Task 4: API tests for Board.is_opponent."""

    def test_is_opponent_white_vs_black(self):
        board = Board()
        assert board.is_opponent(sq("a1"), sq("a8")) is True

    def test_is_opponent_black_vs_white(self):
        board = Board()
        assert board.is_opponent(sq("a8"), sq("a1")) is True

    def test_is_opponent_two_white(self):
        board = Board()
        assert board.is_opponent(sq("a1"), sq("e1")) is False

    def test_is_opponent_two_black(self):
        board = Board()
        assert board.is_opponent(sq("a8"), sq("e8")) is False

    def test_is_opponent_one_occupied_one_empty(self):
        board = Board()
        assert board.is_opponent(sq("a1"), sq("e4")) is False

    def test_is_opponent_both_empty(self):
        board = Board()
        assert board.is_opponent(sq("e4"), sq("d4")) is False

    def test_is_opponent_same_square(self):
        board = Board()
        assert board.is_opponent(sq("a1"), sq("a1")) is False


class TestIsEmpty:
    """Task 5: API tests for Board.is_empty."""

    def test_is_empty_default_board_empty_squares(self):
        board = Board()
        for name in ("e3", "e4", "e5", "e6"):
            assert board.is_empty(sq(name)) is True

    def test_is_empty_occupied_squares(self):
        board = Board()
        for name in ("e1", "e8", "e2", "e7"):
            assert board.is_empty(sq(name)) is False

    def test_is_empty_after_clear_square(self):
        board = Board()
        board.clear_square(sq("e2"))
        assert board.is_empty(sq("e2")) is True

    def test_is_empty_after_set_piece(self):
        board = Board()
        board.clear_square(sq("e4"))
        board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.KNIGHT))
        assert board.is_empty(sq("e4")) is False

    def test_is_empty_occupied_corners(self):
        board = Board()
        for name in ("a1", "h1", "a8", "h8"):
            assert board.is_empty(sq(name)) is False


class TestFindKing:
    """Task 6: API tests for Board.find_king."""

    def test_find_king_default_board_white(self):
        board = Board()
        assert board.find_king(Color.WHITE) == sq("e1")

    def test_find_king_default_board_black(self):
        board = Board()
        assert board.find_king(Color.BLACK) == sq("e8")

    def test_find_king_after_king_move(self):
        board = Board()
        board.clear_square(sq("f1"))
        assert board.make_move(sq("e1"), sq("f1")) is True
        assert board.find_king(Color.WHITE) == sq("f1")

    def test_find_king_after_king_removed(self):
        board = Board()
        board.clear_square(sq("e1"))
        assert board.find_king(Color.WHITE) is None

    def test_find_king_custom_positions(self):
        board = Board()
        board.clear_board()
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        assert board.find_king(Color.WHITE) == sq("a1")
        assert board.find_king(Color.BLACK) == sq("h8")

    def test_find_king_cloned_board_preserves_positions(self):
        board = Board()
        board.clear_square(sq("f1"))
        assert board.make_move(sq("e1"), sq("f1")) is True
        cloned = board.clone()
        assert cloned.find_king(Color.WHITE) == sq("f1")
        assert cloned.find_king(Color.BLACK) == sq("e8")
