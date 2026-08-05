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

## FEN validation policy

`Position::from_fen` is a strict syntax and structural **analysis-position** parser. It does not attempt to prove that a position is reachable from the standard initial position.

It rejects malformed field counts and placement, invalid piece or counter syntax, pawns on rank one or eight, invalid en-passant target ranks, occupied en-passant targets, and positions without exactly one king of each color. It constructs a fresh position and validates mailbox, bitboard, occupancy, cached-king, en-passant, and hash invariants before returning.

It intentionally accepts structurally coherent analysis states that may be illegal or unreachable in an actual game, including:

- castling rights without the matching home rook or with the king away from its home square;
- a correctly ranked but non-capturable en-passant target;
- adjacent kings;
- both kings in check;
- either the side to move or the side not to move already being in check;
- unusual material that cannot arise from the standard initial set.

Structural acceptance is not certification of legal game reachability. Every accepted analysis position must still satisfy the engine's internal representation invariants and remain a safe input to legal move generation. Legal move generation never permits king capture, refuses castling when required pieces or safety conditions are absent, and filters moves against king attack. Zobrist repetition identity includes an en-passant file only when a legal en-passant capture exists, so accepted non-capturable targets do not create a false repetition distinction. The committed differential corpus remains restricted to positions accepted as valid by the pinned independent oracle.
