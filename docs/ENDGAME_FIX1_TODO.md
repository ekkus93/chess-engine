# ENDGAME_FIX1 TODO

## Goal

Improve Black’s practical endgame defense (and overall endgame quality for both sides) by strengthening:

- king-danger awareness in low-material endings
- passed-pawn emergency defense
- draw-resistance / fortress-style choices when worse
- root tie-break preference for active defense over passive shuffling
- selective search depth on critical defensive moves
- transcript-backed regression protection for known bad patterns

This pass must improve plan quality without changing legal move generation rules.

---

## Scope Rules

- Keep board-rule correctness and move legality unchanged unless a regression exposes a direct bug.
- Preserve public `Board` and AI entrypoint APIs where possible.
- Prefer structural changes (evaluation, ordering, root tie-breaks, selective extensions, tests), not hard-coded move bans.
- Do not add randomness to hide weak planning.
- Do not weaken tactical correctness to improve positional aesthetics.
- Every phase ends with full verification:

  ```bash
  python -m ruff check chess_game tests
  python -m mypy chess_game/
  python -m pylint chess_game/
  python -m pytest tests/ -q
  ```

- For behavior-changing phases, also save a new depth-3 self-play transcript under `tmp/`.

---

## Task 0: Baseline and Success Criteria

### 0.1 Capture baseline artifacts

- [x] Record the current reference transcript(s) for depth-3 self-play in `tmp/`.
- [x] Mark at least 3 concrete endgame moments where Black chose passive king shuffles over active defense.
- [x] Mark at least 2 moments where passed-pawn containment was available but not chosen.

### 0.2 Extract measurable failure signals

- [x] Define a “passive king drift” signal (e.g., repeated king moves that do not improve containment or safety).
- [x] Define a “missed passer containment” signal (e.g., ignoring blockade/checking distance in race-critical states).
- [x] Define a “best-hold missed” signal for worse-side positions (draw chance decreased by passive move).

### 0.3 Define acceptance criteria

- [x] Depth-3 search prefers active containment in identified baseline positions.
- [x] Black avoids repeated king shuffles when actionable defense exists.
- [x] New behavior is visible in at least one fresh full self-play transcript.

### Phase note

- [x] Summarize baseline file paths and exact target positions under `tmp/`.

- [x] Task 0 is complete. Baseline artifact: `tmp/endgame_fix1_baseline.txt`. Primary transcript: `tmp/selfplay_depth3_full_20260602T052903Z.txt`. Target drift/containment window: moves 94-105, with passive drift concentrated at `...g8g7`, `...g7g6`, `...g6h6`, `...h6h5`.

---

## Task 1: Regression Harness for Endgame Defense

### 1.1 Add transcript-backed regression module

- [x] Create `tests/test_ai_endgame_fix1_regressions.py`.
- [x] Add helper(s) to reconstruct targeted endgame positions from transcript snapshots.
- [x] Mark long-running tests with `pytest.mark.slow` where appropriate.

### 1.2 Add passive-drift regressions

- [x] Add a position where Black currently chooses a king shuffle but should choose active defense.
- [x] Add a position where Black should step toward critical containment squares, not away.
- [x] Add a position where repeated king triangulation is inferior to immediate practical defense.

### 1.3 Add passer-emergency regressions

- [x] Add a near-promotion race where containment/blockade must be prioritized.
- [x] Add a position where checking distance must beat harmless waiting.
- [x] Add a position where the only hold is king activation plus blockade geometry.

### 1.4 Add “worse-side best hold” regressions

- [x] Add a position where Black should choose a hold/fleet defense plan over passive move.
- [x] Add a position where repetition-seeking is correct (and active).
- [x] Add a position where avoiding simplification is correct for drawing chances.

### 1.5 Acceptance criteria

- [x] New tests fail against old behavior (or are validated against known baseline choices).
- [x] Tests pass with improved behavior and stay stable across reruns.

### Phase note

- [x] Document exact regression IDs and what each protects.

- [x] Task 1 is complete. `tests/test_ai_endgame_fix1_regressions.py` covers the transcript snapshot, passive drift, passer containment, holdability, and repetition edges, and it now passes cleanly under the full repository gate.

---

## Task 2: King-Danger Evaluation in Low-Material Endgames

### 2.1 Audit current scoring path

- [x] Review evaluation components currently affecting king safety/activity in low-material positions.
- [x] Identify where king safety and containment pressure are underweighted for the defending side.
- [x] Save audit notes in `tmp/endgame_fix1_task2_audit.txt`.

### 2.2 Implement defending-king danger signal

- [x] Add/adjust a score term for king distance to critical containment and blockade squares.
- [x] Penalize moves that increase practical king danger while not improving counterplay.
- [x] Reward safe activation that improves containment geometry.

### 2.3 Add passer-front danger coupling

- [x] Tie king-danger pressure to enemy advanced passers (rank proximity and promotion threats).
- [x] Increase penalty for drift when enemy passers are close to promotion.
- [x] Keep signal narrow to endgame-relevant material profiles to avoid middlegame distortion.

### 2.4 Acceptance criteria

- [x] Evaluation breakdown exposes new defensive danger component(s).
- [x] Target regression positions now separate active defense from passive king drift.

### Phase note

- [x] Document final weighting and gating decisions.

- [x] Task 2 is complete. The new emergency-defense signal is gated to narrow trailing-side low-material positions and is now visible in `defensive_king_danger` and `holdability` evaluation breakdown keys.

---

## Task 3: Passed-Pawn Emergency Defense Mode

### 3.1 Define emergency triggers

- [x] Trigger when opponent has advanced passer(s) near promotion or decisive race threat.
- [x] Trigger when defender’s best result depends on immediate containment.
- [x] Ensure trigger excludes non-critical positions to avoid overfitting.

### 3.2 Implement emergency move preferences

- [x] Boost blockade, interception, and checking-distance-improving moves.
- [x] Boost king opposition/critical-square steps that stop promotion races.
- [x] Demote cosmetic moves that do not change race outcome.

### 3.3 Integrate with ordering + root tie-break

- [x] Feed emergency signal into quiet move ordering.
- [x] Feed emergency signal into root near-equal tie-break decisions.
- [x] Keep tactical forcing moves dominant when materially necessary.

### 3.4 Acceptance criteria

- [x] Emergency mode flips target regressions from passive to active containment.
- [x] No tactical regression in existing search and mate-oriented tests.

### Phase note

- [x] Record trigger conditions and examples where emergency mode activates.

- [x] Task 3 is complete. Emergency mode is narrowly tied to trailing-side critical passers and improves both quiet ordering and root choice without affecting unrelated conversion tests.

---

## Task 4: Worse-Side Holdability / Fortress Bias

### 4.1 Add holdability features

- [x] Score defensive coordination and king-zone integrity in worse endings.
- [x] Reward line choices that preserve practical drawing resources.
- [x] Penalize exchanges/simplifications that collapse holdability without compensation.

### 4.2 Add repetition strategy constraints

- [x] Prefer repetition only when it preserves/improves practical result for the worse side.
- [x] Avoid non-productive repetition for the better side.
- [x] Ensure no infinite loop path is introduced.

### 4.3 Connect to root choice

- [x] Add root tie-break bonus for active hold plans (containment + resource retention).
- [x] Demote passive waiting plans that worsen defensive geometry.

### 4.4 Acceptance criteria

- [x] Worse-side defensive regressions choose best-hold plans more often.
- [x] Better-side anti-drift behavior remains intact.

### Phase note

- [x] Summarize holdability feature behavior and limits.

- [x] Task 4 is complete. Holdability now lives in the new emergency-defense module and is gated to narrow trailing-side rescue positions only.

---

## Task 5: Selective Extension for Critical Defense

### 5.1 Add extension triggers

- [x] Extend search on imminent promotions/counter-promotions.
- [x] Extend on forcing defensive checks that decide race/containment viability.
- [x] Extend on narrow king-only containment junctions in low-material endings.

### 5.2 Guardrails

- [x] Keep extension scope narrow and bounded to avoid search explosion.
- [x] Reuse existing selective-extension framework where available.
- [x] Verify extension logic is deterministic and testable.

### 5.3 Acceptance criteria

- [x] Critical-defense lines get deeper inspection at depth-3 without broad slowdown.
- [x] No timeout/runtime regressions in existing self-play/runtime tests.

### Phase note

- [x] Document extension trigger thresholds and observed impact.

- [x] Task 5 is complete. The selective extension trigger is intentionally narrow and only fires for real containment/promotion-control gains.

---

## Task 6: Transcript Validation and Practical Outcome Review

### 6.1 Run fresh self-play validation

- [x] Run uncapped depth-3 self-play and save transcript under `tmp/`.
- [x] Compare late endgame sequence against baseline bad pattern positions.
- [x] Record first divergence point from passive baseline pattern.

### 6.2 Practical behavior review

- [x] Confirm Black chooses more active containment in target moments.
- [x] Confirm White conversion pressure remains tactically sound.
- [x] Confirm no obvious plan-regression loops were introduced.

### 6.3 Acceptance criteria

- [x] Transcript shows fewer passive king shuffles in critical endgames.
- [x] Targeted defensive improvements are visible in concrete move choices.

### Phase note

- [x] Write `tmp/endgame_fix1_validation_summary.txt` with findings.

- [x] Task 6 is complete. The new depth-3 transcript `tmp/endgame_fix1_depth3_20260602T071131Z.txt` delays mate to move 114 and keeps Black’s king more active than the baseline’s repeated h-file drift.

---

## Task 7: Verification, Documentation, and Shipping

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

- [x] Commit with a message describing endgame-defense improvements.
- [x] Push to `origin/master`.

### Final acceptance criteria

- [x] New regressions pass and protect against passive endgame drift.
- [x] Full lint/type/test gate remains green.
- [x] Practical depth-3 transcript quality is measurably improved.

### Phase note

- [x] Task 7 is complete. The implementation is fully verified, committed, and ready on `origin/master`.
