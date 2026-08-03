# Rust Iterative Deepening — Tasks 16.1–16.3

The iterative-deepening layer performs complete searches at every depth from one through the requested maximum, preserves one exact completed record per depth, applies bounded aspiration windows after depth one, and reconstructs a legal principal variation only from exact search data.

## Search sequence

A request for maximum depth `N` searches depths `1..=N` in ascending order. No depth is skipped.

Depth one uses the complete supported alpha-beta score domain. Each later depth begins with a bounded window centered on the prior completed exact score. An initial fail-low or fail-high triggers exactly one complete-window retry. A bound is never retained as the completed iteration.

Every `IterativeDeepeningIteration` contains:

- completed depth;
- exact `AlphaBetaSearchResult`;
- exact score and deterministic best move;
- safely reconstructed legal principal variation and optional ponder move;
- nodes visited by all attempts at that depth;
- bounded aspiration and retry diagnostics;
- aggregate and per-attempt transposition-table diagnostics;
- bounded current-generation hash-full estimate;
- one generation identifier shared by all attempts at that depth.

`IterativeDeepeningSearchResult::total_nodes` is the checked sum of all attempts at all completed depths.

The aspiration contract is documented in `docs/RUST_ASPIRATION_WINDOWS.md`. Principal-variation safety is documented in `docs/RUST_PRINCIPAL_VARIATION.md`.

## Table and history reuse

The convenience entry point `iterative_deepening_search` allocates one fixed-capacity table using `DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES`, currently 1 MiB.

`iterative_deepening_search_with_transposition_table` accepts a caller-owned table. Entries remain available across depths and across an aspiration retry. The generation advances exactly once per depth. Diagnostic counters reset per attempt, then the returned iteration keeps both the exact attempt snapshots and a saturating aggregate.

The same root `Position` and detached `SearchHistory` are reused throughout. Every attempt must restore both before another attempt or depth begins. Invalid maximum depths fail before table mutation. A position/history mismatch fails at depth one before generation advancement.

## Exactness and determinism

Only `AspirationWindowOutcome::Exact` can become an iteration result. A fail-low score is an upper bound; a fail-high score is a lower bound. `AspirationWindowAttempt::exact_score` returns `None` for both.

Complete-window recovery preserves the fixed-depth full-window score and canonical best move. Root determinism, repetition-sensitive score suppression, mate normalization, complete-key TT verification, legal-root-move validation, and fixed-capacity behavior remain those established by Task 15.

PV reconstruction runs only after exact recovery and validates every move in sequence.

## Bounded result storage

Maximum depth must be in `1..=MAX_MATE_PLY`. Result storage reserves exactly that many iteration records through a fallible allocation.

Each depth has exactly one initial attempt and at most one retry. There is no unbounded widening loop. Zero depth, excessive depth, storage allocation failure, attempt failure, unexpected full-window bound classification, PV reconstruction failure, and node-total overflow are typed errors.

## Deferred Task 16 work

Tasks 16.1, 16.2, and 16.3 do not yet add:

- node, soft-time, hard-time, infinite, or explicit-stop limits;
- cancellation fallback to the last fully completed iteration;
- the final unified Task 16.6 search-result API;
- check extensions.
