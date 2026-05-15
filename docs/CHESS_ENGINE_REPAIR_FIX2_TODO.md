# Chess Engine Repair Fix 2 TODO

## Purpose

This TODO is a focused follow-up repair pass after the larger core chess engine repair.

The current code is much better and the existing pytest suite passes, but review found two real chess-rule bugs and several cleanup issues:

1. Queenside castling incorrectly ignores an occupied `b1` or `b8`.
2. En passant incorrectly accepts non-one-row diagonal moves if the destination equals `en_passant_target`.
3. Castling logic is duplicated in `PieceMovers`, which can drift from `CastlingValidator`.
4. Tests still rely heavily on raw row/column constants for real chess positions.
5. `BoardState` appears stale or semi-orphaned.
6. AI evaluation may have a piece-square-table orientation issue.

Do not expand scope beyond this TODO.

---

## Implementation rules

- Keep this patch focused.
- Do not add new engine features.
- Do not tune AI search.
- Do not add GUI, UCI, PGN, or opening book functionality.
- Do not weaken tests to make them pass.
- Prefer algebraic notation helpers such as `sq("e4")` in tests that describe real chess positions.
- Run the full test suite after each major task group:

  ```bash
  python -m pytest tests -q
  ```

- Record any unexpected test failures in implementation notes before fixing them.
- Remove generated files from the repo before final submission.

---

## Task status summary

| Task | Status | Notes |
|------|--------|-------|
| 0: Baseline | DONE | All subtasks complete |
| 1: Regression tests | DONE | Tests in `test_castling_edge_cases.py` and `test_en_passant_edge_cases.py` |
| 2: Queenside castling | DONE | `b1`/`b8` check added to `CastlingValidator` |
| 3: CastlingValidator authority | NOT DONE | `PieceMovers._get_king_moves()` still has castling logic |
| 4: En passant geometry | DONE | Row-delta check added |
| 5: Test coordinate cleanup | IN PROGRESS | 1 file converted; ~338 raw coords remain in 8 priority files |
| 6: Stale comments | DONE | Full-project search clean |
| 7: BoardState | DONE | Option A — removed |
| 8: AI evaluation | DONE | Fix applied; symmetry tests (8.3) complete |
| 9: Cache files | PARTIAL | `.gitignore` needs updating (9.2) |
| 10: Final acceptance | NOT STARTED | Blocked on Tasks 3, 5, 8.3, 9.2 |

---

## Task 0: Establish baseline

**Status: DONE**

### 0.1 Run the full test suite

- [x] From the repo root, run:

   ```bash
   python -m pytest tests -q
   ```

- [x] Confirm the current suite passes before modifying code.
- [x] If it does not pass, record the failures and inspect whether they are related to this TODO.

### 0.2 Create a focused branch

- [x] Create a dedicated branch, for example:

   ```bash
   git checkout -b fix/castling-en-passant-cleanup
   ```

### 0.3 Add this spec/TODO to the repo

- [x] Copy the companion spec to:

   ```text
   docs/CHESS_ENGINE_REPAIR_FIX2_SPEC.md
   ```

- [x] Copy this TODO to:

   ```text
   docs/CHESS_ENGINE_REPAIR_FIX2_TODO.md
   ```

---

## Task 1: Add failing regression tests first

**Status: DONE**

Do this before changing implementation code.

### 1.1 Add white queenside castling blocked-by-b1 test

- [x] Create or update a castling test file, preferably:

   ```text
   tests/test_castling_edge_cases.py
   ```

- [x] Set up this position using algebraic helpers:

   ```text
   White king: e1
   White rook: a1
   White knight or bishop: b1
   Black king: e8
   White to move
   ```

- [x] Attempt:

   ```text
   e1c1
   ```

- [x] Assert the move is rejected.
- [x] Assert the king remains on `e1`.
- [x] Assert the rook remains on `a1`.
- [x] Assert the blocker remains on `b1`.

### 1.2 Add black queenside castling blocked-by-b8 test

- [x] Set up this position using algebraic helpers:

   ```text
   Black king: e8
   Black rook: a8
   Black knight or bishop: b8
   White king: e1
   Black to move
   ```

- [x] Attempt:

   ```text
   e8c8
   ```

- [x] Assert the move is rejected.
- [x] Assert the king remains on `e8`.
- [x] Assert the rook remains on `a8`.
- [x] Assert the blocker remains on `b8`.

### 1.3 Add white illegal long en passant test

- [x] Create or update an en passant edge-case test file, preferably:

   ```text
   tests/test_en_passant_edge_cases.py
   ```

- [x] Set up this position:

   ```text
   White king: e1
   Black king: e8
   White pawn: e3
   Black pawn: d5
   en_passant_target: d6
   White to move
   ```

- [x] Attempt:

   ```text
   e3d6
   ```

- [x] Assert the move is rejected.
- [x] Assert the white pawn remains on `e3`.
- [x] Assert the black pawn remains on `d5`.
- [x] Assert `d6` remains empty.

### 1.4 Add black illegal long en passant test

- [x] Set up this position:

   ```text
   White king: e1
   Black king: e8
   Black pawn: d6
   White pawn: e4
   en_passant_target: e3
   Black to move
   ```

- [x] Attempt:

   ```text
   d6e3
   ```

- [x] Assert the move is rejected.
- [x] Assert the black pawn remains on `d6`.
- [x] Assert the white pawn remains on `e4`.
- [x] Assert `e3` remains empty.

### 1.5 Verify the new tests fail before implementation

- [x] Run:

   ```bash
   python -m pytest tests/test_castling_edge_cases.py tests/test_en_passant_edge_cases.py -q
   ```

- [x] Confirm the new tests fail against the current implementation.
- [x] If any new regression test passes unexpectedly, inspect whether the setup is wrong or the implementation was already fixed.

---

## Task 2: Fix queenside castling path validation

**Status: DONE**

### 2.1 Inspect current castling implementation

- [x] Open:

   ```text
   chess_game/chess/board/castling.py
   ```

- [x] Find the method that checks castling path emptiness.
- [x] Confirm that queenside castling checks `c1/c8` and `d1/d8`.
- [x] Confirm whether it currently misses `b1/b8`.

### 2.2 Fix queenside path emptiness

- [x] Update the castling path-clear logic so queenside castling requires all of these squares to be empty:

   ```text
   White queenside: b1, c1, d1
   Black queenside: b8, c8, d8
   ```

- [x] Do not add `b1/b8` to the attack-path checks.
- [x] Keep the attack-path checks as:

   ```text
   White queenside: e1, d1, c1
   Black queenside: e8, d8, c8
   ```

### 2.3 Preserve kingside behavior

- [x] Ensure kingside castling still requires:

   ```text
   White kingside empty squares: f1, g1
   Black kingside empty squares: f8, g8
   ```

- [x] Ensure kingside attack-path checks remain:

   ```text
   White kingside: e1, f1, g1
   Black kingside: e8, f8, g8
   ```

### 2.4 Run castling tests

- [x] Run:

   ```bash
   python -m pytest tests -q -k castling
   ```

- [x] Confirm all castling tests pass.
- [x] Confirm the new `b1` and `b8` regression tests pass.

---

## Task 3: Make `CastlingValidator` the only castling authority

**Status: NOT DONE** — `PieceMovers._get_king_moves()` still contains castling logic (lines 337-356). Castling moves must be removed from king pseudo-legal generation and added only through `CastlingValidator` in `MoveValidator.get_legal_moves()`.

### 3.1 Inspect king move generation

- [ ] Open:

  ```text
  chess_game/chess/pieces/piece_movers.py
  ```

- [ ] Find `_get_king_moves()` or equivalent.
- [ ] Identify any castling-specific logic in `PieceMovers`.

### 3.2 Remove castling from `PieceMovers`

- [ ] Modify king pseudo-legal move generation so it returns only normal one-square king moves.
- [ ] It must not inspect castling rights.
- [ ] It must not inspect rook positions for castling.
- [ ] It must not inspect castling path squares.
- [ ] It must not call attack detection for castling paths.
- [ ] It must not add `g1`, `c1`, `g8`, or `c8` as king moves because of castling.

### 3.3 Add castling moves through the validator

- [ ] Inspect legal move generation:

  ```text
  Board.get_legal_moves(...)
  MoveValidator.get_legal_moves(...)
  ```

- [ ] Ensure castling moves are added only by asking `CastlingValidator`.
- [ ] Legal castling moves should appear in legal moves when allowed.
- [ ] Illegal castling moves must not appear.

### 3.4 Add or update tests for generated castling moves

- [ ] Add a test where White kingside castling is legal and appears in legal moves as `e1g1`.
- [ ] Add a test where White queenside castling is legal and appears in legal moves as `e1c1`.
- [ ] Add a test where `b1` is occupied and `e1c1` does not appear in legal moves.
- [ ] Add equivalent black tests if not already covered.

### 3.5 Run legal move tests

- [ ] Run:

  ```bash
  python -m pytest tests -q -k "castling or legal"
  ```

---

## Task 4: Fix en passant geometry validation

**Status: DONE**

### 4.1 Inspect en passant detection paths

- [x] Open:

   ```text
   chess_game/chess/board/en_passant.py
   chess_game/chess/board/move_validation.py
   chess_game/chess/board/board.py
   ```

- [x] Identify every place that detects or validates en passant.
- [x] Confirm whether any path bypasses normal geometry validation.

### 4.2 Add exact row-delta validation

- [x] In the canonical en passant validator, require:

   ```python
   direction = -1 if piece.color == Color.WHITE else 1
   int(to_square.row) - int(from_square.row) == direction
   abs(int(to_square.col) - int(from_square.col)) == 1
   ```

- [x] Reject the move if either condition fails.
- [x] Ensure this check happens before en passant execution.
- [x] Ensure this check happens even if `to_square == board.en_passant_target`.

### 4.3 Validate en passant target

- [x] Ensure en passant still requires:

   ```python
   to_square == board.en_passant_target
   ```

- [x] Ensure the captured pawn square is:

   ```python
   captured_square = (from_square.row, to_square.col)
   ```

- [x] Ensure the captured piece must be an enemy pawn.
- [x] Ensure the captured pawn is removed only after validation succeeds.

### 4.4 Preserve valid en passant

- [x] Ensure White valid en passant still works:

   ```text
   White pawn: e5
   Black pawn just moved d7d5
   en_passant_target: d6
   Move: e5d6
   ```

- [x] Ensure Black valid en passant still works:

   ```text
   Black pawn: d4
   White pawn just moved e2e4
   en_passant_target: e3
   Move: d4e3
   ```

### 4.5 Run en passant tests

- [x] Run:

   ```bash
   python -m pytest tests -q -k "en_passant"
   ```

- [x] Confirm both valid and invalid en passant cases pass.

---

## Task 5: Clean up real-position test coordinates

**Status: IN PROGRESS** — `test_en_passant_edge_cases.py` fully converted. Remaining priority files with raw coords: `test_castling.py` (82), `test_en_passant.py` (66), `test_promotion.py` (63), `test_checkmate.py` (59), `test_check_checkmate_stalemate.py` (45), `test_clone.py` (40), `test_board_setup.py` (19). `test_legal_moves.py` has 0 raw coords.

### 5.1 Confirm or add helper functions

- [x] Ensure `tests/helpers.py` contains:

   ```python
   from chess_game.chess.coords import algebraic_to_index

   def sq(name: str):
       return algebraic_to_index(name)
   ```

- [x] Ensure helper assertions exist:

   ```python
   assert_piece(board, "e4", Color.WHITE, PieceType.PAWN)
   assert_empty(board, "e4")
   ```

- [x] Add these helpers if missing.

### 5.2 Convert board setup tests

- [ ] Update `tests/test_board_setup.py`.
- [ ] Replace real-position raw coordinates with `sq("...")`.
- [ ] Examples:

  ```python
  board.get_piece(sq("e1"))
  board.get_piece(sq("e8"))
  board.get_piece(sq("a2"))
  board.get_piece(sq("h7"))
  ```

- [ ] Leave raw coordinate usage only in tests explicitly about internal row/column indexing.

### 5.3 Convert castling tests

- [ ] Update castling-related tests.
- [ ] Use:

  ```python
  sq("e1"), sq("g1"), sq("c1"), sq("a1"), sq("h1")
  sq("e8"), sq("g8"), sq("c8"), sq("a8"), sq("h8")
  ```

- [ ] Ensure comments describe chess squares, not raw row numbers.

### 5.4 Convert en passant tests

- [ ] Update en passant tests.
- [ ] Use algebraic setup:

  ```python
  place_piece(board, "e5", Color.WHITE, PieceType.PAWN)
  place_piece(board, "d5", Color.BLACK, PieceType.PAWN)
  board.en_passant_target = sq("d6")
  ```

- [ ] Avoid raw row comments like `array row 2 = rank 5`.

### 5.5 Convert promotion tests

- [ ] Update promotion tests.
- [ ] Use algebraic setup:

  ```python
  white pawn on e7 promotes to e8
  black pawn on e2 promotes to e1
  ```

### 5.6 Convert selected check/stalemate/legal-move tests

- [ ] Update the highest-risk tests in:

  ```text
  tests/test_legal_moves.py
   tests/test_check_checkmate_stalemate.py
   tests/test_checkmate.py
  ```

- [ ] Convert real chess positions to algebraic helpers.
- [ ] Do not rewrite every low-level unit test if it does not improve clarity.

### 5.7 Count remaining raw coordinate usage

- [ ] Run a grep such as:

  ```bash
  grep -R "get_square_constant(\|ConstantSquare(" -n tests
  ```

- [ ] Review the remaining matches.
- [ ] Ensure each remaining raw coordinate usage is either:
  - [ ] an internal coordinate test, or
  - [ ] a deliberately low-level test with a clear comment explaining why raw coordinates are appropriate.

---

## Task 6: Fix stale coordinate comments

**Status: DONE** — Full-project search found no stale coordinate comments remaining.

### 6.1 Search for stale comments

- [x] Run:

   ```bash
   grep -R "row 0 = rank 1\|row 7 = rank 8\|rank 1.*row 0\|rank 8.*row 7\|array row 2 = rank 5" -n .
   ```

- [x] Also search:

   ```bash
   grep -R "old coordinate\|broken coordinate\|ROW_5.*row 2\|ROW_1.*row 0" -n .
   ```

### 6.2 Correct or remove stale comments

- [x] Fix comments in tests.
- [x] Fix comments in docs.
- [x] Fix comments in source files.
- [x] If a historical doc intentionally describes old behavior, mark the section clearly as obsolete historical context.

### 6.3 Re-run docs/test grep

- [x] Repeat the grep commands.
- [x] Confirm no misleading coordinate comments remain.

---

## Task 7: Resolve `BoardState`

**Status: DONE** — Option A chosen. `BoardState` class/module removed. `Board` owns all state directly.

### 7.1 Determine whether `BoardState` is used

- [x] Search:

   ```bash
   grep -R "BoardState" -n chess_game tests
   ```

- [x] Determine whether `BoardState` is used in the real engine path.
- [x] Determine whether any tests only cover dead `BoardState` behavior.

### 7.2 Choose one path

Choose exactly one of these options.

#### Option A: Remove stale `BoardState` **(CHOSEN)**

Use this option if `BoardState` is unused or only exists from an old design.

- [x] Delete the stale `BoardState` class/module.
- [x] Remove stale imports.
- [x] Remove tests that only test dead `BoardState` behavior.
- [x] Update documentation if it still refers to `BoardState` as part of the live architecture.
- [x] Ensure `Board` is clearly documented as the owner of:
   - [x] board array,
   - [x] turn,
   - [x] castling rights,
   - [x] en passant target.

#### Option B: Keep and repair `BoardState`

Use this option only if `BoardState` is intentionally part of the architecture.

- [ ] Make `Board` use `BoardState` consistently.
- [ ] Ensure no duplicate state can diverge between `Board` and `BoardState`.
- [ ] Rewrite `BoardState.clone()` so:
   - [ ] board rows are new lists,
   - [ ] pieces are new objects,
   - [ ] each cloned piece's `_square` matches the cloned board square,
   - [ ] turn is copied,
   - [ ] castling rights are copied,
   - [ ] en passant target is copied.
- [ ] Add direct `BoardState.clone()` tests.
- [ ] Add a test proving mutating a cloned state does not mutate the original.

### 7.3 Preferred result

- [x] Prefer Option A unless there is a clear, documented reason to keep `BoardState`.

---

## Task 8: Optional AI evaluation orientation fix

**Status: DONE** — Fix applied (`row = 7 - row` for Black in `ai.py:84`). Starting-position evaluation confirmed at `0`. Symmetry tests (8.3) complete with 8 tests in `tests/test_ai.py`.

Do this only after Tasks 1 through 7 are complete.

### 8.1 Check starting-position evaluation

- [x] Run a small smoke script:

   ```python
   from chess_game.chess.board import Board
   from chess_game.chess.ai import evaluate

   print(evaluate(Board()))
   ```

- [x] Decide whether a nonzero starting evaluation is intentional.
- [x] If it is intentional, document the reason.
- [x] If it is not intentional, continue with this task.

### 8.2 Inspect piece-square-table orientation

- [x] Open:

   ```text
   chess_game/chess/ai.py
   ```

- [x] Inspect how piece-square tables are indexed.
- [x] If tables are written from White's perspective, use mirrored rows for Black:

   ```python
   eval_row = row if piece.color == Color.WHITE else 7 - row
   ```

### 8.3 Add evaluation symmetry tests

- [x] Add a test asserting the starting position evaluates to `0`, unless a documented tempo bonus exists.
- [x] Add a mirrored-position test to confirm White/Black piece-square scoring is symmetric.
- [x] Ensure AI simulations still do not mutate the original board.

### 8.4 Do not tune AI search

- [x] Do not change depth behavior.
- [x] Do not add pruning.
- [x] Do not add opening books.
- [x] Do not change the move picker except as needed for the evaluation bug.

---

## Task 9: Remove generated/cache files

**Status: PARTIAL** — Cache files removed (9.1 DONE). `.gitignore` needs updating (9.2 NOT DONE). Current `.gitignore` is missing: `*.py[cod]`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/`, `venv/`.

### 9.1 Remove Python cache files

- [x] Remove any committed/generated cache directories:

   ```bash
   find . -type d -name "__pycache__" -prune -exec rm -rf {} +
   rm -rf .pytest_cache
   ```

- [x] Do not remove virtual environments or user-local files unless they are part of the repo by mistake.

### 9.2 Update `.gitignore`

- [ ] Ensure `.gitignore` includes:

   ```text
   __pycache__/
   *.py[cod]
   .pytest_cache/
   .mypy_cache/
   .ruff_cache/
   .coverage
   htmlcov/
   .venv/
   venv/
   ```

### 9.3 Verify clean status

- [ ] Run:

  ```bash
  git status --short
  ```

- [ ] Confirm no cache files are staged.

---

## Task 10: Final acceptance tests

**Status: NOT STARTED** — Blocked on Tasks 3, 5, 8.3, 9.2.

### 10.1 Run targeted tests

- [ ] Run:

  ```bash
  python -m pytest tests -q -k "castling or en_passant"
  ```

- [ ] Confirm all targeted tests pass.

### 10.2 Run full test suite

- [ ] Run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Required result: zero failures.

### 10.3 Manual smoke script

- [ ] Run this script from the repo root:

  ```python
  from chess_game.chess.board import Board
  from chess_game.chess.move import parse_move_notation
  from chess_game.chess.coords import algebraic_to_index
  from chess_game.chess.types import Color, Piece, PieceType

  def sq(name):
      return algebraic_to_index(name)

  def clear(board):
      board.clear_board()

  # White queenside castling must fail when b1 is occupied.
  board = Board()
  clear(board)
  board.set_piece(sq("e1"), Piece(Color.WHITE, PieceType.KING, sq("e1")))
  board.set_piece(sq("a1"), Piece(Color.WHITE, PieceType.ROOK, sq("a1")))
  board.set_piece(sq("b1"), Piece(Color.WHITE, PieceType.KNIGHT, sq("b1")))
  board.set_piece(sq("e8"), Piece(Color.BLACK, PieceType.KING, sq("e8")))
  board.turn = Color.WHITE
  assert board.make_move(sq("e1"), sq("c1")) is False
  assert board.get_piece(sq("e1")).kind == PieceType.KING
  assert board.get_piece(sq("a1")).kind == PieceType.ROOK
  assert board.get_piece(sq("b1")).kind == PieceType.KNIGHT

  # Black queenside castling must fail when b8 is occupied.
  board = Board()
  clear(board)
  board.set_piece(sq("e8"), Piece(Color.BLACK, PieceType.KING, sq("e8")))
  board.set_piece(sq("a8"), Piece(Color.BLACK, PieceType.ROOK, sq("a8")))
  board.set_piece(sq("b8"), Piece(Color.BLACK, PieceType.KNIGHT, sq("b8")))
  board.set_piece(sq("e1"), Piece(Color.WHITE, PieceType.KING, sq("e1")))
  board.turn = Color.BLACK
  assert board.make_move(sq("e8"), sq("c8")) is False
  assert board.get_piece(sq("e8")).kind == PieceType.KING
  assert board.get_piece(sq("a8")).kind == PieceType.ROOK
  assert board.get_piece(sq("b8")).kind == PieceType.KNIGHT

  # White long en passant must fail.
  board = Board()
  clear(board)
  board.set_piece(sq("e1"), Piece(Color.WHITE, PieceType.KING, sq("e1")))
  board.set_piece(sq("e8"), Piece(Color.BLACK, PieceType.KING, sq("e8")))
  board.set_piece(sq("e3"), Piece(Color.WHITE, PieceType.PAWN, sq("e3")))
  board.set_piece(sq("d5"), Piece(Color.BLACK, PieceType.PAWN, sq("d5")))
  board.en_passant_target = sq("d6")
  board.turn = Color.WHITE
  assert board.make_move(sq("e3"), sq("d6")) is False
  assert board.get_piece(sq("e3")).kind == PieceType.PAWN
  assert board.get_piece(sq("d5")).kind == PieceType.PAWN
  assert board.get_piece(sq("d6")) is None

  # Black long en passant must fail.
  board = Board()
  clear(board)
  board.set_piece(sq("e1"), Piece(Color.WHITE, PieceType.KING, sq("e1")))
  board.set_piece(sq("e8"), Piece(Color.BLACK, PieceType.KING, sq("e8")))
  board.set_piece(sq("d6"), Piece(Color.BLACK, PieceType.PAWN, sq("d6")))
  board.set_piece(sq("e4"), Piece(Color.WHITE, PieceType.PAWN, sq("e4")))
  board.en_passant_target = sq("e3")
  board.turn = Color.BLACK
  assert board.make_move(sq("d6"), sq("e3")) is False
  assert board.get_piece(sq("d6")).kind == PieceType.PAWN
  assert board.get_piece(sq("e4")).kind == PieceType.PAWN
  assert board.get_piece(sq("e3")) is None

  print("fix2 smoke ok")
  ```

### 10.4 Regression checklist

- [ ] `e2e4` still works.
- [ ] `e7e5` still works after White moves.
- [ ] Legal White kingside castling still works.
- [ ] Legal White queenside castling still works.
- [ ] Legal Black kingside castling still works.
- [ ] Legal Black queenside castling still works.
- [ ] White queenside castling with `b1` occupied is rejected.
- [ ] Black queenside castling with `b8` occupied is rejected.
- [ ] White valid en passant still works.
- [ ] Black valid en passant still works.
- [ ] White illegal long en passant is rejected.
- [ ] Black illegal long en passant is rejected.
- [ ] Legal move generation still returns only side-to-move legal moves.
- [ ] Check/checkmate/stalemate tests still pass.
- [ ] Promotion tests still pass.
- [ ] Clone/simulation tests still pass.
- [ ] No generated cache files are committed.

---

## Suggested commit breakdown

Use small commits:

1. `test: add castling and en passant regression tests`
2. `fix: require b-file clear for queenside castling`
3. `refactor: centralize castling validation`
4. `fix: require one-row diagonal en passant geometry`
5. `test: use algebraic helpers for real chess positions`
6. `docs: correct stale coordinate comments`
7. `refactor: resolve stale board state architecture`
8. `fix: clean generated cache files and gitignore`
9. `test: add final fix2 smoke coverage`

If the optional AI evaluation fix is included:

10. `fix: mirror black piece-square table evaluation`
