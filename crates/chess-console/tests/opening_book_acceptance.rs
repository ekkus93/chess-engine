use std::{
    io::{Read, Write},
    process::{Child, ChildStdin, Command, Stdio},
    sync::mpsc::{self, Receiver},
    thread::{self, JoinHandle},
    time::{Duration, Instant},
};

const TIMEOUT: Duration = Duration::from_secs(15);

struct Harness {
    child: Child,
    stdin: ChildStdin,
    output: Receiver<Vec<u8>>,
    reader: JoinHandle<()>,
    stdout: Vec<u8>,
}

impl Harness {
    fn spawn() -> Self {
        let mut child = Command::new(env!("CARGO_BIN_EXE_chess-console"))
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
            .expect("console starts");
        let stdin = child.stdin.take().expect("console stdin");
        let mut stdout = child.stdout.take().expect("console stdout");
        let (sender, output) = mpsc::channel();
        let reader = thread::spawn(move || {
            let mut buffer = [0_u8; 4096];
            loop {
                match stdout.read(&mut buffer) {
                    Ok(0) | Err(_) => break,
                    Ok(count) => {
                        if sender.send(buffer[..count].to_vec()).is_err() {
                            break;
                        }
                    }
                }
            }
        });
        Self {
            child,
            stdin,
            output,
            reader,
            stdout: Vec::new(),
        }
    }

    fn send(&mut self, input: &str) {
        self.stdin.write_all(input.as_bytes()).expect("write input");
        self.stdin.flush().expect("flush input");
    }

    fn wait_for(&mut self, marker: &str) {
        let deadline = Instant::now() + TIMEOUT;
        loop {
            while let Ok(chunk) = self.output.try_recv() {
                self.stdout.extend_from_slice(&chunk);
            }
            if String::from_utf8_lossy(&self.stdout).contains(marker) {
                return;
            }
            if let Some(status) = self.child.try_wait().expect("child status") {
                panic!(
                    "console exited before {marker:?}: {status}; stdout={:?}",
                    String::from_utf8_lossy(&self.stdout)
                );
            }
            if Instant::now() >= deadline {
                let _ = self.child.kill();
                panic!(
                    "timeout waiting for {marker:?}; stdout={:?}",
                    String::from_utf8_lossy(&self.stdout)
                );
            }
            match self.output.recv_timeout(Duration::from_millis(100)) {
                Ok(chunk) => self.stdout.extend_from_slice(&chunk),
                Err(mpsc::RecvTimeoutError::Timeout) => {}
                Err(mpsc::RecvTimeoutError::Disconnected) => {}
            }
        }
    }

    fn finish(mut self) {
        let deadline = Instant::now() + TIMEOUT;
        let status = loop {
            if let Some(status) = self.child.try_wait().expect("child status") {
                break status;
            }
            if Instant::now() >= deadline {
                let _ = self.child.kill();
                panic!(
                    "console did not exit; stdout={:?}",
                    String::from_utf8_lossy(&self.stdout)
                );
            }
            thread::sleep(Duration::from_millis(20));
        };
        drop(self.stdin);
        self.reader.join().expect("stdout reader joins");
        while let Ok(chunk) = self.output.try_recv() {
            self.stdout.extend_from_slice(&chunk);
        }
        assert!(
            status.success(),
            "console failed: {status}; stdout={:?}",
            String::from_utf8_lossy(&self.stdout)
        );
    }
}

#[test]
fn human_white_gets_sicilian_book_reply_after_e2e4() {
    let mut console = Harness::spawn();
    console.wait_for("Selection [1]:");
    console.send("1\n1\n12\n");
    console.wait_for("move> ");
    console.send("e2e4\n");
    console.wait_for("Engine plays: c7c5");
    console.send("quit\nyes\n");
    console.finish();
}

#[test]
fn human_black_gets_e2e4_from_book_before_search() {
    let mut console = Harness::spawn();
    console.wait_for("Selection [1]:");
    console.send("1\n2\n12\n");
    console.wait_for("Engine plays: e2e4");
    console.wait_for("Black to move");
    console.send("quit\nyes\n");
    console.finish();
}
