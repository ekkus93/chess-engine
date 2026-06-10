# responses15.md — Questions & Issues on FIX10 (CHESS_ENGINE_SLOW_STRENGTH_FIX10)

**Date:** 2026-06-10T19:03:06Z
**Model:** Claude Opus 4.8 (1M context)
**Tree state at review:** HEAD = `7d0a7f4` (5 commits ahead of the review snapshot `e0a0157`)
**Status:** No code changed. This is a read-through of
`docs/CHESS_ENGINE_SLOW_STRENGTH_FIX10_SPEC.md` and
`docs/CHESS_ENGINE_SLOW_STRENGTH_FIX10_TODO.md`, cross-checked against the actual
source tree.

---

## Headline issue: the FIX10 SPEC was written against a stale snapshot

ChatGPT 5.5 wrote FIX10 against commit **`e0a0157` ("added code review")**, which
sits immediately after `bd9318f` — the **"2 of 8 done"** point of FIX9. The
subsequent `git pull` rebased the remaining FIX9 commits *on top* of it, so the
current HEAD (`7d0a7f4`) is **5 commits ahead** of what the review saw:

```
7d0a7f4 added missing files            <- current HEAD
bcb54b5 FIX9 COMPLETE: slow suite green (171/0)
b46df82 FIX9: document root false-tie fix ...
35c2e55 FIX9: fix root false-tie from fail-high bound; resolve final 2 (8/8)
376ec01 FIX9: record 6/8 resolved ...
746b549 FIX9: reclassify 4 over-specific slow strength tests
e0a0157 added code review              <- what the FIX10 SPEC reviewed (2/8 state)
bd9318f FIX9: strategy8 fail-low bound (2/8)
85e74fe FIX9: hanging-rook (1/8)
```

Because of this, several FIX10 premises are **already false at current HEAD**:

- **Problem 1's "current code"** is quoted in the SPEC as:
  ```python
  if replace_selected_move and not is_better and not is_tie:
  ```
  The real code (`chess_game/chess/ai.py:652`) is already:
  ```python
  if replace_selected_move and not is_better:
  ```
  That was FIX9's final false-tie fix (`35c2e55`). The `and not is_tie` clause the
  SPEC wants removed is already gone.

- **Problem 2's endgame failure** ("Expected start square: a5 / Actual: d4") — that
  test was already reclassified in FIX9; `tests/test_ai_endgame1_regressions.py`
  currently passes.

- **Problems 3 & 4 (Strategy6 / Strategy7)** — already diagnosed and dispositioned
  in FIX9 (`docs/FIX9_DIAGNOSIS.md`), and the **full slow suite ran 171 passed /
  0 failed** at the end of that session.

So a literal reading of FIX10 — "finish the 6 still-failing targets" — is largely
already done. Before doing any FIX10 work I would re-run the 8 named targets at
current HEAD to establish ground truth, rather than trust either the stale review
or the prior FIX9 completion report.

---

## FIX10 is NOT entirely moot: Problem 1 names a real, still-open latent bug

This is the one part of FIX10 with teeth, and it is independent of the stale
premise. Reading the re-search block (`chess_game/chess/ai.py:631–712`), there are
**two parallel "best" trackers**:

- `search_best_score` / `search_best_move` — the alpha-beta in-window value. Feeds
  `_update_alpha_beta`, the **TT store** (`ai.py:705`), and the **returned score**
  (`ai.py:710`).
- `root_selected_move` / `selected_score` — the tie-break-aware root choice. This
  is the **returned move at root** (`ai.py:711`).

When the full-window re-search (`ai.py:652–676`) computes a move's **exact** score,
it only re-runs `_prefer_root_move`. It does **not**:

- recompute `is_better` / `is_tie` from the exact score, nor
- update `search_best_score` / `search_best_move`.

Consequence: a re-search that promotes `root_selected_move` can make the root
return `(search_best_score, root_selected_move)` where **the score belongs to a
different move than the returned move**, and the **TT stores the stale pairing**
(`_store_tt_cache(..., search_best_score, search_best_move, ...)` at `ai.py:702`).
This is exactly the bookkeeping inconsistency Problem 1 describes — it is present
in the current code, and FIX9 never added regression tests for it. Worth fixing
plus testing regardless of the stale premise.

Return site for reference (`ai.py:709–712`):
```python
return (
    search_best_score,
    root_selected_move if len(params.line_history) == 1 else search_best_move,
)
```

---

## Open questions for the user

1. **How should the stale premise be treated?**
   Recommendation: first re-run the 8 named targets + related files at current HEAD
   to establish ground truth, then scope FIX10 down to *only what is genuinely
   still open* (chiefly Problem 1's bookkeeping fix + its missing regression tests
   + the determinism/pylint items below), instead of re-doing diagnoses that FIX9
   already completed and the slow suite already validated. Does that match intent,
   or should FIX10 be executed literally as written?

2. **Pylint scope conflict.**
   FIX10 repeatedly uses `pylint chess_game/texel --score=y`, but `CLAUDE.md`'s gate
   is the stricter `pylint chess_game` at **10.00/10**. Which governs? Default
   assumption: keep the stricter CLAUDE.md gate unless told otherwise.

3. **Determinism API.**
   Phases 2 & 5 assume `BestMoveOptions(use_opening_book=False, deterministic=True)`.
   The engine internally uses `params.context.deterministic` / `params.context.rng`,
   but a public `BestMoveOptions` with those exact kwargs has not been confirmed to
   exist. Is that API real, or should the current public entry point be used
   ("or the equivalent current API," as the SPEC itself hedges)?

4. **The 6 reclassified tests.**
   FIX9 already widened 4 over-specific assertions and rewrote 2 false-premise ones
   (Strategy6 clean_rook_capture, Strategy7 only_blockade), all validated against
   the full slow suite. Keep them as-is, or re-litigate them under FIX10's
   Problems 2–4 (which were written without knowing they'd been done)?

5. **Full slow suite runtime.**
   The full slow suite is a ~53-minute run; FIX9 already has one green run on
   record. If Problem 1's fix changes search return / TT values, a fresh full slow
   run would be wanted to prove no net regression. Is the ~53-minute runtime
   acceptable, or should only the related slow files be run with the limitation
   documented (as the SPEC permits)?

---

## Short version

The FIX10 SPEC mostly fixes a problem the rebase already carried past — but its
**Problem 1 (root re-search bookkeeping + missing tests)** is a genuine,
still-open correctness issue worth doing. Awaiting direction on the questions
above before changing any code.
