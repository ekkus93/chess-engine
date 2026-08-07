use chess_core::{Color, Game, Position};
use chess_tui::{
    app::{AppState, GameConfig, GameOutcome},
    worker::{EngineEvent, SearchMetrics},
};

#[test]
fn move_submission_while_engine_owns_the_turn_is_rejected_without_mutation() {
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::Black,
        engine_depth: 1,
    })
    .expect("game starts");
    let before = app.session.as_ref().expect("session").game.clone();

    assert!(app.submit_human_move("e7e5").is_err());

    let session = app.session.as_ref().expect("session remains active");
    assert_eq!(session.game, before);
    assert!(session.thinking);
}

#[test]
fn current_progress_changes_presentation_only() {
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::Black,
        engine_depth: 1,
    })
    .expect("game starts");
    let request = app.take_pending_search().expect("search is scheduled");
    let before = app.session.as_ref().expect("session").game.clone();

    app.handle_engine_event(EngineEvent::Progress {
        ticket: request.ticket,
        metrics: SearchMetrics {
            depth: Some(1),
            nodes: Some(20),
            ..SearchMetrics::default()
        },
    })
    .expect("progress is accepted");

    let session = app.session.as_ref().expect("session remains active");
    assert_eq!(session.game, before);
    assert_eq!(session.active_search, Some(request.ticket));
    assert!(session.thinking);
    assert_eq!(
        session.engine_info.as_ref().and_then(|info| info.depth),
        Some(1)
    );
}

#[test]
fn resume_self_play_schedules_from_the_current_position() {
    let mut app = AppState::new();
    app.start_game(GameConfig::SelfPlay {
        white_depth: 1,
        black_depth: 1,
    })
    .expect("self-play starts");
    app.pause_self_play().expect("pause succeeds");
    assert!(app.take_pending_search().is_none());

    app.resume_self_play().expect("resume succeeds");

    let session = app.session.as_ref().expect("session remains active");
    assert!(session.auto_play);
    assert!(session.thinking);
    assert!(app.take_pending_search().is_some());
}

#[test]
fn terminal_self_play_engine_move_schedules_nothing_more() {
    let position =
        Position::from_fen("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1").expect("mate-in-one fixture parses");
    let mut app = AppState::new();
    app.start_game(GameConfig::SelfPlay {
        white_depth: 1,
        black_depth: 1,
    })
    .expect("self-play starts");
    let request = app
        .take_pending_search()
        .expect("white search is scheduled");
    app.session.as_mut().expect("session").game = Game::new(position);
    let mating_move = app
        .session
        .as_mut()
        .expect("session")
        .game
        .legal_moves()
        .expect("legal moves")
        .iter()
        .find(|current| current.to_uci() == "f7g7")
        .expect("fixture mate is legal");

    app.handle_engine_event(EngineEvent::Completed {
        ticket: request.ticket,
        best_move: mating_move,
        metrics: SearchMetrics::default(),
    })
    .expect("mate completion applies");

    let session = app.session.as_ref().expect("session remains available");
    assert_eq!(
        session.outcome,
        Some(GameOutcome::Checkmate {
            winner: Color::White
        })
    );
    assert!(!session.auto_play);
    assert!(!session.thinking);
    assert!(app.take_pending_search().is_none());
}

#[test]
fn failed_save_state_is_visible_and_never_remains_marked_saved() {
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::White,
        engine_depth: 1,
    })
    .expect("game starts");
    app.mark_saved("first.txt".to_owned())
        .expect("synthetic prior save is recorded");

    app.mark_save_failed("Save failed: permission denied".to_owned());

    let session = app.session.as_ref().expect("session remains active");
    assert_eq!(session.saved_path, None);
    assert_eq!(
        session.status_message.as_deref(),
        Some("Save failed: permission denied")
    );
}
