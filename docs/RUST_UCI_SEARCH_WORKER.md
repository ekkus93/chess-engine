# Rust UCI Search Worker

Task 17.2 connects the Task 17.1 protocol parser to the production Task 16 search boundary without introducing process-global mutable search state.

## Ownership

Each UCI adapter session owns one `SearchWorkerSlot`. The slot owns at most one `SearchWorker`. Each worker owns:

- one immutable `SearchRequest` snapshot;
- one detached mutable `Position` cloned from that request;
- one detached repetition `SearchHistory` rooted in the request game;
- one fixed-capacity `TranspositionTable` sized from the request option snapshot;
- one request-local `SearchStopFlag`;
- one named operating-system thread.

The protocol session remains the sole owner of its mutable `Game` and option state. Search never receives mutable access to the live session game.

## Replacement and shutdown rules

The adapter applies one deterministic lifecycle policy:

1. A new `go` stops and joins the prior worker before installing the replacement worker.
2. A successful `position` command updates the session transactionally, then stops and joins any prior worker. The prior worker continues to use only its detached old snapshot until cancellation completes.
3. `ucinewgame` resets the session game, then stops and joins any prior worker through the same path.
4. `stop` requests the active worker's explicit stop flag and joins it exactly once.
5. `quit` and input EOF perform an orderly stop and join before returning.
6. A malformed `position` command does not change session state and does not stop the active worker.

Task 17.4 will convert completed or stopped worker results into `info` and `bestmove` output. Task 17.2 retains the typed result but deliberately emits no search-result text.

## Limit conversion

The worker converts these Task 17.1 request forms directly into `SearchLimits`:

- `go depth` to a completed-depth ceiling;
- `go nodes` to a cumulative production-node budget;
- `go movetime` to a hard wall-clock budget;
- combinations of depth, nodes, and move time;
- `go infinite` to an explicit-stop-only request.

Every request, including finite requests, receives its own `SearchStopFlag`, so `stop`, replacement, and shutdown can interrupt work during a depth.

Clock, increment, and moves-to-go allocation remains exclusively owned by Task 17.3. Such requests fail synchronously with `SearchWorkerError::ClockManagementPending`; no worker thread is started and no provisional fixed-depth policy is substituted.

## Failure behavior

Worker setup and execution are fail-loud through `SearchWorkerError`:

- unsupported pre-time-manager clock allocation;
- invalid typed search limits;
- fixed transposition-table allocation failure;
- production iterative-deepening failure;
- operating-system thread creation failure;
- worker panic during join.

The protocol adapter reports worker failures as `info string error: ...` while preserving its session state.

## Non-goals

Task 17.2 does not implement:

- clock allocation or safety margins;
- periodic iterative-deepening `info` output;
- score, node, NPS, hash-full, or PV formatting;
- `bestmove` or ponder output;
- full process-level transcript coverage.

Those remain Tasks 17.3 through 17.5.

## Completion evidence

Task 17.2 was validated at implementation SHA `d058353692f9f7c350e55dfae2d1a7c21ac64666` through temporary validation PR `#212`, workflow run `30788461155`, job `91606833594`.

The exact implementation passed:

- workspace and validation-asset checks;
- the permanent Task 14.5 exclusion audit;
- committed-lockfile and workspace-metadata checks;
- `cargo fmt --all -- --check`;
- locked all-target, all-feature workspace compilation;
- strict Clippy with warnings denied;
- the complete workspace test suite, including five focused worker and protocol-lifecycle tests;
- authoritative release perft;
- rustdoc with warnings denied;
- debug and release workspace builds;
- the independent differential corpus and seeded playout oracle.

Validation corrections were limited to canonical rustfmt output and removal of one test-only method from the production binary. No lint suppression, fallback search policy, or lifecycle relaxation was introduced.

Task 17.2 is complete. Task 17.3 owns deterministic UCI clock allocation, while Task 17.4 owns periodic search information and final `bestmove` output.
