# Rust Chess Engine Port TODO — Live Status Tracker

**Status:** In progress  
**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Specification:** `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md`  
**Detailed definitions:** `docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md`

## Status rules

- `[x]` is complete with repository or CI evidence.
- `[ ]` is incomplete, blocked, unverified, or not started.
- GitHub Actions is the authoritative Rust execution environment.
- Every first-party warning, lint finding, formatting failure, test failure, or rustdoc warning is a bug and must be fixed at source.
- Update this tracker whenever any task or subtask status changes.

## Program summary

| Task | Status |
|---:|---|
| 0 | **Complete** — frozen Python baseline captured and reviewed. |
| 1 | **Complete** — seven-crate workspace and strict CI validated. |
| 2 | **Implemented; CI pending** — core value types and exhaustive tests committed. |
| 3–24 | **Not started**. |
| 25 | **Partial** — Linux strict CI and initial documentation exist. |
| 26–27 | **Not started**. |

# Task 0: Port baseline and decision record — COMPLETE

## 0.1 Python baseline
- [x] Frozen source SHA recorded: `f743013a84173b551eac5488c638cb48098ec6d0`.
- [x] Fast suite captured: `1203 passed, 179 deselected in 43.92s`.
- [x] Slow suite captured: `179 passed, 1203 deselected in 2449.87s (0:40:49)`.
- [x] Starting-position perft captured: `20`, `400`, `8902`, `197281`.
- [x] UCI handshake and depth-one search captured.
- [x] Stockfish integration prerequisite installed and validated.
- [x] Historical strength/self-play artifacts recorded as comparison-only evidence.

## 0.2 Python-reference inventory
- [x] Rules/board state, FEN/notation, search, evaluation, book, self-play/tuning, UCI, CLI/TUI, and transcript guidance inventoried.
- [x] Retained concepts mapped to Rust milestones.
- [x] Excluded modules explicitly recorded.

## 0.3 Defects Rust must not copy
- [x] Dead-position shortcuts; castling transit blocker bug; clone-per-child; string keys; raw en-passant repetition identity.
- [x] Permissive FEN; implicit queen promotion; multiple move identities; unbounded dictionary TT; missing mate normalization.
- [x] Root tie-break/bound interaction; automatic weight loading; global UCI state; transcript-specific patches.

## 0.4 Evidence
- [x] CI run `30722127447`, commit `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`.
- [x] Python job `91427510964`.
- [x] Artifact `8825590703`, SHA-256 `ed44f43246e5176479825a3fef25aee6595b91af573453ad74f367a6c634d900`.
- [x] Python tree matched the frozen source exactly.

**Task 0 gate:** **CLOSED.**

# Task 1: Cargo workspace and dependency boundaries — COMPLETE

## 1.1 Workspace
- [x] Root workspace and crates: core, search, UCI, FFI, JNI, tools, tune.
- [x] Responsibilities and allowed dependency direction documented.
- [x] Feature-empty crates build cleanly.

## 1.2 Policy
- [x] Rust 2021; MSRV 1.75; stable rustfmt and Clippy.
- [x] `#![forbid(unsafe_code)]` in core and search.
- [x] First-party warnings denied.
- [x] MIT metadata inherited by every crate.
- [x] Reviewed `Cargo.lock` committed.

## 1.3 Architecture and CI
- [x] Core/search dependency boundaries enforced.
- [x] Adapter crates remain outward-facing.
- [x] Architecture document committed.
- [x] Local worktree gitlinks removed and ignored.
- [x] Metadata, format, check, Clippy, tests, rustdoc, debug, and release gates passed.
- [x] CI run `30722127447`, Rust job `91427510938`, exact SHA `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`.

**Task 1 gate:** **CLOSED.**

# Task 2: Core value types and coordinate contracts — IMPLEMENTED; CI PENDING

## 2.1 Color and pieces
- [x] `Color` stable indexing, `opposite()`, pawn direction, home/start/promotion rows.
- [x] `PieceKind` has six non-empty kinds.
- [x] Compact `Piece { color, kind }` has no square.
- [x] FEN conversion/display and size tests.

## 2.2 Square
- [x] Validated transparent `Square(u8)`.
- [x] Mapping: `a8=0`, `h8=7`, `a1=56`, `h1=63`.
- [x] File, row, rank, and index accessors.
- [x] Algebraic parse/format.
- [x] All 64 squares round-trip tested.
- [x] Unchecked construction is crate-private.

## 2.3 Bitboard
- [x] Transparent `Bitboard(u64)`.
- [x] Set, clear, contains, pop-LSB, iteration, count, emptiness, and bitwise operations.
- [x] File/rank masks and non-wrapping cardinal/diagonal shifts.
- [x] Basic and edge tests.

## 2.4 Move encoding
- [x] One packed `Move(u16)` internal identity.
- [x] Source, destination, promotion, and semantic kind encoded.
- [x] Equality/hash/order value semantics.
- [x] All 14 move kinds round-trip tested.
- [x] Eight quiet/capture promotion identities remain distinct.
- [x] Packed layout is private and not an external ABI.

## 2.5 Castling and counters
- [x] Four-bit `CastlingRights` with color/side query and clearing helpers.
- [x] Typed `HalfmoveClock` and one-based `FullmoveNumber`.
- [x] Reset, checked increment, and overflow tests.

## 2.6 Documentation and gate
- [x] Core value/coordinate/move-layout document.
- [x] Compact representation tests.
- [ ] rustfmt exact-SHA pass.
- [ ] Cargo check exact-SHA pass.
- [ ] Clippy `-D warnings` exact-SHA pass.
- [ ] Unit tests exact-SHA pass.
- [ ] rustdoc exact-SHA pass.
- [ ] Debug/release exact-SHA builds.

**Task 2 gate:** **OPEN pending CI.**

# Task 3: `Position` and invariants — NOT STARTED
- [ ] 3.1 Hybrid representation.
- [ ] 3.2 Constructors.
- [ ] 3.3 Accessors/mutation boundary.
- [ ] 3.4 Invariant checker.
- [ ] 3.5 Equality/clone policy.
- [ ] Gate.

# Task 4: Strict FEN and UCI move notation — NOT STARTED
- [ ] 4.1 Structured errors.
- [ ] 4.2 Strict FEN parser.
- [ ] 4.3 Canonical serializer.
- [ ] 4.4 UCI moves.
- [ ] 4.5 Property tests.
- [ ] Gate.

# Task 5: Attack generation — NOT STARTED
- [ ] 5.1 Leapers.
- [ ] 5.2 Sliders.
- [ ] 5.3 Geometry tables.
- [ ] 5.4 Position queries.
- [ ] 5.5 Differential fixtures.
- [ ] Gate.

# Task 6: Pseudo-legal generation — NOT STARTED
- [ ] 6.1 Pawns.
- [ ] 6.2 Pieces.
- [ ] 6.3 Castling candidates.
- [ ] 6.4 Move list.
- [ ] 6.5 Tests.
- [ ] Gate.

# Task 7: Legal generation and special rules — NOT STARTED
- [ ] 7.1 King safety.
- [ ] 7.2 Check evasions.
- [ ] 7.3 Castling.
- [ ] 7.4 En passant.
- [ ] 7.5 Promotions.
- [ ] 7.6 Initial perft.
- [ ] Gate.

# Task 8: Make/unmake — NOT STARTED
- [ ] 8.1 Undo structure.
- [ ] 8.2 Application paths.
- [ ] 8.3 Restoration tests.
- [ ] 8.4 Sequence restoration.
- [ ] Gate.

# Task 9: Zobrist/repetition identity — NOT STARTED
- [ ] 9.1 Tables.
- [ ] 9.2 Full hash.
- [ ] 9.3 Incremental updates.
- [ ] 9.4 Canonical en passant.
- [ ] 9.5 Verification.
- [ ] Gate.

# Task 10: Game/history/draws — NOT STARTED
- [ ] 10.1 Game state.
- [ ] 10.2 Mate/stalemate.
- [ ] 10.3 Claimable draws.
- [ ] 10.4 Automatic draws.
- [ ] 10.5 Dead-position logic.
- [ ] 10.6 Search history.
- [ ] Gate.

# Task 11: Perft/differential validation — NOT STARTED
- [ ] 11.1 Exact suite.
- [ ] 11.2 Slow perft.
- [ ] 11.3 Divide.
- [ ] 11.4 Oracle harness.
- [ ] 11.5 Corpus gate.
- [ ] Gate.

# Task 12: Evaluation — NOT STARTED
- [ ] 12.1 Score convention.
- [ ] 12.2 Baseline terms.
- [ ] 12.3 Efficiency.
- [ ] 12.4 Trace.
- [ ] 12.5 Named weights.
- [ ] 12.6 Exclusion audit.
- [ ] Gate.

# Task 13: Reference search/alpha-beta — NOT STARTED
- [ ] 13.1 Reference search.
- [ ] 13.2 Negamax alpha-beta.
- [ ] 13.3 Equivalence.
- [ ] 13.4 Immutability.
- [ ] 13.5 Terminal fixtures.
- [ ] Gate.

# Task 14: Quiescence/ordering — NOT STARTED
- [ ] 14.1 Quiescence.
- [ ] 14.2 Tactical ordering.
- [ ] 14.3 Quiet ordering.
- [ ] 14.4 Correctness tests.
- [ ] 14.5 Exclusions.
- [ ] Gate.

# Task 15: Transposition table — NOT STARTED
- [ ] 15.1 Entries.
- [ ] 15.2 Storage.
- [ ] 15.3 Mate normalization.
- [ ] 15.4 Probe semantics.
- [ ] 15.5 Replacement.
- [ ] 15.6 Diagnostics/benchmarks.
- [ ] Gate.

# Task 16: Iterative deepening/limits — NOT STARTED
- [ ] 16.1 Iterative deepening.
- [ ] 16.2 Aspiration windows.
- [ ] 16.3 PV.
- [ ] 16.4 Limits.
- [ ] 16.5 Cancellation.
- [ ] 16.6 Result API.
- [ ] 16.7 Check extension.
- [ ] Gate.

# Task 17: Linux UCI — NOT STARTED
- [ ] 17.1 Loop.
- [ ] 17.2 Worker.
- [ ] 17.3 Time manager.
- [ ] 17.4 Output.
- [ ] 17.5 Integration tests.
- [ ] Gate.

# Task 18: Safe API/C ABI/JNI — NOT STARTED
- [ ] 18.1 Safe facade.
- [ ] 18.2 C ABI.
- [ ] 18.3 C tests.
- [ ] 18.4 JNI.
- [ ] 18.5 Android harness.
- [ ] Gate.

# Task 19: Opening book — NOT STARTED
- [ ] 19.1 Abstraction.
- [ ] 19.2 Format.
- [ ] 19.3 Policies.
- [ ] 19.4 Integration.
- [ ] 19.5 Tests.
- [ ] Gate.

# Task 20: Self-play/datasets — NOT STARTED
- [ ] 20.1 Configuration.
- [ ] 20.2 Records.
- [ ] 20.3 Schema.
- [ ] 20.4 Quality.
- [ ] Gate.

# Task 21: Tuning — NOT STARTED
- [ ] 21.1 Weight integration.
- [ ] 21.2 Loss.
- [ ] 21.3 Optimizer.
- [ ] 21.4 Reports.
- [ ] 21.5 Validation.
- [ ] Gate.

# Task 22: Advanced classical terms — NOT STARTED
- [ ] 22.1 Protocol.
- [ ] 22.2 Candidate areas.
- [ ] 22.3 Exclusions.
- [ ] Gate.

# Task 23: Robustness — NOT STARTED
- [ ] 23.1 Properties.
- [ ] 23.2 Fuzzing.
- [ ] 23.3 Runtime analysis.
- [ ] 23.4 Failure preservation.
- [ ] Gate.

# Task 24: Performance — NOT STARTED
- [ ] 24.1 Benchmarks.
- [ ] 24.2 Profiling.
- [ ] 24.3 Measured optimization.
- [ ] 24.4 Regression policy.
- [ ] 24.5 Android measurements.
- [ ] Gate.

# Task 25: CI/docs/workflows — PARTIAL

## 25.1 CI
- [x] Linux debug tests, release build, all-target Clippy, rustdoc, lockfile verification, suppression rejection.
- [x] Python validation preserved separately.
- [x] Exact-SHA status publishing and deterministic dispatch.
- [ ] Release tests/perft, AArch64, Android, JNI, Miri, sanitizer, fuzz, nightly perft, scheduled strength.

## 25.2 Documentation
- [x] Workspace architecture.
- [x] Coordinates/core values/packed move layout.
- [ ] Position, make/unmake, FEN, draws, hashing, search, TT, evaluation, UCI, ABI, Android, perft/fuzz, self-play/tuning docs.

## 25.3 Commands/artifacts
- [x] Full Task 0/1 command; `target/` and local worktrees ignored; lockfile versioned.
- [ ] Bootstrap, fast validation, perft, UCI, Android, self-play, tuning commands.
- [ ] Future schema/fixture and generated-artifact policies.

**Task 25 gate:** **OPEN.**

# Task 26: v0.1 signoff — NOT STARTED
- [ ] 26.1 Rules.
- [ ] 26.2 Search.
- [ ] 26.3 Adapters.
- [ ] 26.4 Quality.
- [ ] 26.5 Evidence report.
- [ ] Gate.

# Task 27: Full port signoff — NOT STARTED
- [ ] 27.1 Optional capabilities.
- [ ] 27.2 Migration decision.
- [ ] 27.3 Final report.
- [ ] 27.4 Release gate.
- [ ] Gate.

## Immediate next operations

1. Run strict CI for Task 2.
2. Fix every first-party finding and rerun until exact-head green.
3. Close Task 2 with exact run/job/test evidence.
4. Begin Task 3 only after Task 2 closes.
