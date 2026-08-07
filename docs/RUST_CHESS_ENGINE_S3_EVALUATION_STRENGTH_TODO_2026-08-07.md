# Rust Chess Engine S3 Evaluation Strength TODO — 2026-08-07

**Status:** Active — not yet implemented  
**Date:** 2026-08-07  
**Branch:** `master`  
**Planning baseline SHA:** `f5fdd516e469cce5e7d6322488e0265950b02197`  
**Specification:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_SPEC_2026-08-07.md`  
**Completed Rust-port tracker:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Completed Rust-port task definitions:** `docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md`  
**S2 closure report:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_IMPLEMENTATION_REPORT.md`

---

## Status rules

- `[x]` means implemented, documented, tested, and supported by exact validation evidence.
- `[ ]` means incomplete.
- This TODO is active authority for S3 evaluation-strength work.
- S3 does not activate S2.
- S3 does not change package/UCI version from `0.1.0` until a separate activation gate succeeds.
- Training loss, benchmark speed, or workflow success alone cannot authorize activation.
- Every first-party failure must be treated as a source defect unless explicitly classified as an external notice.
- No lint suppression, output filtering, ignored failure, hidden fallback, or weakened gate is acceptable.

---

# Task S3-0: Authority registration and v0.1 baseline freeze — NOT STARTED

## S3-0.1 Authority registration

- [ ] Confirm this TODO is registered as active authority in `docs/LEGACY_TODO_INDEX.md`.
- [ ] Confirm every other directly top-level `docs/*TODO*.md` file is classified as authority, authority index, or historical.
- [ ] Update the permanent TODO-authority audit to allow this S3 TODO and reject unclassified additions.
- [ ] Confirm the S2 v0.2 strength TODO remains historical and not active.
- [ ] Confirm no active S2 activation or v0.2 release task remains.

## S3-0.2 Baseline identity freeze

- [ ] Record the exact current `master` SHA.
- [ ] Record the exact production/code baseline SHA.
- [ ] Record package and UCI version.
- [ ] Record search-policy schema, identifier, checksum, and default policy text.
- [ ] Record evaluation-weight schema, identifier, checksum, and value count.
- [ ] Record C ABI version.
- [ ] Record JNI/Kotlin public surface identity.
- [ ] Record opening-book default state.
- [ ] Record tablebase default state.
- [ ] Record current CI, performance, robustness, and Android/JNI evidence.

## S3-0.3 Non-promotion proof

- [ ] Confirm no rejected S2 candidate is enabled by default.
- [ ] Confirm no public adapter exposes experimental `SearchPolicy` selection.
- [ ] Confirm default search still uses v0.1 policy and baseline evaluation weights.
- [ ] Confirm S3 baseline capture is documentation/audit-only unless a later task explicitly changes code.

## S3-0 gate

- [ ] S3 starts from an exact, documented v0.1 authority baseline.

---

# Task S3-1: Public-surface and review-cleanup guardrails — NOT STARTED

## S3-1.1 Experimental-policy exposure audit

- [ ] Add or strengthen a permanent audit proving UCI cannot select experimental S2 policies.
- [ ] Add or strengthen a permanent audit proving the safe Rust facade cannot select experimental S2 policies.
- [ ] Add or strengthen a permanent audit proving the C ABI cannot select experimental S2 policies.
- [ ] Add or strengthen a permanent audit proving JNI/Kotlin cannot select experimental S2 policies.
- [ ] Add or strengthen a permanent audit proving Android harness code cannot select experimental S2 policies.
- [ ] Add negative tests or source scans for PVS, LMR, null move, futility, razoring, late-move pruning, SEE ordering, SEE pruning, delta pruning, Syzygy, and tablebase public options.

## S3-1.2 `PositionEditor` contract hardening

- [ ] Document that `PositionEditor` updates board representations but not Zobrist state.
- [ ] Add tests or debug witnesses showing current make/unmake callers update and verify Zobrist correctly.
- [ ] Add audit coverage preventing new direct editor mutations outside established safe contexts unless explicitly reviewed.
- [ ] Confirm no public API exposes `PositionEditor`.

## S3-1.3 UCI worker stale-result stress

- [ ] Add stress coverage for `go` followed by `position`.
- [ ] Add stress coverage for `go` followed by `ucinewgame`.
- [ ] Add stress coverage for `go` followed by `quit`.
- [ ] Add stress coverage for repeated `stop` and replacement searches.
- [ ] Prove stale discarded workers do not emit final `bestmove`.
- [ ] Prove explicit `stop` emits exactly one final `bestmove`.

## S3-1.4 Validation

- [ ] Run strict workspace validation.
- [ ] Run UCI process tests.
- [ ] Run performance validation if hot-path code changes.
- [ ] Run Android/JNI validation if adapter-facing code changes.
- [ ] Record exact SHAs, run IDs, job IDs, and artifacts.

## S3-1 gate

- [ ] Review-cleanup guardrails are permanent and exact-SHA validated.

---

# Task S3-2: Self-play data pipeline validation — NOT STARTED

## S3-2.1 Configuration contract

- [ ] Specify canonical self-play config format.
- [ ] Reject unknown fields.
- [ ] Reject duplicate fields.
- [ ] Reject noncanonical whitespace where strict parsing requires canonical input.
- [ ] Validate per-side search limits.
- [ ] Validate transposition-table budgets.
- [ ] Validate claimable-draw policy.
- [ ] Validate opening-position policy.
- [ ] Validate max games and max plies bounds.

## S3-2.2 Determinism and provenance

- [ ] Record engine version and source SHA.
- [ ] Record opening input identity.
- [ ] Record config checksum.
- [ ] Record exact invocation.
- [ ] Record random seed.
- [ ] Prove byte-identical output for repeated runs with identical inputs.
- [ ] Prove changed config changes provenance/checksum.

## S3-2.3 Dataset semantics

- [ ] Define training-eligible and held-out rows.
- [ ] Preserve opening rows according to explicit policy.
- [ ] Record side to move, FEN, result, ply index, source game, and eligibility.
- [ ] Reject malformed generated rows.
- [ ] Reject impossible result values.
- [ ] Reject missing terminal status.
- [ ] Bound output size and fail loudly on capacity/config violations.

## S3-2.4 Validation

- [ ] Add unit tests for parser and validation failures.
- [ ] Add deterministic smoke generation tests.
- [ ] Add dataset round-trip tests.
- [ ] Add provenance checksum tests.
- [ ] Run strict workspace validation and record exact evidence.

## S3-2 gate

- [ ] Self-play data generation is reproducible, strict, and provenance-bound.

---

# Task S3-3: Tuning pipeline validation — NOT STARTED

## S3-3.1 Tuning config contract

- [ ] Confirm strict `CHESS_TUNING_CONFIG\t1` marker.
- [ ] Reject unknown fields.
- [ ] Reject duplicate fields.
- [ ] Reject missing fields.
- [ ] Reject noncanonical fields.
- [ ] Validate learning-rate and decay ranges.
- [ ] Validate perturbation schedule.
- [ ] Validate stability constant.
- [ ] Validate min/max weight bounds.
- [ ] Validate regularization strength.
- [ ] Validate K calibration bounds and interval count.
- [ ] Validate candidate and initial weight identities.

## S3-3.2 Resume and checkpoint contract

- [ ] Resume requires exact previous config.
- [ ] Resume requires checkpoint seed match.
- [ ] Resume rejects corrupted checkpoints.
- [ ] Resume rejects completed checkpoints when no iterations remain.
- [ ] Checkpoint writing is atomic.
- [ ] Report writing is atomic.
- [ ] Candidate artifact writing is atomic.

## S3-3.3 Synthetic/known-answer validation

- [ ] Add a tiny deterministic dataset with known expected loss direction.
- [ ] Prove K calibration is deterministic.
- [ ] Prove SPSA updates remain within bounds.
- [ ] Prove regularization affects candidate selection as expected.
- [ ] Prove held-out loss is computed independently from training loss.
- [ ] Prove malformed dataset or config fails before writing candidate artifacts.

## S3-3.4 Validation

- [ ] Run tuning unit tests.
- [ ] Run tuning CLI smoke tests.
- [ ] Run strict workspace validation.
- [ ] Record exact SHAs, commands, and evidence.

## S3-3 gate

- [ ] Tuning pipeline is strict, reproducible, and fail-closed.

---

# Task S3-4: Evaluation loss framework — NOT STARTED

## S3-4.1 Loss definition

- [ ] Define the logistic loss calculation used for tuning.
- [ ] Define K calibration responsibility.
- [ ] Define treatment of wins, draws, losses, unfinished games, and excluded rows.
- [ ] Define train/held-out split semantics.
- [ ] Define acceptable held-out regression tolerance.
- [ ] Define minimum dataset size for each tuning phase.

## S3-4.2 Reporting

- [ ] Report baseline training loss.
- [ ] Report baseline held-out loss.
- [ ] Report candidate training loss.
- [ ] Report candidate held-out loss.
- [ ] Report loss deltas.
- [ ] Report row counts and exclusion counts.
- [ ] Report exact dataset identities.

## S3-4.3 Tests

- [ ] Add loss calculation unit tests.
- [ ] Add train/held-out separation tests.
- [ ] Add excluded-row tests.
- [ ] Add K calibration report tests.
- [ ] Add report checksum tests.

## S3-4 gate

- [ ] Loss evidence is meaningful, reproducible, and not confused with release evidence.

---

# Task S3-5: Existing-weight group tuning — NOT STARTED

## S3-5.1 Group definitions

- [ ] Define material and piece-square tuning group.
- [ ] Define mobility and activity tuning group.
- [ ] Define pawn-structure tuning group.
- [ ] Define king safety and space tuning group.
- [ ] Define endgame king-activity tuning group.
- [ ] Define full existing-evaluator tuning group.
- [ ] Ensure each group has stable parameter masks or equivalent explicit inclusion rules.

## S3-5.2 Group tuning runs

- [ ] Tune material and piece-square group.
- [ ] Tune mobility and activity group.
- [ ] Tune pawn-structure group.
- [ ] Tune king safety and space group.
- [ ] Tune endgame king-activity group.
- [ ] Tune complete existing evaluator only after group results are reviewed.
- [ ] Preserve baseline weights as production defaults.

## S3-5.3 Group candidate reports

For each tuned group:

- [ ] Record config identity.
- [ ] Record dataset identity.
- [ ] Record training loss.
- [ ] Record held-out loss.
- [ ] Record candidate weight identity.
- [ ] Record candidate artifact checksum.
- [ ] Record exact invocation.
- [ ] Record inactive activation state.
- [ ] Record whether the candidate advances to strength testing.

## S3-5 gate

- [ ] Existing-weight tuning candidates are independently reported and inactive.

---

# Task S3-6: Candidate evaluation artifact registry — NOT STARTED

## S3-6.1 Artifact format

- [ ] Define versioned candidate weight artifact format.
- [ ] Include schema version.
- [ ] Include candidate identifier.
- [ ] Include source commit.
- [ ] Include baseline weight identity.
- [ ] Include candidate value checksum.
- [ ] Include dense vector length.
- [ ] Include tuned group or feature mask identity.
- [ ] Include generation timestamp or deterministic replacement if timestamp is forbidden.
- [ ] Include exact tuning config checksum.
- [ ] Include exact dataset checksum.

## S3-6.2 Validation

- [ ] Reject unknown schema.
- [ ] Reject zero or duplicate candidate identifier.
- [ ] Reject wrong dense vector length.
- [ ] Reject out-of-range weights.
- [ ] Reject checksum mismatch.
- [ ] Reject baseline identity mismatch.
- [ ] Reject malformed text/binary.
- [ ] Reject unsupported candidate type.

## S3-6.3 Integration boundary

- [ ] Add controlled internal loading for validation tools.
- [ ] Do not expose candidate loading through production UCI.
- [ ] Do not expose candidate loading through safe Rust facade unless separately specified.
- [ ] Do not expose candidate loading through C ABI/JNI/Android unless separately specified.
- [ ] Confirm production defaults remain baseline.

## S3-6 gate

- [ ] Candidate artifacts are strict, checksummed, and cannot silently affect production defaults.

---

# Task S3-7: Development strength validation — NOT STARTED

## S3-7.1 Smoke validation

- [ ] Run correctness pre-gates before any games.
- [ ] Run tiny smoke match for candidate plumbing.
- [ ] Record crashes, illegal moves, unfinished games, and infrastructure failures separately.
- [ ] Keep reports inactive.

## S3-7.2 Development validation

- [ ] Run fixed-node development validation for advancing candidates.
- [ ] Run clock development validation for advancing candidates.
- [ ] Use color-swapped openings.
- [ ] Use independent transposition tables.
- [ ] Record sample standard error and lower confidence bound.
- [ ] Reject inconclusive candidates.
- [ ] Reject excessive unfinished games.

## S3-7.3 Advancement rule

- [ ] Define predeclared advancement threshold.
- [ ] Advance only candidates meeting the threshold and all correctness gates.
- [ ] Record rejected and deferred candidates explicitly.
- [ ] Do not activate any candidate.

## S3-7 gate

- [ ] Development validation selects candidates without changing production defaults.

---

# Task S3-8: New evaluation-feature candidates — NOT STARTED

## S3-8.1 Feature admission rule

- [ ] Require a written micro-spec for each new feature.
- [ ] Require trace output for each new feature.
- [ ] Require unit tests for each new feature.
- [ ] Require symmetry/orientation tests.
- [ ] Require benchmark impact measurement.
- [ ] Require held-out loss comparison.
- [ ] Require isolated strength evidence before combination.

## S3-8.2 Candidate feature list

Evaluate only if admitted by S3-8.1:

- [ ] Pawn islands.
- [ ] Backward pawns.
- [ ] Knight outposts.
- [ ] Bishop outposts or bishop quality.
- [ ] Rook activity beyond open/semi-open files.
- [ ] Passed-pawn detail by rank/blockade/support.
- [ ] King safety with attacker weights and shelter defects.
- [ ] Endgame king opposition/activity refinements.
- [ ] Threats and hanging pieces if SEE integration is justified.

## S3-8.3 Feature reports

For each feature:

- [ ] Record exact source SHA.
- [ ] Record feature identifier and checksum.
- [ ] Record evaluation trace terms.
- [ ] Record tests and benchmarks.
- [ ] Record training/held-out loss.
- [ ] Record development strength result.
- [ ] Record inactive activation state.

## S3-8 gate

- [ ] New evaluation features are isolated, measurable, and not silently bundled.

---

# Task S3-9: Combined candidate selection — NOT STARTED

## S3-9.1 Selection policy

- [ ] Select only candidates with positive isolated evidence or explicit rationale.
- [ ] Exclude rejected candidates.
- [ ] Exclude inconclusive candidates unless justified by interaction hypothesis.
- [ ] Record every included component.
- [ ] Record every excluded component.
- [ ] Assign a new combined-candidate identity.
- [ ] Regenerate candidate artifact and checksum.

## S3-9.2 Combined validation

- [ ] Run correctness pre-gates.
- [ ] Run held-out loss validation.
- [ ] Run fixed-node development validation.
- [ ] Run clock development validation.
- [ ] Compare against untouched v0.1.
- [ ] Compare against best single candidate if useful.
- [ ] Keep activation false.

## S3-9 gate

- [ ] A single combined candidate is selected or the program records that no candidate advances.

---

# Task S3-10: Production validation — NOT STARTED

## S3-10.1 Preflight

- [ ] Freeze candidate source SHA.
- [ ] Freeze candidate artifact checksum.
- [ ] Freeze validation opening suite.
- [ ] Freeze validation protocols.
- [ ] Freeze acceptance threshold.
- [ ] Freeze unfinished-game ceiling.
- [ ] Freeze performance ceiling.
- [ ] Confirm no public default changed before validation.

## S3-10.2 Fixed-node production validation

- [ ] Run correctness pre-gates.
- [ ] Run production fixed-node match.
- [ ] Record wins, draws, losses, unfinished games, illegal moves, crashes, time forfeits, and infrastructure failures.
- [ ] Record mean score, standard error, lower confidence bound, and checksum.
- [ ] Emit `accepted_for_activation` only if the predeclared rule passes.
- [ ] Otherwise emit `rejected_strength` or `deferred`.

## S3-10.3 Clock production validation

- [ ] Run correctness pre-gates.
- [ ] Run production clock match.
- [ ] Record wins, draws, losses, unfinished games, illegal moves, crashes, time forfeits, and infrastructure failures.
- [ ] Record mean score, standard error, lower confidence bound, and checksum.
- [ ] Emit `accepted_for_activation` only if the predeclared rule passes.
- [ ] Otherwise emit `rejected_strength` or `deferred`.

## S3-10.4 Final production disposition

- [ ] Require both protocols to pass for activation eligibility.
- [ ] Reject if either protocol rejects.
- [ ] Reject if either protocol has infrastructure failure.
- [ ] Reject if unfinished-game ceiling is exceeded.
- [ ] Record exact run IDs, job IDs, artifact IDs, and checksums.

## S3-10 gate

- [ ] Production validation either accepts a candidate for activation or truthfully rejects/defers it.

---

# Task S3-11: Separate activation and release gate — CONDITIONAL / NOT STARTED

## S3-11.1 Preconditions

- [ ] S3-10 fixed-node report is `accepted_for_activation`.
- [ ] S3-10 clock report is `accepted_for_activation`.
- [ ] Candidate artifact identity is frozen.
- [ ] Candidate source SHA is frozen.
- [ ] No unresolved P0/P1 issue blocks activation.
- [ ] User explicitly approves activation.

## S3-11.2 Activation changes

- [ ] Update default evaluation weights or evaluator feature set.
- [ ] Update production identity and checksums.
- [ ] Update package/UCI version only if release criteria require it.
- [ ] Update documentation.
- [ ] Update C ABI/JNI/Android only if required and versioned.
- [ ] Preserve backward-compatible adapter behavior unless intentionally changed.

## S3-11.3 Activation validation

- [ ] Run strict workspace CI.
- [ ] Run performance validation.
- [ ] Run robustness validation.
- [ ] Run Android/JNI validation.
- [ ] Run UCI smoke validation.
- [ ] Run final production identity audit.
- [ ] Run report validation.
- [ ] Record exact activation SHA and evidence.

## S3-11 gate

- [ ] Activation succeeds only as a separate exact-SHA release step.

---

# Task S3-12: Final report and closure — NOT STARTED

## S3-12.1 Final report

- [ ] Create final S3 implementation report.
- [ ] Record final program outcome.
- [ ] Record every candidate disposition.
- [ ] Record accepted, rejected, and deferred work.
- [ ] Record exact evidence for all completed tasks.
- [ ] Record limitations and future roadmap.
- [ ] Record whether activation occurred.

## S3-12.2 Authority cleanup

- [ ] If S3 closes, move this TODO from active authority to historical inventory.
- [ ] Update `docs/LEGACY_TODO_INDEX.md`.
- [ ] Update permanent TODO-authority audit.
- [ ] Confirm no temporary S3 helper remains.
- [ ] Confirm generated artifacts follow policy.

## S3-12.3 Final validation

- [ ] Run strict workspace validation.
- [ ] Run permanent S3 audit.
- [ ] Run report validation.
- [ ] Run adapter validation if activation changed public surface.
- [ ] Record final exact SHA, run IDs, job IDs, and artifacts.

## S3-12 gate

- [ ] S3 is truthfully closed with exact evidence.

---

# Final S3 completion checklist

- [ ] S3-0 authority and baseline freeze complete.
- [ ] S3-1 public-surface and review-cleanup guardrails complete.
- [ ] S3-2 self-play pipeline validation complete.
- [ ] S3-3 tuning pipeline validation complete.
- [ ] S3-4 evaluation loss framework complete.
- [ ] S3-5 existing-weight group tuning complete.
- [ ] S3-6 candidate artifact registry complete.
- [ ] S3-7 development strength validation complete.
- [ ] S3-8 evaluation-feature candidates complete or explicitly deferred.
- [ ] S3-9 combined candidate selection complete or explicitly rejected/deferred.
- [ ] S3-10 production validation complete.
- [ ] S3-11 activation complete or explicitly skipped.
- [ ] S3-12 final report and closure complete.
