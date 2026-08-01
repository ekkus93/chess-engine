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
- A note beginning with **Partial** identifies work that exists but does not yet satisfy the complete wording of the checkbox.
- A task gate stays open until every required action and its exact-SHA validation evidence are complete.
- The full task-definition file preserves every original action item. When an entire subsection below is marked not started, every action item in that subsection remains open.
- Update this file in the same change set, or immediately after it, whenever implementation, testing, CI, documentation, or evidence changes a task or subtask status.

---

## Current task summary

| Task | Status | Current result |
|---:|---|---|
| 0 | **In progress** | Source inventory, decision record, defect record, and capture tooling complete; fresh Python runtime evidence pending. |
| 1 | **Implemented, unverified** | Seven-crate workspace and initial CI are present; Rust execution evidence, `Cargo.lock` review, license decision, and exact-SHA CI remain pending. |
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
| 25 | **Partial** | Workspace architecture documentation and initial Linux Rust CI configuration exist; the full matrix and developer workflow remain open. |
| 26 | **Not started** | v0.1 signoff has not begun. |
| 27 | **Not started** | Full port-program signoff has not begun. |

---

## Program rules — ongoing constraints

These are continuing rules rather than one-time completion items. They remain applicable until final signoff.

- Work only on the `rust-engine` branch unless the user explicitly requests another branch.
- Treat the Rust specification as authoritative for the new implementation.
- Treat Python code and tests as reference material, not as an API-compatibility contract.
- Do not delete or broadly rewrite the Python engine during the port.
- Do not mark a task complete merely because it compiles.
- Add tests with every behavioral implementation task.
- Preserve every discovered rules mismatch as a fixed Rust regression.
- Do not add advanced pruning before reference and baseline alpha-beta paths agree at shallow depths.
- Do not add transcript-specific guidance modules to Rust evaluation or ordering.
- Do not use clone-per-child as production search architecture.
- Do not use string position keys in Rust search or repetition tracking.
- Do not silently load weights, books, or configuration from conventional paths.
- Do not allow Rust panics to cross C or JNI boundaries.
- Record exact commands, results, environment, and commit SHA for every major gate.
- Keep this TODO's task and subtask statuses synchronized with repository reality.

---

# Task 0: Establish the port baseline and decision record

**Task status:** In progress — source-grounded work is complete; runtime evidence is pending.

## 0.1 Preserve the Python baseline

- [x] Record the current `rust-engine` branch SHA before Rust source changes.
  - Frozen baseline: `f743013a84173b551eac5488c638cb48098ec6d0`.
- [ ] Run and record the current fast Python test suite.
- [ ] Run and record the current slow Python test suite when practical.
- [ ] Record current Python perft results and timings for existing exact positions.
- [ ] Record current UCI smoke behavior.
- [x] Record current engine-strength/self-play artifacts useful as historical comparison only.
  - Historical self-play, tuning, Stockfish-annotation, and validation evidence is summarized in the baseline record.

## 0.2 Create a Python-reference inventory

- [x] Inventory Python modules by category:
  - [x] rules and board state;
  - [x] FEN and notation;
  - [x] search;
  - [x] evaluation;
  - [x] opening book;
  - [x] self-play and tuning;
  - [x] UCI;
  - [x] CLI/TUI;
  - [x] transcript-specific guidance.
- [x] Map each retained concept to the relevant Rust milestone.
- [x] Mark excluded modules explicitly so they are not accidentally translated later.

## 0.3 Record known Python defects that Rust must not copy

- [x] Add fixed design notes for:
  - [x] incorrect dead-position and insufficient-material shortcuts;
  - [x] castling transit/destination safety evaluated with the source king still blocking lines;
  - [x] clone-per-child search;
  - [x] string position keys;
  - [x] raw en-passant field included in every repetition key;
  - [x] permissive FEN parsing;
  - [x] implicit queen promotion in core execution;
  - [x] multiple internal move representations;
  - [x] unbounded per-search dictionary TT;
  - [x] missing TT mate-score normalization;
  - [x] root heuristic/tie-break interactions with alpha-beta bounds;
  - [x] automatic tuned-weight file discovery;
  - [x] global UCI control/output state;
  - [x] narrow transcript-driven evaluator and move-ordering patches.

## 0.4 Completion evidence

- [x] Commit the baseline/decision record.
- [x] Record the commit SHA in this task's completion note.
- [x] Do not begin architectural migration by editing Python internals.

### Task 0 completion note — gate still open

- **Baseline commit:** `234e26c1597756aac01ef24b085624c2a834d4e6`
- **Capture-tool commits:**
  - `a579aa28f072934a67df082cbf830ea51831c971`
  - `fba5ca2e0ca6139a943f4018dadb925e2c37a88d`
- **Files:**
  - `docs/RUST_CHESS_ENGINE_PORT_BASELINE_2026-08-01.md`
  - `scripts/capture-rust-port-python-baseline.sh`
- **Commands still required:**

  ```bash
  bash scripts/capture-rust-port-python-baseline.sh
  RUN_SLOW=1 bash scripts/capture-rust-port-python-baseline.sh
  ```

- **Evidence status:** Source inventory and decision evidence complete; runtime evidence not yet captured.
- **Remaining risk:** The current Python reference SHA has not received fresh fast-test, slow-test, timed-perft, and UCI-smoke execution evidence.

**Task 0 gate:** **OPEN.** Do not claim completion until the pending runtime evidence is committed and reviewed.

---

# Task 1: Create the Cargo workspace and dependency boundaries

**Task status:** Implemented but unverified.

## 1.1 Workspace skeleton

- [x] Add root `Cargo.toml` workspace configuration.
- [x] Add crates:
  - [x] `crates/chess-core`;
  - [x] `crates/chess-search`;
  - [x] `crates/chess-uci`;
  - [x] `crates/chess-ffi`;
  - [x] `crates/chess-jni`;
  - [x] `crates/chess-tools`;
  - [x] `crates/chess-tune`.
- [x] Add minimal crate-level documentation describing responsibility and allowed dependencies.
- [ ] Keep optional or future crates buildable even if initially feature-empty.
  - **Partial:** All crate manifests and entry points exist, but successful Cargo builds have not been executed at the current SHA.

## 1.2 Toolchain and policy

- [x] Pin or document the minimum supported Rust version.
  - MSRV: Rust `1.75`.
- [x] Add `rustfmt` and Clippy configuration only where justified.
- [x] Add `#![forbid(unsafe_code)]` to `chess-core` and `chess-search`.
- [x] Add workspace lints and deny warnings in CI.
  - `.github/workflows/ci.yml` runs Clippy with `-D warnings` and rustdoc with `RUSTDOCFLAGS=-D warnings`.
- [ ] Add license and package metadata consistently.
  - **Partial:** Package metadata is inherited consistently and every crate is `publish = false`; the repository owner has not selected or recorded a license.

## 1.3 Architecture enforcement

- [x] Confirm `chess-core` has no dependency on search or adapters.
- [x] Confirm `chess-search` depends only on portable core/support crates.
- [x] Confirm UCI, FFI, JNI, tools, and tuning are outward adapters.
- [x] Add an architecture document or dependency diagram.
  - Evidence: `docs/RUST_WORKSPACE_ARCHITECTURE.md`.

## 1.4 Initial CI

- [x] Add GitHub Actions jobs for formatting, Clippy, tests, and docs.
- [x] Keep existing Python CI intact during the port.
  - Python validation remains on `master`; no Python source or test was removed.
- [x] Add Linux x86-64 debug and release build coverage.
  - The workflow contains debug and release workspace build steps on `ubuntu-24.04`.
- [ ] Add AArch64 and Android compile jobs when toolchains are configured.

### Task 1 completion note — gate still open

- **Implementation range:** `11c7d5d14add069a99cc7347a65e0dd677ab3f37` through `ddb54105aff8ad54c40db436872fceec968bfa06`
- **Status/report commits:**
  - `273b83555c09e6cabea086780be6bc5499646eb2`
  - `4c16e879ec13eff983d86b01defa5129349f82ec`
- **Key files:**
  - `Cargo.toml`
  - `rust-toolchain.toml`
  - `rustfmt.toml`
  - `.github/workflows/ci.yml`
  - `crates/*/Cargo.toml`
  - `crates/*/src/`
  - `docs/RUST_WORKSPACE_ARCHITECTURE.md`
  - `docs/RUST_WORKSPACE_TASK1_VALIDATION_2026-08-01.md`
- **Static result:** Manifest parsing, exact dependency-set checks, unsafe-policy checks, and changed-path audit passed.
- **Dynamic commands still required:**

  ```bash
  cargo fmt --all -- --check
  cargo check --workspace --all-targets --all-features
  cargo clippy --workspace --all-targets --all-features -- -D warnings
  cargo test --workspace --all-features
  RUSTDOCFLAGS="-D warnings" cargo doc --workspace --all-features --no-deps
  cargo build --workspace --all-features
  cargo build --workspace --all-features --release
  ```

- **Remaining risks:**
  - no current-SHA Rust command execution;
  - no reviewed/generated `Cargo.lock`;
  - no recorded license decision;
  - CI issue `#1` does not yet report an exact passing Task 1 SHA;
  - Task 0 runtime evidence remains open.

**Task 1 gate:** **OPEN.** The workspace must pass all dynamic gates at one exact SHA before Task 1 is marked complete.

---

# Tasks 2–24: Implementation status by numbered subtask

Every action item in the full task-definition file remains open unless a partial cross-cutting note is stated below.

## Task 2: Core value types and coordinate contracts — NOT STARTED

- [ ] 2.1 Color and piece types — all action items open.
- [ ] 2.2 Square — all action items open.
- [ ] 2.3 Bitboard — all action items open.
- [ ] 2.4 Move encoding — all action items open.
- [ ] 2.5 Castling rights and counters — all action items open.
- [ ] Task 2 gate.

## Task 3: `Position` and invariants — NOT STARTED

- [ ] 3.1 Hybrid representation — all action items open.
- [ ] 3.2 Constructors — all action items open.
- [ ] 3.3 Accessors and mutation boundary — all action items open.
- [ ] 3.4 Invariant checker — all action items open.
- [ ] 3.5 Equality and clone — all action items open.
- [ ] Task 3 gate.

## Task 4: Strict FEN and UCI move notation — NOT STARTED

- [ ] 4.1 Structured errors — all action items open.
- [ ] 4.2 Strict FEN parser — all action items open.
- [ ] 4.3 Canonical FEN serializer — all action items open.
- [ ] 4.4 UCI move strings — all action items open.
- [ ] 4.5 Property tests — all action items open.
- [ ] Task 4 gate.

## Task 5: Attack-generation infrastructure — NOT STARTED

- [ ] 5.1 Leaper attacks — all action items open.
- [ ] 5.2 Sliding attacks — all action items open.
- [ ] 5.3 Geometric tables — all action items open.
- [ ] 5.4 Position attack queries — all action items open.
- [ ] 5.5 Differential attack fixtures — all action items open.
- [ ] Task 5 gate.

## Task 6: Pseudo-legal move generation — NOT STARTED

- [ ] 6.1 Pawn moves — all action items open.
- [ ] 6.2 Piece moves — all action items open.
- [ ] 6.3 Castling candidates — all action items open.
- [ ] 6.4 Move list — all action items open.
- [ ] 6.5 Tests — all action items open.
- [ ] Task 6 gate.

## Task 7: Complete legal move generation and special rules — NOT STARTED

- [ ] 7.1 King-safety filtering — all action items open.
- [ ] 7.2 Check evasions — all action items open.
- [ ] 7.3 Castling correctness — all action items open.
- [ ] 7.4 En-passant correctness — all action items open.
- [ ] 7.5 Promotion correctness — all action items open.
- [ ] 7.6 Initial legal perft — all action items open.
- [ ] Task 7 gate.

## Task 8: Make/unmake and incremental state — NOT STARTED

- [ ] 8.1 Undo structure — all action items open.
- [ ] 8.2 Move application paths — all action items open.
- [ ] 8.3 Restoration tests — all action items open.
- [ ] 8.4 Sequence restoration — all action items open.
- [ ] Task 8 gate.

## Task 9: Zobrist hashing and canonical repetition identity — NOT STARTED

- [ ] 9.1 Zobrist tables — all action items open.
- [ ] 9.2 Full hash computation — all action items open.
- [ ] 9.3 Incremental updates — all action items open.
- [ ] 9.4 Canonical en-passant identity — all action items open.
- [ ] 9.5 Hash verification — all action items open.
- [ ] Task 9 gate.

## Task 10: `Game`, repetition history, and draw semantics — NOT STARTED

- [ ] 10.1 `Game` state — all action items open.
- [ ] 10.2 Mate and stalemate — all action items open.
- [ ] 10.3 Claimable draws — all action items open.
- [ ] 10.4 Automatic draws — all action items open.
- [ ] 10.5 Conservative dead-position logic — all action items open.
- [ ] 10.6 Search-facing history — all action items open.
- [ ] Task 10 gate.

## Task 11: Authoritative perft and differential validation — NOT STARTED

- [ ] 11.1 Standard exact perft suite — all action items open.
- [ ] 11.2 Slow perft — all action items open.
- [ ] 11.3 Divide tool — all action items open.
- [ ] 11.4 Differential oracle harness — all action items open.
- [ ] 11.5 Corpus gate — all action items open.
- [ ] Task 11 gate.

## Task 12: Baseline evaluator and trace — NOT STARTED

- [ ] 12.1 Evaluation score convention — all action items open.
- [ ] 12.2 Baseline terms — all action items open.
- [ ] 12.3 Evaluation efficiency — all action items open.
- [ ] 12.4 Evaluation trace — all action items open.
- [ ] 12.5 Named weight schema — all action items open.
- [ ] 12.6 Exclusion audit — all action items open.
- [ ] Task 12 gate.

## Task 13: Reference search and negamax alpha-beta — NOT STARTED

- [ ] 13.1 Reference search — all action items open.
- [ ] 13.2 Negamax alpha-beta — all action items open.
- [ ] 13.3 Equivalence tests — all action items open.
- [ ] 13.4 Search immutability — all action items open.
- [ ] 13.5 Terminal fixtures — all action items open.
- [ ] Task 13 gate.

## Task 14: Quiescence and principled move ordering — NOT STARTED

- [ ] 14.1 Quiescence — all action items open.
- [ ] 14.2 Tactical ordering — all action items open.
- [ ] 14.3 Quiet ordering — all action items open.
- [ ] 14.4 Correctness tests — all action items open.
- [ ] 14.5 Explicit exclusions — all action items open.
- [ ] Task 14 gate.

## Task 15: Fixed-capacity transposition table — NOT STARTED

- [ ] 15.1 Entry design — all action items open.
- [ ] 15.2 Storage layout — all action items open.
- [ ] 15.3 Mate normalization — all action items open.
- [ ] 15.4 Probe semantics — all action items open.
- [ ] 15.5 Replacement policy — all action items open.
- [ ] 15.6 Diagnostics and benchmarks — all action items open.
- [ ] Task 15 gate.

## Task 16: Iterative deepening, PV, limits, and cancellation — NOT STARTED

- [ ] 16.1 Iterative deepening — all action items open.
- [ ] 16.2 Aspiration windows — all action items open.
- [ ] 16.3 Principal variation — all action items open.
- [ ] 16.4 Search limits — all action items open.
- [ ] 16.5 Responsive cancellation — all action items open.
- [ ] 16.6 Search result API — all action items open.
- [ ] 16.7 Optional check extension — all action items open.
- [ ] Task 16 gate.

## Task 17: Linux UCI executable — NOT STARTED

- [ ] 17.1 Protocol loop — all behavioral action items open.
- [ ] 17.2 UCI search worker — all action items open.
- [ ] 17.3 Time manager — all action items open.
- [ ] 17.4 Output — all action items open.
- [ ] 17.5 Integration tests — all action items open.
- [ ] Task 17 gate.

**Note:** The `chess-uci` crate placeholder exists under Task 1, but no Task 17 behavior is implemented.

## Task 18: Safe API, C ABI, and Android JNI adapter — NOT STARTED

- [ ] 18.1 Safe Rust facade — all action items open.
- [ ] 18.2 C ABI — all action items open.
- [ ] 18.3 C ABI tests — all action items open.
- [ ] 18.4 Android JNI — all action items open.
- [ ] 18.5 Android test harness — all action items open.
- [ ] Task 18 gate.

**Note:** The `chess-ffi` and `chess-jni` crate placeholders exist under Task 1, but no Task 18 ABI/JNI behavior is implemented.

## Task 19: Optional opening-book infrastructure — NOT STARTED

- [ ] 19.1 Core abstraction — all action items open.
- [ ] 19.2 Backend format — all action items open.
- [ ] 19.3 Selection policies — all action items open.
- [ ] 19.4 Adapter integration — all action items open.
- [ ] 19.5 Tests — all action items open.
- [ ] Task 19 gate.

## Task 20: Self-play and versioned dataset tooling — NOT STARTED

- [ ] 20.1 Self-play configuration — all action items open.
- [ ] 20.2 Game records — all action items open.
- [ ] 20.3 Position dataset schema — all action items open.
- [ ] 20.4 Data quality — all action items open.
- [ ] Task 20 gate.

## Task 21: Named-schema Texel-style tuning — NOT STARTED

- [ ] 21.1 Weight schema integration — all action items open.
- [ ] 21.2 Loss pipeline — all action items open.
- [ ] 21.3 Optimizer — all action items open.
- [ ] 21.4 Reports — all action items open.
- [ ] 21.5 Candidate validation — all action items open.
- [ ] Task 21 gate.

## Task 22: Advanced classical terms — NOT STARTED

- [ ] 22.1 Candidate-term protocol — all action items open.
- [ ] 22.2 Candidate areas — all action items open.
- [ ] 22.3 Explicit exclusions — all action items open.
- [ ] Task 22 gate.

## Task 23: Property testing, fuzzing, sanitizers, and robustness — NOT STARTED

- [ ] 23.1 Property tests — all action items open.
- [ ] 23.2 Fuzz targets — all action items open.
- [ ] 23.3 Runtime analysis — all action items open.
- [ ] 23.4 Failure preservation — all action items open.
- [ ] Task 23 gate.

## Task 24: Performance hardening and regression budgets — NOT STARTED

- [ ] 24.1 Baseline benchmark suite — all action items open.
- [ ] 24.2 Profiling — all action items open.
- [ ] 24.3 Optimizations after measurement — all action items open.
- [ ] 24.4 Regression policy — all action items open.
- [ ] 24.5 Android measurements — all action items open.
- [ ] Task 24 gate.

---

# Task 25: Complete CI, documentation, and developer workflows

**Task status:** Partial — initial Linux CI and workspace architecture documentation exist.

## 25.1 CI matrix

- [ ] Linux debug tests.
  - **Partial:** A debug `cargo test --workspace --all-features` step is configured but has not passed at the current SHA.
- [ ] Linux release tests/perft.
  - **Partial:** Release workspace build is configured; release tests/perft are not configured or verified.
- [ ] Clippy all targets/features.
  - **Partial:** Configured with `-D warnings`; not yet verified at the current SHA.
- [ ] rustdoc.
  - **Partial:** Configured with `RUSTDOCFLAGS=-D warnings`; not yet verified at the current SHA.
- [ ] AArch64 cross-build.
- [ ] Android AArch64 build.
- [ ] JNI smoke/instrumented job where infrastructure supports it.
- [ ] Miri subset.
- [ ] sanitizer job.
- [ ] fuzz smoke job.
- [ ] slow/nightly perft.
- [ ] optional strength/performance scheduled job.
- [x] keep Python validation until migration signoff.
  - Python implementation, tests, and master-branch validation remain preserved.

## 25.2 Documentation

- [x] workspace architecture.
  - Evidence: `docs/RUST_WORKSPACE_ARCHITECTURE.md`.
- [ ] coordinate system.
- [ ] move encoding.
- [ ] position invariants.
- [ ] make/unmake.
- [ ] FEN and move notation.
- [ ] draw semantics.
- [ ] hashing/repetition.
- [ ] search and score convention.
- [ ] TT policy.
- [ ] evaluation terms and weights.
- [ ] UCI usage.
- [ ] C ABI ownership.
- [ ] Android integration.
- [ ] perft/differential/fuzz commands.
- [ ] self-play/tuning reproducibility.

## 25.3 Developer commands

- [ ] One documented bootstrap command.
- [ ] One fast validation command.
- [ ] One full validation command.
- [ ] One perft command.
- [ ] One UCI run command.
- [ ] One Android build command.
- [ ] One self-play command.
- [ ] One tuning command.

## 25.4 Generated artifacts

- [ ] Do not commit transient benchmark/output files unintentionally.
  - **Partial:** Cargo `target/` is ignored; the full generated-artifact policy is not complete.
- [ ] Version schemas and fixtures intentionally.
- [ ] Document generated Zobrist/book/weight artifacts.

**Task 25 gate:** **OPEN.** Initial foundations exist, but the complete matrix, documentation set, and developer workflow do not.

---

# Task 26: v0.1 functional-engine signoff — NOT STARTED

- [ ] 26.1 Rules signoff — all action items open.
- [ ] 26.2 Search signoff — all action items open.
- [ ] 26.3 Adapter signoff — all action items open.
- [ ] 26.4 Quality signoff — all action items open.
- [ ] 26.5 Evidence report — all action items open.
- [ ] Task 26 gate.

# Task 27: Full port-program signoff — NOT STARTED

- [ ] 27.1 Optional capability completion — all action items open.
- [ ] 27.2 Migration decision — all action items open.
- [ ] 27.3 Final implementation report — all action items open.
- [ ] 27.4 Final release gate — all action items open.
- [ ] Task 27 gate.

---

## Immediate next operations

1. Capture Task 0 runtime evidence from a clean runnable `rust-engine` checkout.
2. Run the complete Task 1 Rust command sequence.
3. Fix every first-party warning or failure at its source.
4. Review and commit `Cargo.lock` if generated.
5. Record the repository license decision.
6. Verify the CI status issue reports the exact candidate SHA.
7. Update every affected checkbox and completion note in this file.
8. Close Task 0 and Task 1 only after their gates pass.
9. Begin Task 2 only after the dependency gates are satisfied or an explicit exception is recorded.

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
