# FIX10 Completion Diagnosis

Honest record of the Fix 10 completion patch. Fix 10 was specced against a **stale
intermediate Fix 9 snapshot**; most of its "still failing" premises were already
resolved by later Fix 9 commits that a `git pull` rebased on top of that snapshot.
The one genuinely-open item — a root re-search **bookkeeping** inconsistency — is
fixed and regression-tested here.

See `docs/responses15.md` for the question/answer exchange that scoped this patch,
and `docs/replies15.md` for the user's decisions.

---

## 1. Stale-premise finding (why most of Fix 10 was already done)

The Fix 10 SPEC/TODO were written against commit `e0a0157 "added code review"`,
which sits immediately after `bd9318f` — the **2-of-8** point of Fix 9. The pull
rebased the remaining Fix 9 commits on top of it, so at the current HEAD:

- The root re-search gate is already `if replace_selected_move and not is_better:`
  (Fix 9 `35c2e55`), not the SPEC's quoted `... and not is_tie`.
- The endgame cutoff test and the Strategy6/Strategy7 targets were already
  diagnosed and dispositioned in Fix 9 (`docs/FIX9_DIAGNOSIS.md`).

**Ground-truth re-run at HEAD (before any Fix 10 change), the 8 named targets:**

```
8 passed in 276.17s (0:04:36)
```

So the targeted set was already green. Per the user's direction (replies15.md),
Fix 10 was scoped down to the bookkeeping fix + tests + determinism + docs rather
than re-doing completed Fix 9 diagnoses.

---

## 2. Root re-search bookkeeping bug (the real Fix 10 item)

### The defect

`_search_move_loop` (`chess_game/chess/ai.py`) keeps two "best" trackers:

- `search_best_score` / `search_best_move` — the alpha-beta in-window value. Feeds
  `_update_alpha_beta`, the TT store (`_store_tt_cache`), and the **returned root
  score**.
- `root_selected_move` / `selected_score` — the tie-break-aware root choice; the
  **returned move** at root.

Fix 9 added a full-window re-search so a non-improving root move's *bounded*
`child_score` (an alpha-beta fail-low/high value, not its exact value) cannot win
the root tie-break unless an exact re-search confirms it. But the re-search only
re-ran `_prefer_root_move`; it did **not** re-fold the exact score into
`search_best_score` / `search_best_move`. Consequence: when the exact re-search
proves a move is actually the best, the root could return
`(search_best_score, root_selected_move)` with the **score belonging to a different
move than the returned move**, and the TT could store that stale score/move
pairing.

### The fix

After the full-window re-search, re-fold the exact score into the search best
before deciding root selection, so `search_best_score` / `search_best_move` (and
therefore alpha-beta, the TT store, and the returned root score) reflect the exact
value rather than the discarded bound. The fold logic — `(is_better, is_tie)`
comparison plus the deterministic tie-break update — was extracted into a single
helper `_fold_search_best(params, child_score, search_best_score, search_best_move,
move)` used at both the normal and the re-search update sites. This keeps the two
sites in lockstep and (by removing the duplicated inline `if/else`) keeps
`_search_move_loop` within the pylint branch budget; `pylint chess_game` stays at
10.00/10.

A bounded non-improving move can only resolve to an exact value that is *no better*
than the running best, so in normal alpha-beta this update fires on a genuine exact
tie (consistent TT move) and never silently leaves a bound in the search-best
state. The intentional clearly-winning practical-override path
(`_strong_root_tiebreak_override`, e.g. Strategy7 only_blockade) still lets the
played `root_selected_move` differ from the objective `search_best_move`; that is a
root *playing* preference, not stale bookkeeping, and is preserved.

### Regression tests

`tests/test_root_research_bookkeeping.py` drives `_search_move_loop` directly with a
scripted fake `_evaluate_child_move` (first evaluation of a move = bounded score,
second = exact full-window score). Deterministic and fast (no real search):

1. `test_bounded_high_tiebreak_move_cannot_promote_when_exact_is_worse` — a fail-low
   bound with a huge tie-break (the Fix 9 a2a4 pattern) is rejected once the exact
   re-search proves it worse; search-best/TT stay on the genuine best.
2. `test_exact_better_rescore_updates_search_best_and_return` — when the exact
   re-search proves a move actually best, the returned `(score, move)` and the TT
   entry agree on the exact value. **This test fails without the fix** (returns the
   stale score of a different move: `assert 100 == 160`), demonstrating the bug.
3. `test_genuine_exact_tie_is_resolved_deterministically` — a confirmed exact tie is
   resolved identically across runs; the returned score stays the tie value.
4. `test_minimizing_side_bounded_move_cannot_promote_when_exact_is_worse` — the
   minimizing-side mirror of (1).

Verified by stashing the fix: only test (2) flips to failing without it; the others
lock in pre-existing (Fix 9) correct behavior.

---

## 3. Endgame / Strategy6 / Strategy7 status (already resolved in Fix 9)

No new diagnosis was required: all six were already dispositioned in
`docs/FIX9_DIAGNOSIS.md` (4 over-specific assertions widened to documented
acceptable sets, 2 false-premise assertions rewritten with diagnostic evidence),
and all pass at HEAD. The Fix 10 change does not alter any of those assertions. Fix
10 only added deterministic options to the targeted calls (Section 4).

Reclassified assertions remain non-vacuous (each still rejects the specific bad move
it was written to guard — the king-loosening g-pawn lunge, the Na7 rim retreat, the
...Rxa4-into-Qg6 blunder, the win-throwing rook abandonments, the wrong-side check)
and carry their FIX9 diagnostic rationale inline.

---

## 4. Deterministic targeted slow tests

The 8 named targets now pass `BestMoveOptions(use_opening_book=False,
deterministic=True)` via `get_best_move(..., book_options=...)`, so they no longer
depend on opening-book lookup or random equal-score tie-breaking. Production default
behavior is unchanged. With deterministic tie-breaking the result is stable by
construction (no RNG in the selection path).

Targeted set with deterministic options (post-change):

```
8 passed in 296.94s (0:04:56)
```

---

## 5. Validation commands and results

(Filled in as runs complete.)

Static gates:

```
ruff check chess_game tests        -> all checks passed
mypy chess_game                    -> success, no issues (76 files)
pylint chess_game                  -> 10.00/10 (3 pre-existing R0911, unchanged from baseline)
```

Bookkeeping + search regression (post-refactor):

```
tests/test_root_research_bookkeeping.py + tests/test_ai_search.py
  + tests/test_search_terminal_scores.py  -> 75 passed
```

Full fast suite:

```
pytest -m "not slow"   -> 1033 passed, 171 deselected in 33.10s
```

(1033 = prior 1029 + the 4 new root re-search bookkeeping tests.)

Fix 7 behavior preservation:

```
test_collect / test_position_db / test_loss / test_opening_book (not slow)
  -> 85 passed, 6 deselected
```

Fix 8 TUI runtime preservation:

```
grep for pause(delay=2|3)/sleep(2|3) in tests   -> none found
tests/test_tui.py (not slow)                     -> 31 passed in 9.23s (slowest call 0.82s)
test_test_runtime_markers_integration.py         -> pytestmark = pytest.mark.slow (intact)
```

8 named targets (deterministic options + bookkeeping fix):

```
-> 8 passed in 296.94s (0:04:56)
```

Full slow suite (the no-net-regression gate):

```
pytest -m slow   -> 171 passed, 1033 deselected in 3179.34s (0:52:59)
```

Identical pass count to the Fix 9 baseline (171 passed / 0 failed) — **no net
regression**. The deselected count rose from 1029 to 1033 only because the 4 new
fast bookkeeping tests are excluded by the `slow` marker.

---

## 6. Scope honesty

- Fix 10 did **not** redo completed Fix 9 work; it superseded the stale premises.
- The only engine change is the root re-search bookkeeping fold + the helper
  extraction that keeps pylint at 10.00/10. No FEN-specific or move-specific hacks.
- No new vacuous assertions; no production default behavior change.
- The full slow suite was actually run: **171 passed / 0 failed**, matching the
  Fix 9 baseline (Section 5).
