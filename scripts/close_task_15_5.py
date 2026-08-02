#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()

def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one match in {path}: {old!r}; found {text.count(old)}")
    path.write_text(text.replace(old, new, 1))


def replace_all(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    count = text.count(old)
    if count == 0:
        raise SystemExit(f"expected at least one match in {path}: {old!r}")
    path.write_text(text.replace(old, new))

# Authoritative task definitions.
definitions = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
replace_once(
    definitions,
    "## 15.5 Replacement policy\n\n- [ ] Depth-preferred replacement.\n- [ ] Age awareness.\n- [ ] Document collision behavior.\n- [ ] Add deterministic tests.\n",
    "## 15.5 Replacement policy\n\n- [x] Depth-preferred replacement.\n- [x] Age awareness.\n- [x] Document collision behavior.\n- [x] Add deterministic tests.\n",
)

# Authoritative project TODO.
todo = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
replace_once(
    todo,
    "| 15 | **Active** — Tasks 15.1–15.4 complete; Task 15.5 deterministic replacement next. |",
    "| 15 | **Active** — Tasks 15.1–15.5 complete; Task 15.6 diagnostics and benchmarks next. |",
)
replace_once(todo, "- [ ] 15.5 Replacement.", "- [x] 15.5 Replacement.")
replace_all(
    todo,
    "Tasks 15.1–15.4 are complete; Task 15.5 deterministic replacement is next.",
    "Tasks 15.1–15.5 are complete; Task 15.6 diagnostics and benchmarks is next.",
)
replace_all(
    todo,
    "Tasks 15.2–15.4 are complete; Task 15.5 deterministic replacement is next.",
    "Tasks 15.2–15.5 are complete; Task 15.6 diagnostics and benchmarks is next.",
)
replace_all(
    todo,
    "Tasks 15.3 mate normalization and 15.4 probe semantics are complete; Task 15.5 deterministic replacement is next.",
    "Tasks 15.3–15.5 are complete; Task 15.6 diagnostics and benchmarks is next.",
)
replace_once(
    todo,
    "- The public probe boundary is complete, but production search still does not call it, store entries, select replacements, or activate TT move ordering; insertion and replacement remain Task 15.5.",
    "- The public probe and deterministic store boundaries are complete, but production search still does not call them or activate TT move ordering; diagnostics remain Task 15.6 and search integration remains in the overall Task 15 gate.",
)
replace_once(
    todo,
    "- Task 15.4 safe probe semantics is complete; Task 15.5 deterministic replacement is next.",
    "- Tasks 15.4–15.5 are complete; Task 15.6 diagnostics and benchmarks is next.",
)
replace_once(
    todo,
    "- Production search still does not call the probe boundary, insert entries, choose replacements, or activate TT move ordering; Task 15.5 owns deterministic same-key updates and collision replacement.",
    "- Deterministic same-key updates and collision replacement are complete, but production search still does not call the probe/store boundaries or activate TT move ordering; diagnostics remain Task 15.6 and search integration remains in the overall Task 15 gate.",
)
replace_once(
    todo,
    "- Task 15.5 deterministic depth- and age-aware replacement is next.\n\n# Task 16:",
    "- Task 15.5 deterministic depth- and age-aware replacement is complete; Task 15.6 diagnostics and benchmarks is next.\n\n### Task 15.5 completion evidence\n\n- Store implementation: `crates/chess-search/src/transposition/store.rs`.\n- Public API: `TranspositionTable::store`, `TranspositionStoreAction`, and `TranspositionStoreResult`.\n- Contract documentation: `docs/RUST_TRANSPOSITION_TABLE_REPLACEMENT.md`.\n- Exact validated implementation SHA: `775013a6e11aad7625c88b0cd3b258819211e839`.\n- Permanent CI run/job: `30767556904` / `91548869513`.\n- Complete-key matches update the existing slot in place, preventing duplicate entries for one position.\n- The table's current generation is authoritative for every incoming entry.\n- Different-key stores use the lowest-index empty slot before considering replacement.\n- Full clusters evict the shallowest entry, then the oldest modulo-256 generation, then the lowest slot index.\n- Every store reports its cluster, slot, action, and prior or evicted entry where applicable.\n- Five deterministic cluster-level tests passed, bringing the workspace total to 184 executed non-doc Rust tests.\n- The first validation attempt exposed only a test-only import scoped into production; the second exposed only a strict-Clippy fixture-loop style issue. Both were corrected without lint suppression or replacement-policy changes.\n- Results: workspace assets, permanent Task 14.5 exclusion audit over 12 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 184 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.\n- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.\n- First-party warnings: none.\n- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.\n- Diagnostics, hash-full estimation, microbenchmarks, and production search integration remain outside Task 15.5.\n- Task 15.6 diagnostics and benchmarks is next.\n\n# Task 16:",
)
replace_once(
    todo,
    "1. Implement Task 15.5 deterministic transposition-table insertion and replacement.\n2. Update an existing complete-key entry deterministically instead of creating duplicate same-key slots.\n3. Prefer empty slots, then define depth-preferred and generation-aware collision replacement with stable tie-breaking.\n4. Document exactly which colliding entry is displaced and add deterministic cluster-level regressions.\n5. Preserve the Task 15.4 probe contract and keep repetition-sensitive score suppression unchanged.\n6. Defer diagnostics and benchmarks to Task 15.6, and keep Task 16 iterative deepening, aspiration windows, PV reconstruction, and production limits outside Task 15.",
    "1. Implement Task 15.6 transposition-table diagnostics and benchmarks.\n2. Count probes, complete-key hits, exact hits, bound cutoffs, stores, same-key updates, empty insertions, and collision replacements.\n3. Provide deterministic snapshot/reset operations and a bounded hash-full estimate without scanning unbounded state.\n4. Add repeatable release-mode probe and store microbenchmarks over fixed fixtures.\n5. Preserve fixed-capacity allocation, mate normalization, repetition suppression, and deterministic replacement semantics.\n6. After Task 15.6, complete the overall Task 15 gate by integrating the table into production alpha-beta and proving correctness and measurable usefulness; keep Task 16 outside Task 15.",
)

# Ralph-loop status.
ralph = root / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
replace_once(
    ralph,
    "**Current phase:** Tasks 15.1–15.4 complete; Task 15.5 deterministic replacement is next",
    "**Current phase:** Tasks 15.1–15.5 complete; Task 15.6 diagnostics and benchmarks is next",
)
replace_once(
    ralph,
    "| 15.4 | `b6a015e6cc519aa0bbc8e7bde7dde06bdd660b44` | `30766760085` / `91546779835` | complete-key, depth- and bound-safe probes, repetition suppression, eight focused tests, 179 Rust tests, depth-four perft, and differential oracle green |",
    "| 15.4 | `b6a015e6cc519aa0bbc8e7bde7dde06bdd660b44` | `30766760085` / `91546779835` | complete-key, depth- and bound-safe probes, repetition suppression, eight focused tests, 179 Rust tests, depth-four perft, and differential oracle green |\n| 15.5 | `775013a6e11aad7625c88b0cd3b258819211e839` | `30767556904` / `91548869513` | deterministic same-key updates and depth/age replacement, five focused tests, 184 Rust tests, depth-four perft, and differential oracle green |",
)
replace_once(
    ralph,
    "- Mate normalization is complete; probe semantics, replacement policy, diagnostics, and search integration remain intentionally outside Task 15.2.\n- Task 15.4 safe probe semantics is complete; Task 15.5 deterministic replacement is next.",
    "- Mate normalization, probe semantics, and replacement policy are complete; diagnostics and search integration remain intentionally outside Task 15.2.\n- Task 15.6 diagnostics and benchmarks is next.",
)
replace_once(
    ralph,
    "- Probe semantics are complete; replacement, diagnostics, and production search integration remain intentionally outside Task 15.3.\n- Task 15.4 safe probe semantics is next.",
    "- Probe semantics and replacement are complete; diagnostics and production search integration remain intentionally outside Task 15.3.\n- Task 15.6 diagnostics and benchmarks is next.",
)
replace_once(
    ralph,
    "- Insertion, same-key updates, depth/age replacement, diagnostics, and production search integration remain intentionally outside Task 15.4.\n- Task 15.5 deterministic replacement is next.\n\n## Task 15 active scope",
    "- Deterministic insertion and replacement are complete; diagnostics and production search integration remain intentionally outside Task 15.4.\n- Task 15.6 diagnostics and benchmarks is next.\n\n## Task 15.5 completion\n\nImplemented and validated:\n\n- public `TranspositionTable::store` insertion in `crates/chess-search/src/transposition/store.rs`;\n- in-place complete-key updates with no duplicate same-key slot;\n- authoritative assignment of the table's current generation;\n- stable lowest-index empty-slot selection;\n- full-cluster replacement ordered by shallowest depth, oldest wrapping generation age, and lowest slot index;\n- observable update, insertion, and eviction results;\n- five focused deterministic cluster regressions;\n- `docs/RUST_TRANSPOSITION_TABLE_REPLACEMENT.md`.\n\nEvidence:\n\n- Exact validated implementation SHA: `775013a6e11aad7625c88b0cd3b258819211e839`.\n- Permanent CI run/job: `30767556904` / `91548869513`.\n- Results: workspace assets, Task 14.5 audit over 12 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 184 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.\n- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.\n- First-party warnings: none.\n- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.\n- The first two validation iterations exposed only a test-only import scope issue and a strict-Clippy fixture-loop issue; both were corrected without suppressions or policy changes.\n- Diagnostics, hash-full estimation, microbenchmarks, and production search integration remain intentionally outside Task 15.5.\n- Task 15.6 diagnostics and benchmarks is next.\n\n## Task 15 active scope",
)
replace_once(
    ralph,
    "- [ ] Implement Task 15.5 deterministic replacement.",
    "- [x] Implement Task 15.5 deterministic replacement.",
)
replace_once(
    ralph,
    "No pull request has been created; work remains on `rust-engine`. Task 15.5 deterministic transposition-table replacement is the next operation.",
    "No pull request has been created; work remains on `rust-engine`. Task 15.6 transposition-table diagnostics and benchmarks is the next operation.",
)
