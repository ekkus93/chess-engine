# responses9.md — Questions and Issues on TEXEL_FIX4

## Overview

Read CHESS_ENGINE_TEXEL_FIX4_SPEC.md and CHESS_ENGINE_TEXEL_FIX4_TODO.md. This file documents clarifying questions and potential issues before implementation.

---

## Critical Understanding

TEXEL_FIX4 is a **follow-up to TEXEL_FIX3** addressing remaining blockers found in review. Despite TEXEL_FIX3 being marked "complete," the fast test suite **still times out/hangs** and must be fixed.

**Main Priority:** Make `uv run python -m pytest -m "not slow"` complete reliably (currently hangs at expensive tests)

---

## High-Level Questions

### 1. Current Fast Suite Failure Point

**Question:** Where does the fast suite currently hang?

**Context:** The spec mentions hanging at:
- `tests/test_ai_strategy4_regressions.py`
- `tests/test_ai_strategy8_regressions.py`

and `test_test_runtime_markers_integration.py::TestIntegrationTestMarkers::test_self_play_integration_tests_fast`

**Action:** Phase 0 should identify current state with:
```bash
uv run python -m pytest -m "not slow" -vv
```

**Question for user:** Should I start Phase 0 immediately to identify where it currently hangs? Or do you know the current hang point?

### 2. Runtime-Marker Integration Test Fix Strategy

**Question:** Should expensive subprocess pytest tests be marked slow or rewritten?

**Context:** `test_test_runtime_markers_integration.py` spawns pytest subprocesses. Some are cheap (collect-only), others run full test suites.

**Options:**
- **A) Mark slow:** Add `@pytest.mark.slow` to expensive tests like `test_self_play_integration_tests_fast`
- **B) Rewrite as static:** Replace with AST/file parsing instead of spawning pytest
- **C) Use collect-only:** Keep subprocess pytest but use `--collect-only -q` to avoid running tests

**Recommendation needed:** Which approach for each test in that file?

### 3. OnlineLearningConfig Validation

**Question:** Where should `validation_fraction` validation live?

**Context:** Spec requires:
```
0.0 <= validation_fraction < 1.0
```

**Options:**
- **A) In __post_init__:** Add validation to `OnlineLearningConfig.__post_init__()`, raise `ValueError` on invalid
- **B) In record_game_and_update_weights():** Validate when actually used
- **C) Both:** Validate early in __post_init__, fail fast

**Recommendation needed:** Which approach aligns with project philosophy?

### 4. PositionDB Stats Access

**Question:** How do tests access `.count`, `.total`, `.mean`?

**Context:** Spec requires tests to directly assert:
```python
assert stats.count == 3
assert stats.total == 1.5
assert stats.mean == 0.5
```

**Current Understanding:** PositionDB uses internal `_position_data` dict with PositionStats. Need to understand:
- Are `.count`, `.total`, `.mean` properties on a public PositionStats class?
- Or are they in an internal structure that tests would need to access via internal APIs?
- Should I add public accessors if they don't exist?

**Action needed:** Clarify the PositionStats API structure.

### 5. Texel Loss k Parameter API

**Question:** What's the current API for the k parameter?

**Context:** Spec mentions both:
```python
mean_squared_error(pairs, weights, k=some_k)
mean_squared_error(pairs, weights, opts=LossOptions(k=some_k))
```

**Current Understanding from TEXEL_FIX3 tests:** The function accepts `opts=LossOptions(k=...)` in current tests.

**Action needed:** Confirm whether:
- Only `opts=LossOptions(k=...)` is supported?
- Or is there also a direct `k=` parameter?
- What's the canonical API for the public interface?

### 6. Online-Learning Mocking Strategy

**Question:** At what level should I mock SPSA and validation?

**Context:** Spec says mock/monkeypatch to avoid expensive SPSA and self-play. Need to test:
- Candidate acceptance/rejection logic
- Backup creation
- Cache invalidation
- Active weights preservation

**Options:**
- **A) Mock at optimize() level:** Mock `optimize()` to return a fixed candidate
- **B) Mock at mean_squared_error() level:** Mock `mean_squared_error()` to return controlled MSE values
- **C) Mock both:** Both levels for different test scenarios
- **D) Mock at higher level:** Mock the full game recording/SPSA pipeline

**Recommendation needed:** Which mocking strategy produces the strongest tests?

---

## Specific Technical Issues

### Issue 1: test_self_play_integration_tests_fast Timeout

**Problem:** This test spawns pytest and times out during fast suite run.

**Solution options:**
1. Mark `@pytest.mark.slow` - keeps test, moves to slow suite
2. Rewrite to use `pytest --collect-only` - removes real test execution
3. Rewrite as static check - parses test files without spawning pytest

**Recommendation:** Which approach is preferred?

### Issue 2: PositionDB Stats Verification

**Problem:** Current tests use `all_pairs()` which returns computed means, not raw stats.

**Solution:** Need direct access to `count` and `total`. Either:
1. Add public properties: `.count`, `.total`, `.mean` on PositionStats
2. Use internal API in tests: access `_position_data` dict
3. Create public accessor method: `get_position_stats(fen)`

**Recommendation:** Which is appropriate for a public test?

### Issue 3: Vacuous k Parameter Tests

**Problem:** Tests like:
```python
assert mse_a != mse_b or abs(mse_a - mse_b) < 1e-12
```

always pass (always true when values differ or are very close).

**Solution:** Use real positions with nonzero scores where sigmoid steepness affects MSE. Must use `pytest.approx()` for floating-point comparison:
```python
assert mse_default != pytest.approx(mse_other, rel_tol=1e-6)
```

**Question:** What position/outcome pair reliably shows k-parameter effects? Should I use a position where White has material advantage + draw outcome?

### Issue 4: Opening-Book Seed Test Weakness

**Problem:** Current test asserts `len(moves_found) >= 1`, which passes even if seeds never affect selection.

**Solution:** Use controlled fake book with multiple candidate moves where specific seeds produce different selections.

**Question:** Should I:
1. Monkeypatch the opening book to return a fake with 3-4 candidate moves?
2. Use the real book but find a position with multiple valid book moves?
3. Mock `random.choice()` to map seeds to specific indices?

**Recommendation:** Which is most robust?

---

## Implementation Risks

### Risk 1: Breaking PositionDB Compatibility

**Issue:** Adding public stats accessors or changing internal structure could break saved JSONL files.

**Mitigation:** Ensure new accessors are read-only and don't affect persistence format.

### Risk 2: Online-Learning Behavior Change

**Issue:** Adding `validation_fraction` validation could break existing configs.

**Mitigation:** Use sensible defaults (0.20) and only validate at construction, not silently on use.

### Risk 3: Test Infrastructure Coupling

**Issue:** Tests that mock `optimize()` or `mean_squared_error()` could become brittle if internals change.

**Mitigation:** Mock at the boundary of `record_game_and_update_weights()` rather than deep internals.

---

## Assumptions I'm Making

1. **Fast suite hang is real:** The fast suite does time out at expensive tests, not a past-state issue
2. **Phase 0 should be first:** Running baseline validation will identify current state before fixes
3. **Memory-only candidates:** No file-based candidate persistence was implemented in TEXEL_FIX3
4. **k parameter API:** Current tests use `opts=LossOptions(k=...)`, not a direct `k=` parameter
5. **PositionStats structure:** Stats are stored internally, need to add public accessors for tests
6. **Monkeypatching is acceptable:** Tests can use `monkeypatch` fixture to mock expensive functions

---

## Clarifications Needed From User

Before I proceed with Phase 0 baseline validation, please clarify:

1. **Fast suite status:** Does it currently hang? If so, at which test?
2. **Runtime-marker strategy:** Should expensive subprocess tests be marked slow or rewritten?
3. **validation_fraction validation:** Should this be enforced in `__post_init__()` or elsewhere?
4. **PositionDB API:** Do public stats accessors already exist, or should I add them?
5. **k parameter API:** Is there both a `k=` parameter and `opts=LossOptions(k=...)`, or just one?
6. **Opening-book testing:** What's the preferred way to prove seed affects selection?

---

## Ready to Proceed?

Once these clarifications are provided, I can proceed with Phase 0 baseline validation followed by the 11-phase implementation plan.

The main goal is clear: **Make `uv run python -m pytest -m "not slow"` complete reliably without hanging.**
