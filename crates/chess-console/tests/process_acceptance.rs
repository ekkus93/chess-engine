use std::{
    fs,
    io::{Read, Write},
    path::PathBuf,
    process::{Child, ChildStdin, Command, ExitStatus, Stdio},
    sync::{
        mpsc::{self, Receiver, Sender},
        Mutex, MutexGuard,
    },
    thread::{self, JoinHandle},
    time::{Duration, Instant, SystemTime},
};

const TIMEOUT: Duration = Duration::from_secs(15);
static PROCESS_TEST_LOCK: Mutex<()> = Mutex::new(());

fn process_test_guard() -> MutexGuard<'static, ()> {
    PROCESS_TEST_LOCK
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

#[derive(Debug)]
enum StreamChunk {
    Stdout(Vec<u8>),
    Stderr(Vec<u8>),
}

struct Harness {
    child: Child,
    stdin: Option<ChildStdin>,
    output_rx: Receiver<StreamChunk>,
    readers: Vec<JoinHandle<()>>,
    stdout: Vec<u8>,
    stderr: Vec<u8>,
}

impl Harness {
    fn spawn() -> Self {
        let mut child = Command::new(env!("CARGO_BIN_EXE_chess-console"))
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .expect("console binary starts");
        let stdin = child.stdin.take().expect("stdin pipe");
        let stdout = child.stdout.take().expect("stdout pipe");
        let stderr = child.stderr.take().expect("stderr pipe");
        let (sender, output_rx) = mpsc::channel();
        let stdout_reader = spawn_reader(stdout, sender.clone(), StreamChunk::Stdout);
        let stderr_reader = spawn_reader(stderr, sender, StreamChunk::Stderr);
        Self {
            child,
            stdin: Some(stdin),
            output_rx,
            readers: vec![stdout_reader, stderr_reader],
            stdout: Vec::new(),
            stderr: Vec::new(),
        }
    }

    fn send(&mut self, input: &str) {
        let stdin = self.stdin.as_mut().expect("stdin remains open");
        stdin.write_all(input.as_bytes()).expect("write input");
        stdin.flush().expect("flush input");
    }

    fn close_stdin(&mut self) {
        self.stdin.take();
    }

    fn output_len(&self) -> usize {
        self.stdout.len()
    }

    fn wait_for(&mut self, marker: &str) {
        self.wait_for_since(marker, 0);
    }

    fn wait_for_since(&mut self, marker: &str, start: usize) {
        let deadline = Instant::now() + TIMEOUT;
        loop {
            if String::from_utf8_lossy(&self.stdout[start.min(self.stdout.len())..])
                .contains(marker)
            {
                return;
            }
            if let Some(status) = self.child.try_wait().expect("child status") {
                panic!(
                    "console exited before marker {marker:?}: status={status}; {}",
                    self.diagnostic()
                );
            }
            let now = Instant::now();
            if now >= deadline {
                let _ = self.child.kill();
                panic!(
                    "timeout waiting for marker {marker:?}; {}",
                    self.diagnostic()
                );
            }
            if let Ok(chunk) = self
                .output_rx
                .recv_timeout((deadline - now).min(Duration::from_millis(250)))
            {
                self.record(chunk);
            }
        }
    }

    fn wait_exit(mut self) -> (ExitStatus, String, String) {
        let deadline = Instant::now() + TIMEOUT;
        let status = loop {
            self.drain_available();
            if let Some(status) = self.child.try_wait().expect("child status") {
                break status;
            }
            let now = Instant::now();
            if now >= deadline {
                let _ = self.child.kill();
                panic!("console did not exit; {}", self.diagnostic());
            }
            if let Ok(chunk) = self
                .output_rx
                .recv_timeout((deadline - now).min(Duration::from_millis(250)))
            {
                self.record(chunk);
            }
        };
        self.close_stdin();
        for reader in self.readers.drain(..) {
            reader.join().expect("output reader joins");
        }
        self.drain_available();
        (
            status,
            String::from_utf8_lossy(&self.stdout).into_owned(),
            String::from_utf8_lossy(&self.stderr).into_owned(),
        )
    }

    fn record(&mut self, chunk: StreamChunk) {
        match chunk {
            StreamChunk::Stdout(bytes) => self.stdout.extend_from_slice(&bytes),
            StreamChunk::Stderr(bytes) => self.stderr.extend_from_slice(&bytes),
        }
    }

    fn drain_available(&mut self) {
        while let Ok(chunk) = self.output_rx.try_recv() {
            self.record(chunk);
        }
    }

    fn diagnostic(&self) -> String {
        format!(
            "stdout={:?}; stderr={:?}",
            String::from_utf8_lossy(&self.stdout),
            String::from_utf8_lossy(&self.stderr)
        )
    }
}

fn spawn_reader<R: Read + Send + 'static>(
    mut reader: R,
    sender: Sender<StreamChunk>,
    wrap: fn(Vec<u8>) -> StreamChunk,
) -> JoinHandle<()> {
    thread::spawn(move || {
        let mut buffer = [0_u8; 4096];
        loop {
            match reader.read(&mut buffer) {
                Ok(0) => break,
                Ok(count) => {
                    if sender.send(wrap(buffer[..count].to_vec())).is_err() {
                        break;
                    }
                }
                Err(_) => break,
            }
        }
    })
}

fn unique_path(label: &str) -> PathBuf {
    let stamp = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .expect("clock after epoch")
        .as_nanos();
    std::env::temp_dir().join(format!(
        "chess-console-process-{label}-{}-{stamp}.txt",
        std::process::id()
    ))
}

fn assert_success(status: ExitStatus, stdout: &str, stderr: &str) {
    assert!(
        status.success(),
        "status={status}; stdout={stdout:?}; stderr={stderr:?}"
    );
}

#[test]
fn real_binary_launch_and_quit_from_menu() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("3\n");
    let (status, stdout, stderr) = harness.wait_exit();
    assert_success(status, &stdout, &stderr);
    assert!(stdout.contains("Rust Chess Console"));
}

#[test]
fn real_binary_human_white_gets_exact_engine_response_and_board_command() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("1\n1\n1\n");
    harness.wait_for("move> ");

    let board_start = harness.output_len();
    harness.send("board\n");
    harness.wait_for_since("    a   b   c   d   e   f   g   h", board_start);

    let start = harness.output_len();
    harness.send("e2e4\n");
    harness.wait_for_since("Engine plays:", start);
    harness.wait_for_since("White to move", start);
    harness.send("quit\nyes\n");
    let (status, stdout, stderr) = harness.wait_exit();
    assert_success(status, &stdout, &stderr);
    assert!(stdout.contains("You played: e2e4"));
}

#[test]
fn real_binary_human_black_receives_engine_first_move_and_black_orientation() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("1\n2\n1\n");
    harness.wait_for("    h   g   f   e   d   c   b   a");
    harness.wait_for("Engine plays:");
    harness.wait_for("Black to move");
    harness.send("quit\ny\n");
    let (status, stdout, stderr) = harness.wait_exit();
    assert_success(status, &stdout, &stderr);
}

#[test]
fn real_binary_illegal_move_is_visible_and_nonfatal() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("1\n1\n1\n");
    harness.wait_for("move> ");
    harness.send("e2e5\n");
    harness.wait_for("move is not legal in the current position");
    harness.send("moves\n");
    harness.wait_for("(no moves)");
    harness.send("quit\ny\n");
    let (status, stdout, stderr) = harness.wait_exit();
    assert_success(status, &stdout, &stderr);
}

#[test]
fn real_binary_confirmation_invalid_decline_and_resignation_confirm_are_explicit() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("1\n1\n1\n");
    harness.wait_for("move> ");
    harness.send("resign\n");
    harness.wait_for("Resign this game? [y/N]");
    harness.send("maybe\n");
    harness.wait_for("Please answer y/yes or n/no. Empty input means No.");
    harness.send("\n");
    harness.wait_for("Cancelled.");
    harness.send("resign\nyes\n");
    harness.wait_for("Resignation — Black wins");
    harness.send("quit\n");
    let (status, stdout, stderr) = harness.wait_exit();
    assert_success(status, &stdout, &stderr);
}

#[test]
fn real_binary_new_menu_and_quit_declines_preserve_active_game() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("1\n1\n1\n");
    harness.wait_for("move> ");

    for (command, marker) in [
        ("new", "Abandon this game and start a new one? [y/N]"),
        ("menu", "Abandon this game and return to the menu? [y/N]"),
        ("quit", "Abandon this game and quit? [y/N]"),
    ] {
        let start = harness.output_len();
        harness.send(&format!("{command}\n"));
        harness.wait_for_since(marker, start);
        harness.send("\n");
        harness.wait_for_since("Cancelled.", start);
        let status_start = harness.output_len();
        harness.send("status\n");
        harness.wait_for_since("White to move", status_start);
    }

    harness.send("quit\nyes\n");
    let (status, stdout, stderr) = harness.wait_exit();
    assert_success(status, &stdout, &stderr);
}

#[test]
fn real_binary_mode_invalid_commands_are_visible() {
    let _guard = process_test_guard();
    let mut human = Harness::spawn();
    human.wait_for("Selection [1]:");
    human.send("1\n1\n1\n");
    human.wait_for("move> ");
    human.send("pause\nresume\nstep\n");
    human.wait_for("pause is only available during Self-play");
    human.wait_for("resume is only available during self-play");
    human.wait_for("step is only available during self-play");
    human.send("quit\ny\n");
    let (status, stdout, stderr) = human.wait_exit();
    assert_success(status, &stdout, &stderr);

    let mut self_play = Harness::spawn();
    self_play.wait_for("Selection [1]:");
    self_play.send("2\n1\n1\n");
    self_play.wait_for("Engine thinking...");
    self_play.send("pause\n");
    self_play.wait_for("Self-play paused.");
    self_play.send("resign\n");
    self_play.wait_for("resign is only available in Human vs Engine mode");
    self_play.send("quit\ny\n");
    let (status, stdout, stderr) = self_play.wait_exit();
    assert_success(status, &stdout, &stderr);
}

#[test]
fn real_binary_save_success_failure_and_overwrite_confirmation_are_visible() {
    let _guard = process_test_guard();
    let path = unique_path("save");
    let missing = unique_path("missing-parent").join("game.txt");
    fs::write(&path, "sentinel\n").expect("seed existing file");

    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("1\n1\n1\n");
    harness.wait_for("move> ");

    harness.send(&format!("save {}\n", path.display()));
    harness.wait_for("Overwrite existing file");
    harness.send("\n");
    harness.wait_for("Cancelled.");
    assert_eq!(
        fs::read_to_string(&path).expect("read sentinel"),
        "sentinel\n"
    );

    harness.send(&format!("save {}\nyes\n", path.display()));
    harness.wait_for("Saved to ");
    harness.send(&format!("save {}\n", missing.display()));
    harness.wait_for("Save failed:");
    harness.send("quit\ny\n");
    let (status, stdout, stderr) = harness.wait_exit();
    assert_success(status, &stdout, &stderr);
    let saved = fs::read_to_string(&path).expect("saved file readable");
    assert!(saved.starts_with("Chess Engine Rust Console save v1\n"));
    assert!(!saved.contains("PGN"));
    fs::remove_file(path).expect("cleanup saved file");
}

#[test]
fn real_binary_self_play_pause_step_remains_paused_then_resume() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("2\n1\n1\n");
    harness.wait_for("Engine thinking...");
    harness.send("pause\n");
    harness.wait_for("Self-play paused.");
    let step_start = harness.output_len();
    harness.send("step\n");
    harness.wait_for_since("Engine plays:", step_start);
    let second_step = harness.output_len();
    harness.send("step\n");
    harness.wait_for_since("Self-play step scheduled.", second_step);
    harness.wait_for_since("Engine plays:", second_step);
    let resume_start = harness.output_len();
    harness.send("resume\n");
    harness.wait_for_since("Self-play resumed.", resume_start);
    harness.send("quit\ny\n");
    let (status, stdout, stderr) = harness.wait_exit();
    assert_success(status, &stdout, &stderr);
}

#[test]
fn real_binary_declined_quit_during_engine_search_keeps_search_active() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("1\n1\n12\n");
    harness.wait_for("move> ");
    harness.send("h2h3\n");
    harness.wait_for("Engine thinking...");
    harness.send("quit\n");
    harness.wait_for("Abandon this game and quit? [y/N]");
    harness.send("\n");
    harness.wait_for("Cancelled.");
    let start = harness.output_len();
    harness.send("h3h4\n");
    harness.wait_for_since("engine search is still active", start);
    harness.send("quit\nyes\n");
    let (status, stdout, stderr) = harness.wait_exit();
    assert_success(status, &stdout, &stderr);
}

#[test]
fn real_binary_confirmed_quit_during_engine_search_cancels_and_exits() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("1\n1\n12\n");
    harness.wait_for("move> ");
    harness.send("h2h3\n");
    harness.wait_for("Engine thinking...");
    harness.send("quit\n");
    harness.wait_for("Abandon this game and quit? [y/N]");
    harness.send("yes\n");
    let (status, stdout, stderr) = harness.wait_exit();
    assert_success(status, &stdout, &stderr);
}

#[test]
fn real_binary_eof_while_waiting_for_human_move_exits_cleanly() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("1\n1\n1\n");
    harness.wait_for("move> ");
    harness.close_stdin();
    let (status, stdout, stderr) = harness.wait_exit();
    assert_success(status, &stdout, &stderr);
    assert!(stdout.contains("EOF received; active search resolved; exiting."));
}

#[test]
fn real_binary_eof_during_engine_activity_exits_without_hanging() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("1\n1\n12\n");
    harness.wait_for("move> ");
    harness.send("h2h3\n");
    harness.wait_for("Engine thinking...");
    harness.close_stdin();
    let (status, stdout, stderr) = harness.wait_exit();
    assert_success(status, &stdout, &stderr);
    assert!(stdout.contains("EOF received; active search resolved; exiting."));
}