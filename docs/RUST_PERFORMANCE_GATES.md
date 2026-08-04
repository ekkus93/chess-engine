# Rust Performance Gates

## Purpose

Task 24 measures and protects engine performance without making correctness depend on wall-clock timing. Every benchmark uses the production Rust APIs and release builds. Exact perft, differential, property, fuzz, sanitizer, Android, and lifecycle gates remain independent and authoritative.

## Linux benchmark suite

`cargo run --locked --release -p chess-tools --bin performance -- baseline 7 1`

The suite records tab-separated medians, minima, maxima, allocation counts, and deterministic checksums for:

- leaper and sliding attacks;
- legal move generation;
- make/unmake;
- full and incremental Zobrist hashing;
- evaluation;
- three exact perft positions;
- two fixed-node searches;
- transposition-table store and probe;
- cancellation response;
- C ABI legal-move and fixed-node search calls.

Seven samples are used for committed/reference measurements. The median is the comparison statistic; minimum and maximum values expose runner variance. Operations are repeated inside each sample so timer overhead is not the measured workload.

## Allocation contract

`cargo run --locked --release -p chess-tools --bin performance -- allocation-audit`

The following production hot paths must perform zero allocations after fixture construction and warm-up:

- leaper and sliding attacks;
- legal move generation;
- make/unmake;
- full and incremental hashing;
- normal evaluation;
- transposition-table store and probe.

Fixed-node search and adapter calls report allocations but are not declared allocation-free because result construction and adapter ownership are explicit parts of those APIs.

## Architecture audit

`scripts/task_24_performance_audit.py` rejects:

- `Position::clone` in production recursive-search bodies;
- FEN or `String` position-key construction in recursive search;
- trace or allocation-constructor calls from normal evaluation.

This source audit complements the runtime allocation audit. It does not replace tests or profiling.

## Profiling

The `Performance` workflow runs Callgrind for release Kiwipete perft and a deterministic 250,000-node tactical search on manual and weekly scheduled executions. Profiles are retained as workflow artifacts. Optimizations are accepted only when a measured profile identifies the affected path and exact correctness gates remain green.

## Regression policy

Reference platform: GitHub-hosted `ubuntu-24.04`, x86-64, stable Rust from `rust-toolchain.toml`, release profile, one benchmark process, seven samples.

Wall-clock measurements on shared hosted runners are noisy. A hard comparison may therefore use only committed rows with sufficiently long samples and must require both a material median regression and corroborating distribution evidence. Cancellation latency and Android emulator timings remain bounded diagnostics rather than sub-millisecond hard gates. Correctness gates never receive a timing tolerance.

## Android evidence

The API-35 instrumentation suite records:

- fixed-node search nodes per second;
- native heap deltas for small and larger transposition-table budgets;
- cancellation latency;
- legal-move JNI round-trip latency;
- repeated create/search/cancel/destroy stability;
- delegation of native search away from the main thread.

Android emulator measurements are retained as evidence and guarded by broad failure bounds. They are not compared directly with x86-64 Linux reference values.
