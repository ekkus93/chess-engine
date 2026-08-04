# Rust Chess Engine Port Specification

**Status:** Implementation specification  
**Date:** 2026-08-01  
**Target branch:** `master`  
**Primary implementation language:** Rust  
**Source reference:** Existing Python implementation under `chess_game/`

---

## 1. Purpose

This document defines the architecture, behavior, quality requirements, and acceptance contract for replacing the current Python chess engine with a new portable Rust engine.

This is **not** a line-by-line translation and is **not** a compatibility port of the Python API. The Python project is a behavioral reference, test source, failure-history source, and catalogue of ideas. The Rust implementation becomes the new authoritative engine architecture.

The Rust engine must retain the useful lessons from the Python implementation:

- correctness-first rules work;
- complete legal move support;
- FEN and UCI move notation;
- iterative-deepening alpha-beta search;
- quiescence search;
- transposition-table bounds;
- deterministic operation;
- diagnostics;
- classical evaluation concepts;
- optional opening-book support;
- offline self-play and tuning;
- strong automated testing.

The Rust engine must not reproduce the Python implementation's major liabilities:

- clone-per-child search;
- nested Python object graphs;
- multiple move representations;
- string position keys;
- rules, UI, persistence, and search state mixed into one `Board` object;
- permissive or ambiguous parsing;
- incorrect dead-position and insufficient-material shortcuts;
- castling safety checks performed against the wrong transient board state;
- heuristic patches derived from individual review transcripts;
- platform-global mutable state;
- implicit filesystem-based engine configuration.

---

## 2. Product goals

The completed system must provide:

1. A correct and testable chess rules core.
2. A usable classical chess engine that selects legal moves and produces principal variations.
3. A portable Rust API that can be used on Linux, Android, and other `std`-capable Rust targets.
4. A standalone UCI executable for Linux and desktop chess software.
5. A narrow C ABI and Android JNI adapter that do not expose Rust internals.
6. Optional opening-book, self-play, and parameter-tuning tooling outside the core.
7. Deterministic and reproducible behavior when configured for deterministic operation.
8. Bounded memory usage and responsive search cancellation.
9. A migration path that allows the Python implementation to remain available as a comparison oracle during development.

---

## 3. Non-goals for the initial port

The initial Rust port does not require:

- Python API compatibility;
- Textual TUI compatibility;
- recreation of the current Python CLI;
- multi-threaded search;
- NNUE or another neural evaluator;
- Syzygy tablebases;
- distributed search;
- cloud services;
- network play;
- `no_std` support;
- every Python evaluation or move-ordering heuristic;
- transcript-specific move preferences;
- automatic import of existing Python tuned-weight files;
- immediate removal of the Python implementation.

These features may be added after the Rust engine satisfies the release gates in this specification.

---

## 4. Governing design principles

### 4.1 Correctness before strength

Legal move generation, state transitions, draw rules, make/unmake, and hashing must be proven before engine-strength work is accepted.

### 4.2 One source of truth

The position representation owns piece placement. Piece values must not separately store their current square.

### 4.3 Illegal states should be difficult to represent

Use enums, newtypes, validated constructors, and private fields. Do not use sentinel values and `Option` for the same concept simultaneously.

### 4.4 Search must be reversible

Search uses in-place make/unmake with a complete undo record. Position cloning is allowed in tests and high-level application code, but not as the normal recursive search mechanism.

### 4.5 Core logic must be platform-neutral

The core must not read files, print to terminals, own UI state, start application threads, or call process-exit functions.

### 4.6 Explicit configuration

Engine behavior must not change because an optional file happens to exist. Weights, books, hash size, randomness, and search limits are provided explicitly.

### 4.7 Determinism by default

Equal-score move selection must be stable by default. Randomness is opt-in and seedable.

### 4.8 Objective tests over anecdotal patches

A move-choice regression must be based on a demonstrable tactic, mate, score property, perft result, or curated test suite. A disliked self-play move alone is not sufficient reason to add a special-case heuristic.

---

## 5. Workspace architecture

The Rust implementation must use a Cargo workspace with these logical crates. Exact package names may use hyphens in `Cargo.toml` and underscores in Rust paths.

```text
crates/
  chess-core/       Position, pieces, moves, attacks, legal move generation,
                    make/unmake, FEN, hashing, game-rule primitives
  chess-search/     Evaluation, alpha-beta search, quiescence, TT,
                    move ordering, limits, diagnostics, PV
  chess-uci/        Standalone UCI executable and protocol adapter
  chess-ffi/        Stable C ABI, opaque handles, serialization helpers
  chess-jni/        Android JNI adapter over the safe Rust engine API
  chess-tools/      Perft, divide, benchmark, fixture generation, self-play CLI
  chess-tune/       Offline evaluation-dataset and tuning utilities
```

The first implementation may temporarily place `chess-tools` and `chess-tune` functionality in fewer crates, but the dependency boundaries below are mandatory.

### 5.1 Dependency direction

Allowed high-level dependency direction:

```text
chess-core
   ↑
chess-search
   ↑            ↑
chess-uci    chess-ffi
                 ↑
              chess-jni

chess-tools → chess-core + chess-search
chess-tune  → chess-core + chess-search
```

Forbidden dependencies:

- `chess-core` must not depend on search, UCI, FFI, JNI, tuning, or UI code.
- `chess-search` must not depend on UCI, JNI, Android, filesystem-specific book loading, or application UI.
- `chess-ffi` and `chess-jni` must not expose internal references or layouts.
- Core crates must not depend on the Python implementation at runtime.

### 5.2 Unsafe code policy

- `chess-core` and `chess-search` should use `#![forbid(unsafe_code)]` unless a separately reviewed optimization proves necessary.
- Unsafe code is permitted at FFI boundaries only when narrowly scoped, documented, tested, and covered by sanitizers or Miri where applicable.
- A performance claim alone is not sufficient to add unsafe code before a benchmark demonstrates a meaningful need.

---

## 6. Target platforms

The supported initial targets are:

- Linux x86-64;
- Linux AArch64;
- Android AArch64;
- host-platform unit-test builds used by CI.

The architecture must not prevent future support for:

- macOS;
- iOS through the C ABI;
- Windows;
- WebAssembly with a platform-specific search adapter.

`no_std` is deferred. The portable core may use Rust `std`, but it must avoid OS-specific APIs, process globals, and direct filesystem access.

---

## 7. Core value types

### 7.1 Color

```rust
pub enum Color {
    White,
    Black,
}
```

Required operations:

- `opposite()`;
- stable index conversion for tables;
- pawn push direction;
- home rank, pawn start rank, and promotion rank helpers.

### 7.2 Piece kind and piece

```rust
pub enum PieceKind {
    Pawn,
    Knight,
    Bishop,
    Rook,
    Queen,
    King,
}

pub struct Piece {
    pub color: Color,
    pub kind: PieceKind,
}
```

There is no `Empty` piece kind. Empty occupancy is represented only by the position container.

A `Piece` must not contain a square field.

### 7.3 Square

Use a compact validated square:

```rust
#[repr(transparent)]
pub struct Square(u8);
```

Required contract:

- valid range is `0..64`;
- canonical mapping is `a8 = 0`, `h8 = 7`, `a1 = 56`, `h1 = 63`;
- row/rank and file conversions are explicit;
- algebraic parsing and formatting round-trip;
- unchecked construction is private or limited to audited internal code.

The existing Python row convention is retained behaviorally, but the Python `RowConstant`, `ColConstant`, and compatibility arithmetic are not retained.

### 7.4 Move

The engine must have one canonical compact move representation. A packed `u16` or `u32` is acceptable.

The representation must preserve:

- source square;
- destination square;
- promotion identity;
- enough move-kind information to execute and unexecute castling, en passant, double pawn pushes, captures, and promotions efficiently.

The public API may expose accessors, but callers must not depend on the bit layout.

Recommended semantic move kinds:

```rust
pub enum MoveKind {
    Quiet,
    DoublePawnPush,
    KingCastle,
    QueenCastle,
    Capture,
    EnPassant,
    KnightPromotion,
    BishopPromotion,
    RookPromotion,
    QueenPromotion,
    KnightPromotionCapture,
    BishopPromotionCapture,
    RookPromotionCapture,
    QueenPromotionCapture,
}
```

There must not be separate tuple, `Move`, and `LegalMove` identities inside the engine.

---

## 8. Position representation

The required initial representation is a hybrid mailbox and bitboard position:

```rust
pub struct Position {
    mailbox: [Option<Piece>; 64],
    pieces: [[Bitboard; 6]; 2],
    occupancy: [Bitboard; 2],
    all_occupancy: Bitboard,
    king_squares: [Square; 2],

    side_to_move: Color,
    castling_rights: CastlingRights,
    en_passant: Option<Square>,
    halfmove_clock: u16,
    fullmove_number: u16,
    zobrist: u64,
}
```

Equivalent private layouts are allowed if they preserve the same capabilities and invariants.

### 8.1 Why hybrid

- Bitboards provide efficient attacks, occupancy operations, mobility, pins, and evaluation.
- The mailbox provides direct piece lookup and simplifies FFI, diagnostics, and move execution.
- Redundant structures are acceptable only because they are private and checked against each other.

### 8.2 Position invariants

For every valid `Position`:

1. Mailbox and piece bitboards describe the same pieces.
2. White and black occupancy do not overlap.
3. `all_occupancy == occupancy[White] | occupancy[Black]`.
4. Each normal playable position contains exactly one king per side.
5. Cached king squares point to the matching kings.
6. Side to move is defined.
7. Castling rights are a four-bit state independent of current occupancy.
8. En-passant state is either absent or a valid target square.
9. Halfmove and fullmove counters are in their supported ranges.
10. Incremental Zobrist hash equals a full recomputation.

Debug-only invariant checks must be available and used after make/unmake in tests.

### 8.3 Position versus game

`Position` stores the state needed to generate and search moves. It does not own a user-facing move list, draw claims, PGN tags, UI text, or terminal rendering.

A separate `Game` type owns:

- current `Position`;
- played move history;
- position-hash history;
- repetition counts or an equivalent reversible history mechanism;
- claimable draw information;
- game result;
- future PGN metadata.

Search receives the root game history needed for repetition and maintains a separate reversible search-line history.

---

## 9. FEN and move notation

### 9.1 FEN

The engine must support all six standard FEN fields:

1. piece placement;
2. active color;
3. castling availability;
4. en-passant target;
5. halfmove clock;
6. fullmove number.

The default public parser is strict:

- exactly eight ranks;
- exactly eight files per rank;
- only valid piece characters;
- active color must be `w` or `b`;
- castling field must be syntactically valid and contain no duplicates;
- en-passant field must be `-` or a valid square on the expected target ranks;
- counters must be valid non-negative integers and fullmove number must be at least one;
- exactly one king per side for a playable position;
- no pawns on the first or eighth ranks unless a separate analysis-position mode explicitly permits it;
- invalid text returns a structured error and never partially mutates an existing position.

A separate analysis or lenient mode may later allow syntactically valid but unreachable positions. It must be explicit and must not silently change strict parsing.

`to_fen()` must emit a canonical six-field FEN.

### 9.2 UCI coordinate moves

The engine must parse and format:

- `e2e4`;
- `g1f3`;
- `e7e8q`;
- `e7e8r`;
- `e7e8b`;
- `e7e8n`.

Parsing establishes move syntax, not legality. Resolution against a position must return exactly one matching legal move or a structured error.

Promotion must be explicit in engine-internal legal moves. UI adapters may offer queen as a user convenience before calling the core.

### 9.3 SAN and PGN

SAN generation/parsing and PGN import/export are useful but deferred until after the v0.1 release gate. The architecture must not prevent them.

---

## 10. Attack generation

`chess-core` must provide reusable attack primitives:

- precomputed pawn attacks for each color and square;
- precomputed knight attacks;
- precomputed king attacks;
- rook sliding attacks for arbitrary occupancy;
- bishop sliding attacks for arbitrary occupancy;
- queen attacks as rook plus bishop attacks;
- ray, between-square, and line tables where useful;
- attackers-to-square queries;
- checker detection;
- pinned-piece detection or equivalent legal-generation support.

Sliding attacks may initially use audited ray scans. Magic bitboards, PEXT, or another accelerated scheme may be introduced only after correctness and baseline benchmarks exist.

Attack functions must distinguish attack geometry from legal moves. Pawn attacks, for example, are diagonal regardless of target occupancy.

---

## 11. Move generation

### 11.1 Pseudo-legal generation

The generator must produce pseudo-legal moves for the side to move, including:

- pawn single and double pushes;
- pawn captures;
- all promotion and promotion-capture choices;
- en-passant candidates;
- knight moves;
- bishop, rook, and queen moves;
- king moves;
- castling candidates.

### 11.2 Legal generation

Legal move generation must reject moves that leave the moving side's king in check.

The implementation may use either:

- direct legal generation using checkers, pins, and evasion masks; or
- pseudo-legal generation followed by make/check/unmake.

The first correctness milestone may use the second approach. A later optimization may introduce direct legal generation if it remains behaviorally identical.

### 11.3 Check states

The generator must correctly handle:

- no check;
- single check;
- double check;
- pinned pieces;
- discovered checks;
- king captures into attacked squares;
- interpositions;
- captures of checking pieces;
- en-passant moves that expose a rook or bishop attack on the moving king.

Kings are never capturable pieces. Checkmate is represented by no legal moves while in check.

---

## 12. Special-move rules

### 12.1 Castling

Castling is legal only when all required conditions hold:

- corresponding castling right exists;
- king is on its required starting square;
- correct rook is on its required starting square;
- required path squares are empty;
- king is not currently in check;
- king does not cross an attacked square;
- king does not finish on an attacked square.

Attack checks for transit and destination must use position states that do not incorrectly retain the king as a blocker on its original square. Tests must include sliding attacks revealed when the king vacates its source square.

Castling-right updates must handle:

- king moves;
- rook moves from original squares;
- rook captures on original squares;
- make/unmake restoration.

### 12.2 En passant

En passant requires:

- a valid current en-passant target;
- a correctly placed capturing pawn;
- the expected opposing pawn behind the target;
- correct pawn attack geometry;
- king safety after both the moving pawn and captured pawn are removed from their original squares.

The position may retain a FEN en-passant target after a double pawn push, but repetition hashing must include an en-passant component only when it changes the legal move set according to the engine's canonicalization policy.

### 12.3 Promotion

Legal generation must produce all four choices:

- queen;
- rook;
- bishop;
- knight.

Quiet and capturing promotions must remain distinct moves. The core must not silently promote to queen when an internal move omits promotion identity.

---

## 13. Make and unmake

Search and perft must use reversible in-place transitions:

```rust
pub fn make_move(&mut self, mv: Move) -> Result<Undo, MoveError>;
pub fn unmake_move(&mut self, mv: Move, undo: Undo);
```

For already generated legal moves, an internal optimized path may avoid redundant legality validation:

```rust
pub(crate) fn make_legal_move(&mut self, mv: Move) -> Undo;
```

### 13.1 Undo record

The undo record must restore everything changed by a move, including:

- captured piece and captured square;
- prior castling rights;
- prior en-passant state;
- prior halfmove clock;
- prior fullmove number if not derivable safely;
- prior Zobrist hash or enough information to reverse it;
- promotion state;
- rook movement during castling;
- cached king squares and all occupancy structures.

### 13.2 Restoration contract

For every legal move:

```text
before == position
undo = make(move)
unmake(move, undo)
position == before
```

Equality for this test includes every field, occupancy structure, counter, and hash.

A failed public move application must not partially mutate the position.

---

## 14. Game status and draw rules

The API must distinguish ongoing play, checkmate, stalemate, automatic draws, and claimable draws.

Recommended shape:

```rust
pub enum GameStatus {
    Ongoing,
    Checkmate { winner: Color },
    Stalemate,
    AutomaticDraw(DrawReason),
    ClaimableDraw(DrawReason),
}

pub enum DrawReason {
    ThreefoldRepetition,
    FivefoldRepetition,
    FiftyMoveRule,
    SeventyFiveMoveRule,
    DeadPosition,
}
```

Required semantics:

- threefold repetition is claimable;
- fivefold repetition is automatic;
- fifty-move rule is claimable;
- seventy-five-move rule is automatic;
- stalemate is automatic;
- dead position is automatic;
- checkmate takes precedence when the final move also reaches an automatic move-count threshold.

The engine may expose an `insufficient_mating_material` helper, but it must be a conservative subset of dead-position detection and must not reproduce the Python implementation's broad incorrect classifications.

In particular, the implementation must not assume:

- all two-bishop positions are dead;
- all two-knight positions are dead;
- every two-minor-piece position is insufficient.

Where exact dead-position determination is intentionally conservative, the API and tests must document what is and is not detected. It must never declare a legally mate-reachable position automatically drawn.

---

## 15. Zobrist hashing and repetition

### 15.1 Hash components

The position hash must include:

- piece type, color, and square;
- side to move;
- castling-right state;
- canonical en-passant component when relevant.

Halfmove and fullmove counters are not part of the transposition/repetition position identity.

### 15.2 Incremental correctness

Every make/unmake operation updates the hash incrementally. Tests must compare the incremental result against full recomputation after:

- quiet moves;
- captures;
- double pawn pushes;
- en passant;
- castling;
- promotions;
- promotion captures;
- rook captures affecting castling rights.

### 15.3 Repetition history

The root game supplies prior position hashes. Search maintains a stack of line hashes and reversible occurrence information without constructing strings or allocating a growing tuple per node.

Repetition detection must respect irreversible boundaries where applicable, but correctness takes priority over micro-optimization.

---

## 16. Search architecture

### 16.1 Score convention

Internally, search uses integer scores from the perspective of the side to move. Negamax is mandatory for the primary recursive search.

Use reserved mate-score bands and ply-relative mate distances. External APIs must distinguish ordinary centipawn evaluation from mate scores.

Recommended public form:

```rust
pub enum Score {
    Centipawns(i32),
    MateIn(u16),
    MatedIn(u16),
}
```

### 16.2 Core search

The initial search must include:

- negamax alpha-beta;
- iterative deepening;
- aspiration windows with full-window recovery;
- quiescence search;
- fixed-capacity transposition table;
- TT, capture, promotion, killer, and history move ordering;
- deterministic equal-score selection;
- repetition and draw handling;
- mate-distance scoring;
- optional bounded check extensions;
- search diagnostics;
- cancellation and time/node limits;
- principal variation reconstruction.

### 16.3 Reference search

A simple no-prune negamax or minimax reference must remain available under tests or tools for shallow equivalence checks. It is not part of the performance path.

### 16.4 Deferred search features

The following are deferred until the baseline search is proven:

- null-move pruning;
- late-move reductions;
- futility pruning;
- razoring;
- singular extensions;
- multi-threaded search;
- pondering;
- multi-PV;
- endgame tablebases.

They must not be added in a way that obscures baseline correctness failures.

---

## 17. Quiescence search

Quiescence must:

- evaluate stand-pat only when the side to move is not in check;
- search all legal evasions when in check;
- search legal captures and promotions;
- order tactical moves using inexpensive tactical ordering;
- use alpha-beta bounds;
- obey cancellation;
- use bounded depth or another explicit explosion guard;
- return mate and draw scores consistently with the main search;
- maintain repetition history correctly.

Optional checks in quiescence may be added later only with benchmarks and tactical regression coverage.

---

## 18. Move ordering

Initial ordering priority should be:

1. transposition-table move;
2. previous principal-variation move;
3. winning or high-value captures;
4. promotions;
5. killer moves;
6. history-heuristic quiet moves;
7. stable encoded-move ordering as the final deterministic tie-break.

Capture ordering may begin with MVV-LVA and later use static exchange evaluation.

Move ordering must not introduce a second large strategic evaluator. The following Python-derived categories are explicitly excluded from the initial Rust ordering layer:

- review-loop penalties;
- anti-drift scenarios;
- transcript-specific opening preferences;
- hard-coded exact piece-count windows;
- special handling for individual self-play failures;
- root bonuses capable of overriding a strictly better exact search score.

A root tie-break may choose between genuinely equal exact scores. It must never promote a move whose exact score is worse.

---

## 19. Transposition table

The TT must be fixed-capacity and configured by memory size.

Each logical entry must include:

- verification key or sufficient hash fragment;
- search depth;
- normalized score;
- bound type: exact, lower, or upper;
- best move;
- age/generation;
- optional static evaluation if later justified.

Requirements:

- mate scores are normalized on store and denormalized on probe;
- bound use respects requested depth and alpha-beta window;
- repetition-sensitive nodes are handled safely;
- replacement is depth-preferred with age awareness or an equivalent documented policy;
- clearing or advancing generation is explicit;
- memory use is bounded and observable;
- the initial implementation may be single-threaded.

The engine must not use an unbounded hash map as its production TT.

---

## 20. Iterative deepening, limits, and cancellation

### 20.1 Limits

```rust
pub struct SearchLimits {
    pub max_depth: Option<u16>,
    pub max_nodes: Option<u64>,
    pub soft_time: Option<Duration>,
    pub hard_time: Option<Duration>,
    pub infinite: bool,
}
```

Additional UCI time-control fields may be resolved by the UCI adapter into these limits.

### 20.2 Cancellation

Search must periodically check:

- an atomic stop flag;
- hard deadline;
- node limit.

It must stop inside a search depth, not only between completed iterations.

The returned result must use the best move from the last fully completed iteration unless no iteration completed, in which case it must return a legal fallback or an explicit incomplete result according to the API contract.

### 20.3 Time management

The UCI adapter must not convert time directly into a fixed depth. It must calculate soft and hard budgets from remaining time, increment, moves-to-go, and safety reserve.

The initial algorithm may be simple but must be documented and covered by deterministic unit tests.

---

## 21. Search result and diagnostics

Recommended result:

```rust
pub struct SearchResult {
    pub best_move: Option<Move>,
    pub ponder: Option<Move>,
    pub score: Score,
    pub completed_depth: u16,
    pub selective_depth: u16,
    pub nodes: u64,
    pub quiescence_nodes: u64,
    pub elapsed: Duration,
    pub principal_variation: Vec<Move>,
    pub termination: SearchTermination,
}
```

Diagnostics must support at least:

- nodes;
- quiescence nodes;
- cutoffs;
- TT probes and hits;
- exact and bound TT hits;
- aspiration fail-high and fail-low counts;
- root re-searches;
- completed depth timing;
- selective extensions;
- tactical move width where useful;
- nodes per second.

Instrumentation must be optional and low-overhead when disabled.

---

## 22. Evaluation

### 22.1 Initial evaluator

The first accepted evaluator must be intentionally compact and include:

- material;
- tapered middlegame/endgame piece-square tables;
- mobility;
- pawn structure, including isolated, doubled, passed, and connected pawns;
- bishop pair;
- rook activity on open/semi-open files and seventh rank;
- king safety appropriate to game phase;
- space or central control;
- passed-pawn advancement;
- endgame king activity.

Every component must be color-symmetric unless a documented rule makes symmetry inappropriate.

### 22.2 Excluded evaluator content

Do not initially port the large family of narrow Python guidance modules, including review-loop, anti-drift, opponent-plan, transcript-practicality, and highly specific endgame scenario patches.

A future evaluation term requires:

- a concise chess definition;
- isolated tests;
- symmetry review;
- benchmark cost measurement;
- strength evidence from a controlled match or suite;
- proof that it does not duplicate an existing term excessively.

### 22.3 Evaluation trace

A debug-only or opt-in `EvalTrace` must expose named component totals. Normal search must not allocate maps or strings for every evaluation.

### 22.4 Weights

Weights must use named, versioned schemas. Persisted files must include:

- schema version;
- engine/evaluator version;
- parameter names;
- values;
- optional training metadata and checksum.

The engine must reject unknown incompatible versions. It must not infer compatibility from flat list length or dataclass/struct field order.

Weights are provided explicitly through configuration or an adapter. The core does not search the filesystem automatically.

---

## 23. Opening book

Opening-book support is optional and outside the search core.

Define a narrow abstraction such as:

```rust
pub trait OpeningBook {
    fn candidates(&self, position: &Position) -> Result<Vec<BookMove>, BookError>;
}
```

Requirements:

- book moves are resolved and validated against legal moves;
- deterministic highest-weight selection is supported;
- weighted-random selection is opt-in and seedable;
- corrupt or unsupported data fails loudly;
- no filesystem or JSON parser dependency is required by `chess-core` or `chess-search`;
- absence of a book is normal and does not affect search correctness.

A Polyglot-compatible backend or a versioned project-specific indexed format may be added later.

---

## 24. UCI adapter

`chess-uci` must implement a usable subset of Universal Chess Interface sufficient for common chess GUIs:

- `uci`;
- `isready`;
- `ucinewgame`;
- `setoption` for supported options;
- `position startpos [moves ...]`;
- `position fen <six fields> [moves ...]`;
- `go depth`;
- `go nodes`;
- `go movetime`;
- `go wtime/btime/winc/binc/movestogo`;
- `go infinite`;
- `stop`;
- `quit`;
- periodic `info` lines;
- `bestmove`, with optional ponder move.

At minimum, configurable options should include:

- hash size;
- deterministic mode or random seed if exposed;
- opening-book enablement when a backend exists.

Protocol responsibilities belong to the adapter. The adapter must not redirect process-global stdout or use module-global mutable search state.

Search should run on an adapter-owned worker thread when asynchronous UCI behavior is required. Ownership and shutdown must be explicit.

---

## 25. Portable API and FFI

### 25.1 Safe Rust API

Provide a high-level engine facade:

```rust
pub struct Engine {
    game: Game,
    searcher: Searcher,
}

impl Engine {
    pub fn new(config: EngineConfig) -> Result<Self, EngineError>;
    pub fn set_position(&mut self, fen: &str, moves: &[&str]) -> Result<(), EngineError>;
    pub fn fen(&self) -> String;
    pub fn legal_moves(&self) -> Vec<Move>;
    pub fn play_move(&mut self, mv: Move) -> Result<GameStatus, EngineError>;
    pub fn search(&mut self, limits: SearchLimits) -> Result<SearchResult, EngineError>;
    pub fn stop_handle(&self) -> SearchStopHandle;
}
```

Exact signatures may evolve, but the semantics and ownership rules must remain clear.

### 25.2 C ABI

`chess-ffi` must expose opaque handles and owned buffers. It must not expose Rust enums, slices, vectors, references, trait objects, or struct layouts directly.

Required characteristics:

- explicit create/destroy functions;
- explicit error retrieval or result codes;
- UTF-8 string inputs with lengths;
- engine-owned outputs copied into caller-owned buffers or returned through explicit free functions;
- no unwinding across FFI boundaries;
- null and invalid-handle checks;
- ABI version query;
- thread-safety contract documented per function.

### 25.3 Android JNI

`chess-jni` provides Kotlin-friendly wrappers for:

- engine creation and destruction;
- position setup;
- legal moves;
- move application;
- search start/result;
- cancellation;
- status and error reporting.

Search must not block the Android main thread. The Kotlin application owns coroutine/thread scheduling; the core owns only the search computation and cancellation token.

The JNI layer must catch Rust panics, convert errors predictably, and release native resources deterministically.

---

## 26. Configuration and identity

Recommended configuration:

```rust
pub struct EngineConfig {
    pub hash_mb: usize,
    pub deterministic: bool,
    pub random_seed: Option<u64>,
    pub evaluation: EvaluationConfig,
    pub opening_book: BookPolicy,
}
```

The engine must expose:

- engine semantic version;
- evaluator schema/version identifier;
- active weight-set identifier or checksum;
- build target where useful;
- deterministic configuration.

Self-play records and benchmark artifacts must include these identifiers.

---

## 27. Self-play and tuning

Self-play and tuning are offline tools, not runtime core behavior.

### 27.1 Self-play

Self-play tools must support:

- fixed seeds;
- explicit engine configurations for each side;
- opening diversification through a supplied book or opening set;
- configurable limits;
- adjudication settings recorded in output;
- game records with engine/evaluator identifiers;
- deterministic replay where inputs permit it;
- draw and maximum-ply policies that do not silently label discarded games as valid draws unless explicitly configured.

### 27.2 Position dataset

Datasets must be versioned and include at least:

- FEN or another lossless position encoding;
- game outcome;
- side to move;
- source game identifier;
- ply;
- engine/version metadata;
- filtering metadata.

Training and validation splits must be explicit. Duplicate and near-duplicate position handling must be defined.

### 27.3 Tuning

Texel-style tuning may be retained, but the new pipeline must:

- use named parameter schemas;
- calibrate logistic scaling explicitly;
- fail on empty or malformed datasets;
- preserve initial and final loss reports;
- keep training and validation data separate;
- save complete metadata;
- validate tuned weights in controlled candidate-versus-baseline matches;
- never auto-activate a tuned file merely because it exists.

Depth-one self-play generated and labeled by the same evaluator is not sufficient as the sole evidence for improved weights.

---

## 28. Error handling and panic policy

Public APIs must use structured errors for at least:

- malformed FEN;
- invalid square or move notation;
- illegal move;
- incompatible weight schema;
- corrupt opening-book data;
- invalid configuration;
- search already running;
- search cancellation where represented as an error;
- invalid FFI handle or buffer;
- internal invariant failure in non-debug production paths.

Core libraries must not print errors, call `process::exit`, or silently return a default position after malformed input.

Panics indicate programmer defects. No panic may unwind across C or JNI boundaries.

---

## 29. Determinism and reproducibility

In deterministic mode, identical inputs and configuration must produce identical:

- legal move order where externally observed;
- search best move;
- score;
- completed principal variation for a fixed depth/node limit;
- self-play result when all randomness is seeded and resource limits are deterministic.

Do not use process-global RNG state. Opening-book randomness, self-play randomness, and optional equal-score variety must use explicit local generators.

Wall-clock searches are not required to produce identical depths across machines, but must remain legal, cancellable, and internally consistent.

---

## 30. Testing strategy

### 30.1 Unit tests

Cover every value type, parser, attack primitive, state transition, evaluator component, TT rule, and adapter command.

### 30.2 Authoritative perft

The test suite must include exact perft counts, not smoke-only assertions.

At minimum include the standard positions below through the practical CI depth shown:

#### Starting position

```text
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
D1 20
D2 400
D3 8902
D4 197281
```

#### Kiwipete

```text
r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1
D1 48
D2 2039
D3 97862
D4 4085603
```

#### En-passant and rook-ending stress position

```text
8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1
D1 14
D2 191
D3 2812
D4 43238
```

#### Castling, promotion, checks, and pins stress position

```text
r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1
D1 6
D2 264
D3 9467
D4 422333
```

#### Promotion/check-evasion stress position

```text
rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8
D1 44
D2 1486
D3 62379
D4 2103487
```

#### Tactical positional stress position

```text
r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10
D1 46
D2 2079
D3 89890
D4 3894594
```

Higher-depth counts may run in a slow or nightly job.

A `perft divide` tool must report root move counts to localize failures.

### 30.3 Special-rule regressions

Include direct positions for:

- castling path revealed after the king vacates its source;
- rook capture clearing one castling right;
- en-passant discovered rook/bishop check;
- all four quiet promotions;
- all four capture promotions;
- underpromotion as the only legal or best tactical move;
- double-check king-only evasions;
- pinned-piece restrictions;
- checkmate precedence over the seventy-five-move threshold;
- claimable versus automatic repetition and move-count draws;
- non-dead two-bishop and two-knight examples.

### 30.4 Property-based tests

Required properties:

- FEN parse/serialize round-trip;
- make/unmake byte-for-byte state restoration;
- incremental hash equals recomputed hash;
- every generated legal move is accepted by the legal-move application path;
- every generated legal move leaves the mover's king safe;
- board structures remain internally consistent;
- mirror-and-color-swap evaluation symmetry for applicable terms;
- move encode/decode round-trip.

### 30.5 Differential testing

During development, compare against a trusted external implementation such as `python-chess` or another established legal-move oracle:

1. load identical FENs;
2. compare legal UCI move sets;
3. compare resulting FEN after each move;
4. compare perft counts;
5. run random legal playouts;
6. preserve every discovered mismatch as a fixed Rust regression.

The external oracle is a development/test dependency only.

### 30.6 Fuzzing

Fuzz targets should include:

- FEN parser;
- UCI move parser;
- make/unmake sequences;
- random legal playouts;
- FFI input validation;
- weight and opening-book parsers when implemented.

---

## 31. Benchmarks and performance controls

Benchmark at least:

- attack generation;
- legal move generation;
- make/unmake;
- hash recomputation and incremental update;
- static evaluation;
- starting-position perft;
- Kiwipete perft;
- fixed-node search positions;
- cancellation latency;
- TT probe/store;
- FFI call overhead for representative operations.

Performance gates must begin as recorded baselines. Once stable, CI should reject statistically significant regressions beyond an agreed tolerance.

Android measurements must include at least one AArch64 device or emulator profile and record:

- nodes per second;
- peak native memory for configured hash sizes;
- cancellation latency;
- JNI smoke behavior;
- absence of main-thread blocking in the sample integration.

Correctness must not be weakened to meet a benchmark.

---

## 32. CI quality gates

The Rust workspace must eventually pass:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo test --workspace --all-features
cargo test -p chess-core --release perft
cargo doc --workspace --no-deps
```

Additional jobs should include:

- Linux x86-64 debug tests;
- Linux x86-64 release perft and search tests;
- AArch64 cross-compilation;
- Android target compilation;
- JNI smoke or instrumented test when the Android harness exists;
- Miri for suitable core tests;
- sanitizer jobs for FFI and unsafe boundaries where supported;
- fuzz smoke runs;
- slow perft/strength jobs separated from the fast required gate.

No milestone is complete merely because code compiles.

---

## 33. Documentation requirements

The Rust implementation must include:

- workspace architecture overview;
- coordinate and square mapping;
- move encoding semantics;
- position invariants;
- make/unmake contract;
- repetition and draw semantics;
- search score and mate normalization;
- TT replacement policy;
- evaluation-term definitions;
- C ABI ownership rules;
- Android integration guide;
- UCI usage;
- perft and benchmark commands;
- tuning-data schema and reproducibility requirements.

Public Rust APIs require rustdoc for invariants, errors, ownership, and thread safety.

---

## 34. Python migration policy

The Python engine remains available during the port for:

- behavior comparison;
- fixture extraction;
- identifying previously solved cases;
- documenting known defects that must not be copied.

Rules:

1. New Rust code must not call Python at runtime.
2. Python tests must not be blindly translated when they encode incorrect chess behavior.
3. Existing tuned weights are reference data only and are not automatically compatible.
4. Narrow Python guidance modules are not authoritative design requirements.
5. Rust becomes authoritative only after its release gates pass.
6. Removal or archival of Python code is a separate post-port decision.

---

## 35. Explicitly prohibited port patterns

The Rust implementation must not introduce:

- a piece object that stores its own mutable square;
- both `Empty` and `Option<Piece>` as competing empty-square representations;
- multiple internal move identities;
- clone-per-recursive-child search;
- string-based transposition keys;
- an unbounded production transposition table;
- global mutable search state;
- automatic weight-file discovery;
- UI rendering in `Position` or `Game`;
- process output in core libraries;
- silent queen promotion in internal move execution;
- malformed FEN fallback to a default board;
- draw declarations based on the Python insufficient-material shortcuts;
- root heuristics that override a strictly better exact score;
- transcript-specific heuristic modules without objective evidence;
- FFI unwinding or leaked engine-owned buffers.

---

## 36. v0.1 functional release gate

The Rust engine is considered a functioning v0.1 engine only when all of the following are true:

1. All core types and position invariants are implemented.
2. Strict FEN and UCI move notation work.
3. Complete legal move generation supports castling, en passant, and all promotions.
4. Make/unmake restores exact state and hash.
5. Checkmate, stalemate, claimable draws, and automatic draws follow the documented model.
6. Required perft positions pass exact counts through CI depth.
7. Differential random-play testing has no unresolved mismatch in the accepted corpus.
8. Zobrist hashing and repetition tracking are correct.
9. Negamax alpha-beta, iterative deepening, quiescence, ordering, and TT are implemented.
10. Search produces a legal move, score, depth, diagnostics, and principal variation.
11. Search cancellation works inside a depth and returns a coherent result.
12. The compact baseline evaluator is implemented with trace support.
13. The UCI binary passes protocol integration tests.
14. The safe Rust API is documented and usable independently of UCI.
15. The C ABI and Android JNI smoke tests pass.
16. Formatting, Clippy, tests, release perft, documentation, and platform build gates pass.
17. No prohibited port pattern remains in the accepted implementation.

Opening book, tuning, and advanced evaluation may complete after the first playable engine milestone, but they are required for completion of the full port program defined by the companion TODO.

---

## 37. Full port completion gate

The complete port program is finished only when:

- the v0.1 functional gate passes;
- optional opening-book infrastructure is implemented and tested;
- self-play and versioned dataset tools exist;
- versioned named-weight tuning exists;
- advanced evaluation terms accepted from the good-items list are implemented or explicitly rejected with evidence;
- performance baselines and regression controls exist;
- Android integration documentation and sample usage exist;
- fuzz/property/differential suites run in CI at appropriate cadences;
- migration documentation identifies the Rust engine as authoritative;
- every item in `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md` is complete with recorded evidence.
