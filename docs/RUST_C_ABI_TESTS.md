# C ABI lifecycle and fault-containment tests

Task 18.3 validates the stable Task 18.2 boundary through a dedicated Rust-through-ABI integration harness. The harness imports only the public `chess_ffi::c_abi` surface and calls the same `extern "C"` functions declared in `crates/chess-ffi/include/chess_engine.h`. It does not reach into the safe facade, registries, rule engine, or search implementation.

The primary test file is `crates/chess-ffi/tests/c_abi_lifecycle.rs`.

## Complete lifecycle smoke path

The smoke path performs the consumer-visible sequence:

1. initialize configuration and create an opaque engine;
2. set a strict six-field position through explicit-length UTF-8;
3. retrieve and free legal moves;
4. apply a legal UCI move;
5. retrieve game status;
6. run a fixed-depth search;
7. verify the returned best move belongs to the legal move set;
8. free all search-result buffers;
9. reset the position; and
10. destroy the engine.

Only ABI records, numeric tokens, explicit byte ranges, and ABI-owned buffers are used.

## Repeated lifecycle and stale tokens

The harness creates and destroys 128 engines and 128 cancellation handles. It verifies that every issued token is nonzero and unique within the run. Operations using destroyed tokens must return `CHESS_ENGINE_RESULT_INVALID_HANDLE`; a second destroy must also fail visibly rather than becoming an implicit no-op.

This exercises registry insertion, removal, type tagging, and stale-token rejection without retaining all engine allocations concurrently.

## Invalid input and transactional state

The invalid-input test covers:

- null input with a nonzero explicit length;
- invalid UTF-8;
- malformed FEN;
- malformed UCI move syntax;
- syntactically valid but illegal moves;
- unknown search flag bits;
- incompatible versioned record sizes; and
- null output pointers.

Each path checks its structured result code. Selected paths also retrieve the thread-local error buffer and verify a useful diagnostic. The engine's canonical FEN must remain unchanged across the complete invalid-input sequence.

## Active cross-thread cancellation

The cancellation test starts an infinite synchronous ABI search on a worker thread. A rendezvous channel confirms that the worker has reached the search call boundary before the controlling thread waits briefly and requests cancellation through the independent opaque cancellation token.

The controller then destroys its external cancellation token. The in-flight search must still complete because it retained its resolved internal reference. Completion is bounded by a five-second receive deadline and must report `CHESS_ENGINE_TERMINATION_EXPLICIT_STOP`, a legal best move, and successful search-result cleanup.

## Buffer ownership

The lifecycle test verifies both individual buffers and compound search results:

- a modified pointer/length/token tuple is rejected;
- failed validation does not release the original allocation;
- the unchanged original record remains readable and frees successfully;
- a stale copy is rejected after the allocation is released;
- empty records are safe to free repeatedly; and
- compound result validation is all-or-nothing before any of its three buffers are released.

The tests never reconstruct a Rust allocator layout and never free ABI memory with the process allocator.

## Injected panic

The non-default Cargo feature `ffi-test-faults` compiles one extra symbol:

```text
chess_engine_test_inject_panic
```

The canonical header declares it only when the C consumer defines `CHESS_ENGINE_ENABLE_TEST_FAULTS`. The function deliberately panics inside the same shared `catch_unwind` boundary used by production exports. The harness requires `CHESS_ENGINE_RESULT_PANIC`, retrieves the contained-panic diagnostic, and then creates and uses another engine to prove the process remains usable.

The symbol is absent from default production builds. It is enabled by the permanent all-features validation gate solely for testing.

## Commands

Focused Task 18.3 validation:

```text
cargo test --locked -p chess-ffi --all-features --test c_abi_lifecycle
```

Complete package validation:

```text
cargo test --locked -p chess-ffi --all-features
```

The permanent workspace gate additionally runs rustfmt, locked all-target/all-feature compilation, strict Clippy, complete workspace tests, authoritative release perft, rustdoc with warnings denied, debug and release builds, and the independent differential oracle.

Task 18.4 will wrap the stable ABI from JNI. Task 18.5 owns Android/JVM lifecycle and main-thread exclusion tests.


## Completion evidence

Implementation SHA: `0789ac65590ccafb55b2b86b73873edfba1c7b55`.

Tracker-closure SHA: `d3aab284b461e5afbd3fb38a8634bb04a443f9db`.

Permanent validation:

- PR: `#233`;
- workflow run: `30841137129`;
- job: `91778174797`;
- all six Task 18.3 lifecycle tests passed;
- 297 executed non-doc Rust tests passed across the workspace;
- formatting, committed lockfile, locked all-target/all-feature compilation, strict Clippy with warnings denied and no lint suppression, authoritative release depth-four perft, rustdoc with warnings denied, and debug/release workspace builds passed;
- differential validation passed over 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.

The first validation found only canonical rustfmt differences. The correction also removed a scheduler-sensitive assertion that was not part of the ABI contract; the rendezvous, cross-thread cancel, bounded completion, typed termination, legal result, and cleanup checks remain. No ABI behavior, default production symbol surface, safety policy, lower-layer code, or validation gate was weakened.

Task 18.3 is complete. Task 18.4 owns the Android JNI adapter and AArch64 library integration.
