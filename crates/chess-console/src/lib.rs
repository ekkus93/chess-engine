#![forbid(unsafe_code)]
//! Human-facing scrolling console frontend support.
//!
//! This crate owns ordinary line-oriented stdin/stdout interaction only.
//! Shared game/session lifecycle and search worker behavior live in
//! `chess-app`; chess rules/search remain in `chess-core`/`chess-search`.

pub mod command;
pub mod input;
pub mod menu;
pub mod runtime;
pub mod save;

pub use runtime::{run_console, ExitReason};
