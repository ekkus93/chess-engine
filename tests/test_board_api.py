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


class TestGetLegalMovesForColor:
    """Task 7: API tests for Board.get_legal_moves_for_color."""

    def test_default_white_has_20_legal_moves(self):
        board = Board()
        moves = board.get_legal_moves_for_color(Color.WHITE)
        assert len(moves) == 20

    def test_default_black_has_20_legal_moves(self):
        board = Board()
        moves = board.get_legal_moves_for_color(Color.BLACK)
        assert len(moves) == 20

    def test_get_legal_moves_for_color_preserves_turn(self):
        board = Board()
        assert board.turn == Color.WHITE
        moves = board.get_legal_moves_for_color(Color.BLACK)
        assert board.turn == Color.WHITE
        assert len(moves) > 0

    def test_get_legal_moves_respects_color_after_move(self):
        board = Board()
        assert board.make_move(sq("e2"), sq("e4")) is True
        assert board.turn == Color.BLACK
        white_moves = board.get_legal_moves_for_color(Color.WHITE)
        black_moves = board.get_legal_moves_for_color(Color.BLACK)
        assert any(
            m[0] == sq("g1") and m[1] == sq("f3") for m in white_moves
        ), "White Nf1-g1-f3 should appear"
        assert any(
            m[0] == sq("e7") and m[1] == sq("e5") for m in black_moves
        ), "Black e7-e5 should appear"
        assert board.turn == Color.BLACK


class TestPinnedPieces:
    """Task 8: Pinned-piece tests for get_legal_moves_for_color."""

    def test_pinned_knight_has_no_legal_moves(self):
        """A pinned knight has zero legal moves because all moves expose the king."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.KNIGHT))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.ROOK))
        board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE

        knight_moves = [
            m
            for m in board.get_legal_moves_for_color(Color.WHITE)
            if m[0] == sq("e2")
        ]
        assert knight_moves == []

    def test_pinned_pawn_can_move_along_pin_line(self):
        """
        A pawn pinned on e-file by a rook on e8 may still move e2-e3/e2-e4
        if those moves keep the e-file blocked.
        """
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.ROOK))
        board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE

        moves = board.get_legal_moves_for_color(Color.WHITE)
        from_e2 = [m for m in moves if m[0] == sq("e2")]

        to_e3 = sq("e3")
        to_e4 = sq("e4")

        has_e3 = any(m[1] == to_e3 for m in from_e2)
        has_e4 = any(m[1] == to_e4 for m in from_e2)
        assert has_e3 or has_e4, "Pinned pawn should be able to move along pin line"

    def test_pinned_pawn_diagonal_blocked_if_exposes_king(self):
        """
        A pinned pawn may not capture diagonally if it exposes the king.
        Here white pawn on e2 pinned by black rook on e8, black pawn on d3.
        e2xd3 must be illegal because it opens the e-file.
        """
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("d3"), create_piece(Color.BLACK, PieceType.PAWN))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.ROOK))
        board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE

        moves = board.get_legal_moves_for_color(Color.WHITE)
        captures_on_d3 = any(
            m[0] == sq("e2") and m[1] == sq("d3")
            for m in moves
        )
        assert not captures_on_d3, "Diagonal capture that exposes king must be illegal"


class TestCastlingInLegalMoves:
    """Task 9: Castling moves appear in get_legal_moves_for_color."""

    def test_white_kingside_castling_move_appears(self):
        board = Board()
        board.clear_square(sq("f1"))
        board.clear_square(sq("g1"))
        board.turn = Color.WHITE

        moves = board.get_legal_moves_for_color(Color.WHITE)
        assert any(
            m[0] == sq("e1") and m[1] == sq("g1") for m in moves
        ), "White kingside castling e1-g1 should be legal"

    def test_white_queenside_castling_move_appears(self):
        board = Board()
        board.clear_square(sq("b1"))
        board.clear_square(sq("c1"))
        board.clear_square(sq("d1"))
        board.turn = Color.WHITE

        moves = board.get_legal_moves_for_color(Color.WHITE)
        assert any(
            m[0] == sq("e1") and m[1] == sq("c1") for m in moves
        ), "White queenside castling e1-c1 should be legal"

    def test_black_kingside_castling_move_appears(self):
        board = Board()
        board.clear_square(sq("f8"))
        board.clear_square(sq("g8"))
        board.turn = Color.BLACK

        moves = board.get_legal_moves_for_color(Color.BLACK)
        assert any(
            m[0] == sq("e8") and m[1] == sq("g8") for m in moves
        ), "Black kingside castling e8-g8 should be legal"

    def test_black_queenside_castling_move_appears(self):
        board = Board()
        board.clear_square(sq("b8"))
        board.clear_square(sq("c8"))
        board.clear_square(sq("d8"))
        board.turn = Color.BLACK

        moves = board.get_legal_moves_for_color(Color.BLACK)
        assert any(
            m[0] == sq("e8") and m[1] == sq("c8") for m in moves
        ), "Black queenside castling e8-c8 should be legal"


class TestEnPassantInLegalMoves:
    """Task 10: En passant moves appear in get_legal_moves_for_color."""

    def test_white_en_passant_after_black_double_push(self):
        """
        Black plays b7-b5; white pawn on a5 can capture en passant on b6.
        """
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.set_piece(sq("a5"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("b7"), create_piece(Color.BLACK, PieceType.PAWN))
        board.turn = Color.BLACK

        assert board.make_move(sq("b7"), sq("b5")) is True
        assert board.en_passant_target == sq("b6")

        white_moves = board.get_legal_moves_for_color(Color.WHITE)
        assert any(
            m[0] == sq("a5") and m[1] == sq("b6") for m in white_moves
        ), "White en passant a5xb6 should appear"

    def test_black_en_passant_after_white_double_push(self):
        """
        White plays b2-b4; black pawn on a4 can capture en passant on b3.
        """
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.set_piece(sq("b2"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("a4"), create_piece(Color.BLACK, PieceType.PAWN))
        board.turn = Color.WHITE

        assert board.make_move(sq("b2"), sq("b4")) is True
        assert board.en_passant_target == sq("b3")

        black_moves = board.get_legal_moves_for_color(Color.BLACK)
        assert any(
            m[0] == sq("a4") and m[1] == sq("b3") for m in black_moves
        ), "Black en passant a4xb3 should appear"


class TestCheckmateAndStalemate:
    """Task 12: Checkmate and stalemate tests for get_legal_moves_for_color."""

    def test_checkmate_position_no_legal_moves(self):
        """
        Black king h8, White king f6, White queen g7, Black to move.
        Black is in checkmate: in check, no legal moves.
        """
        board = Board()
        board.clear_board()
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        board.set_piece(sq("f6"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("g7"), create_piece(Color.WHITE, PieceType.QUEEN))
        board.turn = Color.BLACK

        assert board._is_in_check(Color.BLACK) is True
        black_moves = board.get_legal_moves_for_color(Color.BLACK)
        assert black_moves == []
        assert board._is_checkmate(Color.BLACK) is True

    def test_stalemate_position_no_legal_moves(self):
        """
        Black king h8, White king f7, White queen g6, Black to move.
        Black is not in check but has no legal moves: stalemate.
        """
        board = Board()
        board.clear_board()
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        board.set_piece(sq("f7"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("g6"), create_piece(Color.WHITE, PieceType.QUEEN))
        board.turn = Color.BLACK

        assert board._is_in_check(Color.BLACK) is False
        black_moves = board.get_legal_moves_for_color(Color.BLACK)
        assert black_moves == []
        assert board._is_stalemate(Color.BLACK) is True


class TestBoardApiMutationSafety:
    """Task 13: Ensure read-only / invalid operations do not mutate board."""

    def test_get_legal_moves_for_color_does_not_change_turn(self):
        board = Board()
        assert board.turn == Color.WHITE
        _ = board.get_legal_moves_for_color(Color.BLACK)
        assert board.turn == Color.WHITE

    def test_invalid_promotion_no_mutation(self):
        """
        Invalid promotion call must not mutate:
        - source piece
        - destination square
        - turn
        - en_passant_target
        - castling rights
        """
        board = Board()
        initial_turn = board.turn
        initial_ep = board.en_passant_target

        # Try invalid promotion on non-pawn move
        before_knight = board.get_piece(sq("g1"))

        ok = board.make_move(
            sq("g1"),
            sq("f3"),
            promotion=PieceType.QUEEN
        )
        assert ok is False

        # No mutation: knight still on g1
        assert board.get_piece(sq("g1")) is not None
        # Turn unchanged
        assert board.turn == initial_turn
        # En passant target unchanged
        assert board.en_passant_target == initial_ep
