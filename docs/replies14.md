# replies14.md

# Replies to Claude Code on FIX9 Slow-Suite Engine-Strength Triage

Your read-only investigation is exactly the right direction. Fix 9 is different from Fix 7/Fix 8 because it may touch production evaluation/search code, so the bar is higher: diagnose first, change narrowly, and avoid whack-a-mole tuning.

The important correction is this: **yes, bisect-first is in scope and preferred** if the failures can be reproduced cheaply enough. The spec emphasized root-candidate diagnostics because we need to understand the score differences, but git history is also a diagnostic tool. Use both.

---

## 1. Bisect-first vs. forward eval-tuning

Use **bisect-first** for the cheap, clear failures.

I agree with your assessment that the failures may come from a small number of recent search/eval commits rather than long-term drift. That is too valuable to ignore.

Recommended approach:

1. Pick the two clearest/cheapest failures:
   - `tests/test_ai_quality.py::test_simple_quality_benchmark_prefers_hanging_rook_capture`
   - `tests/test_ai_strategy8_regressions.py::test_strategy8_search_demotes_flank_poke_when_castling_is_available`

2. Run a git bisect or manual commit checkout over the suspect commit range.

3. Use the bisect result to focus diagnosis:
   - quiescence changes,
   - check extensions,
   - TT mate-score handling,
   - move ordering/tie handling,
   - eval term changes.

4. Still build root-candidate diagnostics, because bisect tells you **where** the behavior changed, but diagnostics tell you **why** the current engine is choosing the wrong move.

Do not do blind eval tuning before bisecting the cheap failures.

A practical command shape for bisect testing is fine:

```bash
uv run --extra dev python -m pytest   tests/test_ai_quality.py::test_simple_quality_benchmark_prefers_hanging_rook_capture   -q
```

and separately:

```bash
uv run --extra dev python -m pytest   tests/test_ai_strategy8_regressions.py::test_strategy8_search_demotes_flank_poke_when_castling_is_available   -q
```

If a commit cannot run because dependencies or APIs changed, mark it skipped/inconclusive and continue manually.

---

## 2. Regression bar for the 161 currently-passing slow tests

Use option **A: no net regressions**.

Default acceptance bar:

```text
All previously-passing slow tests should still pass.
```

Recommended workflow:

1. During iteration, run targeted failing tests and nearby files.
2. After each production eval/search change, run the related strategy file(s).
3. Before declaring completion, run one full slow-suite pass if feasible:
   ```bash
   uv run --extra dev python -m pytest -m slow
   ```

If full slow suite runtime is too long, document the limitation, but do not use that as an excuse to ignore related failures. At minimum, run:

```bash
uv run --extra dev python -m pytest   tests/test_ai_quality.py   tests/test_ai_endgame1_regressions.py   tests/test_ai_strategy6_regressions.py   tests/test_ai_strategy7_regressions.py   tests/test_ai_strategy8_regressions.py   -q
```

A documented net tradeoff is **not** acceptable by default. If a change fixes one failure but breaks another previously passing slow test, that is not done; continue diagnosing.

The only exception is if diagnostics show a previously passing test was itself wrong or over-specific. In that case, rewrite it with a meaningful invariant and document why.

---

## 3. Tie-break determinism in these tests

Yes, add `deterministic=True` to these specific slow engine-strength tests and diagnostics where the API supports it.

This is acceptable because it makes triage and regression tests stable. It is not a weakening of the assertion. It prevents random tie-break behavior from obscuring whether search/eval actually prefers the expected move.

Use deterministic mode for:

- the 8 targeted slow tests,
- root-candidate diagnostics,
- bisect scripts if possible.

Guidelines:

- Do not change production default behavior just for these tests.
- Do not use deterministic mode to hide a real scoring problem.
- If a test only passes because deterministic tie-break chooses the expected move among exact equal scores, inspect the score tie. In that case, the test may need to assert an acceptable set or the eval may need a stronger preference.

---

## 4. Conflicting requirements / priority order

Use this priority order:

1. **Fix clear material/tactical bugs first.**
   - The hanging-rook test is the least subjective.
   - A quiet queen check should not beat winning a free rook unless there is a concrete tactic.

2. **Fix clear king-safety / unsafe-pawn-lunge bugs second.**
   - The strategy8 test is already a weak invariant: `best_move != a2a4`.
   - It is not over-specific. It should be treated as a real bug unless diagnostics prove otherwise.

3. **Then address strategy6/strategy7/endgame tests by shared root cause.**
   - Look for common eval/search causes after the first two fixes.
   - Do not tune each transcript in isolation.

4. **Rewrite exact-move tests only when diagnostics justify it.**
   - Acceptable: exact expected move becomes an acceptable set or “avoid known bad move.”
   - Not acceptable: `assert move is not None` or any vacuous assertion.

5. **Do not accept residual failures without explicit classification.**
   - If something cannot be fixed within the narrow patch, document it honestly as deferred, but the preferred goal is targeted slow tests all pass.

So yes: clear material/safety bugs should be fixed first; genuinely over-specific exact-move tests can be rewritten to broader meaningful invariants; residuals should only be deferred if they require a broader rewrite outside scope.

---

## 5. Diagnostics location

`tests/helpers/` is fine and preferred.

Put root-candidate diagnostics in test-only code unless there is already a clean dev-diagnostic module. This avoids adding production API surface and avoids making the engine package carry debugging utilities.

Recommended location:

```text
tests/helpers/root_diagnostics.py
```

or similar.

The helper can be imported by the relevant regression tests or used in temporary/local debugging. If the helper is only for diagnosis and not needed after the fix, it can remain as a reusable test helper if it is clean and covered lightly, or it can be removed before final if it becomes dead code.

Keep it simple. Minimum useful output:

- move,
- search/root score,
- static eval after move,
- whether it was selected,
- optional move-order score if easy.

Do not let diagnostics become a broad production feature.

---

## 6. Specific theory from ChatGPT 5.5

The strongest theory is not one single confirmed bug yet, but the evidence points to this cluster:

1. **Quiet check / queen tropism / king-attack scoring may be overvalued** relative to immediate material.
   - Hanging-rook failure: `Qf6+` beats `Qxd5`.
   - That is suspicious because the check is not mate and does not win the rook.

2. **Quiescence or check-extension behavior may be inflating forcing-looking quiet checks.**
   - The history you found around STRATEGY15 and TEXEL_FIX is relevant.
   - Check extensions plus quiescence changes are plausible root causes.

3. **Root child evaluation may overpower move ordering.**
   - Strategy8 shows move ordering likes castling, but depth-2 search still chooses `a2a4`.
   - That points to leaf/root eval, not ordering alone.

4. **Castling/king-safety value may be too weak relative to flank-pawn/space terms.**
   - The flank poke before castling is a classic symptom.

5. **TT mate-score handling is a possible suspect, but not my first guess for the rook test.**
   - Keep it in the bisect range, but diagnostics should show whether mate/near-mate scores are involved.

So the concrete first diagnostic question for hanging-rook should be:

```text
Why does Qf6 score higher than Qxd5?
```

Look specifically at:

- whether Qf6 gets a check extension,
- whether Qf6 receives king-attack/tropism/check bonuses,
- whether Qxd5 static material gain is visible at root,
- whether quiescence after Qxd5 sees a false refutation,
- whether a TT entry is reused incorrectly,
- whether perspective/sign flips between candidate scores.

Do not assume the cause until diagnostics/bisect confirm it.

---

# Responses to your assumptions

| Assumption | Answer |
|---|---|
| Production `chess_game/chess/` may be modified narrowly | Yes. |
| Fix 7/Fix 8 work must be preserved | Yes. Hard requirement. |
| Ruff/mypy/Pylint gates remain hard | Yes. |
| Full slow suite should be run at least once at end | Yes, if feasible. If not, document limitation and run related slow files. |
| Meaningful broader invariants are acceptable | Yes, when justified by diagnostics. |

---

# Recommended implementation order

Use this order:

1. Baseline static checks and fast suite.
2. Reproduce the 8 targeted slow failures.
3. Add `deterministic=True` to the targeted tests/diagnostics where supported.
4. Add root-candidate diagnostics in `tests/helpers/`.
5. Bisect the two cheap failures:
   - hanging rook,
   - strategy8 flank poke.
6. Diagnose hanging-rook first.
7. Fix the smallest general cause of hanging-rook failure.
8. Re-run `tests/test_ai_quality.py`.
9. Diagnose and fix strategy8 flank-poke.
10. Re-run `tests/test_ai_strategy8_regressions.py`.
11. Re-run the remaining strategy6/strategy7/endgame failures and look for shared fixes.
12. Rewrite exact-move assertions only when diagnostics prove they are over-specific.
13. Re-run Fix 7/Fix 8 targeted tests.
14. Run final validation:
    ```bash
    uv run --extra dev python -m ruff check chess_game tests
    uv run --extra dev python -m mypy chess_game
    uv run --extra dev python -m pylint chess_game/texel --score=y
    uv run --extra dev python -m pytest -m "not slow"
    ```
15. Run targeted slow tests and full slow suite if feasible.

---

# Extra guidance: do not overclaim

If bisect finds the breaking commit, document:

- first bad commit,
- command used,
- expected/actual move at good commit,
- expected/actual move at bad commit,
- likely mechanism.

If a test is rewritten, document:

- old assertion,
- why it was too exact,
- new invariant,
- what bad move/behavior it still catches.

If a production change fixes some tests but not all 8, do not declare completion. Either continue or document the remaining failures as deferred with a clear reason.

The goal is not just green tests. The goal is to understand and stabilize the engine-strength regressions without creating new whack-a-mole behavior.
