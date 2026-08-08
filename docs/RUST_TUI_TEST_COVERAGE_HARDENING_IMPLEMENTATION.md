# Rust TUI Test Coverage Hardening Implementation Report

Status: complete — targeted Rust TUI hardening and diagnostic coverage integration validated.

Companion specification: `docs/RUST_TUI_TEST_COVERAGE_HARDENING_SPEC.md`
Completed TODO: `docs/RUST_TUI_TEST_COVERAGE_HARDENING_TODO.md`

## Scope and invariants

This program added deterministic tests and `cargo llvm-cov` evidence around the Rust TUI without changing chess rules, search strength, evaluation weights, tuning state, promotion disposition, opening-book policy, or the underlying search engine. The TUI remains fail-closed: an emergency/fallback-only search result is rejected visibly and never converted into a playable move.

## Implementation summary

- Added `scripts/tui_coverage.sh` with clean, human-summary, JSON-summary, LCOV, and HTML commands.
- Added permanent `.github/workflows/tui-coverage.yml`, pinned to `cargo-llvm-cov 0.8.7`, with a stable coverage host and separate Rust 1.75 compatibility job.
- Extracted a pure internal search-result classifier so fallback-only disposition is deterministic and directly testable while the runtime remains hard-wired to `SearchWorker::spawn`.
- Added direct runtime lifecycle tests for progress, final events, disconnect/no-final behavior, cancellation, spawn failure, worker panic, application errors, and legitimate next-search ownership.
- Added direct keyboard/overlay/menu/move-entry/self-play/Ctrl-C state-machine tests.
- Added defensive `AppState`, terminal-result, automatic/claimable draw, serialization, save transaction, rendering, metrics, and layout-boundary coverage.
- Added only test-scoped worker constructors for deterministic lifecycle injection; no runtime-selectable alternate engine/factory exists.
- Fixed two defects discovered by the tests: Ctrl/Alt-modified printable key filtering and wrapping of the too-small-terminal diagnostic.

## Coverage evidence

Baseline (`22df3480227c3f0938768b70f8d2594f9881b9f5`, run `31276416088`, job `93150555283`):

| Metric | Baseline | Final focused | Delta |
|---|---:|---:|---:|
| Regions | 62.09% | 87.77% | +25.68 pp |
| Functions | 57.14% | 85.38% | +28.24 pp |
| Lines | 61.25% | 89.26% | +28.01 pp |
| `ui.rs` lines | 36.42% | 86.14% | +49.72 pp |

Final focused checklist validation was run `31277368933`, job `93153050871`, against the TUI source/test state published at `2acd49c16267e6bc7e1e38cd2626dfed70f311ac`. No low-coverage production files were excluded to improve the totals.

The permanent workflow was separately exercised on SHA `a4f7b4e82112117320362d8de4305e4481ae7466`: run `31277523302`, coverage job `93153454991`, Rust 1.75 job `93153454992`, artifact `9027442509`. Text, JSON, LCOV, and HTML reports were all generated successfully.

## Residual coverage dispositions

`main.rs` / `TerminalGuard` remains at 0% in unit-level llvm-cov. This is intentional. Terminal mode and alternate-screen lifecycle are concrete TTY side effects; adding a production `TerminalOps` abstraction solely to increase line coverage would add more surface area than confidence. PTY run `31227882334` / job `93025710323` remains the stronger evidence for real launch/quit restoration. Explicit `restore()` errors are returned on the normal path; the destructor remains best-effort because Rust destructors cannot return failures.

A real permission-denied save fixture is also intentionally not forced under privileged CI. Deterministic write-failure tests exercise the same visible failure transaction via `NotFound`, including clearing stale `saved_path` and never emitting success.

## Safety/fallback audit

The implementation contains no TUI first-legal fallback, random fallback, silent depth reduction, alternate search-policy replacement, or Python-engine fallback. `chess-search` itself was not modified. `chess-core`, `chess-book`, and `chess-uci` production behavior were not modified by this hardening program.

## Authority disposition

This hardening TODO is complete and becomes historical. `docs/RUST_TUI_TODO.md` remains the active Rust TUI authority because its manual real-terminal acceptance checklist is intentionally independent and remains open. Final permanent exact-repository-SHA CI/Robustness/coverage run IDs are reported after the closure commit rather than committed back into the repository, which avoids creating an endless evidence-SHA cycle.
