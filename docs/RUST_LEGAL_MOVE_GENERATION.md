# Rust Legal Move Generation and Initial Perft

Task 7 converts Task 6 pseudo-legal candidates into complete legal moves. The
legal layer uses a private reversible move/undo path inside `chess-core`; it does
not clone a `Position` per candidate and does not expose a public move-application
API. Task 8 will formalize the complete undo contract and randomized restoration
suite.

## Legal filtering

For each pseudo-legal candidate, the engine:

1. validates special-move structure that depends on current state;
2. performs the castling source/transit checks when applicable;
3. applies the candidate through the private reversible path;
4. tests the moving side's cached king square against enemy attacks;
5. restores every board and metadata field;
6. retains the exact packed move only when the king is safe.

This naturally handles pinned pieces, single-check captures and blocks, double
check, and ordinary king moves. King captures are never generated.

## Reversible state used by Task 7

The private undo record restores:

- captured piece and capture square, including en passant;
- castling rights;
- en-passant target;
- halfmove clock;
- fullmove number;
- side to move;
- the current Zobrist placeholder value.

Board restoration handles quiet moves, captures, double pushes, promotions,
en-passant captures, and both castling directions. Castling rights are cleared
when a king moves, when a rook leaves its home square, or when a rook is captured
on its home square. Every non-double move expires the en-passant target; a double
push creates the midpoint target.

## Castling legality

A castling candidate is legal only when:

- Task 6's rights, home-piece, and empty-path conditions hold;
- the source king square is not attacked;
- the transit square is not attacked after the king vacates its source square;
- the destination square is not attacked in the completed castled position.

Moving the king to the transit square before testing it prevents the historical
bug where the still-occupied source square incorrectly blocks a sliding attack.
Rights are never reconstructed merely because a king or rook appears back on its
home square.

## En passant legality

The legal layer requires the captured square behind the target to contain the
opposing pawn. Full reversible application removes both the moving pawn's source
occupancy and the captured pawn before checking king safety. This catches
horizontal and diagonal discovered checks that appear only after en passant.

## Promotions

Legal generation preserves all four quiet and all four capture-promotion packed
identities. A promotion flag is accepted only for a pawn reaching its final rank;
non-pawn and non-final-rank promotion identities do not match any legal move.

## Perft and divide

`Position::perft(depth)` recursively counts legal leaf nodes using the same
private make/unmake path. `Position::divide(depth)` returns deterministic root
moves with their child counts. The starting-position acceptance values are:

| Depth | Nodes |
|---:|---:|
| 1 | 20 |
| 2 | 400 |
| 3 | 8,902 |
| 4 | 197,281 |

Tests verify exact restoration after legal generation, every perft depth, and
divide output, in addition to checks, pins, castling, en passant, king safety,
and promotions.
