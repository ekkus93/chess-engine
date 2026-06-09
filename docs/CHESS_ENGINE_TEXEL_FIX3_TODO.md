# CHESS_ENGINE_TEXEL_FIX3_TODO.md

## Implementation checklist

This TODO is for the Fix 3 cleanup patch. The goal is to finish the remaining blockers from the Fix 2 review.

Do **not** implement make/unmake search, bitboards, Zobrist hashing, NNUE, or broad search rewrites in this patch.

---

# Phase 0: Baseline and failure inventory

## 0.1 Run baseline validation

- [ ] Run Ruff:
  - [ ] `uv run python -m ruff check chess_game tests`
- [ ] Run mypy:
  - [ ] `uv run python -m mypy chess_game`
- [ ] Run Pylint on Texel package:
  - [ ] `uv run python -m pylint chess_game/texel --score=y`
- [ ] Run full fast suite:
  - [ ] `uv run python -m pytest -m "not slow" -vv`

## 0.2 Record slow/hanging tests

- [ ] Record the first slow/hanging test.
- [ ] Continue after fixing/marking it until the full fast suite completes.
- [ ] Pay special attention to:
  - [ ] `tests/test_test_runtime_markers_integration.py`
  - [ ] `tests/test_ai_endgame1_regressions.py`
  - [ ] `tests/test_ai_endgame2_regressions.py`
  - [ ] `tests/test_ai_endgame_fix1_regressions.py`
  - [ ] `tests/test_ai_plan_fix_regressions.py`
  - [ ] `tests/test_ai_review_loop.py`
  - [ ] `tests/test_ai_strategy5_regressions.py`
  - [ ] `tests/test_ai_strategy6_regressions.py`
  - [ ] `tests/test_ai_strategy7_regressions.py`
  - [ ] `tests/test_ai_white_improvements3.py`
  - [ ] `tests/test_ai_search.py`

---

# Phase 1: Fix runtime-marker integration tests

## 1.1 Remove hardcoded repo path

- [ ] Open `tests/test_test_runtime_markers_integration.py`.
- [ ] Remove hardcoded `/home/phil/work/chess-engine`.
- [ ] Add dynamic repo root:

```python
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
```

- [ ] Replace subprocess `cwd` with `REPO_ROOT`.
- [ ] Replace direct file paths with `REPO_ROOT / ...`.

## 1.2 Make marker tests cheap or slow

- [ ] Identify tests that spawn pytest subprocesses.
- [ ] If a test runs the full fast suite from inside pytest, rewrite it or mark it slow.
- [ ] Prefer static checks or `pytest --collect-only`.
- [ ] Do not allow these tests to dominate fast-suite runtime.

## 1.3 Validate

- [ ] Run:
  - [ ] `uv run python -m pytest tests/test_test_runtime_markers_integration.py -m "not slow" -q`
- [ ] Confirm it passes or only slow tests are deselected.

---

# Phase 2: Make the full fast suite complete

## 2.1 Iteratively run fast suite

- [ ] Run:
  - [ ] `uv run python -m pytest -m "not slow" -vv`
- [ ] When a slow test is found, classify it:
  - [ ] expensive engine-strength/depth integration test,
  - [ ] test bug,
  - [ ] can be rewritten as fast helper/unit test.

## 2.2 Mark expensive tests slow

For expensive engine-strength/depth tests:

- [ ] Add `@pytest.mark.slow`.
- [ ] Keep meaningful coverage in the slow suite.
- [ ] Add a short comment when useful explaining why it is slow.

## 2.3 Rewrite tests where possible

For tests that can be fast:

- [ ] lower search depth,
- [ ] use deterministic mode,
- [ ] use smaller/tactical positions,
- [ ] test helper functions directly,
- [ ] avoid full depth-3+ root searches in the fast suite.

## 2.4 Confirm fast suite

- [ ] Run:
  - [ ] `uv run python -m pytest -m "not slow"`
- [ ] Confirm it completes.
- [ ] Record approximate runtime.

---

# Phase 3: Complete OnlineLearningConfig behavior

## 3.1 Remove hardcoded validation constants from behavior

- [ ] Open `chess_game/texel/online_learning.py`.
- [ ] Find hardcoded validation constants:
  - [ ] `_VALIDATION_FRACTION`
  - [ ] `_VALIDATION_SEED`
- [ ] Replace behavior use with:
  - [ ] `config.validation_fraction`
  - [ ] `config.validation_seed`
- [ ] Keep module defaults only if they feed the dataclass defaults.

## 3.2 Validate config values

- [ ] Validate `validation_fraction`.
- [ ] Allow `0.0 <= validation_fraction < 1.0`.
- [ ] If validation improvement is required, make sure enough validation positions exist.
- [ ] If not enough validation data and `require_validation_improvement=True`, reject/no-promote.

## 3.3 Honor require_validation_improvement

- [ ] If `config.require_validation_improvement=True`, require validation improvement before promotion.
- [ ] If `False`, allow explicit unsafe/no-validation promotion if that behavior is intended.
- [ ] Document unsafe behavior if supported.

## 3.4 Honor min_validation_mse_improvement

Acceptance condition:

```python
candidate_val_mse <= baseline_val_mse - config.min_validation_mse_improvement
```

- [ ] Reject if candidate improves less than threshold.
- [ ] Add test for below-threshold improvement.

## 3.5 Honor or remove/document keep_rejected_candidate

Choose one:

### File-based candidate behavior

- [ ] Save candidate to candidate path.
- [ ] If rejected and `keep_rejected_candidate=False`, remove candidate.
- [ ] If rejected and `keep_rejected_candidate=True`, preserve candidate.

### In-memory-only candidate behavior

- [ ] Document candidates are not written unless accepted.
- [ ] Remove `keep_rejected_candidate` if it cannot have any effect, or clearly document no effect.
- [ ] Adjust tests accordingly.

Preferred: implement file-based candidate behavior if low risk.

## 3.6 Backup and cache behavior

- [ ] Ensure active weights are preserved on rejection.
- [ ] Ensure backup is created on acceptance if active weights exist.
- [ ] Ensure weight cache invalidation happens only after accepted promotion.
- [ ] If atomic replace is feasible, use it.
- [ ] If atomic replace is not implemented, document future work.

---

# Phase 4: Strengthen online-learning tests

Use monkeypatching/mocking. Do not run expensive SPSA/self-play in fast tests.

Add tests for:

- [ ] candidate accepted when validation improves enough.
- [ ] candidate rejected when validation worsens.
- [ ] candidate rejected when improvement is below `min_validation_mse_improvement`.
- [ ] active weights preserved on rejection.
- [ ] backup created on acceptance when active weights exist.
- [ ] cache invalidated only after accepted promotion.
- [ ] `validation_fraction` changes the split behavior.
- [ ] `validation_seed` controls deterministic split.
- [ ] too-small validation set does not promote by default.
- [ ] explicit unsafe/no-validation promotion behavior, if supported.
- [ ] `keep_rejected_candidate` behavior, if file-based candidates are implemented.

---

# Phase 5: Remove weak/no-op assertions

## 5.1 Search for weak assertions

- [ ] Search tests for:
  - [ ] `assert len(db) >= 0`
  - [ ] `or True`
  - [ ] `assert True`
  - [ ] assertions that cannot fail.

## 5.2 Fix or remove each weak assertion

- [ ] Replace with meaningful assertions.
- [ ] If a test cannot assert a real invariant, delete or rewrite it.
- [ ] Pay special attention to `tests/test_collect.py`.

---

# Phase 6: Strengthen collection behavior tests

## 6.1 Validate max_move_result

- [ ] Ensure `CollectionOptions` or collection entry point rejects invalid `max_move_result`.
- [ ] Accepted values:
  - [ ] `"draw"`
  - [ ] `"discard"`
- [ ] Invalid values raise `ValueError`.

## 6.2 Add fast unit tests with monkeypatching

Add tests proving:

- [ ] `CollectionOptions.weights` is passed into `BestMoveOptions`.
- [ ] Draw outcomes are stored as `0.5`.
- [ ] Max-move result `"draw"` stores draw outcome.
- [ ] Max-move result `"discard"` stores no positions.
- [ ] Invalid `max_move_result` raises `ValueError`.
- [ ] `CollectionOptions(seed=...)` is reproducible.
- [ ] Slow real self-play tests are marked `@pytest.mark.slow`.

## 6.3 Avoid expensive self-play in fast tests

- [ ] Monkeypatch `get_best_move`.
- [ ] Monkeypatch terminal state helpers where useful.
- [ ] Use fake/minimal PositionDatabase if useful.
- [ ] Keep full self-play only in slow tests.

---

# Phase 7: Strengthen PositionDB tests

## 7.1 Fix stale comments

- [ ] Search `tests/test_position_db.py` for “last outcome wins.”
- [ ] Replace with aggregation/mean wording.

## 7.2 Duplicate aggregation test

- [ ] Add same FEN with outcomes:
  - [ ] `1.0`
  - [ ] `0.5`
  - [ ] `0.0`
- [ ] Verify:
  - [ ] `count == 3`
  - [ ] `total == 1.5`
  - [ ] `mean == 0.5`

## 7.3 Old JSONL tests

- [ ] Create hand-authored old-format JSONL:
  - [ ] `{"pos": "...", "outcome": 1.0}`
- [ ] Load DB.
- [ ] Verify `total` and `count`.
- [ ] Add duplicate old-format lines.
- [ ] Verify duplicate aggregation.

## 7.4 New JSONL tests

- [ ] Create hand-authored new-format JSONL:
  - [ ] `{"pos": "...", "total": 3.0, "count": 4}`
- [ ] Load DB.
- [ ] Verify `total == 3.0`.
- [ ] Verify `count == 4`.
- [ ] Verify mean.

## 7.5 Round-trip and empty tests

- [ ] Save/load round-trip preserves stats.
- [ ] Empty DB behavior is tested.

---

# Phase 8: Add opening-book seed tests

## 8.1 Same seed test

- [ ] Add test where `random_opening_book=True`.
- [ ] Call `get_best_move()` multiple times with same `rng_seed`.
- [ ] Assert same move is returned.

## 8.2 Different seed test

- [ ] Use position/book setup with multiple legal book moves.
- [ ] Call with different seeds.
- [ ] Assert different seeds can produce different choices.
- [ ] If randomness distribution makes this flaky, monkeypatch book random choice to make seed effect deterministic.

## 8.3 Global RNG independence

- [ ] Change global RNG state before call.
- [ ] Call seeded `get_best_move()`.
- [ ] Assert seeded result is stable regardless of prior global RNG state.

## 8.4 Collection seed reproducibility

- [ ] Add small/mocked collection test.
- [ ] Same `CollectionOptions(seed=...)` should produce same result.
- [ ] Avoid full expensive self-play.

---

# Phase 9: Add direct Texel loss `k` tests

## 9.1 Non-default k changes MSE

- [ ] Create pair(s) with nonzero score and outcome that makes sigmoid difference visible.
- [ ] Compute:
  - [ ] `mse1 = mean_squared_error(pairs, weights, k=DEFAULT_K)`
  - [ ] `mse2 = mean_squared_error(pairs, weights, k=DEFAULT_K * 2)`
- [ ] Assert `mse1 != mse2`.

## 9.2 Backward compatibility

- [ ] Compute:
  - [ ] `mean_squared_error(pairs, weights, k=some_k)`
  - [ ] `mean_squared_error(pairs, weights, options=LossOptions(k=some_k))`
- [ ] Assert they match, if that compatibility is intended.

## 9.3 Keep existing perspective tests

- [ ] White material advantage positive.
- [ ] Black material advantage negative.
- [ ] Side-to-move does not flip White-relative evaluation sign.

---

# Phase 10: Improve or honestly defer special perft tests

## 10.1 Preserve start-position perft

- [ ] depth 1 = 20.
- [ ] depth 2 = 400.
- [ ] depth 3 = 8902.
- [ ] depth 4 = 197281 marked slow.

## 10.2 Add known-count special perft cases

Where practical, add exact counts for:

- [ ] castling,
- [ ] en passant,
- [ ] promotion,
- [ ] check evasions.

Use shallow depths if needed.

## 10.3 Rename smoke tests honestly

If tests only assert `> 0` or legal moves exist:

- [ ] rename them as smoke tests,
- [ ] do not present them as perft validation.

## 10.4 Document deferred perft categories

If exact counts are not added for all categories, document future work for:

- [ ] pins,
- [ ] discovered checks,
- [ ] complex castling/en passant cases,
- [ ] deeper special perft positions.

---

# Phase 11: Documentation updates

Update docs as needed.

## 11.1 README

- [ ] Fast test command.
- [ ] Slow test command.
- [ ] Lint/type-check commands.
- [ ] Note that expensive engine regressions are slow-marked.

## 11.2 Texel docs

Update `docs/TEXEL_TUNING.md`:

- [ ] online-learning config fields,
- [ ] validation split behavior,
- [ ] minimum validation improvement,
- [ ] candidate promotion/rejection behavior,
- [ ] whether rejected candidates are persisted,
- [ ] seed reproducibility.

## 11.3 Search/test docs

Update `docs/ENGINE_SEARCH_NOTES.md` or other relevant docs:

- [ ] fast vs slow test policy,
- [ ] special perft coverage status,
- [ ] future work for broader perft,
- [ ] future work for make/unmake, Zobrist, TT mate-score normalization.

---

# Phase 12: Final validation

## 12.1 Static checks

Run:

- [ ] `uv run python -m ruff check chess_game tests`
- [ ] `uv run python -m mypy chess_game`
- [ ] `uv run python -m pylint chess_game/texel --score=y`

## 12.2 Full fast suite

Run:

- [ ] `uv run python -m pytest -m "not slow"`

This must complete.

## 12.3 Targeted tests

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

## 12.4 Slow tests

Run:

- [ ] `uv run python -m pytest -m slow`

If too slow:

- [ ] Confirm slow tests are marked slow.
- [ ] Document slow-test runtime limitations.
- [ ] Do not allow slow tests into the fast suite.

---

# Phase 13: Completion criteria

This patch is complete only when:

- [ ] `pytest -m "not slow"` completes.
- [ ] No tests hardcode `/home/phil/work/chess-engine`.
- [ ] Runtime-marker tests are portable.
- [ ] Runtime-marker tests are cheap or marked slow.
- [ ] Remaining expensive search tests are slow-marked or rewritten.
- [ ] Online learning uses `config.validation_fraction`.
- [ ] Online learning uses `config.validation_seed`.
- [ ] Online learning honors `require_validation_improvement`.
- [ ] Online learning honors `min_validation_mse_improvement`.
- [ ] `keep_rejected_candidate` is honored, documented, or removed.
- [ ] Online-learning accept/reject/backup/cache behavior is tested.
- [ ] Weak assertions such as `assert len(db) >= 0` are removed.
- [ ] Collection tests prove actual behavior.
- [ ] PositionDB duplicate aggregation verifies `total`, `count`, and `mean`.
- [ ] PositionDB old JSONL duplicate aggregation is tested.
- [ ] PositionDB new JSONL direct load is tested.
- [ ] Random opening-book seed behavior is directly tested.
- [ ] Texel loss non-default `k` behavior is directly tested.
- [ ] `mean_squared_error(..., k=...)` compatibility is directly tested.
- [ ] Special perft tests include exact known counts where practical or are honestly deferred.
- [ ] Ruff passes.
- [ ] Mypy passes.
- [ ] Pylint for Texel passes or remains acceptably high.
- [ ] Targeted tests pass.
- [ ] Slow tests are isolated from the fast suite.

---

# Notes for Claude Code

## Keep this narrow

The goal is to finish the existing work, not to start a new architecture.

## Do not add weak tests

Every test should fail if the behavior regresses.

## Prefer mocks for Texel workflow tests

Online learning, collection, and validation can be tested with monkeypatches rather than expensive real games.

## Preserve existing APIs where possible

Do not break saved PositionDB files or existing CLI usage.

## Be explicit about deferrals

If exact special perft counts are not added in this patch, document that clearly.
