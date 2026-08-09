use core::ops::{Deref, DerefMut};

use chess_core::Color;

pub use chess_app::{
    AppError, GameConfig, GameController, GameOutcome, GameSession, DEFAULT_SEARCH_DEPTH,
    MIN_SEARCH_DEPTH,
};

use crate::worker::{EngineEvent, SearchRequest};

pub const MAX_MENU_SEARCH_DEPTH: u16 = chess_app::MAX_SEARCH_DEPTH;

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
            (MenuMode::HumanVsEngine, 2) => adjust_depth(&mut self.engine_depth, increase),
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
    OverwriteSave,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Overlay {
    Confirmation(ConfirmationAction),
    SavePath { input: String },
}

/// Ratatui-owned presentation state wrapped around the shared `GameController`.
///
/// The custom `Deref` preserves the historical `app.session` field-access
/// surface for the TUI and its regression tests without duplicating the shared
/// game/search lifecycle state machine.
pub struct AppState {
    controller: GameController,
    pub screen: AppScreen,
    pub menu: MenuState,
    pub overlay: Option<Overlay>,
    pub should_quit: bool,
    pub move_input: String,
    pub saved_path: Option<String>,
    /// TUI-runtime handoff slot. `GameController` creates requests; the wrapper
    /// drains each request into this existing slot until `EngineRuntime` owns it.
    pending_search: Option<SearchRequest>,
    pending_overwrite_path: Option<String>,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            controller: GameController::new(),
            screen: AppScreen::MainMenu,
            menu: MenuState::default(),
            overlay: None,
            should_quit: false,
            move_input: String::new(),
            saved_path: None,
            pending_search: None,
            pending_overwrite_path: None,
        }
    }
}

impl Deref for AppState {
    type Target = GameController;

    fn deref(&self) -> &Self::Target {
        &self.controller
    }
}

impl DerefMut for AppState {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.controller
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
        // The shared controller validates before mutation. Do not mutate TUI
        // state until that operation has succeeded either.
        self.controller.start_game(config)?;
        self.screen = AppScreen::Game;
        self.overlay = None;
        self.pending_search = None;
        self.pending_overwrite_path = None;
        self.move_input.clear();
        self.saved_path = None;
        self.sync_pending_search()
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
        self.controller.abandon_game();
        self.pending_search = None;
        self.pending_overwrite_path = None;
        self.overlay = None;
        self.move_input.clear();
        self.saved_path = None;
        self.screen = AppScreen::MainMenu;
    }

    pub fn request_quit(&mut self) {
        self.pending_search = None;
        self.controller.cancel_search_state(None);
        self.should_quit = true;
        self.overlay = None;
        self.pending_overwrite_path = None;
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
        self.pending_overwrite_path = None;
    }

    pub fn request_overwrite_confirmation(&mut self, path: String) {
        self.pending_overwrite_path = Some(path);
        self.overlay = Some(Overlay::Confirmation(ConfirmationAction::OverwriteSave));
    }

    #[must_use]
    pub fn pending_overwrite_path(&self) -> Option<&str> {
        self.pending_overwrite_path.as_deref()
    }

    #[must_use]
    pub fn take_pending_overwrite_path(&mut self) -> Option<String> {
        self.pending_overwrite_path.take()
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
        self.saved_path = Some(path.clone());
        session.status_message = Some(format!("Saved to {path}"));
        self.overlay = None;
        Ok(())
    }

    pub fn mark_save_failed(&mut self, message: String) {
        self.saved_path = None;
        if let Some(session) = self.session.as_mut() {
            session.status_message = Some(message);
        }
    }

    pub fn submit_human_move(&mut self, input: &str) -> Result<(), AppError> {
        self.controller.submit_human_move(input)?;
        self.move_input.clear();
        self.saved_path = None;
        self.sync_pending_search()
    }

    pub fn resign_human(&mut self) -> Result<(), AppError> {
        self.pending_search = None;
        self.controller.resign_human()?;
        self.overlay = None;
        Ok(())
    }

    pub fn pause_self_play(&mut self) -> Result<(), AppError> {
        self.controller.pause_self_play()?;
        self.pending_search = None;
        Ok(())
    }

    pub fn resume_self_play(&mut self) -> Result<(), AppError> {
        self.controller.resume_self_play()?;
        self.sync_pending_search()
    }

    pub fn step_self_play(&mut self) -> Result<(), AppError> {
        self.controller.step_self_play()?;
        self.sync_pending_search()
    }

    pub fn cancel_search_state(&mut self, message: Option<String>) {
        self.pending_search = None;
        self.controller.cancel_search_state(message);
    }

    #[must_use]
    pub fn take_pending_search(&mut self) -> Option<SearchRequest> {
        self.pending_search.take()
    }

    pub fn handle_engine_event(&mut self, event: EngineEvent) -> Result<(), AppError> {
        let ply_before = self
            .session
            .as_ref()
            .map_or(0, |session| session.game.ply_count());
        self.controller.handle_engine_event(event)?;
        let ply_after = self
            .session
            .as_ref()
            .map_or(0, |session| session.game.ply_count());
        if ply_after != ply_before {
            self.saved_path = None;
        }
        self.sync_pending_search()
    }

    fn refresh_terminal_state(&mut self) -> Result<(), AppError> {
        self.controller.refresh_terminal_state()?;
        if self
            .session
            .as_ref()
            .is_some_and(|session| session.outcome.is_some())
        {
            self.pending_search = None;
        }
        self.sync_pending_search()
    }

    fn sync_pending_search(&mut self) -> Result<(), AppError> {
        let shared = self.controller.take_pending_search();
        match (self.pending_search.is_some(), shared) {
            (false, Some(request)) => self.pending_search = Some(request),
            (true, Some(_)) => {
                return Err(AppError::InvalidState(
                    "TUI already owns a pending search while shared controller scheduled another"
                        .to_owned(),
                ));
            }
            (_, None) => {}
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use chess_core::Color;

    use super::{AppScreen, AppState, GameConfig, MenuMode, DEFAULT_SEARCH_DEPTH};

    #[test]
    fn default_menu_matches_reference_defaults() {
        let app = AppState::new();
        assert_eq!(app.menu.mode, MenuMode::HumanVsEngine);
        assert_eq!(app.menu.human_color, Color::White);
        assert_eq!(app.menu.engine_depth, DEFAULT_SEARCH_DEPTH);
        assert_eq!(app.screen, AppScreen::MainMenu);
    }

    #[test]
    fn wrapper_preserves_human_white_and_black_search_handoff() {
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
    }

    #[test]
    fn successful_human_move_clears_tui_only_input_and_save_state() {
        let mut app = AppState::new();
        app.start_game(GameConfig::HumanVsEngine {
            human_color: Color::White,
            engine_depth: 1,
        })
        .expect("game starts");
        app.move_input = "e2e4".to_owned();
        app.saved_path = Some("old.txt".to_owned());
        app.submit_human_move("e2e4").expect("move applies");
        assert!(app.move_input.is_empty());
        assert!(app.saved_path.is_none());
        assert!(app.take_pending_search().is_some());
    }

    #[test]
    fn invalid_replacement_game_does_not_mutate_existing_tui_state() {
        let mut app = AppState::new();
        app.start_game(GameConfig::HumanVsEngine {
            human_color: Color::White,
            engine_depth: 1,
        })
        .expect("game starts");
        app.move_input = "e2".to_owned();
        let before_generation = app.session.as_ref().expect("session").generation;
        assert!(app
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::Black,
                engine_depth: 0,
            })
            .is_err());
        assert_eq!(app.move_input, "e2");
        assert_eq!(
            app.session.as_ref().expect("session").generation,
            before_generation
        );
    }
}

#[cfg(test)]
mod hardening_tests;
