"""Regression tests for STRATEGY12: endgame conversion acceleration."""

from __future__ import annotations

from chess_game.chess.ai import get_best_move
from chess_game.chess.board import Board, create_piece
from chess_game.chess.forced_win_guidance import forced_win_move_bonus, is_forced_win_endgame
from chess_game.chess.move import Move
from chess_game.chess.pawn_race_move_ordering import pawn_race_move_bonus
from chess_game.chess.passer_race_guidance import explicit_pawn_race_tempo
from chess_game.chess.simple_endgame_guidance import (
    simple_endgame_order_bonus,
    simple_endgame_root_bonus,
)
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def _build_board(
    pieces: list[tuple[str, Color, PieceType]],
    turn: Color,
) -> Board:
    board = Board()
    board.clear_board()
    for square, color, kind in pieces:
        board.set_piece(sq(square), create_piece(color, kind))
    board.turn = turn
    return board


class TestStrategy12ForcedWinDetection:
    """Tests for is_forced_win_endgame() detection logic."""

    def test_q_vs_k_is_forced_win(self) -> None:
        """Q+K vs bare K should be detected as forced win for white."""
        board = _build_board(
            [
                ("e1", Color.WHITE, PieceType.KING),
                ("f1", Color.WHITE, PieceType.QUEEN),
                ("e8", Color.BLACK, PieceType.KING),
            ],
            turn=Color.WHITE,
        )
        assert is_forced_win_endgame(board, Color.WHITE)

    def test_r_vs_k_is_forced_win(self) -> None:
        """R+K vs bare K should be detected as forced win for white."""
        board = _build_board(
            [
                ("e1", Color.WHITE, PieceType.KING),
                ("a1", Color.WHITE, PieceType.ROOK),
                ("e8", Color.BLACK, PieceType.KING),
            ],
            turn=Color.WHITE,
        )
        assert is_forced_win_endgame(board, Color.WHITE)

    def test_equal_position_not_forced_win(self) -> None:
        """Equal material should not be detected as forced win."""
        board = _build_board(
            [
                ("e1", Color.WHITE, PieceType.KING),
                ("d1", Color.WHITE, PieceType.QUEEN),
                ("e8", Color.BLACK, PieceType.KING),
                ("d8", Color.BLACK, PieceType.QUEEN),
            ],
            turn=Color.WHITE,
        )
        assert not is_forced_win_endgame(board, Color.WHITE)

    def test_opponent_has_rook_not_forced_win(self) -> None:
        """When opponent has a rook, should not be forced win."""
        board = _build_board(
            [
                ("e1", Color.WHITE, PieceType.KING),
                ("d1", Color.WHITE, PieceType.QUEEN),
                ("e8", Color.BLACK, PieceType.KING),
                ("a8", Color.BLACK, PieceType.ROOK),
            ],
            turn=Color.WHITE,
        )
        assert not is_forced_win_endgame(board, Color.WHITE)

    def test_black_q_vs_white_k_is_forced_win_for_black(self) -> None:
        """Black Q vs bare white K should detect forced win for black."""
        board = _build_board(
            [
                ("e8", Color.BLACK, PieceType.KING),
                ("d8", Color.BLACK, PieceType.QUEEN),
                ("e1", Color.WHITE, PieceType.KING),
            ],
            turn=Color.BLACK,
        )
        assert is_forced_win_endgame(board, Color.BLACK)


class TestStrategy12ForcedWinMoveBonus:
    """Tests for forced_win_move_bonus() prioritization."""

    def test_pawn_push_gets_bonus_in_forced_win(self) -> None:
        """Pawn push toward promotion should receive bonus in forced win."""
        board = _build_board(
            [
                ("e1", Color.WHITE, PieceType.KING),
                ("h5", Color.WHITE, PieceType.PAWN),
                ("a8", Color.BLACK, PieceType.KING),
            ],
            turn=Color.WHITE,
        )
        pawn_push = Move(start=sq("h5"), end=sq("h6"))  # pawn advance
        king_away = Move(start=sq("e1"), end=sq("d1"))  # quiet king move away
        pawn_bonus = forced_win_move_bonus(board, pawn_push, Color.WHITE)
        king_bonus = forced_win_move_bonus(board, king_away, Color.WHITE)
        assert pawn_bonus > king_bonus, (
            f"Pawn push bonus ({pawn_bonus}) should exceed away king bonus ({king_bonus})"
        )

    def test_king_toward_opponent_beats_away_move(self) -> None:
        """King moving toward opponent king should score higher than retreating."""
        board = _build_board(
            [
                ("e1", Color.WHITE, PieceType.KING),
                ("a1", Color.WHITE, PieceType.QUEEN),
                ("e8", Color.BLACK, PieceType.KING),
            ],
            turn=Color.WHITE,
        )
        # King toward e8 direction (e1->e2 is closer)
        toward = Move(start=sq("e1"), end=sq("e2"))
        away = Move(start=sq("e1"), end=sq("d1"))
        toward_bonus = forced_win_move_bonus(board, toward, Color.WHITE)
        away_bonus = forced_win_move_bonus(board, away, Color.WHITE)
        assert toward_bonus >= away_bonus, (
            f"Toward-king bonus ({toward_bonus}) should be >= away bonus ({away_bonus})"
        )

    def test_no_bonus_in_equal_position(self) -> None:
        """No forced-win bonus should apply in equal material positions."""
        board = _build_board(
            [
                ("e1", Color.WHITE, PieceType.KING),
                ("d1", Color.WHITE, PieceType.QUEEN),
                ("e8", Color.BLACK, PieceType.KING),
                ("d8", Color.BLACK, PieceType.QUEEN),
            ],
            turn=Color.WHITE,
        )
        move = Move(start=sq("d1"), end=sq("d7"))
        bonus = forced_win_move_bonus(board, move, Color.WHITE)
        assert bonus == 0, f"No forced-win bonus in equal position, got {bonus}"


class TestStrategy12SearchBehavior:
    """Tests verifying engine search behavior in endgame positions."""

    def test_queen_vs_king_finds_move(self) -> None:
        """Q vs K: engine should find a legal move at depth 2."""
        board = _build_board(
            [
                ("e1", Color.WHITE, PieceType.KING),
                ("f1", Color.WHITE, PieceType.QUEEN),
                ("a8", Color.BLACK, PieceType.KING),
            ],
            turn=Color.WHITE,
        )
        best = get_best_move(board, depth=2)
        assert best is not None, "Should find a move in Q vs K"

    def test_rook_vs_king_finds_move(self) -> None:
        """R vs K: engine should find a legal move at depth 2."""
        board = _build_board(
            [
                ("e1", Color.WHITE, PieceType.KING),
                ("a1", Color.WHITE, PieceType.ROOK),
                ("e8", Color.BLACK, PieceType.KING),
            ],
            turn=Color.WHITE,
        )
        best = get_best_move(board, depth=2)
        assert best is not None, "Should find a move in R vs K"

    def test_pawn_race_finds_move(self) -> None:
        """K+P vs K+P pawn race: engine should find a legal move."""
        board = _build_board(
            [
                ("e4", Color.WHITE, PieceType.KING),
                ("d6", Color.WHITE, PieceType.PAWN),
                ("e6", Color.BLACK, PieceType.KING),
                ("e3", Color.BLACK, PieceType.PAWN),
            ],
            turn=Color.WHITE,
        )
        best = get_best_move(board, depth=2)
        assert best is not None, "Should find a move in K+P vs K+P"

    def test_king_plus_pawn_vs_king_finds_move(self) -> None:
        """K+P vs K: engine should find a legal move at depth 1."""
        board = _build_board(
            [
                ("d5", Color.WHITE, PieceType.KING),
                ("d6", Color.WHITE, PieceType.PAWN),
                ("d8", Color.BLACK, PieceType.KING),
            ],
            turn=Color.WHITE,
        )
        best = get_best_move(board, depth=1)
        assert best is not None, "Should find a move in K+P vs K"

    def test_strategy12_pawn_race_tempo_calculation_matches_expected(self) -> None:
        """Tempo helper should include side-to-move adjustment in close races."""
        board = _build_board(
            [
                ("e5", Color.WHITE, PieceType.KING),
                ("d6", Color.WHITE, PieceType.PAWN),
                ("e8", Color.BLACK, PieceType.KING),
                ("e3", Color.BLACK, PieceType.PAWN),
            ],
            turn=Color.WHITE,
        )
        white_tempo, black_tempo = explicit_pawn_race_tempo(board)
        assert (white_tempo, black_tempo) == (3, 4)

    def test_strategy12_pawn_race_white_advances_runaway_pawn(self) -> None:
        """When white has the faster passer, engine should push it."""
        board = _build_board(
            [
                ("c6", Color.WHITE, PieceType.KING),
                ("d6", Color.WHITE, PieceType.PAWN),
                ("h8", Color.BLACK, PieceType.KING),
                ("a3", Color.BLACK, PieceType.PAWN),
            ],
            turn=Color.WHITE,
        )
        best = get_best_move(board, depth=2)
        assert best is not None
        assert best.start == sq("d6")
        assert best.end == sq("d7")

    def test_strategy12_pawn_race_king_blocks_opponent_passer(self) -> None:
        """King move that improves race margin should beat drifting king move."""
        board = _build_board(
            [
                ("e5", Color.WHITE, PieceType.KING),
                ("h5", Color.WHITE, PieceType.PAWN),
                ("h8", Color.BLACK, PieceType.KING),
                ("e3", Color.BLACK, PieceType.PAWN),
            ],
            turn=Color.WHITE,
        )
        king_block = Move(start=sq("e5"), end=sq("e4"))
        king_drift = Move(start=sq("e5"), end=sq("f6"))
        block_bonus = pawn_race_move_bonus(board, king_block, Color.WHITE)
        drift_bonus = pawn_race_move_bonus(board, king_drift, Color.WHITE)
        assert block_bonus > drift_bonus

    def test_strategy12_king_plus_pawn_king_activates_king_toward_promotion(
        self,
    ) -> None:
        """King move toward promotion square should beat retreat in K+P vs K."""
        board = _build_board(
            [
                ("b3", Color.WHITE, PieceType.KING),
                ("d5", Color.WHITE, PieceType.PAWN),
                ("d8", Color.BLACK, PieceType.KING),
            ],
            turn=Color.WHITE,
        )
        toward = Move(start=sq("b3"), end=sq("c4"))
        away = Move(start=sq("b3"), end=sq("a2"))
        toward_bonus = simple_endgame_order_bonus(
            board,
            Color.WHITE,
            PieceType.KING,
            toward,
        )
        away_bonus = simple_endgame_order_bonus(
            board,
            Color.WHITE,
            PieceType.KING,
            away,
        )
        assert toward_bonus > away_bonus

    def test_strategy12_king_centralization_overrides_defensive_moves(self) -> None:
        """Root tie-break should prefer king activation over passive bishop drift."""
        board = _build_board(
            [
                ("b3", Color.WHITE, PieceType.KING),
                ("d4", Color.WHITE, PieceType.PAWN),
                ("h1", Color.WHITE, PieceType.BISHOP),
                ("g7", Color.BLACK, PieceType.KING),
            ],
            turn=Color.WHITE,
        )
        king_activate = Move(start=sq("b3"), end=sq("c4"))
        bishop_drift = Move(start=sq("h1"), end=sq("g2"))

        king_child = board.clone()
        bishop_child = board.clone()
        assert king_child.apply_legal_move(king_activate.start, king_activate.end)
        assert bishop_child.apply_legal_move(bishop_drift.start, bishop_drift.end)

        king_bonus = simple_endgame_root_bonus(
            board,
            king_activate,
            king_child,
            Color.WHITE,
        )
        bishop_bonus = simple_endgame_root_bonus(
            board,
            bishop_drift,
            bishop_child,
            Color.WHITE,
        )
        assert king_bonus > bishop_bonus
