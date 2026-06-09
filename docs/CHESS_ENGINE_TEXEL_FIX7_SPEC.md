# CHESS_ENGINE_TEXEL_FIX7_SPEC.md

## Purpose

This document specifies a narrow **Fix 7 final test-reliability patch** for the chess engine's Texel/search/test reliability work.

Fix 6 got several acceptance items closer:

- Ruff passes with dev dependencies.
- mypy passes with dev dependencies.
- Texel Pylint is clean.
- Targeted Fix 6 tests pass.
- `tests/test_test_runtime_markers_integration.py` is now slow-marked.
- README documents dev dependency setup.

However, the latest review still found hard blockers:

1. The full fast suite still does **not** complete reliably as one command:
   ```bash
   uv run --extra dev python -m pytest -m "not slow"
   ```
2. The fast suite appears to pass in chunks, which suggests state leakage, teardown interaction, signal/alarm leakage, subprocess lifecycle issues, global RNG mutation, or similar full-suite interaction.
3. `tests/test_collect.py` still contains behavior-named tests that only assert configuration fields.
4. PositionDB old/new JSONL direct compatibility tests still do not fully assert raw `count`, `total`, and `mean`.
5. Texel loss `k` tests still do not directly prove that changing `k` changes MSE or that `k=` matches `opts=LossOptions(k=...)`.
6. Opening-book seed tests still contain a vacuous `assert True`.
7. Special perft deferrals must remain honest.
8. Dev-extra validation commands must remain documented.

The engine code is close. This patch should focus on **full-suite reliability and replacing weak tests with real behavior tests**.

---

## Hard scope boundaries

### In scope

- Make the full fast suite pass reliably as one command.
- Investigate and fix state leakage or teardown issues that only appear when the whole fast suite runs together.
- Keep runtime-marker meta-tests slow-marked.
- Strengthen collection behavior tests.
- Strengthen PositionDB JSONL raw stats tests.
- Strengthen Texel loss `k` tests.
- Strengthen opening-book seed tests.
- Keep dev-extra validation commands documented.
- Keep special perft deferrals honest.
- Run final validation.

### Out of scope

Do **not** implement:

- make/unmake search,
- bitboards,
- true Zobrist hashing,
- NNUE/neural evaluation,
- large `ai.py` decomposition,
- broad search rewrites,
- new chess heuristics,
- new engine-strength features.

This is a final test-reliability and test-quality patch only.

---

# Required final outcome

The patch is complete only when these commands pass from a clean checkout with dev dependencies:

```bash
uv run --extra dev python -m ruff check chess_game tests
uv run --extra dev python -m mypy chess_game
uv run --extra dev python -m pylint chess_game/texel --score=y
uv run --extra dev python -m pytest -m "not slow"
```

Targeted tests must also pass:

```bash
uv run --extra dev python -m pytest \
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

Slow tests should be run separately:

```bash
uv run --extra dev python -m pytest -m slow
```

If the slow suite is too slow, document that limitation. Do not let slow tests contaminate the fast suite.

---

# Problem 1: Full fast suite still times out as one command

## Current evidence

The latest review found:

```bash
uv run --extra dev python -m pytest -m "not slow"
```

still timed out.

However, split chunks of the collected suite passed:

```text
First collected block: 713 passed, 29 deselected in 28.93s
Remaining collected block: 322 passed, 3 deselected in 19.72s
```

This suggests the issue may not be one simple slow test. It may be a full-suite interaction.

## Likely root causes to inspect

Investigate:

1. Signal/alarm tests:
   - `signal.signal`
   - `signal.alarm`
   - timeout tests
   - tests that monkeypatch signal handlers
   - tests that fail to restore alarms or handlers

2. Global RNG mutation:
   - `random.seed(...)`
   - opening-book seed tests
   - self-play seed tests
   - tests that assume global RNG state

3. Subprocess lifecycle:
   - pytest subprocess tests
   - process handles not closed
   - hanging subprocess output pipes
   - tests that call pytest from pytest

4. Background work:
   - lingering threads
   - timers
   - async tasks
   - Textual/TUI/event-loop cleanup

5. Monkeypatch leakage:
   - manual monkeypatches not using `monkeypatch`
   - `mock.patch(...).start()` without stop
   - module-level mutation not restored

6. Temporary filesystem/state leakage:
   - global files
   - shared cache
   - persistent opening-book state
   - global transposition table or evaluation cache

## Required investigation workflow

Run the full fast suite with tools that help identify the hang:

```bash
uv run --extra dev python -m pytest -m "not slow" -vv
```

If it times out without clear output, use:

```bash
uv run --extra dev python -m pytest -m "not slow" -vv --tb=short
```

Use targeted isolation:

```bash
uv run --extra dev python -m pytest tests/<suspect_file>.py -m "not slow" -q
uv run --extra dev python -m pytest tests/<suspect_file_a>.py tests/<suspect_file_b>.py -m "not slow" -q
```

If needed, use collection order bisection:

```bash
uv run --extra dev python -m pytest --collect-only -q -m "not slow"
```

then run contiguous chunks until the interaction pair/group is found.

## Acceptance criteria

- The full fast suite completes as one command:
  ```bash
  uv run --extra dev python -m pytest -m "not slow"
  ```
- The fix is not just “run tests in chunks.”
- Any discovered state leak is fixed or the offending test is slow-marked if it is inherently integration/runtime-heavy.
- The runtime-marker meta-test file remains slow-marked or is otherwise cheap/static.

---

# Problem 2: Runtime-marker meta-tests must stay isolated

## Current status

`tests/test_test_runtime_markers_integration.py` has been marked slow, which is the right direction.

## Required behavior

Keep it out of the fast suite.

The file may use subprocess/collection checks in the slow suite, but it must not block:

```bash
uv run --extra dev python -m pytest -m "not slow"
```

## Important pytest behavior

If every test in the file is deselected by `-m "not slow"`, pytest may exit with code 5 for that file-only command:

```bash
uv run --extra dev python -m pytest tests/test_test_runtime_markers_integration.py -m "not slow" -q
```

That is acceptable as long as the full fast suite passes.

Do not force fake passing tests into that file just to avoid file-only exit code 5.

## Acceptance criteria

- Runtime-marker meta-tests do not run in the fast suite.
- Full fast suite passes.
- Runtime-marker meta-tests pass when run as slow tests:
  ```bash
  uv run --extra dev python -m pytest tests/test_test_runtime_markers_integration.py -m slow -q
  ```

---

# Problem 3: Collection tests still do not prove behavior

## Current problem

`tests/test_collect.py` still contains tests with behavior-oriented names that only assert config fields.

Unacceptable pattern:

```python
def test_collect_games_max_move_result_draw() -> None:
    """max_move_result='draw' should treat timeout games as draws."""
    opts = CollectionOptions(max_move_result="draw")
    assert opts.max_move_result == "draw"
```

That is only a config-construction test.

## Required behavior tests

Rewrite or add tests proving:

1. `CollectionOptions.weights` is passed into `BestMoveOptions` through the actual collection path.
2. Max-move result `"draw"` produces/stores outcome `0.5`.
3. Max-move result `"discard"` stores no positions or returns `None`, depending on current API.
4. Terminal draw outcome is recorded as `0.5`.
5. Invalid `max_move_result` raises `ValueError`.
6. `CollectionOptions(seed=...)` produces reproducible recorded output under a controlled mocked scenario.
7. Real full self-play collection tests remain slow-marked.

## Required testing style

Use controlled monkeypatches/fakes, not real self-play.

### Weights propagation

Monkeypatch `chess_game.texel.collect.get_best_move`, then call the actual collection path that invokes it, such as `_play_game()` or `collect_games()`.

Capture the `BestMoveOptions` argument and assert:

```python
captured_options.weights is custom_weights
```

Do not only assert:

```python
opts.weights is custom_weights
```

### Max-move draw

If `_play_game()` returns `GameRecord | None`, test:

```python
record = _play_game(options)
assert record is not None
assert record.outcome == 0.5
assert len(record.positions) > 0
```

If the collection wrapper stores game records directly into `PositionDB`, test:

```python
db = collect_games(options)
stats = db.get_stats(some_fen)
assert stats is not None
assert stats.mean == pytest.approx(0.5)
```

### Max-move discard

If `_play_game()` handles discard:

```python
record = _play_game(options)
assert record is None
```

If `collect_games()` handles discard:

```python
db = collect_games(options)
assert len(db) == 0
```

### Terminal draw

If the test directly creates `GameRecord(outcome=0.5)`, name it as a persistence test. If the test claims terminal draw detection, it must exercise the terminal draw path.

### Seed reproducibility

Use mocked deterministic move selection so the same seed produces identical recorded DB/output.

Do not use real random self-play.

## Acceptance criteria

- No behavior-named collection test only checks config construction.
- Weights propagation is proven through actual collection code.
- Max-move draw/discard behavior is directly tested.
- Seed reproducibility is directly tested.
- Tests remain fast and deterministic.

---

# Problem 4: PositionDB old/new JSONL raw stats tests are incomplete

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
stats = db.get_stats(fen)
assert stats is not None
assert stats.count == 3
assert stats.total == pytest.approx(1.5)
assert stats.mean == pytest.approx(0.5)
```

### Old JSONL duplicate aggregation

Create hand-authored old-format JSONL using `tmp_path`:

```json
{"pos": "fen", "outcome": 1.0}
{"pos": "fen", "outcome": 0.5}
{"pos": "fen", "outcome": 0.0}
```

Load:

```python
db = PositionDB.load(path)
```

Assert raw stats:

```python
stats = db.get_stats(fen)
assert stats is not None
assert stats.count == 3
assert stats.total == pytest.approx(1.5)
assert stats.mean == pytest.approx(0.5)
```

Do not rely only on `all_pairs()`.

### New JSONL direct load

Create hand-authored new-format JSONL:

```json
{"pos": "fen", "total": 3.0, "count": 4}
```

Load:

```python
db = PositionDB.load(path)
```

Assert:

```python
stats = db.get_stats(fen)
assert stats is not None
assert stats.count == 4
assert stats.total == pytest.approx(3.0)
assert stats.mean == pytest.approx(0.75)
```

Do not create this test by saving a `PositionDB`. That only tests round-trip behavior.

## Acceptance criteria

- Old JSONL duplicate aggregation directly checks `count`, `total`, and `mean`.
- New JSONL direct load uses hand-authored JSONL and directly checks stats.
- Round-trip tests remain but do not substitute for compatibility tests.

---

# Problem 5: Texel loss k tests still do not prove behavior

## Current issue

`mean_squared_error()` supports:

```python
mean_squared_error(pairs, weights, k=some_k)
mean_squared_error(pairs, weights, opts=LossOptions(k=some_k))
```

The tests must prove both:

1. Changing `k` changes MSE for a nonzero-eval position.
2. The `k=` API matches the `opts=LossOptions(k=...)` API.

## Required tests

### Non-default k changes MSE

Use a nonzero-eval FEN:

```text
4k3/8/8/8/8/8/8/4KQ2 w - - 0 1
```

Pair it with draw outcome:

```python
pairs = [(fen_white_up_queen, 0.5)]
```

Then assert:

```python
mse_default = mean_squared_error(pairs, weights, k=DEFAULT_K)
mse_other = mean_squared_error(pairs, weights, k=DEFAULT_K * 2)

assert mse_default != pytest.approx(mse_other)
```

If this exact FEN is invalid under the current parser, use another simple legal nonzero-eval FEN. Do not use `STARTING_FEN`.

### k= compatibility

Actually call both APIs:

```python
mse_k_kwarg = mean_squared_error(pairs, weights, k=1.5)
mse_opts = mean_squared_error(pairs, weights, opts=LossOptions(k=1.5))

assert mse_k_kwarg == pytest.approx(mse_opts)
```

Do not only assert non-negative MSE.

## Acceptance criteria

- No non-proving `k` tests remain.
- Non-default `k` sensitivity is directly tested.
- `k=` compatibility is directly tested.

---

# Problem 6: Opening-book seed test still contains vacuous assertion

## Current issue

`tests/test_opening_book.py` still contains logic like:

```python
if move_seed_42_run1 is not None or move_seed_99 is not None:
    assert True, "Seed mechanism is working (moves selected from book)"
```

This must be removed.

## Required tests

1. Same seed returns same move.
2. Different seeds return different moves under a controlled multi-candidate setup.
3. Seeded result is independent of prior global RNG state.

## Recommended approach

Use a fake/monkeypatched opening-book path used by `get_best_move()`.

Do not rely on the real bundled book for the different-seed test.

A good test should:

- provide multiple legal candidate moves,
- choose seeds known to select different candidates,
- call the public `get_best_move()` path where possible,
- assert:

```python
assert move_seed_a != move_seed_b
```

## Acceptance criteria

- No `assert True` remains in opening-book seed tests.
- Different-seed behavior is non-vacuously tested.
- Same-seed and global-RNG-independence tests remain.

---

# Problem 7: Global RNG mutation should be considered

## Current issue

Opening-book seeded randomness currently appears to call:

```python
random.seed(options.rng_seed)
```

inside `get_best_move()` or its opening-book path.

That mutates global RNG state. It may contribute to full-suite order sensitivity.

## Required action

At minimum:

- investigate whether this affects full-suite reliability,
- ensure tests that depend on randomness use local seeded randomness or restore global RNG state.

Preferred future-safe implementation:

```python
rng = random.Random(options.rng_seed)
```

and pass/use that local RNG in book selection instead of mutating module-global random state.

This should be done only if it is a small, localized change. Do not broaden the patch into a full opening-book refactor.

## Acceptance criteria

- Seeded opening-book tests do not leave global RNG in a surprising state.
- If global RNG mutation remains, tests must restore/contain it.
- Full fast suite passes.

---

# Problem 8: Signal/alarm tests should restore state

## Current issue

Because split chunks pass but the full suite times out, signal/alarm state leakage is a likely suspect.

## Required action

Search tests for:

```bash
grep -R "signal.alarm\\|signal.signal" tests
```

For any test that manipulates signal handlers or alarms:

- use `try/finally`,
- restore the previous handler,
- call `signal.alarm(0)` in cleanup,
- prefer pytest fixtures that restore state automatically.

## Acceptance criteria

- Signal/alarm tests do not leak alarm state or handlers.
- Full fast suite passes.

---

# Problem 9: Dev-extra validation docs should remain current

## Required behavior

README or current docs must show:

```bash
uv sync --extra dev
```

or direct commands:

```bash
uv run --extra dev python -m pytest -m "not slow"
```

This must remain true after Fix 7.

Do not worry about every historical TODO/spec file containing old commands. Current README/current docs should be correct.

---

# Problem 10: Special perft deferrals remain acceptable

Start-position exact perft tests should remain.

Special tests that only check legal moves or `> 0` should be labeled as smoke tests. Exact special perft counts can remain future work.

Do not block Fix 7 on adding new exact special perft positions unless it is trivial.

---

# Final validation

Run:

```bash
uv run --extra dev python -m ruff check chess_game tests
uv run --extra dev python -m mypy chess_game
uv run --extra dev python -m pylint chess_game/texel --score=y
uv run --extra dev python -m pytest -m "not slow"
```

Run targeted tests:

```bash
uv run --extra dev python -m pytest \
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
uv run --extra dev python -m pytest -m slow
```

If the slow suite is too slow, document the limitation.

---

# Acceptance criteria

Fix 7 is complete only when:

1. Ruff passes with dev dependencies.
2. mypy passes with dev dependencies.
3. Texel Pylint passes or remains acceptably high.
4. Full fast suite completes reliably as one command.
5. Runtime-marker meta-tests remain isolated from the fast suite.
6. Any full-suite state leak is fixed or contained.
7. Collection tests prove weights propagation through actual collection path.
8. Collection tests prove max-move `"draw"` stores `0.5`.
9. Collection tests prove max-move `"discard"` stores no positions.
10. Collection tests prove seed reproducibility.
11. PositionDB old JSONL duplicate aggregation directly checks `count`, `total`, and `mean`.
12. PositionDB new JSONL direct load uses hand-authored JSONL and directly checks stats.
13. Texel loss non-default `k` behavior is directly tested.
14. Texel loss `k=` compatibility is directly tested.
15. Opening-book seed tests contain no vacuous `assert True`.
16. Opening-book different-seed behavior is non-vacuously tested.
17. Dev-extra validation docs remain current.
18. Special perft smoke tests remain honestly labeled.
19. Targeted tests pass.
20. Slow tests are isolated from fast tests.

---

# Notes for Claude Code

## Do not broaden the patch

The engine is close. Avoid architecture and heuristic work.

## Fix full-suite reliability first

The highest-priority deliverable is the full fast suite completing as one command.

## Replace test theater

Behavior tests must exercise production paths or tightly scoped helpers that production uses.

## Watch global state

Full-suite failures often come from global RNG, signal handlers, subprocesses, or background threads.

## Preserve compatibility

Do not break PositionDB JSONL, CLI usage, or public Texel APIs.
