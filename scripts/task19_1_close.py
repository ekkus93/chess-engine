#!/usr/bin/env python3
"""Close only Task 19.1 after exact implementation validation."""

from __future__ import annotations

from pathlib import Path

IMPLEMENTATION_SHA = "6ce31141d0d4516696f1e9d17ee018606ef7bd4b"
RUST_RUN = "30852253445"
RUST_JOB = "91814805656"
ANDROID_RUN = "30852253399"
ANDROID_HOST_JOB = "91814815286"
ANDROID_EMULATOR_JOB = "91814815151"

ROOT = Path(__file__).resolve().parents[1]
DEFINITIONS = ROOT / "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
TODO = ROOT / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
RALPH = ROOT / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
CONTRACT = ROOT / "docs/RUST_OPENING_BOOK_ABSTRACTION.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new, 1)


def close_definitions() -> None:
    text = read(DEFINITIONS)
    task_19_marker = "# Task 19: Implement optional opening-book infrastructure"
    task_20_marker = "# Task 20: Implement self-play and versioned dataset tooling"
    if text.count(task_19_marker) != 1 or text.count(task_20_marker) != 1:
        raise SystemExit("Task 19/20 section markers are not unique")

    prefix, remainder = text.split(task_19_marker, 1)
    task_19, suffix = remainder.split(task_20_marker, 1)

    required = (
        "- [ ] Define adapter-facing `OpeningBook`/`BookProvider` trait outside `chess-core`.",
        "- [ ] Define `BookMove` with move, weight, and optional metadata.",
        "- [ ] Ensure no filesystem dependency enters core/search crates.",
    )
    for item in required:
        task_19 = replace_once(task_19, item, item.replace("[ ]", "[x]", 1), item)

    if "## 19.2 Backend format" not in task_19:
        raise SystemExit("Task 19.2 marker is missing")
    task_19_2_and_later = task_19.split("## 19.2 Backend format", 1)[1]
    if "- [x]" in task_19_2_and_later:
        raise SystemExit("Task 19.2 or later was unexpectedly already checked")

    write(DEFINITIONS, prefix + task_19_marker + task_19 + task_20_marker + suffix)


def close_summary_todo() -> None:
    text = read(TODO)
    text = replace_once(
        text,
        "- [ ] 19.1 Abstraction.",
        "- [x] 19.1 Abstraction.",
        "Task 19.1 summary item",
    )
    if "- [ ] 19.2" not in text:
        raise SystemExit("Task 19.2 summary item is not open")
    if "- [ ] Task 19 gate." not in text:
        raise SystemExit("Task 19 gate is not open")
    write(TODO, text)


def update_ralph_status() -> None:
    text = read(RALPH)
    text = replace_once(
        text,
        "**Current phase:** Task 18 complete; Task 19.1 opening-book abstraction is next",
        "**Current phase:** Task 19.1 opening-book abstraction complete; Task 19.2 backend format is next",
        "Ralph current phase",
    )

    lines = text.splitlines()
    matches = [index for index, line in enumerate(lines) if line.startswith("| 18.5 / 18 gate |")]
    if len(matches) != 1:
        raise SystemExit(f"Task 18.5 Ralph row: expected one occurrence, found {len(matches)}")
    if any(line.startswith("| 19.1 |") for line in lines):
        raise SystemExit("Task 19.1 Ralph row already exists")

    row = (
        f"| 19.1 | `{IMPLEMENTATION_SHA}` | Rust `{RUST_RUN}` / `{RUST_JOB}`; "
        f"Android `{ANDROID_RUN}` / `{ANDROID_HOST_JOB}`, `{ANDROID_EMULATOR_JOB}` | "
        "adapter-neutral `chess-book` crate, typed `OpeningBook`/`BookProvider`, generic weighted "
        "`BookMove`, four focused tests, no core/search I/O dependencies; 310 Rust tests and "
        "Android regressions green |"
    )
    lines.insert(matches[0] + 1, row)
    text = "\n".join(lines) + "\n"

    section = f"""
## Task 19.1 completion

Implemented and validated:

- dedicated platform-neutral `chess-book` workspace crate depending only on `chess-core`;
- `BookMove<M = ()>` with semantic engine move, `u32` relative weight, and optional backend metadata;
- `OpeningBook` as a `Send + Sync` validated-position query with typed fail-visible errors;
- `BookProvider` as an explicit adapter-owned construction boundary with `Ok(None)` for intentionally disabled book support;
- no filesystem, asset, environment, network, global-discovery, or platform dependency in `chess-core` or `chess-search`;
- four focused contract tests covering value preservation, dynamic injection, explicit enable/disable, and typed lookup failure;
- parser/format, selection, legality validation, UCI/safe-API integration, and Android assets remain explicitly deferred to Tasks 19.2–19.5.

Evidence:

- Exact validated implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent Rust validation: run `{RUST_RUN}`, job `{RUST_JOB}`.
- Permanent Android regression validation: run `{ANDROID_RUN}`, host JVM job `{ANDROID_HOST_JOB}`, emulator job `{ANDROID_EMULATOR_JOB}`.
- Results: committed lockfile, metadata, rustfmt, workspace check, strict Clippy, 310 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, differential oracle, host JVM JNI, dual Android ABI build, APK build, and API-35 emulator lifecycle all passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The first executable validation found only canonical rustfmt output; no API, dependency boundary, error policy, test, or gate was weakened.
- Task 19.2 backend format is next. The overall Task 19 gate remains open.
"""
    if "## Task 19.1 completion" in text:
        raise SystemExit("Task 19.1 completion section already exists")
    write(RALPH, text.rstrip() + "\n\n" + section.lstrip())


def update_contract() -> None:
    text = read(CONTRACT)
    if "## Completion evidence" in text:
        raise SystemExit("opening-book contract completion evidence already exists")
    evidence = f"""
## Completion evidence

- Exact validated implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent Rust validation: run `{RUST_RUN}`, job `{RUST_JOB}`.
- Permanent Android regression validation: run `{ANDROID_RUN}`, host JVM job `{ANDROID_HOST_JOB}`, emulator job `{ANDROID_EMULATOR_JOB}`.
- Four focused `chess-book` tests passed; the complete workspace executed 310 non-doc Rust tests with zero failures.
- Release depth-four perft, rustdoc with warnings denied, debug/release builds, and the differential oracle all passed.
- Differential evidence: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The Android regression gate rebuilt and verified both JNI ABIs, passed host JVM tests, rebuilt the AAR/test APK, and passed the API-35 emulator lifecycle.
- The only implementation-validation correction was canonical rustfmt output.
- Task 19.1 is complete. Tasks 19.2–19.5 and the overall Task 19 gate remain open.
"""
    write(CONTRACT, text.rstrip() + "\n\n" + evidence.lstrip())


def main() -> int:
    close_definitions()
    close_summary_todo()
    update_ralph_status()
    update_contract()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
