# Rust Attack-Generation Contract

Task 5 separates chess attack geometry from move legality. These primitives are
implemented in `chess-core` and do not generate moves, inspect side-to-move, or
apply king-safety rules.

## Leaper attacks

Pawn, knight, and king attacks are precomputed for every square. Pawn attacks
are indexed by color and describe diagonal attack geometry regardless of target
occupancy. A pawn therefore attacks its two in-bounds diagonal destinations even
when both destinations are empty.

## Sliding attacks

Rook and bishop attacks use explicit audited ray scans over arbitrary occupancy.
Queen attacks are the union of rook and bishop attacks. Each directional scan:

1. begins on the square adjacent to the source;
2. includes every empty square along the ray;
3. includes the first occupied square;
4. stops immediately after that blocker.

The blocker may belong to either color because attack geometry is independent of
move ownership. Magic bitboards, PEXT, and other accelerated schemes are deferred
until correctness baselines and benchmarks exist.

## Geometry helpers

- `ray(from, through)` excludes `from`, includes `through`, and continues in the
  same direction to the board edge. Non-aligned or identical squares return an
  empty bitboard.
- `between(from, to)` contains only squares strictly between aligned endpoints.
  It is symmetric and empty for adjacent, identical, or non-aligned squares.
- `line(from, to)` contains the complete rank, file, or diagonal through aligned
  endpoints, extending to both board edges. Identical endpoints return that one
  square; non-aligned endpoints return an empty bitboard.

All three helpers are backed by precomputed 64-by-64 tables.

## Position queries

`Position::attackers_to(target, color)` returns the source squares of every piece
of `color` that geometrically attacks `target`. Sliding queries use the current
combined occupancy. Pawn attackers use reverse pawn geometry and do not require
an occupied target.

`Position::is_square_attacked` is the non-empty form of that query.
`Position::checkers_to_king(color)` queries enemy attackers to the cached king
square.

`Position::pinned_pieces(color)` reports absolute pins to that color's king. A
piece is pinned only when it is the sole occupied square between the king and an
opposing rook, bishop, or queen on a compatible ray. This is supporting geometry
for later legal move generation; Task 5 does not itself restrict or generate
moves.

## Validation

Production tables and scans are compared against independent coordinate-based
oracles in tests. Coverage includes all 64 leaper sources, all 4,096 square pairs
for geometry, representative arbitrary occupancies for every slider source,
first-blocker semantics, edge/corner behavior, fixture-wide attackers-to-square
comparisons, double check, absolute pins, and pawn occupancy independence.
