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
