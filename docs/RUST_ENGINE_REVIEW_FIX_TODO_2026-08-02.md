# Rust Engine Review Fix TODO — 2026-08-02

**Status:** Not started  
**Branch:** `rust-engine`  
**Spec:** `docs/RUST_ENGINE_REVIEW_FIX_SPEC_2026-08-02.md`  
**Primary tracker:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Purpose:** Fix review findings before Task 13 search implementation.

---

## Status rules

- `[x]` means implemented, documented, tested, and validated on the exact recorded SHA.
- `[ ]` means incomplete, unverified, deferred, blocked, or not started.
- Do not mark this review-fix pass complete until the final validation gate passes.
- Do not mark Task 13 started or complete as part of this pass.
- Every first-party rustfmt, compiler, Clippy, test, rustdoc, build, perft, or differential finding is a source bug.
- No first-party lint suppression, ignored exit status, or downgraded gate is accepted.

---

## Program guardrails

- [ ] Work only on `rust-engine` unless the user explicitly requests a separate branch.
- [ ] Do not implement Task 13 search in this pass.
- [ ] Do not weaken `chess-core` or `chess-search` dependency boundaries.
- [ ] Do not add unsafe code to `chess-core` or `chess-search`.
- [ ] Do not add clone-per-child as a production search fallback.
- [ ] Do not add automatic config, weight, or book loading.
- [ ] Preserve the existing public safe `Position::make_move(Move)` path.
- [ ] Preserve exact make/unmake restoration.
- [ ] Preserve existing perft and differential corpus behavior except where a deliberate FEN policy change requires fixture updates.

---

# RF-000: Baseline confirmation

## RF-000.1 Verify current review context

- [ ] Confirm `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md` still marks Tasks 0–12 complete and Task 13 active/not started.
- [ ] Confirm `crates/chess-search/src/lib.rs` still has no Task 13 search module.
- [ ] Confirm `crates/chess-core/src/position/make_unmake.rs` still keeps the generated-legal make path unavailable to `chess-search`.
- [ ] Confirm `chess-tools divide` still lacks elapsed output before editing.
- [ ] Confirm `Game` still lacks explicit reset/set-position APIs before editing.
- [ ] Record the starting SHA for this review-fix pass.

## RF-000.2 Failure preservation

- [ ] If any reviewed issue is already fixed by a newer commit, record the commit and do not duplicate the fix.
- [ ] If any reviewed issue is invalid after fresh inspection, document why in the completion notes.
- [ ] Convert every still-valid issue into tests or documented policy.

---

# RF-001: Search-safe generated legal move API

## RF-001.1 API design

- [ ] Add an externally usable legal-move token type or equivalent safe API.
- [ ] Keep token fields private.
- [ ] Ensure external crates cannot construct a fake token manually.
- [ ] Bind each token to the exact packed `Move` identity.
- [ ] Bind each token to enough source-position identity to reject stale/wrong-position use before mutation.
- [ ] Expose read-only token inspection, at least `move_made()` or equivalent.
- [ ] Preserve the existing raw `Move` public API for callers that need full revalidation.
- [ ] Keep the raw generated-legal primitive crate-private or otherwise inaccessible as an unsafe bypass.

## RF-001.2 Token generation

- [ ] Add a legal-token generator on `Position`.
- [ ] Reuse the current legal move generator's legality filtering.
- [ ] Preserve deterministic move order.
- [ ] Preserve fixed-capacity or stack-friendly storage.
- [ ] Avoid heap-heavy token generation.
- [ ] Ensure token generation restores the position exactly before returning.
- [ ] Ensure token generation returns the same move identities as `legal_moves()` for representative positions.

## RF-001.3 Token application

- [ ] Add a public method to apply one token without regenerating legal moves.
- [ ] Reject stale tokens before any mutation.
- [ ] Reject tokens from another position before any mutation.
- [ ] Reject tokens whose move identity no longer matches current board state before any mutation.
- [ ] Return `PositionUndo` on success.
- [ ] Reuse the existing reversible make/unmake implementation internally.
- [ ] Preserve Zobrist incremental update and exact unmake restoration.
- [ ] Add debug/test assertions comparing incremental and recomputed Zobrist after token make/unmake.

## RF-001.4 Cross-crate search usability

- [ ] Add at least one `chess-search` test or helper that uses the public token API from outside `chess-core`.
- [ ] Prove `chess-search` can generate legal tokens, apply one, evaluate/search a child placeholder, and unmake.
- [ ] Do not expose `chess-core` crate-private internals to `chess-search`.
- [ ] Do not introduce a dependency from `chess-core` to `chess-search`.

## RF-001.5 Tests

- [ ] Starting position legal tokens match the legal move set.
- [ ] Kiwipete or another castling-heavy fixture legal tokens match the legal move set.
- [ ] Promotion fixture tokens preserve all underpromotion identities.
- [ ] En-passant fixture token applies and unmakes exactly.
- [ ] Stale token after a different move fails before mutation.
- [ ] Token from a different FEN fails before mutation.
- [ ] Wrong-side or mismatched-origin token fails before mutation.
- [ ] Every token in a curated corpus passes make, invariant validation, unmake, exact equality, and hash restoration.
- [ ] The public safe `make_move(Move)` behavior remains unchanged.

## RF-001 gate

- [ ] `chess-search` has an efficient generated-legal make/unmake path available without legal-list regeneration.
- [ ] Fake/stale/wrong-position bypass attempts are covered by tests and fail non-mutatingly.
- [ ] No search implementation is added beyond minimal API usability tests.

---

# RF-002: Explicit `Game` reset and set-position APIs

## RF-002.1 API implementation

- [ ] Add explicit `Game` reset-to-starting API.
- [ ] Add explicit `Game` set-position API.
- [ ] Choose final method names and document them in rustdoc.
- [ ] Reset/set-position must clear played moves.
- [ ] Reset/set-position must reset position-hash history to exactly one root hash.
- [ ] Reset/set-position must not preserve previous repetition history.
- [ ] Reset/set-position must not preserve old undo tokens as valid history operations.

## RF-002.2 Semantics and errors

- [ ] Decide whether APIs are infallible because `Position` is already validated.
- [ ] If any API is fallible, define structured errors and non-mutating failure behavior.
- [ ] Ensure status after reset/set-position is computed from the new root.
- [ ] Ensure search history after reset/set-position starts from the new root only.

## RF-002.3 Tests

- [ ] Make moves, call reset, and assert equality with `Game::starting()`.
- [ ] Make moves, call set-position, and assert `ply_count() == 0`.
- [ ] Make moves, call set-position, and assert `moves().is_empty()`.
- [ ] Make moves, call set-position, and assert `position_hashes().len() == 1`.
- [ ] Assert the sole hash after set-position equals the new position's Zobrist key.
- [ ] Assert `status()` after set-position reflects the new position.
- [ ] Assert `search_history()` after set-position has the new root length and current hash.
- [ ] Assert stale `GameUndo` from before reset/set-position cannot be used successfully.

## RF-002.4 Documentation

- [ ] Update the game/history documentation with reset/set-position semantics.
- [ ] Update Task 10 completion notes if they mention Game API coverage.

## RF-002 gate

- [ ] The literal Task 10.1 reset/set-position requirement is implemented and tested, or the live TODO explicitly documents a deliberate alternative with rationale.

---

# RF-003: Stable elapsed-time output for `chess-tools divide`

## RF-003.1 Library/tooling design

- [ ] Decide whether elapsed timing belongs only in CLI output or also in a library return type.
- [ ] Preserve existing `divide(fen, depth) -> Vec<(String, u64)>` behavior unless a library type change is clearly justified.
- [ ] Use a stable machine-readable timing field.
- [ ] Prefer `elapsed_nanos\t<N>` as the final output line.

## RF-003.2 CLI implementation

- [ ] Start timing before the divide operation.
- [ ] Stop timing after root rows and total are computed, or document the exact measured region.
- [ ] Print every existing move row unchanged.
- [ ] Print `total\t<N>` unchanged.
- [ ] Print elapsed time after total.
- [ ] Ensure depth-zero behavior remains documented and stable.
- [ ] Ensure errors still exit nonzero and do not print partial success summaries.

## RF-003.3 Tests

- [ ] Update CLI/unit tests that parse divide output.
- [ ] Assert move rows remain sorted.
- [ ] Assert total remains correct.
- [ ] Assert elapsed line exists.
- [ ] Assert elapsed value parses as an unsigned integer.
- [ ] Avoid exact elapsed-value assertions.

## RF-003.4 Documentation

- [ ] Update perft/differential validation docs or tooling docs to show the new divide output format.
- [ ] Update Task 11.3 evidence if applicable.

## RF-003 gate

- [ ] `chess-tools divide` satisfies the detailed Task 11 requirement: canonical root moves, child counts, total, and elapsed time.

---

# RF-004: FEN analysis-position policy

## RF-004.1 Policy decision

- [ ] Decide and document whether `Position::from_fen` is a strict reachable-game parser or a strict syntax/structural analysis-position parser.
- [ ] If keeping analysis-position tolerance, document that the parser does not prove reachability from the standard starting position.
- [ ] If tightening validation, add precise structured errors for newly rejected states.
- [ ] Preserve fail-loud malformed-input behavior.

## RF-004.2 Required policy cases

Lock in parser behavior for each case:

- [ ] Castling rights present while matching home rook is absent.
- [ ] Castling rights present while matching home king is absent or king is elsewhere.
- [ ] Non-capturable en-passant target with correct FEN target rank.
- [ ] Adjacent kings.
- [ ] Both kings in check.
- [ ] Side to move in check.
- [ ] Side not to move in check.
- [ ] Position unreachable from initial chess but structurally usable for analysis.

## RF-004.3 Tests for accepted cases

For every intentionally accepted case:

- [ ] Assert `Position::from_fen` succeeds.
- [ ] Assert `validate_invariants()` succeeds.
- [ ] Assert `to_fen()` behavior is documented and stable.
- [ ] Assert `zobrist() == recomputed_zobrist()`.
- [ ] Assert `legal_moves()` does not panic.
- [ ] Assert `perft(0)` returns one leaf.

## RF-004.4 Tests for rejected cases

For every intentionally rejected case:

- [ ] Assert `Position::from_fen` fails.
- [ ] Assert the exact structured error category.
- [ ] Assert no panic occurs.
- [ ] Assert no partially mutated existing position is possible.

## RF-004.5 Documentation

- [ ] Add a "FEN validation policy" section to the FEN/notation documentation.
- [ ] Define syntax validation.
- [ ] Define structural validation.
- [ ] Define analysis-state tolerance.
- [ ] List accepted illegal/reachability-impossible analysis states, if any.
- [ ] List rejected states.
- [ ] Explain implications for legal move generation, Zobrist canonicalization, and differential corpus entries.

## RF-004 gate

- [ ] FEN parser policy is explicit, tested, and no longer ambiguous under the phrase "strict playable FEN."

---

# RF-005: Live TODO and Task 25 cleanup

## RF-005.1 Fix stale immediate next operations

- [ ] Open `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`.
- [ ] Remove the stale Task 9 Zobrist "Immediate next operations" footer.
- [ ] Replace it with Task 13 preparation/next operations.
- [ ] Include this review-fix TODO as the prerequisite operation before Task 13 search.
- [ ] Do not mark Task 13 subtasks complete.

Suggested new next operations:

1. Complete `docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md`.
2. Add search-safe generated-legal make/unmake API.
3. Validate reset/set-position, divide timing, FEN policy, and tracker cleanup.
4. Begin Task 13 reference search only after the review-fix gate passes.
5. Implement no-prune reference search before alpha-beta.
6. Validate search immutability before Task 13 completion.

## RF-005.2 Task 25 CI checklist cleanup

- [ ] Preserve Task 25 as `PARTIAL`.
- [ ] Mark release depth-four perft CI present if still verified.
- [ ] Mark scheduled/manual depth-five slow perft present if still verified.
- [ ] Keep AArch64 incomplete unless a current workflow proves it.
- [ ] Keep Android compile incomplete unless a current workflow proves it.
- [ ] Keep JNI incomplete unless a current workflow proves it.
- [ ] Keep Miri incomplete unless a current workflow proves it.
- [ ] Keep sanitizer incomplete unless a current workflow proves it.
- [ ] Keep fuzz incomplete unless a current workflow proves it.
- [ ] Keep scheduled strength incomplete unless a current workflow proves it.

## RF-005.3 Task 25 documentation checklist cleanup

- [ ] Mark Zobrist/hash documentation present if verified.
- [ ] Mark game/draw documentation present if verified.
- [ ] Mark differential perft documentation present if verified.
- [ ] Mark baseline evaluation documentation present if verified.
- [ ] Keep search documentation incomplete until Task 13 docs exist.
- [ ] Keep TT documentation incomplete until Task 15 docs exist.
- [ ] Keep ABI/JNI documentation incomplete until Task 18 docs exist.
- [ ] Keep fuzz documentation incomplete until Task 23 docs exist.
- [ ] Keep self-play/tuning documentation incomplete until Tasks 20–21 docs exist.

## RF-005.4 Task 25 command/artifact checklist cleanup

- [ ] Mark perft CLI present if verified.
- [ ] Mark divide CLI present if verified after elapsed output fix.
- [ ] Mark legal/play/suite/oracle tooling present if verified.
- [ ] Mark eval/eval-bench/weights export/weights validate tooling present if verified.
- [ ] Keep UCI command incomplete until Task 17.
- [ ] Keep Android command incomplete until Task 18 or later.
- [ ] Keep self-play command incomplete until Task 20.
- [ ] Keep tuning command incomplete until Task 21.
- [ ] Keep global versioned artifact policy incomplete unless separately documented.
- [ ] Keep Task 25 gate incomplete.

## RF-005.5 Ralph status update

- [ ] Update `docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md` to mention this review-fix pass.
- [ ] State that Task 13 remains active/not started until this pass closes.
- [ ] Record exact files changed and validation evidence after completion.

## RF-005 gate

- [ ] Live trackers are internally consistent and no stale Task 9 next-operation instruction remains.

---

# RF-006: Review-fix validation and closure evidence

## RF-006.1 Local exact validation commands

Run on the final candidate SHA:

- [ ] `cargo fmt --all -- --check`
- [ ] `cargo check --locked --workspace --all-targets --all-features`
- [ ] `cargo clippy --locked --workspace --all-targets --all-features -- -D warnings`
- [ ] `cargo test --locked --workspace --all-features`
- [ ] `RUSTDOCFLAGS="-D warnings" cargo doc --locked --workspace --all-features --no-deps`
- [ ] `cargo build --locked --workspace --all-features`
- [ ] `cargo build --locked --workspace --all-features --release`
- [ ] `cargo test --locked -p chess-core --release authoritative_perft_depth_four -- --ignored --exact`
- [ ] `python scripts/differential_oracle.py --binary target/release/chess-tools --corpus fixtures/differential_corpus.tsv --games 12 --plies 48 --seed 0xC0FFEE`

## RF-006.2 CI validation

- [ ] Dispatch or push to run the permanent CI workflow on the final candidate SHA.
- [ ] Confirm rustfmt passed.
- [ ] Confirm Cargo check passed.
- [ ] Confirm Clippy `-D warnings` passed.
- [ ] Confirm all Rust tests passed and record the test count.
- [ ] Confirm release depth-four perft passed.
- [ ] Confirm rustdoc `-D warnings` passed.
- [ ] Confirm debug build passed.
- [ ] Confirm release build passed.
- [ ] Confirm differential corpus and seeded playouts passed.
- [ ] Record CI run ID and job ID.

## RF-006.3 Documentation evidence

- [ ] Update this TODO status from `Not started` to `Complete` only after validation passes.
- [ ] Record final SHA.
- [ ] Record CI run/job.
- [ ] Record test count.
- [ ] Record release perft result.
- [ ] Record differential oracle summary.
- [ ] Record accepted external notices, if any.
- [ ] Update the primary live TODO with review-fix completion evidence.
- [ ] Update Ralph status with review-fix completion evidence.

## RF-006.4 Cleanup

- [ ] Remove any one-shot workflow created for this pass unless it is intentionally retained and documented.
- [ ] Remove temporary diagnostic scripts not intended for permanent use.
- [ ] Ensure no temporary branch or issue remains open unless intentionally retained.
- [ ] Confirm no generated target/build artifacts are committed.
- [ ] Confirm no first-party lint suppression was added.

## RF-006 gate

- [ ] The review-fix pass has exact-SHA evidence, clean docs, and no unresolved validation failure.

---

# Final completion checklist

- [ ] RF-000 baseline confirmation complete.
- [ ] RF-001 search-safe generated legal move API complete.
- [ ] RF-002 explicit `Game` reset/set-position APIs complete.
- [ ] RF-003 divide elapsed-time output complete.
- [ ] RF-004 FEN policy documentation/tests complete.
- [ ] RF-005 live TODO and Task 25 cleanup complete.
- [ ] RF-006 validation and closure evidence complete.
- [ ] Task 13 remains active/not started.
- [ ] No Tasks 14–27 are marked complete by this pass.

---

# Completion evidence

To be filled in after implementation:

- Final SHA: `TBD`
- CI run/job: `TBD`
- Rust test count: `TBD`
- Release perft: `TBD`
- Differential oracle summary: `TBD`
- Accepted external notices: `TBD`
- Temporary artifacts removed: `TBD`
