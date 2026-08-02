# Rust transposition-table insertion and replacement contract

Task 15.5 adds deterministic stores to the fixed four-entry collision clusters.
It does not activate the table in production search and does not add counters or
benchmarks.

## Store order

For a complete verification key, `TranspositionTable::store` selects exactly one
cluster and applies these rules in order:

1. A complete-key match is updated in its existing slot. The latest same-key
   observation is authoritative even when its depth is lower, and no duplicate
   same-key slot is created.
2. Without a key match, the lowest-index empty slot is used.
3. In a full different-key collision, the shallowest entry is selected.
4. Equal depths select the greatest modulo-256 generation age, calculated as
   `current_generation.wrapping_sub(stored_generation)`.
5. Equal depth and age select the lowest slot index.

The policy is therefore depth-preferred, age-aware, and reproducible across
runs. Generation arithmetic is deliberately wrapping because table generations
are one byte.

## Generation authority

The table's current generation replaces the generation carried by the incoming
entry. Callers cannot insert an entry that appears fresher or older than the
current table lifecycle state.

## Observable result

Every store returns the cluster index, slot index, and one of:

- `UpdatedSameKey`, including the prior entry;
- `InsertedEmpty`;
- `ReplacedCollision`, including the evicted entry.

This makes collision behavior directly testable without exposing mutable table
storage.

## Deferred work

Task 15.6 owns probe/store counters, replacement statistics, hash-full sampling,
and microbenchmarks. Production alpha-beta integration and proof that the table
is measurably useful remain part of the overall Task 15 gate.
