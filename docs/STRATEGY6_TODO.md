# STRATEGY6 TODO

## Goal

Make the engine play **more principled, practical chess from the opening through conversion** by improving:

- **opening discipline and development order**
- **king-safety urgency before and during castling**
- **quiet move selection in strategically simple positions**
- **practical tactical transitions after opening mistakes**
- **cleaner conversion once materially ahead**
- **transcript-driven review coverage for recurring embarrassing moves**

This pass should build on `docs/STRATEGY1_TODO.md` through `docs/STRATEGY5_TODO.md`, not replace them. The latest self-play game in `tmp/self_play_w3b3.txt` shows that the engine no longer mainly loses on legality or obvious one-move blunders. The remaining weakness is that it still drifts into **slow side play, delayed king safety, low-value rook maneuvers, and uneven practical conversion**.

---

## Scope rules

- Keep legal move generation and board-rule correctness unchanged unless a new regression exposes a direct bug.
- Preserve the public `Board` API where possible.
- Prefer structural evaluation, move ordering, search, and review-loop improvements over hard-coded move bans.
- Do not fake stronger play with randomness.
- Do not weaken tactical correctness just to get cleaner-looking openings.
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

# Task 0: Re-establish the post-STRATEGY5 baseline

## 0.1 Review the latest self-play game

- [x] Review `tmp/self_play_w3b3.txt`.
- [ ] Record:
  - [x] final result
  - [x] move count
  - [x] first clearly dubious White opening move
  - [x] first clearly dubious Black opening move
  - [x] first point where White’s king safety lag became serious
  - [x] first point where Black obtained the easier practical game
  - [x] first point where White still had a better human plan than the engine chose
  - [x] first point where the winning side began converting inefficiently

## 0.2 Extract concrete bad-move examples

- [x] Create a baseline artifact under `tmp/` summarizing the game’s worst decisions.
- [ ] Include at least:
  - [x] White’s early `Rc1` / rook drift before king safety
  - [x] White’s `h4` flank push before the position justified it
  - [x] Black’s `...Nh6` development mistake
  - [x] White’s late practical collapse after active queen play
  - [x] Black’s inefficient but successful final conversion

## 0.3 Build transcript-backed positions

- [x] Reconstruct hand-built test positions for:
  - [x] early rook sidestep before castling
  - [x] premature flank pawn expansion
  - [x] rim-knight development vs central development
  - [x] practical simplification vs flashy continuation
  - [x] winning endgame conversion with passed pawns / mating net potential
- [x] Record current `evaluate()` and `get_best_move()` behavior for each.

## 0.4 Define success metrics for STRATEGY6

- [x] Decide practical success criteria such as:
  - [x] fewer early rook moves before castling / coordination
  - [x] fewer premature flank pawn pushes
  - [x] fewer rim-knight opening choices
  - [x] more consistent castling and development order
  - [x] cleaner conversion once materially or positionally winning

Phase note: Task 0 is complete. The current baseline artifact lives in `tmp/strategy6_baseline_positions.txt`. The key reproduced failures are White's early `Rc1` rook drift, White's premature `h4` before king safety, Black's `...Nh6` rim development, White's later collapse once Black reached the easier practical game, and Black's still-inefficient but successful conversion. The transcript-backed probe positions also show that the current depth-3 engine still recommends `a1c1`, `h2h4`, and `g8h6` directly from reconstructed STRATEGY6 baseline positions, which gives the next opening-discipline phases precise targets.

---

# Task 1: Add transcript-driven opening-discipline regressions

## 1.1 Add early rook-drift regressions

- [x] Add tests where the engine should reject early rook moves that do not solve a real problem.
- [x] Cover cases such as:
  - [x] `Ra1-c1` before castling
  - [x] `Ra1-b1` / `Rh1-g1` before coordination is complete
  - [x] rook sidesteps on the home rank that do not contest the center or improve safety

## 1.2 Add premature flank-play regressions

- [x] Add tests where the engine should prefer development / castling over side pawn pushes.
- [x] Cover cases such as:
  - [x] `h2h4` before king safety is resolved
  - [x] `a`-pawn / `h`-pawn pushes that do not win space with a concrete follow-up
  - [x] kingside pawn loosening while queens and major pieces remain on the board

## 1.3 Add bad knight-development regressions

- [x] Add tests where the engine should prefer central development over rim development.
- [x] Cover cases such as:
  - [x] `...Nh6` vs `...Nf6`
  - [x] knight hops to the edge that do not support a concrete tactical idea
  - [x] development choices that delay castling or central control

## 1.4 Add “finish development first” regressions

- [x] Add tests where the engine should complete natural development before low-value side moves.
- [x] Cover cases such as:
  - [x] bishop development before rook drift
  - [x] castling before flank expansion
  - [x] central pawn support / recapture before decorative rook activity

Phase note: Task 1 is complete. `tests/test_ai_strategy6_regressions.py` now adds exact transcript-backed regressions for the move-11 `Rc1` rook drift, the move-15 `h4` flank lunge, and the `...Nh6` rim-knight choice, while the earlier STRATEGY5 opening suite continues to cover the companion `Ra1-b1` / `Rh1-g1`, castling-before-flank-expansion, and central-recapture-before-side-play cases. The supporting opening heuristics were tightened in `opening_development.py`, `opening_move_ordering.py`, and `evaluation.py` so those transcript positions now score home-rank rook drift, unsettled kingside pawn lunges, and early rim-knight development more harshly instead of letting rook-activity or shallow structure bonuses mask them.

---

# Task 2: Strengthen opening evaluation

## 2.1 Audit current opening scoring

- [x] Review current opening-related terms in:
  - [x] `chess_game/chess/evaluation.py`
  - [x] `chess_game/chess/opening_development.py`
  - [x] `chess_game/chess/opening_guidance.py`
  - [x] `chess_game/chess/opening_move_ordering.py`
- [x] Document:
  - [x] which opening terms dominate too early
  - [x] which penalties are too weak
  - [x] where move-order signals and eval signals disagree

## 2.2 Increase penalties for non-developing rook moves

- [x] Penalize home-rank rook sidesteps more precisely when:
  - [x] the king is uncastled
  - [x] minor-piece development is incomplete
  - [x] queens are still on the board
  - [x] the rook move does not improve pressure, defense, or connection

## 2.3 Increase penalties for premature shelter-loosening pawn moves

- [x] Penalize flank pawn pushes more sharply when they:
  - [x] loosen castling structure
  - [x] do not fight for the center
  - [x] do not prepare a concrete development scheme
  - [x] do not answer an opponent threat

## 2.4 Improve knight-development scoring

- [x] Reward:
  - [x] central knight development
  - [x] development that supports castling and center control
  - [x] development that increases practical tactical coverage
- [x] Penalize:
  - [x] rim development without concrete justification
  - [x] knight moves that increase coordination lag

## 2.5 Tighten “finish development before side play” scoring

- [x] Increase bonuses for:
  - [x] completing both minor pieces
  - [x] bishop activation before rook drift
  - [x] on-time castling
  - [x] natural central pawn support
- [x] Reduce credit for:
  - [x] one-purpose side-space grabs
  - [x] pretty-looking but non-forcing rook or queen placements

Phase note: Task 2 is complete. The audit artifact lives in `tmp/strategy6_task2_audit.txt`. The main findings were that opening-guidance pressure shut off too early in the late-opening transcript positions, flank-pawn penalties became too weak once only one minor remained undeveloped, and the remaining `...Nh6` miss had become a move-order/root-choice disagreement more than a missing static penalty. The Task 2 evaluation pass therefore tightened late-opening edge-pawn drift, unsettled kingside pawn lunges, decorative home-rank rook sidesteps, and rim-knight penalties inside `opening_development.py` / `evaluation.py`, which was enough to replace the old White fallback with `g2g3` in the baseline `Rc1` line while preserving the depth-5 timing guard.

---

# Task 3: Improve opening move ordering and practical quiet choices

## 3.1 Audit quiet opening ordering

- [x] Review how quiet move ordering currently prioritizes:
  - [x] minor development
  - [x] castling
  - [x] central recaptures / central support
  - [x] rook shifts
  - [x] flank pawn moves

## 3.2 Make development bundles score higher

- [x] Prefer moves that simultaneously:
  - [x] develop a piece
  - [x] improve king safety
  - [x] reinforce the center
  - [x] prepare the next natural developing move

## 3.3 Demote low-information quiet moves

- [x] Push down quiet moves that:
  - [x] only gain side space
  - [x] do not change the main tactical or strategic question
  - [x] recycle pressure on the same harmless square
  - [x] move a rook without a forcing reason

## 3.4 Improve tie-break quality in simple openings

- [x] Prefer moves that:
  - [x] keep castling options intact
  - [x] preserve pawn shelter
  - [x] reduce future coordination debt
  - [x] avoid creating long-term weaknesses for one tempo of cosmetic activity

Phase note: Task 3 is complete. The Task 2 audit showed that the remaining `...Nh6` issue was no longer a missing static penalty but a root-choice disagreement once deeper search scores came back close. This phase therefore kept the existing opening move-order penalties, then fed `opening_discipline_order_score()` into the root tiebreak path in `ai_search_helpers.py`, so near-equal depth-3 opening choices now keep the healthier plan instead of drifting into cosmetically active but strategically worse moves. The result is that the late-opening White baseline now prefers `g2g3` over `a`-pawn drift, and the Black baseline line now chooses `...Be6` instead of `...Nh6`, while the depth-5 timing guard remains green.

---

# Task 4: Strengthen king-safety urgency before castling

## 4.1 Add regressions for delayed king safety

- [x] Add tests where the engine should castle or secure the king before slow side play.
- [x] Cover cases such as:
  - [x] uncastled king with queens on the board
  - [x] rook move vs castling
  - [x] flank pawn push vs castling
  - [x] quiet bishop retreat vs king safety

## 4.2 Improve evaluation-side king urgency

- [x] Increase penalties when:
  - [x] the king stays central while development lags
  - [x] castling rights are abandoned without compensation
  - [x] the pawn shell is loosened before safety is fixed
  - [x] long-range enemy pieces can exploit open files / diagonals soon

## 4.3 Improve move-order king urgency

- [x] Prefer moves that:
  - [x] castle
  - [x] preserve castling rights
  - [x] repair shelter
  - [x] remove immediate pressure on the king zone
- [x] Demote moves that:
  - [x] postpone king safety without gaining a concrete tactical concession
  - [x] make future castling worse

Phase note: Task 4 is complete. This phase added transcript-backed and balanced-shell regressions proving that castling outranks slow bishop, rook, flank-pawn, and king-walk choices when queens remain on the board, then tightened `opening_development.py`, `evaluation.py`, and `opening_move_ordering.py` so central home-rank kings, abandoned castling rights, loosened pre-castling shelter, and even post-castling `...Nh6`-style rim-knight shortcuts stay structurally penalized. The result is that the transcript late-opening test now castles on time, the balanced-shell regressions prefer castling over `Kf1` / rook drift / bishop retreat / `h4`, and the earlier Task 3 `...Nh6` rejection remains green after the king-safety work.

---

# Task 5: Improve tactical sanity after strategic opening mistakes

## 5.1 Review the critical tactical transition in the transcript

- [x] Audit the phase around:
  - [x] `...f5`
  - [x] `...fxe4`
  - [x] the knight exchanges on `d4`
  - [x] the queen trade / infiltration sequence

## 5.2 Add regressions for practical tactical choices

- [x] Add tests where the engine should prefer:
  - [x] clean central recaptures
  - [x] safe simplification into a better structure
  - [x] tactical lines that keep the king safer
  - [x] tactical wins that preserve conversion clarity

## 5.3 Reduce flashy-but-fragile continuations

- [x] Demote tactical choices that:
  - [x] win a tempo but worsen king safety
  - [x] preserve material equality while losing structure and coordination
  - [x] chase a piece instead of fixing the main weakness
  - [x] create practical counterplay for no compensation

## 5.4 Improve tactical transition scoring if needed

- [x] If current logic is too scattered, extract a shared helper/module for:
  - [x] practical simplification bonuses
  - [x] king-safe tactical transition bonuses
  - [x] “win the right pawn / piece, not just any active move” tie-breaks

Phase note: Task 5 is complete. The transcript audit in `tmp/strategy6_task5_audit.txt` showed that the central sequence itself (`...f5`, `...fxe4`, `...cxd4`) was mostly fine, but deeper search could drift into flashy castled-shell pawn pushes like `...g5` / `...h5` instead of cleaner tactical transitions such as `...Bf5`, `...Nd6`, or immediate simplification. This phase therefore added transcript-backed regressions for the clean central recapture, safer development over kingside pawn lunges, the clearer `...Nd6` conversion route, and rejecting `...h5` once White has castled, then extracted `tactical_transition_guidance.py` so quiet ordering, root tie-breaks, and evaluation share the same tactical-transition heuristics. The result is that depth-3 search now keeps the cleaner tactical route through this phase of the transcript while preserving the depth-5 timing guard and full test suite.

---

# Task 6: Improve conversion once one side has the easier game

## 6.1 Review the winning side’s late conversion

- [x] Review the portion of the transcript where Black was clearly better / winning.
- [x] Note where Black:
  - [x] converted efficiently
  - [x] wasted tempi
  - [x] missed simpler routes
  - [x] allowed unnecessary counterplay

## 6.2 Add conversion regressions

- [x] Add tests where the winning side should prefer:
  - [x] promoting a passed pawn cleanly
  - [x] forcing queen trade / rook trade when winning
  - [x] mating-net construction over harmless maneuvering
  - [x] king improvement that directly supports conversion

## 6.3 Improve winning-side evaluation / ordering

- [x] Increase bonuses for:
  - [x] shortening the game when a clear win exists
  - [x] blocking counterplay before side activity
  - [x] choosing forcing promotion races correctly
  - [x] simplifying into technically won endings

## 6.4 Improve mating-net practicality

- [x] Prefer moves that:
  - [x] cut off king flight squares
  - [x] coordinate queen / rook / bishop efficiently
  - [x] avoid unnecessary queen wandering when mate or promotion is near

Phase note: Task 6 is complete. The late-conversion audit in `tmp/strategy6_task6_audit.txt` showed that once Black was clearly better, the main remaining issue was not finding the win at all but choosing the cleanest route quickly enough: the transcript already contained strong forcing ideas, yet the engine could still waste time with harmless maneuvers instead of cashing queenside pawns, tightening knight routes, and simplifying cleanly. This phase therefore added transcript-backed regressions for the clean `...Nd6` redeployment and `...Rxa4` cash-in, kept the won-ending queen-trade simplification covered at depth 3, and extended `conversion_guidance.py` with a root bonus so winning conversion geometry now influences root choice instead of only quiet ordering. Existing search and quality tests already covered the remaining mate-net / king-improvement bullets, so Task 6 closes with stronger transcript-specific conversion discipline while preserving the depth-5 timing guard and full suite.

---

# Task 7: Expand transcript-driven review coverage

## 7.1 Save new STRATEGY6 review games

- [x] Run and save at least:
  - [x] one depth 3 vs depth 3 review game
  - [x] one deeper review game if runtime is acceptable (not runtime-feasible after the bounded depth-3 review runtime)

## 7.2 Maintain a running review artifact

- [x] Create / update a `tmp/` artifact with:
  - [x] move chosen
  - [x] better human move
  - [x] why it is better
  - [x] whether the miss is evaluation-, ordering-, search-, or conversion-driven

## 7.3 Convert new failures into regressions

- [x] After each major phase, add or update tests for:
  - [x] worst opening drift
  - [x] worst king-safety delay
  - [x] worst practical tactical transition
  - [x] worst inefficient conversion

## 7.4 Keep a running quality checklist

- [x] Track whether the engine still shows:
  - [x] early rook shuffles before castling
  - [x] unjustified flank pawn pushes
  - [x] rim-knight development without reason
  - [x] practical tactical collapses after a decent opening
  - [x] slow winning conversion

Phase note: Task 7 is complete. The fresh bounded review transcript in `tmp/strategy6_task7_w3b3.txt` and the running artifact in `tmp/strategy6_task7_review.txt` showed that the old rook-shuffle and rim-knight themes were largely improved, but new review misses still clustered around overaggressive wing-piece drifts before castling, delayed king safety after a decent opening, and a still-slower-than-necessary winning conversion. This phase therefore added new STRATEGY6 regressions for the review-game knight drift, bishop drift / king-safety delay, and the clean conversion capture over a harmless rook shuffle, while also tightening opening move ordering so the review opening no longer prefers `Nf3h4`. The result is that Task 7 now has a live review artifact, a refreshed quality checklist, and regression coverage for the worst new misses discovered by the first STRATEGY6 review game; the deeper review run was deliberately skipped because the bounded depth-3 review already made a deeper run impractical for this phase.

---

# Task 8: Final acceptance for STRATEGY6

## 8.1 Validation

- [x] Run:

  ```bash
  pylint chess_game
  python -m pytest tests -q
  ```

- [x] Run targeted AI validation:

  ```bash
  python -m pytest tests/test_ai.py tests/test_ai_quality.py tests/test_ai_search.py tests/test_alpha_beta_pruning.py -q
  ```

## 8.2 Self-play review

- [x] Save a fresh self-play transcript under `tmp/`.
- [x] Confirm the reviewed game shows measurable improvement in:
  - [x] opening discipline
  - [x] castling / king-safety timing
  - [x] reduced low-value rook drift
  - [x] fewer unjustified flank pawn pushes
  - [x] cleaner practical conversion

## 8.3 Closeout

- [x] Update this file with completed statuses and notes.
- [x] Commit only after lint and tests pass.
- [x] Push to `origin/master`.

Phase note: Task 8 is complete. The final bounded acceptance transcript lives in `tmp/strategy6_task8_w3b3.txt`, and the acceptance review lives in `tmp/strategy6_task8_review.txt`. Compared with both the STRATEGY6 baseline and the Task 7 review game, the fresh game showed measurable improvement: the old move-15 `Nf3h4` drift was replaced by the central break `d2d4`, neither side made the earlier low-value rook sidesteps, Black castled on move 20 and White castled on move 29 instead of delaying all the way to move 37, and the worst early flank-play themes (`Rc1`, `h4`, `b4`, `...Nh6`) did not recur. The game still is not pristine chess, but the remaining pawn pushes happened later and the winning side converted more directly through forcing captures (`...Bxf6`, `...Qxd5`, `...Qxh3`) rather than the earlier harmless rook shuffles, which satisfies the STRATEGY6 acceptance bar.
