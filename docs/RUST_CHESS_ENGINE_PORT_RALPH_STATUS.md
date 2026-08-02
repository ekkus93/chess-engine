# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-02  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Tasks 15.1–15.4 complete; Task 15.5 deterministic replacement is next

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
| Review fix | `81a7cd4a58a52695eca2ede10d5c73c803851d17` | `30739166607` / `91473334960` | strict gate, 112 Rust tests, depth-four perft, and differential oracle green |
| 13.1 | `7cf7fb027bf86f0658c14f4c9b452bce2cdcbe98` | `30741414286` / `91479443116` | unpruned reference negamax, 118 Rust tests, depth-four perft, and differential oracle green |
| 13.2 | `d662ca07cae6b0044c1ce620a0dc4f3249784d6c` | `30741988672` / `91480926153` | negamax alpha-beta, 124 Rust tests, depth-four perft, and differential oracle green |
| 13.3 | `bdf98a8e7c5cb6aadc55ba3638cd3af2f4ba9e91` | `30743024471` / `91483729312` | shallow equivalence, 127 Rust tests, depth-four perft, and differential oracle green |
| 13.4 | `3644e032504b604c210796f1e6c7ef056d05e94b` | `30743519630` / `91485044296` | completion/cancellation immutability, 131 Rust tests, depth-four perft, and differential oracle green |
| 13.5 / 13 | `7ca429b0c883bbb8484d3eb3a4af7d96cdb57201` | `30745120833` / `91489299233` | terminal/mate-distance fixtures and full Task 13 gate, 135 Rust tests, depth-four perft, and differential oracle green |
| 14.1 | `24e1090e17f8b39bdaac4989daffdeaea4b857e9` | `30749044761` / `91499685362` | correctness-first quiescence, 140 Rust tests, depth-four perft, and differential oracle green |
| 14.2 | `3688cb8e89a7da0c7fd34c3756d52d0fcc8d3d33` | `30753873602` / `91512570865` | bounded tactical ordering, 145 Rust tests, strict node-reduction witness, depth-four perft, and differential oracle green |
| 14.3 | `f08b2d519ffc066d8d6b18326e03ead278d908de` | `30762457921` / `91535329886` | bounded killer/history quiet ordering, 150 Rust tests, deterministic exact-score and strict node-reduction witnesses, depth-four perft, and differential oracle green |
| 14.4 | `dc758a3fc62e7f7002191993c73773dd2a71caef` | `30763226685` / `91537383867` | five explicit quiescence correctness witnesses, 155 Rust tests, depth-four perft, and differential oracle green |
| 14.5 / 14 | `f4dc989e97d8577f4c86bdbfb67ae47e3d5cd7f4` | `30764073097` / `91539614372` | permanent exclusion audit, exact-score boundary, 155 Rust tests, depth-four perft, and differential oracle green |
| 15.1 | `65ef70bfbff3d0bf5fd6e6a19ba20ed5214c3e26` | `30764647127` / `91541116562` | complete TT entry payload, five focused tests, 160 Rust tests, depth-four perft, and differential oracle green |
| 15.2 | `6b2ee0081cd47fd9069aeabb0d3ccb1d3659fea9` | `30765303745` / `91542820537` | fixed MiB storage, four-entry clusters, typed allocation failures, clear/generation operations, 165 Rust tests, depth-four perft, and differential oracle green |
| 15.3 | `ac68b99db53546c31f3aae68ad7337ba256eb982` | `30766126491` / `91545080021` | ply-correct mate normalization, typed conversion failures, six focused tests, 171 Rust tests, depth-four perft, and differential oracle green |
| 15.4 | `b6a015e6cc519aa0bbc8e7bde7dde06bdd660b44` | `30766760085` / `91546779835` | complete-key, depth- and bound-safe probes, repetition suppression, eight focused tests, 179 Rust tests, depth-four perft, and differential oracle green |

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

## Pre-Task-13 review-fix completion

Implemented and validated:

- opaque source-bound legal-move tokens usable by `chess-search`;
- bounded deterministic legal-token storage;
- valid-token application without legal-list regeneration;
- non-mutating stale and wrong-origin token rejection;
- exact token make/unmake and Zobrist restoration;
- cross-crate token API coverage in `chess-search`;
- explicit `Game::reset_to_starting` and `Game::set_position`;
- fresh-root move, hash, repetition, status, and search-history semantics;
- stable `elapsed_nanos` divide output;
- explicit strict structural analysis-FEN policy and downstream safety tests;
- corrected Task 25 coverage and Task 13 next-operation text;
- completed review-fix spec and TODO documents.

Evidence:

- Starting code/documentation SHA: `52377d09b713541044e24c8e3559be3f12002cc1`.
- Validated implementation SHA: `81a7cd4a58a52695eca2ede10d5c73c803851d17`.
- One-shot implementation control run: `30738801841`.
- Permanent implementation CI run/job: `30739166607` / `91473334960`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 112 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime and dependency `punycode` deprecation notices only.
- Temporary implementation and closure workflows/scripts were removed.
- Clean code/workflow SHA `9c27d2c1c4a39a975b30d3357b69b6c96bb64c68` compared against the validated candidate with zero changed files.
- Later commits finalize documentation only; they do not change the validated Rust or permanent workflow tree.
- No pull request was created.

## Task 13.1 completion

Implemented and validated:

- unpruned, full-tree reference negamax in `chess-search`;
- public score, deterministic best-move, and node-count result API;
- legal-token make/unmake with no clone-per-child;
- detached root plus reversible line repetition history;
- checkmate, stalemate, dead-position, repetition, fifty-move, and seventy-five-move scoring;
- checkmate precedence over a simultaneous move-count threshold;
- ply-relative mate scores;
- fail-loud history/root mismatch, depth-domain, and node-overflow errors;
- exact root position, Zobrist, and history restoration;
- `docs/RUST_REFERENCE_SEARCH.md`.

Evidence:

- Exact validated implementation SHA: `7cf7fb027bf86f0658c14f4c9b452bce2cdcbe98`.
- Permanent CI run/job: `30741414286` / `91479443116`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 118 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Starting-position depth-two reference search visits exactly `421` nodes.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13.2 remains not started.

## Task 13.2 completion

Implemented and validated:

- recursive fail-soft negamax alpha-beta with no maximizing/minimizing dual branches;
- full-window exact root search and recursive `(-beta, -alpha)` windows;
- side-to-move scoring and ply-relative mate distance;
- deterministic first-best tie behavior and legal root best moves;
- source-bound legal tokens, make/unmake, and detached line history;
- game-root plus search-line repetition handling;
- checked node accumulation and fail-loud root-history/depth validation;
- exact root position, Zobrist, and history restoration;
- a starting-position depth-three pruning regression below the complete `9,323`-node tree;
- `docs/RUST_NEGAMAX_ALPHA_BETA.md`.

Evidence:

- Exact validated implementation SHA: `d662ca07cae6b0044c1ce620a0dc4f3249784d6c`.
- Permanent CI run/job: `30741988672` / `91480926153`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 124 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13.3 is complete.

## Task 13.3 completion

Implemented and validated:

- curated shallow score equivalence across quiet, tactical, terminal-adjacent, terminal, rule-draw, and repetition-aware positions;
- an independent root-child score oracle proving `d1d8` is the tactical fixture’s unique exact best move;
- alpha-beta node counts no greater than reference counts on every fixture;
- at least one strict pruning witness;
- exact root position, incremental Zobrist, and detached-history restoration after each paired successful search;
- `crates/chess-search/tests/search_equivalence.rs`;
- `docs/RUST_SEARCH_EQUIVALENCE.md`.

Evidence:

- Exact validated implementation SHA: `bdf98a8e7c5cb6aadc55ba3638cd3af2f4ba9e91`.
- Permanent CI run/job: `30743024471` / `91483729312`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 127 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13.4 is complete.

## Task 13.4 completion

Implemented and validated:

- a public `SearchCancellationProbe` callback boundary implemented automatically by `FnMut() -> bool` closures;
- cancellable reference and alpha-beta entry points while preserving the existing never-cancel convenience APIs;
- cancellation checks at node and child boundaries;
- restoration-before-propagation for every recursive child result, including cancellation;
- explicit cancellation error variants with no incomplete score, move, node count, or principal variation;
- repeated-search stability on one mutable game-derived position and detached history;
- mid-tree cancellation after 64 probe checks for both search implementations;
- invariant, incremental/recomputed Zobrist, position snapshot, and history snapshot checks after completion, terminal resolution, validation failure, and cancellation;
- `crates/chess-search/tests/search_immutability.rs`;
- `docs/RUST_SEARCH_IMMUTABILITY.md`.

Evidence:

- Exact validated implementation SHA: `3644e032504b604c210796f1e6c7ef056d05e94b`.
- Permanent CI run/job: `30743519630` / `91485044296`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 131 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13.5 and the overall Task 13 gate are complete; Task 16 still owns full limits, stop-token, iterative-deepening, and partial-result policy.

## Task 13.5 and Task 13 completion

Implemented and validated:

- fixed one-node terminal roots for checkmate precedence, stalemate, dead position, fifty/seventy-five-move draws, and threefold/fivefold repetition draws;
- exact reference/alpha-beta score, best-move, and node-count agreement;
- a shorter-mate witness where `f7e8` is `mate_in(1)` and `f7a7` is `mate_in(3)`;
- a longer-survival witness where `h8g7` is `mated_in(6)` and `h8h7` is `mated_in(4)`;
- deterministic immediate-mate selection at the winning root and unique `h8g7` selection at the forced-loss root;
- explicit one-ply mate normalization for independently searched child roots;
- exact logical-position, detached-history, invariant, and incremental/recomputed-Zobrist restoration after every full-root and per-move oracle search;
- `crates/chess-search/tests/search_terminals.rs`;
- `docs/RUST_SEARCH_TERMINAL_FIXTURES.md`.

Evidence:

- Exact validated implementation SHA: `7ca429b0c883bbb8484d3eb3a4af7d96cdb57201`.
- Permanent CI run/job: `30745120833` / `91489299233`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 135 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13 is complete; Task 14.1 quiescence is next.

## Task 14.1 completion

Implemented and validated:

- standalone and alpha-beta-integrated fail-soft quiescence search;
- stand-pat only outside check and every legal evasion while checked;
- deterministic capture and promotion expansion through source-bound legal tokens;
- shared mate, stalemate, dead-position, repetition, and move-count draw semantics;
- cancellation checks at node and tactical-child boundaries with restoration before error propagation;
- a fail-loud 64-ply tactical guard, including explicit failure when the side remains in check;
- a separate unpruned reference search with quiescence leaves while preserving the original static Task 13 reference API;
- matching-oracle score and node-count equivalence on bounded fixtures;
- fixed hanging-capture, quiet-evasion, promotion, poisoned-capture, draw, cancellation, and guard regressions;
- exact root position, detached history, invariant, and incremental/recomputed-Zobrist restoration;
- `crates/chess-search/tests/search_quiescence.rs` and `docs/RUST_QUIESCENCE_SEARCH.md`.

Evidence:

- Exact validated implementation SHA: `24e1090e17f8b39bdaac4989daffdeaea4b857e9`.
- Permanent CI run/job: `30749044761` / `91499685362`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 140 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Dedicated quiescence suite: 5 passed; matching reference/alpha-beta equivalence suite: 3 passed; terminal/mate-distance suite: 4 passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Tasks 14.2 and 14.3 ordering are complete. Task 14.4 correctness consolidation, Task 15 transposition storage, and Task 16 production limits remain open.

## Task 14.2 completion

Implemented and validated:

- fixed-capacity stack-backed stable ordering over opaque legal-move tokens;
- an explicit transposition-table move hook that returns `None` until Task 15;
- promotion ordering by promoted-piece value, including promotion captures;
- MVV-LVA capture ordering with explicit en-passant pawn-victim semantics;
- generation-stable remaining moves and equal-key ties;
- tactical ordering in production alpha-beta and quiescence search;
- exact generation-order control policy in the unpruned reference search;
- a typed alpha-beta window that preserves the strict lint-clean recursive boundary;
- a fixed narrow-window node-reduction witness with identical fail-soft score and best move;
- exact position, detached-history, invariant, and incremental/recomputed-Zobrist restoration;
- `crates/chess-search/src/move_ordering.rs` and `docs/RUST_TACTICAL_MOVE_ORDERING.md`.

Evidence:

- Exact validated implementation SHA: `3688cb8e89a7da0c7fd34c3756d52d0fcc8d3d33`.
- Permanent CI run/job: `30753873602` / `91512570865`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 145 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- New coverage: four move-ordering unit tests and one quiescence narrow-window node-reduction test.
- Existing search-equivalence, immutability/cancellation, quiescence, terminal/mate-distance, perft, and differential suites remained green.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- SEE remains intentionally absent; Task 14.3 now owns bounded killer/history/stable-tie quiet ordering, while Tasks 15 and 16 own TT storage and real previous-PV data.

## Task 14.3 completion

Implemented and validated:

- fixed-capacity, search-local quiet-ordering state with two killer slots at every supported ply;
- a fixed `2 x 64 x 64` history table keyed by side, source, and destination;
- quiet-cutoff-only learning with depth-squared saturating history bonuses;
- explicit capture/promotion exclusion from killer and history updates;
- deterministic order after tactical moves: primary killer, secondary killer, descending history, then ascending packed move identity;
- an explicit previous-PV hook that remains `None` until Task 16 provides completed-iteration PV data;
- production alpha-beta integration through a lint-clean recursive context carrying ordering state and cancellation;
- generation-order reference control and retained Task 14.2 tactical control;
- exact full-window determinism and a fixed seeded-killer narrow-window node-reduction witness;
- exact position, detached-history, invariant, and incremental/recomputed-Zobrist restoration;
- `docs/RUST_QUIET_MOVE_ORDERING.md`.

Evidence:

- Exact implementation SHA: `f08b2d519ffc066d8d6b18326e03ead278d908de`.
- Focused implementation run/job: `30762211967` / `91534658841`; Cargo check, strict Clippy, and all 51 `chess-search` tests passed.
- Full closure validation run/job: `30762457921` / `91535329886`.
- Results: workspace assets, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 150 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 14.4 consolidated correctness tests are complete; Tasks 14.5, 15, and 16 remain intentionally open.

## Task 14.4 completion

Implemented and validated:

- a true multi-capture horizon sequence (`Qxe5 Rxe5 Rxe5`) searched to a quiet position;
- an in-check leaf that must search a quiet legal evasion and cannot stand pat;
- a promotion sequence searched through forced recapture and counter-recapture;
- a poisoned capture whose static leaf score is explicitly corrected downward by quiescence before root move selection;
- finite guard behavior: one-node stand-pat outside check and fail-loud refusal to truncate while checked;
- exact position, detached-history, invariant, and incremental/recomputed-Zobrist restoration on every new path;
- `crates/chess-search/tests/search_quiescence_task_14_4.rs`.

Evidence:

- Exact validated implementation/evidence SHA: `dc758a3fc62e7f7002191993c73773dd2a71caef`.
- Permanent CI run/job: `30763226685` / `91537383867`.
- Results: workspace assets, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 155 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Dedicated Task 14.4 suite: 5 passed; original quiescence suite: 5 passed; search-equivalence suite: 3 passed; immutability suite: 4 passed; terminal/mate-distance suite: 4 passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 14.5 explicit-exclusion audit and the overall Task 14 gate are complete.

## Task 14.5 and Task 14 completion

Implemented and validated:

- a permanent CI audit over all 10 production `chess-search` Rust modules;
- fail-loud rejection of transcript/review-loop and anti-drift/scenario-scoring identifiers;
- an exact nine-field `MoveOrderKey` boundary containing only TT/PV hooks, tactical material categories, killers, history, and the stable encoded tie-break;
- a restricted ordering read boundary of `Position::piece_at` and `Position::side_to_move` only;
- fail-loud rejection of strategic evaluator identifiers in production move ordering;
- structural enforcement that root alpha-beta uses the complete score window and replaces the best move only for a strictly greater searched score;
- required exact-score and node-reduction witnesses retained in the Rust test tree;
- `scripts/task_14_5_exclusion_audit.py` and `docs/RUST_SEARCH_ORDERING_EXCLUSION_AUDIT.md`.

Evidence:

- Exact validated implementation SHA: `f4dc989e97d8577f4c86bdbfb67ae47e3d5cd7f4`.
- Permanent CI run/job: `30764073097` / `91539614372`.
- Audit output: 10 production Rust files scanned; approved nine ordering fields; ordering position queries limited to `piece_at` and `side_to_move`; all four exact-score/node-reduction witnesses present.
- Results: workspace assets, exclusion audit, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 155 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 14 is complete; Tasks 15.1–15.3 are complete and Task 15.4 safe probe semantics is next.

## Task 15.1 completion

Implemented and validated:

- a complete copyable transposition-entry payload in `crates/chess-search/src/transposition.rs`;
- the full 64-bit Zobrist verification key rather than an index-only fragment;
- `u16` depth and explicit one-byte `Exact`, `Lower`, and `Upper` bound tags;
- a distinct `TranspositionScore` storage-domain wrapper around `Score`;
- optional compact best-move identity and one-byte generation metadata;
- stable public accessors and `chess-search` re-exports;
- a bounded, predictable `repr(C)` layout of at most 24 bytes on supported targets;
- five focused entry-contract tests;
- `docs/RUST_TRANSPOSITION_TABLE_ENTRY.md`.

Evidence:

- Exact validated implementation SHA: `65ef70bfbff3d0bf5fd6e6a19ba20ed5214c3e26`.
- Permanent CI run/job: `30764647127` / `91541116562`.
- Results: workspace assets, Task 14.5 audit over 11 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 160 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Storage allocation, buckets, empty slots, clearing, generation advancement, normalization, probes, replacement, and diagnostics remain intentionally outside Task 15.1.
- Tasks 15.2 fixed-memory storage and 15.3 mate normalization are complete; Task 15.4 safe probe semantics is next.

## Task 15.2 completion

Implemented and validated:

- a fixed-capacity `TranspositionTable` configured in MiB;
- checked MiB-to-byte conversion and whole-cluster budget rounding;
- one private, fallibly reserved `Vec` allocation with no growth or fallback storage;
- four-entry collision clusters and deterministic complete-key cluster indexing;
- typed failures for zero configuration, arithmetic overflow, no complete cluster, and allocator rejection;
- explicit in-place `clear()` preserving allocation and generation;
- explicit wrapping `advance_generation()` retaining existing entries;
- public capacity, allocation, generation, and cluster-index diagnostics required to verify the storage contract;
- five focused storage tests;
- `docs/RUST_TRANSPOSITION_TABLE_STORAGE.md`.

Evidence:

- Exact validated implementation SHA: `6b2ee0081cd47fd9069aeabb0d3ccb1d3659fea9`.
- Permanent CI run/job: `30765303745` / `91542820537`.
- Results: workspace assets, Task 14.5 audit over 11 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 165 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Mate normalization is complete; probe semantics, replacement policy, diagnostics, and search integration remain intentionally outside Task 15.2.
- Task 15.4 safe probe semantics is complete; Task 15.5 deterministic replacement is next.

## Task 15.3 completion

Implemented and validated:

- root-relative to position-relative conversion in `crates/chess-search/src/transposition_score.rs`;
- winning-mate normalization by adding storage ply and denormalization by subtracting probe ply;
- losing-mate normalization by subtracting storage ply and denormalization by adding probe ply;
- exact preservation of every ordinary evaluation score;
- typed rejection of unsupported plies and out-of-domain conversions;
- a crate-private unchecked constructor so public callers must use the tested conversion boundary;
- six focused regressions, including the same winning and losing TT values reached at different plies;
- `docs/RUST_TRANSPOSITION_TABLE_MATE_NORMALIZATION.md`.

Evidence:

- Exact validated implementation SHA: `ac68b99db53546c31f3aae68ad7337ba256eb982`.
- Permanent CI run/job: `30766126491` / `91545080021`.
- Results: workspace assets, Task 14.5 audit over 12 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 171 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Probe semantics are complete; replacement, diagnostics, and production search integration remain intentionally outside Task 15.3.
- Task 15.4 safe probe semantics is next.


## Task 15.4 completion

Implemented and validated:

- a public, storage-only `TranspositionTable::probe` boundary in `crates/chess-search/src/transposition/probe.rs`;
- complete 64-bit verification-key matching after deterministic cluster selection;
- stored-depth sufficiency before score reuse;
- exact-score returns and fail-high/fail-low bound cutoffs at the correct beta/alpha edges;
- current-ply mate-score denormalization before comparison or return;
- verified best-move delivery even when depth or bounds do not permit score reuse;
- explicit `SuppressedForRepetition` handling that disables cached scores while retaining move ordering;
- typed invalid-window and score-conversion failures;
- eight focused probe regressions;
- `docs/RUST_TRANSPOSITION_TABLE_PROBE_SEMANTICS.md`.

Evidence:

- Exact validated implementation SHA: `b6a015e6cc519aa0bbc8e7bde7dde06bdd660b44`.
- Permanent CI run/job: `30766760085` / `91546779835`.
- Results: workspace assets, Task 14.5 audit over 12 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 179 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Insertion, same-key updates, depth/age replacement, diagnostics, and production search integration remain intentionally outside Task 15.4.
- Task 15.5 deterministic replacement is next.

## Task 15 active scope

- [x] Complete Task 15.1 entry design.
- [x] Implement Task 15.2 fixed-memory storage.
- [x] Implement Task 15.3 mate-score normalization.
- [x] Implement Task 15.4 safe probe semantics.
- [ ] Implement Task 15.5 deterministic replacement.
- [ ] Implement Task 15.6 diagnostics and benchmarks.
- [ ] Pass the overall Task 15 gate.

## Task 14 completed scope

- [x] Stand-pat only outside check.
- [x] Search every legal check evasion.
- [x] Search captures and all promotions.
- [x] Preserve fail-soft alpha-beta, draw, repetition, mate-distance, cancellation, and restoration semantics.
- [x] Enforce a bounded fail-loud tactical-ply guard.
- [x] Add independent tactical-oracle and fixed horizon-effect regressions.
- [x] Implement Task 14.2 tactical ordering.
- [x] Implement Task 14.3 quiet ordering.
- [x] Complete Task 14.4 consolidated correctness tests.
- [x] Complete Task 14.5 exclusion audit.
- [x] Pass the overall Task 14 gate.

## Task 13 completed scope

- [x] Implement an unpruned reference minimax/negamax search.
- [x] Count nodes and define terminal/draw scoring.
- [x] Implement negamax alpha-beta using legal tokens and make/unmake.
- [x] Integrate detached root and reversible line repetition history.
- [x] Prove shallow reference/alpha-beta score equivalence.
- [x] Compare uniquely best moves and node counts.
- [x] Prove search restores the root position, Zobrist key, and history exactly.
- [x] Add mate-in-one, mated, stalemate, draw, shorter-mate, and longer-survival fixtures.
- [x] Pass exact-head rustfmt, Cargo check, Clippy, tests, rustdoc, debug, release, perft, and differential gates.

No pull request has been created; work remains on `rust-engine`. Task 15.5 deterministic transposition-table replacement is the next operation.
