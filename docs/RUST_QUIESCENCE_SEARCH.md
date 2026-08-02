# Rust Quiescence Search Contract

## Scope

Task 14.1 adds a correctness-first, fail-soft negamax quiescence search to
`chess-search` and invokes it at every normal alpha-beta depth-zero leaf.
It does not add move-ordering heuristics.

Public entry points:

- `reference_search_with_quiescence` as the unpruned tactical-leaf oracle;
- `reference_search_with_quiescence_and_cancellation`;
- `quiescence_search`;
- `quiescence_search_with_limit`;
- `quiescence_search_with_cancellation`;
- `QuiescenceSearchResult`;
- `MAX_QUIESCENCE_PLY`.

Quiescence uses the existing `AlphaBetaSearchResult` and
`AlphaBetaSearchError` contracts so normal and tactical leaves share one score,
node-count, cancellation, and restoration model.

## Score and bound semantics

- Scores remain from the side-to-move negamax perspective.
- The standalone root uses the complete supported mate-score window and returns
  an exact score under the selected bounded quiescence contract.
- Recursive calls use `(-beta, -alpha)` and return fail-soft scores.
- Mate scores use the absolute ply of the enclosing alpha-beta root, preserving
  the Task 13 shorter-mate and longer-survival ordering.
- Terminal and draw resolution occurs before stand-pat or tactical expansion.

## Tactical move scope

Outside check:

1. compute the static stand-pat score;
2. apply normal alpha/beta stand-pat logic;
3. search every legal capture, including en passant and promotion captures;
4. search every legal quiet promotion;
5. ignore all other quiet moves.

In check:

- stand-pat is forbidden;
- every legal evasion is searched, including quiet king moves, interpositions,
  and quiet moves by other pieces.

Legal generation order is preserved. No Task 14.2 or 14.3 ordering is active,
and equal scores retain the first deterministic move.

## Draws and history

Quiescence uses the same search policy as Task 13:

- no legal moves resolve as checkmate or stalemate before draw checks;
- dead positions score zero;
- repetition count three or greater scores zero;
- halfmove clock 100 or greater scores zero.

Every child is applied through a source-bound legal token, pushed onto the
detached `SearchHistory`, searched, popped, and unmade. No clone-per-child path
is used.

## Cancellation and restoration

Cancellation is checked at node and tactical-child boundaries. Cancellation,
rule errors, history errors, node-count overflow, and guard errors propagate only
after all active child history and position state has been restored.

Successful and failed calls preserve:

- logical `Position` equality;
- incremental and recomputed Zobrist equality;
- position invariants;
- complete detached history and current-root identity.

## Boundedness

The default `MAX_QUIESCENCE_PLY` is 64 tactical plies. A caller may choose a
smaller or larger explicit limit for a standalone search.

- Outside check, reaching the selected guard returns the current stand-pat score
  and does not expand further tactical moves.
- In check, reaching the guard fails loudly with
  `AlphaBetaSearchError::QuiescenceDepthLimitReachedInCheck`; it never treats a
  checked position as quiet.
- Absolute mate-distance ply is checked against `MAX_MATE_PLY` before a child is
  mutated.

This is a correctness and explosion guard, not a production time, node, or stop
policy. Task 16 retains those responsibilities.

## Permanent validation

The regression suite includes:

- an independent fixture-level tactical oracle and the production unpruned
  `reference_search_with_quiescence` oracle compared with alpha-beta quiescence;
- a hanging-rook horizon fixture;
- a checked leaf whose legal evasions are quiet;
- a quiet promotion fixture;
- a poisoned capture followed by a forced recapture;
- repetition draw resolution;
- mid-tree cooperative cancellation;
- a fail-loud in-check guard fixture;
- exact root position, history, invariant, and Zobrist restoration checks.

## Explicit exclusions

Task 14.1 does not implement:

- TT move hooks;
- MVV-LVA;
- static exchange evaluation;
- killer moves;
- history heuristics;
- previous-PV ordering;
- check extensions;
- delta pruning or speculative pruning;
- time limits, node limits, iterative deepening, or partial-result policy.
