use std::{
    fs,
    io::{Read, Write},
    path::PathBuf,
    process::{Child, ChildStdin, Command, ExitStatus, Stdio},
    sync::{
        mpsc::{self, Receiver},
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

struct Harness {
    child: Child,
    stdin: Option<ChildStdin>,
    output_rx: Receiver<Vec<u8>>,
    reader: Option<JoinHandle<()>>,
    output: Vec<u8>,
}

impl Harness {
    fn spawn() -> Self {
        let mut child = Command::new(env!("CARGO_BIN_EXE_chess-console"))
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .expect("console binary starts");
        let stdin = child.stdin.take().expect("stdin pipe");
        let mut stdout = child.stdout.take().expect("stdout pipe");
        let (sender, output_rx) = mpsc::channel();
        let reader = thread::spawn(move || {
            let mut buffer = [0_u8; 4096];
            loop {
                match stdout.read(&mut buffer) {
                    Ok(0) => break,
                    Ok(count) => {
                        if sender.send(buffer[..count].to_vec()).is_err() {
                            break;
                        }
                    }
                    Err(_) => break,
                }
            }
        });
        Self {
            child,
            stdin: Some(stdin),
            output_rx,
            reader: Some(reader),
            output: Vec::new(),
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
        self.output.len()
    }

    fn wait_for(&mut self, marker: &str) {
        self.wait_for_since(marker, 0);
    }

    fn wait_for_since(&mut self, marker: &str, start: usize) {
        let deadline = Instant::now() + TIMEOUT;
        loop {
            if String::from_utf8_lossy(&self.output[start.min(self.output.len())..])
                .contains(marker)
            {
                return;
            }
            if let Some(status) = self.child.try_wait().expect("child status") {
                panic!(
                    "console exited before marker {marker:?}: status={status}; output={}",
                    String::from_utf8_lossy(&self.output)
                );
            }
            let now = Instant::now();
            if now >= deadline {
                let _ = self.child.kill();
                panic!(
                    "timeout waiting for marker {marker:?}; output={}",
                    String::from_utf8_lossy(&self.output)
                );
            }
            if let Ok(chunk) = self
                .output_rx
                .recv_timeout((deadline - now).min(Duration::from_millis(250)))
            {
                self.output.extend_from_slice(&chunk);
            }
        }
    }

    fn wait_exit(mut self) -> (ExitStatus, String) {
        let deadline = Instant::now() + TIMEOUT;
        let status = loop {
            while let Ok(chunk) = self.output_rx.try_recv() {
                self.output.extend_from_slice(&chunk);
            }
            if let Some(status) = self.child.try_wait().expect("child status") {
                break status;
            }
            let now = Instant::now();
            if now >= deadline {
                let _ = self.child.kill();
                panic!(
                    "console did not exit; output={}",
                    String::from_utf8_lossy(&self.output)
                );
            }
            if let Ok(chunk) = self
                .output_rx
                .recv_timeout((deadline - now).min(Duration::from_millis(250)))
            {
                self.output.extend_from_slice(&chunk);
            }
        };
        self.close_stdin();
        while let Ok(chunk) = self.output_rx.recv_timeout(Duration::from_millis(50)) {
            self.output.extend_from_slice(&chunk);
        }
        if let Some(reader) = self.reader.take() {
            reader.join().expect("output reader joins");
        }
        (status, String::from_utf8_lossy(&self.output).into_owned())
    }
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

#[test]
fn real_binary_launch_and_quit_from_menu() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("3\n");
    let (status, output) = harness.wait_exit();
    assert!(status.success(), "output={output}");
    assert!(output.contains("Rust Chess Console"));
}

#[test]
fn real_binary_human_white_gets_exact_engine_response() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("1\n1\n1\n");
    harness.wait_for("move> ");
    let start = harness.output_len();
    harness.send("e2e4\n");
    harness.wait_for_since("Engine plays:", start);
    harness.wait_for_since("White to move", start);
    harness.send("quit\nyes\n");
    let (status, output) = harness.wait_exit();
    assert!(status.success(), "output={output}");
    assert!(output.contains("You played: e2e4"));
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
    let (status, output) = harness.wait_exit();
    assert!(status.success(), "output={output}");
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
    let (status, output) = harness.wait_exit();
    assert!(status.success(), "output={output}");
}

#[test]
fn real_binary_resignation_decline_and_confirm_are_explicit() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("1\n1\n1\n");
    harness.wait_for("move> ");
    harness.send("resign\n");
    harness.wait_for("Resign this game? [y/N]");
    harness.send("\n");
    harness.wait_for("Cancelled.");
    harness.send("resign\nyes\n");
    harness.wait_for("Resignation — Black wins");
    harness.send("quit\n");
    let (status, output) = harness.wait_exit();
    assert!(status.success(), "output={output}");
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
    let (status, output) = harness.wait_exit();
    assert!(status.success(), "output={output}");
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
    let (status, output) = harness.wait_exit();
    assert!(status.success(), "output={output}");
}

#[test]
fn real_binary_confirmed_quit_during_engine_search_cancels_and_exits() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("1\n2\n12\n");
    harness.wait_for("Engine thinking...");
    harness.send("quit\n");
    harness.wait_for("Abandon this game and quit? [y/N]");
    harness.send("yes\n");
    let (status, output) = harness.wait_exit();
    assert!(status.success(), "output={output}");
}

#[test]
fn real_binary_eof_during_engine_activity_exits_without_hanging() {
    let _guard = process_test_guard();
    let mut harness = Harness::spawn();
    harness.wait_for("Selection [1]:");
    harness.send("1\n2\n12\n");
    harness.wait_for("Engine thinking...");
    harness.close_stdin();
    let (status, output) = harness.wait_exit();
    assert!(status.success(), "output={output}");
    assert!(output.contains("EOF received; active search resolved; exiting."));
}
