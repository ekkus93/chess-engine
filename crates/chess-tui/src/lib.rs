#![forbid(unsafe_code)]
//! Native Ratatui frontend for the authoritative Rust chess engine.
//!
//! This crate owns terminal presentation and TUI-only interaction state.
//! Presentation-neutral game/session lifecycle, search-worker orchestration,
//! metrics, and shared text/save primitives live in `chess-app`. Chess rules
//! remain in `chess-core`; search and evaluation remain in `chess-search`.

pub mod app;
pub mod render;
pub mod save;
pub mod ui;
pub mod worker;
