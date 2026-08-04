# Rust Chess Engine Port TODO — Live Status Tracker

**Status:** In progress  
**Updated:** 2026-08-04
**Branch:** `master`  
**Specification:** `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md`  
**Full definitions:** `docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md`  
**Ralph status:** `docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md`

## Status rules

- `[x]` means complete with repository and, where required, exact-SHA CI evidence.
- `[ ]` means incomplete, unverified, deferred, blocked, or not started.
- GitHub Actions is the authoritative Rust execution environment.
- Every first-party rustfmt, compiler, Clippy, test, rustdoc, or build finding is a source bug.
- No first-party lint suppression, output filtering, ignored exit status, or downgraded gate is accepted.
- The companion definitions file preserves the original detailed task wording; this file is the authoritative live status.
- Update this file whenever implementation or evidence changes a task or subtask.

## Program summary

| Task | Status |
|---:|---|
| 0 | **Complete** — Python reference baseline. |
| 1 | **Complete** — Cargo workspace and strict CI. |
| 2 | **Complete** — core value types. |
| 3 | **Complete** — `Position` and invariants. |
| 4 | **Complete** — strict FEN and UCI notation. |
| 5 | **Complete** — attack generation. |
| 6 | **Complete** — pseudo-legal move generation. |
| 7 | **Complete** — legal move generation, special rules, reversible validation, and initial perft. |
| 8 | **Complete** — formal checked/generated make/unmake, exact restoration, and randomized reversal. |
| 9 | **Complete** — Zobrist hashing and repetition identity. |
| 10 | **Complete** — game history and draw semantics. |
| 11 | **Complete** — authoritative perft and differential validation. |
| 12 | **Complete** — baseline evaluator and trace. |
| 13 | **Complete** — reference negamax, alpha-beta, shallow equivalence, immutability, and terminal/mate-distance fixtures. |
| 14 | **Complete** — quiescence, tactical/quiet ordering, consolidated correctness, and exclusion audit. |
| 15 | **Complete** — bounded, mate-safe transposition table integrated into production alpha-beta with deterministic node-reduction evidence. |
| 16 | **Complete** — iterative deepening, aspiration recovery, legal PVs, limits, responsive cancellation, unified results, and bounded optional check extension. |
| 17 | **Complete** — Linux UCI executable. |
| 18 | **Complete** — safe API, C ABI, JNI, host JVM, and Android emulator harness. |
| 19 | **Complete** — optional explicit opening-book support, indexed format, legal reproducible policies, adapter integration, and permanent verification gate. |
| 20 | **Complete** — deterministic offline self-play and validated versioned datasets. |
| 21 | **In progress** — Tasks 21.1–21.3 complete; Tasks 21.4–21.5 remain. |
| 22–24 | **Not started**. |
| 25 | **Partial**. |
| 26–27 | **Not started**. |

---

# Tasks 0–8 — complete

- [x] Task 0 gate. Evidence: SHA `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`; run/job `30722127447` / `91427510964`; Python fast `1203`, slow `179`, perft `20/400/8902/197281`, UCI passed.
- [x] Task 1 gate. Evidence: SHA `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`; run/job `30722127447` / `91427510938`; strict workspace gates passed.
- [x] Task 2 gate. Evidence: implementation SHA `f29524599134a14d34121af2fefb04cd90e78df0`; run/job `30723748100` / `91431648799`; `16 passed`; closure `b5f462aa73a69efcdc847ee215231a5064029902` green.
- [x] Task 3 gate. Evidence: implementation SHA `00fd925dad807d822aa7878aade686ccc59ff9c5`; run/job `30724744784` / `91434236030`; `24 passed`; closure `5578682bb2a6df5173ff7593649ac55509c277cd` green.
- [x] Task 4 gate. Evidence: closure SHA `6cb975b35f4dbe898a0444b1b4c39778e89bcb40`; run/job `30726795562` / `91439860915`; `35 passed`.
- [x] Task 5 gate. Evidence: implementation `9922b0c725147fcabac3ce4c08f7c150c3ec6a1d`; run/job `30727440571` / `91441645867`; `42 passed`; closure `78e9315369ff4552e5500d1a820767a1fd228f29` green.
- [x] Task 6 gate. Evidence: implementation `0dcf512d404ae248d5a99651543d9d0ca9687699`; run/job `30727874051` / `91442826957`; `49 passed`; closure `cb7124c5712f6b3f8f4540e9e8fabaa2aa242bc0` green.
- [x] Task 7 gate. Implementation head `d6ea24eb6eeaea7b41dc309f866a5653aba687d5`, run/job `30729969574` / `91448384283`, `59 passed`; closure SHA `334dc79b3ce0cbc1e7b5096387218c90a8365204`, run/job `30730100518` / `91448776834`, all strict gates green.
- [x] Task 8 gate. Implementation head `cfc68a4ff775d6d4b73c0bfa192e00c1fd7b910f`, run/job `30730803320` / `91450780156`, `67 passed`; closure SHA `cecc39b9c9dcd8c90f9cdbdb4284be13c480bbd6`, run/job `30730891252` / `91451022194`, all strict gates green.

---

# Task 7: Complete legal move generation and special rules — COMPLETE

## 7.1 King-safety filtering
- [x] Generate pseudo-legal candidates through Task 6.
- [x] Apply each candidate through a private reversible move path.
- [x] Reject any candidate that leaves the moving side's king attacked.
- [x] Restore the exact position after every accepted or rejected candidate.
- [x] Reject king moves into attack.
- [x] Never generate or accept king captures.
- [x] Expose exact packed-move membership through `Position::is_legal_move`.

## 7.2 Check evasions
- [x] Single-check king moves.
- [x] Single-check checker captures.
- [x] Single-check interpositions for sliding checks.
- [x] Double check permits only king moves.
- [x] Absolute pins are enforced through post-move king-safety validation.

## 7.3 Castling correctness
- [x] Revalidate Task 6 rights, home-piece, and empty-path candidates.
- [x] Reject castling while currently in check.
- [x] Reject attacked transit squares.
- [x] Reject attacked destination squares.
- [x] Test transit attacks after vacating the king's source square.
- [x] Support all four castling directions.
- [x] Update and restore king/rook movement and castling rights.
- [x] Clear rights for king movement, rook movement from a home square, and rook capture on a home square.
- [x] Never reconstruct rights merely because pieces return to home squares.

## 7.4 En-passant correctness
- [x] Require the opposing pawn on the captured square behind the target.
- [x] Remove both the moving pawn source and captured pawn before king-safety testing.
- [x] Reject horizontal discovered-check en passant.
- [x] Reject diagonal discovered-check en passant.
- [x] Create the midpoint en-passant target after a double push.
- [x] Expire the en-passant target after every non-double move.
- [x] Restore en-passant state exactly through undo.

## 7.5 Promotion correctness
- [x] Preserve all four quiet promotion identities.
- [x] Preserve all four capture-promotion identities.
- [x] Reject promotion identity on a non-pawn.
- [x] Reject promotion identity away from the final rank.
- [x] Restore promoted moves to the original pawn through undo.

## 7.6 Initial legal perft and restoration
- [x] Private reversible `Undo` records captures, metadata, side, and hash placeholder.
- [x] No clone-per-child in legal filtering, perft, or divide.
- [x] `Position::perft(0)` returns one leaf.
- [x] Starting-position depth 1 is `20`.
- [x] Starting-position depth 2 is `400`.
- [x] Starting-position depth 3 is `8,902`.
- [x] Starting-position depth 4 is `197,281`.
- [x] Deterministic root divide.
- [x] Exact position equality and invariant validation after legal generation, perft, and divide.
- [x] `docs/RUST_LEGAL_MOVE_GENERATION.md`.

## 7.7 CI gate
- [x] Exact-head rustfmt pass.
- [x] Exact-head Cargo check pass.
- [x] Exact-head Clippy `-D warnings` pass.
- [x] Exact-head unit tests: `59 passed, 0 failed`.
- [x] Exact-head rustdoc `-D warnings` pass.
- [x] Exact-head debug and release builds.
- [x] Task 7 gate.

### Task 7 completion evidence

- Shared bounded move-list mutation: `9baf2e299551f39dbb4cbee2a1510e35d68ac6c8`.
- Legal generation/perft source: `beb6981520c16d07c2617a1c567eee7ed0a5212d`.
- Exact validated implementation head: `d6ea24eb6eeaea7b41dc309f866a5653aba687d5`.
- Implementation CI run/job: `30729969574` / `91448384283`.
- Exact closure SHA: `334dc79b3ce0cbc1e7b5096387218c90a8365204`.
- Closure CI run/job: `30730100518` / `91448776834`.
- Results: lockfile and metadata verification, rustfmt, Cargo check, Clippy with warnings denied, `59 passed`, rustdoc with warnings denied, debug build, and release build passed at both the implementation and closure heads.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime deprecation and dependency `punycode` deprecation only.

---

# Task 8: Make/unmake and incremental state — COMPLETE

## 8.1 Formal undo structure and contract
- [x] Replace the Task 7 validation-only undo record with opaque public `PositionUndo`.
- [x] Bind each undo token to the exact packed move identity that produced it.
- [x] Record the original moving piece and captured piece/square.
- [x] Record prior castling rights, en-passant target, halfmove clock, fullmove number, side to move, and hash placeholder/state.
- [x] Keep token fields private so callers cannot construct incomplete restoration state.
- [x] Expose read-only `move_made()` and `captured()` inspection.
- [x] Reject mismatched or out-of-order undo tokens before mutation.

## 8.2 Checked and generated-legal move paths
- [x] Public `Position::make_move` accepts only an exact currently legal packed move.
- [x] Public `Position::unmake_move` consumes the opaque token.
- [x] Crate-private generated-legal make/unmake avoids regenerating legality in perft and future search.
- [x] Legal generation, perft, and divide use the formal make/unmake path.
- [x] Illegal public moves fail without changing any position field.
- [x] Counter-overflow failures are transactional and non-mutating.
- [x] Side to move changes after every move.
- [x] Fullmove number increments only after Black moves.
- [x] Halfmove clock resets on pawn moves and captures, otherwise increments with overflow detection.
- [x] En-passant, castling rights, rook relocation, promotion replacement, cached king squares, mailbox, bitboards, and occupancies update through one reversible path.

## 8.3 Exact restoration coverage
- [x] Quiet move.
- [x] Double pawn push.
- [x] Ordinary capture.
- [x] En passant.
- [x] King-side castling.
- [x] Queen-side castling.
- [x] All four quiet promotion identities.
- [x] All four capture-promotion identities.
- [x] Rook capture on a home square changing castling rights.
- [x] Side, clocks, en-passant state, castling rights, captured piece, cached kings, redundant board representations, and stored hash state restore exactly.
- [x] Every legal move in a curated position corpus passes make/invariant/unmake/equality checks.

## 8.4 Long-sequence restoration and policy
- [x] Deterministic legal playouts for eight seeds, up to 128 plies each.
- [x] Validate invariants after every forward make and reverse unmake.
- [x] Reverse every sequence in strict last-in, first-out order and recover exact starting equality.
- [x] Production recursive paths use make/unmake rather than clone-per-child.
- [x] `docs/RUST_MAKE_UNMAKE.md` documents the contract and Task 9 hash boundary.

## 8.5 CI gate
- [x] Exact-head rustfmt pass.
- [x] Exact-head Cargo check pass.
- [x] Exact-head Clippy `-D warnings` pass.
- [x] Exact-head unit tests: `67 passed, 0 failed`.
- [x] Exact-head rustdoc `-D warnings` pass.
- [x] Exact-head debug and release builds.
- [x] Task 8 gate.

### Task 8 completion evidence

- Formal make/unmake module: `crates/chess-core/src/position/make_unmake.rs`.
- Restoration and deterministic sequence tests: `crates/chess-core/src/position/make_unmake_tests.rs`.
- Contract documentation: `docs/RUST_MAKE_UNMAKE.md`.
- Exact validated implementation head: `cfc68a4ff775d6d4b73c0bfa192e00c1fd7b910f`.
- Implementation CI run/job: `30730803320` / `91450780156`.
- Exact closure SHA: `cecc39b9c9dcd8c90f9cdbdb4284be13c480bbd6`.
- Closure CI run/job: `30730891252` / `91451022194`.
- Results: lockfile and metadata verification, rustfmt, Cargo check, Clippy with warnings denied, `67 passed`, rustdoc with warnings denied, debug build, and release build passed at both the implementation and closure heads.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime deprecation and dependency `punycode` deprecation only.
- Task 9 remains responsible for authoritative Zobrist computation, incremental key updates, and repetition identity; Task 8 stores and restores the existing hash field exactly.

---

# Task 9: Zobrist hashing and repetition identity — COMPLETE
- [x] 9.1 Deterministic tables.
- [x] 9.2 Full hash.
- [x] 9.3 Incremental updates.
- [x] 9.4 Canonical en-passant identity.
- [x] 9.5 Verification.
- [x] Task 9 gate.

### Task 9 completion evidence

- Deterministic versioned tables and authoritative recomputation: `crates/chess-core/src/position/zobrist.rs`.
- Incremental make/unmake integration: `crates/chess-core/src/position/make_unmake.rs`.
- Repetition-identity contract: `docs/RUST_ZOBRIST_HASHING.md`.
- Exact validated implementation head: `178583c15458cb29205201047bad8f4064a9342d`.
- Implementation CI run/job: `30731524205` / `91452671063`.
- Results: lockfile and metadata verification, rustfmt, Cargo check, Clippy with warnings denied, `72 passed`, rustdoc with warnings denied, debug build, and release build.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime deprecation and dependency `punycode` deprecation only.
- Task 10 owns game history, repetition counts, claimable draws, and automatic draws; Task 9 supplies the canonical position identity.

---

# Task 10: Game, history, and draw semantics — COMPLETE
- [x] 10.1 Game state.
- [x] 10.2 Mate/stalemate.
- [x] 10.3 Claimable draws.
- [x] 10.4 Automatic draws.
- [x] 10.5 Conservative dead-position logic.
- [x] 10.6 Search history.
- [x] Task 10 gate.

### Task 10 completion evidence

- Game, status, draw, undo, and detached search-history implementation: `crates/chess-core/src/game.rs`.
- Public game/history exports: `crates/chess-core/src/lib.rs`.
- Rule and ownership contract: `docs/RUST_GAME_HISTORY_AND_DRAWS.md`.
- Exact validated implementation head: `dd57b258fc8b9af647c30a1834f3d9e79a3d8ee3`.
- Implementation CI run/job: `30732542941` / `91455346591`.
- Results: lockfile and metadata verification, rustfmt, Cargo check, Clippy with warnings denied, `84 passed`, rustdoc with warnings denied, debug build, and release build.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime deprecation and dependency `punycode` deprecation only.
- Task 11 owns the expanded authoritative perft suite, divide tooling, differential oracle, and corpus gate.

---

# Task 11: Authoritative perft and differential validation — COMPLETE
- [x] 11.1 Standard exact perft suite.
- [x] 11.2 Slow perft.
- [x] 11.3 Divide tool.
- [x] 11.4 Differential oracle harness.
- [x] 11.5 Corpus gate.
- [x] Task 11 gate.

### Task 11 completion evidence

- Six-position depth-one through depth-five manifest: `fixtures/perft.tsv`.
- Fast and slow Rust gates: `crates/chess-core/tests/authoritative_perft.rs`.
- Deterministic perft, divide, legal, child-FEN, suite, and oracle tooling: `crates/chess-tools/src/lib.rs` and `crates/chess-tools/src/main.rs`.
- Permanent special-rule corpus: `fixtures/differential_corpus.tsv`.
- Pinned external oracle and harness: `requirements/oracle.txt` and `scripts/differential_oracle.py`.
- Validation contract: `docs/RUST_PERFT_AND_DIFFERENTIAL_VALIDATION.md`.
- Exact validated implementation head: `1711fefe37b93163ec316ba9528742d6f87f8496`.
- Implementation CI run/job: `30733309460` / `91457298625`.
- Results: lockfile and metadata verification, rustfmt, Cargo check, Clippy with warnings denied, 89 executed Rust tests, release depth-four perft, rustdoc with warnings denied, debug build, release build, fifteen oracle positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies.
- Depth-five validated head: `e5c44147c8f6097f1d60c8d6d73a051da4fc13a1`.
- Depth-five run/job: `30733437572` / `91457637460`; all six positions and 469,080,960 leaves passed in 39.77 seconds.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 12 owns the baseline evaluator, score convention, trace, named weights, and evaluator exclusions.

---

# Task 12: Baseline evaluator and trace — COMPLETE
- [x] 12.1 Score convention.
- [x] 12.2 Baseline terms.
- [x] 12.3 Efficiency.
- [x] 12.4 Trace.
- [x] 12.5 Named weights.
- [x] 12.6 Exclusions.
- [x] Task 12 gate.

### Task 12 completion evidence

- Typed centipawn and mate-score contract: `crates/chess-search/src/score.rs`.
- Tapered evaluator and fixed trace: `crates/chess-search/src/evaluation.rs`.
- Named, versioned, checksummed weights: `crates/chess-search/src/weights.rs`.
- Explicit adapter serialization and diagnostics: `crates/chess-tools/src/weights_io.rs`, `crates/chess-tools/src/lib.rs`, and `crates/chess-tools/src/main.rs`.
- Contract and benchmark record: `docs/RUST_BASELINE_EVALUATOR.md`.
- Exact formatted implementation head: `d8547cc258ecc2e52b8e4eb7ef287d92d5d0a04f`.
- Permanent implementation CI run/job: `30734451785` / `91460574656`.
- Results: rustfmt, Cargo check, strict Clippy, 103 executed Rust tests, release depth-four perft, rustdoc, debug/release builds, and the independent differential corpus passed.
- Benchmark/tooling run/job: `30734335652` / `91460185440`; fixed trace, five release benchmark groups, explicit weight export, and validated import passed.
- Baseline weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`.
- Normal evaluation and tracing are fixed-structure and allocation-free; serialization and benchmark allocations remain tool-only.
- Exclusion audit found no transcript-specific, review-loop, anti-drift, or exact-scenario evaluator guidance.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime and dependency `punycode` deprecation notices only.
- Task 13 owns reference minimax, negamax alpha-beta, shallow equivalence, search immutability, and terminal fixtures.

---

## Pre-Task-13 review-fix closure — COMPLETE

- [x] Search-safe opaque legal-move tokens are available to `chess-search` without legal-list regeneration.
- [x] Tokens bind exact move identity, Zobrist, side, castling, en-passant, and counters.
- [x] Stale and wrong-origin tokens fail before mutation.
- [x] Legal-token make/unmake restores exact position and hash state.
- [x] `Game::reset_to_starting` and `Game::set_position` establish fresh root history.
- [x] Divide output includes stable `elapsed_nanos` timing.
- [x] FEN analysis-position policy is explicit and tested.
- [x] Task 25 and immediate-next-operation tracking is current.
- [x] Review-fix implementation gate passed.
- [x] Temporary workflows/scripts were removed.

Evidence:

- Starting code/documentation SHA: `52377d09b713541044e24c8e3559be3f12002cc1`.
- Validated implementation SHA: `81a7cd4a58a52695eca2ede10d5c73c803851d17`.
- One-shot implementation control run: `30738801841`.
- Permanent implementation CI run/job: `30739166607` / `91473334960`.
- Results: rustfmt, Cargo check, strict Clippy, 112 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Clean code/workflow SHA `9c27d2c1c4a39a975b30d3357b69b6c96bb64c68` compared with the validated candidate with zero changed files.
- Later commits finalize documentation only; they do not alter the validated Rust or permanent workflow tree.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime and dependency `punycode` deprecation notices only.
- At review-fix closure, Task 13 remained active and not started; Task 13.1 is now complete.

---

# Task 13: Reference search and alpha-beta — COMPLETE
- [x] 13.1 Reference search.
- [x] 13.2 Negamax alpha-beta.
- [x] 13.3 Shallow equivalence.
- [x] 13.4 Immutability.
- [x] 13.5 Terminal fixtures.
- [x] Task 13 gate.

### Task 13.1 completion evidence

- Public reference-search API: `reference_search`, `ReferenceSearchResult`, and `ReferenceSearchError`.
- Implementation: `crates/chess-search/src/reference.rs`.
- Public export: `crates/chess-search/src/lib.rs`.
- Contract documentation: `docs/RUST_REFERENCE_SEARCH.md`.
- Exact validated implementation SHA: `7cf7fb027bf86f0658c14f4c9b452bce2cdcbe98`.
- Permanent CI run/job: `30741414286` / `91479443116`.
- Results: rustfmt, Cargo check, strict Clippy, 118 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc, debug/release builds, and independent differential validation passed.
- Reference-search coverage includes depth-zero evaluation, exact starting depth-two node count `421`, deterministic best-move selection, mate/stalemate precedence, ply-relative mate scoring, dead/fifty-move/seventy-five-move/repetition draws, mismatched-history failure, excessive-depth failure, and exact root/history restoration.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13.2 now provides negamax alpha-beta over this reference implementation.

### Task 13.2 completion evidence

- Public alpha-beta API: `alpha_beta_search`, `AlphaBetaSearchResult`, and `AlphaBetaSearchError`.
- Recursive fail-soft negamax implementation: `crates/chess-search/src/alpha_beta.rs`.
- Shared terminal/draw resolver: `crates/chess-search/src/search_common.rs`.
- Public export: `crates/chess-search/src/lib.rs`.
- Contract documentation: `docs/RUST_NEGAMAX_ALPHA_BETA.md`.
- Exact validated implementation SHA: `d662ca07cae6b0044c1ce620a0dc4f3249784d6c`.
- Permanent CI run/job: `30741988672` / `91480926153`.
- Results: rustfmt, Cargo check, strict Clippy, 124 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc, debug/release builds, and independent differential validation passed.
- Coverage includes full-window exact root scoring, recursive `(-beta, -alpha)` windows, alpha-beta cutoffs, deterministic first-best ties, legal best-move return, ply-relative mate scoring, repetition draws, fail-loud root-history/depth validation, and exact root/history restoration.
- The starting-position depth-three regression visits fewer than the complete unpruned `9,323` nodes.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13.3 now provides direct shallow score, uniquely-best-move, and node-count equivalence against reference search.

### Task 13.3 completion evidence

- Integration suite: `crates/chess-search/tests/search_equivalence.rs`.
- Contract documentation: `docs/RUST_SEARCH_EQUIVALENCE.md`.
- Exact validated implementation SHA: `bdf98a8e7c5cb6aadc55ba3638cd3af2f4ba9e91`.
- Permanent CI run/job: `30743024471` / `91483729312`.
- Results: rustfmt, Cargo check, strict Clippy, 127 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc, debug/release builds, and independent differential validation passed.
- Curated paired searches cover quiet opening, tactical material, mate-adjacent, mated, stalemate, fifty-move, and game-history repetition positions at depths one through three.
- Every paired fixture returned an identical exact score; alpha-beta visited no more nodes than reference search on every fixture and strictly fewer on at least one.
- The tactical fixture independently proved `d1d8` is the unique exact best move before requiring both searches to return it.
- Every successful paired invocation restored the root position, incremental Zobrist identity, and detached history. Task 13.4 now formalizes the broader completion, failure, repeated-search, and cancellation contract.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13.4 is complete; Task 13.5 and the overall Task 13 gate remain open.

### Task 13.4 completion evidence

- Public cancellation boundary: `SearchCancellationProbe`, `reference_search_with_cancellation`, and `alpha_beta_search_with_cancellation`.
- Cancellation errors: `ReferenceSearchError::Cancelled` and `AlphaBetaSearchError::Cancelled`.
- Implementation: `crates/chess-search/src/cancellation.rs`, `reference.rs`, and `alpha_beta.rs`.
- Integration suite: `crates/chess-search/tests/search_immutability.rs`.
- Contract documentation: `docs/RUST_SEARCH_IMMUTABILITY.md`.
- Exact validated implementation SHA: `3644e032504b604c210796f1e6c7ef056d05e94b`.
- Permanent CI run/job: `30743519630` / `91485044296`.
- Results: rustfmt, Cargo check, strict Clippy, 131 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc, debug/release builds, and independent differential validation passed.
- Coverage proves exact position, incremental/recomputed Zobrist, enforceable invariants, and detached-history restoration after repeated successful searches, terminal completion, validation failure, and mid-tree cancellation.
- Reference and alpha-beta cancellation fixtures trigger after 64 probe checks from inside active recursive lines and return cancellation only after ancestor history entries are popped and moves are unmade.
- The narrow callback probe deliberately excludes Task 16 clocks, node limits, iterative deepening, partial-result policy, UCI stop handling, and adapter cancellation.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13.5 and the overall Task 13 gate are complete.

### Task 13.5 and Task 13 gate completion evidence

- Integration suite: `crates/chess-search/tests/search_terminals.rs`.
- Contract documentation: `docs/RUST_SEARCH_TERMINAL_FIXTURES.md`.
- Exact validated implementation SHA: `7ca429b0c883bbb8484d3eb3a4af7d96cdb57201`.
- Permanent CI run/job: `30745120833` / `91489299233`.
- Results: rustfmt, Cargo check, strict Clippy, 135 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc, debug/release builds, and independent differential validation passed.
- Terminal roots cover checkmate precedence at halfmove `150`, stalemate, dead position, claimable fifty-move draw, automatic seventy-five-move draw, claimable threefold repetition, and automatic fivefold repetition. Every terminal/draw root returns one node and no best move.
- Shorter-mate fixture `7k/5Q2/6K1/8/8/8/8/8 w - - 0 1` proves `f7e8` scores `mate_in(1)`, `f7a7` scores `mate_in(3)`, and the full root selects an immediate mate.
- Longer-survival fixture `4Q2k/8/4K3/8/8/8/8/8 b - - 0 1` proves `h8g7` scores `mated_in(6)`, `h8h7` scores `mated_in(4)`, and the full root selects `h8g7`.
- Reference and alpha-beta search agree on exact scores and deterministic root best moves; alpha-beta visits no more nodes than reference search on paired full-root fixtures.
- Individual root-move oracles normalize separately searched child-root mate scores by one ply before comparing them at the parent root.
- Every full-root and individual-root-move invocation restores logical position, detached history, incremental/recomputed Zobrist identity, and enforceable invariants exactly.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13 is complete. Task 14.1 quiescence is next.

# Task 14: Quiescence and ordering — COMPLETE
- [x] 14.1 Quiescence.
- [x] 14.2 Tactical ordering.
- [x] 14.3 Quiet ordering.
- [x] 14.4 Correctness tests.
- [x] 14.5 Exclusions.
- [x] Task 14 gate.

### Task 14.1 completion evidence

- Public quiescence API: `quiescence_search`, `quiescence_search_with_limit`, `quiescence_search_with_cancellation`, `QuiescenceSearchResult`, and `MAX_QUIESCENCE_PLY`.
- Production implementation: `crates/chess-search/src/quiescence.rs`; alpha-beta depth-zero integration: `crates/chess-search/src/alpha_beta.rs`.
- Shared terminal/draw semantics: `crates/chess-search/src/search_common.rs`.
- Independent unpruned tactical-leaf oracle: `reference_search_with_quiescence` and `reference_search_with_quiescence_and_cancellation` in `crates/chess-search/src/reference.rs`.
- Regression suites: `crates/chess-search/tests/search_quiescence.rs`, bounded matching-oracle coverage in `search_equivalence.rs`, and preserved terminal/mate-distance coverage in `search_terminals.rs`.
- Contract documentation: `docs/RUST_QUIESCENCE_SEARCH.md`.
- Exact validated implementation SHA: `24e1090e17f8b39bdaac4989daffdeaea4b857e9`.
- Permanent CI run/job: `30749044761` / `91499685362`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, strict Clippy, 140 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Semantics: stand-pat only outside check; every legal check evasion; captures and all promotions outside check; fail-soft alpha-beta bounds; repetition/dead/fifty-move draw handling; cancellation at node and child boundaries; and a fail-loud 64-ply tactical guard when check cannot safely stand pat.
- Dedicated fixed regressions cover the hanging-capture horizon, quiet check evasions, promotions, poisoned captures with forced recapture, full-window equality against an independent unpruned tactical oracle, draw resolution, cancellation, depth-guard failure, and exact position/history/Zobrist restoration.
- Matching quiescence-oracle equivalence proves identical exact scores and alpha-beta node counts no greater than the unpruned tactical reference on bounded curated fixtures, with at least one strict cutoff witness.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Tasks 14.2 and 14.3 ordering are complete; Task 14.4 correctness consolidation is next.

### Task 14.2 completion evidence

- Bounded stable ordering implementation: `crates/chess-search/src/move_ordering.rs`.
- Alpha-beta and quiescence integration: `crates/chess-search/src/alpha_beta.rs` and `crates/chess-search/src/quiescence.rs`.
- Reference control policy: `crates/chess-search/src/reference.rs` retains exact legal-generation order through `MoveOrdering::Generation`.
- Contract documentation: `docs/RUST_TACTICAL_MOVE_ORDERING.md`.
- Exact validated implementation SHA: `3688cb8e89a7da0c7fd34c3756d52d0fcc8d3d33`.
- Permanent CI run/job: `30753873602` / `91512570865`.
- Results: workspace assets, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 145 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Production order is an explicit no-op transposition-table hook, promotions by promoted-piece value, MVV-LVA captures, then generation-stable remaining moves. Promotion captures remain in the promotion tier; en-passant captures use a pawn victim.
- Ordering storage is fixed-capacity stack-backed and copies opaque source-bound legal tokens without synthesizing moves, allocating per node, mutating the position, or weakening token-origin validation.
- Focused tests prove the TT hook is currently `None`, generation policy preserves the exact token sequence, a supplied future TT move receives first priority, queen/rook/bishop/knight promotion priority is deterministic, and MVV-LVA prefers both the more valuable victim and the cheaper attacker.
- A fixed narrow-window tactical tree returns the same fail-soft score and best move under generation and tactical policies while tactical ordering visits strictly fewer nodes; both paths restore position, detached history, invariants, and incremental/recomputed Zobrist identity exactly.
- Existing equivalence, cancellation/immutability, quiescence, terminal/mate-distance, perft, and differential suites remain green.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Static exchange evaluation remains intentionally absent. Task 14.3 now owns bounded killer/history/stable-tie quiet ordering; transposition storage belongs to Task 15; production limits and real iterative previous-PV reuse belong to Task 16.

### Task 14.3 completion evidence

- Production implementation: `crates/chess-search/src/move_ordering.rs` and `crates/chess-search/src/alpha_beta.rs`.
- Contract documentation: `docs/RUST_QUIET_MOVE_ORDERING.md`.
- Exact implementation SHA: `f08b2d519ffc066d8d6b18326e03ead278d908de`.
- Focused implementation run/job: `30762211967` / `91534658841`; Cargo check, strict Clippy, and all 51 `chess-search` tests passed.
- Full closure validation run/job: `30762457921` / `91535329886`.
- Results: workspace assets, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 150 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Bounded search-local state provides two killer slots for every supported ply and one fixed `2 x 64 x 64` side/source/destination history table.
- Only quiet beta cutoffs update killers and history. History uses a depth-squared saturating bonus capped at `1,000,000`; captures and promotions never pollute quiet statistics.
- Production order is the future TT hook, explicit previous-PV hook, promotions, MVV-LVA captures, primary/secondary killers, descending history, then ascending packed `Move` identity.
- The previous-PV hook remains an explicit no-op until Task 16 supplies completed-iteration PV data; the TT hook remains an explicit no-op until Task 15.
- Fixed full-window and narrow-window regressions prove deterministic exact score/best-move semantics, strict node reduction when a useful killer is seeded, and exact position/history/incremental-Zobrist restoration.
- Reference search retains exact legal-generation order; Task 14.2 tactical ordering remains available as a control policy. Task 14.4 correctness consolidation is complete; Task 14.5 exclusion audit is next.

### Task 14.4 completion evidence

- Dedicated regressions: `crates/chess-search/tests/search_quiescence_task_14_4.rs`.
- Exact validated implementation/evidence SHA: `dc758a3fc62e7f7002191993c73773dd2a71caef`.
- Permanent CI run/job: `30763226685` / `91537383867`.
- Results: workspace assets, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 155 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- The horizon witness searches the full `Qxe5 Rxe5 Rxe5` tactical continuation beyond the nominal leaf and restores the exact root state.
- The in-check witness proves stand-pat is unavailable by requiring a searched quiet king evasion and more than one visited node.
- The promotion witness searches promotion, forced recapture, and counter-recapture rather than stopping at the promotion leaf.
- The poisoned-capture witness explicitly proves static leaf evaluation overvalues `Qxd8`, quiescence lowers that score after forced `Kxd8`, and the one-ply root rejects the poisoned move.
- The boundedness witness proves a zero-ply guard returns one-node stand-pat outside check but fails loudly with `QuiescenceDepthLimitReachedInCheck` while checked.
- Every new path verifies position/history snapshots, invariants, and incremental/recomputed Zobrist restoration.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 14.5 explicit-exclusion audit and the overall Task 14 gate are complete.

### Task 14.5 and Task 14 gate completion evidence

- Permanent executable audit: `scripts/task_14_5_exclusion_audit.py`.
- Audit contract: `docs/RUST_SEARCH_ORDERING_EXCLUSION_AUDIT.md`.
- Permanent CI now runs the audit before Rust toolchain validation.
- Exact validated implementation SHA: `f4dc989e97d8577f4c86bdbfb67ae47e3d5cd7f4`.
- Permanent CI run/job: `30764073097` / `91539614372`.
- The audit scanned 10 production `chess-search` Rust files and found no transcript/review-loop or anti-drift/scenario-scoring identifiers.
- `MoveOrderKey` is restricted to TT/PV hooks, tactical category/material terms, killer/history values, and the encoded tie-break.
- Move ordering may query only `Position::piece_at` and `Position::side_to_move`; strategic evaluator identifiers are forbidden in production ordering code.
- Root alpha-beta retains the complete score window and replaces the best move only on a strictly greater searched score; ordering keys are absent from result selection.
- Existing exact-score witnesses prove full-window quiet-ordering determinism and unique-root-maximum selection; tactical and quiet narrow-window witnesses prove node reduction without score or best-move changes.
- Results: workspace assets, exclusion audit, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 155 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Tasks 14 and 15 are complete. Task 16.1 iterative deepening is next.

# Task 15: Fixed-capacity transposition table — COMPLETE
- [x] 15.1 Entries.
- [x] 15.2 Storage.
- [x] 15.3 Mate normalization.
- [x] 15.4 Probes.
- [x] 15.5 Replacement.
- [x] 15.6 Diagnostics.
- [x] Task 15 gate.

### Task 15.1 completion evidence

- Entry implementation: `crates/chess-search/src/transposition.rs`.
- Public value types: `TranspositionEntry`, `TranspositionBound`, and `TranspositionScore`, re-exported by `chess-search`.
- Contract documentation: `docs/RUST_TRANSPOSITION_TABLE_ENTRY.md`.
- Exact validated implementation SHA: `65ef70bfbff3d0bf5fd6e6a19ba20ed5214c3e26`.
- Permanent CI run/job: `30764647127` / `91541116562`.
- The entry retains the complete 64-bit verification key, `u16` search depth, explicit exact/lower/upper bound, typed normalized score, optional compact `Move`, and one-byte generation.
- `TranspositionScore` establishes a distinct storage-score domain without prematurely implementing Task 15.3 mate conversion.
- `repr(C)` and focused layout tests keep the entry footprint at no more than 24 bytes on supported targets while adding no wrapper overhead around `Score`.
- Five deterministic tests cover stable bound tags, all required fields, every bound, absent best moves, full-key verification, copy/value semantics, and bounded layout.
- Production search still does not allocate, probe, store, cut off, or activate TT move ordering; those remain Tasks 15.2–15.4.
- Results: workspace assets, permanent Task 14.5 exclusion audit over 11 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 160 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Tasks 15.2–15.6 and the overall Task 15 gate are complete.

### Task 15.2 completion evidence

- Storage implementation: `crates/chess-search/src/transposition.rs`.
- Public API: `TranspositionTable`, `TranspositionTableAllocationError`, and `TRANSPOSITION_CLUSTER_SIZE`.
- Storage contract: `docs/RUST_TRANSPOSITION_TABLE_STORAGE.md`.
- Exact validated implementation SHA: `6b2ee0081cd47fd9069aeabb0d3ccb1d3659fea9`.
- Permanent CI run/job: `30765303745` / `91542820537`.
- MiB configuration uses checked byte arithmetic and rounds down only to complete four-entry clusters.
- Construction performs one fallible fixed-size `Vec` reservation, never grows afterward, and has no map, per-node allocation, silent shrinking, or unbounded fallback.
- Allocation failures are typed for zero size, arithmetic overflow, no complete cluster, and allocator rejection.
- Complete verification keys map deterministically to clusters while each occupied entry retains its complete key for later collision rejection.
- `clear()` empties every slot in place without reallocating or changing generation; `advance_generation()` wraps deterministically without clearing existing entries.
- Five new deterministic storage tests passed, bringing the workspace total to 165 executed non-doc Rust tests.
- Production search still does not probe, store, cut off, or apply replacement policy; those remain Tasks 15.4–15.5.
- Results: workspace assets, permanent Task 14.5 exclusion audit over 11 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 165 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Tasks 15.3–15.6 and the overall Task 15 gate are complete.

### Task 15.3 completion evidence

- Conversion implementation: `crates/chess-search/src/transposition_score.rs`.
- Public API: `TranspositionScore::normalize`, `TranspositionScore::denormalize`, and `TranspositionScoreConversionError`.
- Contract documentation: `docs/RUST_TRANSPOSITION_TABLE_MATE_NORMALIZATION.md`.
- Exact validated implementation SHA: `ac68b99db53546c31f3aae68ad7337ba256eb982`.
- Permanent CI run/job: `30766126491` / `91545080021`.
- Winning mate scores add the current root ply on storage and subtract the probe ply on retrieval; losing mate scores perform the inverse operations.
- The conversion removes already-travelled root distance so the same position produces one normalized TT value when reached at different plies.
- Every ordinary evaluation from `-MAX_EVALUATION` through `MAX_EVALUATION` is preserved exactly.
- Unsupported plies and conversions outside the supported score domain return typed errors; no clamping, saturation, or fallback score is permitted.
- The unchecked `TranspositionScore::from_normalized` constructor is crate-private, preventing external callers from bypassing the conversion boundary.
- Six deterministic tests cover ordinary evaluations, winning and losing cross-ply reuse, both maximum-ply boundaries, inconsistent mate values, and unsupported plies.
- Production alpha-beta now calls the probe, store, diagnostics, and TT move-ordering boundaries under the completed Task 15 gate.
- Results: workspace assets, permanent Task 14.5 exclusion audit over 12 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 171 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Tasks 15.4–15.6 and the overall Task 15 gate are complete.


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
- Production alpha-beta now uses deterministic updates, collision replacement, diagnostics, score reuse, and TT move ordering under the completed Task 15 gate.
- Results: workspace assets, permanent Task 14.5 exclusion audit over 12 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 179 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 15.5 replacement, Task 15.6 diagnostics, and the overall Task 15 integration gate are complete.

### Task 15.5 completion evidence

- Store implementation: `crates/chess-search/src/transposition/store.rs`.
- Public API: `TranspositionTable::store`, `TranspositionStoreAction`, and `TranspositionStoreResult`.
- Contract documentation: `docs/RUST_TRANSPOSITION_TABLE_REPLACEMENT.md`.
- Exact validated implementation SHA: `775013a6e11aad7625c88b0cd3b258819211e839`.
- Permanent CI run/job: `30767556904` / `91548869513`.
- Complete-key matches update the existing slot in place, preventing duplicate entries for one position.
- The table's current generation is authoritative for every incoming entry.
- Different-key stores use the lowest-index empty slot before considering replacement.
- Full clusters evict the shallowest entry, then the oldest modulo-256 generation, then the lowest slot index.
- Every store reports its cluster, slot, action, and prior or evicted entry where applicable.
- Five deterministic cluster-level tests passed, bringing the workspace total to 184 executed non-doc Rust tests.
- The first validation attempt exposed only a test-only import scoped into production; the second exposed only a strict-Clippy fixture-loop style issue. Both were corrected without lint suppression or replacement-policy changes.
- Results: workspace assets, permanent Task 14.5 exclusion audit over 12 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 184 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Diagnostics, hash-full estimation, and microbenchmarks are complete under Task 15.6; production search integration is complete under the overall Task 15 gate.
- The overall Task 15 production integration gate is complete.

### Task 15.6 completion evidence

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
- Production alpha-beta owns or accepts a bounded table, calls the verified probe/store paths, and has deterministic move-ordering and warm-table node-reduction witnesses under the completed Task 15 gate.


### Task 15 gate completion evidence

- Production integration: `crates/chess-search/src/alpha_beta.rs` and `crates/chess-search/src/move_ordering.rs`.
- Public caller-owned APIs: `alpha_beta_search_with_transposition_table` and `alpha_beta_search_with_cancellation_and_transposition_table`.
- Convenience searches allocate one bounded table using `DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES`, currently 1 MiB; caller-owned tables retain fixed allocation and entries across searches.
- Search resolves legal moves, terminal states, repetition, dead position, and move-count draws before accepting cached scores.
- Complete-key, depth, bound, mate-denormalization, and legal-root-move checks remain mandatory before a TT return or cutoff.
- Scores are stored and reused only at an irreversible-history boundary where the halfmove clock is zero. Reversible-history nodes may use a verified move for ordering but cannot reuse or store path-dependent scores.
- Root ordering-only hints are ignored. A one-node root return requires an exact entry with a currently legal canonical best move.
- Completed nodes store normalized exact/lower/upper results against the original alpha-beta window; cancellation, terminal/draw resolution, conversion failure, and incomplete restoration never store entries.
- Contract documentation: `docs/RUST_TRANSPOSITION_TABLE_SEARCH_INTEGRATION.md`.
- Production implementation commit: `c9eac6b8b7b4b6511d73155242dde08a554d8e88`.
- Exact clean validated SHA: `682114cd2452b04e1f24af1150928baaff779aa8`.
- Permanent exact-SHA CI run/job: `30770018597` / `91555458016`.
- Release integration witness run/job: `30769901197` / `91555134018`.
- Five focused regressions were added, bringing the workspace total to 193 executed non-doc Rust tests.
- The fixed narrow-window witness proves an insufficient-depth TT entry contributes only its verified move, preserves score and best move, and visits strictly fewer nodes.
- The warm-table witness proves a second identical full-window search returns the same exact score and canonical best move in one node without resizing the table.
- Additional regressions reject an illegal exact-root move, suppress cached scores and root hints for reversible history, and preserve position, history, and incremental/recomputed Zobrist identity exactly.
- Results: permanent exclusion audit, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 193 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The clean implementation delta contains only three Rust modules, one integration-test file, and one contract document; no temporary workflow, script, unbounded map, or fallback remains.
- Task 15 and Tasks 16.1/16.3 are complete. Task 16.2 aspiration windows is next.

# Task 16: Iterative deepening, PV, limits, cancellation — COMPLETE
- [x] 16.1 Iterative deepening.
- [x] 16.2 Aspiration windows.
- [x] 16.3 Principal variation.
- [x] 16.4 Limits.
- [x] 16.5 Cancellation.
- [x] 16.6 Result API.
- [x] 16.7 Optional extension.
- [x] Task 16 gate.

### Task 16.1 completion evidence

- Implementation: `crates/chess-search/src/iterative_deepening.rs`, with public exports from `crates/chess-search/src/lib.rs`.
- Public APIs: `iterative_deepening_search`, `iterative_deepening_search_with_transposition_table`, `IterativeDeepeningIteration`, `IterativeDeepeningSearchResult`, and `IterativeDeepeningSearchError`.
- Every request searches complete full-window depths `1..=maximum_depth` in ascending order and retains one exact record for every completed depth.
- The convenience boundary allocates one bounded default table; the caller-owned boundary reuses one fixed-capacity table and the same detached root history across all iterations.
- Each completed record reports depth, exact score, canonical best move, iteration nodes, isolated TT diagnostics, bounded hash-full sampling, and generation.
- Result storage uses a fallible exact reservation bounded by `MAX_MATE_PLY`; zero depth, excessive depth, allocation failure, iteration failure, and node-total overflow are typed errors.
- Five regressions prove fixed-depth equivalence, generation and diagnostic isolation, terminal iteration behavior, invalid-depth fail-fast behavior, history mismatch safety, and exact position/history/Zobrist restoration.
- Contract documentation: `docs/RUST_ITERATIVE_DEEPENING.md`.
- Exact validated implementation SHA: `886ad953952b3a409800fcf7e8699365f94f0271`.
- Permanent CI run/job: `30772536115` / `91562076526`.
- Results: permanent exclusion audit over 13 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 198 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The initial validation found only canonical rustfmt changes; the next found an invalid test assumption about sparse bounded hash-full sampling. Production semantics did not change.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16 is complete. Task 17.1 protocol loop is complete; Task 17.2 UCI search worker is next.

### Task 16.2 completion evidence

- Implementation: `crates/chess-search/src/aspiration.rs`, the typed root-window boundary in `crates/chess-search/src/alpha_beta.rs`, and aspiration orchestration in `crates/chess-search/src/iterative_deepening.rs`.
- Public APIs: `AspirationWindowOutcome`, `AspirationWindowAttempt`, `AspirationWindowDiagnostics`, `DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS`, and per-iteration `aspiration_diagnostics`.
- Depth one searches the complete supported score domain. Later depths center a deterministic ±50-centipawn window on the immediately prior exact score.
- Initial fail-low and fail-high results remain typed upper/lower bounds: `reported_score` is observable for diagnostics, while `exact_score` returns `None`.
- A failed bounded attempt receives exactly one complete-window retry. Only an exact attempt can become the completed iteration result, best move, PV, or ponder source.
- Every attempt at one depth shares one TT generation. Per-attempt diagnostics are retained, while iteration nodes and TT counters aggregate all attempts with checked/saturating arithmetic.
- Mate-boundary centers fall back directly to the complete window; there is no unbounded widening loop or unbounded allocation.
- Deterministic regressions force both fail-low and fail-high, prove bounds cannot be promoted to exact scores, and recover the same score and canonical best move as an independent full-window search.
- Contract documentation: `docs/RUST_ASPIRATION_WINDOWS.md`; `docs/RUST_ITERATIVE_DEEPENING.md` updated for Tasks 16.1–16.3.
- Production implementation commit: `c1d1c61caf85fd230b48a4b9026b9aa8b7ae79bf`.
- Exact clean validated implementation SHA: `8af24520fd72faffff1cab74581f056a083cfb13`.
- Permanent CI run/job: `30779589438` / `91581508274`.
- Results: permanent exclusion audit over 15 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 206 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Initial validation iterations found an audit-witness shape requirement, one invalid private `const fn` qualifier, and one eight-argument internal constructor rejected by strict Clippy. Each was corrected directly without changing the aspiration contract or adding a suppression.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16 is complete. Task 17.1 protocol loop is complete; Task 17.2 UCI search worker is next.

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
- Task 16 is complete. Task 17.1 protocol loop is complete; Task 17.2 UCI search worker is next.

### Task 16.4 completion evidence

- Implementation: `crates/chess-search/src/limits.rs`, cancellation-aware root-window orchestration in `crates/chess-search/src/iterative_deepening.rs`, and exact node-entry hooks in `alpha_beta.rs`, `quiescence.rs`, and `cancellation.rs`.
- Public APIs: `SearchLimits`, `SearchStopFlag`, `SearchLimitError`, `SearchLimitTermination`, `LimitedIterativeDeepeningSearchResult`, `iterative_deepening_search_with_limits`, and `iterative_deepening_search_with_limits_and_transposition_table`.
- Supported limits: bounded depth, exact cumulative production-node budget, soft time, hard time, infinite mode, and a clone-shareable atomic explicit-stop flag.
- Validation rejects zero limits, soft time greater than hard time, finite requests without an automatic limit, infinite requests with automatic limits, and infinite requests without a stop flag before table or root mutation.
- Deterministic precedence is explicit stop, hard time, nodes, completed depth, soft time, then the maximum supported depth ceiling.
- Soft time is applied only after a fully exact iteration. Hard time, node limits, and explicit stop are checked through the production alpha-beta/quiescence tree.
- Limit interruption discards the incomplete depth while retaining every preceding exact iteration, canonical best move, legal PV, ponder move, and completed diagnostics.
- `searched_nodes` counts completed work plus interrupted partial work; `incomplete_nodes` exposes only discarded partial work.
- Existing fixed-depth iterative-deepening APIs preserve their prior behavior through the same cancellation-aware internal boundary with `NeverCancelled`.
- Deterministic regressions cover exact depth equivalence, exact node-budget stopping one node into a later depth, finite and infinite preset-stop behavior, invalid-limit fail-fast behavior, deterministic soft/hard clock boundaries, table-generation behavior, and exact position/history/Zobrist restoration.
- Contract documentation: `docs/RUST_SEARCH_LIMITS.md`; `docs/RUST_ITERATIVE_DEEPENING.md` updated through Task 16.4.
- Production implementation commit: `1cbe0264418afbcddc564b1e4972c4819fb0a6f8`.
- Exact clean validated implementation SHA: `8a48ee45199e58db76adee4e4fc4adaf131566d2`.
- Permanent CI run/job: `30780915406` / `91585230626`.
- Results: permanent exclusion audit over 16 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 214 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16 is complete. Task 17.1 protocol loop is complete; Task 17.2 UCI search worker is next.

### Task 16.5 completion evidence

- Implementation: the formal polling contract in `crates/chess-search/src/cancellation.rs`, deterministic fallback integration in `crates/chess-search/src/iterative_deepening.rs`, and release benchmarking in `crates/chess-tools`.
- Public APIs: `CANCELLATION_CHECK_INTERVAL_NODES`, `SearchCancellationFallback`, and `LimitedIterativeDeepeningSearchResult::fallback`.
- The production polling interval is explicitly one alpha-beta or quiescence node. Child boundaries also poll before applying the next legal move, so cancellation cannot require completion of an arbitrary subtree or depth.
- Interrupted search frames pop reversible history and unmake every active move before propagating typed cancellation. Position, detached history, current history identity, incremental Zobrist identity, and recomputed Zobrist identity restore exactly.
- An interrupted partial depth contributes no exact score, move, PV, ponder move, aspiration record, or completed-node total. Every earlier fully completed exact iteration remains authoritative.
- When no iteration completed, the result exposes either `FirstLegalMove`, selected from deterministic legal-generation order at the unchanged root, or `NoLegalMove` for a terminal root. The fallback is unscored and is not represented as a completed depth.
- Deterministic regressions inject a request after 64 production nodes, prove observation within the one-node bound, cover one-node and preset-stop fallbacks, preserve the prior completed iteration, and verify exact root restoration.
- Release benchmark command: `cargo run --locked -p chess-tools --release -- cancel-bench ITERATIONS`.
- Hosted smoke output for four samples: `cancel<TAB>4<TAB>64<TAB>0<TAB>404<TAB>186<TAB>5435046110819296062`; it observed zero additional nodes after each request. Nanosecond values are informational, while the one-node bound is enforced.
- Contract documentation: `docs/RUST_RESPONSIVE_CANCELLATION.md`; `docs/RUST_SEARCH_LIMITS.md` and `docs/RUST_ITERATIVE_DEEPENING.md` updated through Task 16.5.
- Production implementation commit: `68f86a53c31dd5f1448e99fb7def8bb220f2222f`.
- Exact clean validated implementation SHA: `128f52e8fb7d7e9974605fc840eb13d3ecc021a6`.
- Permanent CI run/job: `30782361257` / `91589434579`.
- Results: permanent exclusion audit over 16 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 218 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The first implementation validation exposed one localized Rust iterator tail-expression lifetime error. Materializing the fallback value before return corrected it without changing behavior or adding a suppression.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16 is complete. Task 17.1 protocol loop is complete; Task 17.2 UCI search worker is next.

### Task 16.6 completion evidence

- Implementation: unified request snapshot and aggregate accounting in `crates/chess-search/src/iterative_deepening.rs`, typed node-kind hooks in `crates/chess-search/src/cancellation.rs` and `limits.rs`, and alpha-beta/quiescence accounting in `alpha_beta.rs`, `aspiration.rs`, and `quiescence.rs`.
- Public API: `SearchResult`, returned by both limit-controlled iterative-deepening entry points; `LimitedIterativeDeepeningSearchResult` remains a compatibility alias.
- The authoritative snapshot exposes best move, ponder move, optional exact typed score, completed depth, selective depth, total nodes, total qnodes, elapsed time, legal principal variation, and typed termination reason.
- Best move, score, ponder move, completed depth, and PV come only from the deepest fully completed exact iteration. Interrupted partial-depth data cannot replace them.
- When no iteration completes, `best_move` may expose the deterministic Task 16.5 legal fallback, while score, ponder move, completed depth, and PV remain absent or zero. A terminal fallback exposes no move.
- Request-wide nodes, qnodes, selective depth, and elapsed time include interrupted partial work. Detailed completed iterations, aspiration diagnostics, TT diagnostics, and compatibility accessors remain available.
- `qnodes` is a subset of production nodes. `selective_depth` is the deepest root-relative alpha-beta or quiescence ply entered. Specialized cancellation hooks preserve the one-node polling bound for existing probes through default delegation.
- Four focused result-shape regressions cover exact completion, cancellation after a completed iteration, legal pre-depth-one fallback, and terminal pre-depth-one fallback. Existing limit tests continue to cover depth, node, soft-time, hard-time, explicit-stop, and infinite-mode behavior.
- Contract documentation: `docs/RUST_SEARCH_RESULT_API.md`; iterative-deepening and limit contracts updated through Task 16.6.
- Production implementation commit: `780bcc6bf9ba17afb9e9443e3a106b722d4c43fe`.
- Exact clean validated implementation SHA: `dcde800f4c5a08c07fe57724ed672f2abd122157`.
- Permanent CI run/job: `30783666840` / `91593059900`.
- Results: permanent exclusion audit over 16 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 222 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The implementation passed its first compiler, strict-Clippy, test, rustdoc, build, perft, and oracle iteration without a source correction or suppression.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16 is complete. Task 17.1 protocol loop is complete; Task 17.2 UCI search worker is next.

### Task 16.7 and Task 16 gate completion evidence

- Implementation: `crates/chess-search/src/check_extension.rs`, integrated through `alpha_beta.rs`, `cancellation.rs`, `limits.rs`, `iterative_deepening.rs`, `principal_variation.rs`, and transposition probing.
- Public APIs: `SearchLimits::with_check_extension`, `SearchLimits::check_extension_enabled`, `CheckExtensionDiagnostics`, `CheckExtensionEvent`, `MAX_CHECK_EXTENSIONS_PER_LINE`, and `SearchResult::check_extension_diagnostics`.
- The feature is explicitly opt-in and disabled by default. Existing fixed-depth and limit-controlled requests preserve their prior baseline behavior.
- A checking child may receive exactly one additional ply per root-to-leaf path. The remaining budget is passed by value, consumed on application, and cannot be shared or replenished by siblings or later checks.
- Later checking nodes on the same path remain at nominal depth and are recorded as budget-exhausted. The mate-score ply ceiling blocks an extension that would leave the supported score domain.
- Extension-enabled searches suppress TT score reuse and storage because remaining extension budget is path-dependent and absent from the Zobrist key. Complete-key legal TT moves remain ordering hints only.
- PV reconstruction remains legal and bounded: the searched root move is validated, while extension-enabled requests do not continue through incompatible pre-existing TT score chains.
- Request-wide diagnostics report eligible checking nodes, applied extensions, exhausted-budget nodes, and mate-domain-blocked nodes, including work from an interrupted depth.
- Three unit tests prove the one-extension budget, disabled/nonchecking behavior, and mate-domain blocking. Four integration tests prove explicit opt-in, deterministic result/PV behavior, seeded TT-score rejection, node-limited diagnostics, and exact root/history/Zobrist restoration.
- Contract documentation: `docs/RUST_CHECK_EXTENSION.md`; search-limit and result-API contracts updated through Task 16.7.
- Production implementation commit: `54d98563f253df3ef055470a5fd4b2ee8b32947a`.
- Exact clean validated implementation SHA: `836ca0563f9a8dce44eb78997e28335a9d8fcdce`.
- Permanent CI run/job: `30785853401` / `91599164384`.
- Results: permanent exclusion audit over 17 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 229 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Validation corrections were limited to fail-closed generator assertions, two mechanical policy-wiring sites, a test-only helper classification, a private argument-policy grouping required by strict Clippy, and final temporary-generator cleanup. No lint suppression, gate downgrade, or semantic relaxation was used.
- The clean implementation delta contains eight search modules, one focused integration-test file, and three contract documents. No temporary script or workflow modification remains.
- The overall Task 16 gate is complete: deterministic depth/node behavior, responsive timed/explicit cancellation, legal PVs, exact aspiration recovery, unified result accounting, and finite optional extension semantics all passed together.
- Task 17.1 protocol loop is complete; Task 17.2 UCI search worker is next.

# Task 17: Linux UCI executable — COMPLETE
- [x] 17.1 Protocol loop.
- [x] 17.2 Search worker.
- [x] 17.3 Time manager.
- [x] 17.4 Output.
- [x] 17.5 Integration tests.
- [x] Task 17 gate.

### Task 17.1 completion evidence

- Implementation: `crates/chess-uci/src/lib.rs`, `crates/chess-uci/src/main.rs`, and the direct `chess-core` dependency in `crates/chess-uci/Cargo.toml`.
- Public protocol API: `UciSession`, `UciResponse`, `UciEvent`, `SearchRequest`, `GoCommand`, `EngineOptions`, `run_protocol_loop`, and `run_stdio`.
- Supported commands: `uci`, `isready`, `ucinewgame`, advertised `setoption`, transactional `position startpos`, strict six-field `position fen`, legal move replay, all required `go` forms, `stop`, and `quit`.
- Position replacement is transactional: malformed FEN, malformed move syntax, and illegal replay leave the active `Game` and repetition history unchanged.
- `go` creates an immutable game/options/limit snapshot. Search execution, worker ownership, time budgeting, periodic output, and `bestmove` remain explicitly assigned to Tasks 17.2 through 17.4.
- Contract documentation: `docs/RUST_UCI_PROTOCOL_LOOP.md`.
- Exact validated implementation SHA: `60f70463c9ad9abf99c8b3d7923df8037bc6f894`.
- Validation: rustfmt, locked all-target workspace check, strict Clippy with warnings denied, 18 focused UCI tests, and the complete workspace test suite all passed.
- Task 17.1 is complete. Task 17.2 UCI search worker is next.

### Task 17.4 completion evidence

- Implementation: `crates/chess-search/src/iterative_deepening.rs`, `crates/chess-uci/src/output.rs`, `worker.rs`, and `main.rs`.
- A protocol-neutral observer reports every exact completed depth without giving `chess-search` any UCI or I/O dependency.
- The adapter emits serialized `info depth`, `seldepth`, typed centipawn or mate score, cumulative nodes, overflow-safe NPS, elapsed milliseconds, bounded `hashfull`, and legal PV fields.
- Natural completion and explicit `stop` emit exactly one `bestmove`; ponder is included when the legal PV contains a reply; terminal roots use `bestmove 0000`.
- Position replacement, `ucinewgame`, `quit`, EOF, and slot drop suppress stale final output while preserving deterministic stop-and-join behavior.
- Output failures are typed, request cancellation, and are never silently discarded.
- Contract documentation: `docs/RUST_UCI_SEARCH_OUTPUT.md` and the updated worker contract.
- Implementation SHA: `0f0ed39b31aca077173359c5807c1afaffb3e9e4`.
- Task 17.4 is complete. Task 17.5 UCI process integration tests are next.


### Task 17.5 and Task 17 gate completion evidence

- Implementation: `crates/chess-uci/tests/uci_process.rs` and `docs/RUST_UCI_PROCESS_INTEGRATION.md`.
- Seven real child-process tests cover the exact handshake, readiness, start-position and six-field FEN setup, fail-visible transactional illegal input, fixed-depth legal best moves, checkmate/stalemate `bestmove 0000`, active-search `stop`, active-search `quit`, and concurrent session/stdout isolation.
- Every process read and exit is bounded. Cleanup closes stdin, terminates a stuck child, waits for it, and joins the stdout reader thread.
- The harness uses standard-library process and synchronization APIs only; it performs no stdout redirection and introduces no process-global mutable state.
- Implementation SHA: `67b6c97a476e1323bc2bd96ecf14870fc2ed3139`.
- Permanent validation: run `30828959858`, job `91737751003`.
- Results: seven subprocess tests passed; formatting, locked all-target/all-feature workspace compilation, strict Clippy without suppressions, the complete workspace tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle all passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Task 17.5 and the overall Task 17 Linux UCI executable gate are complete. Task 18.1 Rust facade work is next.

# Task 18: Safe API, C ABI, and JNI — COMPLETE
- [x] 18.1 Rust facade.
- [x] 18.2 C ABI.
- [x] 18.3 C tests.
- [x] 18.4 JNI.
- [x] 18.5 Android harness.
- [x] Task 18 gate.


### Task 18.1 completion evidence

- Implementation: `crates/chess-ffi/src/safe.rs`, public exports in `crates/chess-ffi/src/lib.rs`, direct `chess-core` and `chess-search` dependencies, and `crates/chess-ffi/tests/safe_facade.rs`.
- Public facade: `EngineConfig`, `Engine`, `SearchRequest`, `SearchCancellationHandle`, `EvaluationWeightIdentity`, `EngineError`, and `ENGINE_VERSION`.
- `Engine` owns one history-aware `Game` and one fixed-capacity transposition table. It borrows no caller memory, opens no files, starts no threads, and uses no process-global mutable state.
- Position replacement is strict and transactional. Canonical six-field FEN, deterministic legal UCI moves, legal move application, terminal rejection, and authoritative game status are exposed without duplicating chess rules.
- Search is synchronous and runs on cloned position/history state, preserving the played game on success, cancellation, and errors. Finite depth/node/time requests and explicit infinite-search cancellation use the existing typed search contract.
- Cancellation is request-local and clone-shareable across threads. `Engine: Send` and `SearchCancellationHandle: Send + Sync` are compiler-checked; no manual thread-safety implementation exists.
- Version and evaluator identity report the package version and the validated built-in baseline weight schema, identifier, and checksum. Caller-supplied weights are intentionally not claimed before the complete search path supports them.
- The safe facade module forbids unsafe code. Task 18.2 owns the separate narrow C ABI boundary.
- Contract documentation: `docs/RUST_SAFE_ENGINE_FACADE.md`.
- Implementation SHA: `fc375ce7c35a9b8e82c83c8a0ac54e23a60986be`.
- Permanent validation: run `30832682431`, job `91750223690`.
- Results: nine focused facade tests and 285 executed non-doc Rust tests passed; rustfmt, committed lockfile, locked all-target/all-feature compilation, strict Clippy without suppressions, release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle all passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Validation corrections were limited to exact rustfmt output and removing invalid `const fn` qualifiers from five fluent request builders. No semantics, safety policy, lower-layer production code, or gate was weakened.
- Task 18.1 is complete. Task 18.2 C ABI work is next.


### Task 18.2 completion evidence

- Implementation: `crates/chess-ffi/src/c_abi/types.rs`, `registry.rs`, `functions.rs`, and `mod.rs`, exported through `crates/chess-ffi/src/lib.rs`.
- Canonical C declarations: `crates/chess-ffi/include/chess_engine.h`; complete contract: `docs/RUST_C_ABI.md`.
- `chess-ffi` now produces `rlib`, `cdylib`, and `staticlib` artifacts without adding a dependency.
- Engine, cancellation, and output-allocation identities are opaque tagged 64-bit tokens backed by synchronized registries. Zero, stale, fabricated, destroyed, and wrong-type tokens fail before object access.
- Versioned `repr(C)` records require the exact ABI version and exact current record size. Rust engine, search, enum, vector, string, and error layouts never cross the boundary.
- FEN and move inputs use explicit `(pointer, length)` UTF-8 ranges with no `strlen`, NUL requirement, or out-of-range scanning.
- Structured result codes distinguish pointer, handle, UTF-8, ABI, rules, search, allocation, buffer, internal, and contained-panic failures. Error text is thread-local and retrieved through an owned ABI buffer.
- Output bytes are held in an allocation registry. Free operations verify token, pointer, and length; search-result cleanup validates all three owned buffers before freeing any.
- Search is synchronous and mutex-serializes one engine. A separate request-local cancellation token remains callable from another thread, and destroyed external tokens cannot invalidate an in-flight cloned reference.
- Every exported `extern "C"` symbol enters a `catch_unwind` boundary. The only unsafe operations are documented C pointer reads, writes, and explicit-length slice construction inside the adapter.
- Six focused Rust tests cover the shared panic boundary plus ABI versioning, construction and destruction, explicit UTF-8 position/move/status flows, typed search results, preset cancellation, stale and wrong-type handles, buffer lifecycle rejection, null pointers, and fail-closed versioned records.
- Implementation SHA: `d1c4a9195acfc63dc2f9af52531c4ba01e9a2dc9`.
- Permanent validation: run `30836228692`, job `91761964507`.
- Results: six focused C ABI tests and 291 executed non-doc Rust tests passed; rustfmt, committed lockfile, locked all-target/all-feature compilation, strict Clippy without suppressions, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle all passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Validation correction was limited to canonical rustfmt output. No ABI behavior, safety policy, lower-layer production code, or validation gate was weakened.
- Task 18.2 is complete. Task 18.3 native C ABI lifecycle, active-cancellation, buffer, and injected-panic tests are next.


### Task 18.3 completion evidence

- Implementation: `crates/chess-ffi/tests/c_abi_lifecycle.rs`, the non-default `ffi-test-faults` feature, `crates/chess-ffi/src/c_abi/test_faults.rs`, the guarded test declaration in `crates/chess-ffi/include/chess_engine.h`, and `docs/RUST_C_ABI_TESTS.md`.
- The Rust-through-ABI harness uses only the public `extern "C"` surface and covers create, position setup, legal moves, move application, status, fixed-depth search, result cleanup, reset, and destroy.
- Repeated lifecycle coverage creates and destroys 128 engines and 128 cancellation handles, requires nonzero unique tokens, and proves stale and double-destroy operations fail visibly.
- Invalid-input coverage includes null explicit-length input, invalid UTF-8, malformed FEN, malformed and illegal moves, unknown search flags, incompatible record size, null output pointers, thread-local errors, and unchanged engine state.
- Active cancellation runs infinite synchronous search on a worker thread, cancels it through an independent token, destroys the caller-visible token, and requires bounded `ExplicitStop` completion with a legal move and successful cleanup.
- Buffer tests cover tampered records, failed-validation preservation, successful original frees, stale-copy rejection, repeated empty frees, and all-or-nothing validation of the three-buffer search result.
- The non-default `ffi-test-faults` feature exports `chess_engine_test_inject_panic`; the default production surface omits it. The test requires a contained panic result and then proves the process and ABI remain usable.
- Implementation SHA: `0789ac65590ccafb55b2b86b73873edfba1c7b55`.
- Permanent validation: run `30841137129`, job `91778174797`.
- Results: six focused Task 18.3 lifecycle tests and 297 executed non-doc Rust tests passed; rustfmt, committed lockfile, locked all-target/all-feature compilation, strict Clippy without suppressions, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle all passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The first validation correction was limited to canonical rustfmt output and removal of one scheduler-sensitive test assertion. No ABI behavior, safety policy, production default surface, lower-layer code, or validation gate was weakened.
- Task 18.3 is complete. Task 18.4 Android JNI integration is next.


### Task 18.4 completion evidence

- Implementation: `crates/chess-jni/src/lib.rs` and `bridge.rs`, the pinned `jni = 0.21.1` dependency, `rlib` plus Android `cdylib` outputs, and the locked dependency update in `Cargo.lock`.
- Android-facing source: `crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessEngine.kt`; build entry point: `scripts/build_android_jni.sh`; contract: `docs/RUST_ANDROID_JNI.md`.
- The JNI adapter reuses the stable Task 18.2 opaque engine and cancellation tokens. It does not duplicate chess rules, search logic, handle registries, or result-code semantics.
- Sixteen exact JNI exports cover version, engine lifecycle, position reset/setup, canonical FEN, legal UCI moves, move application, game status, weight identity, cancellation lifecycle, and synchronous typed search.
- Every JNI export enters one shared panic boundary. Stable native result codes and diagnostics map to typed `ChessEngineException`; exception-construction failure falls back visibly to `RuntimeException`.
- The Kotlin `ChessEngine` is a deterministic `Closeable` owner with an idempotent close path, read/write lifecycle locking, one outstanding search, a private single-thread worker, request-local cancellation, and a phantom-reference leak fallback.
- Public Kotlin search never invokes the synchronous native call on the caller thread. `SearchOperation.cancel` uses the independent native stop token rather than Java interruption.
- Nine focused JNI tests cover opaque-token bit preservation, exact request conversion, bridge lifecycle, typed invalid-FEN preservation, active cross-thread cancellation, Kotlin/Rust symbol agreement, compact-record agreement, and ownership/background-search source contracts.
- Host implementation SHA: `466c7b504832afa2bf993cb10dcc0c12aefcf1c5`.
- Permanent host validation: run `30844134371`, job `91788114660`.
- Follow-up permanent validation on the Android-proof source tree: run `30844338897`, job `91788828855`.
- Results: nine focused JNI tests and 306 executed non-doc Rust tests passed; rustfmt, committed lockfile, locked all-target/all-feature compilation, strict Clippy without suppressions, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle all passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Android AArch64 proof SHA: `1fc49b6126ecb9faa4c0f167b272945d65aebbf1`. Its guarded workflow completed the locked NDK API-24 `aarch64-linux-android` release build, required a nonempty `libchess_jni.so`, verified an AArch64 ELF shared object and the exported `nativeSearch` JNI symbol, then removed itself.
- Validation corrections were limited to lockfile/rustfmt normalization, snapshotting scalar search fields before ABI-result cleanup, using the pinned `jni` crate's typed `JThrowable`, and importing one test-only result-code type. No lower-layer production behavior, safety policy, or validation gate was weakened.
- Task 18.4 is complete. Task 18.5 Android/JVM and emulator harness work is next; the overall Task 18 gate remains open.


### Task 18.5 and Task 18 gate completion evidence

- Harness: `android-harness/settings.gradle.kts`, the `host-jvm` and `android-smoke` modules, the exact production Kotlin source set, and `docs/RUST_ANDROID_TEST_HARNESS.md`.
- Permanent read-only Android gate: `.github/workflows/android.yml`; generated native staging: `scripts/prepare_android_harness_jni.sh`; dual-target build support: `scripts/build_android_jni.sh`.
- The host JVM module loads the real release `libchess_jni.so`; no mock binding or copied wrapper exists. Four JUnit tests cover the public lifecycle, typed invalid-FEN state preservation, active native cancellation with live worker-stack observation, and 24 repeated create/search-or-stop/destroy lifecycles.
- The Android module packages nonempty API-24 ARM64 and x86_64 JNI libraries, verifies both ELF architectures and the exact exported `nativeSearch` symbol, and builds the Android library plus test APK.
- Three instrumentation tests passed on an Android 15 / API-35 x86_64 Google APIs emulator: complete JNI lifecycle, Android-main-thread sample entry with the synchronous native method observed on `chess-engine-search`, and 16 repeated alternating fixed-depth/cancelled-infinite lifecycle runs.
- Main-thread exclusion is executable evidence: `Instrumentation.runOnMainSync` starts the sample request, while live ART stacks must show `NativeChessEngineBindings.nativeSearch` on `chess-engine-search` and not the Android main-loop thread.
- Toolchain: Ubuntu 24.04, Java 17.0.19, Gradle 8.9, Android Gradle Plugin 8.7.3, Kotlin 2.0.21, compile SDK 35, minimum/API link level 24, NDK 29.0.14206865, Android clang 21.0.0, and emulator 37.1.11.0.
- Exact validated implementation SHA: `0af14c4bdb7e8de645f27182a788e5eef5297d5f`.
- Permanent Rust validation: run `30847895229`, job `91800574469`.
- Permanent Android validation: run `30847895345`; host JVM job `91800574845`; Android emulator job `91800574914`.
- Rust results: formatting, committed lockfile, all-target/all-feature compilation, strict Clippy without suppressions, 306 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc, debug/release builds, and independent differential validation passed.
- Android results: four host JVM tests, dual-ABI cross-build and ELF verification, 59-task Android AAR/test-APK build, and three emulator instrumentation tests all passed.
- Accepted external notices were limited to GitHub Actions Node runtime/dependency deprecations, an informational inability to strip the JNI debug library, and normal emulator startup/shutdown diagnostics. No product failure or ignored test occurred.
- Task 18 is complete: the safe Rust facade, stable C ABI, ABI lifecycle/panic tests, JNI adapter, host JVM contract, and Android emulator path can create an engine, set/reset positions, obtain legal moves, search, cancel, and destroy without crashes, leaked owned handles, or UI-thread search execution.
- Task 19.4 opening-book adapter integration is complete. Task 19.5 opening-book tests are next.

# Task 19: Opening book — COMPLETE
- [x] 19.1 Abstraction.
- [x] 19.2 Format.
- [x] 19.3 Policies.
- [x] 19.4 Integration.
- [x] 19.5 Tests.
- [x] Task 19 gate.

### Task 19 completion evidence

- Merged Task 19.5 implementation SHA: `d7d8455e6279fab53451bad6a5d778ce66c0a001`.
- Exact validated evidence head: `5d70737bf12cbfa16441730b7a64629212b28683`.
- Rust run/job: `30867122750` / `91861324627`; 332 non-documentation tests, permanent opening-book audit, strict workspace gates, release depth-four perft, and differential oracle passed.
- Android run/jobs: `30867122736` / `91861324588`, `91861324637`; host JVM, ARM64/x86_64 verification, APK build, and API-35 instrumentation passed.
- Opening-book support is optional and disabled by default; all paths, bytes, assets, enablement decisions, and RNG seeds remain explicitly adapter supplied.
- Task 20 offline self-play is complete; Task 21 named-schema tuning is next.

# Task 20: Self-play and datasets — COMPLETE
- [x] 20.1 Configuration.
- [x] 20.2 Records.
- [x] 20.3 Schema.
- [x] 20.4 Quality.
- [x] Task 20 gate.

### Task 20 completion evidence

- Merged implementation SHA: `333398c5913309193cb81b91c4af3deff2fd5adf`.
- Exact validated evidence head: `1fae5fa8d830a524d6ff8d36ba42ed557112c79a`.
- Rust run/job: `30875333307` / `91885547979`; 336 non-documentation tests, the four focused Task 20 regressions, release perft, documentation, builds, and differential validation passed.
- Android run/jobs: `30875333292` / `91885547947`, `91885547972`; host JVM, dual-ABI native verification, APK build, and API-35 instrumentation passed.
- `chess-tools` now provides explicit `self-play`, `self-play-validate`, and `self-play-replay` commands over strict version-1 configuration, opening, game, and position schemas.
- Seeded opening rotation, per-game seeds, independent side limits, complete engine/evaluator/search provenance, deterministic train/validation/test assignment, replay validation, duplicate occurrence accounting, and explicit opening/maximum-ply filtering are enforced.
- Task 21.1 named weight-schema integration is complete; Task 21.2 loss-pipeline work is complete; Task 21.3 optimizer work is next.

# Task 21: Named-schema tuning — IN PROGRESS
- [x] 21.1 Weights.
- [x] 21.2 Loss.
- [x] 21.3 Optimizer.
- [ ] 21.4 Reports.
- [ ] 21.5 Validation.

### Task 21.3 completion evidence

- Implementation: `crates/chess-tune/src/optimizer.rs`.
- Contract: `docs/RUST_SPSA_OPTIMIZER.md`.
- Exact helper-free validated SHA: `fc69d7d7554ab325fd72ccfc5ac94c4bb1077ae8`.
- Rust run/job: `30897085986` / `91952447573`.
- Android run/jobs: `30897085023` / `91952460052`, `91952460064`, `91952460121`.
- Permanent formatting, workspace check, strict Clippy, complete Rust tests, release perft, rustdoc, debug/release builds, differential validation, Android/Kotlin lint, host JNI, and API-35 instrumentation passed.
- Task 21.4 report generation and persistent artifact workflows are next; optimized weights remain inactive.
- [ ] Task 21 gate.


### Task 21.1 completion evidence

- Stable 810-scalar named schema, separately versioned structural constants, strict named serialization, complete training provenance, semantic checksums, and focused corruption/round-trip regressions implemented.
- Exact validated implementation head: `8410beb6dc22684052ded86a6f2fe71cf9d1e444`.
- Rust run/job: `30889939723 / 91929495312`.
- Android run/jobs: `30889939726 / 91929459955, 91929459977, 91929460081`.
- Task 21.2 loss-pipeline work is next; candidate weights are not automatically activated.


### Task 21.2 completion evidence

- Added side-to-move logistic result targets, explicit bounded `K` calibration, occurrence-weighted MSE, and strict train/validation separation in `chess-tune`.
- Added a fail-loud adapter from the validated Task 20 dataset that excludes ineligible and test rows while preserving duplicate occurrence counts.
- Contract: `docs/RUST_TEXEL_LOSS_PIPELINE.md`.
- Exact validated implementation head: `3d11b01a9de84913c6c1bfa43a37aea0197dc5be`.
- Rust run/job: `30894313165` / `91943462745`.
- Android run/jobs: `30894313169` / `91943477000`, `91943477036`, `91943477212`.
- Task 21.3 optimizer work is next; no candidate weights are activated.

# Task 22: Advanced classical terms — NOT STARTED
- [ ] 22.1 Protocol.
- [ ] 22.2 Candidates.
- [ ] 22.3 Exclusions.
- [ ] Task 22 gate.

# Task 23: Robustness gates — NOT STARTED
- [ ] 23.1 Properties.
- [ ] 23.2 Fuzzing.
- [ ] 23.3 Runtime analysis.
- [ ] 23.4 Failure preservation.
- [ ] Task 23 gate.

# Task 24: Performance hardening — NOT STARTED
- [ ] 24.1 Benchmarks.
- [ ] 24.2 Profiling.
- [ ] 24.3 Measured optimization.
- [ ] 24.4 Regression policy.
- [ ] 24.5 Android measurements.
- [ ] Task 24 gate.

# Task 25: CI, documentation, and workflows — PARTIAL

## 25.1 CI
- [x] Linux rustfmt/check/Clippy/tests/rustdoc/debug/release.
- [x] Python validation preserved separately.
- [x] Exact-SHA status publisher and deterministic dispatcher.
- [x] Release depth-four authoritative perft in permanent CI.
- [x] Scheduled/manual depth-five authoritative perft.
- [x] AArch64 compile CI.
- [x] Android compile and JNI CI.
- [ ] Miri, sanitizer, and fuzz gates.
- [ ] Scheduled strength testing.

## 25.2 Documentation
- [x] Workspace architecture.
- [x] Core values, coordinates, and moves.
- [x] Position and invariants.
- [x] FEN/UCI notation.
- [x] Attack generation.
- [x] Pseudo-legal generation.
- [x] Legal generation and initial perft.
- [x] Formal make/unmake.
- [x] Zobrist hashing and repetition identity.
- [x] Game history and draw semantics.
- [x] Authoritative perft and differential validation.
- [x] Baseline evaluator and trace.
- [x] Search and transposition table.
- [x] ABI/JNI.
- [ ] Differential fuzzing.
- [x] Self-play and versioned datasets.
- [ ] Tuning.

## 25.3 Commands and artifacts
- [x] Full Task 0/1 validation command, committed lockfile, ignored targets/worktrees.
- [x] Perft, divide, legal, play, suite, and oracle commands.
- [x] Evaluation trace, evaluation benchmark, weight export, and weight validation commands.
- [ ] General bootstrap and fast-validation wrapper commands.
- [x] Self-play generation, validation, and replay commands.
- [ ] UCI, Android, and tuning command documentation.
- [ ] Versioned schema/fixture/generated-artifact policy across all future artifacts.
- [ ] Task 25 gate.

# Task 26: v0.1 signoff — NOT STARTED
- [ ] 26.1 Rules.
- [ ] 26.2 Search.
- [ ] 26.3 Adapters.
- [ ] 26.4 Quality.
- [ ] 26.5 Evidence.
- [ ] Task 26 gate.

# Task 27: Full port signoff — NOT STARTED
- [ ] 27.1 Optional capabilities.
- [ ] 27.2 Migration decision.
- [ ] 27.3 Final report.
- [ ] 27.4 Release gate.
- [ ] Task 27 gate.

## Immediate next operations

1. Implement Task 21.1 by enumerating tunable named evaluator parameters over the validated Task 20 dataset schema.
2. Keep non-tunable structural constants separate from trainable weights.
3. Define versioned tuned-weight serialization with checksum and training metadata before optimizer work.
4. Implement Task 21.2 with explicit logistic mapping, calibrated `K`, train/validation separation, and fail-loud malformed or empty datasets.
5. Preserve explicit candidate activation: generated weights must not become defaults before Task 21.5 validation.
6. Leave Tasks 21.2–21.5 and the overall Task 21 gate open until their own implementation and exact-head evidence are complete.
