# CHESS_ENGINE_SLOW_STRENGTH_FIX10_SPEC.md

## Purpose

This document specifies a focused **Fix 10 completion patch** for the incomplete Fix 9 slow-suite engine-strength work.

Fix 9 made real progress:

- hanging-rook capture behavior was fixed,
- Strategy8 flank-pawn-poke behavior was fixed,
- root-candidate diagnostics were added,
- a material-realization root tie-break was introduced,
- a full-window root re-search idea was introduced to prevent bounded fail-low moves from winning root tie-breaks,
- Fix 7 behavior tests and Fix 8 TUI runtime improvements were preserved.

However, Fix 9 is **not complete**:

- the named targeted slow set does not pass,
- the endgame cutoff target still fails,
- Strategy6/Strategy7 targets are not fully diagnosed or proven fixed,
- diagnostics were not used on all remaining named targets,
- the new root re-search logic likely has a state-consistency bug,
- the full slow suite is not proven green.

Fix 10 should **finish Fix 9**, not start a new tuning project.

---

## Hard scope boundaries

### In scope

- Fix the root re-search state-consistency issue in `_search_move_loop()`.
- Add regression tests for root re-search / fail-low / root tie-break behavior.
- Finish the remaining named Fix 9 slow target failures.
- Use diagnostics on all remaining named target failures.
- Add deterministic options to targeted slow regression tests where supported.
- Rewrite exact-move assertions only when diagnostics prove they are over-specific.
- Preserve the good Fix 9 work.
- Preserve Fix 7 and Fix 8 hardening.
- Run final validation.

### Out of scope

Do **not** implement:

- make/unmake search,
- bitboards,
- true Zobrist hashing,
- NNUE/neural evaluation,
- broad search rewrites,
- broad evaluation rewrites,
- broad TUI changes,
- broad Texel changes,
- broad opening-book refactors,
- FEN-specific or move-specific hacks.

This is a narrow completion patch.

---

# Known status from latest review

## Passing

Static gates pass:

```bash
uv run --extra dev python -m ruff check chess_game tests
uv run --extra dev python -m mypy chess_game
uv run --extra dev python -m pylint chess_game/texel --score=y
```

Fix 7 behavior preservation passes:

```bash
uv run --extra dev python -m pytest \
  tests/test_collect.py \
  tests/test_position_db.py \
  tests/test_loss.py \
  tests/test_opening_book.py \
  -m "not slow" -q
```

Fix 8 TUI runtime preservation passes:

```bash
uv run --extra dev python -m pytest tests/test_tui.py -m "not slow" -q --durations=10
```

These Fix 9 targets now pass:

```bash
uv run --extra dev python -m pytest \
  tests/test_ai_quality.py::test_simple_quality_benchmark_prefers_hanging_rook_capture \
  -q
```

```bash
uv run --extra dev python -m pytest \
  tests/test_ai_strategy8_regressions.py::test_strategy8_search_demotes_flank_poke_when_castling_is_available \
  -q
```

Related files also passed in the review:

```bash
uv run --extra dev python -m pytest tests/test_ai_quality.py -q
uv run --extra dev python -m pytest tests/test_ai_strategy8_regressions.py -q
```

## Not passing / not proven

The endgame cutoff target still fails:

```text
tests/test_ai_endgame1_regressions.py::test_endgame1_search_prefers_cutoff_before_starting_pawn_race

Expected start square: a5
Actual start square:   d4
```

The full named Fix 9 targeted set is not green.

Strategy6/Strategy7 targets are not fully diagnosed or proven fixed.

The full slow suite is not proven green.

---

# Required final outcome

The patch is complete only when all static checks pass:

```bash
uv run --extra dev python -m ruff check chess_game tests
uv run --extra dev python -m mypy chess_game
uv run --extra dev python -m pylint chess_game/texel --score=y
```

The full fast suite must pass:

```bash
uv run --extra dev python -m pytest -m "not slow"
```

The named targeted slow set must pass, unless a test is rewritten with a documented, meaningful broader invariant:

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

Related files must pass:

```bash
uv run --extra dev python -m pytest tests/test_ai_quality.py -q
uv run --extra dev python -m pytest tests/test_ai_endgame1_regressions.py -q
uv run --extra dev python -m pytest tests/test_ai_strategy6_regressions.py -q
uv run --extra dev python -m pytest tests/test_ai_strategy7_regressions.py -q
uv run --extra dev python -m pytest tests/test_ai_strategy8_regressions.py -q
```

Full slow suite should pass if feasible:

```bash
uv run --extra dev python -m pytest -m slow
```

If the full slow suite is too expensive to run, document the limitation and run all related slow files.

---

# Problem 1: Root re-search state-consistency bug

## Current issue

Fix 9 introduced a full-window re-search to prevent a bounded fail-low move from being promoted by root tie-break logic.

The idea is good, but the implementation likely has a state-consistency issue.

The problematic pattern is in `_search_move_loop()`:

```python
if replace_selected_move and not is_better and not is_tie:
    child_score, root_tiebreak = _evaluate_child_move(
        board, move, params, -INF, INF
    )
    replace_selected_move = _prefer_root_move(...)
```

After re-searching with a full window, the code must recompute the normal score relationship:

- `is_better`,
- `is_tie`.

It must also update the normal best-search state when appropriate:

- `search_best_score`,
- `search_best_move`.

If the exact full-window re-search returns a score that is better than the current search best, the returned score, TT storage, alpha/beta update, and iterative deepening state must not continue using the stale bounded score.

## Required fix

After full-window re-search:

1. Recompute whether the exact score is better than the current `search_best_score`.
2. Recompute whether the exact score ties the current `search_best_score`.
3. If it is better, update:
   - `search_best_score`,
   - `search_best_move`.
4. If it ties and should win the normal deterministic/random tie-break, update:
   - `search_best_score`,
   - `search_best_move`.
5. Then apply root-selection tie-break logic consistently.
6. Ensure TT storage and returned search score use the correct exact score state.

## Sketch

The exact implementation must match the current code, but the logic should resemble:

```python
if replace_selected_move and not is_better and not is_tie:
    child_score, root_tiebreak = _evaluate_child_move(board, move, params, -INF, INF)

    if params.is_maximizing:
        is_better = child_score > search_best_score
        is_tie = child_score == search_best_score
    else:
        is_better = child_score < search_best_score
        is_tie = child_score == search_best_score

    if is_better or (is_tie and normal_tie_break_prefers_this_move):
        search_best_score = child_score
        search_best_move = LegalMove(move.start, move.end, move.promotion)

    replace_selected_move = _prefer_root_move(...)
```

This is not a drop-in patch; adapt it to the actual `_search_move_loop()` structure.

## Required tests

Add regression tests proving:

1. A bounded fail-low move cannot win root tie-break solely from speculative root tie-break score.
2. A move that wins after exact full-window re-search updates the normal root best score and returned move consistently.
3. TT/root return state does not store stale bounded score if re-search proves a different exact score.
4. A legitimate exact-score tie can still be resolved by root tie-break.

These tests can use monkeypatched helpers if needed. They should be deterministic and fast enough not to burden normal development.

## Acceptance criteria

- Strategy8 remains passing.
- No stale root score/best move state after re-search.
- New regression tests pass.
- Existing search/TT tests still pass.

---

# Problem 2: Finish endgame cutoff failure

## Current failure

```text
tests/test_ai_endgame1_regressions.py::test_endgame1_search_prefers_cutoff_before_starting_pawn_race
```

Observed:

```text
Expected start square: a5
Actual start square:   d4
```

## Required investigation

Use `tests/root_diagnostics.py` or equivalent root-candidate diagnostics on this position.

Compare:

- expected cutoff move starting from `a5`,
- actual move starting from `d4`,
- other top root candidates.

Record:

- root score,
- root tie-break score,
- static eval after move,
- quiescence score after move,
- whether the move is selected,
- whether re-search changes any candidate score,
- whether the new root re-search fix affects this failure.

## Required decision

Determine whether:

1. the cutoff move is truly required and the engine is wrong,
2. the exact start square `a5` is over-specific but the engine still chooses an acceptable cutoff/pawn-race move,
3. the actual `d4` move is a known bad pawn-race decision,
4. the test setup is stale or wrong.

## Required fix or rewrite

If the engine is wrong, fix narrowly:

- improve king cutoff evaluation,
- improve pawn-race urgency,
- improve passed-pawn stop/blockade incentives,
- correct root re-search / root tie-break behavior if it caused the issue.

If the exact assertion is too narrow, rewrite to a meaningful invariant, such as:

- chosen move must stop or delay the enemy race,
- chosen move must be one of a small acceptable cutoff set,
- chosen move must not start the wrong pawn race,
- chosen move must keep the king/rook in the stopping zone.

Do not replace with a vacuous assertion.

## Acceptance criteria

- The endgame cutoff target passes.
- The diagnosis is documented.
- Related endgame file passes.

---

# Problem 3: Finish Strategy6 triage

## Remaining targets

```text
tests/test_ai_strategy6_regressions.py::test_strategy6_search_keeps_king_safer_than_g_pawn_lunge_in_transition
tests/test_ai_strategy6_regressions.py::test_strategy6_search_prefers_clearer_knight_route_over_na7_in_transition
tests/test_ai_strategy6_regressions.py::test_strategy6_search_prefers_clean_rook_capture_during_conversion
```

## Required investigation

For each test:

- run it individually,
- record expected move,
- record actual move,
- run root diagnostics,
- determine whether it is:
  - a real engine regression,
  - an over-specific assertion,
  - a test setup issue,
  - affected by the root re-search bug.

## Required fix or rewrite

If real regression, fix narrowly:

- transition king safety,
- safe piece route selection,
- material conversion,
- tactical capture valuation,
- root scoring / root re-search consistency.

If over-specific, rewrite to a meaningful invariant:

- avoid known unsafe pawn lunge,
- choose an acceptable safe route,
- prefer clean material conversion,
- avoid clearly inferior knight route.

## Acceptance criteria

- All three Strategy6 targets pass.
- `tests/test_ai_strategy6_regressions.py` passes.
- Any rewrites are documented and non-vacuous.

---

# Problem 4: Finish Strategy7 triage

## Remaining targets

```text
tests/test_ai_strategy7_regressions.py::test_strategy7_search_prefers_only_blockade_move_in_passer_race
tests/test_ai_strategy7_regressions.py::test_strategy7_search_prefers_stopping_enemy_race_over_wrong_side_check
```

## Required investigation

For each test:

- run it individually,
- record expected move,
- record actual move,
- run root diagnostics,
- check passer-race urgency,
- check blockade/stop incentives,
- check excessive check/tempo bonus,
- check root re-search impact.

## Required fix or rewrite

If real regression, fix narrowly:

- improve enemy passer threat penalty,
- improve blockade urgency,
- reduce distracting check bonus if it ignores promotion race,
- improve pawn-race horizon handling if simple,
- correct root re-search state if it caused the issue.

If over-specific, rewrite to a meaningful invariant:

- chosen move must stop/blockade the passer,
- chosen move must avoid the wrong-side check,
- chosen move must belong to an acceptable stopping set.

## Acceptance criteria

- Both Strategy7 targets pass.
- `tests/test_ai_strategy7_regressions.py` passes.
- Any rewrites are documented and non-vacuous.

---

# Problem 5: Deterministic slow regression tests

## Current issue

The targeted slow strategy tests mostly call:

```python
get_best_move(board, depth=...)
```

without deterministic options.

These are regression tests, not randomness tests. They should be stable across runs.

## Required change

For the named targeted slow tests, use deterministic options where supported:

```python
BestMoveOptions(
    use_opening_book=False,
    deterministic=True,
)
```

or the equivalent current API.

Use deterministic mode for:

- the 8 named Fix 9/Fix 10 target tests,
- root-candidate diagnostics,
- any new root re-search regression tests.

Do not change production default behavior.

## Acceptance criteria

- Targeted slow tests are deterministic.
- No regression test depends on random tie-breaking.
- Opening-book/randomness tests remain separate.

---

# Problem 6: Preserve good Fix 9 work

Do not regress the work that is already good.

## Preserve

- `tests/root_diagnostics.py` or equivalent diagnostics helper.
- Hanging-rook fix.
- Material-realization root tie-break.
- Strategy8 fail-low/root re-search idea.
- Passing `tests/test_ai_quality.py`.
- Passing `tests/test_ai_strategy8_regressions.py`.

## Required checks

Run:

```bash
uv run --extra dev python -m pytest tests/test_ai_quality.py -q
uv run --extra dev python -m pytest tests/test_ai_strategy8_regressions.py -q
```

## Acceptance criteria

- Hanging-rook target remains passing.
- Strategy8 flank-poke target remains passing.
- No regression in the related files.

---

# Problem 7: Preserve Fix 7 and Fix 8 hardening

## Fix 7 checks

Run:

```bash
uv run --extra dev python -m pytest \
  tests/test_collect.py \
  tests/test_position_db.py \
  tests/test_loss.py \
  tests/test_opening_book.py \
  -m "not slow" -q
```

Confirm:

- collection behavior tests pass,
- PositionDB raw JSONL tests pass,
- loss `k` tests pass,
- opening-book seed tests pass.

## Fix 8 checks

Confirm no old long TUI sleeps:

```bash
grep -R "pause(delay=3\\|pause(delay=2\\|sleep(3\\|sleep(2" tests/test_tui.py tests
```

Run:

```bash
uv run --extra dev python -m pytest tests/test_tui.py -m "not slow" -q --durations=10
```

Confirm:

- TUI tests pass,
- no avoidable 3-second sleeps return.

## Runtime marker checks

Confirm:

```python
pytestmark = pytest.mark.slow
```

still exists in:

```text
tests/test_test_runtime_markers_integration.py
```

## Acceptance criteria

- Fix 7 and Fix 8 improvements are preserved.
- No test-theater regressions return.
- No avoidable slow TUI waits return.

---

# Problem 8: Document diagnosis honestly

Update or create a status/diagnosis doc, preferably:

```text
docs/FIX10_COMPLETION_DIAGNOSIS.md
```

It should include:

- root re-search bug explanation,
- tests added for root re-search state consistency,
- endgame cutoff diagnosis,
- Strategy6 diagnosis,
- Strategy7 diagnosis,
- any rewritten assertions and why they remain meaningful,
- final validation commands and results,
- full slow-suite status or limitation.

Do not write a celebratory completion report unless the criteria are actually met.

---

# Final validation

Run static checks:

```bash
uv run --extra dev python -m ruff check chess_game tests
uv run --extra dev python -m mypy chess_game
uv run --extra dev python -m pylint chess_game/texel --score=y
```

Run full fast suite:

```bash
uv run --extra dev python -m pytest -m "not slow"
```

Run Fix 7/Fix 8 preservation tests:

```bash
uv run --extra dev python -m pytest \
  tests/test_collect.py \
  tests/test_position_db.py \
  tests/test_loss.py \
  tests/test_opening_book.py \
  -m "not slow" -q

uv run --extra dev python -m pytest tests/test_tui.py -m "not slow" -q --durations=10
```

Run Fix 9/Fix 10 targeted tests:

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

Run related files:

```bash
uv run --extra dev python -m pytest tests/test_ai_quality.py -q
uv run --extra dev python -m pytest tests/test_ai_endgame1_regressions.py -q
uv run --extra dev python -m pytest tests/test_ai_strategy6_regressions.py -q
uv run --extra dev python -m pytest tests/test_ai_strategy7_regressions.py -q
uv run --extra dev python -m pytest tests/test_ai_strategy8_regressions.py -q
```

Run full slow suite if feasible:

```bash
uv run --extra dev python -m pytest -m slow
```

If not feasible, document runtime limitation and at least run all related slow files.

---

# Acceptance criteria

Fix 10 is complete only when:

1. Ruff passes.
2. mypy passes.
3. Texel Pylint passes or remains acceptably high.
4. Full fast suite passes.
5. Root re-search state-consistency bug is fixed.
6. Root re-search regression tests are added and pass.
7. Hanging-rook target remains passing.
8. Strategy8 flank-poke target remains passing.
9. Endgame cutoff target passes or is rewritten to a meaningful documented invariant.
10. All three Strategy6 targets pass or are rewritten to meaningful documented invariants.
11. Both Strategy7 targets pass or are rewritten to meaningful documented invariants.
12. The 8 named targeted tests pass as a set.
13. Related files pass.
14. Diagnostics are used on all remaining named failures.
15. Deterministic mode is used for targeted slow regression tests where supported.
16. No vacuous assertions are introduced.
17. No FEN-specific or move-specific hacks are introduced.
18. Fix 7 behavior tests still pass.
19. Fix 8 TUI runtime improvements are preserved.
20. Runtime marker meta-tests remain slow-marked.
21. Full slow suite passes, or any limitation is documented honestly.
22. `docs/FIX10_COMPLETION_DIAGNOSIS.md` or equivalent honestly records what changed and what was validated.

---

# Notes for Claude Code

## Do not start over

Keep the good Fix 9 work.

## Fix the bookkeeping bug first

Root re-search exact scores must update normal root best-score state when appropriate.

## Finish the named targets

Do not stop after hanging-rook and Strategy8.

## Use diagnostics

Every remaining target should have diagnostic evidence.

## Keep tests meaningful

Broaden exact-move assertions only when justified, and never to vacuous checks.

## Preserve previous hardening

Do not regress Fix 7 or Fix 8.
