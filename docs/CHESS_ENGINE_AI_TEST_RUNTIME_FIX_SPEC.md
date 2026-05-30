# CHESS_ENGINE_AI_TEST_RUNTIME_FIX_SPEC.md

## Purpose

This spec defines a focused test-runtime cleanup pass for the chess engine AI/search test suite.

The chess rules engine is currently stable, and the recent AI cleanup improved search correctness, removed the hidden depth-5 opening shortcut, fixed the depth-5 node-count test, and improved TT root score/move handling. However, the default non-slow test suite is still not reliably fast/runnable.

The main confirmed problem is:

> Expensive AI regression tests remain unmarked as `slow`, so `python -m pytest tests -q -m "not slow"` can still run too long or time out.

This pass is about test classification, runtime discipline, and preserving the existing AI/search correctness work. It is **not** a search rewrite and not an engine-strength improvement pass.

---

## Current observed state

From the latest review:

- Rules subset passed quickly:

  ```text
  190 passed in 0.79s
  ```

- Targeted alpha-beta suite passed:

  ```text
  6 passed in 13.42s
  ```

- Targeted AI quality suite passed:

  ```text
  52 passed in 11.35s
  ```

- The default non-slow suite still did **not** reliably finish in the review environment:

  ```bash
  python -m pytest tests -q -m "not slow" --durations=15
  ```

- It collected approximately:

  ```text
  669 items / 61 deselected / 608 selected
  ```

- The run became impractically slow in non-slow AI regression/search tests.

Known likely offenders include:

```text
tests/test_ai_endgame1_regressions.py
tests/test_ai_search.py
tests/test_ai_strategy5_regressions.py
```

The previous cleanup marked some strategy/review files as slow, but not enough.

---

## Non-goals

Do **not** do any of the following in this pass:

- Do not tune evaluation.
- Do not change material values.
- Do not change piece-square tables.
- Do not add chess heuristics.
- Do not add new strategy guidance modules.
- Do not rework minimax.
- Do not rework alpha-beta.
- Do not rework TT semantics.
- Do not reintroduce the hidden depth-5 starting-position shortcut.
- Do not add quiescence search.
- Do not implement undo-based search.
- Do not add UCI support.
- Do not hide failing tests by weakening their assertions.
- Do not mark the entire AI suite slow without preserving fast AI correctness coverage.

---

## Runtime policy

Apply this policy consistently.

### Default non-slow tests

Default non-slow tests should be fast correctness tests.

They may include:

- board/rules tests,
- shallow AI correctness tests,
- mate-in-one at depth 1,
- terminal checkmate/stalemate handling,
- depth validation,
- TT unit-level behavior,
- move ordering helper tests,
- promotion identity tests,
- shallow alpha-beta vs no-prune node-count tests.

### Slow tests

Mark tests `slow` if they include any of these:

- depth 4 or depth 5 search,
- complex depth-3 strategic search,
- transcript-style strategic regressions,
- exact-move tests based on nuanced strategic preferences,
- self-play search loops,
- full-game or multi-move AI sequences,
- tests that regularly take multiple seconds,
- tests that primarily validate playing style instead of core correctness.

### Depth-specific policy

```text
Depth 1:
  Usually allowed in non-slow tests.

Depth 2:
  Usually allowed if position is small/normal.

Depth 3:
  Non-slow only if the position is tiny and runtime is proven fast.
  Otherwise mark slow.

Depth 4+:
  Always slow.

Depth 5:
  Always slow/manual/benchmark.
```

### Category-specific policy

```text
Rules tests:
  Non-slow.

Small tactical AI tests:
  Non-slow if fast.

Strategic regression tests:
  Slow by default.

Transcript-derived AI behavior tests:
  Slow by default.

Self-play tests:
  Slow unless mocked/trivial.

Benchmarks/node-limit tests:
  Slow unless shallow and fast.
```

---

## Required behavior

### Fast default command

This command must complete reliably:

```bash
python -m pytest tests -q -m "not slow" --durations=25
```

Target runtime:

```text
Prefer under 2 minutes.
Hard target under 3 minutes.
```

If it cannot finish under 3 minutes on a normal dev machine, more tests need to be marked slow or rewritten.

### Slow suite command

Slow tests may be expensive and should be run explicitly:

```bash
python -m pytest tests -q -m "slow" --durations=25
```

The slow suite can be used for manual/extended validation, not normal fast iteration.

### Preserve AI correctness tests

Do not move all AI coverage into `slow`.

Keep non-slow tests for:

- mate-in-one at depth 1,
- depth validation,
- legal move return shape,
- TT entry flag/unit behavior,
- alpha-beta shallow pruning vs no-prune,
- promotion-aware move identity,
- self-play formatting helper if cheap.

### No hidden shortcuts

Do not re-add:

```python
if depth >= 5 and _is_initial_position(board):
    return _preferred_starting_move(legal_moves)
```

Depth-5 search should remain real search and should be slow/manual.

### No evaluation/search changes

This pass should normally change only:

- pytest markers,
- test classification,
- maybe test helper/runtime structure,
- documentation/memory notes.

If a test is slow, mark it slow or rewrite it to a cheaper equivalent. Do not “fix” runtime by changing chess engine behavior.

---

## Expected files likely touched

Likely files:

```text
tests/test_ai_endgame1_regressions.py
tests/test_ai_search.py
tests/test_ai_strategy5_regressions.py
pytest.ini or pyproject.toml
memory.md
docs/CHESS_ENGINE_AI_TEST_RUNTIME_FIX_SPEC.md
docs/CHESS_ENGINE_AI_TEST_RUNTIME_FIX_TODO.md
```

Possibly touched if needed:

```text
tests/test_alpha_beta_pruning.py
tests/test_ai_quality.py
```

Do not touch engine modules unless a test helper import or marker issue absolutely requires it.

---

## Acceptance criteria

This patch is complete only when:

1. Expensive non-slow AI regression tests have been identified.
2. Expensive AI/search/strategy tests are marked `slow`.
3. Fast AI correctness tests remain non-slow.
4. `tests/test_ai_endgame1_regressions.py` is either marked slow or split into fast/slow portions.
5. Expensive tests in `tests/test_ai_search.py` are marked slow or rewritten to be cheap.
6. `tests/test_ai_strategy5_regressions.py` has been reviewed and marked slow if needed.
7. `python -m pytest tests -q -m "not slow" --durations=25` passes and completes in a practical time.
8. `python -m pytest tests -q -m "slow" --durations=25` can be run as an explicit extended suite.
9. No search/evaluation/TT behavior was changed merely to reduce test runtime.
10. No hidden depth-5 opening shortcut was reintroduced.
11. `memory.md`, if updated, clearly notes that older AI entries may be historical/stale.
