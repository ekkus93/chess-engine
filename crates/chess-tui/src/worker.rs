pub use chess_app::worker::{
    calculate_nps, classify_success, EngineEvent, SearchMetrics, SearchRequest, SearchTicket,
    SearchWorker, SearchWorkerError,
};

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use chess_core::Game;

    use super::{EngineEvent, SearchRequest, SearchTicket, SearchWorker};

    #[test]
    fn tui_uses_shared_worker_for_an_exact_legal_move() {
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
                .expect("worker event arrives")
            {
                EngineEvent::Progress { .. } => {}
                EngineEvent::Completed { best_move, .. } => break best_move,
                EngineEvent::Cancelled { .. } => panic!("search unexpectedly cancelled"),
                EngineEvent::Failed { message, .. } => panic!("search failed: {message}"),
            }
        };
        worker.join().expect("worker joins");
        assert!(legal.iter().any(|candidate| candidate == best_move));
    }

    #[test]
    fn tui_shared_worker_cancel_never_emits_a_playable_move() {
        let (mut worker, receiver) = SearchWorker::spawn(SearchRequest {
            ticket: SearchTicket {
                generation: 4,
                request: 9,
            },
            game: Game::starting(),
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
