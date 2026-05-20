# Chess Engine AI Search Fix Spec

## Purpose

This specification defines the next focused repair pass for the chess engine AI search layer.

The current known problem is **not** that alpha-beta pruning is completely absent. Manual inspection and shallow node-count comparisons show that alpha-beta can prune. The confirmed issue is that `get_best_move()` uses an unsafe aspiration-window search without fail-high/fail-low re-search. That can cause the search to treat a bound result as an exact best move, which leads to incorrect move selection such as missing mate-in-one at depth 1.

This pass must make the search correct, measurable, and safe before any deeper performance tuning is attempted.

## Scope

This pass is limited to:

1. Removing or disabling unsafe aspiration windows.
2. Correcting minimax terminal-state ordering.
3. Ensuring leaf evaluation returns raw evaluation values.
4. Implementing or repairing correct transposition-table semantics.
5. Making alpha-beta pruning measurable with node counters and shallow no-prune reference tests.
6. Improving move ordering without changing board evaluation.
7. Keeping depth-5 work out of default unit tests.
8. Quarantining or deleting unsafe unused undo-based search helpers.

## Non-goals

Do **not** implement any of the following in this pass:

- Board-evaluation tuning.
- Quiescence search.
- Iterative-deepening time controls.
- UCI protocol support.
- GUI work.
- New chess rules.
- Undo-based make/unmake search.
- Aspiration windows unless proper fail-high/fail-low re-search is also implemented and fully tested.

If the engine already has iterative deepening, keep it. Do not redesign it. The issue is not iterative deepening itself; the issue is unsafe narrow-window search inside it.

## Current diagnosis

### Alpha-beta is not completely broken

The alpha-beta loop updates alpha and beta in the expected places:

```python
if params.is_maximizing:
    alpha = max(alpha, child_score)
    if alpha >= beta:
        break
else:
    beta = min(beta, child_score)
    if beta <= alpha:
        break
```

A shallow comparison from the starting position showed alpha-beta visiting fewer nodes than plain minimax at depth 2. Therefore, do not assume pruning is entirely disabled.

### The aspiration-window implementation is unsafe

The current pattern is approximately:

```python
score = 0
for d in range(1, depth + 1):
    alpha = score - 50
    beta = score + 50
    score, move = minimax(board, depth=d, alpha=alpha, beta=beta)
```

This is an aspiration-window search. A narrow alpha/beta window may return a bound, not an exact score. If the score fails high or fails low, the search must be repeated with a wider window. The current implementation accepts the first result even when it is outside the window.

That is incorrect.

For now, use full-width alpha-beta:

```python
alpha = -INF
beta = INF
```

### Mate-at-horizon must be handled correctly

Terminal positions must be detected before the depth cutoff:

1. Generate legal moves.
2. If no legal moves, return checkmate or stalemate score.
3. Then, if `depth == 0`, return raw `evaluate(board)`.

A depth-1 search must find mate-in-one.

### Leaf scores must not be alpha/beta clamped

At depth 0, return:

```python
return evaluate(board), None
```

Do not return a score clamped to the alpha/beta window. Alpha and beta are pruning bounds, not evaluation modifiers.

## Required search semantics

### Score perspective

The current evaluator appears to score from White's perspective:

- Positive score favors White.
- Negative score favors Black.

Search must preserve that convention consistently.

- White to move is maximizing.
- Black to move is minimizing.

### Terminal scoring

Use clear constants, for example:

```python
INF = 10_000_000
MATE_SCORE = 100_000
```

If the side to move is checkmated:

- If White is checkmated, return `-MATE_SCORE`.
- If Black is checkmated, return `+MATE_SCORE`.

Optionally include depth distance to prefer faster mates and slower losses:

```python
mate_score = MATE_SCORE + depth
```

or

```python
mate_score = MATE_SCORE + ply_remaining
```

Keep this simple and documented. Do not tune evaluation around it.

If the side to move is stalemated, return `0`.

## Transposition table contract

The transposition table must be implemented with correct alpha-beta bound semantics.

### Position key

Use a position key that includes at least:

- Board piece placement.
- Side to move.
- Castling rights.
- En passant target.

Do **not** append depth to the key. Store depth inside the table entry.

Good:

```python
key = _position_key(board)
```

Bad:

```python
key = _position_key(board) + f":d{depth}"
```

If the key is not full FEN, do not call it `_fen_key()`. Prefer `_position_key()`.

### Entry format

Use a dataclass or equivalent:

```python
@dataclass(frozen=True)
class TTEntry:
    depth: int
    score: int
    best_move: LegalMove | None
    flag: TTFlag
```

Use an enum:

```python
class TTFlag(Enum):
    EXACT = "exact"
    LOWERBOUND = "lowerbound"
    UPPERBOUND = "upperbound"
```

`best_move` must preserve promotion identity. If the repo uses a `LegalMove` dataclass, store that. If it uses tuples, store the full `(start, end, promotion)` tuple.

### Probe semantics

A table entry may be used only if:

```python
entry.depth >= requested_depth
```

Then:

- `EXACT`: return `entry.score, entry.best_move`.
- `LOWERBOUND`: return only if `entry.score >= beta`.
- `UPPERBOUND`: return only if `entry.score <= alpha`.
- Otherwise, do not return a score from the table for this node.

Non-cutoff lower/upper bounds may still be useful for narrowing alpha/beta, but that is optional for this pass. If implemented, it must be done carefully and tested. The simpler acceptable behavior is to ignore non-cutoff bounds.

### Store semantics

Store exactly once per searched node.

Keep the original alpha/beta values from before searching the node:

```python
alpha_orig = alpha
beta_orig = beta
```

After searching:

- If `score <= alpha_orig`, store `UPPERBOUND`.
- Else if `score >= beta_orig`, store `LOWERBOUND`.
- Else store `EXACT`.

Do not store twice in both `_search_move_loop()` and `minimax()`.

### TT best move ordering

Even when a TT entry cannot be used directly for a cutoff, its best move may be used for move ordering.

If a TT best move is legal in the current position, order it first.

The TT best move must include promotion:

```python
start
end
promotion
```

Do not match moves by start/end only.

## Move ordering contract

Move ordering may be improved in this pass because it affects pruning performance but not final minimax correctness.

Allowed move-ordering improvements:

1. TT best move first.
2. Captures before quiet moves.
3. MVV-LVA style capture scoring if easy:
   - Most valuable victim.
   - Least valuable attacker.
4. Promotions ordered by promotion piece value:
   - Queen above rook above bishop/knight.
5. Existing reasonable heuristics may remain if they do not change final evaluation.

Do not change board evaluation material values or piece-square tables.

## Node-count instrumentation

Add lightweight instrumentation for tests/benchmarks.

Acceptable designs:

- A mutable stats object passed into `minimax()`.
- A `SearchStats` dataclass.
- A test-local wrapper if production code should stay clean.

The stats should count at least:

- Nodes visited.
- Cutoffs, if practical.
- TT hits, if practical.

Node-count tests should be shallow and deterministic.

## No-prune reference search

Add a no-prune minimax reference for tests/benchmarks only.

It should:

- Use the same terminal handling as the real search.
- Use the same evaluator.
- Not perform alpha-beta cutoffs.
- Be used only at shallow depth, such as depth 1 or 2.

Do not use the no-prune search in production move selection.

## Depth-5 policy

Depth 5 should not be part of the default fast unit test suite.

If depth-5 tests exist, either:

- Mark them as slow with pytest markers, or
- Move them to a benchmark/manual test file, or
- Lower their depth for default CI.

Default tests should normally use depth 1–3.

## Undo-based search policy

Do not switch to undo-based search in this pass.

If functions such as `apply_move_for_search()` and `unapply_move_for_search()` exist and are unused/broken, either:

- Delete them, or
- Move/quarantine them with clear comments that they are not used by current search.

Do not build new search work on unsafe undo helpers.

## Self-play requirements

If self-play formats moves, promotion suffix formatting must use `PieceType` values directly.

Correct pattern:

```python
promo_map = {
    PieceType.QUEEN: "q",
    PieceType.ROOK: "r",
    PieceType.BISHOP: "b",
    PieceType.KNIGHT: "n",
}
```

Do not rely on `str(PieceType.ROOK)`, because `PieceType` is an `IntEnum` and string conversion may produce numeric strings.

Self-play depth arguments must reject depth less than 1.

## Required tests

Add focused tests, preferably in:

```text
tests/test_ai_search.py
```

Required coverage:

1. Mate-in-one is found at depth 1.
2. `get_best_move()` agrees with direct full-window minimax in a mate-in-one position.
3. Terminal checkmate/stalemate is handled before depth cutoff.
4. Depth-0 leaf returns raw evaluation if a direct minimax leaf path remains public/internal enough to test.
5. Alpha-beta visits fewer nodes than a no-prune reference at shallow depth.
6. TT entries use `_position_key(board)` without appending depth.
7. TT entries with sufficient depth are reusable at shallower/equal depths.
8. TT flags `EXACT`, `LOWERBOUND`, and `UPPERBOUND` are stored correctly.
9. TT best move preserves promotion identity.
10. `get_best_move(depth < 1)` raises `ValueError`.
11. Self-play rejects invalid depth values.
12. Self-play formats underpromotion suffixes correctly.

## Acceptance criteria

This pass is complete only when:

- Unsafe aspiration windows are removed or replaced with correct fail-high/fail-low re-search.
- Full-width alpha-beta is used by default.
- Mate-in-one is found at depth 1.
- Terminal states are checked before depth cutoff.
- Leaf evaluation is raw and unclamped.
- TT key does not include depth.
- TT stores exactly once per searched node.
- TT uses `EXACT`, `LOWERBOUND`, and `UPPERBOUND` correctly.
- TT best move ordering preserves promotion identity.
- Alpha-beta pruning is measured against a no-prune reference at shallow depth.
- Default tests do not depend on depth-5 search completing quickly.
- No unsafe undo-based search helpers remain in active use.
- Full test suite passes:

```bash
python -m pytest tests -q
```
