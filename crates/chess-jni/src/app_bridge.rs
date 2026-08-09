use std::{
    collections::HashMap,
    sync::{
        atomic::{AtomicU64, Ordering},
        mpsc::{Receiver, TryRecvError},
        Arc, Mutex, OnceLock,
    },
};

use chess_app::{
    text::{format_duration, format_outcome, format_score},
    EngineEvent, GameConfig, GameController, SearchTicket, SearchWorker,
};
use chess_core::Color;
use chess_ffi::c_abi::ChessEngineResultCode;
use jni::sys::{jint, jlong};

use crate::bridge::{token_from_jlong, token_to_jlong, BridgeError, BridgeResult};

const SNAPSHOT_SEPARATOR: char = '\u{001f}';
const SNAPSHOT_VERSION: &str = "1";
const SNAPSHOT_END: &str = "END";
const WHITE_CODE: jint = 1;
const BLACK_CODE: jint = 2;
const MIN_ANDROID_DEPTH: u16 = 1;
const MAX_ANDROID_DEPTH: u16 = 12;

static NEXT_HANDLE: AtomicU64 = AtomicU64::new(1);
static REGISTRY: OnceLock<Mutex<HashMap<u64, Arc<Mutex<AppGame>>>>> = OnceLock::new();

struct ActiveSearch {
    ticket: SearchTicket,
    worker: SearchWorker,
    receiver: Receiver<EngineEvent>,
}

struct AppGame {
    controller: GameController,
    active: Option<ActiveSearch>,
}

impl AppGame {
    fn new(human_color: Color, depth: u16) -> BridgeResult<Self> {
        let mut controller = GameController::new();
        controller
            .start_game(GameConfig::HumanVsEngine {
                human_color,
                engine_depth: depth,
            })
            .map_err(app_error)?;
        let mut game = Self {
            controller,
            active: None,
        };
        game.spawn_pending()?;
        Ok(game)
    }

    fn submit_move(&mut self, move_text: &str) -> BridgeResult<()> {
        self.poll()?;
        self.controller
            .submit_human_move(move_text)
            .map_err(app_error)?;
        self.spawn_pending()
    }

    fn restart(&mut self) -> BridgeResult<()> {
        self.cancel_active(None)?;
        self.controller.restart_current_game().map_err(app_error)?;
        self.spawn_pending()
    }

    fn resign(&mut self) -> BridgeResult<()> {
        self.cancel_active(None)?;
        self.controller.resign_human().map_err(app_error)
    }

    fn close(&mut self) -> BridgeResult<()> {
        self.cancel_active(Some("Android game closed".to_owned()))?;
        self.controller.abandon_game();
        Ok(())
    }

    fn poll(&mut self) -> BridgeResult<()> {
        loop {
            let event = match self.active.as_ref() {
                Some(active) => match active.receiver.try_recv() {
                    Ok(event) => Some(Ok(event)),
                    Err(TryRecvError::Empty) => None,
                    Err(TryRecvError::Disconnected) => Some(Err(active.ticket)),
                },
                None => None,
            };
            let Some(event) = event else {
                break;
            };

            match event {
                Ok(EngineEvent::Progress { ticket, metrics }) => {
                    self.controller
                        .handle_engine_event(EngineEvent::Progress { ticket, metrics })
                        .map_err(app_error)?;
                }
                Ok(final_event) => {
                    let final_ticket = final_event.ticket();
                    let Some(mut active) = self.active.take() else {
                        return Err(internal_error(
                            "final search event arrived without an active Android worker",
                        ));
                    };
                    if active.ticket != final_ticket {
                        self.controller.cancel_search_state(Some(
                            "Search failed: worker ticket did not match final event".to_owned(),
                        ));
                        active.worker.cancel_and_join().map_err(worker_error)?;
                        return Err(internal_error(
                            "active Android worker ticket did not match final event",
                        ));
                    }
                    if let Err(error) = active.worker.join() {
                        self.controller
                            .handle_engine_event(EngineEvent::Failed {
                                ticket: final_ticket,
                                message: error.to_string(),
                            })
                            .map_err(app_error)?;
                        continue;
                    }
                    self.controller
                        .handle_engine_event(final_event)
                        .map_err(app_error)?;
                }
                Err(ticket) => {
                    let Some(mut active) = self.active.take() else {
                        return Err(internal_error(
                            "search channel disconnected without an active Android worker",
                        ));
                    };
                    let message = match active.worker.join() {
                        Ok(()) => "interactive search event channel closed before a final event"
                            .to_owned(),
                        Err(error) => error.to_string(),
                    };
                    self.controller
                        .handle_engine_event(EngineEvent::Failed { ticket, message })
                        .map_err(app_error)?;
                }
            }
        }
        self.spawn_pending()
    }

    fn spawn_pending(&mut self) -> BridgeResult<()> {
        if self.active.is_some() {
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
                Ok(())
            }
            Err(error) => {
                self.controller
                    .handle_engine_event(EngineEvent::Failed {
                        ticket,
                        message: error.to_string(),
                    })
                    .map_err(app_error)?;
                Err(worker_error(error))
            }
        }
    }

    fn cancel_active(&mut self, message: Option<String>) -> BridgeResult<()> {
        let result = match self.active.take() {
            Some(mut active) => active.worker.cancel_and_join().map_err(worker_error),
            None => Ok(()),
        };
        self.controller.cancel_search_state(message);
        result
    }

    fn snapshot(&mut self) -> BridgeResult<String> {
        let session = self
            .controller
            .session
            .as_mut()
            .ok_or_else(|| BridgeError::Abi {
                code: ChessEngineResultCode::GameError,
                message: "Android game session is not active".to_owned(),
            })?;
        let legal_moves = session
            .game
            .legal_moves()
            .map_err(|error| BridgeError::Abi {
                code: ChessEngineResultCode::GameError,
                message: error.to_string(),
            })?
            .iter()
            .map(|current| current.to_uci())
            .collect::<Vec<_>>()
            .join(" ");
        let moves = session
            .game
            .moves()
            .iter()
            .map(|current| current.to_uci())
            .collect::<Vec<_>>()
            .join(" ");
        let human_color = match session.config.human_color() {
            Some(Color::White) => "white",
            Some(Color::Black) => "black",
            None => "none",
        };
        let side_to_move = match session.game.position().side_to_move() {
            Color::White => "white",
            Color::Black => "black",
        };
        let outcome = session.outcome.map(format_outcome).unwrap_or_default();
        let status = session.status_message.as_deref().unwrap_or_default();
        let metrics = session.engine_info.as_ref();
        let depth = metrics
            .and_then(|value| value.depth)
            .map_or_else(String::new, |value| value.to_string());
        let score = metrics
            .and_then(|value| value.score)
            .map_or_else(String::new, format_score);
        let nodes = metrics
            .and_then(|value| value.nodes)
            .map_or_else(String::new, |value| value.to_string());
        let nps = metrics
            .and_then(|value| value.nps)
            .map_or_else(String::new, |value| value.to_string());
        let elapsed = metrics
            .and_then(|value| value.elapsed)
            .map_or_else(String::new, format_duration);
        let pv = metrics.map_or_else(String::new, |value| {
            value
                .principal_variation
                .iter()
                .map(|current| current.to_uci())
                .collect::<Vec<_>>()
                .join(" ")
        });
        let hash = metrics
            .and_then(|value| value.hash_full_per_mille)
            .map_or_else(String::new, |value| value.to_string());
        let fields = [
            SNAPSHOT_VERSION.to_owned(),
            session.game.position().to_fen(),
            legal_moves,
            moves,
            human_color.to_owned(),
            side_to_move.to_owned(),
            if session.thinking { "1" } else { "0" }.to_owned(),
            sanitize_field(&outcome),
            sanitize_field(status),
            depth,
            score,
            nodes,
            nps,
            elapsed,
            pv,
            hash,
            SNAPSHOT_END.to_owned(),
        ];
        Ok(fields.join(&SNAPSHOT_SEPARATOR.to_string()))
    }
}

impl Drop for AppGame {
    fn drop(&mut self) {
        if self.active.is_some() {
            let _cleanup_result = self.cancel_active(Some("Android game dropped".to_owned()));
        }
    }
}

fn registry() -> &'static Mutex<HashMap<u64, Arc<Mutex<AppGame>>>> {
    REGISTRY.get_or_init(|| Mutex::new(HashMap::new()))
}

pub(crate) fn create_game(human_color: jint, depth: jint) -> BridgeResult<jlong> {
    let color = parse_color(human_color)?;
    let depth =
        u16::try_from(depth).map_err(|_| invalid_argument("search depth is out of range"))?;
    if !(MIN_ANDROID_DEPTH..=MAX_ANDROID_DEPTH).contains(&depth) {
        return Err(invalid_argument("search depth must be between 1 and 12"));
    }
    let game = AppGame::new(color, depth)?;
    let token = NEXT_HANDLE.fetch_add(1, Ordering::Relaxed);
    if token == 0 {
        return Err(internal_error("Android game handle counter exhausted"));
    }
    let mut entries = registry()
        .lock()
        .map_err(|_| internal_error("Android game registry lock was poisoned"))?;
    if entries.insert(token, Arc::new(Mutex::new(game))).is_some() {
        return Err(internal_error("Android game handle collision"));
    }
    Ok(token_to_jlong(token))
}

pub(crate) fn destroy_game(handle: jlong) -> BridgeResult<()> {
    let token = token_from_jlong(handle);
    let game = registry()
        .lock()
        .map_err(|_| internal_error("Android game registry lock was poisoned"))?
        .get(&token)
        .cloned()
        .ok_or_else(|| invalid_handle(token))?;

    {
        let mut game_guard = game
            .lock()
            .map_err(|_| internal_error("Android game lock was poisoned"))?;
        game_guard.close()?;
    }

    let mut entries = registry()
        .lock()
        .map_err(|_| internal_error("Android game registry lock was poisoned"))?;
    let current = entries.get(&token).ok_or_else(|| invalid_handle(token))?;
    if !Arc::ptr_eq(current, &game) {
        return Err(internal_error(
            "Android game registry handle changed during close",
        ));
    }
    entries.remove(&token);
    Ok(())
}

pub(crate) fn snapshot(handle: jlong) -> BridgeResult<String> {
    with_game(handle, |game| game.snapshot())
}

pub(crate) fn poll(handle: jlong) -> BridgeResult<String> {
    with_game(handle, |game| {
        game.poll()?;
        game.snapshot()
    })
}

pub(crate) fn submit_move(handle: jlong, move_text: &str) -> BridgeResult<String> {
    with_game(handle, |game| {
        game.submit_move(move_text)?;
        game.snapshot()
    })
}

pub(crate) fn restart(handle: jlong) -> BridgeResult<String> {
    with_game(handle, |game| {
        game.restart()?;
        game.snapshot()
    })
}

pub(crate) fn resign(handle: jlong) -> BridgeResult<String> {
    with_game(handle, |game| {
        game.resign()?;
        game.snapshot()
    })
}

fn with_game<T>(
    handle: jlong,
    operation: impl FnOnce(&mut AppGame) -> BridgeResult<T>,
) -> BridgeResult<T> {
    let token = token_from_jlong(handle);
    let game = registry()
        .lock()
        .map_err(|_| internal_error("Android game registry lock was poisoned"))?
        .get(&token)
        .cloned()
        .ok_or_else(|| invalid_handle(token))?;
    let mut game = game
        .lock()
        .map_err(|_| internal_error("Android game lock was poisoned"))?;
    operation(&mut game)
}

fn parse_color(value: jint) -> BridgeResult<Color> {
    match value {
        WHITE_CODE => Ok(Color::White),
        BLACK_CODE => Ok(Color::Black),
        _ => Err(invalid_argument(
            "human color must be 1 for White or 2 for Black",
        )),
    }
}

fn sanitize_field(value: &str) -> String {
    value
        .chars()
        .map(|current| {
            if matches!(current, '\r' | '\n' | SNAPSHOT_SEPARATOR) {
                ' '
            } else {
                current
            }
        })
        .collect()
}

fn app_error(error: chess_app::AppError) -> BridgeError {
    BridgeError::Abi {
        code: ChessEngineResultCode::GameError,
        message: error.to_string(),
    }
}

fn worker_error(error: chess_app::SearchWorkerError) -> BridgeError {
    BridgeError::Abi {
        code: ChessEngineResultCode::SearchError,
        message: error.to_string(),
    }
}

fn invalid_argument(message: &str) -> BridgeError {
    BridgeError::Abi {
        code: ChessEngineResultCode::InvalidArgument,
        message: message.to_owned(),
    }
}

fn invalid_handle(token: u64) -> BridgeError {
    BridgeError::Abi {
        code: ChessEngineResultCode::InvalidHandle,
        message: format!("unknown or closed Android game handle: {token}"),
    }
}

fn internal_error(message: &str) -> BridgeError {
    BridgeError::Abi {
        code: ChessEngineResultCode::InternalError,
        message: message.to_owned(),
    }
}

#[cfg(test)]
mod tests {
    use std::{thread, time::Duration};

    use chess_core::Color;

    use super::{AppGame, SNAPSHOT_END, SNAPSHOT_SEPARATOR};

    #[test]
    fn snapshot_protocol_is_complete_and_versioned() {
        let mut game = AppGame::new(Color::White, 1).expect("game starts");
        let snapshot = game.snapshot().expect("snapshot");
        let fields: Vec<_> = snapshot.split(SNAPSHOT_SEPARATOR).collect();
        assert_eq!(fields.len(), 17);
        assert_eq!(fields[0], "1");
        assert_eq!(fields[4], "white");
        assert_eq!(fields[5], "white");
        assert_eq!(fields[6], "0");
        assert_eq!(fields[16], SNAPSHOT_END);
        game.close().expect("game closes");
    }

    #[test]
    fn human_move_and_exact_engine_reply_are_driven_by_shared_controller() {
        let mut game = AppGame::new(Color::White, 1).expect("game starts");
        game.submit_move("e2e4").expect("human move applies");
        assert!(game.controller.session.as_ref().expect("session").thinking);
        for _ in 0..500 {
            game.poll().expect("poll succeeds");
            let session = game.controller.session.as_ref().expect("session");
            if !session.thinking {
                assert_eq!(session.game.moves().len(), 2);
                game.close().expect("game closes");
                return;
            }
            thread::sleep(Duration::from_millis(2));
        }
        panic!("engine did not produce an exact depth-one reply");
    }

    #[test]
    fn black_game_starts_with_engine_search_and_close_resolves_worker() {
        let mut game = AppGame::new(Color::Black, 1).expect("game starts");
        assert!(game.controller.session.as_ref().expect("session").thinking);
        assert!(game.active.is_some());
        game.close().expect("game closes");
        assert!(game.active.is_none());
        assert!(game.controller.session.is_none());
    }
}
