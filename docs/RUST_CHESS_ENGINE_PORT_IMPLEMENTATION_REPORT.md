# Rust Chess Engine Port Implementation Report

**Status:** Task 27 full port-program signoff evidence candidate  
**Report date:** 2026-08-04  
**Authoritative specification:** `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md`  
**Authoritative live TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Functional v0.1 evidence:** `docs/RUST_CHESS_ENGINE_V0_1_IMPLEMENTATION_REPORT.md`  
**Exact Task 27 validation implementation:** `PENDING_EXACT_SHA`

## Executive conclusion

The repository contains a complete correctness-first Rust chess-engine program:

- a strict portable rules core;
- a deterministic classical evaluator and search engine;
- a Linux UCI executable;
- a safe Rust facade, versioned C ABI, JNI adapter, and Android harness;
- an explicit opening-book abstraction and indexed format;
- deterministic offline self-play and versioned position datasets;
- named-schema tuning, checkpointing, reporting, and candidate validation;
- permanent correctness, differential, perft, fuzz, Miri, sanitizer,
  performance, Android, and strength-control gates.

Rust is the authoritative implementation for new integrations. The former
Python engine remains in repository history and source form as reference
material; it is not a maintained production engine. Python remains permitted
for the pinned independent `python-chess` differential oracle and repository
validation tooling. Production Rust crates neither embed nor launch Python.

The built-in baseline evaluation weights remain authoritative. The real Task
21.5 production control candidate completed the required 200 color-balanced
opening pairs and 400 games, but its one-sided confidence bound did not exceed
the baseline threshold. It was correctly rejected and never activated. This is
an evidence-backed completion of the tuning and rejection lifecycle, not a
claim that tuning necessarily produced stronger weights. Any future weight
promotion remains a separate strength change and must pass the unchanged
production protocol before explicit activation.

## Evidence boundary

The functional engine baseline is
`332967613098f30348489a73249e822c9eb70bc3`. Task 26 added the permanent v0.1
report, fail-closed audit, playable UCI smoke, and CI wiring at
`80cf18f77d3901e8285553211a45d51b530b5579`. Those exact trees passed Rust CI,
Android JNI, robustness, and architecture-specific performance gates.

Task 27 adds only release governance and traceability:

- this final implementation report;
- an explicit README authority and migration statement;
- a permanent final-port audit;
- CI wiring for that audit;
- tracker closure after exact-SHA evidence is available.

Task 27 does not silently change rules, search, ABI, JNI, UCI behavior, opening
book semantics, default evaluator weights, or tuning acceptance criteria.

## Final architecture and versions

| Component | Version / identity | Primary implementation |
|---|---|---|
| Workspace packages | `0.1.0` | root `Cargo.toml` and crate manifests |
| Minimum supported Rust | `1.75` | root `Cargo.toml` |
| CI validation toolchain | `1.97.1` | permanent workflows and evidence reports |
| Core/search Rust API | package `0.1.0` | `crates/chess-core`, `crates/chess-search` |
| UCI engine | `chess-engine-rust 0.1.0` | `crates/chess-uci` |
| C ABI | schema/version `1` | `crates/chess-ffi` |
| JNI adapter | package `0.1.0`, versioned native ABI contract | `crates/chess-jni`, `android-harness` |
| Opening-book format | version `1` | `crates/chess-book` |
| Self-play config | schema `1` | `crates/chess-tools/src/self_play.rs` |
| Self-play openings | schema `1` | `crates/chess-tools/src/self_play.rs` |
| Self-play dataset | schema `1` | `crates/chess-tools/src/self_play.rs` |
| Evaluation weight schema | version `1` | `crates/chess-search/src/weights.rs` |
| Evaluator structure schema | version `1` | `crates/chess-search/src/weights.rs` |
| Tuning/checkpoint/report artifacts | versioned, checksummed schemas | `crates/chess-tune`, `crates/chess-tools/src/tuning` |
| Candidate-validation report | version `1` | `crates/chess-tools/src/candidate_validation.rs` |

The dependency direction is intentionally outward:

```text
chess-core
    -> chess-search
    -> outward adapters and tools

chess-book is adapter-neutral.
chess-uci, chess-ffi, chess-jni, chess-tools, and chess-tune do not become
inward dependencies of the core rules layer.
```

## Specification traceability

Every numbered specification section is mapped below to implementation,
validation, and documentation. A section may be satisfied by implementation,
an explicit rejection decision, or a documented deferral when the
specification itself identifies it as non-goal or future work.

| Spec section | Resolution | Primary paths and evidence |
|---:|---|---|
| 1 | Program goals and boundaries implemented | workspace crates; `README.md`; architecture documentation |
| 2 | Existing Python implementation inventoried and preserved | `docs/RUST_CHESS_ENGINE_PORT_BASELINE_2026-08-01.md`; Python source retained |
| 3 | Rust architecture and dependency direction implemented | `docs/RUST_WORKSPACE_ARCHITECTURE.md`; root `Cargo.toml` |
| 4 | Compact core value types implemented | `crates/chess-core/src`; coordinate and move documentation/tests |
| 5 | Hybrid position representation and invariants implemented | position modules; property/invariant tests |
| 6 | Strict FEN and UCI move notation implemented | FEN/notation modules and malformed-input regressions |
| 7 | Attack generation implemented and tested | core attack modules and exhaustive edge fixtures |
| 8 | Pseudo-legal generation implemented | core move-generation modules and focused tests |
| 9 | Complete legal generation and special rules implemented | legal generation, castling, en-passant, promotion, and perft tests |
| 10 | Exact make/unmake implemented | move application/undo modules and byte-for-byte restoration properties |
| 11 | Zobrist hashing and repetition identity implemented | hash/history modules and recomputation/repetition tests |
| 12 | Game history and draw semantics implemented | game-status/history modules and terminal/draw suites |
| 13 | Reference search and alpha-beta implemented | `crates/chess-search/src/reference.rs`, `alpha_beta.rs` |
| 14 | Quiescence and bounded ordering implemented | quiescence, move-ordering, correctness and exclusion audits |
| 15 | Fixed-capacity transposition table implemented | TT modules, mate normalization, replacement and diagnostics tests |
| 16 | Iterative deepening, limits, PV, and cancellation implemented | iterative-deepening modules and limit/cancellation suites |
| 17 | Linux UCI adapter implemented | `crates/chess-uci`; real subprocess integration suite |
| 18 | Rust facade, C ABI, JNI, and Android implemented | `crates/chess-ffi`, `crates/chess-jni`, `android-harness` |
| 19 | Optional opening-book capability implemented | `crates/chess-book`; indexed-format and adapter integration tests |
| 20 | Offline self-play and versioned datasets implemented | `crates/chess-tools/src/self_play.rs`; `docs/RUST_SELF_PLAY_DATASET.md` |
| 21 | Named-schema tuning and candidate lifecycle implemented | `crates/chess-tune`; tuning/report/candidate-validation modules |
| 22 | Advanced classical terms evaluated selectively | `advanced_evaluation.rs`; all eight candidates explicitly accepted/revised/rejected; none silently activated |
| 23 | Property, fuzz, Miri, sanitizer, and failure-preservation gates implemented | `fuzz/`; robustness workflow; `docs/RUST_ROBUSTNESS_GATES.md` |
| 24 | Benchmarks, profiling, Android measurements, and regression controls implemented | performance harness/scripts/workflow; `benchmarks/task24` |
| 25 | CI, documentation, developer commands, and artifact policy implemented | permanent workflows; `scripts/dev.sh`; developer/artifact docs |
| 26 | Functional v0.1 signoff completed | `docs/RUST_CHESS_ENGINE_V0_1_IMPLEMENTATION_REPORT.md`; Task 26 audit and UCI smoke |
| 27 | Optional capability and migration audit completed by this report | Tasks 19–25 evidence plus migration sections below |
| 28 | Rules acceptance criteria satisfied | strict parsing, legal generation, perft, differential validation |
| 29 | Search acceptance criteria satisfied | reference equivalence, terminal scores, TT, PV, limits, cancellation |
| 30 | Adapter acceptance criteria satisfied | UCI subprocess, safe facade, C lifecycle, JNI/API-35 tests |
| 31 | Portability acceptance criteria satisfied | x86-64, native AArch64, Android ARM64/x86-64 gates |
| 32 | Reproducibility and diagnostics satisfied | fixed seeds, schemas, checksums, exact commands, reports and artifacts |
| 33 | Performance policy satisfied without weakening correctness | architecture-specific budgets and independent correctness gates |
| 34 | Security/robustness boundaries satisfied | panic containment, opaque handles, explicit lengths, fuzz/Miri/sanitizers |
| 35 | Python migration policy resolved | Rust authoritative; Python preserved reference-only; oracle tooling retained |
| 36 | Known limitations and roadmap recorded | final roadmap section below |
| 37 | Final release governance enforced | Task 27 audit, exact-SHA CI evidence, tracker/report closure sequence |

## TODO traceability

Tasks 0–26 have individual completion evidence in:

- `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`;
- `docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md`;
- `docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md`.

Task 27 consolidates rather than duplicates those gates.

| Task range | Delivered capability | Final disposition |
|---|---|---|
| 0–1 | baseline, decisions, workspace, CI skeleton | complete |
| 2–12 | rules core, notation, generation, state transitions, hashing, game semantics | complete |
| 13–16 | reference and production search, TT, iterative deepening, limits, cancellation | complete |
| 17–18 | UCI, safe API, C ABI, JNI, Android | complete |
| 19 | opening book | complete and optional by explicit injection |
| 20 | self-play and position dataset | complete |
| 21 | tuning, checkpoint, report, candidate validation and rejection lifecycle | complete; no candidate activated because the production candidate failed strength acceptance |
| 22 | advanced evaluation candidates | complete; every proposed area has an explicit evidence-backed decision |
| 23–25 | robustness, performance, CI, documentation, developer workflows | complete |
| 26 | playable portable v0.1 signoff | complete |
| 27 | migration, traceability, final report and release evidence | evidence candidate pending exact final SHA |

## Optional-capability audit

### Opening book

The adapter-neutral `chess-book` crate provides an explicit abstraction,
versioned indexed format, checksum/corruption validation, deterministic and
seeded weighted selection, and UCI integration. No book is discovered from a
conventional path. The engine remains fully usable without a book.

### Self-play and datasets

`chess-tools` provides explicit self-play generation, validation, and replay.
Configuration, opening input, game records, position records, train/validation/
test partitions, engine identity, weight identity, search settings, seeds,
termination reason, filtering reason, duplicate occurrence counts, and replay
commands are versioned and validated.

### Tuning and candidate validation

The tuning stack provides:

- stable named parameters and separately versioned structural constants;
- strict checksummed artifacts with training provenance;
- calibrated Texel-style loss;
- deterministic SPSA with bounds, regularization, checkpoint and exact resume;
- complete initial/final training and validation reports;
- a fail-closed candidate-versus-baseline protocol.

The production control candidate was deliberately distinct in artifact identity
but used baseline values as a protocol control. It produced 200 independent
opening pairs and 400 color-swapped games with mean pair score `0.5`, standard
error `0.0`, lower confidence bound `0.5`, decision `rejected_strength`, and
`activated=false`. This proves the gate rejects a non-improving candidate.

No API, report, test, workflow, or generated artifact can activate weights.
Future activation requires a real accepted report followed by a separate,
reviewable source change that updates the built-in weight identity and values.

### Advanced evaluation terms

Eight candidate areas were evaluated under a common versioned protocol.
Defender coordination and additional endgame phase-specific scaling were
rejected as overlap. Richer pawn-majority/candidate-passer modeling, improved
king-zone attack units, rook/queen batteries, outposts/bad bishops,
king/passer races, and general simplification incentives were rejected for
insufficient strength evidence under the controlled run. No historical
transcript guidance or position-specific patch was admitted.

### Performance and Android lifecycle

Permanent performance gates compare x86-64 and native AArch64 distributions.
Android validation covers both JNI ABIs, host-JVM declarations/contracts,
Kotlin lint, APK/test APK assembly, API-35 execution, repeated lifecycle,
off-main search, cancellation latency, JNI overhead, nodes per second, and
native heap scaling by hash size.

## Python migration decision

The migration decision is:

1. **Rust is authoritative.** New product integrations must use the safe Rust
   facade, UCI process, C ABI, or JNI boundary.
2. **Python is reference-only.** The former Python engine is not maintained as
   a second production implementation and has no engine-development CI.
3. **History is preserved.** Python source, useful fixtures, and Git history are
   retained. This signoff does not delete the Python implementation.
4. **Validation tooling remains allowed.** The pinned `python-chess` oracle and
   Python repository scripts are validation infrastructure, not runtime engine
   dependencies.
5. **No hidden fallback exists.** Production Rust crates do not embed, import,
   or spawn Python.

## Retained, redesigned, and rejected Python concepts

### Retained as concepts

- standard chess rules and UCI behavior;
- classical material, piece-square, mobility, pawn, rook, king-safety, space,
  and king-activity evaluation concepts;
- iterative deepening, alpha-beta, quiescence, move ordering, TT, and opening
  book as general engine concepts;
- perft positions, useful fixtures, self-play, and offline tuning as validation
  and development workflows.

### Redesigned under Rust contracts

- mutable board state became a private hybrid position with redundant invariant
  checks and exact undo records;
- multiple move shapes became one packed internal move identity;
- permissive parsing became strict typed FEN and notation errors;
- clone-per-child search became make/unmake recursion;
- string search keys became incremental typed Zobrist identity;
- unbounded dictionaries became a fixed-capacity clustered TT;
- global UCI state became per-session owned state and request-local
  cancellation;
- implicit files became explicit injection and versioned artifacts;
- Python-facing integration became safe Rust, opaque C handles, JNI ownership,
  and panic containment;
- informal tuning became named schemas, checksums, checkpoints, held-out
  validation, color-balanced matches, and explicit activation separation.

### Rejected

- incorrect insufficient-material/dead-position shortcuts;
- castling safety with the source king incorrectly blocking attack lines;
- raw en-passant fields in every repetition key;
- implicit queen promotion in core execution;
- clone-per-child production search;
- string position keys;
- unbounded per-search TT allocation;
- missing mate-score normalization;
- unchecked root heuristic interactions with alpha-beta bounds;
- automatic weight or book discovery;
- global UCI control/output state;
- `review_loop_guidance`, `anti_drift_guidance`, transcript-specific move
  preferences, historical-position windows, and similar narrow patches.

## Exact functional evidence inherited from Task 26

| Gate | Exact run | Jobs / result |
|---|---:|---|
| Rust CI | `30962735433` | `92169954502`, `92169954449`; x86-64 and native AArch64 passed |
| Android JNI | `30962735439` | `92169954196`, `92169954245`, `92169954247`; lint, host JVM, dual ABI, API-35 passed |
| Robustness | `30962735450` | `92169954098`, `92169954164`, `92169954171`; fuzzing, Miri, ASan/LSan, TSan passed |
| Performance | `30962735451` | `92169954438`, `92169954397`; x86-64 and AArch64 budgets passed |

The exact Task 26 workspace results were **377 passed, 4 ignored, 0
failed**, plus release depth-four authoritative perft, warning-free rustdoc,
debug/release builds, a playable UCI smoke, and the independent differential
oracle.

Differential validation covered:

```text
15 corpus positions
293 child FENs
272,991 oracle perft nodes
576 seeded plies
seed = 0xC0FFEE
```

## Authoritative perft

| Position | d1 | d2 | d3 | d4 | d5 |
|---|---:|---:|---:|---:|---:|
| Starting position | 20 | 400 | 8,902 | 197,281 | 4,865,609 |
| Kiwipete | 48 | 2,039 | 97,862 | 4,085,603 | 193,690,690 |
| En-passant rook ending | 14 | 191 | 2,812 | 43,238 | 674,624 |
| Castling, promotion and pins | 6 | 264 | 9,467 | 422,333 | 15,833,292 |
| Promotion check evasion | 44 | 1,486 | 62,379 | 2,103,487 | 89,941,194 |
| Tactical/positional | 46 | 2,079 | 89,890 | 3,894,594 | 164,075,551 |

Depth four is permanent push CI. Depth five is scheduled/manual because its
largest cases are intentionally expensive.

## Performance baselines

The Task 26 signoff used GitHub-hosted Ubuntu 24.04.4 LTS, x86-64 and native
AArch64 runners, `rustc 1.97.1`, LLVM 22.1.6, release builds, and seven samples.
Selected x86-64 medians were:

| Benchmark | Median | Allocation result |
|---|---:|---|
| Leaper attack lookup | 1 ns/op | zero |
| Sliding attack sweep | 10,072 ns/op | zero |
| Legal move generation | 2,158 ns/op | zero |
| Make/unmake | 39 ns/op | zero |
| Full hash recomputation | 52 ns/op | zero |
| Incremental hash update | 77 ns/op | zero |
| Full evaluation | 717 ns/op | zero |
| Starting-position perft d4 | 14,712,461 ns | zero |
| Kiwipete perft d3 | 7,064,686 ns | zero |
| Starting search, 20,000 nodes | 76,994,469 ns | bounded |
| Tactical search, 20,000 nodes | 108,317,654 ns | bounded |
| FFI fixed-node search | 19,793,134 ns | bounded |

Reference artifacts:

- x86-64 `8913539885`;
- native AArch64 `8913538200`;
- Android metrics `8913595215`.

Android API-35 evidence recorded legal-move JNI average `70,524 ns`, fixed-node
throughput `71,163 nodes/s`, cancellation response `1,715,438 ns`, and native
heap deltas consistent with 1 MiB and 16 MiB TT budgets.

## Known limitations and future roadmap

These do not invalidate the completed port contract:

- Search is single-threaded; there is no Lazy SMP or parallel root search.
- There is no NNUE or other neural evaluator.
- There is no Syzygy/tablebase integration.
- There is no distributed search, network service, WebAssembly target, or
  `no_std` target.
- Opening books are optional and explicitly injected.
- The baseline evaluator remains active because no candidate has passed the
  production strength gate. Producing and promoting a stronger candidate is a
  future strength improvement, not an incomplete correctness or portability
  requirement.
- Direct legal generation, improved sliding attacks, SEE/quiescence redesign,
  incremental evaluation components, compact move lists, and tighter TT
  packing remain measured optimization candidates. They must not bypass
  correctness gates.
- Open operational issues or historical workflow-trigger records that have no
  P0/P1 correctness designation do not alter the engine guarantees; they may be
  administratively closed separately.

## Final release gate

Task 27 may be marked complete only when all of the following are true:

- this report contains an exact non-placeholder Task 27 validation SHA;
- the permanent Task 27 audit passes on that SHA;
- Rust CI, Android JNI, robustness, and performance workflows pass on that
  exact SHA or are explicitly mapped to an unchanged functional tree;
- Task 27 checklists and the Ralph status are closed with exact evidence;
- no unresolved P0/P1 correctness issue exists;
- no temporary Task 21/Task 27 discovery or closure helper remains;
- README identifies Rust as authoritative and Python as reference-only;
- the report does not claim that rejected weights were accepted or activated.

Until those conditions are recorded, this document remains an evidence
candidate rather than a completion assertion.
