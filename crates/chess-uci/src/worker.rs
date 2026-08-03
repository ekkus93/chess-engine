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

use crate::time_manager::{allocate_time_budget, UciTimeManagerError};

/// Failure to prepare, start, execute, or join one adapter-owned search worker.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum SearchWorkerError {
    /// UCI clock fields could not produce a valid side-to-move budget.
    TimeManager(UciTimeManagerError),
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
            Self::TimeManager(error) => error.fmt(formatter),
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
        let side_to_move = game.position().side_to_move();
        let stop_flag = SearchStopFlag::new();
        let limits = build_search_limits(command, options, side_to_move, stop_flag.clone())?;
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
    side_to_move: chess_core::Color,
    stop_flag: SearchStopFlag,
) -> Result<SearchLimits, SearchWorkerError> {
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
        if let Some(budget) =
            allocate_time_budget(command, side_to_move).map_err(SearchWorkerError::TimeManager)?
        {
            limits = limits
                .with_soft_time(budget.soft())
                .with_hard_time(budget.hard());
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
    use std::time::Duration;

    use chess_core::Color;
    use chess_search::SearchStopFlag;
    use chess_uci::{EngineOptions, GoCommand, UciEvent, UciSession};

    use super::{build_search_limits, SearchWorkerError};
    use crate::time_manager::UciTimeManagerError;

    fn command(input: &str) -> GoCommand {
        let response = UciSession::new().handle_line(input);
        match response.event() {
            Some(UciEvent::StartSearch(request)) => request.command(),
            other => panic!("expected start-search event, found {other:?}"),
        }
    }

    #[test]
    fn clock_budget_is_combined_with_explicit_depth_and_nodes() {
        let limits = build_search_limits(
            command(
                "go depth 7 nodes 50000 wtime 60000 btime 50000 winc 1000 binc 200 movestogo 20",
            ),
            EngineOptions::default(),
            Color::White,
            SearchStopFlag::new(),
        )
        .expect("combined clock limits are valid");

        assert_eq!(limits.depth(), Some(7));
        assert_eq!(limits.nodes(), Some(50000));
        assert_eq!(limits.soft_time(), Some(Duration::from_millis(3600)));
        assert_eq!(limits.hard_time(), Some(Duration::from_millis(7200)));
        assert!(limits.stop_flag().is_some());
    }

    #[test]
    fn worker_limit_conversion_uses_the_position_side_to_move() {
        let command = command(
            "go wtime 90000 btime 12000 winc 5000 binc 400 movestogo 10",
        );
        let white = build_search_limits(
            command,
            EngineOptions::default(),
            Color::White,
            SearchStopFlag::new(),
        )
        .expect("white limits are valid");
        let black = build_search_limits(
            command,
            EngineOptions::default(),
            Color::Black,
            SearchStopFlag::new(),
        )
        .expect("black limits are valid");

        assert_eq!(white.soft_time(), Some(Duration::from_millis(12300)));
        assert_eq!(white.hard_time(), Some(Duration::from_millis(24600)));
        assert_eq!(black.soft_time(), Some(Duration::from_millis(1440)));
        assert_eq!(black.hard_time(), Some(Duration::from_millis(2880)));
    }

    #[test]
    fn move_time_behavior_remains_a_hard_limit_only() {
        let limits = build_search_limits(
            command("go movetime 250"),
            EngineOptions::default(),
            Color::White,
            SearchStopFlag::new(),
        )
        .expect("move-time limit is valid");

        assert_eq!(limits.soft_time(), None);
        assert_eq!(limits.hard_time(), Some(Duration::from_millis(250)));
    }

    #[test]
    fn missing_side_to_move_clock_is_a_typed_worker_error() {
        let error = build_search_limits(
            command("go btime 1000"),
            EngineOptions::default(),
            Color::White,
            SearchStopFlag::new(),
        )
        .expect_err("missing white clock must fail");

        assert_eq!(
            error,
            SearchWorkerError::TimeManager(UciTimeManagerError::MissingSideToMoveClock {
                side: Color::White,
            })
        );
    }
}
