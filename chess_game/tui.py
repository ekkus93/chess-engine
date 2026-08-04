"""Text User Interface for the chess engine."""
from __future__ import annotations

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Label,
    RadioButton,
    RadioSet,
    Select,
)
from textual.widgets.select import NoSelection

from chess_game.chess import Color
from chess_game.tui_game import (
    EngineMoveMessage,
    GameScreen,
    ResignConfirmScreen,
    _GameConfig,
)

# Public facade: the game screen and its widgets moved into tui_game; re-export them
# so chess_game.tui.<name> keeps resolving for callers and tests.
__all__ = [
    "ChessApp",
    "EngineMoveMessage",
    "GameScreen",
    "MainMenuScreen",
    "ResignConfirmScreen",
    "_GameConfig",
    "main",
]


# ──────────────────────────── Main Menu ────────────────────────────


class MainMenuScreen(Screen):
    """Mode selection and game configuration."""

    DEFAULT_CSS = """
    MainMenuScreen {
        align: center middle;
    }
    #menu-box {
        width: 52;
        height: auto;
        border: round $accent;
        padding: 1 2;
    }
    #menu-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
    }
    .section-label {
        margin-top: 1;
    }
    #start-btn {
        margin-top: 2;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="menu-box"):
            yield Label("♟  Chess Engine", id="menu-title")

            yield Label("Mode:", classes="section-label")
            yield RadioSet(
                RadioButton("Human vs Engine", value=True, id="mode-human"),
                RadioButton("Self-play", id="mode-selfplay"),
                id="mode-radio",
            )

            with Vertical(id="config-human"):
                yield Label("Your color:", classes="section-label")
                yield RadioSet(
                    RadioButton("White", value=True, id="color-white"),
                    RadioButton("Black", id="color-black"),
                    id="color-radio",
                )
                yield Label("Engine depth (1–5):", classes="section-label")
                yield Select(
                    [(str(d), d) for d in range(1, 6)],
                    value=3,
                    allow_blank=False,
                    id="human-depth",
                )

            with Vertical(id="config-selfplay"):
                yield Label("White depth (1–5):", classes="section-label")
                yield Select(
                    [(str(d), d) for d in range(1, 6)],
                    value=3,
                    allow_blank=False,
                    id="white-depth",
                )
                yield Label("Black depth (1–5):", classes="section-label")
                yield Select(
                    [(str(d), d) for d in range(1, 6)],
                    value=3,
                    allow_blank=False,
                    id="black-depth",
                )

            yield Button("Start Game ▶", id="start-btn", variant="primary")

    def on_mount(self) -> None:
        """Set initial visibility of the mode-specific config panels."""
        self.query_one("#config-selfplay").display = False

    @on(RadioSet.Changed, "#mode-radio")
    def _on_mode_changed(self, event: RadioSet.Changed) -> None:
        """Toggle visibility between human and self-play config panels."""
        is_selfplay = event.pressed.id == "mode-selfplay"
        self.query_one("#config-human").display = not is_selfplay
        self.query_one("#config-selfplay").display = is_selfplay

    @on(Button.Pressed, "#start-btn")
    def _on_start(self) -> None:
        """Read configuration and push the GameScreen."""
        mode_radio = self.query_one("#mode-radio", RadioSet)
        is_selfplay = (
            mode_radio.pressed_button is not None
            and mode_radio.pressed_button.id == "mode-selfplay"
        )

        if not is_selfplay:
            color_radio = self.query_one("#color-radio", RadioSet)
            is_black = (
                color_radio.pressed_button is not None
                and color_radio.pressed_button.id == "color-black"
            )
            human_color = Color.BLACK if is_black else Color.WHITE
            raw = self.query_one("#human-depth", Select).value
            depth = 3 if isinstance(raw, NoSelection) else int(raw)
            cfg = _GameConfig(
                mode="human",
                human_color=human_color,
                engine_depth=depth,
                white_depth=depth,
                black_depth=depth,
            )
        else:
            wd = self.query_one("#white-depth", Select).value
            bd = self.query_one("#black-depth", Select).value
            cfg = _GameConfig(
                mode="selfplay",
                human_color=Color.WHITE,
                engine_depth=3,
                white_depth=3 if isinstance(wd, NoSelection) else int(wd),
                black_depth=3 if isinstance(bd, NoSelection) else int(bd),
            )
        self.app.push_screen(GameScreen(cfg))


# ──────────────────────────── App ──────────────────────────────────


class ChessApp(App):
    """Root Textual application."""

    TITLE = "Chess Engine"
    BINDINGS = [("q", "quit", "Quit")]

    def on_mount(self) -> None:
        """Push the main menu screen on startup."""
        self.push_screen(MainMenuScreen())


def main() -> None:
    """Launch the TUI."""
    ChessApp().run()


if __name__ == "__main__":
    main()
