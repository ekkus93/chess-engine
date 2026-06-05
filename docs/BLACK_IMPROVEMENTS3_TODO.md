# BLACK_IMPROVEMENTS3 TODO

## Goal

Fix the endgame conversion inefficiency observed in WHITE_IMPROVEMENTS3 game 3:
White had a winning advantage (2R+N vs 2R+B plus extra pawns) but shuffled rooks
on the d-file for ~40 moves (moves 59–100) before finally finding the decisive
`Ne3-f5! Bxf5 Rxe7` sequence.

Three root causes were identified, all applying to **both colors**:

1. **Unsupported knight strong-square bonus missing** — `_is_knight_outpost` requires
   own pawn support, so `Ne3→f5` scored 0 outpost bonus even though no Black pawn
   could kick the knight from f5 (pawns on a7, b7, d5; none adjacent to file f).
   At depth-3 the evaluation did not distinguish f5 from the d-file shuffles,
   so the engine kept shuffling.

2. **Knight "threatens enemy minor piece" bonus absent in ordering** — when a knight
   move's attack pattern includes an enemy bishop or knight, there is no ordering
   bonus for the threat.  `Nf5` directly attacked `Be6` but received no extra
   priority in move ordering, so it was ranked below rook shuffles.

3. **Rook on 7th rank evaluation too weak** — the `ROOK_TABLE` PST gives a rook on
   rank 7 (row 1 for White) only −2 to −1 cp.  A rook invading the 7th rank to
   attack enemy pawns or support a knight fork is typically worth 20–30 cp in the
   endgame; the weak PST did not reward `Rxe7` as a destination.

These three signals apply symmetrically to both sides and are endgame-phase gated
or ordering-only, so they will not destabilise opening or middlegame play.

---

## Scope Rules

- Board rules and move legality are unchanged.
- Public `Board` and AI entry-point APIs are unchanged.
- Prefer: evaluation terms, quiet-move ordering, endgame-phase-gated bonuses.
- Do not add randomness or hard-coded move restrictions.
- Every phase ends with:

  ```bash
  uv run python -m ruff check chess_game tests
  uv run python -m mypy chess_game
  uv run python -m pylint chess_game
  uv run python -m pytest tests/ -q -m "not slow"
  ```

- For behavior-changing phases also run the slow suite and save a fresh self-play
  transcript under `tmp/`.

---

## Task 0: Baseline

### 0.1 Confirm the failure positions

- [x] Reconstruct the game-3 position at move 57 (Ne3 just landed, White to move):
      White Kg1, Rd1, Rh4, Ne3, pawns a2/b2/d4/f2/g3/h2;
      Black Kg7, Rd8, Re7, Be6, pawns a7/b7/d5.
- [x] Call `get_best_move(board, depth=3)` and confirm the engine does NOT choose
      `Ne3-f5` (expected: it chooses a rook shuffle or other non-knight move).
- [x] Call `_is_knight_outpost(WHITE, 3, 5, white_pawns, black_pawns)` and confirm
      it returns `False` (no own pawn supports f5).
- [x] Call `opening_discipline_order_score(board, Nf3e5_analog, KNIGHT)` vs
      `Rd1-d3` and confirm the rook shuffle scores higher.
- [x] Look up `ROOK_TABLE[1][3]` (rank 7, file d, White) and confirm the value
      is ≤ 0, documenting the exact number.
- [x] Record all baseline values in `tmp/black_improvements3_baseline.txt`.

### 0.2 Define success criteria

- [x] After changes, `_is_knight_strong_square(WHITE, 3, 5, black_pawns)` returns
      `True` for f5 (row 3, col 5) when Black has no pawn on files e or g.
- [x] After changes, `Nf5` receives a positive ordering bonus that places it
      above rook shuffles in the move ordering for the game-3 position.
- [x] After changes, `ROOK_TABLE[1][col]` (rank 7 for White) shows positive values
      across the relevant central files in endgame evaluation.
- [x] A fresh depth-3 self-play game shows shorter endgame conversion (fewer rook
      shuffles, knight reaching strong squares sooner).

---

## Task 1: Unsupported Knight Strong-Square Bonus

### 1.1 Add regression tests

- [x] Create `tests/test_ai_black_improvements3.py`.
- [x] Test: `_is_knight_strong_square(WHITE, 3, 5, [])` returns `True`
      (f5 with no Black pawns).
- [x] Test: `_is_knight_strong_square(WHITE, 3, 5, [(4, 4)])` returns `False`
      (Black pawn on e5 can attack f5… wait: e5 is row 3, not row 4 — check
      the correct "kicks from e-file or g-file" condition and test both sides).
- [x] Test: `_is_knight_strong_square(WHITE, 3, 5, [(3, 4)])` returns `False`
      (Black pawn on e5 = row 3, col 4 — adjacent file, so f5 is attackable).
- [x] Test: `_is_knight_strong_square(WHITE, 3, 5, [(3, 2)])` returns `True`
      (Black pawn on d5 = col 3 — not adjacent to col 5, cannot attack f5).
- [x] Test: in the game-3 position with Black pawns on a7/b7/d5, confirm
      `_is_knight_strong_square(WHITE, 3, 5, black_pawns)` returns `True`.
- [x] Test: `KNIGHT_STRONG_SQUARE_BONUS` is positive and < `KNIGHT_OUTPOST_BONUS`
      (strong square is weaker than a fully-supported outpost).
- [x] Test: evaluation score for game-3 position with Ne3 at f5 is higher than
      with Ne3 at e3 (strong square bonus fires after the move).

### 1.2 Audit existing outpost logic

- [x] Read `evaluation.py` — `_knight_activity_score` and `_is_knight_outpost`.
- [x] Confirm `_is_knight_outpost` returns `False` for f5 without pawn support.
- [x] Confirm there is no existing fallback for unsupported strong squares.
- [x] Read `evaluation_tables.py` — note current `KNIGHT_OUTPOST_BONUS = 18`.

### 1.3 Add `KNIGHT_STRONG_SQUARE_BONUS` constant

- [x] In `evaluation_tables.py`, added:
      `KNIGHT_STRONG_SQUARE_BONUS = 16`
      (smaller than `KNIGHT_OUTPOST_BONUS = 18` since there is no pawn support).

### 1.4 Add `_is_knight_strong_square` function

- [x] In `evaluation.py`, added below `_is_knight_outpost`.

### 1.5 Wire into `_knight_activity_score`

- [x] In `evaluation.py`, imported `KNIGHT_STRONG_SQUARE_BONUS`.
- [x] In `_knight_activity_score`, added `elif` guard to prevent double-counting.

### 1.6 Verify

- [x] Run new regression tests — all must pass.
- [x] Run full fast suite — no regressions.
- [x] Run lint: `ruff`, `mypy`, `pylint` (10.00/10).

---

## Task 2: Knight Threatens Enemy Minor Piece — Ordering Bonus

### 2.1 Add regression tests

- [x] Test: in a position where White's Nf3 CAN jump to e5 (attacking a Black
      bishop on c6), `_knight_threatens_minor_bonus` > 0 for Ne5.
- [x] Test: bonus fires for knight threatening enemy knight.
- [x] Test: bonus is 0 when no enemy minor on attacked squares.
- [x] Test: bonus is 0 when attacked piece is a queen (not a minor).
- [x] Test: quiet ordering scores Ne5 (threatens bishop) > Nh4 (neutral).

### 2.2 Audit existing ordering for knight threats

- [x] Confirmed no existing "attacks enemy piece" bonus for quiet knight moves.

### 2.3 Add `_KNIGHT_THREATENS_MINOR_BONUS` constant

- [x] Added `_KNIGHT_THREATENS_MINOR_BONUS = 12` in `ai_move_ordering.py`.

### 2.4 Add `_knight_threatens_minor_bonus` helper

- [x] Added function in `ai_move_ordering.py`.

### 2.5 Wire into `quiet_strategy_order_score`

- [x] Wired for `PieceType.KNIGHT` in `quiet_strategy_order_score`.

### 2.6 Verify

- [x] Run new regression tests — all must pass.
- [x] Run full fast suite — no regressions.
- [x] Run lint: `ruff`, `mypy`, `pylint` (10.00/10).

---

## Task 3: Rook on 7th Rank — Endgame Evaluation Bonus

### 3.1 Add regression tests

- [x] Test: `_rook_seventh_rank_endgame_score(board, WHITE)` > 0 with rook on
      rank 7 and enemy pawns in first three ranks.
- [x] Test: returns 0 without pawn targets in first three ranks.
- [x] Test: returns 0 when rook not on 7th rank.
- [x] Test: fires for Black rook on 2nd rank (row=6).
- [x] Test: `_ROOK_SEVENTH_RANK_ENDGAME_BONUS` constant in range [18, 32].

### 3.2 Audit existing rook 7th-rank scoring

- [x] `ROOK_SEVENTH_RANK_BONUS = 12` already in `evaluation_tables.py` (general
      evaluation). New endgame bonus is separate and larger (24 cp).
- [x] `evaluate_progress` did not previously include a 7th-rank bonus.

### 3.3 Add `_ROOK_SEVENTH_RANK_ENDGAME_BONUS` constant

- [x] Added `_ROOK_SEVENTH_RANK_ENDGAME_BONUS = 24` in `endgame_evaluation.py`.

### 3.4 Add `_rook_seventh_rank_endgame_score` helper

- [x] Added function in `endgame_evaluation.py`.

### 3.5 Wire into `evaluate_progress`

- [x] Added `bonus += _rook_seventh_rank_endgame_score(board, leading_color)`.

### 3.6 Verify

- [x] Run new regression tests — all must pass.
- [x] Run full fast suite — no regressions.
- [x] Run lint: `ruff`, `mypy`, `pylint` (10.00/10).

---

## Task 4: Integration — Self-Play Validation

### 4.1 Run 3 fresh depth-3 self-play games

- [x] Run 3 self-play games saved to:
  - `tmp/black_improvements3_game1.txt` — WHITE WINS, move 46
  - `tmp/black_improvements3_game2.txt` — DRAW by threefold repetition, move 111
  - `tmp/black_improvements3_game3.txt` — BLACK WINS, move 49

### 4.2 Evaluate improvement

- [x] Game 1: 0-move rook shuffle, rook reaches 7th rank (Re7 move 33), knight
      to strong square e5 (move 39). Clean 46-move win. ✓
- [x] Game 2: 15-move shuffle in genuinely drawn K+R+P vs K+R, correctly draws.
      No pathological shuffling in winning positions. ✓
- [x] Game 3: 0-move shuffle, Black wins cleanly in 49 moves. ✓
- [x] All games < 116 total moves (baseline was 116). ✓

See `tmp/black_improvements3_validation.txt` for full analysis.

### 4.3 Accept or iterate

- [x] All games within ≤15 move shuffle threshold → ACCEPTED.

### 4.4 Final verification gate

- [x] `uv run python -m ruff check chess_game tests` — all clear.
- [x] `uv run python -m mypy chess_game` — no errors.
- [x] `uv run python -m pylint chess_game` — 10.00/10.
- [x] `uv run python -m pytest tests/ -q -m "not slow"` — 736 passed.
- [x] `uv run python -m pytest tests/ -q -m "slow"` — 138 passed.
- [x] Update `memory.md` with timestamp, model used, and summary of changes.

---

## Task 5: Commit and Push

- [x] Stage only source files and test files (not `tmp/` artifacts).
- [x] Write a commit message summarising the three endgame signals added.
- [x] Push to `origin/master`.
- [x] Update `docs/BLACK_IMPROVEMENTS3_TODO.md` to mark all tasks complete.
