# STRATEGY7 TODO

## Goal

Make the engine play **stronger practical chess in unstable middlegames and heavy-piece endings** by improving:

- **losing-side defense and threat containment**
- **winning-side conversion discipline**
- **threat-aware move ordering and root choice**
- **queen-and-rook ending coordination**
- **defensive king safety after castling**
- **passed-pawn race judgment**
- **anti-drift behavior in won or lost positions**
- **transcript-driven review coverage for recurring practical failures**

This pass should build on `docs/STRATEGY1_TODO.md` through `docs/STRATEGY6_TODO.md`, not replace them. The latest self-play game in `tmp/selfplay_w3b3_20260526T154110Z.txt` shows that the engine now opens more coherently than before, but it still plays **messy heavy-piece middlegames, weak defense once under pressure, and inefficient conversions that depend on the opponent cooperating**.

---

## Scope rules

- Keep legal move generation and board-rule correctness unchanged unless a new regression exposes a direct bug.
- Preserve the public `Board` API where possible.
- Prefer structural evaluation, move ordering, selective search, and review-loop improvements over hard-coded move bans.
- Do not fake stronger play with randomness.
- Do not weaken tactical correctness just to get cleaner-looking strategic play.
- Define every strategic improvement through targeted tests and transcript-backed positions.
- Every major phase must end with:

  ```bash
  pylint chess_game
  python -m pytest tests -q
  ```

- For AI-heavy phases, also run:

  ```bash
  python -m pytest tests/test_ai.py tests/test_ai_quality.py tests/test_ai_search.py tests/test_alpha_beta_pruning.py -q
  ```

- For phases that materially change strategic behavior, also save and review at least one self-play game under `tmp/`.

---

# Task 0: Re-establish the post-STRATEGY6 baseline

## 0.1 Review the latest self-play game

- [x] Review `tmp/selfplay_w3b3_20260526T154110Z.txt`.
- [x] Record:
  - [x] final result
  - [x] move count
  - [x] first clearly good practical choice by the winning side
  - [x] first clearly avoidable defensive error by the losing side
  - [x] first point where a passed pawn became the dominant strategic feature
  - [x] first point where king safety and piece coordination diverged
  - [x] first point where the position demanded threat containment more than general activity
  - [x] first point where the losing side still had a better defensive plan than the engine chose

## 0.2 Extract concrete bad-move examples

- [x] Create a baseline artifact under `tmp/` summarizing the game’s worst decisions.
- [x] Include at least:
  - [x] Black’s flank pawn loosening after castling (`...h5`, `...h4`) when central and defensive tasks remained
  - [x] White’s decorative bishop drift (`Bh3`) before the position was stabilized
  - [x] Black’s later queen / bishop drift that failed to contain White’s passer
  - [x] a moment where Black should have prioritized stopping promotion over side activity
  - [x] a moment where White had a cleaner forcing conversion than the move played

## 0.3 Build transcript-backed positions

- [x] Reconstruct hand-built test positions for:
  - [x] losing-side defense against an outside passed pawn
  - [x] queen-and-rook coordination with mating threats on both sides
  - [x] forcing queen trade when materially ahead
  - [x] choosing blockade / checking defense over decorative activity
  - [x] avoiding a low-value rook or bishop shuffle in a practically urgent position
- [x] Record current `evaluate()` and `get_best_move()` behavior for each.

## 0.4 Define success metrics for STRATEGY7

- [x] Decide practical success criteria such as:
  - [x] fewer losing-side collapses once one passer becomes dangerous
  - [x] more consistent threat containment before side play
  - [x] cleaner queen-and-rook conversion when ahead
  - [x] fewer low-value shuffles in clearly won or clearly worse positions
  - [x] stronger defensive coordination around king safety and promotion squares

Phase note: Task 0 is complete. The current baseline artifact lives in `tmp/strategy7_baseline_positions.txt`. The key reproduced failures are Black's shell-loosening `...h5` / `...h4`, White's decorative `Bh3`, and Black's later queen / bishop drift away from passer containment once White's outside pawn became the dominant feature. The transcript-backed probes show that the current depth-3 engine still recommends `a7a5`, `d6a6`, `f1h3`, and `h8g7` in the new STRATEGY7 baseline positions, which gives the next defensive-resource and conversion phases precise practical targets.

---

# Task 1: Add transcript-driven defensive-resource regressions

## 1.1 Add “stop the passer first” regressions

- [x] Add tests where the engine should prefer stopping or blockading an enemy passer over irrelevant checks or side play.
- [x] Cover cases such as:
  - [x] occupying the promotion square or its approach square
  - [x] forcing the passer behind a blockade
  - [x] tying a rook or queen to the passer instead of chasing side pawns

## 1.2 Add threat-containment regressions

- [x] Add tests where the worse side should neutralize immediate mate / promotion threats before pursuing vague activity.
- [x] Cover cases such as:
  - [x] defending a back-rank or diagonal mating square
  - [x] preventing a queen-plus-rook invasion on the seventh or eighth rank
  - [x] preferring a checking or interposing move that reduces danger

## 1.3 Add “best practical defense” regressions

- [x] Add tests where the worse side should choose the line that maximizes resistance even if static evaluation remains poor.
- [x] Cover cases such as:
  - [x] perpetual-check tries
  - [x] queen trade avoidance when the resulting ending is immediately lost
  - [x] rook activity behind enemy passers rather than passive waiting

## 1.4 Add anti-panic regressions for the defending side

- [x] Add tests where the engine should reject decorative or irrelevant defensive moves.
- [x] Cover cases such as:
  - [x] bishop shuffles that do not change the threat picture
  - [x] queen moves with no new check, blockade, or trade threat
  - [x] rook sidesteps that do not attack the passer or improve king safety

Phase note:

- [x] Task 1 complete note

Task 1 is complete. The new `tests/test_ai_strategy7_regressions.py` file now pins the first STRATEGY7 defensive-resource theme from the fresh baseline: once White's `b7` passer appears, Black must stay tied to the b-file instead of replaying the old `...a5` or `...Qa6` style drift. This phase also added `chess_game/chess/defensive_containment_guidance.py`, which gives the materially worse side a structural heavy-piece containment signal in evaluation plus a narrow extension/root nudge around advanced enemy passers, and the immediate result is that the old baseline `...a5` panic no longer survives depth-3 search in that first transcript position.

---

# Task 2: Improve losing-side defense and threat containment

## 2.1 Audit current defensive guidance

- [x] Review the existing STRATEGY5/6 endgame, conversion, and passer-race helpers.
- [x] Identify where current logic already helps defense and where it still overvalues generic activity.
- [x] Save the audit under `tmp/`.

## 2.2 Strengthen evaluation for practical defense

- [x] Add or tighten heuristics for:
  - [x] enemy passer proximity to promotion
  - [x] whether the defending rook/queen is behind, beside, or in front of the passer
  - [x] king distance to critical promotion / blockade squares
  - [x] immediate mating-net danger around the king
  - [x] whether a defending piece is overloaded between king safety and promotion control

## 2.3 Strengthen quiet move ordering for defense

- [x] Prefer candidate moves that:
  - [x] reduce immediate promotion danger
  - [x] increase checking resources
  - [x] contest key files / ranks near the king or passer
  - [x] force simplifying defensive resources when appropriate
- [x] Demote quiet moves that:
  - [x] preserve no new defensive resource
  - [x] ignore the most dangerous enemy threat
  - [x] drift away from the main theater

## 2.4 Strengthen root tie-break behavior for defense

- [x] Ensure near-equal root moves prefer the line with the best practical resistance.
- [x] Reward:
  - [x] forcing checks
  - [x] blockade / trade opportunities
  - [x] moves that reduce the opponent’s safe promotion path

Phase note:

- [x] Task 2 complete note

Task 2 is complete. The audit artifact lives in `tmp/strategy7_task2_audit.txt`, and the heavy-piece containment layer now scores front/behind/beside heavy-piece geometry, support for attacked key defenders, immediate mating-net pressure from real heavy-piece channels, and retained checking / trade resources for the worse side. `ai_move_ordering.py` now also feeds the same containment logic into quiet ordering, `tests/test_ai_strategy7_regressions.py` now proves that the later heavy-piece probe rejects the old `...Qa6` drift and prefers covering overloaded defenders, and the phase self-play review in `tmp/strategy7_task2_review.txt` shows that Black still lost but resisted until move 126 while handling the later passer fight with `...Qd6`, `...Qd5`, and `...f5` instead of repeating the old `...Qa6` / `...Kg7` defensive drift.

---

# Task 3: Add transcript-driven winning-conversion regressions

## 3.1 Add “simplify when clearly winning” regressions

- [x] Add tests where the engine should trade into a clearly won heavy-piece ending instead of preserving unnecessary complexity.
- [x] Cover cases such as:
  - [x] queen trade into a won rook ending
  - [x] rook trade into a trivially winning queen ending
  - [x] piece trade that leaves an unstoppable passer

## 3.2 Add “push the main passer” regressions

- [x] Add tests where the engine should prioritize the strongest passed pawn over harmless side activity.
- [x] Cover cases such as:
  - [x] outside passed pawn support
  - [x] rook behind passer
  - [x] queen escort toward promotion

## 3.3 Add “remove counterplay first” regressions

- [x] Add tests where the winning side should neutralize the opponent’s only practical resource before drifting.
- [x] Cover cases such as:
  - [x] removing checking resources
  - [x] covering perpetual squares
  - [x] restricting enemy king approach to the passer

## 3.4 Add anti-drift regressions for the winning side

- [x] Add tests where the engine should reject low-value shuffles while ahead.
- [x] Cover cases such as:
  - [x] queen moves with no mate, trade, or passer support
  - [x] rook moves that do not improve file/rank pressure
  - [x] bishop / king maneuvers that slow promotion without improving safety

Phase note:

- [x] Task 3 complete note

Task 3 is complete. `tests/test_ai_strategy7_regressions.py` now includes six new winning-side regressions covering the conversion themes that still mattered after Task 2: simplifying with queen or rook trades when the resulting ending is trivially won, trading the last minor blocker when that leaves the passer decisive, prioritizing rook/queen passer support over harmless side activity, and rejecting the transcript's `Bh3` drift before the position is stabilized. This phase is intentionally regression-first: the new coverage now pins the remaining STRATEGY7 conversion targets before Task 4 expands the actual conversion guidance.

---

# Task 4: Improve winning-side conversion discipline

## 4.1 Audit current conversion guidance

- [x] Review the existing conversion, defensive-endgame, and passer-race modules against the new transcript.
- [x] Identify where the engine already converts correctly and where root choice still drifts.
- [x] Save the audit under `tmp/`.

## 4.2 Strengthen evaluation for practical conversion

- [x] Add or tighten heuristics for:
  - [x] forcing trade quality when ahead
  - [x] king activation behind the main passer
  - [x] rook / queen support of promotion squares
  - [x] suppression of enemy checking counterplay
  - [x] avoiding unnecessary pawn grabs away from the main winning plan

## 4.3 Strengthen quiet move ordering for conversion

- [x] Prefer:
  - [x] forcing captures that remove counterplay
  - [x] trade offers that simplify into known wins
  - [x] moves that improve passer support or king cut-off
- [x] Demote:
  - [x] harmless side checks
  - [x] lateral rook shuffles without new pressure
  - [x] queen drift that does not improve mate or promotion chances

## 4.4 Strengthen root tie-break behavior for conversion

- [x] Ensure near-equal root choices prefer the most forcing practical win.
- [x] Reward:
  - [x] shorter route to promotion
  - [x] lower counterplay exposure
  - [x] cleaner transition into technically won endgames

Phase note:

- [x] Task 4 is complete. The audit artifact lives in `tmp/strategy7_task4_audit.txt`, the fresh self-play transcript lives in `tmp/strategy7_task4_w3b3_20260526T212046Z.txt`, and the review note lives in `tmp/strategy7_task4_review.txt`. `conversion_guidance.py` now extends beyond simple endgames into clearly winning outside-passer heavy-piece battles, but only when the winning side is not under urgent king danger; it now scores trade quality, king support behind the main passer, promotion-lane support, counterplay suppression, and anti-drift geometry, while `ai_search_helpers.py` allows a bounded root tie-break override only in clearly winning positions. The transcript-backed `Bh3` conversion drift no longer survives at depth 3, White converted the fresh review game cleanly by move 86, and the main remaining visible blemish is that Black still repeated the old `...h5` / `...h4` shell-loosening pattern before the conversion phase.

---

# Task 5: Improve threat-aware move ordering and root choice

## 5.1 Add transcript-driven threat-ordering regressions

- [ ] Add tests where the engine should prefer moves that answer the opponent’s most urgent threat.
- [ ] Cover cases such as:
  - [ ] stopping a passer over making a harmless threat
  - [ ] defending mate squares over pushing a side pawn
  - [ ] forcing queen trade when ahead over speculative pressure

## 5.2 Audit current move-ordering hot paths

- [ ] Review `ai_move_ordering.py`, `ai_search_helpers.py`, and related guidance modules for overlap.
- [ ] Identify which threat-aware signals are cheap enough for hot-path ordering and which belong only in evaluation / root bonuses.
- [ ] Save the audit under `tmp/`.

## 5.3 Add practical threat signals to quiet ordering

- [ ] Score moves for:
  - [ ] reducing enemy checking resources
  - [ ] contesting promotion squares
  - [ ] increasing king flight squares
  - [ ] forcing the opponent into narrower reply sets

## 5.4 Add root-level threat-aware tie-breaks

- [ ] When root scores are near-equal, prefer moves that:
  - [ ] answer the clearest enemy threat
  - [ ] create forcing simplification
  - [ ] lower tactical volatility when ahead
  - [ ] maximize practical resistance when worse

Phase note:

- [ ] Task 5 complete note

---

# Task 6: Add queen-and-rook ending guidance

## 6.1 Add transcript-driven heavy-piece ending regressions

- [ ] Add tests for queen-and-rook / queen-only practical endings exposed by the latest game.
- [ ] Cover cases such as:
  - [ ] rook behind passer
  - [ ] queen escort toward promotion
  - [ ] defending king shelter against repeated checks
  - [ ] queen trade into a clearly won or clearly holdable ending

## 6.2 Audit current heavy-piece logic

- [ ] Review whether existing endgame helpers already recognize these structures.
- [ ] Identify gaps specific to queen-and-rook coordination and king shelter.
- [ ] Save the audit under `tmp/`.

## 6.3 Add evaluation guidance for heavy-piece endings

- [ ] Add or tighten heuristics for:
  - [ ] rook placement behind own or enemy passers
  - [ ] queen proximity to promotion and checking squares
  - [ ] king shelter quality against queen checks
  - [ ] whether heavy pieces are coordinated or stepping on each other

## 6.4 Add quiet-order / root bonuses for heavy-piece practicality

- [ ] Prefer moves that:
  - [ ] improve queen-rook coordination
  - [ ] threaten promotion or forced checks
  - [ ] reduce the opponent’s checking net
- [ ] Demote moves that:
  - [ ] split queen and rook away from the main theater
  - [ ] abandon promotion support
  - [ ] allow easy perpetual or perpetual-like checking sequences

Phase note:

- [ ] Task 6 complete note

---

# Task 7: Strengthen passed-pawn race judgment

## 7.1 Add passed-pawn race regressions

- [ ] Add tests where the engine should correctly identify:
  - [ ] unstoppable passers
  - [ ] only-blockadable passers
  - [ ] queen escort beats side counterplay
  - [ ] wrong-side activity loses the race immediately

## 7.2 Audit existing passer-race guidance

- [ ] Review how `passer_race_guidance.py`, conversion guidance, and defensive guidance interact.
- [ ] Identify missing features from the new transcript.
- [ ] Save the audit under `tmp/`.

## 7.3 Tighten passer-race evaluation

- [ ] Add or refine scoring for:
  - [ ] tempo-to-promotion differences
  - [ ] critical-square ownership
  - [ ] defender tied down to stopping promotion
  - [ ] whether checks help or hurt the race

## 7.4 Tighten passer-race ordering and root choice

- [ ] Prefer moves that:
  - [ ] create or preserve unstoppable promotion
  - [ ] force the defender into passivity
  - [ ] stop the opponent’s only rival race

Phase note:

- [ ] Task 7 complete note

---

# Task 8: Add anti-drift guidance in clearly won or clearly worse positions

## 8.1 Add anti-drift regressions

- [ ] Add tests where the engine should reject low-value activity in practical endings.
- [ ] Cover cases such as:
  - [ ] queen drift with no check / trade / promotion support
  - [ ] bishop shuffles that do not affect king safety or passers
  - [ ] rook moves that do not improve activity, blockade, or support
  - [ ] pawn pushes that do not improve promotion, king shelter, or mating pressure

## 8.2 Audit overlap with prior anti-repetition / quiet-plan logic

- [ ] Review whether current anti-repetition and plan-quality logic already covers parts of this behavior.
- [ ] Isolate only the remaining anti-drift gaps.
- [ ] Save the audit under `tmp/`.

## 8.3 Add practicality scoring

- [ ] Reward moves that:
  - [ ] change the threat picture
  - [ ] simplify into clearer wins or holds
  - [ ] improve promotion geometry
  - [ ] improve king safety materially
- [ ] Penalize moves that:
  - [ ] only look active
  - [ ] repeat pressure without progress
  - [ ] walk away from the main strategic theater

Phase note:

- [ ] Task 8 complete note

---

# Task 9: Review-loop expansion for STRATEGY7

## 9.1 Play fresh bounded review games

- [ ] Save at least one new depth-3 vs depth-3 self-play transcript under `tmp/`.
- [ ] If runtime is practical, also save one deeper review game.

## 9.2 Record fresh practical misses

- [ ] Create a STRATEGY7 review artifact under `tmp/`.
- [ ] For each major miss, record:
  - [ ] move chosen
  - [ ] better human move
  - [ ] why the human move is better
  - [ ] whether the miss was primarily evaluation, ordering, root choice, or search-depth related

## 9.3 Promote the worst new misses to regressions

- [ ] Add targeted tests for the worst recurring new errors.
- [ ] Update the strategy plan if the review reveals an unplanned new theme.

Phase note:

- [ ] Task 9 complete note

---

# Task 10: Final acceptance for STRATEGY7

## 10.1 Validation

- [ ] Run:

  ```bash
  pylint chess_game
  python -m pytest tests -q
  ```

- [ ] Run targeted AI validation:

  ```bash
  python -m pytest tests/test_ai.py tests/test_ai_quality.py tests/test_ai_search.py tests/test_alpha_beta_pruning.py -q
  ```

## 10.2 Self-play review

- [ ] Save a fresh self-play transcript under `tmp/`.
- [ ] Confirm the reviewed game shows measurable improvement in:
  - [ ] losing-side defensive resistance
  - [ ] cleaner winning conversion
  - [ ] fewer low-value heavy-piece shuffles
  - [ ] better passed-pawn race judgment
  - [ ] more coherent queen-and-rook coordination

## 10.3 Closeout

- [ ] Update this file with completed statuses and notes.
- [ ] Commit only after lint and tests pass.
- [ ] Push to `origin/master`.

Phase note:

- [ ] Task 10 complete note
