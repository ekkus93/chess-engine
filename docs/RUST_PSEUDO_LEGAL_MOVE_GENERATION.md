# Rust Pseudo-Legal Move-Generation Contract

Task 6 generates moves that satisfy piece geometry, ownership, occupancy, and
special-move candidate rules. It deliberately does not decide whether a move
leaves the moving king in check. Complete king-safety validation belongs to
Task 7.

## Move list

`MoveList` stores up to 256 packed `Move` values in fixed stack-backed storage.
Generation performs no per-move heap allocation. Capacity exhaustion is a
structured `MoveListOverflow` error rather than truncation or an ignored write.

Generation order is deterministic for testing:

1. pawns;
2. knights;
3. bishops;
4. rooks;
5. queens;
6. ordinary king moves;
7. king-side then queen-side castling candidates.

Within a piece kind, source and destination squares use ascending packed square
index (`a8 = 0`). Pawn pushes precede pawn captures. Promotions are emitted in
knight, bishop, rook, queen order. This ordering is a reproducibility contract,
not a search-strength heuristic.

## Pawn moves

- Single pushes require an empty destination.
- Double pushes require the home rank plus empty intermediate and destination
  squares.
- Captures require an opposing non-king piece.
- A configured en-passant target on the pawn's attack geometry produces an
  `EnPassant` candidate. Captured-pawn existence and king safety are deferred to
  Task 7.
- Quiet and capture promotions emit all four exact packed identities, including
  underpromotions.

## Piece moves

Knight, bishop, rook, queen, and king destinations exclude friendly occupancy.
Occupied opposing non-king destinations are captures; empty destinations are
quiet moves. Sliding pieces use Task 5's first-blocker-inclusive attacks.
Pseudo-legal generation never emits a move that captures a king.

## Castling candidates

A castling candidate requires:

- the corresponding castling-right bit;
- the king on its home square;
- the corresponding rook on its home square;
- every path square empty.

This layer does not test whether the king is currently checked or whether the
transit/destination squares are attacked. Task 7 revalidates complete castling
legality.

## Validation

Tests cover the exact 20-move starting-position order, all eight promotion
identities, edge pawns and knights, sliding blockers, en-passant candidate
geometry, castling rights/pieces/paths versus deferred safety, and bounded
stack-backed storage.
