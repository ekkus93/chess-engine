# Rust Chess Engine v0.2 Strength Program Baseline

**Status:** S2-0 baseline recorded
**Date:** 2026-08-05
**Branch:** `master`
**Baseline SHA:** `1e28defb8835119881f2b03ea60dc5589bec01be`
**Specification:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_SPEC_2026-08-05.md`
**Live TODO:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md`
**Completed v0.1 tracker:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`
**Completed post-port record:** `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md`

---

## 1. Purpose and evidence boundary

This document freezes the exact repository, toolchain, search-policy, test,
performance, and strength-control state that precedes v0.2 implementation.
It is an inventory and evidence record only. It does not implement, activate,
or imply acceptance of SEE, PVS, LMR, pruning, tablebases, new weights, or any
other strength candidate.

Later v0.2 tasks must compare against this baseline or an explicitly superseding
baseline. Historical v0.1 performance or strength evidence may explain context,
but it is not sufficient evidence for accepting a future candidate.

---

## 2. Repository authority and issue state

At the baseline SHA:

- `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md` is the only active
  implementation tracker.
- `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md` and
  `docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md` remain
  completed v0.1 authority records.
- `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md` is a completed
  historical record.
- `docs/LEGACY_TODO_INDEX.md` classifies all 72 top-level TODO-named Markdown
  files: three authority documents, one authority index, and 68 historical
  references.
- `scripts/task_post_port_review_fix_audit.sh` requires the v0.2 spec and TODO,
  checks their reciprocal references, verifies the authority index, and fails
  when a top-level `docs/*TODO*.md` file is unclassified.
- GitHub reported no open issue carrying a `P0` label and no open issue carrying
  a `P1` label. Unlabelled historical workflow/administrative issues are not
  treated as hidden correctness blockers.

The repository's `master` branch is not protected by a GitHub branch-protection
rule. Permanent workflows remain authoritative evidence, but branch protection
is a separate repository-governance decision rather than a search-policy
property.

---

## 3. Versions, toolchain, and platform identity

### 3.1 Workspace and language

- All eight Rust workspace packages are version `0.1.0`.
- Rust edition: `2021`.
- Declared minimum supported Rust version: `1.75`.
- Validation channel: `stable` from `rust-toolchain.toml`.
- Exact baseline validation compiler: `rustc 1.97.1`.
- Rust commit: `8bab26f4f68e0e26f0bb7960be334d5b520ea452`.
- LLVM: `22.1.6`.
- Workspace lint policy:
  - Rust warnings denied;
  - `unsafe_op_in_unsafe_fn` denied;
  - all Clippy lints denied.

### 3.2 Exact hosted-runner identities

x86-64 validation:

- OS: Ubuntu `24.04.4 LTS`;
- runner image: `ubuntu-24.04`;
- runner image version: `20260720.247.2`;
- runner agent: `2.336.0`;
- image provisioner: `20260707.563`.

ARM64 validation:

- OS: Ubuntu `24.04.4 LTS`;
- runner image: `ubuntu-24.04-arm`;
- runner image version: `20260719.67.1`;
- host target: `aarch64-unknown-linux-gnu`;
- runner agent: `2.336.0`;
- image provisioner: `20260707.563`.

### 3.3 Adapter and schema identity

- C ABI version: `1` (`CHESS_ENGINE_ABI_VERSION`).
- JNI package version: `0.1.0` over the versioned C/safe-facade contract.
- Evaluation-weight schema: `1`.
- Evaluation-structure schema: `1`.
- Built-in baseline weight-set identifier: `424153454c494e45`.
- Built-in baseline weight checksum: `d2cca7ae10ec6e34`.
- Canonical weight vector length: `816` signed 16-bit values.
- The baseline weight set remains authoritative; no candidate is active.

---

## 4. Production search defaults

At the baseline SHA there is no general versioned `SearchPolicy` or
`EngineVariant` object. Production entry points implicitly select the built-in
search behavior and `EvaluationWeights::DEFAULT`, except for existing explicit
weighted-search tooling paths.

The default production configuration is:

- fail-soft negamax alpha-beta;
- iterative deepening by completed depth;
- aspiration windows after the first exact iteration, with a complete-window
  retry after fail-low or fail-high;
- one caller-owned bounded clustered transposition table for production
  iterative search;
- convenience alpha-beta entry points allocate a fresh bounded default table;
- default transposition-table size: `1 MiB`;
- UCI Hash range: `1` through `65,536 MiB`;
- check extension: disabled by default;
- opening book: disabled by default and usable only when explicitly supplied;
- built-in baseline weights;
- deterministic move ordering and tie-breaking;
- request-local cooperative cancellation;
- no implicit filesystem, environment, tablebase, weight, or book discovery.

UCI baseline identity is `chess-engine-rust 0.1.0`.

---

## 5. Search implementation inventory

### 5.1 Reference search

`reference.rs` provides deterministic reference negamax and the independent
reference-with-quiescence path used for shallow equivalence and terminal-score
validation. It is a correctness oracle inside the Rust workspace, not the
production high-performance search.

### 5.2 Alpha-beta

`alpha_beta.rs` implements full-window fail-soft negamax alpha-beta with:

- exact history/root validation;
- mate-distance domain checks;
- bounded TT probe/store integration;
- mate-safe TT normalization;
- deterministic best-move selection;
- make/unmake recursion;
- quiescence at the normal depth frontier;
- checked node and qnode accumulation;
- fail-loud cancellation and restoration;
- one optional bounded check extension.

Every ordinary child is searched with the full negated alpha-beta window. There
is no production PVS/null-window child-search policy at this baseline.

### 5.3 Quiescence

`quiescence.rs` implements:

- stand pat only when the side to move is not in check;
- immediate stand-pat beta cutoff;
- all legal evasions while in check;
- captures and every promotion outside check;
- deterministic tactical ordering;
- a maximum tactical-ply guard of `64`;
- fail-loud behavior if the guard is reached while still in check;
- exact history and position restoration on success, cutoff, cancellation, and
  error.

There is no SEE, delta pruning, SEE-negative capture pruning, recapture-only
mode, or other selective tactical filter at this baseline.

### 5.4 Move ordering

`move_ordering.rs` uses fixed-capacity allocation-free ordered storage and ranks:

1. an explicitly supplied TT move;
2. promotion category and promoted piece value;
3. capture category;
4. MVV-LVA-style victim and attacker preference;
5. killer moves for quiet search;
6. a bounded quiet-history table;
7. deterministic packed-move tie-breaking.

The generic TT and previous-PV hook functions return `None`; production
alpha-beta supplies the probed TT move directly. There is no SEE score or
capture-win/equal/loss class.

### 5.5 Transposition table

The production TT is fixed-capacity and clustered. It provides:

- full key verification;
- generation-aware replacement;
- exact/lower/upper bound semantics;
- mate-score normalization by ply;
- safe rejection of unusable repetition-sensitive scores;
- checked probe/store APIs;
- current-generation hash-full sampling;
- probe/store/replacement diagnostics.

### 5.6 Iterative deepening and principal variation

`iterative_deepening.rs` provides:

- exact completed iterations in ascending depth order;
- aspiration attempt diagnostics and complete-window recovery;
- cumulative nodes, qnodes, and selective depth;
- per-iteration TT diagnostics, hash-full, and generation;
- legal TT-derived PV reconstruction;
- progress observation after exact completed iterations;
- preservation of the last completed exact result when a limit or cancellation
  stops later work;
- an explicit deterministic emergency legal-move fallback only when
  cancellation occurs before depth one completes.

The emergency fallback is surfaced in the typed result and adapter output; it
is not a silent strength fallback.

### 5.7 Limits and cancellation

The current limit controller supports:

- maximum completed depth;
- cumulative node budget;
- soft time;
- hard time;
- infinite search until explicit stop;
- request-local stop flags;
- periodic cooperative cancellation checks.

Cancellation is checked at node and child boundaries. Active moves and history
entries are restored before errors propagate.

### 5.8 Check extension

The only selective depth modification in production is a bounded check
extension:

- explicitly enabled by policy/adapter flag;
- disabled by default;
- limited to one extension per search line;
- separately diagnosed and tested;
- not treated as evidence that broader selective search exists.

---

## 6. Candidate-feature presence matrix

| Candidate | Baseline disposition |
|---|---|
| Static Exchange Evaluation | Absent. |
| SEE capture ordering | Absent. |
| SEE-negative quiescence pruning | Absent. |
| Delta pruning | Absent. |
| Principal Variation Search | Absent; PV reconstruction exists but is not PVS. |
| Late Move Reductions | Absent. |
| Null-move pruning | Absent. |
| Futility pruning | Absent. |
| Razoring | Absent. |
| Late-move pruning | Absent. |
| Quiet-move count pruning | Absent. |
| Singular extensions | Absent. |
| Check extension | Present, bounded to one per line, default off. |
| Aspiration windows | Present with exact full-window recovery. |
| TT move ordering | Present through the probed move supplied by alpha-beta. |
| Killer/history ordering | Present for quiet moves. |
| Syzygy/tablebases | Absent. |
| Parallel search / Lazy SMP | Absent. |
| NNUE | Absent. |

A feature is absent unless production search code invokes it. Historical docs,
rejected experiments, or similarly named PV modules do not count as partial
implementation.

---

## 7. Current diagnostics and known gaps

### 7.1 Existing diagnostics

The baseline records:

- total main nodes;
- total quiescence nodes;
- selective depth;
- completed depth;
- best move and legal PV;
- aspiration attempts and fail-low/fail-high/exact outcomes;
- TT probes, hits, usable scores, stores, replacement actions, generations,
  and hash-full;
- check-extension events;
- limit/cancellation termination and explicit fallback kind;
- elapsed time at outward result boundaries.

### 7.2 Diagnostics intentionally missing before S2-1/S2-3

There are no stable counters for:

- total beta cutoffs;
- first-move beta cutoffs;
- capture versus quiet cutoffs;
- SEE calls or SEE result classes;
- quiescence candidates considered/pruned/re-searched;
- PVS null-window searches or re-searches;
- LMR candidates, reductions, and verification re-searches;
- null-move attempts, fail-highs, or verification searches;
- futility, razoring, late-move, or quiet-count pruning;
- branching factor by depth;
- explicit policy or engine-variant identity.

Those gaps are requirements for later v0.2 diagnostics work; they are not filled
with inferred or fabricated values in this baseline.

---

## 8. Entry-point inventory

### 8.1 Public search-core entry points using built-in policy

- `alpha_beta_search`
- `alpha_beta_search_with_cancellation`
- `alpha_beta_search_with_transposition_table`
- `alpha_beta_search_with_cancellation_and_transposition_table`
- `quiescence_search`
- `quiescence_search_with_limit`
- `quiescence_search_with_cancellation`
- `iterative_deepening_search`
- `iterative_deepening_search_with_limits`
- `iterative_deepening_search_with_transposition_table`
- `iterative_deepening_search_with_limits_and_transposition_table`
- `iterative_deepening_search_with_limits_and_transposition_table_and_observer`

The existing weighted iterative entry point changes evaluation weights only; it
does not identify or vary the search policy.

### 8.2 Outward consumers

- Linux UCI worker/session integration;
- safe Rust engine facade;
- C ABI;
- JNI and Android harness;
- self-play;
- candidate validation;
- performance harness;
- tuning/tooling search paths.

S2-1 must preserve existing convenience behavior while introducing explicit
policy/variant identity for experiments. No outward adapter may silently opt in
to an experiment.

---

## 9. Search-correctness and behavior test inventory

The baseline test matrix includes:

- `search_equivalence.rs` — shallow reference/alpha-beta equivalence;
- `search_iterative_deepening.rs` — exact depth progression and final-result
  equivalence;
- `property_search.rs` — legal PV and make/unmake properties;
- `search_terminals.rs` — mate, stalemate, draw, and mate-distance behavior;
- `search_immutability.rs` — root and history restoration;
- `search_quiescence.rs` and `search_quiescence_task_14_4.rs` — tactical
  frontier, in-check behavior, promotions, ordering, and guard behavior;
- `search_check_extension.rs` — bounded extension policy and diagnostics;
- `search_limits.rs` — depth/node/time/infinite limits;
- `search_responsive_cancellation.rs` — bounded cooperative stop response;
- `search_result_api.rs` — unified result semantics;
- `search_transposition.rs` — TT equivalence, reuse, mate normalization,
  replacement, and diagnostics;
- internal alpha-beta, aspiration, PV reconstruction, move-ordering,
  cancellation, and TT unit tests.

Later candidates must add targeted permanent regressions rather than weakening
or replacing this baseline suite.

---

## 10. Exact baseline validation

### 10.1 Rust CI

Exact SHA: `1e28defb8835119881f2b03ea60dc5589bec01be`

- Workflow run: `30986317659` — success.
- Rust workspace quality job: `92241821565` — success.
- Linux ARM64 workspace job: `92241821561` — success.

Passed gates:

- workspace and validation-asset audit;
- Task 25 developer-workflow audits;
- Task 26 v0.1 audit;
- Task 27 full-port audit;
- post-port/TODO-authority audit;
- Task 14.5 exclusion audit;
- Task 19.5 opening-book audit;
- lockfile regeneration check;
- locked workspace metadata;
- `cargo fmt --all -- --check`;
- `cargo check --locked --workspace --all-targets --all-features`;
- `cargo clippy --locked --workspace --all-targets --all-features -- -D warnings`;
- `cargo test --locked --workspace --all-targets --all-features`;
- warning-free rustdoc;
- debug and release workspace builds;
- Linux UCI subprocess smoke;
- native ARM64 debug build, test compilation, and release build.

Workspace result: `380 passed`, `0 failed`, with four deliberately controlled
slow/manual tests ignored by the ordinary all-target run.

### 10.2 Perft and differential oracle

- Explicit release depth-four authoritative perft: passed.
- Starting-position witnesses remained `20`, `20`, `400`, `8,902`, and
  `197,281` for legal moves and depths one through four.
- Differential corpus: `15` positions.
- Child FENs checked: `293`.
- Oracle perft nodes: `272,991`.
- Seeded playouts: `576` plies.
- Seed: `12,648,430` (`0xC0FFEE`).

### 10.3 Exact-head performance workflow

Exact SHA: `1e28defb8835119881f2b03ea60dc5589bec01be`

- Workflow run: `30986317662` — success.
- Linux ARM64 performance job: `92241817103` — success.
- Linux x86-64 performance job: `92241817180` — success.
- Scheduled Callgrind job: correctly skipped on an ordinary push.
- ARM64 artifact: `8922217103`.
- x86-64 artifact: `8922221747`.

Both architecture jobs passed:

- performance-source architecture audit;
- release harness build;
- zero-allocation hot-path audit;
- seven-sample baseline measurement;
- architecture-specific reference-budget comparison;
- artifact preservation.

This is performance status, not candidate-strength evidence.

### 10.4 Strength workflow status

The Strength workflow is intentionally scheduled/manual and runs on push only
when its own workflow definition changes. Therefore it did not run on baseline
SHA `1e28defb8835119881f2b03ea60dc5589bec01be`.

The latest completed control remains:

- run `30960468240` on `8622917fbd5c544363a2b07d9b450cc13d08f564`;
- 200 independent opening pairs / 400 color-balanced games;
- decision `rejected_strength`;
- `activated=false`.

This historical control proves the fail-closed baseline-versus-baseline protocol
rejects a non-improving candidate. It is not fresh evidence for any future
search-policy candidate.

---

## 11. Measured optimization context

The accepted v0.1 Callgrind evidence found:

- legal move generation at `98.31%` inclusive instruction cost in release
  perft;
- quiescence at `95.46%` inclusive instruction cost in the fixed-node search
  profile.

Those figures justify investigating direct legal generation and SEE/quiescence
redesign, but they do not pre-accept either change. Faster sliding attacks,
incremental evaluation, compact move-list storage, and tighter TT packing were
not justified by the v0.1 profile and remain conditional on fresh S2-11
measurement.

---

## 12. S2-0 conclusion

The repository is ready to begin S2-1 without reopening v0.1 signoff:

- authority is unambiguous;
- no labelled P0/P1 issue is open;
- exact correctness and performance baselines are green;
- the current search policy and missing candidate features are recorded;
- current diagnostics and entry points are inventoried;
- no experimental feature or weight is active.

The next permitted implementation task is S2-1: versioned search-policy and
engine-variant identity. SEE, PVS, LMR, pruning, and tablebase implementation
remain prohibited until S2-1, S2-2, and S2-3 establish explicit identity,
validation, and baseline diagnostics.
