# STRATEGY10: General White and Black Strategy Improvements TODO

## Overview

STRATEGY9 improved several tactical and endgame heuristics, but the latest self-play still showed two broader strategy gaps:

1. **White still wastes tempi in the opening** — the engine can drift into repeated minor-piece reroutes and delayed central play instead of choosing `d4`/`e4`, development, and castling.
2. **Black still converts too slowly when clearly ahead** — the engine can keep improving slowly instead of forcing pawn progress, king activation, simplification, or decisive conversion.

This round focuses on general strategy quality rather than one transcript-only bug. The goal is to improve default play for both sides while keeping the existing rules and search structure stable.

## Relevant Files

- `chess_game/chess/opening_move_ordering.py` — opening discipline and tempo-loss penalties
- `chess_game/chess/conversion_guidance.py` — winning conversion move ordering and root bonuses
- `chess_game/chess/passer_race_guidance.py` — passed-pawn urgency and race detection
- `chess_game/chess/endgame_evaluation.py` — endgame progress, king activity, and practical conversion signals
- `chess_game/chess/ai_search_helpers.py` — root tie-breaks and repetition/practicality guidance
- `chess_game/chess/evaluation.py` — evaluation aggregation
- `tests/test_ai_strategy10_regressions.py` — new regression coverage for this round

---

## Task 0 — Baseline capture and test scaffolding

**Goal:** Record the current white-opening and black-conversion weaknesses in concrete regression fixtures before changing strategy.

- [x] **0a** Identify a representative opening seed where White repeats a minor piece before central play or castling.
- [x] **0b** Identify a representative winning-endgame seed where Black has a clear material lead but still prefers shuffling or slow improvement over direct conversion.
- [x] **0c** Record the key board layouts from the latest depth-3 self-play transcript in a temporary notes file under `tmp/`.
- [x] **0d** Create `tests/test_ai_strategy10_regressions.py` with board helpers for:
  - White opening discipline probes
  - Black conversion / passer-progression probes
  - King-activity and anti-drift probes
- [x] **0e** Add baseline assertions that capture the current weaker behavior so the later fixes can be validated against them.

---

## Task 1 — Improve White opening discipline

**Goal:** Make White prefer center play, development, and castling over repeated minor-piece reroutes or cosmetic piece moves.

**Files:** `chess_game/chess/opening_move_ordering.py`, `chess_game/chess/ai_search_helpers.py`

- [x] **1a** Review the current opening penalties and identify the gap that lets a developed minor piece be moved again before the rest of the army is out.
- [x] **1b** Add or tune a quiet opening penalty for repeated minor-piece moves while development is still incomplete.
  - The penalty should apply only when the king is still unsettled and other minor pieces remain undeveloped.
  - It should not interfere with first development moves, captures, or castling.
- [x] **1c** Add a root-level opening bonus for central pawn moves (`d4` / `e4`) when they improve the opening plan rather than just shuffling pieces.
- [x] **1d** Ensure castling and finishing development remain preferred over side-piece drift once the opening is underway.
- [x] **1e** Add regression test `test_strategy10_white_prefers_central_pawn_over_minor_reroute`.
- [x] **1f** Add regression test `test_strategy10_white_penalises_second_minor_piece_move_before_development_is_complete`.

---

## Task 2 — Improve Black winning conversion urgency

**Goal:** Make Black convert clearly winning positions more directly by pushing the main passer and avoiding slow shuffling.

**Files:** `chess_game/chess/conversion_guidance.py`, `chess_game/chess/ai_search_helpers.py`

- [x] **2a** Review the current winning-conversion ordering bonuses and identify where pawn progress is still underweighted relative to rook/queen shuffling.
- [x] **2b** Add or tune a direct main-passer advance bonus so the winning side clearly prefers pushing the most relevant pawn.
- [x] **2c** Add a winning-root bonus that prefers concrete pawn progress over neutral rook or queen repositioning when the side is already ahead by a clear material margin.
- [x] **2d** Make sure the new conversion bonus does not trigger in quiet equal positions or tactical positions where king safety matters more.
- [x] **2e** Add regression test `test_strategy10_black_prefers_main_passer_push_over_shuffle`.
- [x] **2f** Add regression test `test_strategy10_black_conversion_bonus_requires_clear_material_edge`.

---

## Task 3 — Strengthen anti-drift behavior in winning positions

**Goal:** Reduce long rook/queen shuffle sequences when one side is already winning.

**Files:** `chess_game/chess/ai_search_helpers.py`, `chess_game/chess/endgame_evaluation.py`

- [x] **3a** Review the existing repetition and progress heuristics to see whether they register pawn advancement as true progress strongly enough.
- [x] **3b** Add or tune a practical-progress component that rewards passed-pawn advancement in clearly winning endgames.
- [x] **3c** Add a root-only penalty or bonus structure that biases the search toward decisive progress over looped improvement moves.
- [x] **3d** Make sure the anti-drift logic stays narrow enough to avoid changing ordinary rook-endgame technique or draw defense.
- [x] **3e** Add regression test `test_strategy10_winning_positions_penalise_shuffling`.

---

## Task 4 — Improve king activity in conversion and endgame play

**Goal:** Make the winning side bring the king closer earlier in mixed heavy-piece endgames and practical conversion states.

**Files:** `chess_game/chess/endgame_evaluation.py`, `chess_game/chess/conversion_guidance.py`

- [x] **4a** Audit the current king-activity scoring to confirm where it already helps and where it stays too weak.
- [x] **4b** Add a heavy-endgame king-activity helper that rewards centralization when the winning side has a clear material lead but the position still contains heavier pieces.
- [x] **4c** Feed the new king-activity helper into endgame evaluation so the search sees the benefit before the position becomes a bare king-and-pawns ending.
- [x] **4d** Feed the same signal into conversion guidance so king activation competes with passive rook shuffling in practical winning positions.
- [x] **4e** Add regression test `test_strategy10_winning_side_activates_king_earlier`.

---

## Task 5 — Improve white-to-black transition quality in the opening and early middlegame

**Goal:** Make the engine’s general strategic play more coherent when it transitions out of the opening.

**Files:** `chess_game/chess/opening_move_ordering.py`, `chess_game/chess/ai_search_helpers.py`, `chess_game/chess/evaluation.py`

- [x] **5a** Review whether opening discipline and root tie-breaks still overvalue cosmetic minor-piece moves after development is nearly complete.
- [x] **5b** Add any needed root preference that keeps central pawn breaks and safe development ahead of second/third moves by the same minor piece.
- [x] **5c** Ensure the opening heuristics hand off cleanly to the middlegame so the engine does not carry opening-style move ordering too far.
- [x] **5d** Add regression test `test_strategy10_opening_to_middlegame_transition_prefers_real_plan`.

---

## Task 6 — Validation and acceptance

**Goal:** Prove the new strategy layer is sound and measurable.

- [x] **6a** Run `python -m ruff check chess_game tests` and fix every warning.
- [x] **6b** Run `python -m mypy chess_game/` and fix every type issue.
- [x] **6c** Run `python -m pylint chess_game/` and keep the score at `10.00/10`.
- [x] **6d** Run `python -m pytest tests/ -q` and fix any failing regression.
- [x] **6e** Run a new depth-3 vs depth-3 self-play game and save the transcript under `tmp/`.
- [x] **6f** Check whether White plays a central pawn early and whether Black converts faster than the prior STRATEGY9 run.
- [x] **6g** Write a short review note under `tmp/` summarizing the move count, white opening quality, and black conversion quality.

---

## Task 7 — Commit and push

**Goal:** Check in the completed strategy update once validation passes.

- [x] **7a** Stage all changed files.
- [x] **7b** Commit with a clear message describing the white-opening and black-conversion improvements.
- [x] **7c** Push to `origin/master`.
- [x] **7d** Update all checklist items above to reflect final completion.

---

## Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| White opening choice quality | Mixed | Central pawn + development preferred |
| Black winning conversion speed | Slow | Clearly faster |
| Repeated minor-piece opening moves | Still possible | Strongly discouraged |
| Passed-pawn urgency in winning play | Present but narrow | Stronger and more consistent |
| Pylint score | 10.00/10 | 10.00/10 |
| Tests | Passing | Passing |
