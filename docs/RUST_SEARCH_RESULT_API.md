# Rust Search Result API

Task 16.6 defines one authoritative public snapshot for a limit-controlled search request.

## `SearchResult`

`SearchResult` exposes:

- `best_move`: the deepest exact iteration's deterministic move, or the Task 16.5 emergency fallback when no depth completed;
- `ponder_move`: the second validated move from the deepest completed legal PV;
- `score`: an `Option<Score>` because an emergency fallback is intentionally unscored;
- `completed_depth`: the deepest fully exact iterative-deepening depth;
- `selective_depth`: the maximum root-relative ply actually entered, including quiescence and discarded partial work;
- `nodes`: every production node entered across all attempts, completed depths, and interrupted partial work;
- `qnodes`: the quiescence subset of `nodes`;
- `elapsed`: request time measured by the configured search clock;
- `principal_variation`: the deepest completed legal PV;
- `termination`: the typed winning `SearchLimitTermination`.

The detailed `IterativeDeepeningSearchResult` remains available through `completed()` so per-depth aspiration and transposition diagnostics are not lost.

## Exact versus fallback data

Only a fully completed exact iteration may provide score, PV, ponder move, or completed depth. A cancellation before depth one may provide a deterministic legal fallback move, but it cannot invent a score or PV. Terminal fallback is represented by `NoLegalMove`.

## Node accounting

`nodes` includes alpha-beta and quiescence nodes. `qnodes` is a subset. Both include partial interrupted work. `incomplete_nodes()` and `incomplete_qnodes()` subtract fully completed work.

Each production node reports its root-relative ply through the cancellation probe. This lets the limit controller track request-wide selective depth without a second tree walk or unbounded storage.

## Compatibility

`LimitedIterativeDeepeningSearchResult` remains a type alias for `SearchResult`, and `searched_nodes()` remains an accessor alias. New integrations should use `SearchResult`, `nodes()`, and `qnodes()`.
