from pathlib import Path

TODO = Path("docs/RUST_TUI_TEST_COVERAGE_HARDENING_TODO.md")
INDEX = Path("docs/LEGACY_TODO_INDEX.md")
AUDIT = Path("scripts/task_post_port_review_fix_audit.sh")
REPORT = Path("docs/RUST_TUI_TEST_COVERAGE_HARDENING_IMPLEMENTATION.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}: {old!r}")
    return text.replace(old, new, 1)


todo = TODO.read_text()
todo = replace_once(
    todo,
    "Status: active implementation plan; not yet implemented.",
    "Status: complete — Rust TUI test/coverage hardening validated; coverage remains diagnostic and no engine/search/evaluation/tuning behavior changed.",
    "TODO status",
)
todo = replace_once(
    todo,
    "Starting baseline SHA: `1c83c40ff33fb77e9f19f6873b33561af64c9199`",
    "Starting baseline SHA: `1c83c40ff33fb77e9f19f6873b33561af64c9199`\n\nImplementation Ralph-loop start SHA: `e03f7cecba304571e0bc523c3991e93b85c079da`\n\nTUI implementation/test source SHA: `2acd49c16267e6bc7e1e38cd2626dfed70f311ac`",
    "TODO SHA header",
)
# The original illustrative command used --summary-only without an export format.
# The permanent helper uses the supported human-summary invocation instead.
todo = todo.replace(
    "cargo llvm-cov -p chess-tui --all-features --summary-only",
    "bash scripts/tui_coverage.sh summary",
)
todo = todo.replace(
    "cargo llvm-cov -p chess-tui --all-features --lcov --output-path target/chess-tui-lcov.info",
    "bash scripts/tui_coverage.sh lcov",
)
# Every remaining checkbox has either direct evidence or an explicit N/A/disposition below.
todo = todo.replace("- [ ]", "- [x]")
todo = replace_once(
    todo,
    "If a terminal-operations seam is introduced:\n",
    "If a terminal-operations seam is introduced:\n\n> **Disposition:** no terminal-operations seam was introduced. The checkmarks in this conditional subsection record review/disposition, not synthetic execution of an unused abstraction. Production remains directly wired to Crossterm/stdout.\n\n",
    "terminal conditional disposition",
)
closure_evidence = '''## Closure evidence\n\n- Actual implementation-loop start: `e03f7cecba304571e0bc523c3991e93b85c079da`. The older `1c83c40...` field above is retained as the planning/baseline repository identity from the document's creation history.\n- Baseline focused coverage source: `22df3480227c3f0938768b70f8d2594f9881b9f5`; permanent coverage run `31276416088`, job `93150555283`, artifact `9027129674` (`chess-tui-coverage-22df3480227c3f0938768b70f8d2594f9881b9f5`). Toolchain: rustc/cargo 1.97.1, LLVM 22.1.6, `cargo-llvm-cov 0.8.7`. Baseline totals: 62.09% regions, 57.14% functions, 61.25% lines; `ui.rs` line coverage was 36.42%.\n- Primary hardening source commit: `d0e7a28374d9b3465c68b16782655f5248846f27`. Final TUI source/test refinement commit: `2acd49c16267e6bc7e1e38cd2626dfed70f311ac`.\n- Focused final checklist validation: run `31277368933`, job `93153050871`. It passed 86/86 `chess-tui` library tests plus all integration targets, strict Clippy, Rust 1.75 compatibility, summary/JSON/LCOV/HTML coverage generation, bounded-diff verification, and the TODO-authority audit.\n- Final focused coverage totals from that run: 87.77% regions, 85.38% functions, 89.26% lines. Module line coverage: `app.rs` 95.71%, `render.rs` 96.73%, `save.rs` 100%, `ui.rs` 86.14%, `worker.rs` 90.00%, `main.rs` 0%. The comparable deltas are +25.68 region points, +28.24 function points, +28.01 line points; `ui.rs` gained +49.72 line points. No production source exclusions were added.\n- Permanent coverage infrastructure pre-closure proof: SHA `a4f7b4e82112117320362d8de4305e4481ae7466`, run `31277523302`; coverage job `93153454991` and Rust 1.75 MSRV job `93153454992` both succeeded. Artifact `9027442509`, `chess-tui-coverage-a4f7b4e82112117320362d8de4305e4481ae7466`, contains text, JSON, LCOV, and HTML evidence.\n- **Fallback disposition:** the TUI directly classifies a fallback-only result as `Failed`; the deterministic `fallback_only_result_is_rejected_by_tui` test covers this branch. Cancellation/discard remains earlier and cannot turn into `Completed`. No first-legal, random, lower-depth, alternate-engine, or Python fallback was added.\n- **TerminalGuard disposition:** `main.rs` remains uncovered by unit-level llvm-cov because real Crossterm/stdout lifecycle behavior is better evidenced by PTY integration than by a production abstraction added solely for coverage. Existing PTY run `31227882334`, job `93025710323`, proved alternate-screen enter/leave and clean launch/quit restoration. Explicit normal-path restoration errors remain returned; only `Drop` is best-effort by necessity.\n- **Permission-denied save disposition:** root/CI privilege semantics make a real `PermissionDenied` fixture nonportable. The same UI error mapping is deterministically exercised through a `NotFound` write failure, stale saved state is cleared, no success message is emitted, and real permission/read-only behavior remains part of manual terminal/filesystem acceptance. No filesystem mock layer was introduced merely to move coverage.\n- Two real UI defects were found by this hardening work and fixed: control/Alt-modified printable keys could enter save-path input, and the too-small-terminal message could clip its current-dimension suffix because it did not wrap.\n- The original `docs/RUST_TUI_TODO.md` manual real-terminal acceptance items remain independent and open; this hardening closure does not claim them.\n- Permanent exact-final-repository-SHA run IDs are intentionally recorded out-of-band after the closure/bookkeeping commit, avoiding evidence-recursion commits whose only purpose would be to change the SHA being evidenced.\n\n'''
todo = replace_once(todo, "## Recommended test names\n", closure_evidence + "## Recommended test names\n", "closure evidence insertion")
TODO.write_text(todo)

report = '''# Rust TUI Test Coverage Hardening Implementation Report\n\nStatus: complete — targeted Rust TUI hardening and diagnostic coverage integration validated.\n\nCompanion specification: `docs/RUST_TUI_TEST_COVERAGE_HARDENING_SPEC.md`  \nCompleted TODO: `docs/RUST_TUI_TEST_COVERAGE_HARDENING_TODO.md`\n\n## Scope and invariants\n\nThis program added deterministic tests and `cargo llvm-cov` evidence around the Rust TUI without changing chess rules, search strength, evaluation weights, tuning state, promotion disposition, opening-book policy, or the underlying search engine. The TUI remains fail-closed: an emergency/fallback-only search result is rejected visibly and never converted into a playable move.\n\n## Implementation summary\n\n- Added `scripts/tui_coverage.sh` with clean, human-summary, JSON-summary, LCOV, and HTML commands.\n- Added permanent `.github/workflows/tui-coverage.yml`, pinned to `cargo-llvm-cov 0.8.7`, with a stable coverage host and separate Rust 1.75 compatibility job.\n- Extracted a pure internal search-result classifier so fallback-only disposition is deterministic and directly testable while the runtime remains hard-wired to `SearchWorker::spawn`.\n- Added direct runtime lifecycle tests for progress, final events, disconnect/no-final behavior, cancellation, spawn failure, worker panic, application errors, and legitimate next-search ownership.\n- Added direct keyboard/overlay/menu/move-entry/self-play/Ctrl-C state-machine tests.\n- Added defensive `AppState`, terminal-result, automatic/claimable draw, serialization, save transaction, rendering, metrics, and layout-boundary coverage.\n- Added only test-scoped worker constructors for deterministic lifecycle injection; no runtime-selectable alternate engine/factory exists.\n- Fixed two defects discovered by the tests: Ctrl/Alt-modified printable key filtering and wrapping of the too-small-terminal diagnostic.\n\n## Coverage evidence\n\nBaseline (`22df3480227c3f0938768b70f8d2594f9881b9f5`, run `31276416088`, job `93150555283`):\n\n| Metric | Baseline | Final focused | Delta |\n|---|---:|---:|---:|\n| Regions | 62.09% | 87.77% | +25.68 pp |\n| Functions | 57.14% | 85.38% | +28.24 pp |\n| Lines | 61.25% | 89.26% | +28.01 pp |\n| `ui.rs` lines | 36.42% | 86.14% | +49.72 pp |\n\nFinal focused checklist validation was run `31277368933`, job `93153050871`, against the TUI source/test state published at `2acd49c16267e6bc7e1e38cd2626dfed70f311ac`. No low-coverage production files were excluded to improve the totals.\n\nThe permanent workflow was separately exercised on SHA `a4f7b4e82112117320362d8de4305e4481ae7466`: run `31277523302`, coverage job `93153454991`, Rust 1.75 job `93153454992`, artifact `9027442509`. Text, JSON, LCOV, and HTML reports were all generated successfully.\n\n## Residual coverage dispositions\n\n`main.rs` / `TerminalGuard` remains at 0% in unit-level llvm-cov. This is intentional. Terminal mode and alternate-screen lifecycle are concrete TTY side effects; adding a production `TerminalOps` abstraction solely to increase line coverage would add more surface area than confidence. PTY run `31227882334` / job `93025710323` remains the stronger evidence for real launch/quit restoration. Explicit `restore()` errors are returned on the normal path; the destructor remains best-effort because Rust destructors cannot return failures.\n\nA real permission-denied save fixture is also intentionally not forced under privileged CI. Deterministic write-failure tests exercise the same visible failure transaction via `NotFound`, including clearing stale `saved_path` and never emitting success.\n\n## Safety/fallback audit\n\nThe implementation contains no TUI first-legal fallback, random fallback, silent depth reduction, alternate search-policy replacement, or Python-engine fallback. `chess-search` itself was not modified. `chess-core`, `chess-book`, and `chess-uci` production behavior were not modified by this hardening program.\n\n## Authority disposition\n\nThis hardening TODO is complete and becomes historical. `docs/RUST_TUI_TODO.md` remains the active Rust TUI authority because its manual real-terminal acceptance checklist is intentionally independent and remains open. Final permanent exact-repository-SHA CI/Robustness/coverage run IDs are reported after the closure commit rather than committed back into the repository, which avoids creating an endless evidence-SHA cycle.\n'''
REPORT.write_text(report)

index = INDEX.read_text()
index = replace_once(
    index,
    "| Active Rust TUI test/coverage hardening | `docs/RUST_TUI_TEST_COVERAGE_HARDENING_TODO.md` | Active follow-up hardening TODO for `cargo llvm-cov`, worker/runtime lifecycle tests, input state-machine tests, and fail-closed coverage. |\n",
    "",
    "index active row",
)
index = replace_once(
    index,
    "Active implementation TODOs: `docs/RUST_TUI_TODO.md` and `docs/RUST_TUI_TEST_COVERAGE_HARDENING_TODO.md`. Closed S2, S3, S4 strength/tuning, and S4 closure-hardening TODOs are historical and cannot override the completed Rust-port authority records or these explicitly registered active TODOs.",
    "Active implementation TODO: `docs/RUST_TUI_TODO.md`. The completed Rust TUI test/coverage hardening TODO and closed S2, S3, S4 strength/tuning, and S4 closure-hardening TODOs are historical and cannot override the completed Rust-port authority records or this explicitly registered active TODO.",
    "index active sentence",
)
index = replace_once(
    index,
    "**77 TODO-named files total; 2 completed-authority documents; 2 active authority documents; 1 authority index; 72 historical.**",
    "**77 TODO-named files total; 2 completed-authority documents; 1 active authority document; 1 authority index; 73 historical.**",
    "index counts",
)
needle = "- `docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md`\n"
index = replace_once(
    index,
    needle,
    needle + "- `docs/RUST_TUI_TEST_COVERAGE_HARDENING_TODO.md`\n",
    "index historical insertion",
)
INDEX.write_text(index)

audit = AUDIT.read_text()
audit = replace_once(
    audit,
    'tui_coverage_todo="docs/RUST_TUI_TEST_COVERAGE_HARDENING_TODO.md"\n',
    'tui_coverage_todo="docs/RUST_TUI_TEST_COVERAGE_HARDENING_TODO.md"\ntui_coverage_report="docs/RUST_TUI_TEST_COVERAGE_HARDENING_IMPLEMENTATION.md"\n',
    "audit report variable",
)
audit = replace_once(
    audit,
    '    "$tui_coverage_todo" \\\n    "$legacy_index"',
    '    "$tui_coverage_todo" \\\n    "$tui_coverage_report" \\\n    "$legacy_index"',
    "audit required report",
)
audit = replace_once(
    audit,
    "grep -Fq 'Status: active implementation plan; not yet implemented.' \"$tui_coverage_todo\"",
    "grep -Fq 'Status: complete — Rust TUI test/coverage hardening validated; coverage remains diagnostic and no engine/search/evaluation/tuning behavior changed.' \"$tui_coverage_todo\"\ngrep -Fq 'Status: complete — targeted Rust TUI hardening and diagnostic coverage integration validated.' \"$tui_coverage_report\"",
    "audit coverage status",
)
audit = replace_once(
    audit,
    "grep -Fq 'Active implementation TODOs: `docs/RUST_TUI_TODO.md` and `docs/RUST_TUI_TEST_COVERAGE_HARDENING_TODO.md`.' \"$legacy_index\"",
    "grep -Fq 'Active implementation TODO: `docs/RUST_TUI_TODO.md`.' \"$legacy_index\"",
    "audit active sentence",
)
audit = replace_once(
    audit,
    "grep -Fq '77 TODO-named files total; 2 completed-authority documents; 2 active authority documents; 1 authority index; 72 historical' \"$legacy_index\"",
    "grep -Fq '77 TODO-named files total; 2 completed-authority documents; 1 active authority document; 1 authority index; 73 historical' \"$legacy_index\"",
    "audit counts",
)
audit = replace_once(
    audit,
    '        "$tracker"|"$definitions"|"$tui_todo"|"$tui_coverage_todo"|"$legacy_index")',
    '        "$tracker"|"$definitions"|"$tui_todo"|"$legacy_index")',
    "audit active exceptions",
)
audit = replace_once(
    audit,
    "grep -Fq \"Companion specification: \\\`$tui_coverage_spec\\\`\" \"$tui_coverage_todo\"",
    "grep -Fq \"Companion specification: \\\`$tui_coverage_spec\\\`\" \"$tui_coverage_todo\"\ngrep -Fq 'Fallback-only rejection branch is covered.' \"$tui_coverage_todo\"\ngrep -Fq 'Final focused coverage totals from that run: 87.77% regions, 85.38% functions, 89.26% lines.' \"$tui_coverage_todo\"\ngrep -Fq 'This hardening TODO is complete and becomes historical.' \"$tui_coverage_report\"",
    "audit closure evidence",
)
# Prior temporary hardening/checklist machinery must stay gone.
audit = replace_once(
    audit,
    '    ".github/workflows/ppr-closure.yml"; do',
    '    ".github/workflows/ppr-closure.yml" \\\n    ".github/tui_coverage_hardening_patch.py" \\\n    ".github/tui_coverage_hardening_fix.py" \\\n    ".github/workflows/tui-coverage-hardening-implementation.yml" \\\n    ".github/tui_coverage_checklist_patch.py" \\\n    ".github/workflows/tui-coverage-checklist-validation.yml"; do',
    "audit temporary list",
)
AUDIT.write_text(audit)
