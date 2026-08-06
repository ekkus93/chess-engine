# Rust Chess Engine v0.2 S2-11 Profiling and Hot-Path Decisions

**Status:** Complete
**Date:** 2026-08-06
**Baseline source SHA:** `b20d34b3fc6210f0eff7a2124168e6d5e084f36a`
**Portable candidate SHA:** `507a7536e9312b607c091fd873d29396c1b578d7`
**Accepted implementation SHA:** `392342c3122c54c47cf485d8bb36c8f5a8c5a762`
**Final validation witness SHA:** `6f5472de19e2b784d1f965815bb5ee19d09efa43`
**Production integration:** active, behaviorally equivalent

## Decision summary

Fresh Callgrind and seven-sample timing evidence was captured on x86-64 and native ARM64. Direct legal generation is deferred pending dedicated legality-probe instrumentation. Incremental evaluation is deferred because evaluation consumed only about `4.79%` of x86-64 and `3.27%` of ARM64 search instructions. TT replacement/packing is rejected as not hot, custom allocation is rejected because measured hot paths remain zero-allocation, and move-list/layout work is deferred to an isolated future candidate.

Sliding attacks were the only justified implementation target. A portable ray-table candidate improved the microbenchmark on both architectures but regressed representative ARM64 legal-generation, perft, search, and FFI workloads by roughly `2%` to `6.4%`; it was rejected. The accepted candidate uses compile-time architecture dispatch: x86-64 uses precomputed rays and nearest-blocker bit scans, while non-x86 targets preserve the original step-walk. There is no runtime CPU detection, magic-bitboard dependency, PEXT dependency, or silent fallback.

## Correctness contract

The permanent exhaustive oracle test compares rook and bishop attacks for every source square and every relevant blocker subset against the independent step-walk oracle. Candidate and baseline retain identical attack sets, perft results, fixed-node search diagnostics, semantic checksums, and allocation counts. The exact validation workloads remained `4,085,603` perft nodes and `250,000` main nodes / `242,711` qnodes / depth `4` for search.

Because the accepted change is behaviorally equivalent, no chess-strength match was run. A game result would measure noise rather than a semantic engine variant.

## Performance disposition

The accepted dispatch produced the following matched median results:

- x86-64 sliding sweep ratio `0.550814` (`44.9%` faster);
- x86-64 representative search ratios `0.938395` and `0.951872` (`6.2%` and `4.8%` faster);
- x86-64 representative perft ratios from `0.788024` to `0.934694` (`21.2%` to `6.5%` faster);
- ARM64 representative ratios remained approximately parity, from `0.990773` to `1.001534`.

Raw identifiers and digests are preserved in `benchmarks/s2-11/artifact-manifest.tsv`; compact profile and matched-comparison summaries are preserved beside it. Existing performance references and budgets were not overwritten or automatically updated.

## Reconsideration gates

Direct legal generation requires isolated instrumentation proving which legality probes are avoidable, followed by exhaustive move-set equivalence, perft, differential, property, fuzz, and restoration evidence. Incremental evaluation requires a materially larger measured share and exact full-recomputation parity after every make/unmake path. Move-list/layout work requires an isolated candidate with allocation, cache/copy, correctness, and architecture-specific evidence. Magic, PEXT, TT packing, and custom allocator work remain prohibited without new profile evidence.
