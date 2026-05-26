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

- [ ] Review current opening-related terms in:
  - [ ] `chess_game/chess/evaluation.py`
  - [ ] `chess_game/chess/opening_development.py`
  - [ ] `chess_game/chess/opening_guidance.py`
  - [ ] `chess_game/chess/opening_move_ordering.py`
- [ ] Document:
  - [ ] which opening terms dominate too early
  - [ ] which penalties are too weak
  - [ ] where move-order signals and eval signals disagree

## 2.2 Increase penalties for non-developing rook moves

- [ ] Penalize home-rank rook sidesteps more precisely when:
  - [ ] the king is uncastled
  - [ ] minor-piece development is incomplete
  - [ ] queens are still on the board
  - [ ] the rook move does not improve pressure, defense, or connection

## 2.3 Increase penalties for premature shelter-loosening pawn moves

- [ ] Penalize flank pawn pushes more sharply when they:
  - [ ] loosen castling structure
  - [ ] do not fight for the center
  - [ ] do not prepare a concrete development scheme
  - [ ] do not answer an opponent threat

## 2.4 Improve knight-development scoring

- [ ] Reward:
  - [ ] central knight development
  - [ ] development that supports castling and center control
  - [ ] development that increases practical tactical coverage
- [ ] Penalize:
  - [ ] rim development without concrete justification
  - [ ] knight moves that increase coordination lag

## 2.5 Tighten “finish development before side play” scoring

- [ ] Increase bonuses for:
  - [ ] completing both minor pieces
  - [ ] bishop activation before rook drift
  - [ ] on-time castling
  - [ ] natural central pawn support
- [ ] Reduce credit for:
  - [ ] one-purpose side-space grabs
  - [ ] pretty-looking but non-forcing rook or queen placements

---

# Task 3: Improve opening move ordering and practical quiet choices

## 3.1 Audit quiet opening ordering

- [ ] Review how quiet move ordering currently prioritizes:
  - [ ] minor development
  - [ ] castling
  - [ ] central recaptures / central support
  - [ ] rook shifts
  - [ ] flank pawn moves

## 3.2 Make development bundles score higher

- [ ] Prefer moves that simultaneously:
  - [ ] develop a piece
  - [ ] improve king safety
  - [ ] reinforce the center
  - [ ] prepare the next natural developing move

## 3.3 Demote low-information quiet moves

- [ ] Push down quiet moves that:
  - [ ] only gain side space
  - [ ] do not change the main tactical or strategic question
  - [ ] recycle pressure on the same harmless square
  - [ ] move a rook without a forcing reason

## 3.4 Improve tie-break quality in simple openings

- [ ] Prefer moves that:
  - [ ] keep castling options intact
  - [ ] preserve pawn shelter
  - [ ] reduce future coordination debt
  - [ ] avoid creating long-term weaknesses for one tempo of cosmetic activity

---

# Task 4: Strengthen king-safety urgency before castling

## 4.1 Add regressions for delayed king safety

- [ ] Add tests where the engine should castle or secure the king before slow side play.
- [ ] Cover cases such as:
  - [ ] uncastled king with queens on the board
  - [ ] rook move vs castling
  - [ ] flank pawn push vs castling
  - [ ] quiet bishop retreat vs king safety

## 4.2 Improve evaluation-side king urgency

- [ ] Increase penalties when:
  - [ ] the king stays central while development lags
  - [ ] castling rights are abandoned without compensation
  - [ ] the pawn shell is loosened before safety is fixed
  - [ ] long-range enemy pieces can exploit open files / diagonals soon

## 4.3 Improve move-order king urgency

- [ ] Prefer moves that:
  - [ ] castle
  - [ ] preserve castling rights
  - [ ] repair shelter
  - [ ] remove immediate pressure on the king zone
- [ ] Demote moves that:
  - [ ] postpone king safety without gaining a concrete tactical concession
  - [ ] make future castling worse

---

# Task 5: Improve tactical sanity after strategic opening mistakes

## 5.1 Review the critical tactical transition in the transcript

- [ ] Audit the phase around:
  - [ ] `...f5`
  - [ ] `...fxe4`
  - [ ] the knight exchanges on `d4`
  - [ ] the queen trade / infiltration sequence

## 5.2 Add regressions for practical tactical choices

- [ ] Add tests where the engine should prefer:
  - [ ] clean central recaptures
  - [ ] safe simplification into a better structure
  - [ ] tactical lines that keep the king safer
  - [ ] tactical wins that preserve conversion clarity

## 5.3 Reduce flashy-but-fragile continuations

- [ ] Demote tactical choices that:
  - [ ] win a tempo but worsen king safety
  - [ ] preserve material equality while losing structure and coordination
  - [ ] chase a piece instead of fixing the main weakness
  - [ ] create practical counterplay for no compensation

## 5.4 Improve tactical transition scoring if needed

- [ ] If current logic is too scattered, extract a shared helper/module for:
  - [ ] practical simplification bonuses
  - [ ] king-safe tactical transition bonuses
  - [ ] “win the right pawn / piece, not just any active move” tie-breaks

---

# Task 6: Improve conversion once one side has the easier game

## 6.1 Review the winning side’s late conversion

- [ ] Review the portion of the transcript where Black was clearly better / winning.
- [ ] Note where Black:
  - [ ] converted efficiently
  - [ ] wasted tempi
  - [ ] missed simpler routes
  - [ ] allowed unnecessary counterplay

## 6.2 Add conversion regressions

- [ ] Add tests where the winning side should prefer:
  - [ ] promoting a passed pawn cleanly
  - [ ] forcing queen trade / rook trade when winning
  - [ ] mating-net construction over harmless maneuvering
  - [ ] king improvement that directly supports conversion

## 6.3 Improve winning-side evaluation / ordering

- [ ] Increase bonuses for:
  - [ ] shortening the game when a clear win exists
  - [ ] blocking counterplay before side activity
  - [ ] choosing forcing promotion races correctly
  - [ ] simplifying into technically won endings

## 6.4 Improve mating-net practicality

- [ ] Prefer moves that:
  - [ ] cut off king flight squares
  - [ ] coordinate queen / rook / bishop efficiently
  - [ ] avoid unnecessary queen wandering when mate or promotion is near

---

# Task 7: Expand transcript-driven review coverage

## 7.1 Save new STRATEGY6 review games

- [ ] Run and save at least:
  - [ ] one depth 3 vs depth 3 review game
  - [ ] one deeper review game if runtime is acceptable

## 7.2 Maintain a running review artifact

- [ ] Create / update a `tmp/` artifact with:
  - [ ] move chosen
  - [ ] better human move
  - [ ] why it is better
  - [ ] whether the miss is evaluation-, ordering-, search-, or conversion-driven

## 7.3 Convert new failures into regressions

- [ ] After each major phase, add or update tests for:
  - [ ] worst opening drift
  - [ ] worst king-safety delay
  - [ ] worst practical tactical transition
  - [ ] worst inefficient conversion

## 7.4 Keep a running quality checklist

- [ ] Track whether the engine still shows:
  - [ ] early rook shuffles before castling
  - [ ] unjustified flank pawn pushes
  - [ ] rim-knight development without reason
  - [ ] practical tactical collapses after a decent opening
  - [ ] slow winning conversion

---

# Task 8: Final acceptance for STRATEGY6

## 8.1 Validation

- [ ] Run:

  ```bash
  pylint chess_game
  python -m pytest tests -q
  ```

- [ ] Run targeted AI validation:

  ```bash
  python -m pytest tests/test_ai.py tests/test_ai_quality.py tests/test_ai_search.py tests/test_alpha_beta_pruning.py -q
  ```

## 8.2 Self-play review

- [ ] Save a fresh self-play transcript under `tmp/`.
- [ ] Confirm the reviewed game shows measurable improvement in:
  - [ ] opening discipline
  - [ ] castling / king-safety timing
  - [ ] reduced low-value rook drift
  - [ ] fewer unjustified flank pawn pushes
  - [ ] cleaner practical conversion

## 8.3 Closeout

- [ ] Update this file with completed statuses and notes.
- [ ] Commit only after lint and tests pass.
- [ ] Push to `origin/master`.
