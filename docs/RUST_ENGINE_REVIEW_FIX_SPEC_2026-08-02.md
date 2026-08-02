# Rust Engine Review Fix Spec — 2026-08-02

**Status:** Complete  
**Branch:** `rust-engine`  
**Companion TODO:** `docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md`  
**Primary tracker:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Validated implementation SHA:** `81a7cd4a58a52695eca2ede10d5c73c803851d17`

---

## 1. Purpose

This specification defines the corrective pass completed after the comprehensive Rust review of Tasks 0–12 and before Task 13 search implementation.

The pass resolved six findings:

1. `chess-search` needed a safe generated-legal make/unmake API that does not regenerate the legal move list.
2. `Game` lacked explicit reset and set-position operations required by the detailed Task 10 contract.
3. `chess-tools divide` lacked elapsed-time output required by Task 11.3.
4. The live TODO footer still described Task 9 work instead of Task 13 preparation.
5. Task 25's CI, documentation, and command checklist understated completed work.
6. The FEN parser's strict structural analysis-position policy was not explicit.

Task 13 search itself was deliberately excluded. The result is a clean foundation on which reference search and alpha-beta can now be implemented.

---

## 2. Engineering constraints retained

The completed pass preserves these contracts:

- `chess-core` remains independent of search, protocols, adapters, filesystems, and UI.
- `chess-search` depends only on portable core/search support.
- `chess-core` and `chess-search` continue to forbid unsafe code.
- The public raw `Position::make_move(Move)` path remains fully legality checked.
- Production recursive work is still expected to use make/unmake rather than clone-per-child.
- Public failures remain fail-loud and non-mutating.
- Position restoration remains exact across board state, counters, castling, en passant, side to move, cached kings, redundant bitboards, and Zobrist state.
- No automatic weight, configuration, or opening-book loading was added.
- No first-party lint suppression or weakened validation gate was added.
- Task 13 and all later search capabilities remain outside this pass.

---

## 3. Search-safe generated legal move API

### 3.1 Implemented public types

`chess-core` now exposes opaque, source-bound legal move tokens:

```rust
pub struct LegalMoveToken { /* private fields */ }
pub struct LegalMoveTokenList { /* fixed-capacity storage */ }
```

The public API is:

```rust
impl LegalMoveToken {
    pub const fn move_made(self) -> Move;
}

impl LegalMoveTokenList {
    pub const fn len(&self) -> usize;
    pub const fn is_empty(&self) -> bool;
    pub fn get(&self, index: usize) -> Option<LegalMoveToken>;
    pub fn iter(&self) -> impl ExactSizeIterator<Item = LegalMoveToken> + '_;
}

impl Position {
    pub fn legal_move_tokens(
        &mut self,
    ) -> Result<LegalMoveTokenList, LegalMoveError>;

    pub fn make_legal_token(
        &mut self,
        token: LegalMoveToken,
    ) -> Result<PositionUndo, LegalMoveError>;
}
```

### 3.2 Origin binding

Each token binds its exact packed move to the source position's:

- canonical Zobrist key;
- side to move;
- castling rights;
- raw en-passant target;
- halfmove clock;
- fullmove number.

Token fields are private, so external crates cannot construct a fake trusted move.

### 3.3 Application semantics

`Position::make_legal_token`:

1. compares the token origin with the current position;
2. returns `LegalMoveError::LegalMoveTokenMismatch` before mutation on mismatch;
3. delegates valid tokens to the existing reversible generated-legal primitive;
4. returns `PositionUndo` for exact LIFO restoration;
5. does not regenerate the legal move list.

The raw public `Position::make_move(Move)` method remains unchanged for callers without a trusted token.

### 3.4 Storage and ordering

The token list is fixed-capacity and stack-backed, using the same bounded maximum as the move list. Tokens retain deterministic legal generation order and do not introduce a per-move heap allocation.

### 3.5 Cross-crate proof

A `chess-search` test generates a token, applies it, evaluates the child, unmakes it, and proves exact root equality and Zobrist recomputation. This demonstrates that Task 13 can use the public API without reaching into `chess-core` internals.

### 3.6 Regression coverage

Tests cover:

- token identities matching legal move identities;
- starting, castling-heavy, promotion, and en-passant positions;
- valid token make/unmake and exact restoration;
- stale token rejection;
- wrong-position and wrong-side rejection;
- non-mutating failure behavior;
- curated all-token make/invariant/unmake/hash restoration;
- use from the separate `chess-search` crate.

---

## 4. Explicit `Game` root replacement

`Game` now exposes:

```rust
pub fn reset_to_starting(&mut self);
pub fn set_position(&mut self, position: Position);
```

Both operations are infallible because `Position` is already validated.

`reset_to_starting` replaces the game with a fresh standard starting game.

`set_position` establishes the supplied position as a new root.

Both operations:

- clear played moves;
- replace position-hash history with exactly one root hash;
- discard previous repetition history;
- invalidate old history/undo context;
- cause later status and search-history operations to use only the new root.

Tests prove reset equality, cleared histories, correct new-root hash, correct new-root status, correct detached search history, and stale `GameUndo` rejection.

---

## 5. Stable divide timing

The `chess-tools divide` command preserves its existing sorted move rows and total, then appends a stable timing field:

```text
<uci>\t<nodes>
...
total\t<nodes>
elapsed_nanos\t<nanos>
```

The measured interval covers divide calculation and total accumulation before output formatting. Tests verify:

- move rows remain sorted;
- the total remains exact;
- `elapsed_nanos` is present and parseable as an unsigned integer;
- nontrivial work reports a positive duration;
- depth-zero output remains a stable two-line summary.

---

## 6. FEN validation policy

`Position::from_fen` is explicitly a strict syntax and structural **analysis-position** parser. It does not prove reachability from the standard starting position.

It rejects:

- malformed field counts or placement;
- invalid piece, active-color, castling, en-passant, or counter syntax;
- pawns on rank one or rank eight;
- invalid en-passant target rank;
- occupied en-passant targets;
- missing or multiple kings;
- redundant-state invariant failures.

It intentionally accepts structurally coherent analysis states that may be illegal or unreachable in actual play, including:

- castling rights without matching home pieces;
- a correctly ranked but non-capturable en-passant target;
- adjacent kings;
- both kings in check;
- either side already being in check;
- unusual or unreachable material configurations.

Accepted analysis positions must remain safe for invariant validation, canonical FEN serialization, Zobrist recomputation, legal move generation, and depth-zero perft. Legal generation still forbids king capture and refuses invalid castling. Non-capturable en-passant targets remain excluded from canonical repetition identity.

The committed independent differential corpus continues to use positions accepted as valid by the pinned oracle.

---

## 7. Tracker corrections

The implementation pass corrected the live port tracker by:

- replacing stale Task 9 immediate-next operations with review-fix closure and Task 13 preparation;
- retaining Task 13 as active and not started;
- preserving Tasks 14–27 as incomplete according to their existing status;
- recording release depth-four and scheduled/manual depth-five perft coverage;
- recording existing hashing, draw, perft/differential, and evaluation documentation;
- recording existing legal/play/perft/divide/suite/oracle and evaluation/weight tooling;
- keeping AArch64, Android/JNI, Miri, sanitizer, fuzz, scheduled strength, UCI, self-play, tuning, and the Task 25 gate incomplete.

Task 25 remains partial.

---

## 8. Validation evidence

### 8.1 Implementation candidate

- SHA: `81a7cd4a58a52695eca2ede10d5c73c803851d17`
- One-shot implementation control run: `30738801841`
- Permanent CI run/job: `30739166607` / `91473334960`

### 8.2 Passed gates

The exact implementation candidate passed:

- committed workspace and validation asset checks;
- first-party lint-suppression rejection;
- lockfile verification;
- workspace metadata validation;
- `cargo fmt --all -- --check`;
- Cargo check across workspace, all targets, and all features;
- Clippy across workspace, all targets, and all features with `-D warnings`;
- all Rust tests;
- authoritative six-position release depth-four perft;
- rustdoc with warnings denied;
- debug workspace build;
- release workspace build;
- pinned independent differential corpus and seeded playout validation.

### 8.3 Test and oracle totals

- Executed non-doc Rust tests: `112`
- Differential corpus positions: `15`
- Child FENs compared: `293`
- Oracle perft nodes: `272,991`
- Seeded plies: `576`
- Seed: `0xC0FFEE`

### 8.4 Accepted external notices

Only external GitHub Actions Node runtime and dependency `punycode` deprecation notices were accepted. No first-party warning was accepted.

### 8.5 Clean repository state

All temporary implementation and closure workflows/scripts were removed. The clean `rust-engine` tree at `9c27d2c1c4a39a975b30d3357b69b6c96bb64c68` is byte-for-byte equivalent to the validated implementation candidate tree. No temporary branch, generated build output, or first-party lint suppression remains.

---

## 9. Completion criteria

This pass is complete because:

- `chess-search` has a safe efficient generated-legal make/unmake boundary;
- stale and wrong-origin tokens fail before mutation;
- `Game` root replacement semantics are explicit and tested;
- divide emits stable elapsed timing;
- FEN policy is explicit and covered by safe downstream tests;
- Task 25 and immediate-next-operation tracking reflect current reality;
- the strict permanent gate passed with exact implementation evidence;
- the final clean repository tree matches that validated candidate;
- Task 13 remains active and not started.
