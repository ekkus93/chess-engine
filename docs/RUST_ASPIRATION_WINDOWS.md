# Rust Aspiration Windows — Task 16.2

Task 16.2 adds bounded score-centered aspiration searches to iterative deepening without allowing a root bound to masquerade as an exact completed result.

## Policy

Depth one has no prior exact score and therefore searches the complete supported score domain.

For each later depth:

1. take the exact score from the immediately preceding completed iteration;
2. construct an initial window centered on that score with the default half-width `DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS`, currently 50 centipawns;
3. run one fail-soft root search;
4. classify the result as exact, fail-low, or fail-high;
5. on fail-low or fail-high, perform exactly one complete-window retry;
6. retain only an exact attempt as the completed iteration result.

A prior score too close to either absolute mate-score boundary uses the complete window immediately because a symmetric bounded window cannot be represented safely there.

## Bound safety

`AspirationWindowOutcome` is explicit:

- `Exact` means the score lies strictly inside the requested bounded window, or the complete score domain was searched;
- `FailLow` means the reported fail-soft score is an upper bound at or below alpha;
- `FailHigh` means the reported fail-soft score is a lower bound at or above beta.

`AspirationWindowAttempt::reported_score` always exposes the raw fail-soft result for diagnostics. `AspirationWindowAttempt::exact_score` returns `None` for fail-low and fail-high. The iterative-deepening layer cannot construct a completed iteration from those bound outcomes; it must recover through the complete-window retry.

The retry is typed and fail-loud. If a complete-window attempt were ever classified as a bound, the search returns `FullWindowDidNotResolveExactly` instead of publishing an inexact result.

## Retry and table behavior

Each completed depth advances the transposition-table generation exactly once. A retry remains in the same generation so entries found by the failed attempt are reusable without making one logical iteration appear to be multiple generations.

Diagnostics reset before each attempt. Every `AspirationWindowAttempt` records:

- alpha and beta;
- outcome;
- reported score and optional exact score;
- nodes for that attempt;
- TT probe/store counters;
- bounded hash-full sample;
- shared generation identifier.

`AspirationWindowDiagnostics` stores one initial attempt and at most one full-window retry. `IterativeDeepeningIteration::nodes` is the checked sum of all attempts at that depth. `IterativeDeepeningIteration::transposition_diagnostics` is the saturating aggregate, while the exact per-attempt snapshots remain available.

## Determinism and restoration

The exact completed score and canonical best move are compared against an independent full-window fixed-depth search. Failed aspiration attempts never become PV roots. Principal variation reconstruction occurs only after the exact attempt finishes and the root position and detached history have been restored.

Regression coverage includes:

- prior-score centering;
- deterministic fail-low recovery;
- deterministic fail-high recovery;
- explicit proof that bounds have no exact score;
- one-retry maximum;
- exact score and best-move equivalence;
- retry node and TT diagnostics;
- one generation per depth;
- legal PV reconstruction and ponder preservation;
- terminal and mate-boundary full-window fallback;
- exact position, history, and Zobrist restoration.

## Deferred work

Task 16.2 does not add node/time/infinite limits, last-completed-iteration cancellation recovery, the final unified Task 16.6 result API, or check extensions. Those remain Tasks 16.4 through 16.7.
