# Rust Chess Engine v0.2 — S2-14 SEE + LMR Preflight Rejection

**Status:** Complete — rejected before production strength
**Candidate:** S2-5 SEE capture ordering + S2-8 verified Late Move Reductions
**Candidate source SHA:** `69c653d70570408908964444419dd871f3517716`
**Workflow run:** `31143553002`
**Activation:** `false`
**Disposition:** `rejected_performance_preflight`

## Why this combination was tried

S2-5 explicitly retained SEE capture ordering only for later combination experiments. S2-8 retained its bounded, verified LMR implementation inactive after standalone evaluation. The combination was therefore a legitimate S2-14 preselection experiment: both components already had isolated correctness evidence, neither changed evaluation weights or public adapters, and the combined policy could be given an exact checksummed identity.

No PVS, null-move pruning, quiescence pruning, delta pruning, futility pruning, razoring, late quiet-move pruning, opening book, or tablebase behavior was included.

## Frozen preflight rule

Before measurement, `.github/workflows/s2-14-candidate-preflight.yml` fixed the maximum candidate/baseline seven-sample median-time ratio at `1.05` independently on x86-64 and native ARM64. Production strength matches were not allowed to start if this performance preflight failed.

The threshold is not being relaxed after observing the measurements.

## Correctness and reproducibility results

Both architecture jobs passed every gate before the performance decision:

- frozen candidate-policy audit;
- formatting and strict Clippy;
- complete `chess-search` all-target/all-feature tests;
- S2-14 candidate-tool and production-tool tests;
- release builds;
- deterministic evidence generation;
- x86-64 byte-for-byte repeated-evidence comparison;
- complete-variant smoke with `activated=false`;
- production opening-suite uniqueness/provenance checks;
- existing zero-allocation hot-path audit.

The deterministic workload recorded candidate LMR reductions / reduced fail-highs / verification searches as `101 / 38 / 38`, so every reduced alpha raise remained verified. Candidate semantic checksum was `ed86c8ce80f84036` on both measured architectures.

The generated production opening suite contained at least 1,000 unique color-swappable opening lines. The x86-64 normalized suite SHA-256 was `6c3ff4cc9837bc66dd517d4a7c60d56e71a9b3a4e1fb1aabd904de81dad4e9b7`.

## Performance decision

### Linux x86-64

Job `92758276545`:

- baseline median: `201084381 ns`;
- candidate median: `212002652 ns`;
- candidate/baseline ratio: `1.054297`;
- frozen maximum: `1.050000`;
- main nodes: `40000 / 40000`;
- qnodes: `35620 / 35587`;
- selective depth: `22 / 26`;
- beta cutoffs: `3265 / 3485`;
- first-move cutoffs: `2715 / 2959`;
- maximum allocations: `42 / 44`;
- maximum allocated bytes: `30448 / 30466`.

The candidate exceeded the predeclared performance ceiling and failed closed.

### Linux ARM64

Job `92758276606`:

- baseline median: `175093334 ns`;
- candidate median: `184737621 ns`;
- candidate/baseline ratio: `1.055081`;
- frozen maximum: `1.050000`;
- semantic workload/counters matched x86-64;
- maximum allocations: `42 / 44`;
- maximum allocated bytes: `30448 / 30466`.

The candidate independently exceeded the same predeclared ceiling and failed closed.

## Strength disposition

No production fixed-node or clock match was run. That is intentional: the predeclared S2-14 staging rule prohibited spending production-strength evidence on a candidate that had already failed the architecture-specific performance gate.

The one-pair smoke control returned `rejected_strength` with `activated=false`; smoke carries no production activation authority and is not reinterpreted as a production result.

## Final disposition

SEE + LMR is rejected as the S2-14 production candidate. The rejection is based on the frozen performance rule, not on a correctness defect and not on manual judgment. Production v0.1 defaults remain authoritative and unchanged.

S2-14 candidate selection must choose a different already-evaluated candidate or evidence-backed combination. This rejected preflight must not be used to justify activation or a relaxed performance threshold.
