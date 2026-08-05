# Rust Chess Engine Post-Port Review Fix TODO

**Status:** Complete
**Date:** 2026-08-04
**Completed:** 2026-08-04 America/Los_Angeles / 2026-08-05 UTC
**Branch:** `master`
**Spec:** `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_SPEC_2026-08-04.md`
**Authoritative Rust-port tracker:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`
**Final Rust-port report:** `docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md`
**Legacy TODO authority index:** `docs/LEGACY_TODO_INDEX.md`

## Ralph-loop implementation record

- Baseline `master` SHA: `62a80700e4bec8e297bc8899e49496d3ae71ce47`.
- Code implementation SHA: `5f09b051f45769ad11f2b4a44143bb85eca2b981`.
- Exact validation SHA: `c977dfb165721a9875f51573fcaee5a02f553a63`.
- Reproduced findings: legal generation silently skipped contradictory pseudo-legal candidates; the Task 21 detailed heading was stale; legacy TODO authority was ambiguous; and two FEN source labels overclaimed playable legality.
- Implemented policy: fail loudly for genuine internal candidate contradictions, preserve normal king-safety/castling/en-passant filtering, create a non-disruptive TODO authority index, and clarify FEN terminology without narrowing accepted analysis positions.
- Non-issue confirmed: strict FEN behavior already intentionally accepted structurally safe analysis positions without claiming game reachability.
- Ralph-loop defects caught before closure:
  1. the first authority audit accidentally classified `LEGACY_TODO_INDEX.md` as its own legacy entry because its filename contains `TODO`;
  2. the first candidate validator treated a structurally safe, non-capturable en-passant analysis target as an internal generator contradiction instead of normal special-rule filtering.
- Both defects were corrected at source. No failure was suppressed, ignored, filtered from CI, or converted into a fallback.
- Deviations from the spec: none.

## Status rules

- `[x]` means complete with code, documentation, and exact validation evidence.
- This post-port review cleanup does not reopen Task 27.

## Program guardrails — PRESERVED

- [x] Work was performed directly on `master`; no branch or PR was created.
- [x] The patch remains small and auditable.
- [x] No tuned weights were activated.
- [x] Default evaluation weights were not changed.
- [x] Python history and source were not deleted.
- [x] Rust, Android, robustness, performance, Task 26, and Task 27 validation were not weakened.
- [x] No lint suppression, ignored first-party failure, output filter, or fallback gate was added.
- [x] Rust remains authoritative and Python remains reference-only.

---

# Task PPR-0: Baseline inspection and evidence capture — COMPLETE

## PPR-0.1 Confirm repository state

- [x] Confirmed baseline `master` SHA `62a80700e4bec8e297bc8899e49496d3ae71ce47`.
- [x] Confirmed `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_SPEC_2026-08-04.md` exists.
- [x] Confirmed this TODO exists at its required path.
- [x] Confirmed `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md` remains the authoritative Rust-port tracker.
- [x] Confirmed `docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md` remains the final port report.

## PPR-0.2 Reproduce review findings

- [x] Inspected `crates/chess-core/src/position/legal.rs` and reproduced silent skips for internally contradictory pseudo-legal candidates.
- [x] Confirmed the Task 21 detailed heading still read `IN PROGRESS` at baseline.
- [x] Inventoried every top-level `docs/*TODO*.md` file.
- [x] Inspected FEN documentation, source comments, and analysis-position tests for reachability overclaims.

## PPR-0.3 Baseline validation snapshot

- [x] Recorded the baseline SHA and relevant file paths.
- [x] Inspected current repository contents rather than reusing Task 27 evidence as implementation proof.
- [x] Recorded permanent CI as the validation authority.

**PPR-0 gate:** Complete.

---

# Task PPR-1: Fail-loud legal movegen hardening — COMPLETE

## PPR-1.1 Candidate validation refactor

- [x] Isolated private per-candidate validation in `Position::validate_generated_candidate`.
- [x] Added no public or crate-public API.
- [x] Genuine impossible generator output returns `LegalMoveError::InvalidGeneratedMove { current }`.
- [x] Ordinary king-safety rejection remains normal filtering.
- [x] Castling attacked-source/transit/destination rejection remains normal filtering.
- [x] En-passant discovered-check rejection remains normal filtering.
- [x] A geometrically generated en-passant candidate from a structurally safe analysis FEN with no capturable pawn remains a normal special-rule rejection rather than a fabricated internal error.

## PPR-1.2 Replace silent skips with typed failures

- [x] Empty generated source square returns `InvalidGeneratedMove`.
- [x] Wrong-side generated moving piece returns `InvalidGeneratedMove`.
- [x] Encoded move-kind/promotion/capture contradiction returns `InvalidGeneratedMove`.
- [x] `Position::is_legal_move` retains ordinary caller-supplied illegal-move behavior.
- [x] `Position::make_move` retains ordinary caller-supplied illegal-move behavior.

## PPR-1.3 Regression tests

- [x] Added `empty_source_generated_candidate_fails_loudly`.
- [x] Added `wrong_side_generated_candidate_fails_loudly`.
- [x] Added `encoded_state_contradiction_fails_loudly`.
- [x] Preserved king-safety filtering tests.
- [x] Preserved castling and en-passant special-rule filtering tests.
- [x] No public test hook was added; the private helper is exercised from the existing `#[cfg(test)]` child module.

## PPR-1.4 Perft and legality preservation

- [x] Starting-position legal move count remains `20`.
- [x] Starting-position perft depth 1 remains `20`.
- [x] Starting-position perft depth 2 remains `400`.
- [x] Starting-position perft depth 3 remains `8,902`.
- [x] Starting-position perft depth 4 remains `197,281`.
- [x] The authoritative perft suite was not weakened or rewritten.

**PPR-1 gate:** Complete. Internal contradictions fail loudly while normal legal filtering and public illegal-move behavior remain unchanged.

---

# Task PPR-2: Task 21 tracker status consistency — COMPLETE

## PPR-2.1 Normalize live tracker wording

- [x] Updated the detailed Task 21 heading to `COMPLETE`.
- [x] Preserved the summary row marking Task 21 complete.
- [x] Preserved Task 21.5 production-control evidence.
- [x] Preserved `activated=false`.
- [x] Preserved that baseline weights remain authoritative.
- [x] Preserved that future tuned-weight promotion is a separate strength change.

## PPR-2.2 Avoid false activation claims

- [x] Did not claim a tuned candidate passed production validation.
- [x] Did not change default weights.
- [x] Did not modify candidate-validation thresholds.
- [x] Did not modify tuning artifacts beyond status wording.

**PPR-2 gate:** Complete.

---

# Task PPR-3: Legacy TODO archive/deprecation clarity — COMPLETE

## PPR-3.1 Inventory legacy TODOs

- [x] Searched top-level `docs/` for filenames containing `TODO`.
- [x] Classified 71 TODO-named files: three active documents, one authority index, and 67 historical references.
- [x] Recorded the exhaustive inventory in `docs/LEGACY_TODO_INDEX.md`.

## PPR-3.2 Choose cleanup policy

- [x] Chose the least disruptive policy: an authority/index document.
- [x] Did not mass-move files.
- [x] Did not delete historical TODOs.
- [x] Preserved links from final reports and trackers.

## PPR-3.3 Apply policy

- [x] Made the active tracker, task definitions, and this follow-up explicit.
- [x] Classified every other TODO-named implementation document as historical/legacy.
- [x] Classified `LEGACY_TODO_INDEX.md` itself as authority metadata, not an implementation TODO.
- [x] Made clear that historical TODOs cannot override active authority documents.

**PPR-3 gate:** Complete.

---

# Task PPR-4: FEN policy clarification — COMPLETE

## PPR-4.1 Identify affected docs

- [x] Inspected FEN documentation and source comments.
- [x] Inspected `crates/chess-core/src/position/fen.rs`.
- [x] Inspected analysis-position and round-trip tests.
- [x] Identified two source-level uses of playable-position wording that overclaimed the parser contract.

## PPR-4.2 Clarify parser contract

- [x] Documented strict structural FEN for safe analysis positions.
- [x] Documented that structural acceptance is not proof of legal game reachability.
- [x] Documented that accepted positions must satisfy internal invariants and remain safe for legal generation.
- [x] Preserved rejection of malformed field counts, invalid placement/squares, promotion-rank pawns, invalid clocks, duplicate castling tokens, wrong-rank en-passant targets, missing kings, and multiple kings.
- [x] Preserved acceptance of structurally safe unusual castling rights, en-passant targets, check states, and material for analysis.

## PPR-4.3 Preserve behavior

- [x] Did not narrow accepted analysis positions.
- [x] Did not weaken structural validation.
- [x] Preserved FEN round-trip and arbitrary-input tests.
- [x] Added source and documentation wording that prevents future reachability overclaims.

**PPR-4 gate:** Complete.

---

# Task PPR-5: Permanent audit and documentation integration — COMPLETE

## PPR-5.1 Audit scope

- [x] Added `scripts/task_post_port_review_fix_audit.sh`.
- [x] The audit checks Task 21 status/rejection semantics.
- [x] The audit checks active TODO authority and exhaustive historical inventory.
- [x] The audit checks FEN policy wording.
- [x] The audit checks absence of temporary PPR helpers.
- [x] The audit runs Task 26 and Task 27 audits.
- [x] The audit uses stable semantic markers rather than line numbers.
- [x] Wired the audit into `.github/workflows/ci.yml`.

## PPR-5.2 Documentation cross-references

- [x] Confirmed the spec and TODO cross-reference one another.
- [x] Linked `docs/LEGACY_TODO_INDEX.md` from this closure record.
- [x] Did not alter the final Task 27 report.

## PPR-5.3 Honest status

- [x] Kept this follow-up in progress until exact-SHA validation passed.
- [x] Recorded deviations: none.
- [x] Recorded the pre-existing FEN behavior as a confirmed non-issue.
- [x] Recorded both defects discovered during the Ralph loop.

**PPR-5 gate:** Complete.

---

# Task PPR-6: Validation — COMPLETE

## PPR-6.1 Required permanent commands

- [x] `cargo fmt --all -- --check`
- [x] `cargo check --locked --workspace --all-targets --all-features`
- [x] `cargo clippy --locked --workspace --all-targets --all-features -- -D warnings`
- [x] `cargo test --locked --workspace --all-targets --all-features`
- [x] `cargo test --locked -p chess-core --release authoritative_perft_depth_four -- --ignored --exact`
- [x] `python scripts/differential_oracle.py --binary target/release/chess-tools --corpus fixtures/differential_corpus.tsv --games 12 --plies 48 --seed 0xC0FFEE`
- [x] `bash scripts/task_26_v0_1_audit.sh`
- [x] `bash scripts/task_27_full_port_audit.sh`
- [x] `bash scripts/task_post_port_review_fix_audit.sh`

The permanent release depth-four command is the explicit executable form of the TODO's generic release `authoritative_perft` requirement. The differential command records the permanent corpus, game count, ply bound, and seed rather than relying on implicit defaults.

## PPR-6.2 Conditional validation

- [x] Android JNI gate was run because a permanent workflow was touched.
- [x] Performance validation was run because legal move generation is a hot path.
- [x] Robustness validation was run for the core move-generation change.
- [x] The new audit passed directly through permanent CI.

## PPR-6.3 Exact evidence

### Final Rust validation SHA

`c977dfb165721a9875f51573fcaee5a02f553a63`

- CI run `30982663413`
  - Rust workspace quality job `92230288324`: success.
  - Linux ARM64 workspace build job `92230288231`: success.
- All-target workspace result: `380 passed; 0 failed; 4 intentionally controlled/slow tests ignored`.
- Explicit release depth-four authoritative perft: `1 passed; 0 failed`.
- Starting-position legal/perft witnesses: `20`, `20`, `400`, `8,902`, `197,281`.
- Differential oracle: `15 corpus positions`, `293 child FENs`, `272,991 oracle perft nodes`, `576 seeded plies`, seed `12,648,430` (`0xC0FFEE`).
- Task 26 audit: passed.
- Task 27 audit: passed.
- Post-port review fix audit: passed.
- Formatting, check, Clippy, rustdoc, debug/release builds, UCI smoke, and lockfile verification: passed.

### Exact implementation-SHA platform evidence

Implementation SHA: `5f09b051f45769ad11f2b4a44143bb85eca2b981`.

- Android JNI run `30982305144`
  - Android/Kotlin lint job `92229176555`: success.
  - Host JVM JNI contract job `92229176586`: success.
  - Android API 35 JNI smoke job `92229176623`: success.
  - Android performance artifact `8920677629` (`task24-android-performance-5f09b051f45769ad11f2b4a44143bb85eca2b981`).
- Robustness run `30982305321`
  - Native sanitizers and leak checks job `92229164270`: success.
  - Miri core subset job `92229164371`: success.
  - Fuzz smoke and corpus replay job `92229164394`: success.
- Performance run `30982305091`
  - Linux x86-64 performance baseline job `92229162834`: success.
  - Linux ARM64 performance baseline job `92229162844`: success.

The validation SHA differs only by the permanent CI change that expands the workspace test command to the TODO's exact `--all-targets` scope; engine code is identical to the implementation SHA.

**PPR-6 gate:** Complete. No first-party failure was ignored or hidden.

---

# Task PPR-7: Closure — COMPLETE

## PPR-7.1 Evidence update

- [x] Marked every subtask complete only after exact validation.
- [x] Recorded implementation and validation SHAs.
- [x] Recorded exact commands and results.
- [x] Recorded workflow run IDs, job IDs, and Android artifact ID.
- [x] Recorded deviations: none.
- [x] Recorded remaining risks: none identified within this bounded cleanup.

## PPR-7.2 Final consistency checks

- [x] Task 27 remains complete and was not reopened.
- [x] No tuned weights were activated; `activated=false` remains authoritative.
- [x] Legal move counts and authoritative perft remain unchanged.
- [x] Active TODO authority is unambiguous.
- [x] FEN documentation reflects the parser's structural analysis-position policy.
- [x] No temporary workflow or helper file remains.
- [x] No dangerous fallback or quiet/silent failure remains in the reviewed candidate-validation boundary.

## PPR-7.3 Final gate

- [x] PPR-0 gate.
- [x] PPR-1 gate.
- [x] PPR-2 gate.
- [x] PPR-3 gate.
- [x] PPR-4 gate.
- [x] PPR-5 gate.
- [x] PPR-6 gate.
- [x] PPR-7 gate.

**PPR-7 gate:** Complete. The cleanup is implemented, validated, and recorded without reopening Rust-port signoff or making an unverified strength claim.

---

## Completion note

```text
Completion note:
- Implementation SHA: 5f09b051f45769ad11f2b4a44143bb85eca2b981
- Validation SHA: c977dfb165721a9875f51573fcaee5a02f553a63
- Files changed: crates/chess-core/src/position/legal.rs; crates/chess-core/src/position/legal_tests.rs; crates/chess-core/src/position/fen.rs; docs/RUST_FEN_AND_UCI_NOTATION.md; docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md; docs/LEGACY_TODO_INDEX.md; scripts/task_post_port_review_fix_audit.sh; .github/workflows/ci.yml; docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md
- Commands: cargo fmt --all -- --check; cargo check --locked --workspace --all-targets --all-features; cargo clippy --locked --workspace --all-targets --all-features -- -D warnings; cargo test --locked --workspace --all-targets --all-features; cargo test --locked -p chess-core --release authoritative_perft_depth_four -- --ignored --exact; python scripts/differential_oracle.py --binary target/release/chess-tools --corpus fixtures/differential_corpus.tsv --games 12 --plies 48 --seed 0xC0FFEE; bash scripts/task_26_v0_1_audit.sh; bash scripts/task_27_full_port_audit.sh; bash scripts/task_post_port_review_fix_audit.sh
- Results: 380 workspace tests passed, 0 failed, 4 controlled/slow tests ignored in the regular run; explicit release depth-four perft passed; starting counts 20/20/400/8902/197281 preserved; differential oracle passed 15 corpus positions, 293 child FENs, 272991 oracle nodes, and 576 seeded plies; all audits passed
- CI evidence: Rust 30982663413 jobs 92230288324 and 92230288231; Android 30982305144 jobs 92229176555, 92229176586, 92229176623 and artifact 8920677629; robustness 30982305321 jobs 92229164270, 92229164371, 92229164394; performance 30982305091 jobs 92229162834 and 92229162844
- Deviations: none; two Ralph-loop defects were found and fixed before final validation
- Remaining risks: none identified within this bounded post-port review cleanup
```
