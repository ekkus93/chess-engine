use core::fmt;
use std::{
    sync::{
        atomic::{AtomicBool, Ordering},
        mpsc::{self, Receiver, Sender},
        Arc,
    },
    thread::{self, JoinHandle},
    time::{Duration, Instant},
};

use chess_core::{Game, Move};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_observer,
    IterativeDeepeningSearchError, Score, SearchLimits, SearchProgress, SearchStopFlag,
    TranspositionTable, DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,
};

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct SearchTicket {
    pub generation: u64,
    pub request: u64,
}

#[derive(Clone, Debug)]
pub struct SearchRequest {
    pub ticket: SearchTicket,
    pub game: Game,
    pub depth: u16,
}

#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct SearchMetrics {
    pub depth: Option<u16>,
    pub score: Option<Score>,
    pub nodes: Option<u64>,
    pub nps: Option<u64>,
    pub elapsed: Option<Duration>,
    pub principal_variation: Vec<Move>,
    pub hash_full_per_mille: Option<u16>,
}

impl SearchMetrics {
    fn from_progress(progress: SearchProgress<'_>, elapsed: Duration) -> Self {
        let iteration = progress.iteration();
        let nodes = progress.nodes();
        Self {
            depth: Some(iteration.depth()),
            score: Some(iteration.score()),
            nodes: Some(nodes),
            nps: calculate_nps(nodes, elapsed),
            elapsed: Some(elapsed),
            principal_variation: iteration.principal_variation().moves().to_vec(),
            hash_full_per_mille: Some(iteration.hash_full().per_mille()),
        }
    }

    fn from_result(result: &chess_search::SearchResult) -> Option<Self> {
        let iteration = result.completed().final_iteration()?;
        let elapsed = result.elapsed();
        Some(Self {
            depth: Some(iteration.depth()),
            score: Some(iteration.score()),
            nodes: Some(result.nodes()),
            nps: calculate_nps(result.nodes(), elapsed),
            elapsed: Some(elapsed),
            principal_variation: iteration.principal_variation().moves().to_vec(),
            hash_full_per_mille: Some(iteration.hash_full().per_mille()),
        })
    }
}

#[must_use]
pub fn calculate_nps(nodes: u64, elapsed: Duration) -> Option<u64> {
    let nanos = elapsed.as_nanos();
    if nanos == 0 {
        return None;
    }
    let per_second = u128::from(nodes).saturating_mul(1_000_000_000) / nanos;
    Some(u64::try_from(per_second).unwrap_or(u64::MAX))
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum EngineEvent {
    Progress {
        ticket: SearchTicket,
        metrics: SearchMetrics,
    },
    Completed {
        ticket: SearchTicket,
        best_move: Move,
        metrics: SearchMetrics,
    },
    Cancelled {
        ticket: SearchTicket,
    },
    Failed {
        ticket: SearchTicket,
        message: String,
    },
}

impl EngineEvent {
    #[must_use]
    pub const fn ticket(&self) -> SearchTicket {
        match self {
            Self::Progress { ticket, .. }
            | Self::Completed { ticket, .. }
            | Self::Cancelled { ticket }
            | Self::Failed { ticket, .. } => *ticket,
        }
    }

    #[must_use]
    pub const fn is_final(&self) -> bool {
        !matches!(self, Self::Progress { .. })
    }
}

#[derive(Debug)]
pub enum SearchWorkerError {
    ThreadSpawn {
        kind: std::io::ErrorKind,
        message: String,
    },
    ThreadPanicked,
    EventChannelClosed,
}

impl fmt::Display for SearchWorkerError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ThreadSpawn { kind, message } => {
                write!(
                    formatter,
                    "failed to spawn interactive search worker ({kind:?}): {message}"
                )
            }
            Self::ThreadPanicked => formatter.write_str("interactive search worker panicked"),
            Self::EventChannelClosed => {
                formatter.write_str("interactive search event channel closed")
            }
        }
    }
}

impl std::error::Error for SearchWorkerError {}

pub struct SearchWorker {
    stop_flag: SearchStopFlag,
    discard_final: Arc<AtomicBool>,
    handle: Option<JoinHandle<Result<(), SearchWorkerError>>>,
}

impl SearchWorker {
    pub fn spawn(
        request: SearchRequest,
    ) -> Result<(Self, Receiver<EngineEvent>), SearchWorkerError> {
        let stop_flag = SearchStopFlag::new();
        let discard_final = Arc::new(AtomicBool::new(false));
        let worker_stop = stop_flag.clone();
        let worker_discard = Arc::clone(&discard_final);
        let (sender, receiver) = mpsc::channel();

        let handle = thread::Builder::new()
            .name("chess-app-search".to_owned())
            .spawn(move || run_request(request, worker_stop, worker_discard, sender))
            .map_err(|error| SearchWorkerError::ThreadSpawn {
                kind: error.kind(),
                message: error.to_string(),
            })?;

        Ok((
            Self {
                stop_flag,
                discard_final,
                handle: Some(handle),
            },
            receiver,
        ))
    }

    #[must_use]
    pub fn is_finished(&self) -> bool {
        match self.handle.as_ref() {
            Some(handle) => handle.is_finished(),
            None => true,
        }
    }

    pub fn join(&mut self) -> Result<(), SearchWorkerError> {
        let Some(handle) = self.handle.take() else {
            return Ok(());
        };
        handle
            .join()
            .map_err(|_| SearchWorkerError::ThreadPanicked)?
    }

    pub fn cancel_and_join(&mut self) -> Result<(), SearchWorkerError> {
        self.discard_final.store(true, Ordering::Release);
        self.stop_flag.request_stop();
        self.join()
    }

    #[doc(hidden)]
    pub fn finished_with_events_for_test(
        events: Vec<EngineEvent>,
    ) -> (Self, Receiver<EngineEvent>) {
        let stop_flag = SearchStopFlag::new();
        let discard_final = Arc::new(AtomicBool::new(false));
        let (sender, receiver) = mpsc::channel();
        for event in events {
            if sender.send(event).is_err() {
                break;
            }
        }
        drop(sender);
        let handle = thread::spawn(|| Ok(()));
        while !handle.is_finished() {
            thread::yield_now();
        }
        (
            Self {
                stop_flag,
                discard_final,
                handle: Some(handle),
            },
            receiver,
        )
    }

    #[doc(hidden)]
    pub fn waiting_with_event_for_test(event: EngineEvent) -> (Self, Receiver<EngineEvent>) {
        let stop_flag = SearchStopFlag::new();
        let discard_final = Arc::new(AtomicBool::new(false));
        let worker_discard = Arc::clone(&discard_final);
        let (sender, receiver) = mpsc::channel();
        let _ = sender.send(event);
        drop(sender);
        let handle = thread::spawn(move || {
            while !worker_discard.load(Ordering::Acquire) {
                thread::yield_now();
            }
            Ok(())
        });
        (
            Self {
                stop_flag,
                discard_final,
                handle: Some(handle),
            },
            receiver,
        )
    }

    #[doc(hidden)]
    pub fn finished_without_event_for_test() -> (Self, Receiver<EngineEvent>) {
        let stop_flag = SearchStopFlag::new();
        let discard_final = Arc::new(AtomicBool::new(false));
        let (sender, receiver) = mpsc::channel();
        drop(sender);
        let handle = thread::spawn(|| Ok(()));
        while !handle.is_finished() {
            thread::yield_now();
        }
        (
            Self {
                stop_flag,
                discard_final,
                handle: Some(handle),
            },
            receiver,
        )
    }

    #[doc(hidden)]
    pub fn panicking_for_test() -> (Self, Receiver<EngineEvent>) {
        let stop_flag = SearchStopFlag::new();
        let discard_final = Arc::new(AtomicBool::new(false));
        let (sender, receiver) = mpsc::channel();
        drop(sender);
        let handle = thread::spawn(|| -> Result<(), SearchWorkerError> {
            panic!("synthetic shared search worker panic")
        });
        while !handle.is_finished() {
            thread::yield_now();
        }
        (
            Self {
                stop_flag,
                discard_final,
                handle: Some(handle),
            },
            receiver,
        )
    }
}

impl Drop for SearchWorker {
    fn drop(&mut self) {
        if self.handle.is_some() {
            self.discard_final.store(true, Ordering::Release);
            self.stop_flag.request_stop();
            let _cleanup_result = self.join();
        }
    }
}

fn run_request(
    request: SearchRequest,
    stop_flag: SearchStopFlag,
    discard_final: Arc<AtomicBool>,
    sender: Sender<EngineEvent>,
) -> Result<(), SearchWorkerError> {
    let SearchRequest {
        ticket,
        game,
        depth,
    } = request;
    let limits = SearchLimits::new()
        .with_depth(depth)
        .with_stop_flag(stop_flag.clone());
    if let Err(error) = limits.validate() {
        send_event(
            &sender,
            EngineEvent::Failed {
                ticket,
                message: error.to_string(),
            },
        )?;
        return Ok(());
    }

    let mut table = match TranspositionTable::new(DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES) {
        Ok(table) => table,
        Err(error) => {
            send_event(
                &sender,
                EngineEvent::Failed {
                    ticket,
                    message: error.to_string(),
                },
            )?;
            return Ok(());
        }
    };
    let mut position = game.position().clone();
    let mut history = game.search_history();
    let started = Instant::now();
    let progress_sender = sender.clone();
    let progress_stop = stop_flag.clone();
    let mut channel_closed = false;

    let result = iterative_deepening_search_with_limits_and_transposition_table_and_observer(
        &mut position,
        &mut history,
        limits,
        &mut table,
        |progress| {
            if channel_closed {
                return;
            }
            let event = EngineEvent::Progress {
                ticket,
                metrics: SearchMetrics::from_progress(progress, started.elapsed()),
            };
            if progress_sender.send(event).is_err() {
                channel_closed = true;
                progress_stop.request_stop();
            }
        },
    );

    if channel_closed {
        return Err(SearchWorkerError::EventChannelClosed);
    }
    finish_request(ticket, result, &discard_final, &sender)
}

fn finish_request(
    ticket: SearchTicket,
    result: Result<chess_search::SearchResult, IterativeDeepeningSearchError>,
    discard_final: &AtomicBool,
    sender: &Sender<EngineEvent>,
) -> Result<(), SearchWorkerError> {
    if discard_final.load(Ordering::Acquire) {
        send_event(sender, EngineEvent::Cancelled { ticket })?;
        return Ok(());
    }

    let result = match result {
        Ok(result) => result,
        Err(error) => {
            send_event(
                sender,
                EngineEvent::Failed {
                    ticket,
                    message: error.to_string(),
                },
            )?;
            return Ok(());
        }
    };

    let event = classify_success(
        ticket,
        result.completed().best_move(),
        SearchMetrics::from_result(&result),
        result.fallback().is_some(),
    );
    send_event(sender, event)
}

#[must_use]
pub fn classify_success(
    ticket: SearchTicket,
    best_move: Option<Move>,
    metrics: Option<SearchMetrics>,
    has_fallback: bool,
) -> EngineEvent {
    match (best_move, metrics, has_fallback) {
        (Some(best_move), Some(metrics), _) => EngineEvent::Completed {
            ticket,
            best_move,
            metrics,
        },
        (Some(_), None, _) => EngineEvent::Failed {
            ticket,
            message: "search returned an exact move without an exact iteration".to_owned(),
        },
        (None, _, true) => EngineEvent::Failed {
            ticket,
            message: "search ended before completing depth one; interactive frontend rejected the search fallback".to_owned(),
        },
        (None, _, false) => EngineEvent::Failed {
            ticket,
            message: "search completed without an exact best move".to_owned(),
        },
    }
}

fn send_event(sender: &Sender<EngineEvent>, event: EngineEvent) -> Result<(), SearchWorkerError> {
    sender
        .send(event)
        .map_err(|_| SearchWorkerError::EventChannelClosed)
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use chess_core::Game;

    use super::{
        calculate_nps, classify_success, EngineEvent, SearchMetrics, SearchRequest, SearchTicket,
        SearchWorker,
    };

    fn ticket() -> SearchTicket {
        SearchTicket {
            generation: 17,
            request: 23,
        }
    }

    fn opening_move() -> chess_core::Move {
        Game::starting()
            .legal_moves()
            .expect("opening moves")
            .get(0)
            .expect("opening move")
    }

    #[test]
    fn fallback_only_result_is_rejected() {
        let event = classify_success(ticket(), None, None, true);
        assert!(matches!(event, EngineEvent::Failed { .. }));
        if let EngineEvent::Failed { message, .. } = event {
            assert!(message.contains("rejected the search fallback"));
        }
    }

    #[test]
    fn exact_result_requires_exact_iteration_metrics() {
        let best_move = opening_move();
        let metrics = SearchMetrics {
            depth: Some(1),
            nodes: Some(20),
            elapsed: Some(Duration::from_millis(1)),
            ..SearchMetrics::default()
        };
        assert!(matches!(
            classify_success(ticket(), Some(best_move), Some(metrics), false),
            EngineEvent::Completed { .. }
        ));
        assert!(matches!(
            classify_success(ticket(), Some(best_move), None, false),
            EngineEvent::Failed { .. }
        ));
    }

    #[test]
    fn empty_exact_result_fails_closed() {
        assert!(matches!(
            classify_success(ticket(), None, None, false),
            EngineEvent::Failed { .. }
        ));
    }

    #[test]
    fn invalid_limits_fail_without_playable_completion() {
        let (mut worker, receiver) = SearchWorker::spawn(SearchRequest {
            ticket: ticket(),
            game: Game::starting(),
            depth: 0,
        })
        .expect("worker can start");
        worker.join().expect("worker joins");
        let events: Vec<_> = receiver.try_iter().collect();
        assert!(events
            .iter()
            .any(|event| matches!(event, EngineEvent::Failed { .. })));
        assert!(!events
            .iter()
            .any(|event| matches!(event, EngineEvent::Completed { .. })));
    }

    #[test]
    fn fixed_depth_worker_returns_exact_legal_move() {
        let game = Game::starting();
        let mut legality = game.clone();
        let legal = legality.legal_moves().expect("opening legal moves");
        let (mut worker, receiver) = SearchWorker::spawn(SearchRequest {
            ticket: SearchTicket {
                generation: 1,
                request: 1,
            },
            game,
            depth: 1,
        })
        .expect("worker starts");
        let best_move = loop {
            match receiver
                .recv_timeout(Duration::from_secs(10))
                .expect("worker event")
            {
                EngineEvent::Progress { .. } => {}
                EngineEvent::Completed { best_move, .. } => break best_move,
                EngineEvent::Cancelled { .. } => panic!("unexpected cancellation"),
                EngineEvent::Failed { message, .. } => panic!("search failed: {message}"),
            }
        };
        worker.join().expect("worker joins");
        assert!(legal.iter().any(|candidate| candidate == best_move));
    }

    #[test]
    fn explicit_cancel_emits_no_playable_completion() {
        let (mut worker, receiver) = SearchWorker::spawn(SearchRequest {
            ticket: ticket(),
            game: Game::starting(),
            depth: 12,
        })
        .expect("worker starts");
        worker.cancel_and_join().expect("cancel joins");
        let events: Vec<_> = receiver.try_iter().collect();
        assert!(events
            .iter()
            .any(|event| matches!(event, EngineEvent::Cancelled { .. })));
        assert!(!events
            .iter()
            .any(|event| matches!(event, EngineEvent::Completed { .. })));
    }

    #[test]
    fn panic_is_reported_by_join() {
        let (mut worker, _receiver) = SearchWorker::panicking_for_test();
        assert!(worker.join().is_err());
    }

    #[test]
    fn nps_zero_normal_and_saturation_are_explicit() {
        assert_eq!(calculate_nps(10, Duration::ZERO), None);
        assert_eq!(calculate_nps(123, Duration::from_secs(1)), Some(123));
        assert_eq!(
            calculate_nps(u64::MAX, Duration::from_nanos(1)),
            Some(u64::MAX)
        );
    }
}
