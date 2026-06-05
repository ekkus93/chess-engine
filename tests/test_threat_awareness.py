"""Unit tests for chess_game.chess.threat_awareness."""

from __future__ import annotations

import dataclasses

import pytest

from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.defensive_priorities import KingDefenseProfile
from chess_game.chess.move import Move
from chess_game.chess.opponent_plans import OpponentPlanProfile
from chess_game.chess.threat_awareness import (
    ThreatState,
    ThreatWeights,
    threat_response_order_bonus,
    threat_response_root_bonus,
)
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


# ---------------------------------------------------------------------------
# ThreatWeights
# ---------------------------------------------------------------------------


class TestThreatWeights:
    """Tests for the ThreatWeights frozen dataclass."""

    def test_is_frozen(self) -> None:
        """Mutating a ThreatWeights instance raises FrozenInstanceError."""
        weights = ThreatWeights(
            pressure_relief=10,
            check_relief=20,
            passer_relief=24,
            flight_gain=22,
            back_rank_fix=34,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            weights.pressure_relief = 99  # type: ignore[misc]

    def test_all_fields_positive(self) -> None:
        """All five weight fields must be positive."""
        weights = ThreatWeights(
            pressure_relief=10,
            check_relief=20,
            passer_relief=24,
            flight_gain=22,
            back_rank_fix=34,
        )
        assert weights.pressure_relief > 0
        assert weights.check_relief > 0
        assert weights.passer_relief > 0
        assert weights.flight_gain > 0
        assert weights.back_rank_fix > 0


# ---------------------------------------------------------------------------
# ThreatState
# ---------------------------------------------------------------------------


class TestThreatState:
    """Tests for the ThreatState frozen dataclass."""

    def _make_state(self) -> ThreatState:
        plan = OpponentPlanProfile(
            invasion_lines=0, knight_jumps=0, pawn_breaks=0,
            checking_resources=0, passed_pawn_pushes=0,
        )
        defense = KingDefenseProfile(
            danger=0, invasion_lines=0, king_zone_defenders=3,
            heavy_connections=0, back_rank_weak=False, safe_king_moves=2,
        )
        return ThreatState(plan=plan, defense=defense, urgent_enemy_passers=[])

    def test_urgent_enemy_passers_is_list(self) -> None:
        """urgent_enemy_passers field is a list."""
        state = self._make_state()
        assert isinstance(state.urgent_enemy_passers, list)

    def test_is_frozen(self) -> None:
        """Mutating a ThreatState instance raises FrozenInstanceError."""
        state = self._make_state()
        with pytest.raises(dataclasses.FrozenInstanceError):
            state.urgent_enemy_passers = [(3, 4)]  # type: ignore[misc]


# ---------------------------------------------------------------------------
# threat_response_order_bonus — early-exit cases
# ---------------------------------------------------------------------------


class TestOrderBonusEarlyExit:
    """threat_response_order_bonus returns 0 for non-qualifying piece types."""

    def test_knight_move_returns_zero(self) -> None:
        """Knight is not in the qualifying piece set — always returns 0."""
        board = Board()
        move = Move(start=sq("g1"), end=sq("f3"), promotion=None)
        assert threat_response_order_bonus(board, Color.WHITE, PieceType.KNIGHT, move) == 0

    def test_bishop_move_returns_zero(self) -> None:
        """Bishop is not in the qualifying piece set — always returns 0."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.BISHOP))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        move = Move(start=sq("c1"), end=sq("d2"), promotion=None)
        assert threat_response_order_bonus(board, Color.WHITE, PieceType.BISHOP, move) == 0

    def test_center_pawn_move_returns_zero(self) -> None:
        """Pawn on the e-file (col 4) is filtered by the column guard."""
        board = Board()
        move = Move(start=sq("e2"), end=sq("e4"), promotion=None)
        assert threat_response_order_bonus(board, Color.WHITE, PieceType.PAWN, move) == 0

    def test_quiet_position_returns_zero(self) -> None:
        """No urgent threats → rook shuffle scores 0."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE
        move = Move(start=sq("h1"), end=sq("h3"), promotion=None)
        assert threat_response_order_bonus(board, Color.WHITE, PieceType.ROOK, move) == 0


# ---------------------------------------------------------------------------
# threat_response_order_bonus — passer relief
# ---------------------------------------------------------------------------


class TestOrderBonusPasserRelief:
    """Blocking an advanced enemy passer scores higher than an irrelevant move."""

    def _passer_board(self) -> Board:
        """White has an e7 pawn about to promote; Black rook can block on e8."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.ROOK))
        board.turn = Color.BLACK
        return board

    def test_blocking_passer_scores_higher_than_neutral(self) -> None:
        """Black rook moving to e8 (blocking the passer) scores above a neutral shuffle."""
        board = self._passer_board()
        block_move = Move(start=sq("d8"), end=sq("e8"), promotion=None)
        neutral_move = Move(start=sq("d8"), end=sq("a8"), promotion=None)
        block_score = threat_response_order_bonus(board, Color.BLACK, PieceType.ROOK, block_move)
        neutral_score = threat_response_order_bonus(board, Color.BLACK, PieceType.ROOK, neutral_move)
        assert block_score > neutral_score

    def test_blocking_move_scores_positive(self) -> None:
        """The rook move that blocks the passer earns a positive bonus."""
        board = self._passer_board()
        block_move = Move(start=sq("d8"), end=sq("e8"), promotion=None)
        assert threat_response_order_bonus(board, Color.BLACK, PieceType.ROOK, block_move) > 0


# ---------------------------------------------------------------------------
# threat_response_order_bonus — check relief
# ---------------------------------------------------------------------------


class TestOrderBonusCheckRelief:
    """Interposing against a checking threat scores higher than a neutral move."""

    def _check_threat_board(self) -> Board:
        """White queen on e3 threatens Black king on e8 via the open e-file."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.set_piece(sq("h3"), create_piece(Color.BLACK, PieceType.QUEEN))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e3"), create_piece(Color.WHITE, PieceType.QUEEN))
        board.turn = Color.BLACK
        return board

    def test_interposing_scores_higher_than_neutral(self) -> None:
        """Black queen moving to e6 (blocking e-file) scores above moving to h7."""
        board = self._check_threat_board()
        interpose = Move(start=sq("h3"), end=sq("e6"), promotion=None)
        neutral = Move(start=sq("h3"), end=sq("h7"), promotion=None)
        assert threat_response_order_bonus(board, Color.BLACK, PieceType.QUEEN, interpose) > \
               threat_response_order_bonus(board, Color.BLACK, PieceType.QUEEN, neutral)

    def test_interposing_returns_positive_bonus(self) -> None:
        """The interposing move earns a positive bonus."""
        board = self._check_threat_board()
        interpose = Move(start=sq("h3"), end=sq("e6"), promotion=None)
        assert threat_response_order_bonus(board, Color.BLACK, PieceType.QUEEN, interpose) > 0


# ---------------------------------------------------------------------------
# threat_response_root_bonus — basic return type
# ---------------------------------------------------------------------------


class TestRootBonusReturnType:
    """threat_response_root_bonus returns an int in all cases."""

    def test_returns_int_for_rook_move(self) -> None:
        """Returns an integer for a quiet rook move with no threats."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE

        child_board = board.clone()
        child_board.apply_legal_move(sq("d1"), sq("d5"), promotion=None)

        move = Move(start=sq("d1"), end=sq("d5"), promotion=None)
        result = threat_response_root_bonus(board, move, child_board, Color.WHITE)
        assert isinstance(result, int)

    def test_returns_zero_for_knight(self) -> None:
        """Moving kind filtered to KNIGHT returns 0."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KNIGHT))
        board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        board.turn = Color.WHITE

        child_board = board.clone()
        child_board.apply_legal_move(sq("g1"), sq("f3"), promotion=None)

        move = Move(start=sq("g1"), end=sq("f3"), promotion=None)
        assert threat_response_root_bonus(board, move, child_board, Color.WHITE) == 0


# ---------------------------------------------------------------------------
# threat_response_root_bonus — simplification bonus
# ---------------------------------------------------------------------------


class TestRootBonusSimplification:
    """When ahead materially, capturing an enemy heavy piece earns a bonus."""

    def test_capturing_enemy_rook_when_ahead(self) -> None:
        """White queen ahead captures Black rook: simplification bonus fires."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.ROOK))
        board.turn = Color.WHITE

        child_board = board.clone()
        applied = child_board.apply_legal_move(sq("d1"), sq("d5"), promotion=None)
        assert applied

        move = Move(start=sq("d1"), end=sq("d5"), promotion=None)
        bonus = threat_response_root_bonus(board, move, child_board, Color.WHITE)
        assert bonus >= 30

    def test_no_simplification_when_behind(self) -> None:
        """No simplification bonus fires when White is materially behind."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.ROOK))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.QUEEN))
        board.turn = Color.WHITE

        child_board = board.clone()
        applied = child_board.apply_legal_move(sq("d1"), sq("d5"), promotion=None)
        assert applied

        move = Move(start=sq("d1"), end=sq("d5"), promotion=None)
        bonus = threat_response_root_bonus(board, move, child_board, Color.WHITE)
        assert bonus < 30
