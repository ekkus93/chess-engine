# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Final Task 0 and Task 1 exact-head validation pending

---

## Operating rules

- Work directly on `rust-engine`.
- Do not create branches or pull requests without explicit user instruction.
- Every first-party compiler, Clippy, rustdoc, formatting, lint, and test finding is a bug.
- Fix first-party findings at their source; do not hide, suppress, downgrade, ignore, or filter them.
- Third-party, dependency, generated-vendor, and vendored-code warnings are outside the first-party rule unless caused by this repository's integration code.
- Keep the authoritative TODO synchronized with repository reality.
- Use GitHub Actions as the authoritative Rust execution environment.
- Commit each fix directly to `rust-engine`, inspect CI feedback, and repeat until the exact SHA is green.

---

## First CI evidence

Run `30719636049` validated candidate `edd5a94685d23a04df15c69dafed5f077fd3fc74`.

- Rust job `91421155314`: all metadata, formatting, check, Clippy, tests, rustdoc, debug build, release build, and lockfile artifact steps passed on Rust 1.97.1 / Ubuntu 24.04.4.
- Python job `91421155337`: source equivalence, environment capture, dependency sync, and fast suite passed (`1203 passed, 179 deselected in 44.43s`); the slow suite was cancelled by newer branch commits before perft and UCI.
- Reviewed artifacts:
  - Python partial evidence: `8824498772`.
  - Cargo lockfile: `8824440027`.

The full Rust log exposed two first-party repository findings that step summaries did not fail:

- member manifests did not inherit `workspace.package.license`, so Cargo metadata reported `license: null`;
- an orphaned `.claude/worktrees/agent-a04f1cae54e4430d6` gitlink caused checkout cleanup to report a missing `.gitmodules` URL.

The member manifests now use `license.workspace = true`, and the CI-generated `Cargo.lock` is committed. The orphaned gitlink removal is the final tree correction before the exact-head run.

---

## Task status

- **Task 0:** Open pending complete slow-suite, perft, UCI, and final artifact evidence.
- **Task 1:** Open pending exact-head verification of MIT metadata, clean checkout cleanup, and all Rust gates with committed `Cargo.lock`.
- **Task 2:** Not started.

---

## Candidate identity rule

The authoritative candidate is always the current `rust-engine` branch head reported by the `CI` workflow and status issue `#1`. Do not copy a provisional or unreferenced Git object SHA into this file.
