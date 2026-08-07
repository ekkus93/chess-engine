# Rust Chess Engine v0.2 Strength Program Specification

**Status:** Complete — program closed without v0.2 promotion
**Date:** 2026-08-05
**Branch:** `master`
**Companion TODO:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md`
**Closure report:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_IMPLEMENTATION_REPORT.md`
**Closure outcome:** No candidate was promoted; package/UCI v0.1 remains authoritative.
**Completed v0.1 port tracker:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`
**Completed port report:** `docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md`
**Post-port review record:** `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md`
**Planning baseline:** `51cb4fa1b281bd1a6a7d7af20ff3f4a8d99a4e51`

---

## 1. Purpose

The Rust port is complete, correct, portable, playable, and permanently validated. The next program is not another porting or cleanup exercise. It is a bounded strength-development program whose purpose is to make the engine materially stronger while preserving every correctness, reproducibility, portability, robustness, and integration guarantee established by v0.1.

The program must improve strength through measured, independently reviewable changes. It must not convert plausible chess-engine folklore into production behavior without evidence. A change may complete its task by being accepted, rejected, revised, or deferred, but no experimental feature becomes authoritative merely because it was implemented.

The first substantive milestone is:

1. establish an exact v0.1 strength and search-efficiency baseline;
2. implement a correct, allocation-free Static Exchange Evaluation primitive;
3. evaluate SEE first as a semantics-preserving move-ordering aid;
4. only then evaluate SEE-based quiescence pruning as a separate search-semantic change.

---

## 2. Program outcomes

The program has two possible honest outcomes.

### 2.1 Successful v0.2 release

A v0.2 release may be declared only when at least one explicit search/evaluation candidate:

- passes the complete correctness and robustness matrix;
- passes the production strength protocol against the authoritative v0.1 baseline;
- satisfies the configured performance and unfinished-game limits;
- is activated by a separate reviewed source/configuration change;
- passes the complete post-activation release matrix on an exact SHA.

### 2.2 Completed experiment program without a v0.2 release

If no candidate passes the production strength gate, the experiment tasks may still be completed with evidence-backed rejection or deferral decisions. In that case:

- v0.1 remains authoritative;
- package and protocol versions are not relabeled v0.2;
- no experimental feature is silently enabled;
- the final report must say that the strength program completed without a promoted candidate.

Lack of evidence is rejection, not acceptance.

---

## 3. Existing contracts that remain authoritative

The program inherits all v0.1 contracts, including:

- Rust is the authoritative production implementation.
- Python is reference-only except for independent oracle and repository tooling.
- Rules and state transitions remain in `chess-core`.
- Search and evaluation remain in `chess-search`.
- UCI, C ABI, JNI, Android, books, tuning, and tools remain outward adapters.
- Recursive search uses make/unmake, not clone-per-child.
- Position identity uses typed incremental Zobrist hashing, not FEN or strings.
- Transposition storage is bounded and mate-score safe.
- Parsing, ABI/JNI failures, cancellation, and internal contradictions remain fail-loud.
- Books, weights, datasets, tablebases, and configuration are explicitly injected.
- No panic may cross the C or JNI boundary.
- Correctness, performance, robustness, and strength are independent gates.
- Generated evidence never changes runtime defaults automatically.

The v0.1 baseline evaluator and search configuration remain authoritative until an explicit activation commit passes the final release gate.

---

## 4. Non-goals

The following are not initial v0.2 requirements:

- NNUE or another neural evaluator;
- Lazy SMP, parallel root search, or distributed search;
- a network service;
- WebAssembly or `no_std` support;
- automatic opening-book, weight, or tablebase discovery;
- replacing the existing legal move generator before measured evidence justifies it;
- copying Stockfish implementation details without an independently specified contract;
- changing C ABI or JNI behavior merely to expose experiments;
- enabling a collection of pruning heuristics in one unreviewable patch;
- accepting a faster candidate that is weaker or tactically unsafe;
- accepting a stronger candidate that violates correctness, determinism, lifecycle, memory, or portability requirements.

NNUE and parallel search may be future programs after the classical single-threaded engine has a stronger, well-measured baseline.

---

## 5. Governing principles

### 5.1 One independently measurable candidate at a time

Each search-semantic feature must have:

- a stable identifier;
- explicit parameters;
- an isolated implementation diff;
- deterministic unit and integration tests;
- before/after search diagnostics;
- a correctness disposition;
- a performance disposition;
- a strength disposition;
- an explicit activation state.

A compound candidate may be evaluated only after its components have individual evidence and the combination has its own identity.

### 5.2 Three independent evidence axes

Every candidate is evaluated on three separate axes:

1. **Correctness and safety** — rules, mate distance, draws, history, legal PVs, restoration, cancellation, fuzzing, Miri, sanitizers, ABI/JNI lifecycle, and differential validation.
2. **Performance and search efficiency** — wall time, nodes, qnodes, selective depth, cutoffs, TT behavior, allocations, and architecture-specific distributions.
3. **Strength** — color-balanced games using independent opening pairs and a fail-closed confidence bound.

Passing one axis cannot compensate for failing another.

### 5.3 Fail-loud experiments

Experimental paths must not:

- catch an internal error and continue with a weaker hidden path;
- silently disable themselves after an invariant failure;
- convert an unsupported position into a neutral score;
- ignore a failed tablebase probe as though no tablebase entry existed;
- use a default parameter after malformed configuration;
- swallow overflow, cancellation, history, or TT score-conversion errors;
- report an incomplete search as exact;
- accept a partial narrow-window result without required verification.

A deliberately unavailable optional capability is different from a failed configured capability. Absence may be normal; configured corruption or probe failure is an error.

### 5.4 Explicit activation boundary

Implementation, validation, acceptance, and activation are four separate states.

- An implemented feature is inactive by default.
- A validated feature has passed correctness and development evidence.
- An accepted feature has passed the production strength protocol.
- An activated feature has been enabled by a separate reviewed commit and has passed the post-activation release matrix.

No report, artifact, workflow, benchmark, or test may activate production behavior.

---

## 6. Program authority and document governance

The v0.1 port tracker and definitions remain immutable completed-program evidence. They are not reopened by v0.2.

While this program is active, authority is:

1. this specification for requirements and boundaries;
2. `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md` for live execution status;
3. the existing v0.1 reports for inherited guarantees;
4. `docs/LEGACY_TODO_INDEX.md` for active/historical TODO classification.

The completed post-port review TODO must be reclassified as a completed historical record when v0.2 begins. The permanent TODO-authority audit must recognize this v0.2 TODO as active and fail if an unclassified TODO-named file appears.

---

## 7. Baseline identity

Before any strength change, the program must freeze a reproducible baseline record containing:

- exact source SHA;
- package, UCI, Rust API, C ABI, JNI, book, weight, dataset, and report identities;
- Rust and LLVM versions;
- runner architecture and image;
- release profile and relevant compiler settings;
- authoritative default weights and checksum;
- authoritative search policy and checksum;
- transposition-table size;
- opening suite and checksum;
- search limit and time-control definitions;
- game maximum-ply and draw-claim policy;
- all random seeds;
- exact command lines;
- performance reference artifacts;
- strength report artifacts.

The baseline must be runnable from explicit inputs. It may not depend on a developer home directory, ambient current working directory, unversioned opening set, or conventional data-file path.

---

## 8. Search-policy identity

### 8.1 Typed policy

Introduce a typed, versioned search-policy identity for candidate evaluation. The policy should represent only search-semantic choices that need experimental comparison, such as:

- PVS enabled/disabled;
- SEE capture-ordering enabled/disabled;
- SEE quiescence pruning enabled/disabled;
- quiescence delta pruning and margins;
- LMR enabled/disabled and reduction table identity;
- null-move enabled/disabled and restrictions;
- futility/razoring enabled/disabled and margins;
- accepted check-extension configuration;
- any later accepted selective-search feature.

The built-in v0.1 policy must have a stable semantic identifier and checksum. Candidate policies must serialize exact parameter values and schema versions.

### 8.2 Default behavior

The normal public search entry points continue to use the authoritative built-in policy. Experimental policy injection is initially restricted to Rust tools and controlled test entry points.

No experimental UCI option, C ABI field, JNI method, or Android setting is required before acceptance. If external exposure becomes necessary, it must be additive, versioned, explicit, and separately reviewed.

### 8.3 Evaluator separation

A candidate may vary search policy, evaluation weights, or both, but the report must distinguish them. Candidate and baseline searches must use separate transposition tables whenever stored values could depend on policy or evaluation identity.

---

## 9. Strength validation for engine variants

The existing weight-candidate protocol is the minimum model, but v0.2 requires a generalized engine-variant protocol.

### 9.1 Candidate identity

A candidate identity binds:

- exact source SHA;
- engine/package identity;
- search-policy schema, identifier, parameters, and checksum;
- evaluation-weight identifier and checksum;
- opening-book state and checksum if explicitly used;
- tablebase state and identity if explicitly used;
- TT size and replacement policy identity;
- search limits/time control;
- build/toolchain identity;
- exact invocation.

### 9.2 Validation tiers

Three tiers are permitted:

- **Smoke:** small deterministic run used only to catch integration failures.
- **Development:** medium paired run used for iteration and rejection decisions.
- **Production:** at least 200 independent opening pairs and 400 color-swapped games.

Only production evidence may accept a candidate for activation.

### 9.3 Correctness before games

Before any strength games, the candidate must pass the applicable correctness gate:

- complete Rust tests;
- authoritative perft through depth four;
- independent differential corpus and seeded legal playouts;
- mate-distance, stalemate, draw, repetition, promotion, en-passant, and castling fixtures;
- legal principal-variation replay and exact restoration;
- cancellation and limit behavior;
- candidate-specific tactical and equivalence tests;
- policy/artifact checksum and schema validation.

Ordering-only candidates such as SEE ordering or PVS must additionally demonstrate exact score/best-move parity over a defined deterministic corpus at supported depths, except where equal-score tie ordering is explicitly allowed and recorded.

Pruning candidates may change node counts and searched lines, but must pass targeted tactical, quiet-resource, zugzwang, promotion-race, mate-distance, and endgame suites.

### 9.4 Match protocol

Production validation retains the existing fail-closed paired protocol:

- at least 200 semantically distinct openings;
- candidate and baseline each play both colors from the same opening;
- pairs are the independent statistical units;
- one-sided 95% lower confidence bound with `z = 1.6448536269514722`;
- lower bound must be strictly greater than `0.5 + minimum_score_margin`;
- unfinished-game rate must remain below its configured ceiling;
- tied or inconclusive candidates are rejected.

The report must separately record wins, draws, losses, unfinished games, crashes, illegal moves, time forfeits, and infrastructure failures. Infrastructure failure invalidates the run; it is not scored as a chess result unless the protocol explicitly and symmetrically defines that behavior in advance.

### 9.5 Fixed-node and time-control evidence

At least one fixed-node protocol and one clock-based protocol should be maintained.

- Fixed-node matches isolate search selectivity and evaluation effects from speed.
- Clock-based matches measure the combined effect of search efficiency and playing strength.

A candidate intended only as a speed optimization must show fixed-node non-regression and clock-based improvement. A candidate intended as a search-semantic improvement must show strength evidence under the release-relevant protocol.

---

## 10. Search diagnostics

Add deterministic counters sufficient to explain why a candidate changed behavior. Candidate reports and benchmark output should include applicable values for:

- main nodes and qnodes;
- selective depth;
- beta cutoffs;
- first-move cutoffs;
- TT probes, hits, reusable scores, ordering-only hits, stores, replacements, and hash fullness;
- PVS zero-window searches and full-window re-searches;
- SEE calls, cache-free operation count, winning/equal/losing classifications;
- quiescence SEE prunes and delta prunes;
- LMR reductions, verification re-searches, and restored full-depth searches;
- null-move attempts, cutoffs, verification searches, and disabled-by-policy nodes;
- futility/razoring attempts and prunes;
- cancellation observation latency;
- elapsed time and nodes per second.

Counters must not change search semantics. Overflow must be detected or saturating behavior must be explicitly specified and tested. Expensive trace data must remain separate from the normal hot path.

---

## 11. Static Exchange Evaluation

### 11.1 Scope

SEE estimates the material result of a capture sequence on one target square under alternating least-valuable-attacker recaptures. The first implementation is an ordering primitive, not a replacement for legal search.

### 11.2 Required behavior

SEE must correctly model:

- ordinary captures;
- en-passant occupancy changes;
- quiet and capture promotions, including promotion value change;
- x-ray rook, bishop, and queen attackers revealed after removals;
- pawn attack direction;
- king participation without declaring an illegal king capture profitable;
- stable piece values independent from tuned positional weights;
- deterministic equality classification;
- bounded fixed-capacity local storage;
- zero heap allocation in the normal path.

The algorithm must not mutate the caller's position. It may use local occupancy and attacker sets derived from the position.

### 11.3 API and errors

Use a small typed value/result API. Invalid inputs that contradict the supplied position must fail loudly rather than return zero. The API must distinguish at least:

- valid SEE value;
- non-capture or unsupported move category when the caller used the wrong entry point;
- source/target/move-state contradiction;
- internal bounded-capacity or arithmetic failure if such a state is possible.

### 11.4 Validation

SEE requires:

- hand-authored x-ray, defended-capture, overloaded-defender, en-passant, promotion, and king-recapture fixtures;
- symmetry tests;
- no-mutation tests;
- zero-allocation benchmark coverage;
- comparison against an independent brute-force legal capture-sequence oracle on a curated corpus and deterministic generated positions.

### 11.5 Initial integration

The first production candidate may use SEE only for capture ordering. It must not prune moves. This candidate is expected to preserve exact search scores while changing node order/count.

---

## 12. Quiescence redesign

The current measured profile identifies quiescence as the dominant fixed-node search cost. Changes must be staged.

### 12.1 Stage A: SEE ordering

- Order tactical moves by explicit TT/promotion policy and SEE class/value.
- Preserve deterministic packed-move tie breaks.
- Do not prune.
- Require exact-score parity and tactical equivalence.

### 12.2 Stage B: SEE pruning

A later candidate may omit clearly losing non-checking captures only under a precisely documented threshold.

Never SEE-prune:

- an in-check evasion;
- a legal promotion unless separately proven safe;
- a checking move under the initial policy;
- the only legal tactical response;
- a move needed to preserve a mate score;
- an en-passant case not covered by the validated SEE contract.

A move pruned by SEE must be counted and reproducible from policy identity.

### 12.3 Stage C: delta pruning

Delta pruning may be evaluated only after SEE pruning is stable. Margins must be typed, bounded, versioned, and based on explicit material gain limits. Never delta-prune in check or near mate-score domains.

### 12.4 Guard behavior

The existing quiescence depth guard remains fail-loud in check. No redesign may convert guard exhaustion in check into stand-pat, zero, or static evaluation.

---

## 13. Principal Variation Search

PVS is the first selective-search candidate after SEE/quiescence foundations.

Required behavior:

- search the first ordered move with the full window;
- search later moves with a valid null window;
- perform a full-window re-search whenever the narrow result could improve the exact node value;
- never store or report an unverified narrow-window result as exact;
- preserve mate-distance normalization and TT bound semantics;
- preserve cancellation, node-limit, and restoration behavior;
- retain deterministic equal-score policy.

Validation requires exact score and legal-PV parity with the current full-window alpha-beta implementation over a bounded deterministic corpus, plus node-count evidence.

---

## 14. Late Move Reductions

LMR may be evaluated only after PVS and move ordering are stable.

The initial candidate may reduce only moves that are all of:

- quiet;
- non-promotion;
- non-checking;
- sufficiently late in the ordered move list;
- outside the principal-variation first move;
- searched at sufficient remaining depth;
- not an explicit TT move or protected tactical candidate.

A reduced search that raises alpha must be re-searched at the required full depth before its result is accepted. Reduction tables and thresholds must be versioned and bounded.

Targeted tests must cover quiet tactical resources, defensive moves, forced mates, promotion races, and low-mobility endgames.

---

## 15. Null-move pruning

Null-move pruning is optional and high risk. It may be rejected or deferred without blocking the program.

If implemented, it requires a dedicated reversible search-only position transition. It must not be representable as a legal chess move or exposed through game/UCI move APIs.

The policy must conservatively disable null move in at least:

- check;
- pawn-only or low-material zugzwang-prone endings;
- positions below a configured non-pawn-material threshold;
- shallow depth;
- mate-sensitive windows;
- consecutive null-move contexts;
- positions where history/TT semantics cannot be proven safe.

The transition must explicitly define side-to-move, en-passant, clocks, hash identity, undo, history treatment, and TT reuse. Any ambiguity blocks implementation.

A null-move cutoff may require a verification search under configured conditions. Dedicated zugzwang, stalemate, repetition, fifty-move, mate-distance, and restoration suites are mandatory.

---

## 16. Futility pruning, razoring, and quiet-move selectivity

These are optional later candidates and must be independent.

### 16.1 Futility pruning

Initially limited to shallow non-PV, non-check nodes and quiet non-checking moves. Static-evaluation margins must be explicit and versioned. Checks, promotions, tactical captures, mate-score windows, and forced evasions are excluded.

### 16.2 Razoring

Razoring is evaluated only if profiling and node evidence justify it after futility work. It must not turn an uncertain frontier into an exact score without verification.

### 16.3 Quiet-move pruning

Late quiet-move pruning may be considered only after LMR evidence. It must protect TT moves, killers, strong-history moves, checks, promotions, and low-mobility positions according to an explicit policy.

Each candidate requires its own tactical and strength disposition.

---

## 17. Measured hot-path optimization

After accepted or rejected SEE/search candidates, rerun Callgrind and architecture-specific baselines. Optimization work must follow current evidence, not the old profile alone.

The decision set includes:

- direct legal generation using checkers, pins, and evasion masks;
- alternative sliding-attack implementation;
- incremental evaluation components;
- compact move-list representation;
- tighter TT entry packing or cluster layout;
- reduced search allocation or initialization overhead.

Each area must receive an explicit `implement`, `reject`, or `defer` decision with profile evidence.

A direct legal-generation rewrite, if selected, must retain the current pseudo-legal-plus-validation path as an independent test oracle until exhaustive equivalence, perft, differential, property, fuzz, and restoration evidence is complete. It must not be activated solely because perft is faster.

---

## 18. Syzygy tablebases

Syzygy support is optional and follows the core search-strength milestones.

### 18.1 Architecture

Tablebase probing must be an outward optional capability, preferably behind a dedicated adapter-neutral interface or crate. The core rules layer must not discover files or depend on a platform filesystem.

### 18.2 Explicit configuration

The caller supplies:

- enabled/disabled state;
- exact path(s) or provider;
- supported piece-count limit;
- probe policy;
- tablebase implementation/version identity.

No conventional path or environment variable is searched implicitly.

### 18.3 Failure policy

- Disabled or not configured: normal engine search.
- Configured position outside supported scope: typed `not_applicable`, then normal search.
- Configured data missing, corrupt, incompatible, or probe failure: fail visible according to adapter policy; do not silently claim `not_applicable`.

### 18.4 Semantics

WDL/DTZ mapping, fifty-move interaction, root move selection, mate scores, UCI reporting, and TT storage must be explicitly specified before production integration. Licensing and dependency provenance must be reviewed before choosing an implementation.

---

## 19. Public API, UCI, C ABI, JNI, and Android

### 19.1 Compatibility

The program should preserve existing v0.1 public contracts whenever possible. Internal search-policy injection belongs in Rust tools until a candidate is accepted.

### 19.2 Additive changes

Any required external configuration must be additive and versioned:

- a new Rust request/configuration type rather than changing old semantics;
- a new C ABI record version or additive function rather than reinterpreting fields;
- matching JNI/Kotlin ownership and lifecycle tests;
- explicit Android off-main execution and cancellation behavior.

### 19.3 UCI

Accepted production features may be built into the authoritative policy. Optional user-configurable features require documented UCI options with exact defaults and validation. Unknown/invalid values remain fail-visible and transactional.

Experimental options must not be advertised by the release engine unless they are intentionally supported product behavior.

---

## 20. Performance requirements

Performance gates remain architecture-specific and semantically checksummed.

New benchmark rows should cover:

- SEE representative captures;
- SEE capture ordering;
- quiescence candidate searches;
- PVS/LMR diagnostic fixtures;
- engine-variant match overhead;
- tablebase probe overhead if implemented.

Zero allocation is required for SEE and existing zero-allocation hot paths. New policy/diagnostic plumbing must not allocate per recursive node.

Reference artifacts are updated only by an intentional reviewed commit that preserves old and new evidence. Faster timing never permits checksum, node-accounting, or search-result corruption.

---

## 21. Robustness requirements

The program extends permanent robustness coverage with candidate-specific targets:

- fuzz SEE input/move-state combinations;
- fuzz policy parsing and checksums;
- fuzz legal-PV replay under candidate search;
- Miri for bounded SEE and new reversible transitions;
- ASan/LSan for long candidate searches and repeated engine lifecycles;
- TSan for cancellation and adapter interaction;
- minimized permanent regressions for every discovered bug.

No fuzz crash may be dismissed as unreachable without a permanent proof or input-boundary restriction.

---

## 22. CI and workflow policy

### 22.1 Push CI

Every implementation push must retain:

- rustfmt;
- locked metadata/check;
- strict Clippy;
- all-target/all-feature tests;
- release perft depth four;
- differential oracle;
- rustdoc;
- debug/release builds;
- UCI smoke;
- Task 26, Task 27, post-port, and v0.2 audits;
- native ARM64 build;
- applicable Android, robustness, and performance workflows.

### 22.2 Strength workflows

Small deterministic smoke strength runs may execute on push if bounded. Development and production matches should be manual or scheduled because of runtime.

Production reports must be preserved as artifacts and, when accepted for activation, deliberately promoted into versioned repository evidence. Workflows must never modify source defaults.

### 22.3 Exact-SHA rule

A task closes only with exact implementation SHA, commands, run/job IDs, artifact IDs where applicable, and results. Documentation-only closure commits must map explicitly to an unchanged validated implementation tree.

---

## 23. Candidate disposition and activation

Every candidate report records one of:

- `rejected_correctness`;
- `rejected_performance`;
- `rejected_unfinished_rate`;
- `rejected_strength`;
- `deferred_insufficient_evidence`;
- `accepted_for_activation`.

`accepted_for_activation` still serializes `activated=false`.

Activation requires a separate commit that:

- changes the authoritative built-in search policy and/or weights;
- updates engine identity and policy checksum;
- updates documentation and reproducibility fixtures;
- runs full correctness, Android, robustness, performance, and production strength validation;
- proves rollback to the prior authoritative policy remains possible.

The package/UCI version may become `0.2.0` only after this gate passes.

---

## 24. Release acceptance criteria

A successful v0.2 release requires all of the following:

- all v0.1 correctness and integration gates remain green;
- every v0.2 task has an explicit evidence-backed disposition;
- no unresolved P0/P1 correctness issue exists;
- no temporary helper workflow or script remains;
- at least one candidate has `accepted_for_activation` production evidence;
- the activation commit is separate from the acceptance report;
- the activated candidate passes production strength validation against the prior authoritative baseline;
- exact fixed-node and clock-based evidence is preserved;
- x86-64, native ARM64, Android/JNI, fuzz, Miri, sanitizer, leak, and TSan gates pass as applicable;
- performance references are intentionally updated or proven unchanged;
- public API/ABI changes are additive and versioned;
- README and final report identify the exact authoritative policy, weights, and version;
- no experimental feature, tablebase, book, or data dependency is implicitly discovered;
- no quiet fallback or downgraded validation exists.

---

## 25. Initial execution order

The recommended order is:

1. TODO authority cleanup and v0.2 program audit.
2. Exact v0.1 baseline capture.
3. General engine-variant identity and validation report.
4. Search diagnostics and benchmark extensions.
5. Correct allocation-free SEE with an independent oracle.
6. SEE capture-ordering candidate.
7. SEE/quiescence pruning candidate.
8. PVS candidate.
9. LMR candidate.
10. Optional null-move and frontier-pruning candidates, one at a time.
11. Fresh profiling and measured hot-path decisions.
12. Optional explicit Syzygy integration.
13. Production candidate selection and 200-pair validation.
14. Separate activation commit and v0.2 release signoff.

This order is intentional: establish evidence first, improve tactical ordering before pruning, introduce low-risk exact re-search techniques before aggressive reductions, and delay major architecture changes until profiles justify them.
