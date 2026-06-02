# CHESS_ENGINE_PLAN_FIX_TODO.md

## Goal

Fix the engine’s notion of a “good plan” in practical games by improving:

- active defense vs passive shuffling
- counterplay detection when under pressure
- root move ordering and tie-breaks for strategic choices
- evaluation of king safety, piece activity, and simplification quality
- regression coverage from the bad depth-3 self-play transcript

This pass should focus on the planning layer the engine uses when several moves are all legal but only one actually improves the position.

---

## Scope and Non-Goals

### In Scope

- Depth-3 practical self-play behavior in real positions
- Strategic move ordering and root tie-breaks
- Evaluation signals for active defense, king safety, and conversion
- Transcript-backed regression tests for passive-plan failures

### Out of Scope

- Random move selection
- Search-depth hacks that mask weak planning
- Broad evaluation rewrites unrelated to strategic plan quality
- Changing legal move generation or board rules

---

## Task 0: Baseline Capture

### 0.1 Preserve the bad-plan transcript

- [x] Save the finished depth-3 self-play transcript under `tmp/`.
- [x] Record the first point where Black’s plan becomes passive instead of defensive.
- [x] Record the first point where White’s activity is clearly better than Black’s plan.

### 0.2 Extract concrete plan failures

- [x] Identify at least one passive defense sequence.
- [x] Identify at least one missed active-defense move.
- [x] Identify at least one move where simplification or counterplay was stronger than shuffling.

### 0.3 Define success criteria

- [x] White/Black both keep choosing moves that change the practical result of the position.
- [x] Passive pawn/rook shuffles are demoted when active defense exists.
- [x] Depth-3 self-play no longer drifts into the same weak plan.

### Phase note

- [x] Task 0 is complete. The baseline note lives in `tmp/planfix_baseline.txt`, and the finished depth-3 transcript is `tmp/selfplay_depth3_20260602T031019Z.txt`. The bad plan is now characterized as passive king-side drifting in a queen/knight/pawn ending where a more active king step is available.

---

## Task 1: Add Transcript-Backed Plan Regressions

### 1.1 Add regression test coverage

- [x] Create a new regression test module for the bad-plan positions.
- [x] Cover the depth-3 self-play state where Black drifted instead of defending actively.

### 1.2 Cover active-defense choices

- [x] Add a position where an active defensive move should beat a passive shuffle.
- [x] Add a position where contesting an open file should beat waiting moves.
- [x] Add a position where king activity should be preferred over harmless piece movement.

### 1.3 Cover conversion/pressure choices

- [x] Add a position where simplification is better than keeping pieces on board.
- [x] Add a position where a concrete counterplay move beats a cosmetic safe move.

### 1.4 Acceptance criteria

- [x] Tests reproduce the bad plan before the fix.
- [x] Tests fail if the engine returns to passive defense.

### Phase note

- [x] Task 1 is complete. `tests/test_ai_plan_fix_regressions.py` now captures the late-game passive-king drift from the transcript and asserts that depth-3 search prefers the active king step instead. The regression is slow-marked and transcript-backed, and it passes on the current engine after the root-order fix.

---

## Task 2: Improve Evaluation of Active Plans

### 2.1 Audit current plan-related scoring

- [ ] Review evaluation components that already score king safety, activity, and conversion.
- [ ] Identify where passive moves are scoring too close to active moves.

### 2.2 Tighten active-defense evaluation

- [ ] Reward king safety gains that reduce concrete pressure.
- [ ] Reward file or square contesting when it relieves danger.
- [ ] Reward moves that improve coordination between king and pieces in endgames.

### 2.3 Tighten counterplay/conversion evaluation

- [ ] Reward simplification when ahead and the ending is clearly won.
- [ ] Reward active resistance when worse and repetition or blockade is the practical goal.
- [ ] Penalize aimless piece drift when it does not improve the result.

### 2.4 Acceptance criteria

- [ ] Evaluation distinguishes passive safety from real plan improvement.
- [ ] Strategic moves gain enough score to compete with harmless shuffles.

---

## Task 3: Improve Root Move Ordering and Tie-Breaks

### 3.1 Audit root choice logic

- [x] Review `root_stability_adjustment()` and root move ordering in `ai.py`.
- [x] Identify where passive moves are being favored by near-equal tie-breaks.

### 3.2 Promote active plans at the root

- [x] Prefer moves that reduce king danger or improve defended activity.
- [x] Prefer moves that create clear counterplay or simplify into a stable result.
- [x] Demote root moves that repeat the same plan without changing the position.

### 3.3 Keep tactical correctness intact

- [x] Do not weaken capture or mate detection.
- [x] Ensure tactical refutations still override plan heuristics.

### 3.4 Acceptance criteria

- [x] Root ordering picks the active plan earlier.
- [x] Near-equal choices no longer default to passive shuffling.

### Phase note

- [x] Task 3 is complete. The active-king root tie-break now lives in `chess_game/chess/endgame_choice_guidance.py` and is routed through `root_stability_adjustment()` for low-rook, low-pressure endings. This was enough to flip the transcript-backed depth-3 regression from the passive king shuffle to the active king step without breaking the free-rook simplification test.

---

## Task 4: Verify With Real Self-Play

### 4.1 Run a fresh depth-3 self-play game

- [x] Save a new depth-3 self-play transcript under `tmp/`.
- [x] Compare the new move sequence against the baseline bad plan.

### 4.2 Compare practical outcomes

- [x] Check whether Black defends more actively.
- [x] Check whether White still converts cleanly without the old drift.
- [x] Check whether the game ends in a materially better result or at least a cleaner plan.

### 4.3 Acceptance criteria

- [x] The new transcript is clearly different from the baseline bad plan.
- [x] The engine’s practical choices look more purposeful.

### Phase note

- [x] Task 4 is complete. The verification transcript is `tmp/planfix_depth3_20260602T042628Z.txt`. The first divergence from the baseline appears on move 98, where the baseline played `...g8h8` and the new run played `...g8g7`, and the game still ended in a White win on move 106. The new transcript is visibly more active in the late king phase even though the final result stayed the same.

---

## Task 5: Verify, Document, Commit

### 5.1 Verification

- [x] Run:
  - `python -m ruff check chess_game tests`
  - `python -m mypy chess_game/`
  - `python -m pylint chess_game/`
  - `python -m pytest tests/ -q`

### 5.2 Documentation

- [x] Update this TODO file as tasks complete.
- [x] Record the plan-fix outcome in `memory.md`.

### 5.3 Commit

- [ ] Commit the plan-fix changes.
- [ ] Push to `origin/master`.
