#![forbid(unsafe_code)]

use std::io::{self, BufWriter, Write};

use chess_console::{input::InputPump, run_console, ExitReason};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut input = InputPump::stdin()?;
    let stdout = io::stdout();
    let mut output = BufWriter::new(stdout.lock());
    let reason = run_console(&input.receiver, &mut output)?;
    output.flush()?;

    // On EOF the reader has received the terminal condition and should finish;
    // join it when possible. On an explicit interactive quit it may still be
    // blocked in an OS stdin read; it owns no game/search state and is allowed
    // to remain process-lifetime. Engine workers are resolved inside runtime.
    if reason == ExitReason::Eof {
        while !input.join_if_finished()? {
            std::thread::yield_now();
        }
    }
    Ok(())
}
