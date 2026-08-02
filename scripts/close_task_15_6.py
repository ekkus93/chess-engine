from pathlib import Path
import sys

root = Path(sys.argv[1])


def replace_once(path: str, old: str, new: str) -> None:
    target = root / path
    text = target.read_text()
    if old not in text:
        raise SystemExit(f"expected text not found in {path}: {old[:160]!r}")
    target.write_text(text.replace(old, new, 1))


def replace_all(path: str, old: str, new: str) -> None:
    target = root / path
    text = target.read_text()
    if old not in text:
        raise SystemExit(f"expected text not found in {path}: {old[:160]!r}")
    target.write_text(text.replace(old, new))


definitions = "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
replace_once(
    definitions,
    """## 15.6 Diagnostics and benchmarks

- [ ] probes;
- [ ] hits;
- [ ] exact/bound hits;
- [ ] replacement counts if useful;
- [ ] hash fullness estimate;
- [ ] probe/store microbenchmarks.
""",
    """## 15.6 Diagnostics and benchmarks

- [x] probes;
- [x] hits;
- [x] exact/bound hits;
- [x] replacement counts if useful;
- [x] hash fullness estimate;
- [x] probe/store microbenchmarks.
""",
)

todo = "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
replace_once(
    todo,
    "| 15 | **Active** — Tasks 15.1–15.5 complete; Task 15.6 diagnostics and benchmarks next. |",
    "| 15 | **Active** — Tasks 15.1–15.6 complete; overall production alpha-beta integration gate next. |",
)
replace_once(
    todo,
    "- Task 14 is complete. Tasks 15.1–15.5 are complete; Task 15.6 diagnostics and benchmarks is next.",
    "- Task 14 is complete. Tasks 15.1–15.6 are complete; the overall Task 15 production integration gate is next.",
)
replace_once(todo, "- [ ] 15.6 Diagnostics.", "- [x] 15.6 Diagnostics.")
replace_all(
    todo,
    "Task 15.6 diagnostics and benchmarks is next.",
    "The overall Task 15 production integration gate is next.",
)
replace_once(
    todo,
    """# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED
""",
    """### Task 15.6 completion evidence

- Diagnostics implementation: `crates/chess-search/src/transposition/diagnostics.rs` plus instrumentation in `probe.rs` and `store.rs`.
- Public API: `TranspositionTable::diagnostics`, `TranspositionTable::reset_diagnostics`, `TranspositionTable::hash_full`, `TranspositionTableDiagnostics`, `TranspositionHashFull`, and `TRANSPOSITION_HASH_FULL_SAMPLE_LIMIT`.
- Benchmark API and command: `chess_tools::benchmark_transposition` and `chess-tools tt-bench ITERATIONS`.
- Contract documentation: `docs/RUST_TRANSPOSITION_TABLE_DIAGNOSTICS.md`.
- Exact validated implementation SHA: `bd4d5d581c0e82f892435b2874732ac632c2e1f5`.
- Permanent CI run/job: `30768512470` / `91551420579`.
- Saturating counters cover valid probes, complete-key hits and derived misses, exact reuse, lower/upper cutoffs, all stores, same-key updates, empty insertions, and collision replacements.
- Invalid windows fail before lookup and do not increment probe counters; verified hits remain observable even when depth, repetition sensitivity, or a non-cutting bound prevents score reuse.
- Snapshot/reset is deterministic and reset does not alter allocation, entries, generation, or replacement behavior.
- Hash fullness inspects at most 1,000 evenly distributed slots, counts only the current generation, performs no allocation, and is deterministic for a fixed table state.
- The release benchmark uses fixed one-MiB tables, deterministic store keys/depths, and a deterministic three-hit/one-miss probe fixture. Timing is informational; checksums are reproducible.
- Hosted-runner smoke evidence for 100,000 operations: stores `3,064,736 ns`, checksum `7,945,805,154,409,997,841`; probes `1,339,856 ns`, checksum `405,729,600`.
- Four new deterministic tests passed, bringing the workspace total to 188 executed non-doc Rust tests.
- The first validation iteration exposed only a test-only import in production scope; the second exposed only a temporary patch-matcher mismatch. Both were corrected without lint suppression or semantic changes.
- Results: workspace assets, permanent Task 14.5 exclusion audit over 12 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 188 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Production alpha-beta still does not own or call the table; correctness-preserving integration and a measurable node-reduction witness remain the unchecked overall Task 15 gate.

# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED
""",
)
replace_once(
    todo,
    """## Immediate next operations

1. Implement Task 15.6 transposition-table diagnostics and benchmarks.
2. Count probes, complete-key hits, exact hits, bound cutoffs, stores, same-key updates, empty insertions, and collision replacements.
3. Provide deterministic snapshot/reset operations and a bounded hash-full estimate without scanning unbounded state.
4. Add repeatable release-mode probe and store microbenchmarks over fixed fixtures.
5. Preserve fixed-capacity allocation, mate normalization, repetition suppression, and deterministic replacement semantics.
6. After Task 15.6, complete the overall Task 15 gate by integrating the table into production alpha-beta and proving correctness and measurable usefulness; keep Task 16 outside Task 15.
""",
    """## Immediate next operations

1. Complete the overall Task 15 gate by integrating the fixed-capacity transposition table into production alpha-beta.
2. Establish explicit table ownership, sizing, clear, and generation boundaries without adding an unbounded fallback.
3. Probe before move generation, use verified TT moves for ordering, and reuse only depth/bound-safe scores with repetition-sensitive suppression intact.
4. Store normalized exact/lower/upper results after completed nodes using the deterministic Task 15.5 replacement policy.
5. Add deterministic equivalence and immutability regressions proving unchanged scores, best moves, mate distances, draw semantics, cancellation, and root restoration.
6. Add a fixed search witness showing strict node reduction and meaningful probe/hit diagnostics; keep iterative deepening, aspiration windows, PV reconstruction, and Task 16 limits outside Task 15.
""",
)

ralph = "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
replace_once(
    ralph,
    "**Current phase:** Tasks 15.1–15.5 complete; Task 15.6 diagnostics and benchmarks is next",
    "**Current phase:** Tasks 15.1–15.6 complete; overall Task 15 production integration gate is next",
)
replace_once(
    ralph,
    "| 15.5 | `775013a6e11aad7625c88b0cd3b258819211e839` | `30767556904` / `91548869513` | deterministic same-key updates and depth/age replacement, five focused tests, 184 Rust tests, depth-four perft, and differential oracle green |",
    """| 15.5 | `775013a6e11aad7625c88b0cd3b258819211e839` | `30767556904` / `91548869513` | deterministic same-key updates and depth/age replacement, five focused tests, 184 Rust tests, depth-four perft, and differential oracle green |
| 15.6 | `bd4d5d581c0e82f892435b2874732ac632c2e1f5` | `30768512470` / `91551420579` | bounded counters and hash-full sampling, reproducible probe/store benchmark, four focused tests, 188 Rust tests, depth-four perft, and differential oracle green |""",
)
replace_all(
    ralph,
    "Task 15.6 diagnostics and benchmarks is next.",
    "The overall Task 15 production integration gate is next.",
)
replace_once(
    ralph,
    """## Task 15 active scope
""",
    """## Task 15.6 completion

Implemented and validated:

- saturating fixed-size probe, hit, score-reuse, store, and replacement counters in `crates/chess-search/src/transposition/diagnostics.rs`;
- complete-key hit accounting separated from exact/lower/upper score reuse accounting;
- deterministic diagnostic snapshots and reset without table-state mutation;
- bounded current-generation hash-full sampling over at most 1,000 evenly distributed slots;
- a release-mode `chess-tools tt-bench ITERATIONS` command over fixed one-MiB store and probe fixtures;
- deterministic benchmark checksums with timing treated as informational;
- three diagnostics/hash-full regressions and one benchmark reproducibility regression;
- `docs/RUST_TRANSPOSITION_TABLE_DIAGNOSTICS.md`.

Evidence:

- Exact validated implementation SHA: `bd4d5d581c0e82f892435b2874732ac632c2e1f5`.
- Permanent CI run/job: `30768512470` / `91551420579`.
- Results: workspace assets, Task 14.5 audit over 12 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 188 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Benchmark smoke: 100,000 stores in `3,064,736 ns`, checksum `7,945,805,154,409,997,841`; 100,000 probes in `1,339,856 ns`, checksum `405,729,600`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- The initial compiler iteration found only a test-only import in production scope; the next control iteration found only a temporary patch-matcher mismatch. Neither required a lint suppression or semantic change.
- Production search integration remains intentionally outside Task 15.6 and is the unchecked overall Task 15 gate.

## Task 15 active scope
""",
)
replace_once(
    ralph,
    "- [ ] Implement Task 15.6 diagnostics and benchmarks.",
    "- [x] Implement Task 15.6 diagnostics and benchmarks.",
)
replace_once(
    ralph,
    "No pull request has been created; work remains on `rust-engine`. Task 15.6 transposition-table diagnostics and benchmarks is the next operation.",
    "No pull request has been created; work remains on `rust-engine`. The overall Task 15 production alpha-beta integration gate is the next operation.",
)
