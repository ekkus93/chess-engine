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
- The companion definitions file preserves the full original wording; this file is the authoritative live status.

## Program summary

| Task | Status |
|---:|---|
| 0 | **Complete** — Python reference baseline. |
| 1 | **Complete** — Cargo workspace and strict CI. |
| 2 | **Complete** — core value types. |
| 3 | **Complete** — `Position` and invariants. |
| 4 | **Complete** — strict FEN and UCI notation. |
| 5 | **Complete** — attack generation. |
| 6 | **Implemented, CI pending** — pseudo-legal generation and bounded move storage are present. |
| 7–24 | **Not started**. |
| 25 | **Partial**. |
| 26–27 | **Not started**. |

---

# Completed tasks 0–5

## Task 0 — COMPLETE
- [x] Frozen Python source/inventory/defect record.
- [x] Fast and slow suites, perft, UCI smoke, environment, and evidence artifact.
- [x] Task 0 gate.

**Evidence:** SHA `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`; run/job `30722127447` / `91427510964`; fast `1203`; slow `179`; perft `20/400/8902/197281`; UCI passed.

## Task 1 — COMPLETE
- [x] Seven-crate workspace, dependency boundaries, toolchain/lint/unsafe/license policy, lockfile, and Linux strict CI.
- [x] Task 1 gate.

**Evidence:** SHA `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`; run/job `30722127447` / `91427510938`.

## Task 2 — COMPLETE
- [x] 2.1 color/piece values.
- [x] 2.2 square mapping/conversions.
- [x] 2.3 bitboards.
- [x] 2.4 packed move identity.
- [x] 2.5 castling rights and typed counters.
- [x] Task 2 gate.

**Evidence:** green SHA `f29524599134a14d34121af2fefb04cd90e78df0`; run/job `30723748100` / `91431648799`; `16 passed`; closure `b5f462aa73a69efcdc847ee215231a5064029902` green.

## Task 3 — COMPLETE
- [x] 3.1 hybrid representation.
- [x] 3.2 validated constructors.
- [x] 3.3 read-only accessors and sealed mutation boundary.
- [x] 3.4 redundant-state invariants.
- [x] 3.5 logical equality and snapshot clone.
- [x] Documentation and Task 3 gate.

**Evidence:** SHA `00fd925dad807d822aa7878aade686ccc59ff9c5`; run/job `30724744784` / `91434236030`; `24 passed`; closure `5578682bb2a6df5173ff7593649ac55509c277cd` green.

## Task 4 — COMPLETE
- [x] 4.1 structured FEN/UCI errors.
- [x] 4.2 strict six-field FEN parser.
- [x] 4.3 canonical FEN serializer.
- [x] 4.4 syntax-only UCI notation and packed-move formatting.
- [x] 4.5 malformed/round-trip/no-panic tests and documentation.
- [x] Task 4 gate.

**Evidence:** SHA `6cb975b35f4dbe898a0444b1b4c39778e89bcb40`; run/job `30726795562` / `91439860915`; `35 passed`.

## Task 5 — COMPLETE
- [x] 5.1 precomputed pawn/knight/king attacks.
- [x] 5.2 arbitrary-occupancy rook/bishop/queen attacks.
- [x] 5.3 static 64×64 ray/between/line geometry.
- [x] 5.4 attackers/checkers/attacked-square/absolute-pin queries.
- [x] 5.5 independent differential fixtures.
- [x] Documentation and Task 5 gate.

**Evidence:** implementation SHA `9922b0c725147fcabac3ce4c08f7c150c3ec6a1d`; run/job `30727440571` / `91441645867`; `42 passed`; exact closure SHA `78e9315369ff4552e5500d1a820767a1fd228f29`, run/job `30727553897` / `91441947625`, green.

---

# Task 6: Pseudo-legal move generation — IMPLEMENTED, CI PENDING

## 6.1 Pawn moves
- [x] Single pushes require an empty destination.
- [x] Double pushes require the start rank plus empty intermediate/destination squares.
- [x] Captures exclude friendly pieces and kings.
- [x] En-passant target-geometry candidates.
- [x] Four quiet promotion identities.
- [x] Four capture-promotion identities.

## 6.2 Piece moves
- [x] Knights.
- [x] Bishops.
- [x] Rooks.
- [x] Queens.
- [x] Kings without final attack filtering.
- [x] No self-captures or king-capture moves.

## 6.3 Castling candidates
- [x] Rights, king/rook home placement, and empty path required.
- [x] King-in-check and attacked transit/destination checks intentionally deferred to Task 7.

## 6.4 Move list
- [x] Fixed 256-entry stack-backed `MoveList`.
- [x] No per-move heap allocation.
- [x] Structured fail-loud `MoveListOverflow` rather than truncation.
- [x] Deterministic pawn/knight/bishop/rook/queen/king/castling order.
- [x] Deterministic ascending source/destination order and N/B/R/Q promotion order.

## 6.5 Tests and documentation
- [x] Exact starting-position count and order.
- [x] Quiet promotions and capture underpromotions.
- [x] Edge pawns and knights.
- [x] Sliding blockers and capture identity.
- [x] En-passant candidate geometry.
- [x] Castling rights/pieces/paths versus deferred safety.
- [x] Stack-storage/capacity contract.
- [x] `docs/RUST_PSEUDO_LEGAL_MOVE_GENERATION.md`.

## 6.6 CI gate
- [ ] Exact-head rustfmt pass.
- [ ] Exact-head Cargo check pass.
- [ ] Exact-head Clippy `-D warnings` pass.
- [ ] Exact-head unit tests with recorded count.
- [ ] Exact-head rustdoc `-D warnings` pass.
- [ ] Exact-head debug and release builds.
- [ ] Task 6 gate.

**Implementation commit:** `0d8f063dbc9cd096e4e8796c07414bb7d0b4be02`.

---

# Task 7: Complete legal generation and special rules — NOT STARTED
- [ ] 7.1 king-safety filtering.
- [ ] 7.2 check evasions.
- [ ] 7.3 castling correctness.
- [ ] 7.4 en-passant correctness.
- [ ] 7.5 promotion correctness.
- [ ] 7.6 initial legal perft.
- [ ] Task 7 gate.

# Task 8: Make/unmake and incremental state — NOT STARTED
- [ ] 8.1 undo structure.
- [ ] 8.2 apply/unapply paths.
- [ ] 8.3 restoration tests.
- [ ] 8.4 long-sequence restoration.
- [ ] Task 8 gate.

# Task 9: Zobrist hashing and repetition identity — NOT STARTED
- [ ] 9.1 deterministic tables.
- [ ] 9.2 full hash.
- [ ] 9.3 incremental updates.
- [ ] 9.4 canonical en-passant identity.
- [ ] 9.5 verification.
- [ ] Task 9 gate.

# Task 10: Game/history/draw semantics — NOT STARTED
- [ ] 10.1 game state.
- [ ] 10.2 mate/stalemate.
- [ ] 10.3 claimable draws.
- [ ] 10.4 automatic draws.
- [ ] 10.5 conservative dead-position logic.
- [ ] 10.6 search history.
- [ ] Task 10 gate.

# Task 11: Perft and differential validation — NOT STARTED
- [ ] 11.1 exact suite.
- [ ] 11.2 slow perft.
- [ ] 11.3 divide.
- [ ] 11.4 oracle harness.
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
- [ ] 15.2 layout.
- [ ] 15.3 mate normalization.
- [ ] 15.4 probes.
- [ ] 15.5 replacement.
- [ ] 15.6 diagnostics.
- [ ] Task 15 gate.

# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED
- [ ] 16.1 iterative deepening.
- [ ] 16.2 aspirations.
- [ ] 16.3 PV.
- [ ] 16.4 limits.
- [ ] 16.5 cancellation.
- [ ] 16.6 result API.
- [ ] 16.7 optional extension.
- [ ] Task 16 gate.

# Task 17: Linux UCI executable — NOT STARTED
- [ ] 17.1 loop.
- [ ] 17.2 worker.
- [ ] 17.3 time manager.
- [ ] 17.4 output.
- [ ] 17.5 integration tests.
- [ ] Task 17 gate.

# Task 18: Safe API, C ABI, JNI — NOT STARTED
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
- [ ] Release tests/perft, AArch64, Android, JNI, Miri, sanitizer, fuzz, nightly perft, scheduled strength.

## 25.2 Documentation
- [x] Workspace architecture.
- [x] Core values/coordinates/moves.
- [x] Position/invariants.
- [x] FEN/UCI notation.
- [x] Attack generation.
- [x] Pseudo-legal move generation.
- [ ] Legal generation, make/unmake, draws, hashing, search, TT, evaluation, ABI/JNI, perft/fuzz, self-play, tuning.

## 25.3 Commands/artifacts
- [x] Full Task 0/1 validation command, committed lockfile, ignored targets/worktrees.
- [ ] Bootstrap, fast validation, perft, UCI, Android, self-play, tuning commands.
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

1. Run strict CI at the current exact Task 6 status head.
2. Fix every first-party formatting/compiler/Clippy/test/rustdoc/build finding at source.
3. Record the exact green SHA, run, job, and test count.
4. Close Task 6 only after every gate is green.
5. Begin Task 7 only after exact closure verification.
