use std::{
    io::{self, Write},
    path::Path,
    sync::mpsc::{Receiver, RecvTimeoutError, TryRecvError},
    time::{Duration, SystemTime},
};

use chess_app::{
    text::{
        board_lines, format_duration, format_move_history, format_score, format_search_metrics,
        orientation_for_config, turn_status,
    },
    EngineEvent, GameConfig, GameController, SearchMetrics, SearchTicket, SearchWorker,
};

use crate::{
    command::{parse_command, Command},
    input::InputEvent,
    menu::{prompt_menu, MenuSelection},
    save::{serialize_game, write_game},
};

const ACTIVE_INPUT_POLL: Duration = Duration::from_millis(15);

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ExitReason {
    Quit,
    Eof,
}

#[derive(Clone, Debug, Eq, PartialEq)]
enum GameLoopExit {
    Menu,
    Quit,
    Eof,
}

#[derive(Clone, Debug, Eq, PartialEq)]
enum ConfirmationAction {
    Resign,
    New,
    Menu,
    Quit,
    Overwrite(String),
}

struct ActiveSearch {
    ticket: SearchTicket,
    worker: SearchWorker,
    receiver: Receiver<EngineEvent>,
}

struct ConsoleGame {
    controller: GameController,
    active: Option<ActiveSearch>,
    confirmation: Option<ConfirmationAction>,
    prompt_needed: bool,
}

pub fn run_console<W: Write>(
    input: &Receiver<InputEvent>,
    output: &mut W,
) -> io::Result<ExitReason> {
    writeln!(output, "Rust Chess Console")?;
    writeln!(
        output,
        "Authoritative Rust core/search; type help during a game for commands."
    )?;
    output.flush()?;

    loop {
        let Some(selection) = prompt_menu(input, output)? else {
            writeln!(output, "EOF received at menu; exiting.")?;
            output.flush()?;
            return Ok(ExitReason::Eof);
        };
        match selection {
            MenuSelection::Quit => return Ok(ExitReason::Quit),
            MenuSelection::Game(config) => {
                let mut game = ConsoleGame::new(config)?;
                game.print_board_and_status(output)?;
                game.spawn_pending(output)?;
                match game.run(input, output)? {
                    GameLoopExit::Menu => {}
                    GameLoopExit::Quit => return Ok(ExitReason::Quit),
                    GameLoopExit::Eof => return Ok(ExitReason::Eof),
                }
            }
        }
    }
}

impl ConsoleGame {
    fn new(config: GameConfig) -> io::Result<Self> {
        let mut controller = GameController::new();
        controller
            .start_game(config)
            .map_err(|error| io::Error::other(error.to_string()))?;
        Ok(Self {
            controller,
            active: None,
            confirmation: None,
            prompt_needed: true,
        })
    }

    fn run<W: Write>(
        &mut self,
        input: &Receiver<InputEvent>,
        output: &mut W,
    ) -> io::Result<GameLoopExit> {
        loop {
            self.drive_worker(output)?;
            if self.confirmation.is_none() {
                self.spawn_pending(output)?;
            }
            self.print_prompt_if_needed(output)?;

            let event = if self.active.is_some() {
                match input.recv_timeout(ACTIVE_INPUT_POLL) {
                    Ok(event) => Some(event),
                    Err(RecvTimeoutError::Timeout) => None,
                    Err(RecvTimeoutError::Disconnected) => Some(InputEvent::Eof),
                }
            } else {
                match input.recv() {
                    Ok(event) => Some(event),
                    Err(_) => Some(InputEvent::Eof),
                }
            };

            let Some(event) = event else {
                continue;
            };
            match event {
                InputEvent::Line(line) => {
                    self.prompt_needed = true;
                    if let Some(exit) = self.handle_line(&line, output)? {
                        return Ok(exit);
                    }
                }
                InputEvent::Eof => {
                    self.cancel_active()?;
                    self.controller
                        .cancel_search_state(Some("Input closed".to_owned()));
                    writeln!(output, "EOF received; active search resolved; exiting.")?;
                    output.flush()?;
                    return Ok(GameLoopExit::Eof);
                }
                InputEvent::Error(message) => {
                    self.cancel_active()?;
                    self.controller
                        .cancel_search_state(Some(format!("Input failed: {message}")));
                    return Err(io::Error::other(format!("console input failed: {message}")));
                }
            }
        }
    }

    fn handle_line<W: Write>(
        &mut self,
        line: &str,
        output: &mut W,
    ) -> io::Result<Option<GameLoopExit>> {
        if self.confirmation.is_some() {
            return self.handle_confirmation(line, output);
        }

        let command = match parse_command(line) {
            Ok(command) => command,
            Err(error) => {
                writeln!(output, "Error: {error}")?;
                return Ok(None);
            }
        };
        self.handle_command(command, output)
    }

    fn handle_command<W: Write>(
        &mut self,
        command: Command,
        output: &mut W,
    ) -> io::Result<Option<GameLoopExit>> {
        match command {
            Command::Move(input) => match self.controller.submit_human_move(&input) {
                Ok(()) => {
                    let played = self
                        .controller
                        .session
                        .as_ref()
                        .and_then(|session| session.game.moves().last())
                        .map(|current| current.to_uci())
                        .unwrap_or(input);
                    writeln!(output, "You played: {played}")?;
                    self.print_board_and_status(output)?;
                    self.spawn_pending(output)?;
                }
                Err(error) => writeln!(output, "Error: {error}")?,
            },
            Command::Board => self.print_board(output)?,
            Command::Moves => self.print_moves(output)?,
            Command::Status => self.print_status(output)?,
            Command::Engine => self.print_engine(output)?,
            Command::Help => print_help(output)?,
            Command::Resign => {
                let Some(session) = self.controller.session.as_ref() else {
                    writeln!(output, "Error: no game is active")?;
                    return Ok(None);
                };
                if session.config.is_self_play() {
                    writeln!(
                        output,
                        "Error: resign is only available in Human vs Engine mode"
                    )?;
                } else if !session.is_active() {
                    writeln!(output, "Error: the game is already over")?;
                } else {
                    self.request_confirmation(ConfirmationAction::Resign, output)?;
                }
            }
            Command::Save(path) => self.request_save(path, output)?,
            Command::New => {
                if self.game_is_active() {
                    self.request_confirmation(ConfirmationAction::New, output)?;
                } else {
                    self.restart(output)?;
                }
            }
            Command::Menu => {
                if self.game_is_active() {
                    self.request_confirmation(ConfirmationAction::Menu, output)?;
                } else {
                    self.cancel_active()?;
                    self.controller.abandon_game();
                    return Ok(Some(GameLoopExit::Menu));
                }
            }
            Command::Quit => {
                if self.game_is_active() {
                    self.request_confirmation(ConfirmationAction::Quit, output)?;
                } else {
                    self.cancel_active()?;
                    return Ok(Some(GameLoopExit::Quit));
                }
            }
            Command::Pause => self.pause_self_play(output)?,
            Command::Resume => self.resume_self_play(output)?,
            Command::Step => self.step_self_play(output)?,
        }
        Ok(None)
    }

    fn request_confirmation<W: Write>(
        &mut self,
        action: ConfirmationAction,
        output: &mut W,
    ) -> io::Result<()> {
        let overwrite_path = match &action {
            ConfirmationAction::Overwrite(path) => Some(path.clone()),
            _ => None,
        };
        let label = match &action {
            ConfirmationAction::Resign => "Resign this game?",
            ConfirmationAction::New => "Abandon this game and start a new one?",
            ConfirmationAction::Menu => "Abandon this game and return to the menu?",
            ConfirmationAction::Quit => "Abandon this game and quit?",
            ConfirmationAction::Overwrite(_) => "",
        };
        if let Some(path) = overwrite_path {
            self.confirmation = Some(ConfirmationAction::Overwrite(path.clone()));
            writeln!(output, "Overwrite existing file {path:?}? [y/N]")?;
        } else {
            self.confirmation = Some(action);
            writeln!(output, "{label} [y/N]")?;
        }
        output.flush()
    }

    fn handle_confirmation<W: Write>(
        &mut self,
        line: &str,
        output: &mut W,
    ) -> io::Result<Option<GameLoopExit>> {
        let normalized = line.trim().to_ascii_lowercase();
        if matches!(normalized.as_str(), "" | "n" | "no") {
            self.confirmation = None;
            writeln!(output, "Cancelled.")?;
            self.spawn_pending(output)?;
            return Ok(None);
        }
        if !matches!(normalized.as_str(), "y" | "yes") {
            writeln!(
                output,
                "Please answer y/yes or n/no. Empty input means No."
            )?;
            return Ok(None);
        }
        let Some(action) = self.confirmation.take() else {
            return Ok(None);
        };
        match action {
            ConfirmationAction::Resign => {
                self.cancel_active()?;
                self.controller.cancel_search_state(None);
                match self.controller.resign_human() {
                    Ok(()) => self.print_board_and_status(output)?,
                    Err(error) => writeln!(output, "Error: {error}")?,
                }
                Ok(None)
            }
            ConfirmationAction::New => {
                self.cancel_active()?;
                self.controller.cancel_search_state(None);
                self.restart(output)?;
                Ok(None)
            }
            ConfirmationAction::Menu => {
                self.cancel_active()?;
                self.controller.cancel_search_state(None);
                self.controller.abandon_game();
                Ok(Some(GameLoopExit::Menu))
            }
            ConfirmationAction::Quit => {
                self.cancel_active()?;
                self.controller.cancel_search_state(None);
                Ok(Some(GameLoopExit::Quit))
            }
            ConfirmationAction::Overwrite(path) => {
                self.save_to_path(&path, output)?;
                Ok(None)
            }
        }
    }

    fn pause_self_play<W: Write>(&mut self, output: &mut W) -> io::Result<()> {
        let Some(session) = self.controller.session.as_ref() else {
            writeln!(output, "Error: no game is active")?;
            return Ok(());
        };
        if !session.config.is_self_play() {
            writeln!(output, "Error: pause is only available during Self-play")?;
            return Ok(());
        }
        if !session.is_active() {
            writeln!(output, "Error: the game is already over")?;
            return Ok(());
        }
        self.cancel_active()?;
        match self.controller.pause_self_play() {
            Ok(()) => writeln!(output, "Self-play paused.")?,
            Err(error) => writeln!(output, "Error: {error}")?,
        }
        Ok(())
    }

    fn resume_self_play<W: Write>(&mut self, output: &mut W) -> io::Result<()> {
        match self.controller.resume_self_play() {
            Ok(()) => {
                writeln!(output, "Self-play resumed.")?;
                self.spawn_pending(output)?;
            }
            Err(error) => writeln!(output, "Error: {error}")?,
        }
        Ok(())
    }

    fn step_self_play<W: Write>(&mut self, output: &mut W) -> io::Result<()> {
        match self.controller.step_self_play() {
            Ok(()) => {
                writeln!(output, "Self-play step scheduled.")?;
                self.spawn_pending(output)?;
            }
            Err(error) => writeln!(output, "Error: {error}")?,
        }
        Ok(())
    }

    fn restart<W: Write>(&mut self, output: &mut W) -> io::Result<()> {
        self.controller
            .restart_current_game()
            .map_err(|error| io::Error::other(error.to_string()))?;
        writeln!(output, "New game started.")?;
        self.print_board_and_status(output)?;
        self.spawn_pending(output)
    }

    fn request_save<W: Write>(&mut self, path: String, output: &mut W) -> io::Result<()> {
        if path.trim().is_empty() {
            writeln!(output, "Error: save path must not be empty")?;
            return Ok(());
        }
        if self.controller.session.is_none() {
            writeln!(output, "Error: no game exists to save")?;
            return Ok(());
        }
        if Path::new(&path).exists() {
            self.request_confirmation(ConfirmationAction::Overwrite(path), output)
        } else {
            self.save_to_path(&path, output)
        }
    }

    fn save_to_path<W: Write>(&mut self, path: &str, output: &mut W) -> io::Result<()> {
        let Some(session) = self.controller.session.as_ref() else {
            writeln!(output, "Error: no game exists to save")?;
            return Ok(());
        };
        let timestamp = timestamp_label()?;
        let contents = serialize_game(session, Some(&timestamp));
        match write_game(Path::new(path), &contents) {
            Ok(()) => writeln!(output, "Saved to {path}")?,
            Err(error) => writeln!(output, "Save failed: {error}")?,
        }
        Ok(())
    }

    fn spawn_pending<W: Write>(&mut self, output: &mut W) -> io::Result<()> {
        if self.active.is_some() || self.confirmation.is_some() {
            return Ok(());
        }
        let Some(request) = self.controller.take_pending_search() else {
            return Ok(());
        };
        let ticket = request.ticket;
        match SearchWorker::spawn(request) {
            Ok((worker, receiver)) => {
                self.active = Some(ActiveSearch {
                    ticket,
                    worker,
                    receiver,
                });
                writeln!(output, "Engine thinking...")?;
            }
            Err(error) => {
                self.controller
                    .handle_engine_event(EngineEvent::Failed {
                        ticket,
                        message: error.to_string(),
                    })
                    .map_err(|app_error| io::Error::other(app_error.to_string()))?;
                writeln!(output, "Search failed: {error}")?;
            }
        }
        Ok(())
    }

    fn drive_worker<W: Write>(&mut self, output: &mut W) -> io::Result<()> {
        loop {
            let event = match self.active.as_ref() {
                Some(active) => match active.receiver.try_recv() {
                    Ok(event) => Some(Ok(event)),
                    Err(TryRecvError::Empty) => None,
                    Err(TryRecvError::Disconnected) => Some(Err(())),
                },
                None => None,
            };
            let Some(event) = event else {
                break;
            };
            match event {
                Ok(EngineEvent::Progress { ticket, metrics }) => {
                    self.controller
                        .handle_engine_event(EngineEvent::Progress {
                            ticket,
                            metrics: metrics.clone(),
                        })
                        .map_err(|error| io::Error::other(error.to_string()))?;
                    writeln!(output, "{}", format_progress_line(&metrics))?;
                }
                Ok(final_event) => {
                    let Some(mut active) = self.active.take() else {
                        return Err(io::Error::other(
                            "search final event arrived without active worker",
                        ));
                    };
                    if let Err(error) = active.worker.join() {
                        self.controller
                            .handle_engine_event(EngineEvent::Failed {
                                ticket: active.ticket,
                                message: error.to_string(),
                            })
                            .map_err(|app_error| io::Error::other(app_error.to_string()))?;
                        writeln!(output, "Search failed: {error}")?;
                    } else {
                        self.apply_final_event(final_event, output)?;
                    }
                    self.prompt_needed = true;
                    if self.confirmation.is_none() {
                        self.spawn_pending(output)?;
                    }
                }
                Err(()) => {
                    let Some(mut active) = self.active.take() else {
                        break;
                    };
                    let message = match active.worker.join() {
                        Ok(()) => "search worker channel closed before a final event".to_owned(),
                        Err(error) => error.to_string(),
                    };
                    self.controller
                        .handle_engine_event(EngineEvent::Failed {
                            ticket: active.ticket,
                            message: message.clone(),
                        })
                        .map_err(|error| io::Error::other(error.to_string()))?;
                    writeln!(output, "Search failed: {message}")?;
                    self.prompt_needed = true;
                }
            }
        }
        output.flush()
    }

    fn apply_final_event<W: Write>(
        &mut self,
        event: EngineEvent,
        output: &mut W,
    ) -> io::Result<()> {
        match event {
            EngineEvent::Completed {
                ticket,
                best_move,
                metrics,
            } => {
                let uci = best_move.to_uci();
                match self.controller.handle_engine_event(EngineEvent::Completed {
                    ticket,
                    best_move,
                    metrics,
                }) {
                    Ok(()) => {
                        writeln!(output, "Engine plays: {uci}")?;
                        self.print_board_and_status(output)?;
                    }
                    Err(error) => writeln!(output, "Search result rejected: {error}")?,
                }
            }
            EngineEvent::Cancelled { ticket } => {
                self.controller
                    .handle_engine_event(EngineEvent::Cancelled { ticket })
                    .map_err(|error| io::Error::other(error.to_string()))?;
                writeln!(output, "Search cancelled.")?;
            }
            EngineEvent::Failed { ticket, message } => {
                self.controller
                    .handle_engine_event(EngineEvent::Failed {
                        ticket,
                        message: message.clone(),
                    })
                    .map_err(|error| io::Error::other(error.to_string()))?;
                writeln!(output, "Search failed: {message}")?;
            }
            EngineEvent::Progress { .. } => {
                return Err(io::Error::other(
                    "progress event passed to final-event handler",
                ));
            }
        }
        Ok(())
    }

    fn cancel_active(&mut self) -> io::Result<()> {
        let Some(mut active) = self.active.take() else {
            return Ok(());
        };
        active
            .worker
            .cancel_and_join()
            .map_err(|error| io::Error::other(format!("failed to cancel search worker: {error}")))
    }

    fn print_prompt_if_needed<W: Write>(&mut self, output: &mut W) -> io::Result<()> {
        if !self.prompt_needed || self.confirmation.is_some() {
            return Ok(());
        }
        let prompt = self
            .controller
            .session
            .as_ref()
            .map_or("command> ", |session| {
                if session.human_to_move() {
                    "move> "
                } else {
                    "command> "
                }
            });
        write!(output, "{prompt}")?;
        output.flush()?;
        self.prompt_needed = false;
        Ok(())
    }

    fn print_board_and_status<W: Write>(&self, output: &mut W) -> io::Result<()> {
        self.print_board(output)?;
        self.print_status(output)
    }

    fn print_board<W: Write>(&self, output: &mut W) -> io::Result<()> {
        let Some(session) = self.controller.session.as_ref() else {
            writeln!(output, "No game session")?;
            return Ok(());
        };
        for line in board_lines(
            session.game.position(),
            orientation_for_config(session.config),
        ) {
            writeln!(output, "{line}")?;
        }
        Ok(())
    }

    fn print_moves<W: Write>(&self, output: &mut W) -> io::Result<()> {
        let Some(session) = self.controller.session.as_ref() else {
            writeln!(output, "No game session")?;
            return Ok(());
        };
        let moves = format_move_history(session.game.moves());
        if moves.is_empty() {
            writeln!(output, "(no moves)")
        } else {
            writeln!(output, "{moves}")
        }
    }

    fn print_status<W: Write>(&self, output: &mut W) -> io::Result<()> {
        let Some(session) = self.controller.session.as_ref() else {
            writeln!(output, "No game session")?;
            return Ok(());
        };
        writeln!(output, "{}", turn_status(session))
    }

    fn print_engine<W: Write>(&self, output: &mut W) -> io::Result<()> {
        let Some(session) = self.controller.session.as_ref() else {
            writeln!(output, "No game session")?;
            return Ok(());
        };
        writeln!(
            output,
            "{}",
            format_search_metrics(session.engine_info.as_ref())
        )
    }

    fn game_is_active(&self) -> bool {
        self.controller
            .session
            .as_ref()
            .is_some_and(|session| session.is_active())
    }
}

impl Drop for ConsoleGame {
    fn drop(&mut self) {
        if let Some(active) = self.active.as_mut() {
            let _cleanup_result = active.worker.cancel_and_join();
        }
        self.active = None;
    }
}

#[must_use]
pub fn format_progress_line(metrics: &SearchMetrics) -> String {
    let mut fields = Vec::new();
    if let Some(depth) = metrics.depth {
        fields.push(format!("depth {depth}"));
    }
    if let Some(score) = metrics.score {
        fields.push(format!("score {}", format_score(score)));
    }
    if let Some(nodes) = metrics.nodes {
        fields.push(format!("nodes {nodes}"));
    }
    if let Some(nps) = metrics.nps {
        fields.push(format!("nps {nps}"));
    }
    if let Some(elapsed) = metrics.elapsed {
        fields.push(format!("time {}", format_duration(elapsed)));
    }
    if let Some(hash) = metrics.hash_full_per_mille {
        fields.push(format!("hash {hash}‰"));
    }
    if !metrics.principal_variation.is_empty() {
        fields.push(format!(
            "pv {}",
            metrics
                .principal_variation
                .iter()
                .map(|current| current.to_uci())
                .collect::<Vec<_>>()
                .join(" ")
        ));
    }
    if fields.is_empty() {
        "info unavailable".to_owned()
    } else {
        format!("info {}", fields.join(" "))
    }
}

fn print_help<W: Write>(output: &mut W) -> io::Result<()> {
    writeln!(output, "Commands:")?;
    writeln!(output, "  e2e4 | move e2e4   make a human move")?;
    writeln!(output, "  board               print the board")?;
    writeln!(output, "  moves               print numbered move history")?;
    writeln!(output, "  status              print turn/check/result status")?;
    writeln!(output, "  engine              print latest engine metrics")?;
    writeln!(
        output,
        "  resign              resign Human vs Engine game (confirmed)"
    )?;
    writeln!(
        output,
        "  save <path>         save deterministic non-PGN text"
    )?;
    writeln!(
        output,
        "  new | menu | quit   destructive active-game actions are confirmed"
    )?;
    writeln!(output, "  pause/resume/step   Self-play controls")?;
    writeln!(output, "  help                show this help")
}

fn timestamp_label() -> io::Result<String> {
    let elapsed = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .map_err(|error| io::Error::other(error.to_string()))?;
    Ok(format!("unix-seconds:{}", elapsed.as_secs()))
}

#[cfg(test)]
mod tests {
    use std::{sync::mpsc, time::Duration};

    use chess_app::{GameConfig, SearchMetrics};
    use chess_core::Color;

    use super::{format_progress_line, run_console, ExitReason};
    use crate::input::InputEvent;

    fn scripted(lines: &[&str]) -> (ExitReason, String) {
        let (sender, receiver) = mpsc::channel();
        for line in lines {
            sender
                .send(InputEvent::Line((*line).to_owned()))
                .expect("send");
        }
        drop(sender);
        let mut output = Vec::new();
        let reason = run_console(&receiver, &mut output).expect("console run");
        (reason, String::from_utf8(output).expect("utf8"))
    }

    #[test]
    fn startup_quit_and_eof_are_deterministic() {
        let (quit, output) = scripted(&["3"]);
        assert_eq!(quit, ExitReason::Quit);
        assert!(output.contains("Rust Chess Console"));

        let (sender, receiver) = mpsc::channel();
        sender.send(InputEvent::Eof).expect("eof");
        drop(sender);
        let mut output = Vec::new();
        assert_eq!(
            run_console(&receiver, &mut output).expect("console"),
            ExitReason::Eof
        );
    }

    #[test]
    fn human_mode_invalid_command_and_declined_quit_preserve_game() {
        let (reason, output) =
            scripted(&["1", "1", "1", "foobar", "quit", "", "quit", "yes"]);
        assert_eq!(reason, ExitReason::Quit);
        assert!(output.contains("unknown command: foobar"));
        assert!(output.contains("Cancelled."));
    }

    #[test]
    fn mode_invalid_self_play_commands_are_visible_in_human_game() {
        let (reason, output) = scripted(&["1", "1", "1", "pause", "step", "quit", "y"]);
        assert_eq!(reason, ExitReason::Quit);
        assert!(output.contains("pause is only available during Self-play"));
        assert!(output.contains("step is only available during self-play"));
    }

    #[test]
    fn progress_line_omits_missing_fields_instead_of_fabricating_zeroes() {
        let metrics = SearchMetrics {
            depth: Some(4),
            nodes: Some(40),
            elapsed: Some(Duration::from_millis(5)),
            ..SearchMetrics::default()
        };
        let line = format_progress_line(&metrics);
        assert!(line.contains("depth 4"));
        assert!(line.contains("nodes 40"));
        assert!(!line.contains("score 0"));
        assert!(!line.contains("nps 0"));
        assert_eq!(
            format_progress_line(&SearchMetrics::default()),
            "info unavailable"
        );
    }

    #[test]
    fn shared_configs_used_by_console_keep_expected_modes() {
        let human = GameConfig::HumanVsEngine {
            human_color: Color::Black,
            engine_depth: 3,
        };
        assert_eq!(human.human_color(), Some(Color::Black));
        let self_play = GameConfig::SelfPlay {
            white_depth: 2,
            black_depth: 4,
        };
        assert!(self_play.is_self_play());
    }
}
