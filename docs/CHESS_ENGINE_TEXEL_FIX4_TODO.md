# CHESS_ENGINE_TEXEL_FIX4_TODO.md

## Implementation checklist

This TODO is for the Fix 4 final cleanup patch.

The goal is to finish the remaining blockers from the Fix 3 review. Keep this patch narrow. Do **not** implement make/unmake search, bitboards, Zobrist hashing, NNUE, or broad search rewrites.

---

# Phase 0: Baseline and current failure inventory

## 0.1 Run validation commands

- [ ] Run Ruff:
  - [ ] `uv run python -m ruff check chess_game tests`
- [ ] Run mypy:
  - [ ] `uv run python -m mypy chess_game`
- [ ] Run Texel Pylint:
  - [ ] `uv run python -m pylint chess_game/texel --score=y`
- [ ] Run full fast suite:
  - [ ] `uv run python -m pytest -m "not slow" -vv`

## 0.2 Record current slow/hanging tests

- [ ] Record the first test where the fast suite hangs/slows badly.
- [ ] Continue iterating until the full fast suite completes.
- [ ] Pay special attention to:
  - [ ] `tests/test_test_runtime_markers_integration.py`
  - [ ] `tests/test_ai_strategy4_regressions.py`
  - [ ] `tests/test_ai_strategy8_regressions.py`
  - [ ] any depth-3+ `get_best_move()` tests still in the fast suite.

---

# Phase 1: Make runtime-marker tests cheap or slow

## 1.1 Inspect runtime-marker tests

- [ ] Open `tests/test_test_runtime_markers_integration.py`.
- [ ] List every test that spawns a pytest subprocess.
- [ ] Identify whether each subprocess is:
  - [ ] static/collect-only and cheap,
  - [ ] actually running engine tests,
  - [ ] running a broad test selection.

## 1.2 Fix expensive marker tests

For each expensive marker test, choose one:

- [ ] Rewrite it as a static file/AST/text check.
- [ ] Rewrite it to `pytest --collect-only`.
- [ ] Mark it `@pytest.mark.slow`.

Do **not** leave tests that run real engine tests from inside the fast suite.

## 1.3 Validate marker tests

Run:

```bash
uv run python -m pytest tests/test_test_runtime_markers_integration.py -m "not slow" -q
```

- [ ] Confirm it completes quickly.
- [ ] If slow tests are deselected, confirm that is intentional.

---

# Phase 2: Make full fast suite complete

## 2.1 Iterative fast-suite run

- [ ] Run:
  - [ ] `uv run python -m pytest -m "not slow" -vv`
- [ ] When it slows or hangs, identify the current test.
- [ ] Classify it:
  - [ ] expensive engine-strength regression,
  - [ ] test bug,
  - [ ] candidate for narrow rewrite.

## 2.2 Mark slow engine-strength tests

For depth-heavy/full-search regressions:

- [ ] Add `@pytest.mark.slow`.
- [ ] Add a brief comment if useful:
  - [ ] "Depth-heavy engine-strength regression; excluded from fast suite."
- [ ] Preserve the test in the slow suite.

## 2.3 Rewrite tests where better

If a test can be fast:

- [ ] Reduce depth.
- [ ] Use deterministic mode.
- [ ] Use a smaller tactical position.
- [ ] Assert a helper-level invariant.
- [ ] Avoid full root depth-3+ search.

## 2.4 Confirm completion

- [ ] Run:
  - [ ] `uv run python -m pytest -m "not slow"`
- [ ] Confirm it completes reliably.
- [ ] Record approximate runtime.

---

# Phase 3: Finish OnlineLearningConfig behavior

## 3.1 Validate validation_fraction

- [ ] Add validation for `validation_fraction`.
- [ ] Allow:
  - [ ] `0.0 <= validation_fraction < 1.0`
- [ ] Reject:
  - [ ] negative values,
  - [ ] `1.0`,
  - [ ] values greater than `1.0`.

Add tests:

- [ ] `validation_fraction=-0.1` raises.
- [ ] `validation_fraction=1.0` raises.
- [ ] `validation_fraction=1.5` raises.
- [ ] valid values are accepted.

## 3.2 Confirm config fields are actually used

- [ ] Confirm `config.validation_fraction` is used in split behavior.
- [ ] Confirm `config.validation_seed` is used in split behavior.
- [ ] Confirm `config.require_validation_improvement` controls whether improvement is required.
- [ ] Confirm `config.min_validation_mse_improvement` controls the minimum improvement threshold.
- [ ] Confirm `keep_rejected_candidate` is documented as future work for memory-only candidates, or implement file behavior.

## 3.3 Candidate behavior

Use memory-only candidates for this patch unless file-based behavior already exists.

- [ ] Document rejected candidates are not persisted.
- [ ] Document `keep_rejected_candidate` is reserved/future work if not implemented.
- [ ] Ensure rejected candidates never overwrite active weights.
- [ ] Ensure no unexpected candidate file is created.

---

# Phase 4: Strengthen online-learning tests

Use monkeypatching/mocking. Do not use expensive SPSA/self-play in fast tests.

## 4.1 Candidate accepted when validation improves

Mock:

```text
baseline_val_mse = 0.20
candidate_val_mse = 0.10
min_validation_mse_improvement = 0.0
require_validation_improvement = True
```

Assert:

- [ ] update returns accepted/success.
- [ ] active weights are saved/replaced.
- [ ] cache invalidation happens.
- [ ] backup is created if active weights existed.

## 4.2 Candidate rejected when validation worsens

Mock:

```text
baseline_val_mse = 0.20
candidate_val_mse = 0.25
```

Assert:

- [ ] update returns rejected/failure.
- [ ] active weights remain unchanged.
- [ ] cache invalidation does not happen.
- [ ] backup/promotion does not happen.

## 4.3 Candidate rejected below threshold

Mock:

```text
baseline_val_mse = 0.20
candidate_val_mse = 0.195
min_validation_mse_improvement = 0.01
```

Assert:

- [ ] rejected because improvement is insufficient.
- [ ] active weights remain unchanged.

## 4.4 Validation split tests

- [ ] Test `validation_fraction` changes split size.
- [ ] Test same `validation_seed` gives same split.
- [ ] Test different `validation_seed` can change split contents.
- [ ] Test too-small validation set does not promote when validation improvement is required.

## 4.5 Memory-only rejected candidates

- [ ] Test rejected candidates do not create a candidate file.
- [ ] Test `keep_rejected_candidate` does not accidentally create files in memory-only mode.
- [ ] If field is removed instead, update docs/tests accordingly.

## 4.6 Unsafe/no-validation behavior

If `require_validation_improvement=False` allows unsafe promotion:

- [ ] Add explicit test for unsafe promotion.
- [ ] Document this as unsafe.

If not supported:

- [ ] Remove or document unsupported behavior.

---

# Phase 5: Strengthen collection tests

## 5.1 Replace config-only behavior tests

Find tests that only assert config fields, for example:

```python
assert opts.max_move_result == "draw"
```

when the test name claims behavior.

- [ ] Rewrite them to assert actual collection behavior.
- [ ] Use monkeypatches/mocks.

## 5.2 Test weights propagation

- [ ] Monkeypatch `get_best_move`.
- [ ] Capture `BestMoveOptions`.
- [ ] Assert `CollectionOptions.weights` is passed through.

## 5.3 Test max-move draw behavior

- [ ] Use a controlled/mocked game that hits max move limit.
- [ ] Set `max_move_result="draw"`.
- [ ] Assert stored outcome is `0.5`.

## 5.4 Test max-move discard behavior

- [ ] Use a controlled/mocked game that hits max move limit.
- [ ] Set `max_move_result="discard"`.
- [ ] Assert no positions are stored.

## 5.5 Test draw outcome behavior

- [ ] Mock/construct a draw terminal state.
- [ ] Assert recorded outcome is `0.5`.

## 5.6 Test invalid max_move_result

- [ ] Confirm invalid value raises `ValueError`.

## 5.7 Test collection seed reproducibility

- [ ] Use mocked deterministic behavior.
- [ ] Same `CollectionOptions(seed=...)` produces same recorded data.
- [ ] Avoid full self-play.

## 5.8 Keep expensive collection tests slow

- [ ] Ensure real self-play collection tests are marked `@pytest.mark.slow`.

---

# Phase 6: Strengthen PositionDB tests

## 6.1 Duplicate aggregation direct stats

Add same FEN with outcomes:

```text
1.0
0.5
0.0
```

Assert:

- [ ] `stats.count == 3`
- [ ] `stats.total == 1.5`
- [ ] `stats.mean == 0.5`

If no public accessor exists:

- [ ] add one if appropriate, or
- [ ] inspect internal storage in tests.

## 6.2 Old JSONL duplicate aggregation

Create hand-authored old-format JSONL:

```json
{"pos": "fen", "outcome": 1.0}
{"pos": "fen", "outcome": 0.5}
{"pos": "fen", "outcome": 0.0}
```

Load and assert:

- [ ] `stats.count == 3`
- [ ] `stats.total == 1.5`
- [ ] `stats.mean == 0.5`

## 6.3 New JSONL direct load

Create hand-authored new-format JSONL:

```json
{"pos": "fen", "total": 3.0, "count": 4}
```

Load and assert:

- [ ] `stats.count == 4`
- [ ] `stats.total == 3.0`
- [ ] `stats.mean == 0.75`

## 6.4 Round trip

- [ ] Save aggregated stats.
- [ ] Reload.
- [ ] Assert exact stats preserved.

## 6.5 Empty DB

- [ ] Keep/strengthen empty DB tests.

---

# Phase 7: Fix Texel loss k tests

## 7.1 Remove vacuous k assertions

Search for assertions like:

```python
assert mse_a != mse_b or abs(mse_a - mse_b) < ...
```

- [ ] Replace with meaningful assertions.

## 7.2 Test non-default k changes MSE

Use nonzero-score position and outcome where sigmoid steepness affects loss.

Example:

```python
pairs = [(fen_with_white_material_advantage, 0.5)]
mse_default = mean_squared_error(pairs, weights, k=DEFAULT_K)
mse_other = mean_squared_error(pairs, weights, k=DEFAULT_K * 2)
assert mse_default != pytest.approx(mse_other)
```

- [ ] Ensure the test actually fails if `k` is ignored.

## 7.3 Test k= backward compatibility

Call both supported APIs:

```python
mse_k_kwarg = mean_squared_error(pairs, weights, k=some_k)
mse_opts = mean_squared_error(pairs, weights, opts=LossOptions(k=some_k))
```

or use `options=` if that is the supported parameter.

Assert:

- [ ] `mse_k_kwarg == pytest.approx(mse_opts)`

## 7.4 Preserve perspective tests

- [ ] White material advantage positive.
- [ ] Black material advantage negative.
- [ ] Side-to-move does not flip White-relative sign.

---

# Phase 8: Fix opening-book seed tests

## 8.1 Same seed

- [ ] Keep/add test that same seed gives same random book move.

## 8.2 Different seeds under controlled setup

The test must prove different seeds can affect selection.

- [ ] Use monkeypatch/fake opening book if needed.
- [ ] Provide multiple candidate moves.
- [ ] Choose seeds known to produce different choices.
- [ ] Assert the returned moves differ.

Do not use a vacuous assertion like:

```python
assert len(moves_found) >= 1
```

## 8.3 Global RNG independence

- [ ] Keep/add test proving seeded book choice is stable regardless of prior global RNG state.

## 8.4 Exercise real code path

- [ ] Prefer exercising `get_best_move(... random_opening_book=True, rng_seed=...)`.
- [ ] If testing helper directly, ensure it is the helper used by `get_best_move`.

---

# Phase 9: Keep special perft deferral honest

## 9.1 Preserve exact start-position perft

- [ ] depth 1 = 20.
- [ ] depth 2 = 400.
- [ ] depth 3 = 8902.
- [ ] depth 4 = 197281 marked slow.

## 9.2 Smoke-test naming

- [ ] Rename special tests that only assert `> 0` or legal moves exist as smoke tests.
- [ ] Do not call them exact perft validation.

## 9.3 Optional known-count special perft

If easy, add one known-count special position.

- [ ] Kiwipete shallow exact count, or
- [ ] simple promotion/en-passant known count.

Do not block the fast-suite cleanup on this if it becomes time-consuming.

## 9.4 Document deferral

- [ ] Document future work for exact known-count special perft coverage.

---

# Phase 10: Documentation updates

## 10.1 README

Update as needed:

- [ ] fast test command,
- [ ] slow test command,
- [ ] lint/type-check commands,
- [ ] note that engine-strength tests belong in slow suite.

## 10.2 Texel docs

Update `docs/TEXEL_TUNING.md`:

- [ ] memory-only candidate behavior,
- [ ] rejected candidates are not persisted,
- [ ] `keep_rejected_candidate` future-work status if applicable,
- [ ] `validation_fraction`,
- [ ] `validation_seed`,
- [ ] `require_validation_improvement`,
- [ ] `min_validation_mse_improvement`.

## 10.3 Search/test docs

Update `docs/ENGINE_SEARCH_NOTES.md` or test docs:

- [ ] fast vs slow suite policy,
- [ ] special perft smoke-test status,
- [ ] future exact special perft,
- [ ] future make/unmake,
- [ ] future true Zobrist hashing,
- [ ] future TT mate-score normalization.

---

# Phase 11: Final validation

## 11.1 Static checks

Run:

- [ ] `uv run python -m ruff check chess_game tests`
- [ ] `uv run python -m mypy chess_game`
- [ ] `uv run python -m pylint chess_game/texel --score=y`

## 11.2 Full fast suite

Run:

- [ ] `uv run python -m pytest -m "not slow"`

This must complete.

## 11.3 Targeted tests

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
  -m "not slow" -q
```

- [ ] Confirm targeted tests pass.

## 11.4 Slow tests

Run:

- [ ] `uv run python -m pytest -m slow`

If too slow:

- [ ] Document runtime limitations.
- [ ] Confirm slow tests are excluded from the fast suite.

---

# Phase 12: Completion criteria

This patch is complete only when:

- [ ] `pytest -m "not slow"` completes reliably.
- [ ] Runtime-marker integration tests are cheap or marked slow.
- [ ] No fast test runs the full suite from inside pytest.
- [ ] Remaining expensive engine-strength tests are slow-marked or rewritten.
- [ ] `validation_fraction` is validated.
- [ ] Online-learning accept/reject behavior is tested.
- [ ] Online-learning threshold rejection is tested.
- [ ] Active weights are preserved on rejection.
- [ ] Backup/cache behavior is tested on acceptance.
- [ ] Collection tests prove weights propagation.
- [ ] Collection tests prove max-move draw behavior.
- [ ] Collection tests prove max-move discard behavior.
- [ ] Collection tests prove draw outcome behavior.
- [ ] Collection tests prove seed reproducibility.
- [ ] PositionDB tests assert `total`, `count`, and `mean`.
- [ ] Old JSONL duplicate aggregation is directly tested.
- [ ] New JSONL direct load is directly tested.
- [ ] Texel loss non-default `k` behavior is directly tested.
- [ ] Texel loss `k=` compatibility is directly tested.
- [ ] Opening-book different-seed behavior is non-vacuously tested.
- [ ] Special perft smoke tests are honestly labeled.
- [ ] Exact special perft deferrals are documented.
- [ ] Ruff passes.
- [ ] mypy passes.
- [ ] Pylint Texel passes or remains acceptably high.
- [ ] Targeted tests pass.
- [ ] Slow tests are isolated from fast tests.

---

# Notes for Claude Code

## Prioritize the fast suite

Do this first. A hanging fast suite blocks acceptance regardless of other improvements.

## Use monkeypatches

Online-learning and collection behavior should be tested with controlled mocks, not real games or long SPSA runs.

## Avoid vacuous assertions

A test must be able to fail if behavior regresses.

## Keep API compatibility

Do not break existing PositionDB files, existing CLI commands, or public Texel APIs.

## Document deferrals clearly

Deferring exact special perft coverage is acceptable only if docs and test names are honest.
