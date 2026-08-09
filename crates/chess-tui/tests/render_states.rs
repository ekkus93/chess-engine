use chess_core::Color;
use chess_tui::{
    app::{AppState, GameConfig, GameOutcome},
    render::format_search_metrics,
    ui::render,
};
use ratatui::{backend::TestBackend, Terminal};

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
fn game_over_state_renders_terminal_result() {
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::White,
        engine_depth: 1,
    })
    .expect("game starts");
    app.session.as_mut().expect("session").outcome = Some(GameOutcome::Resignation {
        winner: Color::Black,
    });

    let text = rendered_text(&app, 120, 40);
    assert!(text.contains("Resignation"));
    assert!(text.contains("Black wins"));
}

#[test]
fn game_over_state_renders_a_distinguishable_panel() {
    // RF-003.1: the terminal result must be visible in a distinguishable
    // panel, not only folded into the routine in-game status text that
    // `game_over_state_renders_terminal_result` already covers.
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::White,
        engine_depth: 1,
    })
    .expect("game starts");
    app.session.as_mut().expect("session").outcome = Some(GameOutcome::Resignation {
        winner: Color::Black,
    });

    let text = rendered_text(&app, 120, 40);
    assert!(
        text.contains("Game Over"),
        "expected a distinct 'Game Over' panel title:\n{text}"
    );

    let mut in_progress = AppState::new();
    in_progress
        .start_game(GameConfig::HumanVsEngine {
            human_color: Color::White,
            engine_depth: 1,
        })
        .expect("game starts");
    let mid_game_text = rendered_text(&in_progress, 120, 40);
    assert!(
        !mid_game_text.contains("Game Over"),
        "the panel must not appear before the game has a terminal outcome:\n{mid_game_text}"
    );
}

#[test]
fn visible_error_state_renders_status_message() {
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::White,
        engine_depth: 1,
    })
    .expect("game starts");
    app.session.as_mut().expect("session").status_message =
        Some("synthetic visible failure".to_owned());

    let text = rendered_text(&app, 120, 40);
    assert!(text.contains("synthetic visible failure"));
}

#[test]
fn unavailable_engine_metrics_are_not_fabricated_as_zeroes() {
    let text = format_search_metrics(None);
    assert!(text.contains("depth  -"));
    assert!(text.contains("score  -"));
    assert!(text.contains("nodes  -"));
    assert!(text.contains("nps    -"));
    assert!(text.contains("time   -"));
    assert!(text.contains("hash   -"));
    assert!(text.contains("pv     -"));
    assert!(!text.contains("0"));
}
