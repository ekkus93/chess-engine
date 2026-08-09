//! PTY-driven terminal-semantic acceptance coverage for `chess-console`.
//!
//! This integration test lives in the `chess-tui` test crate solely to reuse
//! its existing test-only `portable-pty` dependency. It does not couple either
//! production frontend to the other. `bash scripts/dev.sh console-pty-smoke`
//! first builds `chess-console`, then this harness locates that exact sibling
//! debug binary and drives it through a real OS pseudo-terminal.
//!
//! The ordinary console process suite proves stdin/stdout behavior through
//! pipes. These ignored tests add the objective parts of the Phase 19
//! real-terminal smoke pass: canonical terminal input, scrollback-style output,
//! both human colors, confirmations, save/error paths, Self-play controls, and
//! clean exit while search is active.
//!
//! This is additional automated evidence, not a claim that subjective human UX
//! has been reviewed. Readability, prompt clarity, and overall terminal feel
//! still require a short human-operated pass.

use std::{
    fs,
    io::{Read, Write},
    path::PathBuf,
    sync::mpsc,
    thread::{self, JoinHandle},
    time::{Duration, Instant, SystemTime},
};

use portable_pty::{native_pty_system, Child, CommandBuilder, MasterPty, PtySize};

const WAIT_TIMEOUT: Duration = Duration::from_secs(15);
const POLL_INTERVAL: Duration = Duration::from_millis(20);
const ALT_SCREEN_ENTER: &[u8] = b"\x1b[?1049h";
const ALT_SCREEN_LEAVE: &[u8] = b"\x1b[?1049l";
const CLEAR_SCREEN: &[u8] = b"\x1b[2J";

struct PtySession {
    master: Box<dyn MasterPty + Send>,
    writer: Box<dyn Write + Send>,
    output: mpsc::Receiver<Vec<u8>>,
    reader: Option<JoinHandle<()>>,
    raw: Vec<u8>,
    child: Box<dyn Child + Send + Sync>,
}

impl PtySession {
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
        let cmd = CommandBuilder::new(console_binary());
        let child = pair
            .slave
            .spawn_command(cmd)
            .expect("chess-console spawns under PTY");
        drop(pair.slave);

        let writer = pair.master.take_writer().expect("PTY writer available");
        let mut reader = pair
            .master
            .try_clone_reader()
            .expect("PTY reader available");
        let (sender, output) = mpsc::channel();
        let reader = thread::spawn(move || {
            let mut chunk = [0_u8; 4096];
            loop {
                match reader.read(&mut chunk) {
                    Ok(0) | Err(_) => break,
                    Ok(count) => {
                        if sender.send(chunk[..count].to_vec()).is_err() {
                            break;
                        }
                    }
                }
            }
        });

        Self {
            master: pair.master,
            writer,
            output,
            reader: Some(reader),
            raw: Vec::new(),
            child,
        }
    }

    fn send_line(&mut self, line: &str) {
        self.writer
            .write_all(line.as_bytes())
            .expect("write PTY input");
        self.writer.write_all(b"\r").expect("write PTY Enter");
        self.writer.flush().expect("flush PTY input");
    }

    fn resize(&mut self, cols: u16, rows: u16) {
        self.master
            .resize(PtySize {
                rows,
                cols,
                pixel_width: 0,
                pixel_height: 0,
            })
            .expect("PTY resize succeeds");
    }

    fn output_len(&mut self) -> usize {
        self.pump();
        self.raw.len()
    }

    fn pump(&mut self) {
        while let Ok(chunk) = self.output.try_recv() {
            self.raw.extend_from_slice(&chunk);
        }
    }

    fn wait_for(&mut self, marker: &str) {
        self.wait_for_since(marker, 0);
    }

    fn wait_for_since(&mut self, marker: &str, start: usize) {
        let deadline = Instant::now() + WAIT_TIMEOUT;
        loop {
            self.pump();
            let start = start.min(self.raw.len());
            if String::from_utf8_lossy(&self.raw[start..]).contains(marker) {
                return;
            }
            if let Some(status) = self.child.try_wait().expect("child status available") {
                panic!(
                    "chess-console exited before marker {marker:?}: {status:?}; transcript={:?}",
                    String::from_utf8_lossy(&self.raw)
                );
            }
            if Instant::now() >= deadline {
                let _ = self.child.kill();
                panic!(
                    "timed out waiting for {marker:?}; transcript={:?}",
                    String::from_utf8_lossy(&self.raw)
                );
            }
            thread::sleep(POLL_INTERVAL);
        }
    }

    fn finish(mut self) -> String {
        let deadline = Instant::now() + WAIT_TIMEOUT;
        let status = loop {
            self.pump();
            if let Some(status) = self.child.try_wait().expect("child status available") {
                break status;
            }
            if Instant::now() >= deadline {
                let _ = self.child.kill();
                panic!(
                    "chess-console did not exit; transcript={:?}",
                    String::from_utf8_lossy(&self.raw)
                );
            }
            thread::sleep(POLL_INTERVAL);
        };
        assert!(status.success(), "chess-console PTY exit status: {status:?}");
        drop(self.writer);
        if let Some(reader) = self.reader.take() {
            reader.join().expect("PTY reader joins");
        }
        self.pump();
        assert_plain_scrollback_stream(&self.raw);
        String::from_utf8_lossy(&self.raw).into_owned()
    }
}

impl Drop for PtySession {
    fn drop(&mut self) {
        let _ = self.child.kill();
    }
}

fn console_binary() -> PathBuf {
    let test_binary = std::env::current_exe().expect("current test executable path");
    let deps_dir = test_binary.parent().expect("integration test lives in deps");
    let debug_dir = deps_dir.parent().expect("deps lives under target/debug");
    let binary = debug_dir.join(format!("chess-console{}", std::env::consts::EXE_SUFFIX));
    assert!(
        binary.is_file(),
        "expected prebuilt chess-console binary at {}; run through bash scripts/dev.sh console-pty-smoke",
        binary.display()
    );
    binary
}

fn contains_bytes(haystack: &[u8], needle: &[u8]) -> bool {
    haystack
        .windows(needle.len())
        .any(|window| window == needle)
}

fn assert_plain_scrollback_stream(raw: &[u8]) {
    assert!(
        !contains_bytes(raw, ALT_SCREEN_ENTER),
        "console must not enter alternate screen"
    );
    assert!(
        !contains_bytes(raw, ALT_SCREEN_LEAVE),
        "console must not leave an alternate screen it never entered"
    );
    assert!(
        !contains_bytes(raw, CLEAR_SCREEN),
        "console must not clear normal terminal scrollback"
    );
}

fn unique_path(label: &str) -> PathBuf {
    let stamp = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .expect("clock after epoch")
        .as_nanos();
    std::env::temp_dir().join(format!(
        "chess-console-pty-{label}-{}-{stamp}.txt",
        std::process::id()
    ))
}

fn start_human(session: &mut PtySession, color: u8, depth: u8) {
    session.wait_for("Selection [1]:");
    session.send_line("1");
    session.send_line(&color.to_string());
    session.send_line(&depth.to_string());
    session.wait_for("move> ");
}

#[test]
#[ignore = "spawns a real PTY + process; run via bash scripts/dev.sh console-pty-smoke"]
fn pty_launch_resize_and_plain_scrollback_quit() {
    let mut session = PtySession::spawn(100, 32);
    session.wait_for("Rust Chess Console");
    session.wait_for("Selection [1]:");
    session.resize(72, 24);
    session.send_line("3");
    let transcript = session.finish();
    assert!(transcript.contains("Rust Chess Console"));
    assert!(transcript.contains("Selection [1]:"));
}

#[test]
#[ignore = "spawns a real PTY + process; run via bash scripts/dev.sh console-pty-smoke"]
fn pty_human_white_commands_errors_engine_reply_and_resignation() {
    let mut session = PtySession::spawn(100, 36);
    start_human(&mut session, 1, 1);
    session.wait_for("    a   b   c   d   e   f   g   h");

    for (command, marker) in [
        ("board", "    a   b   c   d   e   f   g   h"),
        ("moves", "(no moves)"),
        ("status", "White to move"),
        ("engine", "info unavailable"),
        ("help", "Commands:"),
    ] {
        let start = session.output_len();
        session.send_line(command);
        session.wait_for_since(marker, start);
    }

    let malformed = session.output_len();
    session.send_line("e2e9");
    session.wait_for_since("Error:", malformed);

    let illegal = session.output_len();
    session.send_line("e2e5");
    session.wait_for_since("move is not legal in the current position", illegal);

    let move_start = session.output_len();
    session.send_line("e2e4");
    session.wait_for_since("You played: e2e4", move_start);
    session.wait_for_since("Engine plays:", move_start);
    session.wait_for_since("White to move", move_start);

    let resign = session.output_len();
    session.send_line("resign");
    session.wait_for_since("Resign this game? [y/N]", resign);
    session.send_line("yes");
    session.wait_for_since("Resignation — Black wins", resign);
    session.send_line("quit");
    let transcript = session.finish();
    assert!(transcript.contains("You played: e2e4"));
}

#[test]
#[ignore = "spawns a real PTY + process; run via bash scripts/dev.sh console-pty-smoke"]
fn pty_human_black_engine_first_move_then_active_search_quit() {
    let mut session = PtySession::spawn(100, 36);
    session.wait_for("Selection [1]:");
    session.send_line("1");
    session.send_line("2");
    session.send_line("1");
    session.wait_for("    h   g   f   e   d   c   b   a");
    session.wait_for("Engine plays:");
    session.wait_for("Black to move");

    let black_move = session.output_len();
    session.send_line("e7e5");
    session.wait_for_since("You played: e7e5", black_move);
    session.wait_for_since("Engine thinking...", black_move);

    let quit = session.output_len();
    session.send_line("quit");
    session.wait_for_since("Abandon this game and quit? [y/N]", quit);
    session.send_line("yes");
    let transcript = session.finish();
    assert!(transcript.contains("Black to move"));
}

#[test]
#[ignore = "spawns a real PTY + process; run via bash scripts/dev.sh console-pty-smoke"]
fn pty_save_success_failure_and_overwrite_confirmation() {
    let path = unique_path("save");
    let missing = unique_path("missing-parent").join("game.txt");
    fs::write(&path, "sentinel\n").expect("seed existing save path");

    let mut session = PtySession::spawn(100, 36);
    start_human(&mut session, 1, 1);

    let decline = session.output_len();
    session.send_line(&format!("save {}", path.display()));
    session.wait_for_since("Overwrite existing file", decline);
    session.send_line("");
    session.wait_for_since("Cancelled.", decline);
    assert_eq!(fs::read_to_string(&path).expect("read sentinel"), "sentinel\n");

    let replace = session.output_len();
    session.send_line(&format!("save {}", path.display()));
    session.wait_for_since("Overwrite existing file", replace);
    session.send_line("yes");
    session.wait_for_since("Saved to ", replace);

    let failure = session.output_len();
    session.send_line(&format!("save {}", missing.display()));
    session.wait_for_since("Save failed:", failure);

    session.send_line("quit");
    session.wait_for("Abandon this game and quit? [y/N]");
    session.send_line("yes");
    let _ = session.finish();

    let saved = fs::read_to_string(&path).expect("saved file readable");
    assert!(saved.starts_with("Chess Engine Rust Console save v1\n"));
    fs::remove_file(path).expect("clean saved file");
}

#[test]
#[ignore = "spawns a real PTY + process; run via bash scripts/dev.sh console-pty-smoke"]
fn pty_self_play_auto_pause_repeated_step_resume_and_quit() {
    let mut session = PtySession::spawn(100, 36);
    session.wait_for("Selection [1]:");
    session.send_line("2");
    session.send_line("1");
    session.send_line("1");
    session.wait_for("Engine thinking...");
    session.wait_for("Engine plays:");

    let pause = session.output_len();
    session.send_line("pause");
    session.wait_for_since("Self-play paused.", pause);

    let first_step = session.output_len();
    session.send_line("step");
    session.wait_for_since("Self-play step scheduled.", first_step);
    session.wait_for_since("Engine plays:", first_step);

    let second_step = session.output_len();
    session.send_line("step");
    session.wait_for_since("Self-play step scheduled.", second_step);
    session.wait_for_since("Engine plays:", second_step);

    let resume = session.output_len();
    session.send_line("resume");
    session.wait_for_since("Self-play resumed.", resume);
    session.wait_for_since("Engine plays:", resume);

    let quit = session.output_len();
    session.send_line("quit");
    session.wait_for_since("Abandon this game and quit? [y/N]", quit);
    session.send_line("yes");
    let _ = session.finish();
}
