from pathlib import Path


def append_once(path: str, marker: str, addition: str) -> None:
    target = Path(path)
    text = target.read_text()
    if marker in text:
        return
    if not text.endswith("\n"):
        text += "\n"
    target.write_text(text + addition)


append_once(
    "crates/chess-tui/src/ui/hardening_tests.rs",
    "fn confirmation_acceptance_keys_and_unrelated_keys_dispatch_correctly()",
    r'''
#[test]
fn confirmation_acceptance_keys_and_unrelated_keys_dispatch_correctly() {
    let mut unrelated = human_app(Color::White);
    let mut unrelated_runtime = EngineRuntime::default();
    unrelated.open_confirmation(ConfirmationAction::Quit);
    handle_overlay_key(
        &mut unrelated,
        &mut unrelated_runtime,
        key(KeyCode::Char('x')),
    )
    .expect("unrelated key is harmless");
    assert_eq!(
        unrelated.overlay,
        Some(Overlay::Confirmation(ConfirmationAction::Quit))
    );
    assert!(!unrelated.should_quit);

    let mut yes = human_app(Color::White);
    let mut yes_runtime = EngineRuntime::default();
    yes.open_confirmation(ConfirmationAction::Quit);
    handle_overlay_key(&mut yes, &mut yes_runtime, key(KeyCode::Char('y')))
        .expect("y confirms");
    assert!(yes.should_quit);

    let mut enter = human_app(Color::White);
    let mut enter_runtime = EngineRuntime::default();
    enter.open_confirmation(ConfirmationAction::Quit);
    handle_overlay_key(&mut enter, &mut enter_runtime, key(KeyCode::Enter))
        .expect("enter confirms");
    assert!(enter.should_quit);
}

#[test]
fn selected_self_play_configuration_starts_exactly_and_depths_clamp() {
    let mut app = AppState::new();
    app.menu.mode = MenuMode::SelfPlay;

    app.menu.selected_row = 1;
    app.menu.white_depth = MIN_SEARCH_DEPTH;
    handle_menu_key(&mut app, key(KeyCode::Left)).expect("white depth low clamp");
    assert_eq!(app.menu.white_depth, MIN_SEARCH_DEPTH);
    app.menu.white_depth = MAX_MENU_SEARCH_DEPTH;
    handle_menu_key(&mut app, key(KeyCode::Right)).expect("white depth high clamp");
    assert_eq!(app.menu.white_depth, MAX_MENU_SEARCH_DEPTH);

    app.menu.selected_row = 2;
    app.menu.black_depth = MIN_SEARCH_DEPTH;
    handle_menu_key(&mut app, key(KeyCode::Left)).expect("black depth low clamp");
    assert_eq!(app.menu.black_depth, MIN_SEARCH_DEPTH);
    app.menu.black_depth = MAX_MENU_SEARCH_DEPTH;
    handle_menu_key(&mut app, key(KeyCode::Right)).expect("black depth high clamp");
    assert_eq!(app.menu.black_depth, MAX_MENU_SEARCH_DEPTH);

    app.menu.white_depth = 2;
    app.menu.black_depth = 4;
    app.menu.selected_row = 3;
    handle_menu_key(&mut app, key(KeyCode::Enter)).expect("selected self-play starts");
    assert_eq!(
        app.session.as_ref().expect("session").config,
        GameConfig::SelfPlay {
            white_depth: 2,
            black_depth: 4,
        }
    );
}

#[test]
fn paused_self_play_step_while_thinking_does_not_duplicate_request() {
    let mut app = self_play_app();
    let mut runtime = EngineRuntime::default();
    handle_game_key(&mut app, &mut runtime, key(KeyCode::Char(' '))).expect("pause handled");
    handle_game_key(&mut app, &mut runtime, key(KeyCode::Char('s')))
        .expect("first step schedules");
    assert!(app.session.as_ref().expect("session").thinking);
    handle_game_key(&mut app, &mut runtime, key(KeyCode::Char('s')))
        .expect("second step is rejected visibly");
    assert!(app.session.as_ref().expect("session").thinking);
    assert!(app
        .session
        .as_ref()
        .expect("session")
        .status_message
        .as_deref()
        .is_some_and(|message| message.contains("already active")));
    assert!(app.take_pending_search().is_some());
    assert!(app.take_pending_search().is_none());
    app.cancel_search_state(None);
}

#[test]
fn idle_runtime_cancel_is_harmless() {
    let mut runtime = EngineRuntime::default();
    runtime.cancel().expect("idle cancel succeeds");
    assert!(runtime.active.is_none());
}

#[test]
fn every_abandonment_confirmation_resolves_active_worker_first() {
    let actions = [
        ConfirmationAction::Resign,
        ConfirmationAction::NewGame,
        ConfirmationAction::MainMenu,
        ConfirmationAction::Quit,
    ];
    for action in actions {
        let mut app = human_app(Color::Black);
        let mut runtime = EngineRuntime::default();
        runtime.drive(&mut app).expect("active worker starts");
        assert!(runtime.active.is_some());
        execute_confirmation(&mut app, &mut runtime, action).expect("confirmation executes");
        assert!(runtime.active.is_none());
        assert!(app
            .session
            .as_ref()
            .is_none_or(|session| !session.thinking && session.active_search.is_none()));
    }
}

#[test]
fn too_small_message_reports_current_and_required_dimensions_when_space_allows() {
    let app = human_app(Color::White);
    let text = rendered_text(&app, 79, 45);
    assert!(text.contains("Terminal too small"));
    assert!(text.contains("80×32"));
    assert!(text.contains("58×46"));
    assert!(text.contains("79×45"));
}
''',
)

append_once(
    "crates/chess-tui/src/app/hardening_tests.rs",
    "fn claimable_threefold_remains_active_and_does_not_stop_scheduling()",
    r'''
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
    app.refresh_terminal_state().expect("claimable status refreshes");
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
''',
)
