# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 0 and Task 1 CI execution in progress  
**Latest repository snapshot before this status update:** `bec4666e7c06689346e3df53b7cf6d5850f5e626`

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

The default branch now keeps Python validation in `.github/workflows/python-ci.yml` and registers `.github/workflows/ci.yml` under the exact workflow name `CI`. The status publisher monitors that name and the persistent dispatcher targets `ci.yml` with `ref=rust-engine`.

The `rust-engine` CI workflow now performs:

- frozen Python baseline capture, including fast tests, slow tests, perft, and UCI smoke;
- complete Rust workspace metadata, formatting, check, Clippy, test, rustdoc, debug-build, and release-build gates;
- generated `Cargo.lock` artifact upload;
- Python baseline evidence artifact upload.

---

## Task 0 status

**In progress.** Source inventory, decision records, defect exclusions, and capture tooling are complete. Runtime evidence is now delegated to the `Python reference baseline` GitHub Actions job.

Task 0 remains open until the current exact-SHA job passes and its evidence artifact is reviewed.

---

## Task 1 status

**Implemented; CI verification in progress.** The seven-crate Cargo workspace, dependency policy, strict warning policy, MIT metadata, architecture documentation, Linux Rust CI, lockfile generation, and artifact upload are present.

Task 1 remains open until the exact candidate SHA passes all Rust steps, the generated `Cargo.lock` is reviewed and committed, and a final exact-SHA CI rerun is green.

---

## Current candidate

```text
bec4666e7c06689346e3df53b7cf6d5850f5e626
```

This commit is intended to trigger the first complete Task 0/1 GitHub Actions validation after repairing the default-branch workflow identity and dispatcher infrastructure.
