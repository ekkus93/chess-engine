use std::time::Duration;

use chess_core::{Color, Game, Position};
use chess_tui::{
    app::{AppState, GameConfig, GameOutcome},
    worker::{EngineEvent, SearchMetrics, SearchTicket, SearchWorker},
};

fn drive_one_exact_search(app: &mut AppState) {
    let request = app.take_pending_search().expect("search is scheduled");
    let (mut worker, receiver) = SearchWorker::spawn(request).expect("worker starts");
    loop {
        let event = receiver
            .recv_timeout(Duration::from_secs(10))
            .expect("search event arrives");
        let final_event = event.is_final();
        app.handle_engine_event(event)
            .expect("engine event applies cleanly");
        if final_event {
            break;
        }
    }
    worker.join().expect("worker joins cleanly");
}

#[test]
fn human_white_move_engine_response_returns_control_to_human() {
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::White,
        engine_depth: 1,
    })
    .expect("game starts");

    app.submit_human_move("e2e4")
        .expect("human opening move applies");
    drive_one_exact_search(&mut app);

    let session = app.session.as_ref().expect("session remains active");
    assert_eq!(session.game.ply_count(), 2);
    assert_eq!(session.game.position().side_to_move(), Color::White);
    assert!(session.human_to_move());
    assert!(!session.thinking);
}

#[test]
fn human_black_game_engine_moves_first_then_returns_control_to_human() {
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::Black,
        engine_depth: 1,
    })
    .expect("game starts");

    drive_one_exact_search(&mut app);

    let session = app.session.as_ref().expect("session remains active");
    assert_eq!(session.game.ply_count(), 1);
    assert_eq!(session.game.position().side_to_move(), Color::Black);
    assert!(session.human_to_move());
    assert!(!session.thinking);
}

#[test]
fn self_play_alternates_two_legal_plies_and_can_pause_between_searches() {
    let mut app = AppState::new();
    app.start_game(GameConfig::SelfPlay {
        white_depth: 1,
        black_depth: 1,
    })
    .expect("self-play starts");

    drive_one_exact_search(&mut app);
    drive_one_exact_search(&mut app);
    app.pause_self_play().expect("pause succeeds");

    let session = app.session.as_ref().expect("session remains active");
    assert_eq!(session.game.ply_count(), 2);
    assert_eq!(session.game.position().side_to_move(), Color::White);
    assert!(!session.auto_play);
    assert!(!session.thinking);
    assert!(app.take_pending_search().is_none());
}

#[test]
fn self_play_step_applies_exactly_one_ply_and_remains_paused() {
    let mut app = AppState::new();
    app.start_game(GameConfig::SelfPlay {
        white_depth: 1,
        black_depth: 1,
    })
    .expect("self-play starts");
    app.pause_self_play().expect("initial auto-play pauses");

    app.step_self_play().expect("one step schedules");
    drive_one_exact_search(&mut app);

    let session = app.session.as_ref().expect("session remains active");
    assert_eq!(session.game.ply_count(), 1);
    assert_eq!(session.game.position().side_to_move(), Color::Black);
    assert!(!session.auto_play);
    assert!(!session.thinking);
    assert!(app.take_pending_search().is_none());
}

#[test]
fn search_failure_clears_thinking_and_is_visible_without_moving() {
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::Black,
        engine_depth: 1,
    })
    .expect("game starts");
    let request = app.take_pending_search().expect("engine search is scheduled");
    let before = app.session.as_ref().expect("session").game.clone();

    app.handle_engine_event(EngineEvent::Failed {
        ticket: request.ticket,
        message: "synthetic search failure".to_owned(),
    })
    .expect("failure event is handled");

    let session = app.session.as_ref().expect("session remains active");
    assert_eq!(session.game, before);
    assert!(!session.thinking);
    assert_eq!(session.active_search, None);
    assert!(session
        .status_message
        .as_deref()
        .is_some_and(|message| message.contains("synthetic search failure")));
}

#[test]
fn stale_progress_is_ignored_without_overwriting_engine_information() {
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::Black,
        engine_depth: 1,
    })
    .expect("game starts");
    let request = app.take_pending_search().expect("engine search is scheduled");

    app.handle_engine_event(EngineEvent::Progress {
        ticket: SearchTicket {
            generation: request.ticket.generation + 1,
            request: request.ticket.request,
        },
        metrics: SearchMetrics {
            depth: Some(99),
            ..SearchMetrics::default()
        },
    })
    .expect("stale progress is harmless");

    let session = app.session.as_ref().expect("session remains active");
    assert_eq!(session.engine_info, None);
    assert_eq!(session.active_search, Some(request.ticket));
    assert!(session.thinking);
}

#[test]
fn terminal_human_move_stops_search_scheduling_and_future_input() {
    let position = Position::from_fen("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1")
        .expect("mate-in-one fixture parses");
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::White,
        engine_depth: 1,
    })
    .expect("game starts");
    app.session.as_mut().expect("session").game = Game::new(position);

    app.submit_human_move("f7g7")
        .expect("fixture checkmate move applies");

    let session = app.session.as_ref().expect("session remains available");
    assert_eq!(
        session.outcome,
        Some(GameOutcome::Checkmate {
            winner: Color::White
        })
    );
    assert!(!session.thinking);
    assert!(app.take_pending_search().is_none());

    let after_mate = app.session.as_ref().expect("session").game.clone();
    assert!(app.submit_human_move("h8g8").is_err());
    assert_eq!(app.session.as_ref().expect("session").game, after_mate);
}

#[test]
fn resignation_as_white_declares_black_winner() {
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::White,
        engine_depth: 1,
    })
    .expect("game starts");

    app.resign_human().expect("resignation succeeds");

    assert_eq!(
        app.session.as_ref().expect("session").outcome,
        Some(GameOutcome::Resignation {
            winner: Color::Black
        })
    );
}
