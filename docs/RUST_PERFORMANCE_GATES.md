# Rust Performance Gates

This document defines the permanent Task 24 measurement, profiling, allocation, and regression policy for the Rust chess engine.

Performance never overrides correctness. Exact perft, state restoration, incremental-hash identity, differential validation, fuzzing, Miri, sanitizers, JNI lifecycle tests, and Android instrumentation remain independent mandatory gates.

## Benchmark harness

The release harness is `crates/chess-tools/src/bin/performance.rs`.

Run the complete baseline:

```bash
cargo build --locked --release -p chess-tools --bin performance
target/release/performance baseline 7 1
```

Run the allocation-sensitive subset:

```bash
target/release/performance allocation-audit
```

Run profiling entry points:

```bash
target/release/performance profile-perft
target/release/performance profile-search
```

The baseline covers:

- pawn, knight, and king attack lookup;
- rook, bishop, and queen sliding attacks;
- legal move generation;
- exact make/unmake;
- full Zobrist recomputation and incremental update/restoration;
- full evaluation;
- three representative perft positions;
- two fixed-node searches;
- transposition-table store and probe;
- cancellation request-to-observation latency;
- C ABI legal-move and fixed-node search calls.

Every row records seven samples, operations per sample, median/minimum/maximum nanoseconds per operation, allocation count, allocated bytes, and a deterministic semantic checksum.

## Reference platforms

The committed references are:

- `benchmarks/task24/performance-linux-x86-64.tsv`
- `benchmarks/task24/performance-linux-arm64.tsv`

They were captured from exact head `911c4e5b24ce91fb6482bde75f22c50ceb42b514` in Performance run `30950729328`:

- x86-64 job `92131844100`, artifact `8908980839`;
- native ARM64 job `92131844019`, artifact `8908980591`.

Reference toolchain:

- Rust `1.97.1` (`8bab26f4f68e0e26f0bb7960be334d5b520ea452`);
- LLVM `22.1.6`;
- Ubuntu `24.04.4`.

Reference runner images:

- x86-64: `ubuntu-24.04`, image `20260720.247.2`;
- ARM64: `ubuntu-24.04-arm`, image `20260719.67.1`.

Hosted runners are not fixed-frequency laboratory machines. The references therefore preserve architecture, toolchain, runner image, seven-sample medians, and observed min/max distributions, while the blocking budgets remain deliberately conservative.

Selected reference medians:

| Benchmark | x86-64 | ARM64 |
|---|---:|---:|
| legal move generation | 2,883 ns | 2,033 ns |
| make/unmake | 63 ns | 42 ns |
| evaluation | 860 ns | 571 ns |
| starting-position perft depth 4 | 17.11 ms | 14.41 ms |
| starting fixed-node search | 131.94 ms | 68.31 ms |
| tactical fixed-node search | 166.39 ms | 94.35 ms |
| C ABI legal moves | 3,805 ns | 3,161 ns |
| C ABI fixed-node search | 33.37 ms | 17.51 ms |

## Allocation policy

The allocation audit is fail-closed and requires zero allocations for:

- leaper and sliding attacks;
- legal move generation;
- make/unmake;
- full and incremental hashing;
- normal evaluation;
- transposition-table probe/store.

Search, cancellation, and C ABI rows report their complete measured allocations instead of pretending they are allocation-free. The regression comparator protects those counts and bytes with broad dual-signal budgets.

The source audit `scripts/task_24_performance_audit.py` also rejects:

- `Position::clone()` in recursive search;
- FEN or `String` position-key construction in recursive search;
- trace or allocation constructors in the normal evaluation entry point.

## Regression comparator

The permanent workflow runs:

```bash
python3 -m unittest scripts.tests.test_compare_performance
python3 scripts/compare_performance.py REFERENCE.tsv CURRENT.tsv
```

The comparator fails immediately when:

- a benchmark is missing or added without an intentional reference update;
- operations per sample change;
- the deterministic semantic checksum changes;
- both timing signals exceed the broad hosted-runner budget;
- both allocation count and allocated-byte signals exceed the broad allocation budget.

A timing regression requires both:

1. current median greater than the larger of 150% of the reference median or reference median plus 50 ns; and
2. current minimum greater than the larger of 125% of the reference maximum or reference maximum plus 25 ns.

An allocation regression requires both:

1. current count greater than the larger of 125% of the reference count or reference count plus two; and
2. current bytes greater than the larger of 125% of reference bytes or reference bytes plus 64 KiB.

The dual-signal rule prevents a single noisy sample from blocking the repository. It does not permit semantic drift: benchmark identity, operation count, checksum, and zero-allocation hot-path contracts remain exact.

Reference files are never rewritten automatically. Updating a reference requires an intentional reviewed commit with the new toolchain/platform provenance and preserved before/after evidence.

## Profiling evidence and optimization decisions

Callgrind profiling completed successfully in run `30950461692`, job `92130944944`, artifact `8908923833`.

Release perft:

- 4,085,603 nodes;
- 4,460,080,144 instruction references;
- `Position::legal_moves` accounted for 98.31% inclusive instruction cost.

Fixed-node search:

- 250,000 main nodes and 242,711 quiescence nodes;
- completed depth 4;
- 16,499,832,243 instruction references;
- quiescence accounted for 95.46% inclusive instruction cost.

The measured review produced these decisions:

- direct legal generation with check/pin masks: plausible perft hotspot, but deferred because it is a correctness-sensitive move-generation redesign rather than a safe Task 24 micro-optimization;
- static exchange evaluation or quiescence redesign: plausible search hotspot, but deferred because it changes tactical search semantics and requires its own exact-score and strength evidence;
- faster sliding attacks: not justified by the measured profile;
- incremental evaluation components: not justified by the measured profile;
- compact move-list storage: not justified because the audited move-generation path is already allocation-free;
- transposition-table packing changes: not justified because probe/store costs are already small and the replacement/score contracts are correctness-sensitive.

Task 24 therefore accepts no speculative production optimization. The benchmark correction that prevented leaper constant folding changed measurement validity only, not engine behavior.

## Android measurements

`ChessEngineInstrumentedTest.task24PerformanceEvidenceIsBoundedOnAndroid` measures and prints machine-readable `TASK24_ANDROID_METRIC` records for:

- legal-move JNI average latency;
- fixed-node total nodes, wall time, and nodes per second;
- native heap deltas for 1 MiB and 16 MiB transposition tables;
- explicit cancellation latency.

The same Android suite proves repeated create/search/stop/destroy lifecycle stability and that the sample controller dispatches native search away from the main thread. The permanent Android workflow extracts the metric records from logcat and uploads them as an artifact.

The native ARM64 Performance job provides architecture-specific core and C ABI throughput. The API-35 emulator provides real Android/JNI/lifecycle evidence. This is not represented as physical-device ARM64 Android evidence; device-specific thermal, scheduler, and OEM runtime characterization belongs in release-device testing.

## Permanent workflow

`.github/workflows/performance.yml` runs on every push to `master`, manually, and on a weekly schedule.

Every push runs:

- comparator unit tests;
- source architecture audit;
- release build;
- zero-allocation audit;
- seven-sample baseline;
- architecture-specific comparison on x86-64 and native ARM64;
- artifact preservation.

Manual and scheduled runs additionally preserve Callgrind perft and fixed-node search profiles.
