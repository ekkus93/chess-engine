# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 5 complete; exact closure-SHA verification pending

## Completed gates

| Task | Evidence SHA | CI run / job | Result |
|---:|---|---|---|
| 0 | `7ca6f8dc0d2577ca552a6bfe115828eb668d2133` | `30722127447` / `91427510964` | Python fast `1203`, slow `179`, perft `20/400/8902/197281`, UCI pass |
| 1 | `7ca6f8dc0d2577ca552a6bfe115828eb668d2133` | `30722127447` / `91427510938` | workspace metadata, rustfmt, check, Clippy, tests, rustdoc, debug/release pass |
| 2 | `f29524599134a14d34121af2fefb04cd90e78df0` | `30723748100` / `91431648799` | `16 passed`; closure `b5f462aa73a69efcdc847ee215231a5064029902` green |
| 3 | `00fd925dad807d822aa7878aade686ccc59ff9c5` | `30724744784` / `91434236030` | `24 passed`; closure `5578682bb2a6df5173ff7593649ac55509c277cd` green |
| 4 | `6cb975b35f4dbe898a0444b1b4c39778e89bcb40` | `30726795562` / `91439860915` | `35 passed`; every strict gate green |
| 5 | `9922b0c725147fcabac3ce4c08f7c150c3ec6a1d` | `30727440571` / `91441645867` | `42 passed`; every strict gate green |

## Task 5 completion

Implemented and validated:

- precomputed pawn attacks for both colors and all 64 squares;
- precomputed knight and king attacks;
- audited rook, bishop, and queen scans over arbitrary occupancy;
- shared static 64×64 ray, between, and line tables;
- exact first-blocker inclusion semantics;
- `Position::attackers_to`, `is_square_attacked`, `checkers_to_king`, and absolute `pinned_pieces`;
- independent all-square, all-square-pair, occupancy, position, check, pin, and pawn-geometry oracles;
- `docs/RUST_ATTACK_GENERATION.md`;
- rustfmt, Cargo check, Clippy with `-D warnings`, tests, rustdoc with `-D warnings`, debug build, and release build.

First-party warnings: none.

Accepted external notices: GitHub Actions Node runtime and dependency `punycode` deprecation messages only.

## Current operation

1. Commit this closure status atomically with the authoritative TODO.
2. Verify that exact documentation SHA through strict CI.
3. Begin Task 6 pseudo-legal move generation only after the closure SHA is green.

No branch or pull request has been created.
