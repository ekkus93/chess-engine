# CHESS_ENGINE_TEXEL_FIX4_SPEC.md

## Purpose

This document specifies a narrow **Fix 4 final cleanup patch** for the chess engine's Texel/search/test reliability work.

Fix 3 improved parts of the implementation, but the latest review still found blockers:

1. The full fast test suite still does not complete.
2. `tests/test_test_runtime_markers_integration.py` is portable now, but still too expensive for the fast suite because it spawns pytest subprocesses.
3. Online-learning behavior is not adequately tested.
4. Collection tests still mostly verify configuration construction rather than actual behavior.
5. PositionDB tests do not directly verify `total`, `count`, and `mean`.
6. Texel loss `k` tests are weak and do not truly verify `k=` backward compatibility.
7. Opening-book different-seed tests are weak and do not prove different seeds can affect random selection.
8. Special perft exact-count coverage remains mostly deferred, which is acceptable only if documented honestly.
9. Final validation is still incomplete because `pytest -m "not slow"` does not pass/complete.

This patch is intended to finish the remaining cleanup. It should not introduce new engine architecture.

---

## Hard scope boundaries

### In scope

- Make the full fast suite complete.
- Fix or slow-mark expensive runtime-marker integration tests.
- Mark remaining expensive engine-strength tests as slow.
- Strengthen online-learning tests using mocks/monkeypatches.
- Validate `OnlineLearningConfig.validation_fraction`.
- Prove online-learning acceptance/rejection/threshold/backup/cache behavior.
- Strengthen collection tests with controlled mocked behavior.
- Strengthen PositionDB compatibility and aggregation tests.
- Add direct Texel loss `k` behavior and `k=` compatibility tests.
- Fix weak opening-book seed tests.
- Keep special perft deferrals honest.
- Run final validation commands.

### Out of scope

Do **not** implement:

- make/unmake search,
- bitboards,
- true Zobrist hashing,
- NNUE/neural evaluation,
- large `ai.py` decomposition,
- broad search refactors,
- new chess-strength heuristics unrelated to the cleanup,
- large feature additions.

This is a final cleanup/test quality patch, not a new engine patch.

---

# Required final outcome

The patch is complete only when these commands pass and the fast suite completes reliably:

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
  -m "not slow" -q
```

Slow tests should be isolated:

```bash
uv run python -m pytest -m slow
```

It is acceptable for the slow suite to take longer, but slow tests must not contaminate the fast suite.

---

# Problem 1: Fast suite still does not complete

## Current problem

The latest review found that:

```bash
uv run python -m pytest -m "not slow"
```

still times out.

The verbose run reached expensive search-regression tests such as:

```text
tests/test_ai_strategy4_regressions.py::test_search_rejects_rook_lift_that_drops_back_rank_safety
tests/test_ai_strategy8_regressions.py
```

and the full fast suite did not complete.

## Required behavior

The non-slow suite must complete reliably. A target of under 150 seconds is acceptable, but the hard requirement is completion.

## Required approach

Claude Code must iteratively run:

```bash
uv run python -m pytest -m "not slow" -vv
```

and for every slow/hanging non-slow test:

1. Classify it:
   - expensive engine-strength regression,
   - test bug,
   - candidate for helper-level rewrite.
2. If it is an engine-strength/depth-heavy regression test, mark it:
   ```python
   @pytest.mark.slow
   ```
3. If it can be fast, rewrite it:
   - lower depth,
   - smaller tactical position,
   - deterministic mode,
   - helper-level assertion,
   - no depth-3+ full root search unless proven fast.
4. Re-run until the full fast suite completes.

## Acceptance criteria

- `uv run python -m pytest -m "not slow"` completes.
- Expensive engine-strength tests are slow-marked.
- Meaningful coverage is preserved in slow tests or narrow fast helper tests.
- No slow or recursive subprocess tests remain in the fast suite.

---

# Problem 2: Runtime-marker integration tests are still too expensive

## Current problem

The hardcoded path was fixed, but this file still spawns pytest subprocesses:

```text
tests/test_test_runtime_markers_integration.py
```

Direct command:

```bash
uv run python -m pytest tests/test_test_runtime_markers_integration.py -m "not slow" -q
```

timed out during review.

It reached:

```text
tests/test_test_runtime_markers_integration.py::TestIntegrationTestMarkers::test_self_play_integration_tests_fast
```

before timing out.

## Required behavior

Runtime-marker tests must not dominate the fast suite. They should not run the full test suite from inside the fast suite.

## Acceptable fixes

Choose one or more:

### Option A: Mark expensive subprocess marker tests slow

If a test spawns pytest and runs more than a tiny collection-only check, mark it slow:

```python
@pytest.mark.slow
def test_self_play_integration_tests_fast(...):
    ...
```

### Option B: Rewrite as static checks

Preferred for fast tests:

- Parse test files.
- Check marker declarations.
- Check naming conventions.
- Avoid invoking full pytest.

### Option C: Use collect-only

If subprocess pytest is needed, keep it cheap:

```bash
python -m pytest tests/specific_file.py --collect-only -q
```

Do not run actual engine tests from inside the marker test.

## Acceptance criteria

- No runtime-marker test hardcodes local paths.
- `tests/test_test_runtime_markers_integration.py -m "not slow"` completes quickly or only slow tests are deselected.
- No fast marker test runs the full fast suite from inside pytest.
- The full fast suite completes.

---

# Problem 3: Online-learning behavior tests are insufficient

## Current problem

Implementation now appears to use:

```python
config.validation_fraction
config.validation_seed
config.require_validation_improvement
config.min_validation_mse_improvement
```

in behavior, which is good.

However, tests mostly verify configuration field existence or basic storage. They do not strongly prove online-learning acceptance/rejection behavior.

## Required behavior

Fast online-learning tests should mock/monkeypatch expensive pieces and prove control flow.

Do not run real SPSA or self-play in these fast tests.

## Required tests

Add or strengthen tests proving all of the following:

### Acceptance

Given mocked values:

```text
baseline_val_mse = 0.20
candidate_val_mse = 0.10
min_validation_mse_improvement = 0.0
require_validation_improvement = True
```

the candidate is accepted and active weights are saved.

### Rejection when worse

Given:

```text
baseline_val_mse = 0.20
candidate_val_mse = 0.25
```

the candidate is rejected and active weights are not overwritten.

### Rejection below threshold

Given:

```text
baseline_val_mse = 0.20
candidate_val_mse = 0.195
min_validation_mse_improvement = 0.01
```

the candidate is rejected because improvement is only `0.005`.

### Active weights preserved

When rejected:

- current active weights file remains unchanged,
- no cache invalidation occurs,
- no backup promotion occurs.

### Backup on acceptance

When accepted and an active weights file already exists:

- backup file is created,
- active weights are replaced by accepted candidate,
- cache invalidation occurs after successful save.

### Validation fraction

`config.validation_fraction` must actually influence train/validation split. Add a test that uses two different fractions and verifies different split sizes.

### Validation seed

`config.validation_seed` must actually influence deterministic split. Add a test proving same seed gives same split and different seed can change ordering/split contents.

### Too-small validation set

If `require_validation_improvement=True` and the validation split is too small:

- no promotion,
- active weights preserved.

### Unsafe/no-validation behavior

If `require_validation_improvement=False` is supported:

- test that explicit unsafe promotion works,
- document that it is unsafe.

If it is not supported, remove the option or document that it is intentionally unsupported.

## Validation fraction input validation

Add runtime validation for:

```text
0.0 <= validation_fraction < 1.0
```

Invalid fractions should raise `ValueError` or fail cleanly.

Suggested tests:

```text
validation_fraction = -0.1 -> ValueError
validation_fraction = 1.0 -> ValueError
validation_fraction = 1.5 -> ValueError
```

## Candidate persistence

Fix 4 should keep memory-only candidate behavior unless file-based candidates are already implemented.

Required documentation:

```text
Rejected candidates are memory-only and are not persisted in the current implementation.
keep_rejected_candidate is reserved for future file-based candidate persistence.
```

If `keep_rejected_candidate` remains in the config, tests should assert it does not accidentally create files in the memory-only implementation.

---

# Problem 4: Collection tests still do not prove behavior

## Current problem

Some collection tests now avoid no-op assertions, but they still mostly test config construction:

```python
assert opts.max_move_result == "draw"
```

That does not prove that max-move draw games store outcome `0.5`.

## Required behavior

Collection tests must use mocks/monkeypatches to prove actual behavior without expensive self-play.

## Required tests

Add fast tests proving:

1. `CollectionOptions.weights` is passed into `BestMoveOptions`.
2. Draw outcomes are stored as `0.5`.
3. Max-move result `"draw"` stores `0.5` for positions from the game.
4. Max-move result `"discard"` stores no positions.
5. Invalid `max_move_result` raises `ValueError`.
6. `CollectionOptions(seed=...)` produces reproducible behavior in a mocked deterministic scenario.
7. Real full self-play tests are marked slow.

## Guidance

Use monkeypatching.

Possible targets:

- monkeypatch `get_best_move`,
- monkeypatch `_play_game`,
- monkeypatch terminal/draw helpers,
- use a fake/minimal PositionDatabase,
- directly test helper functions if available.

Do not rely on full self-play in the fast suite.

## Acceptance criteria

- No collection test claims behavior while only asserting config construction.
- Max-move draw/discard behavior is actually tested.
- Weight propagation is actually tested.
- Seed reproducibility is actually tested.

---

# Problem 5: PositionDB tests are still not strong enough

## Current problem

PositionDB implementation is mostly correct, but tests do not directly verify `total` and `count`.

The TODO asked for:

```text
count == 3
total == 1.5
mean == 0.5
```

for duplicate outcomes `1.0`, `0.5`, `0.0`.

## Required tests

### Duplicate aggregation

Add same FEN with:

```text
1.0
0.5
0.0
```

Assert:

```python
stats.count == 3
stats.total == 1.5
stats.mean == 0.5
```

If internal stats are private, either:

- use a public accessor,
- add a small public accessor if appropriate,
- or inspect the internal map in tests if this is acceptable for persistence testing.

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
stats.total == 1.5
stats.mean == 0.5
```

### New JSONL direct load

Create hand-authored new-format JSONL:

```json
{"pos": "fen", "total": 3.0, "count": 4}
```

Load it and assert:

```python
stats.count == 4
stats.total == 3.0
stats.mean == 0.75
```

### Round trip

Save a DB with aggregated stats, reload, and verify exact stats.

### Empty DB

Keep empty DB tests.

## Acceptance criteria

- PositionDB tests prove stats, not just exported mean pairs.
- Old and new JSONL compatibility are directly tested.

---

# Problem 6: Texel loss `k` tests are weak

## Current problem

A test like:

```python
assert mse_k0_5 != mse_k2_0 or abs(mse_k0_5 - mse_k2_0) < 1e-12
```

is effectively vacuous. It always passes for normal float values.

Another backward-compatibility test does not actually call the old `k=` API.

## Required tests

### Non-default k changes loss

Use a nonzero-score position and an outcome where changing sigmoid steepness affects MSE.

Example structure:

```python
pairs = [(fen_with_white_material_advantage, 0.5)]
mse_default = mean_squared_error(pairs, weights, k=DEFAULT_K)
mse_other = mean_squared_error(pairs, weights, k=DEFAULT_K * 2)

assert mse_default != mse_other
```

Use `math.isclose(..., rel_tol=..., abs_tol=...)` if necessary, but the assertion must prove a real difference.

### Backward compatibility

Actually call both APIs:

```python
mse_k_kwarg = mean_squared_error(pairs, weights, k=some_k)
mse_options = mean_squared_error(pairs, weights, opts=LossOptions(k=some_k))
```

or if the parameter name is `options`:

```python
mse_options = mean_squared_error(pairs, weights, options=LossOptions(k=some_k))
```

Then assert:

```python
assert mse_k_kwarg == pytest.approx(mse_options)
```

If both `opts` and `options` are supported, test the supported public API and keep one spelling canonical.

## Acceptance criteria

- No vacuous `k` assertions remain.
- `k=` backward compatibility is directly tested.
- Non-default `k` behavior is directly tested.

---

# Problem 7: Opening-book seed tests are weak

## Current problem

Same-seed behavior is tested, but the different-seed test only asserts:

```python
assert len(moves_found) >= 1
```

That passes even if different seeds never affect the selected book move.

## Required behavior

Different-seed test must prove seed affects selection in a controlled scenario.

## Preferred approach

Monkeypatch/fake the opening book.

Use a controlled set of candidate moves and a deterministic random-choice path. Then assert:

```python
move_seed_1 != move_seed_2
```

for seeds known to produce different choices.

If exact different choices are hard to guarantee with Python RNG and candidate size, use a controlled fake that maps seed to index or expose the RNG object.

## Required tests

1. Same seed returns same book move.
2. Different seeds can return different book moves under controlled multi-candidate book setup.
3. Seeded opening-book behavior is independent of prior global random state.

## Acceptance criteria

- Different-seed test is not vacuous.
- The test exercises `get_best_move(... random_opening_book=True, rng_seed=...)` or a direct helper used by that code path.

---

# Problem 8: Special perft deferral must stay honest

## Current status

Special perft tests are labeled as smoke tests, and exact known-count special cases are mostly deferred.

This is acceptable for Fix 4, provided docs are clear.

## Required behavior

Do not call smoke tests “perft validation.”

Use names/comments like:

```text
special position smoke test
future work: exact known-count perft for this category
```

If easy, add one known-count special perft test, such as Kiwipete depth 1/2, but do not block the fast-suite cleanup on this.

## Acceptance criteria

- Start-position exact perft counts remain.
- Smoke tests are honestly labeled.
- Deferred exact special perft work is documented.

---

# Problem 9: Documentation cleanup

Update docs as needed:

```text
docs/TEXEL_TUNING.md
docs/ENGINE_SEARCH_NOTES.md
README.md
```

Required doc points:

1. Fast suite must pass with `pytest -m "not slow"`.
2. Expensive engine-strength regressions belong in the slow suite.
3. Online-learning candidate handling is memory-only.
4. `keep_rejected_candidate` is future work unless file-based candidates are implemented.
5. `validation_fraction`, `validation_seed`, `require_validation_improvement`, and `min_validation_mse_improvement` behavior is documented.
6. Special perft smoke tests are not exact known-count validation.
7. Future work remains:
   - make/unmake search,
   - true Zobrist hashing,
   - TT mate-score normalization,
   - broader exact special perft suite,
   - possible search module decomposition.

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
  -m "not slow" -q
```

And separately:

```bash
uv run python -m pytest -m slow
```

If the slow suite is too slow, document that. Do not let slow tests into the fast suite.

---

# Acceptance criteria

Fix 4 is complete only when:

1. `uv run python -m pytest -m "not slow"` completes reliably.
2. Runtime-marker integration tests are cheap or marked slow.
3. No fast test runs the full test suite from inside pytest.
4. Remaining expensive engine-strength tests are slow-marked or rewritten.
5. Online-learning tests prove accept/reject/threshold behavior.
6. Online-learning tests prove active weights are preserved on rejection.
7. Online-learning tests prove backup/cache behavior on acceptance.
8. `validation_fraction` is validated and tested.
9. `validation_seed` behavior is tested.
10. Collection tests prove actual draw/discard/weights/seed behavior.
11. PositionDB tests assert `total`, `count`, and `mean`.
12. PositionDB tests directly load old duplicate JSONL records.
13. PositionDB tests directly load new JSONL total/count records.
14. Texel loss tests directly prove non-default `k` changes loss.
15. Texel loss tests directly prove `k=` compatibility.
16. Opening-book seed tests prove different seeds can affect selection under controlled conditions.
17. Special perft smoke tests are honestly labeled, with exact-count deferrals documented.
18. Ruff passes.
19. mypy passes.
20. Pylint Texel passes or remains acceptably high.
21. Targeted tests pass.
22. Slow tests are isolated from the fast suite.

---

# Notes for Claude Code

## Keep this patch narrow

Do not use this patch to add new engine features.

## Fix the fast suite first

A clean fast suite is the main deliverable.

## Do not add weak tests

A test must fail if the behavior regresses.

## Use monkeypatches

Online learning and collection tests should use monkeypatches/mocks instead of real self-play or long SPSA runs.

## Be honest about deferrals

It is acceptable to defer exact special perft coverage if the docs say so clearly.
