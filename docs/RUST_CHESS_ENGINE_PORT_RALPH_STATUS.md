# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 0 evidence blocked; Task 1 implemented but unverified  
**Latest implementation snapshot before this status update:** `273b83555c09e6cabea086780be6bc5499646eb2`

---

## Operating rules

- Work directly on `rust-engine`.
- Do not create branches or pull requests without explicit user instruction.
- Treat every warning or lint finding in first-party code as a bug.
- Fix first-party warnings at their source; do not hide, suppress, downgrade, or filter them.
- Third-party, dependency, generated-vendor, and vendored-code warnings are outside the first-party rule unless caused by this project's integration code.
- Follow the TODO in dependency order.
- Do not mark a task complete merely because code compiles.
- Do not invent runtime evidence or weaken a gate because the current environment cannot execute it.

---

## Task 0 — baseline and decision record

### Source-grounded work completed

- Frozen the pre-Rust-source baseline at:

  ```text
  f743013a84173b551eac5488c638cb48098ec6d0
  ```

- Created:

  ```text
  docs/RUST_CHESS_ENGINE_PORT_BASELINE_2026-08-01.md
  scripts/capture-rust-port-python-baseline.sh
  ```

- Inventoried Python rules, FEN/notation, search, evaluation, opening book, self-play/tuning, UCI, CLI/TUI, and transcript-specific guidance.
- Mapped retained concepts to Rust milestones.
- Explicitly excluded unsuitable architecture and narrow transcript-driven modules.
- Recorded all fourteen known Python defect/non-copy classes as Rust design constraints.
- Added a fail-loud evidence script that rejects:
  - dirty worktrees;
  - branches other than `rust-engine`;
  - non-descendants of the frozen baseline;
  - changes to `chess_game/`, `tests/`, `pyproject.toml`, or `uv.lock` relative to the frozen baseline.
- Did not modify Python implementation or tests.

### Task 0 commits

```text
234e26c1597756aac01ef24b085624c2a834d4e6  docs: establish Rust port baseline and decision record
a579aa28f072934a67df082cbf830ea51831c971  tools: add reproducible Python baseline capture
fba5ca2e0ca6139a943f4018dadb925e2c37a88d  fix: validate Python baseline by source equivalence
fcbb5930306e9957c9bdbed45aa3ea6f9b9a6c04  docs: record Rust port Ralph Loop status
```

### Task 0 gate

**Open.** Fresh execution evidence is still required for:

- fast Python tests;
- slow Python tests when practical;
- starting-position perft counts and timings;
- UCI smoke behavior.

Run from a clean local checkout:

```bash
git switch rust-engine
git pull --ff-only
bash scripts/capture-rust-port-python-baseline.sh
```

Include the expensive suite with:

```bash
RUN_SLOW=1 bash scripts/capture-rust-port-python-baseline.sh
```

The current connector environment cannot clone or execute the repository, and connector-authored commits do not initiate ordinary push-triggered Actions runs. No runtime result has been inferred.

---

## Task 1 — Cargo workspace and dependency boundaries

The TODO permits later tasks to be prototyped before prerequisite gates close, provided they are not declared complete. Task 1 was therefore implemented after Task 0 source analysis, but its gate remains open.

### Implemented

- Root `Cargo.toml` workspace with seven members:
  - `chess-core`;
  - `chess-search`;
  - `chess-uci`;
  - `chess-ffi`;
  - `chess-jni`;
  - `chess-tools`;
  - `chess-tune`.
- Rust 2021 edition.
- Minimum supported Rust version 1.75.
- Stable local toolchain declaration with `rustfmt` and Clippy.
- Workspace warning and Clippy policy:

  ```toml
  [workspace.lints.rust]
  warnings = "deny"
  unsafe_op_in_unsafe_fn = "deny"

  [workspace.lints.clippy]
  all = "deny"
  ```

- `#![forbid(unsafe_code)]` in `chess-core` and `chess-search`.
- Crate-level rustdoc describing each responsibility and boundary.
- Architecture and dependency document:

  ```text
  docs/RUST_WORKSPACE_ARCHITECTURE.md
  ```

- Validation report:

  ```text
  docs/RUST_WORKSPACE_TASK1_VALIDATION_2026-08-01.md
  ```

- `target/` ignored in `.gitignore`.
- No lint suppression attributes in the new Rust source.
- No chess behavior or premature external ABI was introduced.

### Dependency graph

```text
chess-core
    ^
    |
chess-search
    ^       ^        ^
    |       |        |
chess-uci chess-ffi chess-tools
              ^       ^
              |       |
          chess-jni chess-tune
```

`chess-tools` and `chess-tune` also depend directly on `chess-core`.

Static TOML and dependency-policy validation passed in a local staging tree. Comparing Task 1's starting point with repository snapshot `ddb54105aff8ad54c40db436872fceec968bfa06` showed exactly the intended 19 paths and no Python source/test changes.

### Task 1 dynamic gate

**Open.** The current local execution environment has no Rust toolchain and cannot download one because outbound DNS is unavailable. The following commands have not been represented as passing:

```bash
cargo fmt --all -- --check
cargo check --workspace --all-targets --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo test --workspace --all-features
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --all-features --no-deps
cargo build --workspace --all-features
cargo build --workspace --all-features --release
```

The gate also retains one owner decision: the repository has no top-level license file. All crates are `publish = false`; no license was guessed or asserted.

Task 1 may be marked complete only when:

1. Task 0 evidence is recorded or explicitly dispositioned;
2. all dynamic Rust commands pass at one exact SHA with no first-party warnings;
3. any generated `Cargo.lock` is reviewed and committed;
4. the license decision is recorded;
5. issue `#1` reports the same exact passing SHA;
6. the authoritative TODO receives its completion note.

---

## Current stop point

Task 2 has **not** started.

The next corrective loop is evidence-driven:

1. execute the Task 0 capture script in a runnable checkout;
2. run the Task 1 Rust command sequence;
3. fix every first-party warning or failure at its source;
4. rerun the complete sequence;
5. commit `Cargo.lock` if generated;
6. verify CI issue `#1` matches the exact candidate SHA;
7. close Task 0 and Task 1 in the authoritative TODO;
8. begin Task 2 only after those gates are satisfied.

No branch or pull request was created.
