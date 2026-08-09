use std::{
    io,
    path::Path,
    sync::mpsc::{Receiver, TryRecvError},
    time::{Duration, SystemTime},
};

use crossterm::event::{self, Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers};
use ratatui::{
    backend::Backend,
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Modifier, Style},
    widgets::{Block, Borders, Clear, Paragraph, Wrap},
    Frame, Terminal,
};

use crate::{
    app::{AppScreen, AppState, ConfirmationAction, GameConfig, MenuMode, Overlay},
    render::{
        board_lines, color_name, format_move_history, format_outcome, format_search_metrics,
        layout_decision, orientation_for_config, turn_status, LayoutDecision, MIN_TERMINAL_HEIGHT,
        MIN_TERMINAL_WIDTH, STACKED_MIN_TERMINAL_HEIGHT, WIDE_TERMINAL_WIDTH,
    },
    save::{serialize_game, write_game},
    worker::{EngineEvent, SearchTicket, SearchWorker, SearchWorkerError},
};

const EVENT_POLL_INTERVAL: Duration = Duration::from_millis(50);

pub fn run<B: Backend>(terminal: &mut Terminal<B>) -> io::Result<()> {
    let mut app = AppState::new();
    let mut runtime = EngineRuntime::default();

    while !app.should_quit {
        if let Err(error) = runtime.drive(&mut app) {
            app.cancel_search_state(Some(format!("Search worker failed: {error}")));
        }
        terminal.draw(|frame| render(frame, &app))?;

        if event::poll(EVENT_POLL_INTERVAL)? {
            match event::read()? {
                Event::Key(key) if key.kind == KeyEventKind::Press => {
                    handle_key(&mut app, &mut runtime, key)?;
                }
                Event::Resize(_, _) => {}
                _ => {}
            }
        }
    }

    runtime.cancel()?;
    Ok(())
}

#[derive(Default)]
struct EngineRuntime {
    active: Option<ActiveWorker>,
}

struct ActiveWorker {
    ticket: SearchTicket,
    worker: SearchWorker,
    receiver: Receiver<EngineEvent>,
}

impl EngineRuntime {
    fn drive(&mut self, app: &mut AppState) -> Result<(), SearchWorkerError> {
        let mut saw_final = false;
        if let Some(active) = self.active.as_mut() {
            loop {
                match active.receiver.try_recv() {
                    Ok(event) => {
                        saw_final |= event.is_final();
                        if let Err(error) = app.handle_engine_event(event) {
                            app.cancel_search_state(Some(format!("Application error: {error}")));
                        }
                    }
                    Err(TryRecvError::Empty) => break,
                    Err(TryRecvError::Disconnected) => break,
                }
            }
            if active.worker.is_finished() && !saw_final {
                let ticket = active.ticket;
                active.worker.join()?;
                app.handle_engine_event(EngineEvent::Failed {
                    ticket,
                    message: "search worker ended without a final event".to_owned(),
                })
                .map_err(|_| SearchWorkerError::EventChannelClosed)?;
                saw_final = true;
            }
        }

        if saw_final {
            if let Some(mut active) = self.active.take() {
                active.worker.join()?;
            }
        }

        if self.active.is_none() {
            if let Some(request) = app.take_pending_search() {
                let ticket = request.ticket;
                let spawn_result = SearchWorker::spawn(request);
                self.handle_spawn_result(app, ticket, spawn_result)?;
            }
        }
        Ok(())
    }

    fn handle_spawn_result(
        &mut self,
        app: &mut AppState,
        ticket: SearchTicket,
        spawn_result: Result<(SearchWorker, Receiver<EngineEvent>), SearchWorkerError>,
    ) -> Result<(), SearchWorkerError> {
        match spawn_result {
            Ok((worker, receiver)) => {
                self.active = Some(ActiveWorker {
                    ticket,
                    worker,
                    receiver,
                });
            }
            Err(error) => {
                if let Err(app_error) = app.handle_engine_event(EngineEvent::Failed {
                    ticket,
                    message: error.to_string(),
                }) {
                    app.cancel_search_state(Some(format!("Search spawn failed: {app_error}")));
                }
            }
        }
        Ok(())
    }

    fn cancel(&mut self) -> io::Result<()> {
        let Some(mut active) = self.active.take() else {
            return Ok(());
        };
        active
            .worker
            .cancel_and_join()
            .map_err(|error| io::Error::other(error.to_string()))
    }
}

fn handle_key(app: &mut AppState, runtime: &mut EngineRuntime, key: KeyEvent) -> io::Result<()> {
    if key.modifiers.contains(KeyModifiers::CONTROL) && key.code == KeyCode::Char('c') {
        runtime.cancel()?;
        app.cancel_search_state(None);
        app.request_quit();
        return Ok(());
    }

    if key.modifiers.contains(KeyModifiers::CONTROL) || key.modifiers.contains(KeyModifiers::ALT) {
        return Ok(());
    }

    if app.overlay.is_some() {
        return handle_overlay_key(app, runtime, key);
    }

    match app.screen {
        AppScreen::MainMenu => handle_menu_key(app, key),
        AppScreen::Game => handle_game_key(app, runtime, key),
    }
}

fn handle_menu_key(app: &mut AppState, key: KeyEvent) -> io::Result<()> {
    match key.code {
        KeyCode::Up => app.menu.select_previous(),
        KeyCode::Down => app.menu.select_next(),
        KeyCode::Left => app.menu.adjust_selected(false),
        KeyCode::Right => app.menu.adjust_selected(true),
        KeyCode::Enter if app.menu.selected_row == 3 => {
            if let Err(error) = app.start_from_menu() {
                return Err(io::Error::other(error.to_string()));
            }
        }
        KeyCode::Enter => app.menu.adjust_selected(true),
        KeyCode::Char('q') | KeyCode::Esc => app.request_quit(),
        _ => {}
    }
    Ok(())
}

fn handle_game_key(
    app: &mut AppState,
    runtime: &mut EngineRuntime,
    key: KeyEvent,
) -> io::Result<()> {
    let Some(session) = app.session.as_ref() else {
        app.return_to_menu();
        return Ok(());
    };
    let human_to_move = session.human_to_move();
    let input_nonempty = !session.move_input.is_empty();
    let self_play = session.config.is_self_play();
    let auto_play = session.auto_play;
    let active_game = session.is_active();

    if human_to_move && input_nonempty {
        match key.code {
            KeyCode::Enter => {
                let input = app
                    .session
                    .as_ref()
                    .map(|current| current.move_input.clone())
                    .unwrap_or_default();
                if let Err(error) = app.submit_human_move(&input) {
                    if let Some(session) = app.session.as_mut() {
                        session.status_message = Some(error.to_string());
                    }
                }
            }
            KeyCode::Backspace => {
                if let Some(session) = app.session.as_mut() {
                    session.move_input.pop();
                }
            }
            KeyCode::Esc => {
                if let Some(session) = app.session.as_mut() {
                    session.move_input.clear();
                }
            }
            KeyCode::Char(character) if is_move_input_character(character) => {
                append_move_character(app, character);
            }
            _ => {}
        }
        return Ok(());
    }

    if self_play {
        match key.code {
            KeyCode::Char(' ') if active_game => {
                if auto_play {
                    runtime.cancel()?;
                    app.pause_self_play().map_err(app_error_to_io)?;
                } else {
                    app.resume_self_play().map_err(app_error_to_io)?;
                }
                return Ok(());
            }
            KeyCode::Char('s') if active_game && !auto_play => {
                if let Err(error) = app.step_self_play() {
                    if let Some(session) = app.session.as_mut() {
                        session.status_message = Some(error.to_string());
                    }
                }
                return Ok(());
            }
            _ => {}
        }
    }

    match key.code {
        KeyCode::Char('q') => {
            if active_game {
                app.open_confirmation(ConfirmationAction::Quit);
            } else {
                app.request_quit();
            }
        }
        KeyCode::Char('n') => {
            if active_game {
                app.open_confirmation(ConfirmationAction::NewGame);
            } else {
                app.restart_current_game().map_err(app_error_to_io)?;
            }
        }
        KeyCode::Char('m') | KeyCode::Esc => {
            if active_game {
                app.open_confirmation(ConfirmationAction::MainMenu);
            } else {
                app.return_to_menu();
            }
        }
        KeyCode::Char('r') if active_game && !self_play => {
            app.open_confirmation(ConfirmationAction::Resign);
        }
        KeyCode::Char('v') => app.open_save_path(),
        KeyCode::Char(character) if human_to_move && is_move_input_character(character) => {
            append_move_character(app, character);
        }
        _ => {}
    }
    Ok(())
}

fn handle_overlay_key(
    app: &mut AppState,
    runtime: &mut EngineRuntime,
    key: KeyEvent,
) -> io::Result<()> {
    let overlay = app.overlay.clone();
    match overlay {
        Some(Overlay::Confirmation(action)) => match key.code {
            KeyCode::Char('y') | KeyCode::Enter => execute_confirmation(app, runtime, action),
            KeyCode::Char('n') | KeyCode::Esc => {
                app.dismiss_overlay();
                Ok(())
            }
            _ => Ok(()),
        },
        Some(Overlay::SavePath { .. }) => match key.code {
            KeyCode::Esc => {
                app.dismiss_overlay();
                Ok(())
            }
            KeyCode::Backspace => {
                if let Some(input) = app.save_input_mut() {
                    input.pop();
                }
                Ok(())
            }
            KeyCode::Enter => save_current_game(app),
            KeyCode::Char(character) if !character.is_control() => {
                if let Some(input) = app.save_input_mut() {
                    input.push(character);
                }
                Ok(())
            }
            _ => Ok(()),
        },
        None => Ok(()),
    }
}

fn execute_confirmation(
    app: &mut AppState,
    runtime: &mut EngineRuntime,
    action: ConfirmationAction,
) -> io::Result<()> {
    runtime.cancel()?;
    app.cancel_search_state(None);
    match action {
        ConfirmationAction::Resign => app.resign_human().map_err(app_error_to_io),
        ConfirmationAction::NewGame => app.restart_current_game().map_err(app_error_to_io),
        ConfirmationAction::MainMenu => {
            app.return_to_menu();
            Ok(())
        }
        ConfirmationAction::Quit => {
            app.request_quit();
            Ok(())
        }
    }
}

fn save_current_game(app: &mut AppState) -> io::Result<()> {
    let path_text = app.save_input().unwrap_or_default().trim().to_owned();
    if path_text.is_empty() {
        app.mark_save_failed("Save failed: path must not be empty".to_owned());
        return Ok(());
    }
    let Some(session) = app.session.as_ref() else {
        app.dismiss_overlay();
        return Err(io::Error::other("Save failed: no game exists"));
    };
    let timestamp = unix_timestamp_label()?;
    let contents = serialize_game(session, Some(&timestamp));
    match write_game(Path::new(&path_text), &contents) {
        Ok(()) => app.mark_saved(path_text).map_err(app_error_to_io),
        Err(error) => {
            app.mark_save_failed(format!("Save failed: {error}"));
            Ok(())
        }
    }
}

fn unix_timestamp_label() -> io::Result<String> {
    let elapsed = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .map_err(|error| io::Error::other(error.to_string()))?;
    Ok(format!("unix-seconds:{}", elapsed.as_secs()))
}

fn append_move_character(app: &mut AppState, character: char) {
    if let Some(session) = app.session.as_mut() {
        if session.move_input.len() < 5 {
            session.move_input.push(character.to_ascii_lowercase());
        }
    }
}

fn is_move_input_character(character: char) -> bool {
    character.is_ascii_alphanumeric()
}

fn app_error_to_io(error: crate::app::AppError) -> io::Error {
    io::Error::other(error.to_string())
}

pub fn render(frame: &mut Frame<'_>, app: &AppState) {
    match app.screen {
        AppScreen::MainMenu => render_menu(frame, app),
        AppScreen::Game => render_game(frame, app),
    }
    render_game_over_panel(frame, app);
    render_overlay(frame, app);
}

/// Renders a distinguishable "Game Over" panel over the game screen once the
/// session has a terminal outcome (RF-003.1). The ordinary in-game status
/// area continues to show the same result text via `turn_status`/
/// `format_outcome`; this panel makes the terminal state visually
/// unmistakable rather than folding it into routine status text, matching
/// how `render_overlay` already distinguishes confirmation/save prompts.
fn render_game_over_panel(frame: &mut Frame<'_>, app: &AppState) {
    if app.screen != AppScreen::Game {
        return;
    }
    let size = frame.size();
    if layout_decision(size.width, size.height) == LayoutDecision::TooSmall {
        return;
    }
    let Some(session) = app.session.as_ref() else {
        return;
    };
    let Some(outcome) = session.outcome else {
        return;
    };
    let area = centered_rect(48, 7, frame.size());
    frame.render_widget(Clear, area);
    frame.render_widget(
        Paragraph::new(format!(
            "{}\n\nn new   m menu   v save   q quit",
            format_outcome(outcome)
        ))
        .block(Block::default().borders(Borders::ALL).title("Game Over"))
        .alignment(Alignment::Center)
        .wrap(Wrap { trim: false }),
        area,
    );
}

fn render_menu(frame: &mut Frame<'_>, app: &AppState) {
    let size = frame.size();
    if layout_decision(size.width, size.height) == LayoutDecision::TooSmall {
        render_too_small_message(frame, size);
        return;
    }

    let area = centered_rect(64, 15, frame.size());
    let mode = match app.menu.mode {
        MenuMode::HumanVsEngine => "Human vs Engine",
        MenuMode::SelfPlay => "Self-play",
    };
    let row_one = match app.menu.mode {
        MenuMode::HumanVsEngine => format!("Human color: {}", color_name(app.menu.human_color)),
        MenuMode::SelfPlay => format!("White depth: {}", app.menu.white_depth),
    };
    let row_two = match app.menu.mode {
        MenuMode::HumanVsEngine => format!("Engine depth: {}", app.menu.engine_depth),
        MenuMode::SelfPlay => format!("Black depth: {}", app.menu.black_depth),
    };
    let rows = [
        format!("Mode: {mode}"),
        row_one,
        row_two,
        "Start game".to_owned(),
    ];
    let mut text = String::from("Rust Chess TUI\n\n");
    for (index, row) in rows.iter().enumerate() {
        let marker = if index == app.menu.selected_row {
            ">"
        } else {
            " "
        };
        text.push_str(&format!("{marker} {row}\n"));
    }
    text.push_str("\n↑/↓ select   ←/→ change   Enter activate   q quit");
    let block = Block::default().borders(Borders::ALL).title("Chess Engine");
    frame.render_widget(
        Paragraph::new(text)
            .block(block)
            .alignment(Alignment::Left)
            .wrap(Wrap { trim: false }),
        area,
    );
}

/// Renders the shared minimum-size message when the terminal is below the
/// smallest supported layout, on whichever screen the caller is drawing.
/// Used by both `render_game` and `render_menu` (RF-003.2) so a menu at an
/// unusably small terminal fails the same way the game screen already does,
/// instead of unconditionally attempting a fixed-size centered layout.
fn render_too_small_message(frame: &mut Frame<'_>, size: Rect) {
    let text = format!(
        "Terminal too small. Need {WIDE_TERMINAL_WIDTH}×{MIN_TERMINAL_HEIGHT} for the wide layout or {MIN_TERMINAL_WIDTH}×{STACKED_MIN_TERMINAL_HEIGHT} for the stacked layout; current {}×{}.",
        size.width, size.height
    );
    frame.render_widget(
        Paragraph::new(text)
            .block(Block::default().borders(Borders::ALL).title("Chess Engine"))
            .alignment(Alignment::Center)
            .wrap(Wrap { trim: false }),
        size,
    );
}

fn render_game(frame: &mut Frame<'_>, app: &AppState) {
    let size = frame.size();
    if layout_decision(size.width, size.height) == LayoutDecision::TooSmall {
        render_too_small_message(frame, size);
        return;
    }

    let Some(session) = app.session.as_ref() else {
        frame.render_widget(Paragraph::new("No game session"), size);
        return;
    };

    let outer = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),
            Constraint::Min(10),
            Constraint::Length(5),
            Constraint::Length(3),
        ])
        .split(size);

    let title = match session.config {
        GameConfig::HumanVsEngine {
            human_color,
            engine_depth,
        } => format!(
            "Chess Engine — Human vs Engine — {} — depth {engine_depth}",
            color_name(human_color)
        ),
        GameConfig::SelfPlay {
            white_depth,
            black_depth,
        } => format!("Chess Engine — Self-play — White d{white_depth} / Black d{black_depth}"),
    };
    frame.render_widget(
        Paragraph::new(title)
            .block(Block::default().borders(Borders::ALL))
            .alignment(Alignment::Center)
            .style(Style::default().add_modifier(Modifier::BOLD)),
        outer[0],
    );

    match layout_decision(size.width, size.height) {
        LayoutDecision::Horizontal => {
            let body = Layout::default()
                .direction(Direction::Horizontal)
                .constraints([Constraint::Length(44), Constraint::Min(30)])
                .split(outer[1]);
            render_board(frame, session, body[0]);
            render_side_panel(frame, session, body[1]);
        }
        LayoutDecision::Vertical => {
            let body = Layout::default()
                .direction(Direction::Vertical)
                .constraints([Constraint::Percentage(60), Constraint::Percentage(40)])
                .split(outer[1]);
            render_board(frame, session, body[0]);
            render_side_panel(frame, session, body[1]);
        }
        LayoutDecision::TooSmall => {}
    }

    let thinking = if session.thinking {
        " — thinking…"
    } else {
        ""
    };
    let message = session.status_message.as_deref().unwrap_or("");
    let input = if session.human_to_move() {
        format!("Move: {}_", session.move_input)
    } else if session.config.is_self_play() {
        let state = if session.auto_play {
            "running"
        } else {
            "paused"
        };
        format!("Self-play: {state}")
    } else {
        "Move input disabled while engine is thinking".to_owned()
    };
    frame.render_widget(
        Paragraph::new(format!(
            "{}{}\n{}\n{}",
            turn_status(session),
            thinking,
            input,
            message
        ))
        .block(Block::default().borders(Borders::ALL).title("Status")),
        outer[2],
    );

    let controls = if session.config.is_self_play() {
        "Space pause/resume | s step (paused) | v save | n new | m menu | q quit"
    } else {
        "Enter move | r resign | v save | n new | m menu | q quit"
    };
    frame.render_widget(
        Paragraph::new(controls)
            .block(Block::default().borders(Borders::ALL))
            .alignment(Alignment::Center),
        outer[3],
    );
}

fn render_board(frame: &mut Frame<'_>, session: &crate::app::GameSession, area: Rect) {
    let orientation = orientation_for_config(session.config);
    let text = board_lines(session.game.position(), orientation).join("\n");
    frame.render_widget(
        Paragraph::new(text)
            .block(Block::default().borders(Borders::ALL).title("Board"))
            .wrap(Wrap { trim: false }),
        area,
    );
}

fn render_side_panel(frame: &mut Frame<'_>, session: &crate::app::GameSession, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)])
        .split(area);
    let moves_area = chunks[0];
    let moves = format_move_history(session.game.moves());
    let (moves_text, scroll) = if moves.is_empty() {
        ("No moves yet".to_owned(), 0)
    } else {
        // Keep the tail of the move list visible once it outgrows the pane,
        // rather than always rendering from the top and clipping the current
        // position out of view (RF-002).
        let visible_rows = moves_area.height.saturating_sub(2);
        let line_count = u16::try_from(moves.lines().count()).unwrap_or(u16::MAX);
        (moves, line_count.saturating_sub(visible_rows))
    };
    frame.render_widget(
        Paragraph::new(moves_text)
            .block(Block::default().borders(Borders::ALL).title("Moves"))
            .wrap(Wrap { trim: false })
            .scroll((scroll, 0)),
        moves_area,
    );
    frame.render_widget(
        Paragraph::new(format_search_metrics(session.engine_info.as_ref()))
            .block(Block::default().borders(Borders::ALL).title("Engine"))
            .wrap(Wrap { trim: false }),
        chunks[1],
    );
}

fn render_overlay(frame: &mut Frame<'_>, app: &AppState) {
    let Some(overlay) = app.overlay.as_ref() else {
        return;
    };
    let area = centered_rect(56, 9, frame.size());
    frame.render_widget(Clear, area);
    let text = match overlay {
        Overlay::Confirmation(action) => {
            let prompt = match action {
                ConfirmationAction::Resign => "Resign this game?",
                ConfirmationAction::NewGame => "Abandon this game and start a new one?",
                ConfirmationAction::MainMenu => "Abandon this game and return to the menu?",
                ConfirmationAction::Quit => "Abandon this game and quit?",
            };
            format!("{prompt}\n\ny / Enter = confirm\nn / Esc = cancel")
        }
        Overlay::SavePath { input } => {
            format!("Save game\n\nPath: {input}_\n\nEnter = save   Esc = cancel")
        }
    };
    frame.render_widget(
        Paragraph::new(text)
            .block(Block::default().borders(Borders::ALL).title("Confirm"))
            .alignment(Alignment::Center)
            .wrap(Wrap { trim: false }),
        area,
    );
}

fn centered_rect(width: u16, height: u16, area: Rect) -> Rect {
    let width = width.min(area.width);
    let height = height.min(area.height);
    Rect {
        x: area.x + area.width.saturating_sub(width) / 2,
        y: area.y + area.height.saturating_sub(height) / 2,
        width,
        height,
    }
}

#[cfg(test)]
mod tests {
    use chess_core::Color;
    use ratatui::{backend::TestBackend, Terminal};

    use super::render;
    use crate::app::{AppState, GameConfig};

    fn draw(app: &AppState, width: u16, height: u16) {
        let backend = TestBackend::new(width, height);
        let mut terminal = Terminal::new(backend).expect("test terminal");
        terminal
            .draw(|frame| render(frame, app))
            .expect("render succeeds");
    }

    // RF-004.1: unlike `draw`, this returns the rendered buffer as text so
    // callers can assert on real content, not just "did not panic."
    fn draw_text(app: &AppState, width: u16, height: u16) -> String {
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
    fn menu_renders_headlessly() {
        // 100x30 is below MIN_TERMINAL_HEIGHT (32) and was, before RF-003.2,
        // rendering the real menu anyway only because render_menu had no
        // small-terminal guard. Use a genuinely supported size so this test
        // exercises real menu content, not the "too small" message.
        let text = draw_text(&AppState::new(), 100, 32);
        assert!(text.contains("Mode: Human vs Engine"), "{text}");
        assert!(text.contains("Start game"), "{text}");
    }

    #[test]
    fn human_game_and_thinking_states_render_headlessly() {
        let mut human = AppState::new();
        human
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::White,
                engine_depth: 1,
            })
            .expect("game starts");
        let text = draw_text(&human, 120, 32);
        assert!(text.contains("Human vs Engine"), "{text}");
        assert!(
            !text.contains("thinking"),
            "human-to-move state must not show the thinking indicator:\n{text}"
        );

        let mut thinking = AppState::new();
        thinking
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::Black,
                engine_depth: 1,
            })
            .expect("game starts");
        let text = draw_text(&thinking, 120, 32);
        assert!(
            text.contains("thinking"),
            "engine-searching state must show the thinking indicator:\n{text}"
        );
    }

    #[test]
    fn self_play_and_small_terminal_render_without_panicking() {
        let mut app = AppState::new();
        app.start_game(GameConfig::SelfPlay {
            white_depth: 1,
            black_depth: 1,
        })
        .expect("self-play starts");
        // 80x28 is below MIN_TERMINAL_HEIGHT (32), so render_game already
        // shows the "too small" message there, not real self-play content —
        // use the smallest genuinely supported horizontal size (80x32) to
        // assert on the actual self-play screen.
        let text = draw_text(&app, 80, 32);
        assert!(text.contains("Self-play"), "{text}");
        assert!(
            text.contains("running") || text.contains("thinking"),
            "self-play state must show it is actively running:\n{text}"
        );
        // Still exercise a genuinely too-small size to confirm it doesn't panic.
        draw(&app, 20, 8);
    }
}

#[cfg(test)]
mod hardening_tests;
