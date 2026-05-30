# CHESS_ENGINE_AI_CLEANUP_SPEC.md

## Purpose

This spec defines a focused cleanup pass for the chess engine AI/search layer.

The current chess rules engine is in relatively good shape. The main confirmed problems are now in AI/search engineering discipline:

- The default test suite has become too slow.
- Some expensive AI/strategy tests are not marked `slow`.
- `get_best_move(Board(), depth >= 5)` contains a hidden starting-position shortcut that bypasses real search.
- A depth-5 node-count test is not measuring the real search node counter.
- Some alpha-beta pruning tests are misleading because they compare tight-window alpha-beta to wide-window alpha-beta instead of alpha-beta to a no-prune reference.
- Transposition table entries can store a root tie-break-selected move that may not correspond to the stored best score.
- Generated cache files are still present in the repo tree.
- AI heuristic modules and exact-move strategic tests are growing in complexity and should not be expanded during this cleanup.

This pass is not a chess-strength improvement pass. It is a correctness, maintainability, and test-infrastructure pass.

---

## Non-goals

Do **not** do any of the following in this pass:

- Do not add new chess heuristics.
- Do not tune material values.
- Do not tune piece-square tables.
- Do not add quiescence search.
- Do not add UCI support.
- Do not implement undo-based search.
- Do not replace clone-based search.
- Do not add new opening-book behavior.
- Do not add new time-management or iterative-deepening time controls.
- Do not broaden this into a rules-engine rewrite.
- Do not make tests pass by weakening chess correctness.

---

## Current known-good baseline

From the latest review:

- The board/rules subset passed quickly: `190 passed in 0.78s`.
- `tests/test_alpha_beta_pruning.py` passed: `6 passed in 13.13s`.
- `tests/test_ai_quality.py` passed: `52 passed in 11.23s`.
- The full default test suite collected roughly `668 tests`, but it was too slow to complete in the review environment.
- Even `python -m pytest tests -q -m "not slow"` timed out, which means too many expensive tests are still in the default path.

The cleanup is successful only if the default non-slow suite becomes practically runnable again.

---

## Design principles

### 1. Correctness before strength

The AI should return legal, searched, explainable moves. Do not add more special-case heuristics to mask search or test problems.

### 2. Default tests must be fast

Normal unit tests should cover correctness at shallow depths and small positions. Expensive strategic/depth tests must be marked `slow`.

### 3. Depth means depth

If `get_best_move(board, depth=5)` claims to search depth 5, it must actually search depth 5 unless an explicit, named opening-book option is enabled.

A hidden shortcut inside `get_best_move()` is not acceptable.

### 4. Alpha-beta tests must measure real pruning

A true pruning test compares:

```text
plain minimax node count
vs.
alpha-beta node count
```

Do not call tight-window alpha-beta vs wide-window alpha-beta "with pruning vs without pruning." Both are alpha-beta.

### 5. TT entries must be internally consistent

A transposition table entry's stored score and stored best move must correspond to the same searched move. Root tie-break policy may choose a different near-equal move to return, but that returned root preference should not pollute TT exact entries.

### 6. Keep generated files out of the repo

`__pycache__/`, `.pytest_cache/`, and `*.pyc` files must not appear in the working tree handoff.

---

## Required behavior

### Fast default tests

The following command must complete in a reasonable time:

```bash
python -m pytest tests -q -m "not slow"
```

This should be the CI/default correctness command.

Expensive search/strategy tests must be marked:

```python
@pytest.mark.slow
```

### Depth-5 search behavior

Remove the hidden shortcut:

```python
if depth >= 5 and _is_initial_position(board):
    return _preferred_starting_move(legal_moves)
```

or convert it into an explicit option such as:

```python
get_best_move(board, depth=5, use_opening_book=True)
```

Default behavior must not silently bypass search.

Preferred for this cleanup pass: remove the hidden shortcut entirely.

### Depth-5 tests

Depth-5 tests should be either:

- marked `slow`, or
- converted into shallow correctness tests.

Do not include depth-5 search in the default fast suite.

### Node-count tests

Any node-count test must use the actual node counter used by the search. Prefer `SearchStats` if available.

A broken pattern like this is invalid:

```python
nodes = [0]
params = make_params_with_nodes(depth=5)
minimax(board, params)
assert nodes[0] < 500_000
```

because `nodes` is not connected to the search.

### TT root score/move consistency

At root, separate:

```text
search_best_score
search_best_move_that_produced_score
root_selected_move_after_tiebreak
```

The TT should store:

```text
search_best_score
search_best_move_that_produced_score
```

`get_best_move()` may return:

```text
root_selected_move_after_tiebreak
```

when the root tie-break policy prefers a near-equal move, but this must not corrupt TT entries.

### Alpha-beta tests

Keep or add a true no-prune comparison test:

```text
plain minimax at shallow depth visits more nodes than alpha-beta
```

Remove or rename tests that compare tight-window alpha-beta to wide-window alpha-beta and claim this is "with vs without pruning."

### Repo hygiene

Remove generated files:

```bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

Ensure `.gitignore` contains:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
```

---

## Acceptance criteria

The patch is complete when:

1. The default non-slow test suite completes in a reasonable time.
2. Expensive AI/strategy/depth tests are marked `slow`.
3. Hidden depth-5 starting-position search bypass is removed or made explicit and disabled by default.
4. Depth-5 node-count test uses the real node counter or is removed/marked slow.
5. TT entries do not store a tie-break-selected root move with a score from a different move.
6. Misleading alpha-beta pruning tests are removed or renamed.
7. True no-prune vs alpha-beta pruning tests remain.
8. Generated cache files are removed from the repo tree.
9. No new chess heuristics or evaluation tuning are introduced.
10. Full relevant verification commands pass.
