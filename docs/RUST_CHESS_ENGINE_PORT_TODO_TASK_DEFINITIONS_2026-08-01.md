# Rust Chess Engine Port TODO

**Status:** Not started  
**Date:** 2026-08-01  
**Target branch:** `rust-engine`  
**Authoritative specification:** `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md`

---

## Goal

Build a new portable Rust chess engine using the useful behavior and engineering lessons from the Python implementation while deliberately rejecting its unsuitable architecture, known rules defects, clone-heavy search model, and accumulated narrow heuristic patches.

The completed program must provide:

- a correct Rust rules core;
- a usable classical search engine;
- a Linux UCI executable;
- a stable portable Rust API;
- a C ABI and Android JNI adapter;
- exact perft, property, differential, fuzz, and regression coverage;
- optional opening-book support;
- offline self-play and versioned evaluation tuning;
- reproducible diagnostics, benchmarks, and release evidence.

This TODO is dependency-ordered. Later tasks may be prototyped early, but they must not be declared complete before their prerequisites and phase gates pass.

---

## Program rules

- [ ] Work only on the `rust-engine` branch unless an explicitly named follow-up branch is created.
- [ ] Treat the Rust specification as authoritative for the new implementation.
- [ ] Treat Python code and tests as reference material, not as an API-compatibility contract.
- [ ] Do not delete or broadly rewrite the Python engine during the port.
- [ ] Do not mark a task complete merely because it compiles.
- [ ] Add tests with every behavioral implementation task.
- [ ] Preserve every discovered rules mismatch as a fixed Rust regression.
- [ ] Do not add advanced search pruning until the unpruned and baseline alpha-beta paths agree at shallow depths.
- [ ] Do not add transcript-specific guidance modules to the Rust evaluator or ordering layer.
- [ ] Do not use clone-per-child as the production search architecture.
- [ ] Do not use string position keys in Rust search or repetition tracking.
- [ ] Do not silently load weights, opening books, or configuration from conventional paths.
- [ ] Do not allow Rust panics to cross C or JNI boundaries.
- [ ] Record exact commands, results, benchmark environment, and commit SHA for every major completion gate.

---

## Standard validation commands

These commands become mandatory as soon as the referenced crates and targets exist:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo test --workspace --all-features
cargo doc --workspace --no-deps
```

Release/perft gates:

```bash
cargo test -p chess-core --release perft
cargo run --release -p chess-tools -- perft --suite standard
cargo run --release -p chess-tools -- divide --fen "<FEN>" --depth <N>
```

Cross-platform gates, once configured:

```bash
cargo build --workspace --target aarch64-unknown-linux-gnu
cargo build -p chess-jni --target aarch64-linux-android
```

The exact Android command may use `cargo-ndk`; document the final supported workflow rather than maintaining multiple undocumented paths.

---

# Task 0: Establish the port baseline and decision record

## 0.1 Preserve the Python baseline

- [ ] Record the current `rust-engine` branch SHA before Rust source changes.
- [ ] Run and record the current fast Python test suite.
- [ ] Run and record the current slow Python test suite when practical.
- [ ] Record current Python perft results and timings for existing exact positions.
- [ ] Record current UCI smoke behavior.
- [ ] Record current engine-strength/self-play artifacts that are useful as historical comparison only.

## 0.2 Create a Python-reference inventory

- [ ] Inventory Python modules by category:
  - [ ] rules and board state;
  - [ ] FEN and notation;
  - [ ] search;
  - [ ] evaluation;
  - [ ] opening book;
  - [ ] self-play and tuning;
  - [ ] UCI;
  - [ ] CLI/TUI;
  - [ ] transcript-specific guidance.
- [ ] Map each retained concept to the relevant Rust milestone.
- [ ] Mark excluded modules explicitly so they are not accidentally translated later.

## 0.3 Record known Python defects that Rust must not copy

- [ ] Add fixed design notes for:
  - [ ] incorrect dead-position and insufficient-material shortcuts;
  - [ ] castling transit/destination safety evaluated with the source king still blocking lines;
  - [ ] clone-per-child search;
  - [ ] string position keys;
  - [ ] raw en-passant field included in every repetition key;
  - [ ] permissive FEN parsing;
  - [ ] implicit queen promotion in core execution;
  - [ ] multiple internal move representations;
  - [ ] unbounded per-search dictionary TT;
  - [ ] missing TT mate-score normalization;
  - [ ] root heuristic/tie-break interactions with alpha-beta bounds;
  - [ ] automatic tuned-weight file discovery;
  - [ ] global UCI control/output state;
  - [ ] narrow transcript-driven evaluator and move-ordering patches.

## 0.4 Completion evidence

- [ ] Commit the baseline/decision record.
- [ ] Record the commit SHA in this task's completion note.
- [ ] Do not begin architectural migration by editing Python internals.

**Task 0 gate:** The existing implementation is reproducibly described, known bad behavior is documented, and retained/excluded concepts are traceable.

---

# Task 1: Create the Cargo workspace and dependency boundaries

## 1.1 Workspace skeleton

- [ ] Add root `Cargo.toml` workspace configuration.
- [ ] Add crates:
  - [ ] `crates/chess-core`;
  - [ ] `crates/chess-search`;
  - [ ] `crates/chess-uci`;
  - [ ] `crates/chess-ffi`;
  - [ ] `crates/chess-jni`;
  - [ ] `crates/chess-tools`;
  - [ ] `crates/chess-tune`.
- [ ] Add minimal crate-level documentation describing responsibility and allowed dependencies.
- [ ] Keep optional or future crates buildable even if initially feature-empty.

## 1.2 Toolchain and policy

- [ ] Pin or document the minimum supported Rust version.
- [ ] Add `rustfmt` and Clippy configuration only where justified.
- [ ] Add `#![forbid(unsafe_code)]` to `chess-core` and `chess-search`.
- [ ] Add workspace lints and deny warnings in CI.
- [ ] Add license and package metadata consistently.

## 1.3 Architecture enforcement

- [ ] Confirm `chess-core` has no dependency on search or adapters.
- [ ] Confirm `chess-search` depends only on portable core/support crates.
- [ ] Confirm UCI, FFI, JNI, tools, and tuning are outward adapters.
- [ ] Add an architecture document or dependency diagram.

## 1.4 Initial CI

- [ ] Add GitHub Actions jobs for formatting, Clippy, tests, and docs.
- [ ] Keep existing Python CI intact during the port.
- [ ] Add Linux x86-64 debug and release build coverage.
- [ ] Add AArch64 and Android compile jobs when toolchains are configured.

**Task 1 gate:** Empty/minimal workspace passes format, Clippy, tests, and docs without violating dependency direction.

---

# Task 2: Implement core value types and coordinate contracts

## 2.1 Color and piece types

- [ ] Implement `Color` with stable indexing and `opposite()`.
- [ ] Implement `PieceKind` without an `Empty` variant.
- [ ] Implement compact `Piece { color, kind }` without a mutable square.
- [ ] Add conversion/display tests.

## 2.2 Square

- [ ] Implement validated `Square(u8)`.
- [ ] Retain canonical mapping:
  - [ ] `a8 = 0`;
  - [ ] `h8 = 7`;
  - [ ] `a1 = 56`;
  - [ ] `h1 = 63`.
- [ ] Implement file/rank/row/index accessors.
- [ ] Implement algebraic parse/format.
- [ ] Test all 64 squares round-trip.
- [ ] Keep unchecked construction private or tightly scoped.

## 2.3 Bitboard

- [ ] Implement a `Bitboard` newtype.
- [ ] Add set, clear, contains, pop-lsb, iteration, and count operations.
- [ ] Add edge-mask and shift helpers that cannot wrap across files.
- [ ] Add exhaustive basic-operation tests.

## 2.4 Move encoding

- [ ] Choose and document packed `Move` layout.
- [ ] Encode source, destination, promotion, and move kind.
- [ ] Implement accessors and stable equality/hash/order behavior.
- [ ] Implement encode/decode round-trip tests for every move kind.
- [ ] Ensure all four promotion and promotion-capture identities remain distinct.
- [ ] Do not expose the bit layout as a stable external ABI.

## 2.5 Castling rights and counters

- [ ] Implement four-bit `CastlingRights`.
- [ ] Add color/side query and clearing helpers.
- [ ] Add typed move-counter handling.

**Task 2 gate:** All core value types are compact, documented, exhaustive tests pass, and there is one internal move identity.

---

# Task 3: Implement `Position` and invariants

## 3.1 Hybrid representation

- [ ] Implement private mailbox storage.
- [ ] Implement piece bitboards by color and kind.
- [ ] Implement color occupancy and all occupancy.
- [ ] Cache king squares.
- [ ] Store side to move, castling rights, en-passant state, counters, and Zobrist placeholder/state.

## 3.2 Constructors

- [ ] Implement an empty internal builder for parser/tests.
- [ ] Implement standard starting position.
- [ ] Ensure playable constructors require exactly one king per side.
- [ ] Provide explicit analysis-position construction only if needed; do not weaken default invariants.

## 3.3 Accessors and mutation boundary

- [ ] Implement read-only piece lookup.
- [ ] Keep direct piece placement private or test-only.
- [ ] Implement internal add/remove/move primitives that update all redundant structures.
- [ ] Prevent adapters from mutating mailbox/bitboards directly.

## 3.4 Invariant checker

- [ ] Implement debug/test invariant validation for:
  - [ ] mailbox/bitboard agreement;
  - [ ] occupancy agreement;
  - [ ] no overlap;
  - [ ] one king per side;
  - [ ] correct cached king squares;
  - [ ] valid en-passant state;
  - [ ] correct hash once hashing exists.
- [ ] Run invariant checks in all state-transition tests.

## 3.5 Equality and clone

- [ ] Implement logical equality suitable for restoration tests.
- [ ] Allow `Clone` for tests/application snapshots.
- [ ] Add an explicit comment that production recursive search must not clone per node.

**Task 3 gate:** Starting and constructed positions satisfy invariants and redundant representations cannot diverge through public APIs.

---

# Task 4: Implement strict FEN and UCI move notation

## 4.1 Structured errors

- [ ] Define `FenError`, `MoveParseError`, and related error categories.
- [ ] Include field/rank/token context without exposing internal panics.

## 4.2 Strict FEN parser

- [ ] Parse exactly eight ranks and eight files each.
- [ ] Validate piece characters.
- [ ] Validate active color exactly.
- [ ] Validate castling syntax and duplicates.
- [ ] Validate en-passant syntax and target rank.
- [ ] Validate halfmove and fullmove counters.
- [ ] Require exactly one king per side for normal playable parsing.
- [ ] Define and test pawn-on-promotion-rank policy.
- [ ] Reject malformed FEN without partially mutating an existing position.

## 4.3 Canonical FEN serializer

- [ ] Emit all six fields.
- [ ] Emit deterministic castling ordering.
- [ ] Round-trip starting and curated positions.
- [ ] Preserve counters and en-passant field according to FEN semantics.

## 4.4 UCI move strings

- [ ] Parse four-character normal moves.
- [ ] Parse five-character promotions.
- [ ] Reject invalid files, ranks, lengths, and promotion suffixes.
- [ ] Resolve parsed coordinates against legal moves later without synthesizing an unchecked move.
- [ ] Format every internal legal move correctly.

## 4.5 Property tests

- [ ] FEN parse/serialize/parse stability.
- [ ] Square and move notation round-trip.
- [ ] No parser panic on arbitrary input.

**Task 4 gate:** Strict parsing is fail-loud, canonical serialization is stable, and malformed input cannot create partial state.

---

# Task 5: Implement attack-generation infrastructure

## 5.1 Leaper attacks

- [ ] Precompute pawn attacks for both colors and all squares.
- [ ] Precompute knight attacks for all squares.
- [ ] Precompute king attacks for all squares.
- [ ] Add exhaustive edge/corner tests.

## 5.2 Sliding attacks

- [ ] Implement correct rook attacks for arbitrary occupancy.
- [ ] Implement correct bishop attacks for arbitrary occupancy.
- [ ] Implement queen attacks as combined sliding attacks.
- [ ] Begin with clear ray scans if necessary.
- [ ] Add blocker-before, blocker-on-target, edge, and empty-board tests.

## 5.3 Geometric tables

- [ ] Add ray, line, and between-square helpers where useful.
- [ ] Test collinearity and intermediate-square masks.

## 5.4 Position attack queries

- [ ] Implement attackers-to-square.
- [ ] Implement square-attacked-by-color.
- [ ] Implement checkers-to-king.
- [ ] Implement pinned-piece discovery or equivalent supporting data.
- [ ] Ensure pawn attack semantics do not depend on occupancy.

## 5.5 Differential attack fixtures

- [ ] Compare representative attack maps against a trusted oracle or independently generated fixtures.

**Task 5 gate:** All attack primitives are exhaustively tested and independent of move-legality assumptions.

---

# Task 6: Implement pseudo-legal move generation

## 6.1 Pawn moves

- [ ] Single pushes.
- [ ] Double pushes with start-rank and intermediate-square checks.
- [ ] Captures.
- [ ] En-passant candidates.
- [ ] Four quiet promotions.
- [ ] Four capture promotions.

## 6.2 Piece moves

- [ ] Knights.
- [ ] Bishops.
- [ ] Rooks.
- [ ] Queens.
- [ ] Kings without final king-safety filtering.

## 6.3 Castling candidates

- [ ] Generate only when basic occupancy/right conditions permit.
- [ ] Leave complete safety validation to the legal layer.

## 6.4 Move list

- [ ] Use bounded stack-friendly storage where practical.
- [ ] Avoid per-move heap allocation.
- [ ] Define deterministic generation order for testing, without treating it as a strength feature.

## 6.5 Tests

- [ ] Starting-position pseudo-legal counts.
- [ ] Promotions and underpromotions.
- [ ] Edge pawns and knights.
- [ ] Sliding blockers.
- [ ] En-passant candidate geometry.

**Task 6 gate:** Pseudo-legal generation is complete, allocation-conscious, and preserves exact move identity.

---

# Task 7: Implement complete legal move generation and special rules

## 7.1 King-safety filtering

- [ ] Implement a correctness-first legal filter using make/check/unmake or direct masks.
- [ ] Reject every move that leaves the moving king attacked.
- [ ] Reject king moves into attacked squares.
- [ ] Never generate king captures.

## 7.2 Check evasions

- [ ] Single-check capture.
- [ ] Single-check block.
- [ ] King move.
- [ ] Double-check king-only moves.
- [ ] Pinned-piece restrictions.

## 7.3 Castling correctness

- [ ] Validate current king not in check.
- [ ] Validate transit square.
- [ ] Validate destination square.
- [ ] Validate correct king and rook placement.
- [ ] Validate empty path.
- [ ] Validate castling right.
- [ ] Add regression where vacating the king source reveals a sliding attack.
- [ ] Add all four legal castling cases.
- [ ] Add moved-away-and-back king/rook regressions.

## 7.4 En-passant correctness

- [ ] Validate target and captured pawn.
- [ ] Remove both source pawn and captured pawn before king-safety evaluation.
- [ ] Add horizontal and diagonal discovered-check regressions.
- [ ] Add en-passant target expiry tests.

## 7.5 Promotion correctness

- [ ] Require explicit promotion identity in internal legal moves.
- [ ] Reject non-pawn promotion flags.
- [ ] Reject promotion on a non-promotion rank.
- [ ] Preserve all underpromotions through generation and application.

## 7.6 Initial legal perft

- [ ] Starting position D1-D4 exact.
- [ ] Add `perft` recursive helper using make/unmake.
- [ ] Add `divide` output.

**Task 7 gate:** Exact starting perft passes, special rules have direct regressions, and no unresolved legal-move mismatch remains in the initial fixture set.

---

# Task 8: Complete make/unmake and incremental state

## 8.1 Undo structure

- [ ] Store captured piece and square.
- [ ] Store prior castling rights.
- [ ] Store prior en-passant state.
- [ ] Store prior clocks.
- [ ] Store prior hash or complete reversible hash delta.
- [ ] Restore promotion, castling rook move, and king-square cache correctly.

## 8.2 Move application paths

- [ ] Public checked move application.
- [ ] Internal generated-legal move application.
- [ ] No partial mutation on public failure.
- [ ] Exact side-to-move and fullmove transitions.
- [ ] Halfmove reset on pawn move and capture.

## 8.3 Restoration tests

For every move category:

- [ ] snapshot position;
- [ ] make move;
- [ ] validate invariants;
- [ ] unmake move;
- [ ] assert field-for-field logical equality with snapshot;
- [ ] assert hash equality after Task 9.

Move categories:

- [ ] quiet;
- [ ] double pawn push;
- [ ] normal capture;
- [ ] en passant;
- [ ] king castle;
- [ ] queen castle;
- [ ] each promotion;
- [ ] promotion capture;
- [ ] rook capture that changes castling rights.

## 8.4 Sequence restoration

- [ ] Random legal playout then complete reverse unmake.
- [ ] Repeated make/unmake under property tests.
- [ ] No clone-per-child in perft/search paths.

**Task 8 gate:** Every legal move category reverses exactly, and random sequences return to the original position with all invariants intact.

---

# Task 9: Implement Zobrist hashing and canonical repetition identity

## 9.1 Zobrist tables

- [ ] Deterministically generate or embed piece-square keys.
- [ ] Add side-to-move key.
- [ ] Add castling-state keys.
- [ ] Add en-passant file/square keys under documented canonical policy.
- [ ] Version or document generated constants.

## 9.2 Full hash computation

- [ ] Implement authoritative recomputation.
- [ ] Test stable hash for known fixtures.

## 9.3 Incremental updates

- [ ] Quiet moves.
- [ ] Captures.
- [ ] Double pawn pushes.
- [ ] En passant.
- [ ] Castling.
- [ ] Promotions.
- [ ] Castling-right changes.
- [ ] Side-to-move changes.

## 9.4 Canonical en-passant identity

- [ ] Define when en-passant changes the repetition key.
- [ ] Ensure positions with a non-capturable FEN en-passant target compare correctly for repetition.
- [ ] Add capturable/non-capturable target regressions.

## 9.5 Hash verification

- [ ] Compare incremental and recomputed hash after every move in randomized tests.
- [ ] Verify unmake restores the exact prior hash.

**Task 9 gate:** No randomized hash mismatch remains and repetition identity is not based on allocated strings.

---

# Task 10: Implement `Game`, repetition history, and correct draw semantics

## 10.1 `Game` state

- [ ] Own current `Position`.
- [ ] Own played move/undo history as needed.
- [ ] Own position-hash history.
- [ ] Track repetition counts or equivalent efficient history.
- [ ] Expose reset, set-position, play, undo, and status operations.

## 10.2 Mate and stalemate

- [ ] Checkmate when no legal moves and side to move is in check.
- [ ] Stalemate when no legal moves and side to move is not in check.
- [ ] Add canonical fixtures.

## 10.3 Claimable draws

- [ ] Threefold repetition.
- [ ] Fifty-move rule.
- [ ] Expose claimability without silently ending the game unless caller policy chooses to claim.

## 10.4 Automatic draws

- [ ] Fivefold repetition.
- [ ] Seventy-five-move rule.
- [ ] Dead position.
- [ ] Checkmate precedence on the threshold move.

## 10.5 Conservative dead-position logic

- [ ] Implement only cases proven to be dead.
- [ ] Bare kings.
- [ ] King and single bishop versus king.
- [ ] King and single knight versus king.
- [ ] Bishop-only same-color-complex cases where mate is impossible.
- [ ] Add non-dead regressions for two bishops, bishop+knight, and two-knight constructions where mate is reachable with cooperation.
- [ ] Document any intentionally unsupported exact dead-position cases.
- [ ] Never declare a potentially mate-reachable position automatically drawn.

## 10.6 Search-facing history

- [ ] Provide root history to search.
- [ ] Maintain reversible line history without growing string tuples.
- [ ] Define draw score and optional future contempt separately from rules status.

**Task 10 gate:** Claimable and automatic conditions are distinct, known Python draw bugs are rejected by tests, and game/search histories agree.

---

# Task 11: Build authoritative perft and differential validation

## 11.1 Standard exact perft suite

Implement the specification's exact D1-D4 counts for:

- [ ] starting position;
- [ ] Kiwipete;
- [ ] en-passant/rook-ending stress position;
- [ ] castling/promotion/pin stress position;
- [ ] promotion/check-evasion stress position;
- [ ] tactical positional stress position.

## 11.2 Slow perft

- [ ] Add higher-depth counts to slow/nightly tests where runtime permits.
- [ ] Keep fast CI bounded.

## 11.3 Divide tool

- [ ] Accept FEN and depth.
- [ ] Print canonical UCI root moves and child counts.
- [ ] Print total and elapsed time.
- [ ] Stable output suitable for comparison scripts.

## 11.4 Differential oracle harness

- [ ] Add a development tool using `python-chess` or another trusted oracle.
- [ ] Compare legal UCI move sets.
- [ ] Compare post-move FEN.
- [ ] Compare perft.
- [ ] Run seeded random legal playouts.
- [ ] Save failing FEN, move sequence, seed, and both results.
- [ ] Convert every resolved mismatch into a Rust regression.

## 11.5 Corpus gate

- [ ] Build a committed corpus of tricky positions.
- [ ] Include all special-rule and discovered-bug fixtures.
- [ ] Record oracle/tool version used to generate expectations.

**Task 11 gate:** All exact perft positions pass and the accepted differential corpus has zero unresolved mismatches.

---

# Task 12: Implement the baseline evaluator and trace

## 12.1 Evaluation score convention

- [ ] Score from side-to-move or documented internal negamax perspective.
- [ ] Define centipawn units.
- [ ] Reserve mate-score band outside normal evaluation range.
- [ ] Add color/mirror symmetry tests.

## 12.2 Baseline terms

- [ ] Material.
- [ ] Tapered middlegame/endgame phase.
- [ ] Piece-square tables.
- [ ] Mobility.
- [ ] Isolated pawns.
- [ ] Doubled pawns.
- [ ] Passed pawns.
- [ ] Connected pawns/passers.
- [ ] Bishop pair.
- [ ] Rook open/semi-open files.
- [ ] Rook seventh-rank activity.
- [ ] King safety by phase.
- [ ] Space or central control.
- [ ] Endgame king activity.

## 12.3 Evaluation efficiency

- [ ] Avoid heap allocation in normal evaluation.
- [ ] Reuse attack and pawn information where practical.
- [ ] Benchmark each major term.

## 12.4 Evaluation trace

- [ ] Add opt-in named component breakdown.
- [ ] Ensure normal search does not allocate trace maps/strings.
- [ ] Add sum-of-components consistency tests.

## 12.5 Named weight schema

- [ ] Define versioned Rust weight structures.
- [ ] Add explicit defaults.
- [ ] Add validated serialization/deserialization in an adapter/tool crate.
- [ ] Reject incompatible schema versions.
- [ ] Include weight-set identifier/checksum.
- [ ] Do not auto-load files.

## 12.6 Exclusion audit

- [ ] Confirm no review-loop, anti-drift, transcript-specific, or exact-scenario guidance was ported.

**Task 12 gate:** Compact evaluator is symmetric, traced, benchmarked, explicitly configured, and free of narrow Python patch modules.

---

# Task 13: Implement reference search and negamax alpha-beta

## 13.1 Reference search

- [ ] Implement shallow no-prune negamax/minimax for tests.
- [ ] Count nodes.
- [ ] Handle terminal scores and draws consistently.

## 13.2 Negamax alpha-beta

- [ ] Implement recursive negamax.
- [ ] Remove maximizing/minimizing dual branches.
- [ ] Use side-to-move score convention.
- [ ] Implement mate distance by ply.
- [ ] Return a legal best move.
- [ ] Integrate game and line repetition.

## 13.3 Equivalence tests

- [ ] Compare no-prune and alpha-beta scores at shallow depths.
- [ ] Compare chosen moves when scores are uniquely best.
- [ ] Confirm alpha-beta visits no more nodes than reference on curated trees.

## 13.4 Search immutability

- [ ] Search root position is unchanged after completion.
- [ ] Root position is unchanged after cancellation.
- [ ] Invariant and hash checks pass after every search in debug tests.

## 13.5 Terminal fixtures

- [ ] Mate in one.
- [ ] Mated position.
- [ ] Stalemate.
- [ ] Claimable and automatic draws.
- [ ] Shorter mate preferred.
- [ ] Longer survival preferred when being mated.

**Task 13 gate:** Baseline alpha-beta is score-equivalent to the reference search at accepted shallow depths and leaves root state untouched.

---

# Task 14: Implement quiescence and principled move ordering

## 14.1 Quiescence

- [ ] Stand-pat only when not in check.
- [ ] All legal evasions when in check.
- [ ] Captures.
- [ ] Promotions.
- [ ] Alpha-beta bounds.
- [ ] Repetition/draw handling.
- [ ] Cancellation checks.
- [ ] Bounded depth/explosion guard.

## 14.2 Tactical ordering

- [ ] TT move hook, initially no-op until TT exists.
- [ ] Promotions.
- [ ] MVV-LVA capture ordering.
- [ ] Optional static exchange evaluation only after baseline works.

## 14.3 Quiet ordering

- [x] Killer moves by ply.
- [x] History heuristic by side/from/to or piece/to.
- [x] Stable encoded-move tie-break.
- [x] Optional previous-PV move.

## 14.4 Correctness tests

- [x] Horizon capture sequence.
- [x] In-check leaf may not stand pat.
- [x] Promotion sequence.
- [x] Poisoned capture where qsearch changes evaluation.
- [x] Quiescence boundedness.

## 14.5 Explicit exclusions

- [x] No transcript review-loop ordering.
- [x] No anti-drift scenario scoring.
- [x] No root heuristic that can override a better exact score.
- [x] No large strategic evaluation duplicated inside ordering.

**Task 14 gate:** Tactical leaf behavior is correct, ordering reduces nodes in benchmark positions, and search score semantics remain unchanged.

---

# Task 15: Implement the fixed-capacity transposition table

## 15.1 Entry design

- [x] Verification key/hash fragment.
- [x] Depth.
- [x] exact/lower/upper bound.
- [x] normalized score.
- [x] best move.
- [x] age/generation.

## 15.2 Storage layout

- [x] Fixed memory configured in MiB.
- [x] Bucket/cluster design.
- [x] Predictable allocation failure behavior.
- [x] Explicit clear/new-generation operations.

## 15.3 Mate normalization

- [x] Normalize ply-relative mate scores on store.
- [x] Denormalize on probe.
- [x] Test same TT entry reached at different plies.

## 15.4 Probe semantics

- [x] Depth sufficiency.
- [x] Exact hit.
- [x] Lower-bound cutoff.
- [x] Upper-bound cutoff.
- [x] Best-move use even when score cannot be reused.
- [x] Safe handling of repetition-sensitive nodes.

## 15.5 Replacement policy

- [x] Depth-preferred replacement.
- [x] Age awareness.
- [x] Document collision behavior.
- [x] Add deterministic tests.

## 15.6 Diagnostics and benchmarks

- [x] probes;
- [x] hits;
- [x] exact/bound hits;
- [x] replacement counts if useful;
- [x] hash fullness estimate;
- [x] probe/store microbenchmarks.

**Task 15 gate — COMPLETE:** TT is bounded, mate-safe, correctly flagged, measurably useful, and has no unbounded production map fallback.

---

# Task 16: Add iterative deepening, aspiration windows, PV, limits, and cancellation

## 16.1 Iterative deepening

- [x] Search depth 1 through requested maximum.
- [x] Preserve completed result after each iteration.
- [x] Reuse TT/history appropriately.
- [x] Report per-depth diagnostics.

## 16.2 Aspiration windows

- [x] Center on prior iteration score.
- [x] Detect fail-low and fail-high.
- [x] Re-search with a safe expanded/full window.
- [x] Record retry diagnostics.
- [x] Add regression proving a bound cannot be mistaken for an exact root score.

## 16.3 Principal variation

- [x] Reconstruct PV from search data safely.
- [x] Validate every PV move is legal in sequence.
- [x] Avoid TT collision loops.
- [x] Return ponder move when available.

## 16.4 Search limits

- [x] depth;
- [x] nodes;
- [x] soft time;
- [x] hard time;
- [x] infinite;
- [x] explicit stop flag.

## 16.5 Responsive cancellation

- [x] Check inside the tree at bounded node intervals.
- [x] Stop before arbitrary full-depth completion.
- [x] Preserve root position.
- [x] Return last fully completed iteration.
- [x] Define fallback when no iteration completed.
- [x] Benchmark cancellation latency.

## 16.6 Search result API

- [x] best move;
- [x] ponder move;
- [x] typed score;
- [x] completed depth;
- [x] selective depth;
- [x] nodes and qnodes;
- [x] elapsed time;
- [x] PV;
- [x] termination reason.

## 16.7 Optional check extension

- [x] Add a bounded check extension only after baseline tests pass.
- [x] Prevent unbounded extension chains.
- [x] Record extension diagnostics.

**Task 16 gate — COMPLETE:** Fixed-depth/node searches are deterministic, timed searches cancel responsively, PVs are legal, aspiration recovery never promotes an inexact inferior move, and the optional check extension is explicitly bounded.

---

# Task 17: Implement the Linux UCI executable

## 17.1 Protocol loop

- [x] `uci`.
- [x] `isready`.
- [x] `ucinewgame`.
- [x] `setoption` for supported options.
- [x] `position startpos`.
- [x] `position fen` with six fields.
- [x] replay `moves`.
- [x] `go depth`.
- [x] `go nodes`.
- [x] `go movetime`.
- [x] clock/increment/moves-to-go search.
- [x] `go infinite`.
- [x] `stop`.
- [x] `quit`.

## 17.2 UCI search worker

- [x] Adapter-owned worker thread.
- [x] No process-global mutable search control.
- [x] Explicit stop token.
- [x] Clean shutdown and join behavior.
- [x] Safe new-game/position replacement rules.

## 17.3 Time manager

- [x] Convert clocks into soft/hard budgets, not fixed depth.
- [x] Reserve safety margin.
- [x] Account for increment and moves-to-go.
- [x] Unit-test boundary cases and low-time behavior.

## 17.4 Output

- [x] periodic `info depth`;
- [x] typed `score cp` or `score mate`;
- [x] nodes;
- [x] nps;
- [x] time;
- [x] hashfull when available;
- [x] PV;
- [x] `bestmove` and optional ponder.

## 17.5 Integration tests

- [ ] Handshake transcript.
- [ ] Start position and FEN setup.
- [ ] Illegal move input handling.
- [ ] Fixed-depth legal best move.
- [ ] Mate/stalemate `bestmove 0000` or documented compliant representation.
- [ ] `stop` interrupts active search.
- [ ] `quit` exits cleanly.
- [ ] No stdout redirection or global state leakage between test sessions.

**Task 17 gate:** Common UCI GUI workflows pass integration tests and stop works during a depth.

---

# Task 18: Implement the safe API, C ABI, and Android JNI adapter

## 18.1 Safe Rust facade

- [ ] `EngineConfig`.
- [ ] `Engine::new`.
- [ ] set/reset position.
- [ ] canonical FEN retrieval.
- [ ] legal moves.
- [ ] play move.
- [ ] game status.
- [ ] search.
- [ ] cancellation handle.
- [ ] version and weight identity.
- [ ] ownership and thread-safety rustdoc.

## 18.2 C ABI

- [ ] Opaque engine handle.
- [ ] ABI version query.
- [ ] create/destroy.
- [ ] UTF-8 input with explicit lengths.
- [ ] structured result codes.
- [ ] error-message retrieval.
- [ ] output buffer ownership/free contract.
- [ ] null/invalid-handle checks.
- [ ] no Rust layout exposure.
- [ ] `catch_unwind` at every externally callable boundary.

## 18.3 C ABI tests

- [ ] Native C or Rust-through-ABI smoke harness.
- [ ] Repeated create/destroy.
- [ ] Invalid input.
- [ ] Search and cancellation.
- [ ] Buffer lifecycle.
- [ ] Panic containment test using an injected test-only fault.

## 18.4 Android JNI

- [ ] Build AArch64 shared library.
- [ ] Kotlin wrapper class with deterministic native-handle ownership.
- [ ] Position setup and legal moves.
- [ ] Move application and status.
- [ ] Search from a background dispatcher/thread.
- [ ] Cancellation.
- [ ] Error mapping.
- [ ] Native resource close/finalization policy.

## 18.5 Android test harness

- [ ] Host JVM contract tests where possible.
- [ ] Instrumented or emulator smoke test.
- [ ] Verify no search on main thread in sample integration.
- [ ] Verify repeated lifecycle create/search/stop/destroy.
- [ ] Record Android target/toolchain instructions.

**Task 18 gate:** Linux C ABI and Android JNI smoke paths can create an engine, set a position, obtain legal moves, search, stop, and destroy without leaks, crashes, or UI-thread blocking.

---

# Task 19: Implement optional opening-book infrastructure

## 19.1 Core abstraction

- [ ] Define adapter-facing `OpeningBook`/`BookProvider` trait outside `chess-core`.
- [ ] Define `BookMove` with move, weight, and optional metadata.
- [ ] Ensure no filesystem dependency enters core/search crates.

## 19.2 Backend format

- [ ] Choose Polyglot or a versioned project-specific indexed format.
- [ ] Document version and endianness.
- [ ] Validate checksums/schema where applicable.
- [ ] Reject corrupt input loudly.

## 19.3 Selection policies

- [ ] deterministic highest weight;
- [ ] weighted random;
- [ ] explicit local RNG seed;
- [ ] legal-move validation before return.

## 19.4 Adapter integration

- [ ] UCI option to enable/disable book.
- [ ] Safe API configuration.
- [ ] Android asset-supplied book example.
- [ ] Normal operation when no book exists.

## 19.5 Tests

- [ ] invalid move rejected from book;
- [ ] deterministic tie ordering;
- [ ] seeded weighted selection reproducibility;
- [ ] corrupt/unsupported data error;
- [ ] no auto-discovery.

**Task 19 gate:** Book support is optional, explicit, legal, reproducible, and platform adapters supply all I/O.

---

# Task 20: Implement self-play and versioned dataset tooling

## 20.1 Self-play configuration

- [ ] Independent engine config per side.
- [ ] Fixed depth/node/time limits.
- [ ] Fixed seed.
- [ ] Opening diversification source.
- [ ] Maximum ply policy.
- [ ] Draw/adjudication policy.
- [ ] Output path supplied explicitly.

## 20.2 Game records

- [ ] Moves and final result.
- [ ] Initial position/opening identifier.
- [ ] engine version per side.
- [ ] evaluator/weight identity per side.
- [ ] search limits.
- [ ] seed.
- [ ] termination/adjudication reason.
- [ ] reproducible replay command.

## 20.3 Position dataset schema

- [ ] Versioned record format.
- [ ] Lossless FEN or equivalent.
- [ ] Outcome.
- [ ] Side to move.
- [ ] Game ID and ply.
- [ ] Engine/evaluator metadata.
- [ ] Filtering metadata.
- [ ] Explicit train/validation/test split.

## 20.4 Data quality

- [ ] Reject empty output as success.
- [ ] Define duplicate handling.
- [ ] Exclude or mark opening positions according to explicit policy.
- [ ] Define treatment of max-ply games; do not silently call all of them valid draws.
- [ ] Add deterministic small-run integration test.

**Task 20 gate:** A seeded self-play run can be replayed and produces a validated, versioned dataset with complete provenance.

---

# Task 21: Implement named-schema Texel-style tuning and validation

## 21.1 Weight schema integration

- [ ] Enumerate tunable named parameters.
- [ ] Preserve non-tunable structural constants separately.
- [ ] Version serialization.
- [ ] Include checksum and training metadata.

## 21.2 Loss pipeline

- [ ] Logistic result mapping.
- [ ] Explicit `K` calibration.
- [ ] Mean-squared or documented objective.
- [ ] Train/validation separation.
- [ ] Empty/malformed dataset failure.

## 21.3 Optimizer

- [ ] Implement SPSA or another documented optimizer.
- [ ] Seed optimizer randomness.
- [ ] Bounds/regularization for nonsensical weights.
- [ ] Checkpoint support.
- [ ] Resume validation.

## 21.4 Reports

- [ ] Initial training loss.
- [ ] Initial validation loss.
- [ ] Final training loss.
- [ ] Final validation loss.
- [ ] Parameter deltas.
- [ ] Dataset and engine identifiers.
- [ ] Exact command/config.

## 21.5 Candidate validation

- [ ] Candidate-versus-baseline match.
- [ ] Color-balanced openings.
- [ ] Fixed seeds/opening set.
- [ ] Sufficient sample size documented.
- [ ] Tactical/perft/rules suites rerun.
- [ ] Reject candidate on correctness regression.
- [ ] Do not auto-activate candidate output.

**Task 21 gate:** Tuned weights are named, versioned, reproducible, validated out-of-sample, and explicitly activated.

---

# Task 22: Evaluate and add advanced classical terms selectively

This task covers only concepts from the retained good-items list that are not already adequately represented in the compact baseline.

## 22.1 Candidate-term protocol

For each proposed term:

- [ ] write a concise chess definition;
- [ ] identify overlap with existing terms;
- [ ] add isolated fixtures;
- [ ] verify mirror/color symmetry;
- [ ] benchmark evaluation cost;
- [ ] run fixed-node search comparison;
- [ ] run controlled candidate-versus-baseline matches;
- [ ] accept, revise, or reject with recorded evidence.

## 22.2 Candidate areas

- [ ] richer pawn-majority and candidate-passer modeling;
- [ ] improved king-zone attack units;
- [ ] defender coordination where not duplicated by king safety;
- [ ] rook/queen battery activity;
- [ ] minor-piece outposts and bad bishops;
- [ ] endgame king/passer races;
- [ ] simplification incentives encoded generally rather than scenario patches;
- [ ] endgame phase-specific PSTs or material scaling.

## 22.3 Explicit exclusions

- [ ] Do not port `review_loop_guidance`.
- [ ] Do not port `anti_drift_guidance`.
- [ ] Do not port exact transcript move preferences.
- [ ] Do not add hard-coded windows solely for one historical self-play position.
- [ ] Do not add a term without measurable evidence.

**Task 22 gate:** Every advanced term has an evidence record; rejected Python concepts remain excluded rather than silently reappearing under new names.

---

# Task 23: Add property testing, fuzzing, sanitizers, and robustness gates

## 23.1 Property tests

- [ ] all 64 square conversions;
- [ ] move encode/decode;
- [ ] FEN round-trip;
- [ ] make/unmake restoration;
- [ ] incremental/full hash equality;
- [ ] generated legal move accepted;
- [ ] legal move preserves king safety;
- [ ] internal occupancy invariants;
- [ ] evaluator symmetry;
- [ ] legal PV sequence.

## 23.2 Fuzz targets

- [ ] FEN parser;
- [ ] UCI move parser;
- [ ] random legal sequence plus reverse unmake;
- [ ] game-history/repetition transitions;
- [ ] weight parser;
- [ ] opening-book parser;
- [ ] C ABI buffers and handles.

## 23.3 Runtime analysis

- [ ] Miri-compatible core test subset.
- [ ] Address sanitizer where supported.
- [ ] Undefined-behavior sanitizer where supported.
- [ ] Leak checks for FFI/JNI lifecycle harness.
- [ ] Thread sanitizer if multi-threaded adapter code warrants it.

## 23.4 Failure preservation

- [ ] Every crash or mismatch gets a minimized seed/input.
- [ ] Add regression before closing the defect.
- [ ] Store corpus inputs under a documented path.

**Task 23 gate:** Core parsers/state transitions survive fuzz smoke gates, FFI lifecycle has no known leak/UB, and all minimized failures are permanent regressions.

---

# Task 24: Performance hardening and regression budgets

## 24.1 Baseline benchmark suite

- [ ] leaper attacks;
- [ ] sliding attacks;
- [ ] legal move generation;
- [ ] make/unmake;
- [ ] full and incremental hash;
- [ ] evaluation;
- [ ] perft positions;
- [ ] fixed-node search set;
- [ ] TT probe/store;
- [ ] cancellation latency;
- [ ] FFI legal-move/search calls.

## 24.2 Profiling

- [ ] Profile release perft.
- [ ] Profile fixed-node search.
- [ ] Identify allocation counts.
- [ ] Confirm no recursive board clone.
- [ ] Confirm no normal-evaluation trace allocation.
- [ ] Confirm no string key construction in search.

## 24.3 Optimizations after measurement

Potential optimizations, only if justified:

- [ ] direct legal generation with check/pin masks;
- [ ] faster sliding attacks;
- [ ] static exchange evaluation;
- [ ] incremental evaluation components;
- [ ] compact move-list storage;
- [ ] TT packing improvements.

## 24.4 Regression policy

- [ ] Record reference hardware/toolchain.
- [ ] Establish stable medians and variance.
- [ ] Define acceptable regression tolerance.
- [ ] Add non-flaky CI or scheduled performance comparison.
- [ ] Keep correctness gates independent and mandatory.

## 24.5 Android measurements

- [ ] AArch64 nodes/second.
- [ ] peak memory by hash size.
- [ ] cancellation latency.
- [ ] JNI overhead.
- [ ] lifecycle stability.
- [ ] sample app main-thread compliance.

**Task 24 gate:** Performance is measured, bounded, and protected; optimizations do not weaken exact perft, restoration, hash, or differential results.

---

# Task 25: Complete CI, documentation, and developer workflows

## 25.1 CI matrix

- [ ] Linux debug tests.
- [ ] Linux release tests/perft.
- [ ] Clippy all targets/features.
- [ ] rustdoc.
- [ ] AArch64 cross-build.
- [ ] Android AArch64 build.
- [ ] JNI smoke/instrumented job where infrastructure supports it.
- [ ] Miri subset.
- [ ] sanitizer job.
- [ ] fuzz smoke job.
- [ ] slow/nightly perft.
- [ ] optional strength/performance scheduled job.
- [ ] keep Python validation until migration signoff.

## 25.2 Documentation

- [ ] workspace architecture;
- [ ] coordinate system;
- [ ] move encoding;
- [ ] position invariants;
- [ ] make/unmake;
- [ ] FEN and move notation;
- [ ] draw semantics;
- [ ] hashing/repetition;
- [ ] search and score convention;
- [ ] TT policy;
- [ ] evaluation terms and weights;
- [ ] UCI usage;
- [ ] C ABI ownership;
- [ ] Android integration;
- [ ] perft/differential/fuzz commands;
- [ ] self-play/tuning reproducibility.

## 25.3 Developer commands

- [ ] One documented bootstrap command.
- [ ] One fast validation command.
- [ ] One full validation command.
- [ ] One perft command.
- [ ] One UCI run command.
- [ ] One Android build command.
- [ ] One self-play command.
- [ ] One tuning command.

## 25.4 Generated artifacts

- [ ] Do not commit transient benchmark/output files unintentionally.
- [ ] Version schemas and fixtures intentionally.
- [ ] Document generated Zobrist/book/weight artifacts.

**Task 25 gate:** A new developer can build, test, run UCI, run perft, and build Android integration from repository documentation.

---

# Task 26: v0.1 functional-engine signoff

Complete every v0.1 item from the specification.

## 26.1 Rules signoff

- [ ] strict FEN;
- [ ] legal move generation;
- [ ] special moves;
- [ ] exact make/unmake;
- [ ] correct hash;
- [ ] mate/stalemate;
- [ ] claimable/automatic draws;
- [ ] exact perft suite;
- [ ] differential corpus clean.

## 26.2 Search signoff

- [ ] baseline evaluator;
- [ ] reference search;
- [ ] negamax alpha-beta;
- [ ] quiescence;
- [ ] ordering;
- [ ] TT;
- [ ] iterative deepening;
- [ ] aspiration recovery;
- [ ] legal PV;
- [ ] responsive cancellation;
- [ ] deterministic fixed-limit result.

## 26.3 Adapter signoff

- [ ] UCI integration suite;
- [ ] safe Rust API documentation/tests;
- [ ] C ABI lifecycle suite;
- [ ] Android JNI smoke.

## 26.4 Quality signoff

- [ ] format;
- [ ] Clippy;
- [ ] all workspace tests;
- [ ] release perft;
- [ ] docs;
- [ ] cross-builds;
- [ ] no prohibited port pattern;
- [ ] no unresolved P0/P1 correctness defect.

## 26.5 Evidence report

- [ ] Create `docs/RUST_CHESS_ENGINE_V0_1_IMPLEMENTATION_REPORT.md`.
- [ ] Include exact commit SHA.
- [ ] Include exact command outputs.
- [ ] Include perft table.
- [ ] Include differential corpus statistics.
- [ ] Include benchmark environment/results.
- [ ] Include UCI transcript.
- [ ] Include C ABI/JNI evidence.
- [ ] Include known limitations and deferred features.

**Task 26 gate:** The Rust engine is a correct, playable, portable v0.1 chess engine and can become the preferred implementation for new integrations.

---

# Task 27: Full port-program signoff

This final task covers retained good-list capabilities intentionally scheduled after the first playable engine.

## 27.1 Optional capability completion

- [ ] opening-book abstraction and backend;
- [ ] self-play tool;
- [ ] versioned position dataset;
- [ ] named-schema tuning;
- [ ] candidate-versus-baseline validation;
- [ ] accepted advanced evaluation terms;
- [ ] performance regression controls;
- [ ] sustained Android lifecycle and performance evidence.

## 27.2 Migration decision

- [ ] Decide whether Python remains supported, becomes reference-only, or is archived.
- [ ] Update README to identify the authoritative engine.
- [ ] Preserve Python history and useful fixtures.
- [ ] Do not delete Python implementation without a separate reviewed migration task.

## 27.3 Final implementation report

- [ ] Create `docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md`.
- [ ] Map every specification section to implementation paths and tests.
- [ ] Map every TODO checkbox to evidence.
- [ ] List all Python concepts retained, redesigned, and rejected.
- [ ] Record final crate/API versions.
- [ ] Record Linux and Android build/test evidence.
- [ ] Record self-play/tuning schema versions.
- [ ] Record performance baselines.
- [ ] Record remaining deferred roadmap items.

## 27.4 Final release gate

- [ ] Exact final SHA passes all required CI.
- [ ] No documentation-only follow-up commit is used to claim code evidence from another SHA without explicit mapping.
- [ ] All P0/P1 issues are closed.
- [ ] Known P2/P3 issues are documented and do not invalidate stated guarantees.
- [ ] The full port is declared complete only in the implementation report and README after all evidence is available.

**Task 27 gate:** Everything retained from the good-items list and additional-features list is implemented, validated, documented, or explicitly rejected with evidence under the final Rust architecture.

---

## Completion-note template

Use this structure under each completed major task:

```text
Completion note:
- Commit: <full SHA>
- Files: <key implementation and test paths>
- Commands: <exact commands>
- Results: <exact pass counts/perft/benchmarks>
- Evidence: <artifact paths or CI run URLs>
- Deviations: <spec deviation and rationale, or "none">
- Remaining risks: <known risks, or "none">
```

Do not replace evidence with a narrative assertion that a task is complete.
