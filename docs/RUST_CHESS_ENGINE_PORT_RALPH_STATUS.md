# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 13 reference search and alpha-beta active; implementation not started

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
| 11 | `1711fefe37b93163ec316ba9528742d6f87f8496` | `30733309460` / `91457298625` | strict gate, depth-four perft, and differential oracle green; 89 Rust tests |
| 12 | `d8547cc258ecc2e52b8e4eb7ef287d92d5d0a04f` | `30734451785` / `91460574656` | strict gate, depth-four perft, and differential oracle green; 103 Rust tests |

## Task 12 completion

Implemented and validated:

- typed centipawn scores from the side-to-move negamax perspective;
- a static-evaluation range separated from distance-aware mate scores;
- color, side-to-move, and vertical-mirror symmetry tests;
- tapered middlegame/endgame material and piece-square evaluation;
- mobility, pawn structure, bishop pair, rook activity, king safety, space, and king activity terms;
- fixed, allocation-free normal evaluation and fixed trace structures;
- exact trace-component summation against normal evaluation;
- typed and named phased weights with explicit defaults;
- versioned weight sets with stable identifiers and canonical checksums;
- validated explicit serialization in `chess-tools` with no automatic file discovery;
- stable evaluator trace and per-group benchmark commands;
- benchmark evidence for every major evaluator group;
- exclusion audit against transcript-specific and exact-scenario Python patches;
- `docs/RUST_BASELINE_EVALUATOR.md`.

Evidence:

- Formatted implementation head: `d8547cc258ecc2e52b8e4eb7ef287d92d5d0a04f`.
- Permanent implementation CI run/job: `30734451785` / `91460574656`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 103 executed Rust tests, release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Benchmark/tooling run/job: `30734335652` / `91460185440`.
- Full starting-position release evaluation: 20,000 iterations in 19,596,825 ns, approximately 979.8 ns per evaluation on the hosted runner.
- Baseline weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime and dependency `punycode` deprecation notices only.
- Task 13 owns correctness-first reference search and alpha-beta over this evaluator.

## Task 13 active scope

- [ ] Implement an unpruned reference minimax search.
- [ ] Implement negamax alpha-beta using make/unmake.
- [ ] Prove shallow reference/alpha-beta score and best-move equivalence.
- [ ] Prove search restores the root position and game history exactly.
- [ ] Add checkmate, stalemate, draw, and mate-distance fixtures.
- [ ] Pass exact-head rustfmt, Cargo check, Clippy, tests, rustdoc, debug, and release gates.

No pull request has been created; work remains on `rust-engine`.
