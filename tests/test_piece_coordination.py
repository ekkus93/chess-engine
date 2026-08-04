"""Unit tests for chess_game.chess.piece_coordination."""

from __future__ import annotations

import dataclasses

import pytest

from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.move import Move
from chess_game.chess.piece_coordination import (
    PiecePlacementProfile,
    bishop_coordination_bonus,
    improves_worst_piece,
    queen_coordination_bonus,
    rook_coordination_bonus,
    square_has_friendly_support,
)
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq

# ---------------------------------------------------------------------------
# PiecePlacementProfile
# ---------------------------------------------------------------------------


class TestPiecePlacementProfile:
    """Tests for the PiecePlacementProfile frozen dataclass."""

    def test_is_frozen(self) -> None:
        """Mutating a PiecePlacementProfile raises FrozenInstanceError."""
        profile = PiecePlacementProfile(kind=PieceType.ROOK, square=sq("d1"), score=5)
        with pytest.raises(dataclasses.FrozenInstanceError):
            profile.score = 99  # type: ignore[misc]

    def test_score_is_int(self) -> None:
        """The score field is an int."""
        profile = PiecePlacementProfile(kind=PieceType.KNIGHT, square=sq("g1"), score=27)
        assert isinstance(profile.score, int)


# ---------------------------------------------------------------------------
# improves_worst_piece
# ---------------------------------------------------------------------------


class TestImprovesWorstPiece:
    """Tests for improves_worst_piece."""

    def test_knight_development_returns_true(self) -> None:
        """Knight from b1 (home edge) to c3 (central) improves placement by >4."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("b1"), create_piece(Color.WHITE, PieceType.KNIGHT))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        move = Move(start=sq("b1"), end=sq("c3"), promotion=None)
        assert improves_worst_piece(board, move) is True

    def test_pawn_push_returns_false(self) -> None:
        """Pawn is not a strategic piece — always returns False."""
        board = Board()
        move = Move(start=sq("e2"), end=sq("e4"), promotion=None)
        assert improves_worst_piece(board, move) is False

    def test_king_move_returns_false(self) -> None:
        """King is not a strategic piece — always returns False."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        move = Move(start=sq("e1"), end=sq("f1"), promotion=None)
        assert improves_worst_piece(board, move) is False

    def test_moving_well_placed_piece_to_worse_square_returns_false(self) -> None:
        """Moving a central knight to a peripheral square is not an improvement."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.KNIGHT))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        move = Move(start=sq("d4"), end=sq("c6"), promotion=None)
        assert improves_worst_piece(board, move) is False


# ---------------------------------------------------------------------------
# rook_coordination_bonus
# ---------------------------------------------------------------------------


class TestRookCoordinationBonus:
    """Tests for rook_coordination_bonus."""

    def test_disconnected_rooks_reunite_returns_20(self) -> None:
        """Moving a disconnected rook to the same rank as another returns 20."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("h5"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        # h5→h1: both rooks on rank 1 (connected)
        move = Move(start=sq("h5"), end=sq("h1"), promotion=None)
        assert rook_coordination_bonus(board, Color.WHITE, move) == 20

    def test_already_connected_rook_returns_zero(self) -> None:
        """Moving a rook that is already connected returns 0 immediately."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("d8"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        # d1 and d8 are connected (same file, clear path)
        move = Move(start=sq("d1"), end=sq("a1"), promotion=None)
        assert rook_coordination_bonus(board, Color.WHITE, move) == 0

    def test_disconnected_rooks_stay_disconnected_returns_zero(self) -> None:
        """Moving a disconnected rook that does NOT connect to the other returns 0."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("h5"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        # h5→g5: not on same rank/file as d1
        move = Move(start=sq("h5"), end=sq("g5"), promotion=None)
        assert rook_coordination_bonus(board, Color.WHITE, move) == 0

    def test_non_rook_returns_zero(self) -> None:
        """Function returns 0 if the moving piece is not a rook."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        move = Move(start=sq("d1"), end=sq("d4"), promotion=None)
        assert rook_coordination_bonus(board, Color.WHITE, move) == 0


# ---------------------------------------------------------------------------
# bishop_coordination_bonus
# ---------------------------------------------------------------------------


class TestBishopCoordinationBonus:
    """Tests for bishop_coordination_bonus."""

    def test_bishop_onto_long_diagonal_with_mobility_gain_returns_bonus(self) -> None:
        """Bishop moving from short diagonal to long diagonal earns >= 18."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.BISHOP))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        # c1 is not on a long diagonal; b2 is on the a8-h1 diagonal
        move = Move(start=sq("c1"), end=sq("b2"), promotion=None)
        assert bishop_coordination_bonus(board, move) >= 18

    def test_bishop_already_on_long_diagonal_returns_zero(self) -> None:
        """Bishop already on long diagonal moving along it earns 0."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.BISHOP))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        # a1=(7,0): row+col=7 → on the long diagonal already
        move = Move(start=sq("a1"), end=sq("b2"), promotion=None)
        assert bishop_coordination_bonus(board, move) == 0

    def test_non_bishop_returns_zero(self) -> None:
        """Function returns 0 if the moving piece is not a bishop."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        move = Move(start=sq("d1"), end=sq("c2"), promotion=None)
        assert bishop_coordination_bonus(board, move) == 0


# ---------------------------------------------------------------------------
# queen_coordination_bonus
# ---------------------------------------------------------------------------


class TestQueenCoordinationBonus:
    """Tests for queen_coordination_bonus."""

    def test_queen_moves_to_support_more_pieces(self) -> None:
        """Queen moving to support two extra friendly pieces returns support_gain × 10."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.QUEEN))
        board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("h5"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        # h1 supports: king on a1 (same rank), rook on h5 (same file)
        # d1 would support: king on a1 (same rank), rook on h5 (diagonal), rook on d4 (same file)
        move = Move(start=sq("h1"), end=sq("d1"), promotion=None)
        assert queen_coordination_bonus(board, Color.WHITE, move) > 0

    def test_queen_moves_to_worse_position_returns_zero(self) -> None:
        """Queen moving to a square supporting fewer pieces returns 0."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
        board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("h5"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        # Moving queen from d1 (supports king + 2 rooks) to h1 (supports fewer)
        move = Move(start=sq("d1"), end=sq("h1"), promotion=None)
        assert queen_coordination_bonus(board, Color.WHITE, move) == 0

    def test_non_queen_returns_zero(self) -> None:
        """Function returns 0 if the moving piece is not a queen."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        move = Move(start=sq("d1"), end=sq("d5"), promotion=None)
        assert queen_coordination_bonus(board, Color.WHITE, move) == 0


# ---------------------------------------------------------------------------
# square_has_friendly_support
# ---------------------------------------------------------------------------


class TestSquareHasFriendlySupport:
    """Tests for square_has_friendly_support."""

    def test_pawn_supports_diagonally_forward(self) -> None:
        """White pawn on e4 attacks d5; d5 has friendly support."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        assert square_has_friendly_support(board, Color.WHITE, sq("d5")) is True

    def test_pawn_does_not_support_forward_square(self) -> None:
        """White pawn on e4 does not attack e5 (straight forward)."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        assert square_has_friendly_support(board, Color.WHITE, sq("e5")) is False

    def test_enemy_support_does_not_count(self) -> None:
        """An enemy bishop attacking d5 does not count as White support."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e4"), create_piece(Color.BLACK, PieceType.BISHOP))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        assert square_has_friendly_support(board, Color.WHITE, sq("d5")) is False

    def test_isolated_square_no_support(self) -> None:
        """A square with no nearby friendly pieces has no support."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        assert square_has_friendly_support(board, Color.WHITE, sq("e4")) is False

    def test_edge_square_no_crash(self) -> None:
        """Checking support on a corner square does not raise."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        result = square_has_friendly_support(board, Color.WHITE, sq("h8"))
        assert isinstance(result, bool)
