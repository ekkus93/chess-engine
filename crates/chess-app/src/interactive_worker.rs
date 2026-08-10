use std::sync::mpsc::{self, Receiver};

pub use crate::search_worker::{
    calculate_nps, classify_success, EngineEvent, SearchMetrics, SearchRequest, SearchTicket,
    SearchWorkerError,
};
use crate::search_worker::SearchWorker as SearchOnlyWorker;

enum WorkerInner {
    Search(SearchOnlyWorker),
    Ready,
}

/// Book-aware interactive worker shared by the TUI, console, and Android frontends.
///
/// Opening-book lookup runs before normal search. A validated book hit is
/// returned as an exact completion with no search metrics. A normal book miss
/// delegates to the unchanged search-only worker. Book errors are emitted as
/// visible failures and never converted into a search fallback.
pub struct SearchWorker {
    inner: WorkerInner,
}

impl SearchWorker {
    pub fn spawn(
        request: SearchRequest,
    ) -> Result<(Self, Receiver<EngineEvent>), SearchWorkerError> {
        match crate::book::select_move(request.game.position()) {
            Ok(Some(best_move)) => ready_worker(EngineEvent::Completed {
                ticket: request.ticket,
                best_move,
                metrics: SearchMetrics::default(),
            }),
            Ok(None) => {
                let (worker, receiver) = SearchOnlyWorker::spawn(request)?;
                Ok((
                    Self {
                        inner: WorkerInner::Search(worker),
                    },
                    receiver,
                ))
            }
            Err(message) => ready_worker(EngineEvent::Failed {
                ticket: request.ticket,
                message: format!("opening book failed: {message}"),
            }),
        }
    }

    #[must_use]
    pub fn is_finished(&self) -> bool {
        match &self.inner {
            WorkerInner::Search(worker) => worker.is_finished(),
            WorkerInner::Ready => true,
        }
    }

    pub fn join(&mut self) -> Result<(), SearchWorkerError> {
        match &mut self.inner {
            WorkerInner::Search(worker) => worker.join(),
            WorkerInner::Ready => Ok(()),
        }
    }

    pub fn cancel_and_join(&mut self) -> Result<(), SearchWorkerError> {
        match &mut self.inner {
            WorkerInner::Search(worker) => worker.cancel_and_join(),
            WorkerInner::Ready => Ok(()),
        }
    }

    #[doc(hidden)]
    pub fn finished_with_events_for_test(
        events: Vec<EngineEvent>,
    ) -> (Self, Receiver<EngineEvent>) {
        let (worker, receiver) = SearchOnlyWorker::finished_with_events_for_test(events);
        (
            Self {
                inner: WorkerInner::Search(worker),
            },
            receiver,
        )
    }

    #[doc(hidden)]
    pub fn waiting_with_event_for_test(event: EngineEvent) -> (Self, Receiver<EngineEvent>) {
        let (worker, receiver) = SearchOnlyWorker::waiting_with_event_for_test(event);
        (
            Self {
                inner: WorkerInner::Search(worker),
            },
            receiver,
        )
    }

    #[doc(hidden)]
    pub fn finished_without_event_for_test() -> (Self, Receiver<EngineEvent>) {
        let (worker, receiver) = SearchOnlyWorker::finished_without_event_for_test();
        (
            Self {
                inner: WorkerInner::Search(worker),
            },
            receiver,
        )
    }

    #[doc(hidden)]
    pub fn panicking_for_test() -> (Self, Receiver<EngineEvent>) {
        let (worker, receiver) = SearchOnlyWorker::panicking_for_test();
        (
            Self {
                inner: WorkerInner::Search(worker),
            },
            receiver,
        )
    }
}

fn ready_worker(
    event: EngineEvent,
) -> Result<(SearchWorker, Receiver<EngineEvent>), SearchWorkerError> {
    let (sender, receiver) = mpsc::channel();
    sender
        .send(event)
        .map_err(|_| SearchWorkerError::EventChannelClosed)?;
    drop(sender);
    Ok((
        SearchWorker {
            inner: WorkerInner::Ready,
        },
        receiver,
    ))
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use chess_core::{Game, Position};

    use super::{EngineEvent, SearchMetrics, SearchRequest, SearchTicket, SearchWorker};

    fn ticket() -> SearchTicket {
        SearchTicket {
            generation: 31,
            request: 41,
        }
    }

    #[test]
    fn starting_position_returns_curated_book_move_before_search() {
        let (mut worker, receiver) = SearchWorker::spawn(SearchRequest {
            ticket: ticket(),
            game: Game::starting(),
            depth: 12,
        })
        .expect("book-aware worker starts");
        assert!(worker.is_finished());
        worker.join().expect("ready worker joins");

        let events: Vec<_> = receiver.try_iter().collect();
        assert_eq!(events.len(), 1);
        match &events[0] {
            EngineEvent::Completed {
                best_move, metrics, ..
            } => {
                assert_eq!(best_move.to_uci(), "e2e4");
                assert_eq!(metrics, &SearchMetrics::default());
            }
            other => panic!("expected opening-book completion, got {other:?}"),
        }
    }

    #[test]
    fn uncovered_position_delegates_to_exact_search() {
        let position = Position::from_fen(
            "rnbqkbnr/pppppppp/8/8/8/7P/PPPPPPP1/RNBQKBNR b KQkq - 0 1",
        )
        .expect("non-book fixture");
        let (mut worker, receiver) = SearchWorker::spawn(SearchRequest {
            ticket: ticket(),
            game: Game::new(position),
            depth: 1,
        })
        .expect("search worker starts");

        let completed = loop {
            match receiver
                .recv_timeout(Duration::from_secs(10))
                .expect("worker event")
            {
                EngineEvent::Progress { .. } => {}
                EngineEvent::Completed {
                    best_move, metrics, ..
                } => break (best_move, metrics),
                EngineEvent::Cancelled { .. } => panic!("unexpected cancellation"),
                EngineEvent::Failed { message, .. } => panic!("search failed: {message}"),
            }
        };
        worker.join().expect("search worker joins");
        assert_eq!(completed.1.depth, Some(1));
    }
}
