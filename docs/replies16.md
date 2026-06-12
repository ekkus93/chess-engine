# replies16.md

# Replies to Claude Code on the Texel Fail-Loud Patch

Claude Code’s read-through is accurate. The Texel fail-loud spec matches the current code, and the questions are the right ones. This patch should stay focused on validation, diagnostics, and preventing silent success. It should not turn into a broad optimizer or engine rewrite.

---

## 1. Online-learning API: use the backward-compatible wrapper

Use the wrapper approach.

Add a new structured-result API:

```python
def record_game_and_update_weights_result(...) -> OnlineLearningResult:
    ...
```

and keep the current bool-returning API as a compatibility wrapper:

```python
def record_game_and_update_weights(...) -> bool:
    return record_game_and_update_weights_result(...).updated
```

This gives us the fail-loud/diagnostic behavior we want without creating unnecessary call-site churn. Existing users/tests that only care whether an update happened can keep using the bool wrapper. New tests and future code should prefer the structured result.

The result object should make failures explicit:

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

Use stable reason strings or an enum. Reason strings are fine if tests cover them.

Minimum reasons:

```text
disabled
not_enough_positions
empty_training_split
empty_validation_split
candidate_not_better
candidate_below_threshold
updated
```

If the current implementation cannot distinguish two of these cleanly, either add the needed split or document why that reason is not applicable.

---

## 2. `keep_rejected_candidate`: remove it

Remove `keep_rejected_candidate`.

Claude Code’s analysis is right: the current implementation does not write a candidate file before the accept/reject decision. The candidate is in-memory until acceptance, so there is nothing to preserve or delete.

Implementing `keep_rejected_candidate=True` would require adding new candidate-file writing and cleanup semantics that do not exist today. That is scope creep for this safety patch.

Do this instead:

- remove `keep_rejected_candidate` from `OnlineLearningConfig`,
- update tests that merely assert it is settable,
- do not add new candidate persistence behavior,
- if future candidate inspection is desired, make it a separate explicit feature.

The fail-loud patch should reduce hidden behavior, not add another file lifecycle.

---

## 3. SPSA reproducibility seed: include it if it stays small

Include `seed: int | None = None` in `SPSAOptions` if the change is straightforward.

This is not just convenience. SPSA is stochastic, and tuning runs should be reproducible when debugging or comparing changes.

Preferred implementation:

```python
@dataclass
class SPSAOptions:
    ...
    seed: int | None = None
```

Then in `optimize()`:

```python
rng = random.Random(options.seed)
```

Use that local RNG for perturbation generation instead of module-global `random.random()`.

This should not be a broad behavior change. With `seed=None`, the local RNG still uses system entropy, so normal unseeded behavior remains random. With `seed=123`, tests and experiments become reproducible.

Add one focused test:

```text
same seed + same DB + same options -> same tuned weights
```

and optionally:

```text
different seeds can produce different perturbation paths
```

Do not overbuild this. If adding the seed causes broad churn, document it as follow-up, but my preference is to include it now because it is contained and useful.

---

## 4. Existing tests that encode silent behavior should be updated

Confirmed: this patch intentionally changes behavior that some existing tests may currently encode.

These are intentional contract changes, not regressions:

- `optimize()` on an empty DB should raise instead of returning unchanged weights.
- `validate --weights missing.json` should fail instead of validating defaults.
- `run_tuning()` with an empty DB should raise and should not write output weights.
- empty `calibrate_k()` / calibration entry points should raise instead of returning a misleading default result.

Update those tests to assert the new fail-loud behavior.

The principle is:

```text
A run that did not train, did not validate the requested file, or had no data must not look successful.
```

---

## 5. CollectionOptions validation

Complete the validation.

`CollectionOptions` already validates `max_move_result`; extend it to validate:

```text
num_games >= 1
depth >= 1
max_moves >= 1
skip_opening_plies >= 0
max_move_result in {"draw", "discard"}
```

Reject:

```python
skip_opening_plies >= max_moves
```

unless Claude Code finds a real valid use case. I do not see a useful Texel-training scenario where every move is skipped and zero positions are expected. If someone wants to test empty collection, that should be an explicit test fixture, not a valid training configuration.

Use `ValueError` with clear messages.

---

## 6. `get_best_move()` first-legal fallback

Leave it untouched in this patch.

The spec is correct: this is a separate future engine-contract issue, not Texel fail-loud work. Do not mix search/eval behavior into this patch.

If documenting it, use a note like:

```text
Future engine-contract issue: split get_best_move() from get_best_move_or_first_legal() so fallback behavior is explicit.
```

No production search/eval changes for this patch.

---

## 7. Pylint and module-size guardrails

Use the strict project gate:

```bash
uv run --extra dev python -m pylint chess_game
```

Target:

```text
10.00/10
```

Do not add pragmas to dodge design warnings. Refactor instead.

Also respect the 800-line module ceiling. New Texel code should stay small, so this should not be hard.

Watch for these likely Pylint issues:

```text
too-many-return-statements
too-many-branches
too-many-arguments
too-many-locals
```

If the new `PositionDB.load()` validation grows too branchy, split it into small helpers:

```python
_validate_position_record(...)
_load_old_format_record(...)
_load_new_format_record(...)
_raise_row_error(...)
```

If online learning result logic becomes branch-heavy, split reason decisions into helpers.

---

# Final implementation direction

Use this implementation plan:

1. Baseline:
   ```bash
   uv run --extra dev python -m ruff check chess_game tests
   uv run --extra dev python -m mypy chess_game
   uv run --extra dev python -m pylint chess_game
   uv run --extra dev python -m pytest -m "not slow"
   ```

2. Strict explicit weight loading:
   - explicit missing paths raise,
   - optional default fallback remains only for automatic tuned-weight loading.

3. Empty-data fail-loud:
   - empty tuning DB raises,
   - empty SPSA data raises,
   - empty calibration raises,
   - no output weights written on empty training.

4. PositionDB validation:
   - old/new JSONL compatibility preserved,
   - invalid rows rejected with path and line number.

5. SPSAOptions validation:
   - validate unsafe values,
   - include `seed` if contained.

6. Online learning:
   - add `OnlineLearningResult`,
   - add result-returning API,
   - keep bool wrapper,
   - remove `keep_rejected_candidate`.

7. CollectionOptions validation:
   - reject invalid numeric config,
   - reject `skip_opening_plies >= max_moves`.

8. Preserve prior hardening:
   ```bash
   uv run --extra dev python -m pytest tests/test_root_research_bookkeeping.py -q
   uv run --extra dev python -m pytest tests/test_tui.py -m "not slow" -q --durations=10
   uv run --extra dev python -m pytest      tests/test_collect.py      tests/test_loss.py      tests/test_position_db.py      tests/test_spsa.py      tests/test_tune.py      tests/test_validate.py      tests/test_online_learning.py      -m "not slow" -q
   ```

9. Document in:
   ```text
   docs/TEXEL_FAIL_LOUD_STATUS.md
   ```

---

# Bottom line

The decisions are:

1. **Online learning:** add structured result API and keep bool wrapper.
2. **`keep_rejected_candidate`:** remove it.
3. **SPSA seed:** include it if contained; otherwise document as follow-up, but preference is include now.
4. **Silent-behavior tests:** update them to assert fail-loud behavior.
5. **CollectionOptions:** finish validation and reject `skip_opening_plies >= max_moves`.
6. **Search/eval fallback:** leave untouched.

The goal is to make Texel impossible to misread: missing explicit files, empty training data, invalid DB rows, invalid optimizer options, and rejected online-learning candidates should all be visible and diagnosable.
