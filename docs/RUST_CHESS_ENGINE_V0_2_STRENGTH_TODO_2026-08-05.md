# Rust Chess Engine v0.2 Strength Program TODO

**Status:** In progress
**Date:** 2026-08-05
**Branch:** `master`
**Specification:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_SPEC_2026-08-05.md`
**Completed v0.1 tracker:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`
**Completed v0.1 report:** `docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md`
**Completed post-port review:** `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md`
**Planning baseline:** `51cb4fa1b281bd1a6a7d7af20ff3f4a8d99a4e51`
**S2-0 engine baseline:** `1e28defb8835119881f2b03ea60dc5589bec01be`
**S2-0 baseline record:** `docs/RUST_CHESS_ENGINE_V0_2_BASELINE_2026-08-05.md`

## S2-0 implementation record

- Exact engine/search baseline SHA: `1e28defb8835119881f2b03ea60dc5589bec01be`.
- Baseline documentation commit: `ff83eb506d28c039292189dbf5bc69a1cdddfd78`.
- Rust CI baseline: run `30986317659`; jobs `92241821565` and `92241821561`; success.
- Performance baseline: run `30986317662`; jobs `92241817180` and `92241817103`; artifacts `8922221747` and `8922217103`; success.
- Strength status: no exact-head run was expected because the workflow is scheduled/manual and push-path-limited; latest 200-pair/400-game control run `30960468240` succeeded with `rejected_strength` and `activated=false`.
- Authority state: v0.2 TODO active; v0.1 tracker/definitions completed authority; post-port TODO historical; every top-level TODO-named document classified and unclassified additions fail the permanent authority audit.
- Search inventory: full-window fail-soft alpha-beta, tactical quiescence, aspiration recovery, bounded TT, MVV-LVA/killer/history ordering, request-local limits/cancellation, and one optional bounded check extension. SEE, PVS, LMR, null move, futility, razoring, late-move pruning, tablebases, NNUE, and parallel search are absent from production code.
- No labelled open P0 or P1 issue was found.
- No engine semantics, defaults, weights, adapters, ABI/JNI contracts, or performance references changed in S2-0.
- Exact validation of the permanent S2-0 documentation head is pending before S2-1 may start.

## Status rules

- `[x]` means complete with implementation, documentation, and exact evidence.
- `[ ]` means incomplete, unverified, blocked, deferred, rejected without evidence, or not started.
- A candidate task may close as accepted, rejected, revised, or deferred, but its disposition must be explicit and evidence-backed.
- An implemented or accepted candidate remains inactive until a separate activation task completes.
- Documentation-only closure commits must identify the unchanged validated implementation SHA.
- GitHub Actions is the authoritative execution environment when local and CI evidence differ.

## Program guardrails

- Work directly on `master` unless the user explicitly requests a branch.
- Do not reopen the completed Rust port or post-port cleanup.
- Keep the v0.1 search policy and baseline weights authoritative until a separate activation commit passes.
- Do not combine unrelated search heuristics into one candidate.
- Do not accept a candidate because it is faster if fixed-node strength or correctness regresses.
- Do not accept a candidate because it scores better if it violates correctness, robustness, portability, lifecycle, or unfinished-game limits.
- Do not add first-party lint suppression, ignored failure, output filtering, downgraded gate, or silent fallback.
- Do not automatically rewrite performance references, weights, policy defaults, or report decisions.
- Do not expose experimental behavior through UCI, C ABI, JNI, or Android unless explicitly required and versioned.
- Do not implicitly discover books, weights, datasets, tablebases, or configuration.
- Preserve exact make/unmake restoration, mate-score semantics, draw/history behavior, cancellation, and panic containment.
- Every discovered bug receives a source fix and permanent regression before the loop advances.

---

# Program summary

| Task | Scope | Status |
|---:|---|---|
| S2-0 | Authority cleanup and exact baseline inspection | **Implementation complete — validation pending** |
| S2-1 | Versioned search-policy and engine-variant identity | **Not started** |
| S2-2 | Generalized strength-validation infrastructure | **Not started** |
| S2-3 | Baseline strength, diagnostics, and performance capture | **Not started** |
| S2-4 | Correct allocation-free Static Exchange Evaluation | **Not started** |
| S2-5 | SEE capture-ordering candidate | **Not started** |
| S2-6 | Quiescence redesign candidates | **Not started** |
| S2-7 | Principal Variation Search candidate | **Not started** |
| S2-8 | Late Move Reductions candidate | **Not started** |
| S2-9 | Optional null-move pruning decision/candidate | **Not started** |
| S2-10 | Optional frontier and quiet-move pruning candidates | **Not started** |
| S2-11 | Fresh profiling and measured hot-path decisions | **Not started** |
| S2-12 | Optional Syzygy tablebase decision/integration | **Not started** |
| S2-13 | API, UCI, ABI/JNI, Android, CI, and documentation integration | **Not started** |
| S2-14 | Production candidate selection and validation | **Not started** |
| S2-15 | Separate activation and v0.2 release gate | **Not started** |
| S2-16 | Final audit, report, and closure | **Not started** |

---

# Task S2-0: Authority cleanup and exact baseline inspection — VALIDATION PENDING

## S2-0.1 Confirm repository state

- [x] Record the exact current `master` SHA before implementation.
- [x] Confirm the specification and this TODO exist at their required paths.
- [x] Confirm the completed v0.1 tracker remains complete.
- [x] Confirm the completed post-port review TODO remains complete.
- [x] Confirm no unresolved P0/P1 correctness issue exists.
- [x] Record current Rust toolchain, LLVM version, runner images, package versions, ABI/JNI versions, weight identity, and search defaults.

## S2-0.2 Correct TODO authority

- [x] Update `docs/LEGACY_TODO_INDEX.md` so this v0.2 TODO is active.
- [x] Reclassify the completed post-port review TODO as a completed historical record.
- [x] Preserve the v0.1 tracker and definitions as completed authority documents.
- [x] Update `scripts/task_post_port_review_fix_audit.sh` or replace its authority portion with a permanent generalized TODO-authority audit.
- [x] Ensure every top-level `docs/*TODO*.md` file is classified.
- [x] Ensure an unclassified future TODO-named file fails CI.

## S2-0.3 Inventory current search behavior

- [x] Record current alpha-beta, quiescence, move-ordering, TT, iterative-deepening, aspiration, extension, limit, and cancellation behavior.
- [x] Confirm whether PVS, SEE, LMR, null move, futility, razoring, and late-move pruning are absent or partially present.
- [x] Record current search diagnostics and missing counters.
- [x] Record all public/internal entry points that assume the built-in search policy.
- [x] Record all tests that compare reference search, alpha-beta, iterative deepening, and legal PVs.

## S2-0.4 Baseline smoke validation

- [x] Run the permanent v0.1/post-port audits.
- [x] Run formatting, locked check, strict Clippy, and all-target/all-feature tests.
- [x] Run release perft depth four and the differential oracle.
- [x] Record current performance and strength workflow status.
- [x] Do not mark later implementation tasks complete using historical evidence alone.

**S2-0 gate:** Implementation and inventory complete; exact permanent-head validation pending.

---

# Task S2-1: Versioned search-policy and engine-variant identity — NOT STARTED

## S2-1.1 Define policy schema

- [ ] Add a typed search-policy structure in the appropriate search/tooling layer.
- [ ] Assign a versioned schema and semantic identifier.
- [ ] Represent the authoritative v0.1 policy exactly.
- [ ] Represent experimental switches and parameters without ambient globals.
- [ ] Reject unknown, duplicate, missing, out-of-range, or incompatible fields.
- [ ] Produce a deterministic checksum covering schema, identifiers, flags, thresholds, and tables.
- [ ] Ensure malformed policy input fails before search mutation or TT allocation where practical.

## S2-1.2 Preserve defaults

- [ ] Existing production entry points continue to use the v0.1 policy.
- [ ] Existing UCI defaults remain unchanged.
- [ ] Existing safe Rust facade, C ABI, JNI, and Android behavior remain unchanged.
- [ ] No environment variable or implicit file changes policy.
- [ ] Experimental policy injection is initially restricted to controlled Rust tools/tests.

## S2-1.3 Engine-variant identity

- [ ] Define an engine-variant identity binding source SHA, engine version, search policy, evaluation weights, book state, tablebase state, TT configuration, build identity, and exact invocation.
- [ ] Candidate and baseline identities must differ whenever behavior differs.
- [ ] Candidate reports must distinguish search-policy changes from weight changes.
- [ ] Separate TT instances must be used when policy/evaluator identity can affect stored scores or moves.

## S2-1.4 Tests

- [ ] v0.1 policy checksum is stable.
- [ ] Equivalent policy text/order produces one canonical identity.
- [ ] Every semantic change changes the checksum.
- [ ] Corruption, unsupported versions, and unsafe combinations fail loudly.
- [ ] Existing default search results remain unchanged with the explicit v0.1 policy.

**S2-1 gate:** A stable explicit engine/search identity exists without changing production behavior.

---

# Task S2-2: Generalized strength-validation infrastructure — NOT STARTED

## S2-2.1 Generalize candidate scope

- [ ] Extend or complement the existing weight-candidate validator to compare complete engine variants.
- [ ] Preserve the existing weight-only protocol and reports.
- [ ] Define a versioned engine-variant validation report.
- [ ] Record exact baseline and candidate identities and checksums.
- [ ] Record source SHA, toolchain/build identity, command, TT size, limits, opening suite, seeds, draw policy, and maximum ply.

## S2-2.2 Validation tiers

- [ ] Define bounded smoke protocol.
- [ ] Define development paired protocol.
- [ ] Define production protocol with at least 200 independent opening pairs and 400 games.
- [ ] Only production reports may emit `accepted_for_activation`.
- [ ] Every report retains `activated=false`.

## S2-2.3 Correctness pre-gate

- [ ] Run authoritative perft before games.
- [ ] Run forced-mate and longest-survival fixtures.
- [ ] Run candidate-specific tactical/equivalence fixtures.
- [ ] Reject correctness failures before any games.
- [ ] Record `rejected_correctness` distinctly from infrastructure failure.
- [ ] Never let favorable games compensate for a correctness failure.

## S2-2.4 Pairing and statistics

- [ ] Require semantically distinct openings.
- [ ] Reject duplicate canonical opening lines under different names.
- [ ] Play both colors from each opening.
- [ ] Treat pair averages as independent statistical units.
- [ ] Compute mean, sample standard error, and one-sided 95% lower confidence bound with the existing z-value.
- [ ] Require the lower bound to exceed `0.5 + minimum_score_margin` strictly.
- [ ] Track unfinished games separately and enforce the ceiling.
- [ ] Treat tied/inconclusive evidence as rejection.

## S2-2.5 Failure classification

- [ ] Record wins, draws, losses, unfinished games, illegal moves, crashes, time forfeits, and infrastructure failures separately.
- [ ] Do not score an infrastructure failure as a chess result unless a symmetric predeclared protocol explicitly requires it.
- [ ] Atomic report persistence uses caller-selected paths and checksums.
- [ ] Partial/corrupt reports are rejected.

## S2-2.6 Fixed-node and clock protocols

- [ ] Add at least one fixed-node engine-variant protocol.
- [ ] Add at least one clock-based engine-variant protocol.
- [ ] Record why each is used.
- [ ] Ensure both engines receive identical resources/configuration within a protocol.

**S2-2 gate:** Engine variants can be compared reproducibly without weakening the existing fail-closed candidate protocol.

---

# Task S2-3: Baseline strength, diagnostics, and performance capture — NOT STARTED

## S2-3.1 Search diagnostics

- [ ] Add or inventory main nodes and qnodes.
- [ ] Add selective depth and beta-cutoff counters.
- [ ] Add first-move cutoff counter.
- [ ] Preserve existing TT diagnostics.
- [ ] Reserve deterministic counters for PVS, SEE, quiescence pruning, LMR, null move, and frontier pruning.
- [ ] Define counter overflow behavior and tests.
- [ ] Ensure counters do not change search results.
- [ ] Avoid per-node allocation or expensive tracing.

## S2-3.2 Baseline benchmark extensions

- [ ] Record current seven-sample x86-64 and ARM64 distributions.
- [ ] Record legal generation, quiescence, fixed-node search, TT, allocation, and adapter metrics.
- [ ] Add benchmark rows required for future SEE and candidate comparisons without changing current semantic checksums incorrectly.
- [ ] Preserve zero-allocation hot-path requirements.
- [ ] Preserve old reference artifacts before any intentional update.

## S2-3.3 Baseline strength reports

- [ ] Run deterministic smoke self-play of v0.1 against itself to verify protocol symmetry.
- [ ] Run the selected development baseline protocol.
- [ ] Run or schedule a production control proving an identical policy cannot pass the strength margin.
- [ ] Preserve exact opening suite/checksum, seeds, limits, and reports.
- [ ] Verify mean pair score and confidence behavior are symmetric for the control.

## S2-3.4 Baseline tactical corpus

- [ ] Freeze a versioned candidate-search correctness corpus.
- [ ] Include mate in 1, mate in 2+, longest survival, stalemate, repetition, fifty/seventy-five move, promotion races, en-passant tactics, quiet defense, zugzwang-sensitive endings, poisoned captures, and legal-PV replay.
- [ ] Record exact expected values where semantics require parity.
- [ ] Record pass/fail properties where pruning may legitimately change node paths.

**S2-3 gate:** The authoritative v0.1 policy has exact search, performance, tactical, and strength baseline evidence.

---

# Task S2-4: Correct allocation-free Static Exchange Evaluation — NOT STARTED

## S2-4.1 Design contract

- [ ] Define stable piece values used only for exchange accounting.
- [ ] Define SEE sign and side-to-move/capturing-side convention.
- [ ] Define valid move categories.
- [ ] Define typed errors for non-capture misuse and move/position contradiction.
- [ ] Define bounded local storage and arithmetic domain.
- [ ] Document that SEE is an estimate/order primitive, not a legal search replacement.

## S2-4.2 Core implementation

- [ ] Model ordinary captures.
- [ ] Model en-passant occupancy removal correctly.
- [ ] Model promotion value changes for quiet/capture promotions as applicable.
- [ ] Reveal rook/queen x-rays after occupancy removal.
- [ ] Reveal bishop/queen x-rays after occupancy removal.
- [ ] Handle pawn attack direction exactly.
- [ ] Handle king recapture legality conservatively and correctly.
- [ ] Choose least valuable attackers deterministically.
- [ ] Do not mutate the caller's `Position`.
- [ ] Allocate no heap memory.

## S2-4.3 Independent oracle

- [ ] Implement an independent brute-force legal capture-sequence oracle in tests/tools.
- [ ] Keep the oracle structurally different from the production swap algorithm.
- [ ] Compare curated fixtures.
- [ ] Compare deterministic generated legal positions and captures.
- [ ] Preserve any mismatch as a minimized permanent regression.

## S2-4.4 Focused fixtures

- [ ] Undefended winning capture.
- [ ] Equal exchange.
- [ ] Poisoned capture.
- [ ] Multiple attackers/defenders.
- [ ] X-ray rook/queen sequence.
- [ ] X-ray bishop/queen sequence.
- [ ] Pinned or illegal king recapture.
- [ ] En-passant occupancy case.
- [ ] Quiet promotion accounting if supported by the API.
- [ ] Capture-promotion accounting for all four promotion identities.
- [ ] Symmetry and no-mutation properties.

## S2-4.5 Robustness and performance

- [ ] Add SEE fuzz target or corpus replay.
- [ ] Add Miri coverage.
- [ ] Add zero-allocation benchmark row.
- [ ] Add deterministic semantic checksum.
- [ ] Run sanitizers as applicable.

**S2-4 gate:** SEE matches an independent legal capture oracle, is deterministic, fail-loud, non-mutating, and allocation-free.

---

# Task S2-5: SEE capture-ordering candidate — NOT STARTED

## S2-5.1 Candidate policy

- [ ] Add an inactive `see_capture_ordering` policy flag/identity.
- [ ] Define ordering classes for winning, equal, and losing captures.
- [ ] Preserve TT move and promotion precedence according to an explicit policy.
- [ ] Preserve deterministic packed-move tie breaks.
- [ ] Do not prune any move.

## S2-5.2 Search integration

- [ ] Integrate SEE into main-search capture ordering.
- [ ] Integrate SEE into quiescence capture ordering without pruning.
- [ ] Ensure invalid internal SEE input propagates as a typed search error.
- [ ] Add SEE call/classification diagnostics.
- [ ] Avoid repeated SEE computation where a bounded local ordering pass can reuse results safely.

## S2-5.3 Correctness parity

- [ ] Exact root score parity against v0.1 on the deterministic corpus.
- [ ] Best-move parity except documented equal-score tie-order changes.
- [ ] Legal PV replay parity.
- [ ] Mate-distance parity.
- [ ] Position/history/TT restoration on success, cancellation, and error.
- [ ] Reference-search and alpha-beta equivalence gates remain green.

## S2-5.4 Evidence

- [ ] Record nodes, qnodes, cutoffs, first-move cutoffs, SEE calls, elapsed time, and allocations.
- [ ] Run fixed-node development strength comparison.
- [ ] Run clock-based development comparison if performance changes materially.
- [ ] Record disposition: accept for later combination, revise, reject, or defer.
- [ ] Keep production default inactive.

**S2-5 gate:** SEE ordering has exact correctness evidence and an explicit performance/strength disposition without pruning or activation.

---

# Task S2-6: Quiescence redesign candidates — NOT STARTED

## S2-6.1 Preserve current contract

- [ ] Record current quiescence move set, stand-pat rules, in-check behavior, mate/draw resolution, guard, and ordering.
- [ ] Preserve fail-loud guard exhaustion in check.
- [ ] Preserve legal-evasion search in check.
- [ ] Preserve promotion handling and forced recapture fixtures.

## S2-6.2 SEE-pruning candidate

- [ ] Add a separate inactive policy identity.
- [ ] Define the exact losing-capture threshold.
- [ ] Initially exclude checks, promotions, in-check nodes, only legal tactical responses, and mate-sensitive contexts.
- [ ] Count every SEE prune.
- [ ] Propagate SEE/internal errors rather than falling back to unpruned or static evaluation silently.
- [ ] Add poisoned-capture, checking-sacrifice, promotion, en-passant, mate, and quiet-evasion regressions.

## S2-6.3 Delta-pruning candidate

- [ ] Evaluate only after SEE pruning has a stable disposition.
- [ ] Define typed bounded margins and material-gain assumptions.
- [ ] Exclude in-check and mate-score domains.
- [ ] Exclude promotions/checks under the initial policy.
- [ ] Count attempts and prunes.
- [ ] Record independent disposition.

## S2-6.4 Validation

- [ ] Full tactical corpus.
- [ ] Legal PV and exact restoration.
- [ ] Reference/full tactical oracle comparisons where bounded.
- [ ] Node/qnode/time/allocation diagnostics.
- [ ] Fixed-node and clock-based development matches.
- [ ] Production defaults remain inactive.

**S2-6 gate:** Each quiescence semantic change has an isolated identity, targeted correctness evidence, and explicit acceptance/rejection/defer decision.

---

# Task S2-7: Principal Variation Search candidate — NOT STARTED

## S2-7.1 Implementation

- [ ] Add inactive PVS policy identity.
- [ ] Search the first ordered move with the full window.
- [ ] Search later moves with a valid null window.
- [ ] Re-search with the full window whenever required to establish the exact value.
- [ ] Preserve fail-soft score semantics and bound classification.
- [ ] Preserve TT mate normalization and score reuse policy.
- [ ] Preserve deterministic equal-score handling.
- [ ] Add zero-window and re-search diagnostics.

## S2-7.2 Correctness

- [ ] Exact score parity with full-window alpha-beta over the deterministic corpus.
- [ ] Best-move/PV parity subject only to documented equal-score ties.
- [ ] Mate-distance and longest-survival parity.
- [ ] Aspiration fail-high/fail-low recovery remains exact.
- [ ] Cancellation/node/time limit behavior remains exact.
- [ ] No unverified narrow-window result is stored/reported as exact.
- [ ] Position/history/table restoration passes all paths.

## S2-7.3 Evidence

- [ ] Record node/time/cutoff/re-search distributions.
- [ ] Run fixed-node development protocol.
- [ ] Run clock-based development protocol if speed changes materially.
- [ ] Record independent disposition.
- [ ] Keep default inactive.

**S2-7 gate:** PVS is exact relative to full-window alpha-beta and has measured efficiency/strength evidence.

---

# Task S2-8: Late Move Reductions candidate — NOT STARTED

## S2-8.1 Reduction policy

- [ ] Add versioned inactive LMR policy.
- [ ] Define minimum depth, move index, and reduction table.
- [ ] Initial reductions apply only to quiet, non-checking, non-promotion late moves.
- [ ] Protect TT move, first/PV move, captures, promotions, checks, and configured tactical candidates.
- [ ] Bound reductions so effective depth cannot underflow or escape mate domain.

## S2-8.2 Verification

- [ ] A reduced search that raises alpha receives the required full-depth re-search.
- [ ] Count reductions, reduced fail-highs, and full-depth verification searches.
- [ ] Never report a reduced speculative result as exact without verification.
- [ ] Preserve TT bound/store correctness across reduced searches.

## S2-8.3 Targeted correctness

- [ ] Quiet tactical resource fixtures.
- [ ] Quiet defensive resource fixtures.
- [ ] Forced mate and longest-survival fixtures.
- [ ] Promotion races.
- [ ] Low-mobility and zugzwang-sensitive endings.
- [ ] Check extension interaction.
- [ ] Cancellation/limit/restoration paths.

## S2-8.4 Evidence

- [ ] Node, time, selective depth, reduction, and verification diagnostics.
- [ ] Fixed-node development match.
- [ ] Clock-based development match.
- [ ] Independent disposition and parameters recorded.
- [ ] Default remains inactive.

**S2-8 gate:** LMR is bounded, verified, tactically protected, and independently evaluated.

---

# Task S2-9: Optional null-move pruning decision/candidate — NOT STARTED

## S2-9.1 Feasibility decision

- [ ] Decide whether null move fits the core/search architecture without corrupting legal-move APIs or history semantics.
- [ ] Specify side, en-passant, clocks, hash, undo, TT, repetition/history, and consecutive-null behavior before coding.
- [ ] Review zugzwang and fifty-move risks.
- [ ] Record `implement`, `reject`, or `defer` with rationale.

## S2-9.2 Search-only transition if implemented

- [ ] Add dedicated reversible search-only null transition.
- [ ] It cannot be encoded or accepted as a legal `Move`.
- [ ] It cannot enter UCI/game move history.
- [ ] Exact make/unmake and incremental/full-hash parity.
- [ ] Counter overflow and invalid state fail before mutation.

## S2-9.3 Conservative policy if implemented

- [ ] Disable in check.
- [ ] Disable at shallow depth.
- [ ] Disable in low non-pawn material and pawn-only endings.
- [ ] Disable consecutive null moves.
- [ ] Disable in mate-sensitive windows/contexts as specified.
- [ ] Add optional verification search policy.
- [ ] Count attempts, disabled nodes, cutoffs, and verifications.

## S2-9.4 Validation if implemented

- [ ] Zugzwang corpus.
- [ ] Stalemate and repetition corpus.
- [ ] Fifty/seventy-five move boundaries.
- [ ] Mate-distance and longest-survival corpus.
- [ ] Exact restoration and cancellation.
- [ ] Development fixed-node and clock matches.
- [ ] Explicit disposition; default inactive.

**S2-9 gate:** Null move is either rejected/deferred with architectural evidence or implemented conservatively with dedicated correctness and strength evidence.

---

# Task S2-10: Optional frontier and quiet-move pruning candidates — NOT STARTED

## S2-10.1 Futility pruning

- [ ] Decide based on current profile and accepted prior candidates.
- [ ] Add separate versioned policy if implemented.
- [ ] Limit initial use to shallow non-PV, non-check nodes and quiet non-checking moves.
- [ ] Protect checks, promotions, captures, forced evasions, and mate-score windows.
- [ ] Type and bound margins.
- [ ] Count attempts/prunes.
- [ ] Run independent correctness and strength disposition.

## S2-10.2 Razoring

- [ ] Evaluate only after futility evidence.
- [ ] Specify verification behavior.
- [ ] Never convert uncertain frontier values into exact results without proof.
- [ ] Protect tactical and mate-sensitive contexts.
- [ ] Record independent disposition.

## S2-10.3 Late quiet-move pruning

- [ ] Evaluate only after LMR evidence.
- [ ] Protect TT moves, killers, strong-history moves, checks, promotions, and low-mobility nodes.
- [ ] Define move-count/depth thresholds explicitly.
- [ ] Add quiet strategic/defensive regressions.
- [ ] Record independent disposition.

**S2-10 gate:** Every frontier/selectivity candidate is isolated, bounded, and accepted/rejected/deferred independently.

---

# Task S2-11: Fresh profiling and measured hot-path decisions — NOT STARTED

## S2-11.1 Reprofile

- [ ] Run Callgrind/profile-perft after current candidate set.
- [ ] Run profile-search after current candidate set.
- [ ] Capture x86-64 and native ARM64 performance distributions.
- [ ] Capture Android/JNI metrics if integration code or hot paths changed.
- [ ] Preserve old artifacts and exact provenance.

## S2-11.2 Decision: direct legal generation

- [ ] Compare current legal-generation cost and search share.
- [ ] Decide `implement`, `reject`, or `defer`.
- [ ] If implemented, retain old legal generation as a test oracle.
- [ ] Require exhaustive move-set equivalence, perft, differential, property, fuzz, and restoration evidence before activation.
- [ ] Keep fail-loud internal contradiction coverage.

## S2-11.3 Decision: sliding attacks

- [ ] Re-evaluate measured cost.
- [ ] Decide `implement`, `reject`, or `defer`.
- [ ] Reject speculative magic/PEXT/table rewrites without architecture evidence.
- [ ] Preserve exhaustive attack-oracle tests for any change.

## S2-11.4 Decision: incremental evaluation

- [ ] Re-evaluate measured evaluation cost.
- [ ] Decide `implement`, `reject`, or `defer`.
- [ ] If implemented, bind state to undo and prove full recomputation parity after every move category and random sequence.

## S2-11.5 Decision: move-list and TT layout

- [ ] Re-evaluate allocation, cache, and probe/store profile.
- [ ] Decide separately for move-list compaction and TT packing.
- [ ] Preserve semantic checksums, replacement policy, full-key verification, and mate normalization.

## S2-11.6 Reference update policy

- [ ] Do not overwrite references automatically.
- [ ] Preserve before/after distributions.
- [ ] Update references only in an intentional reviewed commit.
- [ ] Record semantic checksum changes and rationale.

**S2-11 gate:** Every optimization area has a fresh profile-backed disposition; implemented changes retain independent correctness proof.

---

# Task S2-12: Optional Syzygy tablebase decision/integration — NOT STARTED

## S2-12.1 Dependency and architecture review

- [ ] Review implementation/library options, licensing, maintenance, platform support, and provenance.
- [ ] Choose adapter-neutral interface/crate placement.
- [ ] Keep filesystem discovery out of `chess-core` and `chess-search` internals.
- [ ] Record `implement`, `reject`, or `defer`.

## S2-12.2 Explicit configuration if implemented

- [ ] Caller supplies enabled state and provider/path.
- [ ] Caller supplies supported piece-count/probe policy.
- [ ] Record implementation/version/data identity.
- [ ] No environment or conventional path discovery.
- [ ] Disabled/not configured is normal and explicit.

## S2-12.3 Failure semantics if implemented

- [ ] Distinguish `not_applicable` from probe/data failure.
- [ ] Missing/corrupt/incompatible configured data fails visible.
- [ ] No silent fallback after a configured probe error.
- [ ] Define adapter-specific error reporting without panic crossing boundaries.

## S2-12.4 Chess semantics if implemented

- [ ] Specify WDL mapping.
- [ ] Specify DTZ and fifty-move interaction.
- [ ] Specify root move selection and tie policy.
- [ ] Specify TT storage/reuse.
- [ ] Specify UCI score/info behavior.
- [ ] Add known-position oracle fixtures and lifecycle tests.

## S2-12.5 Evidence if implemented

- [ ] Unit/integration/oracle tests.
- [ ] Corrupt/missing data tests.
- [ ] Linux, C ABI/JNI, and Android behavior as applicable.
- [ ] Probe performance and allocation evidence.
- [ ] Strength disposition separate from functional correctness.

**S2-12 gate:** Syzygy is explicitly rejected/deferred or integrated without implicit discovery or silent probe fallback.

---

# Task S2-13: API, UCI, ABI/JNI, Android, CI, and documentation integration — NOT STARTED

## S2-13.1 Rust API

- [ ] Preserve existing production APIs and defaults.
- [ ] Add candidate-policy entry points only where required.
- [ ] Version new request/report structures.
- [ ] Keep ownership, cancellation, TT, and error semantics explicit.

## S2-13.2 UCI

- [ ] Do not advertise unsupported experimental options.
- [ ] For accepted configurable features, define exact option names, types, ranges, defaults, and transactional errors.
- [ ] Preserve handshake, `isready`, position, stop, quit, and stale-output behavior.
- [ ] Add subprocess tests for every new supported option.

## S2-13.3 C ABI/JNI/Android

- [ ] Keep old ABI records/functions stable.
- [ ] Use additive versioned functions/records if external policy configuration is required.
- [ ] Preserve opaque handles and all-or-nothing buffer validation.
- [ ] Preserve panic containment and exact error codes/messages.
- [ ] Update JNI/Kotlin declarations and ownership tests together.
- [ ] Preserve Android off-main search, cancellation, repeated lifecycle, dual ABI, and API-35 tests.

## S2-13.4 Permanent audits

- [ ] Add `scripts/task_v0_2_strength_audit.sh` or equivalent.
- [ ] Audit active TODO/spec/report paths.
- [ ] Audit policy/variant/report schema identities.
- [ ] Audit activation boundary and `activated=false` reports.
- [ ] Audit absence of temporary helpers and hidden Python/runtime fallback.
- [ ] Chain v0.1, Task 26, Task 27, and post-port audits.

## S2-13.5 Workflows

- [ ] Wire v0.2 audit into CI.
- [ ] Add bounded strength smoke workflow if practical.
- [ ] Add manual/scheduled development and production variant validation.
- [ ] Preserve artifacts with exact names/SHAs.
- [ ] Ensure workflows cannot edit source/default policy.
- [ ] Preserve x86-64, ARM64, Android, robustness, performance, slow perft, and strength gates.

## S2-13.6 Documentation

- [ ] Search-policy/variant schema.
- [ ] SEE contract and oracle.
- [ ] Quiescence/selectivity decisions.
- [ ] Strength protocol and report schema.
- [ ] Performance/profiling updates.
- [ ] Optional tablebase configuration/failure policy if implemented.
- [ ] Developer commands and artifact ownership.

**S2-13 gate:** Accepted/internal candidate infrastructure is integrated without breaking existing adapters or weakening permanent CI.

---

# Task S2-14: Production candidate selection and validation — NOT STARTED

## S2-14.1 Select candidate

- [ ] Select one exact candidate or evidence-backed combination from individually evaluated components.
- [ ] Record why each included component is present.
- [ ] Record why excluded/deferred components are absent.
- [ ] Freeze search-policy identity, weights, source SHA, toolchain, opening suite, TT, limits, seeds, and commands.
- [ ] Candidate remains inactive.

## S2-14.2 Full correctness matrix

- [ ] Formatting/check/Clippy/all-target tests.
- [ ] Release perft depth four.
- [ ] Differential oracle and seeded playouts.
- [ ] Tactical/mate/draw/zugzwang/promotion corpus.
- [ ] Legal PV replay and exact restoration.
- [ ] Cancellation, limits, UCI, safe facade, C ABI, JNI, Android.
- [ ] Fuzz, Miri, ASan/LSan, TSan.
- [ ] Candidate-specific audits.

## S2-14.3 Performance matrix

- [ ] x86-64 seven-sample baseline/comparator.
- [ ] Native ARM64 seven-sample baseline/comparator.
- [ ] Zero-allocation audit.
- [ ] Search diagnostics and checksum.
- [ ] Android metrics if applicable.
- [ ] Record any intentional reference update separately.

## S2-14.4 Production strength matrix

- [ ] At least 200 independent opening pairs / 400 games.
- [ ] Color-swapped identical openings.
- [ ] Fixed-node production evidence.
- [ ] Clock-based production evidence for release-relevant strength.
- [ ] Unfinished rate within ceiling.
- [ ] Lower confidence bound strictly exceeds required margin.
- [ ] Report checksum and atomic persistence pass.
- [ ] Report decision is explicit.
- [ ] Report records `activated=false`.

## S2-14.5 Disposition

- [ ] If rejected, preserve exact reason and keep v0.1 authoritative.
- [ ] If accepted, record `accepted_for_activation`; do not change defaults in this task.
- [ ] No manual interpretation may override the report rule.

**S2-14 gate:** One frozen candidate receives complete exact-SHA correctness, performance, and production strength evidence while remaining inactive.

---

# Task S2-15: Separate activation and v0.2 release gate — NOT STARTED

## S2-15.1 Preconditions

- [ ] S2-14 report is `accepted_for_activation`.
- [ ] Report is complete, checksummed, and preserved.
- [ ] No unresolved correctness/performance/robustness issue exists.
- [ ] Candidate source/policy/weight identities match the activation inputs exactly.

## S2-15.2 Activation commit

- [ ] Enable the accepted policy and/or weights in a separate reviewed commit.
- [ ] Update authoritative built-in policy checksum.
- [ ] Update authoritative weight identity only if accepted weights are included.
- [ ] Update package/UCI version to `0.2.0` only here.
- [ ] Preserve rollback instructions and prior v0.1 identity.
- [ ] Do not activate any candidate component not present in the accepted report.

## S2-15.3 Post-activation validation

- [ ] Complete Rust CI on exact activation SHA.
- [ ] Android/JNI exact-SHA validation.
- [ ] Robustness exact-SHA validation.
- [ ] Performance exact-SHA validation.
- [ ] Release perft and differential oracle.
- [ ] UCI playable smoke and option behavior.
- [ ] Production strength validation against prior authoritative v0.1 baseline or an explicitly justified unchanged accepted candidate tree.
- [ ] Verify default entry points now use exactly the activated identity.

## S2-15.4 Release documentation

- [ ] README identifies v0.2 authoritative policy and weights.
- [ ] Developer documentation lists exact commands/defaults.
- [ ] Changelog/release report lists accepted, rejected, deferred, and optional capabilities.
- [ ] Public API/ABI versions are accurate.
- [ ] No report is rewritten to claim it activated the engine.

**S2-15 gate:** A separately accepted candidate is explicitly activated and passes the full exact-SHA release matrix as v0.2.

---

# Task S2-16: Final audit, report, and closure — NOT STARTED

## S2-16.1 Final implementation report

- [ ] Create `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_IMPLEMENTATION_REPORT.md`.
- [ ] Record whether v0.2 released or the program completed without promotion.
- [ ] Map every task to implementation/evidence/disposition.
- [ ] Record exact authoritative source, policy, weight, ABI/JNI, report, opening, and tablebase identities.
- [ ] Record all accepted, rejected, revised, and deferred candidates.
- [ ] Record exact workflow run/job/artifact IDs.
- [ ] Record known limitations and next roadmap.

## S2-16.2 Final permanent audit

- [ ] Require complete spec/TODO/report traceability.
- [ ] Require exact validated implementation SHA.
- [ ] Require active TODO authority consistency.
- [ ] Require activation boundary consistency.
- [ ] Reject placeholder SHAs/IDs/decisions.
- [ ] Reject temporary helper workflows/scripts.
- [ ] Reject hidden Python embedding/spawn in production crates.
- [ ] Reject implicit data discovery and silent optional-capability fallback.
- [ ] Chain all inherited permanent audits.

## S2-16.3 Closure consistency

- [ ] Mark tasks complete only after their gates pass.
- [ ] Reclassify this TODO as completed historical authority when the program closes.
- [ ] If no candidate passed, keep package/UCI v0.1 and say so explicitly.
- [ ] If v0.2 released, verify README/report/default identity agree.
- [ ] Verify no unresolved P0/P1 issue exists.
- [ ] Verify no rejected candidate is active.

## S2-16.4 Final gate

- [ ] S2-0 gate.
- [ ] S2-1 gate.
- [ ] S2-2 gate.
- [ ] S2-3 gate.
- [ ] S2-4 gate.
- [ ] S2-5 gate.
- [ ] S2-6 gate.
- [ ] S2-7 gate.
- [ ] S2-8 gate.
- [ ] S2-9 gate.
- [ ] S2-10 gate.
- [ ] S2-11 gate.
- [ ] S2-12 gate.
- [ ] S2-13 gate.
- [ ] S2-14 gate.
- [ ] S2-15 gate, or explicit no-release disposition if no candidate was accepted.
- [ ] S2-16 gate.

**S2-16 gate:** The strength program is completely auditable and either releases an evidence-backed v0.2 or truthfully closes without promotion.

---

## Required evidence template

Use this block for every completed task or candidate:

```text
Task/candidate:
Disposition:
Implementation SHA:
Validation SHA:
Baseline identity/checksum:
Candidate policy identity/checksum:
Candidate weight identity/checksum:
Files changed:
Commands:
Correctness results:
Performance results:
Strength results:
Workflow runs/jobs/artifacts:
Activation state: false/true
Deviations:
Discovered defects and permanent regressions:
Remaining risks:
```

## Initial next action

Complete exact-head validation for **S2-0**. Do not begin S2-1 or implement SEE, PVS, LMR, pruning, or tablebases until the permanent S2-0 documentation head is green and the tracker records that evidence.
