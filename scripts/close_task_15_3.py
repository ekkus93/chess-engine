#!/usr/bin/env python3
"""Close Task 15.3 after exact-SHA permanent validation."""

from __future__ import annotations

import sys
from pathlib import Path

IMPLEMENTATION_SHA = "ac68b99db53546c31f3aae68ad7337ba256eb982"
RUN_ID = "30766126491"
JOB_ID = "91545080021"


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
        """## 15.3 Mate normalization

- [ ] Normalize ply-relative mate scores on store.
- [ ] Denormalize on probe.
- [ ] Test same TT entry reached at different plies.
""",
        """## 15.3 Mate normalization

- [x] Normalize ply-relative mate scores on store.
- [x] Denormalize on probe.
- [x] Test same TT entry reached at different plies.
""",
    )

    todo = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
    replace_once(
        todo,
        "| 15 | **Active** — Tasks 15.1–15.2 complete; Task 15.3 mate normalization next. |",
        "| 15 | **Active** — Tasks 15.1–15.3 complete; Task 15.4 safe probe semantics next. |",
    )
    replace_once(
        todo,
        "- Task 14 is complete. Tasks 15.1–15.2 are complete; Task 15.3 mate normalization is next.",
        "- Task 14 is complete. Tasks 15.1–15.3 are complete; Task 15.4 safe probe semantics is next.",
    )
    replace_once(
        todo,
        """# Task 15: Fixed-capacity transposition table — ACTIVE
- [x] 15.1 Entries.
- [x] 15.2 Storage.
- [ ] 15.3 Mate normalization.
- [ ] 15.4 Probes.
""",
        """# Task 15: Fixed-capacity transposition table — ACTIVE
- [x] 15.1 Entries.
- [x] 15.2 Storage.
- [x] 15.3 Mate normalization.
- [ ] 15.4 Probes.
""",
    )
    replace_once(
        todo,
        "- Task 15.2 fixed-memory bucket/cluster storage is complete; Task 15.3 mate normalization is next.",
        "- Tasks 15.2 fixed-memory storage and 15.3 mate normalization are complete; Task 15.4 safe probe semantics is next.",
    )
    replace_once(
        todo,
        "- Production search still does not probe, store, cut off, normalize mate scores, or apply replacement policy; those remain Tasks 15.3–15.5.",
        "- Production search still does not probe, store, cut off, or apply replacement policy; those remain Tasks 15.4–15.5.",
    )
    replace_once(
        todo,
        """- Task 15.3 ply-relative mate-score normalization is next.

# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED
""",
        f"""- Task 15.3 ply-relative mate-score normalization is complete; Task 15.4 safe probe semantics is next.

### Task 15.3 completion evidence

- Conversion implementation: `crates/chess-search/src/transposition_score.rs`.
- Public API: `TranspositionScore::normalize`, `TranspositionScore::denormalize`, and `TranspositionScoreConversionError`.
- Contract documentation: `docs/RUST_TRANSPOSITION_TABLE_MATE_NORMALIZATION.md`.
- Exact validated implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent CI run/job: `{RUN_ID}` / `{JOB_ID}`.
- Winning mate scores add the current root ply on storage and subtract the probe ply on retrieval; losing mate scores perform the inverse operations.
- The conversion removes already-travelled root distance so the same position produces one normalized TT value when reached at different plies.
- Every ordinary evaluation from `-MAX_EVALUATION` through `MAX_EVALUATION` is preserved exactly.
- Unsupported plies and conversions outside the supported score domain return typed errors; no clamping, saturation, or fallback score is permitted.
- The unchecked `TranspositionScore::from_normalized` constructor is crate-private, preventing external callers from bypassing the conversion boundary.
- Six deterministic tests cover ordinary evaluations, winning and losing cross-ply reuse, both maximum-ply boundaries, inconsistent mate values, and unsupported plies.
- Production search still does not probe entries, apply depth/bound cutoffs, reuse repetition-sensitive scores, store entries, select replacements, or activate TT move ordering; those remain Tasks 15.4–15.5.
- Results: workspace assets, permanent Task 14.5 exclusion audit over 12 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 171 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 15.4 safe transposition-table probe semantics is next.

# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED
""",
    )
    replace_once(
        todo,
        """## Immediate next operations

1. Implement Task 15.3 mate-score normalization at the transposition storage boundary.
2. Normalize ply-relative winning and losing mate scores on store and denormalize them on retrieval.
3. Add deterministic regressions proving one stored entry is correct when reached at different plies.
4. Preserve ordinary evaluation scores exactly and reject arithmetic outside the supported score domain.
5. Defer probe cutoffs, repetition-sensitive reuse, replacement preference, and diagnostics to Tasks 15.4–15.6.
6. Keep Task 16 iterative deepening, aspiration windows, PV reconstruction, and production limits outside Task 15.
""",
        """## Immediate next operations

1. Implement Task 15.4 safe transposition-table probe semantics.
2. Require complete-key verification and sufficient stored depth before score reuse.
3. Implement exact hits plus lower-bound and upper-bound cutoffs using denormalized scores at the current ply.
4. Return a verified best move for ordering even when depth or bounds do not permit score reuse.
5. Define fail-safe handling for repetition-sensitive nodes before enabling production search integration.
6. Defer replacement preference and diagnostics to Tasks 15.5–15.6, and keep Task 16 iterative deepening, aspiration windows, PV reconstruction, and production limits outside Task 15.
""",
    )

    status = root / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
    replace_once(
        status,
        "**Current phase:** Tasks 15.1–15.2 complete; Task 15.3 mate normalization is next",
        "**Current phase:** Tasks 15.1–15.3 complete; Task 15.4 safe probe semantics is next",
    )
    replace_once(
        status,
        "| 15.2 | `6b2ee0081cd47fd9069aeabb0d3ccb1d3659fea9` | `30765303745` / `91542820537` | fixed MiB storage, four-entry clusters, typed allocation failures, clear/generation operations, 165 Rust tests, depth-four perft, and differential oracle green |",
        f"""| 15.2 | `6b2ee0081cd47fd9069aeabb0d3ccb1d3659fea9` | `30765303745` / `91542820537` | fixed MiB storage, four-entry clusters, typed allocation failures, clear/generation operations, 165 Rust tests, depth-four perft, and differential oracle green |
| 15.3 | `{IMPLEMENTATION_SHA}` | `{RUN_ID}` / `{JOB_ID}` | ply-correct mate normalization, typed conversion failures, six focused tests, 171 Rust tests, depth-four perft, and differential oracle green |""",
    )
    replace_once(
        status,
        "- Task 14 is complete; Tasks 15.1–15.2 are complete and Task 15.3 mate normalization is next.",
        "- Task 14 is complete; Tasks 15.1–15.3 are complete and Task 15.4 safe probe semantics is next.",
    )
    replace_once(
        status,
        "- Task 15.2 fixed-memory storage is complete; Task 15.3 mate normalization is next.",
        "- Tasks 15.2 fixed-memory storage and 15.3 mate normalization are complete; Task 15.4 safe probe semantics is next.",
    )
    replace_once(
        status,
        """- Mate normalization, probe semantics, replacement policy, diagnostics, and search integration remain intentionally outside Task 15.2.
- Task 15.3 mate-score normalization is next.

## Task 15 active scope
""",
        f"""- Mate normalization is complete; probe semantics, replacement policy, diagnostics, and search integration remain intentionally outside Task 15.2.
- Task 15.4 safe probe semantics is next.

## Task 15.3 completion

Implemented and validated:

- root-relative to position-relative conversion in `crates/chess-search/src/transposition_score.rs`;
- winning-mate normalization by adding storage ply and denormalization by subtracting probe ply;
- losing-mate normalization by subtracting storage ply and denormalization by adding probe ply;
- exact preservation of every ordinary evaluation score;
- typed rejection of unsupported plies and out-of-domain conversions;
- a crate-private unchecked constructor so public callers must use the tested conversion boundary;
- six focused regressions, including the same winning and losing TT values reached at different plies;
- `docs/RUST_TRANSPOSITION_TABLE_MATE_NORMALIZATION.md`.

Evidence:

- Exact validated implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent CI run/job: `{RUN_ID}` / `{JOB_ID}`.
- Results: workspace assets, Task 14.5 audit over 12 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 171 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Probe semantics, repetition-sensitive reuse, replacement, diagnostics, and production search integration remain intentionally outside Task 15.3.
- Task 15.4 safe probe semantics is next.

## Task 15 active scope
""",
    )
    replace_once(
        status,
        """- [x] Complete Task 15.1 entry design.
- [x] Implement Task 15.2 fixed-memory storage.
- [ ] Implement Task 15.3 mate-score normalization.
- [ ] Implement Task 15.4 safe probe semantics.
""",
        """- [x] Complete Task 15.1 entry design.
- [x] Implement Task 15.2 fixed-memory storage.
- [x] Implement Task 15.3 mate-score normalization.
- [ ] Implement Task 15.4 safe probe semantics.
""",
    )
    replace_once(
        status,
        "No pull request has been created; work remains on `rust-engine`. Task 15.3 transposition-table mate-score normalization is the next operation.",
        "No pull request has been created; work remains on `rust-engine`. Task 15.4 safe transposition-table probe semantics is the next operation.",
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: close_task_15_3.py <repository-root>")
    close(Path(sys.argv[1]).resolve())
