# Texel Fail-Loud — Implementation Status

**Date:** 2026-06-12
**Model:** Claude Opus 4.8 (1M context)
**Spec/TODO:** `docs/CHESS_ENGINE_TEXEL_FAIL_LOUD_SPEC.md`, `docs/CHESS_ENGINE_TEXEL_FAIL_LOUD_TODO.md`
**Decisions:** `docs/replies16.md` (answers to `docs/responses16.md`)

This patch makes Texel tuning and explicit weight loading **fail loudly by default**:
missing files, empty data, and malformed rows raise clear errors instead of silently
falling back to defaults or no-op'ing. Search and evaluation logic are unchanged.

## What changed

### Strict explicit weight loading (`chess_game/texel/weights_io.py`)
- `load_weights(path)` raises `FileNotFoundError` if the path is missing and
  `ValueError` (naming the path) on malformed/non-dict/invalid-JSON content.
- `load_optional_weights(path | None)` returns defaults **only** when `path is None`;
  a provided-but-missing path still raises.
- `load_weights_or_default(path | None)` is the **intentionally silent** loader,
  retained only for the automatic tuned-weight cache (`ai.py` `TUNED_WEIGHTS_PATH`)
  and online learning's default `weights_path` (which *is* that cache). First-run
  absence yields defaults there by design.
- CLI entry points that take an explicit `--weights` (`validate.py`) use the strict
  loader; `tune.py`/`loss.py` use `load_optional_weights` for their optional initial
  weights.

### Optional default-fallback contract
The only places that fall back to default weights without raising are the tuned-weight
**auto cache** (`ai.py:130`) and online learning's default cache path. Every explicit,
user-supplied path is strict. This is preserved deliberately, not an oversight.

### Empty-data rejection
- `spsa.optimize()` raises `ValueError("SPSA optimize requires at least one training
  position")` instead of returning the unchanged input weights.
- `loss.calibrate_k()` raises on an empty pair list.
- `tune.run_tuning()` raises (and writes **no** output weights) when the existing DB is
  empty or a collection run produced zero positions.

### `PositionDB.load()` row validation (`position_db.py`)
Every non-blank JSONL row is validated; errors are **line-numbered** as
`"{path}:{line_no}: invalid PositionDB row: {reason}"`. Rules:
- `pos` must be a non-empty string.
- Old format: `outcome` must be a finite number in `[0, 1]` (bools rejected).
- New format: `count` must be an `int > 0`, `total` a finite number in `[0, count]`
  (bools rejected).
- A row with both `outcome` and `total`/`count` is ambiguous and rejected.
- A row with neither is rejected.
- Invalid JSON is wrapped with the line number.
- Blank/whitespace-only lines are skipped (not an error).

### `SPSAOptions` validation (`spsa.py`)
`__post_init__` rejects values that would silently no-op or crash later:
`max_iterations >= 1`; `initial_step_size`, `step_decay`, `perturbation_size`,
`perturbation_decay` finite and `> 0`; `stability_constant` finite and `>= 0`;
`batch_size` is `None` or `>= 1`; `checkpoint_every >= 1`. NaN/inf are rejected.
A `seed: int | None` field seeds the perturbation RNG so a tuning run is reproducible
(`seed=None` keeps system-entropy behavior).

### Online-learning result reasons (`online_learning.py`)
- New `OnlineLearningResult` (`updated`, `reason`, `positions`, `baseline_val_mse`,
  `candidate_val_mse`, `candidate_path`) and
  `record_game_and_update_weights_result()` report a distinct `REASON_*` for every
  non-update path: `disabled`, `not_enough_positions`, `empty_validation_split`,
  `empty_training_split`, `candidate_not_better`, `candidate_below_threshold`,
  `updated`.
- `record_game_and_update_weights()` remains as a **bool wrapper** over
  `result.updated`, so `self_play.py` and `tui_game.py` callers are unchanged.
- `candidate_path` is always `None` today — rejected candidates live in memory and are
  never written to disk.

### `keep_rejected_candidate`: removed
The field was never implemented (no candidate file exists to keep or delete).
Implementing it would mean new candidate-file write/cleanup semantics — scope creep for
a safety patch — so per `replies16.md` it was **removed** from `OnlineLearningConfig`.

### `CollectionOptions` validation (`collect.py`)
`__post_init__` now also rejects `num_games < 1`, `depth < 1`, `max_moves < 1`,
`skip_opening_plies < 0`, and `skip_opening_plies >= max_moves` (which would skip every
game's positions), in addition to the existing `max_move_result` check.

## Tests added
- `tests/test_weights_fail_loud.py`
- `tests/test_texel_empty_data.py`
- `tests/test_position_db_validation.py`
- `tests/test_spsa_validation.py`
- `tests/test_online_learning_result.py`
- `tests/test_collection_options_validation.py`

Silent-behavior tests that previously asserted a fallback/no-op were updated to assert
the new fail-loud behavior (e.g. `test_validate.py`, `test_online_learning.py`).

## Validation results (2026-06-12)
- `ruff check chess_game tests` — **passed**.
- `mypy chess_game` — **passed** (98 source files).
- `pylint chess_game` — **10.00/10** (no pragmas; structural fixes only).
- Fast suite `pytest -m "not slow"` — **1093 passed, 171 deselected**.
- Texel suite (collect/loss/position_db/spsa/tune/validate/online_learning) —
  **91 passed**.
- Prior hardening: `test_root_research_bookkeeping.py`, `test_opening_book.py` —
  **44 passed**; `test_tui.py` (Fix 8 runtime) — **31 passed**.

## Limitations / not claimed
- **Slow suite (`pytest -m slow`) was not run** as part of this patch. No claim is made
  about slow AI-regression status here.
- No search or evaluation behavior was changed; `get_best_move`'s own internal fallback
  was intentionally left untouched.
