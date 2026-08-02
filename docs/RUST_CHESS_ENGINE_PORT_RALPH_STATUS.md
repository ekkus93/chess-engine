# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 6 pseudo-legal move generation implemented; CI pending

## Completed gates

| Task | Evidence SHA | CI run / job | Result |
|---:|---|---|---|
| 0 | `7ca6f8dc0d2577ca552a6bfe115828eb668d2133` | `30722127447` / `91427510964` | Python fast `1203`, slow `179`, perft `20/400/8902/197281`, UCI pass |
| 1 | `7ca6f8dc0d2577ca552a6bfe115828eb668d2133` | `30722127447` / `91427510938` | strict workspace gates pass |
| 2 | `b5f462aa73a69efcdc847ee215231a5064029902` | `30723952076` / `91432161445` | closure green; implementation tests `16` |
| 3 | `5578682bb2a6df5173ff7593649ac55509c277cd` | `30724744784` / `91434236030` | closure green; `24 passed` |
| 4 | `6cb975b35f4dbe898a0444b1b4c39778e89bcb40` | `30726795562` / `91439860915` | `35 passed`; all strict gates green |
| 5 | `78e9315369ff4552e5500d1a820767a1fd228f29` | `30727553897` / `91441947625` | closure green; implementation `42 passed` |

## Task 6 implementation

Implementation commit: `0d8f063dbc9cd096e4e8796c07414bb7d0b4be02`.

Implemented:

- pawn single/double pushes and captures;
- exact four quiet and four capture-promotion identities;
- en-passant target-geometry candidates;
- knight, bishop, rook, queen, and ordinary king moves;
- king-side and queen-side castling candidates from rights, pieces, and empty paths;
- no final king-safety, castling-attack, or captured-en-passant-pawn validation before Task 7;
- fixed 256-entry stack-backed `MoveList` with structured overflow;
- deterministic piece/source/destination and promotion ordering;
- starting-position, promotions, edge, blocker, en-passant, castling, and storage tests;
- `docs/RUST_PSEUDO_LEGAL_MOVE_GENERATION.md`.

Task 6 remains open pending exact-SHA rustfmt, Cargo check, Clippy, tests, rustdoc, debug, and release evidence.

No branch or pull request has been created.
