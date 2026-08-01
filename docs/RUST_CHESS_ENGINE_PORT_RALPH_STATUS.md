# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 0 and Task 1 CI execution in progress

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

## Current CI execution model

The default branch keeps Python validation in `.github/workflows/python-ci.yml` and registers `.github/workflows/ci.yml` under the exact workflow name `CI`. The status publisher monitors that name and the dispatcher targets `ci.yml` with `ref=rust-engine`.

The `rust-engine` CI workflow performs:

- frozen Python baseline capture, including fast tests, slow tests, perft, and UCI smoke;
- complete Rust workspace metadata, formatting, check, Clippy, test, rustdoc, debug-build, and release-build gates;
- generated `Cargo.lock` artifact upload;
- Python baseline evidence artifact upload.

---

## Task 0 status

**In progress.** Source inventory, decision records, defect exclusions, and capture tooling are complete. Runtime evidence is delegated to the `Python reference baseline` GitHub Actions job.

Task 0 remains open until the current exact-SHA job passes and its evidence artifact is reviewed.

---

## Task 1 status

**Implemented; CI verification in progress.** The seven-crate Cargo workspace, dependency policy, strict warning policy, MIT metadata, architecture documentation, Linux Rust CI, lockfile generation, and artifact upload are present.

Task 1 remains open until the exact candidate SHA passes all Rust steps, the generated `Cargo.lock` is reviewed and committed, and a final exact-SHA CI rerun is green.

---

## Candidate identity rule

The authoritative candidate is always the current `rust-engine` branch head reported by the `CI` workflow and status issue `#1`. Do not copy a provisional or unreferenced Git object SHA into this file.
