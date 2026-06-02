# ENDGAME_FIX2 TODO

## Goal

Improve Black’s endgame defense further by strengthening:

- critical race detection for “must-hold” endings
- king-escape / blockade geometry in losing endings
- rook-and-pawn endgame practicality
- active counterplay when the defender is behind
- repetition handling based on the actual result of the ending
- transcript-backed regressions for the new failure modes

This pass must build on `docs/ENDGAME_FIX1_TODO.md` and keep legal move generation unchanged.

---

## Scope Rules

- Keep board rules and move legality unchanged unless a direct bug is exposed.
- Preserve public `Board` and AI entrypoint APIs where possible.
- Prefer structural changes: evaluation, ordering, root tie-breaks, selective extensions, tests.
- Do not add randomness or hard-coded move bans.
- Do not weaken tactical correctness to improve positional aesthetics.
- Every phase ends with:

  ```bash
  python -m ruff check chess_game tests
  python -m mypy chess_game/
  python -m pylint chess_game/
  python -m pytest tests/ -q
  ```

- For behavior-changing phases, also save a fresh depth-3 self-play transcript under `tmp/`.

---

## Task 0: Baseline the Remaining Endgame Failures

### 0.1 Capture the current issue set

- [x] Identify the remaining Black endgame failures after ENDGAME_FIX1.
- [x] Record a fresh depth-3 transcript or reuse the latest one if it still shows the issue.
- [x] Mark concrete late-game positions where Black still chooses a suboptimal defense.

### 0.2 Extract failure categories

- [x] Define a “too-late emergency trigger” signal.
- [x] Define a “blockade missed even though the line is critical” signal.
- [x] Define a “rook-endgame drift” signal.
- [x] Define a “best-hold missed in a pawn race” signal.
- [x] Define a “repetition chosen when a practical hold exists” signal.

### 0.3 Define success criteria

- [x] Black chooses more active containment in critical endings.
- [x] Black defends more accurately in rook-and-pawn endings.
- [x] Repetition is chosen only when it preserves the best practical result.
- [x] New behavior is visible in at least one fresh full self-play transcript.

### Phase note

- [x] Summarize baseline transcript paths and the exact late-game positions under `tmp/`.

Task 1 is now in progress.

---

## Task 1: Add Regressions for the Remaining Endgame Failures

### 1.1 Add a new regression module

- [x] Create `tests/test_ai_endgame_fix2_regressions.py`.
- [x] Add transcript-replay helpers or board-fixture helpers for the new positions.
- [x] Mark long-running tests with `pytest.mark.slow` where appropriate.

### 1.2 Add stricter emergency-trigger regressions

- [x] Add a position where the current emergency-defense logic triggers too late.
- [x] Add a position where a defender should activate earlier because the opponent’s passer is one tempo from promotion.
- [x] Add a position where a passive king move loses the only practical hold.

### 1.3 Add rook-and-pawn defense regressions

- [x] Add a position where the defender must get behind the passer.
- [x] Add a position where checking distance matters more than side-pawn moves.
- [x] Add a position where active rook placement beats lateral rook drift.
- [x] Add a position where the king must support the rook defense instead of waiting.

### 1.4 Add repetition / hold regressions

- [x] Add a position where repetition is the correct practical defense for the worse side.
- [ ] Add a position where the better side should avoid repetition because a stronger conversion exists.
- [ ] Add a position where simplification is correct only if it preserves the hold.

### 1.5 Acceptance criteria

- [x] New tests fail against old behavior or are validated against known baseline choices.
- [x] Tests remain stable across reruns and do not rely on fragile move ordering.

### Phase note

- [x] Document exact regression IDs and what each protects.

---

## Task 2: Tighten the Emergency Trigger

### 2.1 Audit the current trigger logic

- [x] Review the current emergency-defense gating in `endgame_emergency_defense.py`.
- [x] Identify positions where the trigger is too broad or too permissive.
- [x] Save audit notes in `tmp/endgame_fix2_task2_audit.txt`.

### 2.2 Make the trigger more exact

- [x] Require truly race-critical passer geometry before the emergency signal activates.
- [x] Require a clear containment or blockade target, not just low material.
- [x] Require the defender to have a real defensive resource to evaluate.
- [x] Keep the trigger off in routine conversion positions.

### 2.3 Improve trigger-specific scoring

- [x] Increase the penalty for king drift when the opponent’s passer is one tempo from promotion.
- [x] Reward direct blockade squares more strongly when they are the only hold.
- [x] Reward king steps that immediately shorten the king-to-blockade path.
- [x] Keep the score narrow so it does not distort non-critical endgames.

### 2.4 Acceptance criteria

- [x] The emergency signal activates only in positions where it changes the move choice for the better.
- [x] Existing winning-conversion tests remain stable.

### Phase note

- [x] Record final trigger conditions and examples.

---

## Task 3: Strengthen King-Escape and Blockade Geometry

### 3.1 Audit king-escape scoring

- [x] Review king-distance and blockade geometry terms in the defensive endgame code.
- [x] Identify where the defender is not being rewarded enough for getting to critical squares.
- [x] Save audit notes in `tmp/endgame_fix2_task3_audit.txt`.

### 3.2 Add stronger blockade logic

- [x] Reward the king for reaching the exact blockade square when that square is available.
- [x] Reward king proximity to the promotion square when that matters more than “activity” in the abstract.
- [x] Reward rook/bishop/queen pieces that directly control the blockade or promotion square.
- [x] Penalize king moves that increase distance to the only useful blockade square.

### 3.3 Add escape-path awareness

- [x] Recognize when the king must escape to a specific file/rank corridor.
- [x] Reward moves that preserve escape squares for the defender’s king.
- [x] Penalize moves that close off the defender’s own escape route without compensation.

### 3.4 Acceptance criteria

- [x] The defender prefers exact blockade/escape geometry over cosmetic activity.
- [x] The regression boards show a measurable increase in practical containment moves.

### Phase note

- [x] Summarize the exact king/blockade patterns that are now recognized.

---

## Task 4: Improve Rook-and-Pawn Endgame Practicality

### 4.1 Audit rook-endgame logic

- [x] Review current rook-endgame guidance and rook-placement heuristics.
- [x] Identify where sideways rook drift is still preferred over practical defense or counterplay.
- [x] Save audit notes in `tmp/endgame_fix2_task4_audit.txt`.

### 4.2 Strengthen rook placement signals

- [x] Reward rooks behind the enemy passer when that is the correct hold.
- [x] Reward active checks only when they improve the practical result.
- [x] Penalize rook shuffles that do not improve blockade, file control, or checking distance.
- [x] Reward cutting off the enemy king when it changes the race.

### 4.3 Strengthen king support in rook endings

- [x] Reward king steps that support the rook in blockade/cutoff roles.
- [x] Penalize king waiting moves when the rook needs king support to hold.
- [x] Reward king-plus-rook coordination that forces the enemy king away from the passer.

### 4.4 Acceptance criteria

- [x] Rook endings prefer active containment over lateral drift.
- [x] The engine picks the practical rook resource instead of cosmetic rook activity.

### Phase note

- [x] Document the rook-and-pawn patterns that now evaluate correctly.

---

## Task 5: Add a Must-Converge / Must-Hold Race Evaluator

### 5.1 Define the race state

- [x] Add a helper that recognizes “must-converge” winning races.
- [x] Add a helper that recognizes “must-hold” defensive races.
- [x] Ensure both helpers are limited to true endgame geometries.

### 5.2 Score the practical race outcome

- [x] Reward moves that preserve a win when the side is winning the race.
- [x] Reward moves that preserve a draw when the side is defending the race.
- [x] Penalize moves that lose the critical tempo in either direction.
- [x] Penalize cosmetic checks that do not change the race result.

### 5.3 Integrate with evaluation / ordering / root

- [x] Add the race signal to evaluation breakdown.
- [x] Add a quiet-order bonus for race-critical moves.
- [x] Add a root tie-break bonus for race-preserving moves.
- [x] Add a selective extension trigger only when the race is extremely close.

### 5.4 Acceptance criteria

- [x] The engine can distinguish real race-preserving moves from fake activity.
- [x] The new race evaluator changes only the intended endgame positions.

### Phase note

- [x] Record the race thresholds and examples in `tmp/`.

---

## Task 6: Validate With Fresh Self-Play

### 6.1 Run fresh depth-3 self-play

- [ ] Run an uncapped depth-3 self-play game and save the transcript under `tmp/`.
- [ ] Compare the late game against the current baseline.
- [ ] Record the first divergence from the old passive pattern.

### 6.2 Compare practical outcomes

- [ ] Check whether Black defends more actively in the late game.
- [ ] Check whether White still converts cleanly.
- [ ] Check whether the game result or length improves in a meaningful way.

### 6.3 Acceptance criteria

- [ ] The new transcript shows fewer passive king shuffles.
- [ ] Rook and pawn endings look more purposeful.
- [ ] The defense is visibly more practical than the baseline.

### Phase note

- [ ] Write `tmp/endgame_fix2_validation_summary.txt` with findings.

---

## Task 7: Verify, Document, Commit

### 7.1 Full verification gate

- [ ] Run:
  - `python -m ruff check chess_game tests`
  - `python -m mypy chess_game/`
  - `python -m pylint chess_game/`
  - `python -m pytest tests/ -q`

### 7.2 TODO and memory updates

- [ ] Update this TODO file task/subtask statuses after each phase.
- [ ] Record major implementation milestones in `memory.md`.

### 7.3 Commit and push

- [ ] Commit with a message describing the endgame-defense improvements.
- [ ] Push to `origin/master`.

### Final acceptance criteria

- [ ] New regressions pass and protect against the remaining passive endgame drift.
- [ ] Full lint/type/test gate remains green.
- [ ] Practical depth-3 transcript quality is measurably improved.
