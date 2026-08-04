# Rust Transposition-Table Entry Design

**Task:** 15.1  
**Branch:** `master`  
**Scope:** entry payload only; storage, probing, replacement, and search integration remain later Task 15 work

## Contract

Each transposition-table entry contains exactly the information required by the Task 15 specification:

1. **Verification key:** the complete 64-bit position Zobrist key. Bucket selection may eventually use only part of the key, but an entry match must verify the full stored key.
2. **Depth:** the searched depth in plies as `u16`.
3. **Bound:** one explicit `TranspositionBound` value:
   - `Exact` for a complete minimax result;
   - `Lower` for a fail-high lower bound;
   - `Upper` for a fail-low upper bound.
4. **Normalized score:** `TranspositionScore`, a distinct wrapper around `Score`. Task 15.3 provides the root-ply conversion rules for mate scores. The wrapper prevents root-relative search scores from being confused with position-relative stored scores once probes are enabled.
5. **Best move:** `Option<Move>`, retaining the engine's compact semantic move identity without legal-token or position ownership.
6. **Generation:** a one-byte generation value for later age-aware replacement.

The implementation is `crates/chess-search/src/transposition.rs` and the public value types are re-exported by `chess-search`.

## Bound semantics

The entry design records semantics but does not yet perform cutoffs:

- `Exact` may eventually satisfy a sufficiently deep probe directly.
- `Lower` may eventually cut off when it reaches or exceeds beta.
- `Upper` may eventually cut off when it reaches or falls below alpha.

Depth sufficiency, repetition-sensitive reuse, and cutoff behavior belong to Task 15.4. No production search path reads or writes entries during Task 15.1.

## Score boundary

`TranspositionScore::normalize(score, ply)` is the public storage boundary. It converts root-relative winning and losing mate scores into position-relative values while preserving static centipawn scores exactly. `TranspositionScore::denormalize(ply)` performs the inverse conversion for a future probe.

The unchecked `from_normalized` constructor is crate-private. Public callers therefore cannot bypass the tested conversion contract. Conversion failures are typed and fail loudly when the ply is unsupported or normalization would leave the score domain.

## Layout and portability

`TranspositionEntry` uses a predictable `repr(C)` field layout and remains a copyable value type. Tests require:

- a one-byte bound tag;
- no storage overhead for `TranspositionScore` relative to `Score`;
- a total entry footprint no larger than 24 bytes on supported targets;
- complete 64-bit key retention;
- round-trip preservation of all six required fields;
- support for every bound and for entries without a best move.

Task 15.2 chose the fixed-memory bucket and cluster shape using this measured entry footprint. Task 15.1 itself introduced no heap table, map, allocation policy, empty-slot encoding, or replacement policy.

## Explicit exclusions

Task 15.1 does not:

- allocate a transposition table;
- index buckets or resolve collisions;
- normalize or denormalize mate scores;
- probe or store from alpha-beta or quiescence search;
- perform exact, lower-bound, or upper-bound cutoffs;
- activate the move-ordering TT hook;
- define age comparison or replacement preference;
- add diagnostics or benchmarks.

Those remain Tasks 15.2 through 15.6.