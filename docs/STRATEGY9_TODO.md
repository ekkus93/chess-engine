# STRATEGY9: Faster Conversion and Opening Discipline TODO

## Overview

Analysis of a depth-3 vs depth-3 self-play game revealed two structural strategy
weaknesses:

1. **Slow winning conversion** — Black was clearly winning by move 44 but took
   85 additional moves to deliver checkmate (129 total). Root causes:
   - `passer_race_guidance` is gated to ≤ 5 non-king pieces, so it never fired
     in this rich endgame (Black had 10+ qualifying pieces). Pawn advancement
     had no urgency signal.
   - No direct "push the main passer" incentive in `conversion_guidance`.
   - Repetition penalty relies on exact threefold repetition; near-repeat rook
     shuffles avoid it entirely and pile up for 40+ moves.
   - King activation (`simple_endgame_guidance`) is disabled when rooks/queens
     are still on the board, so Black's king stayed passive until very late.

2. **Poor White opening** — White played Nc3→Nd5→Nf4, a 3-move knight tour
   with zero centre pawn play. Existing opening penalties cover rim-knight
   development and queen sorties but **not** repeatedly moving the same minor
   piece before other pieces are developed.

## Relevant Files

- `chess_game/chess/passer_race_guidance.py` — `_MAX_NON_KING_PIECES = 5`,
  `_PASSER_PROGRESS_BONUS = 20`, `_HIGH_PRIORITY_PUSH_BONUS = 72`
- `chess_game/chess/conversion_guidance.py` — `winning_conversion_move_bonus()`,
  `_passer_support_score()`, `_promotion_lane_support_score()`
- `chess_game/chess/ai_search_helpers.py` — `RepetitionPolicy`, `repetition_score()`,
  `_repetition_penalty()`
- `chess_game/chess/simple_endgame_guidance.py` — gated to positions with no
  rooks/queens; `_MAX_MINOR_PIECES = 2`, `_MAX_PAWNS = 6`
- `chess_game/chess/opening_move_ordering.py` — `opening_discipline_order_score()`;
  has `QUIET_REPEAT_HEAVY_PIECE_PENALTY` for rooks/queens but no equivalent for
  minor pieces
- `chess_game/chess/endgame_evaluation.py` — `evaluate_endgame_technique()`,
  `_active_king_score()`
- `tests/test_ai_strategy9_regressions.py` — new regression test file (create)

---

## Task 0 — Baseline documentation

**Goal:** Record the problem positions from the existing self-play transcript
so regressions can be written against concrete board states.

- [x] **0a** Identify the 4–5 most representative "drift" positions in the
  `tmp/self_play_d3d3_*.txt` transcript (moves ~60, ~70, ~90, ~110) where
  Black should have made progress but shuffled instead.
- [x] **0b** For each drift position, write down:
  - The FEN or piece layout
  - What Black actually played
  - What Black should have played (pawn push / rook activation)
- [x] **0c** Identify the opening position after White's 3rd move (c3d5) where
  the knight tour started — record as an opening regression seed.
- [x] **0d** Create `tests/test_ai_strategy9_regressions.py` with skeleton
  fixtures (board setup helpers) for each identified position.

---

## Task 1 — Expand passer-race guidance to richer endgames

**Goal:** Make `passer_race_guidance.py` fire in endgames with up to 10
non-king qualifying pieces (currently capped at 5).

**Files:** `chess_game/chess/passer_race_guidance.py`

- [x] **1a** Raise `_MAX_NON_KING_PIECES` from `5` to `10`.
  - `_ALLOWED_RACE_KINDS = {QUEEN, ROOK, PAWN}` already excludes bishops and
    knights from the count, so the gate is actually counting heavy pieces +
    pawns. 10 is appropriate for the rook+pawn endgame phase (2 rooks + 6–8
    pawns = 8–10).
- [x] **1b** Verify `_passes_material_gate()` logic: confirm it counts pieces
  of both colours combined. If it counts only one side, adjust the threshold
  accordingly.
- [x] **1c** Check that `_is_relevant_passer_race()` and
  `_is_relevant_passer_race_evaluation()` still return sensible results in
  middlegame positions after the gate expansion (should not regress, since both
  sides need a "race-critical passer" for the guard to be active).
- [x] **1d** Run `pytest tests/ -q` after the gate change to confirm no
  regressions.
- [x] **1e** Add regression test `test_strategy9_passer_race_fires_in_rook_endgame`:
  Board with 2 rooks + 5 pawns each and a clear passer — verify
  `passer_race_order_score()` returns a nonzero bonus for advancing that passer.

---

## Task 2 — Direct "push the main passer" bonus in conversion guidance

**Goal:** Explicitly reward advancing the main passed pawn when the winning
side is ahead by a rook or more, bridging the gap between "track support
pieces" (current) and "push the pawn" (missing).

**Files:** `chess_game/chess/conversion_guidance.py`

- [x] **2a** Add constant `_PASSER_ADVANCE_BONUS = 30` near the other bonus
  constants at the top of the file.
- [x] **2b** Add helper `_passer_advance_bonus(board, move, context) -> int`:
  - Returns `_PASSER_ADVANCE_BONUS` when:
    - `context.main_passer` is set
    - The moving piece is a pawn
    - `move.end` matches `context.main_passer` (i.e. the move advances the
      main passer by one square)
  - Returns 0 otherwise.
  - This is deliberately narrow: only fire for advancing the specific tracked
    passer, not any pawn push, to avoid noise in other positions.
- [x] **2c** Call `_passer_advance_bonus()` inside `winning_conversion_move_bonus()`,
  after the existing `_passer_support_score` / `_promotion_lane_support_score`
  calls.
- [x] **2d** Add regression test `test_strategy9_conversion_rewards_main_passer_advance`:
  Set up a position with Black rook + bishop + passed d-pawn vs White rook.
  Verify `winning_conversion_move_bonus()` returns a higher score for
  advancing the d-pawn than for a neutral rook shuffle.
- [x] **2e** Run `pytest tests/ -q` and confirm no regressions.

---

## Task 3 — Strengthen anti-drift / repetition deterrent in winning positions

**Goal:** Penalise rook-shuffle loops that arise when the winning side has no
forced plan at depth 3. The current repetition penalty only triggers on exact
threefold repetition; near-repeats (Rd1↔Rd2↔Re1↔Re2 cycles) avoid it.

**Files:** `chess_game/chess/ai_search_helpers.py`,
`chess_game/chess/ai_repetition_patterns.py`

- [x] **3a** Audit `_repetition_penalty()`: the current `scale` is capped at
  5× policy penalty. Determine whether increasing the cap to 8× when
  `practical_evaluation >= 2 × policy.threshold` (i.e. clearly winning)
  would help without breaking drawn-game handling.
- [x] **3b** Audit `_progress()` inside the RepetitionPolicy construction in
  `ai.py`. Confirm it uses `evaluate_progress(board)` from
  `endgame_evaluation.py`. If the progress function does not account for
  pawn advancement (only material), add a pawn-advancement component:
  - Count own passed pawns and their rank distance to promotion.
  - Sum that into the progress score so "pawns advanced" registers as
    genuine progress.
- [x] **3c** Add a **root-cycle penalty** for shuffling when winning: in
  `_strategic_root_bonus()` (or alongside `_repetition_root_penalty()`),
  add a bonus for moves that change the pawn structure (capture or pawn push)
  when the side is winning by ≥ a rook of material. This nudges root move
  selection toward decisive progress even before repetition is triggered.
  - Suggested constant: `_PAWN_STRUCTURE_CHANGE_ROOT_BONUS = 18`.
  - Gate: `material_lead(board, color) >= MATERIAL_VALUES[PieceType.ROOK]`.
- [x] **3d** Add regression test `test_strategy9_root_prefers_pawn_push_over_shuffle_when_winning`:
  Set up a position where Black has a clear passer and a rook shuffle is
  available. Verify `get_best_move()` prefers advancing the passer over the
  shuffle.
- [x] **3e** Run `pytest tests/ -q` and confirm no regressions.

---

## Task 4 — King activation in piece-heavy endgames

**Goal:** Activate the king earlier when the winning side is clearly ahead in
material but `simple_endgame_guidance` is unavailable (because rooks/queens
are still on the board).

**Files:** `chess_game/chess/endgame_evaluation.py`,
`chess_game/chess/simple_endgame_guidance.py`,
`chess_game/chess/ai_search_helpers.py`

- [x] **4a** Audit `_active_king_score()` in `endgame_evaluation.py`: confirm
  it contributes to the evaluation when `endgame_phase > 0`. Check what
  `endgame_phase` value is assigned when both sides still have rooks.
- [x] **4b** Add a new helper `_heavy_endgame_king_activity_bonus(board, color) -> int`
  in `endgame_evaluation.py`:
  - Fires when: both sides have no queens, at least one side has ≤ 1 rook,
    and the winning side has a material lead ≥ bishop value.
  - Returns a bonus proportional to how close the winning side's king is to
    the board centre (Manhattan distance from e4/d5 area).
  - Suggested scale: 0–20 points, so it doesn't override tactical signals.
- [x] **4c** Wire `_heavy_endgame_king_activity_bonus()` into
  `evaluate_endgame_technique()`, scaled by `endgame_phase`.
- [x] **4d** Wire the same bonus into `evaluate_progress()` (separately, so
  it affects both static evaluation and progress-based repetition policy).
- [x] **4e** Add regression test `test_strategy9_king_activates_in_heavy_piece_endgame`:
  Set up Black king + rook + bishop vs White king + rook — verify that a king
  centralisation move scores higher in `evaluate_endgame_technique()` than
  a passive king retreat.
- [x] **4f** Run `pytest tests/ -q` and confirm no regressions.

---

## Task 5 — Penalise repeated minor-piece moves in the opening

**Goal:** Prevent the engine from making the same knight (or bishop) move
multiple times in the opening before other minor pieces are developed,
as observed in the game (Nc3→Nd5→Nf4 on moves 1, 3, 5 before any
pawn or other piece moved).

**Files:** `chess_game/chess/opening_move_ordering.py`

- [x] **5a** Add constant `QUIET_REPEATED_MINOR_PIECE_PENALTY = 22` alongside
  the existing penalty constants.
- [x] **5b** Add helper `_is_repeated_minor_piece_move(board, kind, move) -> bool`:
  - Fires when:
    - `kind` is `KNIGHT` or `BISHOP`
    - The piece at `move.start` has already moved from its home square (i.e.
      `move.start` is NOT the home square for that piece)
    - `undeveloped_minor_count(board) >= 2` (other minor pieces still
      undeveloped)
    - The king is unsettled (`_opening_king_unsettled(board)` is True)
  - This is different from `_is_minor_retreat_before_settling` (which only
    catches retreat to home row); this catches any second move of a piece
    that already moved away from home.
- [x] **5c** Apply `_is_repeated_minor_piece_move` in
  `_minor_opening_discipline_score()`, subtracting
  `QUIET_REPEATED_MINOR_PIECE_PENALTY` when it fires.
- [x] **5d** Confirm the penalty does NOT fire for:
  - A piece capturing (handled separately in the capture ordering path)
  - A piece retreating to its home square (already caught by
    `_is_minor_retreat_before_settling`)
  - A piece that has already developed AND all other minors are also developed
    (`undeveloped_minor_count == 0`).
- [x] **5e** Add regression test `test_strategy9_opening_penalises_knight_tour_moves`:
  Set up the position after `b1c3` with other minor pieces undeveloped.
  Verify `opening_discipline_order_score()` assigns a lower score to
  `c3d5` than to developing a new minor piece (e.g. `g1f3`).
- [x] **5f** Add regression test
  `test_strategy9_opening_allows_settled_knight_repositioning`:
  Set up a position where both minors are developed and the king is castled.
  Verify the penalty does NOT fire for a knight repositioning move.
- [x] **5g** Run `pytest tests/ -q` and confirm no regressions.

---

## Task 6 — Lint, full test suite, and self-play validation

**Goal:** Verify all changes pass the full quality gate and produce measurably
faster conversion in a new self-play game.

- [x] **6a** Run `python -m ruff check chess_game tests` — fix all warnings.
- [x] **6b** Run `python -m mypy chess_game/` — fix all type errors.
- [x] **6c** Run `python -m pylint chess_game/` — achieve 10.00/10. Fix all
  structural warnings (no `# pylint: disable` pragmas).
- [x] **6d** Run `python -m pytest tests/ -q` — all tests must pass.
- [x] **6e** Run a new depth-3 vs depth-3 self-play game:
  ```
  python -m chess_game.self_play --white-depth 3 --black-depth 3 \
    > tmp/strategy9_acceptance_d3d3.txt
  ```
- [x] **6f** Verify the new game ends in ≤ 90 moves (vs 129 in the baseline).
  If conversion is still slow, revisit Task 2 and Task 3 constants.
- [x] **6g** Check White's opening: confirm White plays at least one central
  pawn move (d4 or e4) within the first 5 moves. If not, revisit Task 5
  constants.
- [x] **6h** Write brief notes in `tmp/strategy9_review.txt` summarising:
  - Game result and move count
  - Whether passer-push urgency improved
  - Whether the knight-tour opening recurred
  - Any new issues observed

---

## Task 7 — Commit and push

**Goal:** Check in all changes once the full quality gate passes.

- [x] **7a** Stage all changed files:
  - `chess_game/chess/passer_race_guidance.py`
  - `chess_game/chess/conversion_guidance.py`
  - `chess_game/chess/ai_search_helpers.py`
  - `chess_game/chess/endgame_evaluation.py`
  - `chess_game/chess/opening_move_ordering.py`
  - `tests/test_ai_strategy9_regressions.py`
  - `docs/STRATEGY9_TODO.md`
- [x] **7b** Commit with message:
  `STRATEGY9: faster conversion, passer urgency, opening knight-tour penalty`
- [x] **7c** Push to `origin/master`.
- [x] **7d** Update all task/subtask checkboxes above to reflect final status.

---

## Success Criteria

| Metric | Baseline | Target |
|--------|----------|--------|
| Self-play game length (d3 vs d3) | 129 moves | ≤ 90 moves |
| White plays centre pawn in first 5 moves | ✗ (Nc3→Nd5→Nf4) | ✓ |
| Passer-race guidance fires in rich endgame | ✗ (gate = 5 pieces) | ✓ (gate = 10) |
| Pylint score | 10.00/10 | 10.00/10 |
| All tests pass | 627 | ≥ 627 |
