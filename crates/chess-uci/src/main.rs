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
    env,
    ffi::OsString,
    fs,
    io::{self, BufRead, Write},
    path::PathBuf,
    sync::Arc,
};

use chess_book::{BookSelector, IndexedBook};
use chess_uci::{SearchRequest, UciEvent, UciSession};
use output::{SearchOutput, SharedUciOutput};
use worker::{SearchWorkerError, SearchWorkerSlot};

fn main() -> io::Result<()> {
    let opening_book = load_opening_book(env::args_os().skip(1))?;
    let stdin = io::stdin();
    run_protocol_loop_with_book(stdin.lock(), io::stdout(), opening_book)
}

fn load_opening_book<I>(arguments: I) -> io::Result<Option<IndexedBook>>
where
    I: IntoIterator<Item = OsString>,
{
    let mut arguments = arguments.into_iter();
    let Some(flag) = arguments.next() else {
        return Ok(None);
    };
    if flag != "--book" {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            format!("unsupported argument {flag:?}; expected --book <path>"),
        ));
    }
    let path = arguments
        .next()
        .map(PathBuf::from)
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "--book requires a path"))?;
    if let Some(extra) = arguments.next() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            format!("unexpected extra argument {extra:?}"),
        ));
    }
    let bytes = fs::read(&path)?;
    IndexedBook::from_bytes(&bytes).map(Some).map_err(|error| {
        io::Error::new(
            io::ErrorKind::InvalidData,
            format!("invalid opening book {}: {error}", path.display()),
        )
    })
}

fn run_protocol_loop_with_book<R, W>(
    input: R,
    output: W,
    opening_book: Option<IndexedBook>,
) -> io::Result<()>
where
    R: BufRead,
    W: Write + Send + 'static,
{
    let output = Arc::new(SharedUciOutput::new(output));
    let search_output: Arc<dyn SearchOutput> = output.clone();
    let mut session = UciSession::new();
    let mut workers = SearchWorkerSlot::new(search_output);
    let mut book_selector = BookSelector::deterministic_highest_weight();

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
                match select_opening_book_move(
                    &mut book_selector,
                    opening_book.as_ref(),
                    request.as_ref(),
                ) {
                    Ok(Some(chess_move)) => {
                        report_optional_worker_outcome(output.as_ref(), workers.discard())?;
                        output.write_line(&format!("bestmove {chess_move}"))?;
                    }
                    Ok(None) => {
                        report_optional_worker_outcome(
                            output.as_ref(),
                            workers.start(request.as_ref().clone()),
                        )?;
                    }
                    Err(error) => {
                        report_optional_worker_outcome(output.as_ref(), workers.discard())?;
                        output.write_line(&format!("info string error: {error}"))?;
                    }
                }
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

fn select_opening_book_move(
    selector: &mut BookSelector,
    opening_book: Option<&IndexedBook>,
    request: &SearchRequest,
) -> Result<Option<String>, String> {
    if !request.options().own_book() {
        return Ok(None);
    }
    let Some(opening_book) = opening_book else {
        return Ok(None);
    };
    selector
        .select(opening_book, request.game().position())
        .map(|selected| selected.map(|current| current.chess_move().to_uci()))
        .map_err(|error| error.to_string())
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

#[cfg(test)]
mod book_tests {
    use super::*;
    use chess_book::IndexedBookRecord;
    use chess_core::Position;

    fn request(own_book: bool) -> SearchRequest {
        let mut session = UciSession::new();
        if own_book {
            assert!(session
                .handle_line("setoption name OwnBook value true")
                .lines()
                .is_empty());
        }
        let response = session.handle_line("go depth 1");
        match response.event() {
            Some(UciEvent::StartSearch(request)) => request.as_ref().clone(),
            other => panic!("expected search request, found {other:?}"),
        }
    }

    fn starting_book() -> IndexedBook {
        let position = Position::starting();
        IndexedBook::from_records(vec![IndexedBookRecord::new(
            &position,
            "e2e4".parse().expect("test move syntax is valid"),
            100,
        )
        .expect("test record is valid")])
        .expect("test book is valid")
    }

    #[test]
    fn own_book_hit_bypasses_search_only_when_enabled_and_supplied() {
        let book = starting_book();
        let mut selector = BookSelector::deterministic_highest_weight();
        assert_eq!(
            select_opening_book_move(&mut selector, Some(&book), &request(true)),
            Ok(Some("e2e4".to_owned()))
        );
        assert_eq!(
            select_opening_book_move(&mut selector, Some(&book), &request(false)),
            Ok(None)
        );
        assert_eq!(
            select_opening_book_move(&mut selector, None, &request(true)),
            Ok(None)
        );
    }
}
