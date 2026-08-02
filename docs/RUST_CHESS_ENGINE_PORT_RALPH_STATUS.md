# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 10 game, history, and draw semantics active; implementation not started

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
| 9 | `178583c15458cb29205201047bad8f4064a9342d` | `30731524205` / `91452671063` | strict implementation gate green; `72 passed` |

## Task 9 completion

Implemented and validated:

- compile-time deterministic Zobrist tables with explicit `Position::ZOBRIST_VERSION = 1`;
- stable piece-square, side-to-move, complete castling-state, and en-passant-file key schedules;
- authoritative `Position::recomputed_zobrist()` from private position state;
- canonical repetition identity that excludes move counters;
- en-passant hashing only when at least one king-safe legal en-passant capture exists;
- occupancy-based en-passant legality evaluation without recursive legal move generation;
- incremental XOR updates for every ordinary, capture, en-passant, castling, promotion, and castling-right transition;
- constant-time exact hash restoration through opaque undo state;
- removal of the Task 8 arbitrary placeholder-hash builder seam;
- versioned known fixtures, curated move-category tests, and randomized incremental-versus-recomputed checks after every ply;
- complete randomized reverse restoration to the original position and key;
- `docs/RUST_ZOBRIST_HASHING.md`.

Evidence:

- Hash implementation and tests: `crates/chess-core/src/position/zobrist.rs`.
- Incremental integration: `crates/chess-core/src/position/make_unmake.rs`.
- Validated implementation head: `178583c15458cb29205201047bad8f4064a9342d`.
- Implementation CI run/job: `30731524205` / `91452671063`.
- Results: lockfile and metadata verification, rustfmt, Cargo check, Clippy with `-D warnings`, `72 passed`, rustdoc with `-D warnings`, debug build, and release build.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime and dependency `punycode` deprecation notices only.
- Task 10 owns repetition history, draw thresholds, and game-state semantics over this canonical key.

## Task 10 active scope

- [ ] Define the game/history state and irreversible-move boundaries.
- [ ] Detect checkmate and stalemate from authoritative legal moves.
- [ ] Implement claimable threefold-repetition and fifty-move draws.
- [ ] Implement automatic fivefold-repetition and seventy-five-move draws.
- [ ] Add conservative dead-position logic.
- [ ] Define search-history propagation without corrupting game history.
- [ ] Pass exact-head rustfmt, Cargo check, Clippy, tests, rustdoc, debug, and release gates.

No pull request has been created; work remains on `rust-engine`.
