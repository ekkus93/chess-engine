# Rust transposition-table probe semantics

Task 15.4 defines a storage-only probe boundary. Production alpha-beta search is not yet wired to the table, and replacement policy remains Task 15.5.

## Complete-key verification

`TranspositionTable::probe` selects one four-entry cluster from the complete 64-bit Zobrist key, then accepts only an entry whose stored verification key matches all 64 bits. An index collision is a miss, not a partial hit.

## Depth and bound rules

A verified best move is returned as an ordering hint regardless of stored depth. Score reuse additionally requires `stored_depth >= required_depth`.

After denormalizing the stored score at the current probe ply:

- `Exact` returns the score directly.
- `Lower` returns a fail-high cutoff only when `score >= beta`.
- `Upper` returns a fail-low cutoff only when `score <= alpha`.
- A bound that does not cross its window edge contributes no score, while its verified best move remains available.

The request rejects `alpha >= beta` rather than assigning undefined meaning to an invalid window.

## Mate-distance safety

Every reusable score passes through `TranspositionScore::denormalize(current_ply)` before comparison or return. Conversion failures remain typed `TranspositionProbeError::ScoreConversion` errors; probes never clamp or substitute a score.

## Repetition-sensitive nodes

A Zobrist position key does not encode the path used to reach the position. `TranspositionScoreReuse::SuppressedForRepetition` therefore disables every cached score for a node whose repetition history may affect its value. The verified best move remains an ordering hint only; it cannot terminate search or bypass legal move validation.

The search integration in a later task must choose this conservative mode before probing any repetition-sensitive node.

## Deferred work

Task 15.4 does not define insertion or replacement. Tests install fixtures directly into private clusters. Task 15.5 will provide deterministic same-key updates and collision replacement, and Task 15.6 will add counters, hash-full estimation, and benchmarks.
