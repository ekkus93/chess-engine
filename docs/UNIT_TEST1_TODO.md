# UNIT_TEST1 TODO

## Goal

Add direct unit tests for modules that are currently exercised only through
integration and regression tests. Six modules have been identified as having
no direct import in any test file, making breakage harder to localise.

Priority order: utility functions first (lowest effort, highest signal), then
evaluation modules, then the TUI (requires Textual's headless harness).

---

## Scope Rules

- One new test file per source module.
- Tests import the module under test directly — no testing through `get_best_move`.
- Board positions are set up with helpers from `tests/helpers.py` or by placing
  pieces directly via `Board` public API.
- Every phase ends with:

  ```bash
  uv run python -m ruff check chess_game tests
  uv run python -m mypy chess_game
  uv run python -m pylint chess_game
  uv run python -m pytest tests/ -q -m "not slow"
  ```

- Slow suite must pass after all phases are complete.

---

## Phase 1: `strategy_utils.py`

**New file:** `tests/test_strategy_utils.py`

### 1.1 `iter_board_pieces` and `iter_color_pieces`

- [x] Test `iter_board_pieces` on starting position yields 32 items total.
- [x] Test `iter_color_pieces(board, WHITE)` on starting position yields exactly
      16 pieces, all with `piece.color == WHITE`.
- [x] Test `iter_color_pieces` on empty board yields 0 items.

### 1.2 `legal_move_count`

- [x] Test starting position returns 20 for WHITE (16 pawn + 4 knight moves).
- [x] Test a board where the king is in check returns only legal escape counts
      (not 20).

### 1.3 `king_coordinates`

- [x] Test returns `(7, 4)` for White on the starting position (row 7, col 4 = e1).
- [x] Test returns `(0, 4)` for Black on the starting position (row 0, col 4 = e8).
- [x] Test returns `None` when the king has been removed from the board (edge case).

### 1.4 `is_castled_king`

- [x] Test returns `True` for White king on g1 (kingside castle square).
- [x] Test returns `True` for White king on c1 (queenside castle square).
- [x] Test returns `True` for Black king on g8 and c8.
- [x] Test returns `False` for White king on e1 (starting square, not castled).

### 1.5 `both_queens_on_board`

- [x] Test returns `True` on starting position.
- [x] Test returns `False` after removing White's queen.
- [x] Test returns `False` after removing both queens.

### 1.6 `pawn_supports_square`

- [x] Test White pawn on e4 supports f5 (row=3, col=5).
- [x] Test White pawn on e4 supports d5 (row=3, col=3).
- [x] Test White pawn on e4 does NOT support e5 (forward, not diagonal).
- [x] Test Black pawn on e5 supports f4 and d4 (attacking down).

### 1.7 `center_distance`

- [x] Test d4 (row=4, col=3) and e4 (row=4, col=4) return 0 or 1
      (within center cluster).
- [x] Test a1 (row=7, col=0) returns a value >= 3.
- [x] Verify the function is symmetric: `center_distance(r, c) == center_distance(r, 7-c)`
      for all c.

### 1.8 `is_passed_pawn`

- [x] White pawn on e5 with no Black pawns on d/e/f files ahead → True.
- [x] White pawn on e5 with Black pawn on f6 (blocks diagonally) → False.
- [x] White pawn on e5 with Black pawn on e6 (blocks directly) → False.
- [x] Black pawn on d4 with no White pawns on c/d/e files ahead → True.

### 1.9 `passed_pawns_for_color`

- [x] Returns empty list on starting position (no passed pawns).
- [x] Returns one entry when a single passer is set up and no other passers exist.

### 1.10 `pawn_path_to_promotion_is_clear`

- [x] White pawn on e5 with e6, e7, e8 all empty → True.
- [x] White pawn on e5 with a piece on e6 → False.
- [x] Black pawn on d4 with d3, d2, d1 all empty → True.

### 1.11 `is_advanced_passer`

- [x] White pawn at row 2 (rank 6) → True.
- [x] White pawn at row 4 (rank 4) → False.
- [x] Black pawn at row 5 (rank 3) → True.
- [x] Black pawn at row 3 (rank 5) → False.

### 1.12 `total_non_pawn_material`

- [x] Starting position returns expected sum (both queens + 4 rooks + 4 bishops
      + 4 knights).
- [x] After removing all pieces except kings → 0.
- [x] After removing both queens → sum decreases by 2 × queen value.

### 1.13 `materially_ahead_color` and `materially_behind_color`

- [x] Returns `None` on starting position (equal material).
- [x] Returns `WHITE` after removing a Black bishop.
- [x] `materially_ahead_color` and `materially_behind_color` return opposite
      values for the same asymmetric position.

### 1.14 `non_king_material_lead`

- [x] Returns 0 on starting position.
- [x] Returns approximately bishop value after removing one Black bishop.
- [x] Returns a negative value when White is behind.

### 1.15 `is_capture_move`

- [x] Returns `False` for e2→e4 on starting position.
- [x] Returns `True` when a White piece captures a Black piece.

### 1.16 `scale_signed` and `opposite_color`

- [x] `scale_signed(200, 50)` returns 100; `scale_signed(-200, 50)` returns -100.
- [x] `opposite_color(WHITE)` returns BLACK; `opposite_color(BLACK)` returns WHITE.

### 1.17 `file_pawn_state`

- [x] Returns `"open"` when no pawns on the file.
- [x] Returns `"semi-open"` when only enemy has a pawn on the file.
- [x] Returns `"closed"` when a friendly pawn is present.

### 1.18 `path_clear_between`

- [x] Returns `True` for two adjacent squares.
- [x] Returns `True` for two squares with empty rank between them.
- [x] Returns `False` when a piece blocks the straight path.

### 1.19 Lint and test gate

- [x] `ruff`, `mypy`, `pylint` (10.00/10) all pass.
- [x] `pytest tests/test_strategy_utils.py -q` all pass (62 tests).

---

## Phase 2: `threat_awareness.py`

**New file:** `tests/test_threat_awareness.py`

### 2.1 `ThreatWeights` defaults

- [x] Verify `ThreatWeights` is a frozen dataclass (mutating raises).
- [x] Verify all five fields are positive integers.

### 2.2 `ThreatState` construction

- [x] Construct `ThreatState` from a known position; verify `.urgent_enemy_passers`
      is a list.
- [x] Verify `ThreatState` is frozen (mutating raises `FrozenInstanceError`).

### 2.3 `threat_response_order_bonus` — early-exit cases

- [x] Verify function returns an integer (not None or float).
- [x] KNIGHT and BISHOP moves return 0 (not in qualifying piece set).
- [x] Center pawn move (e-file) returns 0 (column filter).
- [x] Quiet position with no urgent threats returns 0 for rook shuffle.

### 2.4 `threat_response_order_bonus` — check-relief branch

- [x] White queen threatening Black king via open e-file: interposing move scores
      higher than a neutral move.
- [x] Interposing move earns a positive bonus.

### 2.5 `threat_response_order_bonus` — passed-pawn relief branch

- [x] Black rook blocking an advanced White e7 passer scores higher than a
      neutral rook shuffle.
- [x] Blocking move earns a positive bonus.

### 2.6 `threat_response_root_bonus` — returns integer

- [x] Call on a normal position; verify return type is `int`.
- [x] Knight move returns 0.

### 2.7 `threat_response_root_bonus` — simplification branch

- [x] White queen ahead captures Black rook: bonus ≥ 30 (_ROOT_SIMPLIFICATION_BONUS).
- [x] No simplification bonus when White is materially behind.

### 2.8 Lint and test gate

- [x] `ruff`, `mypy`, `pylint` (10.00/10) all pass.
- [x] `pytest tests/test_threat_awareness.py -q` all pass (16 tests).

---

## Phase 3: `piece_coordination.py`

**New file:** `tests/test_piece_coordination.py`

### 3.1 `PiecePlacementProfile` dataclass

- [x] Verify it is frozen (mutating raises).
- [x] Verify `score` field is an `int`.

### 3.2 `improves_worst_piece`

- [x] Knight from b1 to c3 (standard development) returns `True`.
- [x] A king move returns `False` (not a strategic piece).
- [x] A pawn push returns `False` (not a strategic piece).
- [x] Moving a central knight to a worse square returns `False`.

### 3.3 `rook_coordination_bonus`

- [x] Two disconnected rooks — move one to same rank as the other → 20.
- [x] Rook already connected stays connected → 0.
- [x] Disconnected rooks stay disconnected after move → 0.
- [x] Non-rook piece returns 0.

### 3.4 `bishop_coordination_bonus`

- [x] Bishop from c1 (not on long diagonal) to b2 (on a8-h1 diagonal, more mobile) → ≥ 18.
- [x] Bishop already on long diagonal → 0.
- [x] Non-bishop piece returns 0.

### 3.5 `queen_coordination_bonus`

- [x] Queen moves from h1 to d1, supporting more pieces → positive bonus.
- [x] Queen moves to a worse support position → 0.
- [x] Non-queen piece returns 0.

### 3.6 `square_has_friendly_support`

- [x] White pawn on e4 attacks d5 → `True` for WHITE.
- [x] White pawn on e4 does not attack e5 → `False`.
- [x] Enemy bishop attacking d5 does not count as White support → `False`.
- [x] Isolated square with no nearby pieces → `False`.
- [x] Edge square (h8) does not crash.

### 3.7 Lint and test gate

- [x] `ruff`, `mypy`, `pylint` (10.00/10) all pass.
- [x] `pytest tests/test_piece_coordination.py -q` all pass (21 tests).

---

## Phase 4: `pawn_structure_evaluation.py`

**New file:** `tests/test_pawn_structure_evaluation.py`

### 4.1 `collect_pawn_positions`

- [x] Starting position: 8 White pawns on rank 2 (row 6), 8 Black pawns on rank 7 (row 1).
- [x] Cleared board: both lists are empty.

### 4.2 `evaluate_pawn_structure` — symmetric baseline

- [x] Starting position returns 0 (symmetric structure).
- [x] White advanced passer with no Black pawns returns > 0.

### 4.3 `evaluate_pawn_structure` — phase sensitivity

- [x] Castled king position scores differ between endgame_phase=0 and endgame_phase=100.

### 4.4 `evaluate_pawn_structure` — passed pawn advancement

- [x] White passer on e6 scores more than passer on e5.

### 4.5 `_pawn_file_penalty`

- [x] Doubled + isolated → DOUBLED_PAWN_PENALTY + ISOLATED_PAWN_PENALTY.
- [x] Doubled but not isolated → DOUBLED_PAWN_PENALTY only.
- [x] Isolated but not doubled → ISOLATED_PAWN_PENALTY only.
- [x] Single pawn with neighbor → 0.

### 4.6 `_pawn_island_penalty`

- [x] No pawns → 0.
- [x] One island → 0.
- [x] Two islands → PAWN_ISLAND_PENALTY.
- [x] Three islands → 2 × PAWN_ISLAND_PENALTY.

### 4.7 `_central_duo_bonus`

- [x] d4 + e4 (adjacent center files) → CENTRAL_DUO_BONUS.
- [x] a4 + h4 (not center files) → 0.
- [x] Lone e4 pawn → 0.
- [x] CENTER_FILES = {3, 4}.

### 4.8 Lint and test gate

- [x] `ruff`, `mypy`, `pylint` (10.00/10) all pass.
- [x] `pytest tests/test_pawn_structure_evaluation.py -q` all pass (18 tests).

---

## Phase 5: `ai_quiescence_helpers.py`

**New file:** `tests/test_ai_quiescence_helpers.py`

### 5.1 `select_quiescence_moves` — only tactical moves returned

- [x] On a quiet position (no captures, no checks), returns an empty list.
- [x] On a position where White can capture a Black piece, returns at least that
      capture move.
- [x] Does NOT return normal quiet moves (pawn pushes, piece repositioning).

### 5.2 `select_quiescence_moves` — promotions included

- [x] Set up White pawn on e7 with no blocking pieces. Verify the promotion move
      to e8q appears in `select_quiescence_moves` output.

### 5.3 `select_quiescence_moves` — checks included

- [x] Set up a position where a White move gives check. Verify that move is
      included (checks are tactical moves in quiescence).

### 5.4 `select_quiescence_moves` — ordering

- [x] On a position with multiple captures, the highest-value capture appears
      first (sorted by MVV-LVA or similar score, descending).
- [x] A queen capture should appear before a pawn capture.

### 5.5 `_quiescence_capture_mvv_lva` — MVV-LVA ordering

- [x] Capturing a queen with a pawn scores higher than capturing a pawn with a queen
      (most-valuable-victim takes priority over least-valuable-attacker).
- [x] Capturing a rook with a bishop scores higher than capturing a bishop with a rook.

### 5.6 `_quiescence_tactical_score` — promotion bonus

- [x] A promotion move returns a score higher than any plain capture.
- [x] Promotion to queen scores higher than promotion to rook.

### 5.7 `_quiescence_capture_score` — SEE-like behaviour

- [x] A capture where the attacker would be immediately recaptured at a loss
      returns a lower score than a capture that wins material cleanly.
- [x] A free capture (no recapture possible) returns a positive score.

### 5.8 `_quiescence_structure_follow_up_score`

- [x] Returns an integer (not None or float) for any valid board pair.
- [x] Returns 0 or a small value on positions without notable structure change.

### 5.9 Lint and test gate

- [x] `ruff`, `mypy`, `pylint` (10.00/10) all pass.
- [x] `pytest tests/test_ai_quiescence_helpers.py -q` all pass.

---

## Phase 6: `tui.py`

**New file:** `tests/test_tui.py`

**Framework note:** Textual provides an async headless test harness:
`async with ChessApp().run_test() as pilot`. All test functions must be
`async def`, decorated with `@pytest.mark.asyncio` (add `pytest-asyncio` to
dev dependencies in `pyproject.toml`). Verify `ChessApp` can be imported and
instantiated before writing deeper tests.

### 6.1 Environment setup

- [x] Add `pytest-asyncio>=0.23` to `[project.optional-dependencies].dev` in
      `pyproject.toml` and run `uv sync`.
- [x] Add `asyncio_mode = "auto"` under `[tool.pytest.ini_options]` in
      `pyproject.toml` (allows `async def test_*` without per-test markers).

### 6.2 `ChessApp` — app mounts without error

- [x] `async with ChessApp().run_test() as pilot`: verify no exception is raised
      on startup.
- [x] After mounting, `MainMenuScreen` is the active screen.

### 6.3 `MainMenuScreen` — initial widget visibility

- [x] Human-vs-engine config panel (`#config-human`) is visible by default.
- [x] Self-play config panel (`#config-selfplay`) is hidden by default.
- [x] Mode radio set exists and has exactly two buttons.

### 6.4 `MainMenuScreen` — mode toggle

- [x] Click the "Self-play" radio button; verify `#config-selfplay` becomes
      visible and `#config-human` becomes hidden.
- [x] Click the "Human vs Engine" radio button; verify `#config-human` becomes
      visible and `#config-selfplay` becomes hidden.

### 6.5 `MainMenuScreen` — Start button pushes `GameScreen`

- [x] Press the Start button; verify the active screen changes to `GameScreen`.
- [x] After pushing `GameScreen`, a board display widget (`#board-display`) is
      present in the DOM.

### 6.6 `GameScreen` — board display renders

- [x] After mounting `GameScreen` (human-vs-engine mode, White), `#board-display`
      text is non-empty and contains rank separators ("+---").
- [x] The board display contains the letter "K" (White king) and "k" (Black king).

### 6.7 `GameScreen` — move list starts empty

- [x] `#move-list` content shows placeholder at game start.

### 6.8 `GameScreen` — human move input (happy path)

- [x] Type "e2e4" into the move input and press Enter; verify White pawn lands
      on e4 (board state check, engine responds before turn assertion).
- [x] The input field is cleared after submission.

### 6.9 `GameScreen` — invalid human move is rejected

- [x] Type "e2e5" (illegal pawn jump) into the move input and press Enter; verify
      `_board.turn` remains WHITE (no move applied).

### 6.10 `GameScreen` — thinking indicator

- [x] When `_thinking == True`, `#thinking-row` has class "active" (visible).
- [x] When `_thinking == False`, `#thinking-row` lacks class "active" (hidden).

### 6.11 `GameScreen` — resign button

- [x] Click the Resign button; verify `_game_over` is `True`.
- [x] The game-over panel (`#gameover-panel`) becomes visible.
- [x] The result message contains "resign" or "wins" text.

### 6.12 `GameScreen` — self-play mode toggle

- [ ] In self-play mode, click the Pause/Resume button; verify `_auto_play`
      toggles between `True` and `False`.
- [ ] In paused mode, click the Step button; verify the move count increases by 2
      (one move per side) after the step completes.

### 6.13 `GameScreen` — game-over panel on checkmate

- [ ] Set up a one-move checkmate position (e.g., Scholar's mate). Submit the
      mating move. Verify `#gameover-panel` appears and its text indicates
      checkmate.

### 6.14 `GameScreen` — save game to file

- [ ] After a game ends, click the Save button; enter a filename; click Confirm.
- [ ] Verify the file is created on disk with the expected move list content.
- [ ] Verify the file contains at least one move string and a result line.

### 6.15 `_format_move_list` — unit test (no TUI harness needed)

- [x] Instantiate `GameScreen` directly (not through the app); call
      `_format_move_list()` with various move lists.
- [x] Verify output format and line count.
- [x] Verify empty `_move_strings` returns empty string.

### 6.16 `EngineMoveMessage` — typing

- [x] Instantiate `EngineMoveMessage(move=None)` and verify `.move` is `None`.
- [x] Instantiate with a real `LegalMove`; verify `.move` is that move.

### 6.17 Lint and test gate

- [x] `ruff`, `mypy`, `pylint` (10.00/10) all pass with the new test file.
- [x] `pytest tests/test_tui.py -q` all pass (27 tests).

---

## Final Gate

- [x] Full fast suite: `uv run python -m pytest tests/ -q -m "not slow"` — 899 pass.
- [x] Full slow suite: `uv run python -m pytest tests/ -q -m "slow"` — 138 pass.
- [x] `uv run python -m pylint chess_game` — 10.00/10.
- [x] Update `memory.md` with timestamp, model, and summary.
- [x] Commit and push.
