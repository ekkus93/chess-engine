from pathlib import Path
import sys

root = Path(sys.argv[1])

def replace_required(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    if old not in text:
        raise SystemExit(f"required text not found in {path}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1))

# Check the authoritative Task 15.4 criteria.
definitions = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
replace_required(
    definitions,
    """## 15.4 Probe semantics

- [ ] Depth sufficiency.
- [ ] Exact hit.
- [ ] Lower-bound cutoff.
- [ ] Upper-bound cutoff.
- [ ] Best-move use even when score cannot be reused.
- [ ] Safe handling of repetition-sensitive nodes.
""",
    """## 15.4 Probe semantics

- [x] Depth sufficiency.
- [x] Exact hit.
- [x] Lower-bound cutoff.
- [x] Upper-bound cutoff.
- [x] Best-move use even when score cannot be reused.
- [x] Safe handling of repetition-sensitive nodes.
""",
)

# Update the authoritative TODO and add exact evidence.
todo = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
text = todo.read_text()
replacements = [
    (
        "| 15 | **Active** — Tasks 15.1–15.3 complete; Task 15.4 safe probe semantics next. |",
        "| 15 | **Active** — Tasks 15.1–15.4 complete; Task 15.5 deterministic replacement next. |",
    ),
    (
        "- Task 14 is complete. Tasks 15.1–15.3 are complete; Task 15.4 safe probe semantics is next.",
        "- Task 14 is complete. Tasks 15.1–15.4 are complete; Task 15.5 deterministic replacement is next.",
    ),
    ("- [ ] 15.4 Probes.", "- [x] 15.4 Probes."),
    (
        "- Tasks 15.2 fixed-memory storage and 15.3 mate normalization are complete; Task 15.4 safe probe semantics is next.",
        "- Tasks 15.2–15.4 are complete; Task 15.5 deterministic replacement is next.",
    ),
    (
        "- Task 15.3 ply-relative mate-score normalization is complete; Task 15.4 safe probe semantics is next.",
        "- Tasks 15.3 mate normalization and 15.4 probe semantics are complete; Task 15.5 deterministic replacement is next.",
    ),
    (
        "- Production search still does not probe entries, apply depth/bound cutoffs, reuse repetition-sensitive scores, store entries, select replacements, or activate TT move ordering; those remain Tasks 15.4–15.5.",
        "- The public probe boundary is complete, but production search still does not call it, store entries, select replacements, or activate TT move ordering; insertion and replacement remain Task 15.5.",
    ),
    (
        "- Task 15.4 safe transposition-table probe semantics is next.",
        "- Task 15.4 safe probe semantics is complete; Task 15.5 deterministic replacement is next.",
    ),
]
for old, new in replacements:
    if old not in text:
        raise SystemExit(f"TODO replacement missing: {old}")
    text = text.replace(old, new, 1)

section = """
### Task 15.4 completion evidence

- Probe implementation: `crates/chess-search/src/transposition/probe.rs`.
- Public API: `TranspositionTable::probe`, `TranspositionProbeRequest`, `TranspositionProbeResult`, `TranspositionProbeScore`, `TranspositionProbeError`, and `TranspositionScoreReuse`.
- Contract documentation: `docs/RUST_TRANSPOSITION_TABLE_PROBE_SEMANTICS.md`.
- Exact validated implementation SHA: `b6a015e6cc519aa0bbc8e7bde7dde06bdd660b44`.
- Permanent CI run/job: `30766760085` / `91546779835`.
- Probes select a deterministic cluster and accept only a complete 64-bit verification-key match; index collisions remain misses.
- Score reuse requires stored depth at least equal to requested depth, while a verified best move remains available for ordering at insufficient depth.
- Exact entries return a denormalized value; lower bounds cut off only at or above beta; upper bounds cut off only at or below alpha.
- Mate scores are denormalized at the current probe ply before window comparison or return.
- `TranspositionScoreReuse::SuppressedForRepetition` disables all cached score reuse for path-dependent repetition nodes while retaining the verified move as an ordering hint only.
- Invalid alpha-beta windows and score-conversion failures return typed errors; no clamping, fallback score, or partial-key acceptance is permitted.
- Eight deterministic probe tests passed, bringing the workspace total to 179 executed non-doc Rust tests.
- Production search still does not call the probe boundary, insert entries, choose replacements, or activate TT move ordering; Task 15.5 owns deterministic same-key updates and collision replacement.
- Results: workspace assets, permanent Task 14.5 exclusion audit over 12 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 179 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 15.5 deterministic depth- and age-aware replacement is next.

"""
marker = "# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED"
if section not in text:
    if marker not in text:
        raise SystemExit("Task 16 marker missing from TODO")
    text = text.replace(marker, section + marker, 1)

old_next = """## Immediate next operations

1. Implement Task 15.4 safe transposition-table probe semantics.
2. Require complete-key verification and sufficient stored depth before score reuse.
3. Implement exact hits plus lower-bound and upper-bound cutoffs using denormalized scores at the current ply.
4. Return a verified best move for ordering even when depth or bounds do not permit score reuse.
5. Define fail-safe handling for repetition-sensitive nodes before enabling production search integration.
6. Defer replacement preference and diagnostics to Tasks 15.5–15.6, and keep Task 16 iterative deepening, aspiration windows, PV reconstruction, and production limits outside Task 15."""
new_next = """## Immediate next operations

1. Implement Task 15.5 deterministic transposition-table insertion and replacement.
2. Update an existing complete-key entry deterministically instead of creating duplicate same-key slots.
3. Prefer empty slots, then define depth-preferred and generation-aware collision replacement with stable tie-breaking.
4. Document exactly which colliding entry is displaced and add deterministic cluster-level regressions.
5. Preserve the Task 15.4 probe contract and keep repetition-sensitive score suppression unchanged.
6. Defer diagnostics and benchmarks to Task 15.6, and keep Task 16 iterative deepening, aspiration windows, PV reconstruction, and production limits outside Task 15."""
if old_next not in text:
    raise SystemExit("TODO immediate-next block missing")
text = text.replace(old_next, new_next, 1)
todo.write_text(text)

# Update Ralph status and evidence.
ralph = root / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
text = ralph.read_text()
replacements = [
    (
        "**Current phase:** Tasks 15.1–15.3 complete; Task 15.4 safe probe semantics is next",
        "**Current phase:** Tasks 15.1–15.4 complete; Task 15.5 deterministic replacement is next",
    ),
    (
        "| 15.3 | `ac68b99db53546c31f3aae68ad7337ba256eb982` | `30766126491` / `91545080021` | ply-correct mate normalization, typed conversion failures, six focused tests, 171 Rust tests, depth-four perft, and differential oracle green |",
        "| 15.3 | `ac68b99db53546c31f3aae68ad7337ba256eb982` | `30766126491` / `91545080021` | ply-correct mate normalization, typed conversion failures, six focused tests, 171 Rust tests, depth-four perft, and differential oracle green |\n| 15.4 | `b6a015e6cc519aa0bbc8e7bde7dde06bdd660b44` | `30766760085` / `91546779835` | complete-key, depth- and bound-safe probes, repetition suppression, eight focused tests, 179 Rust tests, depth-four perft, and differential oracle green |",
    ),
    (
        "- Task 15.4 safe probe semantics is next.",
        "- Task 15.4 safe probe semantics is complete; Task 15.5 deterministic replacement is next.",
    ),
    (
        "- Probe semantics, repetition-sensitive reuse, replacement, diagnostics, and production search integration remain intentionally outside Task 15.3.",
        "- Probe semantics are complete; replacement, diagnostics, and production search integration remain intentionally outside Task 15.3.",
    ),
    (
        "- [ ] Implement Task 15.4 safe probe semantics.",
        "- [x] Implement Task 15.4 safe probe semantics.",
    ),
    (
        "No pull request has been created; work remains on `rust-engine`. Task 15.4 safe transposition-table probe semantics is the next operation.",
        "No pull request has been created; work remains on `rust-engine`. Task 15.5 deterministic transposition-table replacement is the next operation.",
    ),
]
for old, new in replacements:
    if old not in text:
        raise SystemExit(f"Ralph replacement missing: {old}")
    text = text.replace(old, new, 1)

ralph_section = """
## Task 15.4 completion

Implemented and validated:

- a public, storage-only `TranspositionTable::probe` boundary in `crates/chess-search/src/transposition/probe.rs`;
- complete 64-bit verification-key matching after deterministic cluster selection;
- stored-depth sufficiency before score reuse;
- exact-score returns and fail-high/fail-low bound cutoffs at the correct beta/alpha edges;
- current-ply mate-score denormalization before comparison or return;
- verified best-move delivery even when depth or bounds do not permit score reuse;
- explicit `SuppressedForRepetition` handling that disables cached scores while retaining move ordering;
- typed invalid-window and score-conversion failures;
- eight focused probe regressions;
- `docs/RUST_TRANSPOSITION_TABLE_PROBE_SEMANTICS.md`.

Evidence:

- Exact validated implementation SHA: `b6a015e6cc519aa0bbc8e7bde7dde06bdd660b44`.
- Permanent CI run/job: `30766760085` / `91546779835`.
- Results: workspace assets, Task 14.5 audit over 12 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 179 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Insertion, same-key updates, depth/age replacement, diagnostics, and production search integration remain intentionally outside Task 15.4.
- Task 15.5 deterministic replacement is next.

"""
marker = "## Task 15 active scope"
if ralph_section not in text:
    if marker not in text:
        raise SystemExit("Task 15 active-scope marker missing from Ralph status")
    text = text.replace(marker, ralph_section + marker, 1)
ralph.write_text(text)
