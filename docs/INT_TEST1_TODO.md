# INT_TEST1_TODO.md

## Goal

Implement a comprehensive integration-test layer that verifies cross-module behavior across AI search, opening-book flow, repetition handling, self-play runtime behavior, and board-state transitions.

This plan is focused on high-signal tests that catch regressions in orchestration logic (not just isolated unit helpers).

---

## Scope and Non-Goals

### In Scope

- End-to-end behavior of `get_best_move()` in realistic board states
- Self-play integration paths involving opening book, repetition counts, and timeout handling
- Board metadata/state transitions (castling rights, en-passant target) through AI-selected legal moves
- Test-runtime classification guardrails (`slow` vs `not slow`)

### Out of Scope

- Engine strength tuning
- Evaluation heuristic changes
- Search algorithm refactors unrelated to integration tests

---

## Test File Plan

Create or extend the following integration-focused test files:

- `tests/test_ai_repetition_integration.py` (new)
- `tests/test_opening_book_search_integration.py` (new)
- `tests/test_self_play_runtime_integration.py` (new or extend existing self-play CLI/runtime tests)
- `tests/test_ai_board_state_integration.py` (new)
- `tests/test_test_runtime_markers_integration.py` (new meta-integration test)

Keep tests deterministic and avoid flaky time-based assertions.

---

## Task 0: Baseline and Planning Setup

### 0.1 Baseline verification

- [x] Run baseline lint and tests before adding integration tests:
  - `python -m ruff check chess_game tests`
  - `python -m mypy chess_game/`
  - `python -m pylint chess_game/`
  - `python -m pytest tests/ -q`

### 0.2 Confirm reusable fixtures/helpers

- [x] Review existing helper utilities:
  - `tests/helpers.py`
  - existing board construction helpers in AI test files
- [x] Reuse helper patterns for board setup (`sq`, `create_piece`, `Board.clear_board`) instead of duplicating setup logic.

### 0.3 Define marker policy for new integration tests

- [x] Mark new tests `slow` only if they are multi-second, transcript-heavy, deep search, or self-play loops.
- [x] Keep deterministic shallow integration tests in default fast suite.

---

## Task 1: Repetition + Search Choice Integration Tests

### 1.1 Add integration test module

- [x] Create `tests/test_ai_repetition_integration.py`.

### 1.2 Repetition-avoidance in winning positions

- [x] Add a position where side-to-move can repeat checks but also has a clearly stronger non-repeating move.
- [x] Assert `get_best_move()` prefers the practical non-repetition line.
- [x] Assert selected move is legal and does not immediately recreate known repeat key.

### 1.3 Repetition-neutral behavior in balanced positions

- [x] Add a near-equal position where repetition is acceptable.
- [x] Assert `get_best_move()` remains legal and deterministic across repeated calls.

### 1.4 Position count propagation checks

- [x] Pass `position_counts` explicitly into `get_best_move()`.
- [x] Verify behavior differs when counts imply imminent repetition vs when counts are absent.

### 1.5 Acceptance criteria

- [x] Tests cover both “avoid repetition when better” and “neutral repetition when equal” behaviors.
- [x] No nondeterministic failures across repeated local runs.

---

## Task 2: Opening Book ↔ Search Fallback Chain Integration

### 2.1 Add integration test module

- [x] Create `tests/test_opening_book_search_integration.py`.

### 2.2 Book hit path

- [x] Build a position known to be in book.
- [x] Assert `get_best_move(..., book_options=BestMoveOptions(use_opening_book=True, ...))` returns a valid book move.

### 2.3 Book miss fallback path

- [x] Build a position outside book coverage.
- [x] Assert engine falls back to search and returns a legal non-`None` move.

### 2.4 Custom book load + miss fallback via runtime path

- [x] Use controlled custom book data (minimal valid lines).
- [x] Verify when custom book has no candidate for current position, search still runs and returns legal move.

### 2.5 Book + repetition-count interaction

- [x] Start from a book-covered state, then transition to non-book state with `position_counts` present.
- [x] Assert search fallback still honors repetition-aware behavior after book exits.

### 2.6 Acceptance criteria

- [x] Hit, miss, and transition paths each covered.
- [x] No silent failures when book is enabled but position has no book candidate.

---

## Task 3: Self-Play Runtime and Timeout Integration

### 3.1 Add integration test module

- [x] Create `tests/test_self_play_runtime_integration.py` (or extend `test_self_play_cli.py` with runtime-focused integration cases).

### 3.2 Timeout-induced no-move handling in game loop

- [x] Simulate timeout path causing move selection to return `None`.
- [x] Assert self-play loop exits cleanly without mutating board into invalid state.

### 3.3 Non-timeout normal path in game loop

- [x] Verify self-play applies legal move and records position count updates.
- [x] Assert loop progression/termination semantics for bounded `max_moves`.

### 3.4 Opening-book option propagation through self-play

- [x] Assert runtime passes `BestMoveOptions` values correctly to search layer (`use_opening_book`, custom book object).

### 3.5 Acceptance criteria

- [x] Timeout and non-timeout paths both tested.
- [x] No flaky wall-clock dependency (prefer monkeypatched signal/search behavior).

---

## Task 4: Castling/En-Passant State Transition Integration

### 4.1 Add integration test module

- [x] Create `tests/test_ai_board_state_integration.py`.

### 4.2 Castling-rights-sensitive integration test

- [x] Construct position where castling rights materially change legal choices.
- [x] Assert AI-selected move is legal and resulting castling rights match expected transition.

### 4.3 En-passant-sensitive integration test

- [x] Construct position where en-passant target availability affects legal move set.
- [x] Assert AI-selected move respects current en-passant legality.
- [x] After move application, assert en-passant target updates/clears correctly.

### 4.4 Metadata integrity checks

- [x] Assert board metadata remains internally consistent after AI move:
  - [x] side to move switched correctly
  - [x] castling rights fields valid
  - [x] en-passant target valid or `None`

### 4.5 Acceptance criteria

- [x] Integration tests cover both metadata-sensitive rule domains.
- [x] No direct UI mutation shortcuts; all transitions through board APIs.

---

## Task 5: Runtime Marker Contract (Meta-Integration)

### 5.1 Add marker contract test module

- [x] Create `tests/test_test_runtime_markers_integration.py`.

### 5.2 Assert expensive categories remain marked slow

- [x] Add meta checks that known heavy suites (transcript/depth/self-play heavy) are `slow`-marked.
- [x] Prefer robust checks (node IDs / marker metadata) over fragile string matching.

### 5.3 Assert key fast suites stay unmarked

- [x] Verify core fast correctness suites remain in default run unless intentionally changed.

### 5.4 Acceptance criteria

- [x] Contract test fails with actionable message when marker discipline regresses.
- [x] Default `-m "not slow"` workflow remains practical.

---

## Task 6: Lint, Type, and Test Verification After Each Phase

For each completed task (Tasks 1–5):

- [x] Run:
  - `python -m ruff check chess_game tests`
  - `python -m mypy chess_game/`
  - `python -m pylint chess_game/`
- [x] Run targeted tests for touched modules.
- [x] Fix all warnings/errors structurally (no pragmas for skipped issues).

---

## Task 7: Final Full Verification

### 7.1 Full test run

- [x] Run full suite:
  - `python -m pytest tests/ -q`

### 7.2 Optional split verification

- [x] Run non-slow suite:
  - `python -m pytest tests -q -m "not slow" --durations=25`
- [x] Run slow suite:
  - `python -m pytest tests -q -m "slow" --durations=25`

### 7.3 Final guardrails

- [x] Confirm no search/eval semantics were changed to “make tests pass.”
- [x] Confirm tests remain deterministic and stable.

---

## Task 8: Documentation and Task Tracking Updates

### 8.1 Progress tracking

- [x] Update this file’s checkboxes as each subtask completes.

### 8.2 Notes for maintainers

- [x] Add concise comments/docstrings in tests describing scenario intent and why integration coverage matters.

### 8.3 Memory/log update

- [x] Record integration-test plan completion details in `memory.md` after implementation.

---

## Task 9: Commit and Push

### 9.1 Commit hygiene

- [ ] Stage only intended integration-test and related doc changes.
- [ ] Use clear commit message(s) reflecting integration coverage additions.

### 9.2 Push

- [ ] Push to `origin/master` only after lint + full tests pass.
