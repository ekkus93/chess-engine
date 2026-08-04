#!/usr/bin/env python3
"""Atomically close Task 19.5 and the overall Task 19 tracker gate."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MERGED_SHA = "d7d8455e6279fab53451bad6a5d778ce66c0a001"
VALIDATED_SHA = "5d70737bf12cbfa16441730b7a64629212b28683"
RUST_RUN = "30867122750"
RUST_JOB = "91861324627"
ANDROID_RUN = "30867122736"
HOST_JOB = "91861324588"
EMULATOR_JOB = "91861324637"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one replacement target, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def update_live_tracker() -> None:
    path = ROOT / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
    replace_once(
        path,
        "| 19 | **In progress** — opening-book abstraction, versioned indexed format, selection policies, and adapter integration complete. |",
        "| 19 | **Complete** — optional explicit opening-book support, indexed format, legal reproducible policies, adapter integration, and permanent verification gate. |",
    )
    replace_once(
        path,
        "# Task 19: Opening book — IN PROGRESS\n- [x] 19.1 Abstraction.\n- [x] 19.2 Format.\n- [x] 19.3 Policies.\n- [x] 19.4 Integration.\n- [ ] 19.5 Tests.",
        "# Task 19: Opening book — COMPLETE\n- [x] 19.1 Abstraction.\n- [x] 19.2 Format.\n- [x] 19.3 Policies.\n- [x] 19.4 Integration.\n- [x] 19.5 Tests.\n- [x] Task 19 gate.\n\n### Task 19 completion evidence\n\n- Merged Task 19.5 implementation SHA: `d7d8455e6279fab53451bad6a5d778ce66c0a001`.\n- Exact validated evidence head: `5d70737bf12cbfa16441730b7a64629212b28683`.\n- Rust run/job: `30867122750` / `91861324627`; 332 non-documentation tests, permanent opening-book audit, strict workspace gates, release depth-four perft, and differential oracle passed.\n- Android run/jobs: `30867122736` / `91861324588`, `91861324637`; host JVM, ARM64/x86_64 verification, APK build, and API-35 instrumentation passed.\n- Opening-book support is optional and disabled by default; all paths, bytes, assets, enablement decisions, and RNG seeds remain explicitly adapter supplied.\n- Task 20 offline self-play is next.",
    )


def update_definitions() -> None:
    path = ROOT / "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
    replace_once(
        path,
        "## 19.5 Tests\n\n- [ ] invalid move rejected from book;\n- [ ] deterministic tie ordering;\n- [ ] seeded weighted selection reproducibility;\n- [ ] corrupt/unsupported data error;\n- [ ] no auto-discovery.\n\n**Task 19 gate:** Book support is optional, explicit, legal, reproducible, and platform adapters supply all I/O.",
        "## 19.5 Tests\n\n- [x] invalid move rejected from book;\n- [x] deterministic tie ordering;\n- [x] seeded weighted selection reproducibility;\n- [x] corrupt/unsupported data error;\n- [x] no auto-discovery.\n\n**Task 19 gate:** Book support is optional, explicit, legal, reproducible, and platform adapters supply all I/O. **Complete.**\n\n### Task 19 completion evidence\n\n- Merged Task 19.5 implementation SHA: `d7d8455e6279fab53451bad6a5d778ce66c0a001`.\n- Exact validated evidence head: `5d70737bf12cbfa16441730b7a64629212b28683`.\n- Permanent Rust run/job: `30867122750` / `91861324627`.\n- Permanent Android run/jobs: `30867122736` / `91861324588`, `91861324637`.\n- Four dedicated public-API regressions and the permanent fail-closed no-auto-discovery audit passed with the complete 332-test Rust workspace and Android adapter gates.\n- Task 19 is complete; Task 20 is next.",
    )


def update_ralph_status() -> None:
    path = ROOT / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
    replace_once(
        path,
        "**Current phase:** Task 19.4 opening-book adapter integration complete; Task 19.5 opening-book tests are next",
        "**Current phase:** Task 19 opening-book support complete; Task 20 offline self-play is next",
    )
    text = path.read_text(encoding="utf-8")
    if "| 19.5 / 19 gate |" in text:
        raise RuntimeError(f"{path}: Task 19.5 evidence row already exists")
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("| 19.4 |"):
            lines.insert(
                index + 1,
                "| 19.5 / 19 gate | `5d70737bf12cbfa16441730b7a64629212b28683` | Rust `30867122750` / `91861324627`; Android `30867122736` / `91861324588`, `91861324637` | four public-API regressions, permanent no-auto-discovery audit, 332 Rust tests, release perft, differential oracle, host JVM, dual-ABI Android, APK, and API-35 instrumentation green; Task 19 complete |",
            )
            break
    else:
        raise RuntimeError(f"{path}: Task 19.4 evidence row not found")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_test_contract() -> None:
    path = ROOT / "docs/RUST_OPENING_BOOK_TESTS.md"
    replace_once(
        path,
        "Task 19.5 behavior and architecture are validated. Tracker closure and the overall Task 19 completion record are performed only after this evidence-bearing documentation head passes the same permanent workflows.",
        "Task 19.5 behavior and architecture are validated. The implementation merged at `d7d8455e6279fab53451bad6a5d778ce66c0a001`; the exact evidence-bearing head `5d70737bf12cbfa16441730b7a64629212b28683` passed the permanent Rust and Android workflows. Task 19 and its overall gate are complete; Task 20 offline self-play is next.",
    )


def verify() -> None:
    live = (ROOT / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md").read_text(
        encoding="utf-8"
    )
    definitions = (
        ROOT / "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
    ).read_text(encoding="utf-8")
    ralph = (ROOT / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md").read_text(
        encoding="utf-8"
    )
    contract = (ROOT / "docs/RUST_OPENING_BOOK_TESTS.md").read_text(
        encoding="utf-8"
    )
    required = (
        (live, "# Task 19: Opening book — COMPLETE"),
        (live, "- [x] 19.5 Tests."),
        (live, "- [x] Task 19 gate."),
        (definitions, "- [x] no auto-discovery."),
        (definitions, "**Complete.**"),
        (ralph, "| 19.5 / 19 gate |"),
        (ralph, "Task 20 offline self-play is next"),
        (contract, "Task 19 and its overall gate are complete"),
    )
    for text, marker in required:
        if marker not in text:
            raise RuntimeError(f"missing closure marker: {marker}")


def main() -> None:
    update_live_tracker()
    update_definitions()
    update_ralph_status()
    update_test_contract()
    verify()
    Path(__file__).unlink()
    print(
        "Task 19.5 and Task 19 tracker closure applied for merged SHA "
        f"{MERGED_SHA}; validated SHA {VALIDATED_SHA}; Rust {RUST_RUN}/{RUST_JOB}; "
        f"Android {ANDROID_RUN}/{HOST_JOB},{EMULATOR_JOB}"
    )


if __name__ == "__main__":
    main()
