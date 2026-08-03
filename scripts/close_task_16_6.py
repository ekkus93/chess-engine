from pathlib import Path
import sys

root = Path(sys.argv[1])

def read(path: str) -> str:
    return (root / path).read_text(encoding="utf-8")

def write(path: str, content: str) -> None:
    (root / path).write_text(content, encoding="utf-8")

def replace_once(content: str, old: str, new: str, label: str) -> str:
    count = content.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    return content.replace(old, new, 1)

# Detailed task definitions.
definitions_path = "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
definitions = read(definitions_path)
for item in [
    "best move;",
    "ponder move;",
    "typed score;",
    "completed depth;",
    "selective depth;",
    "nodes and qnodes;",
    "elapsed time;",
    "PV;",
    "termination reason.",
]:
    definitions = replace_once(
        definitions,
        f"- [ ] {item}",
        f"- [x] {item}",
        f"Task 16.6 definition {item}",
    )
write(definitions_path, definitions)

# Live TODO tracker.
todo_path = "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
todo = read(todo_path)
todo = replace_once(
    todo,
    "| 16 | **Active** — Tasks 16.1–16.5 complete; Task 16.6 final result API next. |",
    "| 16 | **Active** — Tasks 16.1–16.6 complete; Task 16.7 optional bounded check extension next. |",
    "program summary",
)
todo = replace_once(todo, "- [ ] 16.6 Result API.", "- [x] 16.6 Result API.", "Task 16.6 checkbox")

# Normalize stale next-operation statements without rewriting historical evidence.
replacements = {
    "Tasks 16.1–16.3 are complete. Task 16.6 final result API is next; cancellation recovery, the final result API, and extensions remain deferred.":
        "Tasks 16.1–16.6 are complete. Task 16.7 optional bounded check extension is next.",
    "Task 16.6 final result API is next. Tasks 16.5–16.7 and the overall Task 16 gate remain open.":
        "Task 16.7 optional bounded check extension is next; Task 16.7 and the overall Task 16 gate remain open.",
    "Tasks 16.1–16.5 are complete. Task 16.6 final result API is the next operation.":
        "Tasks 16.1–16.6 are complete. Task 16.7 optional bounded check extension is the next operation.",
    "Task 16.6 final result API is next. Tasks 16.6–16.7 and the overall Task 16 gate remain open.":
        "Task 16.7 optional bounded check extension is next; Task 16.7 and the overall Task 16 gate remain open.",
    "Task 16.6 final result API is next. Task 16.7 and the overall Task 16 gate remain open.":
        "Task 16.7 optional bounded check extension is next; Task 16.7 and the overall Task 16 gate remain open.",
}
for old, new in replacements.items():
    todo = todo.replace(old, new)

evidence = """### Task 16.6 completion evidence

- Implementation: unified request snapshot and aggregate accounting in `crates/chess-search/src/iterative_deepening.rs`, typed node-kind hooks in `crates/chess-search/src/cancellation.rs` and `limits.rs`, and alpha-beta/quiescence accounting in `alpha_beta.rs`, `aspiration.rs`, and `quiescence.rs`.
- Public API: `SearchResult`, returned by both limit-controlled iterative-deepening entry points; `LimitedIterativeDeepeningSearchResult` remains a compatibility alias.
- The authoritative snapshot exposes best move, ponder move, optional exact typed score, completed depth, selective depth, total nodes, total qnodes, elapsed time, legal principal variation, and typed termination reason.
- Best move, score, ponder move, completed depth, and PV come only from the deepest fully completed exact iteration. Interrupted partial-depth data cannot replace them.
- When no iteration completes, `best_move` may expose the deterministic Task 16.5 legal fallback, while score, ponder move, completed depth, and PV remain absent or zero. A terminal fallback exposes no move.
- Request-wide nodes, qnodes, selective depth, and elapsed time include interrupted partial work. Detailed completed iterations, aspiration diagnostics, TT diagnostics, and compatibility accessors remain available.
- `qnodes` is a subset of production nodes. `selective_depth` is the deepest root-relative alpha-beta or quiescence ply entered. Specialized cancellation hooks preserve the one-node polling bound for existing probes through default delegation.
- Four focused result-shape regressions cover exact completion, cancellation after a completed iteration, legal pre-depth-one fallback, and terminal pre-depth-one fallback. Existing limit tests continue to cover depth, node, soft-time, hard-time, explicit-stop, and infinite-mode behavior.
- Contract documentation: `docs/RUST_SEARCH_RESULT_API.md`; iterative-deepening and limit contracts updated through Task 16.6.
- Production implementation commit: `780bcc6bf9ba17afb9e9443e3a106b722d4c43fe`.
- Exact clean validated implementation SHA: `dcde800f4c5a08c07fe57724ed672f2abd122157`.
- Permanent CI run/job: `30783666840` / `91593059900`.
- Results: permanent exclusion audit over 16 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 222 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The implementation passed its first compiler, strict-Clippy, test, rustdoc, build, perft, and oracle iteration without a source correction or suppression.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16.7 optional bounded check extension is next. The overall Task 16 gate remains open.

"""
todo = replace_once(todo, "# Task 17: Linux UCI executable — NOT STARTED\n", evidence + "# Task 17: Linux UCI executable — NOT STARTED\n", "Task 16.6 evidence insertion")

old_ops = """## Immediate next operations

1. Implement Task 16.6 as one unified public search-result API over completed, limited, and pre-depth-one fallback outcomes.
2. Expose best move, ponder move, typed score, completed depth, selective depth, nodes and qnodes, elapsed time, legal PV, and typed termination reason.
3. Keep exact completed-iteration data distinct from deterministic unscored fallback data.
4. Preserve aspiration exactness, one-node cancellation responsiveness, limit precedence, legal PV reconstruction, and exact root restoration.
5. Add deterministic result-shape tests for normal completion, every limit category, cancellation after a completed depth, cancellation before depth one, and terminal roots.
6. Leave Task 16.7 check extensions optional and keep the overall Task 16 gate open until the result API and final integration evidence are complete."""
new_ops = """## Immediate next operations

1. Evaluate and implement Task 16.7 only as a bounded, explicitly optional check extension that cannot create unbounded selective depth.
2. Define exact extension eligibility, maximum extension budget, interaction with mate-distance scoring, and cancellation/limit accounting before implementation.
3. Prove the extension preserves deterministic root choice, legal PV reconstruction, TT depth semantics, and exact position/history/Zobrist restoration.
4. Add tactical witnesses showing useful horizon improvement without weakening the Task 16.5 cancellation bound or Task 16.6 result accounting.
5. Run the overall Task 16 integration gate after Task 16.7 is either implemented and validated or explicitly declined with documented rationale.
6. Keep Task 17 UCI worker/protocol integration deferred until the Task 16 gate is complete."""
todo = replace_once(todo, old_ops, new_ops, "immediate operations")
write(todo_path, todo)

# Ralph-loop status.
status_path = "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
status = read(status_path)
status = replace_once(
    status,
    "**Current phase:** Tasks 16.1–16.5 complete; Task 16.6 final result API is next",
    "**Current phase:** Tasks 16.1–16.6 complete; Task 16.7 optional bounded check extension is next",
    "current phase",
)
status = replace_once(
    status,
    "| 16.5 | `128f52e8fb7d7e9974605fc840eb13d3ecc021a6` | `30782361257` / `91589434579` | one-node cancellation bound, deterministic fallback, latency benchmark, 218 Rust tests, depth-four perft, and differential oracle green |",
    "| 16.5 | `128f52e8fb7d7e9974605fc840eb13d3ecc021a6` | `30782361257` / `91589434579` | one-node cancellation bound, deterministic fallback, latency benchmark, 218 Rust tests, depth-four perft, and differential oracle green |\n| 16.6 | `dcde800f4c5a08c07fe57724ed672f2abd122157` | `30783666840` / `91593059900` | unified typed result snapshot, request-wide node/qnode/seldepth/time accounting, 222 Rust tests, depth-four perft, and differential oracle green |",
    "completed-gates row",
)

for old, new in {
    "Tasks 16.1–16.4 are complete. Task 16.6 final result API is next.":
        "Tasks 16.1–16.6 are complete. Task 16.7 optional bounded check extension is next.",
    "Task 16.6 final result API is next. Tasks 16.6–16.7 and the overall Task 16 gate remain open.":
        "Task 16.7 optional bounded check extension is next; Task 16.7 and the overall Task 16 gate remain open.",
    "Task 16.6 final result API is next. Task 16.7 and the overall Task 16 gate remain open.":
        "Task 16.7 optional bounded check extension is next; Task 16.7 and the overall Task 16 gate remain open.",
}.items():
    status = status.replace(old, new)

status_evidence = """## Task 16.6 completion

Implemented and validated:

- one unified `SearchResult` snapshot for limit-controlled iterative deepening;
- authoritative best move, optional exact typed score, ponder move, completed depth, legal PV, and typed termination reason;
- request-wide production-node, quiescence-node, selective-depth, and elapsed-time accounting, including interrupted partial work;
- exact completed-iteration preservation with no promotion of partial aspiration or cancellation data;
- explicit unscored legal and terminal fallback semantics before depth one;
- compatibility through `LimitedIterativeDeepeningSearchResult` and `searched_nodes` while detailed per-depth diagnostics remain available;
- specialized alpha-beta and quiescence node hooks that preserve existing cancellation probes and the one-node bound;
- focused normal, interrupted, legal-fallback, and terminal-fallback regressions;
- `docs/RUST_SEARCH_RESULT_API.md` and updated iterative-deepening/limit contracts.

Evidence:

- Production implementation commit: `780bcc6bf9ba17afb9e9443e3a106b722d4c43fe`.
- Exact clean validated SHA: `dcde800f4c5a08c07fe57724ed672f2abd122157`.
- Permanent CI run/job: `30783666840` / `91593059900`.
- Results: permanent exclusion audit over 16 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 222 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Exact completion tests prove all headline fields agree with the deepest exact iteration and that qnodes/selective depth are internally consistent.
- Interruption tests prove total work includes partial nodes/qnodes/seldepth/time while score, move, PV, ponder, and completed depth remain anchored to the prior exact iteration.
- Pre-depth-one tests prove the legal fallback never invents score or PV data and the terminal fallback returns no move.
- The implementation passed its first compiler and strict-Clippy iteration without source corrections or suppressions.
- The clean implementation delta contains only seven search modules, one integration-test file, and three contract documents.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16.7 optional bounded check extension is next. The overall Task 16 gate remains open.

"""
status = replace_once(status, "## Task 16 active scope\n", status_evidence + "## Task 16 active scope\n", "Task 16.6 status insertion")
status = replace_once(status, "- [ ] Implement Task 16.6 final result API.", "- [x] Implement Task 16.6 final result API.", "active-scope checkbox")
status = replace_once(
    status,
    "No pull request has been created; work remains on `rust-engine`. Task 16.6 final result API is the next operation.",
    "No pull request has been created; work remains on `rust-engine`. Task 16.7 optional bounded check extension is the next operation.",
    "status footer",
)
write(status_path, status)

print("Task 16.6 tracker closure applied")
