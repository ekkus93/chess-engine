use core::fmt;

use chess_core::{Color, DrawReason, Game, GameStatus, UciMove};

use crate::worker::{EngineEvent, SearchMetrics, SearchRequest, SearchTicket};

pub const DEFAULT_SEARCH_DEPTH: u16 = 3;
pub const MIN_SEARCH_DEPTH: u16 = 1;
pub const MAX_SEARCH_DEPTH: u16 = 12;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum GameConfig {
    HumanVsEngine {
        human_color: Color,
        engine_depth: u16,
    },
    SelfPlay {
        white_depth: u16,
        black_depth: u16,
    },
}

impl GameConfig {
    #[must_use]
    pub const fn depth_for_side(self, side: Color) -> u16 {
        match self {
            Self::HumanVsEngine { engine_depth, .. } => engine_depth,
            Self::SelfPlay {
                white_depth,
                black_depth,
            } => match side {
                Color::White => white_depth,
                Color::Black => black_depth,
            },
        }
    }

    #[must_use]
    pub const fn human_color(self) -> Option<Color> {
        match self {
            Self::HumanVsEngine { human_color, .. } => Some(human_color),
            Self::SelfPlay { .. } => None,
        }
    }

    #[must_use]
    pub const fn is_self_play(self) -> bool {
        matches!(self, Self::SelfPlay { .. })
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum GameOutcome {
    Checkmate { winner: Color },
    Stalemate,
    Draw(DrawReason),
    Resignation { winner: Color },
}

#[derive(Clone, Debug)]
pub struct GameSession {
    pub game: Game,
    pub config: GameConfig,
    pub generation: u64,
    pub active_search: Option<SearchTicket>,
    pub thinking: bool,
    pub auto_play: bool,
    pub outcome: Option<GameOutcome>,
    pub status_message: Option<String>,
    pub engine_info: Option<SearchMetrics>,
}

impl GameSession {
    #[must_use]
    pub fn human_to_move(&self) -> bool {
        let Some(human_color) = self.config.human_color() else {
            return false;
        };
        self.outcome.is_none()
            && !self.thinking
            && self.game.position().side_to_move() == human_color
    }

    #[must_use]
    pub fn is_active(&self) -> bool {
        self.outcome.is_none()
    }

    fn clear_search(&mut self) {
        self.active_search = None;
        self.thinking = false;
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum AppError {
    InvalidState(String),
    Input(String),
    Rules(String),
}

impl fmt::Display for AppError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidState(message) | Self::Input(message) | Self::Rules(message) => {
                formatter.write_str(message)
            }
        }
    }
}

impl std::error::Error for AppError {}

#[derive(Default)]
pub struct GameController {
    pub session: Option<GameSession>,
    pending_search: Option<SearchRequest>,
    next_generation: u64,
    next_request: u64,
}

impl GameController {
    #[must_use]
    pub fn new() -> Self {
        Self {
            session: None,
            pending_search: None,
            next_generation: 1,
            next_request: 1,
        }
    }

    pub fn start_game(&mut self, config: GameConfig) -> Result<(), AppError> {
        validate_config(config)?;
        let generation = self.next_generation;
        self.next_generation = self.next_generation.saturating_add(1);
        self.pending_search = None;
        self.session = Some(GameSession {
            game: Game::starting(),
            config,
            generation,
            active_search: None,
            thinking: false,
            auto_play: config.is_self_play(),
            outcome: None,
            status_message: None,
            engine_info: None,
        });
        self.refresh_terminal_state()?;
        self.schedule_if_needed()
    }

    pub fn restart_current_game(&mut self) -> Result<(), AppError> {
        let config = self
            .session
            .as_ref()
            .map(|session| session.config)
            .ok_or_else(|| AppError::InvalidState("no active game to restart".to_owned()))?;
        self.start_game(config)
    }

    pub fn abandon_game(&mut self) {
        self.pending_search = None;
        self.session = None;
    }

    pub fn submit_human_move(&mut self, input: &str) -> Result<(), AppError> {
        let parsed = input
            .parse::<UciMove>()
            .map_err(|error| AppError::Input(error.to_string()))?;

        let session = self
            .session
            .as_mut()
            .ok_or_else(|| AppError::InvalidState("no active game".to_owned()))?;
        if session.outcome.is_some() {
            return visible_error(session, "the game is already over");
        }
        let Some(human_color) = session.config.human_color() else {
            return visible_error(session, "human move input is disabled during self-play");
        };
        if session.thinking {
            return visible_error(session, "engine search is still active");
        }
        if session.game.position().side_to_move() != human_color {
            return visible_error(session, "it is not the human side's turn");
        }

        let legal_moves = session
            .game
            .legal_moves()
            .map_err(|error| AppError::Rules(error.to_string()))?;
        let mut matches = legal_moves
            .iter()
            .filter(|candidate| parsed.matches(*candidate));
        let Some(current) = matches.next() else {
            return visible_error(session, "move is not legal in the current position");
        };
        if matches.next().is_some() {
            return visible_error(session, "move syntax resolved to more than one legal move");
        }

        session
            .game
            .make_move(current)
            .map_err(|error| AppError::Rules(error.to_string()))?;
        session.status_message = Some(format!("Played {}", current.to_uci()));
        self.refresh_terminal_state()?;
        self.schedule_if_needed()
    }

    pub fn resign_human(&mut self) -> Result<(), AppError> {
        let human_color = {
            let session = self
                .session
                .as_mut()
                .ok_or_else(|| AppError::InvalidState("no active game".to_owned()))?;
            if session.outcome.is_some() {
                return visible_error(session, "the game is already over");
            }
            let Some(human_color) = session.config.human_color() else {
                return visible_error(
                    session,
                    "resignation is only available in Human vs Engine mode",
                );
            };
            human_color
        };
        self.cancel_search_state(None);
        let Some(session) = self.session.as_mut() else {
            return Err(AppError::InvalidState(
                "game disappeared during resignation".to_owned(),
            ));
        };
        session.outcome = Some(GameOutcome::Resignation {
            winner: human_color.opposite(),
        });
        session.status_message = Some("Human resigned".to_owned());
        Ok(())
    }

    pub fn pause_self_play(&mut self) -> Result<(), AppError> {
        {
            let session = self
                .session
                .as_mut()
                .ok_or_else(|| AppError::InvalidState("no active game".to_owned()))?;
            if !session.config.is_self_play() {
                return visible_error(session, "pause is only available during self-play");
            }
        }
        self.cancel_search_state(None);
        let Some(session) = self.session.as_mut() else {
            return Err(AppError::InvalidState(
                "game disappeared while pausing self-play".to_owned(),
            ));
        };
        session.auto_play = false;
        session.status_message = Some("Self-play paused".to_owned());
        Ok(())
    }

    pub fn resume_self_play(&mut self) -> Result<(), AppError> {
        let session = self
            .session
            .as_mut()
            .ok_or_else(|| AppError::InvalidState("no active game".to_owned()))?;
        if !session.config.is_self_play() {
            return visible_error(session, "resume is only available during self-play");
        }
        if session.outcome.is_some() {
            return visible_error(session, "cannot resume a completed game");
        }
        session.auto_play = true;
        session.status_message = Some("Self-play running".to_owned());
        self.schedule_if_needed()
    }

    pub fn step_self_play(&mut self) -> Result<(), AppError> {
        let session = self
            .session
            .as_ref()
            .ok_or_else(|| AppError::InvalidState("no active game".to_owned()))?;
        if !session.config.is_self_play() {
            return Err(AppError::InvalidState(
                "step is only available during self-play".to_owned(),
            ));
        }
        if session.auto_play {
            return Err(AppError::InvalidState(
                "pause self-play before requesting a single step".to_owned(),
            ));
        }
        if session.thinking || self.pending_search.is_some() {
            return Err(AppError::InvalidState(
                "a search is already active".to_owned(),
            ));
        }
        if session.outcome.is_some() {
            return Err(AppError::InvalidState(
                "cannot step a completed game".to_owned(),
            ));
        }
        self.schedule_search()
    }

    pub fn cancel_search_state(&mut self, message: Option<String>) {
        self.pending_search = None;
        if let Some(session) = self.session.as_mut() {
            session.clear_search();
            if let Some(message) = message {
                session.status_message = Some(message);
            }
        }
    }

    #[must_use]
    pub fn has_pending_search(&self) -> bool {
        self.pending_search.is_some()
    }

    #[must_use]
    pub fn take_pending_search(&mut self) -> Option<SearchRequest> {
        self.pending_search.take()
    }

    pub fn handle_engine_event(&mut self, event: EngineEvent) -> Result<(), AppError> {
        let ticket = event.ticket();
        let Some(session) = self.session.as_ref() else {
            return Ok(());
        };
        if session.active_search != Some(ticket) {
            return Ok(());
        }

        match event {
            EngineEvent::Progress { metrics, .. } => {
                if let Some(session) = self.session.as_mut() {
                    session.engine_info = Some(metrics);
                }
                Ok(())
            }
            EngineEvent::Completed {
                best_move, metrics, ..
            } => {
                let session = self.session.as_mut().ok_or_else(|| {
                    AppError::InvalidState("active search lost its game session".to_owned())
                })?;
                session.clear_search();
                session.engine_info = Some(metrics);

                let legal_moves = session
                    .game
                    .legal_moves()
                    .map_err(|error| AppError::Rules(error.to_string()))?;
                if !legal_moves.iter().any(|candidate| candidate == best_move) {
                    return visible_error(
                        session,
                        "engine returned a move that is no longer legal",
                    );
                }
                session
                    .game
                    .make_move(best_move)
                    .map_err(|error| AppError::Rules(error.to_string()))?;
                session.status_message = Some(format!("Engine played {}", best_move.to_uci()));
                self.refresh_terminal_state()?;
                self.schedule_if_needed()
            }
            EngineEvent::Cancelled { .. } => {
                if let Some(session) = self.session.as_mut() {
                    session.clear_search();
                    session.status_message = Some("Search cancelled".to_owned());
                }
                Ok(())
            }
            EngineEvent::Failed { message, .. } => {
                if let Some(session) = self.session.as_mut() {
                    session.clear_search();
                    session.status_message = Some(format!("Search failed: {message}"));
                }
                Ok(())
            }
        }
    }

    pub fn refresh_terminal_state(&mut self) -> Result<(), AppError> {
        let Some(session) = self.session.as_mut() else {
            return Ok(());
        };
        let status = session
            .game
            .status()
            .map_err(|error| AppError::Rules(error.to_string()))?;
        session.outcome = match status {
            GameStatus::Checkmate { winner } => Some(GameOutcome::Checkmate { winner }),
            GameStatus::Stalemate => Some(GameOutcome::Stalemate),
            GameStatus::AutomaticDraw(reason) => Some(GameOutcome::Draw(reason)),
            GameStatus::Ongoing | GameStatus::ClaimableDraw(_) => None,
        };
        if session.outcome.is_some() {
            session.clear_search();
            session.auto_play = false;
            self.pending_search = None;
        }
        Ok(())
    }

    fn schedule_if_needed(&mut self) -> Result<(), AppError> {
        let Some(session) = self.session.as_ref() else {
            return Ok(());
        };
        if session.outcome.is_some() || session.thinking || self.pending_search.is_some() {
            return Ok(());
        }
        let side = session.game.position().side_to_move();
        let should_search = match session.config {
            GameConfig::HumanVsEngine { human_color, .. } => side != human_color,
            GameConfig::SelfPlay { .. } => session.auto_play,
        };
        if should_search {
            self.schedule_search()?;
        }
        Ok(())
    }

    fn schedule_search(&mut self) -> Result<(), AppError> {
        if self.pending_search.is_some() {
            return Err(AppError::InvalidState(
                "a pending search already exists".to_owned(),
            ));
        }
        let (generation, depth, game) = {
            let session = self
                .session
                .as_ref()
                .ok_or_else(|| AppError::InvalidState("no game to search".to_owned()))?;
            if session.outcome.is_some() {
                return Err(AppError::InvalidState(
                    "cannot search a completed game".to_owned(),
                ));
            }
            let side = session.game.position().side_to_move();
            (
                session.generation,
                session.config.depth_for_side(side),
                session.game.clone(),
            )
        };
        let ticket = SearchTicket {
            generation,
            request: self.next_request,
        };
        self.next_request = self.next_request.saturating_add(1);
        let request = SearchRequest {
            ticket,
            game,
            depth,
        };
        let session = self
            .session
            .as_mut()
            .ok_or_else(|| AppError::InvalidState("game disappeared before search".to_owned()))?;
        session.active_search = Some(ticket);
        session.thinking = true;
        session.engine_info = None;
        session.status_message = Some(format!("Engine thinking at depth {depth}"));
        self.pending_search = Some(request);
        Ok(())
    }
}

fn validate_config(config: GameConfig) -> Result<(), AppError> {
    let depths = match config {
        GameConfig::HumanVsEngine { engine_depth, .. } => [engine_depth, engine_depth],
        GameConfig::SelfPlay {
            white_depth,
            black_depth,
        } => [white_depth, black_depth],
    };
    if depths
        .iter()
        .any(|depth| !(MIN_SEARCH_DEPTH..=MAX_SEARCH_DEPTH).contains(depth))
    {
        return Err(AppError::InvalidState(format!(
            "search depth must be between {MIN_SEARCH_DEPTH} and {MAX_SEARCH_DEPTH}"
        )));
    }
    Ok(())
}

fn visible_error<T>(session: &mut GameSession, message: &str) -> Result<T, AppError> {
    session.status_message = Some(message.to_owned());
    Err(AppError::Input(message.to_owned()))
}

#[cfg(test)]
mod tests {
    use chess_core::{Color, Game, Position, UciMove};

    use super::{GameConfig, GameController, GameOutcome, MAX_SEARCH_DEPTH, MIN_SEARCH_DEPTH};
    use crate::worker::{EngineEvent, SearchMetrics, SearchTicket};

    fn legal_move(game: &mut Game, uci: &str) -> chess_core::Move {
        let syntax = uci.parse::<UciMove>().expect("fixture UCI parses");
        game.legal_moves()
            .expect("legal moves")
            .iter()
            .find(|candidate| syntax.matches(*candidate))
            .expect("fixture move is legal")
    }

    #[test]
    fn configuration_validation_is_fail_before_mutation() {
        let mut controller = GameController::new();
        controller
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::White,
                engine_depth: MIN_SEARCH_DEPTH,
            })
            .expect("valid game starts");
        let before = controller.session.as_ref().expect("session").game.clone();
        assert!(controller
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::Black,
                engine_depth: MAX_SEARCH_DEPTH + 1,
            })
            .is_err());
        assert_eq!(controller.session.as_ref().expect("session").game, before);
    }

    #[test]
    fn human_white_waits_human_black_searches_and_selfplay_searches() {
        let mut white = GameController::new();
        white
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::White,
                engine_depth: 1,
            })
            .expect("white starts");
        assert!(white.session.as_ref().expect("session").human_to_move());
        assert!(white.take_pending_search().is_none());

        let mut black = GameController::new();
        black
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::Black,
                engine_depth: 1,
            })
            .expect("black starts");
        assert!(black.take_pending_search().is_some());

        let mut selfplay = GameController::new();
        selfplay
            .start_game(GameConfig::SelfPlay {
                white_depth: 1,
                black_depth: 1,
            })
            .expect("selfplay starts");
        assert!(selfplay.take_pending_search().is_some());
    }

    #[test]
    fn rejected_and_legal_human_moves_are_transactional() {
        let mut controller = GameController::new();
        controller
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::White,
                engine_depth: 1,
            })
            .expect("game starts");
        let before = controller.session.as_ref().expect("session").game.clone();
        assert!(controller.submit_human_move("bad").is_err());
        assert_eq!(controller.session.as_ref().expect("session").game, before);
        assert!(controller.submit_human_move("e2e5").is_err());
        assert_eq!(controller.session.as_ref().expect("session").game, before);
        controller.submit_human_move("e2e4").expect("legal move");
        assert_eq!(
            controller
                .session
                .as_ref()
                .expect("session")
                .game
                .ply_count(),
            1
        );
        assert!(controller.take_pending_search().is_some());
    }

    #[test]
    fn promotion_identity_is_preserved() {
        let mut controller = GameController::new();
        controller
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::White,
                engine_depth: 1,
            })
            .expect("game starts");
        controller.session.as_mut().expect("session").game =
            Game::new(Position::from_fen("7k/4P3/8/8/8/8/8/7K w - - 0 1").expect("fixture"));
        controller.submit_human_move("e7e8q").expect("promotion");
        assert_eq!(
            controller.session.as_ref().expect("session").game.moves()[0].to_uci(),
            "e7e8q"
        );
    }

    #[test]
    fn stale_completion_is_ignored_and_current_illegal_completion_fails_closed() {
        let mut controller = GameController::new();
        controller
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::Black,
                engine_depth: 1,
            })
            .expect("game starts");
        let request = controller.take_pending_search().expect("request");
        let before = controller.session.as_ref().expect("session").game.clone();
        let mut opening = Game::starting();
        let e2e4 = legal_move(&mut opening, "e2e4");
        controller
            .handle_engine_event(EngineEvent::Completed {
                ticket: SearchTicket {
                    generation: request.ticket.generation + 1,
                    request: request.ticket.request,
                },
                best_move: e2e4,
                metrics: SearchMetrics::default(),
            })
            .expect("stale ignored");
        assert_eq!(controller.session.as_ref().expect("session").game, before);
        assert_eq!(
            controller.session.as_ref().expect("session").active_search,
            Some(request.ticket)
        );

        opening.make_move(e2e4).expect("white move");
        let e7e5 = legal_move(&mut opening, "e7e5");
        assert!(controller
            .handle_engine_event(EngineEvent::Completed {
                ticket: request.ticket,
                best_move: e7e5,
                metrics: SearchMetrics::default(),
            })
            .is_err());
        assert_eq!(controller.session.as_ref().expect("session").game, before);
        assert!(!controller.session.as_ref().expect("session").thinking);
    }

    #[test]
    fn failure_and_cancel_clear_search_without_moving() {
        for failed in [true, false] {
            let mut controller = GameController::new();
            controller
                .start_game(GameConfig::HumanVsEngine {
                    human_color: Color::Black,
                    engine_depth: 1,
                })
                .expect("game starts");
            let request = controller.take_pending_search().expect("request");
            let before = controller.session.as_ref().expect("session").game.clone();
            let event = if failed {
                EngineEvent::Failed {
                    ticket: request.ticket,
                    message: "synthetic".to_owned(),
                }
            } else {
                EngineEvent::Cancelled {
                    ticket: request.ticket,
                }
            };
            controller.handle_engine_event(event).expect("handled");
            let session = controller.session.as_ref().expect("session");
            assert_eq!(session.game, before);
            assert!(!session.thinking);
            assert_eq!(session.active_search, None);
        }
    }

    #[test]
    fn selfplay_pause_step_resume_and_terminal_state_are_explicit() {
        let mut controller = GameController::new();
        controller
            .start_game(GameConfig::SelfPlay {
                white_depth: 1,
                black_depth: 1,
            })
            .expect("selfplay starts");
        controller.pause_self_play().expect("pause");
        assert!(!controller.session.as_ref().expect("session").auto_play);
        controller.step_self_play().expect("step schedules");
        assert!(controller.take_pending_search().is_some());
        controller.cancel_search_state(None);
        controller.resume_self_play().expect("resume");
        assert!(controller.take_pending_search().is_some());

        controller.cancel_search_state(None);
        controller.session.as_mut().expect("session").game =
            Game::new(Position::from_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1").expect("stalemate"));
        controller.refresh_terminal_state().expect("refresh");
        assert_eq!(
            controller.session.as_ref().expect("session").outcome,
            Some(GameOutcome::Stalemate)
        );
        assert!(!controller.has_pending_search());
    }

    #[test]
    fn resignation_declares_the_opponent_for_both_colors() {
        for human_color in [Color::White, Color::Black] {
            let mut controller = GameController::new();
            controller
                .start_game(GameConfig::HumanVsEngine {
                    human_color,
                    engine_depth: 1,
                })
                .expect("game starts");
            controller.resign_human().expect("resign");
            assert_eq!(
                controller.session.as_ref().expect("session").outcome,
                Some(GameOutcome::Resignation {
                    winner: human_color.opposite(),
                })
            );
        }
    }
}
