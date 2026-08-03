# Stable C ABI

Task 18.2 places a narrow C boundary around the completed safe Rust facade in `chess-ffi`. The canonical declarations are in `crates/chess-ffi/include/chess_engine.h`; the Rust implementation is isolated under `crates/chess-ffi/src/c_abi`.

## Versioning and library products

`chess-ffi` builds as an `rlib`, `cdylib`, and `staticlib`. The current ABI version is `1`, returned by `chess_engine_abi_version` and embedded in every versioned input/output record.

Callers should initialize records with the matching initialization function, preserve `struct_size` and `abi_version`, and reject a library whose ABI version is not supported. Versioned records are accepted only when both fields match exactly. This prevents a smaller or differently laid-out record from being interpreted as the current structure.

## Opaque handles

Engine and cancellation handles are opaque nonzero 64-bit tokens. They are not pointers and must never be dereferenced or synthesized by callers.

The adapter stores live objects in synchronized registries and tags token types. Every operation rejects:

- zero handles;
- unknown or destroyed handles;
- an engine token supplied to a cancellation operation;
- a cancellation token supplied to an engine operation.

Registry lookup clones an internal reference before releasing the registry lock. Destroy therefore invalidates future calls immediately while an already-running call may finish safely. The engine instance itself is mutex-serialized because the safe facade requires exclusive mutable access. Cancellation remains request-local and uses its independent atomic stop signal.

## Input strings

FEN and move text are passed as `(const uint8_t *data, size_t len)` pairs. The ABI never calls `strlen`, never scans beyond the provided length, and does not require NUL termination.

A null pointer is accepted only with length zero. Nonempty input must be valid UTF-8. FEN and move validation is delegated to the canonical safe Rust facade, so malformed or illegal input remains transactional.

## Structured result codes and errors

Every fallible exported function returns `ChessEngineResultCode`. Codes distinguish null pointers, invalid handles, invalid UTF-8, ABI mismatches, FEN and move errors, game-over and rule failures, search failures, allocation failures, invalid buffers, internal failures, and contained panics.

The calling thread's most recent error text is retrieved with `chess_engine_last_error_message`. Error storage is thread-local, so independent C threads do not overwrite each other's diagnostics. Successful ordinary calls clear the calling thread's prior error. Retrieving the error itself does not clear it.

## Output-buffer ownership

Text output uses `ChessEngineBuffer`:

- `data` points to immutable bytes;
- `len` is the exact readable byte count;
- `allocation` is an opaque registry token.

The buffer is owned by the ABI registry, not by the C allocator and not by a Rust `Vec` layout exposed to C. A nonempty record must be passed unchanged to `chess_engine_buffer_free` exactly once. The free operation verifies the allocation token, pointer, and length before releasing storage, then resets the caller's record to empty. Stale copies, fabricated records, and already-freed allocations are rejected.

Legal moves are returned as canonical UCI moves separated by newline bytes without a trailing newline. FEN, version, error text, best move, ponder move, and principal variation are UTF-8 and are not NUL terminated.

`ChessEngineSearchResult` owns three independent buffers. Pass the unchanged record to `chess_engine_search_result_free`; it validates all three allocations before freeing any of them and then resets the result.

## Search and cancellation

`ChessEngineSearchRequest` uses explicit presence flags for depth, nodes, soft time, hard time, infinite mode, bounded check extension, and cancellation. Values without their corresponding flag, unknown flags, nonzero reserved fields, and invalid record versions are rejected before search.

Search is synchronous. The caller normally runs it on a worker thread. Another thread may call `chess_engine_cancellation_cancel` using the request's cancellation token. The result reports:

- best move and optional ponder move;
- space-separated legal principal variation;
- no score, centipawn score, or signed full moves to mate;
- completed depth and selective depth;
- nodes and quiescence nodes;
- elapsed milliseconds;
- typed termination category and associated value;
- deterministic pre-depth-one fallback category.

The played game remains unchanged by search because the safe facade searches detached position and history snapshots.

## Game status and weight identity

`ChessEngineGameStatus` uses stable numeric categories for ongoing play, checkmate, stalemate, automatic draw, and claimable draw. Winner and draw reason are separate fields.

`ChessEngineWeightIdentity` reports the schema version, stable identifier, and checksum of the validated built-in evaluator used by production search. The ABI does not claim caller-supplied weight support.

## Panic containment and unsafe scope

Every exported function enters `catch_unwind` before performing Rust work. A contained panic becomes `CHESS_ENGINE_RESULT_PANIC`, stores a thread-local diagnostic, and never unwinds into C.

Unsafe operations are confined to the C-boundary implementation and consist of reading or writing caller-provided records and creating explicit-length byte slices. The safe facade, rules crate, and search crate continue to forbid unsafe code. Valid non-null C pointers must designate readable or writable storage as documented; arbitrary invalid memory addresses are outside the C language contract.

## Build artifacts

From the workspace root:

```text
cargo build --locked -p chess-ffi --release
```

On Linux this produces the shared and static library forms under `target/release`, together with the normal Rust library artifact. Consumers compile against `crates/chess-ffi/include/chess_engine.h` and must use the matching library build.

Task 18.3 adds the native C/Rust-through-ABI lifecycle, active cancellation, buffer, and injected-panic smoke harness. Task 18.4 will wrap this ABI from JNI without exposing Rust layouts to Kotlin.
