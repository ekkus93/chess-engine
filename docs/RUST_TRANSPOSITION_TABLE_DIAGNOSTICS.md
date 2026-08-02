# Rust Transposition-Table Diagnostics and Benchmarks

Task 15.6 adds bounded observability to the fixed-capacity transposition table without changing search or replacement semantics.

## Diagnostic snapshot

`TranspositionTable::diagnostics()` returns a copy of `TranspositionTableDiagnostics`. Every counter is a saturating `u64`; overflow stops at `u64::MAX` rather than wrapping or affecting engine behavior.

The snapshot reports:

- valid probes that reached table lookup;
- complete-key hits and derived misses;
- exact scores actually reused;
- lower-bound and upper-bound cutoffs actually reused;
- all stores;
- same-key updates;
- empty-slot insertions;
- different-key collision replacements.

An invalid alpha-beta window fails before lookup and is not counted as a probe. A complete-key match is counted as a hit even when depth, repetition sensitivity, or a non-cutting bound prevents score reuse. Exact and bound counters count only reusable score outcomes.

`TranspositionTable::reset_diagnostics()` clears the snapshot only. It does not clear entries, change generation, resize storage, or alter replacement order.

## Bounded hash-full estimate

`TranspositionTable::hash_full()` returns `TranspositionHashFull` with:

- sampled slot count;
- sampled slots occupied by the current generation;
- occupancy in per mille.

The scan inspects at most `TRANSPOSITION_HASH_FULL_SAMPLE_LIMIT`, currently 1,000, evenly distributed flattened slots. Tables smaller than the limit inspect every slot. Older generations do not count as current hash fullness. Sampling is deterministic for a fixed table state, performs no allocation, and never scans an arbitrarily large table.

## Reproducible microbenchmarks

Run the release-mode benchmark with:

```text
cargo run --locked -p chess-tools --release -- tt-bench ITERATIONS
```

It prints two tab-separated rows:

```text
operation<TAB>iterations<TAB>elapsed_nanos<TAB>checksum
```

The `store` benchmark uses a fixed one-MiB table, deterministic keys, bounded depths, and the production replacement path. The `probe` benchmark preloads a fixed one-MiB table and executes a deterministic three-hit/one-miss pattern through the production probe path. Checksums and fixture behavior are reproducible for a fixed iteration count; wall-clock timing is informational and intentionally is not a cross-machine pass/fail threshold.

## Scope boundary

Task 15.6 does not connect the table to production alpha-beta. Fixed capacity, complete-key verification, mate normalization, repetition-sensitive score suppression, and deterministic replacement remain unchanged. Production integration and a correctness-plus-node-reduction witness belong to the overall Task 15 gate.
