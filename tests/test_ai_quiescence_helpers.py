"""Unit tests for chess_game.chess.ai_quiescence_helpers."""

from __future__ import annotations

from chess_game.chess.ai_quiescence_helpers import (
    _quiescence_capture_mvv_lva,
    _quiescence_structure_follow_up_score,
    _quiescence_tactical_score,
    select_quiescence_moves,
)
from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.move import Move
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def _noop_order(board: Board, move: Move) -> int:
    """Zero move-order score stub for select_quiescence_moves tests."""
    return 0


# ---------------------------------------------------------------------------
# select_quiescence_moves — filtering
# ---------------------------------------------------------------------------


class TestSelectQuiescenceMoves:
    """Tests for select_quiescence_moves."""

    def test_quiet_move_returns_empty(self) -> None:
        """A quiet pawn push with no captures/promotions/check → []."""
        board = Board()
        quiet = Move(start=sq("e2"), end=sq("e4"), promotion=None)
        assert select_quiescence_moves(board, [quiet], _noop_order, 10) == []

    def test_capture_move_is_included(self) -> None:
        """A capture move appears in the output."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.PAWN))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        capture = Move(start=sq("e4"), end=sq("d5"), promotion=None)
        result = select_quiescence_moves(board, [capture], _noop_order, 10)
        assert len(result) == 1

    def test_promotion_is_included(self) -> None:
        """A promotion move appears in the output."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        promo = Move(start=sq("e7"), end=sq("e8"), promotion=PieceType.QUEEN)
        result = select_quiescence_moves(board, [promo], _noop_order, 10)
        assert len(result) == 1

    def test_quiet_moves_filtered_captures_kept(self) -> None:
        """When both quiet and capture moves are present, only capture is returned."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.PAWN))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        quiet = Move(start=sq("e4"), end=sq("e5"), promotion=None)
        capture = Move(start=sq("e4"), end=sq("d5"), promotion=None)
        result = select_quiescence_moves(board, [quiet, capture], _noop_order, 10)
        assert capture in result
        assert quiet not in result

    def test_quiet_check_is_filtered(self) -> None:
        """A quiet check (no capture) is not included in quiescence moves."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.QUEEN))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        checking_move = Move(start=sq("a1"), end=sq("e5"), promotion=None)
        result = select_quiescence_moves(board, [checking_move], _noop_order, 10)
        assert result == []

    def test_qxp_undefended_included_in_quiescence(self) -> None:
        """Queen capturing an undefended pawn is a winning capture and must be included.

        The old filter blocked ALL QxP captures regardless of whether the pawn was
        defended.  The new filter only rejects captures where the captured piece has
        zero value (impossible in a real game), so QxP on an undefended pawn is
        correctly included and the recursive search evaluates the follow-up.
        """
        board = Board()
        board.clear_board()
        board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.QUEEN))
        board.set_piece(sq("d4"), create_piece(Color.BLACK, PieceType.PAWN))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        qxp = Move(start=sq("e5"), end=sq("d4"), promotion=None)
        result = select_quiescence_moves(board, [qxp], _noop_order, 10)
        assert result == [qxp], "QxP on undefended pawn must be a quiescence candidate"


# ---------------------------------------------------------------------------
# select_quiescence_moves — ordering
# ---------------------------------------------------------------------------


class TestSelectQuiescenceOrdering:
    """Capture ordering tests for select_quiescence_moves."""

    def test_queen_capture_before_bishop_capture(self) -> None:
        """Pawn capturing a queen ranks above pawn capturing a bishop."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("c5"), create_piece(Color.BLACK, PieceType.QUEEN))
        board.set_piece(sq("e5"), create_piece(Color.BLACK, PieceType.BISHOP))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        cap_queen = Move(start=sq("d4"), end=sq("c5"), promotion=None)
        cap_bishop = Move(start=sq("d4"), end=sq("e5"), promotion=None)
        result = select_quiescence_moves(board, [cap_bishop, cap_queen], _noop_order, 10)
        assert len(result) == 2
        assert result.index(cap_queen) < result.index(cap_bishop)


# ---------------------------------------------------------------------------
# _quiescence_capture_mvv_lva
# ---------------------------------------------------------------------------


class TestQuiescenceCaptureMvvLva:
    """Tests for _quiescence_capture_mvv_lva."""

    def test_pawn_captures_queen_scores_positive(self) -> None:
        """Pawn taking a queen is a winning capture — returns positive score."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("e5"), create_piece(Color.BLACK, PieceType.QUEEN))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        move = Move(start=sq("d4"), end=sq("e5"), promotion=None)
        assert _quiescence_capture_mvv_lva(board, move) > 0

    def test_queen_captures_undefended_pawn_returns_positive(self) -> None:
        """Queen taking an undefended pawn returns a positive MVV-LVA score.

        The old filter blocked all QxP captures at the static stage.  The new filter
        only rejects captures where captured_value < 1 (impossible for real pieces),
        so QxP correctly returns a positive score and is included in quiescence.
        """
        board = Board()
        board.clear_board()
        board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.QUEEN))
        board.set_piece(sq("d4"), create_piece(Color.BLACK, PieceType.PAWN))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        move = Move(start=sq("e5"), end=sq("d4"), promotion=None)
        assert _quiescence_capture_mvv_lva(board, move) > 0

    def test_rook_capture_scores_higher_than_bishop(self) -> None:
        """Capturing a rook returns a higher score than capturing a bishop."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("c5"), create_piece(Color.BLACK, PieceType.ROOK))
        board.set_piece(sq("e5"), create_piece(Color.BLACK, PieceType.BISHOP))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        cap_rook = Move(start=sq("d4"), end=sq("c5"), promotion=None)
        cap_bishop = Move(start=sq("d4"), end=sq("e5"), promotion=None)
        assert _quiescence_capture_mvv_lva(board, cap_rook) > _quiescence_capture_mvv_lva(board, cap_bishop)


# ---------------------------------------------------------------------------
# _quiescence_tactical_score
# ---------------------------------------------------------------------------


class TestQuiescenceTacticalScore:
    """Tests for _quiescence_tactical_score."""

    def test_returns_int(self) -> None:
        """_quiescence_tactical_score returns an integer."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.ROOK))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        move = Move(start=sq("e4"), end=sq("d5"), promotion=None)
        assert isinstance(_quiescence_tactical_score(board, move), int)

    def test_pawn_captures_rook_is_high_value(self) -> None:
        """Pawn capturing a rook (clearly winning) returns a positive score."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.ROOK))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        move = Move(start=sq("e4"), end=sq("d5"), promotion=None)
        assert _quiescence_tactical_score(board, move) > 0


# ---------------------------------------------------------------------------
# _quiescence_structure_follow_up_score
# ---------------------------------------------------------------------------


class TestQuiescenceStructureFollowUpScore:
    """Tests for _quiescence_structure_follow_up_score."""

    def test_returns_int(self) -> None:
        """Returns an integer for any valid board pair."""
        board = Board()
        result = _quiescence_structure_follow_up_score(board, board.clone())
        assert isinstance(result, int)

    def test_identical_boards_return_zero(self) -> None:
        """Same structure before and after → score is 0."""
        board = Board()
        assert _quiescence_structure_follow_up_score(board, board.clone()) == 0
