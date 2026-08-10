pub use chess_app::worker::{
    calculate_nps, classify_success, EngineEvent, SearchMetrics, SearchRequest, SearchTicket,
    SearchWorker, SearchWorkerError,
};

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use chess_core::{Game, Position};

    use super::{EngineEvent, SearchRequest, SearchTicket, SearchWorker};

    #[test]
    fn tui_shared_worker_uses_curated_opening_book() {
        let (mut worker, receiver) = SearchWorker::spawn(SearchRequest {
            ticket: SearchTicket {
                generation: 1,
                request: 1,
            },
            game: Game::starting(),
            depth: 12,
        })
        .expect("worker starts");

        let best_move = loop {
            match receiver
                .recv_timeout(Duration::from_secs(10))
                .expect("worker event arrives")
            {
                EngineEvent::Progress { .. } => {}
                EngineEvent::Completed { best_move, .. } => break best_move,
                EngineEvent::Cancelled { .. } => panic!("book lookup unexpectedly cancelled"),
                EngineEvent::Failed { message, .. } => panic!("book lookup failed: {message}"),
            }
        };
        worker.join().expect("worker joins");
        assert_eq!(best_move.to_uci(), "e2e4");
    }

    #[test]
    fn tui_shared_worker_cancel_never_emits_a_playable_move() {
        let position =
            Position::from_fen("rnbqkbnr/pppppppp/8/8/8/7P/PPPPPPP1/RNBQKBNR b KQkq - 0 1")
                .expect("non-book fixture");
        let (mut worker, receiver) = SearchWorker::spawn(SearchRequest {
            ticket: SearchTicket {
                generation: 4,
                request: 9,
            },
            game: Game::new(position),
            depth: 12,
        })
        .expect("worker starts");
        worker.cancel_and_join().expect("worker cancels and joins");

        let events: Vec<_> = receiver.try_iter().collect();
        assert!(events
            .iter()
            .any(|event| matches!(event, EngineEvent::Cancelled { .. })));
        assert!(!events
            .iter()
            .any(|event| matches!(event, EngineEvent::Completed { .. })));
    }
}

#[cfg(test)]
mod hardening_tests;