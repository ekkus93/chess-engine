# STRATEGY13: Conversion Quality and Defensive Practicality TODO

## Overview

The latest full depth-3 self-play game (`tmp/selfplay_w3b3_full_20260530T230721Z.txt`) ended in a Black win by checkmate on move 155.  
That result confirms reasonable tactical competence, but conversion and resistance quality are still inefficient.

This round targets the highest-impact strategy improvements:

1. **Black conversion quality**: finish winning games faster and cleaner.
2. **Black anti-drift discipline**: avoid low-value move cycling while ahead.
3. **White defensive practicality**: maximize drawing chances in worse positions.
4. **White counterplay prioritization**: choose best practical race/blockade plans.
5. **Both-side phase transition discipline**: hand off opening/middlegame plans to endgame goals earlier.

This is a strategy-quality pass, not a full search rewrite.

## Scope and Non-goals

### In-scope
- Move ordering and root tie-break behavior in clearly winning/losing endgames.
- Endgame guidance modules and integration into evaluation/ordering/root choice.
- Regression coverage and self-play acceptance metrics.

### Out-of-scope
- Reintroducing any hidden depth shortcuts.
- Replacing minimax/alpha-beta architecture.
- Engine API redesign.
- Loosening tests to fake improvements.

---

## Task 0 — Baseline capture and instrumentation

**Goal:** Pin exact drift/conversion/resistance failure patterns from the latest full game and make them testable.

- [x] **0a** Analyze `tmp/selfplay_w3b3_full_20260530T230721Z.txt` and annotate:
  - First clearly winning phase for Black.
  - First repeated low-value winning-side move cycle.
  - Key defensive choice points where White had better practical resistance.
  - Promotion/mate conversion phase length.
- [x] **0b** Save findings to `tmp/strategy13_baseline_analysis.txt`.
- [x] **0c** Extract concrete probe positions to `tmp/strategy13_probe_positions.txt`:
  - Winning-side conversion choice.
  - Winning-side anti-drift choice.
  - Losing-side fortress/perpetual-check attempt.
  - Losing-side counterplay race/blockade choice.
- [x] **0d** Create `tests/test_ai_strategy13_regressions.py` scaffold with board helpers and placeholders.

---

## Task 1 — Black: shortest-path conversion when clearly ahead

**Goal:** In clearly winning positions, prefer forced simplification and direct promotion/mate routes.

**Likely files:**
- `chess_game/chess/conversion_guidance.py`
- `chess_game/chess/ai_search_helpers.py`
- `chess_game/chess/ai_move_ordering.py`
- `tests/test_ai_strategy13_regressions.py`

- [x] **1a** Audit current winning-conversion signals:
  - Trade preference when materially ahead.
  - King cutoff and passer support priority.
  - Distinction between forcing and decorative checks.
- [x] **1b** Add/extend helper for **conversion distance pressure**:
  - Reward moves that reduce opponent king mobility.
  - Reward moves that reduce plies-to-promotion/mate route.
  - Reward transitions into trivially won king-and-pawn/queen endgames.
- [x] **1c** Strengthen root tie-break in winning endgames:
  - Prefer lines with clearer conversion over equal-score drift lines.
- [x] **1d** Add regressions:
  - [x] `test_strategy13_black_prefers_forcing_trade_in_won_endgame`
  - [x] `test_strategy13_black_prefers_passer_push_with_king_support`
  - [x] `test_strategy13_black_prefers_king_cutoff_before_side_shuffle`

---

## Task 2 — Black: anti-drift while winning

**Goal:** Penalize repeated non-progress moves when winning unless they are tactically necessary.

**Likely files:**
- `chess_game/chess/review_loop_guidance.py`
- `chess_game/chess/anti_drift_guidance.py`
- `chess_game/chess/ai_move_ordering.py`
- `chess_game/chess/ai_search_helpers.py`
- `tests/test_ai_strategy13_regressions.py`

- [x] **2a** Identify winning-side repetition motifs from baseline (queen/king lateral shuffle, harmless checks).
- [x] **2b** Add a **winning-side drift penalty** gated by:
  - Clear material/evaluation advantage.
  - Low tactical danger.
  - Repeated theater switch or reversible move pattern.
- [x] **2c** Preserve exceptions:
  - Allow repetition if it is best defense against counterplay or is tactical forcing.
- [x] **2d** Add regressions:
  - [x] `test_strategy13_black_rejects_nonforcing_check_loop_when_winning`
  - [x] `test_strategy13_black_rejects_lateral_queen_drift_with_direct_win_available`
  - [x] `test_strategy13_black_keeps_forcing_line_over_repetition`

---

## Task 3 — White: practical defensive strategy in worse positions

**Goal:** Improve drawing resistance via active king, blockade, and checking resources.

**Likely files:**
- `chess_game/chess/defensive_containment_guidance.py`
- `chess_game/chess/endgame_choice_guidance.py`
- `chess_game/chess/ai_move_ordering.py`
- `chess_game/chess/ai_search_helpers.py`
- `tests/test_ai_strategy13_regressions.py`

- [x] **3a** Audit losing-side guidance:
  - Does it overvalue passive waiting?
  - Does it prioritize active king and critical squares?
  - Does it properly score practical check/blockade resources?
- [x] **3b** Add defensive priority tiers for worse side:
  - Tier 1: direct containment of opponent passer/mate threat.
  - Tier 2: active king and checking resources.
  - Tier 3: neutral waiting moves.
- [x] **3c** Add fortress/stalemate-resource bias where materially justified.
- [x] **3d** Add regressions:
  - [x] `test_strategy13_white_prefers_active_king_defense_over_waiting`
  - [x] `test_strategy13_white_prefers_blockade_square_over_side_pawn_push`
  - [x] `test_strategy13_white_prefers_practical_check_resource_when_worse`

---

## Task 4 — White: counterplay and passer-theater prioritization

**Goal:** When losing, choose the most dangerous practical counterplay plan first.

**Likely files:**
- `chess_game/chess/passer_race_guidance.py`
- `chess_game/chess/low_material_race_guidance.py`
- `chess_game/chess/endgame_choice_guidance.py`
- `tests/test_ai_strategy13_regressions.py`

- [x] **4a** Add/adjust worst-side counterplay scoring:
  - Favor highest-urgency enemy passer containment.
  - Favor own best passed-pawn race only when tempo-calculably viable.
  - Penalize non-critical pawn pushes away from main theater.
- [x] **4b** Integrate with root tie-break so near-equal losing options pick the best practical chance.
- [x] **4c** Add regressions:
  - [x] `test_strategy13_white_prioritizes_most_dangerous_enemy_passer`
  - [x] `test_strategy13_white_races_only_when_tempo_favorable`
  - [x] `test_strategy13_white_rejects_irrelevant_side_activity_in_losing_endgame`

---

## Task 5 — Both sides: phase-transition discipline

**Goal:** Transition from opening/middlegame motifs to endgame plan quality earlier and more consistently.

**Likely files:**
- `chess_game/chess/ai_move_ordering.py`
- `chess_game/chess/ai_search_helpers.py`
- `chess_game/chess/endgame_choice_guidance.py`
- `tests/test_ai_strategy13_regressions.py`

- [x] **5a** Define transition trigger(s) (material simplification, king exposure, passer emergence).
- [x] **5b** Add transition-aware bonuses:
  - Early king activation when safe and relevant.
  - Earlier passer-theater commitment.
  - Reduced weight on opening-style quiet shuffles after transition trigger.
- [x] **5c** Add regressions:
  - [x] `test_strategy13_transition_prefers_king_activation_after_simplification`
  - [x] `test_strategy13_transition_prefers_passer_theater_commitment`
  - [x] `test_strategy13_transition_demotes_opening_shuffle_in_endgame_context`

---

## Task 6 — Integration, tuning, and runtime safety

**Goal:** Ensure strategy improvements work together and do not regress runtime discipline.

- [x] **6a** Run targeted regressions:
  - `python -m pytest tests/test_ai_strategy13_regressions.py -q -m "not slow"`
- [x] **6b** Run related existing suites:
  - `python -m pytest tests/test_ai_strategy12_regressions.py -q`
  - `python -m pytest tests/test_ai_strategy11_regressions.py -q`
  - `python -m pytest tests/test_ai_strategy10_regressions.py -q`
  - `python -m pytest tests/test_ai_review_loop.py -q -m "slow"`
- [x] **6c** Verify non-slow suite remains practical:
  - `python -m pytest tests -q -m "not slow" --durations=25`
- [x] **6d** If new expensive tests are added, classify with `pytest.mark.slow` consistently.

---

## Task 7 — Acceptance self-play evaluation

**Goal:** Confirm practical improvement in full games at depth 3.

- [x] **7a** Run at least 3 full self-play games:
  - `python -m chess_game.self_play --white-depth 3 --black-depth 3`
  - Save as `tmp/strategy13_w3b3_game_*.txt`.
- [x] **7b** Record metrics to `tmp/strategy13_acceptance_summary.txt`:
  - Game length.
  - Result.
  - Move count from clearly won phase to finish.
  - Presence/absence of repeated drift motifs.
- [x] **7c** Compare to STRATEGY12 baseline (move 155 game):
  - Target lower median game length.
  - Target shorter winning-side conversion phase.
  - Target higher quality of losing-side practical resistance (without random drift).

---

## Task 8 — Final validation and delivery

- [x] **8a** Lint:
  - `python -m ruff check chess_game tests`
  - `python -m mypy chess_game/`
  - `python -m pylint chess_game/`
- [x] **8b** Full tests:
  - `python -m pytest tests -q`
- [x] **8c** Update this TODO with final status for every task/subtask.
- [x] **8d** Commit and push:
  - Commit message: `STRATEGY13: conversion quality and defensive practicality`
  - Push to `origin/master`.

---

## Success Criteria

- [x] Black converts clearly winning games with fewer non-forcing drift moves.
- [x] White chooses more active, practical defensive resources when worse.
- [x] Both sides transition into coherent endgame plans earlier.
- [ ] Full depth-3 self-play shows reduced conversion length vs STRATEGY12 baseline.
- [x] Lint and full tests are green; runtime discipline for non-slow suite is preserved.
