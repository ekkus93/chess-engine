# Rust UCI Protocol Loop

## Scope

Task 17.1 implements the Linux stdin/stdout Universal Chess Interface boundary. It owns command parsing, session state, supported option values, transactional position replacement, legal move replay, and typed search requests.

This task does not execute search. Task 17.2 owns the adapter worker thread and stop token, Task 17.3 owns clock-to-budget conversion, and Task 17.4 owns periodic `info` and final `bestmove` output.

## Process entry point

`crates/chess-uci/src/main.rs` calls `chess_uci::run_stdio`. The reusable `run_protocol_loop` function accepts arbitrary `BufRead` and `Write` values so protocol behavior can be tested without redirecting process-global stdin or stdout.

Every emitted line is newline-terminated and output is flushed after each command. `quit` flushes pending output and exits cleanly. End-of-file also returns normally.

## Session ownership

`UciSession` owns:

- one `chess_core::Game`, including exact replay and repetition history;
- one `EngineOptions` value;
- no process-global mutable state;
- no search worker or shared cancellation state.

A `go` command produces an immutable `SearchRequest` snapshot containing a cloned game, parsed limits, and the current supported options. Later commands cannot mutate an already-created request.

## Supported commands

### `uci`

The adapter emits engine identity, supported options, and `uciok`:

- `Hash`, a spin option measured in MiB;
- `CheckExtension`, a boolean option controlling the bounded Task 16.7 extension.

### `isready`

The adapter emits `readyok` immediately. Task 17.2 will preserve this responsiveness while search runs on a separate worker.

### `ucinewgame`

The active game is replaced with a fresh standard starting game. Move history, repetition history, and all position state are discarded atomically. Supported option values remain configured.

### `setoption`

Only advertised options are accepted:

- `setoption name Hash value N`, where `N` is between 1 and 65,536 MiB;
- `setoption name CheckExtension value true|false`.

Malformed values and unsupported names produce an `info string error:` line and do not change the prior option state.

### `position startpos`

The session builds a new standard starting game and optionally replays the moves following `moves`.

### `position fen`

The parser consumes exactly six FEN fields, builds a strict playable `Position`, and optionally replays the moves following `moves`.

Position commands are transactional. Parsing and replay occur against a temporary `Game`; the active session game is replaced only after the complete command succeeds. Invalid FEN, malformed UCI syntax, illegal moves, and moves after an automatic terminal state leave the active game unchanged.

### `go`

The parser produces a typed `GoCommand` supporting:

- `depth`;
- `nodes`;
- `movetime`;
- `wtime` and `btime`;
- `winc` and `binc`;
- `movestogo`;
- `infinite`.

Duplicate parameters, zero values for positive-only limits, unsupported parameters, `infinite` combined with automatic limits, and `movetime` combined with clock fields fail loudly. A bare `go` is represented as infinite search requiring a later explicit stop.

Task 17.1 deliberately reports that the search worker is pending rather than running search on the protocol thread. Task 17.2 will consume `StartSearch` events.

### `stop`

The parser emits a `StopSearch` event. It is harmless when no search exists. Task 17.2 will bind the event to an adapter-owned stop token and worker join policy.

### `quit`

The parser emits a `Quit` event. The process loop flushes and returns without reading later input.

### Unknown commands

Unknown top-level commands are ignored, as required for forward-compatible UCI adapters. Recognized commands with malformed arguments fail visibly through `info string error:` output.

## Validation

Task 17.1 adds 18 deterministic unit tests covering:

- handshake identity and option advertisement;
- immediate readiness;
- valid and invalid supported options;
- starting-position and six-field FEN setup;
- legal replay and transactional illegal-replay rejection;
- new-game reset semantics;
- every required `go` form and invalid combination handling;
- immutable request snapshots;
- distinct stop and quit events;
- ignored unknown commands;
- buffered protocol flushing and clean quit behavior.

The implementation passes workspace formatting, locked all-target compilation, strict Clippy with warnings denied, the focused `chess-uci` test suite, and the complete workspace test suite.
