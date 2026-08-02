#!/usr/bin/env python3
"""Close Task 15.1 after exact-SHA validation."""

from __future__ import annotations

import sys
from pathlib import Path

IMPLEMENTATION_SHA = "65ef70bfbff3d0bf5fd6e6a19ba20ed5214c3e26"
RUN_ID = "30764647127"
JOB_ID = "91541116562"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def close(root: Path) -> None:
    definitions = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
    replace_once(
        definitions,
        """## 15.1 Entry design

- [ ] Verification key/hash fragment.
- [ ] Depth.
- [ ] exact/lower/upper bound.
- [ ] normalized score.
- [ ] best move.
- [ ] age/generation.
""",
        """## 15.1 Entry design

- [x] Verification key/hash fragment.
- [x] Depth.
- [x] exact/lower/upper bound.
- [x] normalized score.
- [x] best move.
- [x] age/generation.
""",
    )

    todo = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
    replace_once(
        todo,
        "| 15–24 | **Not started**. |",
        "| 15 | **Active** — Task 15.1 entry design complete; Task 15.2 fixed-memory storage next. |\n| 16–24 | **Not started**. |",
    )
    replace_once(
        todo,
        "- Task 14 is complete. Task 15.1 fixed-capacity transposition-table entry design is next.",
        "- Task 14 is complete. Task 15.1 entry design is complete; Task 15.2 fixed-memory storage is next.",
    )
    replace_once(
        todo,
        """# Task 15: Fixed-capacity transposition table — NOT STARTED
- [ ] 15.1 Entries.
- [ ] 15.2 Storage.
- [ ] 15.3 Mate normalization.
- [ ] 15.4 Probes.
- [ ] 15.5 Replacement.
- [ ] 15.6 Diagnostics.
- [ ] Task 15 gate.

# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED
""",
        f"""# Task 15: Fixed-capacity transposition table — ACTIVE
- [x] 15.1 Entries.
- [ ] 15.2 Storage.
- [ ] 15.3 Mate normalization.
- [ ] 15.4 Probes.
- [ ] 15.5 Replacement.
- [ ] 15.6 Diagnostics.
- [ ] Task 15 gate.

### Task 15.1 completion evidence

- Entry implementation: `crates/chess-search/src/transposition.rs`.
- Public value types: `TranspositionEntry`, `TranspositionBound`, and `TranspositionScore`, re-exported by `chess-search`.
- Contract documentation: `docs/RUST_TRANSPOSITION_TABLE_ENTRY.md`.
- Exact validated implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent CI run/job: `{RUN_ID}` / `{JOB_ID}`.
- The entry retains the complete 64-bit verification key, `u16` search depth, explicit exact/lower/upper bound, typed normalized score, optional compact `Move`, and one-byte generation.
- `TranspositionScore` establishes a distinct storage-score domain without prematurely implementing Task 15.3 mate conversion.
- `repr(C)` and focused layout tests keep the entry footprint at no more than 24 bytes on supported targets while adding no wrapper overhead around `Score`.
- Five deterministic tests cover stable bound tags, all required fields, every bound, absent best moves, full-key verification, copy/value semantics, and bounded layout.
- Production search still does not allocate, probe, store, cut off, or activate TT move ordering; those remain Tasks 15.2–15.4.
- Results: workspace assets, permanent Task 14.5 exclusion audit over 11 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 160 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 15.2 fixed-memory bucket/cluster storage is next.

# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED
""",
    )
    replace_once(
        todo,
        """1. Implement Task 15.1 transposition-table entry design with verification key, depth, bound flag, normalized score, best move, and age/generation.
2. Define fixed-memory bucket/cluster storage and explicit clear/new-generation operations before integrating probes into search.
3. Preserve mate-score normalization across different plies and add exact store/probe regressions before enabling TT cutoffs.
4. Keep repetition-sensitive reuse fail-safe and retain exact full-window score semantics.
5. Benchmark probes, stores, replacement behavior, and node reduction only after correctness tests pass.
6. Keep Task 16 iterative deepening, aspiration windows, PV reconstruction, and production limits outside Task 15.
""",
        """1. Implement Task 15.2 fixed-memory bucket/cluster storage configured in MiB.
2. Define predictable allocation-failure behavior plus explicit clear and new-generation operations.
3. Keep entries optional without an unbounded map or per-node allocation fallback.
4. Preserve the Task 15.1 full-key, bound, normalized-score, best-move, depth, and generation contract unchanged.
5. Defer mate-score conversion, probe cutoffs, replacement preference, and diagnostics to Tasks 15.3–15.6.
6. Keep Task 16 iterative deepening, aspiration windows, PV reconstruction, and production limits outside Task 15.
""",
    )

    ralph = root / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
    replace_once(
        ralph,
        "**Current phase:** Task 14 complete; Task 15.1 transposition-table entry design is next",
        "**Current phase:** Task 15.1 entry design complete; Task 15.2 fixed-memory storage is next",
    )
    replace_once(
        ralph,
        "| 14.5 / 14 | `f4dc989e97d8577f4c86bdbfb67ae47e3d5cd7f4` | `30764073097` / `91539614372` | permanent exclusion audit, exact-score boundary, 155 Rust tests, depth-four perft, and differential oracle green |",
        f"""| 14.5 / 14 | `f4dc989e97d8577f4c86bdbfb67ae47e3d5cd7f4` | `30764073097` / `91539614372` | permanent exclusion audit, exact-score boundary, 155 Rust tests, depth-four perft, and differential oracle green |
| 15.1 | `{IMPLEMENTATION_SHA}` | `{RUN_ID}` / `{JOB_ID}` | complete TT entry payload, five focused tests, 160 Rust tests, depth-four perft, and differential oracle green |""",
    )
    replace_once(
        ralph,
        "- Task 14 is complete; Task 15.1 is next.",
        "- Task 14 is complete; Task 15.1 entry design is complete and Task 15.2 storage is next.",
    )
    replace_once(
        ralph,
        """## Task 14 completed scope
""",
        f"""## Task 15.1 completion

Implemented and validated:

- a complete copyable transposition-entry payload in `crates/chess-search/src/transposition.rs`;
- the full 64-bit Zobrist verification key rather than an index-only fragment;
- `u16` depth and explicit one-byte `Exact`, `Lower`, and `Upper` bound tags;
- a distinct `TranspositionScore` storage-domain wrapper around `Score`;
- optional compact best-move identity and one-byte generation metadata;
- stable public accessors and `chess-search` re-exports;
- a bounded, predictable `repr(C)` layout of at most 24 bytes on supported targets;
- five focused entry-contract tests;
- `docs/RUST_TRANSPOSITION_TABLE_ENTRY.md`.

Evidence:

- Exact validated implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent CI run/job: `{RUN_ID}` / `{JOB_ID}`.
- Results: workspace assets, Task 14.5 audit over 11 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 160 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Storage allocation, buckets, empty slots, clearing, generation advancement, normalization, probes, replacement, and diagnostics remain intentionally outside Task 15.1.
- Task 15.2 fixed-memory storage is next.

## Task 15 active scope

- [x] Complete Task 15.1 entry design.
- [ ] Implement Task 15.2 fixed-memory storage.
- [ ] Implement Task 15.3 mate-score normalization.
- [ ] Implement Task 15.4 safe probe semantics.
- [ ] Implement Task 15.5 deterministic replacement.
- [ ] Implement Task 15.6 diagnostics and benchmarks.
- [ ] Pass the overall Task 15 gate.

## Task 14 completed scope
""",
    )
    replace_once(
        ralph,
        "No pull request has been created; work remains on `rust-engine`. Task 15.1 transposition-table entry design is the next operation.",
        "No pull request has been created; work remains on `rust-engine`. Task 15.2 fixed-memory transposition-table storage is the next operation.",
    )


if __name__ == "__main__":
    repository_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    close(repository_root)
