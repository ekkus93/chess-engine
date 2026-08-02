# Rust Engine Review Fix TODO — 2026-08-02

**Status:** Complete  
**Branch:** `rust-engine`  
**Spec:** `docs/RUST_ENGINE_REVIEW_FIX_SPEC_2026-08-02.md`  
**Primary tracker:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Validated implementation SHA:** `81a7cd4a58a52695eca2ede10d5c73c803851d17`

---

## Status rules

- `[x]` means implemented, documented, tested, and supported by recorded evidence.
- `[ ]` remains incomplete and outside this review-fix pass.
- This pass does not implement Task 13 search.
- Every first-party formatting, compiler, Clippy, test, rustdoc, build, perft, or differential failure was treated as a source defect.
- No first-party lint suppression or weakened validation gate was accepted.

---

# RF-000: Baseline confirmation — COMPLETE

## RF-000.1 Review context

- [x] Confirmed Tasks 0–12 were marked complete before this pass.
- [x] Confirmed Task 13 was active and not started.
- [x] Confirmed `chess-search` contained evaluation/score/weights but no Task 13 search implementation.
- [x] Confirmed the efficient generated-legal make path was inaccessible to the separate `chess-search` crate.
- [x] Confirmed `Game` lacked explicit reset/set-position APIs.
- [x] Confirmed `chess-tools divide` lacked elapsed output.
- [x] Confirmed the live TODO footer still contained stale Task 9 operations.
- [x] Confirmed Task 25 understated existing CI, documentation, and commands.
- [x] Confirmed the FEN analysis-position policy required explicit documentation/tests.
- [x] Recorded the starting code/documentation SHA: `52377d09b713541044e24c8e3559be3f12002cc1`.

## RF-000.2 Failure preservation

- [x] Reinspected each review finding before implementation.
- [x] Preserved valid findings as tests or documented contracts.
- [x] Did not duplicate any finding already fixed by newer source.
- [x] Kept Task 13 itself outside the pass.

---

# RF-001: Search-safe generated legal move API — COMPLETE

## RF-001.1 Public API

- [x] Added opaque `LegalMoveToken` with private fields.
- [x] Added bounded `LegalMoveTokenList`.
- [x] Added read-only `LegalMoveToken::move_made()`.
- [x] Added `Position::legal_move_tokens()`.
- [x] Added `Position::make_legal_token()`.
- [x] Preserved public checked `Position::make_move(Move)`.
- [x] Kept the raw generated-legal primitive crate-private.
- [x] Did not add a dependency from `chess-core` to `chess-search`.

## RF-001.2 Origin identity

Each token is bound to:

- [x] exact packed `Move` identity;
- [x] canonical source Zobrist key;
- [x] source side to move;
- [x] source castling rights;
- [x] source raw en-passant target;
- [x] source halfmove clock;
- [x] source fullmove number.

## RF-001.3 Generation and application

- [x] Token generation reuses legal move generation.
- [x] Token order matches deterministic legal move order.
- [x] Token storage is fixed-capacity and stack-backed.
- [x] Token generation restores the source position exactly.
- [x] Valid token application does not regenerate legal moves.
- [x] Valid token application reuses the existing reversible primitive.
- [x] Valid token application returns `PositionUndo`.
- [x] Stale/wrong-origin tokens return `LegalMoveTokenMismatch` before mutation.
- [x] Generated move/state consistency remains checked by the reversible primitive.
- [x] Zobrist incremental state remains checked against recomputation in debug/tests.

## RF-001.4 Cross-crate usability

- [x] Added a `chess-search` test using the public token API.
- [x] The test generates a legal token, applies it, evaluates the child, unmakes it, and proves exact root restoration.
- [x] `chess-search` does not depend on crate-private `chess-core` internals.
- [x] No search algorithm beyond the API usability test was added.

## RF-001.5 Regression coverage

- [x] Starting-position token identities match legal move identities.
- [x] Castling-heavy token identities match legal move identities.
- [x] Promotion and underpromotion identities are preserved.
- [x] En-passant token make/unmake restores exactly.
- [x] Stale token after another move fails before mutation.
- [x] Token from another position fails before mutation.
- [x] Wrong-side/mismatched-origin token fails before mutation.
- [x] Curated all-token make/invariant/unmake/equality/hash coverage passes.
- [x] Existing raw `make_move(Move)` behavior remains intact.

## RF-001 gate

- [x] `chess-search` has a safe efficient generated-legal make/unmake boundary without legal-list regeneration.

---

# RF-002: Explicit `Game` reset and set-position APIs — COMPLETE

## RF-002.1 API

- [x] Added `Game::reset_to_starting()`.
- [x] Added `Game::set_position(Position)`.
- [x] Documented both methods in rustdoc.
- [x] Kept both methods infallible because `Position` is already validated.

## RF-002.2 State semantics

Both methods:

- [x] replace the current position;
- [x] clear played moves;
- [x] reset position-hash history to exactly one root hash;
- [x] discard old repetition history;
- [x] prevent old game undo context from remaining valid;
- [x] cause status and search-history operations to use only the new root.

## RF-002.3 Tests

- [x] Reset after moves equals `Game::starting()`.
- [x] Set-position resets `ply_count()` to zero.
- [x] Set-position clears `moves()`.
- [x] Set-position leaves exactly one position hash.
- [x] The sole hash equals the new root Zobrist key.
- [x] Status reflects the new root.
- [x] Search history starts at the new root.
- [x] Stale `GameUndo` from before root replacement is rejected.

## RF-002.4 Documentation

- [x] Updated game/history documentation with root replacement semantics.
- [x] Satisfied the literal Task 10.1 reset/set-position requirement.

## RF-002 gate

- [x] Explicit game root replacement is implemented, documented, and tested.

---

# RF-003: Stable elapsed-time output for divide — COMPLETE

## RF-003.1 Output contract

`chess-tools divide` now emits:

```text
<uci>\t<nodes>
...
total\t<nodes>
elapsed_nanos\t<nanos>
```

- [x] Existing sorted move rows are unchanged.
- [x] Existing `total\t<N>` output is unchanged.
- [x] `elapsed_nanos\t<N>` is appended after total.
- [x] Timing covers divide calculation and total accumulation before output.
- [x] Library `divide(fen, depth)` behavior remains unchanged.
- [x] Errors remain nonzero/fail-loud.

## RF-003.2 Tests

- [x] Move rows remain sorted.
- [x] Total remains exact.
- [x] Elapsed line exists.
- [x] Elapsed value parses as `u128`.
- [x] Nontrivial work reports a positive duration.
- [x] Depth-zero output remains a stable two-line summary.

## RF-003.3 Documentation

- [x] Updated perft/differential documentation with the timing field.
- [x] Satisfied the detailed Task 11.3 elapsed-time requirement.

## RF-003 gate

- [x] Divide provides canonical rows, total, and stable elapsed timing.

---

# RF-004: FEN analysis-position policy — COMPLETE

## RF-004.1 Chosen policy

- [x] `Position::from_fen` is documented as a strict syntax and structural analysis-position parser.
- [x] It does not attempt to prove reachability from the standard starting position.
- [x] Malformed input remains fail-loud and panic-free.

## RF-004.2 Rejected states

The parser continues to reject:

- [x] malformed field count or placement;
- [x] invalid piece, active-color, castling, en-passant, or counter syntax;
- [x] pawns on rank one or rank eight;
- [x] invalid en-passant target rank;
- [x] occupied en-passant target;
- [x] missing king;
- [x] multiple kings;
- [x] redundant-state invariant failures.

## RF-004.3 Intentionally accepted analysis states

Policy tests cover acceptance of:

- [x] castling rights without the matching home rook;
- [x] castling rights without the matching home king position;
- [x] correctly ranked but non-capturable en-passant target;
- [x] adjacent kings;
- [x] both kings in check;
- [x] side to move already in check;
- [x] side not to move already in check;
- [x] unusual/unreachable analysis material.

## RF-004.4 Downstream safety tests

For accepted analysis states:

- [x] FEN parsing succeeds.
- [x] Structural invariants pass.
- [x] Canonical FEN output is stable.
- [x] Stored and recomputed Zobrist keys agree.
- [x] Legal move generation does not panic.
- [x] `perft(0)` returns one.
- [x] Parse/serialize/parse equality holds.

## RF-004.5 Rule consequences

- [x] Legal generation never permits king capture.
- [x] Castling remains unavailable without required pieces/path/safety.
- [x] Non-capturable en-passant targets are excluded from repetition identity.
- [x] Differential corpus positions remain constrained by the pinned oracle.

## RF-004.6 Documentation

- [x] Added a “FEN validation policy” section to the FEN/UCI documentation.
- [x] Documented syntax validation, structural validation, analysis tolerance, accepted states, rejected states, and downstream implications.

## RF-004 gate

- [x] FEN parser semantics are explicit and regression-locked.

---

# RF-005: Live TODO and Task 25 cleanup — COMPLETE

## RF-005.1 Immediate operations

- [x] Removed the stale Task 9 Zobrist next-operation footer.
- [x] Added the review-fix pass as the prerequisite to Task 13.
- [x] Added reference-search-first Task 13 sequencing.
- [x] Added search immutability as a Task 13 completion requirement.
- [x] Kept all Task 13 subtasks unchecked/not started.

## RF-005.2 Task 25 CI truth

- [x] Preserved Task 25 as partial.
- [x] Recorded Linux strict CI.
- [x] Recorded release depth-four perft CI.
- [x] Recorded scheduled/manual depth-five perft.
- [x] Kept AArch64 incomplete.
- [x] Kept Android/JNI CI incomplete.
- [x] Kept Miri, sanitizer, and fuzz gates incomplete.
- [x] Kept scheduled strength testing incomplete.

## RF-005.3 Task 25 documentation truth

- [x] Recorded Zobrist/repetition documentation.
- [x] Recorded game/draw documentation.
- [x] Recorded perft/differential documentation.
- [x] Recorded baseline evaluation documentation.
- [x] Kept search/TT documentation incomplete.
- [x] Kept ABI/JNI documentation incomplete.
- [x] Kept fuzzing documentation incomplete.
- [x] Kept self-play/tuning documentation incomplete.

## RF-005.4 Task 25 command truth

- [x] Recorded legal/play/perft/divide/suite/oracle tooling.
- [x] Recorded eval/eval-bench/weight export/weight validation tooling.
- [x] Kept UCI commands incomplete.
- [x] Kept Android commands incomplete.
- [x] Kept self-play and tuning commands incomplete.
- [x] Kept the global generated-artifact policy incomplete.
- [x] Kept the Task 25 gate incomplete.

## RF-005.5 Ralph status

- [x] Recorded the pre-Task-13 review-fix implementation scope.
- [x] Kept Task 13 active and not started.
- [x] Recorded source files, tests, and CI evidence in the final review documents.

## RF-005 gate

- [x] Live planning no longer directs work back to completed Task 9.

---

# RF-006: Validation and closure evidence — COMPLETE

## RF-006.1 Strict validation

The validated implementation candidate passed:

- [x] `cargo fmt --all -- --check`
- [x] `cargo check --locked --workspace --all-targets --all-features`
- [x] `cargo clippy --locked --workspace --all-targets --all-features -- -D warnings`
- [x] `cargo test --locked --workspace --all-features`
- [x] `RUSTDOCFLAGS="-D warnings" cargo doc --locked --workspace --all-features --no-deps`
- [x] `cargo build --locked --workspace --all-features`
- [x] `cargo build --locked --workspace --all-features --release`
- [x] authoritative release depth-four perft
- [x] pinned differential corpus and seeded playout validation

## RF-006.2 CI evidence

- [x] Validated implementation SHA: `81a7cd4a58a52695eca2ede10d5c73c803851d17`
- [x] One-shot implementation control run: `30738801841`
- [x] Permanent CI run: `30739166607`
- [x] Permanent CI job: `91473334960`
- [x] Executed non-doc Rust tests: `112`
- [x] Release depth-four perft: passed for the authoritative six-position suite
- [x] Rustdoc warnings denied: passed
- [x] Debug build: passed
- [x] Release build: passed
- [x] First-party warnings: none

## RF-006.3 Differential evidence

- [x] Corpus positions: `15`
- [x] Child FENs: `293`
- [x] Oracle perft nodes: `272,991`
- [x] Seeded plies: `576`
- [x] Seed: `0xC0FFEE`

## RF-006.4 External notices

- [x] Accepted only GitHub Actions Node runtime deprecation notices.
- [x] Accepted only dependency `punycode` deprecation notices.
- [x] No first-party warning was accepted.

## RF-006.5 Cleanup

- [x] Removed all one-shot implementation workflows.
- [x] Removed all temporary closure workflows/scripts.
- [x] Retained no temporary branch.
- [x] Retained no generated target/build artifact.
- [x] Added no first-party lint suppression.
- [x] Closed or superseded temporary control issues.
- [x] Restored the permanent CI workflow byte-for-byte.

## RF-006.6 Clean-tree proof

- [x] Clean branch SHA after control cleanup: `9c27d2c1c4a39a975b30d3357b69b6c96bb64c68`
- [x] GitHub commit comparison between the validated candidate and that clean SHA reported zero changed files.
- [x] Therefore the final clean code/workflow tree was byte-for-byte equivalent to the exact candidate that passed permanent CI.

## RF-006 gate

- [x] The review-fix pass has exact implementation evidence, a clean repository tree, complete review documents, and no unresolved source validation failure.

---

# Final completion checklist

- [x] RF-000 baseline confirmation complete.
- [x] RF-001 search-safe generated legal move API complete.
- [x] RF-002 explicit `Game` reset/set-position APIs complete.
- [x] RF-003 divide elapsed-time output complete.
- [x] RF-004 FEN policy documentation/tests complete.
- [x] RF-005 live TODO and Task 25 cleanup complete.
- [x] RF-006 validation and closure evidence complete.
- [x] Task 13 remains active/not started.
- [x] No Tasks 14–27 were marked complete by this pass.

---

# Completion evidence

- Validated implementation SHA: `81a7cd4a58a52695eca2ede10d5c73c803851d17`
- One-shot implementation control run: `30738801841`
- Permanent CI run/job: `30739166607` / `91473334960`
- Rust test count: `112` executed non-doc tests
- Release perft: authoritative six-position depth-four gate passed
- Differential oracle: 15 positions, 293 child FENs, 272,991 nodes, 576 seeded plies, seed `0xC0FFEE`
- Accepted external notices: GitHub Actions Node runtime and dependency `punycode` deprecations only
- Clean-tree equivalence SHA: `9c27d2c1c4a39a975b30d3357b69b6c96bb64c68`
- Temporary artifacts removed: all review-fix control workflows/scripts; no temporary branch or build artifact remains
