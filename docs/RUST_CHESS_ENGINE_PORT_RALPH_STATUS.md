# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 4 complete; Task 5 attack-generation infrastructure in progress

## Completed gates

### Task 0 — Python reference baseline

- Evidence SHA: `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`.
- CI run/job: `30722127447` / `91427510964`.
- Fast suite: `1203 passed`.
- Slow suite: `179 passed`.
- Perft: `20/400/8902/197281`.
- UCI smoke: passed.

### Task 1 — Cargo workspace

- Evidence SHA: `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`.
- CI run/job: `30722127447` / `91427510938`.
- Metadata, rustfmt, check, Clippy, tests, rustdoc, debug build, and release build passed.

### Task 2 — core values and coordinates

- Green implementation candidate: `f29524599134a14d34121af2fefb04cd90e78df0`.
- CI run/job: `30723748100` / `91431648799`.
- Unit tests: `16 passed`.
- Exact closure SHA/run/job: `b5f462aa73a69efcdc847ee215231a5064029902` / `30723952076` / `91432161445`.

### Task 3 — `Position` and invariants

- Green candidate: `00fd925dad807d822aa7878aade686ccc59ff9c5`.
- CI run/job: `30724744784` / `91434236030`.
- Unit tests: `24 passed, 0 failed`.
- Exact closure SHA: `5578682bb2a6df5173ff7593649ac55509c277cd`.
- All strict gates passed; first-party warnings: none.

### Task 4 — strict FEN and UCI move notation

- Green implementation candidate: `87e6b81c65340a692af0d800012910399d3ac75b`.
- Exact status/evidence SHA: `6cb975b35f4dbe898a0444b1b4c39778e89bcb40`.
- CI run/job: `30726795562` / `91439860915`.
- Unit tests: `35 passed, 0 failed`.
- Lockfile verification, metadata, rustfmt, Cargo check, Clippy with warnings denied, tests, rustdoc with warnings denied, debug build, and release build passed.
- First-party warnings: none.
- External notices: GitHub Action Node runtime and `punycode` deprecation notices only.

Task 4 gate is closed.

## Current operation — Task 5

Implement attack-generation infrastructure in `chess-core`:

- precomputed pawn attacks for both colors and all squares;
- precomputed knight and king attacks;
- audited rook, bishop, and queen sliding attacks for arbitrary occupancy;
- ray, line, and between-square geometry;
- attackers-to-square, attacked-square, checker, and pinned-piece queries on `Position`;
- independently generated differential fixtures and exhaustive edge/blocker tests;
- strict exact-SHA CI loop.

No branch or pull request has been created.
