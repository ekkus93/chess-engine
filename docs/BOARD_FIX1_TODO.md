# BOARD FIX1 TODO

## Goal

Improve AI move quality without changing chess rules correctness.

This pass focuses on:

- strengthening **board evaluation**
- reducing obvious **search horizon** mistakes
- fixing **self-play repetition detection**
- tightening the remaining **search caveats** already identified

This is a quality-focused AI pass, not a rules-engine rewrite.

---

## Scope rules

- Keep the legal move generator and board rules behavior unchanged unless a new AI test exposes a direct dependency bug.
- Preserve the public `Board` API where possible.
- Prefer small, testable improvements over one large evaluator rewrite.
- Do not mix unrelated refactors into this pass.
- Every major task group must end with:

  ```bash
  python -m pytest tests -q
  ```

- For AI-specific work, also run targeted checks such as:

  ```bash
  python -m pytest tests/test_ai.py tests/test_ai_search.py tests/test_ai_promotion.py -q
  ```

---

# Task 0: Establish a quality baseline

## 0.1 Run the current test suite

- [ ] Run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Record the current pass/fail baseline before changing AI code.
- [ ] If there are pre-existing failures, separate them from this fix.

## 0.2 Capture current self-play behavior

- [ ] Run at least one baseline self-play game:

  ```bash
  python -m chess_game.self_play --white-depth 3 --black-depth 3
  ```

- [ ] Save one transcript under `tmp/` for before/after comparison.
- [ ] Note:
  - [ ] result type (win/loss/draw)
  - [ ] move count
  - [ ] obvious pathologies (repetition loops, queen shuffles, rook shuffles, hanging pieces)

## 0.3 Confirm current evaluator boundaries

- [ ] Verify starting position evaluates to `0`.
- [ ] Verify mirrored positions negate correctly.
- [ ] Verify obvious material-advantage positions still score in the correct direction.

---

# Task 1: Build stronger evaluator regression tests first

## 1.1 Add evaluation-behavior tests

- [ ] Create or extend tests covering:
  - [ ] mobility advantage
  - [ ] isolated pawn penalty
  - [ ] doubled pawn penalty
  - [ ] passed pawn bonus
  - [ ] king shelter / castled king preference
  - [ ] bishop pair bonus
  - [ ] rook on open file bonus

## 1.2 Add tactical-stability tests

- [ ] Add tests for positions where a naive static evaluator overvalues a hanging piece.
- [ ] Add tests for recapture sequences so quiescence work can be validated later.
- [ ] Add at least one position where a superficially good capture fails tactically one move later.

## 1.3 Add draw-awareness tests

- [ ] Add tests for:
  - [ ] true threefold repetition detection inputs
  - [ ] repeated piece placement with different castling rights
  - [ ] repeated piece placement with different en passant rights

- [ ] Ensure draw detection never treats those different states as identical.

## 1.4 Add search-stability tests

- [ ] Add a regression test for `get_best_move()` iterative deepening consistency.
- [ ] Add a regression test that ensures aspiration fallback, if retained, re-searches with a full window before accepting a result.
- [ ] Add tests that compare `minimax()` vs `minimax_no_prune()` on small positions at shallow depth.

---

# Task 2: Refactor evaluator structure before tuning heuristics

## 2.1 Split evaluation into named components

- [ ] Refactor `evaluate(board)` into clear helpers, for example:
  - [ ] `_evaluate_material(board)`
  - [ ] `_evaluate_piece_square_tables(board)`
  - [ ] `_evaluate_mobility(board)`
  - [ ] `_evaluate_pawn_structure(board)`
  - [ ] `_evaluate_king_safety(board)`
  - [ ] `_evaluate_rook_activity(board)`
  - [ ] `_evaluate_bishop_pair(board)`

- [ ] Keep one final `evaluate(board)` entry point returning a single integer from White’s perspective.

## 2.2 Add evaluation constants container

- [ ] Group tunable constants in one place.
- [ ] Avoid scattering raw numeric bonuses and penalties across helper functions.
- [ ] Prefer descriptive names such as:
  - [ ] `ISOLATED_PAWN_PENALTY`
  - [ ] `DOUBLED_PAWN_PENALTY`
  - [ ] `PASSED_PAWN_BONUS_BY_RANK`
  - [ ] `ROOK_OPEN_FILE_BONUS`
  - [ ] `BISHOP_PAIR_BONUS`

## 2.3 Preserve evaluator symmetry

- [ ] Ensure each new heuristic remains color-symmetric.
- [ ] Add or update helper functions so Black uses mirrored rank logic where required.
- [ ] Re-run symmetry tests after each heuristic family is added.

---

# Task 3: Add mobility scoring

## Problem

The current evaluator is mostly material plus piece-square tables. It does not distinguish active pieces from cramped pieces strongly enough.

## 3.1 Define mobility inputs

- [ ] Decide whether mobility counts:
  - [ ] legal moves only, or
  - [ ] pseudo-legal moves

- [ ] Prefer the option that is correct and affordable for this codebase.
- [ ] Document the decision in code comments if not obvious.

## 3.2 Score per-piece mobility

- [ ] Add bonuses for:
  - [ ] knights with many destinations
  - [ ] bishops with open diagonals
  - [ ] rooks with active files/ranks
  - [ ] queens with moderate mobility

- [ ] Do **not** over-reward queen wandering in the opening.
- [ ] Keep king mobility conservative in middlegame-oriented scoring.

## 3.3 Add anti-pathology tests

- [ ] Add a test where a trapped minor piece scores worse than an active one.
- [ ] Add a test where an undeveloped back-rank rook does not outrank a genuinely active rook.

---

# Task 4: Add pawn-structure evaluation

## Problem

Without pawn-structure scoring, the engine accepts ugly long-term positions too easily and misses basic strategic costs.

## 4.1 File-based pawn analysis helpers

- [ ] Add helper(s) to inspect pawns by file and color.
- [ ] Reuse shared logic instead of duplicating White/Black code.

## 4.2 Penalize weak pawn structures

- [ ] Add penalties for:
  - [ ] doubled pawns
  - [ ] isolated pawns
  - [ ] backward pawns, if implementable cleanly

- [ ] Keep the first version simple if backward-pawn detection becomes too noisy.

## 4.3 Reward healthy pawn structures

- [ ] Add bonuses for:
  - [ ] passed pawns
  - [ ] connected passed pawns, if feasible
  - [ ] advanced passed pawns scaled by rank

## 4.4 Guard against overfitting

- [ ] Ensure pawn penalties do not overwhelm material.
- [ ] Ensure passed-pawn bonuses scale sensibly in early vs late phases.

---

# Task 5: Add king-safety scoring

## Problem

The current engine can make strange king decisions because king safety is mostly represented by a single piece-square table.

## 5.1 Add king-zone helpers

- [ ] Add helpers to inspect squares around each king.
- [ ] Keep the implementation simple and deterministic.

## 5.2 Reward safer king placement

- [ ] Add bonuses/penalties for:
  - [ ] castled king vs uncastled king
  - [ ] intact pawn shield
  - [ ] open files or diagonals aimed near the king
  - [ ] exposed central king in middlegame

## 5.3 Prevent endgame distortion

- [ ] Reduce or disable some king-safety penalties when major pieces are mostly gone.
- [ ] Add a basic phase heuristic so king centralization is not always punished in endgames.

## 5.4 Add regression tests

- [ ] Add a test where a castled king scores better than an exposed king in a middlegame-like position.
- [ ] Add a test where king centralization is acceptable in a simplified endgame.

---

# Task 6: Add piece-coordination and activity heuristics

## 6.1 Bishop pair

- [ ] Add a bishop-pair bonus.
- [ ] Verify the bonus is meaningful but smaller than a pawn.

## 6.2 Rook activity

- [ ] Add bonuses for:
  - [ ] rook on open file
  - [ ] rook on semi-open file
  - [ ] rook on the seventh rank, if implementable cleanly

## 6.3 Development sanity

- [ ] Consider a light opening-development heuristic only if current self-play still shows repeated early rook/queen nonsense after Tasks 3-5.
- [ ] If added, keep it minimal and time-limited to early-game patterns.
- [ ] Do not hardcode opening-book behavior.

---

# Task 7: Add quiescence search

## Problem

Depth-3 search with only static evaluation is vulnerable to the horizon effect, especially around captures and recaptures.

## 7.1 Add a capture-focused quiescence entry point

- [ ] Introduce a helper such as:
  - [ ] `quiescence(board, alpha, beta, is_maximizing)`

- [ ] Use stand-pat evaluation as the base score.
- [ ] Search tactical continuations rather than stopping immediately at unstable leaf nodes.

## 7.2 Limit the move set

- [ ] First version should search only:
  - [ ] captures
  - [ ] promotions
  - [ ] optionally checking moves, only if needed and affordable

- [ ] Avoid turning quiescence into an unbounded second minimax.

## 7.3 Wire quiescence into minimax

- [ ] Replace raw `evaluate(board)` at depth 0 with quiescence on non-terminal nodes.
- [ ] Keep terminal checkmate/stalemate handling ahead of quiescence.

## 7.4 Add targeted tests

- [ ] Add a tactical leaf test where plain depth-0 evaluation is misleading.
- [ ] Add a recapture stabilization test.
- [ ] Add a performance guard so quiescence does not explode node count on simple positions.

---

# Task 8: Tighten iterative deepening and aspiration handling

## Problem

`get_best_move()` has aspiration-window retry logic that looks fragile. If the window expands to full width, the code should actually re-search before accepting the pass.

## 8.1 Inspect the current root-search loop

- [ ] Review:
  - [ ] retry conditions
  - [ ] fail-low handling
  - [ ] fail-high handling
  - [ ] full-window fallback behavior

## 8.2 Fix fallback behavior

- [ ] Ensure a widened window causes an actual re-search, not just a loop break.
- [ ] Ensure the accepted root result is exact for the final window used.
- [ ] Prefer correctness over micro-optimization.

## 8.3 Add root-search regression tests

- [ ] Add a test where a narrow window fails high and the engine must re-search.
- [ ] Add a test where a narrow window fails low and the engine must re-search.
- [ ] Add a test ensuring the final returned move matches a full-width search on the same small position.

---

# Task 9: Improve draw and repetition awareness

## Problem

`self_play.py` currently uses a simplified repetition key that ignores castling rights and en passant, so it can report a false threefold repetition draw.

## 9.1 Replace self-play repetition key

- [ ] Update `self_play.py` to use a full position identity including:
  - [ ] piece placement
  - [ ] side to move
  - [ ] castling rights
  - [ ] en passant target

- [ ] Prefer reusing the AI/search position key if it is already correct and stable.
- [ ] Avoid maintaining two subtly different position-key implementations.

## 9.2 Add self-play regression tests

- [ ] Add a test showing same piece placement with different castling rights is **not** the same repetition state.
- [ ] Add a test showing same piece placement with different en passant rights is **not** the same repetition state.

## 9.3 Optional search draw-awareness

- [ ] Evaluate whether the search itself should score forced repetition as drawish when no better line exists.
- [ ] If implemented:
  - [ ] keep it simple,
  - [ ] do not contaminate legal rules code,
  - [ ] add explicit tests.

---

# Task 10: Add instrumentation for evaluator diagnostics

## 10.1 Add optional evaluation breakdown output

- [ ] Add a debug-only helper that returns component scores, for example:
  - [ ] material
  - [ ] PST
  - [ ] mobility
  - [ ] pawn structure
  - [ ] king safety
  - [ ] rook activity
  - [ ] bishop pair

- [ ] Keep the normal `evaluate(board)` API unchanged.

## 10.2 Add search diagnostics

- [ ] Extend or reuse `SearchStats` for:
  - [ ] node count
  - [ ] cutoff count
  - [ ] TT hits
  - [ ] quiescence nodes
  - [ ] fail-high / fail-low retry counts

## 10.3 Use diagnostics in tests and manual analysis

- [ ] Add at least one targeted test asserting quiescence was entered on a tactical leaf, if practical.
- [ ] Use diagnostics to compare before/after move selection on benchmark positions.

---

# Task 11: Add benchmark positions and acceptance checks

## 11.1 Create a small benchmark suite

- [ ] Add a curated set of positions covering:
  - [ ] opening development sanity
  - [ ] hanging piece punishment
  - [ ] recapture sequences
  - [ ] passed pawn races
  - [ ] king-safety tradeoffs
  - [ ] basic mating attacks

## 11.2 Define acceptance targets

- [ ] Engine should still:
  - [ ] find mate in one
  - [ ] avoid illegal moves
  - [ ] preserve board state during search

- [ ] Engine should improve on at least some quality metrics such as:
  - [ ] fewer immediate tactical blunders in benchmark positions
  - [ ] fewer meaningless repetition loops in self-play
  - [ ] more stable preference for development and king safety

## 11.3 Re-run self-play after each major milestone

- [ ] After Tasks 4, 6, 7, and 9, run fresh self-play at depth 3.
- [ ] Save transcripts under `tmp/` with distinct names.
- [ ] Compare:
  - [ ] result length
  - [ ] repetition frequency
  - [ ] major blunders
  - [ ] strange queen/rook behavior

---

# Task 12: Final cleanup and integration

## 12.1 Remove dead code

- [ ] Remove obsolete helpers, constants, or duplicated position-key logic introduced during the refactor.

## 12.2 Keep docs aligned

- [ ] Update README or relevant docs if evaluator/search behavior is described there and becomes outdated.

## 12.3 Final verification

- [ ] Run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Run at least one final self-play game:

  ```bash
  python -m chess_game.self_play --white-depth 3 --black-depth 3
  ```

- [ ] Confirm:
  - [ ] no illegal moves
  - [ ] no false repetition result from the simplified key
  - [ ] no obvious regression in mate/stalemate handling

---

## Recommended execution order

1. Task 0 - baseline
2. Task 1 - tests first
3. Task 2 - evaluator structure
4. Task 3 - mobility
5. Task 4 - pawn structure
6. Task 5 - king safety
7. Task 6 - activity heuristics
8. Task 8 - aspiration/root-search fix
9. Task 7 - quiescence search
10. Task 9 - repetition correctness
11. Task 10 - diagnostics
12. Task 11 - benchmarks
13. Task 12 - cleanup and final verification

---

## Notes

- If move quality improves enough after Tasks 3-6, keep the evaluator simple and avoid speculative heuristics.
- If quiescence causes major performance problems, reduce its move set before adding more evaluator complexity.
- Prefer one correct shared position key over separate AI and self-play key implementations.
