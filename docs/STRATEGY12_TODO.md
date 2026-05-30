# STRATEGY12: Endgame Conversion Acceleration TODO

## Overview

STRATEGY11 established move-1 discipline, advantage preservation, and basic endgame bonuses, but the latest depth-3 self-play revealed extended endgames:

1. **Black won via Queen vs. King after 130 moves** — should be ~10 moves in Q vs K endgame.
2. **Pawn race and king tempo decisions are imprecise** — engine does not sharply calculate "who promotes first" or prioritize king proximity to passed pawns.
3. **Forced-win sequences are not accelerated** — in trivial victories (up a queen), the engine plays safe but slow quiet moves instead of forcing conversion.

This round focuses on:
- **Pawn endgame tempo races** — sharper calculation of who promotes first when both sides have passed pawns.
- **King centralization urgency** — aggressive king activity rewards in low-material endgames.
- **Forced-win detection** — identify and prioritize moves that lead to certain conversion (e.g., checks, pawn pushes, piece captures that guarantee faster mate).

## Relevant Files

- `chess_game/chess/endgame_evaluation.py` — endgame evaluation heuristics and scoring
- `chess_game/chess/passer_race_guidance.py` — passed-pawn race logic (existing but may need refinement)
- `chess_game/chess/simple_endgame_guidance.py` — simple endgame heuristics including king activation
- `chess_game/chess/ai_move_ordering.py` — quiet move ordering; can feed endgame-specific bonuses
- `chess_game/chess/ai_search_helpers.py` — root tie-breaks and conversion tie-breaks
- `tests/test_ai_strategy12_regressions.py` — new regression coverage for this round

---

## Task 0 — Baseline analysis and test scaffolding

**Goal:** Analyze the 130-move Q vs K game to identify where the slowness occurred and create regression fixtures.

- [x] **0a** Parse `tmp/self_play_d3d3_20260530T110610Z.txt` to identify key phases:
  - When did the game transition from middlegame to endgame?
  - Where were pawn races / passed pawns?
  - At what move did Q vs K start, and how many moves did it take to mate?
  - Save detailed analysis to `tmp/strategy12_baseline_analysis.txt`.
- [x] **0b** Extract positions from the game:
  - A pawn race position (if any) where both sides have passed pawns.
  - A king-centralization critical position (e.g., K+P vs K).
  - The Q vs K position just before mate sequence.
  - Save FEN positions to `tmp/strategy12_sample_positions.txt`.
- [x] **0c** Create `tests/test_ai_strategy12_regressions.py` with board helpers for:
  - Pawn race scenarios (both sides with passed pawns; verify tempo calculation).
  - King centralization urgency (K+P vs K; verify king moves toward pawn promotion square).
  - Q vs K forced mate (verify engine finds mate within N moves at depth 3).
  - R+P vs R, R vs B+K endgame conversion speed.
- [x] **0d** Add baseline assertions that expose slow conversion and imprecise pawn race decisions.

---

## Task 1 — Pawn race tempo calculation refinement

**Goal:** When both sides have passed pawns, sharply estimate who queens first and reward the leading side's promotion-push moves.

**Files:** `chess_game/chess/passer_race_guidance.py`, `chess_game/chess/ai_move_ordering.py`

- [x] **1a** Audit `passer_race_guidance.py` to understand current pawn-race evaluation:
  - Does it compute "distance to promotion" for both sides?
  - Does it account for whose turn it is (one side is one tempo ahead)?
  - Does it distinguish "blocked pawn" from "runaway pawn"?
- [x] **1b** Add a `_explicit_pawn_race_tempo(board)` helper that returns:
  - White's tempo to promotion for the most advanced white pawn.
  - Black's tempo to promotion for the most advanced black pawn.
  - Adjusted for whose turn it is (move to promote is faster than opponent's move to block).
- [x] **1c** In `ai_move_ordering.py`, add a `_pawn_race_move_bonus(board, move, side)` that:
  - Fires only in pawn endgames with both sides having passed pawns.
  - Rewards pawn advances that reduce tempo to promotion.
  - Rewards king moves that block the opponent's pawn or support the side's own pawn.
  - Penalizes king moves that move away from the critical action.
- [x] **1d** Feed the bonus into quiet move scoring for pawn endgames (detect via low material count).
- [x] **1e** Add regression test `test_strategy12_pawn_race_white_advances_runaway_pawn`.
- [x] **1f** Add regression test `test_strategy12_pawn_race_king_blocks_opponent_passer`.
- [x] **1g** Add regression test `test_strategy12_pawn_race_tempo_calculation_matches_expected`.

---

## Task 2 — King centralization urgency in low-material endgames

**Goal:** Aggressively reward king moves toward key squares (promotion square, opponent king, center) in endgames with ≤ 3 pieces per side.

**Files:** `chess_game/chess/simple_endgame_guidance.py`, `chess_game/chess/endgame_evaluation.py`

- [x] **2a** Audit `simple_endgame_guidance.py` for king activation scoring:
  - Is king centralization bonus applied to all low-material positions?
  - Is the bonus magnitude strong enough to compete with other heuristics?
  - Are there edge cases (e.g., K+P vs K) where king should be prioritized above all else?
- [x] **2b** Add a `_king_proximity_to_promotion_square(board, side, pawn_position)` helper:
  - Computes distance from king to the pawn's promotion square.
  - Returns higher bonus for shorter distances.
  - Used in K+P vs K endgames to encourage "king supports pawn."
- [x] **2c** Add a `_king_proximity_bonus_aggressive(board, side, material_context)` in `simple_endgame_guidance.py`:
  - Activates only when ≤ 3 pieces per side (or only pawns + one piece).
  - Rewards king moves that reduce distance to promotion square or opponent king.
  - Magnitude must be large enough to override defensive quiet moves.
- [x] **2d** Integrate the bonus into `simple_endgame_evaluation()` or feed it into `ai_move_ordering.py` for quiet moves.
- [x] **2e** Add regression test `test_strategy12_king_plus_pawn_king_activates_king_toward_promotion`.
- [x] **2f** Add regression test `test_strategy12_king_centralization_overrides_defensive_moves`.

---

## Task 3 — Forced-win detection and acceleration

**Goal:** Identify endgame positions where the winning side has a forced mate sequence and prioritize moves that advance that sequence (checks, pawn pushes, piece captures that guarantee faster mate).

**Files:** `chess_game/chess/ai_search_helpers.py`, `chess_game/chess/conversion_guidance.py`, new file `chess_game/chess/forced_win_guidance.py` (optional)

- [x] **3a** Define "forced win" criteria:
  - Winning side is up ≥ 8 points of material (e.g., up a queen, or up R+B).
  - Opponent has no pieces that can give checks or escape (e.g., bare king).
  - Engine is at depth ≥ 2.
- [x] **3b** Add a `_is_forced_win_endgame(board, side)` helper that returns True if the criteria are met.
- [x] **3c** Add a `_forced_win_move_priority(board, move, side)` that scores moves in forced-win endgames:
  - **Tier 1 (highest):** Checks, captures of defending pieces, pawn advances toward promotion.
  - **Tier 2:** Quiet moves that centralize king, drive opponent king to the edge.
  - **Tier 3:** Other quiet moves.
  - Return a high bonus for Tier 1/2 moves to break quiet-move ties.
- [x] **3d** Integrate into `ai_move_ordering.py` and/or `ai_search_helpers.py` root tie-breaks.
  - If in forced-win position and multiple root candidates have equal eval, prefer Tier 1/2 moves.
- [x] **3e** Alternatively, feed forced-win move bonus into `_get_quiet_move_score()` in quiet ordering.
- [x] **3f** Add regression test `test_strategy12_q_vs_k_finds_mate_within_N_moves`.
- [x] **3g** Add regression test `test_strategy12_r_vs_k_finds_mate_within_N_moves`.
- [x] **3h** Add regression test `test_strategy12_forced_win_avoids_slow_quiet_moves`.

---

## Task 4 — Integration and tuning

**Goal:** Validate that Tasks 1–3 work together without conflicts and do not break existing tests.

- [x] **4a** Run full test suite: `pytest tests/ -q` — all 651+ tests must pass.
- [x] **4b** Run specific regression tests: `pytest tests/test_ai_strategy12_regressions.py -v` — all assertions pass.
- [x] **4c** Lint check: `ruff check`, `mypy`, `pylint chess_game/ --disable=all --enable=...` (no new warnings).
- [x] **4d** Tune bonus magnitudes if needed:
  - If pawn-race bonus is too strong, early-middlegame pawn pushes may be over-prioritized.
  - If king-centralization bonus is too weak, king may still wander in K+P vs K.
  - If forced-win moves are over-prioritized, quiet improving moves may be missed in near-won positions.
- [x] **4e** Run depth-3 self-play test game: `python -m chess_game.self_play --white-depth 3 --black-depth 3`
  - Target: average game length ≤ 100 moves (down from 130).
  - Target: Q vs K or similar trivial endgame resolved in ≤ 15 moves.
  - Save output to `tmp/strategy12_acceptance_game.txt`.

---

## Task 5 — Acceptance and regression suite expansion

**Goal:** Ensure STRATEGY12 improvements are stable across multiple test games and do not regress STRATEGY11 or prior behaviors.

- [x] **5a** Run multiple depth-3 self-play games (3–5 games) and aggregate statistics:
  - Average move count, game outcomes, endgame phase duration.
  - Save all games to `tmp/strategy12_games_*.txt`.
- [x] **5b** Run depth-2 self-play to verify no regression in shallower search.
- [x] **5c** Verify STRATEGY11 regression tests still pass: `pytest tests/test_ai_strategy11_regressions.py -v`.
- [x] **5d** Verify STRATEGY10, STRATEGY9, etc. regression tests still pass.
- [x] **5e** Create `tmp/strategy12_acceptance_summary.txt` with:
  - Game statistics (avg length, outcomes, endgame phase durations).
  - Comparison to STRATEGY11 baseline.
  - Key observations (improved king centralization? faster mate? cleaner conversions?).

---

## Task 6 — Final validation

**Goal:** Full lint, test, and commit pipeline.

- [x] **6a** Run full lint suite:
  - `python -m ruff check chess_game tests` — no warnings.
  - `python -m mypy chess_game/` — no type errors.
  - `python -m pylint chess_game/` — target 10.00/10 score, no pragmas.
- [x] **6b** Run full test suite: `pytest tests/ -q` — all tests pass, coverage stable.
- [x] **6c** Stage all modified and new files: `git add chess_game/ tests/ docs/`.
- [x] **6d** Commit with message: `STRATEGY12: endgame conversion acceleration (pawn race tempo, king urgency, forced-win moves)`.
- [x] **6e** Push to `origin/master`: `git push origin master`.
- [x] **6f** Update `docs/STRATEGY12_TODO.md` to mark all tasks complete.

---

## Key Decisions

1. **Pawn race tempo is explicit** — compute "distance to promotion + whose turn" rather than heuristic scoring.
2. **King urgency is aggressive** — in K+P vs K, king activation should dominate quiet-move scoring.
3. **Forced-win moves are tier-ed** — checks and pawn pushes > king moves > quiet moves.
4. **No pylint pragmas** — structural refactors only; keep code clean.

## Testing Strategy

1. **Regression fixtures** in `test_ai_strategy12_regressions.py` (new file).
2. **Self-play acceptance tests** — verify game lengths and endgame resolution speed.
3. **Prior regression stability** — STRATEGY11/10/9/etc. tests must not degrade.
4. **Lint and type check** — pylint 10.00/10, mypy clean, ruff clean.

## Success Criteria

- [x] Pawn-race moves are prioritized; king blocks opponent's passed pawn intelligently.
- [x] King actively centralizes in K+P vs K and low-material endgames.
- [x] Q vs K, R vs K, and other trivial endgames resolve in ≤ 15 moves at depth 3.
- [ ] Average self-play game length ≤ 100 moves (down from 130).
- [x] All tests pass; pylint 10.00/10; no regressions.
- [ ] Commit and push to master.
