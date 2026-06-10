# CHESS_ENGINE_SLOW_STRENGTH_FIX9_SPEC.md

## Purpose

This document specifies a focused **Fix 9 slow-suite engine-strength triage patch** for the chess engine.

The prior Fix 8 work was about fast-suite runtime cleanup. It removed avoidable multi-second TUI waits and kept the fast test suite focused. The remaining issue is separate: the **slow engine-strength suite has 8 failing tests**.

These failures are not caused by the Fix 8 TUI runtime work. They are depth-heavy strategic/tactical regression tests that expose evaluation/search weaknesses or outdated overly-specific assertions.

This patch should focus only on those 8 slow failures.

---

## Hard scope boundaries

### In scope

- Reproduce the 8 failing slow engine-strength tests.
- Add or improve root-candidate diagnostics for failed positions.
- Determine whether each failure is:
  - a real engine regression,
  - an outdated/over-specific test assertion,
  - a test setup issue.
- Fix real tactical/evaluation/search regressions narrowly.
- Rewrite only those slow tests whose assertion is demonstrably over-specific.
- Preserve all fast-suite improvements from Fix 8.
- Preserve Fix 7 behavior-test hardening.
- Run final validation.

### Out of scope

Do **not** implement:

- make/unmake search,
- bitboards,
- true Zobrist hashing,
- NNUE/neural evaluation,
- broad search rewrites,
- broad evaluation rewrites,
- new opening-book architecture,
- broad TUI work,
- broad Texel changes,
- broad test-suite reorganization.

This is a narrow slow-suite triage and engine-strength patch.

---

# Known failing slow tests

The known failing slow tests are:

```text
tests/test_ai_endgame1_regressions.py::test_endgame1_search_prefers_cutoff_before_starting_pawn_race
tests/test_ai_quality.py::test_simple_quality_benchmark_prefers_hanging_rook_capture
tests/test_ai_strategy6_regressions.py::test_strategy6_search_keeps_king_safer_than_g_pawn_lunge_in_transition
tests/test_ai_strategy6_regressions.py::test_strategy6_search_prefers_clearer_knight_route_over_na7_in_transition
tests/test_ai_strategy6_regressions.py::test_strategy6_search_prefers_clean_rook_capture_during_conversion
tests/test_ai_strategy7_regressions.py::test_strategy7_search_prefers_only_blockade_move_in_passer_race
tests/test_ai_strategy7_regressions.py::test_strategy7_search_prefers_stopping_enemy_race_over_wrong_side_check
tests/test_ai_strategy8_regressions.py::test_strategy8_search_demotes_flank_poke_when_castling_is_available
```

The previously observed slow-suite result was approximately:

```text
8 failed, 161 passed, 1031 deselected
```

These should be treated as engine-strength triage targets, not Fix 8 runtime failures.

---

# Required final outcome

The patch is complete only when:

```bash
uv run --extra dev python -m ruff check chess_game tests
uv run --extra dev python -m mypy chess_game
uv run --extra dev python -m pylint chess_game/texel --score=y
uv run --extra dev python -m pytest -m "not slow"
```

pass, and the 8 targeted slow failures are either fixed or honestly reclassified with defensible test changes.

The targeted slow tests must pass:

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

The full slow suite should be run if feasible:

```bash
uv run --extra dev python -m pytest -m slow
```

If full slow-suite runtime is too long, document the limitation and run the targeted slow tests plus nearby slow files.

---

# Problem 1: Lack of root-candidate diagnostics

## Current problem

The 8 failures are engine-strength failures, but the raw assertion failures only say which move was expected and which move was chosen.

That is not enough to fix the engine without guessing.

## Required diagnostic capability

Add a dev/test helper that can report root candidates for a board position.

It should be able to show, for each relevant root move:

- move,
- final root search score,
- static evaluation after the move,
- material/capture delta if available,
- king safety contribution if available,
- passed-pawn/race/endgame contribution if available,
- move-order score if available,
- whether the move was the selected best move.

This can live in test helpers or a dev-only diagnostic module. It does not need to be part of public API.

## Suggested helper shape

```python
def debug_root_candidates(
    board: Board,
    *,
    depth: int,
    top_n: int = 10,
) -> list[RootCandidateDebug]:
    ...
```

or a test-only function inside the relevant test file.

The exact implementation can be simpler if exposing all components is too invasive. At minimum, report:

- legal root moves,
- search score per move,
- static eval after move,
- selected move.

## Acceptance criteria

- The helper can explain why the engine chose the actual move over the expected move for at least the hanging-rook and castling-vs-flank-poke failures.
- The helper is not a broad production feature.
- The helper does not slow down the fast suite.

---

# Problem 2: Simple hanging-rook capture failure

## Known failure

```text
tests/test_ai_quality.py::test_simple_quality_benchmark_prefers_hanging_rook_capture
```

Observed behavior:

```text
Expected: queen d4xd5
Actual:   queen d4xf6
```

This is the clearest likely engine bug. In a simple position with a hanging rook, the engine should prefer taking the rook unless there is a concrete tactical refutation.

## Required investigation

Use root-candidate diagnostics to compare:

- `Qxd5`,
- `Qxf6`,
- any other top candidates.

Determine whether the failure is caused by:

- material/capture reward being too weak,
- queen activity or check/king-safety being too strong,
- quiescence search missing or overvaluing something,
- bad perspective/sign handling,
- root scoring bug,
- test setup ambiguity.

## Required fix

Prefer a narrow fix that improves the engine generally:

- correct capture/material evaluation if wrong,
- tune excessive queen/check/activity bonus if it overwhelms rook capture,
- fix root scoring/perspective if wrong,
- improve quiescence/capture handling if appropriate.

Do not hardcode this position or add a move-specific hack.

## Acceptance criteria

- The hanging-rook test passes.
- Diagnostics show why the expected capture is now preferred.
- Nearby tactical/capture tests still pass.
- Fast suite still passes.

---

# Problem 3: Castling vs flank-pawn poke failure

## Known failure

```text
tests/test_ai_strategy8_regressions.py::test_strategy8_search_demotes_flank_poke_when_castling_is_available
```

Observed behavior:

```text
Expected: not a2a4
Actual:   a2a4
```

The earlier review noted that move ordering may prefer castling, but the depth-2 search still selects `a2a4`. That means the root child evaluation or leaf evaluation is overpowering the move-order preference.

## Required investigation

Use root-candidate diagnostics to compare:

- `O-O` if legal,
- `O-O-O` if legal,
- `a2a4`,
- other top candidates.

Identify whether the engine overvalues:

- flank pawn space,
- rook pawn activity,
- irrelevant pawn expansion,
- short-term quiet move score,

or undervalues:

- castling,
- king safety,
- development,
- transition safety.

## Required fix

Prefer a narrow, general fix:

- strengthen castling/king-safety evaluation where appropriate,
- reduce premature flank-pawn expansion bonus when the king is uncastled,
- penalize flank pawn lunges during unsafe transition positions,
- fix any search/eval perspective issue.

Do not hardcode “never play a2a4.”

## Acceptance criteria

- The test no longer selects `a2a4`.
- If the test is too strict about exactly which alternative move is best, rewrite it to assert a safe acceptable set or only assert `move != a2a4`.
- Nearby castling/king-safety tests still pass.

---

# Problem 4: Strategy6 regression failures

## Known failures

```text
tests/test_ai_strategy6_regressions.py::test_strategy6_search_keeps_king_safer_than_g_pawn_lunge_in_transition
tests/test_ai_strategy6_regressions.py::test_strategy6_search_prefers_clearer_knight_route_over_na7_in_transition
tests/test_ai_strategy6_regressions.py::test_strategy6_search_prefers_clean_rook_capture_during_conversion
```

These likely relate to transition-phase evaluation, king safety, piece routing, and conversion tactics.

## Required investigation

For each failure:

1. Generate root-candidate diagnostics.
2. Compare expected move vs actual move.
3. Identify the scoring component responsible for the difference.
4. Decide whether the test expectation is still valid.

## Required fix

Prefer narrow improvements that address shared causes:

- transition king safety,
- premature flank pawn moves,
- piece route clarity,
- clean material conversion,
- tactical capture valuation.

Avoid adding one-off special cases.

## Acceptance criteria

- All three strategy6 tests pass or are honestly rewritten if over-specific.
- Any rewritten test still catches the bad behavior it was meant to prevent.
- No broad search rewrite is introduced.

---

# Problem 5: Strategy7 passer-race regression failures

## Known failures

```text
tests/test_ai_strategy7_regressions.py::test_strategy7_search_prefers_only_blockade_move_in_passer_race
tests/test_ai_strategy7_regressions.py::test_strategy7_search_prefers_stopping_enemy_race_over_wrong_side_check
```

These likely involve passed-pawn races, blockade urgency, and stopping enemy promotion threats.

## Required investigation

Use root-candidate diagnostics to compare:

- expected blockade/stopping move,
- actual move,
- immediate promotion threats,
- passed-pawn evaluation,
- check/tempo evaluation.

## Required fix

Prefer general improvements to:

- passed-pawn race evaluation,
- blockade urgency,
- enemy passer threat penalties,
- promotion-race horizon handling,
- excessive check bonus if it distracts from stopping a passer.

Do not hardcode transcript-specific moves.

## Acceptance criteria

- Both strategy7 tests pass or are rewritten only if the old expected move is over-specific.
- The engine still avoids the known bad passer-race decisions.
- Related passed-pawn tests still pass.

---

# Problem 6: Endgame pawn-race cutoff failure

## Known failure

```text
tests/test_ai_endgame1_regressions.py::test_endgame1_search_prefers_cutoff_before_starting_pawn_race
```

This likely relates to king activity, pawn-race timing, and cutoff/blockade evaluation.

## Required investigation

Use root-candidate diagnostics to compare:

- expected cutoff move,
- actual move,
- king distance to passed pawns,
- pawn race evaluation,
- promotion timing if available.

## Required fix

Prefer general improvements to:

- king cutoff evaluation,
- pawn-race urgency,
- king-pawn endgame heuristics,
- passed-pawn stop/blockade incentives.

## Acceptance criteria

- Endgame cutoff test passes or is rewritten only if the exact move expectation is too narrow.
- The engine still prefers stopping dangerous pawn races.

---

# Problem 7: Decide when to rewrite tests

Not every slow engine-strength test should necessarily require exactly one move.

## Allowed rewrite

A slow regression test may be rewritten if diagnostics show the current engine move is objectively reasonable and the old expected move is too specific.

Allowed rewrites include:

- expected move belongs to an acceptable set,
- assert the engine avoids a known bad move,
- assert the engine captures material above a threshold,
- assert the engine blocks/stops a passer rather than requiring one exact square,
- assert castling/king safety is preferred over a known unsafe pawn lunge.

## Not allowed

Do not weaken a test merely to get green.

Do not replace a meaningful strategic assertion with:

```python
assert move is not None
```

or other vacuous assertions.

## Required documentation

If a test is rewritten, add a short comment explaining:

- what the original overly-specific assertion was,
- why the broader invariant is still meaningful,
- what bad behavior the test still prevents.

---

# Problem 8: Preserve Fix 7/Fix 8 improvements

This patch must not regress recent hardening.

## Required checks

Confirm these remain true:

- Fast suite still passes.
- TUI tests no longer contain avoidable 3-second waits.
- Runtime marker meta-tests remain slow-marked.
- Collection tests still prove behavior.
- PositionDB tests still assert raw stats from hand-authored JSONL.
- Loss `k` tests still prove `k` behavior.
- Opening-book seed tests remain non-vacuous.
- Opening-book seeded randomness does not mutate global RNG.

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

Run targeted slow failures:

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
uv run --extra dev python -m pytest \
  tests/test_ai_quality.py \
  tests/test_ai_endgame1_regressions.py \
  tests/test_ai_strategy6_regressions.py \
  tests/test_ai_strategy7_regressions.py \
  tests/test_ai_strategy8_regressions.py \
  -q
```

Run full slow suite if feasible:

```bash
uv run --extra dev python -m pytest -m slow
```

If full slow-suite runtime is too long, document the limitation.

---

# Acceptance criteria

Fix 9 is complete only when:

1. Ruff passes.
2. mypy passes.
3. Texel Pylint passes or remains acceptably high.
4. Full fast suite passes.
5. The 8 targeted slow failures pass or are honestly rewritten with meaningful broader invariants.
6. Hanging-rook capture behavior is fixed or the test is justified with diagnostics.
7. Castling-vs-flank-poke behavior is fixed or the test is rewritten to a meaningful invariant.
8. Strategy6 failures are fixed or reclassified with diagnostics.
9. Strategy7 passer-race failures are fixed or reclassified with diagnostics.
10. Endgame cutoff failure is fixed or reclassified with diagnostics.
11. Root-candidate diagnostics exist or equivalent per-position diagnostic output is available.
12. No vacuous assertions are introduced.
13. No hardcoded position-specific move hacks are introduced.
14. Fix 7 behavior tests still pass.
15. Fix 8 runtime improvements are preserved.
16. Targeted slow tests pass.
17. Full slow suite passes, or any remaining slow-suite limitation is documented honestly.

---

# Notes for Claude Code

## Do not guess

Use diagnostics before tuning.

## Fix the clearest bug first

Start with the hanging-rook capture test. It is the least subjective.

## Avoid one-off hacks

Do not special-case FENs or exact moves.

## Prefer meaningful invariants

If exact move expectations are over-specific, rewrite them carefully.

## Keep fast-suite work intact

Do not regress Fix 8.
