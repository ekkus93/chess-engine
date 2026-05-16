# TASK_LOG.md

## Project
- chess-engine (Python)
- Repo root: /home/phil/work/chess-engine
- Branch: master

## Goal
- Implement all tasks/subtasks from docs/BIG_FIX1_TODO.md.
- Style: short, targeted changes; no redesign.
- Constraints:
  - Use BIG_FIX1_TODO.md as source of truth; update checkmarks as we go.
  - Lint after each phase; fix all warnings/errors.
  - Run full test suite after each phase; must pass before committing.
  - Commit and push to GitHub after each green phase.
  - Work on master.

## Commands
- Tests: python -m pytest tests -q
- Lint: python -m pylint chess_game/
- Typical flow: implement -> lint -> tests -> fix -> commit/push -> update BIG_FIX1_TODO.md

## Completed (as of last context)
- Tasks 1-8 effectively done:
  - test_board_api.py exists with:
    - is_valid_position
    - is_same_color
    - is_opponent
    - is_empty
    - find_king
    - get_legal_moves_for_color basic API
  - get_legal_moves_for_color hardened with try/finally.
  - Pinned-piece tests:
    - pinned knight zero moves
    - pinned pawn along pin line
    - pinned pawn diagonal blocked when exposes king
- All tests passing; pylint 10/10.

## In progress / next
- Task 3: DONE (is_same_color tests)
- Task 4: DONE (is_opponent tests)
- Task 5: DONE (is_empty tests)
- Task 9: DONE
- Task 10: DONE
- Task 11: DONE
- Task 12: DONE (273 pass)
- Task 13: DONE (mutation-safety tests; 273 pass)
- Task 14: DONE (board_api, full suite, lint all green)
- Next: review BIG_FIX1_TODO.md acceptance checklist; confirm all tasks done.

## Important notes
- BIG_FIX1_TODO.md is the canonical plan.
- When context runs out:
  - Read TASK_LOG.md.
  - Read docs/BIG_FIX1_TODO.md.
  - Continue from next unchecked task.