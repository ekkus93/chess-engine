# Rust Position Representation and Invariants

`chess-core::Position` is a validated playable-position value. Its redundant
storage is private so adapters and future search code cannot update one view
without updating the others.

## Hybrid representation

Each position stores:

- a 64-entry mailbox for direct piece lookup;
- one bitboard for every color/piece-kind pair;
- white and black occupancy bitboards;
- combined occupancy;
- one cached king square per color;
- side to move, castling rights, FEN en-passant target, halfmove clock,
  fullmove number, and a Zobrist placeholder/state.

The mailbox and bitboards use the Task 2 `a8 = 0` square mapping.

## Construction boundary

The public constructor is `Position::starting()`. An empty `PositionBuilder`
is crate-private for the strict FEN parser and unit tests. `build_playable()`
requires exactly one king per color and validates all redundant structures
before returning a `Position`.

There is no public piece-placement or direct mailbox/bitboard mutation API.
The private position module owns an editor capability that performs atomic
add, remove, and move operations while updating every representation. A king
cannot be removed from a playable position; king moves update the cache in the
same operation.

## Enforced invariants

`validate_invariants()` checks:

1. mailbox and every color/kind bitboard agree;
2. each color occupancy agrees with the mailbox and piece bitboards;
3. white and black occupancy do not overlap;
4. combined occupancy equals the union of color occupancy;
5. exactly one king exists per color;
6. cached king squares match the mailbox;
7. an en-passant target is empty and on rank six with White to move or rank
   three with Black to move.

Task 9 will add full Zobrist recomputation to the same validation contract.
Until then the Zobrist field is stored and restored as explicit placeholder
state but is not recomputed.

## Equality and cloning

`Position` equality compares the complete logical state, including redundant
representations and metadata, so restoration tests detect any divergence.
`Clone` is available for application snapshots and tests. Production recursive
search must use make/unmake and must not clone a position per child node.

## Test coverage

Task 3 tests cover the standard starting position, exact king requirements,
fail-loud duplicate placement, metadata preservation, en-passant validation,
atomic editor updates, failed-edit non-mutation, cached king relocation,
logical snapshot equality, and invariant checks after every state transition.
