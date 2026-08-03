# Rust UCI Process Integration

Task 17.5 validates the Linux UCI executable as a real child process rather than through in-process parser calls or global stdout redirection.

## Harness

`crates/chess-uci/tests/uci_process.rs` starts the Cargo-built `chess-uci` binary with piped stdin and stdout. A dedicated reader thread converts complete stdout lines into a channel, while every read and process exit has a finite deadline. Test cleanup closes stdin, terminates a stuck child, waits for it, and joins the reader thread.

The harness uses only standard-library process and synchronization APIs. It does not replace process-global stdout, install global search state, or share mutable protocol state between sessions.

## Covered workflows

The subprocess suite covers:

- the exact `uci` identity/options/`uciok` transcript and immediate `readyok`;
- clean `quit` from an idle session;
- `position startpos` with replayed moves;
- strict six-field `position fen` setup;
- fixed-depth searches whose returned move is checked against `chess-core` legal moves;
- fail-visible illegal replay input followed by a search proving the previous position remained active;
- checkmate and stalemate roots returning `bestmove 0000`;
- `go infinite` followed by `stop`, one legal final move, and a still-responsive session;
- `quit` during active search with bounded exit and no stale final move;
- two concurrent engine processes with distinct positions and independently captured stdout.

## Boundaries

These tests exercise the shipped executable and its real stdin/stdout worker interaction. Search correctness, time allocation, output formatting internals, and worker lifecycle remain covered by their focused unit tests; this suite validates that those components compose correctly at the process boundary.

## Completion evidence

Implementation SHA: `67b6c97a476e1323bc2bd96ecf14870fc2ed3139`.

Permanent implementation validation:

- PR: `#230`;
- workflow run: `30828959858`;
- job: `91737751003`;
- seven subprocess integration tests passed in `0.05s`;
- formatting, locked all-target/all-feature workspace compilation, strict Clippy with warnings denied, the complete workspace test suite, authoritative release depth-four perft, rustdoc with warnings denied, debug and release builds, and the independent differential corpus with seeded playouts all passed;
- differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.

Task 17.5 and the overall Task 17 Linux UCI executable gate are complete. Task 18.1 Rust facade work is next.
