# Chess Engine Core Repair TODO

**Status: COMPLETE** — All 18 tasks (0–17) implemented, verified, and pushed.

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

- [x] From the repo root, run:

  ```bash
  python -m pytest tests -q
  ```

- [x] Confirm that the starting point is approximately:

  ```text
  97 tests collected
  76 passed
  21 failed
  ```

- [x] If the failure count differs, inspect the failures and continue with the architectural repair anyway.

### 0.2 Create a repair branch

- [x] Create a dedicated branch, for example:

  ```bash
  git checkout -b fix/core-rules-coordinate-system
  ```

### 0.3 Add the spec and TODO docs to the repo

- [x] Copy this TODO into `docs/CHESS_ENGINE_REPAIR_TODO.md`.
- [x] Copy the companion spec into `docs/CHESS_ENGINE_REPAIR_SPEC.md`.
- [x] Do not delete older docs yet; update them later after the code is corrected.

---

## Task 1: Fix the canonical coordinate system

### 1.1 Pick and enforce the canonical convention

- [x] Use this convention everywhere:

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

- [x] Search for all contradictory comments:

  ```bash
  grep -R "row 0 = rank 1\|row 7 = rank 8\|rank 1.*row 0\|rank 8.*row 7" -n .
  ```

- [x] Update or remove all stale comments that describe the old/broken mapping.

### 1.2 Fix row constants

Prefer the rank-semantic mapping:

- [x] In `chess_game/chess/constants.py`, redefine row constants so rank names match chess ranks:

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

- [x] Update any row-list/dict that maps internal row indexes to constants:

  ```python
  ROWS_BY_INDEX = [ROW_8, ROW_7, ROW_6, ROW_5, ROW_4, ROW_3, ROW_2, ROW_1]
  ```

- [x] Ensure `get_row_constant(0)` returns `ROW_8`.
- [x] Ensure `get_row_constant(7)` returns `ROW_1`.
- [x] Update `RowConstant.__repr__()` so it returns the semantic name, not `ROW_{self._value + 1}`.
- [x] If `RowConstant` needs a `rank` property, add one explicitly rather than deriving display names incorrectly.

### 1.3 Fix algebraic conversion

- [x] In `chess_game/chess/coords.py`, fix `algebraic_to_index()`:

  ```python
  rank = int(rank_char)
  row = get_row_constant(8 - rank)
  col = get_col_constant(ord(file_char) - ord("a"))
  ```

- [x] Fix `index_to_algebraic()`:

  ```python
  rank = 8 - int(square.row)
  file_char = chr(ord("a") + int(square.col))
  return f"{file_char}{rank}"
  ```

- [x] Update all docstrings in `coords.py` to say `row 0 = rank 8` and `row 7 = rank 1`.

### 1.4 Add coordinate tests

- [x] Create or update tests for round-trip coordinate conversion:

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

- [x] Add tests for invalid algebraic squares:
  - [x] empty string,
  - [x] one character,
  - [x] three characters,
  - [x] file outside `a`-`h`,
  - [x] rank outside `1`-`8`.

### 1.5 Update tests to avoid raw row confusion

- [x] Add a helper in `tests/helpers.py`:

  ```python
  from chess_game.chess.coords import algebraic_to_index

  def sq(name: str) -> ConstantSquare:
      return algebraic_to_index(name)
  ```

- [x] Prefer `sq("e2")` over `ConstantSquare(row=ROW_2, col=COL_E)` in tests that describe real chess squares.
- [x] Leave raw row/col tests only where the test is explicitly about internals.

---

## Task 2: Fix initial board setup

### 2.1 Update `Board._create_board()`

- [x] In `chess_game/chess/board/board.py`, ensure the initial board is:

  ```text
  row 0: black back rank
  row 1: black pawns
  rows 2-5: empty
  row 6: white pawns
  row 7: white back rank
  ```

- [x] Ensure every created piece has `_square` set to the actual internal square.
- [x] Verify that `ROW_8` is used for black back rank, `ROW_7` for black pawns, `ROW_2` for white pawns, and `ROW_1` for white back rank if using rank-semantic row constants.

### 2.2 Add starting-position tests

- [x] Add tests asserting these exact positions:

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

- [x] Add tests asserting representative empty squares:

  ```python
  assert board.get_piece(sq("e3")) is None
  assert board.get_piece(sq("e4")) is None
  assert board.get_piece(sq("e5")) is None
  assert board.get_piece(sq("e6")) is None
  ```

### 2.3 Add notation smoke tests

- [x] Add a test that standard opening moves work through `parse_move_notation()`:

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

- [x] Review `chess_game/chess/board/move_validation.py`.
- [x] Confirm that `MoveValidator.is_valid_move()` currently returns `True` for many illegal moves because it does not require `to_square` to be in `PieceMovers.get_valid_moves(...)`.
- [x] Review `Board.is_valid_rook_move()`, `is_valid_bishop_move()`, `is_valid_queen_move()`, `is_valid_knight_move()`, `is_valid_king_move()`, and `is_valid_pawn_move()`.
- [x] Confirm these wrappers currently only check source piece type and then call generic validation.

### 3.2 Define the validation flow

- [x] Implement this exact regular-move flow in `MoveValidator.is_valid_move()`:

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

- [x] Remove duplicate en passant checks in `is_valid_move()`.
- [x] Remove debug `print()` calls.

### 3.3 Repair `PieceMovers`

- [x] Review `chess_game/chess/pieces/piece_movers.py` for each piece type.
- [x] Ensure rook moves:
  - [x] same rank/file only,
  - [x] stop at blockers,
  - [x] include first enemy square,
  - [x] exclude friendly occupied square,
  - [x] cannot move diagonally.
- [x] Ensure bishop moves:
  - [x] diagonals only,
  - [x] stop at blockers,
  - [x] include first enemy square,
  - [x] exclude friendly occupied square,
  - [x] cannot move straight.
- [x] Ensure queen moves:
  - [x] rook + bishop movement only,
  - [x] stop at blockers,
  - [x] cannot move like a knight.
- [x] Ensure knight moves:
  - [x] only 8 L-shaped moves,
  - [x] can jump blockers,
  - [x] exclude friendly occupied square,
  - [x] include enemy occupied square.
- [x] Ensure king moves:
  - [x] one square in any direction,
  - [x] exclude friendly occupied square,
  - [x] do not include castling unless this is intentionally part of the architecture,
  - [x] never include two-square normal moves.
- [x] Ensure pawn moves use canonical direction:
  - [x] white `row_delta = -1`,
  - [x] black `row_delta = +1`,
  - [x] one-square forward only if empty,
  - [x] two-square forward only from starting row and both squares empty,
  - [x] diagonal capture only when an enemy piece is present,
  - [x] en passant candidate only when the target matches `board.en_passant_target`.

### 3.4 Add piece-geometry regression tests

- [x] Add/repair tests proving illegal geometry is rejected:
  - [x] rook diagonal move rejected,
  - [x] bishop straight move rejected,
  - [x] queen knight-like move rejected,
  - [x] knight straight move rejected,
  - [x] knight diagonal move rejected,
  - [x] king two-square normal move rejected,
  - [x] pawn backward move rejected,
  - [x] pawn forward capture rejected,
  - [x] pawn diagonal non-capture rejected unless en passant.

### 3.5 Add blocker tests

- [x] Add/repair tests proving sliding pieces cannot move through blockers:
  - [x] rook blocked by friendly piece,
  - [x] rook blocked by enemy before destination,
  - [x] bishop blocked by friendly piece,
  - [x] bishop blocked by enemy before destination,
  - [x] queen blocked on rank/file,
  - [x] queen blocked on diagonal.

---

## Task 4: Fix legal move generation

### 4.1 Update `Board.get_legal_moves()`

- [x] In `Board.get_legal_moves(square=None)`, if `square` is `None`, iterate only pieces whose `piece.color == self.turn`.
- [x] If `square` is provided and empty, return `[]`.
- [x] If `square` is provided and contains an opponent piece, return `[]` unless a clearly documented override is added.
- [x] Do not return moves for both sides in normal game play.

### 4.2 Update `MoveValidator.get_legal_moves()`

- [x] Make `MoveValidator.get_legal_moves(from_square=...)` use pseudo-legal destinations plus legal validation.
- [x] Remove the unused or misleading `piece_type` argument if possible.
- [x] If preserving `piece_type` for compatibility, do not allow it to override the actual piece on the source square.

### 4.3 Add legal move generation tests

- [x] On the starting position, assert `Board.turn == Color.WHITE`.
- [x] Assert `Board.get_legal_moves()` contains White moves such as:
  - [x] `e2e3`,
  - [x] `e2e4`,
  - [x] `g1f3`,
  - [x] `b1c3`.
- [x] Assert it does not contain Black moves such as:
  - [x] `e7e6`,
  - [x] `e7e5`,
  - [x] `g8f6`,
  - [x] `b8c6`.
- [x] After White plays `e2e4`, assert Black legal moves are generated and White moves are not.

---

## Task 5: Implement reliable attack detection and check logic

### 5.1 Add a canonical attack detector

- [x] Implement one canonical helper, for example:

  ```python
  def is_square_attacked(board_state: BoardState, square: ConstantSquare, by_color: Color) -> bool:
      ...
  ```

- [x] It must evaluate attacks without calling full legal move generation recursively.
- [x] It must handle all piece types:
  - [x] pawn attacks,
  - [x] knight attacks,
  - [x] bishop attacks,
  - [x] rook attacks,
  - [x] queen attacks,
  - [x] king attacks.

### 5.2 Fix pawn attack semantics

- [x] Ensure White pawns attack one row upward/decreasing:

  ```text
  from e4, white attacks d5 and f5
  ```

- [x] Ensure Black pawns attack one row downward/increasing:

  ```text
  from e5, black attacks d4 and f4
  ```

- [x] Do not treat pawn forward movement as an attack.

### 5.3 Implement `Board.is_in_check(color)`

- [x] Find the king of the requested color.
- [x] If the king is missing, choose one behavior and test it:
  - [x] either return `False` for tests using kingless isolated boards,
  - [x] or raise a clear exception for invalid game states.
- [x] Prefer returning `False` for compatibility with current isolated piece tests unless stricter behavior is intentionally adopted.
- [x] Check whether the king square is attacked by the opponent.

### 5.4 Implement `Board.is_checkmate(color=None)`

- [x] If `color is None`, use `self.turn`.
- [x] Return `False` if the color is not in check.
- [x] Temporarily set/evaluate legal moves for that color safely.
- [x] Return `True` only if the color is in check and has no legal moves.

### 5.5 Implement `Board.is_stalemate(color=None)`

- [x] If `color is None`, use `self.turn`.
- [x] Return `False` if the color is in check.
- [x] Return `True` only if the color is not in check and has no legal moves.

### 5.6 Remove broken delegation

- [x] Remove calls to non-existent methods:
  - [x] `BoardState.is_in_check`,
  - [x] `BoardState.is_checkmate`,
  - [x] `BoardState.is_stalemate`.

### 5.7 Add check/checkmate/stalemate tests

- [x] Add direct check detection tests:
  - [x] rook checking king on same file,
  - [x] bishop checking king on diagonal,
  - [x] knight checking king,
  - [x] pawn checking king,
  - [x] blocked sliding attack is not check.
- [x] Add checkmate tests:
  - [x] simple back-rank or ladder mate,
  - [x] Fool's Mate through coordinate notation if the move pipeline supports it.
- [x] Add stalemate tests:
  - [x] known king + queen stalemate position.

---

## Task 6: Fix simulation and clone behavior

### 6.1 Rewrite `BoardState.clone()`

- [x] Ensure cloned board rows are new lists.
- [x] Ensure cloned pieces are new `Piece` objects, not references to original pieces.
- [x] Ensure each cloned piece's `_square` points to its cloned square.
- [x] Preserve:
  - [x] `turn`,
  - [x] `en_passant_target`,
  - [x] castling rights.

### 6.2 Rewrite `Board.clone()`

- [x] Create a clone without reusing the original board's state.
- [x] Ensure `cloned.board is cloned._board_state.board`.
- [x] Recreate validators/executors so they point at the cloned `BoardState`.
- [x] Do not leave `cloned._move_validator.board` pointing at the original state.
- [x] Do not leave `cloned._move_executor.board` pointing at the original state.

### 6.3 Add clone tests

- [x] Set up a position with pieces and state:
  - [x] a moved pawn,
  - [x] non-default turn,
  - [x] en passant target,
  - [x] changed castling rights.
- [x] Clone the board.
- [x] Move a piece on the clone.
- [x] Assert original board pieces and piece `_square` values are unchanged.
- [x] Assert clone board pieces changed as expected.
- [x] Assert clone state values were copied correctly.

### 6.4 Use clone for king-safety simulation

- [x] Replace ad-hoc shallow-copy simulation in `MoveValidator._would_expose_king_to_check()` with the canonical clone/simulation path.
- [x] Ensure en passant and castling simulations are handled correctly for king-safety checks.

---

## Task 7: Repair move execution and state transitions

### 7.1 Pick one owner for turn updates

- [x] Decide whether `Board.make_move()` or `MoveExecutor.execute_move()` flips `turn`.
- [x] Ensure the turn flips exactly once for a successful move.
- [x] Ensure the turn does not flip for an illegal move.

### 7.2 Pick one owner for en passant target updates

- [x] Decide whether `Board.make_move()` or `MoveExecutor.execute_move()` updates `en_passant_target`.
- [x] Ensure the old target is cleared after any move that is not a two-square pawn advance.
- [x] Ensure a new target is set after a two-square pawn advance.
- [x] Ensure the target is the passed-over square, not the pawn's destination.

### 7.3 Pick one owner for castling rights updates

- [x] Add a helper such as:

  ```python
  def update_castling_rights_for_move(board_state, moving_piece, from_square, to_square, captured_piece):
      ...
  ```

- [x] Call it exactly once per successful move.

### 7.4 Ensure atomic move execution

- [x] For normal moves:
  - [x] remember destination piece as `captured_piece`,
  - [x] update castling rights,
  - [x] set destination to moving piece,
  - [x] update moving piece `_square`,
  - [x] clear source square.
- [x] For promotion:
  - [x] validate promotion piece before execution,
  - [x] move pawn to destination,
  - [x] replace pawn with promoted piece,
  - [x] set promoted piece `_square`.
- [x] For castling:
  - [x] move king to destination,
  - [x] move rook to correct square,
  - [x] clear original king and rook squares,
  - [x] clear both castling rights for that color.
- [x] For en passant:
  - [x] move capturing pawn to target square,
  - [x] clear source square,
  - [x] clear captured pawn square at `(from_square.row, to_square.col)`.

### 7.5 Remove redundant pin logic

- [x] Review this pattern in `Board.make_move()`:

  ```python
  if start_piece.kind not in (PieceType.KNIGHT, PieceType.KING):
      if self._move_validator.is_piece_pinned(start_pos, start_piece.color):
          return False
  ```

- [x] Remove it if legal validation already simulates the move and rejects self-check.
- [x] Do not reject all pinned-piece moves blindly; a pinned piece may legally move along the pin line in some positions.

---

## Task 8: Repair castling

### 8.1 Validate castling coordinates

- [x] Use canonical castling squares:
  - [x] White: `e1g1`, `e1c1`, rooks `h1f1`, `a1d1`.
  - [x] Black: `e8g8`, `e8c8`, rooks `h8f8`, `a8d8`.

### 8.2 Validate castling rights and pieces

- [x] Require the king to be on the correct starting square.
- [x] Require the rook to be on the correct rook square.
- [x] Require the relevant castling right to be true.
- [x] Reject castling if the destination is occupied.
- [x] Reject castling if any path square between king and rook is occupied.

### 8.3 Validate attacks through castling path

- [x] Reject castling if the king is currently in check.
- [x] Reject kingside castling if `e1`, `f1`, or `g1` is attacked for White.
- [x] Reject queenside castling if `e1`, `d1`, or `c1` is attacked for White.
- [x] Reject kingside castling if `e8`, `f8`, or `g8` is attacked for Black.
- [x] Reject queenside castling if `e8`, `d8`, or `c8` is attacked for Black.

### 8.4 Update castling rights

- [x] Clear both rights when a king moves.
- [x] Clear the side-specific right when a rook moves from its starting square.
- [x] Clear the side-specific right when a rook is captured on its starting square.

### 8.5 Add castling regression tests

- [x] Legal white kingside castling.
- [x] Legal white queenside castling.
- [x] Legal black kingside castling.
- [x] Legal black queenside castling.
- [x] Castling rejected while in check.
- [x] Castling rejected through check.
- [x] Castling rejected into check.
- [x] Castling rejected with blocked path.
- [x] Castling rejected after king moved away and back.
- [x] Castling rejected after relevant rook moved away and back.
- [x] Castling right cleared after rook capture on original square.

---

## Task 9: Repair en passant

### 9.1 Remove wrong two-row diagonal logic

- [x] In `MoveValidator._is_en_passant_move()` and related code, remove any requirement that `row_diff == 2`.
- [x] En passant capture must have:

  ```python
  abs(to_col - from_col) == 1
  to_row - from_row == -1 for White
  to_row - from_row == +1 for Black
  to_square == board.en_passant_target
  ```

### 9.2 Set en passant target correctly

- [x] After White plays `e2e4`, target must be `e3`.
- [x] After Black plays `d7d5`, target must be `d6`.
- [x] The target must be cleared after the opponent makes any move that is not the en passant capture.

### 9.3 Execute en passant correctly

- [x] For White `e5d6` after Black `d7d5`:
  - [x] White pawn lands on `d6`.
  - [x] White pawn source `e5` is empty.
  - [x] Black pawn on `d5` is removed.
- [x] For Black `d4e3` after White `e2e4`:
  - [x] Black pawn lands on `e3`.
  - [x] Black pawn source `d4` is empty.
  - [x] White pawn on `e4` is removed.

### 9.4 Add en passant tests

- [x] White en passant from a constructed position.
- [x] Black en passant from a constructed position.
- [x] Full sequence from starting position where practical.
- [x] En passant expires after one half-move.
- [x] En passant rejected if target square does not match.
- [x] En passant rejected if the adjacent pawn did not just move two squares.
- [x] En passant rejected if it exposes own king to check.

---

## Task 10: Repair promotion

### 10.1 Fix promotion rank logic

- [x] White promotes on row `0` / rank `8`.
- [x] Black promotes on row `7` / rank `1`.
- [x] Remove old logic that says White promotes at row `7` and Black at row `0`.

### 10.2 Validate promotion choices

- [x] Allow only:
  - [x] `PieceType.QUEEN`,
  - [x] `PieceType.ROOK`,
  - [x] `PieceType.BISHOP`,
  - [x] `PieceType.KNIGHT`.
- [x] Reject:
  - [x] `PieceType.KING`,
  - [x] `PieceType.PAWN`,
  - [x] `PieceType.EMPTY`,
  - [x] invalid raw values.

### 10.3 Support default queen promotion

- [x] If a pawn reaches the promotion rank with `promotion=None`, promote to queen unless the CLI/API is deliberately changed to require explicit choices.
- [x] Document whichever behavior is chosen.

### 10.4 Add promotion tests

- [x] White promotes on `e7e8q`.
- [x] White promotes to rook, bishop, and knight.
- [x] Black promotes on `e2e1q`.
- [x] Black promotes to rook, bishop, and knight.
- [x] Illegal promotion piece rejected.
- [x] Pawn cannot promote from the wrong rank.
- [x] Promotion cannot bypass normal pawn movement rules.

---

## Task 11: Fix CLI behavior

### 11.1 Fix game-over calls

- [x] In `chess_game/main.py`, update `_game_over_message()` so it does not call `board.is_checkmate()` or `board.is_stalemate()` incorrectly.
- [x] Either:

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

- [x] `main.py` accepts `--ai`, but `_game_loop()` currently ignores `use_ai` and `ai_depth`.
- [x] Choose one:
  - [x] Wire AI moves into the game loop after human moves, or
  - [x] remove/disable `--ai` and print a clear message that AI mode is not available until after core rules repair.
- [x] Do not leave a no-op AI flag.

### 11.3 Add CLI smoke tests

- [x] Test `parse_move_notation("e2e4")` maps to `e2 -> e4` under the canonical coordinate system.
- [x] Test promotion suffix parsing:
  - [x] `q`,
  - [x] `r`,
  - [x] `b`,
  - [x] `n`.
- [x] Test invalid promotion suffix raises `ValueError`.
- [x] Add a test for `_game_over_message()` if practical.

---

## Task 12: Fix AI safety without expanding scope

### 12.1 Repair AI legal move source

- [x] Inspect `chess_game/chess/ai.py`.
- [x] Ensure AI move generation uses only `board.get_legal_moves()` for the side to move.
- [x] Remove or repair any helper that independently generates pseudo-legal or opponent moves incorrectly.

### 12.2 Repair AI simulation

- [x] Ensure AI simulations use the fixed `Board.clone()`.
- [x] Ensure simulated moves do not mutate the original board.
- [x] Add at least one test where AI considers a move and the original board remains unchanged.

### 12.3 Repair transposition/FEN-like keys

- [x] If `_fen_key()` or equivalent is kept, include:
  - [x] board placement,
  - [x] side to move,
  - [x] castling rights,
  - [x] en passant target.
- [x] Do not call it a valid FEN if it is not full FEN.

### 12.4 Defer AI quality improvements

- [x] Do not tune evaluation tables in this pass unless orientation bugs make them actively wrong.
- [x] Do not add opening books, time controls, or search optimizations.
- [x] Record AI improvement ideas separately after core rules pass.

---

## Task 13: Clean up tests and fixtures

### 13.1 Remove duplicate fixtures

- [x] In `tests/conftest.py`, remove duplicate `simple_opening_position` fixture definitions.
- [x] Ensure helper comments reflect the canonical coordinate system.

### 13.2 Classify and update current failing tests

For each currently failing test, classify it:

- [x] `tests/test_corner.py::test_checkmate_with_promotion`
- [x] `tests/test_corner.py::test_stalemate_after_promotion`
- [x] `tests/test_en_passant.py::test_castling_kingside_with_queenside_rook_only`
- [x] `tests/test_en_passant_edge_cases.py::test_en_passant_capture_removes_pawn_from_original_square`
- [x] `tests/test_en_passant_edge_cases.py::test_full_en_passant_sequence_from_starting_position`
- [x] `tests/test_king_safety.py::test_promotion_from_rank_6_blocked`
- [x] all currently failing `tests/test_piece_moves.py` tests

For each test:

- [x] If the test is conceptually correct, fix the implementation.
- [x] If the test encodes the broken coordinate system, rewrite it using algebraic helpers.
- [x] If the test setup is ambiguous, rewrite it to express the actual chess position clearly.

### 13.3 Add helper assertions

- [x] Add `assert_piece(board, square_name, color, kind)` helper.
- [x] Add `assert_empty(board, square_name)` helper.
- [x] Add `move_tuple_to_names(...)` or equivalent helper to make legal move tests readable.

---

## Task 14: Clean up engine code

### 14.1 Remove debug output

- [x] Remove all engine `print("DEBUG ...")` calls from:
  - [x] `board.py`,
  - [x] `move_validation.py`,
  - [x] `en_passant.py`,
  - [x] any other engine module.

- [x] If diagnostics are still needed, use logging behind a disabled-by-default logger.

### 14.2 Remove duplicate methods

- [x] In `Board`, remove the duplicate `clear_board()` definition.
- [x] Ensure the remaining implementation uses the canonical `get_square_constant(row, col)` or equivalent safely.

### 14.3 Remove stale imports and aliases

- [x] Remove unused imports discovered by static inspection.
- [x] Fix type annotations that refer to undefined `Square` aliases.
- [x] Ensure `mypy.ini` remains coherent if type checking is still intended.

### 14.4 Review debug scripts

- [x] Inspect:
  - [x] `debug_ep.py`,
  - [x] `debug_move.py`,
  - [x] `fix_tests.py`.
- [x] Delete obsolete scripts or move them under `tools/debug/` with clear names.
- [x] Do not leave scripts that encode the old coordinate convention without warning.

---

## Task 15: Fix CI and packaging

### 15.1 Fix GitHub Actions

- [x] Edit `.github/workflows/ci.yml`.
- [x] Remove `pip install -r requirements.txt` unless a real `requirements.txt` is added.
- [x] Use pytest, not unittest:

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

- [x] In `pyproject.toml`, add runtime dependencies if needed:

  ```toml
  dependencies = [
      "pydantic>=2",
  ]
  ```

- [x] Add optional test dependencies if desired:

  ```toml
  [project.optional-dependencies]
  test = ["pytest"]
  ```

- [x] Then CI can use:

  ```bash
  python -m pip install -e '.[test]'
  ```

### 15.3 Run CI-equivalent command locally

- [x] Run:

  ```bash
  python -m pip install -e .
  python -m pytest tests -q
  ```

- [x] Confirm it passes locally before committing.

---

## Task 16: Update documentation

### 16.1 Update coordinate docs

- [x] Update `docs/coordinate_system.md` to match:

  ```text
  row 0 = rank 8
  row 7 = rank 1
  ```

- [x] Include a table:

  ```text
  Algebraic | row | col
  a8        | 0   | 0
  e8        | 0   | 4
  h8        | 0   | 7
  e2        | 6   | 4
  e1        | 7   | 4
  ```

### 16.2 Update en passant docs

- [x] Update `docs/en_passant.md` to explain:
  - [x] passed-over target square,
  - [x] one-row diagonal capture geometry,
  - [x] captured pawn removal square,
  - [x] immediate-half-move expiration.

### 16.3 Update README

- [x] Update `README.md` with:
  - [x] correct coordinate convention,
  - [x] current test command,
  - [x] CLI examples `e2e4`, `e7e5`, `e7e8q`,
  - [x] whether AI mode is currently supported.

### 16.4 Update old planning docs

- [x] Update or annotate:
  - [x] `THE_PLAN.md`,
  - [x] `TODO.md`,
  - [x] `docs/REFACTOR_BOARD_TODO.md`,
  - [x] `docs/REFACTOR_PROGRESS.md`,
  - [x] `docs/EDGE_CASES_TODO.md`.

- [x] Any doc that still mentions the old coordinate mapping must be corrected or marked obsolete.

---

## Task 17: Final acceptance tests

### 17.1 Full test suite

- [x] Run:

  ```bash
  python -m pytest tests -q
  ```

- [x] Required result: zero failures.

### 17.2 Manual smoke script

- [x] Run this script from the repo root:

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

- [x] Start the CLI:

  ```bash
  python -m chess_game.main
  ```

- [x] Enter:

  ```text
  e2e4
  e7e5
  g1f3
  b8c6
  quit
  ```

- [x] Confirm:
  - [x] legal moves are accepted,
  - [x] board display updates correctly,
  - [x] no crash occurs,
  - [x] check/checkmate/stalemate calls do not raise exceptions.

### 17.4 Regression checklist

- [x] `e2e4` works from the starting position.
- [x] `e7e5` works after White moves.
- [x] A rook cannot move diagonally.
- [x] A bishop cannot move straight.
- [x] A queen cannot move like a knight.
- [x] A knight cannot move straight or diagonally.
- [x] A king cannot move two squares except valid castling.
- [x] A pawn cannot move backward.
- [x] A pawn cannot capture forward.
- [x] Sliding pieces cannot move through blockers.
- [x] Legal move generation returns only the side to move.
- [x] Check detection works.
- [x] Checkmate detection works.
- [x] Stalemate detection works.
- [x] Castling works and rights update correctly.
- [x] En passant works for both colors and expires correctly.
- [x] Promotion works for both colors.
- [x] Clone simulation does not mutate original boards.
- [x] CI runs pytest.

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
