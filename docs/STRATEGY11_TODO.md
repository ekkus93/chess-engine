# STRATEGY11: Tactical Safety, Endgame Technique, and Move-1 Discipline TODO

## Overview

STRATEGY10 improved White's opening coherence and Black's conversion urgency, but the latest depth-3 self-play revealed three deeper structural gaps:

1. **Black cannot hold a large advantage** — Black was up +7 at move 70 but collapsed to +1 by move 80. Two mechanisms caused this: (a) Black walked into a tactic and lost 5 material in one White reply (move 71); (b) a queen trade swapped Black's main conversion weapon away, turning a won game into a level endgame.

2. **White still plays Nc3 on move 1** — The STRATEGY10 central-pawn root bonus fires too late. White must prefer 1.e4 or 1.d4 from the very first move, not merely from move 3 onward.

3. **Endgame technique is slow** — After winning a rook (move 111), White required 90 more moves to convert a Rook vs. Bishop+King advantage. Black also failed to convert a Rook+Bishop vs. Rook advantage earlier (moves 100–111). Pure endgame technique needs direct king-centralization and piece-coordination guidance.

This round focuses on move safety, advantage preservation, and endgame technique.

## Relevant Files

- `chess_game/chess/opening_guidance.py` — opening discipline gate and pattern bonuses
- `chess_game/chess/ai_search_helpers.py` — root tie-breaks including opening and conversion bonuses
- `chess_game/chess/conversion_guidance.py` — winning conversion move ordering and root bonuses
- `chess_game/chess/endgame_evaluation.py` — endgame progress, king activity, and practical conversion signals
- `chess_game/chess/evaluation.py` — evaluation aggregation
- `chess_game/chess/ai_move_ordering.py` — quiet move ordering heuristics
- `tests/test_ai_strategy11_regressions.py` — new regression coverage for this round

---

## Task 0 — Baseline capture and test scaffolding

**Goal:** Record the current weaknesses in concrete regression fixtures before changing strategy.

- [x] **0a** Record the three key failure positions from `tmp/strategy10_acceptance.txt`:
  - Move-71 position: Black is +7 but moves into a 5-point tactical swing.
  - Move-79 position: Queens trade off while Black is ahead, collapsing advantage.
  - Move-111 position: White has Rook vs. Bishop+King and takes 90 moves to convert.
- [x] **0b** Note the opening: White's move 1 is still Nc3. Save notes to `tmp/strategy11_baseline_notes.txt`.
- [x] **0c** Create `tests/test_ai_strategy11_regressions.py` with board helpers for:
  - Tactical-safety probes (don't move into tactically unsafe squares when ahead).
  - Anti-queen-trade probes (when clearly ahead, avoid queen swaps).
  - Endgame-technique probes (R vs B+K king activation, R+B vs R coordination).
  - Move-1 probe (White should prefer e4 or d4 on move 1).
- [x] **0d** Add baseline assertions that expose the current weaker behaviors.

---

## Task 1 — Fix White's move-1 central-pawn preference

**Goal:** Ensure White plays 1.e4 or 1.d4 as its very first move in all standard starting positions.

**Files:** `chess_game/chess/ai_search_helpers.py`, `chess_game/chess/opening_guidance.py`

- [x] **1a** Audit `_opening_central_pawn_root_bonus()` to understand why it does not fire on move 1 even though the opening gate is active.
- [x] **1b** Add a `_move1_central_pawn_bonus()` root helper that fires specifically when:
  - All pieces are on their starting ranks (or effectively on move 1).
  - The candidate move is a d-file or e-file pawn advance by two squares.
  - A larger constant (`_MOVE1_CENTRAL_PAWN_BONUS`) is applied to break ties against Nc3/Nf3/etc.
- [x] **1c** Call `_move1_central_pawn_bonus()` from `_opening_root_bonus()` and ensure it supersedes the existing move-1 quiet ordering.
- [x] **1d** Confirm the bonus does not apply after move 1 (guard on ply count or piece density on starting squares).
- [x] **1e** Add regression test `test_strategy11_white_prefers_e4_or_d4_on_move1`.
- [x] **1f** Add regression test `test_strategy11_move1_bonus_does_not_fire_in_late_opening`.

---

## Task 2 — Black advantage preservation: penalise unsafe moves when clearly ahead

**Goal:** When Black has a material lead ≥ +4, penalise candidate moves that leave a piece on a square where it can be immediately captured by an opponent piece of lesser or equal value.

**Files:** `chess_game/chess/ai_move_ordering.py`, `chess_game/chess/ai_search_helpers.py`

- [x] **2a** Write a `_piece_is_immediately_capturable(board, square, color)` helper in `ai_move_ordering.py` (or a new `move_safety_guidance.py`) that returns True if any opponent piece attacks `square` and the capture would be material-positive for the opponent.
- [x] **2b** Add a `_advantage_preservation_quiet_penalty(board, move, side, material_lead)` function:
  - Only activates when `side`'s material lead ≥ 4 points.
  - Applies a negative bonus when the move places an unguarded piece where it can be captured for free.
  - Must not apply in forcing/capture lines — quiet-move ordering only.
- [x] **2c** Feed the new penalty into `_get_quiet_move_score()` in `ai_move_ordering.py`.
- [x] **2d** Ensure the penalty does not fire in equal or behind positions, nor during captures.
- [x] **2e** Add regression test `test_strategy11_black_avoids_hanging_pieces_when_ahead`.
- [x] **2f** Add regression test `test_strategy11_safety_penalty_inactive_in_equal_positions`.

---

## Task 3 — Black advantage preservation: anti-queen-trade heuristic when clearly ahead

**Goal:** When Black has a material lead ≥ +4 and both queens are on the board, penalise Black queen moves to squares where the queen can be captured or traded within one ply.

**Files:** `chess_game/chess/conversion_guidance.py`, `chess_game/chess/ai_search_helpers.py`

- [x] **3a** Add a `_anti_queen_trade_root_penalty(board, move, side, context)` helper in `conversion_guidance.py`:
  - Activates when: side is materially ahead ≥ +4, both queens are on the board, and the candidate move puts the moving side's queen on a square attacked by the opponent's queen or a piece of lesser value.
  - Applies a negative root bonus (`_ANTI_QUEEN_TRADE_PENALTY`).
  - Must not fire in positions where the queen move also wins material (i.e., not a blunder-deterrent — only a trade-deterrent).
- [x] **3b** Call the penalty from `winning_conversion_root_bonus()` when the context is active.
- [x] **3c** Tune `_ANTI_QUEEN_TRADE_PENALTY` so it overrides typical positional tie-breaks but not clearly winning tactical moves.
- [x] **3d** Add regression test `test_strategy11_black_avoids_queen_trade_when_clearly_ahead`.
- [x] **3e** Add regression test `test_strategy11_anti_queen_trade_inactive_in_level_positions`.

---

## Task 4 — Endgame technique: Rook vs. Bishop+King conversion

**Goal:** When the winning side has a Rook and the opponent has only a Bishop+King (or Bishop+one pawn), speed up conversion by rewarding king centralization and rook activity.

**Files:** `chess_game/chess/endgame_evaluation.py`, `chess_game/chess/simple_endgame_guidance.py`

- [x] **4a** Audit `simple_endgame_guidance.py` to understand where pure R vs B+K is handled (or missing).
- [x] **4b** Add a `_rook_vs_bishop_king_conversion_bonus(board, side)` helper in `endgame_evaluation.py`:
  - Activates when: the winning side has exactly one rook and no other pieces (aside from king+pawns), and the losing side has only a bishop (plus king).
  - Rewards the winning king moving toward the center/opponent king.
  - Rewards the rook cutting off the losing king along ranks/files.
  - Adds a tempo urgency bonus so the winning side doesn't shuffle.
- [x] **4c** Feed the helper into `endgame_evaluation()` score.
- [x] **4d** Ensure the helper does not fire in double-rook or queen endgames.
- [x] **4e** Add regression test `test_strategy11_rook_vs_bishop_king_activates_king`.
- [x] **4f** Add regression test `test_strategy11_rook_vs_bishop_king_cuts_off_king_with_rook`.

---

## Task 5 — Endgame technique: Rook+Bishop vs. Rook coordination

**Goal:** When the winning side has a Rook+Bishop vs. a lone Rook, reward piece coordination: rook supports pawn(s) or cuts off the enemy king, bishop covers key squares, and the king advances.

**Files:** `chess_game/chess/endgame_evaluation.py`

- [x] **5a** Audit the current rook endgame handling to identify what is already scored and what is missing for R+B vs R.
- [x] **5b** Add a `_rook_bishop_vs_rook_conversion_bonus(board, side)` helper:
  - Activates when: the winning side has exactly one rook and one bishop (plus king), and the losing side has only a rook.
  - Rewards the bishop controlling squares that restrict the opponent rook.
  - Rewards the rook supporting any passed pawn or pushing toward the 7th rank.
  - Rewards the winning king approaching the opponent king.
- [x] **5c** Feed the helper into `endgame_evaluation()`.
- [x] **5d** Ensure the helper stays quiet in balanced R+B vs R positions (no pawn imbalances, no king exposure).
- [x] **5e** Add regression test `test_strategy11_rook_bishop_vs_rook_coordinates_pieces`.
- [x] **5f** Add regression test `test_strategy11_rook_bishop_vs_rook_inactive_in_equal_rook_endgame`.

---

## Task 6 — Validation and acceptance

**Goal:** Prove the new strategy layer is sound and measurable.

- [x] **6a** Run `python -m ruff check chess_game tests` and fix every warning.
- [x] **6b** Run `python -m mypy chess_game/` and fix every type issue.
- [x] **6c** Run `python -m pylint chess_game/` and keep the score at `10.00/10`.
- [x] **6d** Run `python -m pytest tests/ -q` and fix any failing regression.
- [x] **6e** Run a new depth-3 vs depth-3 self-play game and save the transcript under `tmp/strategy11_acceptance.txt`.
- [x] **6f** Check whether:
  - White plays a central pawn on move 1 (not Nc3/Nf3).
  - Black does not give back a ≥ +4 lead via a single tactical swing.
  - Endgame conversions (R vs B+K, R+B vs R) complete within fewer moves than the STRATEGY10 baseline (90 moves).
- [x] **6g** Write a short review note under `tmp/strategy11_review.txt` summarising move count, White move-1 quality, advantage preservation, and endgame technique.

---

## Task 7 — Commit and push

**Goal:** Check in the completed strategy update once validation passes.

- [x] **7a** Stage all changed files.
- [x] **7b** Commit with a clear message describing the move-1 bonus, advantage-preservation penalties, and endgame-technique helpers.
- [x] **7c** Push to `origin/master`.
- [x] **7d** Update all checklist items above to reflect final completion.

---

## Success Criteria

| Metric | Current (STRATEGY10) | Target |
|--------|----------------------|--------|
| White move 1 | Nc3 (minor piece) | e4 or d4 (central pawn) |
| Black advantage preservation (≥ +4) | Collapses via tactics/trades | Holds lead through to endgame |
| Queen-trade avoidance when ahead | Not present | Active when material lead ≥ +4 |
| R vs B+K conversion speed | ~90 moves | ≤ 50 moves |
| R+B vs R conversion speed | Failed (rook lost) | Achieves win or draws less often |
| Pylint score | 10.00/10 | 10.00/10 |
| Tests | 641 passing | All passing |
