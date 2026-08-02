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
    "| 14 | **Active** — Task 14.1 quiescence complete; Task 14.2 tactical ordering next. |",
    "| 14 | **Active** — Tasks 14.1–14.2 complete; Task 14.3 quiet ordering next. |",
    "TODO program summary",
)

todo = replace_once(
    todo,
    "- [ ] 14.2 Tactical ordering.",
    "- [x] 14.2 Tactical ordering.",
    "TODO Task 14.2 checkbox",
)

todo = replace_once(
    todo,
    "- Task 14.2 tactical ordering is next; TT hooks, MVV-LVA, SEE, killer/history ordering, and other Task 14.2–14.3 features remain intentionally absent.\n\n# Task 15:",
    """- Task 14.2 tactical ordering is complete; Task 14.3 quiet ordering is next.

### Task 14.2 completion evidence

- Bounded stable ordering implementation: `crates/chess-search/src/move_ordering.rs`.
- Alpha-beta and quiescence integration: `crates/chess-search/src/alpha_beta.rs` and `crates/chess-search/src/quiescence.rs`.
- Reference control policy: `crates/chess-search/src/reference.rs` retains exact legal-generation order through `MoveOrdering::Generation`.
- Contract documentation: `docs/RUST_TACTICAL_MOVE_ORDERING.md`.
- Exact validated implementation SHA: `3688cb8e89a7da0c7fd34c3756d52d0fcc8d3d33`.
- Permanent CI run/job: `30753873602` / `91512570865`.
- Results: workspace assets, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 145 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Production order is an explicit no-op transposition-table hook, promotions by promoted-piece value, MVV-LVA captures, then generation-stable remaining moves. Promotion captures remain in the promotion tier; en-passant captures use a pawn victim.
- Ordering storage is fixed-capacity stack-backed and copies opaque source-bound legal tokens without synthesizing moves, allocating per node, mutating the position, or weakening token-origin validation.
- Focused tests prove the TT hook is currently `None`, generation policy preserves the exact token sequence, a supplied future TT move receives first priority, queen/rook/bishop/knight promotion priority is deterministic, and MVV-LVA prefers both the more valuable victim and the cheaper attacker.
- A fixed narrow-window tactical tree returns the same fail-soft score and best move under generation and tactical policies while tactical ordering visits strictly fewer nodes; both paths restore position, detached history, invariants, and incremental/recomputed Zobrist identity exactly.
- Existing equivalence, cancellation/immutability, quiescence, terminal/mate-distance, perft, and differential suites remain green.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Static exchange evaluation remains intentionally absent. Killer/history/PV quiet ordering belongs to Task 14.3; transposition storage belongs to Task 15; production limits belong to Task 16.

# Task 15:""",
    "TODO Task 14.2 evidence insertion",
)

todo = replace_once(
    todo,
    """1. Implement Task 14.2 tactical ordering over the validated Task 14.1 quiescence and alpha-beta semantics.
2. Add the documented transposition-table move hook as an explicit no-op until Task 15 supplies a real table.
3. Order promotions and captures deterministically, beginning with MVV-LVA; preserve exact score and first-best correctness independently of ordering.
4. Keep static exchange evaluation optional and excluded until the baseline ordering is correct, measured, and regression-covered.
5. Compare node counts on fixed tactical benchmark positions while preserving root score, best move, cancellation, history, Zobrist, and restoration contracts.
6. Keep Task 14.3 killer/history/PV quiet ordering, Task 15 transposition storage, and Task 16 production limits out of Task 14.2.
""",
    """1. Implement Task 14.3 quiet ordering over the validated Task 14.1–14.2 search semantics.
2. Add bounded killer moves by ply and a bounded history heuristic keyed by side/from/to or piece/to.
3. Use a stable encoded-move tie-break and keep any previous-PV hook explicit and optional until Task 16 provides iterative deepening and PV data.
4. Prove quiet ordering cannot override a better exact score and preserves deterministic full-window root results.
5. Compare nodes on fixed quiet-search benchmark positions while preserving cancellation, history, Zobrist, and exact make/unmake restoration.
6. Keep Task 14.4 consolidated correctness closure, Task 14.5 exclusion audit, Task 15 transposition storage, and Task 16 production limits outside Task 14.3.
""",
    "TODO immediate operations",
)

ralph = replace_once(
    ralph,
    "**Current phase:** Task 14.1 quiescence complete; Task 14.2 tactical ordering is next",
    "**Current phase:** Tasks 14.1–14.2 complete; Task 14.3 quiet ordering is next",
    "Ralph current phase",
)

ralph = replace_once(
    ralph,
    "| 14.1 | `24e1090e17f8b39bdaac4989daffdeaea4b857e9` | `30749044761` / `91499685362` | correctness-first quiescence, 140 Rust tests, depth-four perft, and differential oracle green |",
    "| 14.1 | `24e1090e17f8b39bdaac4989daffdeaea4b857e9` | `30749044761` / `91499685362` | correctness-first quiescence, 140 Rust tests, depth-four perft, and differential oracle green |\n| 14.2 | `3688cb8e89a7da0c7fd34c3756d52d0fcc8d3d33` | `30753873602` / `91512570865` | bounded tactical ordering, 145 Rust tests, strict node-reduction witness, depth-four perft, and differential oracle green |",
    "Ralph completed gate row",
)

ralph = replace_once(
    ralph,
    "- Task 14.2 tactical ordering is next. Task 14.3 quiet ordering, Task 15 transposition storage, and Task 16 production limits remain open.\n\n## Task 14 active scope",
    """- Task 14.2 tactical ordering is complete. Task 14.3 quiet ordering, Task 15 transposition storage, and Task 16 production limits remain open.

## Task 14.2 completion

Implemented and validated:

- fixed-capacity stack-backed stable ordering over opaque legal-move tokens;
- an explicit transposition-table move hook that returns `None` until Task 15;
- promotion ordering by promoted-piece value, including promotion captures;
- MVV-LVA capture ordering with explicit en-passant pawn-victim semantics;
- generation-stable remaining moves and equal-key ties;
- tactical ordering in production alpha-beta and quiescence search;
- exact generation-order control policy in the unpruned reference search;
- a typed alpha-beta window that preserves the strict lint-clean recursive boundary;
- a fixed narrow-window node-reduction witness with identical fail-soft score and best move;
- exact position, detached-history, invariant, and incremental/recomputed-Zobrist restoration;
- `crates/chess-search/src/move_ordering.rs` and `docs/RUST_TACTICAL_MOVE_ORDERING.md`.

Evidence:

- Exact validated implementation SHA: `3688cb8e89a7da0c7fd34c3756d52d0fcc8d3d33`.
- Permanent CI run/job: `30753873602` / `91512570865`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 145 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- New coverage: four move-ordering unit tests and one quiescence narrow-window node-reduction test.
- Existing search-equivalence, immutability/cancellation, quiescence, terminal/mate-distance, perft, and differential suites remained green.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- SEE remains intentionally absent; Task 14.3 owns killer/history/stable-tie/PV quiet ordering.

## Task 14 active scope""",
    "Ralph Task 14.2 completion insertion",
)

ralph = replace_once(
    ralph,
    "- [ ] Implement Task 14.2 tactical ordering.",
    "- [x] Implement Task 14.2 tactical ordering.",
    "Ralph active scope checkbox",
)

ralph = replace_once(
    ralph,
    "No pull request has been created; work remains on `rust-engine`. Task 14.2 tactical ordering is the next operation.",
    "No pull request has been created; work remains on `rust-engine`. Task 14.3 quiet ordering is the next operation.",
    "Ralph footer",
)

todo_path.write_text(todo)
ralph_path.write_text(ralph)
print("Task 14.2 trackers closed")
