# STRATEGY3 TOOD

## Goal

Make the engine play **higher-quality human-style chess** by improving:

- **prophylaxis**
- **pawn-structure discipline**
- **piece coordination**
- **plan recognition**
- **counterplay suppression**
- **selective search quality**
- **technical endgame conversion**

This pass should build on `docs/STRATEGY1_TODO.md`, `docs/STRATEGY2_TODO.md`, and `docs/STRATEGY3_TODO.md`, not replace them. The intent here is to reduce the remaining “engine-ish” failure mode: the engine can now avoid many fake attacks, but it still does not consistently choose the kind of **restraining, improving, plan-driven moves** that strong human players prefer.

---

## Scope rules

- Keep legal move generation and board-rule correctness unchanged unless a new AI regression exposes a direct engine bug.
- Preserve the public `Board` API where possible.
- Prefer structural evaluation and search improvements over move-specific hacks.
- Do not fake “human style” with randomness.
- Use targeted tests to define what good human-style play means in concrete positions.
- Every major phase must end with:

  ```bash
  pylint chess_game
  python -m pytest tests -q
  ```

- For AI-heavy phases, also run targeted checks such as:

  ```bash
  python -m pytest tests/test_ai.py tests/test_ai_quality.py tests/test_ai_search.py tests/test_alpha_beta_pruning.py -q
  ```

- When a phase changes search behavior materially, also review at least one saved self-play transcript under `tmp/`.

---

# Task 0: Re-establish the “human-style quality” baseline

## 0.1 Record the new failure pattern

- [x] Review the latest depth-5 self-play transcript in `tmp/game2605211902_1_w5b5.md`.
- [x] Note:
  - [x] final result
  - [x] move count
  - [x] first moment one side chose activity over prophylaxis
  - [x] first moment one side damaged its own pawn shelter unnecessarily
  - [x] first moment one side failed to suppress obvious counterplay
  - [x] transition point where one side got an easier human-style plan than the other
  - [x] final technical sequence that converted the advantage

Baseline note: `tmp/game2605211902_1_w5b5.md` ended in a **threefold-repetition draw on move 204** after Black failed to convert a winning rook-and-bishop endgame. White's kingside started to loosen with `17. h3`, then `19. gxf3` created the long-term shelter damage Black later exploited. Black obtained the easier technical plan by the late middlegame/endgame transition, but instead of suppressing counterplay and converting, it repeated the checking loop `...Rg2`, `...Rg3`, `...Rg2`, allowing the draw.

## 0.2 Build baseline “good human move” positions

- [x] Create hand-built positions where a strong human would choose a calm improving move.
- [x] Include positions covering:
  - [x] prophylaxis before attack
  - [x] king-shelter preservation over pawn grabbing
  - [x] improving the worst-placed piece
  - [x] restraining enemy counterplay before pushing one’s own plan
  - [x] centralizing toward a long-term target rather than chasing tactics
  - [x] making a useful waiting move that keeps the plan intact
- [x] Record current `evaluate()` and `get_best_move()` behavior for each.

## 0.3 Build baseline “bad human move” positions

- [x] Create positions where the engine currently likes a move a strong human would distrust.
- [x] Include cases such as:
  - [x] premature pawn storm near own king
  - [x] voluntary king-shelter damage for no concrete gain
  - [x] grabbing a pawn while conceding an invasion file
  - [x] moving the same heavy piece again instead of completing coordination
  - [x] forcing line that improves nothing after the dust settles
  - [x] playing for activity while ignoring the opponent’s only source of counterplay
- [x] Record whether the engine overrates the flashy move.

## 0.4 Build baseline “plan recognition” positions

- [x] Create positions where the right move follows from the pawn structure and piece placement.
- [x] Include cases such as:
  - [x] minority attack vs central restraint
  - [x] opposite-side castling with race-vs-restraint decisions
  - [x] closed center where piece maneuvering matters more than immediate tactics
  - [x] IQP-style positions where blockading and exchanges matter
  - [x] hanging-pawn or backward-pawn structures with clear target squares
- [x] Record current move choice and whether it fits the structure.

Baseline artifact: `tmp/strategy4_baseline_positions.txt` records the latest self-play failure analysis plus the hand-built good-move, bad-move, and plan-recognition baseline positions together with current `evaluate()` and `get_best_move()` outputs.

---

# Task 1: Add regression tests for prophylaxis and self-restraint

## 1.1 Add “stop the opponent first” tests

- [x] Add tests where the best move is prophylactic rather than active.
- [x] Cover cases such as:
  - [x] stopping a file invasion before attacking elsewhere
  - [x] preventing a knight outpost before launching a pawn advance
  - [x] controlling a key entry square before checking
  - [x] creating luft before starting an attack
  - [x] exchanging the opponent’s most active piece before improving one’s own attack

Phase note: Task 1.1 coverage now spans `tests/test_ai_strategy4_regressions.py` plus the earlier defense-first suites: sealing an invasion file and preventing a knight outpost are now explicit STRATEGY4 regressions, while `tests/test_ai_defensive_strategy.py` and `tests/test_ai_quality.py` already lock in the luft-first and active-piece-exchange prophylaxis cases.

## 1.2 Add “do not self-weaken” tests

- [x] Add tests where the engine must reject self-inflicted weaknesses.
- [x] Cover cases such as:
  - [x] `h`-pawn push that weakens the king for no reason
  - [x] `g`-pawn recapture that opens the king without compensation
  - [x] flank pawn grab that abandons the center
  - [x] rook lift that abandons back-rank safety
  - [x] king move that disconnects defenders in a middlegame

Phase note: `tests/test_ai_strategy4_regressions.py` now covers the full Task 1.2 self-weakening set: early castled-king `h`-pawn loosening, `g`-pawn king opening, flank queen sorties that abandon central tension, rook lifts that drop back-rank safety, and middlegame king drift away from its defenders.

## 1.3 Add “quiet improvement beats cosmetic activity” tests

- [x] Add tests where human-style piece improvement should win.
- [x] Cover cases such as:
  - [x] worst-piece improvement over repeated pressure move
  - [x] rook centralization over a harmless side check
  - [x] defender regrouping over a speculative pawn thrust
  - [x] central king improvement in safe endings over pointless checking
  - [x] bishop reroute to a long diagonal over a loose tactical poke

Phase note: Task 1.3 coverage now spans `tests/test_ai_strategy4_regressions.py` plus the earlier activity/defense suites: repeated queen-pressure moves lose to worst-piece improvement, rook centralization beats side checks, defender regrouping beats speculative drifting, winning endings prefer king centralization, and bishop reroutes beat loose queen pokes.

## 1.4 Add “counterplay suppression first” tests

- [x] Add tests where a side with the advantage must first kill counterplay.
- [x] Cover cases such as:
  - [x] blockading the only enemy passer
  - [x] cutting off rook checking distance
  - [x] closing the only open file near one’s king
  - [x] exchanging the enemy active queen before pushing a passer
  - [x] choosing king safety over immediate material gain

Phase note: Task 1.4 is covered by the existing STRATEGY3/4 quality suites: `tests/test_ai_quality.py` locks in blockade-first and rook-cutoff progress choices, `tests/test_ai_defensive_strategy.py` locks in file-closing, queen-trade, and king-safety-over-material behavior, and `tests/test_ai_strategy4_regressions.py` now includes the complementary prophylaxis cases from Task 1.1.

---

# Task 2: Strengthen pawn-structure discipline

## 2.1 Expand pawn-structure evaluation

- [x] Add or refine evaluation terms for:
  - [x] backward pawns
  - [x] weak dark/light square complexes
  - [x] overextended pawn chains
  - [x] loose pawn advances around castled kings
  - [x] fixed pawn targets that a strong human would exploit
  - [x] pawn breaks that are only good when pieces are ready

## 2.2 Penalize needless king-shelter damage more sharply

- [x] Increase penalties when a side:
  - [x] advances `g`/`h` pawns without a real attack
  - [x] opens files around its king while queens remain
  - [x] creates long-term holes near king shelter
  - [x] accepts a pawn structure that makes piece defense harder
- [x] Scale penalties down appropriately in true endings.

## 2.3 Reward human-style pawn restraint

- [x] Reward:
  - [x] keeping a healthy shelter when no attack exists
  - [x] preserving central tension when a break is premature
  - [x] preparing a pawn break with pieces first
  - [x] maintaining flexible pawn structure instead of fixing weaknesses too early

## 2.4 Add pawn-structure regression tests

- [x] Add tests that prefer:
  - [x] stable shelter over speculative pawn pushes
  - [x] prepared breaks over immediate breaks
  - [x] central integrity over side pawn grabs
  - [x] restraining enemy breaks over mirror-image drifting

Phase note: Task 2 is now complete. The pawn-structure evaluator covers loose castled-king shelter advances, queen-sensitive castled-king file gaps, same-color kingside hole complexes, overextended connected chains, backward pawns, fixed targets versus flexible structures, prepared breaks, preserved central tension, and restraining enemy pawn breaks instead of drifting. `tests/test_ai_strategy4_regressions.py` now locks in stable shelter, castled-king file-gap restraint, same-color hole-complex discipline, central integrity, backward-pawn weakness, fixed-target restraint, overextended-chain discipline, prepared-break timing, central-tension restraint, and enemy-break clamping.

---

# Task 3: Improve piece coordination and piece-improvement logic

## 3.1 Define a “worst piece” model

- [x] Decide how to identify the current worst-placed piece.
- [x] Include signals such as:
  - [x] low mobility
  - [x] poor coordination with friendly pieces
  - [x] distance from the relevant theater of play
  - [x] blocked lines
  - [x] defensive overload or misplacement

## 3.2 Reward moves that improve the worst piece

- [x] Reward:
  - [x] rook moves to useful central files
  - [x] bishop reroutes to active diagonals
  - [x] knight maneuvers toward outposts
  - [x] queen repositioning that supports the whole position
  - [x] king centralization in safe technical endings

## 3.3 Penalize repeated movement without plan gain

- [x] Penalize:
  - [x] moving the same heavy piece repeatedly in quiet positions
  - [x] re-aiming an attacker without increasing pressure
  - [x] piece shuffles that preserve identical geometry
  - [x] reroutes that abandon a key defensive responsibility

## 3.4 Add coordination regression tests

- [x] Add tests where the engine should:
  - [x] improve the worst rook instead of check
  - [x] reconnect rooks before starting a side plan
  - [x] bring a bishop to the long diagonal before pawn racing
  - [x] centralize a queen only when it improves team coordination

Phase note: The first Task 3 slice extracts piece-coordination heuristics into `chess_game/chess/piece_coordination.py`, replacing the old center-distance-only worst-piece check with a placement profile that accounts for mobility, coordination, theater distance, blocked lines, and king-side overload. `tests/test_ai_activity_strategy.py` now locks in worst-rook improvement, rook reconnection, bishop long-diagonal reroutes, and queen centralization only when it actually improves coordination.

Task 3 note: The remaining Task 3 bullets are now covered as well. `tests/test_ai_activity_strategy.py` adds the explicit knight-to-outpost maneuver regression and already covered repeated heavy-piece shuffles, no-plan re-aiming, and defensive-responsibility abandonment; `tests/test_ai_quality.py` already locks in safe-endgame king centralization. Task 3 is complete.

- [x] Task 3 complete

---

# Task 4: Teach stronger opponent-threat recognition and prophylaxis

## 4.1 Model the opponent’s next plan

- [x] Add logic that identifies the opponent’s most dangerous near-term plan.
- [x] Include threats such as:
  - [x] file or rank invasions
  - [x] knight jumps into weak squares
  - [x] pawn breaks that open lines toward the king
  - [x] perpetual-check resources
  - [x] passed-pawn activation

## 4.2 Reward prophylactic moves explicitly

- [x] Reward moves that:
  - [x] take away entry squares
  - [x] reduce tactical targets
  - [x] improve defensive flexibility
  - [x] prevent an enemy break before it happens
  - [x] force the opponent into a lower-quality plan

## 4.3 Penalize “my move only” thinking

- [x] Penalize moves that:
  - [x] improve one’s own activity but allow a stronger enemy reply
  - [x] ignore the opponent’s only counterplay source
  - [x] create new hooks or targets around the king
  - [x] open a line the opponent can use better

## 4.4 Add prophylaxis tests

- [x] Add tests where the engine must:
  - [x] stop a break before improving a piece
  - [x] prevent an invasion before pawn winning
  - [x] deny counterplay before converting material
  - [x] choose a human waiting move that improves flexibility

Phase note: Task 4 is now complete. The new `chess_game/chess/opponent_plans.py` profile gives quiet ordering an explicit model of enemy invasion lines, knight jumps, central pawn breaks, checking resources, and passed-pawn pushes. The remaining prophylaxis bullets are covered by the existing STRATEGY3/4 regression set: `tests/test_ai_defensive_strategy.py` locks in queen trades that reduce king danger plus the new break-stopping case, `tests/test_ai_quality.py` locks in blockade-first conversion and useful waiting/luft moves, and `tests/test_ai_strategy4_regressions.py` plus `tests/test_ai_activity_strategy.py` lock in invasion-file defense and punishment for self-weakening king-side drifts.

- [x] Task 4 complete

---

# Task 5: Improve structure-based plan recognition

## 5.1 Group positions by pawn structure

- [ ] Introduce lightweight structure recognition helpers for:
  - [ ] open center
  - [ ] closed center
  - [ ] isolated queen pawn
  - [ ] hanging pawns
  - [ ] opposite-side castling
  - [ ] rook endgames with outside passer / protected passer

## 5.2 Attach structure-appropriate preferences

- [ ] In open centers, prefer:
  - [ ] development lead
  - [ ] open-line control
  - [ ] king safety before flank attacks
- [ ] In closed centers, prefer:
  - [ ] piece maneuvers
  - [ ] useful breaks
  - [ ] restraint before wing expansion
- [ ] In IQP/hanging-pawn structures, prefer:
  - [ ] blockade squares
  - [ ] favorable exchanges
  - [ ] piece pressure on structural targets

## 5.3 Avoid plan mismatch

- [ ] Penalize moves that:
  - [ ] start a flank race in an open center without support
  - [ ] exchange the wrong minor pieces for the structure
  - [ ] push the wrong pawn break too early
  - [ ] chase tactics while ignoring the correct strategic plan

## 5.4 Add structure-plan regression tests

- [ ] Add tests that prefer:
  - [ ] blockading an IQP over aimless centralization
  - [ ] preparing a minority attack instead of a random pawn lunge
  - [ ] maneuvering in a closed center instead of forcing empty tactics
  - [ ] open-file occupation in open positions over side checks

---

# Task 6: Refine move ordering for human-style candidate quality

## 6.1 Improve quiet candidate ordering

- [ ] Push these moves earlier:
  - [ ] prophylactic moves
  - [ ] worst-piece improvements
  - [ ] moves that suppress counterplay
  - [ ] simplifying moves when clearly favorable
  - [ ] structure-consistent plan moves

## 6.2 Push suspicious humanly-bad candidates later

- [ ] Push these moves later:
  - [ ] shelter-loosening pawn moves
  - [ ] repeated heavy-piece shuffles
  - [ ] speculative checks with easy replies
  - [ ] pawn grabs that concede files or diagonals
  - [ ] king moves that worsen coordination in middlegames

## 6.3 Improve root tie-break quality

- [ ] Prefer root moves that:
  - [ ] leave fewer strategic weaknesses
  - [ ] reduce the opponent’s practical options
  - [ ] maintain plan continuity
  - [ ] improve structure while keeping tactical stability

## 6.4 Add ordering regressions

- [ ] Add tests where ordering should prefer:
  - [ ] prophylaxis over cosmetic activity
  - [ ] safer simplification over speculative gain
  - [ ] coordinated improvements over solo-piece heroics
  - [ ] suppression of counterplay over a second-best attack

---

# Task 7: Improve selective search for human-relevant lines

## 7.1 Extend lines that matter strategically

- [ ] Consider bounded extensions for:
  - [ ] forced defensive resources
  - [ ] moves that open or close king files
  - [ ] recaptures that change structure near the king
  - [ ] simplifying trades into favorable technical endings
  - [ ] only-move prophylactic resources

## 7.2 Avoid wasting search on empty forcing moves

- [ ] Reduce priority for:
  - [ ] harmless checks
  - [ ] repeated tactical geometry with no payoff
  - [ ] speculative captures that worsen structure
  - [ ] side threats that ignore the center or king safety

## 7.3 Improve quiescence quality

- [ ] Make quiescence more selective about:
  - [ ] which captures are actually stabilizing
  - [ ] which recaptures matter for king shelter
  - [ ] which checks change the evaluation materially
  - [ ] when structural changes deserve follow-up

## 7.4 Add search regressions

- [ ] Add tests where search should:
  - [ ] see that a prophylactic line is best
  - [ ] prefer a clean simplifying line over repeated checking
  - [ ] reject a material win that opens fatal counterplay
  - [ ] search deeper in structure-changing defensive moments

---

# Task 8: Improve opening play without building a full opening book

## 8.1 Strengthen opening-principle heuristics

- [ ] Further reward:
  - [ ] fast development
  - [ ] central control
  - [ ] safe castling
  - [ ] piece harmony
  - [ ] keeping multiple plans available

## 8.2 Penalize non-human opening habits

- [ ] Penalize:
  - [ ] repeated queen moves
  - [ ] flank pawn pokes without a center or king-safety reason
  - [ ] rook wandering before the minor pieces are coordinated
  - [ ] exchanging helpful developing pieces for no structural reason

## 8.3 Add opening-plan tests

- [ ] Add tests that prefer:
  - [ ] completing development over pawn raids
  - [ ] castling over speculative initiative
  - [ ] central recapture over side pressure
  - [ ] preserving structure over low-value activity

## 8.4 Optional lightweight opening guidance

- [ ] Evaluate whether a small non-random opening preference table would help.
- [ ] If added:
  - [ ] keep it explainable
  - [ ] keep it small
  - [ ] avoid conflicting with legal/evaluation logic
  - [ ] cover only very early move-order sanity

---

# Task 9: Improve technical endgame play

## 9.1 Strengthen endgame “conversion first” logic

- [ ] Reward:
  - [ ] king activation
  - [ ] rook activity behind or behind-against passers
  - [ ] cutting off the enemy king
  - [ ] liquidation into trivially won endings
  - [ ] keeping the opponent tied down to defense

## 9.2 Add explicit rook-endgame guidance

- [ ] Improve heuristics for:
  - [ ] checking distance
  - [ ] Lucena-like winning setup ideas
  - [ ] avoiding passive rook placement
  - [ ] outside passers and rook activity balance
  - [ ] defending from the correct side when worse

## 9.3 Avoid unnecessary counterplay when winning

- [ ] Penalize:
  - [ ] chasing side pawns while allowing active checks
  - [ ] pawn pushes that release the enemy king
  - [ ] king drift that reopens perpetual resources
  - [ ] refusing simplifying trades when the ending is easy

## 9.4 Add endgame regressions

- [ ] Add tests where the engine should:
  - [ ] reduce counterplay before pawn racing
  - [ ] improve king and rook placement before checking
  - [ ] choose a simpler win over a messier stronger-looking line
  - [ ] defend accurately when worse instead of drifting

---

# Task 10: Build a stronger review and comparison loop

## 10.1 Save and classify bad self-play decisions

- [ ] After each major phase, review fresh self-play transcripts.
- [ ] For each poor move, classify it as:
  - [ ] king-safety failure
  - [ ] pawn-structure failure
  - [ ] prophylaxis failure
  - [ ] plan-recognition failure
  - [ ] search-selectivity failure
  - [ ] technical endgame failure

## 10.2 Turn reviewed failures into permanent regressions

- [ ] Add a regression test for every recurring category.
- [ ] Prefer one precise test over one vague aggregate test.
- [ ] Keep a running list of “humanly embarrassing” failures that must not return.

## 10.3 Compare against stronger move choices

- [ ] For selected critical positions, compare engine moves against a stronger reference engine or curated human judgment.
- [ ] Record:
  - [ ] chosen move
  - [ ] expected human move
  - [ ] strategic reason for the difference
  - [ ] whether the miss is evaluation- or search-driven

## 10.4 Keep the review loop explainable

- [ ] Document the final cause of each fixed failure in code comments or tracker notes.
- [ ] Avoid adding opaque bonuses that cannot be justified from the position.

---

# Task 11: Final acceptance

## 11.1 Correctness target

- [ ] `pylint chess_game` passes
- [ ] `python -m pytest tests -q` passes

## 11.2 Human-style quality target

- [ ] The engine prefers prophylaxis over empty activity in targeted tests.
- [ ] The engine avoids damaging its own king shelter without compensation.
- [ ] The engine improves the worst piece more consistently in quiet positions.
- [ ] The engine suppresses the opponent’s main counterplay before converting.
- [ ] The engine follows pawn-structure-appropriate plans more often in regression suites.
- [ ] Self-play shows fewer self-inflicted pawn weaknesses and fewer planless shuffles.

## 11.3 Practicality target

- [ ] Depth-5 remains practical after the new logic.
- [ ] Selective search improvements stay bounded.
- [ ] New positional heuristics do not cause broad tactical blindness.

---

## Deferred work

- Full opening-book implementation remains deferred.
- Neural-network evaluation remains deferred.
- Large-scale automated tuning remains deferred unless hand-authored heuristics plateau.
- Time-management improvements for tournament play remain deferred; this pass is about better move quality, not clock usage.
