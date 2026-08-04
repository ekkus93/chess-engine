# Rust UCI Search Worker

Task 17.2 connects the Task 17.1 protocol parser to the production Task 16 search boundary without introducing process-global mutable search state. Task 17.3 adds deterministic UCI clock allocation. Task 17.4 adds synchronized completed-iteration and final-move output.

## Ownership

Each UCI adapter session owns one `SearchWorkerSlot`. The slot owns at most one `SearchWorker`. Each worker owns:

- one immutable `SearchRequest` snapshot;
- one detached mutable `Position` cloned from that request;
- one detached repetition `SearchHistory` rooted in the request game;
- one fixed-capacity `TranspositionTable` sized from the request option snapshot;
- one request-local `SearchStopFlag`;
- one final-output policy flag;
- one named operating-system thread.

The protocol session remains the sole owner of its mutable `Game` and option state. Search never receives mutable access to the live session game. The main thread and worker share only the synchronized adapter output boundary.

## Replacement and shutdown rules

The adapter applies one deterministic lifecycle policy:

1. A new `go` explicitly stops and joins the prior worker before installing the replacement. The prior request emits one final `bestmove`.
2. A successful `position` command updates the session transactionally, then discards and joins any prior worker. The stale result does not emit `bestmove`.
3. `ucinewgame` resets the session game, then discards and joins any prior worker through the same path.
4. `stop` requests the active worker's explicit stop flag, preserves final output, and joins it exactly once.
5. `quit` and input EOF discard stale output, stop, and join before returning.
6. A malformed `position` command does not change session state and does not stop the active worker.
7. Slot drop uses the same stale-result-suppressing discard path.

## Limit conversion

The worker converts Task 17.1 requests into `SearchLimits`:

- `go depth` to a completed-depth ceiling;
- `go nodes` to a cumulative production-node budget;
- `go movetime` to an exact hard wall-clock budget;
- UCI clocks to Task 17.3 soft and hard wall-clock budgets;
- combinations of depth, nodes, and clock budgets;
- `go infinite` to an explicit-stop-only request.

Every request receives its own `SearchStopFlag`, so explicit stop, replacement, and shutdown can interrupt work during a depth.

## Output handoff

The worker calls the protocol-neutral Task 17.4 observer after every exact completed iteration. It formats and flushes `info` through `SharedUciOutput`, then emits exactly one final `bestmove` for natural completion or explicit stop. The complete formatting contract is documented in `docs/RUST_UCI_SEARCH_OUTPUT.md`.

## Failure behavior

Worker setup, execution, and reporting are fail-loud through `SearchWorkerError`:

- missing or unusable side-to-move clock data;
- invalid typed search limits;
- fixed transposition-table allocation failure;
- production iterative-deepening failure;
- progress or final-output failure;
- operating-system thread creation failure;
- worker panic during join.

Worker-side execution failures are emitted immediately. The protocol adapter avoids duplicate error lines when joining an already-reported worker failure.

## Remaining non-goals

Task 17.5 still owns:

- complete process-level UCI transcripts;
- common GUI workflow integration tests;
- subprocess stop timing;
- clean quit/EOF process assertions;
- cross-session output isolation tests.

## Completion evidence

Task 17.2 implementation SHA: `d058353692f9f7c350e55dfae2d1a7c21ac64666`.

Task 17.3 implementation SHA: `1c71f8dfa8449190ea8ae860386b6566b9176cbd`.

Task 17.4 implementation SHA: `0f0ed39b31aca077173359c5807c1afaffb3e9e4`.

Tasks 17.2 through 17.5 and the overall Task 17 gate are complete. Task 18.1 Rust facade work is next.
