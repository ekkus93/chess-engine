# MIDDLEGAME_FIX1 TODO

## Goal

Improve Black’s middlegame play by strengthening:

- development and piece coordination
- king safety before the endgame
- transition from opening to middlegame
- active counterplay instead of passive shuffling
- tactical defense when Black is slightly worse
- transcript-backed regressions for the new failure modes

This pass should build on the existing opening/endgame work and keep move legality unchanged.

---

## Scope Rules

- Keep board rules and move legality unchanged unless a direct bug is exposed.
- Preserve public `Board` and AI entrypoint APIs where possible.
- Prefer structural changes: evaluation, ordering, root tie-breaks, selective extensions, tests.
- Do not add randomness or hard-coded move bans.
- Do not weaken tactical correctness to improve positional aesthetics.
- Every behavior-changing phase ends with:

  ```bash
  python -m ruff check chess_game tests
  python -m mypy chess_game/
  python -m pylint chess_game/
  python -m pytest tests/ -q
  ```

- For behavior-changing phases, also save a fresh depth-3 self-play transcript under `tmp/`.

---

## Task 0: Baseline the Remaining Middlegame Weaknesses

### 0.1 Capture the current issue set

- [ ] Identify the remaining Black middlegame failures in current self-play.
- [ ] Record a fresh depth-3 transcript or reuse the latest one if it still shows the issue.
- [ ] Mark concrete middlegame positions where Black chooses passive development or king drift.

### 0.2 Extract failure categories

- [ ] Define a “too-passive development” signal.
- [ ] Define a “king safety neglected in the middlegame” signal.
- [ ] Define a “piece coordination missed” signal.
- [ ] Define a “counterplay overlooked while worse” signal.
- [ ] Define a “bad transition into the endgame” signal.

### 0.3 Define success criteria

- [ ] Black develops pieces more actively in the opening-to-middlegame transition.
- [ ] Black keeps the king safer when heavy pieces remain on the board.
- [ ] Black seeks practical counterplay instead of shuffling.
- [ ] New behavior is visible in at least one fresh full self-play transcript.

### Phase note

- [ ] Summarize baseline transcript paths and the exact middlegame positions under `tmp/`.

---

## Task 1: Add Regressions for the Middlegame Failures

### 1.1 Add a new regression module

- [ ] Create `tests/test_ai_middlegame_fix1_regressions.py`.
- [ ] Add transcript-replay helpers or board-fixture helpers for the new positions.
- [ ] Mark long-running tests with `pytest.mark.slow` where appropriate.

### 1.2 Add development regressions

- [ ] Add a position where Black should finish development instead of drifting a queen or rook.
- [ ] Add a position where a minor piece should improve before a pawn poke.
- [ ] Add a position where castling or king shelter should be preferred over side activity.

### 1.3 Add king-safety regressions

- [ ] Add a position where Black should move the king to safety before starting a counterattack.
- [ ] Add a position where king-side looseness should be penalized in the middlegame.
- [ ] Add a position where an active defensive piece beats an empty tempo move.

### 1.4 Add counterplay regressions

- [ ] Add a position where Black should challenge the center instead of waiting.
- [ ] Add a position where creating a threat matters more than improving a cosmetic square.
- [ ] Add a position where trading into a favorable middlegame structure is correct.

### 1.5 Acceptance criteria

- [ ] New tests fail against old behavior or are validated against known baseline choices.
- [ ] Tests remain stable across reruns and do not rely on fragile move ordering.

### Phase note

- [ ] Document exact regression IDs and what each protects.

---

## Task 2: Improve Middlegame Development Signals

### 2.1 Audit the current development logic

- [ ] Review the current opening-to-middlegame development heuristics.
- [ ] Identify where Black still prefers passive piece shuffles.
- [ ] Save audit notes in `tmp/middlegame_fix1_task2_audit.txt`.

### 2.2 Make development more practical

- [ ] Reward completing development when minor pieces remain undeveloped.
- [ ] Reward piece coordination that connects rooks or supports central control.
- [ ] Penalize repeated piece moves that do not improve the position.
- [ ] Keep the logic narrow so it does not distort tactical positions.

### 2.3 Acceptance criteria

- [ ] Black completes development earlier in the regression boards.
- [ ] The signal stays off in positions where the pieces are already coordinated.

### Phase note

- [ ] Record the specific development patterns that are now recognized.

---

## Task 3: Strengthen Middlegame King Safety

### 3.1 Audit king-safety scoring

- [ ] Review king-safety terms that still underweight real danger.
- [ ] Identify where Black is not being rewarded enough for castling or shelter.
- [ ] Save audit notes in `tmp/middlegame_fix1_task3_audit.txt`.

### 3.2 Add stronger safety logic

- [ ] Reward castling or equivalent king-shelter moves when available.
- [ ] Reward closing weak files and reducing open lines near the king.
- [ ] Penalize king-side loosening that opens immediate tactical threats.
- [ ] Reward defensive coordination that covers the king’s escape squares.

### 3.3 Acceptance criteria

- [ ] Black prefers safe king placement over cosmetic centralization.
- [ ] The regression boards show lower king exposure after the new moves.

### Phase note

- [ ] Summarize the exact king-safety patterns that are now recognized.

---

## Task 4: Improve Middlegame Counterplay and Transition Play

### 4.1 Audit transition logic

- [ ] Review the current opening-to-middlegame transition heuristics.
- [ ] Identify where Black misses active counterplay while slightly worse.
- [ ] Save audit notes in `tmp/middlegame_fix1_task4_audit.txt`.

### 4.2 Strengthen counterplay signals

- [ ] Reward central breaks that challenge White’s structure.
- [ ] Reward forcing moves that improve Black’s activity without hanging material.
- [ ] Penalize empty waiting moves when a concrete challenge exists.
- [ ] Reward simplification only when it improves the practical result.

### 4.3 Acceptance criteria

- [ ] Black seeks active counterplay instead of pure defense.
- [ ] The engine chooses practical challenging moves over shuffles.

### Phase note

- [ ] Document the counterplay patterns that now evaluate correctly.

---

## Task 5: Add a Middlegame Practical-Plan Evaluator

### 5.1 Define the practical plan state

- [ ] Add a helper that recognizes active middlegame plans.
- [ ] Add a helper that recognizes defensive middlegame holds.
- [ ] Ensure both helpers are limited to true middlegame geometries.

### 5.2 Score the practical middlegame outcome

- [ ] Reward moves that improve development and king safety together.
- [ ] Reward moves that create real counterplay when worse.
- [ ] Penalize cosmetic activity that does not change the position.
- [ ] Penalize moving the same piece repeatedly without a plan.

### 5.3 Integrate with evaluation / ordering / root

- [ ] Add the middlegame signal to evaluation breakdown.
- [ ] Add a quiet-order bonus for practical middlegame moves.
- [ ] Add a root tie-break bonus for plan-preserving moves.
- [ ] Add a selective extension trigger only when the middlegame is tactically unstable.

### 5.4 Acceptance criteria

- [ ] The engine can distinguish real middlegame plans from fake activity.
- [ ] The new middlegame evaluator changes only the intended positions.

### Phase note

- [ ] Record the plan thresholds and examples in `tmp/`.

---

## Task 6: Validate With Fresh Self-Play

### 6.1 Run fresh depth-3 self-play

- [ ] Run an uncapped depth-3 self-play game and save the transcript under `tmp/`.
- [ ] Compare the middlegame against the current baseline.
- [ ] Record the first divergence from the old passive pattern.

### 6.2 Compare practical outcomes

- [ ] Check whether Black develops more actively in the middlegame.
- [ ] Check whether Black’s king stays safer before the endgame.
- [ ] Check whether the game result or length improves in a meaningful way.

### 6.3 Acceptance criteria

- [ ] The new transcript shows fewer passive shuffles.
- [ ] Black creates more practical counterplay in the middlegame.
- [ ] The defense is visibly more purposeful than the baseline.

### Phase note

- [ ] Write `tmp/middlegame_fix1_validation_summary.txt` with findings.

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

- [ ] Commit with a message describing the middlegame improvements.
- [ ] Push to `origin/master`.

### Final acceptance criteria

- [ ] New regressions pass and protect against the remaining passive middlegame drift.
- [ ] Full lint/type/test gate remains green.
- [ ] Practical depth-3 transcript quality is measurably improved.

