#!/usr/bin/env python3
"""Close Task 15.2 after exact-SHA permanent validation."""

from __future__ import annotations

import sys
from pathlib import Path

IMPLEMENTATION_SHA = "6b2ee0081cd47fd9069aeabb0d3ccb1d3659fea9"
RUN_ID = "30765303745"
JOB_ID = "91542820537"


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
        """## 15.2 Storage layout

- [ ] Fixed memory configured in MiB.
- [ ] Bucket/cluster design.
- [ ] Predictable allocation failure behavior.
- [ ] Explicit clear/new-generation operations.
""",
        """## 15.2 Storage layout

- [x] Fixed memory configured in MiB.
- [x] Bucket/cluster design.
- [x] Predictable allocation failure behavior.
- [x] Explicit clear/new-generation operations.
""",
    )

    todo = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
    replace_once(
        todo,
        "| 15 | **Active** — Task 15.1 entry design complete; Task 15.2 fixed-memory storage next. |",
        "| 15 | **Active** — Tasks 15.1–15.2 complete; Task 15.3 mate normalization next. |",
    )
    replace_once(
        todo,
        "- Task 14 is complete. Task 15.1 entry design is complete; Task 15.2 fixed-memory storage is next.",
        "- Task 14 is complete. Tasks 15.1–15.2 are complete; Task 15.3 mate normalization is next.",
    )
    replace_once(
        todo,
        """# Task 15: Fixed-capacity transposition table — ACTIVE
- [x] 15.1 Entries.
- [ ] 15.2 Storage.
- [ ] 15.3 Mate normalization.
""",
        """# Task 15: Fixed-capacity transposition table — ACTIVE
- [x] 15.1 Entries.
- [x] 15.2 Storage.
- [ ] 15.3 Mate normalization.
""",
    )
    replace_once(
        todo,
        """- Task 15.2 fixed-memory bucket/cluster storage is next.

# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED
""",
        f"""- Task 15.2 fixed-memory bucket/cluster storage is complete; Task 15.3 mate normalization is next.

### Task 15.2 completion evidence

- Storage implementation: `crates/chess-search/src/transposition.rs`.
- Public API: `TranspositionTable`, `TranspositionTableAllocationError`, and `TRANSPOSITION_CLUSTER_SIZE`.
- Storage contract: `docs/RUST_TRANSPOSITION_TABLE_STORAGE.md`.
- Exact validated implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent CI run/job: `{RUN_ID}` / `{JOB_ID}`.
- MiB configuration uses checked byte arithmetic and rounds down only to complete four-entry clusters.
- Construction performs one fallible fixed-size `Vec` reservation, never grows afterward, and has no map, per-node allocation, silent shrinking, or unbounded fallback.
- Allocation failures are typed for zero size, arithmetic overflow, no complete cluster, and allocator rejection.
- Complete verification keys map deterministically to clusters while each occupied entry retains its complete key for later collision rejection.
- `clear()` empties every slot in place without reallocating or changing generation; `advance_generation()` wraps deterministically without clearing existing entries.
- Five new deterministic storage tests passed, bringing the workspace total to 165 executed non-doc Rust tests.
- Production search still does not probe, store, cut off, normalize mate scores, or apply replacement policy; those remain Tasks 15.3–15.5.
- Results: workspace assets, permanent Task 14.5 exclusion audit over 11 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 165 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 15.3 ply-relative mate-score normalization is next.

# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED
""",
    )
    replace_once(
        todo,
        """1. Implement Task 15.2 fixed-memory bucket/cluster storage configured in MiB.
2. Define predictable allocation-failure behavior plus explicit clear and new-generation operations.
3. Keep entries optional without an unbounded map or per-node allocation fallback.
4. Preserve the Task 15.1 full-key, bound, normalized-score, best-move, depth, and generation contract unchanged.
5. Defer mate-score conversion, probe cutoffs, replacement preference, and diagnostics to Tasks 15.3–15.6.
6. Keep Task 16 iterative deepening, aspiration windows, PV reconstruction, and production limits outside Task 15.
""",
        """1. Implement Task 15.3 mate-score normalization at the transposition storage boundary.
2. Normalize ply-relative winning and losing mate scores on store and denormalize them on retrieval.
3. Add deterministic regressions proving one stored entry is correct when reached at different plies.
4. Preserve ordinary evaluation scores exactly and reject arithmetic outside the supported score domain.
5. Defer probe cutoffs, repetition-sensitive reuse, replacement preference, and diagnostics to Tasks 15.4–15.6.
6. Keep Task 16 iterative deepening, aspiration windows, PV reconstruction, and production limits outside Task 15.
""",
    )

    status = root / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
    replace_once(
        status,
        "**Current phase:** Task 15.1 entry design complete; Task 15.2 fixed-memory storage is next",
        "**Current phase:** Tasks 15.1–15.2 complete; Task 15.3 mate normalization is next",
    )
    replace_once(
        status,
        "| 15.1 | `65ef70bfbff3d0bf5fd6e6a19ba20ed5214c3e26` | `30764647127` / `91541116562` | complete TT entry payload, five focused tests, 160 Rust tests, depth-four perft, and differential oracle green |",
        f"""| 15.1 | `65ef70bfbff3d0bf5fd6e6a19ba20ed5214c3e26` | `30764647127` / `91541116562` | complete TT entry payload, five focused tests, 160 Rust tests, depth-four perft, and differential oracle green |
| 15.2 | `{IMPLEMENTATION_SHA}` | `{RUN_ID}` / `{JOB_ID}` | fixed MiB storage, four-entry clusters, typed allocation failures, clear/generation operations, 165 Rust tests, depth-four perft, and differential oracle green |""",
    )
    replace_once(
        status,
        "- Task 14 is complete; Task 15.1 entry design is complete and Task 15.2 storage is next.",
        "- Task 14 is complete; Tasks 15.1–15.2 are complete and Task 15.3 mate normalization is next.",
    )
    replace_once(
        status,
        """- Task 15.2 fixed-memory storage is next.

## Task 15 active scope
""",
        f"""- Task 15.2 fixed-memory storage is complete; Task 15.3 mate normalization is next.

## Task 15.2 completion

Implemented and validated:

- a fixed-capacity `TranspositionTable` configured in MiB;
- checked MiB-to-byte conversion and whole-cluster budget rounding;
- one private, fallibly reserved `Vec` allocation with no growth or fallback storage;
- four-entry collision clusters and deterministic complete-key cluster indexing;
- typed failures for zero configuration, arithmetic overflow, no complete cluster, and allocator rejection;
- explicit in-place `clear()` preserving allocation and generation;
- explicit wrapping `advance_generation()` retaining existing entries;
- public capacity, allocation, generation, and cluster-index diagnostics required to verify the storage contract;
- five focused storage tests;
- `docs/RUST_TRANSPOSITION_TABLE_STORAGE.md`.

Evidence:

- Exact validated implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent CI run/job: `{RUN_ID}` / `{JOB_ID}`.
- Results: workspace assets, Task 14.5 audit over 11 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 165 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Mate normalization, probe semantics, replacement policy, diagnostics, and search integration remain intentionally outside Task 15.2.
- Task 15.3 mate-score normalization is next.

## Task 15 active scope
""",
    )
    replace_once(
        status,
        """- [x] Complete Task 15.1 entry design.
- [ ] Implement Task 15.2 fixed-memory storage.
- [ ] Implement Task 15.3 mate-score normalization.
""",
        """- [x] Complete Task 15.1 entry design.
- [x] Implement Task 15.2 fixed-memory storage.
- [ ] Implement Task 15.3 mate-score normalization.
""",
    )
    replace_once(
        status,
        "No pull request has been created; work remains on `rust-engine`. Task 15.2 fixed-memory transposition-table storage is the next operation.",
        "No pull request has been created; work remains on `rust-engine`. Task 15.3 transposition-table mate-score normalization is the next operation.",
    )


def main() -> int:
    try:
        root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
        close(root)
    except (OSError, RuntimeError) as error:
        print(f"Task 15.2 closure failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
