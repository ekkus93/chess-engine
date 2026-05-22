# STRATEGY3 TODO

## Goal

Make the engine **distinguish real attacking progress from fake activity** so it plays safer, more coordinated, and more purposeful chess in queen/rook-rich positions.

This pass focuses on:

- stronger **king-safety evaluation**
- better detection of **fake queen activity**
- clearer separation of **useful checks** from empty checks
- stronger **defensive coordination** under attack
- better **development and opening sanity**
- more selective **tactical search support** near exposed kings

This pass should build on `docs/STRATEGY1_TODO.md` and `docs/STRATEGY2_TODO.md`, not replace them. The intent here is to fix the failure mode seen in recent depth-3 self-play: flashy queen moves and king walks can look active to the engine even when they are strategically or tactically unsound.

---

## Scope rules

- Keep move legality and board rules unchanged unless a new AI regression exposes a direct engine bug.
- Preserve the public `Board` API where possible.
- Prefer structural evaluation/search improvements over one-off move hacks.
- Do not hide weak play behind randomness.
- Use targeted tests to define when activity is real, when defense is mandatory, and when checks are useful.
- Every major phase must end with:

  ```bash
  pylint chess_game
  python -m pytest tests -q
  ```

- For AI-focused phases, also run targeted checks such as:

  ```bash
  python -m pytest tests/test_ai.py tests/test_ai_quality.py tests/test_ai_search.py tests/test_alpha_beta_pruning.py -q
  ```

---

# Task 0: Re-establish the tactical/king-safety baseline

## 0.1 Record the current failure pattern

- [x] Run and save at least one fresh self-play transcript that highlights the current issue.
- [x] Store the transcript under `tmp/` or `docs/` as appropriate.
- [x] Note:
  - [x] final result
  - [x] move count
  - [x] first point where one king became unsafe
  - [x] first point where queen activity became fake rather than useful
  - [x] first point where defense should have overridden activity
  - [x] final tactical sequence that decided the game

Baseline note: `tmp/strategy3_w3b3.txt` ended with **checkmate on move 40 (White wins)**. Black’s position became strategically unsafe once the queen raid (`...Qa5-b5-a4-f4-f2`) pulled heavy pieces away from king defense while the king drifted (`...Ke7-f6-e7-f8`) into White’s queen/rook lanes. White’s final conversion was the queen-and-rook invasion `Qd7`, `Rd6`, `Qd8#`; Black should have prioritized defense and king shelter much earlier.

## 0.2 Build baseline “unsafe king” positions

- [x] Create a small set of hand-built positions where one side has tempting activity but an unsafe king.
- [x] Include positions covering:
  - [x] central king with queens still on the board
  - [x] king with broken pawn shelter
  - [x] king exposed to queen + rook pressure
  - [x] king vulnerable on open files
  - [x] king with back-rank weaknesses and no luft
  - [x] king walk that loses coordination with defenders
- [x] Record current `evaluate()` and `get_best_move()` behavior for each.

## 0.3 Build baseline “fake activity” positions

- [x] Create targeted positions where flashy queen or rook moves look active but do not improve the position.
- [x] Include cases such as:
  - [x] queen raid that wins no material and creates no mating net
  - [x] repeated queen swings that do not improve king pressure
  - [x] harmless side checks that do not worsen the enemy king
  - [x] rook lift that abandons key defensive squares
  - [x] pawn-grabbing line that opens the moving side’s own king
- [x] Record whether the engine currently overrates the active-looking move.

## 0.4 Build baseline “must defend” positions

- [x] Create positions where one side must defend before pursuing its own plan.
- [x] Include cases such as:
  - [x] contesting an invasion file
  - [x] blocking a mate threat
  - [x] preventing queen penetration on the 7th or 8th rank
  - [x] creating luft before the back rank collapses
  - [x] keeping queen and rook connected around the king
- [x] Record whether the engine chooses defense or drifts into pseudo-activity.

Baseline artifact: `tmp/strategy3_baseline_positions.txt` records the hand-built unsafe-king, fake-activity, and must-defend positions together with current `evaluate()` and `get_best_move()` outputs.

---

# Task 1: Add regression tests for real activity vs fake activity

## 1.1 Add “do not play fake attack” tests

- [x] Add tests where an apparently active move should be rejected.
- [x] Cover cases such as:
  - [x] queen raid without material gain or mating threat
  - [x] repeated queen shuffle without improving geometry
  - [x] side check that does not reduce enemy king safety
  - [x] rook swing that abandons king protection
  - [x] pawn grab that exposes the moving side’s king

## 1.2 Add “useful check vs empty check” tests

- [x] Add tests where checks should be preferred only when they matter.
- [x] Cover checks that:
  - [x] force the enemy king toward the edge
  - [x] force the king away from a key defensive square
  - [x] support simplification or material gain
  - [x] create or preserve a mating net
- [x] Add tests where checks should be downgraded because they:
  - [x] merely repeat geometry
  - [x] improve nothing strategically
  - [x] surrender the attacker’s own king safety
  - [x] concede a key defensive or central square

## 1.3 Add “must defend first” tests

- [x] Add tests where the best move is defensive and non-flashy.
- [x] Cover cases such as:
  - [x] making luft instead of launching a side attack
  - [x] contesting an open file instead of pawn grabbing
  - [x] covering an invasion square instead of checking
  - [x] reconnecting queen and rook instead of chasing pawns
  - [x] moving the king to safety instead of seeking counterplay

## 1.4 Add opening-sanity tests

- [x] Add tests for healthier early-game priorities.
- [x] Cover cases such as:
  - [x] developing a minor piece before repeating a queen move
  - [x] castling readiness over premature queen adventure
  - [x] keeping central pawn structure sound over speculative flank activity
  - [x] preferring completed development over early rook wandering

---

# Task 2: Strengthen king-safety evaluation

## 2.1 Expand king-danger model

- [x] Define a clearer king-danger model for middlegame and queen-heavy positions.
- [x] Include at least:
  - [x] pawn shelter quality
  - [x] open or semi-open files near the king
  - [x] attacker count near king ring squares
  - [x] queen + rook coordination against the king
  - [x] missing escape squares / lack of luft
  - [x] distance of defending pieces from the king

## 2.2 Penalize exposed central kings more accurately

- [x] Increase penalties when:
  - [x] queens remain on the board
  - [x] multiple heavy pieces can attack files or ranks near the king
  - [x] the king leaves shelter without compensation
  - [x] the king walks into zones controlled by enemy heavy pieces
- [x] Ensure the penalty scales down appropriately in simplified endings.

## 2.3 Recognize king-walk danger

- [x] Add logic that penalizes king walks that:
  - [x] reduce coordination with rooks/queen
  - [x] lose cover from pawns
  - [x] step into checking nets
  - [x] move toward central attack lanes
- [x] Avoid over-penalizing purposeful endgame king centralization.

## 2.4 Expose king safety in evaluation breakdown

- [x] Add clearly named king-safety components to `get_evaluation_breakdown()`.
- [x] Keep them explainable and separate from raw material.

---

# Task 3: Downgrade fake queen and rook activity

## 3.1 Define “real activity” for heavy pieces

- [x] Decide what counts as meaningful queen/rook activity.
- [x] Include at least:
  - [x] direct tactical threat
  - [x] material gain or forced concession
  - [x] improved pressure on king entry squares
  - [x] stronger coordination with other attackers
  - [x] reduction of enemy counterplay

## 3.2 Penalize unsupported queen raids

- [x] Penalize queen moves that:
  - [x] enter enemy territory without support
  - [x] create no concrete threat
  - [x] abandon defense of own king
  - [x] repeat the same route with no improved outcome
  - [x] can be chased while losing tempi

## 3.3 Penalize flashy moves that loosen the moving side

- [x] Penalize rook/queen activity that:
  - [x] abandons the back rank
  - [x] disconnects queen and rook
  - [x] loses control of key files
  - [x] opens tactical access to the own king
  - [x] gives the opponent obvious invasion squares

## 3.4 Reward coordinated heavy-piece pressure more precisely

- [x] Reward heavy-piece moves that:
  - [x] attack along open lines toward the king
  - [x] increase pressure on defended-but-stressed squares
  - [x] support mate threats or simplification
  - [x] improve attacker concentration without loosening the rear

---

# Task 4: Distinguish useful checks from empty checks

## 4.1 Define categories of useful checks

- [x] Classify checking moves into:
  - [x] mating-net checks
  - [x] forcing checks that win material
  - [x] driving checks that worsen king safety
  - [x] simplifying checks that lead to favorable trades
  - [x] empty checks that only repeat

## 4.2 Add check-quality scoring

- [x] Add logic that rewards checks more when they:
  - [x] shrink the king’s safe area
  - [x] drive the king away from defenders
  - [x] improve attack geometry for the next move
  - [x] expose tactical follow-ups
- [x] Downgrade checks when they:
  - [x] preserve the same king box
  - [x] can be met by easy king shuffles
  - [x] surrender centralization or defensive control

## 4.3 Apply check quality in ordering and search

- [x] Use check quality in quiet/tactical move ordering.
- [x] Ensure strong forcing checks still search early.
- [x] Prevent empty checks from dominating root choice just because they check.

---

# Task 5: Improve defensive coordination and “must-answer” logic

## 5.1 Model defensive priorities

- [x] Define a defense-first model for positions under pressure.
- [x] Include at least:
  - [x] covering entry squares
  - [x] contesting attack files/ranks
  - [x] reconnecting defenders
  - [x] creating luft
  - [x] trading the attacker’s most dangerous piece

## 5.2 Reward stabilizing defensive moves

- [x] Reward moves that:
  - [x] close or contest a file aimed at the king
  - [x] block queen/rook invasion routes
  - [x] add a defender to the king zone
  - [x] trade off the attacker’s strongest heavy piece
  - [x] restore back-rank safety

## 5.3 Penalize negligent counterplay

- [x] Penalize moves that seek activity while:
  - [x] mate threats remain unresolved
  - [x] the back rank is weak
  - [x] the queen/rook is disconnected from king defense
  - [x] an invasion square is left uncontrolled
  - [x] the king has fewer safe squares after the move

## 5.4 Add defensive regression tests

- [x] Add tests where the engine should:
  - [x] defend instead of check
  - [x] make luft instead of pawn grabbing
  - [x] trade queens or rooks to reduce danger
  - [x] hold a file rather than start a side attack

---

# Task 6: Improve development and opening sanity

## 6.1 Reward healthier early development

- [x] Strengthen early-game preferences for:
  - [x] minor-piece development
  - [x] central control
  - [x] castling readiness
  - [x] piece coordination
  - [x] avoiding repeated queen moves

## 6.2 Penalize premature heavy-piece wandering

- [x] Penalize:
  - [x] early queen moves without concrete gain
  - [x] rook lifts before development is complete
  - [x] flank raids that ignore king safety
  - [x] repeated movement of one piece while others sleep

## 6.3 Add opening regression tests

- [x] Add tests that prefer:
  - [x] developing a knight/bishop over an early queen sortie
  - [x] castling-support moves over speculative queen checks
  - [x] sensible recapture/development over showy queen pressure

---

# Task 7: Extend search support for king attacks and defense

## 7.1 Add selective search help in dangerous positions

- [x] Decide where to extend search when kings are exposed.
- [x] Consider extensions for:
  - [x] forcing checks near exposed kings
  - [x] recaptures that open files toward a king
  - [x] queen/rook invasions on the 7th or 8th rank
  - [x] mate-threat replies
  - [x] only-move defensive resources

## 7.2 Keep extensions bounded and explainable

- [x] Ensure extensions are:
  - [x] structurally limited
  - [x] testable
  - [x] not applied to empty checks or fake attacks
  - [x] not causing large practical regressions at depth 5

## 7.3 Improve root-choice stability in tactical positions

- [x] Ensure root move selection prefers:
  - [x] stable attacking moves with follow-up
  - [x] stable defensive moves that eliminate threats
  - [x] non-repeating tactical lines with genuine payoff

---

# Task 8: Integrate the new signals safely

## 8.1 Decide where each signal belongs

- [x] Audit whether each new heuristic belongs in:
  - [x] static evaluation
  - [x] quiet move ordering
  - [x] tactical move ordering
  - [x] quiescence
  - [x] root tie-break logic
  - [x] selective extensions

## 8.2 Avoid double-counting

- [x] Ensure king danger, attack quality, and check quality do not all reward the same idea three times.
- [x] Keep the implementation explainable in code comments and breakdown output.

## 8.3 Preserve existing STRATEGY2 gains

- [x] Ensure the new logic does not undo:
  - [x] anti-repetition behavior
  - [x] progress-aware conversion
  - [x] trade-when-ahead improvements
  - [x] blockade and luft ordering

---

# Task 9: Measure whether the engine actually improved

## 9.1 Re-run self-play

- [x] Run at least one fresh depth-3 vs depth-3 self-play game.
- [x] Run at least one fresh depth-5 vs depth-5 self-play game if practical.
- [x] Save transcripts under `tmp/` or `docs/` as appropriate.
- [x] Compare them with earlier STRATEGY2 games.

## 9.2 Review outcome quality

- [x] Check whether the new games show:
  - [x] fewer reckless queen raids
  - [x] fewer unsafe king walks
  - [x] more defense-first choices under pressure
  - [x] fewer empty checks
  - [x] better development in the opening
  - [x] better coordination of attack and defense

## 9.3 Re-check performance

- [x] Re-run the depth-5 search benchmark.
- [x] Ensure the new logic does not materially damage current search practicality.
- [x] If performance regresses, note which heuristics or extensions caused it.

---

# Task 10: Final acceptance

## 10.1 Correctness target

- [x] `pylint chess_game` passes
- [x] `python -m pytest tests -q` passes

## 10.2 Strategic-quality target

- [x] The engine distinguishes useful checks from empty checks in targeted tests.
- [x] The engine avoids unsupported queen raids in targeted tests.
- [x] The engine chooses defense-first moves when king danger is urgent.
- [x] The engine values development and king safety more sanely in the opening.
- [x] Self-play shows fewer king walks into heavy-piece pressure.

## 10.3 Performance target

- [x] Depth-5 remains practical after the new logic.
- [x] Tactical extensions stay bounded and do not explode search cost.

---

## Deferred work

- Opening-book work remains deferred.
- Larger-scale selective pruning/search selectivity work remains deferred to `docs/SELECTIVE_PRUNING.md`.
- Full opening-theory behavior remains deferred; this pass is about safer, more purposeful play rather than formal opening preparation.
