# Safe Rust Engine Facade

Task 18.1 provides the process-independent Rust API that later C and JNI adapters wrap. The implementation lives in `chess-ffi` because the specified workspace dependency graph places that crate directly above `chess-search` and below `chess-jni`.

## Public types

- `EngineConfig` selects the fixed transposition-table budget explicitly.
- `Engine` owns one history-aware `chess_core::Game` and one bounded `chess_search::TranspositionTable`.
- `SearchRequest` exposes depth, node, soft-time, hard-time, infinite, explicit-cancellation, and bounded check-extension configuration without exposing mutable search internals.
- `SearchCancellationHandle` is a cloneable atomic stop signal for one synchronous request.
- `EvaluationWeightIdentity` reports the exact schema, identifier, and checksum of the evaluator used by production search.
- `EngineError` preserves FEN, move, rules, search, allocation, and weight-validation failures as typed errors.

## Position and game contract

`Engine::new` creates the standard starting position and performs the complete fixed transposition-table allocation up front. Zero, overflowing, or rejected allocations fail construction rather than falling back to unbounded or smaller storage.

`set_position` parses a strict playable six-field FEN before changing any engine state. On failure, the current game, history, FEN, and transposition table remain unchanged. Successful replacement creates one fresh root and clears table entries while retaining the bounded allocation. `reset_position` applies the same replacement policy for the standard starting position.

`fen` returns canonical six-field FEN. `legal_moves` returns deterministic canonical UCI coordinate strings. `play_move` resolves parsed UCI syntax only against generated legal moves and leaves state unchanged for malformed or illegal input. Automatic terminal positions reject further moves explicitly. `game_status` exposes the authoritative core rule status.

## Search contract

`Engine::search` is synchronous. It clones the current position and detached repetition history into a search root, then searches with the engine-owned bounded transposition table. Search success, cancellation, and errors cannot mutate the played game, canonical FEN, move history, or rule status.

Finite requests may combine depth, nodes, time budgets, and an explicit cancellation handle. Infinite requests require a cancellation handle. Invalid limit combinations fail before search state is entered.

A cancellation handle may be cloned before moving the engine to a worker thread. Calling `cancel` from another thread requests an orderly stop at the established bounded search checkpoints. Handles are not reset implicitly; callers normally create one per request or call `reset` explicitly before reuse.

## Version and evaluator identity

`ENGINE_VERSION` and `Engine::version` report the Cargo package version. `Engine::weight_identity` reports the validated built-in baseline evaluation set using its schema version, stable identifier, and canonical checksum.

Task 18.1 does not claim support for caller-supplied evaluation weights because the current production search path uses the built-in baseline evaluator. A later feature must wire custom weights through the complete search before extending `EngineConfig`.

## Ownership and thread safety

An `Engine` borrows no caller memory, opens no files, uses no process-global mutable state, and starts no threads. Stateful operations require `&mut self`; concurrent mutation therefore requires synchronization chosen by the caller. The engine may be moved to another thread through its compiler-derived `Send` implementation. No manual `Send` or `Sync` implementation exists.

`SearchCancellationHandle` is compiler-derived `Send + Sync` because its clones share only the search crate's atomic stop flag. The safe facade module forbids unsafe code. Task 18.2 may add narrowly scoped unsafe operations only in the separate C-boundary implementation.

## Test coverage

The public integration suite covers:

- configuration, construction, engine version, and exact baseline weight identity;
- typed invalid transposition-table configuration;
- canonical FEN replacement, failed replacement transactionality, and reset;
- deterministic legal UCI move output;
- malformed and illegal move rejection without mutation;
- explicit terminal-game rejection;
- legal fixed-depth search output and played-state immutability;
- invalid limit rejection without mutation;
- deterministic fallback under preset cancellation;
- infinite search cancelled through a handle on another thread;
- compile-time `Engine: Send` and `SearchCancellationHandle: Send + Sync` assertions.

Completion evidence will be recorded after the exact implementation tree passes the permanent full-workspace CI gate.
