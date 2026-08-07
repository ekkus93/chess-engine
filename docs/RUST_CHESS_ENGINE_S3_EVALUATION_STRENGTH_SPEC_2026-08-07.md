# Rust Chess Engine S3 Evaluation Strength Specification — 2026-08-07

**Status:** Active planning authority; implementation not yet complete  
**Date:** 2026-08-07  
**Branch:** `master`  
**Planning baseline SHA:** `f5fdd516e469cce5e7d6322488e0265950b02197`  
**Companion TODO:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md`  
**Completed Rust-port tracker:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Completed Rust-port task definitions:** `docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md`  
**S2 closure report:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_IMPLEMENTATION_REPORT.md`

---

## 1. Executive summary

S3 is a fresh evaluation-strength program for the Rust chess engine. It does
not continue S2 activation, does not reopen the rejected S2 search candidates,
and does not rename the current engine to v0.2.

The goal is to improve playing strength by validating and then using the
existing evaluation, self-play, tuning, and strength-validation infrastructure.
The first candidate work must focus on evaluation weights and evaluation
features rather than reactivating rejected search heuristics.

A future release label such as `0.2.0` is earned only after a separate
production acceptance and activation gate. Until then, the authoritative engine
remains v0.1 with package/UCI version `0.1.0`, v0.1 search policy identifier
`5630315f504f4c31`, and baseline evaluation-weight identifier
`424153454c494e45`.

---

## 2. Background and constraints

The Rust-port program and S2 closure established the following foundation:

- The Rust engine is the authoritative implementation.
- Python is reference-only and must not become a production fallback.
- v0.1 remains authoritative after S2.
- S2 produced useful infrastructure and several rejected or deferred search
  candidates, but no accepted activation candidate.
- S2-15 was skipped because S2-14 did not produce `accepted_for_activation`.
- Public adapters do not expose experimental search-policy selection.
- Syzygy/tablebase support remains absent and disabled.
- Existing self-play and tuning tools are present but have not yet produced an
  activated production evaluator.

S3 starts from the current `master` planning baseline. It may add evidence,
tests, tooling, candidate evaluation weights, candidate evaluator features, and
candidate validation reports. It must not change production defaults until an
explicit activation task succeeds.

---

## 3. Goals

S3 must:

1. Freeze the current v0.1 authority before any new candidate work.
2. Lock down public-surface guardrails so rejected S2 search policies cannot be
   accidentally exposed through UCI, safe Rust, C ABI, JNI, Android, or default
   search entry points.
3. Validate deterministic self-play dataset generation.
4. Validate strict tuning configuration, resume behavior, K calibration, SPSA
   bounds, held-out loss measurement, and candidate artifact provenance.
5. Tune existing evaluation weights in bounded groups before broad all-weight
   tuning.
6. Introduce new evaluation features only when they are independently specified,
   tested, traceable, and measurable.
7. Validate candidate strength with paired equal-resource protocols.
8. Keep candidate reports inactive until a separate activation gate.
9. Close the program truthfully whether the candidate is accepted, rejected, or
   deferred.

---

## 4. Non-goals

S3 must not:

- Promote any S2 candidate.
- Enable PVS, LMR, null-move pruning, SEE ordering, SEE/delta quiescence,
  futility pruning, razoring, late quiet-move pruning, Syzygy, NNUE, or parallel
  search by default.
- Change package/UCI version from `0.1.0` during candidate exploration.
- Expose an experimental search-policy selector through public adapters.
- Treat training loss improvement as release evidence.
- Treat performance-only improvement as strength acceptance.
- Accept silent fallbacks, ignored first-party failures, suppressed lint errors,
  hidden optional dependency discovery, or production subprocess/Python paths.
- Commit generated training datasets, tuning checkpoints, match reports, or
  large artifacts unless a task explicitly approves the artifact policy and the
  permanent audit allows it.

---

## 5. Existing implementation surface to reuse

### 5.1 Evaluation

The evaluator already supports baseline and caller-supplied
`EvaluationWeights`. The canonical runtime weight vector has 816 signed scalar
values. The named optimizer surface contains 810 tunable scalars; six fixed-zero
structural slots (king material plus pawn/king mobility, each in two phases) are
excluded from tuning. S3 should treat the 810 named parameters as the tuning
surface, not as an already-validated strength improvement.

Required tuning groups:

- material and piece-square tables;
- mobility and activity;
- pawn structure;
- king safety and space;
- endgame king activity;
- complete existing evaluator after group-level evidence.

### 5.2 Self-play

The self-play tooling already has versioned schemas, explicit side limits,
transposition-table budgets, claimable-draw policy, opening-position policy,
game and ply limits, and support for baseline/candidate evaluation weights.
S3 must harden this into a reproducible training-data pipeline with permanent
tests and provenance checks.

### 5.3 Tuning

The tuning CLI already parses a strict config marker, validates exact config
fields, supports resume with exact previous config, calibrates logistic K, and
emits reports, candidate artifacts, and checkpoints. S3 must validate the
statistical and artifact semantics before trusting any tuned result.

### 5.4 Strength validation

S3 must reuse the complete-engine-variant validation approach from S2, including
equal-resource fixed-node and clock protocols, color-swapped openings, correctness
pre-gates, unfinished-game accounting, independent transposition tables, lower
confidence bounds, and inactive reports by default.

---

## 6. Candidate identity and activation model

Every S3 candidate must have an explicit identity that records:

- source SHA;
- package/engine version;
- search-policy identity and checksum;
- evaluation-weight schema, identifier, checksum, and value checksum;
- opening and tablebase state;
- build identity;
- exact invocation;
- training dataset identity;
- tuning configuration identity;
- candidate artifact checksum;
- validation protocol;
- activation state.

Candidate reports must serialize `activated=false` until the separate activation
task succeeds. An accepted strength report is necessary but not sufficient for
release; activation remains a distinct task.

---

## 7. Required program phases

### S3-0 — Authority registration and v0.1 baseline freeze

Record the planning baseline, production code identity, package/UCI version,
policy identity, weight identity, C ABI version, JNI/Kotlin surface, opening
identity, tablebase state, and exact CI/performance/robustness/Android status.

### S3-1 — Public-surface and review-cleanup guardrails

Add permanent checks proving rejected S2 experimental search policies cannot be
selected through public adapters. Add documentation/tests for sharp internal
contracts found during review, including the `PositionEditor` Zobrist boundary
and UCI worker stale-result behavior.

### S3-2 — Self-play pipeline validation

Validate strict config parsing, deterministic scheduling, opening handling,
draw policy, search limits, TT isolation, generated dataset schema, train/held-out
split semantics, and reproducible provenance.

### S3-3 — Tuning pipeline validation

Validate tuning config parsing, K calibration, SPSA schedule/bounds, resume
contract, checkpoint integrity, candidate artifact identity, and report
checksums. Include synthetic or controlled tests where the expected direction is
known.

### S3-4 — Evaluation loss framework

Define training and held-out loss measurements. Training loss may guide
candidate selection but cannot authorize activation. Held-out loss regressions
must block strength testing unless explicitly justified.

### S3-5 — Existing-weight group tuning

Tune bounded groups first. Candidate groups must be independently reported and
must not change production defaults.

### S3-6 — Candidate evaluation artifact registry

Create candidate records with stable identifiers, value checksums, provenance,
and exact reproducibility instructions. Reject malformed, mismatched, or
out-of-bounds weight artifacts fail-closed.

### S3-7 — Development strength validation

Run smoke and development matches for each promising candidate. Rejected or
inconclusive candidates remain inactive.

### S3-8 — New evaluation-feature candidates

Only after existing-weight tuning is validated, evaluate new feature terms such
as pawn islands, backward pawns, outposts, rook activity, passed-pawn detail,
richer king safety, and endgame king terms. Each feature must have isolated
tests, traces, benchmarks, and candidate strength evidence.

### S3-9 — Combined candidate selection

Combine only individually justified changes. The combined candidate must have a
new identity and fresh evidence; it cannot inherit acceptance from component
experiments.

### S3-10 — Production validation

Run production strength validation under both fixed-node and clock protocols.
The required lower confidence bound must strictly exceed the predeclared
acceptance threshold. Infrastructure failures, illegal moves, crashes, excessive
unfinished games, or inconclusive results reject.

### S3-11 — Separate activation and release gate

This task is conditional. It may run only if S3-10 emits an
`accepted_for_activation` production report. Activation must update defaults,
versioning, public documentation, and exact-SHA CI evidence in a separate
bounded step.

### S3-12 — Final report and closure

Close truthfully with one of: accepted and activated, accepted but not yet
activated, rejected, or deferred. Preserve exact evidence and update TODO
authority classification.

---

## 8. Acceptance criteria

A candidate may be accepted for activation only if all are true:

- every required correctness pre-gate passes;
- held-out loss does not regress beyond the specified tolerance;
- fixed-node production validation passes;
- clock production validation passes;
- lower confidence bound strictly exceeds the declared margin;
- unfinished games remain within the declared ceiling;
- no illegal move, crash, timeout defect, panic, or infrastructure failure is
  hidden as a chess result;
- performance remains within the declared ceiling or the strength gain justifies
  an explicitly accepted tradeoff;
- public API/ABI/JNI/Android contracts remain stable or are intentionally
  versioned;
- all reports and candidate artifacts are checksummed and reproducible;
- a separate activation commit succeeds on exact `master`.

---

## 9. Validation requirements

At minimum, S3 must preserve or extend:

- `cargo fmt --all -- --check`;
- `cargo check --locked --workspace --all-targets --all-features`;
- `cargo clippy --locked --workspace --all-targets --all-features -- -D warnings`;
- `cargo test --locked --workspace --all-targets --all-features`;
- rustdoc warnings denied;
- authoritative release perft;
- differential oracle and seeded playout validation;
- performance gates on x86-64 and ARM64;
- robustness gates including fuzz/corpus, Miri subset, sanitizers, and leak checks;
- Android/JNI gates when adapter-facing code or public artifacts change;
- permanent TODO-authority audit;
- permanent S3 audit.

---

## 10. Documentation requirements

S3 must keep documentation honest:

- Candidate means inactive unless explicitly activated.
- Accepted-for-activation means eligible for the separate release gate, not
  released.
- Rejected means permanently unusable as activation evidence.
- Deferred means no production claim.
- Historical TODO files remain historical.
- Future active TODO files must be registered in the authority index and audit.

---

## 11. Safety and failure policy

All S3 code must fail loudly on:

- malformed datasets;
- noncanonical tuning config;
- mismatched resume config;
- invalid candidate identities;
- checksum mismatch;
- unknown schema;
- unknown or unsupported feature bits;
- out-of-range weights;
- impossible search/result state;
- adapter-visible unsupported policy requests;
- missing required evidence;
- generated artifact drift.

S3 must not introduce quiet fallbacks, best-effort parsing of critical files,
implicit defaults for absent candidate identity, or hidden optional capability
discovery.

---

## 12. Completion rule

S3 is complete only when the TODO is fully reconciled with code, tests,
documentation, exact validation evidence, and authority classification. If no
candidate earns activation, the final report must explicitly say so and must
leave v0.1 authoritative.
