# CHESS_ENGINE_TEXEL_FAIL_LOUD_SPEC.md

## Purpose

This document specifies a focused **Texel fail-loud safety patch** for the chess engine.

The current engine, search hardening, Fix 7 behavior tests, Fix 8 fast-suite runtime work, and Fix 10 root re-search bookkeeping work are in much better shape. The Texel subsystem is also structurally good and well-tested.

However, the latest review found several dangerous quiet fallback / silent no-op behaviors in Texel and weight-loading paths:

1. Explicitly supplied missing weight files can silently fall back to default weights.
2. Texel tuning can silently write output weights even when the training DB is empty.
3. `PositionDB.load()` accepts malformed or invalid data without enough validation.
4. `SPSAOptions` accepts invalid values that can silently no-op or crash later.
5. Online learning returns a bare `False` for many unrelated reasons.
6. Some caller paths cannot distinguish “training did nothing” from “training succeeded.”

These are operational safety problems. They can make a developer believe that a tuning/validation/online-learning run used real data and real weights when it actually used defaults, skipped work, or accepted bad input.

This patch should make Texel and explicit weight-loading behavior **fail loudly by default**.

---

## Hard scope boundaries

### In scope

- Strict handling for explicitly supplied weight paths.
- Preserve safe default fallback only for the automatic engine tuned-weights cache.
- Reject empty Texel training DBs by default.
- Reject empty SPSA training batches by default.
- Validate `PositionDB` JSONL rows with line-numbered errors.
- Validate `SPSAOptions`.
- Improve online-learning result reporting so callers can tell why an update did not happen.
- Add focused tests for these fail-loud behaviors.
- Preserve existing Texel public behavior only where it is intentionally safe.
- Preserve all search/eval behavior.

### Out of scope

Do **not** implement:

- search/eval changes,
- engine-strength tuning,
- make/unmake search,
- bitboards,
- true Zobrist hashing,
- NNUE/neural eval,
- broad Texel algorithm changes,
- broad CLI redesign,
- broad online-learning redesign,
- broad database format rewrite.

This patch is about safety, validation, and diagnostics only.

---

# Current dangerous behaviors

## 1. Explicit missing weights can silently use defaults

Current helper:

```python
def load_weights_or_default(path: Path | None) -> EvalWeights:
    """Load weights if path exists, else return EvalWeights.default()."""
    if path is None or not path.exists():
        return EvalWeights.default()
    return load_weights(path)
```

This is acceptable only for optional automatic tuned-weight loading, for example:

```text
chess_game/chess/data/tuned_weights.json
```

It is **not acceptable** for explicit user-supplied paths.

Bad behavior examples:

```bash
python -m chess_game.texel.validate --weights typo.json
```

This should fail because `--weights` is explicit. It must not silently validate default weights.

Similarly:

```python
TuningConfig(initial_weights_path=Path("typo.json"))
```

should fail if the path is supplied but missing.

## Required behavior

Introduce separate semantics:

### Optional auto-load behavior

For engine automatic tuned-weight loading:

```python
load_weights_or_default(None) -> EvalWeights.default()
load_weights_or_default(missing_auto_path) -> EvalWeights.default()
```

This can remain if it is used only in explicitly optional auto-load contexts.

### Explicit user-supplied behavior

For explicit paths:

```python
load_weights(path)
```

must raise if the file is missing, malformed, or invalid.

Add a helper if useful:

```python
def load_optional_weights(path: Path | None) -> EvalWeights:
    if path is None:
        return EvalWeights.default()
    return load_weights(path)
```

but do not use `load_weights_or_default()` for explicit user inputs.

## Acceptance criteria

- `validate --weights missing.json` fails loudly.
- `TuningConfig(initial_weights_path=missing_path)` fails loudly.
- Engine automatic fallback to defaults remains available only where intentionally optional.
- Tests prove explicit missing paths do not silently use defaults.

---

# 2. Empty Texel training can silently produce output weights

Current `run_tuning()` flow can produce output even when no positions exist:

```python
pairs = db.all_pairs()
initial_mse = mean_squared_error(pairs, weights, opts=loss_opts) if pairs else 0.0
...
tuned = optimize(weights, db, spsa_opts)
...
final_mse = mean_squared_error(pairs, tuned, opts=loss_opts) if pairs else 0.0
save_weights(tuned, config.output_weights_path)
```

Current `optimize()` can return original weights if `pairs` is empty:

```python
if not pairs:
    break
```

This is dangerous. It creates a weights file even though no training happened.

## Required behavior

Fail loudly by default when:

- existing DB has no positions,
- collected DB has no positions,
- `optimize()` receives no training pairs,
- `calibrate_k()` / `calibrate_and_save_k()` receives no pairs.

Suggested errors:

```python
raise ValueError("Texel tuning DB has no positions; refusing to write tuned weights")
```

```python
raise ValueError("SPSA optimize requires at least one training position")
```

```python
raise ValueError("Cannot calibrate Texel k with no positions")
```

If an escape hatch is needed, it must be explicit:

```python
allow_empty_db: bool = False
```

Default must remain fail-loud.

## Acceptance criteria

- Empty DB tuning does not write output weights.
- Empty collection result does not write output weights unless an explicit escape hatch exists.
- `optimize()` does not silently return unchanged weights for empty data.
- Calibration on empty data raises a clear error.
- Tests cover these behaviors.

---

# 3. `PositionDB.load()` needs row validation

Current load logic accepts invalid rows too easily:

```python
rec = json.loads(line)
pos = rec["pos"]
...
if "outcome" in rec:
    db._data[pos].add(float(rec["outcome"]))
else:
    db._data[pos].total += float(rec["total"])
    db._data[pos].count += int(rec["count"])
```

Problems:

- no line-number context,
- no validation that `pos` is a non-empty string,
- no validation that old-format `outcome` is finite and in range,
- no validation that new-format `count > 0`,
- no validation that `0 <= total <= count`,
- bad `count=0` can later make `mean` look like a neutral draw.

## Required validation

`PositionDB.load(path)` should validate every non-empty row.

Rules:

```text
pos:
  - must be a non-empty string

old format:
  - exactly or effectively contains "pos" and "outcome"
  - outcome must be finite float
  - 0.0 <= outcome <= 1.0

new format:
  - contains "pos", "total", and "count"
  - count must be int > 0
  - total must be finite float
  - 0.0 <= total <= count
```

Malformed rows should raise:

```python
ValueError(f"{path}:{line_no}: invalid PositionDB row: ...")
```

JSON parsing errors should also include path and line number.

## Backward compatibility

Keep support for old JSONL format:

```json
{"pos": "fen", "outcome": 0.5}
```

Keep support for new JSONL format:

```json
{"pos": "fen", "total": 3.0, "count": 4}
```

But validate both.

## Acceptance criteria

- Valid old JSONL still loads.
- Valid new JSONL still loads.
- Invalid JSON raises line-numbered `ValueError`.
- Missing `pos` raises line-numbered `ValueError`.
- Empty `pos` raises line-numbered `ValueError`.
- `outcome < 0` / `outcome > 1` raises.
- `count <= 0` raises.
- `total < 0` raises.
- `total > count` raises.
- Tests cover line-numbered errors.

---

# 4. `SPSAOptions` needs validation

Current SPSA options can silently no-op or crash later.

Examples:

```python
batch_size=0        # empty sample -> no-op
max_iterations=0   # no-op
checkpoint_every=0 # modulo by zero
perturbation_size=0 # division by zero
```

## Required behavior

Add `__post_init__()` validation to `SPSAOptions`.

Minimum validation:

```text
max_iterations >= 1
initial_step_size > 0
step_decay > 0
perturbation_size > 0
perturbation_decay > 0
stability_constant >= 0
batch_size is None or batch_size >= 1
checkpoint_every >= 1
```

If a parameter is not finite, reject it.

## Randomness / reproducibility

SPSA currently uses module-global randomness. For reproducible tuning, add an optional seed if feasible:

```python
seed: int | None = None
```

Then use:

```python
rng = random.Random(options.seed)
```

for perturbation generation.

This is desirable but secondary to validation. If adding seed would touch too much code, keep it as a clearly documented future task.

## Acceptance criteria

- Invalid `SPSAOptions` raise `ValueError` at construction.
- Empty batch/no-op configurations are rejected.
- Tests cover invalid values.
- Existing valid SPSA tests still pass.

---

# 5. Online learning should return reasons, not a bare bool

Current online learning returns only:

```python
True
False
```

A `False` may mean many different things:

- learning disabled,
- not enough data,
- validation set empty,
- candidate worsened,
- candidate failed improvement threshold,
- weights file missing and defaults were used,
- optimizer no-op,
- candidate rejected,
- some other guard path.

This is too quiet.

## Required behavior

Introduce a result object:

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

Possible reason values:

```text
disabled
not_enough_positions
empty_training_split
empty_validation_split
candidate_not_better
candidate_below_threshold
updated
```

If backwards compatibility is needed, keep a wrapper:

```python
def record_game_and_update_weights(...) -> bool:
    return record_game_and_update_weights_result(...).updated
```

or update call sites/tests if the project can tolerate the API change.

## `keep_rejected_candidate`

`OnlineLearningConfig.keep_rejected_candidate` currently appears unused.

Required behavior:

- implement it, or
- remove it if not needed.

If implemented:

```text
keep_rejected_candidate=True:
  preserve candidate weights file and report candidate_path

keep_rejected_candidate=False:
  delete candidate file on rejection if one was created
```

## Acceptance criteria

- Callers can inspect why online learning did not update.
- Tests cover disabled, not enough positions, candidate rejected, candidate accepted.
- `keep_rejected_candidate` is either implemented or removed.
- No silent `False` remains in the primary API.

---

# 6. `get_best_move()` first-legal fallback should be reviewed separately

Current engine behavior includes a fallback to first legal move if root search returns no move while legal moves exist.

This is risky because it can mask differences between:

- terminal/draw state,
- no legal moves,
- timeout,
- internal search bug.

However, changing this is search/engine contract work, not Texel fail-loud work.

## Required behavior for this patch

Do not change this fallback in this Texel patch unless there is a directly failing test.

Instead:

- document it as a separate future engine-contract issue,
- do not introduce new silent fallback patterns.

Suggested future task:

```text
Separate get_best_move() from get_best_move_or_first_legal()
```

---

# 7. Preserve existing behavior and validation

This patch must preserve:

- search/eval behavior,
- Fix 7 behavior tests,
- Fix 8 fast-suite runtime,
- Fix 10 root re-search bookkeeping tests,
- existing valid Texel workflows,
- old and new PositionDB JSONL compatibility.

## Required validation

Run:

```bash
uv run --extra dev python -m ruff check chess_game tests
uv run --extra dev python -m mypy chess_game
uv run --extra dev python -m pylint chess_game --score=y
```

Run fast suite:

```bash
uv run --extra dev python -m pytest -m "not slow"
```

Run Texel tests:

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

Run root bookkeeping tests:

```bash
uv run --extra dev python -m pytest tests/test_root_research_bookkeeping.py -q
```

If feasible, run slow suite after any broad dependency changes:

```bash
uv run --extra dev python -m pytest -m slow
```

---

# Acceptance criteria

This patch is complete only when:

1. Ruff passes.
2. mypy passes.
3. `pylint chess_game` remains 10.00/10 or otherwise acceptable.
4. Full fast suite passes.
5. Explicit missing weights paths fail loudly.
6. Automatic optional tuned-weight fallback remains available only where intended.
7. Empty tuning DB does not produce output weights by default.
8. Empty SPSA optimization data raises a clear error.
9. Empty Texel `k` calibration raises a clear error.
10. `PositionDB.load()` validates old and new JSONL rows.
11. `PositionDB.load()` gives line-numbered errors.
12. `SPSAOptions` validates unsafe values.
13. Online learning exposes structured result reasons or an equivalent non-silent diagnostic API.
14. `keep_rejected_candidate` is implemented or removed.
15. Existing valid Texel tests still pass.
16. Existing Fix 7 behavior tests still pass.
17. Existing Fix 8 TUI runtime tests still pass.
18. Existing Fix 10 root re-search tests still pass.
19. No new silent fallback/no-op behavior is introduced.
20. Any intentionally preserved fallback is documented with a clear caller contract.

---

# Notes for Claude Code

## Fail loud by default

A missing explicit weights file, empty DB, or invalid row should stop the run.

## Keep optional fallback narrow

Default weights are okay only for clearly optional auto-load contexts.

## Do not hide training no-ops

If no training happened, do not write output weights and do not report success.

## Preserve compatibility where valid

Old/new PositionDB formats should still load when valid.

## Do not touch search/eval

This patch is Texel safety, not engine-strength tuning.
