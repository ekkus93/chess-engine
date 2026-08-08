use chess_core::{Color, DrawReason, Game, Position, UciMove};

use super::{
    AppScreen, AppState, ConfirmationAction, GameConfig, GameOutcome, Overlay,
    MAX_MENU_SEARCH_DEPTH, MIN_SEARCH_DEPTH,
};
use crate::worker::{EngineEvent, SearchMetrics, SearchTicket};

fn human_app(color: Color) -> AppState {
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: color,
        engine_depth: 1,
    })
    .expect("human game starts");
    app
}

fn self_play_app() -> AppState {
    let mut app = AppState::new();
    app.start_game(GameConfig::SelfPlay {
        white_depth: 1,
        black_depth: 1,
    })
    .expect("self-play starts");
    app
}

fn set_position(app: &mut AppState, fen: &str) {
    let position = Position::from_fen(fen).expect("fixture FEN parses");
    app.session.as_mut().expect("session").game = Game::new(position);
    app.refresh_terminal_state()
        .expect("status refresh succeeds");
}

fn legal_move(game: &mut Game, uci: &str) -> chess_core::Move {
    let syntax = uci.parse::<UciMove>().expect("fixture UCI parses");
    game.legal_moves()
        .expect("legal moves")
        .iter()
        .find(|candidate| syntax.matches(*candidate))
        .expect("fixture move is legal")
}

#[test]
fn configuration_depth_validation_rejects_out_of_range_and_accepts_boundaries() {
    for depth in [0, MAX_MENU_SEARCH_DEPTH + 1] {
        let mut app = AppState::new();
        assert!(app
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::White,
                engine_depth: depth,
            })
            .is_err());
    }

    for (white_depth, black_depth) in [
        (0, MIN_SEARCH_DEPTH),
        (MAX_MENU_SEARCH_DEPTH + 1, MIN_SEARCH_DEPTH),
        (MIN_SEARCH_DEPTH, 0),
        (MIN_SEARCH_DEPTH, MAX_MENU_SEARCH_DEPTH + 1),
    ] {
        let mut app = AppState::new();
        assert!(app
            .start_game(GameConfig::SelfPlay {
                white_depth,
                black_depth,
            })
            .is_err());
    }

    for depth in [MIN_SEARCH_DEPTH, MAX_MENU_SEARCH_DEPTH] {
        let mut app = AppState::new();
        app.start_game(GameConfig::HumanVsEngine {
            human_color: Color::White,
            engine_depth: depth,
        })
        .expect("boundary depth is valid");
    }
}

#[test]
fn missing_session_operations_return_typed_errors() {
    let mut app = AppState::new();
    assert!(app.restart_current_game().is_err());
    assert!(app.mark_saved("missing.txt".to_owned()).is_err());
    assert!(app.step_self_play().is_err());
    assert!(app.pause_self_play().is_err());
    assert!(app.resume_self_play().is_err());
    assert!(app.resign_human().is_err());
}

#[test]
fn mode_and_turn_misuse_is_rejected_without_game_mutation() {
    let mut self_play = self_play_app();
    let before = self_play.session.as_ref().expect("session").game.clone();
    assert!(self_play.submit_human_move("e2e4").is_err());
    assert_eq!(self_play.session.as_ref().expect("session").game, before);
    assert!(self_play.resign_human().is_err());

    let mut human_white = human_app(Color::White);
    assert!(human_white.pause_self_play().is_err());
    assert!(human_white.resume_self_play().is_err());
    assert!(human_white.step_self_play().is_err());

    let mut human_black = human_app(Color::Black);
    let before = human_black.session.as_ref().expect("session").game.clone();
    assert!(human_black.submit_human_move("e2e4").is_err());
    assert_eq!(human_black.session.as_ref().expect("session").game, before);
    human_black.cancel_search_state(None);
    assert!(human_black.submit_human_move("e2e4").is_err());
    assert_eq!(human_black.session.as_ref().expect("session").game, before);
}

#[test]
fn self_play_step_rejects_running_pending_and_completed_states() {
    let mut running = self_play_app();
    assert!(running.step_self_play().is_err());

    let mut pending = self_play_app();
    pending.session.as_mut().expect("session").auto_play = false;
    assert!(pending.step_self_play().is_err());

    let mut completed = self_play_app();
    completed.pause_self_play().expect("pause succeeds");
    completed.session.as_mut().expect("session").outcome = Some(GameOutcome::Stalemate);
    assert!(completed.step_self_play().is_err());
    assert!(completed.resume_self_play().is_err());
}

#[test]
fn terminal_game_rejects_human_move_and_resignation() {
    let mut app = human_app(Color::White);
    app.session.as_mut().expect("session").outcome = Some(GameOutcome::Stalemate);
    let before = app.session.as_ref().expect("session").game.clone();
    assert!(app.submit_human_move("e2e4").is_err());
    assert!(app.resign_human().is_err());
    assert_eq!(app.session.as_ref().expect("session").game, before);
}

#[test]
fn current_illegal_engine_completion_is_rejected_without_application() {
    let mut app = human_app(Color::Black);
    let request = app.take_pending_search().expect("search request");
    let before = app.session.as_ref().expect("session").game.clone();

    let mut other = Game::starting();
    let white = legal_move(&mut other, "e2e4");
    other.make_move(white).expect("fixture white move applies");
    let illegal_here = legal_move(&mut other, "e7e5");

    let result = app.handle_engine_event(EngineEvent::Completed {
        ticket: request.ticket,
        best_move: illegal_here,
        metrics: SearchMetrics::default(),
    });
    assert!(result.is_err());
    let session = app.session.as_ref().expect("session");
    assert_eq!(session.game, before);
    assert!(!session.thinking);
    assert_eq!(session.active_search, None);
    assert!(session
        .status_message
        .as_deref()
        .is_some_and(|message| message.contains("no longer legal")));
}

#[test]
fn current_failure_and_cancellation_clear_search_state() {
    for event in [
        EngineEvent::Failed {
            ticket: SearchTicket {
                generation: 1,
                request: 1,
            },
            message: "synthetic failure".to_owned(),
        },
        EngineEvent::Cancelled {
            ticket: SearchTicket {
                generation: 1,
                request: 1,
            },
        },
    ] {
        let mut app = human_app(Color::Black);
        let request = app.take_pending_search().expect("request");
        let event = match event {
            EngineEvent::Failed { message, .. } => EngineEvent::Failed {
                ticket: request.ticket,
                message,
            },
            EngineEvent::Cancelled { .. } => EngineEvent::Cancelled {
                ticket: request.ticket,
            },
            _ => unreachable!(),
        };
        app.handle_engine_event(event).expect("event handled");
        let session = app.session.as_ref().expect("session");
        assert!(!session.thinking);
        assert_eq!(session.active_search, None);
        assert!(session.status_message.is_some());
    }
}

#[test]
fn stale_failure_and_cancellation_do_not_touch_current_search() {
    for stale in [
        EngineEvent::Failed {
            ticket: SearchTicket {
                generation: 99,
                request: 99,
            },
            message: "stale failure".to_owned(),
        },
        EngineEvent::Cancelled {
            ticket: SearchTicket {
                generation: 99,
                request: 99,
            },
        },
    ] {
        let mut app = human_app(Color::Black);
        let request = app.take_pending_search().expect("request");
        app.session.as_mut().expect("session").status_message = Some("current".to_owned());
        app.handle_engine_event(stale)
            .expect("stale event is harmless");
        let session = app.session.as_ref().expect("session");
        assert_eq!(session.active_search, Some(request.ticket));
        assert!(session.thinking);
        assert_eq!(session.status_message.as_deref(), Some("current"));
    }
}

#[test]
fn engine_event_without_session_is_harmless() {
    let mut app = AppState::new();
    app.handle_engine_event(EngineEvent::Failed {
        ticket: SearchTicket {
            generation: 1,
            request: 1,
        },
        message: "orphan".to_owned(),
    })
    .expect("orphan event is ignored");
    assert!(app.session.is_none());
}

#[test]
fn explicit_search_state_clearing_preserves_or_sets_message_as_requested() {
    let mut app = human_app(Color::Black);
    app.session.as_mut().expect("session").status_message = Some("existing".to_owned());
    app.cancel_search_state(None);
    let session = app.session.as_ref().expect("session");
    assert!(!session.thinking);
    assert_eq!(session.active_search, None);
    assert_eq!(session.status_message.as_deref(), Some("existing"));
    assert!(app.take_pending_search().is_none());

    let mut app = human_app(Color::Black);
    app.cancel_search_state(Some("cancelled explicitly".to_owned()));
    assert_eq!(
        app.session
            .as_ref()
            .expect("session")
            .status_message
            .as_deref(),
        Some("cancelled explicitly")
    );
}

#[test]
fn menu_quit_and_new_game_clear_stale_presentation_state() {
    let mut app = human_app(Color::White);
    app.open_confirmation(ConfirmationAction::Quit);
    app.request_quit();
    assert!(app.should_quit);
    assert!(app.overlay.is_none());

    let mut app = human_app(Color::White);
    app.open_confirmation(ConfirmationAction::MainMenu);
    app.return_to_menu();
    assert_eq!(app.screen, AppScreen::MainMenu);
    assert!(app.session.is_none());
    assert!(app.overlay.is_none());
    assert!(app.take_pending_search().is_none());

    let mut app = human_app(Color::White);
    app.session.as_mut().expect("session").status_message = Some("stale".to_owned());
    app.session.as_mut().expect("session").engine_info = Some(SearchMetrics::default());
    app.overlay = Some(Overlay::SavePath {
        input: "stale.txt".to_owned(),
    });
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::White,
        engine_depth: 1,
    })
    .expect("replacement game starts");
    let session = app.session.as_ref().expect("session");
    assert!(session.status_message.is_none());
    assert!(session.engine_info.is_none());
    assert!(app.overlay.is_none());
}

#[test]
fn stalemate_and_dead_position_are_terminal_and_clear_search_state() {
    let mut stalemate = self_play_app();
    set_position(&mut stalemate, "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1");
    let session = stalemate.session.as_ref().expect("session");
    assert_eq!(session.outcome, Some(GameOutcome::Stalemate));
    assert!(!session.thinking);
    assert!(!session.auto_play);
    assert!(stalemate.take_pending_search().is_none());

    let mut dead = self_play_app();
    set_position(&mut dead, "7k/8/8/8/8/8/8/K7 w - - 0 1");
    let session = dead.session.as_ref().expect("session");
    assert_eq!(
        session.outcome,
        Some(GameOutcome::Draw(DrawReason::DeadPosition))
    );
    assert!(!session.thinking);
    assert!(!session.auto_play);
    assert!(dead.take_pending_search().is_none());
}

#[test]
fn seventy_five_move_draw_is_automatic_but_fifty_move_claim_remains_active() {
    let mut automatic = self_play_app();
    set_position(&mut automatic, "7k/8/8/8/8/8/R7/K7 w - - 150 76");
    assert_eq!(
        automatic.session.as_ref().expect("session").outcome,
        Some(GameOutcome::Draw(DrawReason::SeventyFiveMoveRule))
    );
    assert!(automatic.take_pending_search().is_none());

    let mut claimable = self_play_app();
    claimable.cancel_search_state(None);
    claimable.session.as_mut().expect("session").auto_play = true;
    set_position(&mut claimable, "7k/8/8/8/8/8/R7/K7 w - - 100 51");
    assert!(claimable
        .session
        .as_ref()
        .expect("session")
        .outcome
        .is_none());
    claimable
        .schedule_if_needed()
        .expect("claimable draw stays playable");
    assert!(claimable.take_pending_search().is_some());
}

#[test]
fn claimable_threefold_remains_active_and_does_not_stop_scheduling() {
    let mut app = self_play_app();
    app.cancel_search_state(None);
    let mut game = Game::starting();
    for uci in [
        "g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8",
    ] {
        let current = legal_move(&mut game, uci);
        game.make_move(current).expect("repetition move applies");
    }
    {
        let session = app.session.as_mut().expect("session");
        session.game = game;
        session.auto_play = true;
    }
    app.refresh_terminal_state()
        .expect("claimable status refreshes");
    assert!(app.session.as_ref().expect("session").outcome.is_none());
    app.schedule_if_needed()
        .expect("claimable repetition remains schedulable");
    assert!(app.take_pending_search().is_some());
}

#[test]
fn quit_and_menu_clear_a_real_pending_search() {
    let mut quit = human_app(Color::Black);
    assert!(quit.take_pending_search().is_some());
    quit.start_game(GameConfig::HumanVsEngine {
        human_color: Color::Black,
        engine_depth: 1,
    })
    .expect("replacement black game starts");
    quit.open_confirmation(ConfirmationAction::Quit);
    quit.request_quit();
    assert!(quit.should_quit);
    assert!(quit.overlay.is_none());
    assert!(quit.take_pending_search().is_none());

    let mut menu = human_app(Color::Black);
    assert!(menu.take_pending_search().is_some());
    menu.start_game(GameConfig::HumanVsEngine {
        human_color: Color::Black,
        engine_depth: 1,
    })
    .expect("replacement black game starts");
    menu.open_confirmation(ConfirmationAction::MainMenu);
    menu.return_to_menu();
    assert_eq!(menu.screen, AppScreen::MainMenu);
    assert!(menu.session.is_none());
    assert!(menu.overlay.is_none());
    assert!(menu.take_pending_search().is_none());
}
