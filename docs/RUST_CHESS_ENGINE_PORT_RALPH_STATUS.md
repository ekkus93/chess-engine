# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 3 complete; Task 4 next

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

- Initial implementation: `dd66b61b745d72f833802826b5d72f2b3f18232a`.
- rustfmt correction: `b36e7e379e35a32aac6c707099bd9c2daa7067cd`.
- Sealed editor capability fix: `bfef2ae3a08722a4215ba788273543c3ba244423`.
- Green candidate: `00fd925dad807d822aa7878aade686ccc59ff9c5`.
- CI run/job: `30724744784` / `91434236030`.
- Unit tests: `24 passed, 0 failed`.
- Lockfile verification, metadata, rustfmt, Cargo check, Clippy with warnings denied, tests, rustdoc with warnings denied, debug build, and release build passed.
- First-party warnings: none.
- External notices: GitHub Action Node runtime deprecation messages only.

Task 3 gate is closed.

## Next operation

Verify the Task 3 closure documentation commit at its exact SHA, then begin Task 4:

- structured FEN and UCI move errors;
- strict six-field FEN parser;
- canonical FEN serializer;
- UCI coordinate-move parse/format;
- exhaustive invalid-input, round-trip, and property tests;
- strict exact-SHA CI loop.

No branch or pull request has been created.
