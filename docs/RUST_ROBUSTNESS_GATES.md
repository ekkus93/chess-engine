# Rust robustness gates

## Scope

Task 23 combines deterministic property tests, mutation fuzzing, runtime analysis, and permanent failure preservation. Production parsers and state transitions are called directly; no parallel test-only parser or move executor is introduced.

## Fuzz workspace

The independent `fuzz/` workspace keeps nightly-only `libFuzzer` tooling out of the production Cargo workspace. `fuzz/src/lib.rs` contains reusable entrypoints that are also exercised by stable tests. Thin targets under `fuzz/fuzz_targets/` cover:

- strict FEN parsing and canonical serialization;
- UCI move syntax parsing and formatting;
- bounded legal sequences followed by exact reverse unmake;
- game-owned history, repetition, draw, and reverse transitions;
- named evaluation-weight artifact parsing;
- indexed opening-book parsing and checksums;
- C ABI valid-pointer buffers, opaque handles, stale handles, and stale allocation records.

Every successful parser result is reserialized and reparsed. Every state transition checks internal invariants and incremental/full Zobrist equality where applicable. Fuzz functions may panic only to report an engine invariant failure; malformed input is an expected typed rejection.

## Continuous smoke budget

The permanent `Robustness` workflow:

1. verifies the independent lockfile;
2. runs formatting, strict Clippy, stable library tests, and committed corpus replay;
3. executes every libFuzzer target for a bounded fixed run count;
4. runs the dedicated core subset under Miri;
5. runs AddressSanitizer with LeakSanitizer over C ABI lifecycle tests;
6. runs ThreadSanitizer over the concurrent cancellation lifecycle.

The CI smoke budget is deliberately bounded. Longer local or scheduled campaigns may increase run counts without changing target semantics.

## Runtime-analysis support boundary

Miri is the authoritative undefined-behavior analysis for the portable core subset. Rust nightly does not expose a general `undefined` sanitizer mode comparable to Clang UBSan for this workspace, so Task 23 records that mode as unsupported rather than claiming a fabricated pass. AddressSanitizer/LeakSanitizer cover allocation, handle, and buffer lifecycle code. ThreadSanitizer is warranted because the C ABI exposes cancellation across threads and owns synchronized registries.

The Android and host-JVM workflows remain the authoritative JNI lifecycle and packaging gates. The JNI bridge delegates to the same safe engine ownership model; native C ABI registry allocations receive the explicit leak-analysis gate.

## Failure preservation

Seed inputs live under `fuzz/corpus/<target>/`. Raw crash outputs under `fuzz/artifacts/` are transient. Every discovered crash, invariant mismatch, sanitizer report, or differential mismatch must be minimized and committed under `fuzz/regressions/<target>/`, then replayed by a named stable regression test before the implementation is corrected. The minimized input remains permanently after the fix.
