# Rust Search Terminal and Mate-Distance Fixtures

## Scope

Task 13.5 closes the correctness-first reference-search and alpha-beta phase with
fixed terminal, rule-draw, and mate-distance fixtures. The suite uses only
public `chess-core` and `chess-search` APIs and does not add production search
features.

The implementation is exercised by
`crates/chess-search/tests/search_terminals.rs`.

## Shared scoring contract

Both searches score positions from the side-to-move perspective:

- checkmate at the current node is `Score::mated_in(0)`;
- a forced win is a positive distance-aware mate score;
- a forced loss is a negative distance-aware mate score;
- stalemate and search-recognized draws are `Score::ZERO`.

Checkmate and stalemate are resolved before draw thresholds. A checkmated
position therefore remains a loss even when its halfmove clock has reached the
seventy-five-move threshold.

Higher scores are always preferred. Consequently:

- among winning mate scores, a shorter mate is higher;
- among losing mate scores, a longer survival is higher because it is less
  negative.

## Terminal and draw matrix

The fixed root matrix covers both reference and alpha-beta search:

| Case | Expected result |
|---|---|
| already checkmated with halfmove clock `150` | `mated_in(0)`, no move, one node |
| stalemate | zero, no move, one node |
| dead king-only position | zero, no move, one node |
| halfmove clock `100` | claimable fifty-move draw, one node |
| halfmove clock `150` | automatic seventy-five-move draw, one node |
| third occurrence | claimable repetition draw, one node |
| fifth occurrence | automatic repetition draw, one node |

The repetition roots are produced through legal knight cycles in `Game`, then
searched with the detached history returned by `Game::search_history()`.

## Shorter-mate fixture

FEN:

```text
7k/5Q2/6K1/8/8/8/8/8 w - - 0 1
```

At depth three, the suite compares two legal winning moves:

- `f7e8` scores `mate_in(1)`;
- `f7a7` scores `mate_in(3)`.

The complete root search must return `mate_in(1)` and select one of the legal
immediate mating moves `f7e8`, `f7f8`, `f7g7`, or `f7h7`. Reference and
alpha-beta search must return the same deterministic move and score.

The discovery diagnostic also observed mate-in-five alternatives, but the
permanent regression uses the minimum depth needed to prove the ordering rule.

## Longer-survival fixture

FEN:

```text
4Q2k/8/4K3/8/8/8/8/8 b - - 0 1
```

At depth six, Black has two legal continuations and both lose by force:

- `h8g7` scores `mated_in(6)`;
- `h8h7` scores `mated_in(4)`.

Because `mated_in(6)` is less negative, the engine must select `h8g7`. Both
search implementations must return that move and exact score.

## Independent root-move scoring

The fixture suite applies each selected legal token, pushes the child into a
detached search history, searches the child, then pops and unmakes before
examining the result.

A separately searched child begins with ply zero, so the test oracle translates
its score back to the parent root by adding one ply of mate distance while
negating the side-to-move perspective. Non-mate scores require only negation.
This prevents a child-root search from silently producing an off-by-one mate
score.

## Restoration requirements

After every full-root and individual-root-move search, the suite requires:

- exact logical `Position` equality with the root snapshot;
- exact detached `SearchHistory` equality with the root snapshot;
- matching incremental and recomputed Zobrist identities;
- a history current key equal to the restored root key;
- all publicly enforceable position invariants to pass.

Alpha-beta must visit no more nodes than the unpruned reference search for each
paired full-root fixture.

## Explicit exclusions

Task 13.5 does not implement:

- quiescence search or move ordering;
- transposition tables;
- iterative deepening or principal variations;
- clocks, node budgets, or production cancellation policy;
- UCI or Android integration.

Those remain assigned to Tasks 14 and later.
