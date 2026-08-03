#![forbid(unsafe_code)]
//! Standalone Universal Chess Interface process adapter.
//!
//! The protocol session owns mutable game state on the main thread. Search runs
//! on one adapter-owned worker with request-local cancellation and no global
//! mutable search control.

mod worker;

use std::io::{self, BufRead, Write};

use chess_uci::{UciEvent, UciSession};
use worker::{SearchWorkerError, SearchWorkerSlot};

fn main() -> io::Result<()> {
    let stdin = io::stdin();
    let stdout = io::stdout();
    run_protocol_loop(stdin.lock(), stdout.lock())
}

fn run_protocol_loop<R, W>(input: R, mut output: W) -> io::Result<()>
where
    R: BufRead,
    W: Write,
{
    let mut session = UciSession::new();
    let mut workers = SearchWorkerSlot::new();

    for line in input.lines() {
        if let Some(outcome) = workers.reap_finished() {
            report_worker_outcome(&mut output, outcome)?;
        }

        let line = line?;
        let command = line.split_whitespace().next();
        let response = session.handle_line(&line);
        for current in response.lines() {
            writeln!(output, "{current}")?;
        }

        let state_replaced =
            matches!(command, Some("position" | "ucinewgame")) && response.lines().is_empty();
        if state_replaced {
            if let Err(error) = workers.stop() {
                report_worker_error(&mut output, &error)?;
            }
        }

        match response.event() {
            Some(UciEvent::StartSearch(request)) => {
                if let Err(error) = workers.start(request.as_ref().clone()) {
                    report_worker_error(&mut output, &error)?;
                }
            }
            Some(UciEvent::StopSearch) => {
                if let Err(error) = workers.stop() {
                    report_worker_error(&mut output, &error)?;
                }
            }
            Some(UciEvent::Quit) => {
                if let Err(error) = workers.shutdown() {
                    report_worker_error(&mut output, &error)?;
                }
                output.flush()?;
                return Ok(());
            }
            None => {}
        }
        output.flush()?;
    }

    if let Err(error) = workers.shutdown() {
        report_worker_error(&mut output, &error)?;
    }
    output.flush()
}

fn report_worker_outcome<W>(
    output: &mut W,
    outcome: Result<chess_search::SearchResult, SearchWorkerError>,
) -> io::Result<()>
where
    W: Write,
{
    if let Err(error) = outcome {
        report_worker_error(output, &error)?;
    }
    Ok(())
}

fn report_worker_error<W>(output: &mut W, error: &SearchWorkerError) -> io::Result<()>
where
    W: Write,
{
    writeln!(output, "info string error: {error}")
}
