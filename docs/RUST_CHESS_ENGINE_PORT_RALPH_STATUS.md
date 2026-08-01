# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 0 — runtime evidence pending  
**Current branch head before this status commit:** `fba5ca2e0ca6139a943f4018dadb925e2c37a88d`

---

## Operating rules

- Work directly on `rust-engine`.
- Do not create branches or pull requests without explicit user instruction.
- Treat every warning or lint finding in first-party code as a bug.
- Fix first-party warnings at their source; do not hide, suppress, downgrade, or filter them.
- Third-party, dependency, generated-vendor, and vendored-code warnings are outside the first-party rule unless caused by this project's integration code.
- Follow the TODO in dependency order.
- Do not mark a gate complete merely because code compiles.
- Do not advance past a blocked gate by inventing evidence or weakening the gate.

---

## Iteration 1 result

### Completed

- Frozen the pre-Rust-source baseline at:

  ```text
  f743013a84173b551eac5488c638cb48098ec6d0
  ```

- Verified that the baseline SHA and the then-current `rust-engine` ref were identical.
- Created the comprehensive source inventory and non-copy decision record:

  ```text
  docs/RUST_CHESS_ENGINE_PORT_BASELINE_2026-08-01.md
  ```

- Inventoried the required Python areas:
  - rules and board state;
  - FEN and notation;
  - search;
  - evaluation;
  - opening book;
  - self-play and tuning;
  - UCI;
  - CLI/TUI;
  - transcript-specific guidance.
- Mapped retained concepts to Rust milestones.
- Explicitly excluded the Python architecture and narrow heuristic modules that must not be translated.
- Recorded all fourteen Task 0.3 defect classes as fixed Rust design constraints.
- Added a reproducible, fail-loud local capture tool:

  ```text
  scripts/capture-rust-port-python-baseline.sh
  ```

- Corrected the capture tool so later documentation and tooling commits are allowed while the executable Python baseline is required to remain byte-identical to the frozen SHA across:
  - `chess_game/`;
  - `tests/`;
  - `pyproject.toml`;
  - `uv.lock`.
- Compared the frozen SHA with the current branch and confirmed that only the baseline document and capture script were added. No Python source, Python tests, dependency declaration, or lockfile changed.
- Did not modify Python engine internals.
- Did not create a branch or pull request.

### Commits

```text
234e26c1597756aac01ef24b085624c2a834d4e6  docs: establish Rust port baseline and decision record
a579aa28f072934a67df082cbf830ea51831c971  tools: add reproducible Python baseline capture
fba5ca2e0ca6139a943f4018dadb925e2c37a88d  fix: validate Python baseline by source equivalence
```

### Gate status

Task 0 remains **open**.

The source-analysis portions are complete, but these required execution results have not been freshly captured:

- fast Python test suite;
- slow Python test suite when practical;
- starting-position perft counts and timings;
- UCI smoke transcript.

The current execution environment can read and write the repository through the GitHub connector, but cannot clone or execute it locally. Connector-authored commits also do not initiate ordinary push-triggered Actions runs. No runtime result has therefore been inferred or fabricated.

---

## Next exact operation

From a clean local checkout of `rust-engine` with `uv` installed:

```bash
git switch rust-engine
git pull --ff-only
bash scripts/capture-rust-port-python-baseline.sh
```

To include the expensive slow suite in the same capture:

```bash
RUN_SLOW=1 bash scripts/capture-rust-port-python-baseline.sh
```

Historical Python lint evidence is optional because Python lint is no longer an authoritative `rust-engine` CI gate. To capture it deliberately:

```bash
RUN_PYTHON_LINT=1 bash scripts/capture-rust-port-python-baseline.sh
```

The script will:

1. reject a dirty worktree;
2. reject any branch other than `rust-engine`;
3. verify ancestry from the frozen baseline;
4. reject changes to the frozen Python source/test/dependency inputs;
5. synchronize the Python environment;
6. execute the selected suites;
7. validate exact starting-position perft depths 1 through 4;
8. validate a UCI handshake and depth-1 search;
9. write structured evidence under `artifacts/rust-port-python-baseline/<capture-sha>/`;
10. return a nonzero status when any required gate fails.

Review all generated evidence before committing it. Do not commit virtual environments, caches, secrets, or unrelated generated files.

---

## Advancement rule

Do not begin Task 1 until Task 0 runtime evidence is committed and the Task 0 gate is explicitly closed in the authoritative TODO.

After Task 0 closes, the next work is Task 1: create the Cargo workspace and dependency boundaries. The existing Rust-only `CI` workflow will then become executable instead of failing at the intentional `Verify Cargo workspace` precondition.
