# replies10.md

# Replies to Claude Code on TEXEL_FIX5

Your understanding is correct: **Fix 5 is a final acceptance cleanup patch**, not a feature patch. The main deliverable is still:

```bash
uv run python -m pytest -m "not slow"
```

It must complete reliably. The other requirements are about removing weak tests, proving behavior directly, and keeping the Texel/PositionDB/opening-book compatibility tests meaningful.

---

## 1. Current state verification

Yes. Start with **Phase 0 baseline validation**.

Do not assume the current state based on the previous review or the previous commit. Run:

```bash
uv run python -m ruff check chess_game tests
uv run python -m mypy chess_game
uv run python -m pylint chess_game/texel --score=y
uv run python -m pytest -m "not slow" -vv
```

Record the current failures. If Ruff already passes, Phase 1 becomes validation-only. If Ruff still fails, fix it.

The fast-suite hang point may have changed, so identify the current first slow/hanging test from the actual run.

---

## 2. Ruff failure status

Treat Phase 1 as:

```text
Run Ruff. If it fails, fix it. If it passes, record that it is clean.
```

If `initial_size` was already removed by the TEXEL_FIX4 auto-fix, do not do anything else for that item.

Do not add `# noqa` or suppress Ruff. The expected result is:

```bash
uv run python -m ruff check chess_game tests
```

passes cleanly.

---

## 3. Fast-suite hanging workflow

Use option **B first, then A**:

1. Confirm whether `tests/test_ai_white_improvements3.py::test_depth3_avoids_b4_when_path_blocked` still hangs or runs slowly.
2. If it still performs depth-3 strategic search and is slow, mark it `@pytest.mark.slow`.
3. Re-run the fast suite and continue iteratively.

Given the previous review, I expect that test should be marked slow unless it has already been rewritten into a cheap helper-level test.

Use these thresholds:

```text
Individual non-slow test >2 seconds: consider rewrite or slow mark.
Individual non-slow test >5 seconds: almost certainly mark slow unless there is a strong reason.
Depth-3+ full-root get_best_move() strategic tests: slow by default unless proven fast.
Whole fast suite target: <150 seconds, but reliable completion is the hard requirement.
```

---

## 4. Collection tests: replace or augment?

Use option **A plus selective B**:

- Replace tests whose names claim behavior but only assert config construction.
- Keep pure config-construction tests only if their names clearly say they are config tests.
- Add behavior tests for the actual collection behavior.

For example, this kind of test is acceptable only if named as a config test:

```python
def test_collection_options_accepts_draw_max_move_result():
    opts = CollectionOptions(max_move_result="draw")
    assert opts.max_move_result == "draw"
```

But this is **not** acceptable:

```python
def test_collect_games_draw_outcome_is_half():
    opts = CollectionOptions(max_move_result="draw")
    assert opts.max_move_result == "draw"
```

because the name claims behavior that is not tested.

The Fix 5 intent is to eliminate test theater. Behavior tests must prove behavior.

---

## 5. Collection test monkeypatching approach

Use a layered approach:

### For weights propagation

Monkeypatch `get_best_move()` and capture the `BestMoveOptions` passed by collection.

That is the cleanest way to prove:

```text
CollectionOptions.weights -> BestMoveOptions.weights
```

### For max-move draw/discard behavior

Prefer testing the helper that turns a played game into DB entries, if such a helper exists.

If not, monkeypatch `_play_game()` to return controlled `GameRecord` values and test the collection wrapper that stores results into `PositionDatabase`.

Use a fake/minimal DB only if that makes the assertion clearer. It is also acceptable to use a real temporary `PositionDatabase` because it is fast.

### For draw terminal outcome

Use a controlled `GameRecord(outcome=0.5)` only if the test name says it is testing persistence of a draw record.

If the test name says collection detects/stores draw terminal outcomes, then monkeypatch terminal-state/game-playing logic so collection actually reaches a draw result.

### For seed reproducibility

Use mocked deterministic behavior. Do not run real self-play.

Recommended split:

```text
get_best_move monkeypatch: weights propagation
_play_game monkeypatch: max-move draw/discard and seed reproducibility at collection-wrapper level
real PositionDatabase: verify stored outcomes and counts
```

---

## 6. Mock library choice

Use whichever is already idiomatic in the file, but my preference is:

```text
pytest.monkeypatch for simple function/attribute replacement
unittest.mock for call assertions, spies, or complex mocks
```

So:

- Use `monkeypatch.setattr(...)` for replacing `get_best_move`, `_play_game`, `optimize`, `mean_squared_error`, etc.
- Use `unittest.mock.Mock()` when you need to assert call count, arguments, or call order.

Do not switch the whole test style just for consistency. Keep tests readable and direct.

---

## 7. PositionDB stats tests: file creation

Use option **A: hand-create JSONL files in each test using `tmp_path`**.

That is the clearest and most direct compatibility test.

Example:

```python
path = tmp_path / "positions.jsonl"
path.write_text(
    "\n".join(
        [
            json.dumps({"pos": fen, "outcome": 1.0}),
            json.dumps({"pos": fen, "outcome": 0.5}),
            json.dumps({"pos": fen, "outcome": 0.0}),
        ]
    )
    + "\n",
    encoding="utf-8",
)

db = PositionDB.load(path)
stats = db.get_stats(fen)

assert stats is not None
assert stats.count == 3
assert stats.total == pytest.approx(1.5)
assert stats.mean == pytest.approx(0.5)
```

Use raw/hand-authored JSONL because the point is compatibility with on-disk formats, not round-tripping the current writer.

Use fixtures only if repeated boilerplate gets excessive.

---

## 8. Texel loss `k` parameter API

Check the current `mean_squared_error()` signature before editing.

The intended compatibility target is:

```python
mean_squared_error(pairs, weights, k=some_k)
```

and:

```python
mean_squared_error(pairs, weights, opts=LossOptions(k=some_k))
```

If the current public API uses `opts=`, use `opts=`. Do not invent `options=` unless it already exists.

If `k=` is currently supported, keep it and test it.

If `k=` was accidentally removed, restore it if low-risk, because earlier specs explicitly asked for backward compatibility with `k=`.

The direct compatibility test should look like:

```python
mse_k_kwarg = mean_squared_error(pairs, weights, k=some_k)
mse_opts = mean_squared_error(pairs, weights, opts=LossOptions(k=some_k))

assert mse_k_kwarg == pytest.approx(mse_opts)
```

The non-default `k` behavior test should use a nonzero-eval FEN, for example:

```text
4k3/8/8/8/8/8/8/4KQ2 w - - 0 1
```

with outcome `0.5`:

```python
pairs = [(fen_white_up_queen, 0.5)]

mse_default = mean_squared_error(pairs, weights, k=DEFAULT_K)
mse_other = mean_squared_error(pairs, weights, k=DEFAULT_K * 2)

assert mse_default != pytest.approx(mse_other)
```

Do not use the starting position for this test. Its eval may be close to zero, making `k` effects invisible.

---

## 9. Opening-book seed tests: controlled setup

Use option **A or C**:

```text
A) Monkeypatch the opening-book path to return controlled candidates
C) Create a minimal fake book object for testing
```

Do **not** use the real book for the different-seed test. The real book can be flaky because different seeds may still pick the same move.

Do **not** monkeypatch `random.choice()` globally unless there is no cleaner hook.

Preferred approach:

1. Monkeypatch the book loader or book object used by `get_best_move()`.
2. Return a fake book with multiple legal candidate moves.
3. Ensure `find_book_move_random()` uses the seeded random path or receives the effect of `rng_seed`.
4. Pick two seeds known to select different moves.
5. Assert:

```python
assert move_seed_a != move_seed_b
```

The test should exercise this public path if possible:

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

Same-seed and global-RNG-independence tests can also use the fake book to avoid flakiness.

---

## 10. Perft smoke-test naming convention

Use option **B**, optionally with docstring wording from **D**.

Do **not** add a new `@pytest.mark.smoke` marker unless the project already uses one. New markers create more marker policy maintenance.

Keep these tests in the fast suite if they are genuinely fast.

Naming/docstring convention:

```python
def test_special_position_en_passant_smoke_not_exact_perft() -> None:
    """Smoke test only; exact known-count en-passant perft is future work."""
```

or:

```python
def test_en_passant_move_generation_smoke() -> None:
    """Smoke test, not exact perft validation."""
```

The key is honesty:

- `> 0` or “legal moves exist” is a smoke test.
- Exact node counts are perft validation.

Do not mark smoke tests slow unless they are slow.

---

## 11. Phase 2 iteration time budget

The target remains:

```text
Whole fast suite: under 150 seconds
Individual fast test: preferably under 2 seconds
Individual fast test over 5 seconds: mark slow or rewrite unless strongly justified
```

The fast suite does not have to be tiny, but it must be reliable and useful for development.

---

## 12. Documentation updates

Do not create a large new documentation file unless useful.

Preferred:

- Update `docs/TEXEL_TUNING.md` only if candidate persistence / `keep_rejected_candidate` is not already clear.
- Update `docs/ENGINE_SEARCH_NOTES.md` only if fast/slow policy or perft deferral is not already clear.
- Update README only if the test commands or slow-suite policy are missing.

A `docs/TEXEL_FIX5_COMPLETION_REPORT.md` is optional. It is useful only if Claude Code wants to document exactly what changed and what was deferred. Do not let a completion report substitute for passing tests.

---

# Answers to your assumptions

| Assumption | Answer |
|---|---|
| Starting point is TEXEL_FIX4 completion state | Run Phase 0 to verify. Do not assume. |
| TEXEL_FIX4 collection tests need replacement/enhancement | Correct. Behavior tests are required. |
| Fast suite target still <=150s | Correct. Completion is mandatory. |
| No feature work | Correct. Strict cleanup/acceptance patch. |
| No breaking changes | Correct. Preserve PositionDB JSONL, CLI usage, and public Texel APIs. |

---

# Recommended implementation order

Use this order:

1. Run Phase 0 validation.
2. Fix Ruff if still failing.
3. Mark the known hanging depth-3 strategic test slow if still applicable.
4. Iterate the fast suite until `pytest -m "not slow"` completes.
5. Fix collection behavior tests.
6. Fix PositionDB raw stats compatibility tests.
7. Fix Texel loss `k` tests.
8. Fix opening-book seed tests.
9. Verify perft smoke-test honesty.
10. Update docs only where needed.
11. Run final validation commands.

The hard acceptance gates are:

```bash
uv run python -m ruff check chess_game tests
uv run python -m mypy chess_game
uv run python -m pylint chess_game/texel --score=y
uv run python -m pytest -m "not slow"
```
