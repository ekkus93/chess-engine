# Rust Responsive Cancellation — Task 16.5

Task 16.5 formalizes the cancellation behavior used by fixed-depth alpha-beta, quiescence, and typed limited iterative deepening. Cancellation is cooperative, bounded in production-node units, and never exposes a partially searched depth as exact work.

## Checkpoint contract

`CANCELLATION_CHECK_INTERVAL_NODES` is currently `1`.

Every production alpha-beta node and every production quiescence node calls `SearchCancellationProbe::on_node` before ordinary node work. Move loops also call `should_cancel` before applying the next child move. The strict response target is therefore no more than one additional production-node entry after a request becomes observable.

The one-node bound is a correctness assertion. It is not replaced by a wall-clock threshold, because hosted runners and target devices have different scheduling and node costs.

## Orderly unwind

A cancellation result propagates only after each active child frame:

1. pops its reversible search-history entry;
2. unmakes its applied legal move;
3. restores the parent Zobrist identity;
4. returns the typed cancellation error.

The root boundary verifies the original position, detached history lengths, current history identity, incremental Zobrist value, and recomputed Zobrist value. Cancellation cannot leave a partially applied line behind.

## Iterative-deepening result policy

A cancelled aspiration attempt or depth is discarded completely. It contributes no exact score, best move, principal variation, ponder move, aspiration record, or completed node total.

Every earlier exact iteration remains in `LimitedIterativeDeepeningSearchResult::completed`. Once at least one iteration exists, the deepest completed iteration is authoritative and `fallback()` returns `None`.

## No-completed-iteration fallback

When cancellation occurs before depth one completes, `fallback()` returns one typed `SearchCancellationFallback`:

- `FirstLegalMove(move)` — the first move in deterministic legal-generation order;
- `NoLegalMove` — the root is terminal.

The fallback is generated and validated at the unchanged root. It is not scored, is not inserted into the transposition table, and is never represented as a completed depth-one result. Task 16.6 may wrap this value in the final unified result API without changing this policy.

## Latency benchmark

Run the release benchmark with:

```text
cargo run --locked -p chess-tools --release -- cancel-bench ITERATIONS
```

Output fields are:

```text
operation<TAB>iterations<TAB>request_after_nodes<TAB>maximum_response_nodes<TAB>total_latency_nanos<TAB>maximum_latency_nanos<TAB>checksum
```

Each sample injects a deterministic request after 64 entered production nodes, requires typed cancellation from an unfinished depth-five search, verifies exact position/history/Zobrist restoration, and rejects any sample exceeding `CANCELLATION_CHECK_INTERVAL_NODES` additional nodes. Nanosecond values are informational; the node bound and checksum are the deterministic evidence.
