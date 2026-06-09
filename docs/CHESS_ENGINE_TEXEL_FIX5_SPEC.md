# CHESS_ENGINE_TEXEL_FIX5_SPEC.md

## Purpose

This document specifies a narrow **Fix 5 final acceptance patch** for the chess engine's Texel/search/test reliability work.

Fix 4 made progress, but the latest review still found hard acceptance blockers:

1. Ruff fails due to an unused variable in `tests/test_online_learning.py`.
2. The full fast test suite still does not complete.
3. A current known hanging fast test is:
   ```text
   tests/test_ai_white_improvements3.py::test_depth3_avoids_b4_when_path_blocked
   ```
4. Collection tests still mostly prove configuration construction rather than behavior.
5. PositionDB compatibility tests still do not fully assert `total`, `count`, and `mean`.
6. Texel loss `k` tests still do not directly prove non-default `k` behavior or `k=` backward compatibility.
7. Opening-book different-seed tests still contain vacuous assertions.
8. Special perft exact-count coverage remains deferred; this is acceptable only if the deferral remains honest and documented.

This patch should finish those remaining acceptance issues. It should not add new chess-engine architecture or new engine-strength features.

---

## Hard scope boundaries

### In scope

- Fix Ruff failure.
- Make `uv run python -m pytest -m "not slow"` complete reliably.
- Mark remaining depth-heavy/engine-strength regression tests slow.
- Remove/replace vacuous assertions.
- Strengthen collection behavior tests.
- Strengthen PositionDB stats/JSONL tests.
- Strengthen Texel loss `k` tests.
- Strengthen opening-book seed tests.
- Preserve honest special perft deferrals.
- Run final validation.

### Out of scope

Do **not** implement:

- make/unmake search,
- bitboards,
- true Zobrist hashing,
- NNUE/neural evaluation,
- large `ai.py` decomposition,
- broad search refactors,
- new chess heuristics,
- broad feature additions.

This is an acceptance-cleanup patch only.

---

# Required final outcome

The patch is complete only when all of these pass:

```bash
uv run python -m ruff check chess_game tests
uv run python -m mypy chess_game
uv run python -m pylint chess_game/texel --score=y
uv run python -m pytest -m "not slow"
```

Targeted tests must also pass:

```bash
uv run python -m pytest \
  tests/test_ai_quiescence_production.py \
  tests/test_search_terminal_scores.py \
  tests/test_perft.py \
  tests/test_loss.py \
  tests/test_spsa.py \
  tests/test_position_db.py \
  tests/test_collect.py \
  tests/test_online_learning.py \
  tests/test_validate.py \
  tests/test_tune.py \
  tests/test_opening_book.py \
  -m "not slow" -q
```

Run slow tests separately:

```bash
uv run python -m pytest -m slow
```

If the slow suite is very slow, document it, but slow tests must be excluded from the fast suite.

---

# Problem 1: Ruff currently fails

## Current failure

Ruff reports:

```text
F841 Local variable `initial_size` is assigned to but never used
tests/test_online_learning.py:636:9
```

## Required fix

Remove the unused variable or replace it with a real assertion.

Do not paper over the warning with `# noqa`. This project’s lint policy should remain strict.

## Acceptance criteria

```bash
uv run python -m ruff check chess_game tests
```

passes.

---

# Problem 2: Full fast suite still times out

## Current problem

The full fast suite still times out:

```bash
uv run python -m pytest -m "not slow"
```

The latest review found the current known hanging test:

```text
tests/test_ai_white_improvements3.py::test_depth3_avoids_b4_when_path_blocked
```

This test performs depth-3 strategic search and belongs in the slow suite unless rewritten into a cheap helper-level test.

## Required fix

Mark this test slow:

```python
@pytest.mark.slow
def test_depth3_avoids_b4_when_path_blocked(...):
    ...
```

or rewrite it into a genuinely fast helper-level regression. Marking it slow is preferred because it is an engine-strength/depth-heavy strategic regression.

Then rerun:

```bash
uv run python -m pytest -m "not slow" -vv
```

and continue marking any remaining depth-heavy/engine-strength tests slow until the fast suite completes.

## Rule

- Depth-3+ full-root `get_best_move()` tests are slow by default unless proven fast.
- Strategic/engine-strength behavior regressions belong in the slow suite.
- Fast tests should be helper-level, low-depth, deterministic, or narrowly tactical.

## Acceptance criteria

```bash
uv run python -m pytest -m "not slow"
```

completes reliably.

---

# Problem 3: Collection tests still do not prove behavior

## Current problem

Some tests still only check config construction, for example:

```python
assert opts.max_move_result == "draw"
```

when the test name claims that max-move draw behavior stores outcome `0.5`.

That is not a behavior test.

## Required behavior

Collection tests must use monkeypatching or controlled fake games to prove actual behavior without expensive self-play.

## Required tests

Add or strengthen fast tests proving:

1. `CollectionOptions.weights` is passed into `BestMoveOptions`.
2. Max-move result `"draw"` stores `0.5` for positions from the game.
3. Max-move result `"discard"` stores no positions.
4. Draw terminal outcomes are recorded as `0.5`.
5. Invalid `max_move_result` raises `ValueError`.
6. `CollectionOptions(seed=...)` produces reproducible recorded data under a controlled mocked scenario.
7. Real full self-play collection tests remain marked slow.

## Guidance

Use monkeypatches/fakes. Acceptable approaches:

- Monkeypatch `get_best_move()` and capture `BestMoveOptions`.
- Monkeypatch `_play_game()` to return controlled `GameRecord`s.
- Use a fake/minimal `PositionDatabase`.
- Directly test collection helper functions if those are the actual code paths.

Do not rely on full self-play in fast tests.

## Acceptance criteria

- No collection test claims behavior while only asserting config field values.
- The draw/discard/weights/seed behaviors are actually tested.
- Fast collection tests complete quickly.

---

# Problem 4: PositionDB stats tests are still incomplete

## Current problem

`PositionDB.get_stats()` now exists, but tests still do not fully assert raw stats for all required compatibility cases.

## Required tests

### Duplicate aggregation

Add the same FEN with outcomes:

```text
1.0
0.5
0.0
```

Assert:

```python
stats.count == 3
stats.total == pytest.approx(1.5)
stats.mean == pytest.approx(0.5)
```

### Old JSONL duplicate aggregation

Create hand-authored old-format JSONL:

```json
{"pos": "fen", "outcome": 1.0}
{"pos": "fen", "outcome": 0.5}
{"pos": "fen", "outcome": 0.0}
```

Load it and assert:

```python
stats.count == 3
stats.total == pytest.approx(1.5)
stats.mean == pytest.approx(0.5)
```

### New JSONL direct load

Create hand-authored new-format JSONL:

```json
{"pos": "fen", "total": 3.0, "count": 4}
```

Load it and assert:

```python
stats.count == 4
stats.total == pytest.approx(3.0)
stats.mean == pytest.approx(0.75)
```

### Round trip

Save and reload aggregated stats, then verify exact `count`, `total`, and `mean`.

## Acceptance criteria

- Tests prove raw stats, not just `all_pairs()` means.
- Old and new JSONL compatibility are directly tested with hand-authored files.
- Existing saved PositionDB compatibility is preserved.

---

# Problem 5: Texel loss k tests are still weak

## Current problem

Existing `k` tests still do not prove:

1. non-default `k` changes MSE,
2. `k=` is backward-compatible with `opts=LossOptions(k=...)`.

A test that only asserts values are non-negative is not sufficient.

## Required tests

### Non-default k changes MSE

Use a nonzero-eval FEN and a draw outcome so sigmoid steepness matters.

Recommended FEN:

```text
4k3/8/8/8/8/8/8/4KQ2 w - - 0 1
```

White is up a queen. Pair with outcome `0.5`:

```python
pairs = [(fen_white_up_queen, 0.5)]
```

Then assert:

```python
mse_default = mean_squared_error(pairs, weights, k=DEFAULT_K)
mse_other = mean_squared_error(pairs, weights, k=DEFAULT_K * 2)

assert mse_default != pytest.approx(mse_other)
```

This should fail if `k` is ignored.

### k= backward compatibility

Actually call both APIs:

```python
mse_k_kwarg = mean_squared_error(pairs, weights, k=some_k)
mse_opts = mean_squared_error(pairs, weights, opts=LossOptions(k=some_k))

assert mse_k_kwarg == pytest.approx(mse_opts)
```

If the current public parameter is `options=` instead of `opts=`, use the current public spelling. Do not invent a new spelling unnecessarily.

## Acceptance criteria

- No vacuous `k` assertions remain.
- `k=` behavior is directly tested.
- Non-default `k` behavior is directly tested.

---

# Problem 6: Opening-book different-seed test is still vacuous

## Current problem

A test still contains logic like:

```python
if move_seed_42_run1 is not None or move_seed_99 is not None:
    assert True, "Seed mechanism is working"
```

That proves nothing.

## Required behavior

Use a controlled fake/monkeypatched opening-book path so the test can prove different seeds can select different moves.

## Required tests

1. Same seed returns the same book move.
2. Different seeds return different book moves under a controlled multi-candidate setup.
3. Seeded book selection is independent of prior global RNG state.

## Preferred approach

Monkeypatch the opening-book path used by `get_best_move()`:

- Provide fake book candidate moves.
- Ensure candidate moves are legal.
- Choose seeds known to produce different choices.
- Call the real public path:

```python
get_best_move(
    board,
    depth=1,
    book_options=BestMoveOptions(
        use_opening_book=True,
        random_opening_book=True,
        rng_seed=seed,
    ),
)
```

If using the real book is flaky, do not use it for the different-seed test. Use a controlled fake.

## Acceptance criteria

- No `assert True` seed tests remain.
- Different-seed behavior is tested non-vacuously.
- Same-seed and global-RNG-independence tests still pass.

---

# Problem 7: Special perft deferral must remain honest

## Current status

Start-position exact perft tests exist and should remain.

Special perft tests are mostly smoke tests, with exact known-count special positions deferred. This is acceptable for Fix 5 if documented honestly.

## Required behavior

- Keep exact start-position perft:
  - depth 1 = 20,
  - depth 2 = 400,
  - depth 3 = 8902,
  - depth 4 = 197281 marked slow.
- Do not describe `> 0` smoke tests as exact perft validation.
- Keep comments/docs saying exact special perft coverage is future work.
- Optional: add one known-count special perft test if easy, but do not block fast-suite cleanup on it.

## Acceptance criteria

- Perft test names/comments are honest.
- Exact special perft deferrals are documented.

---

# Problem 8: Documentation cleanup

Update docs only where needed.

Required doc points:

1. Fast suite must complete with:
   ```bash
   uv run python -m pytest -m "not slow"
   ```
2. Expensive engine-strength tests belong in the slow suite.
3. Online-learning candidates are memory-only.
4. Rejected candidates are not persisted.
5. `keep_rejected_candidate` is future work unless file-based candidate persistence is implemented.
6. Exact special perft coverage is future work where only smoke tests exist.

Do not over-document unrelated architecture.

---

# Final validation commands

Claude Code must run:

```bash
uv run python -m ruff check chess_game tests
uv run python -m mypy chess_game
uv run python -m pylint chess_game/texel --score=y
uv run python -m pytest -m "not slow"
```

Then:

```bash
uv run python -m pytest \
  tests/test_ai_quiescence_production.py \
  tests/test_search_terminal_scores.py \
  tests/test_perft.py \
  tests/test_loss.py \
  tests/test_spsa.py \
  tests/test_position_db.py \
  tests/test_collect.py \
  tests/test_online_learning.py \
  tests/test_validate.py \
  tests/test_tune.py \
  tests/test_opening_book.py \
  -m "not slow" -q
```

Then:

```bash
uv run python -m pytest -m slow
```

If the slow suite is too slow, document the limitation. Do not let slow tests contaminate the fast suite.

---

# Acceptance criteria

Fix 5 is complete only when:

1. Ruff passes.
2. mypy passes.
3. Texel Pylint passes or remains acceptably high.
4. `pytest -m "not slow"` completes reliably.
5. The known hanging depth-3 test is slow-marked or rewritten:
   ```text
   tests/test_ai_white_improvements3.py::test_depth3_avoids_b4_when_path_blocked
   ```
6. Any remaining depth-heavy fast tests are slow-marked or rewritten.
7. Collection tests prove weights propagation.
8. Collection tests prove max-move `"draw"` stores `0.5`.
9. Collection tests prove max-move `"discard"` stores no positions.
10. Collection tests prove draw outcome behavior.
11. Collection tests prove seed reproducibility.
12. PositionDB tests assert `total`, `count`, and `mean`.
13. Old JSONL duplicate aggregation is directly tested.
14. New JSONL direct load is directly tested.
15. Texel loss non-default `k` behavior is directly tested.
16. Texel loss `k=` compatibility is directly tested.
17. Opening-book same-seed behavior is tested.
18. Opening-book different-seed behavior is tested non-vacuously.
19. Opening-book global RNG independence is tested.
20. No vacuous assertions such as `assert True` remain in these Fix 5 areas.
21. Special perft smoke tests are honestly labeled.
22. Exact special perft deferrals are documented.
23. Targeted tests pass.
24. Slow tests are isolated from fast tests.

---

# Notes for Claude Code

## Prioritize hard blockers

Fix Ruff and the fast suite first. If those fail, the patch cannot be accepted.

## Keep this patch small

Do not add engine features. Do not refactor the whole search.

## Use monkeypatches

Collection and opening-book seed tests should use controlled fakes. Online-learning tests should use mocked expensive pieces.

## Avoid test theater

Do not write tests that only prove a config field was set when the test name claims behavior.

## Preserve compatibility

Do not break existing PositionDB JSONL files, CLI usage, or public Texel APIs.
