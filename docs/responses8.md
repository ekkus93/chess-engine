# responses8.md — Questions and Issues on TEXEL_FIX3

## Overview

Read CHESS_ENGINE_TEXEL_FIX3_SPEC.md and CHESS_ENGINE_TEXEL_FIX3_TODO.md. This file documents clarifying questions and potential issues before implementation.

---

## High-Level Questions

### 1. OnlineLearningConfig Candidate File Handling

**Question:** Should candidates be file-based or memory-only?

**Context:** The spec mentions preferred file structure:
```
weights.candidate.json
weights.previous.json
weights.json
```

But also says:
> If implementing file-based candidates is too invasive, keep candidate in memory, but document that explicitly.

**Options:**
- **A) File-based:** Save candidate → validate → promote/reject (remove if rejected unless `keep_rejected_candidate=True`)
- **B) Memory-only:** Keep candidate in memory, document no file persistence, adjust tests

**Recommendation:** Start with memory-only if current code already works that way, document explicitly, mark file-based as future work. This avoids introducing file I/O complexity.

---

### 2. Special Perft Known Counts

**Question:** What perft positions/depths should be included?

**Context:** Spec says:
> Use known standard perft positions with expected counts. Example candidates: Kiwipete, dedicated en passant positions, etc.
> If exact counts are unavailable, explicitly defer with documentation.

**Options:**
- **A) Standard positions:** Find/use Kiwipete and other standard test positions
- **B) Custom simple positions:** Create minimal positions with known counts at shallow depths
- **C) Honestly defer:** Rename existing `> 0` tests as smoke tests, document future work

**Recommendation:** Do both: use 1-2 known standard positions if available (like Kiwipete depth 1), and honestly defer complex cases. Don't force exact counts for all categories.

---

### 3. Fast Suite Timeout Tolerance

**Question:** What's the acceptable fast-suite runtime?

**Context:** Current fast suite runs ~100 seconds. Phase 2 goal is to identify and mark slow tests.

**Needed:** 
- Target runtime for fast suite? (Current ~100s, acceptable range?)
- Cutoff threshold for marking a test `@pytest.mark.slow`? (e.g., >1s per test?)

**Recommendation:** Target fast suite should complete in <150 seconds. Individual tests >2 seconds should be marked slow or rewritten.

---

### 4. Online-Learning Test Scope

**Question:** How deep should online-learning tests go with monkeypatching?

**Context:** Spec says use mocks/monkeypatches, avoid expensive SPSA/self-play. But needs to test:
- Train/validate split with `validation_seed`
- Candidate acceptance/rejection logic
- Cache invalidation
- File preservation (if file-based)

**Options:**
- **A) Full mock:** Mock SPSA, mock validation, test only config flow
- **B) Light integration:** Run tiny SPSA (2-3 iterations), real validation on mocked DB
- **C) Hybrid:** Mock where needed, light integration where meaningful

**Recommendation:** Full mock for fast tests (test config behavior in isolation). One light-integration test in slow suite (proves end-to-end works).

---

## Specific Technical Issues

### Issue 1: test_test_runtime_markers_integration.py Scope

**Concern:** Spec mentions "tests that spawn pytest subprocesses" can be expensive.

**Current status:** Need to check if this test runs full pytest suite from inside pytest.

**Action:** Phase 1 must identify which tests spawn subprocess pytest and evaluate runtime. If expensive, either:
1. Rewrite to use `pytest --collect-only`
2. Mark as slow
3. Rewrite as static parser check

---

### Issue 2: PositionDB Format Compatibility

**Concern:** Old JSONL format and new format must coexist during load.

**Expected behavior:** Load should handle both:
```json
# Old
{"pos": "fen", "outcome": 1.0}

# New
{"pos": "fen", "total": 3.0, "count": 4}
```

**Action:** Phase 7 tests must verify:
1. Old format loads correctly (convert outcome → total=outcome, count=1)
2. New format loads directly (total and count as-is)
3. Duplicate entries aggregate correctly
4. Save/reload preserves new format (no regression)

---

### Issue 3: Texel Loss `k` Parameter API

**Concern:** Need to verify backward compatibility between two APIs.

**Current status:** Spec mentions:
```python
mean_squared_error(pairs, weights, k=some_k)
mean_squared_error(pairs, weights, options=LossOptions(k=some_k))
```

**Action:** Phase 9 must verify both work and produce identical results. If not, document which is preferred.

---

### Issue 4: Opening-Book Seed Flakiness Risk

**Concern:** Random selection from multiple book moves may be flaky if distribution doesn't guarantee selection.

**Mitigation:** Spec suggests monkeypatching book lookup to return controlled set of moves.

**Action:** Phase 8 should use monkeypatch if real book doesn't have reliable multi-choice position, or use fixed board with explicit book moves.

---

## Implementation Risks

### Risk 1: Test Coverage Loss

**Issue:** Moving expensive tests to slow suite could create gap if slow suite is rarely run.

**Mitigation:** 
- Document which engine-strength tests moved to slow
- Keep at least one shallow-depth regression test in fast suite for each area
- Fast suite should test behavior; slow suite tests strength

### Risk 2: Online-Learning Behavioral Change

**Issue:** Using `config.validation_fraction` and `config.validation_seed` changes how train/validation split works if hardcoded constants currently differ.

**Action:** Phase 3 must verify new behavior is intentional. If regression, adjust defaults or document breaking change.

### Risk 3: Candidate File Persistence

**Issue:** If candidates persist but current code doesn't expect them, could accumulate stale files.

**Action:** 
- If implementing file-based, add cleanup logic
- Or start memory-only (safer), document file-based as future work

---

## Assumptions I'm Making

1. **Fast suite timeout:** Currently ~100s is acceptable; target <150s
2. **OnlineLearningConfig:** Current code is memory-only; keep it that way initially
3. **Special perft:** Existing smoke tests are acceptable; add 1-2 known counts, defer the rest
4. **Hardcoded path:** Only in test_test_runtime_markers_integration.py
5. **No breaking changes:** Preserve PositionDB file format, CLI usage, public APIs

---

## Ready to Proceed?

I'm ready to start Phase 0 (baseline validation) immediately. This will:

1. Run full linting (ruff, mypy, pylint)
2. Attempt fast test suite and identify first hanging/slow test
3. Document findings for Phase 1-2

Confirm if my assumptions above are correct, or clarify any of the high-level questions (1-4) before I proceed.

