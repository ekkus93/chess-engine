# Rust Search Equivalence

## Scope

Task 13.3 proves that the Task 13.2 negamax alpha-beta search preserves the
Task 13.1 reference-search result at accepted shallow depths.

This task adds verification only. It does not change evaluation, terminal
semantics, legal move generation, repetition policy, mate scoring, or search
move ordering.

## Required equivalence

For every curated fixture and accepted depth:

- alpha-beta and reference search return the same exact root score;
- alpha-beta visits no more nodes than reference search;
- the fixture set demonstrates at least one strict node reduction;
- each search restores the root `Position`, incremental Zobrist identity, and
  detached `SearchHistory` exactly.

Best-move equality is required only when the root has one exact best score.
Tied best moves remain deterministic inside each search, but Task 13.3 does not
turn one arbitrary tie choice into a semantic requirement.

## Curated fixture matrix

The integration suite in
`crates/chess-search/tests/search_equivalence.rs` covers:

| Category | Fixture | Depth |
|---|---|---:|
| quiet | standard starting position | 3 |
| tactical | queen can capture a hanging rook | 2 |
| terminal-adjacent | mate-in-one root | 2 |
| terminal | already mated root | 3 |
| terminal | stalemate root | 3 |
| rule draw | claimable fifty-move root | 3 |
| repetition | threefold game history from two knight cycles | 3 |

The starting-position fixture supplies the strict-pruning witness. Its complete
unpruned depth-three tree contains `9,323` nodes, while alpha-beta must visit
strictly fewer.

## Unique-best verification

The tactical position

```text
3r3k/8/8/8/8/8/8/K2Q4 w - - 0 1
```

is not accepted merely because both root searches happen to return the same
move. The test independently scores every legal root child with the reference
search, proves that exactly one child has the maximum score, and then requires
both root searches to return that move. The expected move is `d1d8`.

## Repetition verification

The repetition fixture is constructed through normal `Game` moves:

```text
g1f3 g8f6 f3g1 f6g8
```

repeated twice. The resulting root has repetition count three. Reference and
alpha-beta search must both return a zero score, no move, and one visited node
without changing the game-derived search history.

## Explicit exclusions

Task 13.3 does not complete:

- cancellation restoration;
- the full Task 13.4 immutability matrix;
- shorter-mate preference fixtures;
- longer-survival-when-mated fixtures;
- quiescence;
- move ordering;
- transposition tables;
- iterative deepening or principal variation storage.

Those remain assigned to Task 13.4, Task 13.5, and later search tasks.
