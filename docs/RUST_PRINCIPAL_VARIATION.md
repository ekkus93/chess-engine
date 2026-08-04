# Rust Principal Variation — Task 16.3

Task 16.3 adds bounded, collision-safe principal-variation reconstruction to every completed iterative-deepening result. Task 16.2 aspiration windows remains open and is not implemented by this change.

## Reconstruction contract

The first PV move comes from the completed exact root `AlphaBetaSearchResult`. Later moves come only from transposition entries that satisfy all of these conditions:

- the complete 64-bit verification key matches the current position;
- the entry bound is `Exact`;
- the stored depth is at least the remaining PV depth;
- the entry contains a best move.

Lookup is read-only and does not increment TT probes, hits, cutoffs, stores, or replacement counters.

Every candidate is matched against freshly generated legal move tokens for the current position before it is appended. An illegal stored move terminates reconstruction and is never returned. Search now retains best moves in internal exact entries so complete exact chains can be followed after the search has restored the root.

## Bounded termination

`PrincipalVariation` reserves at most the completed search depth in moves and at most depth plus one complete position identities. Reconstruction stops explicitly when it:

- reaches the requested depth;
- reaches a position with no legal moves;
- lacks an exact entry with sufficient depth;
- encounters a root result without a move;
- rejects an illegal stored move; or
- reaches a previously visited Zobrist identity.

The repeated-identity guard prevents a legal cyclic TT chain from looping, while the completed-depth bound provides an independent hard maximum.

## Ponder move

The ponder move is the second validated PV move. It is returned only when at least two legal moves were reconstructed. Terminal, truncated, collision-rejected, and one-ply lines return no ponder move.

## Public API

- `PrincipalVariation`
- `PrincipalVariationTermination`
- `PrincipalVariationError`
- `IterativeDeepeningIteration::principal_variation`
- `IterativeDeepeningIteration::ponder_move`
- `IterativeDeepeningSearchResult::principal_variation`
- `IterativeDeepeningSearchResult::ponder_move`

## Validation

Focused tests cover complete exact chains, ponder extraction, full-key collision rejection, exact-bound/depth requirements, illegal stored moves, repeated-position termination, diagnostic non-mutation, legal replay of every returned move, terminal roots, and exact root/history/Zobrist restoration.
