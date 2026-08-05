# Rust Chess Engine v0.2 S2-4 Static Exchange Evaluation

**Status:** Implemented; inactive standalone primitive  
**Task:** S2-4  
**Starting master:** `f5a4217ca55a8b8d469b3e23e727f85706ba9aff`  
**Core implementation:** `cbffe1287f7a0c54eae63de71c18211fd75d9503`

## Contract

`chess_core::static_exchange_evaluation` is a deterministic material-exchange primitive. It evaluates one legal capture or promotion event from the initiating side's perspective. The initiating event is mandatory. Later recaptures alternate by side and may be declined whenever continuation would lose material.

SEE is not a legal-search replacement, a tactical oracle, or a tuned evaluator. Production search does not call it in S2-4.

## Stable identity

- schema: `1`
- policy identifier: `0x5345_4556_414c_3031`
- semantic checksum: `0x0367_2231_0488_6e8e`
- maximum alternating recapture plies: `64`
- piece values: pawn `100`, knight `320`, bishop `330`, rook `500`, queen `900`, king `20000`

These values are exchange-accounting constants and are deliberately independent of `EvaluationWeights`.

## Semantics

- Captures, en passant, quiet promotions, and capture promotions are valid entry categories.
- Ordinary quiet moves, double pawn pushes, and castling fail with `NonExchangeMove`.
- The move must agree with source occupancy, side to move, target occupancy, piece geometry, promotion rank, and king safety.
- En passant removes the actual captured pawn before x-ray attacks are recomputed.
- Rook/queen and bishop/queen x-rays are recomputed from the local occupancy after every exchange.
- Each side selects the least valuable legal attacker. Equal-value attackers use ascending source-square identity.
- Pawn recaptures onto the promotion rank evaluate all four promotion identities independently.
- Pinned attackers and illegal king recaptures are excluded by local king-safety simulation.
- The caller's `Position`, clocks, metadata, and Zobrist identity are never mutated.
- Fixed local bitboards and bounded recursion are used; the hot path performs no heap allocation.

## Failure model

Malformed or contradictory input is typed and fail-loud:

- `NonExchangeMove`
- `MoveStateContradiction`
  - missing source piece
  - wrong side to move
  - invalid target state
  - invalid geometry or promotion state
  - illegal king exposure
- `ExchangeCapacityExceeded`
- `ArithmeticOverflow`

No error is converted into a neutral score or an unvalidated fallback.

## Independent oracle

The test oracle is structurally different from the production local-bitboard algorithm. It:

1. applies the initial legal move with the authoritative `Position` make/unmake path;
2. regenerates complete legal moves after each exchange;
3. filters legal captures to the contested square;
4. chooses the least valuable source piece and stable source-square tie;
5. recursively explores promotion identities;
6. permits each responding side to decline a losing continuation.

Curated x-ray, pin, king, promotion, en-passant, and poisoned-capture fixtures are compared with the oracle. Deterministically generated legal positions and every encountered exchange event are also compared.

## Robustness and performance

- `static_exchange` fuzz target exercises deterministic legal sequences, all legal exchange events, repeated equality, exact roots, invariants, and material bounds.
- The Miri core suite covers deterministic en-passant SEE and exact non-mutation.
- Native AddressSanitizer/LeakSanitizer runs the focused SEE core tests.
- `s2_4_see_benchmark` records a seven-sample `see.exchange` distribution and fails if any tracked allocation occurs.
- The existing Task 24 performance rows and references remain unchanged.

## Activation boundary

S2-4 adds only the standalone SEE primitive and its evidence. Search policy, move ordering, quiescence, UCI, safe Rust facade, C ABI, JNI, Android, evaluation weights, package version, and production defaults remain unchanged. Search integration is reserved for S2-5 or later.
