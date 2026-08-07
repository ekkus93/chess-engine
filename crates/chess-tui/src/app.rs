use core::fmt;

use chess_core::{Color, DrawReason, Game, GameStatus, UciMove};

use crate::worker::{EngineEvent, SearchMetrics, SearchRequest, SearchTicket};

pub const DEFAULT_SEARCH_DEPTH: u16 = 3;
pub const MIN_SEARCH_DEPTH: u16 = 1;
pub const MAX_MENU_SEARCH_DEPTH: u16 = 12;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MenuMode {
    HumanVsEngine,
    SelfPlay,
}

impl MenuMode {
    #[must_use]
    pub const fn toggled(self) -> Self {
        match self {
            Self::HumanVsEngine => Self::SelfPlay,
            Self::SelfPlay => Self::HumanVsEngine,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct MenuState {
    pub mode: MenuMode,
    pub human_color: Color,
    pub engine_depth: u16,
    pub white_depth: u16,
    pub black_depth: u16,
    pub selected_row: usize,
}

impl Default for MenuState {
    fn default() -> Self {
        Self {
            mode: MenuMode::HumanVsEngine,
            human_color: Color::White,
            engine_depth: DEFAULT_SEARCH_DEPTH,
            white_depth: DEFAULT_SEARCH_DEPTH,
            black_depth: DEFAULT_SEARCH_DEPTH,
            selected_row: 0,
        }
    }
}

impl MenuState {
    pub const ROW_COUNT: usize = 4;

    pub fn select_previous(&mut self) {
        self.selected_row = self.selected_row.saturating_sub(1);
    }

    pub fn select_next(&mut self) {
        self.selected_row = (self.selected_row + 1).min(Self::ROW_COUNT - 1);
    }

    pub fn adjust_selected(&mut self, increase: bool) {
        match (self.mode, self.selected_row) {
            (_, 0) => self.mode = self.mode.toggled(),
            (MenuMode::HumanVsEngine, 1) => self.human_color = self.human_color.opposite(),
            (MenuMode::HumanVsEngine, 2) => {
                adjust_depth(&mut self.engine_depth, increase);
            }
            (MenuMode::SelfPlay, 1) => adjust_depth(&mut self.white_depth, increase),
            (MenuMode::SelfPlay, 2) => adjust_depth(&mut self.black_depth, increase),
            _ => {}
        }
    }

    #[must_use]
    pub const fn config(self) -> GameConfig {
        match self.mode {
            MenuMode::HumanVsEngine => GameConfig::HumanVsEngine {
                human_color: self.human_color,
                engine_depth: self.engine_depth,
            },
            MenuMode::SelfPlay => GameConfig::SelfPlay {
                white_depth: self.white_depth,
                black_depth: self.black_depth,
            },
        }
    }
}

fn adjust_depth(depth: &mut u16, increase: bool) {
    if increase {
        *depth = depth.saturating_add(1).min(MAX_MENU_SEARCH_DEPTH);
    } else {
        *depth = depth.saturating_sub(1).max(MIN_SEARCH_DEPTH);
    }
}

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
pub enum AppScreen {
    MainMenu,
    Game,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ConfirmationAction {
    Resign,
    NewGame,
    MainMenu,
    Quit,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Overlay {
    Confirmation(ConfirmationAction),
    SavePath { input: String },
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
    pub move_input: String,
    pub engine_info: Option<SearchMetrics>,
    pub saved_path: Option<String>,
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

pub struct AppState {
    pub screen: AppScreen,
    pub menu: MenuState,
    pub session: Option<GameSession>,
    pub overlay: Option<Overlay>,
    pub should_quit: bool,
    pending_search: Option<SearchRequest>,
    next_generation: u64,
    next_request: u64,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            screen: AppScreen::MainMenu,
            menu: MenuState::default(),
            session: None,
            overlay: None,
            should_quit: false,
            pending_search: None,
            next_generation: 1,
            next_request: 1,
        }
    }
}

impl AppState {
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    pub fn start_from_menu(&mut self) -> Result<(), AppError> {
        self.start_game(self.menu.config())
    }

    pub fn start_game(&mut self, config: GameConfig) -> Result<(), AppError> {
        validate_config(config)?;
        let generation = self.next_generation;
        self.next_generation = self.next_generation.saturating_add(1);
        self.screen = AppScreen::Game;
        self.overlay = None;
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
            move_input: String::new(),
            engine_info: None,
            saved_path: None,
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

    pub fn return_to_menu(&mut self) {
        self.pending_search = None;
        self.session = None;
        self.overlay = None;
        self.screen = AppScreen::MainMenu;
    }

    pub fn request_quit(&mut self) {
        self.pending_search = None;
        self.should_quit = true;
        self.overlay = None;
    }

    pub fn open_confirmation(&mut self, action: ConfirmationAction) {
        self.overlay = Some(Overlay::Confirmation(action));
    }

    pub fn open_save_path(&mut self) {
        self.overlay = Some(Overlay::SavePath {
            input: "game.txt".to_owned(),
        });
    }

    pub fn dismiss_overlay(&mut self) {
        self.overlay = None;
    }

    pub fn save_input_mut(&mut self) -> Option<&mut String> {
        match self.overlay.as_mut() {
            Some(Overlay::SavePath { input }) => Some(input),
            _ => None,
        }
    }

    #[must_use]
    pub fn save_input(&self) -> Option<&str> {
        match self.overlay.as_ref() {
            Some(Overlay::SavePath { input }) => Some(input.as_str()),
            _ => None,
        }
    }

    pub fn mark_saved(&mut self, path: String) -> Result<(), AppError> {
        let session = self
            .session
            .as_mut()
            .ok_or_else(|| AppError::InvalidState("no game exists to mark saved".to_owned()))?;
        session.saved_path = Some(path.clone());
        session.status_message = Some(format!("Saved to {path}"));
        self.overlay = None;
        Ok(())
    }

    pub fn mark_save_failed(&mut self, message: String) {
        if let Some(session) = self.session.as_mut() {
            session.saved_path = None;
            session.status_message = Some(message);
        }
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
        session.move_input.clear();
        session.status_message = Some(format!("Played {}", current.to_uci()));
        session.saved_path = None;
        self.refresh_terminal_state()?;
        self.schedule_if_needed()
    }

    pub fn resign_human(&mut self) -> Result<(), AppError> {
        self.pending_search = None;
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
        session.active_search = None;
        session.thinking = false;
        session.outcome = Some(GameOutcome::Resignation {
            winner: human_color.opposite(),
        });
        session.status_message = Some("Human resigned".to_owned());
        self.overlay = None;
        Ok(())
    }

    pub fn pause_self_play(&mut self) -> Result<(), AppError> {
        self.pending_search = None;
        let session = self
            .session
            .as_mut()
            .ok_or_else(|| AppError::InvalidState("no active game".to_owned()))?;
        if !session.config.is_self_play() {
            return visible_error(session, "pause is only available during self-play");
        }
        session.auto_play = false;
        session.active_search = None;
        session.thinking = false;
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
            session.active_search = None;
            session.thinking = false;
            if let Some(message) = message {
                session.status_message = Some(message);
            }
        }
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
                session.active_search = None;
                session.thinking = false;
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
                session.saved_path = None;
                self.refresh_terminal_state()?;
                self.schedule_if_needed()
            }
            EngineEvent::Cancelled { .. } => {
                if let Some(session) = self.session.as_mut() {
                    session.active_search = None;
                    session.thinking = false;
                    session.status_message = Some("Search cancelled".to_owned());
                }
                Ok(())
            }
            EngineEvent::Failed { message, .. } => {
                if let Some(session) = self.session.as_mut() {
                    session.active_search = None;
                    session.thinking = false;
                    session.status_message = Some(format!("Search failed: {message}"));
                }
                Ok(())
            }
        }
    }

    fn refresh_terminal_state(&mut self) -> Result<(), AppError> {
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
            session.active_search = None;
            session.thinking = false;
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
        .any(|depth| !(MIN_SEARCH_DEPTH..=MAX_MENU_SEARCH_DEPTH).contains(depth))
    {
        return Err(AppError::InvalidState(format!(
            "search depth must be between {MIN_SEARCH_DEPTH} and {MAX_MENU_SEARCH_DEPTH}"
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
    use chess_core::{Color, Game, Position};

    use super::{AppState, GameConfig, GameOutcome, MenuMode, DEFAULT_SEARCH_DEPTH};
    use crate::worker::{EngineEvent, SearchMetrics, SearchTicket};

    #[test]
    fn default_menu_matches_reference_defaults() {
        let app = AppState::new();
        assert_eq!(app.menu.mode, MenuMode::HumanVsEngine);
        assert_eq!(app.menu.human_color, Color::White);
        assert_eq!(app.menu.engine_depth, DEFAULT_SEARCH_DEPTH);
    }

    #[test]
    fn human_white_waits_and_human_black_searches_first() {
        let mut white = AppState::new();
        white
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::White,
                engine_depth: 1,
            })
            .expect("white game starts");
        assert!(white.session.as_ref().expect("session").human_to_move());
        assert!(white.take_pending_search().is_none());

        let mut black = AppState::new();
        black
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::Black,
                engine_depth: 1,
            })
            .expect("black game starts");
        assert!(black.take_pending_search().is_some());
        assert!(black.session.as_ref().expect("session").thinking);
    }

    #[test]
    fn self_play_starts_white_search_and_pause_clears_scheduling() {
        let mut app = AppState::new();
        app.start_game(GameConfig::SelfPlay {
            white_depth: 1,
            black_depth: 1,
        })
        .expect("self-play starts");
        assert!(app.take_pending_search().is_some());
        app.pause_self_play().expect("pause works");
        assert!(!app.session.as_ref().expect("session").auto_play);
        assert!(!app.session.as_ref().expect("session").thinking);
    }

    #[test]
    fn new_game_uses_a_new_generation() {
        let mut app = AppState::new();
        app.start_game(GameConfig::HumanVsEngine {
            human_color: Color::White,
            engine_depth: 1,
        })
        .expect("game starts");
        let first = app.session.as_ref().expect("session").generation;
        app.restart_current_game().expect("restart works");
        let second = app.session.as_ref().expect("session").generation;
        assert_ne!(first, second);
    }

    #[test]
    fn legal_and_illegal_human_input_is_transactional() {
        let mut app = AppState::new();
        app.start_game(GameConfig::HumanVsEngine {
            human_color: Color::White,
            engine_depth: 1,
        })
        .expect("game starts");
        let before = app.session.as_ref().expect("session").game.clone();
        assert!(app.submit_human_move("bad").is_err());
        assert_eq!(app.session.as_ref().expect("session").game, before);
        assert!(app.submit_human_move("e2e5").is_err());
        assert_eq!(app.session.as_ref().expect("session").game, before);
        app.submit_human_move("e2e4").expect("e2e4 is legal");
        assert_eq!(app.session.as_ref().expect("session").game.ply_count(), 1);
        assert!(app.take_pending_search().is_some());
    }

    #[test]
    fn promotion_identity_is_preserved_by_core_resolution() {
        let position =
            Position::from_fen("7k/4P3/8/8/8/8/8/7K w - - 0 1").expect("promotion fixture parses");
        let mut app = AppState::new();
        app.start_game(GameConfig::HumanVsEngine {
            human_color: Color::White,
            engine_depth: 1,
        })
        .expect("game starts");
        let generation = app.session.as_ref().expect("session").generation;
        app.session.as_mut().expect("session").game = Game::new(position);
        app.submit_human_move("e7e8q").expect("promotion is legal");
        assert_eq!(
            app.session.as_ref().expect("session").game.moves()[0].to_uci(),
            "e7e8q"
        );
        assert_eq!(
            app.session.as_ref().expect("session").generation,
            generation
        );
    }

    #[test]
    fn stale_completion_is_ignored_without_mutation() {
        let mut app = AppState::new();
        app.start_game(GameConfig::HumanVsEngine {
            human_color: Color::Black,
            engine_depth: 1,
        })
        .expect("game starts");
        let request = app.take_pending_search().expect("search requested");
        let before = app.session.as_ref().expect("session").game.clone();
        let legal = app
            .session
            .as_mut()
            .expect("session")
            .game
            .legal_moves()
            .expect("legal moves")
            .get(0)
            .expect("opening move");
        app.handle_engine_event(EngineEvent::Completed {
            ticket: SearchTicket {
                generation: request.ticket.generation + 1,
                request: request.ticket.request,
            },
            best_move: legal,
            metrics: SearchMetrics::default(),
        })
        .expect("stale event is harmless");
        assert_eq!(app.session.as_ref().expect("session").game, before);
        assert_eq!(
            app.session.as_ref().expect("session").active_search,
            Some(request.ticket)
        );
    }

    #[test]
    fn resignation_declares_opponent_winner() {
        let mut app = AppState::new();
        app.start_game(GameConfig::HumanVsEngine {
            human_color: Color::Black,
            engine_depth: 1,
        })
        .expect("game starts");
        app.resign_human().expect("resignation works");
        assert_eq!(
            app.session.as_ref().expect("session").outcome,
            Some(GameOutcome::Resignation {
                winner: Color::White
            })
        );
    }
}
