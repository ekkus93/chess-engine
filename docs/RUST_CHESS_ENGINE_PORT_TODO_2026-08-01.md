# Rust Chess Engine Port TODO — Live Status Tracker

**Status:** In progress  
**Date created:** 2026-08-01  
**Last status update:** 2026-08-01  
**Target branch:** `rust-engine`  
**Authoritative specification:** `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md`  
**Full task definitions:** `docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md`  
**Ralph Loop status:** `docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md`

---

## Status rules

- `[x]` means the action is complete and supported by repository evidence.
- `[ ]` means the action is incomplete, blocked, unverified, or not started.
- **Partial** means implementation exists but the complete wording or exact-SHA gate is not yet satisfied.
- A task gate stays open until every required action and its validation evidence are complete.
- The full task-definition file preserves every original action item.
- Update this file whenever implementation, tests, CI, documentation, or evidence changes any task or subtask status.

---

## Current task summary

| Task | Status | Current result |
|---:|---|---|
| 0 | **In progress — final CI pending** | Frozen source equivalence and the fast Python suite passed; the slow suite, perft, and UCI evidence were interrupted by concurrency and require an uninterrupted exact-head rerun. |
| 1 | **Implemented — final CI pending** | All Rust gates passed once. The generated lockfile is committed, member license inheritance is fixed, and an orphaned worktree gitlink is being removed before final exact-head validation. |
| 2 | **Not started** | Core value types have not been implemented. |
| 3 | **Not started** | `Position` and invariants have not been implemented. |
| 4 | **Not started** | Strict FEN and UCI move notation have not been implemented. |
| 5 | **Not started** | Attack-generation infrastructure has not been implemented. |
| 6 | **Not started** | Pseudo-legal move generation has not been implemented. |
| 7 | **Not started** | Complete legal move generation and special rules have not been implemented. |
| 8 | **Not started** | Make/unmake and incremental state have not been implemented. |
| 9 | **Not started** | Zobrist hashing and canonical repetition identity have not been implemented. |
| 10 | **Not started** | `Game`, history, and Rust draw semantics have not been implemented. |
| 11 | **Not started** | Authoritative Rust perft and differential validation have not been implemented. |
| 12 | **Not started** | Baseline Rust evaluation has not been implemented. |
| 13 | **Not started** | Reference search and negamax alpha-beta have not been implemented. |
| 14 | **Not started** | Quiescence and principled move ordering have not been implemented. |
| 15 | **Not started** | Fixed-capacity transposition table has not been implemented. |
| 16 | **Not started** | Iterative deepening, PV, limits, and cancellation have not been implemented. |
| 17 | **Not started** | Linux UCI behavior has not been implemented beyond an empty crate placeholder. |
| 18 | **Not started** | Safe API, C ABI, and Android JNI behavior have not been implemented beyond empty crate placeholders. |
| 19 | **Not started** | Optional Rust opening-book infrastructure has not been implemented. |
| 20 | **Not started** | Rust self-play and dataset tooling have not been implemented. |
| 21 | **Not started** | Rust named-schema tuning has not been implemented. |
| 22 | **Not started** | Advanced classical terms have not been evaluated under the Rust protocol. |
| 23 | **Not started** | Property, fuzz, sanitizer, and robustness gates have not been implemented. |
| 24 | **Not started** | Performance hardening and regression budgets have not been implemented. |
| 25 | **Partial** | Workspace architecture, dedicated Python CI, registered Rust `CI`, deterministic dispatch, Linux Rust gates, and artifact collection exist; the complete matrix and developer workflow remain open. |
| 26 | **Not started** | v0.1 signoff has not begun. |
| 27 | **Not started** | Full port-program signoff has not begun. |

---

## Program rules — ongoing constraints

- Work only on `rust-engine` unless the user explicitly authorizes a narrowly scoped CI-support change on `master`.
- Do not create a branch or pull request without explicit user instruction.
- Treat the Rust specification as authoritative.
- Treat Python code/tests as reference material, not an API compatibility contract.
- Preserve the Python implementation during the port.
- Every first-party compiler warning, Clippy warning, rustdoc warning, formatting failure, lint error, and test failure is a bug.
- Fix first-party findings at their source; do not hide, suppress, downgrade, ignore, or filter them.
- Third-party, dependency, generated-vendor, and vendored-code warnings are outside the first-party rule unless caused by this repository's integration code.
- Add tests with every behavioral implementation task.
- Preserve every discovered rules mismatch as a Rust regression test.
- Do not add advanced pruning before reference and baseline alpha-beta agree at shallow depths.
- Do not port transcript-specific guidance.
- Do not use clone-per-child in production search.
- Do not use string position keys in Rust search/repetition tracking.
- Do not silently auto-load weights, books, or configuration.
- Do not allow Rust panics across C or JNI boundaries.
- Use GitHub Actions as the authoritative Rust execution environment.
- Commit each fix directly to `rust-engine`, inspect CI feedback, and repeat until the exact SHA is green.
- Record exact commands, results, environment, artifacts, run IDs, job IDs, and commit SHA for every major gate.
- Keep this TODO synchronized with repository reality.

---

# Task 0: Establish the port baseline and decision record

**Task status:** In progress — fast evidence passed; remaining runtime evidence requires an uninterrupted final run.

## 0.1 Preserve the Python baseline

- [x] Record the `rust-engine` SHA before Rust source changes.
  - Frozen baseline: `f743013a84173b551eac5488c638cb48098ec6d0`.
- [x] Run and record the current fast Python test suite.
  - Run `30719636049`, job `91421155337`, candidate `edd5a94685d23a04df15c69dafed5f077fd3fc74`.
  - Result: `1203 passed, 179 deselected in 44.43s`.
- [ ] Run and record the current slow Python test suite when practical.
  - **Partial:** execution began and was cancelled by branch concurrency after 73 tests had reported progress; no pass result is claimed.
- [ ] Record current Python perft results and timings for existing exact positions.
- [ ] Record current UCI smoke behavior.
- [x] Record useful engine-strength/self-play artifacts as historical comparison only.

## 0.2 Create a Python-reference inventory

- [x] Inventory rules and board state.
- [x] Inventory FEN and notation.
- [x] Inventory search.
- [x] Inventory evaluation.
- [x] Inventory opening book.
- [x] Inventory self-play and tuning.
- [x] Inventory UCI.
- [x] Inventory CLI/TUI.
- [x] Inventory transcript-specific guidance.
- [x] Map retained concepts to Rust milestones.
- [x] Mark excluded modules explicitly.

## 0.3 Record Python defects Rust must not copy

- [x] Incorrect dead-position/insufficient-material shortcuts.
- [x] Castling safety with the source king still blocking attack lines.
- [x] Clone-per-child search.
- [x] String position keys.
- [x] Raw en-passant field in every repetition key.
- [x] Permissive FEN parsing.
- [x] Implicit queen promotion.
- [x] Multiple internal move representations.
- [x] Unbounded per-search dictionary TT.
- [x] Missing TT mate-score normalization.
- [x] Root heuristic/tie-break interaction with alpha-beta bounds.
- [x] Automatic tuned-weight discovery.
- [x] Global UCI control/output state.
- [x] Narrow transcript-driven evaluation/ordering patches.

## 0.4 Completion evidence

- [x] Commit the baseline/decision record.
- [x] Record its SHA.
- [x] Avoid architectural migration through Python-internal edits.
- [x] Add fail-loud Python baseline capture tooling.
- [x] Add a GitHub Actions `Python reference baseline` job.
- [x] Review the first baseline artifact.
  - Artifact ID `8824498772`, SHA-256 `045b8f3f395189095beca42c34991338b174b53a3426e8205bea7a879b418d63`.
  - Confirmed Python tree equivalence, runner environment, `uv sync`, and fast-suite success.
  - Slow/perft/UCI evidence absent because the job was cancelled.

### Task 0 completion note — gate open

- **Baseline commit:** `234e26c1597756aac01ef24b085624c2a834d4e6`
- **Capture tooling:**
  - `a579aa28f072934a67df082cbf830ea51831c971`
  - `fba5ca2e0ca6139a943f4018dadb925e2c37a88d`
  - `7ed9fa063ea512ca94f5f100e3192578da3fce3a`
- **First evidence run:** `30719636049` at `edd5a94685d23a04df15c69dafed5f077fd3fc74`.
- **Remaining evidence:** complete slow suite, exact perft counts/timings, UCI smoke, and final exact-head artifact.

**Task 0 gate:** **OPEN.**

---

# Task 1: Create the Cargo workspace and dependency boundaries

**Task status:** Implemented; all Rust commands passed once, with first-run metadata/repository findings corrected before final validation.

## 1.1 Workspace skeleton

- [x] Add root Cargo workspace configuration.
- [x] Add `crates/chess-core`.
- [x] Add `crates/chess-search`.
- [x] Add `crates/chess-uci`.
- [x] Add `crates/chess-ffi`.
- [x] Add `crates/chess-jni`.
- [x] Add `crates/chess-tools`.
- [x] Add `crates/chess-tune`.
- [x] Add minimal crate-level responsibility/dependency documentation.
- [x] Keep all optional/future crates buildable while feature-empty.
  - All seven packages passed check, Clippy, tests, rustdoc, debug build, and release build at `edd5a94685d23a04df15c69dafed5f077fd3fc74`.

## 1.2 Toolchain and policy

- [x] Pin or document the minimum supported Rust version.
  - MSRV: Rust `1.75`.
- [x] Add justified stable rustfmt configuration.
- [x] Configure Clippy through workspace lints and CI.
- [x] Add `#![forbid(unsafe_code)]` to `chess-core` and `chess-search`.
- [x] Deny first-party warnings in workspace policy and CI.
- [x] Add consistent license and package metadata.
  - MIT license file and shared Cargo metadata are present.
  - First CI metadata showed `license: null` in every member, revealing that inheritance was incomplete.
  - `license.workspace = true` has now been added to every member manifest; final CI metadata must confirm `MIT`.
- [x] Commit the CI-generated `Cargo.lock`.
  - Source artifact ID `8824440027`, digest `acc3a519b466d4df8f903fb230ac730aa3acc03fb3a77b8d7dafcf0405fda14c`.
  - Reviewed contents contain only the seven local workspace packages and expected path dependencies.

## 1.3 Architecture enforcement

- [x] Confirm `chess-core` has no search/adapter dependency.
- [x] Confirm `chess-search` depends only on portable core/support crates.
- [x] Confirm UCI, FFI, JNI, tools, and tuning are outward adapters.
- [x] Add architecture/dependency documentation.
- [ ] Confirm checkout/post-job cleanup has no first-party repository warning.
  - **Fix pending final verification:** remove orphaned `.claude/worktrees/agent-a04f1cae54e4430d6` gitlink that caused `fatal: No url found ... in .gitmodules` during checkout cleanup.

## 1.4 Initial CI and local validation

- [x] Add formatting, Clippy, tests, and docs to Rust CI.
- [x] Preserve Python validation on `master` in `.github/workflows/python-ci.yml`.
- [x] Register `.github/workflows/ci.yml` under exact workflow name `CI` on `master`.
- [x] Add Linux x86-64 debug and release build coverage.
- [ ] Add AArch64 and Android compile jobs when toolchains are configured.
- [x] Add Cargo lockfile generation and `--locked` validation.
- [x] Add Cargo metadata validation.
- [x] Upload generated `Cargo.lock` as an exact-SHA artifact.
- [x] Add deterministic issue-triggered Rust CI dispatch infrastructure on `master` under explicit authorization.
- [x] Execute the first complete Rust CI gate.
  - Run `30719636049`, job `91421155314`, Rust `1.97.1` on Ubuntu `24.04.4`.
  - Formatting, metadata, check, Clippy, tests, rustdoc, debug build, release build, and artifact upload all passed.
  - Rust packages currently contain no behavioral tests; Task 2 adds the first exhaustive value-type tests.
- [ ] Execute final exact-head CI after committing corrections and lockfile.

### Task 1 completion note — gate open

- **Workspace implementation range:** `11c7d5d14add069a99cc7347a65e0dd677ab3f37` through `ddb54105aff8ad54c40db436872fceec968bfa06`.
- **First successful Rust job:** run `30719636049`, job `91421155314`, candidate `edd5a94685d23a04df15c69dafed5f077fd3fc74`.
- **Third-party warnings accepted:** Node/action deprecation messages emitted by GitHub-maintained actions and `Swatinem/rust-cache` are outside first-party source control.
- **First-party findings fixed/pending verification:** crate license inheritance and orphaned worktree gitlink.
- **Pending evidence:** final exact-head Rust success, metadata license confirmation, warning-free checkout cleanup, and final status issue update.

**Task 1 gate:** **OPEN.**

---

# Tasks 2–24: Numbered subtask status

Every action in the full task-definition file remains open unless stated otherwise.

## Task 2: Core value types and coordinate contracts — NOT STARTED
- [ ] 2.1 Color and piece types.
- [ ] 2.2 Square.
- [ ] 2.3 Bitboard.
- [ ] 2.4 Move encoding.
- [ ] 2.5 Castling rights and counters.
- [ ] Task 2 gate.

## Task 3: `Position` and invariants — NOT STARTED
- [ ] 3.1 Hybrid representation.
- [ ] 3.2 Constructors.
- [ ] 3.3 Accessors and mutation boundary.
- [ ] 3.4 Invariant checker.
- [ ] 3.5 Equality and clone.
- [ ] Task 3 gate.

## Task 4: Strict FEN and UCI move notation — NOT STARTED
- [ ] 4.1 Structured errors.
- [ ] 4.2 Strict FEN parser.
- [ ] 4.3 Canonical FEN serializer.
- [ ] 4.4 UCI move strings.
- [ ] 4.5 Property tests.
- [ ] Task 4 gate.

## Task 5: Attack-generation infrastructure — NOT STARTED
- [ ] 5.1 Leaper attacks.
- [ ] 5.2 Sliding attacks.
- [ ] 5.3 Geometric tables.
- [ ] 5.4 Position attack queries.
- [ ] 5.5 Differential attack fixtures.
- [ ] Task 5 gate.

## Task 6: Pseudo-legal move generation — NOT STARTED
- [ ] 6.1 Pawn moves.
- [ ] 6.2 Piece moves.
- [ ] 6.3 Castling candidates.
- [ ] 6.4 Move list.
- [ ] 6.5 Tests.
- [ ] Task 6 gate.

## Task 7: Complete legal move generation and special rules — NOT STARTED
- [ ] 7.1 King-safety filtering.
- [ ] 7.2 Check evasions.
- [ ] 7.3 Castling correctness.
- [ ] 7.4 En-passant correctness.
- [ ] 7.5 Promotion correctness.
- [ ] 7.6 Initial legal perft.
- [ ] Task 7 gate.

## Task 8: Make/unmake and incremental state — NOT STARTED
- [ ] 8.1 Undo structure.
- [ ] 8.2 Move application paths.
- [ ] 8.3 Restoration tests.
- [ ] 8.4 Sequence restoration.
- [ ] Task 8 gate.

## Task 9: Zobrist hashing and repetition identity — NOT STARTED
- [ ] 9.1 Zobrist tables.
- [ ] 9.2 Full hash computation.
- [ ] 9.3 Incremental updates.
- [ ] 9.4 Canonical en-passant identity.
- [ ] 9.5 Hash verification.
- [ ] Task 9 gate.

## Task 10: `Game`, history, and draw semantics — NOT STARTED
- [ ] 10.1 `Game` state.
- [ ] 10.2 Mate and stalemate.
- [ ] 10.3 Claimable draws.
- [ ] 10.4 Automatic draws.
- [ ] 10.5 Conservative dead-position logic.
- [ ] 10.6 Search-facing history.
- [ ] Task 10 gate.

## Task 11: Authoritative perft and differential validation — NOT STARTED
- [ ] 11.1 Standard exact perft suite.
- [ ] 11.2 Slow perft.
- [ ] 11.3 Divide tool.
- [ ] 11.4 Differential oracle harness.
- [ ] 11.5 Corpus gate.
- [ ] Task 11 gate.

## Task 12: Baseline evaluator and trace — NOT STARTED
- [ ] 12.1 Evaluation score convention.
- [ ] 12.2 Baseline terms.
- [ ] 12.3 Evaluation efficiency.
- [ ] 12.4 Evaluation trace.
- [ ] 12.5 Named weight schema.
- [ ] 12.6 Exclusion audit.
- [ ] Task 12 gate.

## Task 13: Reference search and negamax alpha-beta — NOT STARTED
- [ ] 13.1 Reference search.
- [ ] 13.2 Negamax alpha-beta.
- [ ] 13.3 Equivalence tests.
- [ ] 13.4 Search immutability.
- [ ] 13.5 Terminal fixtures.
- [ ] Task 13 gate.

## Task 14: Quiescence and principled move ordering — NOT STARTED
- [ ] 14.1 Quiescence.
- [ ] 14.2 Tactical ordering.
- [ ] 14.3 Quiet ordering.
- [ ] 14.4 Correctness tests.
- [ ] 14.5 Explicit exclusions.
- [ ] Task 14 gate.

## Task 15: Fixed-capacity transposition table — NOT STARTED
- [ ] 15.1 Entry design.
- [ ] 15.2 Storage layout.
- [ ] 15.3 Mate normalization.
- [ ] 15.4 Probe semantics.
- [ ] 15.5 Replacement policy.
- [ ] 15.6 Diagnostics and benchmarks.
- [ ] Task 15 gate.

## Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED
- [ ] 16.1 Iterative deepening.
- [ ] 16.2 Aspiration windows.
- [ ] 16.3 Principal variation.
- [ ] 16.4 Search limits.
- [ ] 16.5 Responsive cancellation.
- [ ] 16.6 Search result API.
- [ ] 16.7 Optional check extension.
- [ ] Task 16 gate.

## Task 17: Linux UCI executable — NOT STARTED
- [ ] 17.1 Protocol loop.
- [ ] 17.2 UCI search worker.
- [ ] 17.3 Time manager.
- [ ] 17.4 Output.
- [ ] 17.5 Integration tests.
- [ ] Task 17 gate.

## Task 18: Safe API, C ABI, and Android JNI — NOT STARTED
- [ ] 18.1 Safe Rust facade.
- [ ] 18.2 C ABI.
- [ ] 18.3 C ABI tests.
- [ ] 18.4 Android JNI.
- [ ] 18.5 Android test harness.
- [ ] Task 18 gate.

## Task 19: Optional opening-book infrastructure — NOT STARTED
- [ ] 19.1 Core abstraction.
- [ ] 19.2 Backend format.
- [ ] 19.3 Selection policies.
- [ ] 19.4 Adapter integration.
- [ ] 19.5 Tests.
- [ ] Task 19 gate.

## Task 20: Self-play and versioned dataset tooling — NOT STARTED
- [ ] 20.1 Self-play configuration.
- [ ] 20.2 Game records.
- [ ] 20.3 Position dataset schema.
- [ ] 20.4 Data quality.
- [ ] Task 20 gate.

## Task 21: Named-schema Texel-style tuning — NOT STARTED
- [ ] 21.1 Weight schema integration.
- [ ] 21.2 Loss pipeline.
- [ ] 21.3 Optimizer.
- [ ] 21.4 Reports.
- [ ] 21.5 Candidate validation.
- [ ] Task 21 gate.

## Task 22: Advanced classical terms — NOT STARTED
- [ ] 22.1 Candidate-term protocol.
- [ ] 22.2 Candidate areas.
- [ ] 22.3 Explicit exclusions.
- [ ] Task 22 gate.

## Task 23: Property, fuzz, sanitizer, and robustness gates — NOT STARTED
- [ ] 23.1 Property tests.
- [ ] 23.2 Fuzz targets.
- [ ] 23.3 Runtime analysis.
- [ ] 23.4 Failure preservation.
- [ ] Task 23 gate.

## Task 24: Performance hardening and regression budgets — NOT STARTED
- [ ] 24.1 Baseline benchmark suite.
- [ ] 24.2 Profiling.
- [ ] 24.3 Measurement-justified optimizations.
- [ ] 24.4 Regression policy.
- [ ] 24.5 Android measurements.
- [ ] Task 24 gate.

---

# Task 25: CI, documentation, and developer workflows

**Task status:** Partial.

## 25.1 CI matrix
- [x] Linux debug tests for the Task 1 skeleton.
- [ ] Linux release tests/perft — release build passes; release tests/perft remain future-task work.
- [x] Clippy all targets/features for the Task 1 skeleton.
- [x] rustdoc for the Task 1 skeleton.
- [ ] AArch64 cross-build.
- [ ] Android AArch64 build.
- [ ] JNI smoke/instrumented job.
- [ ] Miri subset.
- [ ] Sanitizer job.
- [ ] Fuzz smoke job.
- [ ] Slow/nightly perft.
- [ ] Optional strength/performance scheduled job.
- [x] Preserve Python validation until migration signoff.
- [x] Separate Python CI and Rust `CI` workflow identities on `master`.
- [x] Add exact-SHA baseline and lockfile artifacts.
- [x] Add deterministic issue-triggered Rust CI dispatch.

## 25.2 Documentation
- [x] Workspace architecture.
- [ ] Coordinate system.
- [ ] Move encoding.
- [ ] Position invariants.
- [ ] Make/unmake.
- [ ] FEN and move notation.
- [ ] Draw semantics.
- [ ] Hashing/repetition.
- [ ] Search and score convention.
- [ ] TT policy.
- [ ] Evaluation terms and weights.
- [ ] UCI usage.
- [ ] C ABI ownership.
- [ ] Android integration.
- [ ] Perft/differential/fuzz commands.
- [ ] Self-play/tuning reproducibility.

## 25.3 Developer commands
- [ ] One bootstrap command.
- [ ] One fast validation command.
- [x] One full validation command.
  - `bash scripts/validate-rust-port-task0-task1.sh`
- [ ] One perft command.
- [ ] One UCI run command.
- [ ] One Android build command.
- [ ] One self-play command.
- [ ] One tuning command.

## 25.4 Generated artifacts
- [ ] Prevent unintended transient benchmark/output commits.
  - **Partial:** `target/` is ignored; CI uploads evidence deliberately; orphaned worktree gitlink cleanup awaits final verification.
- [ ] Version schemas and fixtures intentionally.
- [ ] Document generated Zobrist/book/weight artifacts.

**Task 25 gate:** **OPEN.**

---

# Task 26: v0.1 functional-engine signoff — NOT STARTED
- [ ] 26.1 Rules signoff.
- [ ] 26.2 Search signoff.
- [ ] 26.3 Adapter signoff.
- [ ] 26.4 Quality signoff.
- [ ] 26.5 Evidence report.
- [ ] Task 26 gate.

# Task 27: Full port-program signoff — NOT STARTED
- [ ] 27.1 Optional capability completion.
- [ ] 27.2 Migration decision.
- [ ] 27.3 Final implementation report.
- [ ] 27.4 Final release gate.
- [ ] Task 27 gate.

---

## Immediate next operations

1. Complete removal of the orphaned worktree gitlink.
2. Trigger one uninterrupted exact-head `CI` run through issue dispatch.
3. Verify complete Python slow/perft/UCI evidence.
4. Verify Rust metadata reports `MIT` for all seven packages and checkout cleanup has no first-party warning.
5. Review the final artifacts and status issue.
6. Close Task 0 and Task 1 only after all exact-head evidence is complete.
7. Begin Task 2 after Task 0/1 closure.

---

## Completion-note template

```text
Completion note:
- Commit: <full SHA>
- Files: <key implementation and test paths>
- Commands: <exact commands>
- Results: <exact pass counts/perft/benchmarks>
- Evidence: <artifact paths or CI run URLs>
- Deviations: <spec deviation and rationale, or "none">
- Remaining risks: <known risks, or "none">
```

Do not replace evidence with a narrative assertion that a task is complete.
