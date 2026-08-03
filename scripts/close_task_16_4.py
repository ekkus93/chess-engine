#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()


def read(path: str) -> str:
    return (root / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    (root / path).write_text(content, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def insert_before(text: str, marker: str, addition: str, label: str) -> str:
    count = text.count(marker)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    return text.replace(marker, addition + marker, 1)

# Detailed definitions.
definitions_path = "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
definitions = read(definitions_path)
definitions = replace_once(
    definitions,
    """## 16.4 Search limits

- [ ] depth;
- [ ] nodes;
- [ ] soft time;
- [ ] hard time;
- [ ] infinite;
- [ ] explicit stop flag.
""",
    """## 16.4 Search limits

- [x] depth;
- [x] nodes;
- [x] soft time;
- [x] hard time;
- [x] infinite;
- [x] explicit stop flag.
""",
    "Task 16.4 definitions",
)
write(definitions_path, definitions)

# Live TODO tracker.
todo_path = "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
todo = read(todo_path)
todo = replace_once(
    todo,
    "| 16 | **Active** — Tasks 16.1–16.3 complete; Task 16.4 search limits next. |",
    "| 16 | **Active** — Tasks 16.1–16.4 complete; Task 16.5 responsive cancellation next. |",
    "program summary",
)
todo = replace_once(todo, "- [ ] 16.4 Limits.", "- [x] 16.4 Limits.", "Task 16.4 checkbox")
todo = todo.replace("Task 16.4 search limits is next", "Task 16.5 responsive cancellation is next")
todo = todo.replace(
    "Task 16.3 is complete. Task 16.2 aspiration windows remains open and is next.",
    "Tasks 16.1–16.4 are complete. Task 16.5 responsive cancellation is next.",
)
completion = """### Task 16.4 completion evidence

- Implementation: `crates/chess-search/src/limits.rs`, cancellation-aware root-window orchestration in `crates/chess-search/src/iterative_deepening.rs`, and exact node-entry hooks in `alpha_beta.rs`, `quiescence.rs`, and `cancellation.rs`.
- Public APIs: `SearchLimits`, `SearchStopFlag`, `SearchLimitError`, `SearchLimitTermination`, `LimitedIterativeDeepeningSearchResult`, `iterative_deepening_search_with_limits`, and `iterative_deepening_search_with_limits_and_transposition_table`.
- Supported limits: bounded depth, exact cumulative production-node budget, soft time, hard time, infinite mode, and a clone-shareable atomic explicit-stop flag.
- Validation rejects zero limits, soft time greater than hard time, finite requests without an automatic limit, infinite requests with automatic limits, and infinite requests without a stop flag before table or root mutation.
- Deterministic precedence is explicit stop, hard time, nodes, completed depth, soft time, then the maximum supported depth ceiling.
- Soft time is applied only after a fully exact iteration. Hard time, node limits, and explicit stop are checked through the production alpha-beta/quiescence tree.
- Limit interruption discards the incomplete depth while retaining every preceding exact iteration, canonical best move, legal PV, ponder move, and completed diagnostics.
- `searched_nodes` counts completed work plus interrupted partial work; `incomplete_nodes` exposes only discarded partial work.
- Existing fixed-depth iterative-deepening APIs preserve their prior behavior through the same cancellation-aware internal boundary with `NeverCancelled`.
- Deterministic regressions cover exact depth equivalence, exact node-budget stopping one node into a later depth, finite and infinite preset-stop behavior, invalid-limit fail-fast behavior, deterministic soft/hard clock boundaries, table-generation behavior, and exact position/history/Zobrist restoration.
- Contract documentation: `docs/RUST_SEARCH_LIMITS.md`; `docs/RUST_ITERATIVE_DEEPENING.md` updated through Task 16.4.
- Production implementation commit: `1cbe0264418afbcddc564b1e4972c4819fb0a6f8`.
- Exact clean validated implementation SHA: `8a48ee45199e58db76adee4e4fc4adaf131566d2`.
- Permanent CI run/job: `30780915406` / `91585230626`.
- Results: permanent exclusion audit over 16 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 214 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16.5 responsive cancellation is next. Tasks 16.6–16.7 and the overall Task 16 gate remain open.

"""
todo = insert_before(todo, "# Task 17: Linux UCI executable — NOT STARTED\n", completion, "Task 16.4 evidence")
old_next = """1. Implement Task 16.4 typed search limits for depth, nodes, soft time, hard time, infinite search, and an explicit stop flag.
2. Define deterministic precedence and validation for conflicting or invalid limit combinations.
3. Thread limit checks through iterative deepening and the production tree without weakening exact root restoration.
4. Preserve the last fully completed iteration as the stable result boundary when a later depth reaches a limit.
5. Add fixed regressions for each limit category, boundary behavior, deterministic stop points where applicable, and exact position/history/Zobrist restoration.
6. Keep responsive cancellation latency/fallback details in Task 16.5, the final unified result API in Task 16.6, and check extensions in Task 16.7."""
new_next = """1. Implement Task 16.5 responsive cancellation with a documented bounded node-check interval and latency target.
2. Prove active recursive state unwinds before returning and the exact root position, detached history, and Zobrist identity are restored.
3. Preserve the last fully completed exact iteration when cancellation interrupts a later depth.
4. Define and test the fallback result when cancellation occurs before depth one completes.
5. Add deterministic cancellation-point regressions plus a reproducible cancellation-latency benchmark.
6. Preserve Task 16.4 limit semantics while keeping the final unified result API in Task 16.6 and check extensions in Task 16.7."""
todo = replace_once(todo, old_next, new_next, "immediate operations")
write(todo_path, todo)

# Ralph status.
ralph_path = "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
ralph = read(ralph_path)
ralph = replace_once(
    ralph,
    "**Current phase:** Tasks 16.1–16.3 complete; Task 16.4 search limits is next",
    "**Current phase:** Tasks 16.1–16.4 complete; Task 16.5 responsive cancellation is next",
    "current phase",
)
ralph = replace_once(
    ralph,
    "| 16.3 | `e8afc9959a60519c6d5617963521e1707d37c6a9` | `30776274173` / `91572310565` | safe legal PV reconstruction, ponder support, 204 Rust tests, depth-four perft, and differential oracle green |",
    "| 16.3 | `e8afc9959a60519c6d5617963521e1707d37c6a9` | `30776274173` / `91572310565` | safe legal PV reconstruction, ponder support, 204 Rust tests, depth-four perft, and differential oracle green |\n| 16.4 | `8a48ee45199e58db76adee4e4fc4adaf131566d2` | `30780915406` / `91585230626` | typed depth/node/time/infinite/stop limits, partial-depth discard, 214 Rust tests, depth-four perft, and differential oracle green |",
    "completed-gates row",
)
ralph = ralph.replace("Task 16.4 search limits is next", "Task 16.5 responsive cancellation is next")
ralph = ralph.replace(
    "Task 16.3 is complete. Task 16.2 aspiration windows remains open and is next.",
    "Tasks 16.1–16.4 are complete. Task 16.5 responsive cancellation is next.",
)
ralph_completion = """## Task 16.4 completion

Implemented and validated:

- typed depth, exact cumulative node, soft-time, hard-time, infinite, and explicit-stop limits;
- a clone-shareable atomic `SearchStopFlag` suitable for an external search controller;
- fail-loud validation and deterministic precedence for conflicting or simultaneously reached limits;
- exact production-node accounting through one `on_node` hook per alpha-beta or quiescence node;
- soft-time stopping only at exact iteration boundaries and hard/node/stop interruption inside the production tree;
- preservation of every fully completed exact iteration and rejection of all partial-depth result/PV/ponder data;
- exact searched-node and incomplete-node reporting, including interrupted aspiration work;
- reuse of one bounded TT and exact restoration of position, detached history, and incremental/recomputed Zobrist identity;
- deterministic integration and scripted-clock regressions;
- `docs/RUST_SEARCH_LIMITS.md` and updated `docs/RUST_ITERATIVE_DEEPENING.md`.

Evidence:

- Production implementation commit: `1cbe0264418afbcddc564b1e4972c4819fb0a6f8`.
- Exact clean validated SHA: `8a48ee45199e58db76adee4e4fc4adaf131566d2`.
- Permanent CI run/job: `30780915406` / `91585230626`.
- Results: permanent exclusion audit over 16 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 214 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The exact node-budget regression completes depth one, enters exactly one node of depth two, reports that node as incomplete work, discards the partial depth, and preserves the complete depth-one result.
- Preset finite and infinite stop requests terminate before table generation or root mutation; invalid combinations fail before allocation or search mutation.
- Scripted clocks prove soft-time boundary stopping and hard-time precedence without wall-clock flakiness.
- The implementation passed its first compiler and strict-Clippy iteration without source corrections or suppressions.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16.5 responsive cancellation is next. Tasks 16.6–16.7 and the overall Task 16 gate remain open.

"""
ralph = insert_before(ralph, "## Task 16 active scope\n", ralph_completion, "Ralph Task 16.4 section")
ralph = replace_once(
    ralph,
    "- [ ] Implement Task 16.4 search limits.",
    "- [x] Implement Task 16.4 search limits.",
    "Ralph Task 16.4 checkbox",
)
ralph = replace_once(
    ralph,
    "No pull request has been created; work remains on `rust-engine`. Task 16.4 search limits is the next operation.",
    "No pull request has been created; work remains on `rust-engine`. Task 16.5 responsive cancellation is the next operation.",
    "Ralph closing sentence",
)
write(ralph_path, ralph)

print("Task 16.4 tracker closure applied")
