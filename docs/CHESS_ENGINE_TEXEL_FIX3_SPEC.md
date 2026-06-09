# CHESS_ENGINE_TEXEL_FIX3_SPEC.md

## Purpose

This document specifies a narrow **Fix 3 cleanup patch** for the chess engine's Texel/search/test reliability work.

The previous Fix 2 patch improved the core engine code substantially, but the latest review found remaining blockers:

1. The full fast test suite still does not complete.
2. A runtime-marker integration test hardcodes `/home/phil/work/chess-engine`.
3. Online-learning configuration fields exist but are mostly ignored.
4. Some tests still contain weak assertions such as `assert len(db) >= 0`.
5. Collection tests do not strongly verify behavior.
6. PositionDB tests are incomplete/stale.
7. Random opening-book seed behavior is not directly tested.
8. Texel loss tests do not directly prove non-default `k` behavior.
9. Special perft tests are mostly smoke tests rather than known-count tests.

This patch should finish those blockers.

---

## Hard scope boundaries

### In scope

- Test runtime cleanup.
- Fix hardcoded test paths.
- Mark remaining expensive tests as slow or rewrite them.
- Complete online-learning config behavior.
- Add/strengthen online-learning tests.
- Remove weak/no-op assertions.
- Strengthen collection tests using mocks/monkeypatches.
- Strengthen PositionDB tests.
- Add random opening-book seed tests.
- Add direct Texel loss `k` compatibility tests.
- Improve special perft tests with known counts where practical, or explicitly defer complex cases.
- Keep docs accurate.

### Out of scope

Do **not** implement:

- make/unmake search,
- bitboards,
- Zobrist hashing,
- NNUE/neural evaluation,
- broad `ai.py` decomposition,
- large search rewrites,
- new chess heuristics unrelated to the remaining blockers.

This is a cleanup/completion patch, not a new engine architecture patch.

---

# Required final outcome

The patch is complete only when:

```bash
uv run python -m ruff check chess_game tests
uv run python -m mypy chess_game
uv run python -m pylint chess_game/texel --score=y
uv run python -m pytest -m "not slow"
```

all pass and the fast test suite completes in a reasonable time.

Targeted tests should also pass:

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

If slow tests are very slow, that is acceptable only if they are clearly marked slow and do not contaminate the fast suite.

---

# Problem 1: Fast suite still does not complete

## Current problem

`uv run python -m pytest -m "not slow"` still times out.

The previous known slow tests were handled:

```text
tests/test_ai_repetition_integration.py::test_repetition_sensitive_position_counts_change_root_choice
tests/test_ai_strategy15_regressions.py::TestQuiescenceDepth::test_quiescence_resolves_capture_chain
```

But other unmarked expensive tests remain.

Likely sources include depth-heavy tests in files such as:

```text
tests/test_ai_endgame1_regressions.py
tests/test_ai_endgame2_regressions.py
tests/test_ai_endgame_fix1_regressions.py
tests/test_ai_plan_fix_regressions.py
tests/test_ai_review_loop.py
tests/test_ai_strategy5_regressions.py
tests/test_ai_strategy6_regressions.py
tests/test_ai_strategy7_regressions.py
tests/test_ai_white_improvements3.py
tests/test_ai_search.py
tests/test_test_runtime_markers_integration.py
```

This list is not exhaustive. Claude Code must run the fast suite and identify the actual remaining slow tests.

## Required behavior

The non-slow suite must complete reliably.

For each slow non-slow test:

1. If it is a depth-heavy engine-strength regression test, mark it `@pytest.mark.slow`.
2. If it can be rewritten into a narrow fast unit test, do that instead.
3. Avoid full `get_best_move(... depth=3+)` searches in the fast suite unless the position is tiny and proven fast.
4. Prefer deterministic, low-depth, helper-level tests for fast suite.
5. Do not delete meaningful coverage; move expensive coverage into the slow suite.

## Acceptance criteria

- `uv run python -m pytest -m "not slow"` completes.
- Known expensive tests are marked slow or rewritten.
- Slow tests remain runnable with `uv run python -m pytest -m slow`.

---

# Problem 2: `test_test_runtime_markers_integration.py` hardcodes local path

## Current problem

`tests/test_test_runtime_markers_integration.py` hardcodes:

```python
cwd="/home/phil/work/chess-engine"
```

and opens:

```python
/home/phil/work/chess-engine/pyproject.toml
```

This makes the test non-portable. It fails anywhere the repo is not located at that exact path.

## Required fix

Use a dynamic repo root:

```python
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
```

Then use:

```python
cwd=REPO_ROOT
REPO_ROOT / "pyproject.toml"
```

## Additional guidance

Meta-tests that spawn pytest from inside pytest can be expensive. If these tests run real pytest subprocesses, either:

1. mark them `@pytest.mark.slow`, or
2. rewrite them to cheap static/collection-only checks.

Do not run the full test suite from inside the fast suite.

## Acceptance criteria

- No test hardcodes `/home/phil/work/chess-engine`.
- Runtime-marker integration tests are portable.
- Expensive subprocess pytest tests are slow-marked or rewritten.

---

# Problem 3: OnlineLearningConfig fields exist but are ignored

## Current problem

`OnlineLearningConfig` includes fields such as:

```python
require_validation_improvement: bool = True
min_validation_mse_improvement: float = 0.0
keep_rejected_candidate: bool = False
validation_fraction: float = 0.20
validation_seed: int = 0
```

but current code still uses hardcoded constants like:

```python
_VALIDATION_FRACTION = 0.20
_VALIDATION_SEED = 0
```

and ignores several config fields.

## Required behavior

Use the config fields.

### validation_fraction

Use:

```python
config.validation_fraction
```

when splitting train/validation data.

Validate it:

```text
0.0 <= validation_fraction < 1.0
```

If validation is required, `validation_fraction` must produce enough validation data.

### validation_seed

Use:

```python
config.validation_seed
```

for deterministic train/validation splitting.

The same DB and seed should produce the same split.

Different seeds may produce different splits.

### require_validation_improvement

If `True`, candidate weights may be promoted only if validation improves enough.

If `False`, candidate weights may be promoted without validation improvement, but this is intentionally unsafe and must be explicit.

### min_validation_mse_improvement

Candidate acceptance condition should be:

```python
candidate_val_mse <= baseline_val_mse - config.min_validation_mse_improvement
```

If the improvement is smaller than the threshold, reject.

### keep_rejected_candidate

If candidate files are persisted:

- `False`: remove rejected candidate file.
- `True`: keep rejected candidate file for inspection.

If candidates remain in memory only, either:

1. remove this field, or
2. document that it has no effect because rejected candidates are not persisted.

Prefer making it meaningful if candidate files already exist.

## Candidate behavior

Preferred:

```text
weights.candidate.json
weights.previous.json
weights.json
```

Flow:

1. Train candidate.
2. Save candidate to candidate path.
3. Validate candidate.
4. If accepted:
   - backup current active weights,
   - atomically promote candidate to active weights,
   - invalidate cache,
   - remove candidate unless configured to keep it.
5. If rejected:
   - active weights unchanged,
   - remove candidate unless `keep_rejected_candidate=True`.

If implementing file-based candidates is too invasive, keep candidate in memory, but document that explicitly and make tests match that behavior.

## Acceptance criteria

- No hardcoded validation fraction/seed are used in the online-learning path.
- All config fields either affect behavior or are removed/documented.
- Candidate promotion honors validation improvement and minimum improvement threshold.
- Rejected candidates do not overwrite active weights.
- Cache invalidation happens only after accepted promotion.

---

# Problem 4: Online-learning tests are incomplete

## Required tests

Add or strengthen tests for:

1. Candidate accepted when validation improves enough.
2. Candidate rejected when validation worsens.
3. Candidate rejected when improvement is below `min_validation_mse_improvement`.
4. Active weights preserved on rejection.
5. Backup created on acceptance when active weights exist.
6. Cache invalidated only after accepted promotion.
7. `validation_fraction` is used.
8. `validation_seed` is used.
9. Too-small validation set does not promote by default when `require_validation_improvement=True`.
10. Unsafe/no-validation promotion requires explicit config if supported.
11. `keep_rejected_candidate` behavior is tested if file-based candidates are implemented.

Use monkeypatching/mocking where needed. Do not rely on expensive SPSA or full self-play in fast tests.

---

# Problem 5: Weak collection tests

## Current problem

`tests/test_collect.py` still contains weak assertions such as:

```python
assert len(db) >= 0
```

This always passes and proves nothing.

## Required behavior

Remove all no-op assertions.

Every collection test must verify a meaningful invariant.

## Required collection tests

Add fast unit tests using monkeypatches/mocks.

Tests should prove:

1. `CollectionOptions.weights` is passed into `BestMoveOptions`.
2. Draw outcomes are stored as `0.5`.
3. Max-move result `"draw"` stores draw outcome.
4. Max-move result `"discard"` stores no positions.
5. Invalid `max_move_result` raises `ValueError`.
6. `CollectionOptions(seed=...)` is reproducible.
7. Slow real self-play collection tests are marked `@pytest.mark.slow`.

## Guidance

Do not use full self-play for fast tests. Instead, monkeypatch:

- `get_best_move`,
- board terminal-state helpers,
- `_play_game` if testing collection wrapper behavior,
- PositionDatabase add/write behavior.

Use real self-play only in slow tests.

---

# Problem 6: PositionDB tests are incomplete/stale

## Current problem

The PositionDB implementation mostly supports aggregation, but tests are incomplete and still contain a stale comment saying “last outcome wins.”

## Required behavior

Fix the stale comment and strengthen tests.

## Required tests

### Duplicate aggregation

Add same FEN with:

```text
1.0
0.5
0.0
```

Verify:

```text
count == 3
total == 1.5
mean == 0.5
```

### Old JSONL load

Use hand-authored old-format lines:

```json
{"pos": "fen", "outcome": 1.0}
```

Verify conversion to:

```python
PositionStats(total=1.0, count=1)
```

### Old JSONL duplicate aggregation

Use duplicate old-format lines and verify `total`, `count`, and `mean`.

### New JSONL direct load

Use hand-authored new-format line:

```json
{"pos": "fen", "total": 3.0, "count": 4}
```

Verify direct load.

### New JSONL save/load round trip

Save and reload a DB with duplicate stats and verify exact preservation.

### Empty DB

Verify length/export/save/load behavior for an empty DB.

---

# Problem 7: Opening-book seed behavior needs direct tests

## Current status

The code now seeds before opening-book lookup, which is good. But the original bug was not directly covered by tests.

## Required tests

Add tests proving:

1. Same seed gives same random opening-book move.
2. Different seeds can produce different book choices when multiple book moves exist.
3. Opening-book seeding does not depend on previous global RNG state.
4. Collection seeding is reproducible in a small/mocked scenario.

## Guidance

If the built-in opening book does not provide reliable multiple choices for a compact test position, use monkeypatching:

- patch book lookup to return from a list of candidate moves,
- patch random choice path,
- assert seed controls the selected move.

Prefer a test that exercises `get_best_move()` with `random_opening_book=True`.

---

# Problem 8: Texel loss `k` tests are missing

## Current problem

Texel loss tests cover material sign and quiescence/static modes, but do not directly prove:

1. non-default `k` changes MSE,
2. `mean_squared_error(..., k=...)` compatibility still works.

## Required tests

Add tests where the position score is nonzero and the outcome is not exactly matched, then assert:

```python
loss_k1 != loss_k2
```

Example:

```python
mse_default = mean_squared_error(pairs, weights, k=DEFAULT_K)
mse_other = mean_squared_error(pairs, weights, k=DEFAULT_K * 2)
assert mse_default != mse_other
```

Also test that:

```python
mean_squared_error(pairs, weights, k=some_k)
```

matches:

```python
mean_squared_error(pairs, weights, options=LossOptions(k=some_k))
```

if that compatibility is intended.

## Acceptance criteria

- Non-default `k` behavior is directly tested.
- Backward-compatible `k=` API is directly tested.

---

# Problem 9: Special perft tests are mostly smoke tests

## Current problem

Special perft tests mostly assert:

```python
assert _perft(board, 1) > 0
```

or:

```python
assert len(moves) > 0
```

Those are smoke tests, not perft validation.

## Required behavior

Add real known-count special perft tests where practical.

Minimum categories:

1. castling,
2. en passant,
3. promotion,
4. check evasions.

## Acceptable approaches

### Preferred

Use known standard perft positions with expected counts.

Example candidates:

- Kiwipete for castling/pins/checks.
- Dedicated en passant perft positions.
- Dedicated promotion positions.
- Dedicated check-evasion positions.

Use shallow depths if performance is a concern.

### If exact counts are unavailable

For this patch, it is acceptable to explicitly defer complex special perft counts if:

1. the docs/TODO clearly say they are deferred,
2. existing smoke tests are renamed as smoke tests, not perft validation,
3. at least one or two known-count special positions are added.

Do not pretend `> 0` is equivalent to perft validation.

## Acceptance criteria

- Start-position perft exact counts remain.
- At least some special cases have exact known counts.
- Remaining smoke tests are named/described honestly.
- Deferred cases are documented as future work.

---

# Problem 10: Runtime-marker tests must not make the fast suite expensive

## Required behavior

Tests that check pytest marker behavior must be cheap.

Avoid running the full test suite from inside tests.

Good options:

1. Static parse/check of test files for markers.
2. Use `pytest --collect-only` if needed.
3. Run a tiny dedicated dummy test module if absolutely necessary.
4. Mark expensive subprocess tests as slow.

## Acceptance criteria

- Marker tests do not hardcode paths.
- Marker tests do not run the full fast suite from inside the fast suite.
- Marker tests do not dominate test runtime.

---

# Documentation updates

Update docs if needed:

```text
docs/ENGINE_SEARCH_NOTES.md
docs/TEXEL_TUNING.md
README.md
```

Required documentation points:

1. Fast tests are expected to pass with `pytest -m "not slow"`.
2. Expensive engine-strength regressions belong in the slow suite.
3. Online learning uses configurable validation gate fields.
4. If candidates are in-memory only, document that.
5. If candidate files exist, document candidate/backup file behavior.
6. Special perft coverage status is honest.
7. Future work remains:
   - make/unmake search,
   - Zobrist hashing,
   - TT mate-score normalization,
   - broader special perft suite,
   - search module decomposition.

---

# Final validation

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

If slow tests are very slow, document that, but they must be marked slow and excluded from the fast suite.

---

# Acceptance criteria

This Fix 3 patch is complete only when:

1. `pytest -m "not slow"` completes.
2. No tests hardcode `/home/phil/work/chess-engine`.
3. Runtime-marker tests are portable and cheap or marked slow.
4. Remaining expensive engine regression tests are slow-marked or rewritten.
5. Online learning uses `config.validation_fraction`.
6. Online learning uses `config.validation_seed`.
7. Online learning honors `require_validation_improvement`.
8. Online learning honors `min_validation_mse_improvement`.
9. `keep_rejected_candidate` is honored, documented, or removed.
10. Online-learning accept/reject/backup/cache behavior is tested.
11. Weak assertions such as `assert len(db) >= 0` are removed.
12. Collection tests prove actual behavior using mocks/monkeypatches.
13. PositionDB tests verify `total`, `count`, `mean`, old JSONL duplicate aggregation, and new JSONL direct load.
14. Random opening-book seed behavior is directly tested.
15. Texel loss non-default `k` behavior is directly tested.
16. `mean_squared_error(..., k=...)` compatibility is directly tested.
17. Special perft tests include exact known counts where practical or are honestly deferred.
18. Ruff passes.
19. Mypy passes.
20. Pylint for Texel passes or remains acceptably high.
21. Targeted tests pass.
22. Slow tests are isolated from the fast suite.

---

# Notes for Claude Code

## Keep the patch narrow

Do not touch unrelated engine behavior.

## Do not hide slow tests

The goal is not to make tests pass by deleting coverage. Move expensive integration coverage to the slow suite and preserve fast unit/regression coverage.

## Avoid no-op tests

Every test should be able to fail if the implementation regresses.

## Prefer monkeypatching for Texel/collection/online-learning tests

Fast tests should not depend on expensive self-play or SPSA runs.

## Be honest in docs

If a perft category is smoke-tested rather than known-count tested, say so. If a feature is deferred, document it explicitly.
