use core::fmt;
use std::{
    io,
    thread::{self, JoinHandle},
    time::Duration,
};

use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table, IterativeDeepeningSearchError,
    SearchLimitError, SearchLimits, SearchResult, SearchStopFlag, TranspositionTable,
    TranspositionTableAllocationError,
};
use chess_uci::{EngineOptions, GoCommand, SearchRequest};

/// Failure to prepare, start, execute, or join one adapter-owned search worker.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum SearchWorkerError {
    /// Clock allocation remains owned by Task 17.3.
    ClockManagementPending,
    /// The typed request could not form a valid search-limit combination.
    InvalidLimits(SearchLimitError),
    /// The requested fixed-capacity transposition table could not be allocated.
    TranspositionTableAllocation(TranspositionTableAllocationError),
    /// Production iterative deepening failed.
    Search(IterativeDeepeningSearchError),
    /// The operating system rejected creation of the named worker thread.
    ThreadSpawn {
        /// Portable I/O error classification.
        kind: io::ErrorKind,
        /// Original operating-system error text.
        message: String,
    },
    /// The worker unwound instead of returning a typed result.
    ThreadPanicked,
}

impl fmt::Display for SearchWorkerError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ClockManagementPending => formatter
                .write_str("clock-based go requests require the Task 17.3 UCI time manager"),
            Self::InvalidLimits(error) => error.fmt(formatter),
            Self::TranspositionTableAllocation(error) => error.fmt(formatter),
            Self::Search(error) => error.fmt(formatter),
            Self::ThreadSpawn { kind, message } => {
                write!(
                    formatter,
                    "failed to spawn UCI search worker ({kind:?}): {message}"
                )
            }
            Self::ThreadPanicked => formatter.write_str("UCI search worker panicked"),
        }
    }
}

impl std::error::Error for SearchWorkerError {}

/// One adapter-owned search thread and its request-local explicit stop token.
#[derive(Debug)]
pub struct SearchWorker {
    stop_flag: SearchStopFlag,
    handle: JoinHandle<Result<SearchResult, SearchWorkerError>>,
}

impl SearchWorker {
    /// Starts one production search from an immutable request snapshot.
    ///
    /// No process-global mutable state is used. The worker owns a detached
    /// position, repetition history, transposition table, and stop flag.
    pub fn spawn(request: SearchRequest) -> Result<Self, SearchWorkerError> {
        let game = request.game().clone();
        let command = request.command();
        let options = request.options();
        let stop_flag = SearchStopFlag::new();
        let limits = build_search_limits(command, options, stop_flag.clone())?;
        let table_mebibytes = options.hash_mebibytes();

        let handle = thread::Builder::new()
            .name("chess-uci-search".to_owned())
            .spawn(move || run_search(game, limits, table_mebibytes))
            .map_err(|error| SearchWorkerError::ThreadSpawn {
                kind: error.kind(),
                message: error.to_string(),
            })?;

        Ok(Self { stop_flag, handle })
    }

    /// Requests an orderly stop at the production search cancellation boundary.
    pub fn request_stop(&self) {
        self.stop_flag.request_stop();
    }

    /// Returns whether the worker thread has returned and can be joined without blocking.
    #[must_use]
    pub fn is_finished(&self) -> bool {
        self.handle.is_finished()
    }

    /// Joins the worker and returns its typed production-search result.
    pub fn join(self) -> Result<SearchResult, SearchWorkerError> {
        self.handle
            .join()
            .map_err(|_| SearchWorkerError::ThreadPanicked)?
    }

    /// Requests cancellation and then joins the worker exactly once.
    pub fn stop_and_join(self) -> Result<SearchResult, SearchWorkerError> {
        self.request_stop();
        self.join()
    }
}

/// Single active-search slot owned by one UCI adapter session.
///
/// Starting a replacement search stops and joins the prior worker before the
/// new worker is installed. Position/new-game replacement and shutdown use the
/// same stop-and-join path through [`Self::stop`].
#[derive(Debug, Default)]
pub struct SearchWorkerSlot {
    active: Option<SearchWorker>,
}

impl SearchWorkerSlot {
    /// Creates an empty adapter-owned worker slot.
    #[must_use]
    pub const fn new() -> Self {
        Self { active: None }
    }

    /// Returns whether one worker is currently owned by this slot.
    #[must_use]
    pub const fn is_active(&self) -> bool {
        self.active.is_some()
    }

    /// Stops and joins a prior worker, then starts the replacement request.
    ///
    /// The returned result, when present, belongs to the replaced worker.
    pub fn start(
        &mut self,
        request: SearchRequest,
    ) -> Result<Option<SearchResult>, SearchWorkerError> {
        let previous = self.stop()?;
        self.active = Some(SearchWorker::spawn(request)?);
        Ok(previous)
    }

    /// Requests stop and joins the active worker, if one exists.
    pub fn stop(&mut self) -> Result<Option<SearchResult>, SearchWorkerError> {
        self.active
            .take()
            .map(SearchWorker::stop_and_join)
            .transpose()
    }

    /// Joins a naturally completed worker without blocking.
    pub fn reap_finished(&mut self) -> Option<Result<SearchResult, SearchWorkerError>> {
        if !self.active.as_ref().is_some_and(SearchWorker::is_finished) {
            return None;
        }
        self.active.take().map(SearchWorker::join)
    }

    /// Performs the same orderly stop-and-join operation used by `quit` and EOF.
    pub fn shutdown(&mut self) -> Result<Option<SearchResult>, SearchWorkerError> {
        self.stop()
    }
}

impl Drop for SearchWorkerSlot {
    fn drop(&mut self) {
        if let Some(worker) = self.active.take() {
            let _ignored = worker.stop_and_join();
        }
    }
}

fn build_search_limits(
    command: GoCommand,
    options: EngineOptions,
    stop_flag: SearchStopFlag,
) -> Result<SearchLimits, SearchWorkerError> {
    if has_clock_fields(command) {
        return Err(SearchWorkerError::ClockManagementPending);
    }

    let mut limits = SearchLimits::new().with_stop_flag(stop_flag);
    if command.is_infinite() {
        limits = limits.infinite();
    } else {
        if let Some(depth) = command.depth() {
            limits = limits.with_depth(depth);
        }
        if let Some(nodes) = command.nodes() {
            limits = limits.with_nodes(nodes);
        }
        if let Some(move_time_ms) = command.move_time_ms() {
            limits = limits.with_hard_time(Duration::from_millis(move_time_ms));
        }
    }
    if options.check_extension() {
        limits = limits.with_check_extension();
    }
    limits
        .validate()
        .map_err(SearchWorkerError::InvalidLimits)?;
    Ok(limits)
}

fn has_clock_fields(command: GoCommand) -> bool {
    command.white_time_ms().is_some()
        || command.black_time_ms().is_some()
        || command.white_increment_ms().is_some()
        || command.black_increment_ms().is_some()
        || command.moves_to_go().is_some()
}

fn run_search(
    game: chess_core::Game,
    limits: SearchLimits,
    table_mebibytes: usize,
) -> Result<SearchResult, SearchWorkerError> {
    let mut position = game.position().clone();
    let mut history = game.search_history();
    let mut transposition_table = TranspositionTable::new(table_mebibytes)
        .map_err(SearchWorkerError::TranspositionTableAllocation)?;
    iterative_deepening_search_with_limits_and_transposition_table(
        &mut position,
        &mut history,
        limits,
        &mut transposition_table,
    )
    .map_err(SearchWorkerError::Search)
}

#[cfg(test)]
mod tests {
    use std::io::Cursor;

    use chess_search::SearchLimitTermination;
    use chess_uci::{SearchRequest, UciEvent, UciSession};

    use super::{SearchWorker, SearchWorkerError, SearchWorkerSlot};
    use crate::run_protocol_loop;

    fn request(command: &str) -> SearchRequest {
        let response = UciSession::new().handle_line(command);
        match response.event() {
            Some(UciEvent::StartSearch(request)) => request.as_ref().clone(),
            other => panic!("expected start-search request, found {other:?}"),
        }
    }

    #[test]
    fn finite_worker_runs_production_search_on_detached_state() {
        let source = UciSession::new();
        let source_game = source.game().clone();
        let result = SearchWorker::spawn(request("go depth 1"))
            .expect("worker starts")
            .join()
            .expect("worker search succeeds");

        assert_eq!(
            result.termination(),
            SearchLimitTermination::Depth { depth: 1 }
        );
        assert_eq!(result.completed_depth(), 1);
        assert!(result.best_move().is_some());
        assert!(result.nodes() > 0);
        assert_eq!(source.game(), &source_game);
    }

    #[test]
    fn infinite_worker_obeys_its_request_local_stop_flag() {
        let worker = SearchWorker::spawn(request("go infinite")).expect("worker starts");
        let result = worker.stop_and_join().expect("worker stops cleanly");
        assert_eq!(result.termination(), SearchLimitTermination::ExplicitStop);
    }

    #[test]
    fn replacement_go_stops_and_joins_the_prior_worker() {
        let mut slot = SearchWorkerSlot::new();
        assert!(slot
            .start(request("go infinite"))
            .expect("first worker starts")
            .is_none());
        assert!(slot.is_active());

        let replaced = slot
            .start(request("go depth 1"))
            .expect("replacement worker starts")
            .expect("prior worker result is returned");
        assert_eq!(replaced.termination(), SearchLimitTermination::ExplicitStop);
        assert!(slot.is_active());
        let _replacement = slot.stop().expect("replacement worker joins");
        assert!(!slot.is_active());
    }

    #[test]
    fn clock_request_waits_for_task_17_3_without_spawning() {
        assert_eq!(
            SearchWorker::spawn(request("go wtime 60000 btime 60000"))
                .expect_err("clock request is not allocated early"),
            SearchWorkerError::ClockManagementPending
        );
    }

    #[test]
    fn protocol_state_replacement_and_quit_stop_active_workers() {
        let input = Cursor::new(
            b"go infinite\nposition startpos moves e2e4\ngo infinite\nucinewgame\nisready\nquit\n"
                .as_slice(),
        );
        let mut output = Vec::new();
        run_protocol_loop(input, &mut output).expect("protocol loop shuts down cleanly");
        let output = String::from_utf8(output).expect("protocol output is UTF-8");
        assert_eq!(output, "readyok\n");
    }
}
