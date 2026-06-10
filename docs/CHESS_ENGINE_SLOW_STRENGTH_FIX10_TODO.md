# CHESS_ENGINE_SLOW_STRENGTH_FIX10_TODO.md

## Implementation checklist

This TODO is for the Fix 10 completion patch for incomplete Fix 9 slow-suite engine-strength work.

Keep this patch narrow. Do **not** implement make/unmake search, bitboards, true Zobrist hashing, NNUE, broad search rewrites, broad evaluation rewrites, broad TUI changes, broad Texel changes, broad opening-book refactors, or FEN-specific/move-specific hacks.

---

# Phase 0: Baseline and current status

## 0.1 Static checks

- [ ] `uv run --extra dev python -m ruff check chess_game tests`
- [ ] `uv run --extra dev python -m mypy chess_game`
- [ ] `uv run --extra dev python -m pylint chess_game/texel --score=y`

## 0.2 Fast suite

- [ ] `uv run --extra dev python -m pytest -m "not slow"`
- [ ] Record pass/fail and runtime.
- [ ] Confirm Fix 8 fast-suite runtime work remains intact.

## 0.3 Reproduce Fix 10 blockers

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

- [ ] Record which tests pass.
- [ ] Record which tests fail.
- [ ] Record expected and actual move for each failing target.
- [ ] Record search depth/options used by each target.

## 0.4 Confirm known good Fix 9 targets

- [ ] `uv run --extra dev python -m pytest tests/test_ai_quality.py::test_simple_quality_benchmark_prefers_hanging_rook_capture -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy8_regressions.py::test_strategy8_search_demotes_flank_poke_when_castling_is_available -q`
- [ ] Confirm both still pass before making changes.

---

# Phase 1: Fix root re-search state consistency

## 1.1 Inspect `_search_move_loop()`

- [ ] Locate full-window re-search logic in `chess_game/chess/ai.py`.
- [ ] Identify variables involved:
  - [ ] `child_score`
  - [ ] `root_tiebreak`
  - [ ] `is_better`
  - [ ] `is_tie`
  - [ ] `search_best_score`
  - [ ] `search_best_move`
  - [ ] `root_selected_move`
  - [ ] `root_selected_score`
  - [ ] alpha/beta update variables
  - [ ] TT storage variables

## 1.2 Fix stale score/best-move handling

After full-window re-search:

- [ ] Recompute `is_better` using the exact `child_score`.
- [ ] Recompute `is_tie` using the exact `child_score`.
- [ ] If exact score is better, update:
  - [ ] `search_best_score`
  - [ ] `search_best_move`
- [ ] If exact score is tied and normal tie-break prefers the move, update:
  - [ ] `search_best_score`
  - [ ] `search_best_move`
- [ ] Ensure root tie-break selection uses exact score/tie state.
- [ ] Ensure alpha/beta update uses correct score.
- [ ] Ensure TT storage uses correct best score and best move.
- [ ] Ensure iterative deepening receives correct root score.

## 1.3 Add regression tests

Add tests proving:

- [ ] Bounded fail-low move cannot win root tie-break solely because of speculative tie-break score.
- [ ] Full-window re-search can promote a move only when exact score justifies it.
- [ ] Exact re-searched better score updates returned root score and normal best move.
- [ ] TT/root storage does not retain stale bounded score after re-search.
- [ ] Legitimate exact-score tie can still be resolved by root tie-break.

Use deterministic fakes/monkeypatches if necessary. Avoid slow tests unless unavoidable.

## 1.4 Validate search-related tests

Run:

- [ ] `uv run --extra dev python -m pytest tests/test_ai_search.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_search_terminal_scores.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy8_regressions.py -q`

---

# Phase 2: Deterministic targeted slow regression tests

## 2.1 Update targeted tests where supported

For each named Fix 9/Fix 10 target, use deterministic options where supported:

```python
BestMoveOptions(
    use_opening_book=False,
    deterministic=True,
)
```

or current equivalent.

Targets:

- [ ] endgame cutoff target
- [ ] hanging-rook target
- [ ] Strategy6 king-safety target
- [ ] Strategy6 knight-route target
- [ ] Strategy6 rook-capture target
- [ ] Strategy7 blockade target
- [ ] Strategy7 wrong-side-check target
- [ ] Strategy8 flank-poke target

## 2.2 Confirm no randomness dependency

- [ ] Run targeted set twice.
- [ ] Confirm same results both times.
- [ ] Do not modify production default randomness behavior.

---

# Phase 3: Finish endgame cutoff target

## 3.1 Reproduce

Run:

```bash
uv run --extra dev python -m pytest \
  tests/test_ai_endgame1_regressions.py::test_endgame1_search_prefers_cutoff_before_starting_pawn_race \
  -q --tb=short
```

- [ ] Confirm expected move/start.
- [ ] Confirm actual move/start.
- [ ] Confirm whether root re-search fix changes the result.

## 3.2 Diagnose

Use `tests/root_diagnostics.py` or equivalent:

- [ ] Generate top root candidates.
- [ ] Compare expected cutoff move from `a5` vs actual move from `d4`.
- [ ] Record:
  - [ ] root score,
  - [ ] root tie-break,
  - [ ] static eval,
  - [ ] quiescence eval,
  - [ ] selected flag,
  - [ ] search depth/options.

## 3.3 Decide classification

Choose one:

- [ ] Real engine regression.
- [ ] Exact `a5` assertion is over-specific.
- [ ] Test setup is stale/wrong.
- [ ] Failure caused by root re-search state bug.

Document the decision.

## 3.4 Fix or rewrite

If real regression, fix narrowly:

- [ ] king cutoff evaluation,
- [ ] pawn-race urgency,
- [ ] passed-pawn stop/blockade incentive,
- [ ] root scoring / root re-search consistency.

If over-specific, rewrite to meaningful invariant:

- [ ] acceptable cutoff set,
- [ ] must stop/delay enemy race,
- [ ] must not start wrong pawn race,
- [ ] must keep stopping resource active.

Do not use a vacuous assertion.

## 3.5 Validate

- [ ] Endgame cutoff target passes.
- [ ] `uv run --extra dev python -m pytest tests/test_ai_endgame1_regressions.py -q` passes.

---

# Phase 4: Finish Strategy6 targets

## 4.1 Reproduce each

Run each individually:

- [ ] `test_strategy6_search_keeps_king_safer_than_g_pawn_lunge_in_transition`
- [ ] `test_strategy6_search_prefers_clearer_knight_route_over_na7_in_transition`
- [ ] `test_strategy6_search_prefers_clean_rook_capture_during_conversion`

For each:

- [ ] record expected move,
- [ ] record actual move,
- [ ] record depth/options.

## 4.2 Diagnose each

Use root diagnostics for each:

- [ ] top root candidates,
- [ ] expected vs actual score,
- [ ] static eval,
- [ ] quiescence eval,
- [ ] root tie-break,
- [ ] selected flag,
- [ ] root re-search impact.

## 4.3 Fix or rewrite each

For each target, choose:

- [ ] narrow engine fix, or
- [ ] meaningful invariant rewrite.

Acceptable engine fixes:

- [ ] transition king safety,
- [ ] safe piece route selection,
- [ ] clean material conversion,
- [ ] tactical capture valuation,
- [ ] root scoring / root re-search consistency.

Acceptable invariant rewrites:

- [ ] avoid unsafe pawn lunge,
- [ ] choose acceptable safe development route,
- [ ] prefer clean material conversion,
- [ ] avoid clearly inferior knight route.

## 4.4 Validate

- [ ] All three Strategy6 targets pass.
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy6_regressions.py -q` passes.

---

# Phase 5: Finish Strategy7 targets

## 5.1 Reproduce each

Run each individually:

- [ ] `test_strategy7_search_prefers_only_blockade_move_in_passer_race`
- [ ] `test_strategy7_search_prefers_stopping_enemy_race_over_wrong_side_check`

For each:

- [ ] record expected move,
- [ ] record actual move,
- [ ] record depth/options.

## 5.2 Diagnose each

Use root diagnostics for each:

- [ ] top root candidates,
- [ ] expected vs actual score,
- [ ] static eval,
- [ ] quiescence eval,
- [ ] root tie-break,
- [ ] selected flag,
- [ ] passer-race urgency,
- [ ] wrong-side-check issue if applicable.

## 5.3 Fix or rewrite each

For each target, choose:

- [ ] narrow engine fix, or
- [ ] meaningful invariant rewrite.

Acceptable engine fixes:

- [ ] enemy passer threat penalty,
- [ ] blockade urgency,
- [ ] reduce distracting check bonus,
- [ ] pawn-race horizon handling,
- [ ] root scoring / root re-search consistency.

Acceptable invariant rewrites:

- [ ] must stop/blockade passer,
- [ ] must avoid wrong-side check,
- [ ] acceptable stopping set.

## 5.4 Validate

- [ ] Both Strategy7 targets pass.
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy7_regressions.py -q` passes.

---

# Phase 6: Preserve good Fix 9 work

## 6.1 Hanging-rook

- [ ] `uv run --extra dev python -m pytest tests/test_ai_quality.py::test_simple_quality_benchmark_prefers_hanging_rook_capture -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_quality.py -q`

## 6.2 Strategy8 flank-poke

- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy8_regressions.py::test_strategy8_search_demotes_flank_poke_when_castling_is_available -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy8_regressions.py -q`

## 6.3 Diagnostics

- [ ] Preserve `tests/root_diagnostics.py` or equivalent.
- [ ] Confirm diagnostics still work after changes.

---

# Phase 7: Preserve Fix 7 and Fix 8 hardening

## 7.1 Fix 7 behavior tests

Run:

```bash
uv run --extra dev python -m pytest \
  tests/test_collect.py \
  tests/test_position_db.py \
  tests/test_loss.py \
  tests/test_opening_book.py \
  -m "not slow" -q
```

- [ ] Collection behavior tests pass.
- [ ] PositionDB raw JSONL tests pass.
- [ ] Loss `k` tests pass.
- [ ] Opening-book seed tests pass.

## 7.2 Fix 8 TUI runtime

- [ ] Confirm no long sleeps:
  - [ ] `grep -R "pause(delay=3\\|pause(delay=2\\|sleep(3\\|sleep(2" tests/test_tui.py tests`
- [ ] Run:
  - [ ] `uv run --extra dev python -m pytest tests/test_tui.py -m "not slow" -q --durations=10`
- [ ] Confirm TUI tests pass.
- [ ] Confirm no avoidable 3-second waits return.

## 7.3 Runtime-marker meta-tests

- [ ] Confirm `tests/test_test_runtime_markers_integration.py` remains slow-marked.

---

# Phase 8: Document diagnosis

## 8.1 Create/update diagnosis document

Create or update:

```text
docs/FIX10_COMPLETION_DIAGNOSIS.md
```

Include:

- [ ] Root re-search state-consistency bug explanation.
- [ ] Root re-search regression tests added.
- [ ] Endgame cutoff diagnosis.
- [ ] Strategy6 diagnosis.
- [ ] Strategy7 diagnosis.
- [ ] Any rewritten assertions and justification.
- [ ] Commands run and results.
- [ ] Full slow-suite status or limitation.

## 8.2 Avoid overclaiming

- [ ] Do not claim full slow suite green unless actually run.
- [ ] Do not claim a target is fixed unless the target passes.
- [ ] If a test is rewritten, document the invariant.

---

# Phase 9: Final validation

## 9.1 Static checks

- [ ] `uv run --extra dev python -m ruff check chess_game tests`
- [ ] `uv run --extra dev python -m mypy chess_game`
- [ ] `uv run --extra dev python -m pylint chess_game/texel --score=y`

## 9.2 Full fast suite

- [ ] `uv run --extra dev python -m pytest -m "not slow"`

## 9.3 Fix 7/Fix 8 preservation

- [ ] `uv run --extra dev python -m pytest tests/test_collect.py tests/test_position_db.py tests/test_loss.py tests/test_opening_book.py -m "not slow" -q`
- [ ] `uv run --extra dev python -m pytest tests/test_tui.py -m "not slow" -q --durations=10`

## 9.4 Targeted Fix 10 slow set

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

- [ ] Confirm all pass.

## 9.5 Related files

- [ ] `uv run --extra dev python -m pytest tests/test_ai_quality.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_endgame1_regressions.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy6_regressions.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy7_regressions.py -q`
- [ ] `uv run --extra dev python -m pytest tests/test_ai_strategy8_regressions.py -q`

## 9.6 Full slow suite

- [ ] `uv run --extra dev python -m pytest -m slow`
- [ ] If not feasible, document limitation and run all related slow files.

---

# Phase 10: Completion criteria

This patch is complete only when:

- [ ] Ruff passes.
- [ ] mypy passes.
- [ ] Texel Pylint passes or remains acceptably high.
- [ ] Full fast suite passes.
- [ ] Root re-search state-consistency bug is fixed.
- [ ] Root re-search regression tests are added and pass.
- [ ] Hanging-rook target remains passing.
- [ ] Strategy8 flank-poke target remains passing.
- [ ] Endgame cutoff target passes or is rewritten to a meaningful documented invariant.
- [ ] All three Strategy6 targets pass or are rewritten to meaningful documented invariants.
- [ ] Both Strategy7 targets pass or are rewritten to meaningful documented invariants.
- [ ] The 8 named targeted tests pass as a set.
- [ ] Related files pass.
- [ ] Diagnostics are used on all remaining named failures.
- [ ] Deterministic mode is used for targeted slow regression tests where supported.
- [ ] No vacuous assertions are introduced.
- [ ] No FEN-specific or move-specific hacks are introduced.
- [ ] Fix 7 behavior tests still pass.
- [ ] Fix 8 TUI runtime improvements are preserved.
- [ ] Runtime marker meta-tests remain slow-marked.
- [ ] Full slow suite passes, or any limitation is documented honestly.
- [ ] `docs/FIX10_COMPLETION_DIAGNOSIS.md` or equivalent honestly records what changed and what was validated.

---

# Notes for Claude Code

## This is a completion patch

Do not start a new engine tuning adventure.

## Root re-search bookkeeping first

Exact re-search scores must update normal root best state when appropriate.

## Finish every named target

Do not stop at hanging-rook and Strategy8.

## Diagnose before changing

Use root diagnostics on every remaining failing target.

## Keep prior good work

Preserve Fix 7, Fix 8, and the good parts of Fix 9.
