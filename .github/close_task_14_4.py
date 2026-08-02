#!/usr/bin/env python3
"""Close Rust port Task 14.4 trackers idempotently."""

from __future__ import annotations

import sys
from pathlib import Path

IMPLEMENTATION_SHA = "dc758a3fc62e7f7002191993c73773dd2a71caef"
RUN_ID = "30763226685"
JOB_ID = "91537383867"


def ensure_replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return
    if new not in text:
        raise RuntimeError(f"{path}: neither old nor new text found: {old!r}")


def close(root: Path) -> None:
    definitions = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
    ensure_replace(
        definitions,
        """## 14.4 Correctness tests

- [ ] Horizon capture sequence.
- [ ] In-check leaf may not stand pat.
- [ ] Promotion sequence.
- [ ] Poisoned capture where qsearch changes evaluation.
- [ ] Quiescence boundedness.
""",
        """## 14.4 Correctness tests

- [x] Horizon capture sequence.
- [x] In-check leaf may not stand pat.
- [x] Promotion sequence.
- [x] Poisoned capture where qsearch changes evaluation.
- [x] Quiescence boundedness.
""",
    )

    todo = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
    ensure_replace(
        todo,
        "| 14 | **Active** — Tasks 14.1–14.2 complete; Task 14.3 quiet ordering next. |",
        "| 14 | **Active** — Tasks 14.1–14.4 complete; Task 14.5 exclusion audit next. |",
    )
    ensure_replace(todo, "- [ ] 14.4 Correctness tests.", "- [x] 14.4 Correctness tests.")
    old_todo_tail = (
        "- Reference search retains exact legal-generation order; Task 14.2 tactical ordering "
        "remains available as a control policy. Task 14.4 correctness consolidation is next.\n\n"
        "# Task 15: Fixed-capacity transposition table — NOT STARTED"
    )
    new_todo_tail = f"""- Reference search retains exact legal-generation order; Task 14.2 tactical ordering remains available as a control policy. Task 14.4 correctness consolidation is complete; Task 14.5 exclusion audit is next.

### Task 14.4 completion evidence

- Dedicated regressions: `crates/chess-search/tests/search_quiescence_task_14_4.rs`.
- Exact validated implementation/evidence SHA: `{IMPLEMENTATION_SHA}`.
- Permanent CI run/job: `{RUN_ID}` / `{JOB_ID}`.
- Results: workspace assets, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 155 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- The horizon witness searches the full `Qxe5 Rxe5 Rxe5` tactical continuation beyond the nominal leaf and restores the exact root state.
- The in-check witness proves stand-pat is unavailable by requiring a searched quiet king evasion and more than one visited node.
- The promotion witness searches promotion, forced recapture, and counter-recapture rather than stopping at the promotion leaf.
- The poisoned-capture witness explicitly proves static leaf evaluation overvalues `Qxd8`, quiescence lowers that score after forced `Kxd8`, and the one-ply root rejects the poisoned move.
- The boundedness witness proves a zero-ply guard returns one-node stand-pat outside check but fails loudly with `QuiescenceDepthLimitReachedInCheck` while checked.
- Every new path verifies position/history snapshots, invariants, and incremental/recomputed Zobrist restoration.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 14.5 explicit-exclusion audit is next; the overall Task 14 gate remains open.

# Task 15: Fixed-capacity transposition table — NOT STARTED"""
    ensure_replace(todo, old_todo_tail, new_todo_tail)

    ralph = root / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
    ensure_replace(
        ralph,
        "**Current phase:** Tasks 14.1–14.3 complete; Task 14.4 correctness consolidation is next",
        "**Current phase:** Tasks 14.1–14.4 complete; Task 14.5 explicit-exclusion audit is next",
    )
    old_row = (
        "| 14.3 | `f08b2d519ffc066d8d6b18326e03ead278d908de` | "
        "`30762457921` / `91535329886` | bounded killer/history quiet ordering, "
        "150 Rust tests, deterministic exact-score and strict node-reduction witnesses, "
        "depth-four perft, and differential oracle green |"
    )
    new_row = (
        old_row
        + f"\n| 14.4 | `{IMPLEMENTATION_SHA}` | `{RUN_ID}` / `{JOB_ID}` | "
        "five explicit quiescence correctness witnesses, 155 Rust tests, depth-four perft, "
        "and differential oracle green |"
    )
    ensure_replace(ralph, old_row, new_row)

    old_completion = (
        "- Task 14.4 consolidated correctness tests are next; Tasks 14.5, 15, and 16 "
        "remain intentionally open.\n\n## Task 14 active scope"
    )
    new_completion = f"""- Task 14.4 consolidated correctness tests are complete; Tasks 14.5, 15, and 16 remain intentionally open.

## Task 14.4 completion

Implemented and validated:

- a true multi-capture horizon sequence (`Qxe5 Rxe5 Rxe5`) searched to a quiet position;
- an in-check leaf that must search a quiet legal evasion and cannot stand pat;
- a promotion sequence searched through forced recapture and counter-recapture;
- a poisoned capture whose static leaf score is explicitly corrected downward by quiescence before root move selection;
- finite guard behavior: one-node stand-pat outside check and fail-loud refusal to truncate while checked;
- exact position, detached-history, invariant, and incremental/recomputed-Zobrist restoration on every new path;
- `crates/chess-search/tests/search_quiescence_task_14_4.rs`.

Evidence:

- Exact validated implementation/evidence SHA: `{IMPLEMENTATION_SHA}`.
- Permanent CI run/job: `{RUN_ID}` / `{JOB_ID}`.
- Results: workspace assets, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 155 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Dedicated Task 14.4 suite: 5 passed; original quiescence suite: 5 passed; search-equivalence suite: 3 passed; immutability suite: 4 passed; terminal/mate-distance suite: 4 passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 14.5 explicit-exclusion audit is next; the overall Task 14 gate remains open.

## Task 14 active scope"""
    ensure_replace(ralph, old_completion, new_completion)
    ensure_replace(
        ralph,
        "- [ ] Complete Task 14.4 consolidated correctness tests and Task 14.5 exclusion audit.",
        "- [x] Complete Task 14.4 consolidated correctness tests.\n- [ ] Complete Task 14.5 exclusion audit.",
    )
    ensure_replace(
        ralph,
        "No pull request has been created; work remains on `rust-engine`. Task 14.4 consolidated correctness tests are the next operation.",
        "No pull request has been created; work remains on `rust-engine`. Task 14.5 explicit-exclusion audit is the next operation.",
    )

    for relative in (
        ".github/workflows/task-14-4-validation.yml",
        "docs/TASK_14_4_CI_EVIDENCE.txt",
    ):
        path = root / relative
        if path.exists():
            path.unlink()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: close_task_14_4.py REPOSITORY_ROOT", file=sys.stderr)
        return 2
    close(Path(sys.argv[1]).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
