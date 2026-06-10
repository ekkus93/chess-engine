# FIX9 (Slow-Suite Engine-Strength Triage) — Questions and Issues

## Overview

I have read both CHESS_ENGINE_SLOW_STRENGTH_FIX9_SPEC.md and
CHESS_ENGINE_SLOW_STRENGTH_FIX9_TODO.md. This patch is materially different from
Fix 7/Fix 8: it touches **production evaluation/search**, not just tests, so the
risk profile is higher (an eval change can move the 161 currently-passing slow
engine-strength tests).

Before raising questions I did read-only investigation (read the two clearest
tests, the board setups, and the git history of the failing test files and
recent eval/search commits). Findings below ground the questions.

---

## Grounded findings (read-only)

### Hanging-rook test (the clearest case)

`tests/test_ai_quality.py::test_simple_quality_benchmark_prefers_hanging_rook_capture`:

```
Kings on a1 (White) and h8 (Black); White Qd4, Black Rd5; White to move.
Expected: Qd4xd5 (win the free rook).  Actual: Qf6 (per spec).
```

This is effectively K+Q vs K+R. `Qf6` is a **quiet check** along the f6-g7-h8
diagonal — it does NOT win the rook (f6 does not attack d5) and is NOT mate
(Black king escapes to g8/h7; White king is on a1, too far to help). So the
engine prefers a non-winning quiet check over winning a free rook. I agree with
the spec that this is the clearest, least-subjective engine bug. Likely cause:
something overvalues queen-near-enemy-king / a checking line vs +5 material
(candidates: check extensions, a king-attack/tropism term, or quiescence).

### Strategy8 flank-poke test

`tests/test_ai_strategy8_regressions.py::test_strategy8_search_demotes_flank_poke_when_castling_is_available`:

The test already asserts the *weak* invariant `best_move != a2a4` (not "must
castle"), and separately asserts move-ordering prefers castling (that part
passes). So this test is **not** over-specific — it needs a real king-safety /
castling-vs-flank-pawn eval fix. The engine plays the aimless `a2a4` at depth 2.

### Git history strongly suggests a small number of recent commits

The failing test files were last set in two engine commits:

- `18d177b STRATEGY15` (2026-06-06): "quiescence depth, pawn-capture filter,
  **check extensions**" — last touched `test_ai_strategy6_regressions` and
  `test_ai_strategy7_regressions`.
- `12c8b5c TEXEL_FIX` (2026-06-08): "**quiescence improvements** + test fixes" —
  last touched `test_ai_quality` (the hanging-rook test).

Because the strategy6/7 tests were committed *alongside* STRATEGY15, they passed
at that commit; something **after** STRATEGY15 broke them. The commits after
STRATEGY15 that can affect search results are:

- `12c8b5c TEXEL_FIX` (quiescence improvements),
- `f010621 TEXEL_FIX2 Phase 3` (**safe TT mate-score handling**),
- `5725e4b TEXEL_FIX2 Phase 1` (deterministic-mode sort-key crash fix),
- `b230cf3 TEXEL_FIX2 Phase 5` (RNG seed before opening book),
- `4d7a33a FIX7 Phase 1` (local RNG — proven NOT the cause earlier).

"Check extensions" (STRATEGY15) + a quiet *check* being overvalued
(hanging-rook) + "quiescence improvements" / "TT mate-score handling" is a
suggestive cluster. This points to a **root-cause-bisect** opportunity rather
than long-term drift.

---

## Questions

### 1. Bisect-first vs. forward eval-tuning? (most important)

The history suggests these 8 broke from a *small number of recent commits*, not
gradual drift. I recommend **git-bisecting the cheap failing tests** (strategy8
~11s, hanging-rook ~2s) to pin the breaking commit(s) before touching eval
weights. Upside:

- one root cause may explain several failures (far more surgical),
- it distinguishes an unintended side-effect (fix at source) from a deliberate
  tuning tradeoff,
- it avoids the whack-a-mole risk of blind eval tuning regressing the 161
  passing slow tests.

The Fix 9 spec assumes forward-fixing via diagnostics + narrow eval tuning and
does not mention bisecting. **Is bisect-first in scope and preferred?** (I would
still build the root-candidate diagnostics the spec asks for; bisect just tells
me *where* to look.)

### 2. Regression bar for the 161 currently-passing slow tests

Any eval/search change can move other engine-strength tests. The full slow suite
is ~48 min. **What is the acceptance bar?**

- (a) All previously-passing slow tests must still pass (one ~48-min full run at
  the end, plus faster per-file runs during iteration), or
- (b) A documented net improvement is acceptable if a fix trades one passing
  test for another?

My default is (a) — no net regressions — with iteration validated on the
related strategy files (faster subsets) and a single full slow run at the end.
Confirm.

### 3. Tie-break determinism in these tests

These tests call `get_best_move(board, depth=2)` **without** `deterministic=True`,
so equal-score ties are decided by RNG (the Fix 7 local `random.Random`).
strategy8 fails 3/3 (deterministic), but some of the other 7 may be
tie-sensitive (flaky). For reliable triage/bisect AND robust regression tests,
may I add `deterministic=True` to these specific tests and to the diagnostics?
This is a robustness change (stable tie-break via `_move_sort_key`), not a
weakening of any assertion. **Acceptable?**

### 4. Conflicting-requirements / priority order

The 8 tests may pull evaluation in opposite directions (material/king-safety vs.
aggression/initiative). If a single tuning cannot satisfy all 8 without
regressing currently-passing tests, what priority do you want?

- fix the clear material/safety bugs (hanging-rook, castling-vs-flank-poke),
- rewrite the genuinely over-specific exact-move tests to broader invariants
  (per Problem 7), with documentation,
- accept and document any residual that cannot be fixed without broader rewrites
  (which are out of scope)?

### 5. Diagnostics location

I plan to put the root-candidate diagnostic helper in `tests/helpers/`
(test-only), so it adds no production API surface and is not held to the
pylint-10 production gate. The spec also allows a dev module under
`chess_game/chess/`. **Confirm `tests/helpers/` is fine**, or do you want it in
production?

### 6. Did ChatGPT 5.5 have a specific theory?

For the hanging-rook failure in particular — did ChatGPT 5.5 propose a specific
mechanism (check extensions, a king-attack/tropism term, quiescence
over/under-valuation, TT mate-score handling)? If so, that would focus the
diagnosis and possibly corroborate the bisect result.

---

## Assumptions I am making

1. This patch may modify production `chess_game/chess/` evaluation/search code,
   but only narrowly (no broad rewrites; no FEN/move-specific hacks).
2. Fix 7/Fix 8 work must be preserved (fast suite, TUI waits, meta-test
   isolation, collection/PositionDB/loss/opening-book behavior tests).
3. Pylint 10.00/10, mypy clean, ruff clean remain hard gates for any production
   change.
4. The full slow suite (~48 min) is run at least once at the end; per-file slow
   runs are used during iteration.
5. Rewriting an over-specific test to a meaningful broader invariant (avoid bad
   move / acceptable set / material threshold) is acceptable and not "weakening
   to get green," provided it still catches the bad behavior and is documented.

---

## Proposed implementation order (pending your answers)

1. Phase 0: baseline — static checks, fast suite, reproduce the 8 (with
   `deterministic=True` if approved) and record expected/actual per test.
2. Build root-candidate diagnostics in `tests/helpers/`.
3. (If approved) git-bisect the two cheap failures to identify breaking
   commit(s); use diagnostics to confirm the mechanism.
4. Fix the clearest tactical/eval bug first (hanging-rook), re-validating the
   related files + a slow subset after each change.
5. Castling-vs-flank-poke, then strategy6, strategy7, endgame1 — fix or rewrite
   per diagnostics.
6. Preserve Fix 7/Fix 8 (re-run their tests).
7. Final validation incl. one full slow-suite run; document any residual.

No code changed.
