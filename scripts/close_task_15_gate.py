#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])


def replace_once(path: str, old: str, new: str) -> None:
    target = root / path
    text = target.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one match in {path}, found {count}: {old[:180]!r}")
    target.write_text(text.replace(old, new, 1))


def replace_all(path: str, old: str, new: str) -> None:
    target = root / path
    text = target.read_text()
    if old not in text:
        raise SystemExit(f"expected text in {path}: {old[:180]!r}")
    target.write_text(text.replace(old, new))


def insert_before_once(path: str, marker: str, inserted: str) -> None:
    target = root / path
    text = target.read_text()
    count = text.count(marker)
    if count != 1:
        raise SystemExit(f"expected exactly one marker in {path}, found {count}: {marker!r}")
    target.write_text(text.replace(marker, inserted + marker, 1))


defs = "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
replace_once(
    defs,
    "**Task 15 gate:** TT is bounded, mate-safe, correctly flagged, measurably useful, and has no unbounded production map fallback.",
    "**Task 15 gate — COMPLETE:** TT is bounded, mate-safe, correctly flagged, measurably useful, and has no unbounded production map fallback.",
)

todo = "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
replace_once(
    todo,
    "| 15 | **Active** — Tasks 15.1–15.6 complete; overall production alpha-beta integration gate next. |",
    "| 15 | **Complete** — bounded, mate-safe transposition table integrated into production alpha-beta with deterministic node-reduction evidence. |",
)
replace_once(
    todo,
    "- Task 14 is complete. Tasks 15.1–15.6 are complete; the overall Task 15 production integration gate is next.",
    "- Tasks 14 and 15 are complete. Task 16.1 iterative deepening is next.",
)
replace_once(
    todo,
    "# Task 15: Fixed-capacity transposition table — ACTIVE",
    "# Task 15: Fixed-capacity transposition table — COMPLETE",
)
replace_once(todo, "- [ ] Task 15 gate.", "- [x] Task 15 gate.")
replace_once(todo, "- [ ] Search and transposition table.", "- [x] Search and transposition table.")

replacements = [
    (
        "- Tasks 15.2–15.6 are complete; the overall Task 15 production integration gate is next.",
        "- Tasks 15.2–15.6 and the overall Task 15 gate are complete.",
    ),
    (
        "- Tasks 15.3–15.6 are complete; the overall Task 15 production integration gate is next.",
        "- Tasks 15.3–15.6 and the overall Task 15 gate are complete.",
    ),
    (
        "- Tasks 15.4–15.6 are complete; the overall Task 15 production integration gate is next.",
        "- Tasks 15.4–15.6 and the overall Task 15 gate are complete.",
    ),
    (
        "- Task 15.5 deterministic depth- and age-aware replacement is complete; the overall Task 15 production integration gate is next.",
        "- Task 15.5 replacement, Task 15.6 diagnostics, and the overall Task 15 integration gate are complete.",
    ),
    (
        "- The overall Task 15 production integration gate is next.",
        "- The overall Task 15 production integration gate is complete.",
    ),
    (
        "- The public probe, deterministic store, and diagnostics boundaries are complete, but production search still does not call them or activate TT move ordering; integration remains the overall Task 15 gate.",
        "- Production alpha-beta now calls the probe, store, diagnostics, and TT move-ordering boundaries under the completed Task 15 gate.",
    ),
    (
        "- Deterministic same-key updates, collision replacement, and diagnostics are complete, but production search still does not call the TT boundaries or activate TT move ordering; integration remains the overall Task 15 gate.",
        "- Production alpha-beta now uses deterministic updates, collision replacement, diagnostics, score reuse, and TT move ordering under the completed Task 15 gate.",
    ),
    (
        "- Diagnostics, hash-full estimation, and microbenchmarks are complete under Task 15.6; production search integration remains outside Task 15.5 and is the overall Task 15 gate.",
        "- Diagnostics, hash-full estimation, and microbenchmarks are complete under Task 15.6; production search integration is complete under the overall Task 15 gate.",
    ),
    (
        "- Production alpha-beta still does not own or call the table; correctness-preserving integration and a measurable node-reduction witness remain the unchecked overall Task 15 gate.",
        "- Production alpha-beta owns or accepts a bounded table, calls the verified probe/store paths, and has deterministic move-ordering and warm-table node-reduction witnesses under the completed Task 15 gate.",
    ),
]
for old, new in replacements:
    replace_all(todo, old, new)

gate_evidence = r'''
### Task 15 gate completion evidence

- Production integration: `crates/chess-search/src/alpha_beta.rs` and `crates/chess-search/src/move_ordering.rs`.
- Public caller-owned APIs: `alpha_beta_search_with_transposition_table` and `alpha_beta_search_with_cancellation_and_transposition_table`.
- Convenience searches allocate one bounded table using `DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES`, currently 1 MiB; caller-owned tables retain fixed allocation and entries across searches.
- Search resolves legal moves, terminal states, repetition, dead position, and move-count draws before accepting cached scores.
- Complete-key, depth, bound, mate-denormalization, and legal-root-move checks remain mandatory before a TT return or cutoff.
- Scores are stored and reused only at an irreversible-history boundary where the halfmove clock is zero. Reversible-history nodes may use a verified move for ordering but cannot reuse or store path-dependent scores.
- Root ordering-only hints are ignored. A one-node root return requires an exact entry with a currently legal canonical best move.
- Completed nodes store normalized exact/lower/upper results against the original alpha-beta window; cancellation, terminal/draw resolution, conversion failure, and incomplete restoration never store entries.
- Contract documentation: `docs/RUST_TRANSPOSITION_TABLE_SEARCH_INTEGRATION.md`.
- Production implementation commit: `c9eac6b8b7b4b6511d73155242dde08a554d8e88`.
- Exact clean validated SHA: `682114cd2452b04e1f24af1150928baaff779aa8`.
- Permanent exact-SHA CI run/job: `30770018597` / `91555458016`.
- Release integration witness run/job: `30769901197` / `91555134018`.
- Five focused regressions were added, bringing the workspace total to 193 executed non-doc Rust tests.
- The fixed narrow-window witness proves an insufficient-depth TT entry contributes only its verified move, preserves score and best move, and visits strictly fewer nodes.
- The warm-table witness proves a second identical full-window search returns the same exact score and canonical best move in one node without resizing the table.
- Additional regressions reject an illegal exact-root move, suppress cached scores and root hints for reversible history, and preserve position, history, and incremental/recomputed Zobrist identity exactly.
- Results: permanent exclusion audit, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 193 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The clean implementation delta contains only three Rust modules, one integration-test file, and one contract document; no temporary workflow, script, unbounded map, or fallback remains.
- Task 15 is complete. Task 16.1 iterative deepening is next.

'''
insert_before_once(
    todo,
    "# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED",
    gate_evidence,
)

path = root / todo
text = path.read_text()
marker = "## Immediate next operations\n"
if text.count(marker) != 1:
    raise SystemExit("expected one immediate-next marker in TODO")
prefix = text.split(marker, 1)[0]
next_operations = r'''## Immediate next operations

1. Implement Task 16.1 iterative deepening from depth 1 through the requested maximum.
2. Preserve and expose the last fully completed result after every iteration.
3. Reuse the caller-owned fixed-capacity TT and bounded history heuristics across iterations without changing root correctness.
4. Add per-depth diagnostics for completed depth, score, best move, nodes, TT probes/hits/cutoffs, and hash fullness.
5. Prove every completed iteration preserves position, history, Zobrist identity, deterministic score, and canonical best move.
6. Keep aspiration windows, PV reconstruction, time/node limits, and responsive cancellation in their explicit Task 16.2–16.6 scopes.
'''
path.write_text(prefix + next_operations)

ralph = "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
replace_once(
    ralph,
    "**Current phase:** Tasks 15.1–15.6 complete; overall Task 15 production integration gate is next",
    "**Current phase:** Task 15 complete; Task 16.1 iterative deepening is next",
)
replace_once(
    ralph,
    "| 15.6 | `bd4d5d581c0e82f892435b2874732ac632c2e1f5` | `30768512470` / `91551420579` | bounded counters and hash-full sampling, reproducible probe/store benchmark, four focused tests, 188 Rust tests, depth-four perft, and differential oracle green |",
    "| 15.6 | `bd4d5d581c0e82f892435b2874732ac632c2e1f5` | `30768512470` / `91551420579` | bounded counters and hash-full sampling, reproducible probe/store benchmark, four focused tests, 188 Rust tests, depth-four perft, and differential oracle green |\n| 15 / gate | `682114cd2452b04e1f24af1150928baaff779aa8` | `30770018597` / `91555458016` | production alpha-beta integration, 193 Rust tests, two release node-reduction witnesses, depth-four perft, and differential oracle green |",
)

ralph_replacements = [
    (
        "- The overall Task 15 production integration gate is next.",
        "- The overall Task 15 production integration gate is complete.",
    ),
    (
        "- Mate normalization, probe semantics, replacement policy, and diagnostics are complete; production search integration remains intentionally outside Task 15.2.",
        "- Mate normalization, probe semantics, replacement policy, diagnostics, and production search integration are complete under Task 15.",
    ),
    (
        "- Probe semantics, replacement, and diagnostics are complete; production search integration remains intentionally outside Task 15.3.",
        "- Probe semantics, replacement, diagnostics, and production search integration are complete under Task 15.",
    ),
    (
        "- Deterministic insertion, replacement, and diagnostics are complete; production search integration remains intentionally outside Task 15.4.",
        "- Deterministic insertion, replacement, diagnostics, and production search integration are complete under Task 15.",
    ),
    (
        "- Diagnostics, hash-full estimation, and microbenchmarks are complete under Task 15.6; production search integration remains intentionally outside Task 15.5.",
        "- Diagnostics, hash-full estimation, microbenchmarks, and production search integration are complete under Task 15.",
    ),
    (
        "- Production search integration remains intentionally outside Task 15.6 and is the unchecked overall Task 15 gate.",
        "- Production search integration is complete under the overall Task 15 gate.",
    ),
]
for old, new in ralph_replacements:
    replace_all(ralph, old, new)

ralph_gate = r'''## Task 15 completion

Implemented and validated:

- production alpha-beta ownership of a fresh bounded default table and public caller-owned fixed-table search APIs;
- generation advancement and diagnostic reset once per valid caller-owned search without resizing or clearing retained entries;
- terminal and rule-draw resolution before cached-score reuse;
- complete-key, depth, exact/lower/upper bound, mate-distance, and legal-root-move enforcement;
- irreversible-history-only score storage and reuse, with verified move-only ordering at reversible-history nodes;
- root determinism through suppression of ordering-only hints and legal canonical-move validation for exact root returns;
- normalized post-search exact/lower/upper storage only after complete child restoration;
- fixed-capacity operation with no production map or unbounded fallback;
- five focused integration/order regressions and two release-mode node-reduction witnesses;
- `docs/RUST_TRANSPOSITION_TABLE_SEARCH_INTEGRATION.md`.

Evidence:

- Production implementation commit: `c9eac6b8b7b4b6511d73155242dde08a554d8e88`.
- Exact clean validated SHA: `682114cd2452b04e1f24af1150928baaff779aa8`.
- Permanent CI run/job: `30770018597` / `91555458016`.
- Release-witness validation run/job: `30769901197` / `91555134018`.
- Results: permanent exclusion audit over 12 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 193 executed non-doc Rust tests, both release node-reduction witnesses, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The move-ordering witness preserves score and best move while visiting strictly fewer nodes from an insufficient-depth move-only hit.
- The warm-table witness preserves the exact score and canonical root move while reducing the second identical search to one node.
- Reversible-history, illegal-root-move, allocation-capacity, position/history restoration, and incremental/recomputed Zobrist regressions all passed.
- The clean implementation delta is limited to three Rust modules, one integration-test file, and one contract document.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 15 is complete. Task 16.1 iterative deepening is next.

'''
insert_before_once(ralph, "## Task 15 active scope", ralph_gate)
replace_once(ralph, "## Task 15 active scope", "## Task 15 completed scope")
replace_once(ralph, "- [ ] Pass the overall Task 15 gate.", "- [x] Pass the overall Task 15 gate.")
replace_once(
    ralph,
    "No pull request has been created; work remains on `rust-engine`. The overall Task 15 production alpha-beta integration gate is the next operation.",
    "No pull request has been created; work remains on `rust-engine`. Task 16.1 iterative deepening is the next operation.",
)
