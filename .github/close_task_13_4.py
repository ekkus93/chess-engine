#!/usr/bin/env python3
"""Apply the exact documentation closure for validated Task 13.4."""

from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: close_task_13_4.py REPOSITORY_ROOT")

    root = Path(sys.argv[1]).resolve()
    todo_path = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
    ralph_path = root / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
    todo = todo_path.read_text()
    ralph = ralph_path.read_text()

    todo = replace_once(
        todo,
        "| 13 | **Active** — Tasks 13.1–13.3 complete; Task 13.4 immutability is next. |",
        "| 13 | **Active** — Tasks 13.1–13.4 complete; Task 13.5 terminal fixtures are next. |",
        "TODO program summary",
    )
    todo = replace_once(
        todo,
        "- [ ] 13.4 Immutability.",
        "- [x] 13.4 Immutability.",
        "TODO 13.4 checkbox",
    )
    todo = replace_once(
        todo,
        "- Every successful paired invocation restored the root position, incremental Zobrist identity, and detached history. Task 13.4 remains open for its broader immutability and cancellation contract.",
        "- Every successful paired invocation restored the root position, incremental Zobrist identity, and detached history. Task 13.4 now formalizes the broader completion, failure, repeated-search, and cancellation contract.",
        "TODO 13.3 restoration note",
    )
    todo = replace_once(
        todo,
        "- Task 13.4 is next; Task 13.5 and the overall Task 13 gate remain open.\n\n# Task 14: Quiescence and ordering — NOT STARTED",
        """- Task 13.4 is complete; Task 13.5 and the overall Task 13 gate remain open.

### Task 13.4 completion evidence

- Public cancellation boundary: `SearchCancellationProbe`, `reference_search_with_cancellation`, and `alpha_beta_search_with_cancellation`.
- Cancellation errors: `ReferenceSearchError::Cancelled` and `AlphaBetaSearchError::Cancelled`.
- Implementation: `crates/chess-search/src/cancellation.rs`, `reference.rs`, and `alpha_beta.rs`.
- Integration suite: `crates/chess-search/tests/search_immutability.rs`.
- Contract documentation: `docs/RUST_SEARCH_IMMUTABILITY.md`.
- Exact validated implementation SHA: `3644e032504b604c210796f1e6c7ef056d05e94b`.
- Permanent CI run/job: `30743519630` / `91485044296`.
- Results: rustfmt, Cargo check, strict Clippy, 131 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc, debug/release builds, and independent differential validation passed.
- Coverage proves exact position, incremental/recomputed Zobrist, enforceable invariants, and detached-history restoration after repeated successful searches, terminal completion, validation failure, and mid-tree cancellation.
- Reference and alpha-beta cancellation fixtures trigger after 64 probe checks from inside active recursive lines and return cancellation only after ancestor history entries are popped and moves are unmade.
- The narrow callback probe deliberately excludes Task 16 clocks, node limits, iterative deepening, partial-result policy, UCI stop handling, and adapter cancellation.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13.5 is next; the overall Task 13 gate remains open.

# Task 14: Quiescence and ordering — NOT STARTED""",
        "TODO 13.4 evidence insertion",
    )
    todo = replace_once(
        todo,
        """1. Implement Task 13.4 search immutability as a dedicated contract.
2. Add cancellation support or the minimum cancellable search boundary required to prove cancellation restoration without prematurely implementing Task 16 limits.
3. Require root position, Zobrist identity, and detached history to remain exact after normal completion, terminal completion, validation failure, and cancellation.
4. Exercise repeated searches from the same root and verify no state or history drift accumulates.
5. Keep Task 13.5 shorter-mate and longer-survival fixtures open until the immutability contract is complete.
6. Do not close the overall Task 13 gate until Tasks 13.4 and 13.5 pass exact-head validation.""",
        """1. Implement Task 13.5 as a dedicated terminal and mate-distance fixture suite.
2. Cover mate in one, already mated, stalemate, claimable draws, and automatic draws for both reference and alpha-beta search.
3. Add a position with multiple forced mates and prove the shorter mate receives the higher score and is selected.
4. Add a forced-loss position with multiple continuations and prove the engine selects the line that delays mate longest.
5. Reconfirm exact reference/alpha-beta scores, legal best moves, and root position/Zobrist/history restoration for every terminal fixture.
6. Close the overall Task 13 gate only after Task 13.5 passes the full exact-head permanent validation suite.""",
        "TODO immediate operations",
    )

    ralph = replace_once(
        ralph,
        "**Current phase:** Tasks 13.1–13.3 complete; Task 13.4 immutability is next",
        "**Current phase:** Tasks 13.1–13.4 complete; Task 13.5 terminal fixtures are next",
        "Ralph current phase",
    )
    ralph = replace_once(
        ralph,
        "| 13.3 | `bdf98a8e7c5cb6aadc55ba3638cd3af2f4ba9e91` | `30743024471` / `91483729312` | shallow equivalence, 127 Rust tests, depth-four perft, and differential oracle green |",
        """| 13.3 | `bdf98a8e7c5cb6aadc55ba3638cd3af2f4ba9e91` | `30743024471` / `91483729312` | shallow equivalence, 127 Rust tests, depth-four perft, and differential oracle green |
| 13.4 | `3644e032504b604c210796f1e6c7ef056d05e94b` | `30743519630` / `91485044296` | completion/cancellation immutability, 131 Rust tests, depth-four perft, and differential oracle green |""",
        "Ralph evidence row",
    )
    ralph = replace_once(
        ralph,
        "- Task 13.4 remains not started.",
        "- Task 13.4 is complete.",
        "Ralph 13.3 next note",
    )
    ralph = replace_once(
        ralph,
        "## Task 13 active scope\n",
        """## Task 13.4 completion

Implemented and validated:

- a public `SearchCancellationProbe` callback boundary implemented automatically by `FnMut() -> bool` closures;
- cancellable reference and alpha-beta entry points while preserving the existing never-cancel convenience APIs;
- cancellation checks at node and child boundaries;
- restoration-before-propagation for every recursive child result, including cancellation;
- explicit cancellation error variants with no incomplete score, move, node count, or principal variation;
- repeated-search stability on one mutable game-derived position and detached history;
- mid-tree cancellation after 64 probe checks for both search implementations;
- invariant, incremental/recomputed Zobrist, position snapshot, and history snapshot checks after completion, terminal resolution, validation failure, and cancellation;
- `crates/chess-search/tests/search_immutability.rs`;
- `docs/RUST_SEARCH_IMMUTABILITY.md`.

Evidence:

- Exact validated implementation SHA: `3644e032504b604c210796f1e6c7ef056d05e94b`.
- Permanent CI run/job: `30743519630` / `91485044296`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 131 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13.5 remains not started; Task 16 still owns full limits, stop-token, iterative-deepening, and partial-result policy.

## Task 13 active scope
""",
        "Ralph 13.4 completion insertion",
    )
    ralph = replace_once(
        ralph,
        "- [ ] Prove search restores the root position, Zobrist key, and history exactly.",
        "- [x] Prove search restores the root position, Zobrist key, and history exactly.",
        "Ralph restoration checkbox",
    )

    todo_path.write_text(todo)
    ralph_path.write_text(ralph)


if __name__ == "__main__":
    main()
