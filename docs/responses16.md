# responses16.md — Questions & Issues on the Texel Fail-Loud patch

**Date:** 2026-06-12
**Model:** Claude Opus 4.8 (1M context)
**Re:** `docs/CHESS_ENGINE_TEXEL_FAIL_LOUD_SPEC.md` + `docs/CHESS_ENGINE_TEXEL_FAIL_LOUD_TODO.md`
**Status:** Reviewed both files; no code written. Awaiting decisions below.

---

## Summary

The spec is **accurate** — unlike the earlier FIX10 spec, every quoted snippet
matches the current code, and the referenced test files exist. Verified:

- `weights_io.py`: `load_weights(path)` (line 19) and `load_weights_or_default(path)`
  (line 36) both exist; `load_optional_weights` does not yet.
- `spsa.py`: `SPSAOptions` (line 27, **no `__post_init__`**), `optimize()` (line 100)
  with `if not pairs:` at line 122.
- `tune.py`: `run_tuning()` (line 30) calls
  `load_weights_or_default(config.initial_weights_path)` (line 55) — the dangerous
  explicit-path-via-optional-loader case; `all_pairs()` at 67; `save_weights()` at 81.
- `validate.py`: CLI `--weights required=True` (line 150) +
  `load_weights_or_default(Path(_args.weights))` (line 154) — the exact dangerous
  pattern from the spec.
- `loss.py`: `calibrate_k` (78), `calibrate_and_save_k` (97).
- `online_learning.py`: `keep_rejected_candidate` field (line 37);
  `record_game_and_update_weights(...) -> bool` (line 57).
- `tests/test_spsa.py` and `tests/test_validate.py` both present.

Overall: a clean, well-scoped safety/validation/diagnostics patch. The only real
forks are the three decisions below.

---

## Decisions that change the work

### 1. Online-learning API — backward-compatible wrapper, or breaking change?

`record_game_and_update_weights()` returns `bool` today, and
`tests/test_online_learning.py` references it **15 times** (many assert the bool).
The spec offers both paths.

**Recommendation: the wrapper.** Add
`record_game_and_update_weights_result(...) -> OnlineLearningResult` carrying the
structured `reason`/MSEs, and keep the bool function as a thin
`return ...result(...).updated`. This delivers the diagnostics with minimal test
churn and matches the spec's "preserve existing behavior" theme.

**Question:** wrapper (keep the bool API), or a clean break that rewrites the bool
call sites/tests?

### 2. `keep_rejected_candidate` — implement, or remove?

Important wrinkle found in the code: in the current flow the candidate is an
**in-memory `EvalWeights`** (`candidate = optimize(...)`, online_learning.py:108) and
a file is only ever written **on acceptance** (`save_weights(candidate, weights_path)`,
line 122). There is **no candidate file created before the accept/reject decision**,
so there is nothing to "preserve or delete." The field is currently **unused in
logic** (only the dataclass field + 4 test sites that merely assert it is settable:
test_online_learning.py lines 107/116/122, 368, 583-601).

Implementing the spec's preserve/delete-candidate-file semantics would require
**adding new candidate-file-writing logic that does not exist today** — scope creep
for a safety patch.

**Recommendation: remove it** (and update the ~4 test references).

**Question:** remove (recommended), or do you specifically want the candidate-file
persistence behavior built out (which adds new write/cleanup logic)?

### 3. SPSA reproducibility `seed` — in this patch, or deferred?

The spec marks `seed` as "desirable but secondary." It's a contained but real change:
thread a local `random.Random(seed)` through `optimize()`'s perturbation generation,
replacing module-global `random`.

**Question:** include the seed now, or document it as a follow-up so this patch stays
purely validation/diagnostics (no behavior change to the optimizer's RNG source)?

---

## Confirmation (not a blocker)

### 4. This patch intentionally breaks some existing tests — confirming that's expected

The fail-loud changes alter behavior that current tests encode as the silent path,
e.g.:

- `optimize()` on an empty DB (today returns weights unchanged → will raise),
- `validate --weights <missing>` (today silently uses defaults → will error),
- possibly empty-DB `run_tuning`.

Per the spec ("update call sites/tests... record intentionally changed behavior"),
the plan is to **update those tests to assert the new fail-loud behavior**.
Confirming these are treated as intentional contract changes, not regressions to be
avoided.

---

## Minor notes (no action needed)

- **`CollectionOptions` is already half-validated** — it has `__post_init__` for
  `max_move_result` (collect.py:39-42) but not `num_games`/`depth`/`max_moves`/
  `skip_opening_plies`. Phase 6 just completes it. Also need a decision on
  `skip_opening_plies >= max_moves` (spec recommends reject; confirm there's no valid
  use case).
- **Section 6 (`get_best_move` first-legal fallback):** clear — leave it untouched,
  add the "separate future engine-contract issue" note, per the spec.
- **New repo guardrails this session (FYI for whoever implements):**
  - An **800-line module ceiling** is now enforced (pylint `max-module-lines=800` in
    `pyproject.toml` + `tests/test_module_size_limit.py`). New Texel code is subject
    to it; the Texel files are all small (~100–200 lines), so no risk.
  - I will hold **`pylint chess_game` strict 10.00/10 with structural fixes (no
    pragmas)** per CLAUDE.md — the spec's "or otherwise acceptable" is looser, but the
    project gate is 10.00. New validation adds returns/branches, so watch for
    `R0911`/`R0912` and refactor rather than suppress.

---

## Bottom line

Give three calls — **#1** (wrapper vs break), **#2** (remove vs implement
`keep_rejected_candidate`), **#3** (seed now vs later) — and confirm **#4**, and this
is ready to implement phase-by-phase with the usual gates (ruff, mypy, pylint 10.00,
fast suite, plus the named Texel + Fix7/8/10 preservation runs).
