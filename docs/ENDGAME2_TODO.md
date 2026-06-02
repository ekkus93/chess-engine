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

## Task 0: Baseline the Stalemate Failure ✅

### 0.1 Capture the current issue set

- [x] Identify the exact move sequence that converted a winning endgame into stalemate.
- [x] Record the current depth-3 transcript or reuse the latest one if it still shows the issue.
- [x] Mark the exact move where Black had already won but began to overconstrain White.
- [x] Mark the exact move where the final stalemate became unavoidable.

### 0.2 Extract failure categories

- [x] Define a "stalemate risk while winning" signal.
- [x] Define a "boxing in without check" signal.
- [x] Define a "best win turned into draw" signal.
- [x] Define a "simplification without escape-square coverage" signal.
- [x] Define a "pawn race won but conversion incomplete" signal.

### 0.3 Define success criteria

- [x] Black keeps winning endgames winning instead of stalemating the opponent.
- [x] Black prefers lines that preserve check, promotion pressure, or spare mobility for the defender.
- [x] White gets more practical chances to defend, but not by relying on stalemate luck.
- [x] New behavior is visible in at least one fresh full self-play transcript.

### Phase note

- [x] Summarize baseline transcript paths and the exact endgame positions under `tmp/`.

---

## Task 1: Add Regressions for the Stalemate Failure Modes ✅

### 1.1 Add a new regression module

- [x] Create `tests/test_ai_endgame2_regressions.py`.
- [x] Add transcript-replay helpers or board-fixture helpers for the new positions.
- [x] Mark long-running tests with `pytest.mark.slow` where appropriate.

### 1.2 Add winning-side stalemate regressions

- [x] Add a position where Black should keep checking instead of boxing White in.
- [x] Add a position where a winning rook endgame should preserve at least one legal reply for the defender.
- [x] Add a position where a promotion race should be converted with a checking net rather than a stalemate net.

### 1.3 Add simplification regressions

- [x] Add a position where Black should simplify only if the resulting king-and-pawn ending is still a clean win.
- [x] Add a position where Black should avoid trading into a dead draw or stalemate trap.
- [x] Add a position where the best simplification still needs a tempo reserve.

### 1.4 Add defensive endgame regressions

- [x] Add a position where White should seek active defense instead of passive box-in resistance.
- [x] Add a position where White should prefer king mobility over hiding behind a stalemate pattern.
- [x] Add a position where White should use checks or blockade to keep the game alive.

### 1.5 Acceptance criteria

- [x] New tests fail against old behavior or are validated against known baseline choices.
- [x] Tests remain stable across reruns and do not rely on fragile move ordering.

### Phase note

- [x] Document exact regression IDs and what each protects.

---

## Task 2: Add Anti-Stalemate Conversion Guidance ✅

### 2.1 Audit the current conversion logic

- [x] Review the winning-side endgame evaluation and root tie-break logic.
- [x] Identify where Black prefers to reduce legal moves too aggressively.
- [x] Save audit notes in `tmp/endgame2_task2_audit.txt`.

### 2.2 Make conversion stalemate-aware

- [x] Reward lines that keep the defender in check when a check-winning route exists.
- [x] Reward conversions that preserve at least one defender move until the win is secure.
- [x] Penalize positions where the defender is boxed in but not actually losing.
- [x] Penalize overconstraining king-and-pawn endings that risk stalemate.

### 2.3 Acceptance criteria

- [x] Black no longer prefers stalemate-prone wins over cleaner winning lines.
- [x] The regression boards show safer conversion choices.

### Phase note

- [x] Record the specific stalemate-risk patterns that are now recognized.

---

## Task 3: Strengthen Winning-Side King and Queen Safety ✅

### 3.1 Audit king-safety scoring

- [x] Review king-safety terms that still underweight the risk of overconstraining the defender.
- [x] Identify where Black is not being rewarded enough for preserving checking distance.
- [x] Save audit notes in `tmp/endgame2_task3_audit.txt`.

### 3.2 Add stronger winning-side safety logic

- [x] Reward checking distance that keeps the enemy king under pressure.
- [x] Reward safe king placement that still allows a clean win.
- [x] Reward queen and rook placement that avoid blocking the opponent's last legal squares too early.
- [x] Penalize king-side net construction that can collapse into stalemate.

### 3.3 Acceptance criteria

- [x] Black prefers winning lines with spare pressure over bare box-ins.
- [x] The regression boards show fewer stalemate-prone king nets.

### Phase note

- [x] Summarize the exact conversion-safety patterns that are now recognized.

---

## Task 4: Improve Defender Practical Resistance in Losing Endgames ✅

### 4.1 Audit defensive logic

- [x] Review the current losing-side hold scoring and practical-defense guidance.
- [x] Identify where White can still find active defense instead of being mated or stalemated.
- [x] Save audit notes in `tmp/endgame2_task4_audit.txt`.

### 4.2 Strengthen defensive signals

- [x] Reward checks that force the winning side to keep the king active.
- [x] Reward king mobility when a stalemate net is available.
- [x] Reward blockade and temporary counterplay over passive waiting.
- [x] Penalize moves that voluntarily walk into a box with no practical payoff.

### 4.3 Acceptance criteria

- [x] White prefers active containment over passive drift.
- [x] The regression boards show better practical defense choices.

### Phase note

- [x] Document the exact defensive patterns that now evaluate correctly.

---

## Task 5: Add a Practical Endgame Conversion Evaluator ✅

### 5.1 Define the practical conversion state

- [x] Add a helper that recognizes winning-side clean conversion plans.
- [x] Add a helper that recognizes stalemate-risk winning positions.
- [x] Add a helper that recognizes defensive escape-resource positions.
- [x] Ensure all helpers are limited to true endgame geometries.

### 5.2 Score the practical endgame outcome

- [x] Reward moves that preserve pressure without removing all defender mobility.
- [x] Reward moves that convert by check, promotion, or safe simplification.
- [x] Penalize cosmetic activity that causes the defender to run out of legal moves.
- [x] Penalize moving the same piece repeatedly without increasing winning margin.

### 5.3 Integrate with evaluation / ordering / root

- [x] Add the endgame signal to evaluation breakdown.
- [x] Add a quiet-order bonus for practical endgame moves.
- [x] Add a root tie-break bonus for plan-preserving moves.
- [x] Add a selective extension trigger only when the endgame is tactically unstable.

### 5.4 Acceptance criteria

- [x] The engine can distinguish real conversion plans from stalemate traps.
- [x] The new endgame evaluator changes only the intended positions.

### Phase note

- [x] Record the plan thresholds and examples in `tmp/`.

---

## Task 6: Validate With Fresh Self-Play ✅

### 6.1 Run fresh depth-3 self-play

- [x] Run an uncapped depth-3 self-play game and save the transcript under `tmp/`.
- [x] Compare the endgame against the current baseline.
- [x] Record the first divergence from the old box-in pattern.

### 6.2 Compare practical outcomes

- [x] Check whether Black still converts winning endings cleanly.
- [x] Check whether stalemate endings disappear from winning positions.
- [x] Check whether White's defensive resources become more realistic.
- [x] Check whether the game result or length improves in a meaningful way.

### 6.3 Acceptance criteria

- [x] The new transcript shows fewer stalemate-prone box-ins.
- [x] Winning positions remain wins.
- [x] The endgame is visibly more practical than the baseline.

### Phase note

- [x] Write `tmp/endgame2_validation_summary.txt` with findings.

---

## Task 7: Verify, Document, Commit ✅

### 7.1 Full verification gate

- [x] Run:
  - `python -m ruff check chess_game tests`
  - `python -m mypy chess_game/`
  - `python -m pylint chess_game/`
  - `python -m pytest tests/ -q`

### 7.2 TODO and memory updates

- [x] Update this TODO file task/subtask statuses after each phase.
- [x] Record major implementation milestones in `memory.md`.

### 7.3 Commit and push

- [x] Commit with a message describing the endgame improvements.
- [x] Push to `origin/master`.
