# FIX9 Diagnosis Log

Honest, evidence-based triage of the 8 slow engine-strength failures. Diagnosis
before any engine change (per replies14.md: bisect for "where", root-candidate
diagnostics for "why").

Tooling: `tests/root_diagnostics.py::debug_root_candidates(board, depth=...)`
reports, per legal root move, the depth-N White-relative search score, static
eval after the move, and quiescence score after the move.

---

## Hanging-rook (`test_ai_quality.py::test_simple_quality_benchmark_prefers_hanging_rook_capture`)

Position: Ka1, Qd4 (White); Kh8, Rd5 (Black); White to move, depth 2.
Expected `d4d5` (Qxd5). Engine plays `d4f6` (Qf6+).

### Bisect — first bad commit

Portable probe (construct position, run `get_best_move(depth=2)`, check move) run
across `chess_game/chess/` checked out at each commit:

```
b62b841 GOOD   17e5c4e GOOD   18d177b(STRATEGY15) GOOD   913437d GOOD   1463a09 GOOD
12c8b5c(TEXEL_FIX) BAD   ...   HEAD BAD
```

**First bad commit: `12c8b5c` "TEXEL_FIX: ... quiescence improvements".** GOOD at
its parent `1463a09`. The hanging-rook test was *added in 12c8b5c itself* and was
already failing there (it is slow-marked, so the slow suite was not run green).

### Mechanism — confirmed by root-candidate diagnostics (NOT what the spec assumed)

The spec framed this as "a quiet check beats winning a rook." Diagnostics show
something subtler:

```
move   score   static_after   (depth 2, deterministic)
d4d5    8580        8659       win the rook NOW
d4f6    8580        3333       Qf6+, win the rook NEXT move
d4b2    8580        3319       quiet, win the rook NEXT move
```

All three moves **tie at search score 8580** — the engine wins the rook in every
line. `12c8b5c` broadened quiescence captures (`_select_quiescence_moves`
replaced the old `_is_interesting_capture` filter, which had *rejected* Q-takes-R
because captured(rook 500) < attacker(queen 900)). With the broader quiescence,
`QxR` is now seen in the follow-up of `d4f6`/`d4b2`, so those lines also realize
the rook and tie with the immediate `d4d5`. Random tie-break then picks `d4f6`.

So this is **not a gross blunder** (the engine wins the rook either way) and the
old quiescence filter was arguably *too* restrictive (it excluded a winning
QxR). The real gap: among equal-score root moves, the engine does not prefer to
**realize material immediately**. This is the "exact score tie" case replies14.md
flagged (section 3): resolve via a stronger eval/selection preference, or via an
acceptable-set test — not by reverting the quiescence improvement.

### Candidate fixes (for decision)

1. **Root tie-break prefers higher static-eval-after among equal search scores**
   (realize advantage sooner). Narrow: only changes tie resolution at root
   selection, not search values — so it cannot change any test where the best
   move is strictly best; it only affects ties. Lower regression risk, but still
   must be validated against the 161 passing slow tests.
2. **Rewrite the test** to a meaningful invariant: the engine wins the rook
   (e.g., the chosen line captures the rook / material gain >= rook), rather than
   requiring the exact square `d4d5`. Defensible because `Qf6+` then `QxR` is
   objectively winning; but the spec prefers an engine fix here.

Recommendation: option 1 (general "prefer realizing material sooner" root
tie-break) — it matches replies14.md's "stronger eval preference" and is the
narrowest engine change.

### FIXED (option 1 implemented)

Diagnostics revealed the real imbalance: at the exact tie, `root_stability_adjustment`
gave `Qf6+` an `_attacking_root_bonus` of **46** (speculative queen pressure near
the king) vs `Qxd5`'s 30 — so a speculative nudge outranked concrete material.

Fix (`chess_game/chess/ai_search_helpers.py`): added `_material_realization_bonus`
to `root_stability_adjustment` — a mover-relative root tie-break scaled by
captured value (`MATERIAL_VALUES[captured] // 10`) and capped at 49 (just under
`ROOT_TIEBREAK_MARGIN`=50). A concrete capture now outranks the speculative
attack/strategic nudges at (near-)equal search scores, but cannot override a
score difference the search judged larger than the tie band.

Validation: hanging-rook passes; `test_ai_quality.py` 52 passed; fast suite 1029
passed; strategy6/7/8 + endgame1 files 88 passed (only the other 7 known
failures remain — no new regressions). Full slow suite to be run at the end.

---

## Strategy8 flank-poke (`test_strategy8_search_demotes_flank_poke_when_castling_is_available`)

Position: a constructed middlegame; White to move, depth 2. Expected `!= a2a4`.
Engine plays `a2a4` deterministically (all seeds) — so NOT tie-break flakiness.

### Bisect — same first bad commit as hanging-rook

`12c8b5c` BAD, parent `1463a09` GOOD (plays `d1d5`). So `12c8b5c` broke both.

### Mechanism — a genuine SEARCH bug (not eval)

Scoring each candidate through the engine's real root machinery
(`search_root_depth` on each child):

```
a2a4 = 2256   (lowest!)   e1g1 = 2641   e2c4 = 2680   d1d5 = 3945
```

The engine returns the **worst** move. Not aspiration (full window also picks
a2a4), not TT (TT disabled also picks a2a4). Replicating the root loop:

```
e1g1: child_score=2641  -> selected
d1d5: child_score=3945  -> selected (alpha now 3945, correct)
a2a4: child_score=3919  tiebreak=111  REPLACE=True -> a2a4
```

`a2a4`'s true value is 2256, but searched against the raised `alpha=3945` it
returns a **fail-low bound of 3919** (just under alpha). `prefer_root_move` then
sees a fake 26-point near-tie and `a2a4`'s high tie-break (111 vs 20) triggers
the score-gap<0 override, promoting it over the genuinely best `d1d5`.

Root cause: **the root tie-break override treats an alpha-beta fail-low/high
bound as if it were the move's exact value.** Under alpha-beta a non-improving
move's `child_score` is only a bound, so the "promote a slightly-lower-scoring
but higher-tie-break move" override is unsound. (Why 12c8b5c surfaced it: the
quiescence/eval changes shifted a2a4's bound into the tie margin and/or its
tie-break above the threshold.)

### FIXED

`ai.py` `_search_move_loop`: when the override would promote a move that neither
improves nor ties the best exact score (i.e. its `child_score` is a bound),
**re-search that one move with a full window** to get its exact value and
re-decide via `prefer_root_move`. A bounded-worse move (a2a4 -> true 2256) is
then correctly rejected, while a genuine near-tie (e.g.
`test_search_plays_active_queen_move_with_pawn_threat`: Qd1-g4 vs e4xd5) is
preserved. Targeted: the re-search only runs when the override would otherwise
fire on a non-improving move (rare).

A first attempt (a blunt guard rejecting all non-improving overrides) regressed
that opening test by also rejecting genuine near-ties — the re-search version
distinguishes the two correctly.

Validation: strategy8 passes; the opening near-tie test passes; hanging-rook
still passes; fast suite 1029 passed; ruff/mypy clean. Strategy6/7/endgame1
likely share this root cause (same 12c8b5c origin) — slow validation pending.

## Remaining failures

Strategy6 x3, strategy7 x2, endgame1 — re-checking after the search fix (it may
resolve several given the shared 12c8b5c origin), then fix-or-reclassify any
residual per replies14.md.
