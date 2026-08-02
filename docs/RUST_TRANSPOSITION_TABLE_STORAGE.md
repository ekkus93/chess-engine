# Rust Transposition-Table Storage Contract

## Scope

This document defines Task 15.2 only: fixed-capacity storage, cluster layout, allocation behavior, clearing, and generation advancement.

It does not define mate-score normalization, probe cutoffs, repetition-sensitive reuse, replacement preference, diagnostics, or search integration. Those remain Tasks 15.3 through 15.6.

## Fixed memory budget

`TranspositionTable::new(mebibytes)` accepts a size in MiB, where one MiB is 1,048,576 bytes.

The requested byte budget is divided by the size of one complete cluster. Any remainder smaller than a cluster is intentionally unused. The resulting cluster count and entry capacity never grow after construction.

The table uses one `Vec<TranspositionCluster>` reservation. The vector is private and no public API can reserve, push, or append storage. There is no `HashMap`, per-node allocation, or unbounded fallback.

## Cluster layout

Each cluster contains exactly four optional `TranspositionEntry` slots.

The complete 64-bit verification key selects a cluster deterministically by modulo reduction over the fixed cluster count. Keys that collide at the cluster index remain distinguishable through the complete verification key stored in every occupied entry.

Task 15.5 will define which of the four slots is replaced. Task 15.2 deliberately provides no production store operation.

## Allocation failures

Construction is fail-loud and returns `TranspositionTableAllocationError`.

The error categories are:

- zero-MiB configuration;
- MiB-to-byte arithmetic overflow;
- a byte budget too small for one complete cluster;
- failure to reserve the complete cluster array.

The implementation never retries with a smaller table and never switches to a different storage structure. Callers must decide explicitly whether to report the failure, choose a different configured size, or run without a transposition table.

## Clear operation

`clear()` marks every slot empty in place.

It preserves:

- the vector allocation;
- cluster count;
- entry capacity;
- configured MiB budget;
- current generation.

This operation performs no allocation.

## Generation operation

`advance_generation()` increments the one-byte current generation with defined wrapping arithmetic.

Existing entries are retained. This allows Task 15.5 to compare entry generations when implementing age-aware replacement. Generation advancement performs no allocation and does not change table capacity.

## Validation requirements

Task 15.2 tests prove:

- zero and overflowing sizes fail with typed errors;
- a MiB budget rounds down only to complete clusters;
- every cluster contains exactly four slots;
- cluster indexing is deterministic and collision behavior is explicit;
- clearing empties all slots without reallocating or changing generation;
- generation advancement wraps deterministically without clearing entries.
