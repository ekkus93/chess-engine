# Rust Reference Search

## Scope

Task 13.1 adds a correctness-first, unpruned negamax search to `chess-search`.
It is a reference implementation for tests and for later alpha-beta equivalence
work. It is not intended to be the final production search loop.

The public entry point is:

```rust
reference_search(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
) -> Result<ReferenceSearchResult, ReferenceSearchError>
```

The result contains:

- a `Score` from the root side-to-move perspective;
- the first deterministic best legal move, when the root is non-terminal and
  depth is greater than zero;
- the complete number of visited nodes, including the root.

## Tree semantics

The search visits every legal child. It performs no alpha-beta pruning,
quiescence, transposition-table probe, heuristic move ordering, extension, or
reduction.

Each node:

1. generates source-bound legal-move tokens;
2. resolves checkmate or stalemate when no token exists;
3. resolves search draws;
4. evaluates statically at depth zero;
5. otherwise makes every token, pushes the child hash, searches recursively,
   pops history, and unmakes exactly.

Tied moves preserve legal generation order. This deterministic tie policy is a
testing property, not a strength heuristic.

## Score convention

Scores retain the evaluator's side-to-move negamax convention.

- Static leaves use `evaluate(position)`.
- A side checkmated at ply `p` receives `Score::mated_in(p)`.
- Negation on return makes a mate found by the parent `Score::mate_in(p)`.
- Stalemate scores zero.
- Dead positions score zero.
- Threefold-repetition and fifty-move claim opportunities score zero because a
  searching side may claim them.
- Fivefold repetition and the seventy-five-move rule are covered by the lower
  claim thresholds and therefore also score zero.

Legal moves are generated before draw thresholds are checked. Checkmate
therefore takes precedence when the final move also reaches a move-count draw
threshold, matching `Game::status`.

## History contract

The supplied `SearchHistory` must end at the supplied `Position` Zobrist key.
A mismatch fails before search begins.

The reference search uses the public legal-token API and reversible
`SearchHistory` push/pop tokens. It does not clone the position per child. On a
successful search, the position, Zobrist key, history length, line length, and
current history key are restored to their root values.

## Node counting

Every entered node counts as one, including:

- the root;
- static-evaluation leaves;
- checkmate and stalemate nodes;
- draw nodes.

For example, the starting position at depth two visits `1 + 20 + 400 = 421`
nodes.

## Explicit exclusions

Task 13.1 does not implement:

- alpha-beta pruning;
- principal variation storage;
- iterative deepening;
- cancellation or time/node limits;
- quiescence;
- transposition tables;
- search move ordering;
- contempt or nonzero draw scores.

Those remain later Task 13 and subsequent-task work.
