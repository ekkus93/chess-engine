# BLACK_IMPROVEMENTS1 TODO

## Goal

Improve Black's practical play based on recurring weaknesses observed in the
`tmp/selfplay_d3d3_20260603.txt` depth-3 self-play transcript.  Four distinct
problems were identified:

1. **Rim knight** — Black played Nc6-a5 on move 8, leaving the knight
   passively on the board edge for the rest of the game.
2. **Premature kingside pawn advances** — Black pushed g7-g5 (move 20) and
   h7-h5 (move 26) without compensation, weakening the castled king's shelter.
3. **Rook shuffling** — Black's rook oscillated between e7 and e8 multiple
   times with no progress.
4. **Passive bishop retreat** — Black retreated Bd7-c8 (move 38) when more
   active options were available.

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
  under `tmp/` and record the result in memory.md.

---

## Task 0: Baseline and Regression Setup

### 0.1 Capture the failure positions

- [x] Open `tmp/selfplay_d3d3_20260603.txt` and replay the game move by move.
- [x] Record the exact board state at move 8 (Nc6-a5 — rim knight).
- [x] Record the exact board state at move 20 (g7-g5 — first shelf pawn push).
- [x] Record the exact board state at move 26 (h7-h5 — second shelter push).
- [x] Record the exact board state at move 38 (Bd7-c8 — passive bishop retreat).
- [x] For each position, run `get_best_move(board, depth=3)` and confirm the
      bad move is currently chosen.
- [x] Save the four board states in `tmp/black_improvements1_baseline.txt`.

### 0.2 Identify active heuristics at each failure point

- [x] At move 8 (Na5): check what `opening_move_ordering.py` and
      `opening_development.py` currently score for Na5 vs Nd4 or Nc6-stay.
- [x] At move 20 (g5): check what `pawn_structure_evaluation.py` scores for
      the shelter pawn advance with the castled king at g8.
- [x] At move 26 (h5): same shelter check with queens still on the board.
- [x] At move 38 (Bd7-c8): check what `ai_move_ordering.py` quiet ordering
      scores for the retreat vs a more active alternative.
- [x] Document each gap in `tmp/black_improvements1_baseline.txt`.

### 0.3 Define success criteria

- [x] At depth=3, the Na5 move is **not** chosen; a more central/useful
      Black knight move is preferred.
- [x] At depth=3, g7-g5 is **not** chosen while the castled king shelter is
      intact and White's queen is still active.
- [x] At depth=3, h7-h5 is **not** chosen in the same context.
- [x] At depth=3, Bd7-c8 retreat is replaced by a more active bishop move.
- [x] A fresh depth-3 self-play game shows fewer or none of these four patterns.

---

## Task 1: Rim Knight Penalty

### 1.1 Add regression tests

- [x] Create `tests/test_ai_black_improvements1.py` (or add to an existing
      regression file).
- [x] Add a test that reconstructs the move-8 board from the transcript.
- [x] Assert `get_best_move(board, depth=3) != LegalMove(Nc6→a5)`.
- [x] Also assert that `opening_discipline_order_score` scores Nc6→a5 lower
      than Nc6→d4 or another central destination.
- [x] Mark depth-3 best-move tests with `pytest.mark.slow`.

### 1.2 Audit existing rim-knight penalty

- [x] Read `chess_game/chess/opening_move_ordering.py` — find the existing
      rim-knight penalty (previously added for `...Nh6`).
- [x] Check that the penalty also fires for knight moves to a5, h5, a4, h4
      (all four rim squares reachable from a developed knight).
- [x] Check that the penalty scale is large enough to survive the depth-3
      root tie-break at move 8 of a Sicilian.

### 1.3 Strengthen rim-knight evaluation signal

- [x] In `chess_game/chess/opening_development.py`, add or increase the
      penalty for a knight landing on any rim square (col 0 or col 7) during
      the opening phase (move count ≤ 15 or undeveloped pieces > 0).
- [x] Use phase-weighted scaling so the penalty is strongest before castling
      and fades in pure endgames.
- [x] Wire the new penalty into `evaluation.py` under the `development` key.

### 1.4 Strengthen root tie-break

- [x] In `chess_game/chess/ai_search_helpers.py`, add a root-only override
      that vetoes a rim knight move when an alternative exists with a score
      within `ROOT_TIEBREAK_MARGIN` of the best raw score.
- [x] Gate the override to the opening phase only (same phase condition as 1.3).

### 1.5 Verify

- [x] Run new regression tests — all must pass.
- [x] Run the full fast test suite — no regressions.
- [x] Run lint: `ruff`, `mypy`, `pylint` (10.00/10).

---

## Task 2: Premature Kingside Shelter Pawn Advances

### 2.1 Add regression tests

- [x] Add a test for the move-20 board state (g7-g5 while king is at g8 and
      queens are on the board).
- [x] Assert `get_best_move(board, depth=3)` does not choose g7-g5.
- [x] Add a test for the move-26 board state (h7-h5 in the same context).
- [x] Assert `get_best_move(board, depth=3)` does not choose h7-h5.
- [x] Add a move-ordering test: `_move_order_score(board, g5_push, None)` <
      `_move_order_score(board, a_reasonable_alternative, None)`.

### 2.2 Audit existing shelter penalty

- [x] Read `chess_game/chess/pawn_structure_evaluation.py` — find the existing
      castled-king shelter-pawn penalty (added in STRATEGY4).
- [x] Verify the penalty correctly fires for g7-g5 and h7-h5 when the king
      is at g8 (kingside castled, Black side).
- [x] Check whether the penalty is queen-scaled (should be heavier when the
      enemy queen is still on the board).

### 2.3 Strengthen shelter advance penalty in evaluation

- [x] In `chess_game/chess/pawn_structure_evaluation.py`, ensure the g/h pawn
      advance penalty is multiplied by a queen-present factor: if the opponent
      has a queen, apply 1.5× the base penalty.
- [x] The penalty should apply to both the file the pawn starts on (g or h)
      and the resulting shelter gap it creates.

### 2.4 Strengthen quiet-order penalty

- [x] In `chess_game/chess/ai_move_ordering.py` or
      `chess_game/chess/opening_move_ordering.py`, add an explicit quiet-order
      penalty for g/h pawn pushes by the castled side when:
      - The king is castled kingside.
      - The advancing pawn is a g2/g7 or h2/h7 shelter pawn.
      - The enemy queen is still on the board.
      - The advance does not capture or deliver check.
- [x] The penalty must be large enough to consistently suppress the move
      at depth=3 in the opening/early middlegame.

### 2.5 Add root tie-break signal

- [x] In `chess_game/chess/ai_search_helpers.py` (`_strategic_root_bonus`),
      add a negative bonus for shelter pawn advances that match the above
      criteria, so the root tiebreak also discourages the pattern.

### 2.6 Verify

- [x] Run new regression tests — all must pass.
- [x] Run the full fast test suite — no regressions.
- [x] Run lint.

---

## Task 3: Rook Shuffling / Anti-Drift

### 3.1 Add regression tests

- [x] Reconstruct the position around move 29 where Black's rook was
      oscillating between e7 and e8.
- [x] Assert that `quiet_strategy_order_score` penalizes the move that
      directly reverses the previous rook move.
- [x] Assert that `get_best_move(board, depth=3)` does not return the
      reversing rook move when a more productive alternative exists.

### 3.2 Audit existing anti-repetition / anti-drift machinery

- [x] Read `chess_game/chess/ai_repetition_patterns.py` —
      `move_undoes_last_own_move()`.
- [x] Confirm it correctly detects the Re7→e8 reversal when the last own
      move was Re8→e7.
- [x] Read `chess_game/chess/anti_drift_guidance.py` — check whether heavy
      piece anti-shuffle penalties apply in non-race, non-endgame middlegame
      positions with queens still on the board.
- [x] Check `chess_game/chess/ai_move_ordering.py` — confirm
      `quiet_cycle_penalty` fires for the repeated rook moves.

### 3.3 Strengthen mid-game rook shuffle penalty

- [x] In `chess_game/chess/ai_move_ordering.py`, increase the quiet-cycle
      penalty weight for rook moves that directly undo the previous rook move
      in middlegame positions (more than 6 non-pawn pieces per side).
- [x] Ensure the penalty applies even when the rook is on a "useful" file
      but bouncing between two squares on that file.

### 3.4 Add anti-drift signal for purposeless rook triangulation

- [x] In `chess_game/chess/anti_drift_guidance.py`, extend the existing
      anti-drift order bonus to also penalise rook moves that:
      - Return the rook to its exact square from two moves ago (already done
        by `quiet_cycle_penalty`).
      - Move the rook along a rank/file where it already has the optimal
        position (no new file opened, no new rank pressure, no discovered
        attack).
- [x] Gate the extension to middlegame positions where the position is not
      a forced race.

### 3.5 Verify

- [x] Run new regression tests — all must pass.
- [x] Run the full fast test suite — no regressions.
- [x] Run lint.

---

## Task 4: Passive Bishop Retreat

### 4.1 Add regression tests

- [x] Reconstruct the move-38 position (Bd7-c8 retreat).
- [x] Identify the best alternatives at that moment (e.g., a capturing move
      or the bishop finding an active diagonal).
- [x] Assert `get_best_move(board, depth=3)` does not choose Bd7-c8 when
      a clearly superior active bishop move is available.
- [x] Add a move-ordering assertion: the retreat scores lower than the
      active alternative.

### 4.2 Audit existing piece-coordination signals

- [x] Read `chess_game/chess/piece_coordination.py` — check
      `worst_piece_improvement_bonus` for bishops.
- [x] Check `chess_game/chess/low_material_coordination_guidance.py` — does
      it fire for middlegame bishop positions?
- [x] Check `chess_game/chess/opening_development.py` — does it penalise a
      bishop retreating to a square it already occupied earlier in the game?

### 4.3 Add bishop retreat penalty

- [x] In `chess_game/chess/ai_move_ordering.py`, add a quiet-order penalty
      for any bishop move that:
      - Returns the bishop to a square it previously occupied (same piece,
        same square, within the last 10 moves or so — reuse position history
        if available, otherwise approximate with last-own-move check).
      - Reduces the bishop's mobility (fewer attacks from the destination
        vs the current square).
      - Is not a forced recapture.
- [x] The penalty should be proportional to the mobility reduction.

### 4.4 Strengthen piece-coordination ordering for bishops

- [x] In `chess_game/chess/piece_coordination.py`, extend
      `worst_piece_improvement_bonus` so that improving the worst-placed
      bishop (lowest mobility) gets a larger bonus than a passive retreat for
      a bishop that was already reasonably active.
- [x] Wire the extended signal into quiet ordering via `ai_move_ordering.py`.

### 4.5 Verify

- [x] Run new regression tests — all must pass.
- [x] Run the full fast test suite — no regressions.
- [x] Run lint.

---

## Task 5: Integration — Self-Play Validation

### 5.1 Run multiple self-play games

- [ ] Run at least 3 fresh depth-3 self-play games:
  ```bash
  uv run python -m chess_game.self_play --white-depth 3 --black-depth 3
  ```
- [x] Save each transcript to `tmp/black_improvements1_game<N>.txt`.

### 5.2 Evaluate improvement

For each game, check:
- [x] Does Black play Na5 (or another rim knight) in the opening?
- [x] Does Black push g5 or h5 before move 25 while still castled and under queen pressure?
- [x] Does Black's rook shuffle between the same two squares more than once consecutively?
- [x] Does Black play a clearly passive bishop retreat when active alternatives exist?

Record findings in `tmp/black_improvements1_validation.txt`.

### 5.3 Accept or iterate

- [x] If all four weaknesses are reduced or eliminated → mark this TODO complete.
- [x] If one or more persist → revisit the relevant task and increase signal
      strength, then re-run.

### 5.4 Final verification gate

- [x] `uv run python -m ruff check chess_game tests` — all clear.
- [x] `uv run python -m mypy chess_game` — no errors.
- [x] `uv run python -m pylint chess_game` — 10.00/10.
- [ ] `uv run python -m pytest tests/ -q -m "not slow"` — all pass.
- [ ] `uv run python -m pytest tests/ -q -m "slow"` — all pass.
- [x] Update `memory.md` with timestamp, model used, and summary of changes.

---

## Task 6: Commit and Push

- [x] Stage only source files and test files (not `tmp/` artifacts).
- [x] Write a commit message summarising the four improvements.
- [x] Push to `origin/master`.
- [x] Update `docs/BLACK_IMPROVEMENTS1_TODO.md` to mark all tasks complete.
