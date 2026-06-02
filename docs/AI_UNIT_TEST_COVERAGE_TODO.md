# AI_UNIT_TEST_COVERAGE_TODO.md

## Goal

Add fast, deterministic unit tests for core helper logic that is currently tested mostly through integration/regression suites.

## Priority Order (fast-first)

1. `chess_game/chess/ai_search_helpers.py` pure helper functions
2. `chess_game/chess/position_utils.py` repetition-key invariants
3. `chess_game/self_play.py` move-selection timeout wrapper behavior

## Phase Checklist

### Phase 1: `ai_search_helpers` unit coverage

- [x] Add direct tests for:
  - `initial_root_window()`
  - `rerun_full_window_if_needed()`
  - `search_position_counts()`
  - `position_occurrence_count()`
  - `update_alpha_beta()`
  - `promotion_order_score()`

### Phase 2: Position-key and self-play wrapper coverage

- [x] Add direct tests for `position_key()` turn/castling/en-passant invariants.
- [x] Add direct tests for `_get_best_move_with_timeout()`:
  - no-timeout path forwards arguments/options correctly
  - timeout path returns `None` and restores signal state

### Phase 3: Verification

- [x] Run lint stack (`ruff`, `mypy`, `pylint`).
- [x] Run full test suite.
