# Rust Candidate Validation

Task 21.5 validates a named tuned-weight artifact against the built-in baseline without changing runtime defaults.

## Scope

The implementation is in:

- `crates/chess-search/src/iterative_deepening.rs`, `alpha_beta.rs`, and `quiescence.rs` for explicit evaluator injection;
- `crates/chess-tools/src/self_play.rs` for the shared weighted game controller;
- `crates/chess-tools/src/candidate_validation.rs` for correctness gates, paired matches, statistics, reporting, and persistence.

The normal production-search APIs continue to use `EvaluationWeights::DEFAULT`. Candidate weights are used only when an adapter explicitly calls the weighted search entry point.

## Required inputs

A validation run binds:

- a validated `NamedWeightArtifact` candidate;
- the built-in baseline `EvaluationWeightSet`;
- the exact source commit and engine identity;
- the exact invocation string;
- a fixed opening suite;
- a fixed opening-rotation seed;
- one identical search-limit and transposition-table configuration for both evaluators;
- a maximum-ply policy and claimable-draw policy;
- an acceptance margin and unfinished-game ceiling.

The candidate and baseline use separate transposition tables. Evaluator-dependent transposition scores are never shared across weight sets.

## Correctness gate

Correctness runs before any strength match.

Production validation reruns:

1. every authoritative perft fixture at depths one through four;
2. weighted-search forced-mate fixtures covering immediate-mate selection and longest-survival selection;
3. normal named-artifact and runtime-weight validation.

A correctness failure produces `rejected_correctness` and no match games are played. A candidate cannot compensate for a rules, tactical, schema, checksum, or structural regression with a favorable match score.

Permanent CI independently reruns the complete Rust test suite, release perft, differential oracle, Android/JNI regressions, documentation, and debug/release builds.

## Color-balanced match protocol

The production minimum is **200 independent opening pairs**, which means **400 games**. The fixed suite must contain at least 200 semantically distinct opening lines. Production validation rejects both an undersized suite and differently named rows that resolve to the same canonical initial FEN and opening-move sequence, so an opening cannot be reused as a second independent pair.

For each pair:

1. select one opening deterministically from the fixed suite and seed;
2. play candidate as White and baseline as Black;
3. replay the exact same opening with baseline as White and candidate as Black;
4. retain the same pair seed, opening identifier, limits, draw policy, and maximum-ply boundary in both games.

Each pair contributes the average of its two candidate scores. Pairs, not individual games, are the independent statistical units. This prevents color or opening asymmetry from being mistaken for evaluator strength.

Candidate game scores are:

- win: `1.0`;
- completed draw: `0.5`;
- loss: `0.0`;
- unfinished maximum-ply game: `0.5` for score calculation, while also counted separately against the fail-closed unfinished-rate ceiling.

Treating unfinished games separately prevents a candidate from obtaining acceptance by merely steering games into the maximum-ply boundary.

## Acceptance rule

For the independent pair scores, the report computes:

- mean candidate pair score;
- sample standard error;
- one-sided 95% lower confidence bound using `z = 1.6448536269514722`.

A candidate is accepted only when all of the following hold:

1. every correctness check passed;
2. the unfinished-game rate is no greater than the configured ceiling;
3. the lower confidence bound is strictly greater than `0.5 + minimum_score_margin`;
4. the production sample contains at least 200 opening pairs.

Otherwise the report records one of:

- `rejected_correctness`;
- `rejected_unfinished_rate`;
- `rejected_strength`.

A tied or statistically inconclusive candidate is rejected. The protocol does not convert lack of evidence into acceptance.

## Versioned evidence

`CandidateValidationReport` records:

- report schema and semantic identifier;
- engine version, engine identifier, source commit, and exact invocation;
- baseline, candidate, and named-artifact identifiers/checksums;
- opening-suite checksum and source opening count;
- every search, game-length, draw, statistical, and unfinished-rate setting;
- perft and tactical correctness results;
- every paired game, candidate color, result, termination, move list, final FEN, and candidate score;
- wins, draws, losses, unfinished games, mean pair score, standard error, lower confidence bound, and decision;
- a semantic FNV-1a checksum over the complete report.

Text fields are encoded unambiguously and floating-point values include their exact IEEE-754 bits.

The report writer requires caller-selected destination and temporary paths in the same directory, flushes and synchronizes the temporary file, and atomically renames it into place.

## Activation boundary

Validation reports always serialize:

```text
activated=false
```

Neither an accepted report nor a candidate artifact changes `EvaluationWeights::DEFAULT`, the baseline identifier, UCI behavior, JNI behavior, Android behavior, or any global state. Activation requires a separate explicit source/configuration change and its own review and validation evidence.
