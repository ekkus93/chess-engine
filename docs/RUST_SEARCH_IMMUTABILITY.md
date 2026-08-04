# Rust Search Immutability and Cancellation

## Scope

Task 13.4 formalizes the state-restoration contract for the Task 13 reference
and alpha-beta searches. It adds a narrow cooperative cancellation boundary so
cancellation can be exercised from inside recursive search lines.

This task does not implement Task 16 search limits. It does not add clocks,
node budgets, iterative deepening, aspiration windows, principal variation
storage, partial-result policy, or a production stop token.

## Public cancellation boundary

The search crate exports:

- `SearchCancellationProbe`;
- `reference_search_with_cancellation`;
- `alpha_beta_search_with_cancellation`.

A probe returns `true` when search should stop. Closures implementing
`FnMut() -> bool` automatically implement the probe trait. Existing
`reference_search` and `alpha_beta_search` remain unchanged convenience APIs
that use a probe which never cancels.

Cancellation is cooperative. Both searches check the probe at node and child
boundaries. They do not interrupt move generation, evaluation, make/unmake, or
history restoration halfway through an operation.

## Restoration ordering

For every applied child, search performs the following sequence:

1. apply a source-bound legal move token;
2. push the child identity into detached line history;
3. recurse;
4. pop the line-history entry;
5. unmake the child move;
6. only then propagate success, cancellation, or another child error.

Therefore an error returned by a descendant cannot bypass restoration of an
active ancestor line. Restoration errors remain higher priority than the child
result because they indicate corrupted engine state.

## Required immutability

After every public search invocation, including cancellation and validation
failure:

- the logical `Position` equals its root snapshot;
- the incremental Zobrist key equals the root key;
- recomputed and incremental Zobrist identities agree;
- every enforceable position invariant passes;
- detached `SearchHistory` equals its root snapshot;
- the history's current identity still equals the root position identity.

Repeated searches from the same mutable position and history must return the
same deterministic result and may not accumulate line entries, hashes, moves,
or other drift.

## Validation matrix

`crates/chess-search/tests/search_immutability.rs` covers:

- repeated reference and alpha-beta completion from a nontrivial game-derived
  root history;
- reference cancellation after 64 probe checks from inside an active tree;
- alpha-beta cancellation after 64 probe checks from inside an active tree;
- checkmate, stalemate, and rule-draw terminal completion;
- mismatched-history rejection;
- excessive-depth rejection;
- invariant and recomputed-hash checks after each invocation.

The cancellation tests intentionally do not use an already-cancelled root.
They prove unwind behavior after recursive make/push operations have occurred.

## Error contract

Cancellation returns:

- `ReferenceSearchError::Cancelled`; or
- `AlphaBetaSearchError::Cancelled`.

No incomplete score, best move, node count, or principal variation is returned.
Task 16 will own any future policy for retaining the last fully completed
iteration or exposing partial diagnostics.

## Explicit exclusions

Task 13.4 does not complete:

- Task 13.5 terminal-distance fixtures;
- time or node limits;
- asynchronous worker ownership;
- atomic cancellation-token storage;
- iterative deepening;
- principal variations;
- quiescence cancellation;
- UCI `stop` integration;
- Android/JNI cancellation.

Those remain assigned to Task 13.5 and later search, adapter, and integration
tasks.
