use core::fmt;
use std::{
    io,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    thread::{self, JoinHandle},
    time::{Duration, Instant},
};

use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_observer,
    IterativeDeepeningSearchError, SearchLimitError, SearchLimits, SearchResult, SearchStopFlag,
    TranspositionTable, TranspositionTableAllocationError,
};
use chess_uci::{EngineOptions, GoCommand, SearchRequest};

use crate::{
    output::SearchOutput,
    time_manager::{allocate_time_budget, UciTimeManagerError},
};

/// Failure to prepare, start, execute, report, or join one adapter-owned search worker.
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
    /// Search-thread output failed.
    Output {
        /// Portable I/O error classification.
        kind: io::ErrorKind,
        /// Original output error text.
        message: String,
    },
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

impl SearchWorkerError {
    fn from_output_error(error: io::Error) -> Self {
        Self::Output {
            kind: error.kind(),
            message: error.to_string(),
        }
    }

    /// Returns whether the worker already emitted the underlying failure.
    #[must_use]
    pub const fn was_reported_by_worker(&self) -> bool {
        matches!(
            self,
            Self::TranspositionTableAllocation(_) | Self::Search(_)
        )
    }
}

impl fmt::Display for SearchWorkerError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::TimeManager(error) => error.fmt(formatter),
            Self::InvalidLimits(error) => error.fmt(formatter),
            Self::TranspositionTableAllocation(error) => error.fmt(formatter),
            Self::Search(error) => error.fmt(formatter),
            Self::Output { kind, message } => {
                write!(formatter, "UCI search output failed ({kind:?}): {message}")
            }
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
pub struct SearchWorker {
    stop_flag: SearchStopFlag,
    emit_final: Arc<AtomicBool>,
    handle: JoinHandle<Result<SearchResult, SearchWorkerError>>,
}

impl SearchWorker {
    /// Starts one production search from an immutable request snapshot.
    ///
    /// No process-global mutable state is used. The worker owns a detached
    /// position, repetition history, transposition table, and stop flag.
    pub fn spawn(
        request: SearchRequest,
        output: Arc<dyn SearchOutput>,
    ) -> Result<Self, SearchWorkerError> {
        let game = request.game().clone();
        let command = request.command();
        let options = request.options();
        let side_to_move = game.position().side_to_move();
        let stop_flag = SearchStopFlag::new();
        let limits = build_search_limits(command, options, side_to_move, stop_flag.clone())?;
        let table_mebibytes = options.hash_mebibytes();
        let emit_final = Arc::new(AtomicBool::new(true));
        let worker_emit_final = Arc::clone(&emit_final);
        let progress_stop = stop_flag.clone();

        let handle = thread::Builder::new()
            .name("chess-uci-search".to_owned())
            .spawn(move || {
                let outcome = run_search(
                    game,
                    limits,
                    table_mebibytes,
                    progress_stop,
                    Arc::clone(&output),
                );
                match outcome {
                    Ok(result) => {
                        if worker_emit_final.load(Ordering::Acquire) {
                            output
                                .report_bestmove(&result)
                                .map_err(SearchWorkerError::from_output_error)?;
                        }
                        Ok(result)
                    }
                    Err(error) => {
                        if !matches!(&error, SearchWorkerError::Output { .. }) {
                            output
                                .report_error(&error.to_string())
                                .map_err(SearchWorkerError::from_output_error)?;
                        }
                        Err(error)
                    }
                }
            })
            .map_err(|error| SearchWorkerError::ThreadSpawn {
                kind: error.kind(),
                message: error.to_string(),
            })?;

        Ok(Self {
            stop_flag,
            emit_final,
            handle,
        })
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

    /// Requests explicit UCI `stop`, preserving one final `bestmove` record.
    pub fn stop_and_join(self) -> Result<SearchResult, SearchWorkerError> {
        self.stop_flag.request_stop();
        self.join()
    }

    /// Cancels stale work and suppresses a final move from the replaced position.
    pub fn discard_and_join(self) -> Result<SearchResult, SearchWorkerError> {
        self.emit_final.store(false, Ordering::Release);
        self.stop_flag.request_stop();
        self.join()
    }
}

/// Single active-search slot owned by one UCI adapter session.
pub struct SearchWorkerSlot {
    active: Option<SearchWorker>,
    output: Arc<dyn SearchOutput>,
}

impl SearchWorkerSlot {
    /// Creates an empty adapter-owned worker slot using one synchronized output boundary.
    #[must_use]
    pub fn new(output: Arc<dyn SearchOutput>) -> Self {
        Self {
            active: None,
            output,
        }
    }

    /// Stops and joins a prior worker, then starts the replacement request.
    ///
    /// A replacement `go` is treated like an explicit stop of the prior request,
    /// so the prior worker emits exactly one final move before the new search starts.
    pub fn start(
        &mut self,
        request: SearchRequest,
    ) -> Result<Option<SearchResult>, SearchWorkerError> {
        let previous = self.stop()?;
        self.active = Some(SearchWorker::spawn(request, Arc::clone(&self.output))?);
        Ok(previous)
    }

    /// Requests explicit stop and joins the active worker, if one exists.
    pub fn stop(&mut self) -> Result<Option<SearchResult>, SearchWorkerError> {
        self.active
            .take()
            .map(SearchWorker::stop_and_join)
            .transpose()
    }

    /// Cancels and joins stale work without emitting a final move.
    pub fn discard(&mut self) -> Result<Option<SearchResult>, SearchWorkerError> {
        self.active
            .take()
            .map(SearchWorker::discard_and_join)
            .transpose()
    }

    /// Joins a naturally completed worker without blocking.
    pub fn reap_finished(&mut self) -> Option<Result<SearchResult, SearchWorkerError>> {
        if !self.active.as_ref().is_some_and(SearchWorker::is_finished) {
            return None;
        }
        self.active.take().map(SearchWorker::join)
    }

    /// Performs an orderly stale-result-suppressing stop for `quit` and EOF.
    pub fn shutdown(&mut self) -> Result<Option<SearchResult>, SearchWorkerError> {
        self.discard()
    }
}

impl Drop for SearchWorkerSlot {
    fn drop(&mut self) {
        if let Some(worker) = self.active.take() {
            let _ignored = worker.discard_and_join();
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
    progress_stop: SearchStopFlag,
    output: Arc<dyn SearchOutput>,
) -> Result<SearchResult, SearchWorkerError> {
    let mut position = game.position().clone();
    let mut history = game.search_history();
    let mut transposition_table = TranspositionTable::new(table_mebibytes)
        .map_err(SearchWorkerError::TranspositionTableAllocation)?;
    let started = Instant::now();
    let mut output_error = None;

    let result = iterative_deepening_search_with_limits_and_transposition_table_and_observer(
        &mut position,
        &mut history,
        limits,
        &mut transposition_table,
        |progress| {
            if output_error.is_some() {
                return;
            }
            if let Err(error) = output.report_progress(progress, started.elapsed()) {
                progress_stop.request_stop();
                output_error = Some(SearchWorkerError::from_output_error(error));
            }
        },
    );

    if let Some(error) = output_error {
        return Err(error);
    }
    result.map_err(SearchWorkerError::Search)
}

#[cfg(test)]
mod tests {
    use std::{
        io,
        sync::{Arc, Mutex},
        time::Duration,
    };

    use chess_core::Color;
    use chess_search::{SearchProgress, SearchResult, SearchStopFlag};
    use chess_uci::{EngineOptions, GoCommand, SearchRequest, UciEvent, UciSession};

    use super::{build_search_limits, SearchWorker, SearchWorkerError};
    use crate::{output::SearchOutput, time_manager::UciTimeManagerError};

    #[derive(Default)]
    struct RecordingOutput {
        depths: Mutex<Vec<u16>>,
        final_count: Mutex<usize>,
        errors: Mutex<Vec<String>>,
        fail_progress: bool,
    }

    impl RecordingOutput {
        fn depths(&self) -> Vec<u16> {
            self.depths.lock().expect("depth lock").clone()
        }

        fn final_count(&self) -> usize {
            *self.final_count.lock().expect("final-count lock")
        }
    }

    impl SearchOutput for RecordingOutput {
        fn report_progress(
            &self,
            progress: SearchProgress<'_>,
            _elapsed: Duration,
        ) -> io::Result<()> {
            if self.fail_progress {
                return Err(io::Error::other("synthetic progress failure"));
            }
            self.depths
                .lock()
                .expect("depth lock")
                .push(progress.iteration().depth());
            Ok(())
        }

        fn report_bestmove(&self, _result: &SearchResult) -> io::Result<()> {
            let mut count = self.final_count.lock().expect("final-count lock");
            *count += 1;
            Ok(())
        }

        fn report_error(&self, message: &str) -> io::Result<()> {
            self.errors
                .lock()
                .expect("error lock")
                .push(message.to_owned());
            Ok(())
        }
    }

    fn command(input: &str) -> GoCommand {
        request(input).command()
    }

    fn request(input: &str) -> SearchRequest {
        let response = UciSession::new().handle_line(input);
        match response.event() {
            Some(UciEvent::StartSearch(request)) => request.as_ref().clone(),
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
        let command = command("go wtime 90000 btime 12000 winc 5000 binc 400 movestogo 10");
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

    #[test]
    fn natural_completion_reports_each_depth_and_one_final_move() {
        let recorder = Arc::new(RecordingOutput::default());
        let output: Arc<dyn SearchOutput> = recorder.clone();
        let worker = SearchWorker::spawn(request("go depth 2"), output)
            .expect("worker starts from a valid request");
        let result = worker.join().expect("worker search succeeds");

        assert_eq!(result.completed_depth(), 2);
        assert_eq!(recorder.depths(), vec![1, 2]);
        assert_eq!(recorder.final_count(), 1);
    }

    #[test]
    fn explicit_stop_reports_exactly_one_final_move() {
        let recorder = Arc::new(RecordingOutput::default());
        let output: Arc<dyn SearchOutput> = recorder.clone();
        let worker =
            SearchWorker::spawn(request("go infinite"), output).expect("infinite worker starts");
        let _result = worker.stop_and_join().expect("explicit stop joins");

        assert_eq!(recorder.final_count(), 1);
    }

    #[test]
    fn stale_discard_suppresses_final_move() {
        let recorder = Arc::new(RecordingOutput::default());
        let output: Arc<dyn SearchOutput> = recorder.clone();
        let worker =
            SearchWorker::spawn(request("go infinite"), output).expect("infinite worker starts");
        let _result = worker.discard_and_join().expect("stale worker joins");

        assert_eq!(recorder.final_count(), 0);
    }

    #[test]
    fn output_failure_is_typed_and_requests_search_stop() {
        let recorder = Arc::new(RecordingOutput {
            fail_progress: true,
            ..RecordingOutput::default()
        });
        let output: Arc<dyn SearchOutput> = recorder;
        let worker = SearchWorker::spawn(request("go depth 3"), output)
            .expect("worker starts before synthetic output failure");
        let error = worker
            .join()
            .expect_err("progress output failure is returned");

        assert!(matches!(error, SearchWorkerError::Output { .. }));
    }
}
