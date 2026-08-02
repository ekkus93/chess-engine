#!/usr/bin/env python3
"""Apply the exact documentation closure for validated Task 13."""

from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: close_task_13.py REPOSITORY_ROOT")

    root = Path(sys.argv[1]).resolve()
    todo_path = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
    ralph_path = root / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
    todo = todo_path.read_text()
    ralph = ralph_path.read_text()

    todo = replace_once(
        todo,
        "| 13 | **Active** — Tasks 13.1–13.4 complete; Task 13.5 terminal fixtures are next. |",
        "| 13 | **Complete** — reference negamax, alpha-beta, shallow equivalence, immutability, and terminal/mate-distance fixtures. |",
        "TODO program summary",
    )
    todo = replace_once(
        todo,
        "# Task 13: Reference search and alpha-beta — ACTIVE",
        "# Task 13: Reference search and alpha-beta — COMPLETE",
        "TODO Task 13 heading",
    )
    todo = replace_once(todo, "- [ ] 13.5 Terminal fixtures.", "- [x] 13.5 Terminal fixtures.", "TODO 13.5 checkbox")
    todo = replace_once(todo, "- [ ] Task 13 gate.", "- [x] Task 13 gate.", "TODO Task 13 gate")
    todo = replace_once(
        todo,
        "- Task 13.5 is next; the overall Task 13 gate remains open.\n\n# Task 14: Quiescence and ordering — NOT STARTED",
        """- Task 13.5 and the overall Task 13 gate are complete.

### Task 13.5 and Task 13 gate completion evidence

- Integration suite: `crates/chess-search/tests/search_terminals.rs`.
- Contract documentation: `docs/RUST_SEARCH_TERMINAL_FIXTURES.md`.
- Exact validated implementation SHA: `7ca429b0c883bbb8484d3eb3a4af7d96cdb57201`.
- Permanent CI run/job: `30745120833` / `91489299233`.
- Results: rustfmt, Cargo check, strict Clippy, 135 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc, debug/release builds, and independent differential validation passed.
- Terminal roots cover checkmate precedence at halfmove `150`, stalemate, dead position, claimable fifty-move draw, automatic seventy-five-move draw, claimable threefold repetition, and automatic fivefold repetition. Every terminal/draw root returns one node and no best move.
- Shorter-mate fixture `7k/5Q2/6K1/8/8/8/8/8 w - - 0 1` proves `f7e8` scores `mate_in(1)`, `f7a7` scores `mate_in(3)`, and the full root selects an immediate mate.
- Longer-survival fixture `4Q2k/8/4K3/8/8/8/8/8 b - - 0 1` proves `h8g7` scores `mated_in(6)`, `h8h7` scores `mated_in(4)`, and the full root selects `h8g7`.
- Reference and alpha-beta search agree on exact scores and deterministic root best moves; alpha-beta visits no more nodes than reference search on paired full-root fixtures.
- Individual root-move oracles normalize separately searched child-root mate scores by one ply before comparing them at the parent root.
- Every full-root and individual-root-move invocation restores logical position, detached history, incremental/recomputed Zobrist identity, and enforceable invariants exactly.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13 is complete. Task 14.1 quiescence is next.

# Task 14: Quiescence and ordering — NOT STARTED""",
        "TODO Task 13.5 evidence insertion",
    )
    todo = replace_once(
        todo,
        """1. Implement Task 13.5 as a dedicated terminal and mate-distance fixture suite.
2. Cover mate in one, already mated, stalemate, claimable draws, and automatic draws for both reference and alpha-beta search.
3. Add a position with multiple forced mates and prove the shorter mate receives the higher score and is selected.
4. Add a forced-loss position with multiple continuations and prove the engine selects the line that delays mate longest.
5. Reconfirm exact reference/alpha-beta scores, legal best moves, and root position/Zobrist/history restoration for every terminal fixture.
6. Close the overall Task 13 gate only after Task 13.5 passes the full exact-head permanent validation suite.""",
        """1. Begin Task 14.1 with a correctness-first quiescence-search contract over the existing alpha-beta search.
2. Define the stand-pat convention, tactical move scope, terminal/draw handling, and mate-distance propagation before adding heuristics.
3. Search legal captures, promotions, and required check evasions through source-bound legal tokens and exact make/unmake; do not use clone-per-child.
4. Add a reference tactical-leaf oracle and fixed horizon-effect fixtures before integrating quiescence into normal alpha-beta leaves.
5. Preserve Task 13 score, cancellation, history, Zobrist, and restoration contracts at every quiescence exit path.
6. Keep Task 14.2 tactical ordering, Task 14.3 quiet ordering, transposition tables, and production limits out of Task 14.1.""",
        "TODO immediate operations",
    )

    ralph = replace_once(
        ralph,
        "**Current phase:** Tasks 13.1–13.4 complete; Task 13.5 terminal fixtures are next",
        "**Current phase:** Task 13 complete; Task 14.1 quiescence is next",
        "Ralph current phase",
    )
    ralph = replace_once(
        ralph,
        "| 13.4 | `3644e032504b604c210796f1e6c7ef056d05e94b` | `30743519630` / `91485044296` | completion/cancellation immutability, 131 Rust tests, depth-four perft, and differential oracle green |",
        """| 13.4 | `3644e032504b604c210796f1e6c7ef056d05e94b` | `30743519630` / `91485044296` | completion/cancellation immutability, 131 Rust tests, depth-four perft, and differential oracle green |
| 13.5 / 13 | `7ca429b0c883bbb8484d3eb3a4af7d96cdb57201` | `30745120833` / `91489299233` | terminal/mate-distance fixtures and full Task 13 gate, 135 Rust tests, depth-four perft, and differential oracle green |""",
        "Ralph Task 13 evidence row",
    )
    ralph = replace_once(
        ralph,
        "- Task 13.5 remains not started; Task 16 still owns full limits, stop-token, iterative-deepening, and partial-result policy.\n\n## Task 13 active scope",
        """- Task 13.5 and the overall Task 13 gate are complete; Task 16 still owns full limits, stop-token, iterative-deepening, and partial-result policy.

## Task 13.5 and Task 13 completion

Implemented and validated:

- fixed one-node terminal roots for checkmate precedence, stalemate, dead position, fifty/seventy-five-move draws, and threefold/fivefold repetition draws;
- exact reference/alpha-beta score, best-move, and node-count agreement;
- a shorter-mate witness where `f7e8` is `mate_in(1)` and `f7a7` is `mate_in(3)`;
- a longer-survival witness where `h8g7` is `mated_in(6)` and `h8h7` is `mated_in(4)`;
- deterministic immediate-mate selection at the winning root and unique `h8g7` selection at the forced-loss root;
- explicit one-ply mate normalization for independently searched child roots;
- exact logical-position, detached-history, invariant, and incremental/recomputed-Zobrist restoration after every full-root and per-move oracle search;
- `crates/chess-search/tests/search_terminals.rs`;
- `docs/RUST_SEARCH_TERMINAL_FIXTURES.md`.

Evidence:

- Exact validated implementation SHA: `7ca429b0c883bbb8484d3eb3a4af7d96cdb57201`.
- Permanent CI run/job: `30745120833` / `91489299233`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 135 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13 is complete; Task 14.1 quiescence is next.

## Task 13 completed scope""",
        "Ralph Task 13.5 insertion",
    )
    ralph = replace_once(
        ralph,
        "- [ ] Add mate-in-one, mated, stalemate, draw, shorter-mate, and longer-survival fixtures.",
        "- [x] Add mate-in-one, mated, stalemate, draw, shorter-mate, and longer-survival fixtures.",
        "Ralph fixture checkbox",
    )
    ralph = replace_once(
        ralph,
        "- [ ] Pass exact-head rustfmt, Cargo check, Clippy, tests, rustdoc, debug, release, perft, and differential gates.",
        "- [x] Pass exact-head rustfmt, Cargo check, Clippy, tests, rustdoc, debug, release, perft, and differential gates.",
        "Ralph gate checkbox",
    )

    todo_path.write_text(todo)
    ralph_path.write_text(ralph)


if __name__ == "__main__":
    main()
