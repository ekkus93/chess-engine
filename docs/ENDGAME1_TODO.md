# ENDGAME1 TODO

## Goal

Make the engine play **stronger practical endgames** by improving:

- **anti-drift behavior in simplified positions**
- **king activation and opposition awareness**
- **passed-pawn race judgment**
- **winning-side conversion discipline**
- **losing-side defensive resistance**
- **endgame-specific move ordering and root choice**
- **repetition handling based on practical result**
- **bishop-ending and low-material coordination**

This pass should build on `docs/STRATEGY7_TODO.md`, not replace it. The latest depth-3 self-play game in `tmp/selfplay_w3b3_20260527T160502Z.txt` shows that the engine can reach playable endings, but it still drifts in low-material positions with repeated bishop moves, passive kings, and unclear pawn-race plans instead of converging on practical wins or holds.

---

## Scope rules

- Keep legal move generation and board-rule correctness unchanged unless a new regression exposes a direct bug.
- Preserve the public `Board` API where possible.
- Prefer structural evaluation, move ordering, selective search, and review-loop improvements over hard-coded move bans.
- Do not fake stronger endgame play with randomness.
- Do not weaken tactical correctness just to make the ending look cleaner.
- Define every major improvement through targeted tests and transcript-backed positions.
- Every major phase must end with:

  ```bash
  pylint chess_game
  python -m pytest tests -q
  ```

- For AI-heavy phases, also run:

  ```bash
  python -m pytest tests/test_ai.py tests/test_ai_quality.py tests/test_ai_search.py tests/test_alpha_beta_pruning.py -q
  ```

- For phases that materially change practical endgame behavior, also save and review at least one self-play game under `tmp/`.

---

# Task 0: Re-establish the endgame baseline

## 0.1 Review the latest simplified-phase self-play

- [x] Review `tmp/selfplay_w3b3_20260527T160502Z.txt`.
- [x] Record:
  - [x] final result
  - [x] move count
  - [x] first point where the game became clearly an endgame
  - [x] first low-value repetition loop
  - [x] first missed king-activation chance
  - [x] first point where a passer race became more important than piece activity
  - [x] first point where the better side could have simplified cleanly
  - [x] first point where the worse side still had a stronger drawing setup than the move chosen

## 0.2 Extract concrete endgame mistakes

- [x] Create a baseline artifact under `tmp/` summarizing the game's worst endgame decisions.
- [x] Include at least:
  - [x] the repeated bishop loop from the late phase
  - [x] a passive-king sequence by the better side
  - [x] a passive-king or wrong-blockade sequence by the worse side
  - [x] a moment where a passed pawn should have dominated the move choice
  - [x] a moment where simplification was stronger than maneuvering

## 0.3 Build transcript-backed endgame positions

- [x] Reconstruct hand-built test positions for:
  - [x] bishop-loop drift with no practical gain
  - [x] king activation versus passive waiting
  - [x] supporting the main passed pawn
  - [x] blockading the enemy passer
  - [x] simplifying into a clearly won ending
  - [x] choosing repetition only when it preserves the best result
- [x] Record current `evaluate()` and `get_best_move()` behavior for each.

## 0.4 Define success metrics for ENDGAME1

- [x] Decide practical success criteria such as:
  - [x] fewer low-value endgame repetition loops
  - [x] earlier king activation in low-material positions
  - [x] stronger passed-pawn prioritization
  - [x] cleaner conversion when ahead
  - [x] stronger drawing resistance when worse
  - [x] fewer bishop or rook maneuvers that do not change the practical result

Phase note:

- [x] Task 0 is complete. The baseline artifact lives in `tmp/endgame1_baseline_positions.txt`. The fresh depth-3 self-play ended with a White mate on move 236, but the first clear low-material endgame already began on move 89 and the first obvious low-value bishop loop appeared by moves 117-129. The reproduced baseline probes now pin the current problems directly: the bishop-loop position still chooses `e4g6`, the king-activation probe still retreats with `h2g1`, the king-and-pawn probe still picks `c2b2` instead of making the h-pawn the main plan, while the queen-versus-king probe already finds the clean `e7b7` mate. Phase validation is green at `pylint chess_game` (`10.00/10`), `python -m pytest tests -q` (`577 passed`), and `python -m pytest tests/test_ai.py tests/test_ai_quality.py tests/test_ai_search.py tests/test_alpha_beta_pruning.py -q` (`120 passed`).

---

# Task 1: Add endgame anti-drift regressions

## 1.1 Add low-value repetition regressions

- [x] Add tests where the engine should reject repeating piece loops that do not improve evaluation or practical winning chances.
- [x] Cover cases such as:
  - [x] bishop triangles with no new target
  - [x] rook shuffles with no file gain or checking net
  - [x] queen checks that do not improve repetition, mate, or promotion geometry

## 1.2 Add “change the position” regressions

- [x] Add tests where the engine should prefer moves that alter the practical state of the ending.
- [x] Cover cases such as:
  - [x] king step toward critical squares over piece drift
  - [x] pawn break or passer support over harmless maneuvering
  - [x] simplification over decorative pressure

## 1.3 Add result-aware repetition regressions

- [x] Add tests where the better side should avoid repetition.
- [x] Add tests where the worse side should seek repetition when it preserves a draw or best resistance.

Phase note:

- [x] Task 1 is complete. The new `tests/test_ai_endgame1_regressions.py` file now locks in the late bishop-loop and passive-king problems from the fresh endgame baseline, plus endgame-specific repetition and conversion sanity checks. This phase added `chess_game/chess/simple_endgame_guidance.py`, which feeds quiet ordering and root choice only in low-material endings with no queens or rooks so the search now prefers immediate king activation over bishop-loop drift and passive king retreats like `Kg1`. Phase validation is green at `pylint chess_game` (`10.00/10`), `python -m pytest tests -q` (`583 passed`), and `python -m pytest tests/test_ai.py tests/test_ai_quality.py tests/test_ai_search.py tests/test_alpha_beta_pruning.py -q` (`120 passed`).

---

# Task 2: Improve king activation and king geometry

## 2.1 Audit current king-activity scoring

- [x] Review existing evaluation helpers that already reward king centralization, shelter, and endgame activity.
- [x] Identify where current logic is too weak once queens or heavy pieces leave the board.
- [x] Save the audit under `tmp/`.

## 2.2 Add king-activation evaluation guidance

- [x] Add or tighten heuristics for:
  - [x] distance to center in low-material endings
  - [x] distance to own passer and enemy passer
  - [x] distance to promotion and blockade squares
  - [x] opposition-like geometry in king-and-pawn style structures
  - [x] king cut-off opportunities against the enemy king

## 2.3 Add king-activation ordering and root bonuses

- [x] Prefer moves that:
  - [x] step the king toward critical files, ranks, and entry squares
  - [x] escort or attack the main passer
  - [x] gain opposition or restrict enemy king entry
- [x] Demote moves that:
  - [x] keep the king frozen without tactical justification
  - [x] move pieces instead of activating the king when the king should lead

Phase note:

- [x] Task 2 is complete. The audit artifact lives in `tmp/endgame1_task2_audit.txt`. This phase extended `chess_game/chess/simple_endgame_guidance.py` with a dedicated `king_activation` evaluation component for true late endgames, covering king escort distance to own passers, blockade distance to enemy passers, opposition-like geometry, and simple king cut-off patterns, while keeping the heavier search hooks narrowly limited to king and bishop moves. `tests/test_ai_endgame1_regressions.py` now exposes these king-geometry improvements directly through the evaluation breakdown, and the final validation is green at `pylint chess_game` (`10.00/10`), `python -m pytest tests -q` (`587 passed`), and `python -m pytest tests/test_ai.py tests/test_ai_quality.py tests/test_ai_search.py tests/test_alpha_beta_pruning.py -q` (`120 passed`).

---

# Task 3: Strengthen passed-pawn race judgment in true endgames

## 3.1 Add deeper passed-pawn race regressions

- [x] Add tests where the engine must correctly choose between racing, blockading, checking, and simplifying.
- [x] Cover cases such as:
  - [x] one tempo from promotion versus side activity
  - [x] king catches the passer only with immediate activation
  - [x] bishop or rook must stop the passer instead of chasing counterplay
  - [x] pushing the wrong pawn loses immediately

## 3.2 Audit current race logic in simplified endings

- [x] Review `passer_race_guidance.py`, endgame evaluation helpers, and any root tiebreak logic that already reasons about promotion races.
- [x] Identify where current logic works in heavy-piece endings but still misses cleaner low-material races.
- [x] Save the audit under `tmp/`.

## 3.3 Tighten evaluation for race-critical positions

- [x] Add or refine scoring for:
  - [x] true tempo-to-promotion differences
  - [x] whether the king or minor piece controls the critical squares
  - [x] whether a defender is tied down to a promotion square
  - [x] whether checks help the race or only waste tempi
  - [x] whether simplification preserves or kills the winning race

## 3.4 Tighten race-aware ordering and root choice

- [x] Prefer moves that:
  - [x] create or preserve an unstoppable passer
  - [x] remove the opponent's only rival race
  - [x] improve escort geometry instead of cosmetic threats
- [x] Demote flashy checks or maneuvers that do not improve the race.

Phase note:

- [x] Task 3 is complete. The audit artifact lives in `tmp/endgame1_task3_audit.txt`. This phase added `chess_game/chess/low_material_race_guidance.py` as a narrow low-material race layer for no-queen / no-rook endings, and wired it into `endgame_evaluation.py`, `ai_move_ordering.py`, and `ai_search_helpers.py` without touching the shared heavy-piece passer-race path. `tests/test_ai_endgame1_regressions.py` now covers one-tempo promotion pushes, immediate king activation in pawn races, bishop blockade of a near-promotion passer, and rejection of the wrong pawn push, while final validation is green at `pylint chess_game` (`10.00/10`), `python -m pytest tests -q` (`592 passed`), and `python -m pytest tests/test_ai.py tests/test_ai_quality.py tests/test_ai_search.py tests/test_alpha_beta_pruning.py -q` (`120 passed`).

---

# Task 4: Improve winning-side conversion discipline

## 4.1 Add winning-conversion endgame regressions

- [ ] Add tests where the better side should convert with the cleanest practical plan.
- [ ] Cover cases such as:
  - [ ] force king activity before piece drift
  - [ ] trade into a trivially won king-and-pawn or minor-piece ending
  - [ ] support the main passer instead of grabbing side pawns
  - [ ] cut off the enemy king before starting a pawn race

## 4.2 Audit current conversion guidance in low-material positions

- [ ] Review existing conversion modules against the new low-material positions.
- [ ] Identify where heavy-piece conversion logic does not carry over cleanly once only bishops, rooks, or kings and pawns remain.
- [ ] Save the audit under `tmp/`.

## 4.3 Add endgame conversion evaluation guidance

- [ ] Add or tighten heuristics for:
  - [ ] king lead toward promotion squares
  - [ ] forcing simplification quality
  - [ ] cut-off value against the defending king
  - [ ] outside-passer support versus side-pawn greed
  - [ ] avoiding repeated moves when one clean plan is available

## 4.4 Add conversion ordering and root tie-breaks

- [ ] Ensure near-equal root choices prefer:
  - [ ] the shortest practical route to promotion
  - [ ] the lowest counterplay exposure
  - [ ] the cleanest simplification into a known win

Phase note:

- [ ] Task 4 complete note

---

# Task 5: Improve losing-side defensive resistance in endgames

## 5.1 Add drawing-technique regressions

- [ ] Add tests where the worse side should choose the strongest practical hold.
- [ ] Cover cases such as:
  - [ ] blockade over side activity
  - [ ] active king defense over passive piece shuffling
  - [ ] repetition or checking resource that holds
  - [ ] avoiding losing trades into dead-lost pawn races

## 5.2 Audit current defensive guidance in low-material endings

- [ ] Review defensive-containment and endgame guidance modules for overlap and gaps.
- [ ] Identify where current logic still overvalues vague activity when the only real task is holding the draw or maximizing resistance.
- [ ] Save the audit under `tmp/`.

## 5.3 Add endgame defensive evaluation guidance

- [ ] Add or tighten heuristics for:
  - [ ] practical blockade quality
  - [ ] king proximity to key defensive squares
  - [ ] whether the defending bishop/rook attacks the correct side of the pawn chain
  - [ ] whether simplification increases or decreases drawing chances
  - [ ] whether a piece is tied to the only drawing resource

## 5.4 Add defensive ordering and root tie-breaks

- [ ] Prefer moves that:
  - [ ] preserve the only drawing zone
  - [ ] force the stronger side to prove technique
  - [ ] keep the defending king active
- [ ] Demote passive waiting and pretty moves that concede the key squares.

Phase note:

- [ ] Task 5 complete note

---

# Task 6: Add bishop-ending and low-material coordination guidance

## 6.1 Add bishop-ending regressions

- [ ] Add tests for practical bishop endings and bishop-plus-pawns structures.
- [ ] Cover cases such as:
  - [ ] bishop on the correct color complex for the pawn race
  - [ ] wrong bishop drift away from the promotion theater
  - [ ] bishop plus king coordination against an outside passer
  - [ ] bishop triangulation that wastes tempi

## 6.2 Audit current low-material piece guidance

- [ ] Review how current move ordering and evaluation handle bishop-only, rook-light, and king-and-pawn-adjacent endings.
- [ ] Identify piece-specific gaps exposed by the current bishop-loop self-play sequence.
- [ ] Save the audit under `tmp/`.

## 6.3 Add piece-specific endgame evaluation guidance

- [ ] Add or tighten heuristics for:
  - [ ] bishop mobility relative to relevant pawn color complexes
  - [ ] bishop control of promotion and blockade squares
  - [ ] rook activity behind passers in reduced material
  - [ ] king-plus-piece coordination around the main theater

## 6.4 Add piece-specific ordering and root bonuses

- [ ] Prefer moves that:
  - [ ] keep the bishop or rook aligned with the critical pawn structure
  - [ ] increase coordination with the king
  - [ ] avoid repeating aimless diagonals or files

Phase note:

- [ ] Task 6 complete note

---

# Task 7: Add endgame-specific ordering, root choice, and repetition policy

## 7.1 Audit current endgame hot paths

- [ ] Review `ai_move_ordering.py`, `ai_search_helpers.py`, and any repetition-aware logic with an endgame-only lens.
- [ ] Identify which signals are cheap enough for hot-path ordering and which belong only in evaluation or root tie-breaks.
- [ ] Save the audit under `tmp/`.

## 7.2 Add endgame-specific quiet-order signals

- [ ] Score moves for:
  - [ ] king activation
  - [ ] passer support or blockade
  - [ ] cut-off geometry
  - [ ] meaningful simplification
  - [ ] entering or avoiding repetition based on practical result

## 7.3 Add endgame-specific root tie-break behavior

- [ ] When root scores are near-equal, prefer moves that:
  - [ ] improve the best practical result
  - [ ] reduce low-value repetition if the side is better
  - [ ] preserve repetition if the side is worse and that is the best hold
  - [ ] narrow the opponent's useful replies

Phase note:

- [ ] Task 7 complete note

---

# Task 8: Optional low-material precision upgrade

## 8.1 Investigate tablebase integration feasibility

- [ ] Evaluate whether Syzygy-style tablebase probing is practical for this project.
- [ ] Record:
  - [ ] supported environments
  - [ ] dependency cost
  - [ ] runtime/storage trade-offs
  - [ ] API integration points
  - [ ] fallback behavior when tablebases are absent

## 8.2 Decide whether to implement or defer

- [ ] If feasible, create a narrowly scoped implementation plan.
- [ ] If not feasible, document why and define the highest-value heuristic substitutes.

Phase note:

- [ ] Task 8 complete note

---

# Task 9: Review-loop expansion for ENDGAME1

## 9.1 Play fresh review games

- [ ] Save at least one new self-play transcript under `tmp/` after the main endgame changes land.
- [ ] If runtime is practical, also save one seeded late-phase continuation focused on low-material play.

## 9.2 Record fresh practical misses

- [ ] Create an ENDGAME1 review artifact under `tmp/`.
- [ ] For each major miss, record:
  - [ ] move chosen
  - [ ] better human move
  - [ ] why the human move is better
  - [ ] whether the miss was primarily evaluation, ordering, root choice, repetition policy, or search-depth related

## 9.3 Promote the worst new misses to regressions

- [ ] Add targeted tests for the worst recurring new endgame errors.
- [ ] Update the endgame plan if the review reveals an unplanned theme.

Phase note:

- [ ] Task 9 complete note

---

# Task 10: Final acceptance for ENDGAME1

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
  - [ ] king activation
  - [ ] fewer low-value repetition loops
  - [ ] cleaner passed-pawn prioritization
  - [ ] better winning conversion in low-material positions
  - [ ] stronger practical defense in worse endings
  - [ ] more coherent bishop/rook coordination in reduced material

## 10.3 Closeout

- [ ] Update this file with completed statuses and notes.
- [ ] Commit only after lint and tests pass.
- [ ] Push to `origin/master`.

Phase note:

- [ ] Task 10 complete note
