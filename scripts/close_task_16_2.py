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
    """## 16.2 Aspiration windows

- [ ] Center on prior iteration score.
- [ ] Detect fail-low and fail-high.
- [ ] Re-search with a safe expanded/full window.
- [ ] Record retry diagnostics.
- [ ] Add regression proving a bound cannot be mistaken for an exact root score.
""",
    """## 16.2 Aspiration windows

- [x] Center on prior iteration score.
- [x] Detect fail-low and fail-high.
- [x] Re-search with a safe expanded/full window.
- [x] Record retry diagnostics.
- [x] Add regression proving a bound cannot be mistaken for an exact root score.
""",
    "Task 16.2 definitions",
)
write(definitions_path, definitions)

# Live tracker.
todo_path = "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
todo = read(todo_path)
todo = replace_once(
    todo,
    "| 16 | **Active** — Tasks 16.1 and 16.3 complete; Task 16.2 aspiration windows next. |",
    "| 16 | **Active** — Tasks 16.1–16.3 complete; Task 16.4 search limits next. |",
    "Task 16 program summary",
)
todo = replace_once(
    todo,
    "- [ ] 16.2 Aspiration windows.",
    "- [x] 16.2 Aspiration windows.",
    "Task 16.2 live checkbox",
)
todo = todo.replace(
    "- Task 16.2 aspiration windows is next. Limits, cancellation recovery, the final result API, and extensions remain deferred.",
    "- Tasks 16.1–16.3 are complete. Task 16.4 search limits is next; cancellation recovery, the final result API, and extensions remain deferred.",
)
todo = todo.replace(
    "- Task 16.2 aspiration windows remains open and is the next operation.",
    "- Task 16.2 aspiration windows is complete. Task 16.4 search limits is the next operation.",
)
task_16_2_evidence = """### Task 16.2 completion evidence

- Implementation: `crates/chess-search/src/aspiration.rs`, the typed root-window boundary in `crates/chess-search/src/alpha_beta.rs`, and aspiration orchestration in `crates/chess-search/src/iterative_deepening.rs`.
- Public APIs: `AspirationWindowOutcome`, `AspirationWindowAttempt`, `AspirationWindowDiagnostics`, `DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS`, and per-iteration `aspiration_diagnostics`.
- Depth one searches the complete supported score domain. Later depths center a deterministic ±50-centipawn window on the immediately prior exact score.
- Initial fail-low and fail-high results remain typed upper/lower bounds: `reported_score` is observable for diagnostics, while `exact_score` returns `None`.
- A failed bounded attempt receives exactly one complete-window retry. Only an exact attempt can become the completed iteration result, best move, PV, or ponder source.
- Every attempt at one depth shares one TT generation. Per-attempt diagnostics are retained, while iteration nodes and TT counters aggregate all attempts with checked/saturating arithmetic.
- Mate-boundary centers fall back directly to the complete window; there is no unbounded widening loop or unbounded allocation.
- Deterministic regressions force both fail-low and fail-high, prove bounds cannot be promoted to exact scores, and recover the same score and canonical best move as an independent full-window search.
- Contract documentation: `docs/RUST_ASPIRATION_WINDOWS.md`; `docs/RUST_ITERATIVE_DEEPENING.md` updated for Tasks 16.1–16.3.
- Production implementation commit: `c1d1c61caf85fd230b48a4b9026b9aa8b7ae79bf`.
- Exact clean validated implementation SHA: `8af24520fd72faffff1cab74581f056a083cfb13`.
- Permanent CI run/job: `30779589438` / `91581508274`.
- Results: permanent exclusion audit over 15 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 206 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Initial validation iterations found an audit-witness shape requirement, one invalid private `const fn` qualifier, and one eight-argument internal constructor rejected by strict Clippy. Each was corrected directly without changing the aspiration contract or adding a suppression.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16.4 search limits is next. Tasks 16.5–16.7 and the overall Task 16 gate remain open.

"""
todo = insert_before(
    todo,
    "### Task 16.3 completion evidence\n",
    task_16_2_evidence,
    "Task 16.2 evidence insertion",
)
next_marker = "## Immediate next operations\n"
if todo.count(next_marker) != 1:
    raise RuntimeError("live tracker immediate-next marker missing or duplicated")
todo = todo.split(next_marker, 1)[0] + """## Immediate next operations

1. Implement Task 16.4 typed search limits for depth, nodes, soft time, hard time, infinite search, and an explicit stop flag.
2. Define deterministic precedence and validation for conflicting or invalid limit combinations.
3. Thread limit checks through iterative deepening and the production tree without weakening exact root restoration.
4. Preserve the last fully completed iteration as the stable result boundary when a later depth reaches a limit.
5. Add fixed regressions for each limit category, boundary behavior, deterministic stop points where applicable, and exact position/history/Zobrist restoration.
6. Keep responsive cancellation latency/fallback details in Task 16.5, the final unified result API in Task 16.6, and check extensions in Task 16.7.
"""
write(todo_path, todo)

# Ralph-loop status.
ralph_path = "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
ralph = read(ralph_path)
ralph = replace_once(
    ralph,
    "**Current phase:** Tasks 16.1 and 16.3 complete; Task 16.2 aspiration windows is next",
    "**Current phase:** Tasks 16.1–16.3 complete; Task 16.4 search limits is next",
    "Ralph current phase",
)
ralph = replace_once(
    ralph,
    "| 16.1 | `886ad953952b3a409800fcf7e8699365f94f0271` | `30772536115` / `91562076526` | full-window iterative deepening, five focused tests, 198 Rust tests, depth-four perft, and differential oracle green |\n| 16.3 | `e8afc9959a60519c6d5617963521e1707d37c6a9` | `30776274173` / `91572310565` | safe legal PV reconstruction, ponder support, 204 Rust tests, depth-four perft, and differential oracle green |",
    "| 16.1 | `886ad953952b3a409800fcf7e8699365f94f0271` | `30772536115` / `91562076526` | full-window iterative deepening, five focused tests, 198 Rust tests, depth-four perft, and differential oracle green |\n| 16.2 | `8af24520fd72faffff1cab74581f056a083cfb13` | `30779589438` / `91581508274` | bounded aspiration retries, fail-low/fail-high exact recovery, 206 Rust tests, depth-four perft, and differential oracle green |\n| 16.3 | `e8afc9959a60519c6d5617963521e1707d37c6a9` | `30776274173` / `91572310565` | safe legal PV reconstruction, ponder support, 204 Rust tests, depth-four perft, and differential oracle green |",
    "Ralph completed table",
)
task_16_2_ralph = """## Task 16.2 completion

Implemented and validated:

- a typed internal root-window search boundary that classifies exact, fail-low, and fail-high outcomes;
- depth-one complete-window search and later ±50-centipawn windows centered on the prior exact completed score;
- exactly one complete-window recovery attempt after either bound outcome;
- an invariant that bound attempts expose no exact score and cannot populate the completed iteration, PV, or ponder result;
- one transposition-table generation per depth, including retries;
- immutable per-attempt alpha/beta, outcome, score, node, TT-counter, hash-full, and generation diagnostics;
- checked aggregate node accounting and saturating aggregate TT diagnostics across attempts;
- mate-boundary complete-window fallback and a fail-loud unexpected-full-window-bound error;
- deterministic fail-low/fail-high recovery regressions and updated iterative-deepening equivalence/restoration coverage;
- `docs/RUST_ASPIRATION_WINDOWS.md` and updated `docs/RUST_ITERATIVE_DEEPENING.md`.

Evidence:

- Production implementation commit: `c1d1c61caf85fd230b48a4b9026b9aa8b7ae79bf`.
- Exact clean validated SHA: `8af24520fd72faffff1cab74581f056a083cfb13`.
- Permanent CI run/job: `30779589438` / `91581508274`.
- Results: permanent exclusion audit over 15 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 206 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Both forced bound regressions prove `exact_score() == None` before one complete-window retry recovers the independent exact score and canonical move.
- Retry diagnostics prove one generation per logical depth and exact per-attempt plus aggregate accounting.
- Position, detached history, incremental Zobrist identity, PV legality, and ponder behavior remain restored and deterministic.
- The validation loop corrected the permanent audit witness, a private non-const comparison, and a strict-Clippy constructor shape without suppressions or semantic relaxation.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16.4 search limits is next.

"""
ralph = insert_before(
    ralph,
    "## Task 16.3 completion\n",
    task_16_2_ralph,
    "Ralph Task 16.2 section insertion",
)
ralph = replace_once(
    ralph,
    "- [ ] Implement Task 16.2 aspiration windows.",
    "- [x] Implement Task 16.2 aspiration windows.",
    "Ralph Task 16.2 checkbox",
)
ralph = ralph.replace(
    "Task 16.2 aspiration windows is the next operation.",
    "Task 16.4 search limits is the next operation.",
)
ralph = ralph.replace(
    "Task 16.2 aspiration windows is next.",
    "Task 16.4 search limits is next.",
)
write(ralph_path, ralph)

print("Task 16.2 trackers closed")
