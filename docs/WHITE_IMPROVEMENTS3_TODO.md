# WHITE_IMPROVEMENTS3 TODO

## Goal

Fix the castling urgency failure identified in WHITE_IMPROVEMENTS2 game 2:
White played b2-b4 / b4-b5 on moves 9-13 instead of developing the f1
bishop and castling, resulting in the king never formally castling and
Black winning in 201 moves.

Root causes identified:
1. `QUIET_FLANK_PAWN_POKE_PENALTY = 18` — ordering penalty for wing pawn
   poke while uncastled is too small (only -18 cp).
2. `castling_path_blocked_penalty` = flat 56 cp regardless of how many
   moves have passed — does not grow with urgency.
3. `_LATE_CASTLING_BASE_PENALTY = 16` — at fullmove 5 the scaling penalty
   is only 16 cp, trivially overridden by tactical pawn pressure.
4. `QUIET_CLEARS_CASTLING_PATH_BONUS = 36` — developing Bf1 to unblock
   castling gives too small a boost vs tactical alternatives.

## Scope

- Evaluation and move ordering only.
- No changes to legal move generation or public API.
- Every phase ends with:

  ```bash
  uv run python -m ruff check chess_game tests
  uv run python -m mypy chess_game
  uv run python -m pylint chess_game
  uv run python -m pytest tests/ -q -m "not slow"
  ```

---

## Task 0: Baseline

- [x] Confirmed game 2 failure: White never castled (king walked e1→f2→g1
      on moves 35-37). f1 bishop stayed home blocking kingside; queen on
      d1 blocked queenside.
- [x] At fullmove 5 (move 9, b2-b4): total anti-b4 signals = only 18+16+56
      = 90 cp — not enough to override tactical pawn pressure (~100+ cp).
- [x] Root cause: QUIET_FLANK_PAWN_POKE_PENALTY (18), late castling
      urgency (16 at fm5), castling_path_blocked (56 flat) all too weak.

---

## Task 1: Regression Tests

Add tests in `tests/test_ai_white_improvements3.py` that fail before the
fixes and pass after.

- [x] Test 1: `castling_path_blocked_penalty` grows with fullmove number —
      at fullmove 5 returns the base value (56), at fullmove 10 returns more.
- [x] Test 2: After developing the f1 bishop (clearing castling path),
      `castling_path_blocked_penalty` drops to 0.
- [x] Test 3: In the game-2 opening position at fullmove 5, developing
      Bf1 scores ≥ 40 cp higher in ordering than b2-b4.
- [x] Test 4: `late_castling_urgency_penalty` at fullmove 5 is ≥ 32 cp
      (reflects increased base penalty).
- [x] Test 5: Depth-3 search in game-2 style position prefers castling
      or bishop development over b2-b4 wing pawn push.

---

## Task 2: Increase Flank Pawn Poke Ordering Penalty

### 2.1 opening_move_ordering.py

- [x] Change `QUIET_FLANK_PAWN_POKE_PENALTY` from 18 to **40**.
- [x] Change `QUIET_CLEARS_CASTLING_PATH_BONUS` from 36 to **56**.

### 2.2 Verify

- [x] Regression tests for Task 1 pass (or at least Test 3 passes).
- [x] Full fast suite passes, no regressions.

---

## Task 3: Scale castling_path_blocked_penalty with Fullmove

### 3.1 opening_development.py

- [x] Change `castling_path_blocked_penalty` to return a scaled value:
      `min(_BISHOP_BLOCKS_CASTLING_PENALTY + 8 * max(0, fullmove - 6), 128)`.
      This means:
      - fullmove ≤ 6: 56 cp (unchanged for very early game)
      - fullmove 8: 72 cp
      - fullmove 10: 88 cp
      - fullmove 12: 104 cp
      - fullmove 15+: 128 cp (capped)

### 3.2 Verify

- [x] Test 1 (scaling) passes.
- [x] Full fast suite passes, no regressions.

---

## Task 4: Strengthen Late-Castling Urgency Scaling

### 4.1 opening_development.py

- [x] Change `_LATE_CASTLING_BASE_PENALTY` from 16 to **20**.
- [x] Change the threshold from `fullmove_number - 4` to
      `fullmove_number - 3` (starts one move earlier).
- [x] Change `_LATE_CASTLING_MAX_PENALTY` from 128 to **160**.
      New values:
      - fullmove 4: 20 cp
      - fullmove 5: 40 cp
      - fullmove 6: 60 cp
      - fullmove 8: 100 cp
      - fullmove 11+: 160 cp (capped)

### 4.2 Verify

- [x] Test 4 (fullmove 5 penalty ≥ 32) passes.
- [x] Full fast suite passes, no regressions.

---

## Task 5: Integration — Self-Play Validation

- [x] Run 3 depth-3 self-play games:
  ```bash
  uv run python -m chess_game.self_play --white-depth 3 --black-depth 3
  ```
  Save to `tmp/white_improvements3_game{1,2,3}.txt`.

- [x] For each game, check:
  - Does White castle formally (e1g1 or e1c1) by move 25?
  - Does White avoid playing b4/b5/a4 before castling?
  - What are game lengths and results?
  - G1: Black wins 49 moves, White castled move 7 ✓
  - G2: WHITE WINS 74 moves, White castled move 23 ✓, no pre-castle wing pawns ✓
  - G3: WHITE WINS 116 moves, White castled move 7 ✓

- [x] Accept if White castles by move 25 in all 3 games. ← PASS
- [x] If any game fails → revisit Task 2-4 and increase signals, re-run.

- [x] Final verification gate:
  ```bash
  uv run python -m ruff check chess_game tests
  uv run python -m mypy chess_game
  uv run python -m pylint chess_game
  uv run python -m pytest tests/ -q -m "not slow"
  uv run python -m pytest tests/ -q -m "slow"
  ```
  ← All pass: 715 fast + 139 slow, pylint 10.00/10, ruff clean, mypy clean.
- [x] Update `memory.md` with timestamp, model, and summary.

---

## Task 6: Commit and Push

- [x] Stage source and test files (not `tmp/`).
- [x] Write commit message summarising the three signal increases.
- [x] Push to `origin/master`.
- [x] Update `docs/WHITE_IMPROVEMENTS3_TODO.md` to mark all tasks complete.
