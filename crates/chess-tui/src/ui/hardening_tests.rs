use std::{fs, io, path::PathBuf, process, time::SystemTime};

use chess_core::{Color, Game, UciMove};
use crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::{backend::TestBackend, Terminal};

use super::{
    execute_confirmation, handle_game_key, handle_key, handle_menu_key, handle_overlay_key, render,
    save_current_game, ActiveWorker, EngineRuntime,
};
use crate::{
    app::{
        AppScreen, AppState, ConfirmationAction, GameConfig, MenuMode, Overlay,
        MAX_MENU_SEARCH_DEPTH, MIN_SEARCH_DEPTH,
    },
    save::serialize_game,
    worker::{EngineEvent, SearchMetrics, SearchTicket, SearchWorker, SearchWorkerError},
};

fn key(code: KeyCode) -> KeyEvent {
    KeyEvent::new(code, KeyModifiers::NONE)
}

fn ctrl(code: KeyCode) -> KeyEvent {
    KeyEvent::new(code, KeyModifiers::CONTROL)
}

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

fn unique_path(label: &str) -> PathBuf {
    let stamp = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .expect("clock after epoch")
        .as_nanos();
    std::env::temp_dir().join(format!(
        "chess-tui-ui-{label}-{}-{stamp}.txt",
        process::id()
    ))
}

fn opening_move() -> chess_core::Move {
    Game::starting()
        .legal_moves()
        .expect("opening moves")
        .get(0)
        .expect("opening move")
}

fn rendered_text(app: &AppState, width: u16, height: u16) -> String {
    let backend = TestBackend::new(width, height);
    let mut terminal = Terminal::new(backend).expect("test terminal");
    terminal
        .draw(|frame| render(frame, app))
        .expect("render succeeds");
    let buffer = terminal.backend().buffer();
    let mut text = String::new();
    for y in 0..height {
        for x in 0..width {
            text.push_str(buffer.get(x, y).symbol());
        }
        text.push('\n');
    }
    text
}

#[test]
fn menu_navigation_and_adjustment_clamp_at_bounds() {
    let mut app = AppState::new();
    handle_menu_key(&mut app, key(KeyCode::Up)).expect("up works");
    assert_eq!(app.menu.selected_row, 0);
    for _ in 0..10 {
        handle_menu_key(&mut app, key(KeyCode::Down)).expect("down works");
    }
    assert_eq!(app.menu.selected_row, 3);

    app.menu.selected_row = 0;
    handle_menu_key(&mut app, key(KeyCode::Right)).expect("mode changes");
    assert_eq!(app.menu.mode, MenuMode::SelfPlay);
    handle_menu_key(&mut app, key(KeyCode::Enter)).expect("mode changes with enter");
    assert_eq!(app.menu.mode, MenuMode::HumanVsEngine);

    app.menu.selected_row = 1;
    handle_menu_key(&mut app, key(KeyCode::Right)).expect("color changes");
    assert_eq!(app.menu.human_color, Color::Black);

    app.menu.selected_row = 2;
    app.menu.engine_depth = MIN_SEARCH_DEPTH;
    handle_menu_key(&mut app, key(KeyCode::Left)).expect("depth clamps low");
    assert_eq!(app.menu.engine_depth, MIN_SEARCH_DEPTH);
    app.menu.engine_depth = MAX_MENU_SEARCH_DEPTH;
    handle_menu_key(&mut app, key(KeyCode::Right)).expect("depth clamps high");
    assert_eq!(app.menu.engine_depth, MAX_MENU_SEARCH_DEPTH);

    app.menu.mode = MenuMode::SelfPlay;
    app.menu.selected_row = 1;
    app.menu.white_depth = 3;
    handle_menu_key(&mut app, key(KeyCode::Right)).expect("white depth changes");
    assert_eq!(app.menu.white_depth, 4);
    assert_eq!(app.menu.black_depth, 3);
    app.menu.selected_row = 2;
    handle_menu_key(&mut app, key(KeyCode::Left)).expect("black depth changes");
    assert_eq!(app.menu.black_depth, 2);
    assert_eq!(app.menu.white_depth, 4);
}

#[test]
fn menu_start_and_exit_keys_change_only_expected_state() {
    let mut start = AppState::new();
    start.menu.selected_row = 3;
    handle_menu_key(&mut start, key(KeyCode::Enter)).expect("start works");
    assert_eq!(start.screen, AppScreen::Game);
    assert!(start.session.is_some());

    for code in [KeyCode::Char('q'), KeyCode::Esc] {
        let mut app = AppState::new();
        handle_menu_key(&mut app, key(code)).expect("exit key works");
        assert!(app.should_quit);
    }
}

#[test]
fn move_input_is_lowercased_length_limited_and_focus_safe() {
    let mut app = human_app(Color::White);
    let mut runtime = EngineRuntime::default();
    for character in ['E', '2', 'E', '4', 'Q', 'Z'] {
        handle_game_key(&mut app, &mut runtime, key(KeyCode::Char(character)))
            .expect("move character accepted");
    }
    assert_eq!(app.session.as_ref().expect("session").move_input, "e2e4q");
    assert!(app.overlay.is_none(), "q inside input must not quit");

    handle_game_key(&mut app, &mut runtime, key(KeyCode::Backspace)).expect("backspace works");
    assert_eq!(app.session.as_ref().expect("session").move_input, "e2e4");
    handle_game_key(&mut app, &mut runtime, key(KeyCode::Esc)).expect("escape clears input");
    assert!(app.session.as_ref().expect("session").move_input.is_empty());
    assert!(app.overlay.is_none());
    handle_game_key(&mut app, &mut runtime, key(KeyCode::Backspace))
        .expect("empty backspace harmless");
}

#[test]
fn enter_submits_legal_move_and_invalid_input_is_transactional() {
    let mut legal = human_app(Color::White);
    let mut runtime = EngineRuntime::default();
    for character in ['e', '2', 'e', '4'] {
        handle_game_key(&mut legal, &mut runtime, key(KeyCode::Char(character)))
            .expect("typing works");
    }
    handle_game_key(&mut legal, &mut runtime, key(KeyCode::Enter)).expect("submit works");
    assert_eq!(legal.session.as_ref().expect("session").game.ply_count(), 1);
    assert!(legal.take_pending_search().is_some());

    let mut malformed = human_app(Color::White);
    let before = malformed.session.as_ref().expect("session").game.clone();
    for character in ['e', '2'] {
        handle_game_key(&mut malformed, &mut runtime, key(KeyCode::Char(character)))
            .expect("typing works");
    }
    handle_game_key(&mut malformed, &mut runtime, key(KeyCode::Enter))
        .expect("invalid submit is surfaced in app state");
    assert_eq!(malformed.session.as_ref().expect("session").game, before);
    assert!(malformed
        .session
        .as_ref()
        .expect("session")
        .status_message
        .is_some());

    let mut illegal = human_app(Color::White);
    let before = illegal.session.as_ref().expect("session").game.clone();
    for character in ['e', '2', 'e', '5'] {
        handle_game_key(&mut illegal, &mut runtime, key(KeyCode::Char(character)))
            .expect("typing works");
    }
    handle_game_key(&mut illegal, &mut runtime, key(KeyCode::Enter))
        .expect("illegal submit is surfaced in app state");
    assert_eq!(illegal.session.as_ref().expect("session").game, before);
}

#[test]
fn move_characters_are_ignored_when_input_is_not_owned_by_human() {
    let mut runtime = EngineRuntime::default();
    let mut engine_turn = human_app(Color::Black);
    handle_game_key(&mut engine_turn, &mut runtime, key(KeyCode::Char('e'))).expect("key handled");
    assert!(engine_turn
        .session
        .as_ref()
        .expect("session")
        .move_input
        .is_empty());

    let mut self_play = self_play_app();
    handle_game_key(&mut self_play, &mut runtime, key(KeyCode::Char('e'))).expect("key handled");
    assert!(self_play
        .session
        .as_ref()
        .expect("session")
        .move_input
        .is_empty());
}

#[test]
fn active_game_shortcuts_open_the_expected_overlay() {
    let cases = [
        (KeyCode::Char('r'), ConfirmationAction::Resign),
        (KeyCode::Char('n'), ConfirmationAction::NewGame),
        (KeyCode::Char('m'), ConfirmationAction::MainMenu),
        (KeyCode::Esc, ConfirmationAction::MainMenu),
        (KeyCode::Char('q'), ConfirmationAction::Quit),
    ];
    for (code, expected) in cases {
        let mut app = human_app(Color::White);
        handle_game_key(&mut app, &mut EngineRuntime::default(), key(code))
            .expect("shortcut handled");
        assert_eq!(app.overlay, Some(Overlay::Confirmation(expected)));
    }

    let mut save = human_app(Color::White);
    handle_game_key(
        &mut save,
        &mut EngineRuntime::default(),
        key(KeyCode::Char('v')),
    )
    .expect("save shortcut handled");
    assert_eq!(save.save_input(), Some("game.txt"));

    let mut self_play = self_play_app();
    handle_game_key(
        &mut self_play,
        &mut EngineRuntime::default(),
        key(KeyCode::Char('r')),
    )
    .expect("self-play r is harmless");
    assert!(self_play.overlay.is_none());
}

#[test]
fn confirmation_cancel_keys_do_not_execute_action() {
    for code in [KeyCode::Char('n'), KeyCode::Esc] {
        let mut app = human_app(Color::White);
        let generation = app.session.as_ref().expect("session").generation;
        app.open_confirmation(ConfirmationAction::NewGame);
        handle_overlay_key(&mut app, &mut EngineRuntime::default(), key(code))
            .expect("cancel handled");
        assert!(app.overlay.is_none());
        assert_eq!(
            app.session.as_ref().expect("session").generation,
            generation
        );
    }
}

#[test]
fn confirmation_actions_resolve_search_state_before_transition() {
    let mut resign = human_app(Color::White);
    execute_confirmation(
        &mut resign,
        &mut EngineRuntime::default(),
        ConfirmationAction::Resign,
    )
    .expect("resign executes");
    assert!(resign.session.as_ref().expect("session").outcome.is_some());

    let mut new_game = human_app(Color::Black);
    let first_generation = new_game.session.as_ref().expect("session").generation;
    let mut runtime = EngineRuntime::default();
    runtime.drive(&mut new_game).expect("worker starts");
    execute_confirmation(&mut new_game, &mut runtime, ConfirmationAction::NewGame)
        .expect("new game executes");
    assert!(runtime.active.is_none());
    assert_ne!(
        new_game.session.as_ref().expect("session").generation,
        first_generation
    );

    let mut menu = human_app(Color::White);
    execute_confirmation(
        &mut menu,
        &mut EngineRuntime::default(),
        ConfirmationAction::MainMenu,
    )
    .expect("menu executes");
    assert_eq!(menu.screen, AppScreen::MainMenu);
    assert!(menu.session.is_none());

    let mut quit = human_app(Color::White);
    execute_confirmation(
        &mut quit,
        &mut EngineRuntime::default(),
        ConfirmationAction::Quit,
    )
    .expect("quit executes");
    assert!(quit.should_quit);
}

#[test]
fn self_play_space_pause_resume_and_step_never_double_schedule() {
    let mut app = self_play_app();
    let mut runtime = EngineRuntime::default();
    handle_game_key(&mut app, &mut runtime, key(KeyCode::Char(' '))).expect("pause handled");
    assert!(!app.session.as_ref().expect("session").auto_play);
    assert!(!app.session.as_ref().expect("session").thinking);
    assert!(app.take_pending_search().is_none());

    handle_game_key(&mut app, &mut runtime, key(KeyCode::Char('s'))).expect("step handled");
    let one_step = app
        .take_pending_search()
        .expect("exactly one step scheduled");
    assert!(app.take_pending_search().is_none());
    app.cancel_search_state(None);

    handle_game_key(&mut app, &mut runtime, key(KeyCode::Char(' '))).expect("resume handled");
    assert!(app.session.as_ref().expect("session").auto_play);
    assert!(app.take_pending_search().is_some());

    let before_request = one_step.ticket.request;
    handle_game_key(&mut app, &mut runtime, key(KeyCode::Char('s')))
        .expect("running step key harmless");
    assert!(app.session.as_ref().expect("session").thinking);
    assert!(before_request > 0);
}

#[test]
fn terminal_self_play_controls_do_not_restart_search() {
    let mut app = self_play_app();
    app.cancel_search_state(None);
    {
        let session = app.session.as_mut().expect("session");
        session.auto_play = false;
        session.outcome = Some(crate::app::GameOutcome::Stalemate);
    }
    let mut runtime = EngineRuntime::default();
    for code in [KeyCode::Char(' '), KeyCode::Char('s')] {
        handle_game_key(&mut app, &mut runtime, key(code)).expect("terminal control harmless");
        assert!(app.take_pending_search().is_none());
    }
}

#[test]
fn ctrl_c_clears_search_and_quits_with_or_without_worker() {
    let mut idle = human_app(Color::White);
    let mut idle_runtime = EngineRuntime::default();
    handle_key(&mut idle, &mut idle_runtime, ctrl(KeyCode::Char('c'))).expect("idle ctrl-c works");
    assert!(idle.should_quit);
    assert!(idle_runtime.active.is_none());

    let mut active = human_app(Color::Black);
    let mut runtime = EngineRuntime::default();
    runtime.drive(&mut active).expect("worker starts");
    handle_key(&mut active, &mut runtime, ctrl(KeyCode::Char('c'))).expect("active ctrl-c works");
    assert!(active.should_quit);
    assert!(runtime.active.is_none());
    let session = active.session.as_ref().expect("session");
    assert!(!session.thinking);
    assert_eq!(session.active_search, None);
}

#[test]
fn runtime_starts_one_pending_worker_and_cancel_joins_it() {
    let mut app = human_app(Color::Black);
    let expected = app.session.as_ref().expect("session").active_search;
    let mut runtime = EngineRuntime::default();
    runtime.drive(&mut app).expect("pending worker starts");
    assert_eq!(
        runtime.active.as_ref().map(|active| active.ticket),
        expected
    );
    assert!(app.take_pending_search().is_none());
    runtime.cancel().expect("worker cancels and joins");
    app.cancel_search_state(None);
    assert!(runtime.active.is_none());
}

#[test]
fn runtime_progress_keeps_worker_active_until_cancelled() {
    let mut app = human_app(Color::Black);
    let request = app.take_pending_search().expect("request");
    let progress = EngineEvent::Progress {
        ticket: request.ticket,
        metrics: SearchMetrics {
            depth: Some(7),
            nodes: Some(77),
            ..SearchMetrics::default()
        },
    };
    let (worker, receiver) = SearchWorker::waiting_with_event_for_test(progress);
    let mut runtime = EngineRuntime {
        active: Some(ActiveWorker {
            ticket: request.ticket,
            worker,
            receiver,
        }),
    };
    runtime.drive(&mut app).expect("progress drains");
    assert!(runtime.active.is_some());
    assert_eq!(
        app.session
            .as_ref()
            .expect("session")
            .engine_info
            .as_ref()
            .and_then(|metrics| metrics.depth),
        Some(7)
    );
    runtime.cancel().expect("synthetic worker cancels");
    app.cancel_search_state(None);
}

#[test]
fn runtime_final_events_join_and_clear_worker_ownership() {
    let cases = [
        EngineEvent::Completed {
            ticket: SearchTicket {
                generation: 1,
                request: 1,
            },
            best_move: opening_move(),
            metrics: SearchMetrics::default(),
        },
        EngineEvent::Failed {
            ticket: SearchTicket {
                generation: 1,
                request: 1,
            },
            message: "synthetic runtime failure".to_owned(),
        },
        EngineEvent::Cancelled {
            ticket: SearchTicket {
                generation: 1,
                request: 1,
            },
        },
    ];

    for template in cases {
        let mut app = human_app(Color::Black);
        let request = app.take_pending_search().expect("request");
        let event = match template {
            EngineEvent::Completed {
                best_move, metrics, ..
            } => EngineEvent::Completed {
                ticket: request.ticket,
                best_move,
                metrics,
            },
            EngineEvent::Failed { message, .. } => EngineEvent::Failed {
                ticket: request.ticket,
                message,
            },
            EngineEvent::Cancelled { .. } => EngineEvent::Cancelled {
                ticket: request.ticket,
            },
            EngineEvent::Progress { .. } => unreachable!(),
        };
        let (worker, receiver) = SearchWorker::finished_with_events_for_test(vec![event]);
        let mut runtime = EngineRuntime {
            active: Some(ActiveWorker {
                ticket: request.ticket,
                worker,
                receiver,
            }),
        };
        runtime.drive(&mut app).expect("final event drains");
        assert!(runtime.active.is_none());
        assert!(!app.session.as_ref().expect("session").thinking);
    }
}

#[test]
fn runtime_worker_without_final_event_fails_visibly() {
    let mut app = human_app(Color::Black);
    let request = app.take_pending_search().expect("request");
    let (worker, receiver) = SearchWorker::finished_without_event_for_test();
    let mut runtime = EngineRuntime {
        active: Some(ActiveWorker {
            ticket: request.ticket,
            worker,
            receiver,
        }),
    };
    runtime
        .drive(&mut app)
        .expect("missing final event is converted to failure");
    assert!(runtime.active.is_none());
    let session = app.session.as_ref().expect("session");
    assert!(!session.thinking);
    assert!(session
        .status_message
        .as_deref()
        .is_some_and(|message| message.contains("without a final event")));
}

#[test]
fn runtime_worker_panic_propagates_and_boundary_can_clear_thinking() {
    let mut app = human_app(Color::Black);
    let request = app.take_pending_search().expect("request");
    let (worker, receiver) = SearchWorker::panicking_for_test();
    let mut runtime = EngineRuntime {
        active: Some(ActiveWorker {
            ticket: request.ticket,
            worker,
            receiver,
        }),
    };
    let error = runtime.drive(&mut app).expect_err("panic must propagate");
    assert!(matches!(error, SearchWorkerError::ThreadPanicked));
    app.cancel_search_state(Some(format!("Search worker failed: {error}")));
    let session = app.session.as_ref().expect("session");
    assert!(!session.thinking);
    assert!(session
        .status_message
        .as_deref()
        .is_some_and(|message| message.contains("panicked")));
}

#[test]
fn runtime_spawn_failure_is_visible_and_clears_thinking() {
    let mut app = human_app(Color::Black);
    let request = app.take_pending_search().expect("request");
    let mut runtime = EngineRuntime::default();
    runtime
        .handle_spawn_result(
            &mut app,
            request.ticket,
            Err(SearchWorkerError::ThreadSpawn {
                kind: io::ErrorKind::Other,
                message: "synthetic spawn failure".to_owned(),
            }),
        )
        .expect("spawn failure is converted to app failure state");
    assert!(runtime.active.is_none());
    let session = app.session.as_ref().expect("session");
    assert!(!session.thinking);
    assert_eq!(session.active_search, None);
    assert!(session
        .status_message
        .as_deref()
        .is_some_and(|message| message.contains("synthetic spawn failure")));
}

#[test]
fn runtime_application_error_never_leaves_thinking_wedged() {
    let mut app = human_app(Color::Black);
    let request = app.take_pending_search().expect("request");
    let mut other = Game::starting();
    let white_syntax = "e2e4".parse::<UciMove>().expect("syntax");
    let white = other
        .legal_moves()
        .expect("moves")
        .iter()
        .find(|candidate| white_syntax.matches(*candidate))
        .expect("e2e4 legal");
    other.make_move(white).expect("white move");
    let black_syntax = "e7e5".parse::<UciMove>().expect("syntax");
    let illegal_here = other
        .legal_moves()
        .expect("moves")
        .iter()
        .find(|candidate| black_syntax.matches(*candidate))
        .expect("e7e5 legal after e2e4");

    let (worker, receiver) =
        SearchWorker::finished_with_events_for_test(vec![EngineEvent::Completed {
            ticket: request.ticket,
            best_move: illegal_here,
            metrics: SearchMetrics::default(),
        }]);
    let mut runtime = EngineRuntime {
        active: Some(ActiveWorker {
            ticket: request.ticket,
            worker,
            receiver,
        }),
    };
    runtime
        .drive(&mut app)
        .expect("application error handled at runtime boundary");
    assert!(runtime.active.is_none());
    let session = app.session.as_ref().expect("session");
    assert!(!session.thinking);
    assert!(session
        .status_message
        .as_deref()
        .is_some_and(|message| message.contains("Application error")));
}

#[test]
fn self_play_final_cleanup_can_start_the_legitimate_next_search() {
    let mut app = self_play_app();
    let request = app.take_pending_search().expect("white request");
    let (worker, receiver) =
        SearchWorker::finished_with_events_for_test(vec![EngineEvent::Completed {
            ticket: request.ticket,
            best_move: opening_move(),
            metrics: SearchMetrics::default(),
        }]);
    let mut runtime = EngineRuntime {
        active: Some(ActiveWorker {
            ticket: request.ticket,
            worker,
            receiver,
        }),
    };
    runtime.drive(&mut app).expect("white completion handled");
    assert!(
        runtime.active.is_some(),
        "black search should start only after cleanup"
    );
    assert_eq!(app.session.as_ref().expect("session").game.ply_count(), 1);
    runtime.cancel().expect("next search cancels cleanly");
    app.cancel_search_state(None);
}

#[test]
fn save_overlay_editing_and_cancel_are_deterministic() {
    let mut app = human_app(Color::White);
    let mut runtime = EngineRuntime::default();
    app.open_save_path();
    assert_eq!(app.save_input(), Some("game.txt"));
    handle_overlay_key(&mut app, &mut runtime, key(KeyCode::Backspace)).expect("backspace");
    assert_eq!(app.save_input(), Some("game.tx"));
    handle_overlay_key(&mut app, &mut runtime, key(KeyCode::Char('t'))).expect("append");
    assert_eq!(app.save_input(), Some("game.txt"));
    handle_key(&mut app, &mut runtime, ctrl(KeyCode::Char('x')))
        .expect("control-modified key ignored");
    assert_eq!(app.save_input(), Some("game.txt"));
    handle_overlay_key(&mut app, &mut runtime, key(KeyCode::Esc)).expect("cancel");
    assert!(app.overlay.is_none());

    app.overlay = Some(Overlay::SavePath {
        input: String::new(),
    });
    handle_overlay_key(&mut app, &mut runtime, key(KeyCode::Backspace))
        .expect("empty backspace harmless");
    assert_eq!(app.save_input(), Some(""));
}

#[test]
fn empty_and_failed_save_paths_never_mark_success() {
    for input in ["", "   "] {
        let mut app = human_app(Color::White);
        app.overlay = Some(Overlay::SavePath {
            input: input.to_owned(),
        });
        save_current_game(&mut app).expect("empty path becomes visible failure");
        let session = app.session.as_ref().expect("session");
        assert_eq!(session.saved_path, None);
        assert!(session
            .status_message
            .as_deref()
            .is_some_and(|message| message.contains("path must not be empty")));
    }

    let mut app = human_app(Color::White);
    app.mark_saved("stale.txt".to_owned())
        .expect("stale save recorded");
    let missing = unique_path("missing-parent").join("game.txt");
    app.overlay = Some(Overlay::SavePath {
        input: missing.display().to_string(),
    });
    save_current_game(&mut app).expect("write failure is represented in state");
    let session = app.session.as_ref().expect("session");
    assert_eq!(session.saved_path, None);
    assert!(session
        .status_message
        .as_deref()
        .is_some_and(|message| message.starts_with("Save failed:")));
    assert!(!session
        .status_message
        .as_deref()
        .unwrap_or_default()
        .contains("Saved to"));
}

#[test]
fn no_session_save_fails_loudly() {
    let mut app = AppState::new();
    app.overlay = Some(Overlay::SavePath {
        input: "orphan.txt".to_owned(),
    });
    let error = save_current_game(&mut app).expect_err("impossible no-session save must be loud");
    assert!(error.to_string().contains("no game exists"));
    assert!(app.overlay.is_none());
}

#[test]
fn successful_save_transaction_records_exact_path_contents_and_clears_after_move() {
    let path = unique_path("success");
    let mut app = human_app(Color::White);
    app.overlay = Some(Overlay::SavePath {
        input: path.display().to_string(),
    });
    save_current_game(&mut app).expect("save succeeds");
    let contents = fs::read_to_string(&path).expect("save file readable");
    let timestamp = contents
        .lines()
        .find_map(|line| line.strip_prefix("date: "))
        .expect("timestamp line present");
    let session = app.session.as_ref().expect("session");
    assert_eq!(contents, serialize_game(session, Some(timestamp)));
    assert_eq!(
        session.saved_path.as_deref(),
        Some(path.to_string_lossy().as_ref())
    );
    assert!(session
        .status_message
        .as_deref()
        .is_some_and(|message| message.starts_with("Saved to ")));
    assert!(app.overlay.is_none());

    app.submit_human_move("e2e4").expect("later move applies");
    assert_eq!(app.session.as_ref().expect("session").saved_path, None);
    fs::remove_file(path).expect("temporary save removed");
}

#[test]
fn overlay_and_safe_render_states_are_structurally_visible() {
    let overlays = [
        (
            Overlay::Confirmation(ConfirmationAction::Resign),
            "Resign this game?",
        ),
        (
            Overlay::Confirmation(ConfirmationAction::NewGame),
            "start a new one?",
        ),
        (
            Overlay::Confirmation(ConfirmationAction::MainMenu),
            "return to the menu?",
        ),
        (Overlay::Confirmation(ConfirmationAction::Quit), "and quit?"),
        (
            Overlay::SavePath {
                input: "chosen.txt".to_owned(),
            },
            "chosen.txt",
        ),
    ];
    for (overlay, expected) in overlays {
        let mut app = human_app(Color::White);
        app.overlay = Some(overlay);
        assert!(rendered_text(&app, 120, 40).contains(expected));
    }

    let app = human_app(Color::White);
    let too_small = rendered_text(&app, 40, 10);
    assert!(too_small.contains("Terminal too small"));

    let mut no_session = AppState::new();
    no_session.screen = AppScreen::Game;
    assert!(rendered_text(&no_session, 120, 40).contains("No game session"));
}
