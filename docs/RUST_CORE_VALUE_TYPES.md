# Rust Core Value Types and Coordinate Contracts

This document defines the Task 2 value types exported by `chess-core`. These
are internal engine contracts, not C, JNI, or stable serialized ABIs.

## Coordinates

`Square` is a validated transparent `u8` newtype. The canonical mapping is
row-major from Black's back rank:

```text
a8 = 0   h8 = 7
a1 = 56  h1 = 63
```

Rows are zero-based from rank eight to rank one. Files are zero-based from
`a` to `h`. Algebraic formatting and parsing are exact inverses for all 64
squares. Unchecked construction remains crate-private and is used only after
an index is proven to be below 64.

## Pieces

`Color` and `PieceKind` use stable zero-based table indices. `PieceKind` has no
`Empty` variant; absence is represented by the future position container.
`Piece` contains only `color` and `kind`, never a mutable square.

## Bitboards

`Bitboard` is a transparent `u64` newtype using the same square indices.
North decreases a square index by eight and south increases it by eight.
East/west and diagonal shifts mask the source edge first, so bits cannot wrap
between files.

## Move identity

`Move` is the engine's only internal move identity. It is a transparent packed
`u16` with private layout:

```text
bits 0..=5   source square
bits 6..=11  destination square
bits 12..=15 semantic MoveKind
```

Promotion identity is represented by `MoveKind`; quiet and capturing knight,
bishop, rook, and queen promotions are eight distinct values. Callers use
accessors and must not depend on the packed layout. This layout is not an FFI,
JNI, file-format, or network compatibility promise.

## Castling and counters

`CastlingRights` is a four-bit value with one independent bit for each
color/side pair. Rights describe historical eligibility and are not inferred
from current piece occupancy.

`HalfmoveClock` and `FullmoveNumber` are separate `u16` newtypes. The halfmove
clock is zero-based and resettable. The fullmove number is one-based and
rejects zero. Both expose checked increment operations and never wrap.

## Test contract

Task 2 tests cover:

- stable color and piece-kind indexing and FEN display conversion;
- all 64 square parse/format round trips and the four mapping corners;
- bitboard set, clear, membership, population count, iteration, pop-LSB,
  bitwise operations, and non-wrapping shifts;
- encode/decode behavior for all 14 move kinds;
- eight distinct quiet/capturing promotion identities;
- independent castling bits and scoped clearing;
- valid counter defaults, reset behavior, and overflow rejection;
- compact representation sizes.
