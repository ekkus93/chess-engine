# Rust UCI Search Output

Task 17.4 turns exact completed search work into serialized Universal Chess Interface output without moving protocol concerns into `chess-search`.

## Architecture

`chess-search` exposes a protocol-neutral `SearchProgress` snapshot and an observer-enabled iterative-deepening entry point. The observer runs synchronously on the search thread after one exact depth completes and after cumulative node counters are updated. It receives no writer, UCI command, or mutable search control.

`chess-uci` owns one `SharedUciOutput` protected by a mutex. The protocol thread and the adapter-owned search worker share that boundary, so every line is written and flushed atomically even while the protocol thread is blocked waiting for the next command.

The worker measures wall-clock time from request start for progress reporting. Search limits and termination continue to use the authoritative Task 16 search clock.

## Iteration information

After each exact completed depth, the worker emits one line containing:

```text
info depth <depth> seldepth <seldepth> score <cp|mate> nodes <nodes> nps <nps> time <ms> hashfull <permille> pv <moves...>
```

Fields have these meanings:

- `depth`: deepest exact completed iteration;
- `seldepth`: deepest root-relative ply entered through that iteration;
- `score cp`: exact side-to-move score outside the reserved mate band;
- `score mate`: signed full-move distance derived from the engine's signed ply-distance encoding;
- `nodes`: cumulative production nodes entered through the completed depth;
- `nps`: overflow-safe `nodes * 1000 / max(time_ms, 1)`;
- `time`: request wall-clock milliseconds, saturated to `u64::MAX` only if the platform duration exceeds that domain;
- `hashfull`: bounded current-generation transposition occupancy in per mille;
- `pv`: safely reconstructed legal principal variation in root-to-leaf UCI move notation.

The `pv` token is omitted only when the exact completed iteration has no move sequence.

## Final move

Natural completion and explicit `stop` emit exactly one final line:

```text
bestmove <move>
bestmove <move> ponder <reply>
bestmove 0000
```

The optional ponder move is the second legal move in the deepest completed PV. A terminal root, or another result with no legal move, uses the UCI null move `0000`.

A replacement `go` first explicitly stops the previous request, so the previous request emits one final move before the replacement starts.

Successful `position`, `ucinewgame`, `quit`, input EOF, and slot drop cancel stale work but suppress its final move. This prevents a result from an obsolete position from appearing after session state has changed.

## Failure behavior

Search setup failures that occur before thread creation are reported by the protocol thread. Search execution and transposition-allocation failures are reported by the worker immediately. Output failures become a typed `SearchWorkerError::Output`, request cancellation, and are not silently discarded. A poisoned output lock is also a fail-loud I/O error.

## Tests

Task 17.4 adds focused coverage for:

- ordered completed-depth observation;
- centipawn and signed mate conversion;
- zero-time and overflow-safe NPS calculation;
- all required `info` fields, hash fullness, and legal PV formatting;
- final best move with ponder;
- terminal `bestmove 0000`;
- natural completion emitting one final move;
- explicit stop emitting one final move;
- stale-result suppression;
- typed output failure and cancellation.

Full process transcripts, GUI workflow coverage, and stop/quit subprocess tests remain Task 17.5.

## Completion evidence

Implementation SHA: `0f0ed39b31aca077173359c5807c1afaffb3e9e4`.

Permanent clean-tree validation:

- PR: `#228`;
- workflow run: `30805483433`;
- job: `91659743430`;
- formatting, locked all-target/all-feature workspace compilation, strict Clippy, the complete workspace test suite, authoritative release perft, rustdoc with warnings denied, debug and release builds, and the independent differential corpus with seeded playouts all passed.

Task 17.4 is complete. Task 17.5 and the overall Task 17 gate are also complete. Task 18.1 Rust facade work is next.
