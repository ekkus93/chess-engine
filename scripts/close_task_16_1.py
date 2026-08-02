#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one match in {path}, found {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


definitions = ROOT / "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
live = ROOT / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
ralph = ROOT / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"

replace_once(
    definitions,
    """## 16.1 Iterative deepening

- [ ] Search depth 1 through requested maximum.
- [ ] Preserve completed result after each iteration.
- [ ] Reuse TT/history appropriately.
- [ ] Report per-depth diagnostics.
""",
    """## 16.1 Iterative deepening

- [x] Search depth 1 through requested maximum.
- [x] Preserve completed result after each iteration.
- [x] Reuse TT/history appropriately.
- [x] Report per-depth diagnostics.
""",
)

replace_once(
    live,
    "| 16–24 | **Not started**. |",
    "| 16 | **Active** — Task 16.1 iterative deepening complete; aspiration windows next. |\n| 17–24 | **Not started**. |",
)
replace_once(
    live,
    """# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED
- [ ] 16.1 Iterative deepening.
- [ ] 16.2 Aspiration windows.
- [ ] 16.3 Principal variation.
- [ ] 16.4 Limits.
- [ ] 16.5 Cancellation.
- [ ] 16.6 Result API.
- [ ] 16.7 Optional extension.
- [ ] Task 16 gate.

# Task 17: Linux UCI executable — NOT STARTED
""",
    """# Task 16: Iterative deepening, PV, limits, cancellation — ACTIVE
- [x] 16.1 Iterative deepening.
- [ ] 16.2 Aspiration windows.
- [ ] 16.3 Principal variation.
- [ ] 16.4 Limits.
- [ ] 16.5 Cancellation.
- [ ] 16.6 Result API.
- [ ] 16.7 Optional extension.
- [ ] Task 16 gate.

### Task 16.1 completion evidence

- Implementation: `crates/chess-search/src/iterative_deepening.rs`, with public exports from `crates/chess-search/src/lib.rs`.
- Public APIs: `iterative_deepening_search`, `iterative_deepening_search_with_transposition_table`, `IterativeDeepeningIteration`, `IterativeDeepeningSearchResult`, and `IterativeDeepeningSearchError`.
- Every request searches complete full-window depths `1..=maximum_depth` in ascending order and retains one exact record for every completed depth.
- The convenience boundary allocates one bounded default table; the caller-owned boundary reuses one fixed-capacity table and the same detached root history across all iterations.
- Each completed record reports depth, exact score, canonical best move, iteration nodes, isolated TT diagnostics, bounded hash-full sampling, and generation.
- Result storage uses a fallible exact reservation bounded by `MAX_MATE_PLY`; zero depth, excessive depth, allocation failure, iteration failure, and node-total overflow are typed errors.
- Five regressions prove fixed-depth equivalence, generation and diagnostic isolation, terminal iteration behavior, invalid-depth fail-fast behavior, history mismatch safety, and exact position/history/Zobrist restoration.
- Contract documentation: `docs/RUST_ITERATIVE_DEEPENING.md`.
- Exact validated implementation SHA: `886ad953952b3a409800fcf7e8699365f94f0271`.
- Permanent CI run/job: `30772536115` / `91562076526`.
- Results: permanent exclusion audit over 13 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 198 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The initial validation found only canonical rustfmt changes; the next found an invalid test assumption about sparse bounded hash-full sampling. Production semantics did not change.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16.2 aspiration windows is next. PV reconstruction, limits, cancellation recovery, final result API, and extensions remain deferred.

# Task 17: Linux UCI executable — NOT STARTED
""",
)
replace_once(
    live,
    """1. Implement Task 16.1 iterative deepening from depth 1 through the requested maximum.
2. Preserve and expose the last fully completed result after every iteration.
3. Reuse the caller-owned fixed-capacity TT and bounded history heuristics across iterations without changing root correctness.
4. Add per-depth diagnostics for completed depth, score, best move, nodes, TT probes/hits/cutoffs, and hash fullness.
5. Prove every completed iteration preserves position, history, Zobrist identity, deterministic score, and canonical best move.
6. Keep aspiration windows, PV reconstruction, time/node limits, and responsive cancellation in their explicit Task 16.2–16.6 scopes.
""",
    """1. Implement Task 16.2 aspiration windows centered on the prior completed iteration score.
2. Detect fail-low and fail-high without promoting a bound to an exact root result.
3. Re-search failed windows through a deterministic safe expansion or complete-window fallback.
4. Record retry counts and window outcomes per completed depth without losing the Task 16.1 iteration record.
5. Add fixed regressions for fail-low, fail-high, exact recovery, canonical best-move preservation, and root restoration.
6. Keep PV reconstruction, time/node limits, responsive cancellation, the final result API, and check extensions in Tasks 16.3–16.7.
""",
)

replace_once(
    ralph,
    "**Current phase:** Task 15 complete; Task 16.1 iterative deepening is next",
    "**Current phase:** Task 16.1 iterative deepening complete; Task 16.2 aspiration windows is next",
)
replace_once(
    ralph,
    "| 15 / gate | `682114cd2452b04e1f24af1150928baaff779aa8` | `30770018597` / `91555458016` | production alpha-beta integration, 193 Rust tests, two release node-reduction witnesses, depth-four perft, and differential oracle green |",
    "| 15 / gate | `682114cd2452b04e1f24af1150928baaff779aa8` | `30770018597` / `91555458016` | production alpha-beta integration, 193 Rust tests, two release node-reduction witnesses, depth-four perft, and differential oracle green |\n| 16.1 | `886ad953952b3a409800fcf7e8699365f94f0271` | `30772536115` / `91562076526` | full-window iterative deepening, five focused tests, 198 Rust tests, depth-four perft, and differential oracle green |",
)
replace_once(
    ralph,
    "- Task 15 is complete. Task 16.1 iterative deepening is next.",
    "- Task 15 and Task 16.1 are complete. Task 16.2 aspiration windows is next.",
)
replace_once(
    ralph,
    """## Task 15 completed scope
""",
    """## Task 16.1 completion

Implemented and validated:

- a correctness-first iterative-deepening layer over the established full-window fixed-depth alpha-beta boundary;
- ascending complete searches at every depth from one through the requested maximum;
- one retained exact result record for every completed iteration;
- one bounded default TT for convenience searches and one caller-owned fixed table reused across depths;
- reuse of the same detached root history with exact restoration before every next iteration;
- per-depth score, canonical best move, nodes, TT diagnostics, bounded hash-full estimate, and generation reporting;
- fallible iteration-record reservation bounded by `MAX_MATE_PLY` and typed failure categories;
- five integration regressions and `docs/RUST_ITERATIVE_DEEPENING.md`.

Evidence:

- Exact validated implementation SHA: `886ad953952b3a409800fcf7e8699365f94f0271`.
- Permanent CI run/job: `30772536115` / `91562076526`.
- Results: permanent exclusion audit over 13 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 198 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Every retained iteration matched an independent fixed-depth full-window score and canonical best move on the deterministic benchmark.
- Generation sequence, diagnostic isolation, terminal roots, invalid maximum depths, mismatched histories, table capacity, position/history restoration, and incremental/recomputed Zobrist identity are covered.
- The first validation iteration found canonical rustfmt differences only. The second found a test-only assumption that sparse bounded hash-full sampling must observe an occupied slot; the assertion was corrected to the documented sampling contract without production changes.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16.1 is complete. Task 16.2 aspiration windows is next.

## Task 16 active scope

- [x] Implement Task 16.1 iterative deepening.
- [ ] Implement Task 16.2 aspiration windows.
- [ ] Implement Task 16.3 principal variation.
- [ ] Implement Task 16.4 search limits.
- [ ] Implement Task 16.5 responsive cancellation.
- [ ] Implement Task 16.6 final result API.
- [ ] Consider Task 16.7 optional bounded check extension.
- [ ] Pass the overall Task 16 gate.

## Task 15 completed scope
""",
)
replace_once(
    ralph,
    "No pull request has been created; work remains on `rust-engine`. Task 16.1 iterative deepening is the next operation.",
    "No pull request has been created; work remains on `rust-engine`. Task 16.2 aspiration windows is the next operation.",
)

print("Task 16.1 tracker closure applied")
