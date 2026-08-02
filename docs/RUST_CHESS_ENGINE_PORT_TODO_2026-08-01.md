# Rust Chess Engine Port TODO — Live Status Tracker

**Status:** In progress  
**Updated:** 2026-08-02  
**Branch:** `rust-engine`  
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
| 15 | **Active** — Tasks 15.1–15.4 complete; Task 15.5 deterministic replacement next. |
| 16–24 | **Not started**. |
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
- Task 14 is complete. Tasks 15.1–15.4 are complete; Task 15.5 deterministic replacement is next.

# Task 15: Fixed-capacity transposition table — ACTIVE
- [x] 15.1 Entries.
- [x] 15.2 Storage.
- [x] 15.3 Mate normalization.
- [x] 15.4 Probes.
- [ ] 15.5 Replacement.
- [ ] 15.6 Diagnostics.
- [ ] Task 15 gate.

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
- Tasks 15.2–15.4 are complete; Task 15.5 deterministic replacement is next.

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
- Tasks 15.3 mate normalization and 15.4 probe semantics are complete; Task 15.5 deterministic replacement is next.

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
- The public probe boundary is complete, but production search still does not call it, store entries, select replacements, or activate TT move ordering; insertion and replacement remain Task 15.5.
- Results: workspace assets, permanent Task 14.5 exclusion audit over 12 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 171 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential oracle: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 15.4 safe probe semantics is complete; Task 15.5 deterministic replacement is next.


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

# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED
- [ ] 16.1 Iterative deepening.
- [ ] 16.2 Aspiration windows.
- [ ] 16.3 Principal variation.
- [ ] 16.4 Limits.
- [ ] 16.5 Cancellation.
- [ ] 16.6 Result API.
- [ ] 16.7 Optional extension.
- [ ] Task 16 gate.

# Task 17: Linux UCI executable — NOT STARTED
- [ ] 17.1 Protocol loop.
- [ ] 17.2 Search worker.
- [ ] 17.3 Time manager.
- [ ] 17.4 Output.
- [ ] 17.5 Integration tests.
- [ ] Task 17 gate.

# Task 18: Safe API, C ABI, and JNI — NOT STARTED
- [ ] 18.1 Rust facade.
- [ ] 18.2 C ABI.
- [ ] 18.3 C tests.
- [ ] 18.4 JNI.
- [ ] 18.5 Android harness.
- [ ] Task 18 gate.

# Task 19: Opening book — NOT STARTED
- [ ] 19.1 Abstraction.
- [ ] 19.2 Format.
- [ ] 19.3 Policies.
- [ ] 19.4 Integration.
- [ ] 19.5 Tests.
- [ ] Task 19 gate.

# Task 20: Self-play and datasets — NOT STARTED
- [ ] 20.1 Configuration.
- [ ] 20.2 Records.
- [ ] 20.3 Schema.
- [ ] 20.4 Quality.
- [ ] Task 20 gate.

# Task 21: Named-schema tuning — NOT STARTED
- [ ] 21.1 Weights.
- [ ] 21.2 Loss.
- [ ] 21.3 Optimizer.
- [ ] 21.4 Reports.
- [ ] 21.5 Validation.
- [ ] Task 21 gate.

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
- [ ] AArch64 compile CI.
- [ ] Android compile and JNI CI.
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
- [ ] Search and transposition table.
- [ ] ABI/JNI.
- [ ] Differential fuzzing.
- [ ] Self-play and tuning.

## 25.3 Commands and artifacts
- [x] Full Task 0/1 validation command, committed lockfile, ignored targets/worktrees.
- [x] Perft, divide, legal, play, suite, and oracle commands.
- [x] Evaluation trace, evaluation benchmark, weight export, and weight validation commands.
- [ ] General bootstrap and fast-validation wrapper commands.
- [ ] UCI, Android, self-play, and tuning commands.
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

1. Implement Task 15.5 deterministic transposition-table insertion and replacement.
2. Update an existing complete-key entry deterministically instead of creating duplicate same-key slots.
3. Prefer empty slots, then define depth-preferred and generation-aware collision replacement with stable tie-breaking.
4. Document exactly which colliding entry is displaced and add deterministic cluster-level regressions.
5. Preserve the Task 15.4 probe contract and keep repetition-sensitive score suppression unchanged.
6. Defer diagnostics and benchmarks to Task 15.6, and keep Task 16 iterative deepening, aspiration windows, PV reconstruction, and production limits outside Task 15.
