use std::time::Duration;

use chess_core::{Game, Position};

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
        .expect("at least one opening move")
}

#[test]
fn fallback_only_result_is_rejected_by_tui() {
    let event = classify_success(ticket(), None, None, true);
    match event {
        EngineEvent::Failed {
            ticket: actual,
            message,
        } => {
            assert_eq!(actual, ticket());
            assert!(message.contains("rejected the search fallback"));
        }
        EngineEvent::Completed { .. } => panic!("fallback became a playable completion"),
        other => panic!("unexpected fallback disposition: {other:?}"),
    }
}

#[test]
fn exact_result_with_metrics_is_completed() {
    let best_move = opening_move();
    let metrics = SearchMetrics {
        depth: Some(1),
        nodes: Some(20),
        elapsed: Some(Duration::from_millis(1)),
        ..SearchMetrics::default()
    };
    let event = classify_success(ticket(), Some(best_move), Some(metrics.clone()), false);
    assert_eq!(
        event,
        EngineEvent::Completed {
            ticket: ticket(),
            best_move,
            metrics,
        }
    );
}

#[test]
fn exact_result_without_exact_iteration_metrics_fails_closed() {
    let event = classify_success(ticket(), Some(opening_move()), None, false);
    match event {
        EngineEvent::Failed { message, .. } => {
            assert!(message.contains("without an exact iteration"));
        }
        other => panic!("missing exact metrics did not fail closed: {other:?}"),
    }
}

#[test]
fn result_without_exact_move_or_fallback_fails_closed() {
    let event = classify_success(ticket(), None, None, false);
    match event {
        EngineEvent::Failed { message, .. } => {
            assert!(message.contains("without an exact best move"));
        }
        other => panic!("empty result did not fail closed: {other:?}"),
    }
}

#[test]
fn invalid_search_limits_fail_without_playable_completion() {
    let position = Position::from_fen("rnbqkbnr/pppppppp/8/8/8/7P/PPPPPPP1/RNBQKBNR b KQkq - 0 1")
        .expect("non-book fixture");
    let (mut worker, receiver) = SearchWorker::spawn(SearchRequest {
        ticket: ticket(),
        game: Game::new(position),
        depth: 0,
    })
    .expect("worker thread can start");
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
fn engine_event_identity_and_finality_are_explicit() {
    let progress = EngineEvent::Progress {
        ticket: ticket(),
        metrics: SearchMetrics::default(),
    };
    let cancelled = EngineEvent::Cancelled { ticket: ticket() };
    assert_eq!(progress.ticket(), ticket());
    assert!(!progress.is_final());
    assert_eq!(cancelled.ticket(), ticket());
    assert!(cancelled.is_final());
}

#[test]
fn nps_handles_zero_normal_and_saturating_cases() {
    assert_eq!(calculate_nps(10, Duration::ZERO), None);
    assert_eq!(calculate_nps(123, Duration::from_secs(1)), Some(123));
    assert_eq!(
        calculate_nps(u64::MAX, Duration::from_nanos(1)),
        Some(u64::MAX)
    );
}
