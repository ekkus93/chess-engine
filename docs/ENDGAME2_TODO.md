# ENDGAME2 TODO

## Goal

Fix the endgame conversion flaw that allowed a winning position to collapse into stalemate by strengthening:

- winning-side conversion discipline
- anti-stalemate move selection
- king-and-pawn conversion safety
- practical simplification when ahead
- holding technique when the defender is worse
- transcript-backed regressions for stalemate-risk endings

This pass should build on `docs/ENDGAME_FIX1_TODO.md` and `docs/ENDGAME_FIX2_TODO.md` without changing legal move generation.

---

## Scope Rules

- Keep board rules and move legality unchanged unless a direct bug is exposed.
- Preserve public `Board` and AI entrypoint APIs where possible.
- Prefer structural changes: evaluation, ordering, root tie-breaks, selective extensions, tests.
- Do not add randomness or hard-coded move bans.
- Do not weaken tactical correctness to avoid stalemate in a way that creates worse play elsewhere.
- Every phase ends with:

  ```bash
  python -m ruff check chess_game tests
  python -m mypy chess_game/
  python -m pylint chess_game/
  python -m pytest tests/ -q
  ```

- For behavior-changing phases, also save a fresh depth-3 self-play transcript under `tmp/`.

---

## Task 0: Baseline the Stalemate Failure

### 0.1 Capture the current issue set

- [ ] Identify the exact move sequence that converted a winning endgame into stalemate.
- [ ] Record the current depth-3 transcript or reuse the latest one if it still shows the issue.
- [ ] Mark the exact move where Black had already won but began to overconstrain White.
- [ ] Mark the exact move where the final stalemate became unavoidable.

### 0.2 Extract failure categories

- [ ] Define a “stalemate risk while winning” signal.
- [ ] Define a “boxing in without check” signal.
- [ ] Define a “best win turned into draw” signal.
- [ ] Define a “simplification without escape-square coverage” signal.
- [ ] Define a “pawn race won but conversion incomplete” signal.

### 0.3 Define success criteria

- [ ] Black keeps winning endgames winning instead of stalemating the opponent.
- [ ] Black prefers lines that preserve check, promotion pressure, or spare mobility for the defender.
- [ ] White gets more practical chances to defend, but not by relying on stalemate luck.
- [ ] New behavior is visible in at least one fresh full self-play transcript.

### Phase note

- [ ] Summarize baseline transcript paths and the exact endgame positions under `tmp/`.

---

## Task 1: Add Regressions for the Stalemate Failure Modes

### 1.1 Add a new regression module

- [ ] Create `tests/test_ai_endgame2_regressions.py`.
- [ ] Add transcript-replay helpers or board-fixture helpers for the new positions.
- [ ] Mark long-running tests with `pytest.mark.slow` where appropriate.

### 1.2 Add winning-side stalemate regressions

- [ ] Add a position where Black should keep checking instead of boxing White in.
- [ ] Add a position where a winning rook endgame should preserve at least one legal reply for the defender.
- [ ] Add a position where a promotion race should be converted with a checking net rather than a stalemate net.

### 1.3 Add simplification regressions

- [ ] Add a position where Black should simplify only if the resulting king-and-pawn ending is still a clean win.
- [ ] Add a position where Black should avoid trading into a dead draw or stalemate trap.
- [ ] Add a position where the best simplification still needs a tempo reserve.

### 1.4 Add defensive endgame regressions

- [ ] Add a position where White should seek active defense instead of passive box-in resistance.
- [ ] Add a position where White should prefer king mobility over hiding behind a stalemate pattern.
- [ ] Add a position where White should use checks or blockade to keep the game alive.

### 1.5 Acceptance criteria

- [ ] New tests fail against old behavior or are validated against known baseline choices.
- [ ] Tests remain stable across reruns and do not rely on fragile move ordering.

### Phase note

- [ ] Document exact regression IDs and what each protects.

---

## Task 2: Add Anti-Stalemate Conversion Guidance

### 2.1 Audit the current conversion logic

- [ ] Review the winning-side endgame evaluation and root tie-break logic.
- [ ] Identify where Black prefers to reduce legal moves too aggressively.
- [ ] Save audit notes in `tmp/endgame2_task2_audit.txt`.

### 2.2 Make conversion stalemate-aware

- [ ] Reward lines that keep the defender in check when a check-winning route exists.
- [ ] Reward conversions that preserve at least one defender move until the win is secure.
- [ ] Penalize positions where the defender is boxed in but not actually losing.
- [ ] Penalize overconstraining king-and-pawn endings that risk stalemate.

### 2.3 Acceptance criteria

- [ ] Black no longer prefers stalemate-prone wins over cleaner winning lines.
- [ ] The regression boards show safer conversion choices.

### Phase note

- [ ] Record the specific stalemate-risk patterns that are now recognized.

---

## Task 3: Strengthen Winning-Side King and Queen Safety

### 3.1 Audit king-safety scoring

- [ ] Review king-safety terms that still underweight the risk of overconstraining the defender.
- [ ] Identify where Black is not being rewarded enough for preserving checking distance.
- [ ] Save audit notes in `tmp/endgame2_task3_audit.txt`.

### 3.2 Add stronger winning-side safety logic

- [ ] Reward checking distance that keeps the enemy king under pressure.
- [ ] Reward safe king placement that still allows a clean win.
- [ ] Reward queen and rook placement that avoid blocking the opponent’s last legal squares too early.
- [ ] Penalize king-side net construction that can collapse into stalemate.

### 3.3 Acceptance criteria

- [ ] Black prefers winning lines with spare pressure over bare box-ins.
- [ ] The regression boards show fewer stalemate-prone king nets.

### Phase note

- [ ] Summarize the exact conversion-safety patterns that are now recognized.

---

## Task 4: Improve Defender Practical Resistance in Losing Endgames

### 4.1 Audit defensive logic

- [ ] Review the current losing-side hold scoring and practical-defense guidance.
- [ ] Identify where White can still find active defense instead of being mated or stalemated.
- [ ] Save audit notes in `tmp/endgame2_task4_audit.txt`.

### 4.2 Strengthen defensive signals

- [ ] Reward checks that force the winning side to keep the king active.
- [ ] Reward king mobility when a stalemate net is available.
- [ ] Reward blockade and temporary counterplay over passive waiting.
- [ ] Penalize moves that voluntarily walk into a box with no practical payoff.

### 4.3 Acceptance criteria

- [ ] White prefers active containment over passive drift.
- [ ] The regression boards show better practical defense choices.

### Phase note

- [ ] Document the exact defensive patterns that now evaluate correctly.

---

## Task 5: Add a Practical Endgame Conversion Evaluator

### 5.1 Define the practical conversion state

- [ ] Add a helper that recognizes winning-side clean conversion plans.
- [ ] Add a helper that recognizes stalemate-risk winning positions.
- [ ] Add a helper that recognizes defensive escape-resource positions.
- [ ] Ensure all helpers are limited to true endgame geometries.

### 5.2 Score the practical endgame outcome

- [ ] Reward moves that preserve pressure without removing all defender mobility.
- [ ] Reward moves that convert by check, promotion, or safe simplification.
- [ ] Penalize cosmetic activity that causes the defender to run out of legal moves.
- [ ] Penalize moving the same piece repeatedly without increasing winning margin.

### 5.3 Integrate with evaluation / ordering / root

- [ ] Add the endgame signal to evaluation breakdown.
- [ ] Add a quiet-order bonus for practical endgame moves.
- [ ] Add a root tie-break bonus for plan-preserving moves.
- [ ] Add a selective extension trigger only when the endgame is tactically unstable.

### 5.4 Acceptance criteria

- [ ] The engine can distinguish real conversion plans from stalemate traps.
- [ ] The new endgame evaluator changes only the intended positions.

### Phase note

- [ ] Record the plan thresholds and examples in `tmp/`.

---

## Task 6: Validate With Fresh Self-Play

### 6.1 Run fresh depth-3 self-play

- [ ] Run an uncapped depth-3 self-play game and save the transcript under `tmp/`.
- [ ] Compare the endgame against the current baseline.
- [ ] Record the first divergence from the old box-in pattern.

### 6.2 Compare practical outcomes

- [ ] Check whether Black still converts winning endings cleanly.
- [ ] Check whether stalemate endings disappear from winning positions.
- [ ] Check whether White’s defensive resources become more realistic.
- [ ] Check whether the game result or length improves in a meaningful way.

### 6.3 Acceptance criteria

- [ ] The new transcript shows fewer stalemate-prone box-ins.
- [ ] Winning positions remain wins.
- [ ] The endgame is visibly more practical than the baseline.

### Phase note

- [ ] Write `tmp/endgame2_validation_summary.txt` with findings.

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

- [ ] Commit with a message describing the endgame improvements.
- [ ] Push to `origin/master`.
