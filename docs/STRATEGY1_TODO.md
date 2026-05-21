# STRATEGY1 TODO

## Goal

Make the engine play **more strategically** without weakening correctness or the search gains already recovered.

This pass focuses on:

- stronger **positional evaluation**
- better **phase-aware planning**
- more realistic **king safety and pawn-structure judgment**
- better handling of **quiet strategic moves**
- basic **bread-and-butter endgame mating protocols**

This pass does **not** include an opening database yet. Opening-book work is explicitly deferred to a later feature pass.

---

## Scope rules

- Keep legal move generation and rules correctness unchanged unless a new AI test exposes a direct bug.
- Preserve the public `Board` API where possible.
- Prefer structural improvements over ad hoc bonuses.
- Do not silently downgrade requested search behavior.
- Add tests before or alongside new evaluator/endgame behavior.
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

# Task 0: Re-establish the strategic baseline

## 0.1 Record current search-quality baseline

- [ ] Run at least one depth-5 self-play game from the current engine.
- [ ] Save the transcript under `tmp/`.
- [ ] Note:
  - [ ] result
  - [ ] move count
  - [ ] obvious strategic defects
  - [ ] odd king walks
  - [ ] pointless piece shuffles
  - [ ] whether winning sides simplify cleanly or keep hacking tactically

## 0.2 Record evaluation baseline on strategic test positions

- [ ] Collect small hand-built positions covering:
  - [ ] strong outpost vs no outpost
  - [ ] active rook vs passive rook
  - [ ] healthy pawn structure vs weak pawn structure
  - [ ] safe king vs exposed king
  - [ ] space advantage vs cramped position
- [ ] Record current `evaluate()` output for each.

## 0.3 Record endgame baseline

- [ ] Build simple winning endgames for:
  - [ ] king + two rooks vs lone king
  - [ ] king + queen + rook vs lone king
  - [ ] king + queen vs lone king
  - [ ] king + rook vs lone king
- [ ] Check whether the current engine converts these cleanly.
- [ ] Note whether it wastes time with checks, repetition, or aimless drifting.

---

# Task 1: Add strategic regression tests first

## 1.1 Add positional-evaluation tests

- [x] Create or extend tests covering:
  - [x] knight outpost bonus
  - [x] bishop blocked by own pawns penalty
  - [x] rook on open file bonus
  - [x] rook trapped behind own pawns penalty
  - [x] active king in endgame bonus
  - [x] space advantage preference
  - [ ] weak-square / hole exploitation preference
  - [x] better minor-piece coordination preference

## 1.2 Add quiet-move strategy tests

- [x] Add positions where the best move is a quiet improving move, not a forcing tactic.
- [ ] Cover cases such as:
  - [ ] centralizing a queen or rook
  - [ ] improving the worst-placed piece
  - [x] stepping the king to safety
  - [ ] restraining an enemy passed pawn before it runs

## 1.3 Add conversion tests for winning strategic positions

- [x] Add tests that a clearly better side prefers:
  - [x] simplifying into a won ending
  - [x] trading into favorable material balance
  - [ ] reducing counterplay when ahead

## 1.4 Add endgame protocol tests

- [ ] Add regression tests for:
  - [ ] king + two rooks mate procedure eventually converging
  - [ ] king + queen + rook mate procedure eventually converging
  - [ ] king + queen vs king not stalemating trivially
  - [ ] king + rook vs king basic driving technique improving position
- [ ] Keep these tests deterministic enough to catch regressions without relying on very long searches.

---

# Task 2: Refactor evaluation into strategy-friendly components

## 2.1 Make evaluator breakdown more explicit

- [x] Ensure the evaluator has clearly named components for:
  - [x] material
  - [x] piece-square values
  - [x] mobility
  - [x] pawn structure
  - [x] king safety
  - [x] rook activity
  - [x] minor-piece activity
  - [x] space
  - [x] endgame technique / king activity
  - [x] conversion / simplification incentives

## 2.2 Separate middlegame and endgame terms

- [x] Introduce explicit phase weighting.
- [x] Define how phase is computed:
  - [x] by remaining non-pawn material
  - [ ] by piece count
  - [ ] or a hybrid
- [x] Blend relevant heuristics instead of applying the same bonus in every phase.

## 2.3 Centralize tunable constants

- [x] Keep strategic weights in one place.
- [x] Use descriptive names such as:
  - [x] `KNIGHT_OUTPOST_BONUS`
  - [x] `SPACE_ADVANTAGE_BONUS`
  - [x] `BAD_BISHOP_PENALTY`
  - [x] `KING_ACTIVITY_ENDGAME_BONUS`
  - [x] `TRADE_WHEN_AHEAD_BONUS`

---

# Task 3: Improve pawn-structure understanding

## 3.1 Expand structural pawn analysis

- [x] Reuse existing file-based helpers where possible.
- [x] Add or refine support for:
  - [x] pawn islands
  - [x] weak pawn chains
  - [x] blocked central pawns
  - [x] pawn majorities
  - [x] candidate passed pawns

## 3.2 Connect pawn structure to plans

- [ ] Reward structures that create natural plans:
  - [ ] queenside majority in endgame
  - [x] protected passed pawns
  - [x] central pawn duo when stable
- [ ] Penalize structures that limit plans:
  - [x] fixed backward pawns
  - [ ] permanently weak files/squares created by pawn moves

## 3.3 Make pawn bonuses phase-aware

- [ ] Ensure passed pawns matter more in endgames than openings.
- [ ] Ensure king-shelter pawn moves are not over-penalized when tactically justified.
- [ ] Ensure central-space pawns are not rewarded blindly if overextended and unsupported.

---

# Task 4: Improve king safety and prophylaxis

## 4.1 Expand king-safety scoring

- [x] Evaluate:
  - [x] pawn shield quality
  - [x] open files/diagonals toward the king
  - [x] nearby attacking pieces
  - [ ] weak escape squares
  - [x] back-rank looseness

## 4.2 Reward preventive play

- [ ] Add incentives for moves that:
  - [ ] reduce direct attacking lanes
  - [ ] challenge an attacking piece before it arrives
  - [ ] create luft when appropriate
  - [ ] avoid self-weakening pawn pushes

## 4.3 Avoid pathological king walks

- [ ] Add tests and penalties for early king wandering in non-forcing positions.
- [ ] Ensure king activity is still rewarded in genuine endgames.

---

# Task 5: Improve piece activity and coordination

## 5.1 Add outpost and anchor-square scoring

- [x] Reward stable knight outposts.
- [x] Reward bishops posted on active long diagonals.
- [ ] Reward pieces defended by pawns when they create lasting pressure.

## 5.2 Penalize bad piece placement

- [ ] Penalize:
  - [ ] trapped bishops
  - [x] knights on the rim without compensation
  - [x] passive rooks blocked by own pawns
  - [ ] queen overextension without support

## 5.3 Score coordination, not just individual activity

- [ ] Add bonuses for:
  - [ ] doubled rooks on open files
  - [x] queen + rook battery pressure
  - [x] bishop + knight cooperation around central squares
  - [ ] multiple pieces attacking the same weak square

---

# Task 6: Add space and restriction evaluation

## 6.1 Measure space advantage

- [x] Add a simple, stable space heuristic.
- [x] Prefer counting controlled/useful central and near-central squares rather than raw emptiness.

## 6.2 Reward restriction

- [x] Reward positions where the opponent’s pieces have few useful squares.
- [x] Penalize self-inflicted cramping.
- [ ] Avoid double-counting with mobility too aggressively.

## 6.3 Add anti-noise tests

- [ ] Ensure “space” does not reward overextension with hanging pawns.
- [ ] Ensure cramped-but-solid defensive setups are not always mis-scored as losing.

---

# Task 7: Encourage better conversion when ahead

## 7.1 Add simplification incentives

- [x] When materially ahead, reward:
  - [x] trading queens if it reduces counterplay
  - [x] trading into winning rook or queen endings
  - [x] reducing tactical complexity when safe

## 7.2 Penalize flashy but unnecessary complications

- [ ] Avoid overvaluing repeated checking if a clean conversion is available.
- [ ] Avoid endless tactical harassment when a decisive simplification exists.

## 7.3 Add “play against counterplay” heuristics

- [ ] Reward cutting off the enemy king.
- [x] Reward blockading dangerous passed pawns.
- [ ] Reward forcing enemy pieces into passivity while ahead.

---

# Task 8: Add basic endgame mating protocols

## 8.1 Choose protocol structure

- [x] Decide whether these are implemented as:
  - [x] explicit search/evaluation bonuses
  - [ ] special-case endgame helpers
  - [ ] protocol detectors with move-priority helpers
- [x] Prefer the smallest correct design that does not distort general play.

## 8.2 Detect trivial won mating-material endings

- [x] Add detectors for:
  - [x] KRR vs K
  - [x] KQR vs K
  - [x] KQ vs K
  - [x] KR vs K

## 8.3 Encode basic mating principles

- [ ] For these endings, reward:
  - [x] driving the enemy king to the edge
  - [ ] reducing the enemy king’s box
  - [x] bringing own king closer
  - [ ] avoiding stalemate patterns
  - [ ] avoiding needless repetition

## 8.4 Add search tie-breakers for mating protocols

- [ ] Prefer moves that reduce the mating box size.
- [x] Prefer king-centralization moves when safe.
- [ ] Prefer coordination between heavy pieces.

## 8.5 Validate practical conversion

- [ ] Run self-play or guided engine-vs-engine checks on these endings.
- [ ] Ensure the stronger side wins reliably without absurd move counts.

---

# Task 9: Improve search support for strategic play

## 9.1 Improve quiet-move ordering

- [x] Boost ordering for:
  - [x] improving moves from iterative deepening
  - [x] strong TT quiet moves
  - [x] king-safety improving quiet moves
  - [x] passed-pawn pushes in favorable positions

## 9.2 Add selective support for strategic moves

- [ ] Evaluate whether search should extend or protect:
  - [ ] passed-pawn races
  - [ ] checking sequences near exposed kings
  - [ ] promotion races
  - [ ] critical quiet conversion moves

## 9.3 Keep performance under control

- [x] Re-measure depth-5 timing after every major strategic heuristic addition.
- [x] Ensure strategic improvements do not undo the depth-5 recovery pass.

---

# Task 10: Validate game-quality improvements

## 10.1 Run comparison self-play

- [ ] Run at least:
  - [ ] depth-5 vs depth-5 before/after comparison
  - [ ] depth-7 vs depth-7 once practical

## 10.2 Review games for strategic quality

- [ ] Compare whether the improved engine shows:
  - [ ] fewer pointless king walks
  - [ ] fewer purposeless piece shuffles
  - [ ] more coherent development
  - [ ] better pawn-structure respect
  - [ ] cleaner simplification when winning
  - [ ] stronger conversion in basic winning endings

## 10.3 Validate against regressions

- [ ] Ensure tactical sharpness is not lost while adding strategic features.
- [ ] Ensure repetition detection, mate finding, and promotion behavior remain correct.

---

# Task 11: Final acceptance

## 11.1 Correctness target

- [x] `pylint chess_game` passes
- [x] `python -m pytest tests -q` passes

## 11.2 Strategic-quality target

- [x] The engine prefers stronger pawn structures in regression tests.
- [x] The engine prefers safer kings in regression tests.
- [x] The engine chooses more quiet improving moves in targeted positions.
- [x] The engine converts simple winning endings more reliably.

## 11.3 Performance target

- [x] Depth-5 remains practical after strategic additions.
- [x] Strategic heuristics do not cause another major search-speed collapse.

---

## Deferred work

- Opening database / opening book integration is explicitly deferred to a later pass.
- More advanced endgame tablebase-like behavior is deferred; this pass only covers basic mating protocols and practical winning technique.
