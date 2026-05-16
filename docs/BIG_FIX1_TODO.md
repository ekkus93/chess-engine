# BIG_FIX1_TODO.md — Board API Test Batch + 7 Failing Tests Repair Plan

## Purpose

This file consolidates the unchecked work from:

- `API_UNIT_TEST1.md`
- `7FAILING_TESTS_TODO.md`

It also adds explicit implementation guidance based on direct inspection of the current chess engine code.

The immediate goal is **not** to redesign the engine. The goal is to add the missing Board API unit tests, correct bad/stale test assumptions, and fix any real bugs exposed by those tests.

## Current baseline observed from latest repo zip

From the latest reviewed repo:

```bash
python -m pytest tests -q
```

currently reports:

```text
195 passed
```

There is currently **no `tests/test_board_api.py`** in the uploaded repo. The API test work from `API_UNIT_TEST1.md` appears not to have been added yet.

Important current-code facts:

- `Board.is_valid_position(square)` exists in `chess_game/chess/board/board.py`.
- `Board.is_same_color(square1, square2)` exists.
- `Board.is_opponent(square1, square2)` exists.
- `Board.is_empty(square)` exists.
- `Board.find_king(color)` currently scans the board array and returns the square containing the king. It does **not** use `_white_king_pos` or `_black_king_pos` fields in the current code.
- `Board.get_legal_moves_for_color(color)` exists. It temporarily sets `self.turn = color`, calls the normal legal-move generator, and then restores the old turn.
- Promotion move generation is still incomplete in the current inspected code: `MoveValidator._get_promotion_piece()` hardcodes queen promotion, so `get_legal_moves()` emits only queen promotions.
- Some assumptions in `7FAILING_TESTS_TODO.md` are stale or test-design bugs, not engine bugs. Do not blindly implement the stale root-cause text.

## Global implementation rules

- Keep the canonical coordinate convention unchanged:

  ```text
  row 0 = rank 8
  row 7 = rank 1
  e2 = row 6, col 4
  e7 = row 1, col 4
  ```

- Use existing test helpers from `tests/helpers.py`:

  ```python
  sq("e4")
  assert_piece(...)
  assert_empty(...)
  ```

- Do not use raw row/column constants in new tests unless the test is specifically about invalid raw coordinates.
- Do not weaken existing tests.
- Do not add new AI features, GUI work, UCI support, or a broad move-classification refactor.
- If a failing API test has a bad chess position, fix the test setup rather than bending the engine to match an invalid expectation.
- After each major task group, run:

  ```bash
  python -m pytest tests -q
  ```

---

# Task 0: Establish baseline and add this handoff

## 0.1 Run the current test suite

- [x] From the repo root, run:

  ```bash
  python -m pytest tests -q
  ```

- [x] Expected current baseline from the latest reviewed zip:

  ```text
  195 passed
  ```

- [x] If there are failures before starting this work, stop and inspect those failures first. Do not mix existing failures with BIG_FIX1 changes.

## 0.2 Create a focused branch

- [x] Create a dedicated branch, for example:

  ```bash
  git checkout -b fix/board-api-tests-and-remaining-rule-regressions
  ```

## 0.3 Add this TODO to the repo

- [x] Copy this file into:

  ```text
  docs/BIG_FIX1_TODO.md
  ```

---

# Task 1: Create `tests/test_board_api.py`

## 1.1 Create the test file

- [x] Add:

  ```text
  tests/test_board_api.py
  ```

- [x] Use pytest functional tests unless surrounding repo style changes.
- [x] Import existing helpers:

  ```python
  from tests.helpers import sq, assert_piece, assert_empty
  ```

- [x] Import core engine types as needed:

  ```python
  from chess_game.chess.board import Board, create_piece
  from chess_game.chess.types import Color, PieceType
  from chess_game.chess.constants import ConstantSquare, RowConstant, ColConstant
  ```

## 1.2 Add small local helpers only if useful

- [x] Add a local move string helper if needed:

  ```python
  from chess_game.chess.coords import index_to_algebraic

  def move_to_str(move):
      start, end, promotion = move
      suffix = "" if promotion is None else promotion.name[0].lower()
      return index_to_algebraic(start) + index_to_algebraic(end) + suffix
  ```

- [x] Add a local helper for extracting promotions if needed:

  ```python
  def promotions_for(board: Board, start: str, end: str) -> set[PieceType | None]:
      return {
          promotion
          for move_start, move_end, promotion in board.get_legal_moves_for_color(board.turn)
          if move_start == sq(start) and move_end == sq(end)
      }
  ```

- [x] Adjust helper signatures to match actual test needs. Do not duplicate helpers that already exist globally.

---

# Task 2: Add API tests for `Board.is_valid_position`

Source: unchecked `API_UNIT_TEST1.md` section 1.

## Problem

`is_valid_position(square)` should return `True` only when `0 <= row < 8` and `0 <= col < 8`.

The tricky part: `get_row_constant(-1)` and `get_col_constant(-1)` intentionally raise `ValueError`, so tests for invalid squares must construct invalid constants directly with `RowConstant(-1)` / `ColConstant(8)`.

## Subtasks

- [x] Test valid corner squares return `True`:
  - [x] `a1`
  - [x] `a8`
  - [x] `h1`
  - [x] `h8`

  Example:

  ```python
  def test_is_valid_position_corners():
      board = Board()
      for name in ["a1", "a8", "h1", "h8"]:
          assert board.is_valid_position(sq(name)) is True
  ```

- [x] Test valid center squares return `True`:
  - [x] `e4`
  - [x] `d5`

- [x] Test out-of-bounds column index returns `False`:
  - [x] column `< 0`
  - [x] column `>= 8`

  Example:

  ```python
  bad_left = ConstantSquare(row=RowConstant(0), col=ColConstant(-1))
  bad_right = ConstantSquare(row=RowConstant(0), col=ColConstant(8))
  assert board.is_valid_position(bad_left) is False
  assert board.is_valid_position(bad_right) is False
  ```

- [x] Test out-of-bounds row index returns `False`:
  - [x] row `< 0`
  - [x] row `>= 8`

- [x] Test negative row and column together return `False`:

  ```python
  bad = ConstantSquare(row=RowConstant(-1), col=ColConstant(-1))
  assert board.is_valid_position(bad) is False
  ```

## Expected code change

- [x] Usually no engine change should be required. Current implementation already checks integer bounds.

---

# Task 3: Add API tests for `Board.is_same_color`

Source: unchecked `API_UNIT_TEST1.md` section 2.

## Problem

`is_same_color(square1, square2)` should return `True` only when both squares are occupied and both pieces have the same color.

## Subtasks

- [ ] Test two white pieces on different squares return `True`.

  Example default board squares:

  ```python
  assert Board().is_same_color(sq("a1"), sq("e1")) is True
  ```

- [ ] Test two black pieces on different squares return `True`.

  Example:

  ```python
  assert Board().is_same_color(sq("a8"), sq("e8")) is True
  ```

- [ ] Test one white and one black piece return `False`.

  Example:

  ```python
  assert Board().is_same_color(sq("a1"), sq("a8")) is False
  ```

- [ ] Test same occupied square returns `True`.

  Example:

  ```python
  assert Board().is_same_color(sq("e1"), sq("e1")) is True
  ```

- [ ] Test one occupied and one empty square returns `False`.

  Use an actually empty default-board square such as `e4`, not `e2` or `e7`.

- [ ] Test both squares empty return `False`.

  Example:

  ```python
  assert Board().is_same_color(sq("e4"), sq("d4")) is False
  ```

## Expected code change

- [ ] Usually no engine change should be required. Current implementation already returns false when either piece is missing.

---

# Task 4: Add API tests for `Board.is_opponent`

Source: unchecked `API_UNIT_TEST1.md` section 3.

## Problem

`is_opponent(square1, square2)` should return `True` only when both squares are occupied and the pieces have opposite colors.

## Subtasks

- [ ] Test white vs black piece returns `True`.
- [ ] Test black vs white piece returns `True`.
- [ ] Test two white pieces return `False`.
- [ ] Test two black pieces return `False`.
- [ ] Test one occupied and one empty square returns `False`.
- [ ] Test both squares empty return `False`.
- [ ] Test same square returns `False`.

## Explicit test positions

Use the default board for most tests:

```python
board = Board()
assert board.is_opponent(sq("a1"), sq("a8")) is True
assert board.is_opponent(sq("a8"), sq("a1")) is True
assert board.is_opponent(sq("a1"), sq("e1")) is False
assert board.is_opponent(sq("a8"), sq("e8")) is False
assert board.is_opponent(sq("a1"), sq("e4")) is False
assert board.is_opponent(sq("e4"), sq("d4")) is False
assert board.is_opponent(sq("a1"), sq("a1")) is False
```

## Expected code change

- [ ] Usually no engine change should be required.

---

# Task 5: Add API tests for `Board.is_empty`

Source: unchecked `API_UNIT_TEST1.md` section 4.

## Important correction to source TODO

`API_UNIT_TEST1.md` says to test default board empty squares such as `e2` and `e7`. That is wrong.

On a correct starting board:

- `e2` has a white pawn.
- `e7` has a black pawn.
- empty representative squares are `e3`, `e4`, `e5`, and `e6`.

Do **not** write a test expecting `e2` or `e7` to be empty.

## Subtasks

- [x] Test default-board empty squares return `True`:
  - [x] `e3`
  - [x] `e4`
  - [x] `e5`
  - [x] `e6`

- [x] Test occupied squares return `False`:
  - [x] `e1` has white king.
  - [x] `e8` has black king.
  - [x] `e2` has white pawn.
  - [x] `e7` has black pawn.

- [x] Test square after `clear_square` returns `True`:

  ```python
  board = Board()
  board.clear_square(sq("e2"))
  assert board.is_empty(sq("e2")) is True
  ```

- [x] Test square after `set_piece` returns `False`:

  ```python
  board = Board()
  board.clear_square(sq("e4"))
  board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.KNIGHT))
  assert board.is_empty(sq("e4")) is False
  ```

- [x] Test occupied corner squares on default board return `False`:
  - [x] `a1`
  - [x] `h1`
  - [x] `a8`
  - [x] `h8`

## Expected code change

- [ ] Usually no engine change should be required.

---

# Task 6: Add API tests for `Board.find_king`

Sources:

- unchecked `API_UNIT_TEST1.md` section 5
- `7FAILING_TESTS_TODO.md` failing tests #1 and #2

## Important correction to `7FAILING_TESTS_TODO.md`

The failing-tests TODO says the root cause is stale `_white_king_pos` / `_black_king_pos` tracking. That is not accurate for the current inspected repo.

Current `Board.find_king(color)` scans the board array directly. There are no `_white_king_pos` or `_black_king_pos` fields in the current `board.py`.

Do **not** add new king-tracking fields unless your working branch already has them. A board scan is simple, reliable, and avoids stale cache bugs.

## Subtasks

- [x] Test default board white king found at `e1`.
- [x] Test default board black king found at `e8`.

  Example:

  ```python
  board = Board()
  assert board.find_king(Color.WHITE) == sq("e1")
  assert board.find_king(Color.BLACK) == sq("e8")
  ```

- [x] Test after a legal king move, the new square is returned.

  Important: `e1 -> f1` is illegal on the default board because `f1` starts occupied by a white bishop. Clear `f1` first or construct an empty board.

  Example:

  ```python
  board = Board()
  board.clear_square(sq("f1"))
  assert board.make_move(sq("e1"), sq("f1")) is True
  assert board.find_king(Color.WHITE) == sq("f1")
  ```

- [x] Test after king removed from board, `find_king(color)` returns `None`.

  Do not use a normal legal move to “capture” a king. King capture is illegal. For this API edge case, directly clear the king square:

  ```python
  board = Board()
  board.clear_square(sq("e1"))
  assert board.find_king(Color.WHITE) is None
  ```

- [x] Test both colors independently return correct squares after custom placement.

  Example:

  ```python
  board = Board()
  board.clear_board()
  board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
  board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
  assert board.find_king(Color.WHITE) == sq("a1")
  assert board.find_king(Color.BLACK) == sq("h8")
  ```

- [x] Test cloned board preserves king positions after king movement.

  Example:

  ```python
  board = Board()
  board.clear_square(sq("f1"))
  assert board.make_move(sq("e1"), sq("f1")) is True
  cloned = board.clone()
  assert cloned.find_king(Color.WHITE) == sq("f1")
  assert cloned.find_king(Color.BLACK) == sq("e8")
  ```

## Expected code change

- [ ] If current `find_king()` scans the board, this should require no code change.
- [ ] If your branch introduced `_white_king_pos` / `_black_king_pos`, either remove that cache and scan the board, or update it in every board mutation path:
  - [ ] normal king move,
  - [ ] castling,
  - [ ] `set_piece`,
  - [ ] `clear_square`,
  - [ ] `clone`.
- [ ] Preferred implementation: keep `find_king()` as a board scan unless profiling proves it is a bottleneck.

---

# Task 7: Add API tests for `Board.get_legal_moves_for_color`

Sources:

- unchecked `API_UNIT_TEST1.md` section 6
- several failing tests from `7FAILING_TESTS_TODO.md`

## Problem

`get_legal_moves_for_color(color)` should return legal moves for the requested color, independent of whose turn it currently is, and it must not permanently mutate `board.turn`.

Current implementation temporarily changes `self.turn`, calls the normal legal-move generator, and restores the old turn. That design is acceptable, but it should be guarded with `try/finally` so an exception cannot leave the board with the wrong turn.

## Required code hardening

- [x] In `Board.get_legal_moves_for_color`, replace this pattern:

  ```python
  saved_turn = self.turn
  self.turn = color
  moves = self._validators.move_validator.get_legal_moves()
  self.turn = saved_turn
  return moves
  ```

  with this safer version:

  ```python
  saved_turn = self.turn
  try:
      self.turn = color
      return self._validators.move_validator.get_legal_moves()
  finally:
      self.turn = saved_turn
  ```

- [x] Add a test that `board.turn` is unchanged after calling `get_legal_moves_for_color`.

## General API subtasks

- [x] Test default board white has 20 legal moves.
- [x] Test default board black has 20 legal moves.
- [x] Test calling `get_legal_moves_for_color(Color.BLACK)` while `board.turn == Color.WHITE` returns Black moves and does not change `board.turn`.
- [x] Test after a move, requested color is respected regardless of current turn.

  Example:

  ```python
  board = Board()
  assert board.make_move(sq("e2"), sq("e4")) is True
  assert board.turn == Color.BLACK
  white_moves = board.get_legal_moves_for_color(Color.WHITE)
  black_moves = board.get_legal_moves_for_color(Color.BLACK)
  assert any(m[0] == sq("g1") and m[1] == sq("f3") for m in white_moves)
  assert any(m[0] == sq("e7") and m[1] == sq("e5") for m in black_moves)
  assert board.turn == Color.BLACK
  ```

- [ ] Test pinned pieces do not produce illegal moves. See Task 8 for exact test design.
- [ ] Test castling moves appear when conditions are met. See Task 9.
- [ ] Test en passant move appears when available. See Task 10.
- [ ] Test promotion moves appear when pawn reaches promotion rank. See Task 11.
- [ ] Test checkmate position returns empty list for side in checkmate. See Task 12.
- [ ] Test stalemate position returns empty list for side in stalemate.

---

# Task 8: Correctly test pinned pieces in `get_legal_moves_for_color`

Source: `7FAILING_TESTS_TODO.md` failing test #3.

## Important correction to source TODO

Do not write a generic test that says “a pinned piece has zero legal moves.” That is false in chess.

A pinned sliding piece or pawn may sometimes legally move along the pin line while still shielding the king. Example: a pawn on `e2` pinned by a rook on `e8` to a king on `e1` can often move `e2e3` or `e2e4` and remain on the same file, still blocking the rook.

The correct test is either:

1. Use a pinned knight, because a knight cannot move along the pin line and all its moves expose the king; or
2. Test that a pinned piece only has moves that do not expose the king.

## Required test: pinned knight has no legal moves

- [ ] Construct this position:

  ```text
  White king: e1
  White knight: e2
  Black rook: e8
  Black king: a8
  White to move
  ```

- [ ] Assert the knight on `e2` has zero legal moves:

  ```python
  board = Board()
  board.clear_board()
  board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
  board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.KNIGHT))
  board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.ROOK))
  board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.KING))
  board.turn = Color.WHITE

  knight_moves = [m for m in board.get_legal_moves_for_color(Color.WHITE) if m[0] == sq("e2")]
  assert knight_moves == []
  ```

## Optional test: pinned pawn can still move along pin line

- [ ] Construct this position:

  ```text
  White king: e1
  White pawn: e2
  Black rook: e8
  Black king: a8
  White to move
  ```

- [ ] Assert `e2e3` and/or `e2e4` may be legal if they continue blocking the rook.
- [ ] Assert diagonal pawn captures that leave the `e` file open are rejected.

## Expected code change

- [ ] Do not reintroduce old blanket pin rejection logic.
- [ ] Correct approach: every generated move must be simulated and rejected if it leaves the moving side's king in check.
- [ ] Current `MoveValidator.is_valid_move()` already calls `_would_expose_king_to_check(...)`; if the pinned-knight test fails, inspect that simulation path.

---

# Task 9: Ensure castling moves appear in `get_legal_moves_for_color`

Source: `7FAILING_TESTS_TODO.md` failing test #4.

## Important correction to source TODO

A fresh board after only `e2e4` does **not** allow White to castle. White kingside castling is still blocked by:

- bishop on `f1`,
- knight on `g1`.

White queenside castling is still blocked by:

- queen on `d1`,
- bishop on `c1`,
- knight on `b1`.

Do not write a test expecting castling after only `e2e4`.

## Subtasks: White kingside castling appears

- [ ] Construct a legal position where White castling rights still exist and `f1`/`g1` are empty.

  Fast direct setup:

  ```python
  board = Board()
  board.clear_square(sq("f1"))
  board.clear_square(sq("g1"))
  board.turn = Color.WHITE
  ```

- [ ] Assert `e1g1` appears in `board.get_legal_moves_for_color(Color.WHITE)`.

## Subtasks: White queenside castling appears

- [ ] Construct a legal position where White castling rights still exist and `b1`/`c1`/`d1` are empty.

  ```python
  board = Board()
  board.clear_square(sq("b1"))
  board.clear_square(sq("c1"))
  board.clear_square(sq("d1"))
  board.turn = Color.WHITE
  ```

- [ ] Assert `e1c1` appears in `board.get_legal_moves_for_color(Color.WHITE)`.

## Subtasks: Black castling appears

- [ ] Add equivalent tests for Black if desired:
  - [ ] `e8g8` with `f8`/`g8` empty.
  - [ ] `e8c8` with `b8`/`c8`/`d8` empty.

## Expected code change

- [ ] In the current inspected code, castling move generation is handled by `MoveValidator._get_castling_moves()` and appended for kings. This should work if the test setup is legal.
- [ ] If the test fails, inspect:
  - [ ] `MoveValidator._get_legal_moves_for_piece()` includes castling destinations for kings.
  - [ ] `CastlingValidator.can_castle_kingside(...)` / `can_castle_queenside(...)` path checks.
  - [ ] Current castling rights are still true.

---

# Task 10: Ensure en passant moves appear in `get_legal_moves_for_color`

Source: `7FAILING_TESTS_TODO.md` failing test #5.

## Important correction to source TODO

The source TODO says “After a double pawn push, e.g. `b2-b4`, the en passant capture `axb3` or `cxb3` does not appear in `get_legal_moves_for_color(White)`.” That is color-confused.

If **White** plays `b2-b4`, then **Black** may capture en passant from `a4` to `b3` or from `c4` to `b3`.

If **Black** plays `b7-b5`, then **White** may capture en passant from `a5` to `b6` or from `c5` to `b6`.

## Required white en passant generation test

- [ ] Construct this position:

  ```text
  White king: e1
  Black king: e8
  White pawn: a5
  Black pawn: b7
  Black to move
  ```

- [ ] Execute Black's double push:

  ```python
  assert board.make_move(sq("b7"), sq("b5")) is True
  assert board.en_passant_target == sq("b6")
  ```

- [ ] Assert White legal moves include `a5b6`:

  ```python
  white_moves = board.get_legal_moves_for_color(Color.WHITE)
  assert any(m[0] == sq("a5") and m[1] == sq("b6") for m in white_moves)
  ```

## Required black en passant generation test

- [ ] Construct this position:

  ```text
  White king: e1
  Black king: e8
  White pawn: b2
  Black pawn: a4
  White to move
  ```

- [ ] Execute White's double push:

  ```python
  assert board.make_move(sq("b2"), sq("b4")) is True
  assert board.en_passant_target == sq("b3")
  ```

- [ ] Assert Black legal moves include `a4b3`:

  ```python
  black_moves = board.get_legal_moves_for_color(Color.BLACK)
  assert any(m[0] == sq("a4") and m[1] == sq("b3") for m in black_moves)
  ```

## Expected code change

- [ ] Current `PieceMovers._get_en_passant_moves(...)` should already append the en-passant target if:
  - [ ] `board.en_passant_target` is set,
  - [ ] target row equals the pawn's next row,
  - [ ] target file is one file away.
- [ ] If tests fail, inspect:
  - [ ] `EnPassantValidator.set_en_passant_target_if_valid(...)`,
  - [ ] `PieceMovers._get_en_passant_moves(...)`,
  - [ ] `MoveValidator._is_en_passant_move(...)`,
  - [ ] `EnPassantValidator.validate_en_passant_capture(...)`.

---

# Task 11: Fix and test promotion move generation

Sources:

- unchecked `API_UNIT_TEST1.md` section 6 promotion bullet
- `7FAILING_TESTS_TODO.md` failing test #6
- current code inspection

## Problem

The current inspected code emits only queen promotions from legal move generation.

Known suspicious current pattern in `chess_game/chess/board/move_validation.py`:

```python
if piece.color == Color.WHITE and int(to_square.row) == 0:
    return PieceType.QUEEN
if piece.color == Color.BLACK and int(to_square.row) == 7:
    return PieceType.QUEEN
```

That means a pawn on `e7` moving to `e8` appears only as `e7e8q`, but a complete chess engine must generate:

```text
e7e8q
e7e8r
e7e8b
e7e8n
```

## Required code changes

### 11.1 Add/reuse canonical promotion piece list

- [ ] In `chess_game/chess/board/promotion.py`, define or reuse one canonical list/tuple:

  ```python
  PROMOTION_PIECES = (
      PieceType.QUEEN,
      PieceType.ROOK,
      PieceType.BISHOP,
      PieceType.KNIGHT,
  )
  ```

- [ ] Use it in:
  - [ ] `get_promotion_options`,
  - [ ] `is_valid_promotion_piece`,
  - [ ] `is_valid_promotion_choice`,
  - [ ] move generation.

### 11.2 Harden promotion validation

Even though this task comes from Board API work, fix the known promotion API bugs at the same time.

- [ ] If `promotion is not None`, require `isinstance(promotion, PieceType)`.
- [ ] Reject raw integers such as `promotion=5`.
- [ ] Reject strings such as `promotion="q"`.
- [ ] Reject invalid `PieceType` values:
  - [ ] `PieceType.KING`,
  - [ ] `PieceType.PAWN`,
  - [ ] `PieceType.EMPTY`.
- [ ] Reject promotion suffixes on non-pawn moves.
- [ ] Reject promotion suffixes on pawn moves that do not end on promotion rank.
- [ ] Preserve default queen promotion when `promotion is None` and a pawn legally reaches the promotion rank.

### 11.3 Generate all legal promotion choices

- [ ] In `MoveValidator._get_legal_moves_for_piece(...)`, replace the single-promotion append logic with expansion.

Current shape is roughly:

```python
for to_square in valid_moves:
    if self.is_valid_move(from_square, to_square):
        promotion = None
        if piece.kind == PieceType.PAWN:
            promotion = self._get_promotion_piece(piece, to_square)
        moves.append((from_square, to_square, promotion))
```

Replace with logic equivalent to:

```python
for to_square in valid_moves:
    if not self.is_valid_move(from_square, to_square):
        continue

    if self.board._validators.promotion_validator.is_promotion_rank(piece, to_square):
        for promotion in PROMOTION_PIECES:
            moves.append((from_square, to_square, promotion))
    else:
        moves.append((from_square, to_square, None))
```

Do not literally reach through private attributes if you can structure it cleaner. Better options:

- import/use `PROMOTION_PIECES` and a local `_is_promotion_rank(...)` helper, or
- add a public helper on `PromotionValidator` and use it cleanly.

### 11.4 Update AI move identity to include promotion

The current inspected `ai.py` still matches ordered moves back to legal moves using only start/end:

```python
move = next(
    m
    for m in legal_moves
    if m.start == move_key.start and m.end == move_key.end
)
```

Once underpromotions are generated, start/end no longer uniquely identifies a move.

- [ ] Add `promotion: Optional[PieceType]` to `MoveOrderingKey`.
- [ ] When creating `MoveOrderingKey`, include `move.promotion`.
- [ ] When mapping ordered keys back to legal moves, match:

  ```python
  m.start == move_key.start
  and m.end == move_key.end
  and m.promotion == move_key.promotion
  ```

- [ ] Add an AI/unit test proving ordered promotion moves preserve distinct promotion values.

## Required promotion tests in `tests/test_board_api.py` or `tests/test_promotion_move_generation.py`

- [ ] White quiet promotion generation:
  - [ ] White king present.
  - [ ] Black king present.
  - [ ] White pawn on `e7`.
  - [ ] `e8` empty.
  - [ ] White to move.
  - [ ] Legal moves for `e7 -> e8` include exactly queen, rook, bishop, knight.

- [ ] White capture promotion generation:
  - [ ] White pawn on `e7`.
  - [ ] Black piece on `d8` or `f8`.
  - [ ] Legal capture promotion includes exactly queen, rook, bishop, knight.

- [ ] Black quiet promotion generation:
  - [ ] Black pawn on `e2`.
  - [ ] `e1` empty.
  - [ ] Black to move.
  - [ ] Legal moves for `e2 -> e1` include exactly queen, rook, bishop, knight.

- [ ] Black capture promotion generation:
  - [ ] Black pawn on `e2`.
  - [ ] White piece on `d1` or `f1`.
  - [ ] Legal capture promotion includes exactly queen, rook, bishop, knight.

- [ ] No duplicate identical promotion moves.

- [ ] Invalid promotion API tests:
  - [ ] `g1f3q` rejected, no board mutation, no turn flip.
  - [ ] `e2e4q` rejected, no board mutation, no turn flip.
  - [ ] `promotion=5` rejected.
  - [ ] `promotion="q"` rejected.
  - [ ] `promotion=PieceType.KING` rejected.
  - [ ] `promotion=PieceType.PAWN` rejected.
  - [ ] `promotion=PieceType.EMPTY` rejected.
  - [ ] valid rook/bishop/knight/queen underpromotion still accepted.

---

# Task 12: Add checkmate and stalemate tests for `get_legal_moves_for_color`

Sources:

- unchecked `API_UNIT_TEST1.md` section 6
- `7FAILING_TESTS_TODO.md` failing test #7

## Important correction to source TODO

If a checkmate test returns two king moves such as `d8` and `f8`, first verify the test position. The test setup may simply not be checkmate.

Do not “fix” legal move filtering to make a non-checkmate position have zero moves.

## Required checkmate test

Use a known small checkmate that the current engine recognizes:

```text
Black king: h8
White king: f6
White queen: g7
Black to move
```

- [ ] Construct the board:

  ```python
  board = Board()
  board.clear_board()
  board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
  board.set_piece(sq("f6"), create_piece(Color.WHITE, PieceType.KING))
  board.set_piece(sq("g7"), create_piece(Color.WHITE, PieceType.QUEEN))
  board.turn = Color.BLACK
  ```

- [ ] Assert:

  ```python
  assert board._is_in_check(Color.BLACK) is True
  assert board.get_legal_moves_for_color(Color.BLACK) == []
  assert board._is_checkmate(Color.BLACK) is True
  ```

## Required stalemate test

Use a known small stalemate:

```text
Black king: h8
White king: f7
White queen: g6
Black to move
```

- [ ] Construct the board.
- [ ] Assert:

  ```python
  assert board._is_in_check(Color.BLACK) is False
  assert board.get_legal_moves_for_color(Color.BLACK) == []
  assert board._is_stalemate(Color.BLACK) is True
  ```

## Expected code change

- [ ] If these positions fail, inspect king-safety simulation and attack detection.
- [ ] If only a custom test position fails, fix the test position first.

---

# Task 13: Preserve Board API mutation safety

## Problem

Several API tests should verify that read-only queries do not mutate the board.

## Subtasks

- [ ] Test `get_legal_moves_for_color(Color.BLACK)` does not change `board.turn`.
- [ ] Test invalid moves used in promotion validation do not mutate:
  - [ ] source piece remains on source square,
  - [ ] destination remains unchanged,
  - [ ] turn does not change,
  - [ ] en passant target does not unexpectedly change,
  - [ ] castling rights do not unexpectedly change.

## Expected code change

- [ ] Add `try/finally` to `get_legal_moves_for_color` as described in Task 7.
- [ ] Ensure `Board.make_move(...)` performs all validation before calling `MoveExecutor.execute_move(...)`.

---

# Task 14: Run focused and full verification

## 14.1 Run the new API test file

- [ ] Run:

  ```bash
  python -m pytest tests/test_board_api.py -q
  ```

- [ ] All tests in `tests/test_board_api.py` must pass.

## 14.2 Run promotion tests

- [ ] Run existing and new promotion-focused tests:

  ```bash
  python -m pytest tests/test_promotion.py tests/test_board_api.py -q
  ```

- [ ] If you add `tests/test_promotion_move_generation.py`, include it:

  ```bash
  python -m pytest tests/test_promotion.py tests/test_promotion_move_generation.py tests/test_board_api.py -q
  ```

## 14.3 Run full suite

- [ ] Run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Expected result: all tests pass.
- [ ] The count should be greater than the previous `195 passed` baseline after new tests are added.

## 14.4 Optional lint

- [ ] If the project currently uses pylint in the workflow, run:

  ```bash
  pylint chess_game/
  ```

- [ ] Do not chase unrelated lint refactors unless required by CI.

---

# Task 15: Suggested implementation order

Use this order. It avoids chasing stale failures from bad test setups.

1. [ ] Add `tests/test_board_api.py` with API tests for:
   - [ ] `is_valid_position`,
   - [ ] `is_same_color`,
   - [ ] `is_opponent`,
   - [ ] `is_empty`,
   - [ ] `find_king`.

2. [ ] Harden `get_legal_moves_for_color` with `try/finally` and add mutation-safety tests.

3. [ ] Add correct pinned-knight, castling, en-passant, checkmate, and stalemate tests.

4. [ ] Fix promotion move generation and validation:
   - [ ] all four promotion choices in legal move generation,
   - [ ] invalid promotion values rejected,
   - [ ] non-pawn promotion suffix rejected,
   - [ ] AI move ordering includes promotion identity.

5. [ ] Run focused tests.

6. [ ] Run full suite.

---

# Task 16: Do not implement these stale/wrong ideas

These were present or implied in the source TODOs but are not correct for the current codebase.

- [ ] Do **not** expect `e2` or `e7` to be empty on the default board.
- [ ] Do **not** expect White to be able to castle after only `e2e4`.
- [ ] Do **not** write an en-passant test where White captures after White's own `b2b4` double push.
- [ ] Do **not** assume every pinned piece has zero legal moves.
- [ ] Do **not** add `_white_king_pos` / `_black_king_pos` tracking just because the old failing-tests TODO mentions it. The current implementation scans the board and that is acceptable.
- [ ] Do **not** allow raw integer promotion values just because `PieceType` is an `IntEnum`.
- [ ] Do **not** match AI moves only by `(start, end)` once promotion alternatives are generated.

---

# Acceptance checklist

The patch is complete only when all of these are true:

- [ ] `tests/test_board_api.py` exists.
- [ ] API tests cover all six methods listed in `API_UNIT_TEST1.md`:
  - [ ] `is_valid_position`,
  - [ ] `is_same_color`,
  - [ ] `is_opponent`,
  - [ ] `is_empty`,
  - [ ] `find_king`,
  - [ ] `get_legal_moves_for_color`.
- [ ] The stale assumptions from `7FAILING_TESTS_TODO.md` are corrected in the actual tests.
- [ ] Pinned-piece test uses a position where the expected result is actually correct.
- [ ] Castling test uses a position where path squares are actually clear.
- [ ] En-passant test uses the correct side after the opponent's double push.
- [ ] Promotion legal move generation emits queen, rook, bishop, and knight for both colors, quiet and capture promotions.
- [ ] Invalid promotion inputs are rejected without mutation.
- [ ] AI move ordering/search preserves promotion identity.
- [ ] `get_legal_moves_for_color` restores `board.turn` even if an exception occurs.
- [ ] Full suite passes:

  ```bash
  python -m pytest tests -q
  ```

