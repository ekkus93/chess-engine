# Rust Iterative Deepening — Task 16.1

Task 16.1 adds a correctness-first iterative-deepening layer above the existing full-window fixed-depth negamax alpha-beta search.

## Search sequence

A request for maximum depth `N` performs complete searches at depths `1` through `N` in ascending order. No depth is skipped. Every successful iteration is retained in the returned `IterativeDeepeningSearchResult` as an `IterativeDeepeningIteration` containing:

- completed depth;
- exact full-window `AlphaBetaSearchResult`;
- score and deterministic best move;
- nodes visited by that iteration;
- transposition-table probe/store diagnostics for that iteration;
- bounded current-generation hash-full estimate;
- transposition-table generation identifier.

`total_nodes` is the checked sum of all completed iteration node counts.

## Table and history reuse

The convenience entry point `iterative_deepening_search` allocates one fixed-capacity table using `DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES`, currently 1 MiB. It does not allocate one table per depth.

`iterative_deepening_search_with_transposition_table` accepts a caller-owned fixed table. Entries remain available between iterations. The existing fixed-depth boundary advances the table generation and resets diagnostics once per iteration, which gives each returned record an isolated diagnostic snapshot while preserving retained entries for later-depth probes and move ordering.

The same root `Position` and detached `SearchHistory` are reused for every iteration. Fixed-depth search must restore both exactly before the next depth begins. Invalid maximum depths fail before mutating a caller-owned table. A position/history mismatch fails at depth one before generation advancement.

## Exactness and determinism

Every Task 16.1 iteration uses the complete supported alpha-beta window. Therefore each recorded root score is exact rather than an aspiration-window bound. Root move determinism, repetition-sensitive score suppression, mate normalization, legal-root-move verification, and fixed-capacity TT behavior remain those established by Task 15.

Regression tests compare every retained iteration with an independent fixed-depth full-window search and verify exact position, history, and incremental/recomputed Zobrist restoration.

## Bounded result storage

Maximum depth must be in `1..=MAX_MATE_PLY`. The result reserves exactly that many bounded iteration records through a fallible allocation. Zero depth, excessive depth, result-storage allocation failure, fixed-depth failure, and node-total overflow are typed errors. There is no unbounded map or implicit retry path.

## Deliberately deferred Task 16 work

Task 16.1 does not add:

- aspiration windows or fail-high/fail-low retries;
- node, time, infinite, or stop limits;
- cancellation fallback to the last fully completed iteration;
- the final unified Task 16.6 search-result API;
- check extensions.

Task 16.3 now adds safe legal PV reconstruction and ponder extraction as documented in `docs/RUST_PRINCIPAL_VARIATION.md`. Aspiration windows, limits, cancellation recovery, the final result API, and check extensions remain in Tasks 16.2 and 16.4 through 16.7.
