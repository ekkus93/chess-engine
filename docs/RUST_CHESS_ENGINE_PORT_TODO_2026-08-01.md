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
| 8 | **Active, not started** — formal make/unmake and incremental state. |
| 9–24 | **Not started**. |
| 25 | **Partial**. |
| 26–27 | **Not started**. |

---

# Tasks 0–7 — complete

- [x] Task 0 gate. Evidence: SHA `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`; run/job `30722127447` / `91427510964`; Python fast `1203`, slow `179`, perft `20/400/8902/197281`, UCI passed.
- [x] Task 1 gate. Evidence: SHA `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`; run/job `30722127447` / `91427510938`; strict workspace gates passed.
- [x] Task 2 gate. Evidence: implementation SHA `f29524599134a14d34121af2fefb04cd90e78df0`; run/job `30723748100` / `91431648799`; `16 passed`; closure `b5f462aa73a69efcdc847ee215231a5064029902` green.
- [x] Task 3 gate. Evidence: implementation SHA `00fd925dad807d822aa7878aade686ccc59ff9c5`; run/job `30724744784` / `91434236030`; `24 passed`; closure `5578682bb2a6df5173ff7593649ac55509c277cd` green.
- [x] Task 4 gate. Evidence: closure SHA `6cb975b35f4dbe898a0444b1b4c39778e89bcb40`; run/job `30726795562` / `91439860915`; `35 passed`.
- [x] Task 5 gate. Evidence: implementation `9922b0c725147fcabac3ce4c08f7c150c3ec6a1d`; run/job `30727440571` / `91441645867`; `42 passed`; closure `78e9315369ff4552e5500d1a820767a1fd228f29` green.
- [x] Task 6 gate. Evidence: implementation `0dcf512d404ae248d5a99651543d9d0ca9687699`; run/job `30727874051` / `91442826957`; `49 passed`; closure `cb7124c5712f6b3f8f4540e9e8fabaa2aa242bc0` green.
- [x] Task 7 gate. Implementation head `d6ea24eb6eeaea7b41dc309f866a5653aba687d5`, run/job `30729969574` / `91448384283`, `59 passed`; closure SHA `334dc79b3ce0cbc1e7b5096387218c90a8365204`, run/job `30730100518` / `91448776834`, all strict gates green.

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

# Task 8: Make/unmake and incremental state — ACTIVE, NOT STARTED
- [ ] 8.1 Public/internal formal undo structure and contract.
- [ ] 8.2 Complete application/unapplication paths.
- [ ] 8.3 Exact restoration tests for every move class.
- [ ] 8.4 Long randomized legal-sequence restoration.
- [ ] Task 8 gate.

# Task 9: Zobrist hashing and repetition identity — NOT STARTED
- [ ] 9.1 Deterministic tables.
- [ ] 9.2 Full hash.
- [ ] 9.3 Incremental updates.
- [ ] 9.4 Canonical en-passant identity.
- [ ] 9.5 Verification.
- [ ] Task 9 gate.

# Task 10: Game, history, and draw semantics — NOT STARTED
- [ ] 10.1 Game state.
- [ ] 10.2 Mate/stalemate.
- [ ] 10.3 Claimable draws.
- [ ] 10.4 Automatic draws.
- [ ] 10.5 Conservative dead-position logic.
- [ ] 10.6 Search history.
- [ ] Task 10 gate.

# Task 11: Authoritative perft and differential validation — NOT STARTED
- [ ] 11.1 Standard exact perft suite.
- [ ] 11.2 Slow perft.
- [ ] 11.3 Divide tool.
- [ ] 11.4 Differential oracle harness.
- [ ] 11.5 Corpus gate.
- [ ] Task 11 gate.

# Task 12: Baseline evaluator and trace — NOT STARTED
- [ ] 12.1 Score convention.
- [ ] 12.2 Baseline terms.
- [ ] 12.3 Efficiency.
- [ ] 12.4 Trace.
- [ ] 12.5 Named weights.
- [ ] 12.6 Exclusions.
- [ ] Task 12 gate.

# Task 13: Reference search and alpha-beta — NOT STARTED
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
- [ ] Release tests/perft, AArch64, Android, JNI, Miri, sanitizer, fuzz, nightly perft, and scheduled strength.

## 25.2 Documentation
- [x] Workspace architecture.
- [x] Core values, coordinates, and moves.
- [x] Position and invariants.
- [x] FEN/UCI notation.
- [x] Attack generation.
- [x] Pseudo-legal generation.
- [x] Legal generation and initial perft.
- [ ] Formal make/unmake, draws, hashing, search, TT, evaluation, ABI/JNI, differential perft/fuzz, self-play, and tuning.

## 25.3 Commands and artifacts
- [x] Full Task 0/1 validation command, committed lockfile, ignored targets/worktrees.
- [ ] Bootstrap, fast validation, perft CLI, UCI, Android, self-play, and tuning commands.
- [ ] Versioned schema/fixture/generated-artifact policy.
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

1. Extract Task 8's exact make/unmake and incremental-state contracts from the companion definitions.
2. Replace the Task 7 private validation-only undo path with the formal reusable Task 8 API without weakening proven legality or perft behavior.
3. Add exact restoration coverage for every move class and long deterministic randomized legal sequences.
4. Run all strict gates and close Task 8 only at an exact green SHA.
