#![forbid(unsafe_code)]
//! Native terminal frontend for the authoritative Rust chess engine.
//!
//! This crate owns presentation and application-session state only. Chess rules
//! remain in `chess-core`; search, evaluation, limits, and cancellation remain
//! in `chess-search`.

pub mod app;
pub mod render;
pub mod save;
pub mod ui;
pub mod worker;
