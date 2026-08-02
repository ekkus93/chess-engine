# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 8 make/unmake and incremental state active; implementation not started

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

## Task 7 completion

Implemented and validated:

- legal filtering through private reversible make/unmake;
- single-check captures, blocks, and king evasions;
- double-check king-only filtering;
- absolute-pin enforcement;
- king destination safety and no king captures;
- complete castling source/transit/destination validation with source-vacated transient testing;
- en-passant captured-pawn validation and horizontal/diagonal discovered-check rejection;
- all quiet and capture promotion identities plus invalid-promotion rejection;
- castling rights, en-passant, clocks, side, captures, promotions, rook movement, and hash-placeholder restoration;
- starting-position perft depths 1–4: `20`, `400`, `8,902`, `197,281`;
- deterministic divide plus exact restoration and invariant checks;
- `docs/RUST_LEGAL_MOVE_GENERATION.md`;
- lockfile and metadata verification, rustfmt, Cargo check, Clippy with `-D warnings`, `59 passed`, rustdoc with `-D warnings`, debug build, and release build.

Evidence:

- Shared bounded move-list mutation: `9baf2e299551f39dbb4cbee2a1510e35d68ac6c8`.
- Legal generation/perft source: `beb6981520c16d07c2617a1c567eee7ed0a5212d`.
- Validated implementation head: `d6ea24eb6eeaea7b41dc309f866a5653aba687d5`.
- Implementation CI run/job: `30729969574` / `91448384283`.
- Closure SHA: `334dc79b3ce0cbc1e7b5096387218c90a8365204`.
- Closure CI run/job: `30730100518` / `91448776834`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime and dependency `punycode` deprecation notices only.

## Task 8 active scope

- [ ] Formalize the reusable undo structure and contract.
- [ ] Complete move application and unapplication paths for every legal move class.
- [ ] Add exact restoration tests for quiet moves, captures, double pushes, en passant, castling, and every promotion class.
- [ ] Add long deterministic randomized legal-sequence make/unmake restoration.
- [ ] Pass exact-head rustfmt, Cargo check, Clippy, tests, rustdoc, debug, and release gates.

No branch or pull request has been created.
