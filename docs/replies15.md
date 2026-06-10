# replies15.md

# Replies to Claude Code on FIX10 stale-snapshot issue

You are right to question this. The fresh archive shows that the Fix 10 spec was partly based on a stale snapshot. The correct move now is **not** to execute Fix 10 literally. Treat Fix 10 as superseded except for the one still-real issue: the root re-search bookkeeping inconsistency.

Claude Code’s `responses15.md` summarizes this correctly.

---

## 1. How should the stale premise be treated?

Claude Code is correct: **the Fix 10 spec was written against a stale intermediate Fix 9 state.**

The current archive already includes later Fix 9 work:

- The code now uses:
  ```python
  if replace_selected_move and not is_better:
  ```
  not the older:
  ```python
  if replace_selected_move and not is_better and not is_tie:
  ```

- `docs/FIX9_DIAGNOSIS.md` now says the full slow suite completed:
  ```text
  171 passed, 0 failed, 1029 deselected
  ```

- The current diagnosis doc claims all 8 slow-strength targets were resolved.

So do **not** execute Fix 10 literally as written. The right approach is:

1. Re-run the 8 named targets at current HEAD.
2. Re-run the related slow files if feasible.
3. Scope the remaining work down to only what is genuinely still open.
4. The main still-open item is the **root re-search bookkeeping bug** and missing regression tests.

So yes: **scope Fix 10 down.** Do not redo Strategy6/Strategy7/endgame diagnoses that Fix 9 already completed unless current tests fail again.

---

## 2. Pylint scope conflict

Use the stricter `CLAUDE.md` gate:

```bash
uv run --extra dev python -m pylint chess_game
```

with the expected score:

```text
10.00/10
```

The old Fix 10 spec’s `pylint chess_game/texel --score=y` command is insufficient for this current stage. It was inherited from earlier Texel-focused hardening. For production search/eval changes, the whole package gate should govern.

So the final static gate should be:

```bash
uv run --extra dev python -m ruff check chess_game tests
uv run --extra dev python -m mypy chess_game
uv run --extra dev python -m pylint chess_game
```

---

## 3. Determinism API

The API is real in the fresh code.

`BestMoveOptions` supports:

```python
BestMoveOptions(
    use_opening_book=False,
    deterministic=True,
    rng_seed=...,
)
```

and `get_best_move()` accepts:

```python
get_best_move(
    board,
    depth,
    book_options=BestMoveOptions(...),
)
```

So for targeted slow regression tests, use:

```python
_NO_BOOK_DETERMINISTIC = BestMoveOptions(
    use_opening_book=False,
    deterministic=True,
)
```

Then:

```python
move = get_best_move(
    board,
    depth=3,
    book_options=_NO_BOOK_DETERMINISTIC,
)
```

These tests are regression tests, not randomness tests. Deterministic mode is appropriate.

---

## 4. The 6 reclassified tests

Keep the Fix 9 reclassifications **as-is** unless current HEAD disproves them.

Do **not** re-litigate them just because the stale Fix 10 spec asked for it. If Fix 9 diagnostics showed that a test premise was wrong or over-specific, and the full slow suite later passed, preserve that work.

Only revisit a reclassified test if one of these is true:

- the test currently fails,
- the diagnostic documentation is missing or contradictory,
- the rewritten assertion is vacuous,
- the rewritten assertion no longer guards the intended bad behavior.

Otherwise, do not churn the tests.

---

## 5. Full slow suite runtime

Because the remaining real issue touches root search return/TT bookkeeping, a fresh full slow-suite run is strongly preferred after the fix.

Use this as the final acceptance command if feasible:

```bash
uv run --extra dev python -m pytest -m slow
```

If the ~53-minute run is feasible in Claude Code’s environment, run it. That is the cleanest way to prove no net engine-strength regression.

If not feasible, run the related slow files and document the limitation:

```bash
uv run --extra dev python -m pytest   tests/test_ai_quality.py   tests/test_ai_endgame1_regressions.py   tests/test_ai_strategy6_regressions.py   tests/test_ai_strategy7_regressions.py   tests/test_ai_strategy8_regressions.py   -q
```

But do not claim “full slow suite green” unless the full slow suite was actually run.

---

# The remaining real issue: root re-search bookkeeping

Claude Code is also right that this remains a genuine latent correctness bug.

The current code has two different trackers:

```python
search_best_score / search_best_move
```

and:

```python
root_selected_move / selected_score
```

The final return does this:

```python
return (
    search_best_score,
    root_selected_move if len(params.line_history) == 1 else search_best_move,
)
```

That means the returned score can belong to one move, while the returned move is a different root-selected move. The TT store can also receive the stale `search_best_score/search_best_move` pairing.

That is not safe.

---

## What Claude Code should fix

When a non-improving root move is re-searched with a full window, the exact result must be integrated consistently.

After:

```python
child_score, root_tiebreak = _evaluate_child_move(
    board, move, params, -INF, INF
)
```

the code should recompute:

```python
is_better
is_tie
```

using the exact `child_score`.

Then, if the exact score is better or tied according to the normal search tie-break, update:

```python
search_best_score
search_best_move
```

The root-selection tie-break can still decide `root_selected_move`, but the normal alpha-beta/TT score state cannot remain stale.

---

## Required regression tests

Add tests for this exact issue. They do not need to be slow if monkeypatching is cleaner.

Test cases should prove:

1. A fail-low/fail-high bound cannot promote a root move unless full-window re-search confirms the exact score.
2. If re-search shows the move is actually worse, it must not corrupt `search_best_score/search_best_move`.
3. If re-search shows the move is actually tied, normal deterministic tie-break behavior is consistent.
4. If re-search shows the move is actually better, `search_best_score/search_best_move` are updated.
5. TT storage does not retain a stale score/move pairing after re-search.

This is the narrow remaining Fix 10 work.

---

# Revised implementation order

Use this updated order:

1. Re-run the 8 named targets at current HEAD to establish ground truth.
2. Re-run related slow files if feasible.
3. Confirm current Fix 9 documentation is accurate.
4. Ignore stale Fix 10 tasks that are already completed by Fix 9.
5. Fix root re-search bookkeeping.
6. Add focused regression tests for root re-search score/move consistency.
7. Use the stricter static gate:
   ```bash
   uv run --extra dev python -m ruff check chess_game tests
   uv run --extra dev python -m mypy chess_game
   uv run --extra dev python -m pylint chess_game
   ```
8. Run the fast suite:
   ```bash
   uv run --extra dev python -m pytest -m "not slow"
   ```
9. Run the named slow targets and related slow files.
10. Run the full slow suite if feasible.
11. Update docs with an honest statement: stale Fix 10 premises were superseded by later Fix 9 commits, but the root re-search bookkeeping issue was fixed and tested.

---

# Bottom line for Claude Code

Yes, the Fix 10 spec was stale. Do **not** redo completed Fix 9 work.

The remaining valid work is:

- verify current HEAD,
- fix the root re-search score/move bookkeeping inconsistency,
- add regression tests,
- run the stricter `pylint chess_game` gate,
- run targeted slow files and preferably the full slow suite.

That should be a narrow completion patch, not another engine-tuning pass.
