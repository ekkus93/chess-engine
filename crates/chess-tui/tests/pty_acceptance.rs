//! Additional PTY-driven regression coverage for `chess-tui`.
//!
//! This drives the real compiled binary through an OS pseudo-terminal —
//! catching real terminal-lifecycle behavior (alternate-screen enter/leave,
//! raw-mode key decoding, real process exit) that the in-process
//! `ratatui::backend::TestBackend` unit tests cannot exercise.
//!
//! This is **additional automated evidence, not a replacement** for the
//! Phase 12 manual real-terminal acceptance items in
//! `docs/RUST_TUI_TODO.md`. `docs/RUST_TUI_RALPH_STATUS.md` records that
//! those items "intentionally remain human-operated and are not satisfied
//! by headless/unit/PTY automation" — a scripted keystroke sequence proves
//! the code behaves mechanically correctly, not that a human's actual
//! experience in a real terminal emulator is sound. All tests here are
//! `#[ignore]`d by default; run them explicitly with
//! `bash scripts/dev.sh tui-pty-smoke`.

use std::{
    io::{Read, Write},
    sync::mpsc,
    thread,
    time::{Duration, Instant},
};

use portable_pty::{native_pty_system, Child, CommandBuilder, MasterPty, PtySize};

/// How long to wait for expected output before failing. Generous because
/// this spawns a real process and waits on real search threads (depth-1
/// searches complete quickly, but CI/dev machines vary).
const WAIT_TIMEOUT: Duration = Duration::from_secs(15);
const POLL_INTERVAL: Duration = Duration::from_millis(20);

/// Raw bytes a real terminal sends for keys that aren't a single ASCII
/// character. Crossterm decodes these from raw mode input exactly as a real
/// terminal driver would emit them. Plain character keys (including menu
/// shortcuts like `'q'`/`'r'`/`'v'`) are sent via `PtySession::key_char`
/// rather than listed here, since any ASCII byte already works that way.
mod keys {
    pub const ENTER: &[u8] = b"\r";
    pub const ESC: &[u8] = b"\x1b";
    pub const BACKSPACE: &[u8] = b"\x7f";
    pub const DOWN: &[u8] = b"\x1b[B";
    pub const RIGHT: &[u8] = b"\x1b[C";
}

struct PtySession {
    master: Box<dyn MasterPty + Send>,
    writer: Box<dyn Write + Send>,
    output: mpsc::Receiver<Vec<u8>>,
    /// Reconstructs the actual screen grid from the raw byte stream (cursor
    /// moves, alternate-screen switches, etc.) — see the module-level
    /// comment on `vt100` above for why this is necessary rather than
    /// substring-matching the raw stream directly.
    parser: vt100::Parser,
    /// The full raw byte stream, kept alongside `parser` for the one thing
    /// screen-content assertions can't check: whether a specific literal
    /// escape sequence (alternate-screen enter/leave) was ever emitted.
    /// Unlike rendered text, an exact escape sequence isn't subject to the
    /// cursor-skip optimization, so literal substring matching is correct
    /// here — it's rendered *content* that needs the emulator.
    raw: Vec<u8>,
    child: Box<dyn Child + Send + Sync>,
}

impl PtySession {
    /// Spawns `chess-tui` (built by `cargo test`'s own build of this crate's
    /// binary target) attached to a fresh PTY of the given size.
    fn spawn(cols: u16, rows: u16) -> Self {
        let pty_system = native_pty_system();
        let pair = pty_system
            .openpty(PtySize {
                rows,
                cols,
                pixel_width: 0,
                pixel_height: 0,
            })
            .expect("openpty succeeds");

        let cmd = CommandBuilder::new(env!("CARGO_BIN_EXE_chess-tui"));
        let child = pair
            .slave
            .spawn_command(cmd)
            .expect("chess-tui spawns under the pty");
        // The child owns the slave end now; drop our handle so the parent
        // doesn't also hold it open (standard portable-pty usage).
        drop(pair.slave);

        let writer = pair.master.take_writer().expect("pty writer available");
        let mut reader = pair
            .master
            .try_clone_reader()
            .expect("pty reader available");

        // Read on a background thread and stream raw chunks back, since
        // reads block and PTY output arrives in an unpredictable number of
        // chunks as the child renders. Bytes are handed to vt100::Parser
        // unmodified — it owns UTF-8/escape-sequence decoding.
        let (tx, rx) = mpsc::channel();
        thread::spawn(move || {
            let mut chunk = [0_u8; 4096];
            loop {
                match reader.read(&mut chunk) {
                    Ok(0) | Err(_) => break,
                    Ok(count) => {
                        if tx.send(chunk[..count].to_vec()).is_err() {
                            break;
                        }
                    }
                }
            }
        });

        Self {
            master: pair.master,
            writer,
            output: rx,
            parser: vt100::Parser::new(rows, cols, 0),
            raw: Vec::new(),
            child,
        }
    }

    fn send(&mut self, bytes: &[u8]) {
        self.writer.write_all(bytes).expect("write to pty succeeds");
        self.writer.flush().expect("flush pty succeeds");
    }

    fn type_text(&mut self, text: &str) {
        self.send(text.as_bytes());
    }

    /// Sends a single plain character key (menu/game shortcuts like `'q'`,
    /// `'r'`, `'v'`, `'s'`, `' '` are all just their own ASCII byte in raw
    /// terminal input — no escape sequence needed).
    fn key_char(&mut self, character: char) {
        let mut buffer = [0_u8; 4];
        self.send(character.encode_utf8(&mut buffer).as_bytes());
    }

    fn resize(&mut self, cols: u16, rows: u16) {
        self.master
            .resize(PtySize {
                rows,
                cols,
                pixel_width: 0,
                pixel_height: 0,
            })
            .expect("pty resize succeeds");
        // Keep the emulator's grid dimensions in sync so subsequent cursor-
        // position escapes from the child are interpreted correctly.
        self.parser.set_size(rows, cols);
    }

    /// Drains any output currently queued from the reader thread into the
    /// terminal emulator without blocking.
    fn pump(&mut self) {
        while let Ok(chunk) = self.output.try_recv() {
            self.parser.process(&chunk);
            self.raw.extend_from_slice(&chunk);
        }
    }

    /// Polls the raw byte stream until it contains `needle` (an exact
    /// escape sequence, not rendered text — see the `raw` field doc), or
    /// panics after `WAIT_TIMEOUT`.
    fn wait_for_raw(&mut self, needle: &[u8]) {
        let deadline = Instant::now() + WAIT_TIMEOUT;
        loop {
            self.pump();
            if self
                .raw
                .windows(needle.len())
                .any(|window| window == needle)
            {
                return;
            }
            if Instant::now() >= deadline {
                panic!(
                    "timed out after {WAIT_TIMEOUT:?} waiting for {needle:?} in the raw PTY byte stream"
                );
            }
            thread::sleep(POLL_INTERVAL);
        }
    }

    /// Returns the current reconstructed screen contents. Useful with
    /// `wait_for_change` to prove an action had an effect, without racing a
    /// possibly-instant transient state (see that method's doc).
    fn screen_snapshot(&mut self) -> String {
        self.pump();
        self.parser.screen().contents()
    }

    /// Polls until the screen contents differ from `previous`, or panics
    /// after `WAIT_TIMEOUT`. Prefer this over waiting for a transient
    /// indicator (like "thinking…") to appear-then-disappear: a fast search
    /// can complete between two polls, so the indicator might never be
    /// observed at all. Waiting for a *persistent* change has no such race.
    fn wait_for_change(&mut self, previous: &str) {
        let deadline = Instant::now() + WAIT_TIMEOUT;
        loop {
            self.pump();
            if self.parser.screen().contents() != previous {
                return;
            }
            if Instant::now() >= deadline {
                panic!("timed out after {WAIT_TIMEOUT:?} waiting for the screen to change");
            }
            thread::sleep(POLL_INTERVAL);
        }
    }

    /// Polls until `needle` no longer appears on screen, or panics after
    /// `WAIT_TIMEOUT`. Used after a standalone Escape keypress: a real
    /// terminal's raw-mode reader (and Crossterm on the receiving end) must
    /// briefly wait to distinguish a bare Esc from the start of an escape
    /// *sequence* (arrow keys, etc.). Sending Esc immediately followed by
    /// another key without confirming the first was processed risks them
    /// being coalesced into a single Alt-modified keypress instead of two
    /// separate ones — this waits out that ambiguity window properly
    /// instead of papering over it with a fixed sleep.
    fn wait_for_absence(&mut self, needle: &str) {
        let deadline = Instant::now() + WAIT_TIMEOUT;
        loop {
            self.pump();
            if !self.parser.screen().contents().contains(needle) {
                return;
            }
            if Instant::now() >= deadline {
                panic!("timed out after {WAIT_TIMEOUT:?} waiting for {needle:?} to disappear from screen");
            }
            thread::sleep(POLL_INTERVAL);
        }
    }

    /// Polls the reconstructed screen contents until `needle` appears, or
    /// panics after `WAIT_TIMEOUT`.
    fn wait_for(&mut self, needle: &str) {
        let deadline = Instant::now() + WAIT_TIMEOUT;
        loop {
            self.pump();
            let screen = self.parser.screen().contents();
            if screen.contains(needle) {
                return;
            }
            if Instant::now() >= deadline {
                panic!(
                    "timed out after {WAIT_TIMEOUT:?} waiting for {needle:?} on screen.\n\
                     --- current screen ---\n{screen}\n--- end screen ---"
                );
            }
            thread::sleep(POLL_INTERVAL);
        }
    }

    /// Waits for the child process to exit on its own and returns whether
    /// it exited successfully.
    fn wait_for_exit(&mut self) -> bool {
        let deadline = Instant::now() + WAIT_TIMEOUT;
        loop {
            if let Some(status) = self.child.try_wait().expect("try_wait succeeds") {
                return status.success();
            }
            if Instant::now() >= deadline {
                panic!("timed out after {WAIT_TIMEOUT:?} waiting for chess-tui to exit");
            }
            thread::sleep(POLL_INTERVAL);
        }
    }
}

impl Drop for PtySession {
    fn drop(&mut self) {
        // Best-effort cleanup if a test fails partway through and the child
        // is still running; never panics from within Drop.
        let _ = self.child.kill();
    }
}

#[test]
#[ignore = "spawns a real PTY + process; run explicitly via bash scripts/dev.sh tui-pty-smoke"]
fn launch_shows_menu_and_quit_exits_cleanly() {
    let mut session = PtySession::spawn(100, 32);
    // Crossterm's EnterAlternateScreen emits exactly this CSI sequence
    // (verified against crates.io crossterm 0.27.0's terminal.rs) — this is
    // the same real launch/quit/terminal-restoration evidence the
    // historical CI PTY runs referenced in docs/RUST_TUI_TODO.md claimed,
    // now reproducible in-repo.
    session.wait_for_raw(b"\x1b[?1049h");
    session.wait_for("Rust Chess TUI");
    session.wait_for("Start game");

    session.send(keys::ESC);
    let exited_cleanly = session.wait_for_exit();
    assert!(exited_cleanly, "chess-tui must exit 0 on menu-screen quit");
    session.wait_for_raw(b"\x1b[?1049l");
}

/// Navigates the default menu selection (row 0) down to the "Start game"
/// row (row 3) and presses Enter. Caller is responsible for adjusting rows
/// 0-2 first if the default configuration (Human vs Engine, White, depth 3)
/// isn't what the test wants.
fn start_game_from_menu(session: &mut PtySession) {
    for _ in 0..3 {
        session.send(keys::DOWN);
    }
    session.send(keys::ENTER);
}

#[test]
#[ignore = "spawns a real PTY + process; run explicitly via bash scripts/dev.sh tui-pty-smoke"]
fn human_white_move_gets_a_real_engine_response() {
    let mut session = PtySession::spawn(100, 32);
    session.wait_for("Start game");
    // Default menu config is Human vs Engine, White, depth 3 — start as-is.
    start_game_from_menu(&mut session);
    session.wait_for("Human vs Engine");
    session.wait_for("White to move");

    session.type_text("e2e4");
    session.send(keys::ENTER);
    // A real depth-3 search runs here; the engine's reply is authoritative
    // chess-search output, not a canned response.
    session.wait_for("Engine played");
    session.wait_for("1. e2e4");

    session.key_char('q');
    session.wait_for("Abandon this game and quit?");
    session.key_char('y');
    assert!(session.wait_for_exit(), "chess-tui must exit 0");
}

#[test]
#[ignore = "spawns a real PTY + process; run explicitly via bash scripts/dev.sh tui-pty-smoke"]
fn self_play_pause_step_and_resume_transition_correctly() {
    let mut session = PtySession::spawn(100, 32);
    session.wait_for("Start game");
    // Row 0: toggle Human vs Engine -> Self-play.
    session.send(keys::RIGHT);
    start_game_from_menu(&mut session);
    session.wait_for("Self-play");
    // Let the first automatic ply complete before pausing, so the pause
    // observation isn't racing the initial auto-scheduled search.
    session.wait_for("1.");

    session.key_char(' ');
    session.wait_for("Self-play: paused");

    // "Self-play: paused" is already on screen and won't disappear during
    // the step (auto_play stays false throughout), so it can't itself prove
    // the step did anything. Snapshot first and wait for a real change —
    // the completed step's move text — instead.
    let before_step = session.screen_snapshot();
    session.key_char('s');
    session.wait_for_change(&before_step);
    // ...and confirm it settled back into paused, not auto-resumed.
    session.wait_for("Self-play: paused");

    session.key_char(' ');
    session.wait_for("Self-play: running");

    session.key_char('q');
    session.wait_for("Abandon this game and quit?");
    session.key_char('y');
    assert!(session.wait_for_exit(), "chess-tui must exit 0");
}

#[test]
#[ignore = "spawns a real PTY + process; run explicitly via bash scripts/dev.sh tui-pty-smoke"]
fn resignation_confirmation_declares_the_opponent_winner() {
    let mut session = PtySession::spawn(100, 32);
    session.wait_for("Start game");
    start_game_from_menu(&mut session);
    session.wait_for("White to move");

    session.key_char('r');
    session.wait_for("Resign this game?");
    session.key_char('y');

    session.wait_for("Game Over");
    session.wait_for("Resignation");
    session.wait_for("Black wins");

    // The game is now terminal (is_active() == false), so 'q' quits
    // immediately without an abandon-confirmation prompt.
    session.key_char('q');
    assert!(session.wait_for_exit(), "chess-tui must exit 0");
}

#[test]
#[ignore = "spawns a real PTY + process; run explicitly via bash scripts/dev.sh tui-pty-smoke"]
fn quitting_while_the_engine_is_thinking_requires_confirmation_and_cancels_cleanly() {
    let mut session = PtySession::spawn(100, 32);
    session.wait_for("Start game");
    // Row 1: toggle human color White -> Black, so the engine (White)
    // starts thinking immediately on game start.
    session.send(keys::DOWN);
    session.send(keys::RIGHT);
    start_game_from_menu(&mut session);
    session.wait_for("thinking");

    // 'q' while a search is genuinely in flight must open the abandon
    // confirmation, not quit immediately — and confirming it must cancel
    // the in-flight worker before the process exits (proven by exiting
    // cleanly rather than hanging or crashing).
    session.key_char('q');
    session.wait_for("Abandon this game and quit?");
    session.key_char('y');
    assert!(
        session.wait_for_exit(),
        "chess-tui must exit 0 even when quitting mid-search"
    );
}

#[test]
#[ignore = "spawns a real PTY + process; run explicitly via bash scripts/dev.sh tui-pty-smoke"]
fn resizing_the_terminal_mid_game_does_not_crash_or_corrupt_state() {
    let mut session = PtySession::spawn(100, 32);
    session.wait_for("Start game");
    start_game_from_menu(&mut session);
    session.wait_for("White to move");

    // Shrink below the smallest supported layout, then back up to a
    // comfortably supported size.
    session.resize(40, 10);
    session.wait_for("Terminal too small");

    session.resize(100, 32);
    session.wait_for("White to move");

    // Confirm the process is still fully responsive post-resize by playing
    // a real move through it, not just that it redrew without panicking.
    session.type_text("e2e4");
    session.send(keys::ENTER);
    session.wait_for("Engine played");

    session.key_char('q');
    session.wait_for("Abandon this game and quit?");
    session.key_char('y');
    assert!(
        session.wait_for_exit(),
        "chess-tui must exit 0 after a resize"
    );
}

fn unique_temp_path(label: &str) -> std::path::PathBuf {
    let stamp = std::time::SystemTime::now()
        .duration_since(std::time::SystemTime::UNIX_EPOCH)
        .expect("clock is after epoch")
        .as_nanos();
    std::env::temp_dir().join(format!(
        "chess-tui-pty-{label}-{}-{stamp}.txt",
        std::process::id()
    ))
}

/// Clears whatever default text the save overlay pre-filled (`"game.txt"`)
/// with more backspaces than could possibly be needed — extra backspaces on
/// an already-empty input are a documented no-op, not an error.
fn clear_save_input(session: &mut PtySession) {
    for _ in 0..32 {
        session.send(keys::BACKSPACE);
    }
}

#[test]
#[ignore = "spawns a real PTY + process; run explicitly via bash scripts/dev.sh tui-pty-smoke"]
fn saving_to_a_writable_path_succeeds() {
    let path = unique_temp_path("success");
    let mut session = PtySession::spawn(100, 32);
    session.wait_for("Start game");
    start_game_from_menu(&mut session);
    session.wait_for("White to move");

    session.key_char('v');
    session.wait_for("Save game");
    clear_save_input(&mut session);
    session.type_text(&path.display().to_string());
    session.send(keys::ENTER);
    session.wait_for("Saved to");

    let contents = std::fs::read_to_string(&path).expect("saved file is readable");
    assert!(contents.starts_with("Chess Engine Rust TUI save v1"));
    std::fs::remove_file(&path).expect("temporary save is removed");

    session.key_char('q');
    session.wait_for("Abandon this game and quit?");
    session.key_char('y');
    assert!(session.wait_for_exit(), "chess-tui must exit 0");
}

#[test]
#[ignore = "spawns a real PTY + process; run explicitly via bash scripts/dev.sh tui-pty-smoke"]
fn saving_to_an_unwritable_path_fails_visibly() {
    // A parent directory that does not exist, so the write fails.
    let path = unique_temp_path("missing-parent-dir").join("game.txt");
    let mut session = PtySession::spawn(100, 32);
    session.wait_for("Start game");
    start_game_from_menu(&mut session);
    session.wait_for("White to move");

    session.key_char('v');
    session.wait_for("Save game");
    clear_save_input(&mut session);
    session.type_text(&path.display().to_string());
    session.send(keys::ENTER);
    session.wait_for("Save failed:");

    // On failure the save overlay stays open by design (so the path can be
    // corrected and retried) — 'q' at this point would be typed into the
    // path field, not treated as a quit shortcut. Dismiss it first, and
    // confirm it's actually gone before sending the next key (see
    // wait_for_absence's doc for why that matters here).
    session.send(keys::ESC);
    session.wait_for_absence("Save game");
    session.key_char('q');
    session.wait_for("Abandon this game and quit?");
    session.key_char('y');
    assert!(session.wait_for_exit(), "chess-tui must exit 0");
}
