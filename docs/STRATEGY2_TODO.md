# STRATEGY2 TODO

## Goal

Make the engine **convert advantages more cleanly** and avoid drifting into sterile repetitions when better progress is available.

This pass focuses on:

- stronger **progress awareness**
- better **anti-repetition behavior**
- more purposeful **winning-endgame conversion**
- better **play against counterplay**
- stronger **quiet improving move selection**
- more practical **endgame protocol guidance**

This pass should build on `docs/STRATEGY1_TODO.md`, not replace it. The intent here is to fix the specific failure mode seen in depth-5 self-play: the engine can often stay safe, but it still struggles to **improve**, **restrict**, and **finish**.

---

## Scope rules

- Keep legal move generation and rules correctness unchanged unless a new AI test exposes a direct bug.
- Preserve the public `Board` API where possible.
- Prefer structural changes over one-off evaluation hacks.
- Do not hide repetition problems behind randomization.
- Use tests to define when a repeated line is acceptable and when it is pathological.
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

# Task 0: Re-establish the conversion baseline

## 0.1 Record the current failure pattern

- [x] Review `docs/game3_w5b5.md`.
- [x] Note:
  - [x] final result
  - [x] move count
  - [x] first point where one side looked better
  - [x] first point where progress stalled
  - [x] repeated move cycle at the end
  - [x] whether the repetition was forced or voluntary

Baseline note: `docs/game3_w5b5.md` ended in a voluntary threefold-repetition draw on move 114 after a repeating rook swing cycle (`...a5e5`, `...e5a5`) and king shuffle (`...e6f6`, `...f6e6`). The late endgame had no forcing draw sequence; it was a drift/stagnation failure rather than best defense.

## 0.2 Build baseline “should make progress” positions

- [x] Create a small set of hand-built positions where a side is clearly better but not immediately tactical.
- [x] Include positions covering:
  - [x] better king activity in a simplified ending
  - [x] rook behind a passed pawn
  - [x] rook cutting off the enemy king
  - [x] queen trade when ahead
  - [x] blockade of an enemy passer
  - [x] improvement of the worst-placed piece
- [x] Record current `evaluate()` and `get_best_move()` behavior for each.

## 0.3 Build baseline repetition positions

- [x] Create targeted positions where the engine currently tends to repeat:
  - [x] lateral rook checks with no conversion
  - [ ] queen shuffle without structural gain
  - [x] king shuffle in a non-forcing ending
  - [x] repeated checking when already materially ahead
- [x] Record whether repetition is:
  - [x] best defense for the worse side
  - [x] lazy safety choice for the better side

---

# Task 1: Add regression tests for progress and anti-repetition

## 1.1 Add “do not drift” tests

- [x] Add tests where the better side should choose a move that improves the position instead of repeating.
- [ ] Cover cases such as:
  - [x] rook improves king cutoff instead of checking from the side
  - [x] king centralizes instead of shuffling laterally
  - [ ] queen trade is chosen over a harmless repeated check
  - [x] rook activation is chosen over a neutral waiting move

## 1.2 Add “repetition is allowed only when justified” tests

- [x] Add tests where repetition is correct:
  - [x] worse side forces perpetual or drawable repetition
  - [ ] only non-losing defense is repeated checking
- [x] Add tests where repetition is incorrect:
  - [x] stronger side repeats from a winning position
  - [ ] equal side repeats despite a clear improving plan

## 1.3 Add conversion-choice tests

- [x] Add tests that a winning side prefers:
  - [x] queen trade into a clearly won ending
  - [ ] rook trade into a trivially won king-and-pawn or rook ending
  - [x] king activation before pointless checking
  - [x] restricting the enemy king before pawn pushing
  - [x] blockading the opponent’s passer before chasing side pawns

## 1.4 Add quiet progress tests

- [x] Add tests for quiet moves that improve without forcing tactics:
  - [x] improve the worst-placed rook
  - [x] bring the king one square closer in an ending
  - [x] move a heavy piece behind a passed pawn
  - [ ] occupy a file/rank that reduces enemy mobility
  - [x] create luft to avoid future back-rank issues

---

# Task 2: Add explicit progress-awareness to evaluation

## 2.1 Define a progress model

- [x] Decide which static features count as “real progress.”
- [x] Include at least:
  - [x] improved king activity
  - [x] better heavy-piece coordination
  - [x] stronger king cutoff
  - [x] safer simplification
  - [x] improved passed-pawn support
  - [x] increased enemy restriction

## 2.2 Add a progress-oriented evaluation component

- [x] Add a clearly named evaluation component such as:
  - [x] `progress`
  - [ ] `conversion_progress`
  - [ ] `restriction`
- [x] Make it visible in `get_evaluation_breakdown()`.
- [x] Keep it separate from raw material and mobility.

## 2.3 Reward moves that improve the side with the advantage

- [x] When materially ahead, reward:
  - [x] king centralization in safe endgames
  - [x] heavy pieces moving to more active files/ranks
  - [x] piece coordination around the enemy king box
  - [x] clean transitions into easier endings
  - [x] improved control of promotion squares

## 2.4 Avoid fake progress

- [x] Do not reward:
  - [x] repeated checks that do not tighten the position
  - [x] rook/queen shuffles that preserve the same geometry
  - [x] king wandering that does not improve safety or activity
  - [x] pawn pushes that create targets without support

---

# Task 3: Add anti-repetition logic without breaking correct drawing play

## 3.1 Define repetition policy

- [x] Decide how the engine should treat repeated positions in search:
  - [x] neutral when repetition is best defense
  - [x] negative for the better side if improvement exists
  - [x] acceptable when evaluation is near equal and no stable gain is visible
- [x] Document this policy in code comments where the logic lives.

## 3.2 Detect voluntary repetition by the stronger side

- [x] Add logic that recognizes when:
  - [x] the same side is re-entering the same position
  - [x] that side is materially or positionally better
  - [x] no immediate tactical necessity justifies the repetition
- [x] Penalize those lines modestly rather than catastrophically.

## 3.3 Keep valid defensive repetition intact

- [x] Ensure the worse side is still allowed to seek perpetual or repetition.
- [x] Ensure forced repetition is not penalized as though it were laziness.
- [ ] Add regression tests for perpetual-check style saves.

## 3.4 Decide where the penalty belongs

- [x] Evaluate whether anti-repetition belongs in:
  - [ ] static evaluation
  - [ ] move ordering
  - [x] search node scoring
  - [x] history/repetition bookkeeping
- [x] Prefer the smallest correct design that avoids double-counting.

---

# Task 4: Improve winning-endgame conversion heuristics

## 4.1 Strengthen king-cutoff evaluation

- [x] Reward positions where a rook or queen:
  - [x] cuts the enemy king off by file
  - [x] cuts the enemy king off by rank
  - [x] keeps the enemy king away from the center
  - [x] keeps the enemy king away from the passer

## 4.2 Reward box-shrinking and restriction

- [x] Add heuristics for:
  - [x] shrinking the enemy king’s legal box
  - [x] forcing enemy king toward edge or corner
  - [x] reducing useful checking distance
  - [x] making enemy rook/queen defense more passive

## 4.3 Improve passer-conversion logic

- [x] Reward:
  - [x] rook behind own passed pawn
  - [x] king escort of a passed pawn
  - [x] controlling key promotion squares
  - [ ] fixing enemy king/piece in front of the pawn
- [ ] Penalize:
  - [ ] pushing the passer too early without support
  - [ ] abandoning the passer to chase side checks

## 4.4 Prefer cleaner winning transitions

- [x] When ahead, reward:
  - [x] exchanging queens if the resulting ending is simpler and still winning
  - [x] exchanging one rook if the remaining ending is trivially won
  - [x] avoiding unnecessary tactical complications
  - [x] eliminating enemy checking resources

---

# Task 5: Play against counterplay

## 5.1 Identify the opponent’s main source of activity

- [x] Add logic that recognizes whether counterplay comes from:
  - [ ] a passed pawn
  - [x] checking distance from a rook
  - [x] checking distance from a queen
  - [ ] active king penetration
  - [x] open-file access

## 5.2 Reward moves that reduce counterplay first

- [x] Reward:
  - [x] blockading enemy passers
  - [ ] closing or contesting checking files
  - [ ] exchanging the enemy’s most active piece
  - [x] cutting off the enemy king
  - [x] creating luft before it becomes urgent

## 5.3 Penalize flashy but loose play

- [x] Penalize moves that:
  - [x] keep giving harmless checks instead of simplifying
  - [ ] chase pawns while allowing perpetual-check resources
  - [ ] activate a piece but loosen king safety or passer control
  - [ ] choose activity that increases enemy practical chances

---

# Task 6: Improve quiet move ordering for strategic progress

## 6.1 Extend quiet move ordering categories

- [x] Add or refine ordering bonuses for:
  - [x] king cutoff moves
  - [x] rook-behind-passer moves
  - [x] king-centralization moves in winning endings
  - [x] queen-trade offers when materially ahead
  - [x] blockade moves against enemy passers
  - [x] moves that improve the worst-placed piece

## 6.2 Distinguish progress checks from empty checks

- [ ] Score checks differently when they:
  - [ ] force king toward the edge
  - [ ] force king away from the passer
  - [ ] support simplification
  - [ ] merely repeat the same geometry

## 6.3 Tie ordering to current advantage

- [ ] Ensure the search uses different quiet priorities when:
  - [ ] ahead and converting
  - [ ] equal and maneuvering
  - [ ] worse and trying to force a draw

---

# Task 7: Strengthen endgame protocol helpers

## 7.1 Extend existing mating/protocol support into practical conversion

- [x] Reuse the current endgame helper structure.
- [x] Add protocol guidance for:
  - [x] rook endgames with king cutoff
  - [ ] queen endgames with perpetual-check risk
  - [x] queen + rook vs lone king practical coordination
  - [x] rook + passer endings

## 7.2 Add move-priority helpers for conversion

- [x] Prefer moves that:
  - [x] reduce the enemy king’s space
  - [x] bring own king closer
  - [x] coordinate rook and king
  - [x] place rook behind the passer
  - [x] eliminate checking distance

## 7.3 Avoid pathological protocol behavior

- [x] Ensure helpers do not blindly:
  - [x] force repetition
  - [ ] stalemate the opponent
  - [ ] walk into avoidable checks
  - [x] overrule tactical necessities

---

# Task 8: Search integration and bookkeeping

## 8.1 Audit repetition bookkeeping

- [x] Review the current repetition key and history use in AI search and self-play.
- [x] Confirm whether the search has enough information to distinguish:
  - [x] true repetition pressure
  - [x] voluntary repetition
  - [x] transposition reuse that is not actually a draw attempt

## 8.2 Integrate progress-aware scoring into search safely

- [x] Decide whether to apply progress/anti-repetition logic in:
  - [ ] static evaluation only
  - [ ] quiescence stand-pat interpretation
  - [ ] root move selection tie-breaks
  - [ ] iterative deepening carry-over heuristics
- [x] Keep the implementation explainable and testable.

## 8.3 Preserve tactical sharpness

- [x] Ensure the new logic does not cause the engine to:
  - [x] reject necessary perpetuals
  - [x] avoid valid checking sequences
  - [x] trade into drawn endings by mistake
  - [x] miss tactics because quiet heuristics dominate too strongly

---

# Task 9: Measure whether the engine actually improved

## 9.1 Re-run depth-5 self-play

- [x] Run at least one new depth-5 vs depth-5 self-play game.
- [x] Save the transcript under `tmp/` or `docs/` as appropriate.
- [x] Compare with `docs/game3_w5b5.md`.

## 9.2 Review outcome quality

- [x] Check whether the new game shows:
  - [x] fewer pointless repetitions
  - [x] fewer neutral rook/queen shuffles
  - [ ] more king activation in endings
  - [x] better simplification when one side is ahead
  - [x] clearer play against enemy counterplay

Comparison note: `tmp/strategy2_w5b5.txt` ended with **checkmate on move 69 (Black wins)** instead of drifting into a move-114 repetition draw. The new game still was not “perfect strategic chess,” but it was materially more decisive and did not collapse into the same sterile rook cycle as `docs/game3_w5b5.md`.

## 9.3 Re-check performance

- [x] Re-run the depth-5 search benchmark.
- [x] Ensure the new logic does not undo the current depth-5 practicality.
- [x] If performance regresses materially, note which heuristics caused it.

Performance note: `tests/test_ai_search.py::test_depth_5_search_completes` still passes, but the measured time rose from about **28.5s** in the STRATEGY1 pass to about **37.8s** here, mainly from the added progress/repetition bookkeeping and richer endgame-progress evaluation.

Phase note: the follow-up regression slice added green coverage for queen-trade simplification, rookless conversion scoring, blockade ordering, luft creation, and progress-aware repetition scoring; the depth-5 benchmark remained practical at about **36.5s** on the latest run.

---

# Task 10: Final acceptance

## 10.1 Correctness target

- [x] `pylint chess_game` passes
- [x] `python -m pytest tests -q` passes

## 10.2 Strategic-quality target

- [x] The engine avoids voluntary repetition when a stable improving plan exists.
- [x] The engine still allows repetition when it is the best drawing resource.
- [x] The engine prefers king activation, restriction, and simplification in winning endings.
- [x] The engine chooses more quiet progress moves in targeted tests.

## 10.3 Performance target

- [x] Depth-5 remains practical after the new logic.
- [x] New progress heuristics do not cause a major search slowdown.

---

## Deferred work

- Opening-book work remains deferred.
- More aggressive pruning/search selectivity remains deferred to `docs/SELECTIVE_PRUNING.md`.
- Full endgame tablebase behavior remains deferred; this pass is about practical conversion and anti-drift, not perfect play in every reduced material ending.
