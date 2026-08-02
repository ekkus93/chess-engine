#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
todo_path = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
ralph_path = root / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
todo = todo_path.read_text()
ralph = ralph_path.read_text()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


todo = replace_once(
    todo,
    "| 14–24 | **Not started**. |",
    "| 14 | **Active** — Task 14.1 quiescence complete; Task 14.2 tactical ordering next. |\n| 15–24 | **Not started**. |",
    "program summary",
)

todo = replace_once(
    todo,
    "# Task 14: Quiescence and ordering — NOT STARTED\n- [ ] 14.1 Quiescence.\n- [ ] 14.2 Tactical ordering.\n- [ ] 14.3 Quiet ordering.\n- [ ] 14.4 Correctness tests.\n- [ ] 14.5 Exclusions.\n- [ ] Task 14 gate.\n",
    """# Task 14: Quiescence and ordering — ACTIVE
- [x] 14.1 Quiescence.
- [ ] 14.2 Tactical ordering.
- [ ] 14.3 Quiet ordering.
- [ ] 14.4 Correctness tests.
- [ ] 14.5 Exclusions.
- [ ] Task 14 gate.

### Task 14.1 completion evidence

- Public quiescence API: `quiescence_search`, `quiescence_search_with_limit`, `quiescence_search_with_cancellation`, `QuiescenceSearchResult`, and `MAX_QUIESCENCE_PLY`.
- Production implementation: `crates/chess-search/src/quiescence.rs`; alpha-beta depth-zero integration: `crates/chess-search/src/alpha_beta.rs`.
- Shared terminal/draw semantics: `crates/chess-search/src/search_common.rs`.
- Independent unpruned tactical-leaf oracle: `reference_search_with_quiescence` and `reference_search_with_quiescence_and_cancellation` in `crates/chess-search/src/reference.rs`.
- Regression suites: `crates/chess-search/tests/search_quiescence.rs`, bounded matching-oracle coverage in `search_equivalence.rs`, and preserved terminal/mate-distance coverage in `search_terminals.rs`.
- Contract documentation: `docs/RUST_QUIESCENCE_SEARCH.md`.
- Exact validated implementation SHA: `24e1090e17f8b39bdaac4989daffdeaea4b857e9`.
- Permanent CI run/job: `30749044761` / `91499685362`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, strict Clippy, 140 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Semantics: stand-pat only outside check; every legal check evasion; captures and all promotions outside check; fail-soft alpha-beta bounds; repetition/dead/fifty-move draw handling; cancellation at node and child boundaries; and a fail-loud 64-ply tactical guard when check cannot safely stand pat.
- Dedicated fixed regressions cover the hanging-capture horizon, quiet check evasions, promotions, poisoned captures with forced recapture, full-window equality against an independent unpruned tactical oracle, draw resolution, cancellation, depth-guard failure, and exact position/history/Zobrist restoration.
- Matching quiescence-oracle equivalence proves identical exact scores and alpha-beta node counts no greater than the unpruned tactical reference on bounded curated fixtures, with at least one strict cutoff witness.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 14.2 tactical ordering is next; TT hooks, MVV-LVA, SEE, killer/history ordering, and other Task 14.2–14.3 features remain intentionally absent.
""",
    "Task 14 section",
)

todo = replace_once(
    todo,
    """1. Begin Task 14.1 with a correctness-first quiescence-search contract over the existing alpha-beta search.
2. Define the stand-pat convention, tactical move scope, terminal/draw handling, and mate-distance propagation before adding heuristics.
3. Search legal captures, promotions, and required check evasions through source-bound legal tokens and exact make/unmake; do not use clone-per-child.
4. Add a reference tactical-leaf oracle and fixed horizon-effect fixtures before integrating quiescence into normal alpha-beta leaves.
5. Preserve Task 13 score, cancellation, history, Zobrist, and restoration contracts at every quiescence exit path.
6. Keep Task 14.2 tactical ordering, Task 14.3 quiet ordering, transposition tables, and production limits out of Task 14.1.
""",
    """1. Implement Task 14.2 tactical ordering over the validated Task 14.1 quiescence and alpha-beta semantics.
2. Add the documented transposition-table move hook as an explicit no-op until Task 15 supplies a real table.
3. Order promotions and captures deterministically, beginning with MVV-LVA; preserve exact score and first-best correctness independently of ordering.
4. Keep static exchange evaluation optional and excluded until the baseline ordering is correct, measured, and regression-covered.
5. Compare node counts on fixed tactical benchmark positions while preserving root score, best move, cancellation, history, Zobrist, and restoration contracts.
6. Keep Task 14.3 killer/history/PV quiet ordering, Task 15 transposition storage, and Task 16 production limits out of Task 14.2.
""",
    "immediate operations",
)

ralph = replace_once(
    ralph,
    "**Current phase:** Task 13 complete; Task 14.1 quiescence is next",
    "**Current phase:** Task 14.1 quiescence complete; Task 14.2 tactical ordering is next",
    "Ralph phase",
)

ralph = replace_once(
    ralph,
    "| 13.5 / 13 | `7ca429b0c883bbb8484d3eb3a4af7d96cdb57201` | `30745120833` / `91489299233` | terminal/mate-distance fixtures and full Task 13 gate, 135 Rust tests, depth-four perft, and differential oracle green |",
    "| 13.5 / 13 | `7ca429b0c883bbb8484d3eb3a4af7d96cdb57201` | `30745120833` / `91489299233` | terminal/mate-distance fixtures and full Task 13 gate, 135 Rust tests, depth-four perft, and differential oracle green |\n| 14.1 | `24e1090e17f8b39bdaac4989daffdeaea4b857e9` | `30749044761` / `91499685362` | correctness-first quiescence, 140 Rust tests, depth-four perft, and differential oracle green |",
    "completed gate row",
)

ralph = replace_once(
    ralph,
    "## Task 13 completed scope\n",
    """## Task 14.1 completion

Implemented and validated:

- standalone and alpha-beta-integrated fail-soft quiescence search;
- stand-pat only outside check and every legal evasion while checked;
- deterministic capture and promotion expansion through source-bound legal tokens;
- shared mate, stalemate, dead-position, repetition, and move-count draw semantics;
- cancellation checks at node and tactical-child boundaries with restoration before error propagation;
- a fail-loud 64-ply tactical guard, including explicit failure when the side remains in check;
- a separate unpruned reference search with quiescence leaves while preserving the original static Task 13 reference API;
- matching-oracle score and node-count equivalence on bounded fixtures;
- fixed hanging-capture, quiet-evasion, promotion, poisoned-capture, draw, cancellation, and guard regressions;
- exact root position, detached history, invariant, and incremental/recomputed-Zobrist restoration;
- `crates/chess-search/tests/search_quiescence.rs` and `docs/RUST_QUIESCENCE_SEARCH.md`.

Evidence:

- Exact validated implementation SHA: `24e1090e17f8b39bdaac4989daffdeaea4b857e9`.
- Permanent CI run/job: `30749044761` / `91499685362`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 140 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Dedicated quiescence suite: 5 passed; matching reference/alpha-beta equivalence suite: 3 passed; terminal/mate-distance suite: 4 passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 14.2 tactical ordering is next. Task 14.3 quiet ordering, Task 15 transposition storage, and Task 16 production limits remain open.

## Task 14 active scope

- [x] Stand-pat only outside check.
- [x] Search every legal check evasion.
- [x] Search captures and all promotions.
- [x] Preserve fail-soft alpha-beta, draw, repetition, mate-distance, cancellation, and restoration semantics.
- [x] Enforce a bounded fail-loud tactical-ply guard.
- [x] Add independent tactical-oracle and fixed horizon-effect regressions.
- [ ] Implement Task 14.2 tactical ordering.
- [ ] Implement Task 14.3 quiet ordering.
- [ ] Complete Task 14.4 consolidated correctness tests and Task 14.5 exclusion audit.
- [ ] Pass the overall Task 14 gate.

## Task 13 completed scope
""",
    "Task 14 Ralph section",
)

ralph = replace_once(
    ralph,
    "No pull request has been created; work remains on `rust-engine`.",
    "No pull request has been created; work remains on `rust-engine`. Task 14.2 tactical ordering is the next operation.",
    "Ralph footer",
)

todo_path.write_text(todo)
ralph_path.write_text(ralph)
print("Task 14.1 trackers closed")
