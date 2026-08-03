#![forbid(unsafe_code)]
//! Standalone Universal Chess Interface process adapter.
//!
//! The protocol session owns mutable game state on the main thread. Search runs
//! on one adapter-owned worker with request-local cancellation and synchronized
//! protocol output.

mod output;
mod time_manager;
mod worker;

use std::{
    io::{self, BufRead, Write},
    sync::Arc,
};

use chess_uci::{UciEvent, UciSession};
use output::{SearchOutput, SharedUciOutput};
use worker::{SearchWorkerError, SearchWorkerSlot};

fn main() -> io::Result<()> {
    let stdin = io::stdin();
    run_protocol_loop(stdin.lock(), io::stdout())
}

fn run_protocol_loop<R, W>(input: R, output: W) -> io::Result<()>
where
    R: BufRead,
    W: Write + Send + 'static,
{
    let output = Arc::new(SharedUciOutput::new(output));
    let search_output: Arc<dyn SearchOutput> = output.clone();
    let mut session = UciSession::new();
    let mut workers = SearchWorkerSlot::new(search_output);

    for line in input.lines() {
        if let Some(outcome) = workers.reap_finished() {
            report_worker_outcome(output.as_ref(), outcome)?;
        }

        let line = line?;
        let command = line.split_whitespace().next();
        let response = session.handle_line(&line);
        for current in response.lines() {
            output.write_line(current)?;
        }

        let state_replaced =
            matches!(command, Some("position" | "ucinewgame")) && response.lines().is_empty();
        if state_replaced {
            report_optional_worker_outcome(output.as_ref(), workers.discard())?;
        }

        match response.event() {
            Some(UciEvent::StartSearch(request)) => {
                report_optional_worker_outcome(
                    output.as_ref(),
                    workers.start(request.as_ref().clone()),
                )?;
            }
            Some(UciEvent::StopSearch) => {
                report_optional_worker_outcome(output.as_ref(), workers.stop())?;
            }
            Some(UciEvent::Quit) => {
                report_optional_worker_outcome(output.as_ref(), workers.shutdown())?;
                return Ok(());
            }
            None => {}
        }
    }

    report_optional_worker_outcome(output.as_ref(), workers.shutdown())
}

fn report_optional_worker_outcome<W>(
    output: &SharedUciOutput<W>,
    outcome: Result<Option<chess_search::SearchResult>, SearchWorkerError>,
) -> io::Result<()>
where
    W: Write,
{
    match outcome {
        Ok(Some(result)) => report_worker_outcome(output, Ok(result)),
        Ok(None) => Ok(()),
        Err(error) => report_worker_outcome(output, Err(error)),
    }
}

fn report_worker_outcome<W>(
    output: &SharedUciOutput<W>,
    outcome: Result<chess_search::SearchResult, SearchWorkerError>,
) -> io::Result<()>
where
    W: Write,
{
    if let Err(error) = outcome {
        if !error.was_reported_by_worker() {
            output.write_line(&format!("info string error: {error}"))?;
        }
    }
    Ok(())
}
