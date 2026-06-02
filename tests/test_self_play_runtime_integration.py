"""Integration tests for self-play runtime, timeout handling, and option propagation."""

import signal

import chess_game.self_play as self_play_module
from chess_game.chess.board import Board
from chess_game.chess.coords import algebraic_to_index
from chess_game.chess.opening_book import OpeningBook
from chess_game.chess.types import Color, LegalMove, PieceType
from chess_game.self_play import (
    _MoveSelectionParams,
    _SelfPlayOptions,
    _get_best_move_with_timeout,
    run_self_play,
)


def _legal_move(start: str, end: str, promotion: PieceType | None = None) -> LegalMove:
    return LegalMove(
        start=algebraic_to_index(start),
        end=algebraic_to_index(end),
        promotion=promotion,
    )


class TestSelfPlayTimeoutHandling:
    """Test self-play timeout mechanism and cleanup."""

    def test_timeout_returns_none(self, monkeypatch):
        """Verify that timeout during move selection returns None."""
        board = Board()
        params = _MoveSelectionParams(
            board=board,
            depth=2,
            timeout=1.0,
            position_counts=None,
            use_opening_book=False,
        )
        handler = {}

        def fake_signal(_sig, callback):
            handler["callback"] = callback
            return object()

        def fake_alarm(seconds):
            if seconds:
                pass

        def fake_get_best_move(_board, **kwargs):
            del kwargs
            handler["callback"](signal.SIGALRM, None)

        monkeypatch.setattr(self_play_module.signal, "signal", fake_signal)
        monkeypatch.setattr(self_play_module.signal, "alarm", fake_alarm)
        monkeypatch.setattr(self_play_module, "get_best_move", fake_get_best_move)

        assert _get_best_move_with_timeout(params) is None

    def test_non_timeout_returns_legal_move(self, monkeypatch):
        """Verify that the non-timeout path returns the search result."""
        board = Board()
        expected = _legal_move("e2", "e4")
        captured = {}

        def fake_get_best_move(board_arg, **kwargs):
            captured["board"] = board_arg
            captured["depth"] = kwargs["depth"]
            captured["position_counts"] = kwargs["position_counts"]
            captured["book_options"] = kwargs["book_options"]
            return expected

        monkeypatch.setattr(self_play_module, "get_best_move", fake_get_best_move)

        params = _MoveSelectionParams(
            board=board,
            depth=2,
            timeout=None,
            position_counts={"pos": 1},
            use_opening_book=False,
        )

        result = _get_best_move_with_timeout(params)
        assert result == expected
        assert captured["board"] is board
        assert captured["depth"] == 2
        assert captured["position_counts"] == {"pos": 1}


class TestSelfPlayBoardStateIntegrity:
    """Test that self-play maintains board state consistency."""

    def test_self_play_applies_one_move(self, monkeypatch):
        """Verify self-play can apply a move and update board state."""
        board = Board()
        move = _legal_move("e2", "e4")

        def fake_board_factory():
            return board

        def fake_get_best_move(_board, **kwargs):
            del kwargs
            return move

        def fake_terminal_message(_board, _counts):
            del _counts
            return None if board.turn == Color.WHITE else "done"

        monkeypatch.setattr(self_play_module, "Board", fake_board_factory)
        monkeypatch.setattr(self_play_module, "get_best_move", fake_get_best_move)
        monkeypatch.setattr(self_play_module, "terminal_message", fake_terminal_message)

        run_self_play(1, 1, _SelfPlayOptions(max_moves=1, verbose=False, use_opening_book=False))

        assert board.turn == Color.BLACK
        assert board.en_passant_target == algebraic_to_index("e3")
        assert board.halfmove_clock == 0

    def test_self_play_stops_cleanly_without_move(self, monkeypatch):
        """Verify self-play exits cleanly when no move is available."""
        board = Board()

        def fake_board_factory():
            return board

        def fake_get_best_move(_board, **kwargs):
            del kwargs
            pass

        def fake_terminal_message(_board, _counts):
            del _counts
            pass

        monkeypatch.setattr(self_play_module, "Board", fake_board_factory)
        monkeypatch.setattr(self_play_module, "get_best_move", fake_get_best_move)
        monkeypatch.setattr(self_play_module, "terminal_message", fake_terminal_message)

        run_self_play(1, 1, _SelfPlayOptions(max_moves=1, verbose=False, use_opening_book=False))

        assert board.turn == Color.WHITE
        assert board.en_passant_target is None


class TestSelfPlayOpeningBookPropagation:
    """Test that opening-book options propagate through self-play runtime."""

    def test_opening_book_option_propagates_to_search(self, monkeypatch):
        """Verify use_opening_book flag is respected in move selection."""
        board = Board()
        expected = _legal_move("e2", "e4")
        captured = {}

        def fake_get_best_move(board_arg, **kwargs):
            captured["board"] = board_arg
            captured["book_options"] = kwargs["book_options"]
            return expected

        monkeypatch.setattr(self_play_module, "get_best_move", fake_get_best_move)

        params = _MoveSelectionParams(
            board=board,
            depth=2,
            timeout=None,
            position_counts=None,
            use_opening_book=False,
            opening_book=None,
        )

        result = _get_best_move_with_timeout(params)
        assert result == expected
        assert captured["board"] is board
        assert captured["book_options"].use_opening_book is False
        assert captured["book_options"].opening_book is None

    def test_custom_opening_book_passed_through(self, monkeypatch):
        """Verify custom opening book object is passed to search."""
        board = Board()
        book = OpeningBook.bundled()
        expected = _legal_move("e2", "e4")
        captured = {}

        def fake_get_best_move(board_arg, **kwargs):
            del board_arg
            captured["book_options"] = kwargs["book_options"]
            return expected

        monkeypatch.setattr(self_play_module, "get_best_move", fake_get_best_move)

        params = _MoveSelectionParams(
            board=board,
            depth=2,
            timeout=None,
            position_counts=None,
            use_opening_book=True,
            opening_book=book,
        )

        result = _get_best_move_with_timeout(params)
        assert result == expected
        assert captured["book_options"].use_opening_book is True
        assert captured["book_options"].opening_book is book


class TestSelfPlayOptionsStructure:
    """Test that _SelfPlayOptions dataclass handles parameter propagation."""

    def test_self_play_options_defaults(self):
        """Verify _SelfPlayOptions has sensible defaults."""
        opts = _SelfPlayOptions()

        assert opts.max_moves == 1000
        assert opts.verbose is True
        assert opts.use_opening_book is True
        assert opts.opening_book is None

    def test_self_play_options_custom_values(self):
        """Verify _SelfPlayOptions accepts custom values."""
        book = OpeningBook.bundled()
        opts = _SelfPlayOptions(
            max_moves=50,
            verbose=False,
            use_opening_book=False,
            opening_book=book,
        )

        assert opts.max_moves == 50
        assert opts.verbose is False
        assert opts.use_opening_book is False
        assert opts.opening_book is book


class TestSelfPlayMoveSelectionParams:
    """Test that _MoveSelectionParams encapsulates move selection context."""

    def test_move_selection_params_with_position_counts(self):
        """Verify position counts are passed and accessible."""
        board = Board()
        counts = {"position_key_1": 1, "position_key_2": 2}

        params = _MoveSelectionParams(
            board=board,
            depth=2,
            timeout=None,
            position_counts=counts,
            use_opening_book=False,
        )

        assert params.position_counts == counts
        assert params.depth == 2

    def test_move_selection_params_no_position_counts(self):
        """Verify position counts default to None."""
        board = Board()

        params = _MoveSelectionParams(
            board=board,
            depth=2,
            timeout=None,
        )

        assert params.position_counts is None


class TestSelfPlayRuntimeOptionsIntegration:
    """Test runtime option propagation through self-play layers."""

    def test_book_disabled_in_non_timeout_path(self, monkeypatch):
        """Verify book-disabled flag works in standard path."""
        board = Board()
        expected = _legal_move("e2", "e4")

        def fake_get_best_move(board_arg, **kwargs):
            del board_arg
            assert kwargs["book_options"].use_opening_book is False
            return expected

        monkeypatch.setattr(self_play_module, "get_best_move", fake_get_best_move)

        params = _MoveSelectionParams(
            board=board,
            depth=2,
            timeout=None,
            use_opening_book=False,
        )

        result = _get_best_move_with_timeout(params)
        assert result == expected

    def test_book_enabled_in_non_timeout_path(self, monkeypatch):
        """Verify book-enabled flag works in standard path."""
        board = Board()
        expected = _legal_move("e2", "e4")

        def fake_get_best_move(board_arg, **kwargs):
            del board_arg
            assert kwargs["book_options"].use_opening_book is True
            assert kwargs["book_options"].opening_book is not None
            return expected

        monkeypatch.setattr(self_play_module, "get_best_move", fake_get_best_move)

        params = _MoveSelectionParams(
            board=board,
            depth=2,
            timeout=None,
            use_opening_book=True,
            opening_book=OpeningBook.bundled(),
        )

        result = _get_best_move_with_timeout(params)
        assert result == expected
