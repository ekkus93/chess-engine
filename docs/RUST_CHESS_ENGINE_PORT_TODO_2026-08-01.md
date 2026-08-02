# Rust Chess Engine Port TODO — Live Status Tracker

**Status:** In progress  
**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Specification:** `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md`  
**Detailed definitions:** `docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md`

## Status rules

- `[x]` is complete with repository or CI evidence.
- `[ ]` is incomplete, unverified, deferred, blocked, or not started.
- GitHub Actions is the authoritative Rust execution environment.
- Every first-party formatting, compiler, Clippy, test, or rustdoc finding is a bug and must be fixed at source.
- Update this file whenever any task or subtask status changes.

## Program summary

| Task | Status |
|---:|---|
| 0 | **Complete** — frozen Python baseline captured and reviewed. |
| 1 | **Complete** — workspace and strict CI validated. |
| 2 | **Complete** — core value types and exact-SHA CI complete. |
| 3 | **Complete** — hybrid `Position`, invariants, tests, documentation, and exact-SHA CI complete. |
| 4 | **Complete** — strict FEN and UCI notation, robustness tests, documentation, and exact-SHA CI complete. |
| 5 | **Implemented, CI pending** — attack primitives, position queries, independent tests, and documentation are present. |
| 6–24 | **Not started**. |
| 25 | **Partial** — Linux strict CI and initial docs/workflows exist. |
| 26–27 | **Not started**. |

## Tasks 0–2 — complete

- [x] Task 0 gate. Evidence: SHA `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`, run `30722127447`, Python job `91427510964`, artifact `8825590703`; fast `1203 passed`, slow `179 passed`; perft `20/400/8902/197281`; UCI passed.
- [x] Task 1 gate. Evidence: SHA `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`, run `30722127447`, Rust job `91427510938`; metadata/fmt/check/Clippy/tests/rustdoc/debug/release passed.
- [x] Task 2 gate. Implementation `878f9090af3d5fdee77ca87aaea24761a8df0312`; formatting fix `f29524599134a14d34121af2fefb04cd90e78df0`; run `30723748100`, job `91431648799`; 16 tests passed; exact closure SHA `b5f462aa73a69efcdc847ee215231a5064029902`, run `30723952076`, job `91432161445` passed.

# Task 3: `Position` and invariants — COMPLETE

## 3.1 Hybrid representation
- [x] Private 64-square mailbox.
- [x] Piece bitboards by color and kind.
- [x] Color occupancy and combined occupancy.
- [x] Cached king squares.
- [x] Side, castling rights, en-passant state, typed counters, and Zobrist placeholder/state.

## 3.2 Constructors
- [x] Crate-private empty builder for parser/tests.
- [x] Standard starting position.
- [x] Playable construction requires exactly one king per color.
- [x] No weakened analysis-position constructor added.

## 3.3 Accessors and mutation boundary
- [x] Read-only piece, bitboard, occupancy, king, and metadata accessors.
- [x] Direct placement remains private to the position module.
- [x] Atomic internal add/remove/move primitives update every redundant representation.
- [x] Adapters cannot obtain or construct the sealed editor capability.
- [x] Mailbox and bitboard fields remain private.

## 3.4 Invariant checker
- [x] Mailbox/bitboard agreement.
- [x] Occupancy agreement and no color overlap.
- [x] Combined occupancy agreement.
- [x] Exactly one king per color and correct king caches.
- [x] En-passant target rank and emptiness validation.
- [x] Zobrist recomputation explicitly deferred to Task 9.
- [x] Every state-transition test runs invariant validation.

## 3.5 Equality and clone
- [x] Complete logical equality for restoration tests.
- [x] Clone for snapshots/tests.
- [x] Explicit prohibition on clone-per-node production search.

## 3.6 Documentation and gate
- [x] Position representation/invariant documentation.
- [x] Starting-position, construction, metadata, mutation, failure atomicity, king relocation, equality, and invariant tests.
- [x] rustfmt exact-SHA pass.
- [x] Cargo check exact-SHA pass.
- [x] Clippy `-D warnings` exact-SHA pass.
- [x] Unit tests exact-SHA pass: `24 passed, 0 failed`.
- [x] rustdoc `-D warnings` exact-SHA pass.
- [x] Debug/release exact-SHA builds.
- [x] Task 3 gate.

### Task 3 completion evidence

- Initial implementation: `dd66b61b745d72f833802826b5d72f2b3f18232a`.
- rustfmt correction: `b36e7e379e35a32aac6c707099bd9c2daa7067cd`.
- Sealed editor capability fix: `bfef2ae3a08722a4215ba788273543c3ba244423`.
- Corrected sealed re-export and green candidate: `00fd925dad807d822aa7878aade686ccc59ff9c5`.
- CI run/job: `30724744784` / `91434236030`.
- Results: lockfile verification, metadata, rustfmt, Cargo check, Clippy with warnings denied, 24 unit tests, rustdoc with warnings denied, debug build, and release build passed.
- First-party warnings: none.
- Accepted external notices: GitHub Action Node runtime deprecation messages only.
- Deviations: Zobrist recomputation remains intentionally deferred to Task 9; no other deviations.

# Task 4: Strict FEN and UCI move notation — COMPLETE

## 4.1 Structured errors
- [x] Public `FenError` distinguishes field count, rank count/width, placement characters, promotion-rank pawns, active color, castling, en-passant, counters, and position construction failures.
- [x] Public `MoveParseError` distinguishes length, non-ASCII input, source/destination coordinates, and promotion suffix errors.
- [x] Both error types implement `Display` and `Error` without panic-based control flow.

## 4.2 Strict FEN parser
- [x] Exactly six fields required.
- [x] Exactly eight ranks and eight expanded files per rank required.
- [x] Piece characters and digits are validated fail-loud.
- [x] Pawns on rank one/eight are rejected.
- [x] Active color is strictly `w` or `b`.
- [x] Castling field is `-` or unique `KQkq` tokens.
- [x] En-passant coordinate and active-color rank consistency are validated.
- [x] Halfmove and fullmove counters use typed bounded values; fullmove zero is rejected.
- [x] Playable construction requires exactly one king per color.
- [x] Parsing uses the crate-private `PositionBuilder`; no adapter mutation surface was added.

## 4.3 Canonical FEN serializer
- [x] Piece placement is compressed canonically.
- [x] Castling rights serialize in `KQkq` order.
- [x] Active color, en-passant field, halfmove clock, and fullmove number serialize deterministically.
- [x] Parse/serialize/parse stability is tested on a curated corpus.

## 4.4 UCI move notation
- [x] Syntax-only `UciMove` parses four- and five-character coordinate moves.
- [x] Promotion suffixes are limited to lowercase `n`, `b`, `r`, and `q`.
- [x] Syntax values do not synthesize unchecked internal moves.
- [x] `UciMove::matches` compares against generated internal move identity without being incorrectly declared `const`.
- [x] Every internal `MoveKind` formats through the single packed `Move` representation.

## 4.5 Robustness, documentation, and gate
- [x] Malformed FEN categories have explicit regression tests.
- [x] Arbitrary deterministic Unicode input is verified not to panic for FEN and UCI parsers.
- [x] Starting-position and curated FEN round trips are tested.
- [x] Normal and all promotion UCI suffixes round trip.
- [x] FEN/UCI contract documentation exists at `docs/RUST_FEN_AND_UCI_NOTATION.md`.
- [x] Exact-head rustfmt pass.
- [x] Exact-head Cargo check pass.
- [x] Exact-head Clippy `-D warnings` pass.
- [x] Exact-head unit-test pass: `35 passed, 0 failed`.
- [x] Exact-head rustdoc `-D warnings` pass.
- [x] Exact-head debug/release builds.
- [x] Task 4 gate.

### Task 4 completion evidence

- Green implementation candidate: `87e6b81c65340a692af0d800012910399d3ac75b`.
- Exact status/evidence SHA: `6cb975b35f4dbe898a0444b1b4c39778e89bcb40`.
- CI run/job: `30726795562` / `91439860915`.
- Results: lockfile verification, metadata, rustfmt, Cargo check, Clippy with warnings denied, 35 unit tests, rustdoc with warnings denied, debug build, and release build passed.
- First-party warnings: none.
- Accepted external notices: GitHub Action Node runtime and `punycode` deprecation notices only.
- Deviations: none.

# Task 5: Attack-generation infrastructure — IMPLEMENTED, CI PENDING

## 5.1 Leaper attacks
- [x] Precompute pawn attacks for both colors and all squares.
- [x] Precompute knight attacks for all squares.
- [x] Precompute king attacks for all squares.
- [x] Add exhaustive edge/corner and all-square oracle tests.

## 5.2 Sliding attacks
- [x] Implement correct rook attacks for arbitrary occupancy.
- [x] Implement correct bishop attacks for arbitrary occupancy.
- [x] Implement queen attacks as combined sliding attacks.
- [x] Use clear audited ray scans; no premature magic/PEXT optimization.
- [x] Add blocker-before, blocker-on-target, edge, empty-board, full-board, and patterned-occupancy tests.

## 5.3 Geometric tables
- [x] Add precomputed 64-by-64 ray, line, and between-square tables.
- [x] Define identical and non-collinear endpoint behavior explicitly.
- [x] Test every one of the 4,096 square pairs against an independent oracle.

## 5.4 Position attack queries
- [x] Implement `Position::attackers_to`.
- [x] Implement `Position::is_square_attacked`.
- [x] Implement `Position::checkers_to_king`.
- [x] Implement absolute `Position::pinned_pieces` discovery.
- [x] Ensure pawn attack semantics do not depend on occupancy.

## 5.5 Differential attack fixtures
- [x] Compare all target/color attack maps for representative positions against an independent coordinate/path oracle.
- [x] Add double-check, single-pin, two-blocker non-pin, edge, and pawn-occupancy fixtures.

## 5.6 Documentation and gate
- [x] Document attack geometry, blocker inclusion, geometric helper semantics, and pin semantics in `docs/RUST_ATTACK_GENERATION.md`.
- [ ] Exact-head rustfmt pass.
- [ ] Exact-head Cargo check pass.
- [ ] Exact-head Clippy `-D warnings` pass.
- [ ] Exact-head unit-test pass with recorded count.
- [ ] Exact-head rustdoc `-D warnings` pass.
- [ ] Exact-head debug/release builds.
- [ ] Task 5 gate.

### Task 5 implementation evidence

- Attached source implementation: `af649ba40ecaa22c196f0bcbb726fe7a33fce48e`.
- Status synchronization: `694b4f737ed4050d0cb831e1758ff2db5369a71e`.
- Current status head includes the complete source tree and documentation.
- Exact CI evidence remains pending.

# Tasks 6–24 — not started

- [ ] Task 6: pseudo-legal generation — 6.1 pawns; 6.2 pieces; 6.3 castling candidates; 6.4 move list; 6.5 tests; gate.
- [ ] Task 7: legal generation/special rules — 7.1 king safety; 7.2 evasions; 7.3 castling; 7.4 en passant; 7.5 promotions; 7.6 initial perft; gate.
- [ ] Task 8: make/unmake — 8.1 undo; 8.2 application; 8.3 restoration; 8.4 sequences; gate.
- [ ] Task 9: Zobrist/repetition — 9.1 tables; 9.2 full hash; 9.3 incremental; 9.4 canonical en passant; 9.5 verification; gate.
- [ ] Task 10: game/history/draws — 10.1 game state; 10.2 mate/stalemate; 10.3 claims; 10.4 automatic; 10.5 dead position; 10.6 search history; gate.
- [ ] Task 11: perft/differential — 11.1 suite; 11.2 slow; 11.3 divide; 11.4 oracle; 11.5 corpus; gate.
- [ ] Task 12: evaluation — 12.1 score; 12.2 terms; 12.3 efficiency; 12.4 trace; 12.5 weights; 12.6 exclusions; gate.
- [ ] Task 13: reference search/alpha-beta — 13.1 reference; 13.2 negamax; 13.3 equivalence; 13.4 immutability; 13.5 terminals; gate.
- [ ] Task 14: quiescence/ordering — 14.1 quiescence; 14.2 tactical; 14.3 quiet; 14.4 tests; 14.5 exclusions; gate.
- [ ] Task 15: transposition table — 15.1 entries; 15.2 storage; 15.3 mate normalization; 15.4 probes; 15.5 replacement; 15.6 diagnostics; gate.
- [ ] Task 16: iterative deepening/limits — 16.1 ID; 16.2 aspirations; 16.3 PV; 16.4 limits; 16.5 cancellation; 16.6 result API; 16.7 extension; gate.
- [ ] Task 17: Linux UCI — 17.1 loop; 17.2 worker; 17.3 time; 17.4 output; 17.5 integration; gate.
- [ ] Task 18: safe API/C ABI/JNI — 18.1 facade; 18.2 C ABI; 18.3 C tests; 18.4 JNI; 18.5 Android harness; gate.
- [ ] Task 19: opening book — 19.1 abstraction; 19.2 format; 19.3 policies; 19.4 integration; 19.5 tests; gate.
- [ ] Task 20: self-play/datasets — 20.1 config; 20.2 records; 20.3 schema; 20.4 quality; gate.
- [ ] Task 21: tuning — 21.1 weights; 21.2 loss; 21.3 optimizer; 21.4 reports; 21.5 validation; gate.
- [ ] Task 22: advanced classical terms — 22.1 protocol; 22.2 candidates; 22.3 exclusions; gate.
- [ ] Task 23: robustness — 23.1 properties; 23.2 fuzz; 23.3 runtime analysis; 23.4 failure preservation; gate.
- [ ] Task 24: performance — 24.1 benchmarks; 24.2 profiling; 24.3 measured optimization; 24.4 regression policy; 24.5 Android; gate.

# Task 25: CI, documentation, and workflows — partial

## 25.1 CI
- [x] Linux strict formatting/check/Clippy/tests/rustdoc/debug/release gates.
- [x] Python validation preserved separately.
- [x] Exact-SHA status publisher and deterministic dispatcher.
- [ ] Release tests/perft, AArch64, Android, JNI, Miri, sanitizer, fuzz, nightly perft, and scheduled strength.

## 25.2 Documentation
- [x] Workspace architecture.
- [x] Core values/coordinates/move layout.
- [x] Position representation and invariants.
- [x] Strict FEN and UCI move notation.
- [x] Attack-generation contract.
- [ ] Make/unmake, draws, hashing, search, TT, evaluation, ABI/JNI, perft/fuzz, self-play, and tuning docs.

## 25.3 Commands and artifacts
- [x] Full Task 0/1 validation command; committed lockfile; targets/worktrees ignored.
- [ ] Bootstrap, fast validation, perft, UCI, Android, self-play, and tuning commands.
- [ ] Versioned schema/fixture/generated-artifact policy.
- [ ] Task 25 gate.

# Tasks 26–27 — not started

- [ ] Task 26: rules, search, adapter, quality, evidence, and v0.1 gate.
- [ ] Task 27: optional capabilities, migration decision, final report, and release gate.

## Immediate next operations

1. Run strict CI at the current exact `rust-engine` head.
2. Fix every Task 5 first-party formatting, compiler, Clippy, test, rustdoc, or build finding at source.
3. Record the exact green SHA, run ID, job ID, and test count.
4. Close Task 5 only after every gate checkbox is complete.
5. Begin Task 6 pseudo-legal move generation after Task 5 closure.
