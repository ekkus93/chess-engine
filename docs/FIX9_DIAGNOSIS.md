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
narrowest engine change. Pending confirmation before implementing, given
engine-wide tie-break changes touch the 161 passing slow tests.

---

## Remaining 7 failures

Not yet diagnosed in this checkpoint. Same method to follow: bisect (cheap ones)
+ root-candidate diagnostics, then fix-or-reclassify per replies14.md priority
order (king-safety/castling next, then strategy6/7/endgame by shared cause).
