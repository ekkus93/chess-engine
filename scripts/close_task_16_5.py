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

# Detailed task definitions.
definitions_path = "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
definitions = read(definitions_path)
definitions = replace_once(
    definitions,
    """## 16.5 Responsive cancellation

- [ ] Check inside the tree at bounded node intervals.
- [ ] Stop before arbitrary full-depth completion.
- [ ] Preserve root position.
- [ ] Return last fully completed iteration.
- [ ] Define fallback when no iteration completed.
- [ ] Benchmark cancellation latency.
""",
    """## 16.5 Responsive cancellation

- [x] Check inside the tree at bounded node intervals.
- [x] Stop before arbitrary full-depth completion.
- [x] Preserve root position.
- [x] Return last fully completed iteration.
- [x] Define fallback when no iteration completed.
- [x] Benchmark cancellation latency.
""",
    "Task 16.5 definitions",
)
write(definitions_path, definitions)

# Authoritative TODO tracker.
todo_path = "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
todo = read(todo_path)
todo = replace_once(
    todo,
    "| 16 | **Active** — Tasks 16.1–16.4 complete; Task 16.5 responsive cancellation next. |",
    "| 16 | **Active** — Tasks 16.1–16.5 complete; Task 16.6 final result API next. |",
    "program summary",
)
todo = replace_once(todo, "- [ ] 16.5 Cancellation.", "- [x] 16.5 Cancellation.", "Task 16.5 checkbox")
# Normalize prior next-operation wording without rewriting historical evidence.
todo = todo.replace("Task 16.5 responsive cancellation is next", "Task 16.6 final result API is next")
todo = todo.replace(
    "Task 16.5 responsive cancellation is next. Tasks 16.5–16.7 and the overall Task 16 gate remain open.",
    "Task 16.6 final result API is next. Tasks 16.6–16.7 and the overall Task 16 gate remain open.",
)
todo = todo.replace(
    "Task 16.2 aspiration windows is complete. Task 16.4 search limits is the next operation.",
    "Tasks 16.1–16.5 are complete. Task 16.6 final result API is the next operation.",
)
completion = """### Task 16.5 completion evidence

- Implementation: the formal polling contract in `crates/chess-search/src/cancellation.rs`, deterministic fallback integration in `crates/chess-search/src/iterative_deepening.rs`, and release benchmarking in `crates/chess-tools`.
- Public APIs: `CANCELLATION_CHECK_INTERVAL_NODES`, `SearchCancellationFallback`, and `LimitedIterativeDeepeningSearchResult::fallback`.
- The production polling interval is explicitly one alpha-beta or quiescence node. Child boundaries also poll before applying the next legal move, so cancellation cannot require completion of an arbitrary subtree or depth.
- Interrupted search frames pop reversible history and unmake every active move before propagating typed cancellation. Position, detached history, current history identity, incremental Zobrist identity, and recomputed Zobrist identity restore exactly.
- An interrupted partial depth contributes no exact score, move, PV, ponder move, aspiration record, or completed-node total. Every earlier fully completed exact iteration remains authoritative.
- When no iteration completed, the result exposes either `FirstLegalMove`, selected from deterministic legal-generation order at the unchanged root, or `NoLegalMove` for a terminal root. The fallback is unscored and is not represented as a completed depth.
- Deterministic regressions inject a request after 64 production nodes, prove observation within the one-node bound, cover one-node and preset-stop fallbacks, preserve the prior completed iteration, and verify exact root restoration.
- Release benchmark command: `cargo run --locked -p chess-tools --release -- cancel-bench ITERATIONS`.
- Hosted smoke output for four samples: `cancel<TAB>4<TAB>64<TAB>0<TAB>404<TAB>186<TAB>5435046110819296062`; it observed zero additional nodes after each request. Nanosecond values are informational, while the one-node bound is enforced.
- Contract documentation: `docs/RUST_RESPONSIVE_CANCELLATION.md`; `docs/RUST_SEARCH_LIMITS.md` and `docs/RUST_ITERATIVE_DEEPENING.md` updated through Task 16.5.
- Production implementation commit: `68f86a53c31dd5f1448e99fb7def8bb220f2222f`.
- Exact clean validated implementation SHA: `128f52e8fb7d7e9974605fc840eb13d3ecc021a6`.
- Permanent CI run/job: `30782361257` / `91589434579`.
- Results: permanent exclusion audit over 16 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 218 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The first implementation validation exposed one localized Rust iterator tail-expression lifetime error. Materializing the fallback value before return corrected it without changing behavior or adding a suppression.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16.6 final result API is next. Task 16.7 and the overall Task 16 gate remain open.

"""
todo = insert_before(todo, "# Task 17: Linux UCI executable — NOT STARTED\n", completion, "Task 16.5 evidence")
old_next = """1. Implement Task 16.5 responsive cancellation with a documented bounded node-check interval and latency target.
2. Prove active recursive state unwinds before returning and the exact root position, detached history, and Zobrist identity are restored.
3. Preserve the last fully completed exact iteration when cancellation interrupts a later depth.
4. Define and test the fallback result when cancellation occurs before depth one completes.
5. Add deterministic cancellation-point regressions plus a reproducible cancellation-latency benchmark.
6. Preserve Task 16.4 limit semantics while keeping the final unified result API in Task 16.6 and check extensions in Task 16.7."""
new_next = """1. Implement Task 16.6 as one unified public search-result API over completed, limited, and pre-depth-one fallback outcomes.
2. Expose best move, ponder move, typed score, completed depth, selective depth, nodes and qnodes, elapsed time, legal PV, and typed termination reason.
3. Keep exact completed-iteration data distinct from deterministic unscored fallback data.
4. Preserve aspiration exactness, one-node cancellation responsiveness, limit precedence, legal PV reconstruction, and exact root restoration.
5. Add deterministic result-shape tests for normal completion, every limit category, cancellation after a completed depth, cancellation before depth one, and terminal roots.
6. Leave Task 16.7 check extensions optional and keep the overall Task 16 gate open until the result API and final integration evidence are complete."""
todo = replace_once(todo, old_next, new_next, "immediate operations")
write(todo_path, todo)

# Ralph status tracker.
ralph_path = "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
ralph = read(ralph_path)
ralph = replace_once(
    ralph,
    "**Current phase:** Tasks 16.1–16.4 complete; Task 16.5 responsive cancellation is next",
    "**Current phase:** Tasks 16.1–16.5 complete; Task 16.6 final result API is next",
    "current phase",
)
ralph = replace_once(
    ralph,
    "| 16.4 | `8a48ee45199e58db76adee4e4fc4adaf131566d2` | `30780915406` / `91585230626` | typed depth/node/time/infinite/stop limits, partial-depth discard, 214 Rust tests, depth-four perft, and differential oracle green |",
    "| 16.4 | `8a48ee45199e58db76adee4e4fc4adaf131566d2` | `30780915406` / `91585230626` | typed depth/node/time/infinite/stop limits, partial-depth discard, 214 Rust tests, depth-four perft, and differential oracle green |\n| 16.5 | `128f52e8fb7d7e9974605fc840eb13d3ecc021a6` | `30782361257` / `91589434579` | one-node cancellation bound, deterministic fallback, latency benchmark, 218 Rust tests, depth-four perft, and differential oracle green |",
    "completed-gates row",
)
ralph = ralph.replace("Task 16.5 responsive cancellation is next", "Task 16.6 final result API is next")
ralph = ralph.replace(
    "Task 16.3 is complete. Task 16.2 aspiration windows remains open and is next.",
    "Tasks 16.1–16.5 are complete. Task 16.6 final result API is next.",
)
completion_ralph = """## Task 16.5 completion

Implemented and validated:

- an exported one-production-node maximum cancellation polling interval;
- cancellation checks at every alpha-beta and quiescence node plus child boundaries before move application;
- typed cancellation that unwinds every active move and reversible history entry before reaching the root;
- preservation of the deepest fully completed exact iterative-deepening result while discarding all partial-depth data;
- deterministic `FirstLegalMove` and terminal `NoLegalMove` fallbacks when depth one never completes;
- exact position, detached history, history identity, incremental Zobrist, and recomputed Zobrist restoration;
- a reproducible release cancellation benchmark with an enforced node bound, informational wall-clock measurements, and deterministic checksum;
- focused integration regressions and `docs/RUST_RESPONSIVE_CANCELLATION.md`.

Evidence:

- Production implementation commit: `68f86a53c31dd5f1448e99fb7def8bb220f2222f`.
- Exact clean validated SHA: `128f52e8fb7d7e9974605fc840eb13d3ecc021a6`.
- Permanent CI run/job: `30782361257` / `91589434579`.
- Results: permanent exclusion audit over 16 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 218 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The deterministic in-tree witness issues a request after 64 nodes, observes it within the exported one-node bound, returns typed cancellation before depth completion, and restores every root invariant.
- The release smoke output was `cancel<TAB>4<TAB>64<TAB>0<TAB>404<TAB>186<TAB>5435046110819296062`: four samples, zero maximum additional nodes, 404 total measured nanoseconds, 186 maximum measured nanoseconds, and a stable checksum.
- One-node-budget and preset-stop tests prove a deterministic legal fallback; a terminal preset-stop test proves the explicit no-legal-move fallback; completed-depth tests prove fallback suppression and last-iteration preservation.
- The initial compiler iteration found one fallback iterator lifetime issue. A local materialized value fixed it without semantic relaxation or lint suppression.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16.6 final result API is next. Task 16.7 and the overall Task 16 gate remain open.

"""
ralph = insert_before(ralph, "## Task 16 active scope\n", completion_ralph, "Ralph Task 16.5 section")
ralph = replace_once(
    ralph,
    "- [ ] Implement Task 16.5 responsive cancellation.",
    "- [x] Implement Task 16.5 responsive cancellation.",
    "Ralph Task 16.5 checkbox",
)
ralph = replace_once(
    ralph,
    "No pull request has been created; work remains on `rust-engine`. Task 16.5 responsive cancellation is the next operation.",
    "No pull request has been created; work remains on `rust-engine`. Task 16.6 final result API is the next operation.",
    "Ralph closing sentence",
)
write(ralph_path, ralph)

print("Task 16.5 tracker closure applied")
