# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 9 Zobrist hashing and repetition identity active; implementation not started

## Completed gates

| Task | Evidence SHA | CI run / job | Result |
|---:|---|---|---|
| 0 | `7ca6f8dc0d2577ca552a6bfe115828eb668d2133` | `30722127447` / `91427510964` | Python fast `1203`, slow `179`, perft `20/400/8902/197281`, UCI pass |
| 1 | `7ca6f8dc0d2577ca552a6bfe115828eb668d2133` | `30722127447` / `91427510938` | strict workspace gates pass |
| 2 | `b5f462aa73a69efcdc847ee215231a5064029902` | `30723952076` / `91432161445` | closure green; implementation tests `16` |
| 3 | `5578682bb2a6df5173ff7593649ac55509c277cd` | `30724744784` / `91434236030` | closure green; `24 passed` |
| 4 | `6cb975b35f4dbe898a0444b1b4c39778e89bcb40` | `30726795562` / `91439860915` | `35 passed`; all strict gates green |
| 5 | `78e9315369ff4552e5500d1a820767a1fd228f29` | `30727553897` / `91441947625` | closure green; implementation `42 passed` |
| 6 | `cb7124c5712f6b3f8f4540e9e8fabaa2aa242bc0` | `30727972433` | closure green; implementation `49 passed` |
| 7 | `334dc79b3ce0cbc1e7b5096387218c90a8365204` | `30730100518` / `91448776834` | closure green; implementation `59 passed` |
| 8 | `cecc39b9c9dcd8c90f9cdbdb4284be13c480bbd6` | `30730891252` / `91451022194` | closure green; implementation `67 passed` |

## Task 8 completion

Implemented and validated:

- opaque public `PositionUndo` with private complete restoration state;
- move-bound undo tokens with mismatch and out-of-order rejection before mutation;
- public checked `Position::make_move` and consuming `Position::unmake_move`;
- crate-private generated-legal make/unmake for legal generation, perft, divide, and future search;
- transactional illegal-move and counter-overflow failures;
- exact updates and restoration for side, clocks, en-passant, castling rights, captures, castling rook movement, promotions, mailbox, bitboards, occupancies, cached kings, and stored hash state;
- exact round trips for quiet moves, double pushes, captures, en passant, both castling directions, all quiet promotions, all capture promotions, and rook captures that alter castling rights;
- every legal move in a curated position corpus checked through make, invariants, unmake, and exact equality;
- deterministic random legal playouts for eight seeds and up to 128 plies, followed by complete reverse restoration;
- `docs/RUST_MAKE_UNMAKE.md`;
- lockfile and metadata verification, rustfmt, Cargo check, Clippy with `-D warnings`, `67 passed`, rustdoc with `-D warnings`, debug build, and release build.

Evidence:

- Formal make/unmake module: `crates/chess-core/src/position/make_unmake.rs`.
- Restoration and sequence tests: `crates/chess-core/src/position/make_unmake_tests.rs`.
- Validated implementation head: `cfc68a4ff775d6d4b73c0bfa192e00c1fd7b910f`.
- Implementation CI run/job: `30730803320` / `91450780156`.
- Closure SHA: `cecc39b9c9dcd8c90f9cdbdb4284be13c480bbd6`.
- Closure CI run/job: `30730891252` / `91451022194`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime and dependency `punycode` deprecation notices only.
- Task 9 owns real Zobrist computation and incremental key updates; Task 8 stores and restores the current hash field exactly.

## Task 9 active scope

- [ ] Define deterministic versioned Zobrist tables.
- [ ] Implement authoritative full-position hash recomputation.
- [ ] Update keys incrementally through every make/unmake move class.
- [ ] Canonicalize en-passant repetition identity only when a legal en-passant capture exists.
- [ ] Compare incremental and recomputed keys after curated and randomized make/unmake sequences.
- [ ] Pass exact-head rustfmt, Cargo check, Clippy, tests, rustdoc, debug, and release gates.

No branch or pull request has been created.
