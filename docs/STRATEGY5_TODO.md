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

- [ ] Add tests where the engine should avoid short back-and-forth moves.
- [ ] Cover cases such as:
  - [ ] rook moves to a file and immediately back with no gain
  - [ ] king steps forward and back in a quiet ending
  - [ ] queen reroutes that recreate the same geometry
  - [ ] knight hops out and back without improving control

## 1.2 Add “do not repeat while better” regressions

- [ ] Add tests where one side is better and should reject repetition.
- [ ] Cover cases such as:
  - [ ] side with an outside passer should improve king support instead of checking
  - [ ] side with a more active rook should cut off the king instead of repeating
  - [ ] side with safer king and extra pawn should simplify instead of looping
  - [ ] side with a winning queen/rook placement should keep pressure instead of resetting

## 1.3 Add “repetition is acceptable when genuinely necessary” regressions

- [ ] Add tests where the engine should preserve drawing resources.
- [ ] Cover cases such as:
  - [ ] side down material uses perpetual check as best defense
  - [ ] side under promotion threat uses repetition to avoid losing
  - [ ] equal dead-drawn endgame where repetition is fine

## 1.4 Add transcript-specific repetition regressions

- [ ] Add direct regressions from `tmp/selfplay_w3b3_20260525T212702Z.txt`.
- [ ] Cover at least:
  - [ ] the late White rook shuffle loop
  - [ ] the late Black king oscillation loop
  - [ ] the final repeated `Rh3/Rh4` vs `Kd3/Ke4` pattern

---

# Task 2: Strengthen anti-repetition and anti-shuffle scoring

## 2.1 Audit existing repetition logic

- [ ] Review current repetition scoring in:
  - [ ] `chess_game/chess/ai.py`
  - [ ] `chess_game/chess/ai_search_helpers.py`
  - [ ] root move tie-break logic
  - [ ] quiet move ordering
- [ ] Document:
  - [ ] when repetition penalties currently begin
  - [ ] how strongly they scale
  - [ ] where they are too late or too weak

## 2.2 Penalize short-cycle quiet shuffles before formal repetition

- [ ] Add structural penalties for:
  - [ ] immediate move undo patterns
  - [ ] same-piece oscillation over 2-4 plies
  - [ ] heavy-piece file hopping without new pressure
  - [ ] king triangulation that does not improve opposition, shelter, or conversion

## 2.3 Scale anti-repetition pressure by advantage and progress

- [ ] Increase penalties when the side to move has:
  - [ ] material edge
  - [ ] safer king
  - [ ] more active rook/queen
  - [ ] advanced passer
  - [ ] clear conversion setup
- [ ] Keep repetition acceptable when:
  - [ ] materially behind
  - [ ] under direct tactical pressure
  - [ ] forcing draw is the only practical resource

## 2.4 Improve root move selection against equal-scoring loops

- [ ] Add stronger root tie-break preference for moves that:
  - [ ] improve king position
  - [ ] cut off enemy king
  - [ ] increase passer support
  - [ ] trade into a simpler favorable ending
  - [ ] create fresh threats instead of recycled pressure

## 2.5 Add anti-shuffle helpers if needed

- [ ] If current logic is too scattered, extract a shared helper/module for:
  - [ ] short-cycle detection
  - [ ] quiet shuffle classification
  - [ ] plan-preserving improvement bonuses

---

# Task 3: Improve opening discipline and reduce low-value drift

## 3.1 Review opening mistakes from the transcript

- [ ] Identify every early move in the game that a strong human would distrust.
- [ ] Especially review:
  - [ ] `a2a4`
  - [ ] repeated rook moves before coordination is finished
  - [ ] quiet moves that neglect king safety or central control

## 3.2 Increase penalties for unjustified flank play

- [ ] Penalize early flank pawn moves more sharply when they:
  - [ ] do not fight for the center
  - [ ] do not prepare development
  - [ ] weaken structure
  - [ ] create no concrete tactical gain

## 3.3 Reward normal development and coordination more strongly

- [ ] Increase bonuses for:
  - [ ] completing minor-piece development
  - [ ] castling on time
  - [ ] connecting rooks
  - [ ] central rook placement after development
  - [ ] queen restraint in the opening

## 3.4 Penalize opening heavy-piece drift

- [ ] Penalize rook and queen moves in the opening when they:
  - [ ] repeat without improving coordination
  - [ ] abandon a useful file or square
  - [ ] delay king safety
  - [ ] chase cosmetic threats

## 3.5 Add opening-discipline regressions

- [ ] Add tests that prefer:
  - [ ] normal development over flank pawn pushes
  - [ ] king safety over rook drift
  - [ ] central recapture / structure preservation over side activity
  - [ ] finishing coordination before speculative pressure

---

# Task 4: Improve plan recognition in quiet middlegames

## 4.1 Revisit “worst piece improvement” after STRATEGY4

- [ ] Review whether the current worst-piece model still misses:
  - [ ] trapped or inactive rooks
  - [ ] bishops lacking diagonals
  - [ ] knights with no route to useful squares
  - [ ] queens over-pressing instead of coordinating

## 4.2 Reward plan-consistent improvement

- [ ] Reward moves that:
  - [ ] improve the least useful piece
  - [ ] reinforce the main file/diagonal of play
  - [ ] support the intended pawn break
  - [ ] prepare conversion instead of preserving static pressure

## 4.3 Penalize “activity with no plan”

- [ ] Penalize moves that:
  - [ ] attack a square twice without increasing real threats
  - [ ] relocate a piece to an equally useless square
  - [ ] preserve pressure but worsen coordination
  - [ ] create harmless threats while neglecting the only real plan

## 4.4 Add quiet-plan regressions

- [ ] Add tests where the engine should choose:
  - [ ] improving the worst rook over a harmless check
  - [ ] king improvement over repeated pressure
  - [ ] restraining the opponent before pushing its own plan
  - [ ] activation tied to the pawn structure instead of free-form drifting

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
