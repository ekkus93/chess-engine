#![forbid(unsafe_code)]
//! Standalone Universal Chess Interface process adapter.
//!
//! Protocol parsing, process I/O, and session ownership live in `chess_uci`;
//! reusable rules and search behavior stay in lower-level crates.

fn main() -> std::io::Result<()> {
    chess_uci::run_stdio()
}
