# WHITE_IMPROVEMENTS2 TODO

## Goal

Continue improving White's (and both sides') practical play based on patterns
observed across the three WHITE_IMPROVEMENTS1 validation games:

- `tmp/white_improvements1_game1.txt` — White wins, move 154
- `tmp/white_improvements1_game2.txt` — Black wins, move 209 (queen endgame)
- `tmp/white_improvements1_game3.txt` — Black wins, move 93 (promoted pawn)

Three remaining root causes:

1. **Luft timing still too late** — White played h2-h3 on moves 103 and 117,
   far from the ideal window of 3-5 moves after castling.  The signal fires
   eventually but loses to competing middlegame plans too long.

2. **Castling urgency inconsistent** — Game 2 had White castling on move 47.
   King safety should be treated as urgent from around move 10 onward, not
   deferred until the middlegame is already deep.

3. **Endgame technique** — Games 2 and 3 were both lost in the endgame:
   - Game 2: White had a rook vs. Black's queen after pawn promotion on move
     204 — classic rook-vs-queen technique was missing.
   - Game 3: White promoted a pawn to a queen on move 81 but then allowed
     Black to promote too, and Black's pawn queened with check (d4-g1 fork/
     promotion) winning the endgame at move 90.

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

- For behavior-changing phases also save a fresh self-play transcript under
  `tmp/` and record the result in `memory.md`.

---

## Task 0: Baseline

### 0.1 Capture the failure positions

- [ ] Replay `tmp/white_improvements1_game2.txt` to the position where White
      castled (move 47) and confirm the king was still on e1 through move 46.
- [ ] Replay `tmp/white_improvements1_game1.txt` to the position just after
      White castled (move 19) and confirm h2-h3 was not played until move 103.
- [ ] Replay `tmp/white_improvements1_game3.txt` to move 88 (Black plays d4
      toward promotion) and record the board state.
- [ ] For each position, run `get_best_move(board, depth=3)` and identify
      what the engine actually plays vs. the correct defensive choice.
- [ ] Save baseline board states in `tmp/white_improvements2_baseline.txt`.

### 0.2 Audit existing signals

- [ ] Audit `late_castling_urgency_penalty` from BLACK_IMPROVEMENTS2 — does
      it fire for White in game 2's position at fullmove 10-20?  Is the
      threshold (fullmove > 4) too lenient?
- [ ] Audit `h_pawn_exposure_penalty` from WHITE_IMPROVEMENTS1 — why is h3
      deferred to move 103/117?  Is the penalty large enough to override
      middlegame plans at depth=3?
- [ ] Check `_h_pawn_luft_root_bonus` in `ai_search_helpers.py` — does the
      +36 root bonus fire even when h2 is NOT yet threatened (to encourage
      prophylactic h3)?
- [ ] Audit endgame evaluation for queen-vs-rook and pawn promotion races.

### 0.3 Define success criteria

- [ ] White plays h2-h3 within 5 moves of castling in ≥ 2 of 3 new games.
- [ ] White castles by move 25 in all 3 new games.
- [ ] White does not lose queen-vs-rook endgames due to passive play.
- [ ] White correctly stops opponent pawn promotion when ahead in material.

---

## Task 1: Early Post-Castling Luft (h3 Within 5 Moves)

The h_pawn_exposure_penalty only fires when a bishop is *already* aimed at h2.
We need a prophylactic bonus that fires immediately after castling — before any
threat is visible — to make h3 a natural first post-castling move.

### 1.1 Add regression tests

- [ ] Construct the game-1 board at move 20 (just after White castled on
      move 19, no bishop threat yet).
- [ ] Assert `quiet_strategy_order_score(board, h2h3, None)` is in the
      top-5 quiet moves even with no visible bishop threat.
- [ ] Assert the ordering gap between h2-h3 and the next best quiet pawn
      move is ≥ 20 cp when the king has just castled kingside with queens
      on the board.

### 1.2 Add prophylactic post-castling luft bonus

- [ ] In `opening_move_ordering.py` or `ai_move_ordering.py`, add a
      `_is_prophylactic_luft(board, color, move)` function that fires when:
      - The king is castled kingside (at g1/g8).
      - The h2/h7 pawn is still on its starting square (unmoved).
      - The king has been castled for ≤ 5 fullmoves (tracked via
        `board.fullmove_number` vs. estimated castle move).
      - Queens are still on the board.
      - The move is h2-h3 (or h7-h6 for Black).
- [ ] The bonus should be ≥ 24 cp so it consistently beats passive
      piece shuffles in the first few moves after castling.
- [ ] This is a *prophylactic* bonus — it fires even when no piece
      currently threatens h2.

### 1.3 Wire into root tie-break

- [ ] In `ai_search_helpers.py`, extend `_h_pawn_luft_root_bonus` to
      also fire prophylactically (not only when `h_pawn_exposure_penalty
      >= 15`) using the same just-castled condition from 1.2.
- [ ] The root bonus should be ≥ 30 cp in the prophylactic case.

### 1.4 Verify

- [ ] Run new regression tests — all must pass.
- [ ] Run the full fast test suite — no regressions.
- [ ] Run lint: `ruff`, `mypy`, `pylint` (10.00/10).

---

## Task 2: Consistent Early Castling

Game 2 had White castling on move 47.  The existing `late_castling_urgency_penalty`
triggers from fullmove 5 but is apparently not strong enough.

### 2.1 Add regression tests

- [ ] Construct the game-2 board at fullmove 15 (around move 29-30, king
      still at e1) and confirm `late_castling_urgency_penalty(board, WHITE)` >
      0 and confirm castling scores significantly above passive rook moves.
- [ ] Assert `quiet_strategy_order_score(board, e1g1, None)` >
      `quiet_strategy_order_score(board, Re1e2, None)` + 40 at this position.

### 2.2 Increase late-castling urgency for later moves

- [ ] In `opening_development.py`, increase `_LATE_CASTLING_BASE_PENALTY`
      from 12 to 16 so the scaling penalty grows faster after fullmove 4.
- [ ] Add a hard cap increase: `_LATE_CASTLING_MAX_PENALTY` from 96 to 128.
- [ ] Consider adding a secondary "mid-game uncastled" penalty that fires
      if the king is still on e1/e8 past fullmove 12 and queens are on the
      board — a flat +40 cp on top of the scaling term.

### 2.3 Strengthen castling ordering bonus

- [ ] In `opening_move_ordering.py`, increase `QUIET_OPENING_CASTLING_URGENCY_BONUS`
      from 40 to 56 and `QUIET_LATE_CASTLING_URGENCY_BONUS` from 48 to 64.
- [ ] Verify the increased bonus does not cause regressions in positions
      where castling would walk into a pin or attack.

### 2.4 Verify

- [ ] Run new regression tests — all must pass.
- [ ] Run the full fast test suite — no regressions.
- [ ] Run lint.

---

## Task 3: Rook-vs-Queen Endgame Defense

Game 2 ended with White having a rook against Black's newly-promoted queen.
White shuffled passively (Ra1-b1-a1) while Black's queen dominated.

### 3.1 Add regression tests

- [ ] Construct a KQvKR ending (Black queen, White rook).
- [ ] Assert that the engine recognizes the king must centralise and the
      rook must stay active (avoid passive rank-1 shuffling).
- [ ] Assert `get_best_move(board, depth=3)` prefers rook centralisation
      over passive back-rank moves in the relevant endgame position.

### 3.2 Audit existing queen-vs-rook endgame guidance

- [ ] Check `endgame_evaluation.py` — is there any KQvKR-specific logic?
- [ ] Check `rook_endgame_guidance.py` — does the passive rook penalty
      (`_WORSE_SIDE_CHECK_DRIFT_PENALTY`) apply to the losing side in a
      queen-vs-rook ending?
- [ ] Check `defensive_endgame_guidance.py` — does it recognize the need
      for king activity in this ending type?

### 3.3 Add queen-vs-rook endgame signals

- [ ] In `endgame_evaluation.py`, add a `evaluate_queen_vs_rook(board,
      endgame_phase)` function that:
      - Detects KQvKR positions (one queen, one rook, no other pieces).
      - Rewards the queen side for king centralisation and forcing checks.
      - Penalises the rook side for passive back-rank play.
      - Rewards the rook side for keeping the rook active and checking.
- [ ] Wire the new function into the evaluation breakdown.
- [ ] In `ai_move_ordering.py`, add a quiet-order penalty for rook moves
      that shuffle back and forth on the first rank in KQvKR positions.

### 3.4 Verify

- [ ] Run new regression tests — all must pass.
- [ ] Run the full fast test suite — no regressions.
- [ ] Run lint.

---

## Task 4: Pawn Promotion Race Awareness

Game 3 had both sides promoting pawns; White promoted first but then allowed
Black's d-pawn to queen with a fork (d4-g1 check/promotion) winning the game.

### 4.1 Add regression tests

- [ ] Construct the game-3 board near move 88 (Black's d4 pawn about
      to promote).
- [ ] Assert `get_best_move(board, depth=3)` prioritises stopping the
      d4 promotion over continuing White's own plans.
- [ ] Assert that `passer_race_guidance` rates Black's d4 pawn as a
      critical threat and raises the evaluation accordingly.

### 4.2 Audit passer race detection

- [ ] Check `passer_race_guidance.py` — does `_is_relevant_passer_race`
      fire correctly when both sides have near-promotion passers?
- [ ] Check `_is_near_promotion_passer_push` — does it detect Black's d4
      pawn push (one or two squares from queening) as a high-priority threat?
- [ ] Check `low_material_race_guidance.py` — does `endgame_race_context`
      correctly classify the position as a "must-hold" race for White?

### 4.3 Strengthen opposing-passer urgency

- [ ] In `passer_race_guidance.py`, ensure `_ENEMY_PASSER_DANGER_BONUS`
      is large enough that a near-promotion enemy passer in a race outweighs
      White's own promotion plans.
- [ ] In `ai_search_helpers.py`, add a root-only penalty for ignoring a
      near-promotion enemy passer when one is present: if the opponent has
      a pawn within 2 squares of promotion, deprioritise moves that do not
      address it.
- [ ] Gate the penalty to low-material positions (≤ 6 non-pawn pieces).

### 4.4 Verify

- [ ] Run new regression tests — all must pass.
- [ ] Run the full fast test suite — no regressions.
- [ ] Run lint.

---

## Task 5: Integration — Self-Play Validation

### 5.1 Run 3 fresh self-play games

- [ ] Run:
  ```bash
  uv run python -m chess_game.self_play --white-depth 3 --black-depth 3
  ```
  three times, saving transcripts to:
  - `tmp/white_improvements2_game1.txt`
  - `tmp/white_improvements2_game2.txt`
  - `tmp/white_improvements2_game3.txt`

### 5.2 Evaluate improvement

For each game, check:
- [ ] Does White castle by move 25?
- [ ] Does White play h2-h3 within 5 moves of castling?
- [ ] Does White avoid losing KQvKR endgames through passive play?
- [ ] Does White stop near-promotion enemy pawns in endgame races?
- [ ] What are game lengths and results?

Record findings in `tmp/white_improvements2_validation.txt`.

### 5.3 Accept or iterate

- [ ] If White castles by move 25 in all 3 games → Task 2 success.
- [ ] If h3 appears within 5 moves of castling in ≥ 2 games → Task 1 success.
- [ ] If no KQvKR losses through passive rook play → Task 3 success.
- [ ] If no pawn-race blunders → Task 4 success.
- [ ] If any criterion fails → revisit the relevant task and increase the
      signal, then re-run.

### 5.4 Final verification gate

- [ ] `uv run python -m ruff check chess_game tests` — all clear.
- [ ] `uv run python -m mypy chess_game` — no errors.
- [ ] `uv run python -m pylint chess_game` — 10.00/10.
- [ ] `uv run python -m pytest tests/ -q -m "not slow"` — all pass.
- [ ] `uv run python -m pytest tests/ -q -m "slow"` — all pass.
- [ ] Update `memory.md` with timestamp, model used, and summary of changes.

---

## Task 6: Commit and Push

- [ ] Stage only source files and test files (not `tmp/` artifacts).
- [ ] Write a commit message summarising the four improvements.
- [ ] Push to `origin/master`.
- [ ] Update `docs/WHITE_IMPROVEMENTS2_TODO.md` to mark all tasks complete.
