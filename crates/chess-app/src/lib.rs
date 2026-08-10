#![forbid(unsafe_code)]
//! Shared application/session support for human-facing Rust chess frontends.
//!
//! `chess-app` owns presentation-neutral interactive game lifecycle, search
//! worker orchestration primitives, text formatting, and atomic save I/O.
//! Chess rules remain in `chess-core`; search/evaluation remain in
//! `chess-search`. UCI remains an independent external protocol adapter.

mod book;
pub mod controller;
pub mod save;
#[path = "worker.rs"]
mod search_worker;
pub mod text;
#[path = "interactive_worker.rs"]
pub mod worker;

pub use controller::{
    AppError, GameConfig, GameController, GameOutcome, GameSession, DEFAULT_SEARCH_DEPTH,
    MAX_SEARCH_DEPTH, MIN_SEARCH_DEPTH,
};
pub use worker::{
    EngineEvent, SearchMetrics, SearchRequest, SearchTicket, SearchWorker, SearchWorkerError,
};
