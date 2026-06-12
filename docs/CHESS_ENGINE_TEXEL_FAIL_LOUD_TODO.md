# CHESS_ENGINE_TEXEL_FAIL_LOUD_TODO.md

## Implementation checklist

This TODO is for the Texel fail-loud safety patch.

Keep this patch narrow. Do **not** change search/eval behavior, engine-strength heuristics, make/unmake, bitboards, Zobrist hashing, NNUE, broad Texel algorithms, broad CLI behavior, or broad online-learning architecture.

---

# Phase 0: Baseline validation

## 0.1 Static checks

- [ ] `uv run --extra dev python -m ruff check chess_game tests`
- [ ] `uv run --extra dev python -m mypy chess_game`
- [ ] `uv run --extra dev python -m pylint chess_game --score=y`

## 0.2 Fast suite

- [ ] `uv run --extra dev python -m pytest -m "not slow"`

## 0.3 Texel test baseline

Run:

```bash
uv run --extra dev python -m pytest \
  tests/test_collect.py \
  tests/test_loss.py \
  tests/test_position_db.py \
  tests/test_spsa.py \
  tests/test_tune.py \
  tests/test_validate.py \
  tests/test_online_learning.py \
  -m "not slow" -q
```

- [ ] Record pass/fail.
- [ ] Record any currently expected behavior that this patch intentionally changes.

## 0.4 Root bookkeeping preservation

- [ ] `uv run --extra dev python -m pytest tests/test_root_research_bookkeeping.py -q`

---

# Phase 1: Strict explicit weight loading

## 1.1 Audit weight-loading call sites

Search for:

```bash
grep -R "load_weights_or_default" -n chess_game tests
```

Classify every call site:

- [ ] automatic optional tuned-weight cache,
- [ ] explicit user-supplied path,
- [ ] CLI required path,
- [ ] tuning initial weights path,
- [ ] online-learning initial/current weights path,
- [ ] test fixture.

## 1.2 Define strict helper semantics

Ensure these semantics exist:

```python
load_weights(path: Path) -> EvalWeights
```

- [ ] Raises `FileNotFoundError` if missing.
- [ ] Raises clear error if JSON malformed.
- [ ] Raises clear error if weights invalid.

Optional helper if useful:

```python
load_optional_weights(path: Path | None) -> EvalWeights
```

- [ ] Returns defaults only when `path is None`.
- [ ] Raises if `path` is provided but missing.

Keep:

```python
load_weights_or_default(path)
```

only for explicitly optional auto-load behavior.

## 1.3 Fix validation CLI

In Texel validation CLI:

- [ ] Replace `load_weights_or_default(Path(args.weights))` with strict `load_weights(Path(args.weights))`.
- [ ] Missing `--weights` path should fail loudly.
- [ ] Malformed weights should fail loudly.
- [ ] Do not silently validate default weights when user supplied a path.

## 1.4 Fix tuning initial weights

In `run_tuning()`:

- [ ] If `initial_weights_path is None`, use default weights.
- [ ] If `initial_weights_path` is provided, call strict `load_weights(path)`.
- [ ] Missing supplied initial weights path raises.

## 1.5 Fix online-learning weight load if needed

For online learning:

- [ ] Decide whether missing current weights path is valid first-run behavior.
- [ ] If missing current path is allowed, make that explicit in the result reason.
- [ ] If a user explicitly supplies a path that should exist, fail loudly.
- [ ] Do not hide missing paths behind default fallback without reporting.

## 1.6 Tests

Add tests:

- [ ] `validate --weights missing.json` raises/fails.
- [ ] `run_tuning(initial_weights_path=missing)` raises.
- [ ] optional default path still returns defaults when intentionally optional.
- [ ] malformed weights still raise.
- [ ] valid explicit weights still load.

---

# Phase 2: Empty training data must fail loudly

## 2.1 `run_tuning()` empty DB

In `run_tuning()`:

- [ ] After loading or collecting DB, check position count.
- [ ] If DB has no positions, raise:
  - [ ] `ValueError("Texel tuning DB has no positions; refusing to write tuned weights")`
- [ ] Do not write output weights when DB is empty.

## 2.2 Collected empty DB

If `collect_games()` returns/stores zero positions:

- [ ] `run_tuning()` should treat this as empty DB and fail.
- [ ] Error message should distinguish empty collected DB if easy.

## 2.3 `optimize()` empty pairs

In `spsa.optimize()`:

- [ ] If `db.all_pairs()` is empty, raise `ValueError`.
- [ ] Do not silently return unchanged weights.

## 2.4 `calibrate_k()` / calibration entry points

- [ ] If calibration pairs are empty, raise `ValueError`.
- [ ] Do not silently choose `k_min`.
- [ ] Ensure CLI/helper calibration paths also fail loudly.

## 2.5 Tests

Add tests:

- [ ] `run_tuning()` with empty existing DB raises and writes no weights.
- [ ] `run_tuning()` with collection producing zero positions raises and writes no weights.
- [ ] `optimize()` with empty DB raises.
- [ ] `calibrate_k([])` or equivalent raises.
- [ ] Existing non-empty tuning tests still pass.

---

# Phase 3: PositionDB row validation

## 3.1 Implement row validator

In `position_db.py`, add internal validation helper(s):

- [ ] validate non-empty `pos` string.
- [ ] validate old-format `outcome`.
- [ ] validate new-format `total` and `count`.
- [ ] include file path and line number in errors.

Suggested error pattern:

```python
raise ValueError(f"{path}:{line_no}: invalid PositionDB row: {reason}")
```

## 3.2 Old format validation

For rows like:

```json
{"pos": "...", "outcome": 0.5}
```

Validate:

- [ ] `pos` exists.
- [ ] `pos` is non-empty string.
- [ ] `outcome` exists.
- [ ] `outcome` is finite.
- [ ] `0.0 <= outcome <= 1.0`.

## 3.3 New format validation

For rows like:

```json
{"pos": "...", "total": 3.0, "count": 4}
```

Validate:

- [ ] `pos` exists.
- [ ] `pos` is non-empty string.
- [ ] `total` exists.
- [ ] `total` is finite.
- [ ] `count` exists.
- [ ] `count` is int.
- [ ] `count > 0`.
- [ ] `0.0 <= total <= count`.

## 3.4 JSON errors

- [ ] Catch `json.JSONDecodeError`.
- [ ] Re-raise as `ValueError` with path and line number.
- [ ] Preserve useful original error info in message or exception chaining.

## 3.5 Ambiguous/mixed rows

Decide and test behavior for rows containing both:

```json
{"pos": "...", "outcome": 0.5, "total": 1.0, "count": 2}
```

Recommended:

- [ ] reject ambiguous rows.

Also reject rows with neither valid old nor valid new format.

## 3.6 Tests

Add tests for valid data:

- [ ] valid old JSONL loads.
- [ ] valid old duplicate rows aggregate.
- [ ] valid new JSONL loads.
- [ ] valid round-trip still works.

Add tests for invalid data:

- [ ] invalid JSON.
- [ ] missing `pos`.
- [ ] empty `pos`.
- [ ] non-string `pos`.
- [ ] missing `outcome`/`total`/`count`.
- [ ] outcome below 0.
- [ ] outcome above 1.
- [ ] non-finite outcome.
- [ ] count 0.
- [ ] negative count.
- [ ] non-int count.
- [ ] total below 0.
- [ ] total greater than count.
- [ ] non-finite total.
- [ ] ambiguous old+new row.

Each invalid test should assert line-numbered error text.

---

# Phase 4: SPSAOptions validation

## 4.1 Add `__post_init__()`

In `SPSAOptions`, validate:

- [ ] `max_iterations >= 1`
- [ ] `initial_step_size > 0`
- [ ] `step_decay > 0`
- [ ] `perturbation_size > 0`
- [ ] `perturbation_decay > 0`
- [ ] `stability_constant >= 0`
- [ ] `batch_size is None or batch_size >= 1`
- [ ] `checkpoint_every >= 1`

Also validate floats are finite:

- [ ] `initial_step_size`
- [ ] `step_decay`
- [ ] `perturbation_size`
- [ ] `perturbation_decay`
- [ ] `stability_constant`

## 4.2 Optional seed

If low-risk, add:

```python
seed: int | None = None
```

and use local RNG for perturbations.

- [ ] `rng = random.Random(options.seed)`
- [ ] do not use global `random.random()` for perturbations.
- [ ] tests cover reproducible perturbation/tuning behavior if feasible.

If not implemented, document as future work.

## 4.3 Tests

Add invalid-option tests:

- [ ] `max_iterations=0`
- [ ] `initial_step_size=0`
- [ ] `step_decay=0`
- [ ] `perturbation_size=0`
- [ ] `perturbation_decay=0`
- [ ] `stability_constant=-1`
- [ ] `batch_size=0`
- [ ] `checkpoint_every=0`
- [ ] NaN/inf float values.

Add valid-option tests:

- [ ] default options construct.
- [ ] valid custom options construct.
- [ ] existing SPSA behavior tests still pass.

---

# Phase 5: Online-learning result reasons

## 5.1 Add result type

Add:

```python
@dataclass(frozen=True)
class OnlineLearningResult:
    updated: bool
    reason: str
    positions: int = 0
    baseline_val_mse: float | None = None
    candidate_val_mse: float | None = None
    candidate_path: Path | None = None
```

Use an enum if preferred:

```python
class OnlineLearningReason(str, Enum): ...
```

but a string is acceptable if tests cover expected values.

## 5.2 Add result-returning API

Implement:

```python
def record_game_and_update_weights_result(...) -> OnlineLearningResult:
    ...
```

or change the existing API if all call sites/tests can be updated safely.

If preserving compatibility:

```python
def record_game_and_update_weights(...) -> bool:
    return record_game_and_update_weights_result(...).updated
```

## 5.3 Reason coverage

Return distinct reasons for at least:

- [ ] `disabled`
- [ ] `not_enough_positions`
- [ ] `empty_training_split`
- [ ] `empty_validation_split`
- [ ] `candidate_not_better`
- [ ] `candidate_below_threshold`
- [ ] `updated`

If some categories are not applicable to current implementation, document why.

## 5.4 Implement or remove `keep_rejected_candidate`

Find:

```python
keep_rejected_candidate: bool = False
```

Choose one:

### Option A: implement

- [ ] If rejected and `keep_rejected_candidate=True`, preserve candidate file.
- [ ] Set `candidate_path` in result.
- [ ] If rejected and `False`, delete candidate file if created.

### Option B: remove

- [ ] Remove config field.
- [ ] Remove tests/docs referencing it.

Preferred: implement if candidate files already exist in the flow.

## 5.5 Tests

Add tests:

- [ ] disabled returns `updated=False`, reason `disabled`.
- [ ] not enough positions returns reason.
- [ ] empty validation split returns reason.
- [ ] rejected candidate returns reason and MSEs.
- [ ] accepted candidate returns `updated=True`, reason `updated`.
- [ ] bool wrapper still returns expected bool if kept.
- [ ] `keep_rejected_candidate=True` preserves candidate file if implemented.
- [ ] `keep_rejected_candidate=False` deletes candidate file if implemented.

---

# Phase 6: Collect/tuning input validation

## 6.1 Validate collection options if not already done

For `CollectionOptions` or collection entry point, validate:

- [ ] `num_games >= 1`
- [ ] `depth >= 1`
- [ ] `max_moves >= 1`
- [ ] `skip_opening_plies >= 0`
- [ ] `max_move_result in {"draw", "discard"}`

Decide behavior for:

```python
skip_opening_plies >= max_moves
```

Recommended:

- [ ] reject with `ValueError`, unless there is a valid use case.

## 6.2 Tests

Add tests:

- [ ] invalid `num_games`.
- [ ] invalid `depth`.
- [ ] invalid `max_moves`.
- [ ] invalid `skip_opening_plies`.
- [ ] invalid `max_move_result`.
- [ ] valid options still construct/run.

---

# Phase 7: Preserve search/eval and prior hardening

## 7.1 Search/eval untouched

- [ ] Confirm no changes to search/eval modules unless needed for imports/tests.
- [ ] Do not alter engine move selection.

## 7.2 Fix 7 behavior tests

Run:

```bash
uv run --extra dev python -m pytest \
  tests/test_collect.py \
  tests/test_position_db.py \
  tests/test_loss.py \
  tests/test_opening_book.py \
  -m "not slow" -q
```

- [ ] Confirm pass.

## 7.3 Fix 8 TUI runtime tests

Run:

```bash
uv run --extra dev python -m pytest tests/test_tui.py -m "not slow" -q --durations=10
```

- [ ] Confirm pass.
- [ ] Confirm no 3-second sleeps:
  - [ ] `grep -R "pause(delay=3\\|pause(delay=2\\|sleep(3\\|sleep(2" tests/test_tui.py tests`

## 7.4 Fix 10 root bookkeeping tests

Run:

```bash
uv run --extra dev python -m pytest tests/test_root_research_bookkeeping.py -q
```

- [ ] Confirm pass.

---

# Phase 8: Documentation

## 8.1 Add or update status document

Create:

```text
docs/TEXEL_FAIL_LOUD_STATUS.md
```

Include:

- [ ] strict explicit weights behavior,
- [ ] optional default fallback contract,
- [ ] empty DB/training rejection,
- [ ] PositionDB validation rules,
- [ ] SPSAOptions validation,
- [ ] online-learning result reasons,
- [ ] `keep_rejected_candidate` decision,
- [ ] validation commands and results.

## 8.2 Avoid overclaiming

- [ ] Do not claim slow suite green unless run.
- [ ] Do not claim online learning updated unless result says `updated=True`.
- [ ] Do not hide intentionally preserved fallback behavior.

---

# Phase 9: Final validation

## 9.1 Static checks

- [ ] `uv run --extra dev python -m ruff check chess_game tests`
- [ ] `uv run --extra dev python -m mypy chess_game`
- [ ] `uv run --extra dev python -m pylint chess_game --score=y`

## 9.2 Fast suite

- [ ] `uv run --extra dev python -m pytest -m "not slow"`

## 9.3 Texel tests

Run:

```bash
uv run --extra dev python -m pytest \
  tests/test_collect.py \
  tests/test_loss.py \
  tests/test_position_db.py \
  tests/test_spsa.py \
  tests/test_tune.py \
  tests/test_validate.py \
  tests/test_online_learning.py \
  -m "not slow" -q
```

## 9.4 Prior hardening tests

- [ ] `uv run --extra dev python -m pytest tests/test_root_research_bookkeeping.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_tui.py -m "not slow" -q --durations=10`
- [ ] `uv run --extra dev python -m pytest tests/test_opening_book.py -m "not slow" -q`

## 9.5 Slow suite

If feasible:

- [ ] `uv run --extra dev python -m pytest -m slow`

If not feasible:

- [ ] document limitation in `docs/TEXEL_FAIL_LOUD_STATUS.md`.

---

# Phase 10: Completion criteria

This patch is complete only when:

- [ ] Ruff passes.
- [ ] mypy passes.
- [ ] `pylint chess_game` remains 10.00/10 or otherwise acceptable.
- [ ] Full fast suite passes.
- [ ] Explicit missing weights paths fail loudly.
- [ ] Automatic optional tuned-weight fallback remains available only where intended.
- [ ] Empty tuning DB does not produce output weights by default.
- [ ] Empty SPSA optimization data raises a clear error.
- [ ] Empty Texel `k` calibration raises a clear error.
- [ ] `PositionDB.load()` validates old and new JSONL rows.
- [ ] `PositionDB.load()` gives line-numbered errors.
- [ ] `SPSAOptions` validates unsafe values.
- [ ] Online learning exposes structured result reasons or equivalent non-silent diagnostic API.
- [ ] `keep_rejected_candidate` is implemented or removed.
- [ ] Existing valid Texel tests still pass.
- [ ] Existing Fix 7 behavior tests still pass.
- [ ] Existing Fix 8 TUI runtime tests still pass.
- [ ] Existing Fix 10 root re-search tests still pass.
- [ ] No new silent fallback/no-op behavior is introduced.
- [ ] Any intentionally preserved fallback is documented with a clear caller contract.
- [ ] `docs/TEXEL_FAIL_LOUD_STATUS.md` documents changes and validation.

---

# Notes for Claude Code

## No silent success

If training did not happen, do not write weights and do not report success.

## Strict explicit paths

A user-supplied missing file is an error.

## Validate training data

Bad labels must not silently enter Texel.

## Preserve optional auto-load only where intentional

Engine tuned-weight fallback can remain if clearly scoped.

## Keep search/eval out of this patch

Do not touch engine strength behavior.
