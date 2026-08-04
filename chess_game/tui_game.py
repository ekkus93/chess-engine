"""Game-play TUI screen and its supporting widgets.

Extracted from ``tui``. Holds the in-game ``GameScreen`` plus the pieces it depends
on (the rich board renderer, the game-config dataclass, the engine-move message and
the resign-confirm modal). ``tui`` keeps the menu screen / app shell and re-imports
these (re-exporting the public ones) so existing imports keep working.
"""

from __future__ import annotations

import dataclasses
import datetime
import threading
from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    LoadingIndicator,
    Static,
)

from chess_game.chess import Board, Color, PieceType
from chess_game.chess.ai import BestMoveOptions, get_best_move
from chess_game.chess.board.game_state import (
    is_in_check,
    record_position,
    terminal_message,
)
from chess_game.chess.coords import index_to_algebraic
from chess_game.chess.move import parse_move_notation
from chess_game.chess.types import LegalMove
from chess_game.texel.game_result import outcome_from_message
from chess_game.texel.online_learning import (
    OnlineLearningConfig,
    record_game_and_update_weights,
)
from chess_game.texel.position_db import GameRecord
from chess_game.texel.weights_io import TUNED_WEIGHTS_PATH

_SKIP_OPENING_PLIES = 10
_WHITE_PIECE_STYLE = "bold yellow"
_BLACK_PIECE_STYLE = "bold cyan"
# Detect at import time whether tuned weights are available.
_ENGINE_LABEL = "Engine: tuned" if TUNED_WEIGHTS_PATH.exists() else "Engine: default"


def _render_board_rich(board: Board) -> str:
    """Return the board as a Rich-markup string with colored piece letters."""
    sep = "  +---+---+---+---+---+---+---+---+"
    lines = ["    a   b   c   d   e   f   g   h", sep]
    for row_index, row in enumerate(board.board):
        rank = 8 - row_index
        cells = []
        for piece in row:
            if piece is None:
                cells.append("   ")
            else:
                sym = piece.kind.name[0]
                if piece.kind == PieceType.KNIGHT:
                    sym = "N"
                style = (
                    _WHITE_PIECE_STYLE
                    if piece.color == Color.WHITE
                    else _BLACK_PIECE_STYLE
                )
                if piece.color == Color.BLACK:
                    sym = sym.lower()
                cells.append(f" [{style}]{sym}[/{style}] ")
        lines.append(f"{rank} |{'|'.join(cells)}|")
        lines.append(sep)
    lines.append(f"  Turn: {board.turn.name.upper()}")
    return "\n".join(lines)

@dataclasses.dataclass
class _GameConfig:
    """Immutable game configuration passed to GameScreen."""

    mode: str
    human_color: Color
    engine_depth: int
    white_depth: int
    black_depth: int

class EngineMoveMessage(Message):
    """Carries a computed engine move from the worker thread to the main thread."""

    def __init__(self, move: LegalMove | None) -> None:
        super().__init__()
        self.move: LegalMove | None = move

class ResignConfirmScreen(ModalScreen[bool]):
    """Modal asking the user to confirm resignation before acting."""

    DEFAULT_CSS = """
    ResignConfirmScreen {
        align: center middle;
    }
    ResignConfirmScreen > Vertical {
        background: $surface;
        border: solid $error;
        padding: 1 2;
        width: 44;
        height: auto;
    }
    ResignConfirmScreen #confirm-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
    }
    ResignConfirmScreen #confirm-body {
        text-align: center;
        margin-bottom: 1;
        width: 100%;
    }
    ResignConfirmScreen Horizontal {
        align: center middle;
        height: auto;
    }
    ResignConfirmScreen Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Resign?", id="confirm-title")
            yield Static("Are you sure you want to resign?", id="confirm-body")
            with Horizontal():
                yield Button("Yes, resign", variant="error", id="confirm-yes")
                yield Button("Cancel", variant="primary", id="confirm-no")

    @on(Button.Pressed, "#confirm-yes")
    def _on_yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#confirm-no")
    def _on_no(self) -> None:
        self.dismiss(False)

class GameScreen(Screen):
    """Main game screen for both human-vs-engine and self-play modes."""

    DEFAULT_CSS = """
    GameScreen {
        layout: vertical;
    }
    #game-layout {
        height: 1fr;
        layout: horizontal;
    }
    #board-pane {
        width: 44;
        padding: 0 1;
        layout: vertical;
    }
    #board-display {
        height: 20;
    }
    #status-bar {
        height: 1;
        padding: 0 1;
        background: $surface;
    }
    #thinking-row {
        height: 3;
        layout: horizontal;
        display: none;
    }
    #thinking-row.active {
        display: block;
    }
    #thinking-indicator {
        width: 3;
        height: 1;
    }
    #thinking-label {
        padding: 1 0 1 1;
    }
    #human-controls {
        height: 3;
        layout: horizontal;
        display: none;
    }
    #human-controls.active {
        display: block;
    }
    #move-input {
        width: 1fr;
    }
    #resign-btn {
        width: 12;
    }
    #selfplay-controls {
        height: 3;
        layout: horizontal;
        display: none;
    }
    #selfplay-controls.active {
        display: block;
    }
    #toggle-btn {
        width: 14;
    }
    #step-btn {
        width: 10;
    }
    #move-pane {
        width: 1fr;
        border-left: solid $accent;
        padding: 0 1;
    }
    #move-list {
        height: auto;
    }
    #gameover-panel {
        height: auto;
        padding: 1 2;
        background: $surface-darken-1;
        border-top: solid $success;
        display: none;
    }
    #gameover-panel.active {
        display: block;
    }
    #gameover-msg {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
    }
    #save-row {
        layout: horizontal;
        height: 3;
        display: none;
    }
    #save-row.active {
        display: block;
    }
    #save-filename {
        width: 1fr;
    }
    #save-confirm-btn {
        width: 10;
    }
    #gameover-btns {
        layout: horizontal;
        height: 3;
        align: center middle;
    }
    #save-game-btn {
        margin: 0 1;
        width: 16;
    }
    #menu-btn {
        margin: 0 1;
        width: 16;
    }
    """

    _thinking: reactive[bool] = reactive(False)

    def __init__(self, config: _GameConfig) -> None:
        super().__init__()
        self._config = config
        self._board = Board()
        self._position_counts: dict[str, int] = {}
        self._move_strings: list[str] = []
        self._board_fens: list[str] = []
        self._game_over = False
        self._auto_play = True
        record_position(self._board, self._position_counts)

    # ── Compose ──────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="game-layout"):
            with Vertical(id="board-pane"):
                yield Static("", id="board-display")
                yield Static("", id="status-bar")
                with Horizontal(id="thinking-row"):
                    yield LoadingIndicator(id="thinking-indicator")
                    yield Label(" Thinking...", id="thinking-label")
                with Horizontal(id="human-controls"):
                    yield Input(placeholder="e2e4  (or 'resign')", id="move-input")
                    yield Button("Resign", id="resign-btn", variant="error")
                with Horizontal(id="selfplay-controls"):
                    yield Button("⏸ Pause", id="toggle-btn")
                    yield Button("▶ Step", id="step-btn", disabled=True)
            with ScrollableContainer(id="move-pane"):
                yield Static("", id="move-list")
        with Vertical(id="gameover-panel"):
            yield Static("", id="gameover-msg")
            with Horizontal(id="gameover-btns"):
                yield Button("💾 Save Game", id="save-game-btn", variant="primary")
                yield Button("⬅  Main Menu", id="menu-btn")
            with Horizontal(id="save-row"):
                yield Input(
                    placeholder="game_2026-06-05.txt",
                    id="save-filename",
                )
                yield Button("Save", id="save-confirm-btn", variant="success")
        yield Footer()

    # ── Lifecycle ─────────────────────────────────────────────────

    def on_mount(self) -> None:
        """Initialise display and kick off the first engine move if needed."""
        self._refresh_display()
        if self._config.mode == "selfplay":
            self.query_one("#selfplay-controls").add_class("active")
            self._trigger_engine_move()
        else:
            # Human mode: show controls on human's turn
            self._update_human_controls()
            if self._board.turn != self._config.human_color:
                self._trigger_engine_move()

    # ── Display ───────────────────────────────────────────────────

    def _refresh_display(self) -> None:
        self.query_one("#board-display", Static).update(
            _render_board_rich(self._board)
        )
        self.query_one("#move-list", Static).update(
            self._format_move_list() or "(no moves yet)"
        )
        move_pane = self.query_one("#move-pane", ScrollableContainer)
        move_pane.scroll_end(animate=False)
        self._update_status()

    def _format_move_list(self) -> str:
        """Format self._move_strings as a numbered move list."""
        lines = []
        for i in range(0, len(self._move_strings), 2):
            move_num = i // 2 + 1
            white_mv = self._move_strings[i]
            black_mv = self._move_strings[i + 1] if i + 1 < len(self._move_strings) else ""
            lines.append(f"{move_num:3}. {white_mv:<8}{black_mv}")
        return "\n".join(lines)

    def _update_status(self) -> None:
        if self._game_over:
            status = ""
        elif self._thinking:
            color = self._board.turn.name.capitalize()
            status = f"  {color} is thinking...  [{_ENGINE_LABEL}]"
        elif is_in_check(self._board, self._board.turn):
            color = self._board.turn.name.capitalize()
            status = f"  {color} is in CHECK!  [{_ENGINE_LABEL}]"
        else:
            color = self._board.turn.name.capitalize()
            if self._config.mode == "human":
                if self._board.turn == self._config.human_color:
                    status = f"  Your turn ({color})  [{_ENGINE_LABEL}]"
                else:
                    status = f"  Engine ({color}) to move  [{_ENGINE_LABEL}]"
            else:
                status = f"  {color} to move  [{_ENGINE_LABEL}]"
        self.query_one("#status-bar", Static).update(status)

    def _update_human_controls(self) -> None:
        is_human_turn = (
            not self._game_over
            and not self._thinking
            and self._board.turn == self._config.human_color
        )
        ctrls = self.query_one("#human-controls")
        if is_human_turn:
            ctrls.add_class("active")
            self.query_one("#move-input", Input).focus()
        else:
            ctrls.remove_class("active")

    # ── Thinking indicator ────────────────────────────────────────

    def watch__thinking(self, thinking: bool) -> None:
        """Show or hide the thinking indicator when the reactive changes."""
        row = self.query_one("#thinking-row")
        if thinking:
            row.add_class("active")
        else:
            row.remove_class("active")
        self._update_status()

    def _start_thinking(self) -> None:
        self._thinking = True
        if self._config.mode == "human":
            self.query_one("#human-controls").remove_class("active")

    def _stop_thinking(self) -> None:
        self._thinking = False

    # ── Engine worker ─────────────────────────────────────────────

    def _current_depth(self) -> int:
        if self._config.mode == "human":
            return self._config.engine_depth
        if self._board.turn == Color.WHITE:
            return self._config.white_depth
        return self._config.black_depth

    def _trigger_engine_move(self) -> None:
        if self._game_over:
            return
        self._start_thinking()
        self._run_engine()

    @work(thread=True)
    def _run_engine(self) -> None:
        board_copy = self._board.clone()
        depth = self._current_depth()
        pos_counts = dict(self._position_counts)
        move = get_best_move(
            board_copy,
            depth,
            position_counts=pos_counts,
            book_options=BestMoveOptions(random_opening_book=True),
        )
        self.post_message(EngineMoveMessage(move))

    @on(EngineMoveMessage)
    def _on_engine_move(self, event: EngineMoveMessage) -> None:
        self._stop_thinking()
        lm = event.move
        if lm is None or self._game_over:
            return
        self._apply_move(lm.start, lm.end, lm.promotion)
        if not self._game_over:
            if self._config.mode == "selfplay":
                if self._auto_play:
                    self._trigger_engine_move()
                else:
                    self.query_one("#step-btn").disabled = False
            else:
                self._update_human_controls()

    # ── Move application ──────────────────────────────────────────

    def _apply_move(self, start, end, promotion=None) -> None:
        success = self._board.make_move(start, end, promotion=promotion)
        if not success:
            return
        move_str = index_to_algebraic(start) + index_to_algebraic(end)
        if promotion is not None:
            move_str += promotion.name.lower()[0]
        self._move_strings.append(move_str)
        record_position(self._board, self._position_counts)
        # Collect post-move FEN for online learning (skip the opening book phase).
        if len(self._move_strings) > _SKIP_OPENING_PLIES:
            self._board_fens.append(self._board.to_fen())
        self._refresh_display()
        self._check_game_over()

    def _check_game_over(self) -> None:
        msg = terminal_message(self._board, self._position_counts)
        if msg:
            self._game_over = True
            self._update_status()
            panel = self.query_one("#gameover-panel")
            panel.add_class("active")
            self.query_one("#gameover-msg", Static).update(msg)
            if self._config.mode == "human":
                self.query_one("#human-controls").remove_class("active")
            else:
                self.query_one("#selfplay-controls").remove_class("active")
                self._trigger_online_learning(msg)

    def _trigger_online_learning(self, result_message: str) -> None:
        """Start a background thread to update weights from this self-play game."""
        outcome = outcome_from_message(result_message)
        if outcome is None or not self._board_fens:
            return
        fens = list(self._board_fens)
        record = GameRecord(positions=fens, outcome=outcome)
        cfg = OnlineLearningConfig()

        def _learn() -> None:
            record_game_and_update_weights(record, cfg)

        thread = threading.Thread(target=_learn, daemon=True)
        thread.start()

    # ── Human mode input ──────────────────────────────────────────

    @on(Input.Submitted, "#move-input")
    def _on_move_submitted(self, event: Input.Submitted) -> None:
        if self._game_over or self._thinking:
            return
        if self._config.mode != "human" or self._board.turn != self._config.human_color:
            return
        raw = event.value.strip()
        event.input.clear()
        if raw.lower() == "resign":
            self.app.push_screen(ResignConfirmScreen(), self._on_resign_confirmed)
            return
        try:
            move = parse_move_notation(raw)
        except ValueError as exc:
            self.query_one("#status-bar", Static).update(
                f"  [red]Invalid: {exc}[/red]"
            )
            return
        ok = self._board.make_move(move.start, move.end, promotion=move.promotion)
        if not ok:
            self.query_one("#status-bar", Static).update(
                f"  [red]Illegal move: {raw}[/red]"
            )
            return
        move_str = index_to_algebraic(move.start) + index_to_algebraic(move.end)
        if move.promotion is not None:
            move_str += move.promotion.name.lower()[0]
        self._move_strings.append(move_str)
        record_position(self._board, self._position_counts)
        self._refresh_display()
        self._check_game_over()
        if not self._game_over:
            self._trigger_engine_move()

    def _on_resign(self) -> None:
        """Handle human resignation — declare the opponent the winner."""
        self._game_over = True
        color = self._config.human_color.name.capitalize()
        winner = "Black" if self._config.human_color == Color.WHITE else "White"
        msg = f"{color} resigns. {winner} wins."
        panel = self.query_one("#gameover-panel")
        panel.add_class("active")
        self.query_one("#gameover-msg", Static).update(msg)
        self.query_one("#human-controls").remove_class("active")
        self._update_status()

    @on(Button.Pressed, "#resign-btn")
    def _on_resign_btn(self) -> None:
        self.app.push_screen(ResignConfirmScreen(), self._on_resign_confirmed)

    def _on_resign_confirmed(self, confirmed: bool | None) -> None:
        if confirmed:
            self._on_resign()

    # ── Self-play controls ────────────────────────────────────────

    @on(Button.Pressed, "#toggle-btn")
    def _on_toggle(self) -> None:
        self._auto_play = not self._auto_play
        btn = self.query_one("#toggle-btn", Button)
        step_btn = self.query_one("#step-btn", Button)
        if self._auto_play:
            btn.label = "⏸ Pause"
            step_btn.disabled = True
            if not self._thinking and not self._game_over:
                self._trigger_engine_move()
        else:
            btn.label = "▶ Resume"
            step_btn.disabled = self._thinking

    @on(Button.Pressed, "#step-btn")
    def _on_step(self) -> None:
        if self._game_over or self._thinking:
            return
        self.query_one("#step-btn").disabled = True
        self._trigger_engine_move()

    # ── Post-game actions ─────────────────────────────────────────

    @on(Button.Pressed, "#save-game-btn")
    def _on_save_game(self) -> None:
        save_row = self.query_one("#save-row")
        save_row.toggle_class("active")
        if "active" in save_row.classes:
            default = f"game_{datetime.date.today()}.txt"
            inp = self.query_one("#save-filename", Input)
            if not inp.value:
                inp.value = default
            inp.focus()

    @on(Button.Pressed, "#save-confirm-btn")
    def _on_save_confirm(self) -> None:
        filename = self.query_one("#save-filename", Input).value.strip()
        if not filename:
            filename = f"game_{datetime.date.today()}.txt"
        self._write_game_file(filename)
        self.query_one("#save-row").remove_class("active")
        self.query_one("#save-game-btn", Button).label = "✓ Saved"
        self.query_one("#save-game-btn").disabled = True

    @on(Button.Pressed, "#menu-btn")
    def _on_menu(self) -> None:
        self.app.pop_screen()

    def _write_game_file(self, filename: str) -> None:
        path = Path(filename)
        lines = [
            f"Date: {datetime.date.today()}",
            f"Mode: {self._config.mode}",
        ]
        if self._config.mode == "human":
            lines.append(
                f"Human: {self._config.human_color.name.capitalize()}"
                f"  Engine depth: {self._config.engine_depth}"
            )
        else:
            lines.append(
                f"White depth: {self._config.white_depth}  "
                f"Black depth: {self._config.black_depth}"
            )
        lines.append("")
        move_list = self._format_move_list()
        if move_list:
            lines.extend(move_list.splitlines())
        lines.append("")
        result = terminal_message(self._board, self._position_counts) or "(resigned)"
        lines.append(result)
        path.write_text("\n".join(lines), encoding="utf-8")
        self.notify(f"Game saved to {path.resolve()}", severity="information")
