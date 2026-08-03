#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one match in {path}, found {count}: {old[:160]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


definitions = ROOT / "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
live = ROOT / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
ralph = ROOT / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"

replace_once(
    definitions,
    """## 16.3 Principal variation

- [ ] Reconstruct PV from search data safely.
- [ ] Validate every PV move is legal in sequence.
- [ ] Avoid TT collision loops.
- [ ] Return ponder move when available.
""",
    """## 16.3 Principal variation

- [x] Reconstruct PV from search data safely.
- [x] Validate every PV move is legal in sequence.
- [x] Avoid TT collision loops.
- [x] Return ponder move when available.
""",
)

replace_once(
    live,
    "| 16 | **Active** — Task 16.1 iterative deepening complete; aspiration windows next. |",
    "| 16 | **Active** — Tasks 16.1 and 16.3 complete; Task 16.2 aspiration windows next. |",
)
replace_once(
    live,
    """# Task 16: Iterative deepening, PV, limits, cancellation — ACTIVE
- [x] 16.1 Iterative deepening.
- [ ] 16.2 Aspiration windows.
- [ ] 16.3 Principal variation.
- [ ] 16.4 Limits.
""",
    """# Task 16: Iterative deepening, PV, limits, cancellation — ACTIVE
- [x] 16.1 Iterative deepening.
- [ ] 16.2 Aspiration windows.
- [x] 16.3 Principal variation.
- [ ] 16.4 Limits.
""",
)
replace_once(
    live,
    "- Task 15 and Task 16.1 are complete. Task 16.2 aspiration windows is next.",
    "- Task 15 and Tasks 16.1/16.3 are complete. Task 16.2 aspiration windows is next.",
)
replace_once(
    live,
    "- Task 16.2 aspiration windows is next. PV reconstruction, limits, cancellation recovery, final result API, and extensions remain deferred.\n\n# Task 17: Linux UCI executable — NOT STARTED",
    """- Task 16.2 aspiration windows is next. Limits, cancellation recovery, the final result API, and extensions remain deferred.

### Task 16.3 completion evidence

- Implementation: `crates/chess-search/src/principal_variation.rs` and `crates/chess-search/src/transposition/principal_variation.rs`, integrated through `alpha_beta.rs`, `iterative_deepening.rs`, and public exports in `lib.rs`.
- Public APIs: `PrincipalVariation`, `PrincipalVariationTermination`, `PrincipalVariationError`, per-iteration/final `principal_variation`, and per-iteration/final `ponder_move`.
- The exact root result supplies the first PV move; later moves require a complete-key exact TT entry with sufficient remaining depth and a stored move.
- Every candidate is regenerated and matched against a current legal token before it can enter the returned line.
- Reconstruction is bounded by completed depth, terminates explicitly on missing data, terminal positions, illegal stored moves, or repeated Zobrist identities, and cannot loop through a colliding TT chain.
- The ponder move is returned only as the second validated legal PV move.
- PV lookup is observational and does not alter TT diagnostics, generation, allocation, or replacement state.
- Internal exact entries now retain their searched best move so a complete exact chain can be reconstructed after root restoration.
- Contract documentation: `docs/RUST_PRINCIPAL_VARIATION.md`; iterative-deepening documentation updated accordingly.
- Exact clean validated implementation SHA: `e8afc9959a60519c6d5617963521e1707d37c6a9`.
- Permanent CI run/job: `30776274173` / `91572310565`.
- Results: permanent exclusion audit over 14 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 204 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Focused coverage includes exact-chain reconstruction, legal replay, ponder extraction, full-key collision rejection, exact-bound/depth requirements, illegal-entry rejection, repeated-position termination, terminal roots, and diagnostic non-mutation.
- The first compiler iteration found only an ambiguous integer literal in a collision test; adding an explicit `u64` fixed the test without changing production behavior.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16.2 aspiration windows remains open and is the next operation.

# Task 17: Linux UCI executable — NOT STARTED""",
)
replace_once(
    live,
    "6. Keep PV reconstruction, time/node limits, responsive cancellation, the final result API, and check extensions in Tasks 16.3–16.7.",
    "6. Preserve the completed Task 16.3 legal PV/ponder contract while keeping limits, responsive cancellation, the final result API, and check extensions in Tasks 16.4–16.7.",
)

replace_once(
    ralph,
    "**Current phase:** Task 16.1 iterative deepening complete; Task 16.2 aspiration windows is next",
    "**Current phase:** Tasks 16.1 and 16.3 complete; Task 16.2 aspiration windows is next",
)
replace_once(
    ralph,
    "| 16.1 | `886ad953952b3a409800fcf7e8699365f94f0271` | `30772536115` / `91562076526` | full-window iterative deepening, five focused tests, 198 Rust tests, depth-four perft, and differential oracle green |",
    """| 16.1 | `886ad953952b3a409800fcf7e8699365f94f0271` | `30772536115` / `91562076526` | full-window iterative deepening, five focused tests, 198 Rust tests, depth-four perft, and differential oracle green |
| 16.3 | `e8afc9959a60519c6d5617963521e1707d37c6a9` | `30776274173` / `91572310565` | safe legal PV reconstruction, ponder support, 204 Rust tests, depth-four perft, and differential oracle green |""",
)
replace_once(
    ralph,
    "- Task 15 and Task 16.1 are complete. Task 16.2 aspiration windows is next.",
    "- Task 15 and Tasks 16.1/16.3 are complete. Task 16.2 aspiration windows is next.",
)
replace_once(
    ralph,
    "- Task 16.1 is complete. Task 16.2 aspiration windows is next.\n\n## Task 16 active scope",
    """- Task 16.1 and Task 16.3 are complete. Task 16.2 aspiration windows is next.

## Task 16.3 completion

Implemented and validated:

- bounded legal principal-variation reconstruction attached to every completed iterative-deepening iteration;
- exact root best-move anchoring and complete-key, exact-bound, sufficient-depth TT continuation;
- legal-token regeneration and validation before every returned move;
- explicit terminal, missing-entry, illegal-entry, root-without-move, requested-depth, and repeated-position termination;
- repeated-Zobrist cycle protection independent of the completed-depth hard bound;
- observational TT lookup that leaves diagnostics and table state unchanged;
- second-validated-move ponder extraction at both iteration and final-result boundaries;
- best-move retention in internal exact entries;
- focused unit/integration regressions and `docs/RUST_PRINCIPAL_VARIATION.md`.

Evidence:

- Exact clean validated implementation SHA: `e8afc9959a60519c6d5617963521e1707d37c6a9`.
- Permanent CI run/job: `30776274173` / `91572310565`.
- Results: permanent exclusion audit over 14 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 204 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Focused tests prove complete exact chains, legal sequential replay, ponder extraction, complete-key collision rejection, exact-bound/depth enforcement, illegal-move exclusion, repeated-position termination, terminal-root behavior, and diagnostic non-mutation.
- The initial compiler pass found only one test-only ambiguous integer literal; an explicit `u64` annotation resolved it without production semantic changes.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16.3 is complete. Task 16.2 aspiration windows remains open and is next.

## Task 16 active scope""",
)
replace_once(
    ralph,
    """- [x] Implement Task 16.1 iterative deepening.
- [ ] Implement Task 16.2 aspiration windows.
- [ ] Implement Task 16.3 principal variation.
- [ ] Implement Task 16.4 search limits.
""",
    """- [x] Implement Task 16.1 iterative deepening.
- [ ] Implement Task 16.2 aspiration windows.
- [x] Implement Task 16.3 principal variation.
- [ ] Implement Task 16.4 search limits.
""",
)

print("Task 16.3 tracker closure applied")
