# Rust Chess Engine Port TODO — Live Status Tracker

**Status:** In progress  
**Date created:** 2026-08-01  
**Last status update:** 2026-08-01  
**Target branch:** `rust-engine`  
**Authoritative specification:** `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md`  
**Full task definitions:** `docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md`  
**Ralph Loop status:** `docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md`

---

## Status rules

- `[x]` means implementation or evidence exists in the repository.
- `[ ]` means incomplete, unverified, deferred, blocked, or not started.
- A task gate remains open until its implementation and exact evidence requirements pass.
- Every first-party compiler, Clippy, rustdoc, formatting, lint, and test finding is a bug and must be fixed at its source.
- GitHub Actions is the authoritative Rust execution environment.
- Update this file whenever implementation or validation changes a task or subtask status.

---

## Current task summary

| Task | Status | Current result |
|---:|---|---|
| 0 | **Complete** | Frozen Python baseline, fast/slow suites, perft, UCI smoke, inventory, exclusions, and evidence are complete. |
| 1 | **Complete** | Seven-crate workspace, boundaries, policy, license, lockfile, CI, and exact-SHA Rust validation are complete. |
| 2 | **Complete** | Core value types, coordinate contract, packed move identity, exhaustive tests, documentation, and exact-SHA CI are complete. |
| 3 | **Not started** | `Position` and invariants remain open. |
| 4 | **Not started** | Strict FEN and UCI move notation remain open. |
| 5 | **Not started** | Attack generation remains open. |
| 6 | **Not started** | Pseudo-legal generation remains open. |
| 7 | **Not started** | Complete legal generation remains open. |
| 8 | **Not started** | Make/unmake remains open. |
| 9 | **Not started** | Zobrist hashing and repetition identity remain open. |
| 10 | **Not started** | `Game`, history, and draw semantics remain open. |
| 11 | **Not started** | Rust perft and differential validation remain open. |
| 12 | **Not started** | Baseline evaluation remains open. |
| 13 | **Not started** | Reference search and alpha-beta remain open. |
| 14 | **Not started** | Quiescence and move ordering remain open. |
| 15 | **Not started** | Fixed-capacity transposition table remains open. |
| 16 | **Not started** | Iterative deepening, PV, limits, and cancellation remain open. |
| 17 | **Not started** | Linux UCI behavior remains open. |
| 18 | **Not started** | Safe API, C ABI, and JNI remain open. |
| 19 | **Not started** | Opening-book infrastructure remains open. |
| 20 | **Not started** | Self-play and datasets remain open. |
| 21 | **Not started** | Named-schema tuning remains open. |
| 22 | **Not started** | Advanced classical terms remain open. |
| 23 | **Not started** | Property/fuzz/sanitizer robustness remains open. |
| 24 | **Not started** | Performance hardening remains open. |
| 25 | **Partial** | Linux CI, architecture docs, strict gates, dispatch, and one full-validation command exist; the complete matrix/workflow remains open. |
| 26 | **Not started** | v0.1 signoff remains open. |
| 27 | **Not started** | Full port signoff remains open. |

---

# Task 0: Establish the port baseline and decision record

**Task status:** Complete.

## 0.1 Preserve the Python baseline

- [x] Freeze the pre-Rust Python source baseline at `f743013a84173b551eac5488c638cb48098ec6d0`.
- [x] Prove current Python source/test/dependency inputs are byte-equivalent to the frozen baseline.
- [x] Run and record the fast Python suite.
- [x] Run and record the slow Python suite with Stockfish available.
- [x] Record starting-position perft depths 1–4 and timings.
- [x] Record UCI handshake and depth-one smoke behavior.
- [x] Record historical engine-strength, self-play, and tuning artifacts as comparison-only evidence.

## 0.2 Python-reference inventory

- [x] Inventory rules and board state.
- [x] Inventory FEN and notation.
- [x] Inventory search and evaluation.
- [x] Inventory opening-book, self-play, and tuning code.
- [x] Inventory UCI and CLI/TUI adapters.
- [x] Inventory and exclude transcript-specific guidance.
- [x] Map retained concepts to Rust milestones.

## 0.3 Defects Rust must not copy

- [x] Record all fourteen fixed non-copy constraints, including clone-per-child search, string keys, permissive FEN, implicit queen promotion, unbounded TT storage, missing mate normalization, unsafe castling attack-state checks, and automatic tuned-weight discovery.

## 0.4 Completion evidence

- [x] Baseline record and fail-loud capture tooling committed.
- [x] Exact commands, environment, logs, timings, and CI artifact reviewed.
- [x] Task 0 gate.

### Task 0 completion note

- Frozen source baseline: `f743013a84173b551eac5488c638cb48098ec6d0`.
- Final evidence candidate: `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`.
- Final CI run/job: `30722127447` / `91427510964`.
- Fast suite: `1203 passed, 179 deselected in 43.92s`.
- Slow suite: `179 passed, 1203 deselected in 2449.87s (0:40:49)`.
- Perft: `depths 1–4 = 20, 400, 8902, 197281`.
- UCI: `handshake, ready check, and depth-one `bestmove g1f3` passed`.
- Artifact: `ID 8825590703; SHA-256 ed44f43246e5176479825a3fef25aee6595b91af573453ad74f367a6c634d900`.
- Deviations: none.

---

# Task 1: Create the Cargo workspace and dependency boundaries

**Task status:** Complete.

## 1.1 Workspace skeleton

- [x] Add root Cargo workspace configuration.
- [x] Add `chess-core`, `chess-search`, `chess-uci`, `chess-ffi`, `chess-jni`, `chess-tools`, and `chess-tune`.
- [x] Document each crate's responsibility and allowed dependencies.
- [x] Keep every feature-empty crate buildable.

## 1.2 Toolchain and policy

- [x] Use Rust 2021 and document MSRV 1.75.
- [x] Configure stable rustfmt and Clippy.
- [x] Forbid unsafe code in `chess-core` and `chess-search`.
- [x] Deny first-party warnings in workspace policy and CI.
- [x] Add MIT license metadata consistently to all seven packages.
- [x] Commit and verify `Cargo.lock`.

## 1.3 Architecture enforcement

- [x] Keep `chess-core` independent of search and adapters.
- [x] Keep `chess-search` dependent only on portable lower-level code.
- [x] Keep UCI, FFI, JNI, tools, and tuning as outward adapters.
- [x] Document the dependency graph.
- [x] Remove and ignore tracked local Claude worktrees.

## 1.4 Initial CI

- [x] Add formatting, metadata, check, Clippy, test, rustdoc, debug-build, and release-build gates.
- [x] Keep Python validation on `master` during migration.
- [x] Add deterministic `rust-engine` workflow dispatch and status publishing.
- [x] Validate Linux x86-64 debug and release builds.
- [ ] Add AArch64 and Android compile jobs when those toolchains are configured; tracked under Task 25.
- [x] Task 1 gate.

### Task 1 completion note

- Final evidence candidate: `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`.
- Final CI run/job: `30722127447` / `91427510938`.
- Rust toolchain/runner: `Rust 1.97.1 on Ubuntu 24.04.4`.
- Result: metadata, formatting, check, Clippy, tests, rustdoc, debug build, release build, lockfile verification, MIT metadata, and checkout cleanup passed.
- Accepted external notices: third-party GitHub Action runtime deprecations only.
- Deviations: AArch64 and Android compile jobs remain deferred to Task 25.

---

# Task 2: Implement core value types and coordinate contracts

**Task status:** Complete.

## 2.1 Color and piece types

- [x] Implement `Color` with stable indexing, `opposite()`, pawn direction, and rank helpers.
- [x] Implement `PieceKind` without `Empty`.
- [x] Implement compact `Piece { color, kind }` without square ownership.
- [x] Add stable conversion and display tests.

## 2.2 Square

- [x] Implement validated transparent `Square(u8)`.
- [x] Preserve `a8 = 0`, `h8 = 7`, `a1 = 56`, and `h1 = 63`.
- [x] Implement file, rank, row, and index accessors.
- [x] Implement strict lowercase algebraic parse/format.
- [x] Test all 64 squares round-trip.
- [x] Keep unchecked construction crate-private and audited.

## 2.3 Bitboard

- [x] Implement transparent `Bitboard(u64)`.
- [x] Implement set, clear, contains, pop-LSB, iteration, count, and bitwise operations.
- [x] Implement rank/file masks and eight non-wrapping shifts.
- [x] Add exhaustive basic and edge-operation tests.

## 2.4 Move encoding

- [x] Document private packed `u16` move layout.
- [x] Encode source, destination, promotion identity, and 14 semantic move kinds.
- [x] Implement source, destination, kind, promotion, and capture accessors.
- [x] Derive stable equality, hash, and order behavior.
- [x] Test every move kind round-trip.
- [x] Keep all four promotions and promotion captures distinct.
- [x] Keep packed layout out of the external ABI contract.

## 2.5 Castling rights and counters

- [x] Implement validated four-bit `CastlingRights`.
- [x] Implement color/side query, set, clear, and clear-color helpers.
- [x] Implement checked typed `HalfmoveClock` and nonzero `FullmoveNumber`.

- [x] Task 2 gate: exact-SHA format, metadata, compiler, Clippy, tests, rustdoc, debug, and release validation.

### Task 2 implementation note

- Files: `crates/chess-core/src/{lib,piece,square,bitboard,move_encoding,castling,counters}.rs` and `docs/RUST_CORE_VALUE_TYPES.md`.
- No dependencies added.
- No unsafe code or lint suppression added.
- Production search architecture remains untouched.

### Task 2 completion evidence

- Implementation commit: `878f9090af3d5fdee77ca87aaea24761a8df0312`.
- Formatting fix: `f29524599134a14d34121af2fefb04cd90e78df0`.
- CI run/job: `30723748100` / `91431648799`.
- Tests: `16 passed, 0 failed`; all other workspace crates and doctests passed with zero tests.
- Formatting, lockfile verification, metadata, Cargo check, Clippy with `-D warnings`, tests, rustdoc with `-D warnings`, debug build, and release build passed.
- First-party warnings: none. Third-party GitHub Action runtime deprecation notices only.
- Deviations: none.

**Task 2 gate:** **CLOSED.**

---

# Tasks 3–24: Numbered subtask status

Every action in these tasks remains open.

- [ ] Task 3: `Position` and invariants — subsections 3.1–3.5 and gate open.
- [ ] Task 4: strict FEN and UCI move notation — subsections 4.1–4.5 and gate open.
- [ ] Task 5: attack-generation infrastructure — subsections 5.1–5.5 and gate open.
- [ ] Task 6: pseudo-legal move generation — subsections 6.1–6.5 and gate open.
- [ ] Task 7: complete legal generation and special rules — subsections 7.1–7.6 and gate open.
- [ ] Task 8: make/unmake and incremental state — subsections 8.1–8.4 and gate open.
- [ ] Task 9: Zobrist hashing and repetition identity — subsections 9.1–9.5 and gate open.
- [ ] Task 10: `Game`, history, and draw semantics — subsections 10.1–10.6 and gate open.
- [ ] Task 11: Rust perft and differential validation — subsections 11.1–11.5 and gate open.
- [ ] Task 12: baseline evaluator and trace — subsections 12.1–12.6 and gate open.
- [ ] Task 13: reference search and alpha-beta — subsections 13.1–13.5 and gate open.
- [ ] Task 14: quiescence and move ordering — subsections 14.1–14.5 and gate open.
- [ ] Task 15: fixed-capacity TT — subsections 15.1–15.6 and gate open.
- [ ] Task 16: iterative deepening/PV/limits/cancellation — subsections 16.1–16.7 and gate open.
- [ ] Task 17: Linux UCI — subsections 17.1–17.5 and gate open.
- [ ] Task 18: safe API/C ABI/JNI — subsections 18.1–18.5 and gate open.
- [ ] Task 19: opening-book infrastructure — subsections 19.1–19.5 and gate open.
- [ ] Task 20: self-play and datasets — subsections 20.1–20.4 and gate open.
- [ ] Task 21: named-schema tuning — subsections 21.1–21.5 and gate open.
- [ ] Task 22: advanced classical terms — subsections 22.1–22.3 and gate open.
- [ ] Task 23: property/fuzz/sanitizer robustness — subsections 23.1–23.4 and gate open.
- [ ] Task 24: performance hardening — subsections 24.1–24.5 and gate open.

---

# Task 25: Complete CI, documentation, and developer workflows

**Task status:** Partial.

## 25.1 CI matrix

- [x] Linux debug tests, Clippy all targets/features, rustdoc, debug build, and release build.
- [x] Preserve Python validation until migration signoff.
- [x] Maintain deterministic Rust CI dispatch and exact-SHA status publishing.
- [ ] Linux release tests/perft.
- [ ] AArch64 and Android AArch64 builds.
- [ ] JNI instrumented smoke.
- [ ] Miri, sanitizer, and fuzz smoke jobs.
- [ ] Slow/nightly Rust perft and optional scheduled performance/strength jobs.

## 25.2 Documentation

- [x] Workspace architecture.
- [x] Core coordinate system, value types, bitboards, packed move identity, castling bits, and counters.
- [ ] Position invariants, make/unmake, notation, draws, hashing, search, TT, evaluation, UCI, FFI/JNI, perft/fuzz, self-play, and tuning documentation.

## 25.3 Developer commands

- [x] One full Task 0/1 validation command.
- [ ] Bootstrap, fast validation, perft, UCI, Android, self-play, and tuning commands.

## 25.4 Generated artifacts

- [x] Ignore Cargo targets and local Claude worktrees.
- [x] Commit the intentional Cargo lockfile.
- [ ] Complete versioned schema/fixture/generated-artifact policy.

- [ ] Task 25 gate.

---

# Task 26: v0.1 functional-engine signoff

- [ ] Rules signoff.
- [ ] Search signoff.
- [ ] Adapter signoff.
- [ ] Quality signoff.
- [ ] Evidence report and Task 26 gate.

# Task 27: Full port-program signoff

- [ ] Optional capability completion.
- [ ] Migration decision.
- [ ] Final implementation report.
- [ ] Final release gate.

---

## Immediate next operations

1. Begin Task 3: `Position` and invariants.
2. Implement the hybrid mailbox/bitboard representation and private mutation boundary.
3. Add starting-position construction, king caches, invariant checks, equality, and restoration-oriented tests.
4. Ralph Loop Task 3 through exact-SHA strict CI.
