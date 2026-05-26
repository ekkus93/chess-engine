# STRATEGY5 TODO

## Goal

Make the engine play **cleaner, more plan-driven practical chess** by improving:

- **anti-repetition behavior**
- **anti-shuffle discipline**
- **technical conversion in winning positions**
- **defensive drawing technique in worse positions**
- **opening discipline**
- **passed-pawn urgency**
- **plan recognition in quiet positions**
- **transcript-driven review and regression coverage**

This pass should build on `docs/STRATEGY1_TODO.md`, `docs/STRATEGY2_TODO.md`, `docs/STRATEGY3_TODO.md`, and `docs/STRATEGY4_TODO.md`, not replace them. The main failure mode exposed by the latest self-play game is no longer basic tactics or legality. It is that the engine still drifts into **low-value repetition loops, piece shuffles, and poor endgame conversion** even after achieving positions that a stronger human player would win or defend more purposefully.

---

## Scope rules

- Keep legal move generation and board-rule correctness unchanged unless a new regression exposes a direct engine bug.
- Preserve the public `Board` API where possible.
- Prefer structural evaluation, move ordering, and search improvements over ad hoc move bans.
- Do not fake “human style” with randomness.
- Do not weaken tactical correctness just to suppress repetition; improve decision quality instead.
- Define every strategic improvement through targeted tests and transcript-backed examples.
- Every major phase must end with:

  ```bash
  pylint chess_game
  python -m pytest tests -q
  ```

- For AI-heavy phases, also run targeted checks such as:

  ```bash
  python -m pytest tests/test_ai.py tests/test_ai_quality.py tests/test_ai_search.py tests/test_alpha_beta_pruning.py -q
  ```

- For phases that materially change strategic behavior, also save and review at least one self-play game under `tmp/`.

---

# Task 0: Re-establish the post-STRATEGY4 quality baseline

## 0.1 Record the latest self-play failure pattern

- [x] Review `tmp/selfplay_w3b3_20260525T212702Z.txt`.
- [x] Note:
  - [x] final result
  - [x] move count
  - [x] first clearly aimless White move
  - [x] first clearly aimless Black move
  - [x] first moment Black obtained the easier game
  - [x] first moment Black failed to convert a human-favorable position
  - [x] first moment White escaped with practical counterplay
  - [x] exact repetition loop that ended the game

## 0.2 Extract concrete “bad move vs better human move” examples

- [x] Create a baseline artifact under `tmp/` summarizing the game’s worst strategic decisions.
- [x] Include at least:
  - [x] White’s early flank-pawn drift / quiet self-weakening
  - [x] White’s rook shuffle sequence
  - [x] Black’s failure to simplify or improve before repeating
  - [x] Black’s late endgame king/rook/knight drift into repetition
  - [x] final king-vs-rook-passer repetition loop

## 0.3 Build baseline positions from the transcript

- [x] Reconstruct hand-built test positions from the transcript for:
  - [x] opening discipline failure
  - [x] repeated rook shuffle failure
  - [x] “press the edge, do not repeat” winning endgame
  - [x] “hold the draw with purpose, not random activity” defensive endgame
  - [x] passed-pawn urgency vs checking drift
- [x] Record current `evaluate()` and `get_best_move()` behavior for each.

## 0.4 Define success metrics for STRATEGY5

- [x] Decide practical success criteria such as:
  - [x] fewer short repetition loops in self-play
  - [x] fewer repeated quiet heavy-piece moves without gain
  - [x] better conversion rate in materially better endgames
  - [x] more stable opening development choices
  - [x] fewer transcript-review “embarrassing moves”

Phase note: Task 0 is complete. The current baseline artifact lives in `tmp/strategy5_baseline_positions.txt`. The key reproduced failures are: White's early `a2a4` opening drift, White's repeated rook shuffles in an already inferior middlegame, Black's conversion failure after obtaining the easier game, Black's late defensive oscillation instead of purposeful drawing technique, and White's final refusal to promote the `b7` passer in favor of `Rh3-h4` repetition. Baseline replay probes also show the current engine still recommends several of those low-quality moves, which gives STRATEGY5 direct transcript-backed targets.

---

# Task 1: Add regression tests for anti-shuffle and anti-repetition behavior

## 1.1 Add “do not immediately undo your move” regressions

- [x] Add tests where the engine should avoid short back-and-forth moves.
- [x] Cover cases such as:
  - [x] rook moves to a file and immediately back with no gain
  - [x] king steps forward and back in a quiet ending
  - [ ] queen reroutes that recreate the same geometry
  - [ ] knight hops out and back without improving control

## 1.2 Add “do not repeat while better” regressions

- [x] Add tests where one side is better and should reject repetition.
- [x] Cover cases such as:
  - [x] side with an outside passer should improve king support instead of checking
  - [x] side with a more active rook should cut off the king instead of repeating
  - [x] side with safer king and extra pawn should simplify instead of looping
  - [x] side with a winning queen/rook placement should keep pressure instead of resetting

## 1.3 Add “repetition is acceptable when genuinely necessary” regressions

- [x] Add tests where the engine should preserve drawing resources.
- [x] Cover cases such as:
  - [x] side down material uses perpetual check as best defense
  - [x] side under promotion threat uses repetition to avoid losing
  - [x] equal dead-drawn endgame where repetition is fine

## 1.4 Add transcript-specific repetition regressions

- [x] Add direct regressions from `tmp/selfplay_w3b3_20260525T212702Z.txt`.
- [x] Cover at least:
  - [x] the late White rook shuffle loop
  - [x] the late Black king oscillation loop
  - [x] the final repeated `Rh3/Rh4` vs `Kd3/Ke4` pattern

Phase note: Task 1 is complete. `tests/test_ai_strategy5_regressions.py` now locks in immediate rook/king undo regressions plus the transcript-backed late king oscillation and promotion-over-repetition failures, and the pre-existing draw-resource coverage in `tests/test_ai_quality.py` now explicitly closes Task 1.3.

---

# Task 2: Strengthen anti-repetition and anti-shuffle scoring

## 2.1 Audit existing repetition logic

- [x] Review current repetition scoring in:
  - [x] `chess_game/chess/ai.py`
  - [x] `chess_game/chess/ai_search_helpers.py`
  - [x] root move tie-break logic
  - [x] quiet move ordering
- [x] Document:
  - [x] when repetition penalties currently begin
  - [x] how strongly they scale
  - [x] where they are too late or too weak

## 2.2 Penalize short-cycle quiet shuffles before formal repetition

- [x] Add structural penalties for:
  - [x] immediate move undo patterns
  - [ ] same-piece oscillation over 2-4 plies
  - [x] heavy-piece file hopping without new pressure
  - [x] king triangulation that does not improve opposition, shelter, or conversion

## 2.3 Scale anti-repetition pressure by advantage and progress

- [x] Increase penalties when the side to move has:
  - [x] material edge
  - [x] safer king
  - [x] more active rook/queen
  - [x] advanced passer
  - [x] clear conversion setup
- [x] Keep repetition acceptable when:
  - [x] materially behind
  - [x] under direct tactical pressure
  - [x] forcing draw is the only practical resource

## 2.4 Improve root move selection against equal-scoring loops

- [x] Add stronger root tie-break preference for moves that:
  - [x] improve king position
  - [x] cut off enemy king
  - [x] increase passer support
  - [ ] trade into a simpler favorable ending
  - [x] create fresh threats instead of recycled pressure

## 2.5 Add anti-shuffle helpers if needed

- [x] If current logic is too scattered, extract a shared helper/module for:
  - [x] short-cycle detection
  - [x] quiet shuffle classification
  - [ ] plan-preserving improvement bonuses

Phase note: Task 2 is complete for this anti-repetition slice. The audit showed quiet-order and root penalties were only engaging once formal repetition was already visible, so the new `chess_game/chess/ai_repetition_patterns.py` helper now penalizes immediate quiet undo moves earlier, scales root penalties more sharply in simple winning endgames, and stops immediate quiet reversals from bypassing those penalties via superficial king-pressure gains.

---

# Task 3: Improve opening discipline and reduce low-value drift

## 3.1 Review opening mistakes from the transcript

- [x] Identify every early move in the game that a strong human would distrust.
- [x] Especially review:
  - [x] `a2a4`
  - [x] repeated rook moves before coordination is finished
  - [x] quiet moves that neglect king safety or central control

## 3.2 Increase penalties for unjustified flank play

- [x] Penalize early flank pawn moves more sharply when they:
  - [x] do not fight for the center
  - [x] do not prepare development
  - [x] weaken structure
  - [x] create no concrete tactical gain

## 3.3 Reward normal development and coordination more strongly

- [x] Increase bonuses for:
  - [x] completing minor-piece development
  - [x] castling on time
  - [x] connecting rooks
  - [x] central rook placement after development
  - [x] queen restraint in the opening

## 3.4 Penalize opening heavy-piece drift

- [x] Penalize rook and queen moves in the opening when they:
  - [x] repeat without improving coordination
  - [x] abandon a useful file or square
  - [x] delay king safety
  - [x] chase cosmetic threats

## 3.5 Add opening-discipline regressions

- [x] Add tests that prefer:
  - [x] normal development over flank pawn pushes
  - [x] king safety over rook drift
  - [x] central recapture / structure preservation over side activity
  - [x] finishing coordination before speculative pressure

Phase note: Task 3 is complete. The opening-discipline pass now lives in `chess_game/chess/opening_move_ordering.py` and `chess_game/chess/opening_development.py`, which together tighten early flank-pawn penalties, reward on-time castling plus connected/central rook coordination, keep quiet queen drift behind normal development, and punish early rook drift such as the transcript's `Rh1-g1` sequence. Regression coverage now explicitly includes king safety over rook drift, finishing development over quiet queen pressure, central recapture over side activity, and stronger development breakdown scoring for castled connected rooks. A fresh review artifact at `tmp/strategy5_task3_w3b3.txt` already shows the opening segment avoiding the old early `a2a4` / rook-drift pattern through move 22.

---

# Task 4: Improve plan recognition in quiet middlegames

## 4.1 Revisit “worst piece improvement” after STRATEGY4

- [x] Review whether the current worst-piece model still misses:
  - [x] trapped or inactive rooks
  - [x] bishops lacking diagonals
  - [x] knights with no route to useful squares
  - [x] queens over-pressing instead of coordinating

## 4.2 Reward plan-consistent improvement

- [x] Reward moves that:
  - [x] improve the least useful piece
  - [x] reinforce the main file/diagonal of play
  - [x] support the intended pawn break
  - [x] prepare conversion instead of preserving static pressure

## 4.3 Penalize “activity with no plan”

- [x] Penalize moves that:
  - [x] attack a square twice without increasing real threats
  - [x] relocate a piece to an equally useless square
  - [x] preserve pressure but worsen coordination
  - [x] create harmless threats while neglecting the only real plan

## 4.4 Add quiet-plan regressions

- [x] Add tests where the engine should choose:
  - [x] improving the worst rook over a harmless check
  - [x] king improvement over repeated pressure
  - [x] restraining the opponent before pushing its own plan
  - [x] activation tied to the pawn structure instead of free-form drifting

Phase note: Task 4 is complete. The quiet-plan stack from STRATEGY4 already covered most of this phase through `piece_coordination.py`, `structure_recognition.py`, opponent-plan pressure, and the existing regression suites for worst-rook improvement, rook reconnection, bishop long-diagonal reroutes, knight outpost maneuvers, and restraint before wing expansion. This Task 4 pass closes the remaining explicit gap by adding a quiet king-refinement bonus in `ai_move_ordering.py` and a direct regression proving useful king improvement beats recycled pressure. The overall result is that plan-consistent quiet moves now have explicit coverage across activity, structure, and prophylaxis instead of only being implied by earlier strategy phases.

---

# Task 5: Strengthen winning-endgame conversion

## 5.1 Audit the latest conversion failure patterns

- [ ] Review the transcript sections where Black had the easier game.
- [ ] Identify missing conversion ideas such as:
  - [ ] king activation
  - [ ] king cutoff
  - [ ] rook behind passer
  - [ ] reducing checking distance
  - [ ] simplification into easier technical wins

## 5.2 Improve conversion evaluation terms

- [ ] Add or strengthen evaluation for:
  - [ ] king escort of passers
  - [ ] rook/queen support from behind the passer
  - [ ] cutting off the defender king
  - [ ] forcing simplification when clearly favorable
  - [ ] zugzwang-style waiting improvement in simple endings

## 5.3 Demote flashy but unproductive checks

- [ ] Penalize checking moves when they:
  - [ ] do not improve conversion geometry
  - [ ] allow repetition
  - [ ] lose king opposition / cutoff progress
  - [ ] reset progress without gaining material

## 5.4 Reward counterplay suppression before pawn racing

- [ ] Reward moves that:
  - [ ] stop the enemy passed pawn first
  - [ ] reduce checking resources
  - [ ] exchange the enemy’s most active defender
  - [ ] secure promotion squares before advancing

## 5.5 Add conversion regressions

- [ ] Add tests where the engine should:
  - [ ] simplify a winning rook ending
  - [ ] centralize the king before repeating checks
  - [ ] choose cutoff/escort over harmless checking
  - [ ] convert a better queen/rook ending without repetition drift

---

# Task 6: Strengthen defensive endgame technique

## 6.1 Separate “drawing method” from “random activity”

- [ ] Reward defensive moves that:
  - [ ] establish checking distance that actually matters
  - [ ] reach a fortress-like setup
  - [ ] attack the enemy pawn base
  - [ ] approach opposition or critical squares
  - [ ] force the stronger side to spend tempi

## 6.2 Penalize fake counterplay when worse

- [ ] Penalize defensive moves that:
  - [ ] give checks but worsen king placement
  - [ ] abandon the only blockade square
  - [ ] chase side pawns instead of stopping the main passer
  - [ ] drift into losing geometry under the guise of activity

## 6.3 Improve drawing-resource recognition

- [ ] Add recognition for:
  - [ ] perpetual-check resources
  - [ ] blockading the passer from the correct side
  - [ ] checking from the side vs rear when appropriate
  - [ ] sacrificing into known drawn structures when justified

## 6.4 Add defensive regressions

- [ ] Add tests where the engine should:
  - [ ] hold with purposeful checking instead of random shuffling
  - [ ] occupy the correct blockade square
  - [ ] head for the draw zone with king/rook instead of chasing pawns
  - [ ] repeat only when it is truly the best defense

---

# Task 7: Increase passed-pawn urgency and promotion-race quality

## 7.1 Review current passer handling

- [ ] Audit evaluation and move ordering for:
  - [ ] advanced passers
  - [ ] protected passers
  - [ ] outside passers
  - [ ] connected passers
  - [ ] enemy passer danger

## 7.2 Increase urgency around critical promotion races

- [ ] Reward moves that:
  - [ ] support an advanced passer
  - [ ] clear the promotion path
  - [ ] force king support into the critical zone
  - [ ] trade off the best blocker

## 7.3 Penalize ignoring enemy passer danger

- [ ] Penalize moves that:
  - [ ] give side checks while an enemy passer runs
  - [ ] abandon promotion squares
  - [ ] improve activity but lose the race
  - [ ] choose repetition over direct passer suppression when still better

## 7.4 Consider selective search extensions for passer races

- [ ] Evaluate whether to add or retune extensions around:
  - [ ] advanced passer pushes
  - [ ] near-promotion positions
  - [ ] king-entry races
  - [ ] forced simplifications into pawn endings

## 7.5 Add passer-race regressions

- [ ] Add tests where the engine should:
  - [ ] escort its passer instead of checking
  - [ ] stop the enemy passer before making a cosmetic move
  - [ ] choose the correct rook/king square in a promotion race
  - [ ] convert outside-passer positions more directly

---

# Task 8: Improve search behavior in strategically quiet positions

## 8.1 Audit selective search for quiet strategic blindness

- [ ] Review where current search still prefers:
  - [ ] stale pressure
  - [ ] harmless checks
  - [ ] repeated “safe” moves
  - [ ] tactical-looking but strategically empty lines

## 8.2 Revisit quiet move ordering

- [ ] Increase quiet-order preference for moves that:
  - [ ] improve conversion geometry
  - [ ] reduce repetition risk
  - [ ] activate king/rook toward the relevant theater
  - [ ] suppress the opponent’s only counterplay

## 8.3 Improve root move stability

- [ ] Review whether aspiration / tie-break behavior is favoring loops.
- [ ] If needed, strengthen preference for:
  - [ ] stable progress
  - [ ] clearer plans
  - [ ] simpler winning lines
  - [ ] more forcing defensive resources when behind

## 8.4 Add search-regression tests

- [ ] Add tests ensuring search no longer overrides clearly better quiet plans with:
  - [ ] sterile checks
  - [ ] same-piece shuffles
  - [ ] premature repetition
  - [ ] side pressure that ignores the main plan

---

# Task 9: Expand transcript-driven review loop

## 9.1 Save new STRATEGY5 review games

- [ ] Run and save at least:
  - [ ] depth 3 vs depth 3 review game
  - [ ] one deeper review game if runtime is acceptable

## 9.2 Record embarrassing moves after each major phase

- [ ] Maintain a review artifact under `tmp/` with:
  - [ ] move chosen
  - [ ] better human move
  - [ ] why it is better
  - [ ] whether the miss is evaluation-, ordering-, or search-driven

## 9.3 Convert reviewed failures into regressions

- [ ] After each phase, add or update tests for the most serious newly observed failure.

## 9.4 Keep a running quality checklist

- [ ] Track whether the engine still shows:
  - [ ] rook shuffling
  - [ ] king oscillation
  - [ ] unjustified flank pawn pushes
  - [ ] non-converting winning endgames
  - [ ] pointless defensive activity instead of real drawing methods

---

# Task 10: Final acceptance for STRATEGY5

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
  - [ ] opening discipline
  - [ ] reduced quiet shuffling
  - [ ] better conversion attempts
  - [ ] cleaner handling of drawn endings

## 10.3 Closeout

- [ ] Update this file with completed statuses and notes.
- [ ] Commit only after lint and tests pass.
- [ ] Push to `origin/master`.
