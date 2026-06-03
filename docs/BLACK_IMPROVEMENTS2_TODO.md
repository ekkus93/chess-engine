# BLACK_IMPROVEMENTS2 TODO

## Goal

Continue improving Black's practical play based on patterns observed across four
depth-3 self-play games (`tmp/selfplay_d3d3_20260603.txt` and
`tmp/black_improvements1_game*.txt`).

The central finding after BLACK_IMPROVEMENTS1: **Black stopped castling** in all
three post-improvement games (the baseline castled on move 14).  Once g7-g5 weakens
the kingside and Na5 strands the knight on the rim, the king is stuck in the center
and White converts quickly.

Four targeted improvements:

1. **Castling urgency past move 12** — penalise a king still on e8/e1 after the
   early opening with queens on the board, making castling clearly the highest-value
   quiet move regardless of attacking ideas on the other wing.

2. **g7-g5 blocks castling** — g5 with the f8 bishop still on its home square
   means Black cannot castle kingside.  The penalty should be context-aware:
   heavier when castling has not yet happened and the g-pawn lunge forecloses it.

3. **Queenside castling as fallback** — when the kingside is compromised (g-pawn
   advanced, g-file weakened) and queenside castling rights are intact, reward
   e8-c8 more strongly so the engine considers it as a viable escape route.

4. **Na5 with castling rights still held** — attacking the bishop is a real tactic,
   but the engine should weigh the cost more: if Black still needs to castle, going
   to the rim should be penalised harder because it delays king safety.

This pass targets evaluation, ordering, and root tie-break signals only.
No changes to legal move generation or the public API.

---

## Scope Rules

- Board rules and move legality are unchanged.
- Public `Board` and AI entry-point APIs are unchanged.
- Prefer: evaluation terms, quiet-move ordering, root tie-break signals.
- Do not add randomness or hard-coded move bans.
- Every phase ends with:

  ```bash
  uv run python -m ruff check chess_game tests
  uv run python -m mypy chess_game
  uv run python -m pylint chess_game
  uv run python -m pytest tests/ -q -m "not slow"
  ```

- For behavior-changing phases also save a fresh depth-3 self-play transcript
  under `tmp/` and record the result in `memory.md`.

---

## Task 0: Baseline

### 0.1 Confirm current state

- [x] Verify that `tmp/black_improvements1_game1.txt`, `game2.txt`, and `game3.txt`
      show Black never castling.
- [x] Check move 8 in each game: confirm Black plays Na5 with castling rights intact.
- [x] Check move 10: confirm g7-g5 is played with f8 bishop still on f8 (blocking
      kingside castling).
- [x] Confirm `opening_king_urgency_penalty` and `opening_king_safety_score` are
      already wired into evaluation — audit their scale vs. the tactical gain from Na5.

### 0.2 Define success criteria

- [x] In a fresh depth-3 self-play game, Black castles at least once per game.
- [x] g7-g5 before castling (with f8 bishop blocking) is suppressed at depth=3.
- [x] Black considers queenside castling when the kingside is compromised.
- [x] Na5 with castling rights still held scores lower than a developing/castling move.

---

## Task 1: Castling Urgency Past Move 12

### 1.1 Add regression tests

- [x] Construct a board from `black_improvements1_game1.txt` at move 13 (Black to
      move, king at e8, castling rights intact, g5 pawn advanced).
- [x] Assert `get_best_move(board, depth=3)` chooses a castling or castling-enabling
      move rather than another wing pawn push or queen move.
- [x] Add an ordering test: `_move_order_score(board, e8g8, None)` >
      `_move_order_score(board, h7h5, None)` at this position.
- [x] Mark depth-3 best-move tests with `pytest.mark.slow`.

### 1.2 Audit existing castling urgency signals

- [x] Read `opening_development.py` — find `opening_king_safety_score` and
      `opening_king_urgency_penalty`.  Check their current magnitude and phase gate.
- [x] Read `opening_move_ordering.py` — find `QUIET_OPENING_CASTLING_URGENCY_BONUS`.
      Confirm it fires for e8-g8 and e8-c8.
- [x] Check whether the bonus scales with move count (should be larger the longer
      the king has been uncastled with queens on the board).

### 1.3 Strengthen late-opening castling urgency

- [x] In `opening_development.py`, add a `late_castling_urgency_penalty` that scales
      with move count: for each move beyond move 10 that the king is still on its
      initial square with queens on the board, add an increasing penalty.
      Suggested formula: `(fullmove - 10) * BASE_URGENCY` capped at a max.
- [x] Gate the penalty to positions where:
      - The king is on its home square (e1/e8).
      - At least one castling option is still available.
      - Both queens are on the board.
- [x] Wire the new penalty into `evaluation.py` under the `development` key.
- [x] In `opening_move_ordering.py`, increase `QUIET_OPENING_CASTLING_URGENCY_BONUS`
      when the move count is beyond 12 — or add a separate
      `QUIET_LATE_CASTLING_URGENCY_BONUS` that fires only in the late opening.

### 1.4 Add root tie-break signal

- [x] In `ai_search_helpers.py` (`_strategic_root_bonus`), add a root-only bonus
      for castling moves when the king has been uncastled for more than 10 moves.
- [x] The bonus should be large enough (≥ 40 cp) to override near-equal alternatives.

### 1.5 Verify

- [x] Run new regression tests — all must pass.
- [x] Run the full fast test suite — no regressions.
- [x] Run lint: `ruff`, `mypy`, `pylint` (10.00/10).

---

## Task 2: g7-g5 Blocks Castling — Context-Aware Penalty

### 2.1 Add regression tests

- [x] Construct the board at move 9 from the validation games (Black to move, king
      at e8, f8 bishop at home, kingside castling rights intact).
- [x] Assert `quiet_strategy_order_score(board, g7g5, None)` <
      `quiet_strategy_order_score(board, f8e7, None)` (developing the bishop).
- [x] Assert `quiet_strategy_order_score(board, g7g5, None)` <
      `quiet_strategy_order_score(board, e8g8, None)` (castling).

### 2.2 Add bishop-blocking condition to shelter penalty

- [x] In `opening_move_ordering.py`, extend `_is_castled_shelter_pawn_advance` (or
      add a companion `_is_castling_blocking_pawn_advance`) that fires when:
      - The king is uncastled (on e1/e8).
      - The kingside castling rights are intact.
      - The g7/g2 pawn advance to g5/g4 would leave the g-file weakened with the
        f8/f1 bishop still on its home square (blocking castling).
- [x] The additional penalty for this "castling-blocking" condition should be larger
      than the plain shelter advance penalty (≥ 40 cp total ordering penalty).

### 2.3 Add evaluation signal

- [x] In `pawn_structure_evaluation.py` or `opening_development.py`, add a penalty
      for the *static* position where:
      - The king is uncastled.
      - The g-pawn (for the side to move) has advanced 2+ squares from its home row.
      - The corresponding bishop (f1/f8) is still on its home square.
      This combination means castling is blocked by one's own bishop while the
      king shelter is already weakened.
- [x] Wire the new term into `evaluation.py` under `development`.

### 2.4 Verify

- [x] Run new regression tests — all must pass.
- [x] Run the full fast test suite — no regressions.
- [x] Run lint.

---

## Task 3: Queenside Castling as Fallback

### 3.1 Add regression tests

- [x] Construct a position where Black's kingside is compromised (g5 advanced, g-file
      open) and queenside castling is still available (a8 rook intact, no pieces
      between d8 and a8, b8 and c8 clear).
- [x] Assert `quiet_strategy_order_score(board, e8c8, None)` >
      `quiet_strategy_order_score(board, some_passive_queen_move, None)`.

### 3.2 Audit queenside castling bonus

- [x] Confirm `QUIET_OPENING_CASTLING_URGENCY_BONUS` fires for e8-c8 (queenside
      castling) as well as e8-g8 (kingside).
- [x] Check whether the bonus is reduced or suppressed when queenside files are not
      fully cleared (it should still fire if the castling move itself is legal).

### 3.3 Add kingside-compromised queenside bonus

- [x] In `opening_move_ordering.py`, add a conditional bonus for queenside castling
      that fires specifically when:
      - The moving side's g-pawn has advanced 2+ squares from home (kingside weakened).
      - Queenside castling is the move being considered.
      Make this bonus larger than the base castling urgency bonus to compensate for
      the engine's tendency to avoid queenside castling.

### 3.4 Verify

- [x] Run new regression tests — all must pass.
- [x] Run the full fast test suite — no regressions.
- [x] Run lint.

---

## Task 4: Na5 Penalty — Weight Castling Rights Cost

### 4.1 Add regression tests

- [x] Reconstruct the move-8 board from the validation games.
- [x] Assert `quiet_strategy_order_score(board, c6a5, None)` <
      `quiet_strategy_order_score(board, e8g8, None)` (castling is always preferred).
- [x] Assert the gap between castling and Na5 in ordering is ≥ 60 cp.

### 4.2 Add castling-delay cost to rim-knight penalty

- [x] In `opening_move_ordering.py`, extend `_is_knight_wing_drift` or add a
      companion function that applies an extra penalty when:
      - The knight moves to the rim (col 0 or 7).
      - The moving side's king is still uncastled (on e1/e8).
      - Castling rights are still intact (the rim move delays castling).
      Extra penalty: `QUIET_RIM_KNIGHT_DELAYS_CASTLING_PENALTY` (suggested: 28 cp).
- [x] In `opening_development.py`, extend `middlegame_rim_knight_penalty` to scale
      higher when the king is still uncastled — the positional cost of the rim knight
      is compounded by the king-safety delay.

### 4.3 Verify

- [x] Run new regression tests — all must pass.
- [x] Run the full fast test suite — no regressions.
- [x] Run lint.

---

## Task 5: Integration — Self-Play Validation

### 5.1 Run at least 3 fresh depth-3 self-play games

- [x] Run:
  ```bash
  uv run python -m chess_game.self_play --white-depth 3 --black-depth 3
  ```
  three times, saving each transcript to:
  - `tmp/black_improvements2_game1.txt`
  - `tmp/black_improvements2_game2.txt`
  - `tmp/black_improvements2_game3.txt`

### 5.2 Evaluate improvement

For each game check:
- [x] Does Black castle (e8-g8 or e8-c8) before move 20?
- [x] Does Black push g7-g5 before castling?
- [x] Does Black's king survive into the endgame more often?
- [x] What is the game length and result?

Record findings in `tmp/black_improvements2_validation.txt`.

### 5.3 Accept or iterate

- [x] If Black castles in ≥ 2 of 3 games → mark this TODO complete.
- [x] If castling still doesn't happen → revisit Task 1 and increase the urgency
      penalty, then re-run.

### 5.4 Final verification gate

- [x] `uv run python -m ruff check chess_game tests` — all clear.
- [x] `uv run python -m mypy chess_game` — no errors.
- [x] `uv run python -m pylint chess_game` — 10.00/10.
- [x] `uv run python -m pytest tests/ -q -m "not slow"` — all pass.
- [x] `uv run python -m pytest tests/ -q -m "slow"` — all pass.
- [x] Update `memory.md` with timestamp, model used, and summary of changes.

---

## Task 6: Commit and Push

- [x] Stage only source files and test files (not `tmp/` artifacts).
- [x] Write a commit message summarising the four improvements.
- [x] Push to `origin/master`.
- [x] Update `docs/BLACK_IMPROVEMENTS2_TODO.md` to mark all tasks complete.
