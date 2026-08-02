# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 5 attack-generation implementation ready for CI

## Completed gates

### Task 0 — Python reference baseline
- Evidence SHA: `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`.
- CI run/job: `30722127447` / `91427510964`.
- Fast `1203 passed`; slow `179 passed`; perft `20/400/8902/197281`; UCI passed.

### Task 1 — Cargo workspace
- Evidence SHA: `7ca6f8dc0d2577ca552a6bfe115828eb668d2133`.
- CI run/job: `30722127447` / `91427510938`.
- Metadata, rustfmt, check, Clippy, tests, rustdoc, debug, and release passed.

### Task 2 — core values and coordinates
- Green implementation candidate: `f29524599134a14d34121af2fefb04cd90e78df0`.
- CI run/job: `30723748100` / `91431648799`; `16 passed`.
- Exact closure SHA/run/job: `b5f462aa73a69efcdc847ee215231a5064029902` / `30723952076` / `91432161445`.

### Task 3 — `Position` and invariants
- Green candidate: `00fd925dad807d822aa7878aade686ccc59ff9c5`.
- CI run/job: `30724744784` / `91434236030`; `24 passed`.
- Exact closure SHA: `5578682bb2a6df5173ff7593649ac55509c277cd`.

### Task 4 — strict FEN and UCI move notation
- Green implementation candidate: `87e6b81c65340a692af0d800012910399d3ac75b`.
- Exact evidence SHA: `6cb975b35f4dbe898a0444b1b4c39778e89bcb40`.
- CI run/job: `30726795562` / `91439860915`; `35 passed`.
- All strict gates passed; first-party warnings: none.

## Task 5 implementation

Current implementation candidate: `1ed6cbd17186584ee61aed980a2a00b8bdbc86fc`.

Implemented:

- precomputed pawn attacks for both colors and all squares;
- precomputed knight and king attacks;
- audited rook, bishop, and queen scans for arbitrary occupancy;
- precomputed 64-by-64 ray, between, and line tables;
- `Position::attackers_to`, `is_square_attacked`, `checkers_to_king`, and `pinned_pieces`;
- independent coordinate-oracle tests for every leaper square, every geometry pair, representative slider occupancies, fixtures, checks, pins, and pawn semantics;
- `docs/RUST_ATTACK_GENERATION.md`.

Task 5 remains open pending exact-SHA rustfmt, Cargo check, Clippy, tests, rustdoc, debug, and release evidence.

No branch or pull request has been created.
