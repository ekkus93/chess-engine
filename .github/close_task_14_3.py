#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
MODE = sys.argv[2]
IMPLEMENTATION_SHA = "f08b2d519ffc066d8d6b18326e03ead278d908de"
FOCUSED_RUN = "30762211967"
FOCUSED_JOB = "91534658841"


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    path.write_text(text.replace(old, new, 1))


if MODE == "prepare":
    alpha_beta = ROOT / "crates/chess-search/src/alpha_beta.rs"
    replace_once(
        alpha_beta,
        """/// promotions, and every legal check evasion. Legal moves use deterministic
/// deterministic ordering: the future TT and previous-PV hooks, promotions,
/// MVV-LVA captures, bounded killer and history heuristics, then a stable packed
/// quiet-move tie-break. The root uses the complete supported score window, so
/// its returned score is exact
/// rather than a bound.""",
        """/// promotions, and every legal check evasion. Legal moves use deterministic
/// ordering: the future TT and previous-PV hooks, promotions, MVV-LVA captures,
/// bounded killer and history heuristics, then a stable packed quiet-move
/// tie-break. The root uses the complete supported score window, so its returned
/// score is exact rather than a bound.""",
        "alpha-beta ordering documentation",
    )
    print("Task 14.3 closure preparation applied")
    raise SystemExit(0)

if MODE != "close" or len(sys.argv) != 6:
    raise SystemExit("usage: close_task_14_3.py ROOT prepare | ROOT close RUN JOB TEST_COUNT")

run_id, job_id, test_count = sys.argv[3:6]
if not run_id.isdigit() or not job_id.isdigit() or not test_count.isdigit():
    raise SystemExit("run, job, and test count must be decimal integers")

# Authoritative task tracker.
todo = ROOT / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
replace_once(todo, "- [ ] 14.3 Quiet ordering.", "- [x] 14.3 Quiet ordering.", "Task 14.3 checkbox")
replace_once(
    todo,
    "- Task 14.2 tactical ordering is complete; Task 14.3 quiet ordering is next.",
    "- Tasks 14.2 and 14.3 ordering are complete; Task 14.4 correctness consolidation is next.",
    "Task 14.1 next-operation evidence",
)
replace_once(
    todo,
    "- Static exchange evaluation remains intentionally absent. Killer/history/PV quiet ordering belongs to Task 14.3; transposition storage belongs to Task 15; production limits belong to Task 16.\n\n# Task 15: Fixed-capacity transposition table — NOT STARTED",
    f"""- Static exchange evaluation remains intentionally absent. Task 14.3 now owns bounded killer/history/stable-tie quiet ordering; transposition storage belongs to Task 15; production limits and real iterative previous-PV reuse belong to Task 16.

### Task 14.3 completion evidence

- Production implementation: `crates/chess-search/src/move_ordering.rs` and `crates/chess-search/src/alpha_beta.rs`.
- Contract documentation: `docs/RUST_QUIET_MOVE_ORDERING.md`.
- Exact implementation SHA: `{IMPLEMENTATION_SHA}`.
- Focused implementation run/job: `{FOCUSED_RUN}` / `{FOCUSED_JOB}`; Cargo check, strict Clippy, and all 51 `chess-search` tests passed.
- Full closure validation run/job: `{run_id}` / `{job_id}`.
- Results: workspace assets, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, {test_count} executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Bounded search-local state provides two killer slots for every supported ply and one fixed `2 x 64 x 64` side/source/destination history table.
- Only quiet beta cutoffs update killers and history. History uses a depth-squared saturating bonus capped at `1,000,000`; captures and promotions never pollute quiet statistics.
- Production order is the future TT hook, explicit previous-PV hook, promotions, MVV-LVA captures, primary/secondary killers, descending history, then ascending packed `Move` identity.
- The previous-PV hook remains an explicit no-op until Task 16 supplies completed-iteration PV data; the TT hook remains an explicit no-op until Task 15.
- Fixed full-window and narrow-window regressions prove deterministic exact score/best-move semantics, strict node reduction when a useful killer is seeded, and exact position/history/incremental-Zobrist restoration.
- Reference search retains exact legal-generation order; Task 14.2 tactical ordering remains available as a control policy. Task 14.4 correctness consolidation is next.

# Task 15: Fixed-capacity transposition table — NOT STARTED""",
    "Task 14.3 completion evidence insertion",
)

# Detailed task definitions.
definitions = ROOT / "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
for text in (
    "Killer moves by ply.",
    "History heuristic by side/from/to or piece/to.",
    "Stable encoded-move tie-break.",
    "Optional previous-PV move.",
):
    replace_once(definitions, f"- [ ] {text}", f"- [x] {text}", f"Task 14.3 definition: {text}")

# Ralph-loop status.
status = ROOT / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
replace_once(
    status,
    "**Current phase:** Tasks 14.1–14.2 complete; Task 14.3 quiet ordering is next",
    "**Current phase:** Tasks 14.1–14.3 complete; Task 14.4 correctness consolidation is next",
    "status current phase",
)
replace_once(
    status,
    "| 14.2 | `3688cb8e89a7da0c7fd34c3756d52d0fcc8d3d33` | `30753873602` / `91512570865` | bounded tactical ordering, 145 Rust tests, strict node-reduction witness, depth-four perft, and differential oracle green |",
    f"""| 14.2 | `3688cb8e89a7da0c7fd34c3756d52d0fcc8d3d33` | `30753873602` / `91512570865` | bounded tactical ordering, 145 Rust tests, strict node-reduction witness, depth-four perft, and differential oracle green |
| 14.3 | `{IMPLEMENTATION_SHA}` | `{run_id}` / `{job_id}` | bounded killer/history quiet ordering, {test_count} Rust tests, deterministic exact-score and strict node-reduction witnesses, depth-four perft, and differential oracle green |""",
    "status completed-gates row",
)
replace_once(
    status,
    "- Task 14.2 tactical ordering is complete. Task 14.3 quiet ordering, Task 15 transposition storage, and Task 16 production limits remain open.",
    "- Tasks 14.2 and 14.3 ordering are complete. Task 14.4 correctness consolidation, Task 15 transposition storage, and Task 16 production limits remain open.",
    "status Task 14.1 next scope",
)
replace_once(
    status,
    "- SEE remains intentionally absent; Task 14.3 owns killer/history/stable-tie/PV quiet ordering.\n\n## Task 14 active scope",
    f"""- SEE remains intentionally absent; Task 14.3 now owns bounded killer/history/stable-tie quiet ordering, while Tasks 15 and 16 own TT storage and real previous-PV data.

## Task 14.3 completion

Implemented and validated:

- fixed-capacity, search-local quiet-ordering state with two killer slots at every supported ply;
- a fixed `2 x 64 x 64` history table keyed by side, source, and destination;
- quiet-cutoff-only learning with depth-squared saturating history bonuses;
- explicit capture/promotion exclusion from killer and history updates;
- deterministic order after tactical moves: primary killer, secondary killer, descending history, then ascending packed move identity;
- an explicit previous-PV hook that remains `None` until Task 16 provides completed-iteration PV data;
- production alpha-beta integration through a lint-clean recursive context carrying ordering state and cancellation;
- generation-order reference control and retained Task 14.2 tactical control;
- exact full-window determinism and a fixed seeded-killer narrow-window node-reduction witness;
- exact position, detached-history, invariant, and incremental/recomputed-Zobrist restoration;
- `docs/RUST_QUIET_MOVE_ORDERING.md`.

Evidence:

- Exact implementation SHA: `{IMPLEMENTATION_SHA}`.
- Focused implementation run/job: `{FOCUSED_RUN}` / `{FOCUSED_JOB}`; Cargo check, strict Clippy, and all 51 `chess-search` tests passed.
- Full closure validation run/job: `{run_id}` / `{job_id}`.
- Results: workspace assets, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, {test_count} executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 14.4 consolidated correctness tests are next; Tasks 14.5, 15, and 16 remain intentionally open.

## Task 14 active scope""",
    "status Task 14.3 completion section",
)
replace_once(
    status,
    "- [ ] Implement Task 14.3 quiet ordering.",
    "- [x] Implement Task 14.3 quiet ordering.",
    "status Task 14.3 active checkbox",
)
replace_once(
    status,
    "No pull request has been created; work remains on `rust-engine`. Task 14.3 quiet ordering is the next operation.",
    "No pull request has been created; work remains on `rust-engine`. Task 14.4 consolidated correctness tests are the next operation.",
    "status final next operation",
)

print(f"Task 14.3 closure applied for run {run_id}, job {job_id}, tests {test_count}")
