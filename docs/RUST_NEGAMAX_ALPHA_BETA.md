# Rust Negamax Alpha-Beta Search

## Scope

Task 13.2 adds a recursive, full-window negamax alpha-beta search to
`chess-search`.

The public entry point is:

```rust
alpha_beta_search(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
```

The result contains:

- an exact root `Score` from the root side-to-move perspective;
- the first deterministic best legal move when the root is searched rather
  than resolved as a leaf, terminal, or draw;
- the number of nodes actually visited, including the root.

Task 13.2 does not replace the Task 13.1 reference search. The reference search
remains the no-prune correctness oracle for the formal shallow equivalence work
owned by Task 13.3.

## Negamax contract

The implementation has one recursive side-to-move branch. It does not maintain
separate maximizing and minimizing functions.

For every legal child:

1. apply the source-bound legal token;
2. push the child position into detached line history;
3. search the child through the negated window `(-beta, -alpha)`;
4. pop line history and unmake the move exactly;
5. negate the child score for the current side;
6. update the first strictly better move and the alpha bound;
7. stop searching siblings when `alpha >= beta`.

The implementation is fail-soft internally: a cutoff returns the best searched
score rather than replacing it with the beta bound. The public root always uses
the complete supported score window, so the public root score is exact.

## Score, terminal, and draw semantics

Alpha-beta uses the same semantics as the reference search:

- static leaves use the side-to-move evaluator;
- checkmate at ply `p` is `Score::mated_in(p)`;
- score negation converts a child loss into a parent mate score;
- stalemate scores zero;
- dead positions score zero;
- threefold repetition and fifty-move claim opportunities score zero;
- fivefold repetition and the seventy-five-move rule are covered by the lower
  claim thresholds and also score zero;
- legal generation precedes draw thresholds so checkmate retains precedence on
  a simultaneous halfmove threshold.

The supported depth is bounded by `MAX_MATE_PLY` so mate-distance scores remain
inside the reserved score domain.

## Move and tie semantics

Legal generation order remains deterministic. A move replaces the current best
move only when its score is strictly greater. Equal scores retain the first
legal move.

This is a reproducibility contract for reference comparison, not a strength
ordering heuristic. Tactical and quiet move ordering remain Task 14 work.

## History and restoration

The supplied `SearchHistory` must end at the supplied root position. A mismatch
fails before search begins.

The search uses legal tokens, make/unmake, and reversible history push/pop. It
does not clone the position per child. Successful searches and validated input
failures preserve:

- the complete root `Position`;
- the root Zobrist key and recomputed hash equality;
- history length;
- line-history length;
- current history key.

Cancellation restoration is not claimed by Task 13.2 because cancellation is
introduced by Task 16. Task 13.4 retains that future acceptance item.

## Node counting

Every entered node counts as one. Cut-off siblings and their descendants are not
visited and therefore are not counted.

The starting position at depth three has a complete unpruned tree of
`1 + 20 + 400 + 8,902 = 9,323` nodes. The Task 13.2 regression requires the
alpha-beta implementation to visit fewer nodes while restoring root state
exactly.

Task 13.3 will add direct score, uniquely-best-move, and node-count comparisons
between reference and alpha-beta searches across a curated fixture set.

## Explicit exclusions

Task 13.2 does not implement:

- quiescence;
- tactical or quiet move ordering;
- transposition tables;
- iterative deepening;
- aspiration windows;
- principal variation storage;
- cancellation, time limits, or node limits;
- extensions or reductions;
- contempt or nonzero draw scores.
