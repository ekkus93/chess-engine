# Rust UCI Time Manager

Task 17.3 converts UCI clock fields into validated soft and hard search budgets. It is an adapter policy layer: `chess-search` continues to understand only typed `SearchLimits`, while `chess-uci` interprets clocks, increments, moves-to-go, and side to move.

## Inputs

The allocator receives:

- the parsed `GoCommand` snapshot;
- the current position's side to move;
- that side's remaining clock;
- that side's increment, when supplied;
- `movestogo`, when supplied.

The opponent's clock and increment do not influence the current move budget. They remain available in the parsed request for protocol completeness, but the allocator always selects the values belonging to the side to move.

A request containing clock-related fields must include a positive remaining clock for the side to move. Missing and zero side-to-move clocks are typed errors. The adapter does not silently substitute the opponent's clock, a fixed depth, or an arbitrary move time.

Requests without clock fields return no allocated budget. Consequently:

- `go depth` remains a depth limit;
- `go nodes` remains a node limit;
- `go movetime` remains an exact hard wall-clock limit;
- `go infinite` remains explicit-stop-only.

Depth and node limits may be combined with clock fields. In that case the search stops at whichever configured condition is reached first.

## Allocation policy

All calculations are integer millisecond calculations and are deterministic.

Let:

- `remaining` be the side-to-move clock;
- `increment` be the side-to-move increment, defaulting to zero;
- `horizon` be `movestogo`, defaulting to 30;
- `reserve` be the wall-clock safety reserve;
- `usable = remaining - reserve`.

The safety reserve is:

```text
reserve = max(10 ms, floor(remaining / 20))
```

For very small positive clocks, the reserve is capped at `remaining - 1 ms` so the search always receives at least one millisecond. A zero clock is rejected.

The soft budget is:

```text
base_share      = max(1 ms, floor(usable / horizon))
increment_share = floor(increment * 3 / 4)
soft            = min(usable, base_share + increment_share)
```

The hard budget is:

```text
hard = min(usable, 2 * soft)
```

The implementation uses overflow-safe integer decomposition and saturating arithmetic. The resulting invariants are:

- `soft > 0`;
- `hard > 0`;
- `soft <= hard`;
- `hard + reserve <= remaining`.

## Search semantics

The soft budget is checked only after a fully completed iterative-deepening iteration. It encourages the engine to return the deepest exact completed result without beginning another iteration after the normal allocation has expired.

The hard budget is checked inside the production search tree through the existing bounded cancellation path. It prevents a difficult incomplete iteration from consuming the safety reserve.

The request-local explicit stop flag remains active for clock searches. `stop`, replacement `go`, successful position replacement, `ucinewgame`, `quit`, EOF, and worker drop therefore retain the Task 17.2 cancellation contract.

## Boundary behavior

The deterministic tests cover:

- requests without clock fields;
- explicit `movestogo`;
- the default 30-move horizon;
- increment contribution;
- asymmetric White and Black clocks and increments;
- selection by the position's side to move;
- combined depth, node, soft-time, and hard-time limits;
- clocks of 1 ms, 10 ms, and 100 ms;
- missing side-to-move clock;
- zero side-to-move clock;
- maximum `u64` clock and increment values without overflow;
- preservation of hard-only `go movetime` behavior.

## Non-goals

Task 17.3 does not implement:

- position-complexity or branching-factor adjustments;
- ponder time;
- move-stability extensions or reductions;
- tournament phase detection;
- periodic `info` output;
- score, node, NPS, hash-full, or PV formatting;
- final `bestmove` output.

Search-result formatting and emission remain Task 17.4. Process-level UCI transcript coverage remains Task 17.5.
