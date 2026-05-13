# Chess Engine Core Repair TODO

## Implementation rules for Copilot

- Treat `CHESS_ENGINE_REPAIR_SPEC.md` as the authoritative contract.
- Do not chase the 21 current failing tests one by one before fixing the coordinate invariant and legal-move pipeline.
- Do not weaken tests to make the broken engine pass.
- Do not add new AI features until the rules engine is correct.
- Keep the public API stable where practical, but correctness wins over preserving broken behavior.
- After every major task group, run `python -m pytest tests -q` and record the current failure count in your implementation notes.

---

## Task 0: Establish baseline and working branch

### 0.1 Reproduce the current test state

- [ ] From the repo root, run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Confirm that the starting point is approximately:

  ```text
  97 tests collected
  76 passed
  21 failed
  ```

- [ ] If the failure count differs, inspect the failures and continue with the architectural repair anyway.

### 0.2 Create a repair branch

- [ ] Create a dedicated branch, for example:

  ```bash
  git checkout -b fix/core-rules-coordinate-system
  ```

### 0.3 Add the spec and TODO docs to the repo

- [ ] Copy this TODO into `docs/CHESS_ENGINE_REPAIR_TODO.md`.
- [ ] Copy the companion spec into `docs/CHESS_ENGINE_REPAIR_SPEC.md`.
- [ ] Do not delete older docs yet; update them later after the code is corrected.

---

## Task 1: Fix the canonical coordinate system

### 1.1 Pick and enforce the canonical convention

- [ ] Use this convention everywhere:

  ```text
  row 0 = rank 8
  row 1 = rank 7
  row 2 = rank 6
  row 3 = rank 5
  row 4 = rank 4
  row 5 = rank 3
  row 6 = rank 2
  row 7 = rank 1

  col 0 = file a
  col 1 = file b
  col 2 = file c
  col 3 = file d
  col 4 = file e
  col 5 = file f
  col 6 = file g
  col 7 = file h
  ```

- [ ] Search for all contradictory comments:

  ```bash
  grep -R "row 0 = rank 1\|row 7 = rank 8\|rank 1.*row 0\|rank 8.*row 7" -n .
  ```

- [ ] Update or remove all stale comments that describe the old/broken mapping.

### 1.2 Fix row constants

Prefer the rank-semantic mapping:

- [ ] In `chess_game/chess/constants.py`, redefine row constants so rank names match chess ranks:

  ```python
  ROW_8 = RowConstant(0)
  ROW_7 = RowConstant(1)
  ROW_6 = RowConstant(2)
  ROW_5 = RowConstant(3)
  ROW_4 = RowConstant(4)
  ROW_3 = RowConstant(5)
  ROW_2 = RowConstant(6)
  ROW_1 = RowConstant(7)
  ```

- [ ] Update any row-list/dict that maps internal row indexes to constants:

  ```python
  ROWS_BY_INDEX = [ROW_8, ROW_7, ROW_6, ROW_5, ROW_4, ROW_3, ROW_2, ROW_1]
  ```

- [ ] Ensure `get_row_constant(0)` returns `ROW_8`.
- [ ] Ensure `get_row_constant(7)` returns `ROW_1`.
- [ ] Update `RowConstant.__repr__()` so it returns the semantic name, not `ROW_{self._value + 1}`.
- [ ] If `RowConstant` needs a `rank` property, add one explicitly rather than deriving display names incorrectly.

### 1.3 Fix algebraic conversion

- [ ] In `chess_game/chess/coords.py`, fix `algebraic_to_index()`:

  ```python
  rank = int(rank_char)
  row = get_row_constant(8 - rank)
  col = get_col_constant(ord(file_char) - ord("a"))
  ```

- [ ] Fix `index_to_algebraic()`:

  ```python
  rank = 8 - int(square.row)
  file_char = chr(ord("a") + int(square.col))
  return f"{file_char}{rank}"
  ```

- [ ] Update all docstrings in `coords.py` to say `row 0 = rank 8` and `row 7 = rank 1`.

### 1.4 Add coordinate tests

- [ ] Create or update tests for round-trip coordinate conversion:

  ```python
  @pytest.mark.parametrize("algebraic,row,col", [
      ("a8", 0, 0),
      ("e8", 0, 4),
      ("h8", 0, 7),
      ("a1", 7, 0),
      ("e1", 7, 4),
      ("h1", 7, 7),
      ("e2", 6, 4),
      ("e7", 1, 4),
  ])
  def test_algebraic_to_index_canonical(algebraic, row, col): ...
  ```

- [ ] Add tests for invalid algebraic squares:
  - [ ] empty string,
  - [ ] one character,
  - [ ] three characters,
  - [ ] file outside `a`-`h`,
  - [ ] rank outside `1`-`8`.

### 1.5 Update tests to avoid raw row confusion

- [ ] Add a helper in `tests/helpers.py`:

  ```python
  from chess_game.chess.coords import algebraic_to_index

  def sq(name: str) -> ConstantSquare:
      return algebraic_to_index(name)
  ```

- [ ] Prefer `sq("e2")` over `ConstantSquare(row=ROW_2, col=COL_E)` in tests that describe real chess squares.
- [ ] Leave raw row/col tests only where the test is explicitly about internals.

---

## Task 2: Fix initial board setup

### 2.1 Update `Board._create_board()`

- [ ] In `chess_game/chess/board/board.py`, ensure the initial board is:

  ```text
  row 0: black back rank
  row 1: black pawns
  rows 2-5: empty
  row 6: white pawns
  row 7: white back rank
  ```

- [ ] Ensure every created piece has `_square` set to the actual internal square.
- [ ] Verify that `ROW_8` is used for black back rank, `ROW_7` for black pawns, `ROW_2` for white pawns, and `ROW_1` for white back rank if using rank-semantic row constants.

### 2.2 Add starting-position tests

- [ ] Add tests asserting these exact positions:

  ```python
  assert_piece(board, "a8", Color.BLACK, PieceType.ROOK)
  assert_piece(board, "e8", Color.BLACK, PieceType.KING)
  assert_piece(board, "h8", Color.BLACK, PieceType.ROOK)
  assert_piece(board, "a7", Color.BLACK, PieceType.PAWN)
  assert_piece(board, "e7", Color.BLACK, PieceType.PAWN)
  assert_piece(board, "h7", Color.BLACK, PieceType.PAWN)

  assert_piece(board, "a2", Color.WHITE, PieceType.PAWN)
  assert_piece(board, "e2", Color.WHITE, PieceType.PAWN)
  assert_piece(board, "h2", Color.WHITE, PieceType.PAWN)
  assert_piece(board, "a1", Color.WHITE, PieceType.ROOK)
  assert_piece(board, "e1", Color.WHITE, PieceType.KING)
  assert_piece(board, "h1", Color.WHITE, PieceType.ROOK)
  ```

- [ ] Add tests asserting representative empty squares:

  ```python
  assert board.get_piece(sq("e3")) is None
  assert board.get_piece(sq("e4")) is None
  assert board.get_piece(sq("e5")) is None
  assert board.get_piece(sq("e6")) is None
  ```

### 2.3 Add notation smoke tests

- [ ] Add a test that standard opening moves work through `parse_move_notation()`:

  ```python
  board = Board()

  move = parse_move_notation("e2e4")
  assert board.make_move(move.start, move.end, move.promotion) is True
  assert_piece(board, "e4", Color.WHITE, PieceType.PAWN)
  assert board.turn == Color.BLACK

  move = parse_move_notation("e7e5")
  assert board.make_move(move.start, move.end, move.promotion) is True
  assert_piece(board, "e5", Color.BLACK, PieceType.PAWN)
  assert board.turn == Color.WHITE
  ```

---

## Task 3: Repair the regular move-validation pipeline

### 3.1 Inspect the current broken path

- [ ] Review `chess_game/chess/board/move_validation.py`.
- [ ] Confirm that `MoveValidator.is_valid_move()` currently returns `True` for many illegal moves because it does not require `to_square` to be in `PieceMovers.get_valid_moves(...)`.
- [ ] Review `Board.is_valid_rook_move()`, `is_valid_bishop_move()`, `is_valid_queen_move()`, `is_valid_knight_move()`, `is_valid_king_move()`, and `is_valid_pawn_move()`.
- [ ] Confirm these wrappers currently only check source piece type and then call generic validation.

### 3.2 Define the validation flow

- [ ] Implement this exact regular-move flow in `MoveValidator.is_valid_move()`:

  ```text
  1. Source square must contain a piece.
  2. Destination must be on board.
  3. Destination must not contain a friendly piece.
  4. Castling must be detected and delegated to castling validation.
  5. En passant must be detected and delegated to en passant validation.
  6. For normal moves, destination must be in PieceMovers.get_valid_moves(piece, board_state).
  7. Simulate the move on a cloned state.
  8. Reject the move if it leaves the moving side's king in check.
  9. Otherwise return True.
  ```

- [ ] Remove duplicate en passant checks in `is_valid_move()`.
- [ ] Remove debug `print()` calls.

### 3.3 Repair `PieceMovers`

- [ ] Review `chess_game/chess/pieces/piece_movers.py` for each piece type.
- [ ] Ensure rook moves:
  - [ ] same rank/file only,
  - [ ] stop at blockers,
  - [ ] include first enemy square,
  - [ ] exclude friendly occupied square,
  - [ ] cannot move diagonally.
- [ ] Ensure bishop moves:
  - [ ] diagonals only,
  - [ ] stop at blockers,
  - [ ] include first enemy square,
  - [ ] exclude friendly occupied square,
  - [ ] cannot move straight.
- [ ] Ensure queen moves:
  - [ ] rook + bishop movement only,
  - [ ] stop at blockers,
  - [ ] cannot move like a knight.
- [ ] Ensure knight moves:
  - [ ] only 8 L-shaped moves,
  - [ ] can jump blockers,
  - [ ] exclude friendly occupied square,
  - [ ] include enemy occupied square.
- [ ] Ensure king moves:
  - [ ] one square in any direction,
  - [ ] exclude friendly occupied square,
  - [ ] do not include castling unless this is intentionally part of the architecture,
  - [ ] never include two-square normal moves.
- [ ] Ensure pawn moves use canonical direction:
  - [ ] white `row_delta = -1`,
  - [ ] black `row_delta = +1`,
  - [ ] one-square forward only if empty,
  - [ ] two-square forward only from starting row and both squares empty,
  - [ ] diagonal capture only when an enemy piece is present,
  - [ ] en passant candidate only when the target matches `board.en_passant_target`.

### 3.4 Add piece-geometry regression tests

- [ ] Add/repair tests proving illegal geometry is rejected:
  - [ ] rook diagonal move rejected,
  - [ ] bishop straight move rejected,
  - [ ] queen knight-like move rejected,
  - [ ] knight straight move rejected,
  - [ ] knight diagonal move rejected,
  - [ ] king two-square normal move rejected,
  - [ ] pawn backward move rejected,
  - [ ] pawn forward capture rejected,
  - [ ] pawn diagonal non-capture rejected unless en passant.

### 3.5 Add blocker tests

- [ ] Add/repair tests proving sliding pieces cannot move through blockers:
  - [ ] rook blocked by friendly piece,
  - [ ] rook blocked by enemy before destination,
  - [ ] bishop blocked by friendly piece,
  - [ ] bishop blocked by enemy before destination,
  - [ ] queen blocked on rank/file,
  - [ ] queen blocked on diagonal.

---

## Task 4: Fix legal move generation

### 4.1 Update `Board.get_legal_moves()`

- [ ] In `Board.get_legal_moves(square=None)`, if `square` is `None`, iterate only pieces whose `piece.color == self.turn`.
- [ ] If `square` is provided and empty, return `[]`.
- [ ] If `square` is provided and contains an opponent piece, return `[]` unless a clearly documented override is added.
- [ ] Do not return moves for both sides in normal game play.

### 4.2 Update `MoveValidator.get_legal_moves()`

- [ ] Make `MoveValidator.get_legal_moves(from_square=...)` use pseudo-legal destinations plus legal validation.
- [ ] Remove the unused or misleading `piece_type` argument if possible.
- [ ] If preserving `piece_type` for compatibility, do not allow it to override the actual piece on the source square.

### 4.3 Add legal move generation tests

- [ ] On the starting position, assert `Board.turn == Color.WHITE`.
- [ ] Assert `Board.get_legal_moves()` contains White moves such as:
  - [ ] `e2e3`,
  - [ ] `e2e4`,
  - [ ] `g1f3`,
  - [ ] `b1c3`.
- [ ] Assert it does not contain Black moves such as:
  - [ ] `e7e6`,
  - [ ] `e7e5`,
  - [ ] `g8f6`,
  - [ ] `b8c6`.
- [ ] After White plays `e2e4`, assert Black legal moves are generated and White moves are not.

---

## Task 5: Implement reliable attack detection and check logic

### 5.1 Add a canonical attack detector

- [ ] Implement one canonical helper, for example:

  ```python
  def is_square_attacked(board_state: BoardState, square: ConstantSquare, by_color: Color) -> bool:
      ...
  ```

- [ ] It must evaluate attacks without calling full legal move generation recursively.
- [ ] It must handle all piece types:
  - [ ] pawn attacks,
  - [ ] knight attacks,
  - [ ] bishop attacks,
  - [ ] rook attacks,
  - [ ] queen attacks,
  - [ ] king attacks.

### 5.2 Fix pawn attack semantics

- [ ] Ensure White pawns attack one row upward/decreasing:

  ```text
  from e4, white attacks d5 and f5
  ```

- [ ] Ensure Black pawns attack one row downward/increasing:

  ```text
  from e5, black attacks d4 and f4
  ```

- [ ] Do not treat pawn forward movement as an attack.

### 5.3 Implement `Board.is_in_check(color)`

- [ ] Find the king of the requested color.
- [ ] If the king is missing, choose one behavior and test it:
  - [ ] either return `False` for tests using kingless isolated boards,
  - [ ] or raise a clear exception for invalid game states.
- [ ] Prefer returning `False` for compatibility with current isolated piece tests unless stricter behavior is intentionally adopted.
- [ ] Check whether the king square is attacked by the opponent.

### 5.4 Implement `Board.is_checkmate(color=None)`

- [ ] If `color is None`, use `self.turn`.
- [ ] Return `False` if the color is not in check.
- [ ] Temporarily set/evaluate legal moves for that color safely.
- [ ] Return `True` only if the color is in check and has no legal moves.

### 5.5 Implement `Board.is_stalemate(color=None)`

- [ ] If `color is None`, use `self.turn`.
- [ ] Return `False` if the color is in check.
- [ ] Return `True` only if the color is not in check and has no legal moves.

### 5.6 Remove broken delegation

- [ ] Remove calls to non-existent methods:
  - [ ] `BoardState.is_in_check`,
  - [ ] `BoardState.is_checkmate`,
  - [ ] `BoardState.is_stalemate`.

### 5.7 Add check/checkmate/stalemate tests

- [ ] Add direct check detection tests:
  - [ ] rook checking king on same file,
  - [ ] bishop checking king on diagonal,
  - [ ] knight checking king,
  - [ ] pawn checking king,
  - [ ] blocked sliding attack is not check.
- [ ] Add checkmate tests:
  - [ ] simple back-rank or ladder mate,
  - [ ] Fool's Mate through coordinate notation if the move pipeline supports it.
- [ ] Add stalemate tests:
  - [ ] known king + queen stalemate position.

---

## Task 6: Fix simulation and clone behavior

### 6.1 Rewrite `BoardState.clone()`

- [ ] Ensure cloned board rows are new lists.
- [ ] Ensure cloned pieces are new `Piece` objects, not references to original pieces.
- [ ] Ensure each cloned piece's `_square` points to its cloned square.
- [ ] Preserve:
  - [ ] `turn`,
  - [ ] `en_passant_target`,
  - [ ] castling rights.

### 6.2 Rewrite `Board.clone()`

- [ ] Create a clone without reusing the original board's state.
- [ ] Ensure `cloned.board is cloned._board_state.board`.
- [ ] Recreate validators/executors so they point at the cloned `BoardState`.
- [ ] Do not leave `cloned._move_validator.board` pointing at the original state.
- [ ] Do not leave `cloned._move_executor.board` pointing at the original state.

### 6.3 Add clone tests

- [ ] Set up a position with pieces and state:
  - [ ] a moved pawn,
  - [ ] non-default turn,
  - [ ] en passant target,
  - [ ] changed castling rights.
- [ ] Clone the board.
- [ ] Move a piece on the clone.
- [ ] Assert original board pieces and piece `_square` values are unchanged.
- [ ] Assert clone board pieces changed as expected.
- [ ] Assert clone state values were copied correctly.

### 6.4 Use clone for king-safety simulation

- [ ] Replace ad-hoc shallow-copy simulation in `MoveValidator._would_expose_king_to_check()` with the canonical clone/simulation path.
- [ ] Ensure en passant and castling simulations are handled correctly for king-safety checks.

---

## Task 7: Repair move execution and state transitions

### 7.1 Pick one owner for turn updates

- [ ] Decide whether `Board.make_move()` or `MoveExecutor.execute_move()` flips `turn`.
- [ ] Ensure the turn flips exactly once for a successful move.
- [ ] Ensure the turn does not flip for an illegal move.

### 7.2 Pick one owner for en passant target updates

- [ ] Decide whether `Board.make_move()` or `MoveExecutor.execute_move()` updates `en_passant_target`.
- [ ] Ensure the old target is cleared after any move that is not a two-square pawn advance.
- [ ] Ensure a new target is set after a two-square pawn advance.
- [ ] Ensure the target is the passed-over square, not the pawn's destination.

### 7.3 Pick one owner for castling rights updates

- [ ] Add a helper such as:

  ```python
  def update_castling_rights_for_move(board_state, moving_piece, from_square, to_square, captured_piece):
      ...
  ```

- [ ] Call it exactly once per successful move.

### 7.4 Ensure atomic move execution

- [ ] For normal moves:
  - [ ] remember destination piece as `captured_piece`,
  - [ ] update castling rights,
  - [ ] set destination to moving piece,
  - [ ] update moving piece `_square`,
  - [ ] clear source square.
- [ ] For promotion:
  - [ ] validate promotion piece before execution,
  - [ ] move pawn to destination,
  - [ ] replace pawn with promoted piece,
  - [ ] set promoted piece `_square`.
- [ ] For castling:
  - [ ] move king to destination,
  - [ ] move rook to correct square,
  - [ ] clear original king and rook squares,
  - [ ] clear both castling rights for that color.
- [ ] For en passant:
  - [ ] move capturing pawn to target square,
  - [ ] clear source square,
  - [ ] clear captured pawn square at `(from_square.row, to_square.col)`.

### 7.5 Remove redundant pin logic

- [ ] Review this pattern in `Board.make_move()`:

  ```python
  if start_piece.kind not in (PieceType.KNIGHT, PieceType.KING):
      if self._move_validator.is_piece_pinned(start_pos, start_piece.color):
          return False
  ```

- [ ] Remove it if legal validation already simulates the move and rejects self-check.
- [ ] Do not reject all pinned-piece moves blindly; a pinned piece may legally move along the pin line in some positions.

---

## Task 8: Repair castling

### 8.1 Validate castling coordinates

- [ ] Use canonical castling squares:
  - [ ] White: `e1g1`, `e1c1`, rooks `h1f1`, `a1d1`.
  - [ ] Black: `e8g8`, `e8c8`, rooks `h8f8`, `a8d8`.

### 8.2 Validate castling rights and pieces

- [ ] Require the king to be on the correct starting square.
- [ ] Require the rook to be on the correct rook square.
- [ ] Require the relevant castling right to be true.
- [ ] Reject castling if the destination is occupied.
- [ ] Reject castling if any path square between king and rook is occupied.

### 8.3 Validate attacks through castling path

- [ ] Reject castling if the king is currently in check.
- [ ] Reject kingside castling if `e1`, `f1`, or `g1` is attacked for White.
- [ ] Reject queenside castling if `e1`, `d1`, or `c1` is attacked for White.
- [ ] Reject kingside castling if `e8`, `f8`, or `g8` is attacked for Black.
- [ ] Reject queenside castling if `e8`, `d8`, or `c8` is attacked for Black.

### 8.4 Update castling rights

- [ ] Clear both rights when a king moves.
- [ ] Clear the side-specific right when a rook moves from its starting square.
- [ ] Clear the side-specific right when a rook is captured on its starting square.

### 8.5 Add castling regression tests

- [ ] Legal white kingside castling.
- [ ] Legal white queenside castling.
- [ ] Legal black kingside castling.
- [ ] Legal black queenside castling.
- [ ] Castling rejected while in check.
- [ ] Castling rejected through check.
- [ ] Castling rejected into check.
- [ ] Castling rejected with blocked path.
- [ ] Castling rejected after king moved away and back.
- [ ] Castling rejected after relevant rook moved away and back.
- [ ] Castling right cleared after rook capture on original square.

---

## Task 9: Repair en passant

### 9.1 Remove wrong two-row diagonal logic

- [ ] In `MoveValidator._is_en_passant_move()` and related code, remove any requirement that `row_diff == 2`.
- [ ] En passant capture must have:

  ```python
  abs(to_col - from_col) == 1
  to_row - from_row == -1 for White
  to_row - from_row == +1 for Black
  to_square == board.en_passant_target
  ```

### 9.2 Set en passant target correctly

- [ ] After White plays `e2e4`, target must be `e3`.
- [ ] After Black plays `d7d5`, target must be `d6`.
- [ ] The target must be cleared after the opponent makes any move that is not the en passant capture.

### 9.3 Execute en passant correctly

- [ ] For White `e5d6` after Black `d7d5`:
  - [ ] White pawn lands on `d6`.
  - [ ] White pawn source `e5` is empty.
  - [ ] Black pawn on `d5` is removed.
- [ ] For Black `d4e3` after White `e2e4`:
  - [ ] Black pawn lands on `e3`.
  - [ ] Black pawn source `d4` is empty.
  - [ ] White pawn on `e4` is removed.

### 9.4 Add en passant tests

- [ ] White en passant from a constructed position.
- [ ] Black en passant from a constructed position.
- [ ] Full sequence from starting position where practical.
- [ ] En passant expires after one half-move.
- [ ] En passant rejected if target square does not match.
- [ ] En passant rejected if the adjacent pawn did not just move two squares.
- [ ] En passant rejected if it exposes own king to check.

---

## Task 10: Repair promotion

### 10.1 Fix promotion rank logic

- [ ] White promotes on row `0` / rank `8`.
- [ ] Black promotes on row `7` / rank `1`.
- [ ] Remove old logic that says White promotes at row `7` and Black at row `0`.

### 10.2 Validate promotion choices

- [ ] Allow only:
  - [ ] `PieceType.QUEEN`,
  - [ ] `PieceType.ROOK`,
  - [ ] `PieceType.BISHOP`,
  - [ ] `PieceType.KNIGHT`.
- [ ] Reject:
  - [ ] `PieceType.KING`,
  - [ ] `PieceType.PAWN`,
  - [ ] `PieceType.EMPTY`,
  - [ ] invalid raw values.

### 10.3 Support default queen promotion

- [ ] If a pawn reaches the promotion rank with `promotion=None`, promote to queen unless the CLI/API is deliberately changed to require explicit choices.
- [ ] Document whichever behavior is chosen.

### 10.4 Add promotion tests

- [ ] White promotes on `e7e8q`.
- [ ] White promotes to rook, bishop, and knight.
- [ ] Black promotes on `e2e1q`.
- [ ] Black promotes to rook, bishop, and knight.
- [ ] Illegal promotion piece rejected.
- [ ] Pawn cannot promote from the wrong rank.
- [ ] Promotion cannot bypass normal pawn movement rules.

---

## Task 11: Fix CLI behavior

### 11.1 Fix game-over calls

- [ ] In `chess_game/main.py`, update `_game_over_message()` so it does not call `board.is_checkmate()` or `board.is_stalemate()` incorrectly.
- [ ] Either:

  ```python
  if board.is_checkmate(board.turn): ...
  if board.is_stalemate(board.turn): ...
  ```

  or implement default `color=None` in the Board methods and keep:

  ```python
  if board.is_checkmate(): ...
  if board.is_stalemate(): ...
  ```

### 11.2 Fix or disable the fake AI flag

- [ ] `main.py` accepts `--ai`, but `_game_loop()` currently ignores `use_ai` and `ai_depth`.
- [ ] Choose one:
  - [ ] Wire AI moves into the game loop after human moves, or
  - [ ] remove/disable `--ai` and print a clear message that AI mode is not available until after core rules repair.
- [ ] Do not leave a no-op AI flag.

### 11.3 Add CLI smoke tests

- [ ] Test `parse_move_notation("e2e4")` maps to `e2 -> e4` under the canonical coordinate system.
- [ ] Test promotion suffix parsing:
  - [ ] `q`,
  - [ ] `r`,
  - [ ] `b`,
  - [ ] `n`.
- [ ] Test invalid promotion suffix raises `ValueError`.
- [ ] Add a test for `_game_over_message()` if practical.

---

## Task 12: Fix AI safety without expanding scope

### 12.1 Repair AI legal move source

- [ ] Inspect `chess_game/chess/ai.py`.
- [ ] Ensure AI move generation uses only `board.get_legal_moves()` for the side to move.
- [ ] Remove or repair any helper that independently generates pseudo-legal or opponent moves incorrectly.

### 12.2 Repair AI simulation

- [ ] Ensure AI simulations use the fixed `Board.clone()`.
- [ ] Ensure simulated moves do not mutate the original board.
- [ ] Add at least one test where AI considers a move and the original board remains unchanged.

### 12.3 Repair transposition/FEN-like keys

- [ ] If `_fen_key()` or equivalent is kept, include:
  - [ ] board placement,
  - [ ] side to move,
  - [ ] castling rights,
  - [ ] en passant target.
- [ ] Do not call it a valid FEN if it is not full FEN.

### 12.4 Defer AI quality improvements

- [ ] Do not tune evaluation tables in this pass unless orientation bugs make them actively wrong.
- [ ] Do not add opening books, time controls, or search optimizations.
- [ ] Record AI improvement ideas separately after core rules pass.

---

## Task 13: Clean up tests and fixtures

### 13.1 Remove duplicate fixtures

- [ ] In `tests/conftest.py`, remove duplicate `simple_opening_position` fixture definitions.
- [ ] Ensure helper comments reflect the canonical coordinate system.

### 13.2 Classify and update current failing tests

For each currently failing test, classify it:

- [ ] `tests/test_corner.py::test_checkmate_with_promotion`
- [ ] `tests/test_corner.py::test_stalemate_after_promotion`
- [ ] `tests/test_en_passant.py::test_castling_kingside_with_queenside_rook_only`
- [ ] `tests/test_en_passant_edge_cases.py::test_en_passant_capture_removes_pawn_from_original_square`
- [ ] `tests/test_en_passant_edge_cases.py::test_full_en_passant_sequence_from_starting_position`
- [ ] `tests/test_king_safety.py::test_promotion_from_rank_6_blocked`
- [ ] all currently failing `tests/test_piece_moves.py` tests

For each test:

- [ ] If the test is conceptually correct, fix the implementation.
- [ ] If the test encodes the broken coordinate system, rewrite it using algebraic helpers.
- [ ] If the test setup is ambiguous, rewrite it to express the actual chess position clearly.

### 13.3 Add helper assertions

- [ ] Add `assert_piece(board, square_name, color, kind)` helper.
- [ ] Add `assert_empty(board, square_name)` helper.
- [ ] Add `move_tuple_to_names(...)` or equivalent helper to make legal move tests readable.

---

## Task 14: Clean up engine code

### 14.1 Remove debug output

- [ ] Remove all engine `print("DEBUG ...")` calls from:
  - [ ] `board.py`,
  - [ ] `move_validation.py`,
  - [ ] `en_passant.py`,
  - [ ] any other engine module.

- [ ] If diagnostics are still needed, use logging behind a disabled-by-default logger.

### 14.2 Remove duplicate methods

- [ ] In `Board`, remove the duplicate `clear_board()` definition.
- [ ] Ensure the remaining implementation uses the canonical `get_square_constant(row, col)` or equivalent safely.

### 14.3 Remove stale imports and aliases

- [ ] Remove unused imports discovered by static inspection.
- [ ] Fix type annotations that refer to undefined `Square` aliases.
- [ ] Ensure `mypy.ini` remains coherent if type checking is still intended.

### 14.4 Review debug scripts

- [ ] Inspect:
  - [ ] `debug_ep.py`,
  - [ ] `debug_move.py`,
  - [ ] `fix_tests.py`.
- [ ] Delete obsolete scripts or move them under `tools/debug/` with clear names.
- [ ] Do not leave scripts that encode the old coordinate convention without warning.

---

## Task 15: Fix CI and packaging

### 15.1 Fix GitHub Actions

- [ ] Edit `.github/workflows/ci.yml`.
- [ ] Remove `pip install -r requirements.txt` unless a real `requirements.txt` is added.
- [ ] Use pytest, not unittest:

  ```yaml
  - name: Install package and test dependencies
    run: |
      python -m pip install --upgrade pip
      python -m pip install -e .
      python -m pip install pytest pydantic

  - name: Run tests
    run: python -m pytest tests -q
  ```

### 15.2 Formalize dependencies

- [ ] In `pyproject.toml`, add runtime dependencies if needed:

  ```toml
  dependencies = [
      "pydantic>=2",
  ]
  ```

- [ ] Add optional test dependencies if desired:

  ```toml
  [project.optional-dependencies]
  test = ["pytest"]
  ```

- [ ] Then CI can use:

  ```bash
  python -m pip install -e '.[test]'
  ```

### 15.3 Run CI-equivalent command locally

- [ ] Run:

  ```bash
  python -m pip install -e .
  python -m pytest tests -q
  ```

- [ ] Confirm it passes locally before committing.

---

## Task 16: Update documentation

### 16.1 Update coordinate docs

- [ ] Update `docs/coordinate_system.md` to match:

  ```text
  row 0 = rank 8
  row 7 = rank 1
  ```

- [ ] Include a table:

  ```text
  Algebraic | row | col
  a8        | 0   | 0
  e8        | 0   | 4
  h8        | 0   | 7
  e2        | 6   | 4
  e1        | 7   | 4
  ```

### 16.2 Update en passant docs

- [ ] Update `docs/en_passant.md` to explain:
  - [ ] passed-over target square,
  - [ ] one-row diagonal capture geometry,
  - [ ] captured pawn removal square,
  - [ ] immediate-half-move expiration.

### 16.3 Update README

- [ ] Update `README.md` with:
  - [ ] correct coordinate convention,
  - [ ] current test command,
  - [ ] CLI examples `e2e4`, `e7e5`, `e7e8q`,
  - [ ] whether AI mode is currently supported.

### 16.4 Update old planning docs

- [ ] Update or annotate:
  - [ ] `THE_PLAN.md`,
  - [ ] `TODO.md`,
  - [ ] `docs/REFACTOR_BOARD_TODO.md`,
  - [ ] `docs/REFACTOR_PROGRESS.md`,
  - [ ] `docs/EDGE_CASES_TODO.md`.

- [ ] Any doc that still mentions the old coordinate mapping must be corrected or marked obsolete.

---

## Task 17: Final acceptance tests

### 17.1 Full test suite

- [ ] Run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Required result: zero failures.

### 17.2 Manual smoke script

- [ ] Run this script from the repo root:

  ```python
  from chess_game.chess.board import Board
  from chess_game.chess.move import parse_move_notation
  from chess_game.chess.types import Color, PieceType
  from chess_game.chess.coords import algebraic_to_index, index_to_algebraic

  board = Board()

  for name in ["a1", "e1", "h1", "a8", "e8", "h8", "e2", "e7"]:
      assert index_to_algebraic(algebraic_to_index(name)) == name

  assert board.get_piece(algebraic_to_index("e2")).color == Color.WHITE
  assert board.get_piece(algebraic_to_index("e2")).kind == PieceType.PAWN
  assert board.get_piece(algebraic_to_index("e7")).color == Color.BLACK
  assert board.get_piece(algebraic_to_index("e7")).kind == PieceType.PAWN

  move = parse_move_notation("e2e4")
  assert board.make_move(move.start, move.end, move.promotion) is True
  assert board.get_piece(algebraic_to_index("e4")).color == Color.WHITE
  assert board.turn == Color.BLACK

  move = parse_move_notation("e7e5")
  assert board.make_move(move.start, move.end, move.promotion) is True
  assert board.get_piece(algebraic_to_index("e5")).color == Color.BLACK
  assert board.turn == Color.WHITE

  print("smoke ok")
  ```

### 17.3 CLI smoke test

- [ ] Start the CLI:

  ```bash
  python -m chess_game.main
  ```

- [ ] Enter:

  ```text
  e2e4
  e7e5
  g1f3
  b8c6
  quit
  ```

- [ ] Confirm:
  - [ ] legal moves are accepted,
  - [ ] board display updates correctly,
  - [ ] no crash occurs,
  - [ ] check/checkmate/stalemate calls do not raise exceptions.

### 17.4 Regression checklist

- [ ] `e2e4` works from the starting position.
- [ ] `e7e5` works after White moves.
- [ ] A rook cannot move diagonally.
- [ ] A bishop cannot move straight.
- [ ] A queen cannot move like a knight.
- [ ] A knight cannot move straight or diagonally.
- [ ] A king cannot move two squares except valid castling.
- [ ] A pawn cannot move backward.
- [ ] A pawn cannot capture forward.
- [ ] Sliding pieces cannot move through blockers.
- [ ] Legal move generation returns only the side to move.
- [ ] Check detection works.
- [ ] Checkmate detection works.
- [ ] Stalemate detection works.
- [ ] Castling works and rights update correctly.
- [ ] En passant works for both colors and expires correctly.
- [ ] Promotion works for both colors.
- [ ] Clone simulation does not mutate original boards.
- [ ] CI runs pytest.

---

## Suggested commit breakdown

Use small commits so regressions are easier to isolate:

1. `docs: add chess engine repair spec and todo`
2. `fix: enforce canonical board coordinate system`
3. `fix: repair initial board setup and algebraic parsing`
4. `fix: require pseudo-legal geometry in move validation`
5. `fix: generate legal moves only for side to move`
6. `fix: implement check checkmate and stalemate detection`
7. `fix: repair board cloning and simulation`
8. `fix: repair castling rights and execution`
9. `fix: repair en passant validation and execution`
10. `fix: repair promotion ranks and choices`
11. `fix: repair cli game-over and ai flag behavior`
12. `test: add core rules regression coverage`
13. `ci: run pytest correctly`
14. `docs: update coordinate and rules documentation`
