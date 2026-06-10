# CHESS_ENGINE_SLOW_STRENGTH_FIX9_TODO.md

## Implementation checklist

This TODO is for the Fix 9 slow-suite engine-strength triage patch.

Keep this patch narrow. Do **not** implement make/unmake search, bitboards, true Zobrist hashing, NNUE, broad search rewrites, broad evaluation rewrites, broad TUI changes, or broad Texel changes.

---

# Phase 0: Baseline reproduction

## 0.1 Static checks

- [ ] `uv run --extra dev python -m ruff check chess_game tests`
- [ ] `uv run --extra dev python -m mypy chess_game`
- [ ] `uv run --extra dev python -m pylint chess_game/texel --score=y`

## 0.2 Fast suite

- [ ] `uv run --extra dev python -m pytest -m "not slow"`
- [ ] Confirm Fix 8 fast-suite runtime work remains intact.

## 0.3 Reproduce targeted slow failures

Run:

```bash
uv run --extra dev python -m pytest \
  tests/test_ai_endgame1_regressions.py::test_endgame1_search_prefers_cutoff_before_starting_pawn_race \
  tests/test_ai_quality.py::test_simple_quality_benchmark_prefers_hanging_rook_capture \
  tests/test_ai_strategy6_regressions.py::test_strategy6_search_keeps_king_safer_than_g_pawn_lunge_in_transition \
  tests/test_ai_strategy6_regressions.py::test_strategy6_search_prefers_clearer_knight_route_over_na7_in_transition \
  tests/test_ai_strategy6_regressions.py::test_strategy6_search_prefers_clean_rook_capture_during_conversion \
  tests/test_ai_strategy7_regressions.py::test_strategy7_search_prefers_only_blockade_move_in_passer_race \
  tests/test_ai_strategy7_regressions.py::test_strategy7_search_prefers_stopping_enemy_race_over_wrong_side_check \
  tests/test_ai_strategy8_regressions.py::test_strategy8_search_demotes_flank_poke_when_castling_is_available \
  -q
```

- [ ] Record expected move.
- [ ] Record actual move.
- [ ] Record search depth/options used by each test.

## 0.4 Run related files

- [ ] `uv run --extra dev python -m pytest tests/test_ai_quality.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_endgame1_regressions.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy6_regressions.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy7_regressions.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy8_regressions.py -q`

---

# Phase 1: Add root-candidate diagnostics

## 1.1 Decide location

Add diagnostics in one of:

- [ ] `tests/helpers/`
- [ ] a local helper in the relevant regression test file,
- [ ] a dev-only module under `chess_game/chess/` if already acceptable.

Do not add public UI/API surface unless necessary.

## 1.2 Minimum diagnostic data

For each relevant root candidate, record:

- [ ] move,
- [ ] root search score,
- [ ] static evaluation after move,
- [ ] selected/best move flag.

If low-risk, also record:

- [ ] move-order score,
- [ ] material/capture delta,
- [ ] king-safety contribution,
- [ ] passed-pawn/race contribution,
- [ ] endgame contribution.

## 1.3 Use diagnostics on all 8 failures

For each failing test:

- [ ] Generate top root candidates.
- [ ] Compare expected move vs actual move.
- [ ] Identify which scoring/eval component explains the difference.
- [ ] Decide:
  - [ ] real engine regression,
  - [ ] over-specific test,
  - [ ] test setup bug.

---

# Phase 2: Fix hanging-rook capture first

## 2.1 Reproduce

- [ ] Run:
  - [ ] `uv run --extra dev python -m pytest tests/test_ai_quality.py::test_simple_quality_benchmark_prefers_hanging_rook_capture -q`
- [ ] Confirm expected `Qxd5` vs actual move.

## 2.2 Diagnose

- [ ] Compare root candidates:
  - [ ] `Qxd5`,
  - [ ] actual move,
  - [ ] other top candidates.
- [ ] Check:
  - [ ] material evaluation,
  - [ ] capture valuation,
  - [ ] queen activity/check bonus,
  - [ ] king-safety bonus,
  - [ ] quiescence result,
  - [ ] perspective/sign handling.

## 2.3 Fix narrowly

Use the smallest general fix:

- [ ] correct material/capture scoring if wrong,
- [ ] reduce excessive bonus that overpowers rook capture if wrong,
- [ ] fix root scoring/perspective if wrong,
- [ ] fix quiescence/capture handling if wrong.

Do not hardcode this position.

## 2.4 Validate

- [ ] Hanging-rook test passes.
- [ ] `uv run --extra dev python -m pytest tests/test_ai_quality.py -q` passes.
- [ ] Fast suite still passes.

---

# Phase 3: Fix castling vs flank-poke failure

## 3.1 Reproduce

- [ ] Run:
  - [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy8_regressions.py::test_strategy8_search_demotes_flank_poke_when_castling_is_available -q`
- [ ] Confirm actual move is `a2a4` or current bad flank-pawn move.

## 3.2 Diagnose

- [ ] Compare:
  - [ ] castling move(s),
  - [ ] `a2a4`,
  - [ ] other top root candidates.
- [ ] Check:
  - [ ] castling/king-safety value,
  - [ ] flank pawn expansion bonus,
  - [ ] development bonus,
  - [ ] leaf eval after candidate moves,
  - [ ] move ordering vs final search score.

## 3.3 Fix narrowly

Prefer:

- [ ] strengthen king-safety/castling evaluation in unsafe transition positions,
- [ ] reduce premature flank-pawn expansion bonus when king is uncastled,
- [ ] fix root/leaf evaluation if castling is undervalued.

Do not hardcode `a2a4`.

## 3.4 Validate

- [ ] Test no longer chooses `a2a4`.
- [ ] Related strategy8 tests pass.
- [ ] Fast suite still passes.

---

# Phase 4: Triage Strategy6 failures

## 4.1 Reproduce each

- [ ] `test_strategy6_search_keeps_king_safer_than_g_pawn_lunge_in_transition`
- [ ] `test_strategy6_search_prefers_clearer_knight_route_over_na7_in_transition`
- [ ] `test_strategy6_search_prefers_clean_rook_capture_during_conversion`

## 4.2 Diagnose each

For each test:

- [ ] Record expected move.
- [ ] Record actual move.
- [ ] Generate root-candidate diagnostics.
- [ ] Identify shared scoring cause if any.

## 4.3 Fix or rewrite

For each test:

- [ ] Fix real engine regression, or
- [ ] rewrite over-specific exact-move assertion to meaningful invariant.

Acceptable invariants:

- [ ] avoid known unsafe pawn lunge,
- [ ] choose one of acceptable safe king/piece-development moves,
- [ ] prefer clean material conversion,
- [ ] avoid clearly inferior knight route.

## 4.4 Validate

- [ ] Strategy6 targeted tests pass.
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy6_regressions.py -q` passes.

---

# Phase 5: Triage Strategy7 passer-race failures

## 5.1 Reproduce each

- [ ] `test_strategy7_search_prefers_only_blockade_move_in_passer_race`
- [ ] `test_strategy7_search_prefers_stopping_enemy_race_over_wrong_side_check`

## 5.2 Diagnose each

For each test:

- [ ] Compare expected blockade/stopping move vs actual move.
- [ ] Check passed-pawn urgency.
- [ ] Check promotion race timing.
- [ ] Check excessive check/tempo bonus.
- [ ] Check king distance/blockade evaluation.

## 5.3 Fix or rewrite

Use narrow general fixes:

- [ ] improve enemy passer threat penalty,
- [ ] improve blockade urgency,
- [ ] reduce distracting check bonus if it ignores promotion race,
- [ ] improve pawn-race horizon handling if simple.

Or rewrite exact move requirement if too specific.

## 5.4 Validate

- [ ] Strategy7 targeted tests pass.
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy7_regressions.py -q` passes.

---

# Phase 6: Triage endgame cutoff failure

## 6.1 Reproduce

- [ ] `test_endgame1_search_prefers_cutoff_before_starting_pawn_race`

## 6.2 Diagnose

- [ ] Compare expected cutoff move vs actual move.
- [ ] Check king distance to pawn race.
- [ ] Check pawn-race urgency.
- [ ] Check passed-pawn stop/blockade incentives.
- [ ] Check promotion timing if available.

## 6.3 Fix or rewrite

Use narrow general fixes:

- [ ] improve king cutoff evaluation,
- [ ] improve pawn-race urgency,
- [ ] improve king-pawn endgame heuristic,
- [ ] rewrite exact-move assertion if overly specific.

## 6.4 Validate

- [ ] Endgame targeted test passes.
- [ ] `uv run --extra dev python -m pytest tests/test_ai_endgame1_regressions.py -q` passes.

---

# Phase 7: Preserve prior hardening

## 7.1 Fix 8 runtime improvements

- [ ] Confirm no 3-second TUI waits:
  - [ ] `grep -R "pause(delay=3\\|pause(delay=2\\|sleep(3\\|sleep(2" tests/test_tui.py tests`
- [ ] Run:
  - [ ] `uv run --extra dev python -m pytest tests/test_tui.py -m "not slow" -q --durations=20`

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

- [ ] Confirm collection behavior tests still pass.
- [ ] Confirm PositionDB raw JSONL tests still pass.
- [ ] Confirm loss `k` tests still pass.
- [ ] Confirm opening-book seed tests still pass.

## 7.3 Runtime-marker meta-tests

- [ ] Confirm `tests/test_test_runtime_markers_integration.py` remains slow-marked.

---

# Phase 8: Final validation

## 8.1 Static checks

- [ ] `uv run --extra dev python -m ruff check chess_game tests`
- [ ] `uv run --extra dev python -m mypy chess_game`
- [ ] `uv run --extra dev python -m pylint chess_game/texel --score=y`

## 8.2 Fast suite

- [ ] `uv run --extra dev python -m pytest -m "not slow"`

## 8.3 Targeted 8 slow tests

Run:

```bash
uv run --extra dev python -m pytest \
  tests/test_ai_endgame1_regressions.py::test_endgame1_search_prefers_cutoff_before_starting_pawn_race \
  tests/test_ai_quality.py::test_simple_quality_benchmark_prefers_hanging_rook_capture \
  tests/test_ai_strategy6_regressions.py::test_strategy6_search_keeps_king_safer_than_g_pawn_lunge_in_transition \
  tests/test_ai_strategy6_regressions.py::test_strategy6_search_prefers_clearer_knight_route_over_na7_in_transition \
  tests/test_ai_strategy6_regressions.py::test_strategy6_search_prefers_clean_rook_capture_during_conversion \
  tests/test_ai_strategy7_regressions.py::test_strategy7_search_prefers_only_blockade_move_in_passer_race \
  tests/test_ai_strategy7_regressions.py::test_strategy7_search_prefers_stopping_enemy_race_over_wrong_side_check \
  tests/test_ai_strategy8_regressions.py::test_strategy8_search_demotes_flank_poke_when_castling_is_available \
  -q
```

## 8.4 Related files

- [ ] `uv run --extra dev python -m pytest tests/test_ai_quality.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_endgame1_regressions.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy6_regressions.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy7_regressions.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy8_regressions.py -q`

## 8.5 Slow suite

- [ ] `uv run --extra dev python -m pytest -m slow`
- [ ] If too slow, document limitation.

---

# Phase 9: Completion criteria

This patch is complete only when:

- [ ] Ruff passes.
- [ ] mypy passes.
- [ ] Texel Pylint passes or remains acceptably high.
- [ ] Full fast suite passes.
- [ ] The 8 targeted slow failures pass or are honestly rewritten with meaningful broader invariants.
- [ ] Hanging-rook capture behavior is fixed or justified with diagnostics.
- [ ] Castling-vs-flank-poke behavior is fixed or rewritten to meaningful invariant.
- [ ] Strategy6 failures are fixed or reclassified with diagnostics.
- [ ] Strategy7 passer-race failures are fixed or reclassified with diagnostics.
- [ ] Endgame cutoff failure is fixed or reclassified with diagnostics.
- [ ] Root-candidate diagnostics exist or equivalent per-position diagnostic output is available.
- [ ] No vacuous assertions are introduced.
- [ ] No hardcoded position-specific move hacks are introduced.
- [ ] Fix 7 behavior tests still pass.
- [ ] Fix 8 runtime improvements are preserved.
- [ ] Targeted slow tests pass.
- [ ] Full slow suite passes, or any remaining slow-suite limitation is documented honestly.

---

# Notes for Claude Code

## Start with diagnostics

Do not tune blindly.

## Fix tactical material regression first

The hanging-rook test is the least subjective.

## Prefer general fixes

Avoid FEN-specific or move-specific hacks.

## Rewrite tests only when justified

If exact moves are too specific, replace them with meaningful invariants.

## Preserve fast-suite work

Do not regress Fix 8.
