# Rust Chess Engine v0.2 — S2-14 Production Candidate Selection

**Status:** Candidate selected; production validation pending
**Task:** S2-14
**Selected candidate:** standalone Principal Variation Search (PVS)
**Activation:** `false`
**Public adapter change:** none

## Selection rule

S2-14 selects one exact, already-evaluated behaviorally distinct candidate and subjects it to a fresh exact-SHA correctness, architecture-specific performance, and production-strength program. Selection does not activate the candidate. The production v0.1 policy remains authoritative unless a later explicit activation task changes source defaults after an `accepted_for_activation` report.

The exact source SHA, target/toolchain identity, invocation, opening suite, TT size, resource protocol, seeds, report checksum, and complete-variant checksums are bound mechanically by the S2-14 preflight and production artifacts. The workflow head SHA is the source identity; no branch name or implicit filesystem state substitutes for it.

## Selected semantic identity

The candidate is the existing S2-7 standalone PVS policy, reused without changing its search semantics:

- search-policy identifier: `5332375056533031`;
- search-policy checksum: `ef730d158002ccfa`;
- baseline search-policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`;
- evaluation-weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`;
- opening book: disabled;
- tablebase: disabled;
- transposition table: 1 MiB per side;
- production fixed-node resource limit: 2,000 nodes per move;
- production clock resource limit: 10 ms per move;
- production maximum game length: 256 plies;
- production candidate remains `activated=false` regardless of report disposition.

The S2-14 production harness rejects any accidental addition of SEE capture ordering, SEE quiescence pruning, delta pruning, LMR, or null-move pruning to the candidate policy.

## Why PVS was selected

S2-7 established exact score/depth/PV correctness, deterministic reproduction, restoration, limit behavior, and native x86-64/ARM64 evidence. Its standalone development matches were statistically insufficient for activation because most games reached the bounded maximum-ply boundary, but the completed-game signal was favorable rather than negative:

- fixed-node development: candidate `2` wins, `0` losses, `14` unfinished;
- clock development: candidate `1` win, `0` losses, `15` unfinished;
- illegal moves, crashes, time forfeits, and infrastructure failures: all zero.

PVS also remained comfortably inside the S2-14 predeclared 5% median-time ceiling in its prior isolated measurements:

- x86-64 candidate/baseline ratio: `1.010052`;
- ARM64 candidate/baseline ratio: `1.014173`.

Those results do not authorize activation. They justify spending the production evidence budget on PVS.

## Why the other candidates were not selected

### SEE capture ordering

S2-5 was retained only for later combination experiments after standalone strength rejection. Its isolated seven-sample median was approximately 5.5% slower on both x86-64 and ARM64, already outside the S2-14 5% preflight ceiling.

### SEE quiescence pruning

S2-6 SEE pruning remained within the 5% timing ceiling but every game in both development protocols reached the explicit maximum-ply boundary. It therefore supplied no completed-game strength signal for S2-14 selection.

### SEE plus delta pruning

S2-6 SEE-plus-delta was independently rejected and measured approximately 8.47% slower on x86-64 and 7.75% slower on ARM64.

### Late Move Reductions

S2-8 LMR was correct and nearly timing-neutral, but its completed development games were symmetric (`2` wins / `2` losses) in both protocols. Its original isolation rule is restored; S2-14 does not silently combine LMR with PVS.

### Null-move pruning and later frontier pruning

S2-9 null-move pruning was rejected. S2-10 futility, razoring, and late quiet-move pruning were deferred/inactive. None is promoted into S2-14.

### Hot-path dispatch and Syzygy

S2-11's accepted x86-64 sliding-attack dispatch is already part of the implementation baseline and is not a behaviorally distinct search candidate. S2-12 Syzygy integration was deferred and remains absent.

## Rejected SEE + LMR preselection experiment

The first S2-14 preselection experiment combined S2-5 SEE capture ordering with S2-8 verified LMR. It passed correctness and reproducibility but failed the predeclared performance ceiling independently on both architectures:

- x86-64 ratio: `1.054297` > `1.05`;
- ARM64 ratio: `1.055081` > `1.05`.

That threshold was not relaxed after measurement. No production match was run for the failed combination. Exact evidence is recorded in `docs/RUST_CHESS_ENGINE_V0_2_S2_14_SEE_LMR_PREFLIGHT_REJECTION_2026-08-06.md`.

The rejected combination policy and its duplicate S2-14 candidate binary were removed from active source. S2-8 LMR again accepts only its isolated policy identity.

## Fresh S2-14 evidence program

The permanent preflight runs on native x86-64 and ARM64 and requires:

- candidate-boundary audit;
- rustfmt and strict Clippy;
- complete `chess-search` tests;
- PVS evidence-tool and S2-14 production-tool tests;
- deterministic repeated evidence;
- exact complete-variant smoke with `activated=false`;
- 1,200 unique deterministic first-party opening lines;
- zero-allocation hot-path gate;
- seven-sample timing distribution on both architectures;
- candidate/baseline median-time ratio `<= 1.05` independently on both architectures.

Only a successful exact-SHA preflight may trigger the production-strength workflow. The production workflow checks out the exact preflight SHA and runs fixed-node and clock protocols separately. Both preserve complete reports and never write source.

## Failure and activation policy

No source default is changed by preflight or production evidence. A correctness failure, infrastructure/game failure, unfinished-rate rejection, or strength rejection remains a rejection. An `accepted_for_activation` production report is evidence for later review only; it does not itself activate PVS.

There is no manual override, threshold relaxation, baseline-search fallback, ignored configuration, or silent reinterpretation of a rejected report.
