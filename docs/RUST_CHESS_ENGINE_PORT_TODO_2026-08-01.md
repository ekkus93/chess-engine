# Rust Chess Engine Port TODO — Live Status Tracker

**Status:** In progress  
**Updated:** 2026-08-01  
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
| 13 | **Active** — reference search and alpha-beta; implementation remains not started pending review-fix closure. |
| 14–24 | **Not started**. |
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

# Task 13: Reference search and alpha-beta — ACTIVE, NOT STARTED
- [ ] 13.1 Reference search.
- [ ] 13.2 Negamax alpha-beta.
- [ ] 13.3 Shallow equivalence.
- [ ] 13.4 Immutability.
- [ ] 13.5 Terminal fixtures.
- [ ] Task 13 gate.

# Task 14: Quiescence and ordering — NOT STARTED
- [ ] 14.1 Quiescence.
- [ ] 14.2 Tactical ordering.
- [ ] 14.3 Quiet ordering.
- [ ] 14.4 Correctness tests.
- [ ] 14.5 Exclusions.
- [ ] Task 14 gate.

# Task 15: Fixed-capacity transposition table — NOT STARTED
- [ ] 15.1 Entries.
- [ ] 15.2 Storage.
- [ ] 15.3 Mate normalization.
- [ ] 15.4 Probes.
- [ ] 15.5 Replacement.
- [ ] 15.6 Diagnostics.
- [ ] Task 15 gate.

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

1. Complete and validate `docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md`.
2. Confirm the search-safe legal-token API, game root replacement, divide timing, FEN policy, and tracker cleanup on an exact green SHA.
3. Begin Task 13 reference search only after the review-fix gate passes.
4. Implement no-prune reference search before alpha-beta.
5. Validate terminal scoring, line repetition, and exact search immutability before Task 13 completion.
