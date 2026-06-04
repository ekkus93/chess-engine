# WHITE_IMPROVEMENTS1 TODO

## Goal

Improve White's (and both sides') practical play based on the failure patterns
observed in `tmp/selfplay_varied_game2.txt`.  Three root causes were identified:

1. **No luft after castling** — White never played h3 or g3 after castling,
   leaving h2 completely undefended.  Black exploited this with the classic
   bishop-sacrifice pattern Bxh2+ on move 26 and delivered checkmate by move 34.

2. **Undefended h2/h7 evaluation blind spot** — White's evaluation did not
   recognise that a bishop aimed at h2 with no pawn shield created a king-safety
   emergency.  The h2 weakness was present from move 19 (castling) through move
   25 without any defensive response.

3. **Pawn-recapture blindness in exchanges (Nxe5 blunder)** — On move 15 White
   played Nf3-e5 intending to fork the Ng4 and Bd7, but failed to see that
   Black's d6-pawn could simply recapture on e5, winning a knight for a pawn.
   This is a "pseudo-fork" pattern where the forking piece can be immediately
   recaptured by an unguarded pawn.

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

- [x] Replay `tmp/selfplay_varied_game2.txt` up to move 15 (White's Nxe5 blunder)
      and record the exact board state.
- [x] Replay to move 19 (White castles, h2 undefended) and record board state.
- [x] Replay to move 25 (last move before Bxh2+) and record board state.
- [x] For each position, run `get_best_move(board, depth=3)` and confirm the
      bad move is chosen.
- [x] Save all three board states in `tmp/white_improvements1_baseline.txt`.

### 0.2 Audit existing signals

- [x] Check `opening_development.py` — does `opening_king_safety_score` or
      `_uncastled_shell_penalty` detect an undefended h2/h7 after castling?
- [x] Check `pawn_structure_evaluation.py` — does `_shelter_file_gap_penalty`
      fire for a missing h2/g2 pawn when the king is castled?
- [x] Check `ai_move_ordering.py` — does `QUIET_URGENT_LUFT_BONUS` or any
      luft signal fire at move 19-25 of game 2?
- [x] Check `defensive_priorities.py` — does `king_danger_index` or
      `king_defense_profile` flag the h2 weakness?
- [x] Document each gap in `tmp/white_improvements1_baseline.txt`.

### 0.3 Define success criteria

- [x] At depth=3, White plays h3 (or g3) within the first 5 moves after
      castling when h2 is undefended and queens are on the board.
- [x] At depth=3, White does not play Nxe5 in the game-2 position because
      the fork is answered by a pawn recapture.
- [x] A fresh self-play game no longer ends in the Bxh2+ mating pattern
      within 35 moves.

---

## Task 1: Luft Creation After Castling

The h3/g3 pawn move after castling is one of the most important defensive
principles in chess.  The engine currently has a luft bonus but it fires too
weakly or too late.

### 1.1 Add regression tests

- [x] Create (or extend) `tests/test_ai_white_improvements1.py`.
- [x] Reconstruct the move-19 board from game 2 (White just castled, h2 bare).
- [x] Assert `quiet_strategy_order_score(board, h2h3, None)` is among the top-3
      scoring quiet moves — i.e., the ordering strongly encourages luft.
- [x] Assert `get_best_move(board, depth=3)` does **not** choose a purely
      passive move (Re2, Bd2) when h2 is undefended and a bishop is aimed at it.
- [x] Add a move-ordering test for the castled position:
      `_move_order_score(board, h2h3, None)` > `_move_order_score(board, Re1e2, None)`.

### 1.2 Audit existing luft signals

- [x] Find `QUIET_LUFT_BONUS` and `QUIET_URGENT_LUFT_BONUS` in `ai_move_ordering.py`.
      Record their current values and the conditions that fire them.
- [x] Check `_defensive_priority_bonus` in `ai_move_ordering.py` — does it
      reward luft creation or only active defense?
- [x] Check `king_needs_shelter` in `defensive_priorities.py` — does it detect
      the h2-undefended pattern?

### 1.3 Add "h2/h7 exposed" evaluation penalty

- [x] In `opening_development.py` or `pawn_structure_evaluation.py`, add a
      `h_pawn_exposure_penalty(board, color)` function that fires when:
      - The king is castled kingside (at g1/g8).
      - The h2/h7 pawn is **absent** (already advanced or captured).
      - The enemy has a bishop or queen on a diagonal that attacks h2/h7.
      - Queens are still on the board.
- [x] Make the penalty proportional to how directly the attacking piece threatens
      h2/h7 (a bishop one move away = maximum penalty; two moves away = half).
- [x] Wire the new penalty into `evaluation.py` under the `king_safety` or
      `king_exposure` breakdown key.

### 1.4 Strengthen the luft ordering bonus

- [x] In `ai_move_ordering.py`, increase `QUIET_LUFT_BONUS` or add a new
      `QUIET_SHELTER_LUFT_BONUS` that fires specifically when:
      - The king is castled kingside.
      - The h2/h7 pawn is on its starting square (not yet advanced).
      - An enemy bishop or queen has line-of-sight to h2/h7 (even if blocked).
      - The move being considered is h2-h3 (or h7-h6 for Black).
- [x] The bonus should be large enough (≥ 36 cp) that h3 beats passive rook
      shuffles in ordering.

### 1.5 Add root tie-break signal

- [x] In `ai_search_helpers.py` (`_strategic_root_bonus`), add a root-only
      bonus for h-pawn luft moves when the king is castled and the h-file
      shelter is gone or threatened.
- [x] Gate the bonus to positions where the enemy has a piece that could
      exploit h2/h7 within 2 moves.

### 1.6 Verify

- [x] Run new regression tests — all must pass.
- [x] Run the full fast test suite — no regressions.
- [x] Run lint: `ruff`, `mypy`, `pylint` (10.00/10).

---

## Task 2: Bishop-Sacrifice Target Awareness (h2/h7 King-Safety)

Even if luft is created, the engine should recognise when h2 is under attack
before the bishop arrives — treating the diagonal threat as a king-danger signal.

### 2.1 Add regression tests

- [x] Reconstruct the move-25 board (position just before Bxh2+).
- [x] Assert `king_danger_index(board, Color.WHITE)` ≥ some threshold that
      would trigger defensive priority ordering.
- [x] Assert that `quiet_strategy_order_score` rewards defensive moves
      (g2-g3, Rf1-h1) over offensive moves (Re2-e3) in this position.
- [x] Assert that the move-order score for h2-h3 or g2-g3 is highest among
      all quiet moves in this position.

### 2.2 Add diagonal bishop-threat detection to king danger

- [x] In `defensive_priorities.py`, extend `king_defense_profile` or
      `king_danger_index` to detect when an enemy bishop has an unobstructed
      or near-unobstructed diagonal leading to h2 (or h7 for Black).
- [x] A bishop on d6 targeting h2 with no pieces in between should raise the
      danger score by at least 2 points (equivalent to an open invasion line).
- [x] A bishop on c5/e3 with one piece in between should raise it by 1 point.

### 2.3 Wire the new danger signal into ordering

- [x] Ensure the higher danger score from 2.2 causes `_defensive_priority_bonus`
      in `ai_move_ordering.py` to rank defensive moves (h3, g3, Rh1) higher.
- [x] Confirm that `QUIET_DANGER_RELIEF_BONUS` fires for moves that block the
      diagonal (interposing a piece between the bishop and h2).

### 2.4 Verify

- [x] Run new regression tests — all must pass.
- [x] Run the full fast test suite — no regressions.
- [x] Run lint.

---

## Task 3: Pseudo-Fork Penalty (Pawn-Recapture Blindness)

On move 15 White played Nxe5 as a "fork" but Black immediately won the knight
with dxe5 — a pawn recapture White should have seen coming.

### 3.1 Add regression tests

- [x] Reconstruct the move-14 board (White to move after Black played ...e7-e5).
- [x] Assert `get_best_move(board, depth=3)` does **not** choose Nf3-e5.
- [x] Assert `capture_order_score(board, Nf3e5)` is negative or very low when
      the landing square can be immediately recaptured by an enemy pawn.
- [x] Assert that a defensive move (e.g. Bf4-e3 or d4xe5) scores higher than
      Nf3-e5 in quiet or capture ordering at this position.

### 3.2 Add pseudo-fork detection to capture ordering

- [x] In `ai_capture_ordering.py`, add a penalty for captures where:
      - The capturing piece is a knight (or bishop).
      - The destination square is currently attacked by **at least one enemy pawn**
        that is not also attacked by a friendly pawn of equal or greater value.
      - The capture is not delivering check.
      - The piece being captured is worth less than the capturing piece (i.e.
        the knight is capturing a pawn or is capturing into a losing trade).
- [x] Name the function `_pawn_recapture_risk_penalty` or similar.
- [x] The penalty should be large enough (≥ piece value difference) to make
      such captures rank below safe alternatives in ordering.

### 3.3 Extend evaluation for hanging piece after fork attempt

- [x] In `evaluation.py` or `piece_coordination.py`, add a small evaluation
      penalty for a position where a knight (or bishop) has just landed on a
      square attacked by an enemy pawn — i.e., the piece is en-prise to a pawn.
- [x] This is a static signal: "if any own piece is attacked by an enemy pawn
      and not defended, penalise the position."
- [x] Gate the penalty to middlegame positions to avoid over-penalising
      endgame pawn chains.

### 3.4 Verify

- [x] Run new regression tests — all must pass.
- [x] Run the full fast test suite — no regressions.
- [x] Run lint.

---

## Task 4: Passive Bishop Penalty

On move 17 White retreated the bishop to d2, blocking the d-file and contributing
nothing for the rest of the game.

### 4.1 Add regression tests

- [x] Reconstruct the move-16 board (after Black dxe5, White to move).
- [x] Assert that `quiet_strategy_order_score(board, Bf4d2, None)` is **lower**
      than an active bishop move (e.g. Bf4-e3 developing/defending).
- [x] Assert that the bishop-retreat-to-back-rank penalty from BLACK_IMPROVEMENTS1
      also fires for White's bishops (it should — the penalty is symmetric).

### 4.2 Audit the existing bishop penalty

- [x] Check `_bishop_passive_retreat_penalty` in `ai_move_ordering.py` — does
      it fire for White's Bf4-d2 move?  (d2 is NOT the back rank for White, so
      it may not fire.)
- [x] If Bf4-d2 is not caught, extend the penalty to cover moves that:
      - Retreat a bishop to the **second rank** (rank 2 for White, rank 7 for
        Black — the rank just in front of the home rank).
      - Move the bishop to a square where it is blocked by its own pawns on
        the same diagonal.
      - Reduce the bishop's mobility by ≥ 3 squares compared to its current
        position.

### 4.3 Add second-rank bishop penalty

- [x] In `ai_move_ordering.py`, add or extend `_bishop_passive_retreat_penalty`
      to also fire when a bishop retreats to the **second rank** (rank 2 for
      White, rank 7 for Black) while queens are on the board and the bishop
      has better squares available.
- [x] The penalty should be proportional to mobility loss.

### 4.4 Verify

- [x] Run new regression tests — all must pass.
- [x] Run the full fast test suite — no regressions.
- [x] Run lint.

---

## Task 5: Integration — Self-Play Validation

### 5.1 Run 3 fresh self-play games

- [x] Run:
  ```bash
  uv run python -m chess_game.self_play --white-depth 3 --black-depth 3
  ```
  three times, saving transcripts to:
  - `tmp/white_improvements1_game1.txt`
  - `tmp/white_improvements1_game2.txt`
  - `tmp/white_improvements1_game3.txt`

### 5.2 Evaluate improvement

For each game, check:
- [x] Does White create luft (h3 or g3) within 5 moves of castling?
- [x] Does the Bxh2+ mating pattern occur in any game?
- [x] Are there any Nxe5-style pseudo-fork blunders?
- [x] What are the game lengths and results vs the baseline games?

Record findings in `tmp/white_improvements1_validation.txt`.

### 5.3 Accept or iterate

- [x] If the Bxh2+ pattern is eliminated in all 3 games → mark this TODO complete.
- [x] If pseudo-fork blunders still appear → revisit Task 3 and increase the
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
- [x] Write a commit message summarising the three improvements.
- [x] Push to `origin/master`.
- [x] Update `docs/WHITE_IMPROVEMENTS1_TODO.md` to mark all tasks complete.
