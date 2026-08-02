# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 12 baseline evaluator and trace active; implementation not started

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

## Task 11 completion

Implemented and validated:

- one authoritative six-position perft manifest through depth five;
- direct manifest consumption by Rust integration tests;
- fast depth-one through depth-three gates with exact restoration checks;
- required release-mode depth-four CI validation;
- permanent weekly and manual release-mode depth-five validation;
- deterministic UCI-sorted legal-move and divide output;
- canonical child-FEN and perft tooling;
- a persistent machine-readable Rust oracle protocol;
- pinned independent `chess==1.11.2` validation;
- fifteen-position permanent special-rule corpus;
- complete legal-set, every-child-FEN, independent-perft, and seeded-playout comparisons;
- fail-loud corpus validation and reproducible mismatch diagnostics;
- correction of two specification FEN/count pairing errors;
- `docs/RUST_PERFT_AND_DIFFERENTIAL_VALIDATION.md`.

Evidence:

- Validated implementation head: `1711fefe37b93163ec316ba9528742d6f87f8496`.
- Implementation CI run/job: `30733309460` / `91457298625`.
- Results: lockfile and metadata verification, rustfmt, Cargo check, Clippy with `-D warnings`, 89 executed Rust tests, release depth-four perft, rustdoc with `-D warnings`, debug build, and release build.
- Differential result: fifteen positions, 293 child FENs, 272,991 independently counted perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Depth-five validated head: `e5c44147c8f6097f1d60c8d6d73a051da4fc13a1`.
- Depth-five run/job: `30733437572` / `91457637460`.
- Depth-five result: all six positions and 469,080,960 leaves passed in 39.77 seconds.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 12 owns evaluation semantics and traceability over the validated rule layer.

## Task 12 active scope

- [ ] Define the score convention and terminal-score boundary.
- [ ] Implement the required baseline evaluation terms.
- [ ] Preserve efficient evaluation suitable for search.
- [ ] Add a term-by-term evaluation trace.
- [ ] Centralize named weights and document their meaning.
- [ ] Enforce the Task 12 evaluator exclusions.
- [ ] Pass exact-head rustfmt, Cargo check, Clippy, tests, rustdoc, debug, and release gates.

No pull request has been created; work remains on `rust-engine`.
