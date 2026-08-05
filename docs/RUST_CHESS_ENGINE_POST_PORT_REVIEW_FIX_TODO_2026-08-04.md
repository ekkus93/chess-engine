# Rust Chess Engine Post-Port Review Fix TODO

**Status:** Not started
**Date:** 2026-08-04
**Branch:** `master`
**Spec:** `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_SPEC_2026-08-04.md`
**Authoritative Rust-port tracker:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`
**Final Rust-port report:** `docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md`

## Status rules

- `[x]` means complete with code, documentation, and validation evidence.
- `[ ]` means incomplete, unverified, blocked, deferred, or not started.
- Do not mark the final gate complete without exact commit SHA and validation
  evidence.
- This TODO is a post-port review cleanup plan. It does not reopen Task 27.

## Program guardrails

- Work directly on `master` unless the user explicitly asks for a branch.
- Keep the patch small and auditable.
- Do not activate tuned weights.
- Do not change default evaluation weights.
- Do not delete Python history or source.
- Do not weaken Rust, Android, robustness, performance, Task 26, or Task 27
  validation.
- Do not add lint suppressions, ignored tests, output filters, or fallback gates.
- Preserve the final Rust-port authority decision: Rust is authoritative; Python
  is reference-only.

---

# Task PPR-0: Baseline inspection and evidence capture — NOT STARTED

## PPR-0.1 Confirm repository state

- [ ] Confirm current `master` SHA before changes.
- [ ] Confirm this spec exists at
      `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_SPEC_2026-08-04.md`.
- [ ] Confirm this TODO exists at
      `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md`.
- [ ] Confirm `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md` remains the
      authoritative Rust-port tracker.
- [ ] Confirm `docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md` remains the
      final port report.

## PPR-0.2 Reproduce review findings

- [ ] Inspect `crates/chess-core/src/position/legal.rs` and identify any
      silent skip of internally contradictory pseudo-legal candidates.
- [ ] Inspect `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md` and confirm
      whether the Task 21 detailed heading still says `IN PROGRESS`.
- [ ] Inventory TODO-like files under `docs/` that are not the active Rust-port
      tracker, task definitions, or this follow-up.
- [ ] Inspect FEN documentation and tests for wording that may overclaim
      game-reachable legality.

## PPR-0.3 Baseline validation snapshot

- [ ] Record the current commit SHA.
- [ ] Record current relevant file paths and any known CI status.
- [ ] Do not mark any implementation task complete based on prior Task 27
      evidence alone; inspect current repository contents.

**PPR-0 gate:** Baseline state and exact review findings are recorded before any
code or documentation cleanup.

---

# Task PPR-1: Fail-loud legal movegen hardening — NOT STARTED

## PPR-1.1 Candidate validation refactor

- [ ] In `crates/chess-core/src/position/legal.rs`, isolate the per-candidate
      validation that checks source occupancy, moving side, and encoded move
      consistency.
- [ ] Keep the helper private or crate-private; do not expose a new public API.
- [ ] Ensure the helper returns `LegalMoveError::InvalidGeneratedMove { current }`
      for impossible internal generator output.
- [ ] Ensure ordinary king-safety rejection remains normal filtering.
- [ ] Ensure castling attacked-source/transit/destination rejection remains
      normal filtering.
- [ ] Ensure en-passant discovered-check rejection remains normal filtering.

## PPR-1.2 Replace silent skips with typed failures

- [ ] Empty source square from an internally generated candidate returns
      `InvalidGeneratedMove`.
- [ ] Wrong-side moving piece from an internally generated candidate returns
      `InvalidGeneratedMove`.
- [ ] Encoded move kind/promotion/capture state contradiction returns
      `InvalidGeneratedMove`.
- [ ] Existing `Position::is_legal_move` behavior remains intact for ordinary
      caller-supplied illegal moves.
- [ ] Existing `Position::make_move` behavior remains intact for ordinary
      caller-supplied illegal moves.

## PPR-1.3 Regression tests

- [ ] Add a focused test for empty-source internal candidate failure.
- [ ] Add a focused test for wrong-side internal candidate failure.
- [ ] Add a focused test for encoded-state contradiction failure.
- [ ] Add or preserve a test proving ordinary king-safety filtering does not
      become an internal error.
- [ ] Add or preserve a test proving special-rule filtering does not become an
      internal error.
- [ ] Ensure any test hook is compiled only under `#[cfg(test)]` and is not
      public API.

## PPR-1.4 Perft and legality preservation

- [ ] Starting-position legal move count remains `20`.
- [ ] Starting-position perft depth 1 remains `20`.
- [ ] Starting-position perft depth 2 remains `400`.
- [ ] Starting-position perft depth 3 remains `8,902`.
- [ ] Starting-position perft depth 4 remains `197,281`.
- [ ] Existing authoritative perft suite remains unchanged unless a real bug is
      found and documented.

**PPR-1 gate:** Internal pseudo-legal contradictions fail loudly with typed errors,
while normal legal filtering and public illegal-move behavior remain unchanged.

---

# Task PPR-2: Task 21 tracker status consistency — NOT STARTED

## PPR-2.1 Normalize live tracker wording

- [ ] Update the detailed Task 21 heading in
      `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md` to `COMPLETE` if it still
      reads `IN PROGRESS`.
- [ ] Preserve the summary table row that marks Task 21 complete.
- [ ] Preserve the Task 21.5 evidence for the production control run.
- [ ] Preserve `activated=false` language.
- [ ] Preserve the statement that baseline weights remain authoritative.
- [ ] Preserve the statement that future tuned-weight promotion is a separate
      strength change.

## PPR-2.2 Avoid false activation claims

- [ ] Do not state that a tuned candidate passed production validation.
- [ ] Do not change default weights.
- [ ] Do not modify candidate-validation acceptance thresholds.
- [ ] Do not modify tuning artifacts except to clarify status wording.

**PPR-2 gate:** Every Task 21 status surface is consistent and still truthfully
records rejection/no-activation semantics.

---

# Task PPR-3: Legacy TODO archive/deprecation clarity — NOT STARTED

## PPR-3.1 Inventory legacy TODOs

- [ ] Search `docs/` for files whose names contain `TODO`.
- [ ] Classify each TODO-like file as one of:
  - active Rust-port tracker;
  - active Rust-port definitions;
  - active post-port review follow-up;
  - historical/legacy reference;
  - generated/obsolete duplicate candidate.
- [ ] Record the inventory in a new or existing documentation section.

## PPR-3.2 Choose cleanup policy

- [ ] Prefer the least disruptive policy that prevents confusion.
- [ ] Option A: create `docs/LEGACY_TODO_INDEX.md` identifying all non-active
      TODOs as historical.
- [ ] Option B: add deprecation banners to legacy TODO files.
- [ ] Option C: move legacy TODO files under an archive directory.
- [ ] Do not perform a mass move unless links from existing reports are checked.
- [ ] Do not delete historical TODOs unless removal is separately justified.

## PPR-3.3 Apply policy

- [ ] Make the active TODO set explicit:
  - `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`;
  - `docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md`;
  - `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md`.
- [ ] Mark older TODO files historical, archived, or deprecated.
- [ ] Avoid breaking final report and tracker references.
- [ ] If an index is created, make it clear that historical TODOs are not active
      implementation instructions.

**PPR-3 gate:** Future agents can identify the active TODO files without confusing
legacy planning files for current work.

---

# Task PPR-4: FEN policy clarification — NOT STARTED

## PPR-4.1 Identify affected docs

- [ ] Inspect FEN-related documentation, especially any file that describes
      strict FEN, playable positions, or analysis-position policy.
- [ ] Inspect `crates/chess-core/src/position/fen.rs` doc comments.
- [ ] Inspect `crates/chess-core/src/position/fen_tests.rs` analysis-position
      tests.
- [ ] Identify any wording that implies every accepted FEN is game-reachable.

## PPR-4.2 Clarify parser contract

- [ ] State that `Position::from_fen` accepts strict structural FEN for safe
      analysis positions.
- [ ] State that structural acceptance is not proof of legal game reachability.
- [ ] State that safe analysis positions must still satisfy internal invariants
      and must not make legal generation unsafe.
- [ ] State the parser still rejects malformed six-field FEN, invalid squares,
      promotion-rank pawns, invalid clocks, duplicate castling tokens, wrong-rank
      en-passant targets, missing kings, and multiple kings.
- [ ] State that unusual castling rights, en-passant targets, or check states may
      be accepted for analysis when structurally safe.

## PPR-4.3 Preserve behavior

- [ ] Do not narrow accepted analysis positions unless a concrete safety bug is
      found.
- [ ] Do not weaken structural validation.
- [ ] Preserve existing FEN round-trip tests.
- [ ] Add one documentation or test assertion if needed to prevent future
      overclaiming.

**PPR-4 gate:** FEN docs accurately describe strict structural analysis FEN and no
longer overclaim game-reachable legality.

---

# Task PPR-5: Permanent audit and documentation integration — NOT STARTED

## PPR-5.1 Decide audit scope

- [ ] Decide whether to add a small dedicated post-port review audit script.
- [ ] If added, place it under `scripts/` with a clear name, for example
      `scripts/task_post_port_review_fix_audit.sh`.
- [ ] The audit should check only stable repository facts:
  - Task 21 heading consistency;
  - active TODO/index wording;
  - FEN policy wording;
  - absence of temporary helper files;
  - existing Task 26 and Task 27 audits still pass.
- [ ] Avoid brittle checks that depend on line wrapping or prose punctuation.

## PPR-5.2 Update documentation cross-references

- [ ] Link this TODO from the spec if not already linked.
- [ ] Link the spec from this TODO.
- [ ] If a legacy TODO index is created, link it from this TODO or relevant docs.
- [ ] Do not alter the final Task 27 report except for a narrow post-port
      follow-up note if absolutely necessary.

## PPR-5.3 Keep final status honest

- [ ] Do not mark this follow-up complete until validation evidence exists.
- [ ] Record all deviations from the spec.
- [ ] Record any discovered non-issues so future agents do not repeat the same
      audit work.

**PPR-5 gate:** Follow-up documentation and optional audit enforce the cleanup
without making the repository brittle or reopening the port signoff.

---

# Task PPR-6: Validation — NOT STARTED

## PPR-6.1 Required local or CI commands

Run and record exact results for:

- [ ] `cargo fmt --all -- --check`
- [ ] `cargo check --workspace --locked --all-targets --all-features`
- [ ] `cargo clippy --workspace --locked --all-targets --all-features -- -D warnings`
- [ ] `cargo test --workspace --locked --all-targets --all-features`
- [ ] `cargo test --workspace --locked --release authoritative_perft`
- [ ] `python3 scripts/differential_oracle.py`
- [ ] `bash scripts/task_26_v0_1_audit.sh`
- [ ] `bash scripts/task_27_full_port_audit.sh`

## PPR-6.2 Conditional validation

- [ ] If Android-facing files, ABI/JNI contracts, generated artifacts, or
      workflows are touched, run the permanent Android JNI gate and record run
      and job IDs.
- [ ] If movegen/search hot-path code is touched, run performance validation or
      record an explicit rationale for why the change cannot affect successful
      legal-position performance.
- [ ] If audit scripts are added or changed, run them directly and through the
      appropriate permanent CI path.

## PPR-6.3 Exact evidence capture

- [ ] Record implementation commit SHA.
- [ ] Record validation commit SHA if different.
- [ ] Record workflow run IDs and job IDs.
- [ ] Record exact Rust test count.
- [ ] Record perft and differential oracle summary.
- [ ] Record whether Android, robustness, or performance gates were required.

**PPR-6 gate:** Required validation passes on an exact SHA with no ignored
first-party failures and no weakened gates.

---

# Task PPR-7: Closure — NOT STARTED

## PPR-7.1 Update this TODO with evidence

- [ ] Mark completed subtasks only after implementation and validation.
- [ ] Add exact implementation SHA.
- [ ] Add exact validation commands and results.
- [ ] Add CI run/job IDs when available.
- [ ] Add deviations and rationale, or state `none`.
- [ ] Add remaining risks, or state `none`.

## PPR-7.2 Final consistency checks

- [ ] Confirm Task 27 remains complete and is not reopened.
- [ ] Confirm no tuned weights are activated.
- [ ] Confirm legal move counts and authoritative perft are unchanged.
- [ ] Confirm active TODO documents are unambiguous.
- [ ] Confirm FEN documentation reflects the actual parser policy.
- [ ] Confirm no temporary workflow or helper file remains.

## PPR-7.3 Final gate

- [ ] PPR-0 gate.
- [ ] PPR-1 gate.
- [ ] PPR-2 gate.
- [ ] PPR-3 gate.
- [ ] PPR-4 gate.
- [ ] PPR-5 gate.
- [ ] PPR-6 gate.
- [ ] PPR-7 gate.

**PPR-7 gate:** The post-port review cleanup is complete, validated, and recorded
without reopening the Rust-port signoff or making unverified strength claims.

---

## Completion-note template

Use this exact structure at closure:

```text
Completion note:
- Implementation SHA: <full SHA>
- Validation SHA: <full SHA or same>
- Files changed: <paths>
- Commands: <exact commands>
- Results: <exact pass counts/perft/oracle/audit outcomes>
- CI evidence: <run/job IDs or "not run" with reason>
- Deviations: <none or exact rationale>
- Remaining risks: <none or exact risks>
```
