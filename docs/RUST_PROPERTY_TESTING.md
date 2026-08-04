# Rust Property Testing

Task 23.1 adds deterministic generative property coverage across `chess-core` and `chess-search`. The tests operate on legal positions reached through the engine's own move generator and checked move API; they do not weaken playable-position invariants or manufacture arbitrary impossible boards.

## Core properties

`crates/chess-core/tests/property_invariants.rs` proves:

- all 64 square indices, row/file coordinates, and algebraic strings round-trip;
- every source, destination, and `MoveKind` combination preserves packed move identity;
- canonical FEN parse/serialize/parse is stable for generated legal positions;
- every generated legal move is accepted by the checked public move API;
- legal generation and legality queries leave the source position unchanged;
- every applied legal move preserves the moving king's safety;
- mailbox, piece bitboards, occupancies, king caches, en-passant state, and related internal invariants remain consistent;
- incremental Zobrist hashes equal full recomputation after every transition;
- immediate and full-sequence make/unmake restore the exact logical position and hash.

The legal-position generator starts from six curated roots covering the initial position, castling, en passant, promotion races, middlegame structure, and constrained check-line play. Four fixed seeds drive up to 48 plies from every root. Failure messages include the root index, seed, ply, FEN, and move where applicable.

## Search properties

`crates/chess-search/tests/property_search.rs` proves:

- color-swapped vertical mirrors of generated legal positions receive exactly equal side-relative evaluation scores;
- every move in every returned principal variation is legal in sequence;
- principal-variation application preserves king safety, internal invariants, and incremental/full hash equality;
- reversing a complete principal variation restores the root exactly;
- iterative deepening leaves caller-owned positions and search histories unchanged.

Twenty-four deterministic cases are generated from varied legal roots. Each case runs iterative deepening through depth two, making the suite bounded enough for normal CI while exercising nontrivial multi-ply principal variations.

## Reproduction and failure preservation

The suite has no time-based or entropy-based input. A failure is reproducible from the reported case or hexadecimal seed. Any discovered counterexample must be minimized and retained as a named permanent regression before the implementation is corrected. Task 23.2 will add parser and state-machine fuzz targets; it does not replace these deterministic properties.
