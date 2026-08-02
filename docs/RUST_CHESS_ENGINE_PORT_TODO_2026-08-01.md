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
- Every first-party rustfmt, compiler, Clippy, test, rustdoc, or build finding is a bug and must be fixed at source.
- The companion definitions file preserves the original detailed wording; this file is the authoritative live status.
- Update this file whenever implementation or evidence changes any task or subtask.

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
| 7 | **Implemented, CI pending** — legal filtering, special rules, reversible validation path, and initial perft are present. |
| 8–24 | **Not started**. |
| 25 | **Partial**. |
| 26–27 | **Not started**. |

---

# Tasks 0–6 — complete

- [x] Task 0 gate. Evidence: SHA `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`; run/job `30722127447` / `91427510964`; fast `1203`, slow `179`, perft `20/400/8902/197281`, UCI passed.
- [x] Task 1 gate. Evidence: SHA `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`; run/job `30722127447` / `91427510938`; all strict workspace gates passed.
- [x] Task 2 gate. Evidence: SHA `f29524599134a14d34121af2fefb04cd90e78df0`; run/job `30723748100` / `91431648799`; `16 passed`; closure `b5f462aa73a69efcdc847ee215231a5064029902` green.
- [x] Task 3 gate. Evidence: SHA `00fd925dad807d822aa7878aade686ccc59ff9c5`; run/job `30724744784` / `91434236030`; `24 passed`; closure `5578682bb2a6df5173ff7593649ac55509c277cd` green.
- [x] Task 4 gate. Evidence: SHA `6cb975b35f4dbe898a0444b1b4c39778e89bcb40`; run/job `30726795562` / `91439860915`; `35 passed`.
- [x] Task 5 gate. Evidence: implementation `9922b0c725147fcabac3ce4c08f7c150c3ec6a1d`; run/job `30727440571` / `91441645867`; `42 passed`; closure `78e9315369ff4552e5500d1a820767a1fd228f29` green.
- [x] Task 6 gate. Evidence: implementation `0dcf512d404ae248d5a99651543d9d0ca9687699`; run/job `30727874051` / `91442826957`; `49 passed`; closure `cb7124c5712f6b3f8f4540e9e8fabaa2aa242bc0` green.

---

# Task 7: Complete legal move generation and special rules — IMPLEMENTED, CI PENDING

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
- [x] Test the transit square after vacating the king's source square, preventing source-blocker attack bugs.
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
- [x] Starting-position depth 1 expected `20`.
- [x] Starting-position depth 2 expected `400`.
- [x] Starting-position depth 3 expected `8,902`.
- [x] Starting-position depth 4 expected `197,281`.
- [x] Deterministic root divide.
- [x] Exact position equality and invariant validation after legal generation, perft, and divide.
- [x] `docs/RUST_LEGAL_MOVE_GENERATION.md`.

## 7.7 CI gate
- [ ] Exact-head rustfmt pass.
- [ ] Exact-head Cargo check pass.
- [ ] Exact-head Clippy `-D warnings` pass.
- [ ] Exact-head unit tests with recorded count.
- [ ] Exact-head rustdoc `-D warnings` pass.
- [ ] Exact-head debug and release builds.
- [ ] Task 7 gate.

### Task 7 implementation evidence

- Shared bounded move-list mutation within `chess-core`: `9baf2e299551f39dbb4cbee2a1510e35d68ac6c8`.
- Legal generation/perft implementation: `beb6981520c16d07c2617a1c567eee7ed0a5212d`.
- Exact CI evidence remains pending.

---

# Task 8: Make/unmake and incremental state — NOT STARTED
- [ ] 8.1 Public/internal formal undo structure and contract.
- [ ] 8.2 Complete application/unapplication paths.
- [ ] 8.3 Exact restoration tests for every move class.
- [ ] 8.4 Long randomized legal-sequence restoration.
- [ ] Task 8 gate.

# Task 9: Zobrist hashing and repetition identity — NOT STARTED
- [ ] 9.1 deterministic tables.
- [ ] 9.2 full hash.
- [ ] 9.3 incremental updates.
- [ ] 9.4 canonical en-passant identity.
- [ ] 9.5 verification.
- [ ] Task 9 gate.

# Task 10: Game, history, and draw semantics — NOT STARTED
- [ ] 10.1 game state.
- [ ] 10.2 mate/stalemate.
- [ ] 10.3 claimable draws.
- [ ] 10.4 automatic draws.
- [ ] 10.5 conservative dead-position logic.
- [ ] 10.6 search history.
- [ ] Task 10 gate.

# Task 11: Authoritative perft and differential validation — NOT STARTED
- [ ] 11.1 standard exact perft suite.
- [ ] 11.2 slow perft.
- [ ] 11.3 divide tool.
- [ ] 11.4 differential oracle harness.
- [ ] 11.5 corpus gate.
- [ ] Task 11 gate.

# Task 12: Baseline evaluator and trace — NOT STARTED
- [ ] 12.1 score convention.
- [ ] 12.2 baseline terms.
- [ ] 12.3 efficiency.
- [ ] 12.4 trace.
- [ ] 12.5 named weights.
- [ ] 12.6 exclusions.
- [ ] Task 12 gate.

# Task 13: Reference search and alpha-beta — NOT STARTED
- [ ] 13.1 reference search.
- [ ] 13.2 negamax alpha-beta.
- [ ] 13.3 shallow equivalence.
- [ ] 13.4 immutability.
- [ ] 13.5 terminal fixtures.
- [ ] Task 13 gate.

# Task 14: Quiescence and ordering — NOT STARTED
- [ ] 14.1 quiescence.
- [ ] 14.2 tactical ordering.
- [ ] 14.3 quiet ordering.
- [ ] 14.4 correctness tests.
- [ ] 14.5 exclusions.
- [ ] Task 14 gate.

# Task 15: Fixed-capacity transposition table — NOT STARTED
- [ ] 15.1 entries.
- [ ] 15.2 storage.
- [ ] 15.3 mate normalization.
- [ ] 15.4 probes.
- [ ] 15.5 replacement.
- [ ] 15.6 diagnostics.
- [ ] Task 15 gate.

# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED
- [ ] 16.1 iterative deepening.
- [ ] 16.2 aspiration windows.
- [ ] 16.3 PV.
- [ ] 16.4 limits.
- [ ] 16.5 cancellation.
- [ ] 16.6 result API.
- [ ] 16.7 optional extension.
- [ ] Task 16 gate.

# Task 17: Linux UCI executable — NOT STARTED
- [ ] 17.1 protocol loop.
- [ ] 17.2 search worker.
- [ ] 17.3 time manager.
- [ ] 17.4 output.
- [ ] 17.5 integration tests.
- [ ] Task 17 gate.

# Task 18: Safe API, C ABI, and JNI — NOT STARTED
- [ ] 18.1 Rust facade.
- [ ] 18.2 C ABI.
- [ ] 18.3 C tests.
- [ ] 18.4 JNI.
- [ ] 18.5 Android harness.
- [ ] Task 18 gate.

# Task 19: Opening book — NOT STARTED
- [ ] 19.1 abstraction.
- [ ] 19.2 format.
- [ ] 19.3 policies.
- [ ] 19.4 integration.
- [ ] 19.5 tests.
- [ ] Task 19 gate.

# Task 20: Self-play and datasets — NOT STARTED
- [ ] 20.1 configuration.
- [ ] 20.2 records.
- [ ] 20.3 schema.
- [ ] 20.4 quality.
- [ ] Task 20 gate.

# Task 21: Named-schema tuning — NOT STARTED
- [ ] 21.1 weights.
- [ ] 21.2 loss.
- [ ] 21.3 optimizer.
- [ ] 21.4 reports.
- [ ] 21.5 validation.
- [ ] Task 21 gate.

# Task 22: Advanced classical terms — NOT STARTED
- [ ] 22.1 protocol.
- [ ] 22.2 candidates.
- [ ] 22.3 exclusions.
- [ ] Task 22 gate.

# Task 23: Robustness gates — NOT STARTED
- [ ] 23.1 properties.
- [ ] 23.2 fuzz.
- [ ] 23.3 runtime analysis.
- [ ] 23.4 failure preservation.
- [ ] Task 23 gate.

# Task 24: Performance hardening — NOT STARTED
- [ ] 24.1 benchmarks.
- [ ] 24.2 profiling.
- [ ] 24.3 measured optimization.
- [ ] 24.4 regression policy.
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
- [ ] 26.1 rules.
- [ ] 26.2 search.
- [ ] 26.3 adapters.
- [ ] 26.4 quality.
- [ ] 26.5 evidence.
- [ ] Task 26 gate.

# Task 27: Full port signoff — NOT STARTED
- [ ] 27.1 optional capabilities.
- [ ] 27.2 migration decision.
- [ ] 27.3 final report.
- [ ] 27.4 release gate.
- [ ] Task 27 gate.

## Immediate next operations

1. Run strict CI at the current exact Task 7 status head.
2. Fix every first-party formatting/compiler/Clippy/test/rustdoc/build finding at source.
3. Verify starting-position legal perft depths 1–4 and all special-rule regressions.
4. Record the exact green SHA, run, job, and test count.
5. Close Task 7 only after every gate is green.
6. Begin Task 8 only after exact closure verification.
