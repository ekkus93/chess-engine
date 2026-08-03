#![forbid(unsafe_code)]

use std::{
    io::{BufRead, BufReader, Write},
    process::{Child, ChildStdin, Command, ExitStatus, Stdio},
    sync::mpsc::{self, Receiver, RecvTimeoutError, TryRecvError},
    thread::{self, JoinHandle},
    time::{Duration, Instant},
};

use chess_core::{Game, Position, UciMove};

const OUTPUT_TIMEOUT: Duration = Duration::from_secs(10);
const EXIT_TIMEOUT: Duration = Duration::from_secs(5);
const POLL_INTERVAL: Duration = Duration::from_millis(10);

#[derive(Debug)]
enum OutputEvent {
    Line(String),
    Error(String),
    Eof,
}

struct UciProcess {
    child: Child,
    stdin: Option<ChildStdin>,
    output: Receiver<OutputEvent>,
    reader: Option<JoinHandle<()>>,
}

impl UciProcess {
    fn spawn() -> Self {
        let mut child = Command::new(env!("CARGO_BIN_EXE_chess-uci"))
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
            .expect("UCI binary starts");
        let stdin = child.stdin.take().expect("child stdin is piped");
        let stdout = child.stdout.take().expect("child stdout is piped");
        let (sender, output) = mpsc::channel();
        let reader = thread::spawn(move || {
            let mut reader = BufReader::new(stdout);
            let mut line = String::new();
            loop {
                line.clear();
                match reader.read_line(&mut line) {
                    Ok(0) => {
                        let _ = sender.send(OutputEvent::Eof);
                        return;
                    }
                    Ok(_) => {
                        if line.ends_with('\n') {
                            line.pop();
                            if line.ends_with('\r') {
                                line.pop();
                            }
                        }
                        if sender.send(OutputEvent::Line(line.clone())).is_err() {
                            return;
                        }
                    }
                    Err(error) => {
                        let _ = sender.send(OutputEvent::Error(error.to_string()));
                        return;
                    }
                }
            }
        });

        Self {
            child,
            stdin: Some(stdin),
            output,
            reader: Some(reader),
        }
    }

    fn send(&mut self, command: &str) {
        let stdin = self.stdin.as_mut().expect("child stdin remains open");
        writeln!(stdin, "{command}").expect("write UCI command");
        stdin.flush().expect("flush UCI command");
    }

    fn next_line(&self, timeout: Duration) -> String {
        match self.output.recv_timeout(timeout) {
            Ok(OutputEvent::Line(line)) => line,
            Ok(OutputEvent::Error(error)) => panic!("UCI stdout reader failed: {error}"),
            Ok(OutputEvent::Eof) => panic!("UCI process closed stdout before the expected line"),
            Err(RecvTimeoutError::Timeout) => panic!("timed out waiting for UCI output"),
            Err(RecvTimeoutError::Disconnected) => {
                panic!("UCI stdout reader disconnected before the expected line")
            }
        }
    }

    fn read_until<F>(&self, timeout: Duration, mut predicate: F) -> Vec<String>
    where
        F: FnMut(&str) -> bool,
    {
        let deadline = Instant::now() + timeout;
        let mut lines = Vec::new();
        loop {
            let remaining = deadline.saturating_duration_since(Instant::now());
            assert!(
                !remaining.is_zero(),
                "timed out waiting for matching UCI output; observed {lines:?}"
            );
            let line = self.next_line(remaining);
            let matched = predicate(&line);
            lines.push(line);
            if matched {
                return lines;
            }
        }
    }

    fn read_through_bestmove(&self) -> Vec<String> {
        self.read_until(OUTPUT_TIMEOUT, |line| line.starts_with("bestmove "))
    }

    fn wait_for_exit(&mut self, timeout: Duration) -> ExitStatus {
        let deadline = Instant::now() + timeout;
        let status = loop {
            match self.child.try_wait().expect("query UCI process status") {
                Some(status) => break status,
                None if Instant::now() < deadline => thread::sleep(POLL_INTERVAL),
                None => {
                    let _ = self.child.kill();
                    let _ = self.child.wait();
                    panic!("UCI process did not exit within {timeout:?}");
                }
            }
        };
        self.stdin.take();
        if let Some(reader) = self.reader.take() {
            reader.join().expect("stdout reader thread joins");
        }
        status
    }

    fn drain_lines(&self) -> Vec<String> {
        let mut lines = Vec::new();
        loop {
            match self.output.try_recv() {
                Ok(OutputEvent::Line(line)) => lines.push(line),
                Ok(OutputEvent::Error(error)) => panic!("UCI stdout reader failed: {error}"),
                Ok(OutputEvent::Eof) | Err(TryRecvError::Disconnected) => return lines,
                Err(TryRecvError::Empty) => return lines,
            }
        }
    }

    fn quit_cleanly(&mut self) {
        self.send("quit");
        let status = self.wait_for_exit(EXIT_TIMEOUT);
        assert!(status.success(), "UCI process exited with {status}");
    }
}

impl Drop for UciProcess {
    fn drop(&mut self) {
        self.stdin.take();
        if matches!(self.child.try_wait(), Ok(None)) {
            let _ = self.child.kill();
            let _ = self.child.wait();
        }
        if let Some(reader) = self.reader.take() {
            let _ = reader.join();
        }
    }
}

fn bestmove_line(lines: &[String]) -> &str {
    lines
        .iter()
        .rev()
        .find(|line| line.starts_with("bestmove "))
        .map(String::as_str)
        .expect("transcript contains bestmove")
}

fn bestmove_text(line: &str) -> &str {
    let mut tokens = line.split_whitespace();
    assert_eq!(tokens.next(), Some("bestmove"), "unexpected line {line:?}");
    tokens.next().expect("bestmove includes a move")
}

fn assert_legal_bestmove(mut game: Game, line: &str) {
    let text = bestmove_text(line);
    assert_ne!(text, "0000", "nonterminal position returned null move");
    let syntax = text.parse::<UciMove>().expect("bestmove uses UCI syntax");
    let legal_moves = game.legal_moves().expect("generate expected legal moves");
    assert!(
        legal_moves
            .iter()
            .any(|candidate| syntax.matches(candidate)),
        "bestmove {text:?} is not legal in the expected position"
    );
}

fn game_after_moves(moves: &[&str]) -> Game {
    let mut game = Game::starting();
    for text in moves {
        let syntax = text
            .parse::<UciMove>()
            .expect("fixture move uses UCI syntax");
        let legal_moves = game.legal_moves().expect("generate fixture legal moves");
        let current = legal_moves
            .iter()
            .find(|candidate| syntax.matches(*candidate))
            .expect("fixture move is legal");
        game.make_move(current).expect("apply fixture move");
    }
    game
}

fn game_from_fen(fen: &str) -> Game {
    Game::new(Position::from_fen(fen).expect("fixture FEN is valid"))
}

#[test]
fn handshake_transcript_is_exact_and_quit_exits_cleanly() {
    let mut process = UciProcess::spawn();
    process.send("uci");

    let actual = (0..5)
        .map(|_| process.next_line(OUTPUT_TIMEOUT))
        .collect::<Vec<_>>();
    let expected = vec![
        format!("id name chess-engine-rust {}", env!("CARGO_PKG_VERSION")),
        "id author Phillip Chin".to_owned(),
        "option name Hash type spin default 1 min 1 max 65536".to_owned(),
        "option name CheckExtension type check default false".to_owned(),
        "uciok".to_owned(),
    ];
    assert_eq!(actual, expected);

    process.send("isready");
    assert_eq!(process.next_line(OUTPUT_TIMEOUT), "readyok");
    process.quit_cleanly();
}

#[test]
fn start_position_and_fen_searches_return_legal_fixed_depth_moves() {
    let mut process = UciProcess::spawn();

    process.send("position startpos moves e2e4 e7e5");
    process.send("go depth 1");
    let startpos_lines = process.read_through_bestmove();
    assert!(
        startpos_lines
            .iter()
            .any(|line| line.starts_with("info depth 1 ")),
        "missing completed-depth info: {startpos_lines:?}"
    );
    assert_legal_bestmove(
        game_after_moves(&["e2e4", "e7e5"]),
        bestmove_line(&startpos_lines),
    );

    let fen = "7k/8/8/8/8/8/8/KQ6 w - - 0 1";
    process.send(&format!("position fen {fen}"));
    process.send("go depth 1");
    let fen_lines = process.read_through_bestmove();
    assert!(
        fen_lines
            .iter()
            .any(|line| line.starts_with("info depth 1 ")),
        "missing completed-depth info: {fen_lines:?}"
    );
    assert_legal_bestmove(game_from_fen(fen), bestmove_line(&fen_lines));

    process.quit_cleanly();
}

#[test]
fn illegal_position_input_is_fail_visible_and_transactional() {
    let mut process = UciProcess::spawn();
    process.send("position startpos moves e2e4");
    process.send("position startpos moves e2e5");
    assert_eq!(
        process.next_line(OUTPUT_TIMEOUT),
        "info string error: illegal UCI move \"e2e5\" at replay ply 1"
    );

    process.send("go depth 1");
    let lines = process.read_through_bestmove();
    assert_legal_bestmove(game_after_moves(&["e2e4"]), bestmove_line(&lines));
    process.quit_cleanly();
}

#[test]
fn checkmate_and_stalemate_return_null_bestmove() {
    let mut process = UciProcess::spawn();
    for fen in [
        "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1",
        "7k/5Q2/7K/8/8/8/8/8 b - - 0 1",
    ] {
        process.send(&format!("position fen {fen}"));
        process.send("go depth 1");
        let lines = process.read_through_bestmove();
        assert_eq!(bestmove_line(&lines), "bestmove 0000", "{lines:?}");
    }
    process.quit_cleanly();
}

#[test]
fn stop_interrupts_infinite_search_and_session_remains_ready() {
    let mut process = UciProcess::spawn();
    process.send("position startpos");
    process.send("go infinite");
    let before_stop = process.read_until(OUTPUT_TIMEOUT, |line| line.starts_with("info depth "));
    assert!(before_stop
        .iter()
        .all(|line| !line.starts_with("bestmove ")));

    let stop_started = Instant::now();
    process.send("stop");
    let after_stop = process.read_through_bestmove();
    assert!(
        stop_started.elapsed() < OUTPUT_TIMEOUT,
        "stop did not complete within the bounded integration timeout"
    );
    assert_legal_bestmove(Game::starting(), bestmove_line(&after_stop));

    process.send("isready");
    let readiness = process.read_until(OUTPUT_TIMEOUT, |line| line == "readyok");
    let bestmove_count = before_stop
        .iter()
        .chain(after_stop.iter())
        .chain(readiness.iter())
        .filter(|line| line.starts_with("bestmove "))
        .count();
    assert_eq!(bestmove_count, 1, "unexpected stop transcript");
    process.quit_cleanly();
}

#[test]
fn quit_interrupts_active_search_without_stale_bestmove() {
    let mut process = UciProcess::spawn();
    process.send("position startpos");
    process.send("go infinite");
    let before_quit = process.read_until(OUTPUT_TIMEOUT, |line| line.starts_with("info depth "));
    assert!(before_quit
        .iter()
        .all(|line| !line.starts_with("bestmove ")));

    process.send("quit");
    let status = process.wait_for_exit(EXIT_TIMEOUT);
    assert!(status.success(), "UCI process exited with {status}");
    let remaining = process.drain_lines();
    assert!(
        remaining.iter().all(|line| !line.starts_with("bestmove ")),
        "quit leaked a stale final move: {remaining:?}"
    );
}

#[test]
fn concurrent_processes_keep_state_and_stdout_isolated() {
    let mut terminal = UciProcess::spawn();
    let mut normal = UciProcess::spawn();

    terminal.send("position fen 7k/5Q2/7K/8/8/8/8/8 b - - 0 1");
    normal.send("position startpos");
    terminal.send("go depth 1");
    normal.send("go depth 1");

    let terminal_lines = terminal.read_through_bestmove();
    let normal_lines = normal.read_through_bestmove();
    assert_eq!(bestmove_line(&terminal_lines), "bestmove 0000");
    assert_legal_bestmove(Game::starting(), bestmove_line(&normal_lines));
    assert!(
        normal_lines.iter().all(|line| line != "bestmove 0000"),
        "terminal-session output leaked into normal session: {normal_lines:?}"
    );

    terminal.quit_cleanly();
    normal.quit_cleanly();
}
