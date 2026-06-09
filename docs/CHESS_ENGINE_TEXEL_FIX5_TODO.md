# CHESS_ENGINE_TEXEL_FIX5_TODO.md

## Implementation checklist

This TODO is for the Fix 5 final acceptance patch.

Keep this patch narrow. Do **not** implement make/unmake search, bitboards, true Zobrist hashing, NNUE, broad search rewrites, or new chess heuristics.

---

# Phase 0: Baseline and hard blockers

## 0.1 Run validation commands

- [ ] Run Ruff:
  - [ ] `uv run python -m ruff check chess_game tests`
- [ ] Run mypy:
  - [ ] `uv run python -m mypy chess_game`
- [ ] Run Texel Pylint:
  - [ ] `uv run python -m pylint chess_game/texel --score=y`
- [ ] Run full fast suite:
  - [ ] `uv run python -m pytest -m "not slow" -vv`

## 0.2 Record blockers

- [ ] Confirm Ruff failure, if still present:
  - [ ] `tests/test_online_learning.py:636:9 F841 initial_size`
- [ ] Confirm the current first hanging/slow fast test.
- [ ] Specifically check:
  - [ ] `tests/test_ai_white_improvements3.py::test_depth3_avoids_b4_when_path_blocked`
- [ ] Continue iterating until the full fast suite completes.

---

# Phase 1: Fix Ruff

## 1.1 Fix unused variable

- [ ] Open `tests/test_online_learning.py`.
- [ ] Find unused local variable:
  - [ ] `initial_size`
- [ ] Remove it or replace it with a real assertion.
- [ ] Do not suppress with `# noqa`.

## 1.2 Validate

- [ ] Run:
  - [ ] `uv run python -m ruff check chess_game tests`
- [ ] Confirm Ruff passes.

---

# Phase 2: Make full fast suite complete

## 2.1 Mark known hanging depth-3 test slow

- [ ] Open `tests/test_ai_white_improvements3.py`.
- [ ] Find:
  - [ ] `test_depth3_avoids_b4_when_path_blocked`
- [ ] Mark it:
  - [ ] `@pytest.mark.slow`
- [ ] Add/import `pytest` if needed.
- [ ] Optionally add comment:
  - [ ] depth-heavy strategic regression; excluded from fast suite.

## 2.2 Iteratively run fast suite

- [ ] Run:
  - [ ] `uv run python -m pytest -m "not slow" -vv`
- [ ] If it hangs/slows badly, identify the current test.
- [ ] If the test is depth-heavy/full-search/engine-strength:
  - [ ] mark it slow.
- [ ] If the test can be rewritten cheaply:
  - [ ] lower depth,
  - [ ] use deterministic mode,
  - [ ] use smaller tactical position,
  - [ ] test helper-level invariant.
- [ ] Repeat until:
  - [ ] `uv run python -m pytest -m "not slow"` completes.

## 2.3 Validate fast suite

- [ ] Run:
  - [ ] `uv run python -m pytest -m "not slow"`
- [ ] Record approximate runtime.
- [ ] Confirm it completes reliably.

---

# Phase 3: Strengthen collection tests

## 3.1 Remove config-only behavior tests

- [ ] Search `tests/test_collect.py` for tests that claim behavior but only assert config fields.
- [ ] Rewrite those tests to prove actual behavior.
- [ ] Do not keep tests that only do:
  - [ ] `assert opts.max_move_result == "draw"`
  - [ ] `assert opts.max_move_result == "discard"`
  - [ ] similar config-only checks.

## 3.2 Test weights propagation

- [ ] Monkeypatch `get_best_move`.
- [ ] Capture the `BestMoveOptions` passed by collection code.
- [ ] Configure `CollectionOptions(weights=custom_weights)`.
- [ ] Assert captured options contain the same weights.

## 3.3 Test max-move draw behavior

- [ ] Use controlled/mocked game that hits max move limit.
- [ ] Configure `max_move_result="draw"`.
- [ ] Assert recorded outcome is `0.5`.
- [ ] Assert expected positions are stored.

## 3.4 Test max-move discard behavior

- [ ] Use controlled/mocked game that hits max move limit.
- [ ] Configure `max_move_result="discard"`.
- [ ] Assert no positions are stored.

## 3.5 Test terminal draw outcome

- [ ] Mock or construct a draw terminal state.
- [ ] Assert outcome is recorded as `0.5`.

## 3.6 Test invalid max_move_result

- [ ] Confirm invalid value raises `ValueError`.

## 3.7 Test seed reproducibility

- [ ] Use mocked deterministic behavior.
- [ ] Same `CollectionOptions(seed=...)` should produce same recorded data.
- [ ] Avoid full self-play.

## 3.8 Preserve slow markers

- [ ] Ensure real self-play collection tests are marked:
  - [ ] `@pytest.mark.slow`

---

# Phase 4: Strengthen PositionDB tests

## 4.1 Duplicate aggregation direct stats

- [ ] Add same FEN with outcomes:
  - [ ] `1.0`
  - [ ] `0.5`
  - [ ] `0.0`
- [ ] Use `db.get_stats(fen)`.
- [ ] Assert:
  - [ ] `stats.count == 3`
  - [ ] `stats.total == pytest.approx(1.5)`
  - [ ] `stats.mean == pytest.approx(0.5)`

## 4.2 Old JSONL duplicate aggregation

Create hand-authored old-format JSONL:

```json
{"pos": "fen", "outcome": 1.0}
{"pos": "fen", "outcome": 0.5}
{"pos": "fen", "outcome": 0.0}
```

- [ ] Load with `PositionDB.load(path)`.
- [ ] Use `db.get_stats(fen)`.
- [ ] Assert:
  - [ ] `stats.count == 3`
  - [ ] `stats.total == pytest.approx(1.5)`
  - [ ] `stats.mean == pytest.approx(0.5)`

## 4.3 New JSONL direct load

Create hand-authored new-format JSONL:

```json
{"pos": "fen", "total": 3.0, "count": 4}
```

- [ ] Load with `PositionDB.load(path)`.
- [ ] Use `db.get_stats(fen)`.
- [ ] Assert:
  - [ ] `stats.count == 4`
  - [ ] `stats.total == pytest.approx(3.0)`
  - [ ] `stats.mean == pytest.approx(0.75)`

## 4.4 Round trip

- [ ] Save DB with aggregated stats.
- [ ] Reload.
- [ ] Assert exact count/total/mean preserved.

## 4.5 Empty DB

- [ ] Keep or strengthen existing empty DB tests.

---

# Phase 5: Fix Texel loss k tests

## 5.1 Remove weak k tests

- [ ] Search `tests/test_loss.py` for `k` tests.
- [ ] Remove assertions that only prove non-negative MSE.
- [ ] Remove vacuous assertions like:
  - [ ] `assert mse_a != mse_b or abs(...) < ...`

## 5.2 Add non-default k changes MSE test

Use nonzero-eval FEN:

```text
4k3/8/8/8/8/8/8/4KQ2 w - - 0 1
```

- [ ] Create pairs:
  - [ ] `[(fen_white_up_queen, 0.5)]`
- [ ] Compute:
  - [ ] `mse_default = mean_squared_error(pairs, weights, k=DEFAULT_K)`
  - [ ] `mse_other = mean_squared_error(pairs, weights, k=DEFAULT_K * 2)`
- [ ] Assert:
  - [ ] `mse_default != pytest.approx(mse_other)`

## 5.3 Add k= compatibility test

- [ ] Compute:
  - [ ] `mse_k_kwarg = mean_squared_error(pairs, weights, k=some_k)`
  - [ ] `mse_opts = mean_squared_error(pairs, weights, opts=LossOptions(k=some_k))`
- [ ] Assert:
  - [ ] `mse_k_kwarg == pytest.approx(mse_opts)`

If the public parameter is `options=` instead of `opts=`, use the actual supported spelling.

## 5.4 Preserve perspective tests

- [ ] White material advantage positive.
- [ ] Black material advantage negative.
- [ ] Side-to-move does not flip White-relative sign.

---

# Phase 6: Fix opening-book seed tests

## 6.1 Remove vacuous seed assertions

- [ ] Search `tests/test_opening_book.py` for:
  - [ ] `assert True`
  - [ ] weak seed assertions
  - [ ] `len(moves_found) >= 1`
- [ ] Replace with behavior assertions.

## 6.2 Same-seed behavior

- [ ] Keep/add test proving same seed returns same book move.

## 6.3 Different-seed behavior under controlled setup

- [ ] Monkeypatch/fake opening-book path used by `get_best_move`.
- [ ] Provide multiple legal candidate moves.
- [ ] Choose seeds known to select different moves.
- [ ] Assert:
  - [ ] `move_seed_a != move_seed_b`

## 6.4 Global RNG independence

- [ ] Keep/add test proving seeded book selection is stable regardless of previous global RNG state.

## 6.5 Use real public path where possible

Prefer:

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

- [ ] If testing a helper directly, confirm it is the helper used by `get_best_move`.

---

# Phase 7: Keep special perft deferral honest

## 7.1 Preserve exact start-position perft

- [ ] depth 1 = 20.
- [ ] depth 2 = 400.
- [ ] depth 3 = 8902.
- [ ] depth 4 = 197281 marked slow.

## 7.2 Ensure smoke tests are named honestly

- [ ] Special tests that only assert `> 0` or legal moves exist should be named/commented as smoke tests.
- [ ] Do not present smoke tests as exact perft validation.

## 7.3 Document exact special perft deferral

- [ ] Add/update comment or docs:
  - [ ] exact known-count special perft positions are future work.

## 7.4 Optional

- [ ] Add one known-count special perft test if easy.
- [ ] Do not block fast-suite cleanup on this.

---

# Phase 8: Documentation updates

## 8.1 README / docs

Update only as needed:

- [ ] Fast suite command:
  - [ ] `uv run python -m pytest -m "not slow"`
- [ ] Slow suite command:
  - [ ] `uv run python -m pytest -m slow`
- [ ] Engine-strength regressions belong in the slow suite.

## 8.2 Texel docs

Update `docs/TEXEL_TUNING.md` if not already clear:

- [ ] candidates are memory-only,
- [ ] rejected candidates are not persisted,
- [ ] `keep_rejected_candidate` is future work unless file-based persistence exists.

## 8.3 Perft docs/comments

- [ ] Smoke tests are not exact special perft validation.
- [ ] Exact special perft coverage is future work.

---

# Phase 9: Final validation

## 9.1 Static checks

Run:

- [ ] `uv run python -m ruff check chess_game tests`
- [ ] `uv run python -m mypy chess_game`
- [ ] `uv run python -m pylint chess_game/texel --score=y`

## 9.2 Full fast suite

Run:

- [ ] `uv run python -m pytest -m "not slow"`

This must complete.

## 9.3 Targeted tests

Run:

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

- [ ] Confirm targeted tests pass.

## 9.4 Slow tests

Run:

- [ ] `uv run python -m pytest -m slow`

If too slow:

- [ ] Document runtime limitation.
- [ ] Confirm slow tests are isolated from fast tests.

---

# Phase 10: Completion criteria

This patch is complete only when:

- [ ] Ruff passes.
- [ ] mypy passes.
- [ ] Texel Pylint passes or remains acceptably high.
- [ ] `pytest -m "not slow"` completes reliably.
- [ ] Known hanging test is slow-marked or rewritten:
  - [ ] `tests/test_ai_white_improvements3.py::test_depth3_avoids_b4_when_path_blocked`
- [ ] Any remaining depth-heavy fast tests are slow-marked or rewritten.
- [ ] Collection tests prove weights propagation.
- [ ] Collection tests prove max-move `"draw"` stores `0.5`.
- [ ] Collection tests prove max-move `"discard"` stores no positions.
- [ ] Collection tests prove draw outcome behavior.
- [ ] Collection tests prove seed reproducibility.
- [ ] PositionDB tests assert `total`, `count`, and `mean`.
- [ ] Old JSONL duplicate aggregation is directly tested.
- [ ] New JSONL direct load is directly tested.
- [ ] Texel loss non-default `k` behavior is directly tested.
- [ ] Texel loss `k=` compatibility is directly tested.
- [ ] Opening-book same-seed behavior is tested.
- [ ] Opening-book different-seed behavior is tested non-vacuously.
- [ ] Opening-book global RNG independence is tested.
- [ ] No vacuous assertions such as `assert True` remain in these Fix 5 areas.
- [ ] Special perft smoke tests are honestly labeled.
- [ ] Exact special perft deferrals are documented.
- [ ] Targeted tests pass.
- [ ] Slow tests are isolated from fast tests.

---

# Notes for Claude Code

## Fix hard blockers first

Ruff and the fast suite are the acceptance gates.

## Do not refactor broadly

No new architecture work.

## Use controlled tests

Monkeypatch/fake collection and opening-book behavior. Do not rely on real self-play or real book randomness for fast behavioral tests.

## Do not write test theater

A test that only checks config construction is not a behavior test.

## Preserve compatibility

Do not break PositionDB JSONL compatibility or public Texel APIs.
