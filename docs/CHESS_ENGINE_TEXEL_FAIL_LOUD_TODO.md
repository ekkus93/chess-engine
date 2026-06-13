# CHESS_ENGINE_TEXEL_FAIL_LOUD_TODO.md

## Implementation checklist

This TODO is for the Texel fail-loud safety patch.

Keep this patch narrow. Do **not** change search/eval behavior, engine-strength heuristics, make/unmake, bitboards, Zobrist hashing, NNUE, broad Texel algorithms, broad CLI behavior, or broad online-learning architecture.

---

# Phase 0: Baseline validation

## 0.1 Static checks

- [x] `uv run --extra dev python -m ruff check chess_game tests`
- [x] `uv run --extra dev python -m mypy chess_game`
- [x] `uv run --extra dev python -m pylint chess_game --score=y`

## 0.2 Fast suite

- [x] `uv run --extra dev python -m pytest -m "not slow"`

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

- [x] Record pass/fail.
- [x] Record any currently expected behavior that this patch intentionally changes.

## 0.4 Root bookkeeping preservation

- [x] `uv run --extra dev python -m pytest tests/test_root_research_bookkeeping.py -q`

---

# Phase 1: Strict explicit weight loading

## 1.1 Audit weight-loading call sites

Search for:

```bash
grep -R "load_weights_or_default" -n chess_game tests
```

Classify every call site:

- [x] automatic optional tuned-weight cache,
- [x] explicit user-supplied path,
- [x] CLI required path,
- [x] tuning initial weights path,
- [x] online-learning initial/current weights path,
- [x] test fixture.

## 1.2 Define strict helper semantics

Ensure these semantics exist:

```python
load_weights(path: Path) -> EvalWeights
```

- [x] Raises `FileNotFoundError` if missing.
- [x] Raises clear error if JSON malformed.
- [x] Raises clear error if weights invalid.

Optional helper if useful:

```python
load_optional_weights(path: Path | None) -> EvalWeights
```

- [x] Returns defaults only when `path is None`.
- [x] Raises if `path` is provided but missing.

Keep:

```python
load_weights_or_default(path)
```

only for explicitly optional auto-load behavior.

## 1.3 Fix validation CLI

In Texel validation CLI:

- [x] Replace `load_weights_or_default(Path(args.weights))` with strict `load_weights(Path(args.weights))`.
- [x] Missing `--weights` path should fail loudly.
- [x] Malformed weights should fail loudly.
- [x] Do not silently validate default weights when user supplied a path.

## 1.4 Fix tuning initial weights

In `run_tuning()`:

- [x] If `initial_weights_path is None`, use default weights.
- [x] If `initial_weights_path` is provided, call strict `load_weights(path)`.
- [x] Missing supplied initial weights path raises.

## 1.5 Fix online-learning weight load if needed

For online learning:

- [x] Decide whether missing current weights path is valid first-run behavior.
- [x] If missing current path is allowed, make that explicit in the result reason.
- [x] If a user explicitly supplies a path that should exist, fail loudly.
- [x] Do not hide missing paths behind default fallback without reporting.

## 1.6 Tests

Add tests:

- [x] `validate --weights missing.json` raises/fails.
- [x] `run_tuning(initial_weights_path=missing)` raises.
- [x] optional default path still returns defaults when intentionally optional.
- [x] malformed weights still raise.
- [x] valid explicit weights still load.

---

# Phase 2: Empty training data must fail loudly

## 2.1 `run_tuning()` empty DB

In `run_tuning()`:

- [x] After loading or collecting DB, check position count.
- [x] If DB has no positions, raise:
  - [x] `ValueError("Texel tuning DB has no positions; refusing to write tuned weights")`
- [x] Do not write output weights when DB is empty.

## 2.2 Collected empty DB

If `collect_games()` returns/stores zero positions:

- [x] `run_tuning()` should treat this as empty DB and fail.
- [x] Error message should distinguish empty collected DB if easy.

## 2.3 `optimize()` empty pairs

In `spsa.optimize()`:

- [x] If `db.all_pairs()` is empty, raise `ValueError`.
- [x] Do not silently return unchanged weights.

## 2.4 `calibrate_k()` / calibration entry points

- [x] If calibration pairs are empty, raise `ValueError`.
- [x] Do not silently choose `k_min`.
- [x] Ensure CLI/helper calibration paths also fail loudly.

## 2.5 Tests

Add tests:

- [x] `run_tuning()` with empty existing DB raises and writes no weights.
- [x] `run_tuning()` with collection producing zero positions raises and writes no weights.
- [x] `optimize()` with empty DB raises.
- [x] `calibrate_k([])` or equivalent raises.
- [x] Existing non-empty tuning tests still pass.

---

# Phase 3: PositionDB row validation

## 3.1 Implement row validator

In `position_db.py`, add internal validation helper(s):

- [x] validate non-empty `pos` string.
- [x] validate old-format `outcome`.
- [x] validate new-format `total` and `count`.
- [x] include file path and line number in errors.

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

- [x] `pos` exists.
- [x] `pos` is non-empty string.
- [x] `outcome` exists.
- [x] `outcome` is finite.
- [x] `0.0 <= outcome <= 1.0`.

## 3.3 New format validation

For rows like:

```json
{"pos": "...", "total": 3.0, "count": 4}
```

Validate:

- [x] `pos` exists.
- [x] `pos` is non-empty string.
- [x] `total` exists.
- [x] `total` is finite.
- [x] `count` exists.
- [x] `count` is int.
- [x] `count > 0`.
- [x] `0.0 <= total <= count`.

## 3.4 JSON errors

- [x] Catch `json.JSONDecodeError`.
- [x] Re-raise as `ValueError` with path and line number.
- [x] Preserve useful original error info in message or exception chaining.

## 3.5 Ambiguous/mixed rows

Decide and test behavior for rows containing both:

```json
{"pos": "...", "outcome": 0.5, "total": 1.0, "count": 2}
```

Recommended:

- [x] reject ambiguous rows.

Also reject rows with neither valid old nor valid new format.

## 3.6 Tests

Add tests for valid data:

- [x] valid old JSONL loads.
- [x] valid old duplicate rows aggregate.
- [x] valid new JSONL loads.
- [x] valid round-trip still works.

Add tests for invalid data:

- [x] invalid JSON.
- [x] missing `pos`.
- [x] empty `pos`.
- [x] non-string `pos`.
- [x] missing `outcome`/`total`/`count`.
- [x] outcome below 0.
- [x] outcome above 1.
- [x] non-finite outcome.
- [x] count 0.
- [x] negative count.
- [x] non-int count.
- [x] total below 0.
- [x] total greater than count.
- [x] non-finite total.
- [x] ambiguous old+new row.

Each invalid test should assert line-numbered error text.

---

# Phase 4: SPSAOptions validation

## 4.1 Add `__post_init__()`

In `SPSAOptions`, validate:

- [x] `max_iterations >= 1`
- [x] `initial_step_size > 0`
- [x] `step_decay > 0`
- [x] `perturbation_size > 0`
- [x] `perturbation_decay > 0`
- [x] `stability_constant >= 0`
- [x] `batch_size is None or batch_size >= 1`
- [x] `checkpoint_every >= 1`

Also validate floats are finite:

- [x] `initial_step_size`
- [x] `step_decay`
- [x] `perturbation_size`
- [x] `perturbation_decay`
- [x] `stability_constant`

## 4.2 Optional seed

If low-risk, add:

```python
seed: int | None = None
```

and use local RNG for perturbations.

- [x] `rng = random.Random(options.seed)`
- [x] do not use global `random.random()` for perturbations.
- [x] tests cover reproducible perturbation/tuning behavior if feasible.

If not implemented, document as future work.

## 4.3 Tests

Add invalid-option tests:

- [x] `max_iterations=0`
- [x] `initial_step_size=0`
- [x] `step_decay=0`
- [x] `perturbation_size=0`
- [x] `perturbation_decay=0`
- [x] `stability_constant=-1`
- [x] `batch_size=0`
- [x] `checkpoint_every=0`
- [x] NaN/inf float values.

Add valid-option tests:

- [x] default options construct.
- [x] valid custom options construct.
- [x] existing SPSA behavior tests still pass.

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

- [x] `disabled`
- [x] `not_enough_positions`
- [x] `empty_training_split`
- [x] `empty_validation_split`
- [x] `candidate_not_better`
- [x] `candidate_below_threshold`
- [x] `updated`

If some categories are not applicable to current implementation, document why.

## 5.4 Implement or remove `keep_rejected_candidate`

Find:

```python
keep_rejected_candidate: bool = False
```

Choose one:

### Option A: implement

- [ ] If rejected and `keep_rejected_candidate=True`, preserve candidate file. — N/A (Option B chosen)
- [ ] Set `candidate_path` in result. — N/A as file-persistence (the field exists in OnlineLearningResult but is always None)
- [ ] If rejected and `False`, delete candidate file if created. — N/A (Option B chosen)

### Option B: remove (chosen — per docs/replies16.md)

- [x] Remove config field.
- [x] Remove tests/docs referencing it.

Preferred: implement if candidate files already exist in the flow.
Decision: candidate weights are in-memory only (no candidate file ever written), so
Option B (remove) was chosen.

## 5.5 Tests

Add tests:

- [x] disabled returns `updated=False`, reason `disabled`.
- [x] not enough positions returns reason.
- [x] empty validation split returns reason.
- [x] rejected candidate returns reason and MSEs.
- [x] accepted candidate returns `updated=True`, reason `updated`.
- [x] bool wrapper still returns expected bool if kept.
- [ ] `keep_rejected_candidate=True` preserves candidate file if implemented. — N/A (removed, not implemented)
- [ ] `keep_rejected_candidate=False` deletes candidate file if implemented. — N/A (removed, not implemented)

---

# Phase 6: Collect/tuning input validation

## 6.1 Validate collection options if not already done

For `CollectionOptions` or collection entry point, validate:

- [x] `num_games >= 1`
- [x] `depth >= 1`
- [x] `max_moves >= 1`
- [x] `skip_opening_plies >= 0`
- [x] `max_move_result in {"draw", "discard"}`

Decide behavior for:

```python
skip_opening_plies >= max_moves
```

Recommended:

- [x] reject with `ValueError`, unless there is a valid use case.

## 6.2 Tests

Add tests:

- [x] invalid `num_games`.
- [x] invalid `depth`.
- [x] invalid `max_moves`.
- [x] invalid `skip_opening_plies`.
- [x] invalid `max_move_result`.
- [x] valid options still construct/run.

---

# Phase 7: Preserve search/eval and prior hardening

## 7.1 Search/eval untouched

- [x] Confirm no changes to search/eval modules unless needed for imports/tests.
- [x] Do not alter engine move selection.

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

- [x] Confirm pass.

## 7.3 Fix 8 TUI runtime tests

Run:

```bash
uv run --extra dev python -m pytest tests/test_tui.py -m "not slow" -q --durations=10
```

- [x] Confirm pass.
- [x] Confirm no 3-second sleeps:
  - [x] `grep -R "pause(delay=3\\|pause(delay=2\\|sleep(3\\|sleep(2" tests/test_tui.py tests`

## 7.4 Fix 10 root bookkeeping tests

Run:

```bash
uv run --extra dev python -m pytest tests/test_root_research_bookkeeping.py -q
```

- [x] Confirm pass.

---

# Phase 8: Documentation

## 8.1 Add or update status document

Create:

```text
docs/TEXEL_FAIL_LOUD_STATUS.md
```

Include:

- [x] strict explicit weights behavior,
- [x] optional default fallback contract,
- [x] empty DB/training rejection,
- [x] PositionDB validation rules,
- [x] SPSAOptions validation,
- [x] online-learning result reasons,
- [x] `keep_rejected_candidate` decision,
- [x] validation commands and results.

## 8.2 Avoid overclaiming

- [x] Do not claim slow suite green unless run.
- [x] Do not claim online learning updated unless result says `updated=True`.
- [x] Do not hide intentionally preserved fallback behavior.

---

# Phase 9: Final validation

## 9.1 Static checks

- [x] `uv run --extra dev python -m ruff check chess_game tests`
- [x] `uv run --extra dev python -m mypy chess_game`
- [x] `uv run --extra dev python -m pylint chess_game --score=y`

## 9.2 Fast suite

- [x] `uv run --extra dev python -m pytest -m "not slow"`

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

- [x] `uv run --extra dev python -m pytest tests/test_root_research_bookkeeping.py -q`
- [x] `uv run --extra dev python -m pytest tests/test_tui.py -m "not slow" -q --durations=10`
- [x] `uv run --extra dev python -m pytest tests/test_opening_book.py -m "not slow" -q`

## 9.5 Slow suite

If feasible:

- [x] `uv run --extra dev python -m pytest -m slow`

If not feasible:

- [ ] document limitation in `docs/TEXEL_FAIL_LOUD_STATUS.md`. — N/A (slow suite was run: 171 passed)

---

# Phase 10: Completion criteria

This patch is complete only when:

- [x] Ruff passes.
- [x] mypy passes.
- [x] `pylint chess_game` remains 10.00/10 or otherwise acceptable.
- [x] Full fast suite passes.
- [x] Explicit missing weights paths fail loudly.
- [x] Automatic optional tuned-weight fallback remains available only where intended.
- [x] Empty tuning DB does not produce output weights by default.
- [x] Empty SPSA optimization data raises a clear error.
- [x] Empty Texel `k` calibration raises a clear error.
- [x] `PositionDB.load()` validates old and new JSONL rows.
- [x] `PositionDB.load()` gives line-numbered errors.
- [x] `SPSAOptions` validates unsafe values.
- [x] Online learning exposes structured result reasons or equivalent non-silent diagnostic API.
- [x] `keep_rejected_candidate` is implemented or removed.
- [x] Existing valid Texel tests still pass.
- [x] Existing Fix 7 behavior tests still pass.
- [x] Existing Fix 8 TUI runtime tests still pass.
- [x] Existing Fix 10 root re-search tests still pass.
- [x] No new silent fallback/no-op behavior is introduced.
- [x] Any intentionally preserved fallback is documented with a clear caller contract.
- [x] `docs/TEXEL_FAIL_LOUD_STATUS.md` documents changes and validation.

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
