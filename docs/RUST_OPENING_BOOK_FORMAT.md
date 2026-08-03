# Rust opening-book indexed format

Task 19.2 chooses a versioned project-specific indexed binary format rather than Polyglot.

The format is implemented by `crates/chess-book/src/indexed.rs`. The crate accepts and returns complete byte slices only. It performs no filesystem, Android asset, environment, network, current-directory, or process-global discovery. Platform adapters remain responsible for explicitly obtaining bytes and passing them to `IndexedBook::from_bytes`.

## Why the project-specific format was selected

Polyglot would require a second position-hash schedule, Polyglot-specific move encoding, and compatibility rules unrelated to the engine's existing canonical FEN and UCI boundaries. The project-specific format instead stores:

- a collision-free canonical textual position identity;
- unresolved UCI coordinate-move syntax;
- a 32-bit relative weight; and
- optional 32-bit backend metadata.

Task 19.2 deliberately stores unresolved `UciMove` values rather than constructing unchecked internal moves. Task 19.3 remains responsible for resolving records against generated legal moves and applying deterministic or seeded weighted selection.

## Version and byte order

- Magic: eight bytes `CHBKIDX\0`.
- Format version: `1`.
- Position-key schema version: `1`.
- All multi-byte integers are little-endian.
- The header contains the marker `0x01020304`; a byte-swapped or otherwise different marker is rejected.
- Header size: 64 bytes.
- Record size: 104 bytes.

A reader must reject unknown versions, key schemas, record sizes, header sizes, flags, or nonzero reserved bytes. Future incompatible changes require a new format or key-schema version rather than heuristic interpretation.

## Position-key schema version 1

The key is the first four fields of canonical six-field FEN emitted by `Position::to_fen`:

1. piece placement;
2. side to move;
3. castling rights in canonical order; and
4. the FEN en-passant target.

Halfmove and fullmove counters are excluded. During decoding, the stored key is extended with `0 1`, parsed through the strict playable FEN parser, serialized again, and required to match byte-for-byte. This rejects malformed, noncanonical, or semantically invalid position identities.

The fixed key field reserves 84 bytes. Version-1 canonical keys exceeding that bound are rejected rather than truncated.

## Header layout

| Offset | Size | Field |
|---:|---:|---|
| 0 | 8 | magic `CHBKIDX\0` |
| 8 | 2 | format version, little-endian `u16` |
| 10 | 2 | header size, little-endian `u16` |
| 12 | 4 | endianness marker, little-endian `u32` |
| 16 | 2 | record size, little-endian `u16` |
| 18 | 2 | position-key schema version, little-endian `u16` |
| 20 | 4 | header flags; version 1 requires zero |
| 24 | 8 | record count, little-endian `u64` |
| 32 | 8 | payload length, little-endian `u64` |
| 40 | 4 | payload CRC-32 |
| 44 | 4 | header CRC-32 |
| 48 | 16 | reserved; version 1 requires zero |

The header checksum uses the standard reflected CRC-32 polynomial `0xEDB88320`, initial value `0xFFFFFFFF`, and final complement. The header checksum field is treated as zero while calculating the header checksum.

The payload checksum uses the same CRC-32 definition over every record byte.

## Record layout

| Offset | Size | Field |
|---:|---:|---|
| 0 | 1 | position-key byte length, 1 through 84 |
| 1 | 1 | UCI move byte length, 4 or 5 |
| 2 | 2 | record flags, little-endian `u16` |
| 4 | 4 | relative weight, little-endian `u32` |
| 8 | 4 | optional metadata word, little-endian `u32` |
| 12 | 84 | UTF-8 canonical position key, zero padded |
| 96 | 8 | ASCII UCI move, zero padded |

Record flag bit zero means that the metadata word is present. Every other bit is reserved. When the metadata flag is absent, the metadata word must be zero.

The complete payload is strictly sorted by `(position key, UCI move)`. Duplicate pairs and out-of-order records are rejected. This gives a deterministic file image and allows `IndexedBook::records_for_position` to return one contiguous range using binary partition points.

Weights are stored exactly. Version 1 does not normalize weights or assign special meaning to zero; that remains Task 19.3 policy.

## Validation order and failure behavior

`IndexedBook::from_bytes` validates all of the following before returning a loaded book:

1. minimum header length and exact magic;
2. format version, header size, endianness, record size, key schema, flags, and reserved bytes;
3. header CRC-32;
4. checked record-count and payload-length arithmetic;
5. exact file length with no trailing or missing bytes;
6. payload CRC-32;
7. every record's lengths, flags, metadata contract, UTF-8, zero padding, canonical FEN key, and UCI syntax; and
8. strict index ordering and duplicate rejection.

Every failure is returned as a structured `IndexedBookError`. Corruption is never converted into an empty book or an empty position lookup. Parsing is transactional: a caller receives either one fully validated `IndexedBook` or an error, never a partially populated book.

## Serialization

`IndexedBook::from_records` sorts records canonically and rejects duplicate `(position, move)` pairs. `IndexedBook::to_bytes` then emits one deterministic version-1 image with exact header and payload checksums. Encoding the same logical record set in a different input order produces the same bytes.

## Deferred work

Task 19.2 does not:

- resolve stored UCI syntax to internal legal moves;
- reject a syntactically valid but position-illegal book move;
- choose the highest-weight record;
- perform weighted random selection;
- define or consume an RNG seed;
- add UCI options, safe-facade configuration, JNI integration, or Android asset loading; or
- discover or open any file automatically.

Those behaviors remain assigned to Tasks 19.3 through 19.5.
