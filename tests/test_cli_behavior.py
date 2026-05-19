"""Tests for CLI/console behavior: move parsing, game_over_message, and _game_loop."""

from __future__ import annotations

from unittest.mock import patch, MagicMock
from chess_game.chess.constants import ROW_2, ROW_4, COL_E
from chess_game.chess.move import parse_move_notation
from chess_game.chess.types import Color, PieceType
import pytest


# ---------- parse_move_notation edge cases ---------- #


class TestParseMoveNotationEdgeCases:
    """Ensure CLI move parser is robust and predictable."""

    def test_empty_input_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid move format"):
            parse_move_notation("")

    def test_whitespace_only_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid move format"):
            parse_move_notation("   ")

    def test_too_short_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid move format"):
            parse_move_notation("e2")

    def test_extra_chars_after_valid_move_raises(self) -> None:
        # e2e44 is length 5 but not a valid promotion suffix
        with pytest.raises(ValueError):
            parse_move_notation("e2e44")

    def test_leading_trailing_spaces_rejected(self) -> None:
        # Leading/trailing spaces change length/chars → rejected.
        with pytest.raises(ValueError):
            parse_move_notation(" e2e4")

        with pytest.raises(ValueError):
            parse_move_notation("e2e4 ")

    def test_mixed_case_letters_accepted(self) -> None:
        # Ensure user typing "E2E4" still works.
        move = parse_move_notation("E2E4")
        assert move.start.row == ROW_2
        assert move.start.col == COL_E
        assert move.end.row == ROW_4
        assert move.end.col == COL_E

    def test_mixed_case_promotion_accepted(self) -> None:
        move = parse_move_notation("e7E8Q")
        assert move.promotion == PieceType.QUEEN

    def test_uppercase_promotion_letters_accepted(self) -> None:
        for ch in ("Q", "R", "B", "N"):
            m = parse_move_notation(f"e7e8{ch}")
            assert m.promotion is not None

    def test_off_board_row_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_move_notation("e9e9")

    def test_off_board_col_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_move_notation("i1h1")

    def test_leading_digit_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_move_notation("1e2e4")

    def test_garbage_input_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_move_notation("aaaa")


# ---------- _game_over_message ---------- #


class TestGameOverMessage:
    """Verify _game_over_message from main.py."""

    def test_checkmate_black_to_move(self) -> None:
        from chess_game.main import _game_over_message

        board = MagicMock()
        board.turn = Color.BLACK
        with patch("chess_game.main.is_checkmate", return_value=True):
            msg = _game_over_message(board)
        assert msg is not None
        assert "Checkmate" in msg
        assert "White wins" in msg

    def test_checkmate_white_to_move(self) -> None:
        from chess_game.main import _game_over_message

        board = MagicMock()
        board.turn = Color.WHITE
        with patch("chess_game.main.is_checkmate", return_value=True):
            msg = _game_over_message(board)
        assert msg is not None
        assert "Checkmate" in msg
        assert "Black wins" in msg

    def test_stalemate(self) -> None:
        from chess_game.main import _game_over_message

        board = MagicMock()
        with patch("chess_game.main.is_checkmate", return_value=False):
            with patch("chess_game.main.is_stalemate", return_value=True):
                msg = _game_over_message(board)
        assert msg is not None
        assert "Stalemate" in msg or "draw" in (msg or "").lower()

    def test_no_game_over(self) -> None:
        from chess_game.main import _game_over_message

        board = MagicMock()
        with patch("chess_game.main.is_checkmate", return_value=False):
            with patch("chess_game.main.is_stalemate", return_value=False):
                msg = _game_over_message(board)
        assert msg is None


# ---------- _game_loop integration tests ---------- #


class TestGameLoop:
    """Light integration tests for the interactive game loop."""

    def test_quit_command_exits_loop(self) -> None:
        # Mock Board + inputs so loop exits cleanly.
        with patch("chess_game.main.Board") as MockBoard, \
             patch("builtins.input", side_effect=["quit"]):
            # Ensure _game_loop completes without error.
            from chess_game.main import _game_loop

            _game_loop(MockBoard())

    def test_invalid_input_keeps_loop_running(self) -> None:
        from chess_game.main import _game_loop

        # First invalid move, then quit.
        inputs = ["badmove", "quit"]

        with patch("chess_game.main.Board") as MockBoard, \
             patch("builtins.input", side_effect=inputs):
            _game_loop(MockBoard())

    def test_checkmate_ends_loop(self) -> None:
        from chess_game.main import _game_loop

        board_mock = MagicMock()
        board_mock.turn = Color.WHITE

        # Simulate one move then checkmate detected.
        with patch("chess_game.main.Board"), \
             patch("builtins.input", side_effect=["e2e4"]), \
             patch("chess_game.main.is_checkmate", return_value=True):
            # make_move returns True once, then _game_over_message will end loop.
            board_mock.make_move.return_value = True
            _game_loop(board_mock)
