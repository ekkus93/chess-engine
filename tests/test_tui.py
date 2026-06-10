"""Unit tests for chess_game.tui."""

from __future__ import annotations

import asyncio
import time

from textual.app import App, ComposeResult
from textual.widgets import RadioButton, RadioSet, Static

from chess_game.chess import Color
from chess_game.chess.ai_board_utils import get_legal_moves
from chess_game.chess.types import LegalMove, PieceType
from chess_game.tui import (
    ChessApp,
    EngineMoveMessage,
    GameScreen,
    MainMenuScreen,
    ResignConfirmScreen,
    _GameConfig,  # type: ignore[attr-defined]
)
from tests.helpers import sq


async def wait_until(predicate, *, timeout: float = 2.0, interval: float = 0.01) -> None:
    """Poll until predicate() is truthy or timeout elapses.

    Lets fast UI tests wait for an expected state transition instead of sleeping
    a fixed wall-clock duration. Returns as soon as the condition holds.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        await asyncio.sleep(interval)
    raise AssertionError("condition was not met before timeout")


def _fake_engine_first_legal_move(board, depth, position_counts=None, book_options=None):
    """Deterministic, instant fake for chess_game.tui.get_best_move.

    Returns the first legal move for the position so the engine reply is legal
    regardless of board state, without running a real search.
    """
    moves = get_legal_moves(board)
    return moves[0] if moves else None


# ---------------------------------------------------------------------------
# Helper: minimal app that pushes a depth-1 human game directly
# ---------------------------------------------------------------------------


class _HumanGameApp(App):
    """Test fixture: push GameScreen with human-vs-engine depth-1."""

    def on_mount(self) -> None:
        cfg = _GameConfig(
            mode="human",
            human_color=Color.WHITE,
            engine_depth=1,
            white_depth=1,
            black_depth=1,
        )
        self.push_screen(GameScreen(cfg))

    def compose(self) -> ComposeResult:  # pragma: no cover
        return super().compose()


# ---------------------------------------------------------------------------
# 6.2 ChessApp mounts without error
# ---------------------------------------------------------------------------


class TestAppMounts:
    """Verify ChessApp starts cleanly."""

    async def test_app_mounts_without_error(self) -> None:
        """ChessApp context opens without raising an exception."""
        async with ChessApp().run_test() as pilot:
            assert pilot.app is not None

    async def test_main_menu_screen_is_active(self) -> None:
        """After startup the active screen is MainMenuScreen."""
        async with ChessApp().run_test() as pilot:
            await pilot.pause()
            assert isinstance(pilot.app.screen, MainMenuScreen)


# ---------------------------------------------------------------------------
# 6.3 MainMenuScreen — initial widget visibility
# ---------------------------------------------------------------------------


class TestMainMenuScreenVisibility:
    """Tests for initial widget state in MainMenuScreen."""

    async def test_human_config_visible_by_default(self) -> None:
        """Human config panel is visible when the app starts."""
        async with ChessApp().run_test() as pilot:
            await pilot.pause()
            assert pilot.app.screen.query_one("#config-human").display is True

    async def test_selfplay_config_hidden_by_default(self) -> None:
        """Self-play config panel is hidden at startup."""
        async with ChessApp().run_test() as pilot:
            await pilot.pause()
            assert pilot.app.screen.query_one("#config-selfplay").display is False

    async def test_mode_radio_has_two_buttons(self) -> None:
        """The mode RadioSet contains exactly two RadioButton widgets."""
        async with ChessApp().run_test() as pilot:
            await pilot.pause()
            buttons = pilot.app.screen.query_one("#mode-radio", RadioSet).query(RadioButton)
            assert len(list(buttons)) == 2


# ---------------------------------------------------------------------------
# 6.4 MainMenuScreen — mode toggle
# ---------------------------------------------------------------------------


class TestMainMenuModeToggle:
    """Tests for toggling between human and self-play mode in the menu."""

    async def test_click_selfplay_shows_selfplay_config(self) -> None:
        """Clicking the Self-play button shows the self-play config panel."""
        async with ChessApp().run_test() as pilot:
            await pilot.pause()
            await pilot.click("#mode-selfplay")
            await pilot.pause()
            assert pilot.app.screen.query_one("#config-selfplay").display is True

    async def test_click_selfplay_hides_human_config(self) -> None:
        """Clicking the Self-play button hides the human config panel."""
        async with ChessApp().run_test() as pilot:
            await pilot.pause()
            await pilot.click("#mode-selfplay")
            await pilot.pause()
            assert pilot.app.screen.query_one("#config-human").display is False


# ---------------------------------------------------------------------------
# 6.5 MainMenuScreen — Start button pushes GameScreen
# ---------------------------------------------------------------------------


class TestStartButton:
    """Tests for the Start Game button navigating to GameScreen."""

    async def test_start_button_pushes_game_screen(self) -> None:
        """Clicking Start Game switches the active screen to GameScreen."""
        async with ChessApp().run_test() as pilot:
            await pilot.pause()
            await pilot.click("#start-btn")
            await pilot.pause()
            assert isinstance(pilot.app.screen, GameScreen)

    async def test_board_display_present_after_start(self) -> None:
        """After pushing GameScreen, a #board-display widget exists in the DOM."""
        async with ChessApp().run_test() as pilot:
            await pilot.pause()
            await pilot.click("#start-btn")
            await pilot.pause()
            assert pilot.app.screen.query_one("#board-display") is not None


# ---------------------------------------------------------------------------
# 6.6 GameScreen — board display renders
# ---------------------------------------------------------------------------


class TestBoardDisplay:
    """Tests for the board display widget in GameScreen."""

    async def test_board_display_non_empty(self) -> None:
        """The board display shows non-empty content after mounting."""
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            content = pilot.app.screen.query_one("#board-display", Static).content
            assert content != ""

    async def test_board_display_contains_rank_separator(self) -> None:
        """The board string contains '+---' rank separator markers."""
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            content = pilot.app.screen.query_one("#board-display", Static).content
            assert "+---" in content

    async def test_board_display_contains_both_kings(self) -> None:
        """The board display shows 'K' (White king) and 'k' (Black king)."""
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            content = pilot.app.screen.query_one("#board-display", Static).content
            assert "K" in content
            assert "k" in content


# ---------------------------------------------------------------------------
# 6.7 GameScreen — move list starts empty
# ---------------------------------------------------------------------------


class TestMoveListInitial:
    """Tests for the initial state of the move list widget."""

    async def test_move_list_shows_placeholder_at_start(self) -> None:
        """Move list displays placeholder text before any moves are made."""
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            content = pilot.app.screen.query_one("#move-list", Static).content
            assert "(no moves yet)" in content


# ---------------------------------------------------------------------------
# 6.8 GameScreen — human move input (happy path)
# ---------------------------------------------------------------------------


class TestHumanMoveInput:
    """Tests for submitting a valid human move."""

    async def test_human_move_pawn_lands_on_e4(self) -> None:
        """After typing 'e2e4', a White pawn occupies e4 on the board."""
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, GameScreen)
            await pilot.click("#move-input")
            await pilot.press("e", "2", "e", "4")
            await pilot.press("enter")
            # The human move is applied immediately; no need to wait for the engine.
            await pilot.pause()
            piece = screen._board.get_piece(sq("e4"))  # type: ignore[union-attr]
            assert piece is not None
            assert piece.kind == PieceType.PAWN
            assert piece.color == Color.WHITE

    async def test_human_move_appears_in_move_list(self) -> None:
        """Human move is recorded in the move list immediately after submission."""
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, GameScreen)
            await pilot.click("#move-input")
            await pilot.press("e", "2", "e", "4")
            await pilot.press("enter")
            await pilot.pause()
            # e2e4 must be in _move_strings right away (before engine responds)
            assert "e2e4" in screen._move_strings  # type: ignore[union-attr]

    async def test_move_list_shows_both_sides_after_engine_reply(self, monkeypatch) -> None:
        """After the engine replies, both the human move and engine move appear.

        Uses a deterministic instant fake engine and waits for the move-list
        state rather than sleeping for a real search.
        """
        monkeypatch.setattr(
            "chess_game.tui.get_best_move", _fake_engine_first_legal_move
        )
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, GameScreen)
            await pilot.click("#move-input")
            await pilot.press("e", "2", "e", "4")
            await pilot.press("enter")
            # Wait for the (faked) engine reply to be applied to the move list.
            await wait_until(lambda: len(screen._move_strings) >= 2)  # type: ignore[union-attr]
            # Both moves recorded: white at index 0, black at index 1
            assert len(screen._move_strings) >= 2  # type: ignore[union-attr]
            assert screen._move_strings[0] == "e2e4"  # type: ignore[union-attr]

    async def test_input_cleared_after_valid_move(self) -> None:
        """The move input field is empty after a valid move is submitted."""
        from textual.widgets import Input

        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            await pilot.click("#move-input")
            await pilot.press("e", "2", "e", "4")
            await pilot.press("enter")
            # Input is cleared on submission of the human move; no engine wait needed.
            await pilot.pause()
            input_val = pilot.app.screen.query_one("#move-input", Input).value
            assert input_val == ""


# ---------------------------------------------------------------------------
# 6.9 GameScreen — invalid move rejected
# ---------------------------------------------------------------------------


class TestInvalidMoveRejected:
    """Tests for submitting an illegal move."""

    async def test_illegal_move_does_not_change_turn(self) -> None:
        """Submitting 'e2e5' (illegal pawn jump) leaves the turn as WHITE."""
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, GameScreen)
            await pilot.click("#move-input")
            await pilot.press("e", "2", "e", "5")
            await pilot.press("enter")
            await pilot.pause()
            assert screen._board.turn == Color.WHITE  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# 6.10 GameScreen — thinking indicator
# ---------------------------------------------------------------------------


class TestThinkingIndicator:
    """Tests for the thinking indicator reactive."""

    async def test_thinking_row_hidden_when_not_thinking(self) -> None:
        """The thinking-row is hidden when _thinking is False."""
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            assert not pilot.app.screen.query_one("#thinking-row").has_class("active")

    async def test_thinking_row_visible_when_thinking(self) -> None:
        """Setting _thinking = True makes the thinking-row visible."""
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, GameScreen)
            screen._thinking = True  # type: ignore[union-attr]
            await pilot.pause()
            assert pilot.app.screen.query_one("#thinking-row").has_class("active")


# ---------------------------------------------------------------------------
# 6.11 GameScreen — resign button
# ---------------------------------------------------------------------------


class TestResignButton:
    """Tests for the human resign action (requires confirmation dialog)."""

    async def test_resign_shows_confirm_modal(self) -> None:
        """Clicking Resign pushes the confirmation modal before ending the game."""
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            game_screen = pilot.app.screen
            assert isinstance(game_screen, GameScreen)
            await pilot.click("#resign-btn")
            await pilot.pause()
            assert isinstance(pilot.app.screen, ResignConfirmScreen)
            assert game_screen._game_over is False  # type: ignore[union-attr]

    async def test_resign_cancel_does_not_end_game(self) -> None:
        """Clicking Cancel on the confirm modal leaves the game running."""
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            game_screen = pilot.app.screen
            assert isinstance(game_screen, GameScreen)
            await pilot.click("#resign-btn")
            await pilot.pause()
            await pilot.click("#confirm-no")
            await pilot.pause()
            assert isinstance(pilot.app.screen, GameScreen)
            assert game_screen._game_over is False  # type: ignore[union-attr]

    async def test_resign_confirm_sets_game_over(self) -> None:
        """Clicking 'Yes, resign' in the modal sets _game_over to True."""
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            game_screen = pilot.app.screen
            assert isinstance(game_screen, GameScreen)
            await pilot.click("#resign-btn")
            await pilot.pause()
            await pilot.click("#confirm-yes")
            await pilot.pause()
            assert game_screen._game_over is True  # type: ignore[union-attr]

    async def test_gameover_panel_visible_after_resign(self) -> None:
        """The game-over panel becomes visible after confirming resignation."""
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            game_screen = pilot.app.screen
            await pilot.click("#resign-btn")
            await pilot.pause()
            await pilot.click("#confirm-yes")
            await pilot.pause()
            assert game_screen.query_one("#gameover-panel").has_class("active")

    async def test_resign_message_contains_wins(self) -> None:
        """The game-over message mentions who wins after confirming resignation."""
        async with _HumanGameApp().run_test() as pilot:
            await pilot.pause()
            game_screen = pilot.app.screen
            assert isinstance(game_screen, GameScreen)
            await pilot.click("#resign-btn")
            await pilot.pause()
            await pilot.click("#confirm-yes")
            await pilot.pause()
            msg = game_screen.query_one("#gameover-msg", Static).content
            assert "wins" in msg or "resign" in msg.lower()


# ---------------------------------------------------------------------------
# 6.15 _format_move_list — unit test (no TUI harness)
# ---------------------------------------------------------------------------


class TestFormatMoveList:
    """Tests for GameScreen._format_move_list (no app context needed)."""

    def _make_screen(self) -> GameScreen:
        cfg = _GameConfig("human", Color.WHITE, 1, 1, 1)
        return GameScreen(cfg)

    def test_empty_move_list_returns_empty_string(self) -> None:
        """No moves → empty string (placeholder shown separately by _refresh_display)."""
        screen = self._make_screen()
        assert screen._format_move_list() == ""

    def test_single_white_move(self) -> None:
        """One move (White only) formats as '  1. e2e4'."""
        screen = self._make_screen()
        screen._move_strings = ["e2e4"]
        result = screen._format_move_list()
        assert "1" in result
        assert "e2e4" in result

    def test_two_moves_same_line(self) -> None:
        """White and Black move on move 1 appear on the same line."""
        screen = self._make_screen()
        screen._move_strings = ["e2e4", "e7e5"]
        result = screen._format_move_list()
        assert "e2e4" in result
        assert "e7e5" in result
        assert result.count("\n") == 0

    def test_three_moves_spans_two_lines(self) -> None:
        """Three moves produce two lines (move 1 complete, move 2 partial)."""
        screen = self._make_screen()
        screen._move_strings = ["e2e4", "e7e5", "g1f3"]
        result = screen._format_move_list()
        lines = result.strip().splitlines()
        assert len(lines) == 2
        assert "g1f3" in lines[1]


# ---------------------------------------------------------------------------
# 6.16 EngineMoveMessage — typing
# ---------------------------------------------------------------------------


class TestEngineMoveMessage:
    """Tests for the EngineMoveMessage message class."""

    def test_none_move(self) -> None:
        """EngineMoveMessage with move=None stores None."""
        msg = EngineMoveMessage(move=None)
        assert msg.move is None

    def test_with_legal_move(self) -> None:
        """EngineMoveMessage stores a LegalMove correctly."""
        lm = LegalMove(start=sq("e2"), end=sq("e4"), promotion=None)
        msg = EngineMoveMessage(move=lm)
        assert msg.move is lm
