# Strict FEN and UCI Coordinate Notation

Task 4 adds strict, fail-loud text boundaries without weakening the engine's single internal `Move` identity or the private `Position` mutation boundary.

## Strict six-field FEN

`Position::from_fen()` and `FromStr for Position` require exactly six fields:

1. piece placement;
2. active color;
3. castling availability;
4. en-passant target;
5. halfmove clock;
6. fullmove number.

The parser rejects:

- fewer or more than eight placement ranks;
- ranks that do not expand to exactly eight files;
- invalid piece characters and invalid run-length digits;
- pawns on rank one or rank eight;
- active colors other than `w` or `b`;
- castling characters outside `KQkq`, embedded `-`, and duplicate rights;
- en-passant coordinates outside the side-to-move target rank;
- occupied en-passant targets through position invariant validation;
- non-decimal, negative, overflowing, or zero fullmove counters;
- positions without exactly one king per color.

Parsing constructs a fresh crate-private `PositionBuilder`. Invalid input cannot partially mutate an existing `Position`.

`Position::to_fen()` emits canonical placement compression, `w`/`b`, castling rights in `KQkq` order or `-`, lowercase en-passant coordinates or `-`, and canonical decimal counters.

## UCI coordinate syntax

`UciMove` is a notation-layer syntax value containing:

- source `Square`;
- destination `Square`;
- optional promotion `PieceKind`.

It accepts exactly:

- four-character moves such as `e2e4` and `g1f3`;
- five-character promotions ending in lowercase `n`, `b`, `r`, or `q`.

`UciMove` does not convert directly into an unchecked internal `Move`. Future legal resolution compares the syntax value with generated legal moves and must return exactly one match.

The internal packed `Move` implements canonical UCI formatting through `Display` and `Move::to_uci()`. Promotion identity comes from `MoveKind`; the packed bit layout remains private and is not an ABI contract.

## Error and robustness contract

`FenError` and `MoveParseError` preserve the failing field or token category. Tests cover valid examples, malformed category fixtures, curated parse/serialize round trips, canonical castling ordering, all internal move kinds, all promotion suffixes, non-mutation after failed FEN parsing, and deterministic arbitrary Unicode input corpora that must never panic.
