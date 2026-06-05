"""Unit tests for chess_game.chess.strategy_utils."""

from __future__ import annotations

from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.evaluation_tables import MATERIAL_VALUES
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    both_queens_on_board,
    center_distance,
    file_pawn_state,
    is_advanced_passer,
    is_capture_move,
    is_castled_king,
    is_passed_pawn,
    iter_board_pieces,
    iter_color_pieces,
    king_coordinates,
    legal_move_count,
    materially_ahead_color,
    materially_behind_color,
    non_king_material_lead,
    opposite_color,
    passed_pawns_for_color,
    path_clear_between,
    pawn_path_to_promotion_is_clear,
    pawn_supports_square,
    scale_signed,
    total_non_pawn_material,
)
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


# ---------------------------------------------------------------------------
# iter_board_pieces / iter_color_pieces
# ---------------------------------------------------------------------------


class TestIterBoardPieces:
    """Tests for iter_board_pieces and iter_color_pieces."""

    def test_starting_position_yields_32_pieces(self) -> None:
        """Standard board has 32 occupied squares."""
        board = Board()
        pieces = list(iter_board_pieces(board))
        assert len(pieces) == 32

    def test_iter_color_pieces_white_starting(self) -> None:
        """Starting position has exactly 16 White pieces."""
        board = Board()
        pieces = list(iter_color_pieces(board, Color.WHITE))
        assert len(pieces) == 16
        assert all(p.color == Color.WHITE for p, _, _ in pieces)

    def test_iter_color_pieces_empty_board(self) -> None:
        """Empty board yields no pieces for either color."""
        board = Board()
        board.clear_board()
        assert list(iter_color_pieces(board, Color.WHITE)) == []
        assert list(iter_color_pieces(board, Color.BLACK)) == []


# ---------------------------------------------------------------------------
# legal_move_count
# ---------------------------------------------------------------------------


class TestLegalMoveCount:
    """Tests for legal_move_count."""

    def test_starting_position_white_20(self) -> None:
        """White has exactly 20 legal moves from the starting position."""
        board = Board()
        assert legal_move_count(board, Color.WHITE) == 20

    def test_king_in_check_fewer_than_20(self) -> None:
        """King in check has far fewer legal moves than 20."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.QUEEN))
        board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        assert legal_move_count(board, Color.WHITE) < 20


# ---------------------------------------------------------------------------
# king_coordinates
# ---------------------------------------------------------------------------


class TestKingCoordinates:
    """Tests for king_coordinates."""

    def test_white_king_starting_position(self) -> None:
        """White king starts at e1 — row 7, col 4."""
        board = Board()
        assert king_coordinates(board, Color.WHITE) == (7, 4)

    def test_black_king_starting_position(self) -> None:
        """Black king starts at e8 — row 0, col 4."""
        board = Board()
        assert king_coordinates(board, Color.BLACK) == (0, 4)

    def test_returns_none_for_missing_king(self) -> None:
        """Returns None when the king for that color is absent."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        assert king_coordinates(board, Color.BLACK) is None


# ---------------------------------------------------------------------------
# is_castled_king
# ---------------------------------------------------------------------------


class TestIsCastledKing:
    """Tests for is_castled_king."""

    def test_white_kingside_g1(self) -> None:
        """g1 is White's kingside castling square."""
        assert is_castled_king(Color.WHITE, sq("g1")) is True

    def test_white_queenside_c1(self) -> None:
        """c1 is White's queenside castling square."""
        assert is_castled_king(Color.WHITE, sq("c1")) is True

    def test_black_kingside_g8(self) -> None:
        """g8 is Black's kingside castling square."""
        assert is_castled_king(Color.BLACK, sq("g8")) is True

    def test_black_queenside_c8(self) -> None:
        """c8 is Black's queenside castling square."""
        assert is_castled_king(Color.BLACK, sq("c8")) is True

    def test_starting_square_not_castled(self) -> None:
        """e1 is the starting square, not a castled position."""
        assert is_castled_king(Color.WHITE, sq("e1")) is False


# ---------------------------------------------------------------------------
# both_queens_on_board
# ---------------------------------------------------------------------------


class TestBothQueensOnBoard:
    """Tests for both_queens_on_board."""

    def test_starting_position_true(self) -> None:
        """Starting position has both queens."""
        assert both_queens_on_board(Board()) is True

    def test_missing_white_queen_false(self) -> None:
        """Removing White's queen makes the function return False."""
        board = Board()
        board.set_piece(sq("d1"), None)
        assert both_queens_on_board(board) is False

    def test_both_queens_removed_false(self) -> None:
        """Removing both queens returns False."""
        board = Board()
        board.set_piece(sq("d1"), None)
        board.set_piece(sq("d8"), None)
        assert both_queens_on_board(board) is False


# ---------------------------------------------------------------------------
# pawn_supports_square
# ---------------------------------------------------------------------------


class TestPawnSupportsSquare:
    """Tests for pawn_supports_square."""

    def test_white_pawn_e4_supports_f5(self) -> None:
        """White pawn on e4 diagonally supports f5."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
        assert pawn_supports_square(board, Color.WHITE, 3, 5) is True

    def test_white_pawn_e4_supports_d5(self) -> None:
        """White pawn on e4 diagonally supports d5."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
        assert pawn_supports_square(board, Color.WHITE, 3, 3) is True

    def test_white_pawn_e4_does_not_support_e5(self) -> None:
        """White pawn on e4 does not support e5 (forward, not diagonal)."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
        assert pawn_supports_square(board, Color.WHITE, 3, 4) is False

    def test_black_pawn_attacks_downward(self) -> None:
        """Black pawn on e5 supports f4 and d4 (attacks toward rank 1)."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e5"), create_piece(Color.BLACK, PieceType.PAWN))
        assert pawn_supports_square(board, Color.BLACK, 4, 5) is True
        assert pawn_supports_square(board, Color.BLACK, 4, 3) is True


# ---------------------------------------------------------------------------
# center_distance
# ---------------------------------------------------------------------------


class TestCenterDistance:
    """Tests for center_distance."""

    def test_d4_is_central(self) -> None:
        """d4 is one of the four central squares — distance 0."""
        assert center_distance(4, 3) == 0

    def test_e4_is_central(self) -> None:
        """e4 is one of the four central squares — distance 0."""
        assert center_distance(4, 4) == 0

    def test_a1_is_far_from_center(self) -> None:
        """a1 corner is at least 3 steps from the center."""
        assert center_distance(7, 0) >= 3

    def test_symmetric_across_center_file(self) -> None:
        """center_distance is symmetric: col c mirrors col f, etc."""
        for r in range(8):
            for c in range(8):
                assert center_distance(r, c) == center_distance(r, 7 - c)


# ---------------------------------------------------------------------------
# is_passed_pawn
# ---------------------------------------------------------------------------


class TestIsPassedPawn:
    """Tests for is_passed_pawn."""

    def test_white_pawn_no_blockers_is_passed(self) -> None:
        """White pawn on e5 with no Black pawns ahead is passed."""
        assert is_passed_pawn(Color.WHITE, 3, 4, []) is True

    def test_white_pawn_blocked_same_file(self) -> None:
        """Black pawn on e6 (directly ahead) blocks the White passer."""
        assert is_passed_pawn(Color.WHITE, 3, 4, [(2, 4)]) is False

    def test_white_pawn_blocked_adjacent_file(self) -> None:
        """Black pawn on f6 (adjacent file, ahead) blocks the passer."""
        assert is_passed_pawn(Color.WHITE, 3, 4, [(2, 5)]) is False

    def test_white_pawn_not_blocked_by_pawn_on_same_rank(self) -> None:
        """Black pawn on d5 (same rank) does not block the e5 passer."""
        assert is_passed_pawn(Color.WHITE, 3, 4, [(3, 3)]) is True

    def test_black_pawn_no_blockers_is_passed(self) -> None:
        """Black pawn on d4 with no White pawns ahead is passed."""
        assert is_passed_pawn(Color.BLACK, 4, 3, []) is True

    def test_black_pawn_blocked_adjacent_file(self) -> None:
        """White pawn on c3 (ahead of Black's d4) blocks the Black passer."""
        assert is_passed_pawn(Color.BLACK, 4, 3, [(5, 2)]) is False


# ---------------------------------------------------------------------------
# passed_pawns_for_color
# ---------------------------------------------------------------------------


class TestPassedPawnsForColor:
    """Tests for passed_pawns_for_color."""

    def test_starting_position_no_passers(self) -> None:
        """Starting position has no passed pawns for either side."""
        board = Board()
        assert passed_pawns_for_color(board, Color.WHITE) == []
        assert passed_pawns_for_color(board, Color.BLACK) == []

    def test_isolated_passer_detected(self) -> None:
        """A lone White pawn with no enemy pawns ahead is identified as a passer."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        passers = passed_pawns_for_color(board, Color.WHITE)
        assert len(passers) == 1
        assert (3, 4) in passers


# ---------------------------------------------------------------------------
# pawn_path_to_promotion_is_clear
# ---------------------------------------------------------------------------


class TestPawnPathToPromotionIsClear:
    """Tests for pawn_path_to_promotion_is_clear."""

    def test_white_clear_path(self) -> None:
        """White pawn on e5 with empty e6/e7/e8 has a clear path."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        assert pawn_path_to_promotion_is_clear(board, Color.WHITE, (3, 4)) is True

    def test_white_blocked_path(self) -> None:
        """White pawn on e5 blocked by a pawn on e6 — path not clear."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("e6"), create_piece(Color.BLACK, PieceType.PAWN))
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        assert pawn_path_to_promotion_is_clear(board, Color.WHITE, (3, 4)) is False

    def test_black_clear_path(self) -> None:
        """Black pawn on d4 with empty d3/d2/d1 has a clear path."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("d4"), create_piece(Color.BLACK, PieceType.PAWN))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        assert pawn_path_to_promotion_is_clear(board, Color.BLACK, (4, 3)) is True


# ---------------------------------------------------------------------------
# is_advanced_passer
# ---------------------------------------------------------------------------


class TestIsAdvancedPasser:
    """Tests for is_advanced_passer."""

    def test_white_rank_6_is_advanced(self) -> None:
        """White pawn on rank 6 (row 2) is advanced."""
        assert is_advanced_passer(Color.WHITE, 2) is True

    def test_white_rank_4_not_advanced(self) -> None:
        """White pawn on rank 4 (row 4) is not advanced."""
        assert is_advanced_passer(Color.WHITE, 4) is False

    def test_black_rank_3_is_advanced(self) -> None:
        """Black pawn on rank 3 (row 5) is advanced."""
        assert is_advanced_passer(Color.BLACK, 5) is True

    def test_black_rank_5_not_advanced(self) -> None:
        """Black pawn on rank 5 (row 3) is not advanced."""
        assert is_advanced_passer(Color.BLACK, 3) is False


# ---------------------------------------------------------------------------
# total_non_pawn_material
# ---------------------------------------------------------------------------


class TestTotalNonPawnMaterial:
    """Tests for total_non_pawn_material."""

    def test_starting_position_expected_sum(self) -> None:
        """Starting material: 2 queens + 4 rooks + 4 bishops + 4 knights."""
        expected = (
            2 * MATERIAL_VALUES[PieceType.QUEEN]
            + 4 * MATERIAL_VALUES[PieceType.ROOK]
            + 4 * MATERIAL_VALUES[PieceType.BISHOP]
            + 4 * MATERIAL_VALUES[PieceType.KNIGHT]
        )
        assert total_non_pawn_material(Board()) == expected

    def test_kings_only_returns_zero(self) -> None:
        """Board with only kings has zero non-pawn material."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        assert total_non_pawn_material(board) == 0

    def test_both_queens_removed_decreases_by_two_queen_values(self) -> None:
        """Removing both queens decreases material by 2 × queen value."""
        board = Board()
        before = total_non_pawn_material(board)
        board.set_piece(sq("d1"), None)
        board.set_piece(sq("d8"), None)
        after = total_non_pawn_material(board)
        assert before - after == 2 * MATERIAL_VALUES[PieceType.QUEEN]


# ---------------------------------------------------------------------------
# materially_ahead_color / materially_behind_color
# ---------------------------------------------------------------------------


class TestMaterialBalance:
    """Tests for materially_ahead_color and materially_behind_color."""

    def test_equal_material_returns_none(self) -> None:
        """Starting position is equal — both functions return None."""
        board = Board()
        assert materially_ahead_color(board) is None
        assert materially_behind_color(board) is None

    def test_ahead_after_removing_enemy_bishop(self) -> None:
        """White is ahead after removing a Black bishop."""
        board = Board()
        board.set_piece(sq("c8"), None)
        assert materially_ahead_color(board) == Color.WHITE

    def test_ahead_and_behind_are_opposite(self) -> None:
        """materially_ahead and materially_behind return opposite colors."""
        board = Board()
        board.set_piece(sq("c8"), None)
        assert materially_behind_color(board) == Color.BLACK


# ---------------------------------------------------------------------------
# non_king_material_lead
# ---------------------------------------------------------------------------


class TestNonKingMaterialLead:
    """Tests for non_king_material_lead."""

    def test_starting_position_zero(self) -> None:
        """Equal material gives zero lead for both sides."""
        board = Board()
        assert non_king_material_lead(board, Color.WHITE) == 0
        assert non_king_material_lead(board, Color.BLACK) == 0

    def test_lead_after_removing_black_bishop(self) -> None:
        """Removing a Black bishop gives White a lead of one bishop value."""
        board = Board()
        board.set_piece(sq("c8"), None)
        assert non_king_material_lead(board, Color.WHITE) == MATERIAL_VALUES[PieceType.BISHOP]

    def test_black_lead_is_negative_for_white(self) -> None:
        """When Black is ahead, White's lead is negative."""
        board = Board()
        board.set_piece(sq("c1"), None)
        assert non_king_material_lead(board, Color.WHITE) < 0


# ---------------------------------------------------------------------------
# is_capture_move
# ---------------------------------------------------------------------------


class TestIsCaptureMove:
    """Tests for is_capture_move."""

    def test_quiet_pawn_push_is_not_capture(self) -> None:
        """e2e4 is a quiet move — no capture."""
        board = Board()
        move = Move(start=sq("e2"), end=sq("e4"), promotion=None)
        assert is_capture_move(board, move) is False

    def test_pawn_captures_enemy_pawn(self) -> None:
        """White pawn on e4 capturing Black pawn on d5 is a capture."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.PAWN))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        move = Move(start=sq("e4"), end=sq("d5"), promotion=None)
        assert is_capture_move(board, move) is True


# ---------------------------------------------------------------------------
# scale_signed / opposite_color
# ---------------------------------------------------------------------------


class TestScaleSigned:
    """Tests for scale_signed."""

    def test_positive_value_scaled(self) -> None:
        """Positive value is scaled by the percentage factor."""
        assert scale_signed(200, 50) == 100

    def test_negative_value_preserves_sign(self) -> None:
        """Negative value stays negative after scaling."""
        assert scale_signed(-200, 50) == -100

    def test_small_value_rounds_toward_zero(self) -> None:
        """Small value scaled by a small factor rounds toward zero."""
        assert scale_signed(10, 3) == 0

    def test_large_value_scaled(self) -> None:
        """Large value: 1000 scaled by 3% == 30."""
        assert scale_signed(1000, 3) == 30


class TestOppositeColor:
    """Tests for opposite_color."""

    def test_white_returns_black(self) -> None:
        """opposite_color(WHITE) is BLACK."""
        assert opposite_color(Color.WHITE) == Color.BLACK

    def test_black_returns_white(self) -> None:
        """opposite_color(BLACK) is WHITE."""
        assert opposite_color(Color.BLACK) == Color.WHITE


# ---------------------------------------------------------------------------
# file_pawn_state
# ---------------------------------------------------------------------------


class TestFilePawnState:
    """Tests for file_pawn_state."""

    def test_open_file_no_pawns(self) -> None:
        """A file with no pawns is open."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        assert file_pawn_state(board, Color.WHITE, 4) == "open"

    def test_semi_open_only_enemy_pawn(self) -> None:
        """A file with only an enemy pawn is semi-open for the asking side."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e5"), create_piece(Color.BLACK, PieceType.PAWN))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        assert file_pawn_state(board, Color.WHITE, 4) == "semi-open"

    def test_closed_friendly_pawn_present(self) -> None:
        """A file with a friendly pawn is closed regardless of enemy pawns."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        assert file_pawn_state(board, Color.WHITE, 4) == "closed"


# ---------------------------------------------------------------------------
# path_clear_between
# ---------------------------------------------------------------------------


class TestPathClearBetween:
    """Tests for path_clear_between."""

    def test_adjacent_squares_always_clear(self) -> None:
        """Adjacent squares have no squares between them — always clear."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        assert path_clear_between(board, (7, 0), (7, 1)) is True

    def test_clear_rank(self) -> None:
        """Empty squares between two rooks on the same rank returns True."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.KING))
        assert path_clear_between(board, (7, 0), (7, 7)) is True

    def test_blocked_rank(self) -> None:
        """A piece between start and end returns False."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.KING))
        assert path_clear_between(board, (7, 0), (7, 7)) is False
