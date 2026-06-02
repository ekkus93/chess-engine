# STRATEGY14: Practical Middlegame Stability TODO

## Overview

The latest depth-3 self-play game (`tmp/middlegame_fix1_depth3_20260602T092000Z.txt`) showed an important pattern:
Black can build a large advantage, but can still overpress, drift into an exposed king, and allow White to convert with a direct attack.
White, meanwhile, can miss earlier defensive resources but still win when the attack becomes concrete.

This pass targets both sides:

1. **Black conversion discipline**: keep winning positions winning without loosening the king.
2. **Black defensive stability**: avoid overextension when the attack is not yet forced.
3. **White practical defense**: improve king safety, blockade, and counterplay when worse.
4. **White conversion discipline**: turn attack chances into clean wins instead of loose tactics.
5. **Both-side middlegame practicality**: prefer active plans that actually improve the position.

This is a strategy-quality pass, not a legality rewrite.

## Scope and Non-goals

### In-scope
- Middlegame evaluation, ordering, root tie-breaks, and selective extensions.
- Regression coverage for Black overpressing and White conversion/defense.
- Transcript-backed validation from fresh depth-3 self-play.

### Out-of-scope
- Rewriting legal move generation.
- Introducing randomness or move bans.
- Weakening tactical correctness for positional style.
- Changing the public Board API unless a direct bug is exposed.

---

## Task 0 — Baseline the Current Middlegame Problem

**Goal:** Pin the current failure modes from the latest full game and make them testable.

### 0.1 Capture the current issue set

- [x] Identify the exact moves where Black’s advantage became unstable.
- [x] Identify the exact moves where White’s winning attack became concrete.
- [x] Record the current depth-3 transcript or reuse the latest one if it still shows the issue.
- [x] Mark the moments where Black should have consolidated instead of continuing to press.

### 0.2 Extract failure categories

- [x] Define a “winning-side overpress” signal.
- [x] Define a “king safety neglected while ahead” signal.
- [x] Define a “practical defense missed while worse” signal.
- [x] Define a “conversion attack became too loose” signal.
- [x] Define a “middlegame plan without payoff” signal.

### 0.3 Define success criteria

- [x] Black preserves large advantages more cleanly.
- [x] Black avoids king exposure when the win is already in hand.
- [x] White finds stronger practical defenses when worse.
- [x] White converts attacks with fewer tactical leaks.
- [x] New behavior is visible in at least one fresh full self-play transcript.

### Phase note

- [x] Summarize baseline transcript paths and the exact middlegame positions under `tmp/`.

---

## Task 1 — Add Regressions for the Middlegame Failure Modes

**Goal:** Capture the new failure classes in focused regression boards.

### 1.1 Add a regression module

- [x] Create `tests/test_ai_strategy14_regressions.py`.
- [x] Add board-fixture helpers for the new positions.
- [x] Mark long-running tests with `pytest.mark.slow` where appropriate.

### 1.2 Add Black conversion regressions

- [x] Add a position where Black should castle or consolidate instead of chasing extra material.
- [x] Add a position where Black should keep the king sheltered before a pawn break.
- [x] Add a position where Black should convert by simplifying, not by drifting the queen.

### 1.3 Add Black stability regressions

- [x] Add a position where Black should avoid loosening king-side pawns.
- [x] Add a position where Black should stop overextending after gaining the edge.
- [x] Add a position where an active defense beats a flashy but unnecessary attack.

### 1.4 Add White defense regressions

- [x] Add a position where White should prioritize king safety over activity.
- [x] Add a position where White should choose a blockade or hold instead of a waiting move.
- [x] Add a position where White should create counterplay instead of passively defending.

### 1.5 Add White conversion regressions

- [x] Add a position where White should finish an attack with a forcing line.
- [x] Add a position where White should avoid overcommitting pieces before the king is safe.
- [x] Add a position where White should prefer a clean tactical win over a cosmetic gain.

### 1.6 Acceptance criteria

- [x] New tests fail against old behavior or are validated against known baseline choices.
- [x] Tests remain stable across reruns and do not rely on fragile move ordering.

### Phase note

- [x] Document exact regression IDs and what each protects.

---

## Task 2 — Strengthen Black Conversion Discipline

**Goal:** Keep winning positions under control instead of drifting into unnecessary risk.

### 2.1 Audit the current conversion logic

- [x] Review the current winning-side evaluation and root tie-break logic.
- [x] Identify where Black still prefers extra pressure over safe simplification.
- [x] Save audit notes in `tmp/strategy14_task2_audit.txt`.

### 2.2 Make conversion more practical

- [x] Reward safe king placement when Black is already winning.
- [x] Reward direct simplification that preserves the advantage.
- [x] Reward promotion routes that do not expose the king.
- [x] Penalize long winning-side detours that create counterplay.

### 2.3 Acceptance criteria

- [x] Black preserves large advantages with fewer unnecessary checks and queen drifts.
- [x] The regression boards show safer conversion choices.

### Phase note

- [x] Record the specific conversion patterns that are now recognized.

---

## Task 3 — Strengthen Black Middlegame King Safety

**Goal:** Avoid turning a winning position into a tactical liability.

### 3.1 Audit king-safety scoring

- [x] Review king-safety terms that still underweight real danger while ahead.
- [x] Identify where Black is not being rewarded enough for castling or shelter.
- [x] Save audit notes in `tmp/strategy14_task3_audit.txt`.

### 3.2 Add stronger safety logic

- [x] Reward castling or equivalent king-shelter moves when available.
- [x] Reward closing weak files and reducing open lines near the king.
- [x] Penalize king-side loosening that opens immediate tactical threats.
- [x] Reward defensive coordination that covers the king’s escape squares.

### 3.3 Acceptance criteria

- [x] Black prefers safe king placement over cosmetic centralization.
- [x] The regression boards show lower king exposure after the new moves.

### Phase note

- [x] Summarize the exact king-safety patterns that are now recognized.

---

## Task 4 — Improve White Practical Defense

**Goal:** Help White survive worse positions with active defense instead of passive waiting.

### 4.1 Audit defensive logic

- [x] Review the current losing-side guidance and practical hold scoring.
- [x] Identify where White misses blockade, king activity, or checking resources.
- [x] Save audit notes in `tmp/strategy14_task4_audit.txt`.

### 4.2 Strengthen defensive signals

- [x] Reward the king reaching a safer defensive square.
- [x] Reward rook or queen activity that directly contests the attacker.
- [x] Reward blockade and containment over cosmetic pawn moves.
- [x] Penalize waiting moves when a concrete hold exists.

### 4.3 Acceptance criteria

- [x] White prefers active containment over passive drift.
- [x] The regression boards show better practical defense choices.

### Phase note

- [x] Document the exact defensive patterns that now evaluate correctly.

---

## Task 5 — Improve White Conversion and Attack Discipline

**Goal:** Convert attacking chances cleanly without letting Black escape.

### 5.1 Audit conversion logic

- [x] Review attack continuation and tactical payoff scoring.
- [x] Identify where White overextends before the attack is fully secure.
- [x] Save audit notes in `tmp/strategy14_task5_audit.txt`.

### 5.2 Strengthen attack discipline

- [x] Reward forcing moves that keep the king boxed in.
- [x] Reward simplification only when it improves the practical result.
- [x] Penalize loose queen/rook shuffles that hand back tempo.
- [x] Penalize attack moves that weaken White’s own king unnecessarily.

### 5.3 Acceptance criteria

- [x] White keeps the attack concrete when winning chances exist.
- [x] The regression boards show fewer loose tactical sequences.

### Phase note

- [x] Record the exact attack patterns that are now recognized.

---

## Task 6 — Add a Middlegame Practical-Plan Evaluator

**Goal:** Distinguish real middlegame plans from fake activity on both sides.

### 6.1 Define the practical plan state

- [x] Add a helper that recognizes winning-side consolidation plans.
- [x] Add a helper that recognizes defensive middlegame holds.
- [x] Add a helper that recognizes concrete attacking continuations.
- [x] Ensure all helpers are limited to true middlegame geometries.

### 6.2 Score the practical middlegame outcome

- [x] Reward moves that improve king safety and position stability together.
- [x] Reward moves that create real counterplay when worse.
- [x] Reward moves that simplify cleanly when ahead.
- [x] Penalize cosmetic activity that does not change the position.
- [x] Penalize moving the same piece repeatedly without a plan.

### 6.3 Integrate with evaluation / ordering / root

- [x] Add the middlegame signal to evaluation breakdown.
- [x] Add a quiet-order bonus for practical middlegame moves.
- [x] Add a root tie-break bonus for plan-preserving moves.
- [x] Add a selective extension trigger only when the middlegame is tactically unstable.

### 6.4 Acceptance criteria

- [x] The engine can distinguish real middlegame plans from fake activity.
- [x] The new middlegame evaluator changes only the intended positions.

### Phase note

- [x] Record the plan thresholds and examples in `tmp/`.

---

## Task 7 — Validate With Fresh Self-Play

**Goal:** Confirm the behavior change in a full game.

### 7.1 Run fresh depth-3 self-play

- [x] Run an uncapped depth-3 self-play game and save the transcript under `tmp/`.
- [x] Compare the middlegame against the current baseline.
- [x] Record the first divergence from the old passive pattern.

### 7.2 Compare practical outcomes

- [x] Check whether Black converts large advantages more safely.
- [x] Check whether Black’s king stays safer before the endgame.
- [x] Check whether White defends more actively when worse.
- [x] Check whether White’s winning attacks stay more concrete.

### 7.3 Acceptance criteria

- [x] The new transcript shows fewer loose winning-side overpresses.
- [x] White shows stronger defensive and conversion discipline.
- [x] The defense is visibly more purposeful than the baseline.

### Phase note

- [x] Write `tmp/strategy14_validation_summary.txt` with findings.

---

## Task 8 — Verify, Document, Commit

### 8.1 Full verification gate

- [ ] Run:
  - `python -m ruff check chess_game tests`
  - `python -m mypy chess_game/`
  - `python -m pylint chess_game/`
  - `python -m pytest tests/ -q`
  - Current status: blocked by pre-existing AI/endgame regression failures in the wider suite.

### 8.2 TODO and memory updates

- [x] Update this TODO file task/subtask statuses after each phase.
- [x] Record major implementation milestones in `memory.md`.

### 8.3 Commit and push

- [ ] Commit with a message describing the strategy improvements.
- [ ] Push to `origin/master`.
