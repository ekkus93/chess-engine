# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 11 authoritative perft and differential validation active; implementation not started

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
| 10 | `dd57b258fc8b9af647c30a1834f3d9e79a3d8ee3` | `30732542941` / `91455346591` | strict implementation gate green; `84 passed` |

## Task 10 completion

Implemented and validated:

- history-free `Position` retained as the rule-state primitive;
- history-owning `Game` with current position, played moves, and root-to-current canonical hashes;
- transactional legal move application and exact LIFO game undo;
- fail-loud mismatch handling without position or history mutation;
- explicit ongoing, checkmate, stalemate, claimable-draw, and automatic-draw statuses;
- claimable threefold-repetition and fifty-move draws;
- automatic fivefold-repetition and seventy-five-move draws;
- checkmate and stalemate precedence over automatic move-count draws;
- conservative dead-position recognition without broad minor-piece shortcuts;
- repetition counting limited to the reversible halfmove window;
- detached search-history cloning with reversible line push/pop;
- search operations isolated from game move and repetition histories;
- illegal game moves proven non-mutating;
- `docs/RUST_GAME_HISTORY_AND_DRAWS.md`.

Evidence:

- Implementation and tests: `crates/chess-core/src/game.rs`.
- Public exports: `crates/chess-core/src/lib.rs`.
- Validated implementation head: `dd57b258fc8b9af647c30a1834f3d9e79a3d8ee3`.
- Implementation CI run/job: `30732542941` / `91455346591`.
- Results: lockfile and metadata verification, rustfmt, Cargo check, Clippy with `-D warnings`, `84 passed`, rustdoc with `-D warnings`, debug build, and release build.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime and dependency `punycode` deprecation notices only.
- Task 11 owns expanded perft fixtures, divide output, independent differential validation, and the rule corpus gate.

## Task 11 active scope

- [ ] Add the standard exact perft fixture suite and expected node counts.
- [ ] Add explicitly gated slow perft depths.
- [ ] Harden deterministic divide output for diagnosis.
- [ ] Build an independent differential oracle harness.
- [ ] Establish a curated corpus gate across special-rule positions.
- [ ] Pass exact-head rustfmt, Cargo check, Clippy, tests, rustdoc, debug, and release gates.

No pull request has been created; work remains on `rust-engine`.
