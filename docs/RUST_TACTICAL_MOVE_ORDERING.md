# Rust Tactical Move Ordering

Task 14.2 adds a deterministic, bounded move-ordering layer to alpha-beta and
quiescence search without changing legal move identity or score semantics.

## Ordering pipeline

The production search order is:

1. a transposition-table move hook;
2. promotions, with higher promoted material first;
3. captures ordered by most-valuable victim, then least-valuable attacker;
4. remaining moves in their original deterministic legal-generation order.

The transposition-table hook deliberately returns `None` until Task 15 provides
bounded transposition storage. Keeping the hook explicit fixes the integration
point without introducing a fake cache or unbounded map.

Promotion captures remain in the promotion tier. Equal ordering keys are stable:
the insertion sorter does not displace an earlier legal token with an equal key.
This preserves deterministic behavior without using a strategic score as a move
override.

## Storage and state safety

`OrderedLegalMoves` is stack-backed with the same 256-entry capacity as legal
move generation. It copies opaque source-bound legal tokens into an ordered view;
it does not synthesize moves, mutate the position, allocate per node, or weaken
token origin validation. Search still applies and restores every child through
the existing token, history, and make/unmake contracts.

The unpruned reference search uses the explicit `Generation` policy, which
retains its original token order exactly. This provides a production-used
control policy and keeps reference-search semantics independent of heuristics.

## Correctness and performance evidence

Unit coverage verifies:

- the transposition-table hook is currently an explicit no-op;
- generation policy preserves the exact legal-token sequence;
- a supplied future TT move takes first priority;
- queen, rook, bishop, and knight promotions are ordered by material value;
- MVV-LVA prefers a more valuable victim and, for equal victims, a cheaper
  attacker;
- a fixed narrow-window tactical tree returns the same fail-soft score and best
  move while visiting fewer nodes than generation order;
- both searches restore the exact position, history, and Zobrist identity.

The permanent reference-equivalence, terminal, cancellation, quiescence, perft,
and differential gates continue to protect exact search semantics.

## Explicit exclusions

Task 14.2 does not add static exchange evaluation, killer moves, history
heuristics, previous-PV ordering, transposition storage, iterative deepening, or
production search limits. SEE remains optional only after the baseline ordering
is measured and correct. Quiet ordering belongs to Task 14.3, transposition
storage to Task 15, and limits/PV management to Task 16.
