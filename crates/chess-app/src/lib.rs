#![forbid(unsafe_code)]
//! Shared application/session support for human-facing Rust chess frontends.
//!
//! `chess-app` owns presentation-neutral interactive game lifecycle, search
//! worker orchestration primitives, text formatting, and atomic save I/O.
//! Chess rules remain in `chess-core`; search/evaluation remain in
//! `chess-search`. UCI remains an independent external protocol adapter.

pub mod controller;
pub mod save;
pub mod text;
pub mod worker;

pub use controller::{
    AppError, GameConfig, GameController, GameOutcome, GameSession, DEFAULT_SEARCH_DEPTH,
    MAX_SEARCH_DEPTH, MIN_SEARCH_DEPTH,
};
pub use worker::{
    EngineEvent, SearchMetrics, SearchRequest, SearchTicket, SearchWorker, SearchWorkerError,
};
