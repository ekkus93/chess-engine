# Rust Chess Engine Port TODO — Live Status Tracker

**Status:** In progress  
**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Specification:** `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md`  
**Detailed definitions:** `docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md`  
**Ralph status:** `docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md`

## Status rules

- `[x]` means complete with repository and, where required, exact-SHA CI evidence.
- `[ ]` means incomplete, unverified, deferred, blocked, or not started.
- GitHub Actions is the authoritative Rust execution environment.
- Every first-party rustfmt, compiler, Clippy, test, rustdoc, or build finding is a bug and must be fixed at source.
- The companion task-definition file preserves the full original wording; this file is the authoritative live status.
- Update this file whenever implementation or evidence changes a task or subtask.

## Program summary

| Task | Status |
|---:|---|
| 0 | **Complete** — frozen Python reference baseline captured and reviewed. |
| 1 | **Complete** — seven-crate workspace and strict CI validated. |
| 2 | **Complete** — core value types and coordinate contracts. |
| 3 | **Complete** — hybrid `Position` and invariants. |
| 4 | **Complete** — strict FEN and UCI move notation. |
| 5 | **Complete** — attack-generation infrastructure and exact-SHA CI. |
| 6–24 | **Not started**. |
| 25 | **Partial** — Linux strict CI and foundational documentation/workflows exist. |
| 26–27 | **Not started**. |

---

# Task 0: Establish the port baseline and decision record — COMPLETE

- [x] Freeze the pre-Rust Python source SHA.
- [x] Inventory Python rules, state, FEN, notation, search, evaluation, books, self-play, tuning, UCI, CLI/TUI, and excluded transcript guidance.
- [x] Record all known Python defects and architectural patterns Rust must not copy.
- [x] Capture fast and slow Python suites, perft, UCI smoke, environment, and source equivalence.
- [x] Task 0 gate.

**Evidence:** SHA `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`; run/job `30722127447` / `91427510964`; artifact `8825590703`; fast `1203 passed`; slow `179 passed`; perft `20/400/8902/197281`; UCI passed.

# Task 1: Cargo workspace and dependency boundaries — COMPLETE

- [x] Seven-crate Cargo workspace and documented dependency direction.
- [x] Rust 2021, MSRV 1.75, rustfmt, Clippy, denied warnings, and unsafe policy.
- [x] MIT metadata inherited by every crate; committed `Cargo.lock`.
- [x] Linux metadata, rustfmt, check, Clippy, tests, rustdoc, debug, and release gates.
- [x] Task 1 gate.

**Evidence:** SHA `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`; run/job `30722127447` / `91427510938`.

# Task 2: Core value types and coordinate contracts — COMPLETE

## 2.1–2.5
- [x] `Color`, `PieceKind`, compact `Piece`.
- [x] `Square` with canonical `a8 = 0` mapping and exhaustive conversion tests.
- [x] `Bitboard` primitives, iteration, and file-safe shifts.
- [x] Single packed `Move` identity with all move and promotion kinds.
- [x] Four-bit castling rights and typed checked counters.
- [x] Task 2 gate.

**Evidence:** implementation `878f9090af3d5fdee77ca87aaea24761a8df0312`; green candidate `f29524599134a14d34121af2fefb04cd90e78df0`; run/job `30723748100` / `91431648799`; `16 passed`; closure SHA/run/job `b5f462aa73a69efcdc847ee215231a5064029902` / `30723952076` / `91432161445`.

# Task 3: `Position` and invariants — COMPLETE

## 3.1 Hybrid representation
- [x] Private mailbox, piece bitboards, color occupancy, combined occupancy, king caches, side, castling, en-passant, counters, and hash placeholder.

## 3.2 Constructors
- [x] Crate-private builder, starting position, and exactly-one-king playable construction.
- [x] No weakened public analysis constructor.

## 3.3 Accessors and mutation boundary
- [x] Read-only state accessors and atomic internal add/remove/move primitives.
- [x] Sealed editor capability; no adapter mutation access.

## 3.4 Invariants
- [x] Mailbox/bitboard, occupancy, color overlap, king cache/count, en-passant, and combined-occupancy validation.
- [x] Zobrist recomputation explicitly deferred to Task 9.

## 3.5 Equality and clone
- [x] Complete logical equality and snapshot clone; clone-per-node search prohibited.

## 3.6 Gate
- [x] Representation/invariant documentation and transition/failure tests.
- [x] Exact-SHA rustfmt, check, Clippy, tests, rustdoc, debug, and release.
- [x] Task 3 gate.

**Evidence:** green SHA `00fd925dad807d822aa7878aade686ccc59ff9c5`; run/job `30724744784` / `91434236030`; `24 passed`; closure SHA `5578682bb2a6df5173ff7593649ac55509c277cd`.

# Task 4: Strict FEN and UCI move notation — COMPLETE

## 4.1 Structured errors
- [x] Public fail-loud `FenError` and `MoveParseError` categories with `Display` and `Error`.

## 4.2 Strict FEN parser
- [x] Six fields, eight ranks/files, piece syntax, pawn rank, active color, castling, en-passant, counters, and playable-king validation.
- [x] Parser uses crate-private construction only.

## 4.3 Canonical FEN serializer
- [x] Canonical placement compression, `KQkq` order, metadata serialization, and stable round trips.

## 4.4 UCI move notation
- [x] Syntax-only coordinate parsing, exact promotion suffixes, packed-move formatting, and generated-move matching.

## 4.5 Gate
- [x] Malformed-category tests, deterministic arbitrary-Unicode no-panic tests, round trips, and notation documentation.
- [x] Exact-SHA rustfmt, check, Clippy, tests, rustdoc, debug, and release.
- [x] Task 4 gate.

**Evidence:** green implementation `87e6b81c65340a692af0d800012910399d3ac75b`; evidence SHA `6cb975b35f4dbe898a0444b1b4c39778e89bcb40`; run/job `30726795562` / `91439860915`; `35 passed`; no first-party warnings.

# Task 5: Attack-generation infrastructure — COMPLETE

## 5.1 Leaper attacks
- [x] Precomputed pawn attacks for both colors and all squares.
- [x] Precomputed knight and king attacks for all squares.
- [x] Exhaustive all-square, edge, and corner oracle comparisons.

## 5.2 Sliding attacks
- [x] Audited rook and bishop scans for arbitrary occupancy.
- [x] Queen attacks as the union of rook and bishop attacks.
- [x] First blocker included; squares beyond it excluded.
- [x] Empty, full, patterned, edge, and explicit-blocker tests.
- [x] No premature magic-bitboard or PEXT optimization.

## 5.3 Geometric tables
- [x] Precomputed 64×64 ray, between, and line tables.
- [x] Explicit identical, adjacent, and non-collinear semantics.
- [x] All 4,096 square pairs compared with an independent coordinate oracle.

## 5.4 Position attack queries
- [x] `Position::attackers_to` and `Position::is_square_attacked`.
- [x] `Position::checkers_to_king`.
- [x] Absolute `Position::pinned_pieces` discovery.
- [x] Pawn attacks remain independent of target occupancy.

## 5.5 Differential fixtures
- [x] Representative full-position attack maps compared against an independent piece/path oracle.
- [x] Double-check, single-pin, two-blocker non-pin, edge, and pawn fixtures.

## 5.6 Documentation and gate
- [x] `docs/RUST_ATTACK_GENERATION.md` documents geometry, blocker, query, and pin semantics.
- [x] Large geometry arrays use shared static storage; no Clippy suppression.
- [x] Exact-SHA rustfmt pass.
- [x] Exact-SHA Cargo check pass.
- [x] Exact-SHA Clippy `-D warnings` pass.
- [x] Exact-SHA unit tests: `42 passed, 0 failed`.
- [x] Exact-SHA rustdoc `-D warnings` pass.
- [x] Exact-SHA debug and release builds.
- [x] Task 5 gate.

### Task 5 completion evidence

- Initial attached implementation: `af649ba40ecaa22c196f0bcbb726fe7a33fce48e`.
- rustfmt correction: `2b163fce25bb429f0a995b01e09863931917e46b`.
- Clippy/static-storage and oracle correction: `9922b0c725147fcabac3ce4c08f7c150c3ec6a1d`.
- CI run/job: `30727440571` / `91441645867`.
- Results: lockfile verification, metadata, rustfmt, Cargo check, Clippy with warnings denied, `42 passed`, rustdoc with warnings denied, debug build, and release build passed.
- First-party warnings: none.
- Accepted external notices: GitHub Action Node runtime and dependency `punycode` deprecation notices only.
- Deviations: none.

---

# Task 6: Pseudo-legal move generation — NOT STARTED
- [ ] 6.1 Pawn single/double pushes, captures, en-passant candidates, and four promotion identities.
- [ ] 6.2 Knight, bishop, rook, queen, and king moves without self-capture.
- [ ] 6.3 Castling candidates from rights and occupancy only; attack legality deferred to Task 7.
- [ ] 6.4 Bounded allocation-conscious move list.
- [ ] 6.5 Starting, edge, blocker, promotion, en-passant, and castling-candidate tests.
- [ ] Task 6 gate.

# Task 7: Complete legal move generation and special rules — NOT STARTED
- [ ] 7.1 King-safety filtering.
- [ ] 7.2 Check evasions.
- [ ] 7.3 Castling correctness, including transient king-square attacks.
- [ ] 7.4 En-passant discovered-check correctness.
- [ ] 7.5 Promotion correctness.
- [ ] 7.6 Initial legal perft.
- [ ] Task 7 gate.

# Task 8: Make/unmake and incremental state — NOT STARTED
- [ ] 8.1 Undo structure.
- [ ] 8.2 Move application/unapplication paths.
- [ ] 8.3 Exact restoration tests.
- [ ] 8.4 Long sequence restoration.
- [ ] Task 8 gate.

# Task 9: Zobrist hashing and repetition identity — NOT STARTED
- [ ] 9.1 Deterministic tables.
- [ ] 9.2 Full hash.
- [ ] 9.3 Incremental updates.
- [ ] 9.4 Canonical en-passant identity.
- [ ] 9.5 Verification tests.
- [ ] Task 9 gate.

# Task 10: `Game`, history, and draw semantics — NOT STARTED
- [ ] 10.1 Game state/history.
- [ ] 10.2 Mate/stalemate.
- [ ] 10.3 Claimable draws.
- [ ] 10.4 Automatic draws.
- [ ] 10.5 Conservative dead-position logic.
- [ ] 10.6 Search-facing history.
- [ ] Task 10 gate.

# Task 11: Authoritative perft and differential validation — NOT STARTED
- [ ] 11.1 Exact standard perft suite.
- [ ] 11.2 Slow perft.
- [ ] 11.3 Divide tool.
- [ ] 11.4 Differential oracle harness.
- [ ] 11.5 Corpus gate.
- [ ] Task 11 gate.

# Task 12: Baseline evaluator and trace — NOT STARTED
- [ ] 12.1 Score convention.
- [ ] 12.2 Baseline terms.
- [ ] 12.3 Efficient implementation.
- [ ] 12.4 Evaluation trace.
- [ ] 12.5 Named weight schema.
- [ ] 12.6 Exclusion audit.
- [ ] Task 12 gate.

# Task 13: Reference search and negamax alpha-beta — NOT STARTED
- [ ] 13.1 Reference search.
- [ ] 13.2 Negamax alpha-beta.
- [ ] 13.3 Shallow equivalence.
- [ ] 13.4 Search immutability.
- [ ] 13.5 Terminal fixtures.
- [ ] Task 13 gate.

# Task 14: Quiescence and move ordering — NOT STARTED
- [ ] 14.1 Quiescence.
- [ ] 14.2 Tactical ordering.
- [ ] 14.3 Quiet ordering.
- [ ] 14.4 Correctness tests.
- [ ] 14.5 Explicit exclusions.
- [ ] Task 14 gate.

# Task 15: Fixed-capacity transposition table — NOT STARTED
- [ ] 15.1 Entry design.
- [ ] 15.2 Storage layout.
- [ ] 15.3 Mate normalization.
- [ ] 15.4 Probe semantics.
- [ ] 15.5 Replacement policy.
- [ ] 15.6 Diagnostics/benchmarks.
- [ ] Task 15 gate.

# Task 16: Iterative deepening, PV, limits, cancellation — NOT STARTED
- [ ] 16.1 Iterative deepening.
- [ ] 16.2 Aspiration windows.
- [ ] 16.3 Principal variation.
- [ ] 16.4 Search limits.
- [ ] 16.5 Responsive cancellation.
- [ ] 16.6 Search result API.
- [ ] 16.7 Optional check extension.
- [ ] Task 16 gate.

# Task 17: Linux UCI executable — NOT STARTED
- [ ] 17.1 Protocol loop.
- [ ] 17.2 Search worker.
- [ ] 17.3 Time manager.
- [ ] 17.4 Output.
- [ ] 17.5 Integration tests.
- [ ] Task 17 gate.

# Task 18: Safe API, C ABI, and Android JNI — NOT STARTED
- [ ] 18.1 Safe Rust facade.
- [ ] 18.2 C ABI.
- [ ] 18.3 C ABI tests.
- [ ] 18.4 JNI.
- [ ] 18.5 Android harness.
- [ ] Task 18 gate.

# Task 19: Optional opening-book infrastructure — NOT STARTED
- [ ] 19.1 Abstraction.
- [ ] 19.2 Format.
- [ ] 19.3 Policies.
- [ ] 19.4 Adapter integration.
- [ ] 19.5 Tests.
- [ ] Task 19 gate.

# Task 20: Self-play and datasets — NOT STARTED
- [ ] 20.1 Configuration.
- [ ] 20.2 Game records.
- [ ] 20.3 Dataset schema.
- [ ] 20.4 Data quality.
- [ ] Task 20 gate.

# Task 21: Named-schema tuning — NOT STARTED
- [ ] 21.1 Weight integration.
- [ ] 21.2 Loss pipeline.
- [ ] 21.3 Optimizer.
- [ ] 21.4 Reports.
- [ ] 21.5 Candidate validation.
- [ ] Task 21 gate.

# Task 22: Advanced classical terms — NOT STARTED
- [ ] 22.1 Candidate protocol.
- [ ] 22.2 Candidate areas.
- [ ] 22.3 Explicit exclusions.
- [ ] Task 22 gate.

# Task 23: Property, fuzz, sanitizer, and robustness gates — NOT STARTED
- [ ] 23.1 Property tests.
- [ ] 23.2 Fuzz targets.
- [ ] 23.3 Runtime analysis.
- [ ] 23.4 Failure preservation.
- [ ] Task 23 gate.

# Task 24: Performance hardening and regression budgets — NOT STARTED
- [ ] 24.1 Baseline benchmarks.
- [ ] 24.2 Profiling.
- [ ] 24.3 Measurement-justified optimization.
- [ ] 24.4 Regression policy.
- [ ] 24.5 Android measurements.
- [ ] Task 24 gate.

# Task 25: CI, documentation, and developer workflows — PARTIAL

## 25.1 CI
- [x] Linux rustfmt/check/Clippy/tests/rustdoc/debug/release.
- [x] Python validation preserved separately.
- [x] Exact-SHA status publisher and deterministic dispatcher.
- [ ] Release tests/perft, AArch64, Android, JNI, Miri, sanitizer, fuzz, nightly perft, and scheduled strength.

## 25.2 Documentation
- [x] Workspace architecture.
- [x] Core values, coordinates, and move encoding.
- [x] Position representation/invariants.
- [x] Strict FEN/UCI notation.
- [x] Attack-generation contract.
- [ ] Move generation, make/unmake, draws, hashing, search, TT, evaluation, ABI/JNI, perft/fuzz, self-play, and tuning documentation.

## 25.3 Commands and artifacts
- [x] Full Task 0/1 validation command, committed lockfile, ignored targets/worktrees.
- [ ] Bootstrap, fast validation, perft, UCI, Android, self-play, and tuning commands.
- [ ] Versioned schema/fixture/generated-artifact policy.
- [ ] Task 25 gate.

# Task 26: v0.1 functional-engine signoff — NOT STARTED
- [ ] 26.1 Rules signoff.
- [ ] 26.2 Search signoff.
- [ ] 26.3 Adapter signoff.
- [ ] 26.4 Quality signoff.
- [ ] 26.5 Evidence report.
- [ ] Task 26 gate.

# Task 27: Full port-program signoff — NOT STARTED
- [ ] 27.1 Optional capabilities.
- [ ] 27.2 Migration decision.
- [ ] 27.3 Final implementation report.
- [ ] 27.4 Release gate.
- [ ] Task 27 gate.

## Immediate next operations

1. Verify this Task 5 closure commit at its exact SHA through strict CI.
2. Begin Task 6 only after the closure SHA is green.
3. Implement pseudo-legal generation with complete promotion identities, en-passant candidates, castling candidates, and bounded move storage.
4. Keep every Task 6 subtask synchronized during the next Ralph Loop.
