# Rust Position Make/Unmake Contract

## Scope

Task 8 formalizes the reversible position mutation path used by legal move generation, perft, and future search. It does not implement Zobrist key computation; Task 9 owns authoritative and incremental hashing. The current hash field is nevertheless preserved exactly by every undo token.

## Public checked API

`Position::make_move(Move)` accepts only an exact packed move identity returned by `Position::legal_moves`. It returns an opaque `PositionUndo` on success. An illegal identity or a counter-overflow error leaves the complete position unchanged.

`Position::unmake_move(PositionUndo)` consumes the corresponding opaque token. Tokens are move-bound and must be consumed in last-in, first-out order against the same position. A token that does not match the current post-move state is rejected before mutation.

`PositionUndo` intentionally has private fields. Callers can inspect only:

- `move_made()`;
- `captured()`, which returns the captured square and piece when applicable.

The token stores all state required for exact restoration:

- the applied move and original moving piece;
- captured piece and square;
- prior castling rights;
- prior en-passant target;
- prior halfmove clock;
- prior fullmove number;
- prior side to move;
- prior hash placeholder/state.

## Internal generated-legal path

Legal move filtering, perft, divide, and future search use the crate-private generated-legal path. This avoids regenerating the legal move list after a move has already been produced by the engine while still validating that the packed move identity agrees with the current position state.

Production recursive paths use make/unmake. They do not clone the position per child. `Clone` remains available only for application snapshots, tests, and diagnostics.

## State transitions

A successful move updates all redundant board representations through `PositionEditor`:

- mailbox;
- piece bitboards;
- color occupancies;
- combined occupancy;
- cached king squares.

It also updates:

- side to move after every move;
- fullmove number after Black moves;
- halfmove clock, resetting on pawn moves and captures;
- en-passant target, creating it only for a double pawn push and clearing it otherwise;
- castling rights after king movement, rook movement from a home square, or rook capture on a home square.

Castling moves relocate both king and rook. Promotion replaces the pawn with the exact promoted piece identity. En passant records and restores the captured pawn on its actual square rather than the destination square.

## Restoration guarantees

Every successful unmake restores field-for-field logical equality with the pre-move position, including cached king squares and the stored hash field. Task 8 tests cover:

- quiet moves;
- double pawn pushes;
- normal captures;
- en passant;
- king-side and queen-side castling;
- all four quiet promotions;
- all four capture promotions;
- rook captures that remove castling rights;
- side, clock, and en-passant transitions;
- public failure atomicity;
- mismatched undo rejection;
- every legal move in a curated position corpus;
- deterministic random legal playouts followed by complete reverse unmake.

Task 9 will extend the randomized verification to compare the incremental hash with authoritative recomputation after every make and unmake.