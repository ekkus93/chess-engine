#!/usr/bin/env python3
"""Close Task 14.5 and the overall Task 14 gate idempotently."""

from __future__ import annotations

import sys
from pathlib import Path

IMPLEMENTATION_SHA = "f4dc989e97d8577f4c86bdbfb67ae47e3d5cd7f4"
RUN_ID = "30764073097"
JOB_ID = "91539614372"


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
        """## 14.5 Explicit exclusions

- [ ] No transcript review-loop ordering.
- [ ] No anti-drift scenario scoring.
- [ ] No root heuristic that can override a better exact score.
- [ ] No large strategic evaluation duplicated inside ordering.
""",
        """## 14.5 Explicit exclusions

- [x] No transcript review-loop ordering.
- [x] No anti-drift scenario scoring.
- [x] No root heuristic that can override a better exact score.
- [x] No large strategic evaluation duplicated inside ordering.
""",
    )

    todo = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
    ensure_replace(
        todo,
        "| 14 | **Active** — Tasks 14.1–14.4 complete; Task 14.5 exclusion audit next. |",
        "| 14 | **Complete** — quiescence, tactical/quiet ordering, consolidated correctness, and exclusion audit. |",
    )
    ensure_replace(
        todo,
        "# Task 14: Quiescence and ordering — ACTIVE",
        "# Task 14: Quiescence and ordering — COMPLETE",
    )
    ensure_replace(todo, "- [ ] 14.5 Exclusions.", "- [x] 14.5 Exclusions.")
    ensure_replace(todo, "- [ ] Task 14 gate.", "- [x] Task 14 gate.")

    old_tail = (
        "- Task 14.5 explicit-exclusion audit is next; the overall Task 14 gate remains open.\n\n"
        "# Task 15: Fixed-capacity transposition table — NOT STARTED"
    )
    new_tail = f"""- Task 14.5 explicit-exclusion audit and the overall Task 14 gate are complete.

### Task 14.5 and Task 14 gate completion evidence

- Permanent executable audit: `scripts/task_14_5_exclusion_audit.py`.
- Audit contract: `docs/RUST_SEARCH_ORDERING_EXCLUSION_AUDIT.md`.
- Permanent CI now runs the audit before Rust toolchain validation.
- Exact validated implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent CI run/job: `{RUN_ID}` / `{JOB_ID}`.
- The audit scanned 10 production `chess-search` Rust files and found no transcript/review-loop or anti-drift/scenario-scoring identifiers.
- `MoveOrderKey` is restricted to TT/PV hooks, tactical category/material terms, killer/history values, and the encoded tie-break.
- Move ordering may query only `Position::piece_at` and `Position::side_to_move`; strategic evaluator identifiers are forbidden in production ordering code.
- Root alpha-beta retains the complete score window and replaces the best move only on a strictly greater searched score; ordering keys are absent from result selection.
- Existing exact-score witnesses prove full-window quiet-ordering determinism and unique-root-maximum selection; tactical and quiet narrow-window witnesses prove node reduction without score or best-move changes.
- Results: workspace assets, exclusion audit, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 155 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 14 is complete. Task 15.1 fixed-capacity transposition-table entry design is next.

# Task 15: Fixed-capacity transposition table — NOT STARTED"""
    ensure_replace(todo, old_tail, new_tail)

    old_next = """## Immediate next operations

1. Implement Task 14.3 quiet ordering over the validated Task 14.1–14.2 search semantics.
2. Add bounded killer moves by ply and a bounded history heuristic keyed by side/from/to or piece/to.
3. Use a stable encoded-move tie-break and keep any previous-PV hook explicit and optional until Task 16 provides iterative deepening and PV data.
4. Prove quiet ordering cannot override a better exact score and preserves deterministic full-window root results.
5. Compare nodes on fixed quiet-search benchmark positions while preserving cancellation, history, Zobrist, and exact make/unmake restoration.
6. Keep Task 14.4 consolidated correctness closure, Task 14.5 exclusion audit, Task 15 transposition storage, and Task 16 production limits outside Task 14.3."""
    new_next = """## Immediate next operations

1. Implement Task 15.1 transposition-table entry design with verification key, depth, bound flag, normalized score, best move, and age/generation.
2. Define fixed-memory bucket/cluster storage and explicit clear/new-generation operations before integrating probes into search.
3. Preserve mate-score normalization across different plies and add exact store/probe regressions before enabling TT cutoffs.
4. Keep repetition-sensitive reuse fail-safe and retain exact full-window score semantics.
5. Benchmark probes, stores, replacement behavior, and node reduction only after correctness tests pass.
6. Keep Task 16 iterative deepening, aspiration windows, PV reconstruction, and production limits outside Task 15."""
    ensure_replace(todo, old_next, new_next)

    ralph = root / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
    ensure_replace(
        ralph,
        "**Current phase:** Tasks 14.1–14.4 complete; Task 14.5 explicit-exclusion audit is next",
        "**Current phase:** Task 14 complete; Task 15.1 transposition-table entry design is next",
    )
    old_row = (
        "| 14.4 | `dc758a3fc62e7f7002191993c73773dd2a71caef` | "
        "`30763226685` / `91537383867` | five explicit quiescence correctness witnesses, "
        "155 Rust tests, depth-four perft, and differential oracle green |"
    )
    new_row = (
        old_row
        + f"\n| 14.5 / 14 | `{IMPLEMENTATION_SHA}` | `{RUN_ID}` / `{JOB_ID}` | "
        "permanent exclusion audit, exact-score boundary, 155 Rust tests, depth-four perft, "
        "and differential oracle green |"
    )
    ensure_replace(ralph, old_row, new_row)

    old_completion = (
        "- Task 14.5 explicit-exclusion audit is next; the overall Task 14 gate remains open.\n\n"
        "## Task 14 active scope"
    )
    new_completion = f"""- Task 14.5 explicit-exclusion audit and the overall Task 14 gate are complete.

## Task 14.5 and Task 14 completion

Implemented and validated:

- a permanent CI audit over all 10 production `chess-search` Rust modules;
- fail-loud rejection of transcript/review-loop and anti-drift/scenario-scoring identifiers;
- an exact nine-field `MoveOrderKey` boundary containing only TT/PV hooks, tactical material categories, killers, history, and the stable encoded tie-break;
- a restricted ordering read boundary of `Position::piece_at` and `Position::side_to_move` only;
- fail-loud rejection of strategic evaluator identifiers in production move ordering;
- structural enforcement that root alpha-beta uses the complete score window and replaces the best move only for a strictly greater searched score;
- required exact-score and node-reduction witnesses retained in the Rust test tree;
- `scripts/task_14_5_exclusion_audit.py` and `docs/RUST_SEARCH_ORDERING_EXCLUSION_AUDIT.md`.

Evidence:

- Exact validated implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent CI run/job: `{RUN_ID}` / `{JOB_ID}`.
- Audit output: 10 production Rust files scanned; approved nine ordering fields; ordering position queries limited to `piece_at` and `side_to_move`; all four exact-score/node-reduction witnesses present.
- Results: workspace assets, exclusion audit, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 155 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 14 is complete; Task 15.1 is next.

## Task 14 completed scope"""
    ensure_replace(ralph, old_completion, new_completion)
    ensure_replace(
        ralph,
        "- [ ] Complete Task 14.5 exclusion audit.",
        "- [x] Complete Task 14.5 exclusion audit.",
    )
    ensure_replace(
        ralph,
        "- [ ] Pass the overall Task 14 gate.",
        "- [x] Pass the overall Task 14 gate.",
    )
    ensure_replace(
        ralph,
        "No pull request has been created; work remains on `rust-engine`. Task 14.5 explicit-exclusion audit is the next operation.",
        "No pull request has been created; work remains on `rust-engine`. Task 15.1 transposition-table entry design is the next operation.",
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: close_task_14_5.py REPOSITORY_ROOT", file=sys.stderr)
        return 2
    close(Path(sys.argv[1]).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
