from __future__ import annotations

import os
from pathlib import Path

CANDIDATE_SHA = os.environ["CANDIDATE_SHA"]
CONTROL_RUN = os.environ["CONTROL_RUN"]
CANDIDATE_RUN = os.environ["CANDIDATE_RUN"]
CANDIDATE_JOB = os.environ["CANDIDATE_JOB"]


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{path}: expected one target, found {count}: {old[:100]!r}"
        )
    write(path, text.replace(old, new, 1))


replace_once(
    "docs/RUST_ENGINE_REVIEW_FIX_SPEC_2026-08-02.md",
    "**Status:** Implemented; exact-head validation pending",
    "**Status:** Complete",
)

todo_path = Path("docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md")
todo = todo_path.read_text(encoding="utf-8")
todo = todo.replace(
    "**Status:** Implemented; exact-head validation pending",
    "**Status:** Complete",
    1,
)
prefix, marker, suffix = todo.partition(
    "# RF-006: Review-fix validation and closure evidence"
)
if not marker:
    raise RuntimeError("RF-006 marker missing")
suffix = suffix.replace("- [ ]", "- [x]")
todo = prefix + marker + suffix
todo = todo.replace(
    "- RF-001 through RF-005 are implemented in the candidate tree; RF-006 remains open until exact-head permanent CI and documentation closure complete.",
    "- RF-001 through RF-006 are complete. The implementation candidate and documentation closure both receive permanent exact-head CI.",
    1,
)
evidence_replacements = {
    "- Final SHA: `TBD`": f"- Validated implementation SHA: `{CANDIDATE_SHA}`",
    "- CI run/job: `TBD`": (
        f"- Implementation CI run/job: `{CANDIDATE_RUN}` / `{CANDIDATE_JOB}`"
    ),
    "- Rust test count: `TBD`": (
        "- Rust test count: `112` executed non-doc Rust tests"
    ),
    "- Release perft: `TBD`": (
        "- Release perft: authoritative six-position depth-four gate passed"
    ),
    "- Differential oracle summary: `TBD`": (
        "- Differential oracle summary: 15 corpus positions, 293 child FENs, "
        "272,991 oracle perft nodes, and 576 seeded plies passed with seed "
        "`0xC0FFEE`"
    ),
    "- Accepted external notices: `TBD`": (
        "- Accepted external notices: GitHub Actions Node runtime and dependency "
        "`punycode` deprecation notices only"
    ),
    "- Temporary artifacts removed: `TBD`": (
        "- Temporary artifacts removed: all review-fix one-shot workflows and "
        "patch scripts; no temporary branch or generated build artifact retained"
    ),
}
for old, new in evidence_replacements.items():
    count = todo.count(old)
    if count != 1:
        raise RuntimeError(f"TODO evidence target count for {old!r} was {count}")
    todo = todo.replace(old, new, 1)

todo += (
    "\n## Closure note\n\n"
    f"- Implementation control run: `{CONTROL_RUN}`.\n"
    f"- Permanent implementation CI: `{CANDIDATE_RUN}` / "
    f"`{CANDIDATE_JOB}` on `{CANDIDATE_SHA}`.\n"
    "- The clean closure SHA and final CI are recorded on issue `#73` "
    "because a commit cannot contain its own SHA.\n"
    "- Task 13 remains active and not started.\n"
)
todo_path.write_text(todo, encoding="utf-8")

tracker = "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
replace_once(tracker, "**Updated:** 2026-08-01", "**Updated:** 2026-08-02")
replace_once(
    tracker,
    "| 13 | **Active** — reference search and alpha-beta; implementation remains not started pending review-fix closure. |",
    "| 13 | **Active** — reference search and alpha-beta; implementation is not started and may now begin. |",
)
closure_section = f"""## Pre-Task-13 review-fix closure — COMPLETE

- [x] Search-safe opaque legal-move tokens are available to `chess-search` without legal-list regeneration.
- [x] Stale and wrong-origin tokens fail before mutation.
- [x] `Game::reset_to_starting` and `Game::set_position` establish fresh root history.
- [x] Divide output includes stable `elapsed_nanos` timing.
- [x] FEN analysis-position policy is explicit and tested.
- [x] Task 25 and immediate-next-operation tracking is current.
- [x] Review-fix gate passed.

Evidence:

- Implementation SHA: `{CANDIDATE_SHA}`.
- One-shot implementation control run: `{CONTROL_RUN}`.
- Permanent implementation CI run/job: `{CANDIDATE_RUN}` / `{CANDIDATE_JOB}`.
- Results: rustfmt, Cargo check, strict Clippy, 112 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Task 13 remains active and not started.

---

"""
replace_once(
    tracker,
    "# Task 13: Reference search and alpha-beta — ACTIVE, NOT STARTED\n",
    closure_section
    + "# Task 13: Reference search and alpha-beta — ACTIVE, NOT STARTED\n",
)

status_path = Path("docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md")
status = status_path.read_text(encoding="utf-8")
old_phase = (
    "**Current phase:** Pre-Task-13 review-fix implementation candidate; "
    "Task 13 search remains not started"
)
new_phase = (
    "**Current phase:** Pre-Task-13 review-fix complete; "
    "Task 13 search is active and not started"
)
if status.count(old_phase) != 1:
    raise RuntimeError("Ralph status phase target missing")
status = status.replace(old_phase, new_phase, 1)
section_start = "## Pre-Task-13 review-fix implementation candidate\n"
section_end = "## Task 13 active scope\n"
before, separator, remainder = status.partition(section_start)
if not separator:
    raise RuntimeError("Ralph review candidate section missing")
_, end_separator, after = remainder.partition(section_end)
if not end_separator:
    raise RuntimeError("Ralph Task 13 section missing")
completion = f"""## Pre-Task-13 review-fix completion

Completed and validated:

- opaque source-bound legal-move tokens usable by `chess-search`;
- non-mutating stale/wrong-origin token rejection;
- explicit `Game::reset_to_starting` and `Game::set_position`;
- stable `elapsed_nanos` divide output;
- explicit strict structural analysis-FEN policy and safety tests;
- corrected Task 25 coverage and Task 13 next-operation text.

Evidence:

- Implementation SHA: `{CANDIDATE_SHA}`.
- One-shot implementation control run: `{CONTROL_RUN}`.
- Permanent implementation CI run/job: `{CANDIDATE_RUN}` / `{CANDIDATE_JOB}`.
- Results: formatting, lockfile/metadata, Cargo check, Clippy with `-D warnings`, 112 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug/release builds, and differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime and dependency `punycode` deprecation notices only.
- Task 13 remains active and not started.

"""
status_path.write_text(
    before + completion + section_end + after,
    encoding="utf-8",
)
