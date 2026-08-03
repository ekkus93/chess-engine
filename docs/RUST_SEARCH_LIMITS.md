# Rust Search Limits — Task 16.4

Task 16.4 adds a typed limit boundary around the exact iterative-deepening engine. Limits never turn a partial depth, aspiration bound, or interrupted principal variation into a completed result.

## Public request types

`SearchLimits` may contain:

- a completed-depth limit;
- a cumulative node limit across every aspiration attempt and depth;
- a soft time limit;
- a hard time limit;
- explicit infinite mode;
- a shared `SearchStopFlag`.

Finite mode requires at least one automatic depth, node, or time limit. Infinite mode rejects every automatic limit and requires a stop flag. A stop flag may also accompany finite limits.

Zero depth, zero nodes, zero-duration time limits, depth above `MAX_MATE_PLY`, soft time above hard time, empty finite requests, and conflicting infinite requests fail before the caller-owned table, position, or history is mutated.

## Deterministic precedence

At every limit checkpoint, termination precedence is:

1. explicit stop flag;
2. hard time;
3. cumulative nodes;
4. completed depth;
5. soft time;
6. the engine's `MAX_MATE_PLY` safety ceiling for requests without an explicit depth.

This ordering makes simultaneous boundaries reproducible. For example, an explicit stop wins over an expired hard time, and an exhausted node budget wins over a soft-time crossing.

## Node accounting

The node budget counts production alpha-beta and quiescence node entries exactly once. It includes:

- all completed depths;
- an initial aspiration attempt;
- a full-window retry;
- the entered portion of an interrupted attempt.

`LimitedIterativeDeepeningSearchResult::searched_nodes` reports the complete cumulative count. `completed().total_nodes()` covers only exact completed iterations. Their difference is available through `incomplete_nodes()` and represents discarded partial work.

The controller permits at most the configured number of node entries. Once exhausted, the active recursion unwinds through the existing make/history/unmake discipline before the limited result is returned.

## Soft and hard time

Soft time is an iteration-boundary policy. It is checked only after a fully exact depth, including aspiration recovery and legal PV reconstruction. A soft crossing therefore preserves that newly completed iteration and never interrupts it.

Hard time is checked at production tree node and child boundaries. It may interrupt an initial aspiration attempt or full-window retry. The interrupted depth is omitted; earlier exact iterations remain available.

Wall-clock measurement begins after limit validation and transposition-table allocation. Task 16.6 remains responsible for the final public elapsed-time field.

## Explicit stop and infinite mode

`SearchStopFlag` is backed by a shared atomic boolean. Clones observe the same state. `request_stop()` may be called from another thread; `reset()` is intended only before starting a later request.

An already-set flag terminates before table generation advancement or root search. Infinite mode is intentionally stop-driven: it requires a flag and has no automatic depth, node, soft-time, or hard-time limit. `MAX_MATE_PLY` remains a fail-safe engine-domain ceiling.

## Partial-depth policy

The limit-aware entry points return `LimitedIterativeDeepeningSearchResult`:

- `completed()` contains only exact fully completed iterations;
- `termination()` identifies the limit that won precedence;
- `searched_nodes()` includes completed and discarded work;
- `incomplete_nodes()` isolates discarded partial work.

A cancelled depth cannot contribute a score, best move, PV, ponder move, aspiration record, or completed node total. The caller can inspect the last completed iteration when one exists. When no iteration completed, `fallback()` returns a deterministic first legal move or an explicit terminal `NoLegalMove` value. The one-node polling bound and cancellation benchmark are documented in `docs/RUST_RESPONSIVE_CANCELLATION.md`. Task 16.6 remains responsible for the final unified engine result API.

## Entry points

The new convenience API is:

```rust
iterative_deepening_search_with_limits(position, history, limits)
```

The caller-owned bounded-table API is:

```rust
iterative_deepening_search_with_limits_and_transposition_table(
    position,
    history,
    limits,
    transposition_table,
)
```

The pre-existing fixed-depth APIs retain their original exact behavior and error contract.

## Task 16.6 result accounting

The final `SearchResult` reports request-wide elapsed time, nodes, qnodes, and selective depth. These totals include discarded partial work; exact score, move, PV, ponder move, and completed depth still come only from the last fully completed iteration.


## Optional bounded check extension

`SearchLimits::with_check_extension()` opts the request into the Task 16.7
one-ply-per-line check extension. The feature is not an automatic stopping limit
and is valid in finite or infinite mode. Its extra nodes remain subject to the
same node, hard-time, and explicit-stop checkpoints. Request-wide extension
diagnostics include interrupted partial work.
