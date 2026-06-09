# CHESS_ENGINE_TEXEL_FIX6_SPEC.md

## Purpose

This document specifies a narrow **Fix 6 acceptance-hardening patch** for the chess engine's Texel/search/test reliability work.

Fix 5 got the engine and most targeted tests close to acceptance, but the latest review still found remaining blockers:

1. The full fast suite still does not complete when `tests/test_test_runtime_markers_integration.py` is included.
2. The validation commands in the docs/TODO are not reproducible in a clean checkout unless dev dependencies are installed.
3. `tests/test_collect.py` still contains behavior-named tests that only assert config construction or manually constructed records.
4. PositionDB tests still do not fully prove raw stats compatibility for old/new JSONL.
5. Texel loss `k` tests still do not directly prove non-default `k` changes MSE or `k=` compatibility.
6. Opening-book different-seed testing still contains a vacuous assertion.
7. Special perft deferrals must remain honest.

The engine code itself is close. This patch should focus on **test runtime, test quality, and validation-command reproducibility**.

---

## Hard scope boundaries

### In scope

- Make the full fast suite pass reliably.
- Fix or slow-mark `tests/test_test_runtime_markers_integration.py`.
- Update docs/validation commands for dev extras.
- Rewrite weak collection tests into real behavior tests.
- Strengthen PositionDB raw stats tests.
- Strengthen Texel loss `k` tests.
- Strengthen opening-book seed tests.
- Preserve special perft honesty.
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

This is an acceptance-hardening patch only.

---

# Required final outcome

The patch is complete only when the following commands pass from a clean checkout after installing dev dependencies, or when using `--extra dev` directly.

Preferred clean-checkout workflow:

```bash
uv sync --extra dev
uv run python -m ruff check chess_game tests
uv run python -m mypy chess_game
uv run python -m pylint chess_game/texel --score=y
uv run python -m pytest -m "not slow"
```

Equivalent direct workflow:

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

Run slow tests separately:

```bash
uv run --extra dev python -m pytest -m slow
```

If the slow suite is too slow, document the limitation. Do not let slow tests contaminate the fast suite.

---

# Problem 1: Full fast suite blocked by runtime-marker meta-tests

## Current evidence

The latest review found:

```bash
uv run --extra dev python -m pytest -m "not slow" -q
```

timed out.

But this command completed:

```bash
uv run --extra dev python -m pytest \
  -m "not slow" \
  --ignore=tests/test_test_runtime_markers_integration.py \
  -q
```

with approximately:

```text
1035 passed, 154 deselected in 42.39s
```

This strongly indicates that `tests/test_test_runtime_markers_integration.py` is the remaining fast-suite blocker.

The file itself may pass alone, but it is still too heavy and brittle for the fast suite because it repeatedly spawns broad pytest collection subprocesses.

## Required fix

Choose one of these acceptable approaches:

### Preferred: mark the whole marker meta-test file slow

At the top of `tests/test_test_runtime_markers_integration.py`:

```python
import pytest

pytestmark = pytest.mark.slow
```

This is acceptable because marker integration tests are meta-tests, not product behavior. They should not block normal fast development.

### Alternative: rewrite as static checks

Replace subprocess pytest calls with static checks that inspect test files or AST.

Acceptable static checks:

- verify expensive test files contain `@pytest.mark.slow`,
- verify known slow integration files are slow-marked,
- verify marker configuration exists in `pyproject.toml`.

### Avoid

Do not leave broad subprocess calls in the fast suite, even if they are `--collect-only`.

Do not run real engine tests from a marker meta-test in the fast suite.

## Acceptance criteria

- `uv run --extra dev python -m pytest tests/test_test_runtime_markers_integration.py -m "not slow" -q` should either:
  - deselect all tests quickly if the file is marked slow, or
  - complete quickly if rewritten as static checks.
- `uv run --extra dev python -m pytest -m "not slow"` completes reliably.
- The non-marker fast suite remains healthy.

---

# Problem 2: Validation commands need dev dependency clarity

## Current problem

In a clean checkout, commands like:

```bash
uv run python -m ruff check chess_game tests
uv run python -m mypy chess_game
uv run python -m pylint chess_game/texel --score=y
uv run python -m pytest -m "not slow"
```

can fail with:

```text
No module named ruff
No module named mypy
No module named pylint
No module named pytest
```

because these tools are dev dependencies.

## Required fix

Update README and relevant docs to show one of these workflows.

### Preferred workflow

```bash
uv sync --extra dev

uv run python -m ruff check chess_game tests
uv run python -m mypy chess_game
uv run python -m pylint chess_game/texel --score=y
uv run python -m pytest -m "not slow"
```

### Direct workflow

```bash
uv run --extra dev python -m ruff check chess_game tests
uv run --extra dev python -m mypy chess_game
uv run --extra dev python -m pylint chess_game/texel --score=y
uv run --extra dev python -m pytest -m "not slow"
```

## Acceptance criteria

- Docs explain how to run validation from a clean checkout.
- Final report/notes use dev-extra-aware commands.
- No one has to infer why `ruff`, `mypy`, `pylint`, or `pytest` are missing.

---

# Problem 3: Collection tests still do not prove behavior

## Current problem

`tests/test_collect.py` still contains tests whose names claim behavior but only assert config values.

Example of an unacceptable behavior test:

```python
def test_collect_games_max_move_result_draw() -> None:
    """max_move_result='draw' should treat timeout games as draws."""
    opts = CollectionOptions(max_move_result="draw")
    assert opts.max_move_result == "draw"
```

A config test may assert config construction, but its name must say that it is a config test. A behavior test must prove behavior.

## Required behavior tests

Rewrite or add tests proving:

1. `CollectionOptions.weights` is passed into `BestMoveOptions`.
2. Max-move result `"draw"` stores `0.5` for positions from the game.
3. Max-move result `"discard"` stores no positions.
4. Terminal draw outcome is recorded as `0.5`.
5. Invalid `max_move_result` raises `ValueError`.
6. `CollectionOptions(seed=...)` produces reproducible recorded data under controlled mocked behavior.
7. Real full self-play collection tests remain marked slow.

## Recommended implementation approach

Use controlled monkeypatches, not full self-play.

### Weights propagation

Monkeypatch `chess_game.texel.collect.get_best_move`.

Then call the actual collection path that invokes `get_best_move`, such as `_play_game()` or `collect_games()`, depending on the current implementation.

Capture the `BestMoveOptions` argument and assert:

```python
captured_options.weights is custom_weights
```

Do not only assert:

```python
opts.weights is custom_weights
```

### Max-move draw/discard

Prefer testing the real `_play_game()` max-move behavior if available and fast.

For example:

- monkeypatch `get_best_move()` to return a legal move sequence or repeated legal moves,
- set `max_moves` low,
- set `max_move_result="draw"` or `"discard"`,
- assert returned record/outcome or stored DB stats.

If `_play_game()` returns `GameRecord | None`:

```python
record = _play_game(options)
assert record is not None
assert record.outcome == 0.5
assert len(record.positions) > 0
```

For discard:

```python
record = _play_game(options)
assert record is None
```

or if collection wrapper handles discard:

```python
db = collect_games(options)
assert len(db) == 0
```

### Terminal draw

If terminal draw detection is in `_play_game()`, monkeypatch board/draw helpers as needed and assert the returned record has `outcome == 0.5`.

If the test only verifies that a `GameRecord(outcome=0.5)` is stored, name it as a persistence test, not terminal-draw collection behavior.

### Seed reproducibility

Use a controlled mocked path so same seed produces identical recorded DB/output.

Do not rely on real self-play randomness.

## Acceptance criteria

- No behavior-named collection test only checks config construction.
- Weights propagation is tested through the actual collection call path.
- Max-move draw/discard behavior is directly tested.
- Seed reproducibility is directly tested.
- Fast collection tests are deterministic and quick.

---

# Problem 4: PositionDB raw stats compatibility tests incomplete

## Current problem

PositionDB implementation is mostly correct, and `get_stats()` exists, but tests still do not fully prove raw stats compatibility.

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

Create a hand-authored old-format JSONL file:

```json
{"pos": "fen", "outcome": 1.0}
{"pos": "fen", "outcome": 0.5}
{"pos": "fen", "outcome": 0.0}
```

Load it with `PositionDB.load(path)`, then assert:

```python
stats = db.get_stats(fen)
assert stats is not None
assert stats.count == 3
assert stats.total == pytest.approx(1.5)
assert stats.mean == pytest.approx(0.5)
```

Do not rely only on `all_pairs()`.

### New JSONL direct load

Create a hand-authored new-format JSONL file:

```json
{"pos": "fen", "total": 3.0, "count": 4}
```

Load it and assert:

```python
stats = db.get_stats(fen)
assert stats is not None
assert stats.count == 4
assert stats.total == pytest.approx(3.0)
assert stats.mean == pytest.approx(0.75)
```

Do not create this file by saving a `PositionDB`; that only tests round-trip behavior.

### Round trip

Keep the round-trip test, but do not let it substitute for direct compatibility tests.

## Acceptance criteria

- Old JSONL duplicate aggregation directly checks `count`, `total`, and `mean`.
- New JSONL direct load uses a hand-authored file and directly checks stats.
- Round-trip tests still pass.
- Existing JSONL compatibility is preserved.

---

# Problem 5: Texel loss k tests still do not prove behavior

## Current problem

`mean_squared_error()` supports both:

```python
mean_squared_error(pairs, weights, k=some_k)
```

and:

```python
mean_squared_error(pairs, weights, opts=LossOptions(k=some_k))
```

but tests still do not directly prove:

1. changing `k` changes MSE,
2. `k=` and `opts=LossOptions(k=...)` are compatible.

Tests using `STARTING_FEN` and only checking non-negative values are not sufficient.

## Required tests

### Non-default k changes MSE

Use a position with a nonzero evaluation and a draw outcome.

Recommended FEN:

```text
4k3/8/8/8/8/8/8/4KQ2 w - - 0 1
```

White is up a queen. Pair it with draw outcome:

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

### k= compatibility

Actually call both APIs:

```python
some_k = 1.5
mse_k_kwarg = mean_squared_error(pairs, weights, k=some_k)
mse_opts = mean_squared_error(pairs, weights, opts=LossOptions(k=some_k))

assert mse_k_kwarg == pytest.approx(mse_opts)
```

Do not merely assert non-negative MSE.

## Acceptance criteria

- No vacuous or non-proving `k` tests remain.
- Non-default `k` changes MSE for a nonzero-eval position.
- `k=` compatibility is directly tested.

---

# Problem 6: Opening-book seed test is still vacuous

## Current problem

`tests/test_opening_book.py` still contains logic like:

```python
if move_seed_42_run1 is not None or move_seed_99 is not None:
    assert True, "Seed mechanism is working (moves selected from book)"
```

This assertion is vacuous and must be removed.

## Required behavior

Test opening-book seed behavior under a controlled multi-candidate setup.

Required tests:

1. Same seed returns same move.
2. Different seeds return different moves under a controlled setup.
3. Seeded result is independent of prior global RNG state.

## Preferred approach

Use a fake or monkeypatched opening-book object/path, not the real book.

The real book may not contain enough reliable diversity for a deterministic different-seed assertion.

### Example approach

- Monkeypatch the book lookup used by `get_best_move()`.
- Return multiple legal candidate moves from the starting position.
- Use seeds known to select different candidates.
- Call the public path if possible.

Example desired assertion:

```python
move_seed_a = get_best_move(board, depth=1, book_options=options_a)
move_seed_b = get_best_move(board, depth=1, book_options=options_b)

assert move_seed_a != move_seed_b
```

If the current implementation uses global `random.seed()`, this test can still pass, but consider future cleanup to use local RNG instead.

## Acceptance criteria

- No `assert True` remains in opening-book seed tests.
- Different-seed behavior is tested non-vacuously.
- Same-seed behavior remains tested.
- Global RNG independence remains tested.

---

# Problem 7: Special perft deferral honesty

## Current status

Start-position exact perft tests exist. Special perft tests are mostly smoke tests, and exact known-count special positions are deferred.

This is acceptable.

## Required behavior

Keep test names/comments honest:

- exact start-position perft remains exact,
- special `>0`/legal-move tests are labeled smoke tests,
- exact known-count special perft coverage is documented as future work.

Do not block Fix 6 on adding new exact special perft positions unless it is trivial.

---

# Problem 8: Documentation updates

Update only what is necessary.

## Required docs

Update README and/or relevant docs to clarify dev dependency setup:

```bash
uv sync --extra dev
```

or use direct commands:

```bash
uv run --extra dev python -m pytest -m "not slow"
```

Update docs if needed for:

- fast vs slow suite,
- marker meta-tests being slow,
- memory-only rejected candidates,
- `keep_rejected_candidate` future-work status,
- special perft smoke-test deferral.

Do not create a large completion report unless it is useful.

---

# Final validation

Claude Code must run:

```bash
uv run --extra dev python -m ruff check chess_game tests
uv run --extra dev python -m mypy chess_game
uv run --extra dev python -m pylint chess_game/texel --score=y
uv run --extra dev python -m pytest -m "not slow"
```

Then run targeted tests:

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

Then run slow tests separately:

```bash
uv run --extra dev python -m pytest -m slow
```

If the slow suite is too slow, document the limitation.

---

# Acceptance criteria

Fix 6 is complete only when:

1. `uv run --extra dev python -m ruff check chess_game tests` passes.
2. `uv run --extra dev python -m mypy chess_game` passes.
3. `uv run --extra dev python -m pylint chess_game/texel --score=y` passes or remains acceptably high.
4. `uv run --extra dev python -m pytest -m "not slow"` completes reliably.
5. `tests/test_test_runtime_markers_integration.py` no longer blocks the fast suite.
6. Docs clearly explain dev dependency setup or use `--extra dev` commands.
7. Collection tests prove weights propagation through the actual collection path.
8. Collection tests prove max-move `"draw"` stores `0.5`.
9. Collection tests prove max-move `"discard"` stores no positions.
10. Collection tests prove seed reproducibility.
11. PositionDB old JSONL duplicate aggregation directly checks `count`, `total`, and `mean`.
12. PositionDB new JSONL direct load uses hand-authored JSONL and directly checks stats.
13. Texel loss non-default `k` behavior is directly tested.
14. Texel loss `k=` compatibility is directly tested.
15. Opening-book seed tests contain no vacuous `assert True`.
16. Opening-book different-seed behavior is non-vacuously tested.
17. Special perft smoke tests remain honestly labeled.
18. Targeted tests pass.
19. Slow tests are isolated from fast tests.

---

# Notes for Claude Code

## Fix the fast suite first

The marker meta-test file is the current likely blocker. Resolve that before refining smaller test quality items.

## Do not broaden the patch

The engine code is close. Avoid architecture or heuristic work.

## Prefer static/slow marker meta-tests

Marker integration tests are not product behavior. They should not repeatedly collect the full suite inside the fast suite.

## Use controlled fakes

Collection and opening-book tests should use controlled fakes/monkeypatches rather than real self-play or real book randomness.

## Do not write test theater

A test that only checks that an option field exists is not a behavior test.

## Preserve compatibility

Do not break PositionDB JSONL compatibility, CLI usage, or public Texel APIs.
