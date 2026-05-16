# Chess Engine Repair Fix 3 TODO

## Goal

Fix the remaining confirmed execution-layer chess bugs:

1. Legal moves must never capture/remove the opponent king.
2. Non-pawn moves to the en-passant target must not execute en passant.
3. Non-king moves with castling-shaped coordinates must not execute castling rook movement.

This is a focused correctness patch. Do not broaden scope into AI improvements, GUI work, new features, or a large rewrite unless the minimal safe fix becomes impossible.

## Implementation rules

- Treat `docs/CHESS_ENGINE_REPAIR_FIX3_SPEC.md` as the authoritative contract.
- Keep the canonical coordinate system unchanged:
  - `row 0 = rank 8`
  - `row 7 = rank 1`
  - `e2 = row 6, col 4`
  - `e7 = row 1, col 4`
- Use algebraic test helpers such as `sq("e4")` for chess positions.
- Do not weaken, skip, or delete tests to make the suite pass.
- Do not add debug `print()` statements to engine code.
- Keep the public API stable unless a small internal API change is required for correctness.
- After each task group, run `python -m pytest tests -q`.
- The expected baseline from the latest review was `189 passed`. The final count may be higher after adding tests.

---

## Task 0: Baseline and docs

### 0.1 Confirm the current baseline

- [ ] From the repo root, run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Record the result in your implementation notes.
- [ ] If the result is not approximately `189 passed`, inspect the delta before changing code.
- [ ] Do not proceed by deleting or weakening tests.

### 0.2 Add the Fix 3 docs

- [ ] Copy `CHESS_ENGINE_REPAIR_FIX3_SPEC.md` into:

  ```text
  docs/CHESS_ENGINE_REPAIR_FIX3_SPEC.md
  ```

- [ ] Copy this TODO into:

  ```text
  docs/CHESS_ENGINE_REPAIR_FIX3_TODO.md
  ```

- [ ] Leave prior repair docs in place unless the project already has an accepted archive/obsolete-doc convention.

---

## Task 1: Add failing regression tests first

Add tests before or alongside the fixes. These tests should fail on the reviewed buggy version and pass after implementation.

Recommended files:

```text
tests/test_king_safety.py
tests/test_board_edge_cases.py
tests/test_en_passant_edge_cases.py
tests/test_castling_edge_cases.py
```

Create a new test file if that is cleaner.

### 1.1 Add king-capture regression helpers

- [ ] Use existing helpers where available:
  - [ ] `sq("e4")`
  - [ ] `assert_piece(...)`
  - [ ] `assert_empty(...)`
- [ ] If needed, add a local helper to clear and construct small board positions.
- [ ] Do not use raw row/col constants for chess-square positions unless testing internals.

### 1.2 Add rook-cannot-capture-king test

- [ ] Construct:

  ```text
  White king: e1
  White rook: a1
  Black king: a8
  White to move
  ```

- [ ] Attempt:

  ```text
  a1a8
  ```

- [ ] Assert:
  - [ ] `board.make_move(sq("a1"), sq("a8")) is False`
  - [ ] black king remains on `a8`
  - [ ] white rook remains on `a1`
  - [ ] `board.turn` does not flip

### 1.3 Add queen-cannot-capture-king test

- [ ] Construct a position where a queen has a clear line to the opponent king.
- [ ] Attempt the king-capturing move.
- [ ] Assert the move is rejected and both kings remain.

Suggested position:

```text
White king: e1
White queen: a4
Black king: e8
White to move
Attempt: a4e8
Expected: False
```

### 1.4 Add legal-moves-exclude-king-capture test

- [ ] Construct the rook/king position from Task 1.2.
- [ ] Call `board.get_legal_moves()`.
- [ ] Assert no move has:

  ```text
  from_square == a1
  to_square == a8
  ```

- [ ] If move objects use different field names, adapt the assertion without weakening it.

### 1.5 Add king-adjacency/capture test if not already covered

- [ ] Construct adjacent kings or a king move onto the opponent king.
- [ ] Assert the move is rejected.
- [ ] If existing attack-detection tests already cover this clearly, add only the missing king-capture-specific assertion.

---

## Task 2: Fix king-capture validation

### 2.1 Inspect the current validator path

- [ ] Inspect:

  ```text
  chess_game/chess/board/move_validation.py
  chess_game/chess/board/board.py
  chess_game/chess/board/move_execution.py
  ```

- [ ] Identify where the destination piece is checked.
- [ ] Confirm the current logic rejects friendly-piece captures but does not reject opponent king captures.

### 2.2 Add explicit opponent-king capture rejection

- [ ] In the move validation path, add a guard equivalent to:

  ```python
  dest_piece = self.board.get_piece(to_square)
  if dest_piece is not None and dest_piece.kind == PieceType.KING:
      return False
  ```

- [ ] Put this guard before pseudo-legal destination approval and before simulation/execution.
- [ ] Ensure the guard applies regardless of moving piece type.
- [ ] Ensure the guard applies to both colors.

### 2.3 Ensure `get_legal_moves()` inherits the rejection

- [ ] Confirm `Board.get_legal_moves()` filters candidate moves through the same validator.
- [ ] Confirm king-capturing moves are not returned.
- [ ] Do not add a separate ad-hoc filter in `get_legal_moves()` unless the architecture requires it.

### 2.4 Verify king-capture tests

- [ ] Run king-capture tests only, for example:

  ```bash
  python -m pytest tests/test_king_safety.py tests/test_board_edge_cases.py -q
  ```

- [ ] Then run the full suite:

  ```bash
  python -m pytest tests -q
  ```

---

## Task 3: Add en-passant execution misclassification tests

The bug: a non-pawn move to `board.en_passant_target` can incorrectly execute as en passant and delete a pawn.

### 3.1 Add black knight to white en-passant target test

- [ ] Construct:

  ```text
  White king: e1
  Black king: e8
  White pawn: e2
  Black knight: f5
  White to move
  ```

- [ ] Execute:

  ```text
  White: e2e4
  Black: f5e3
  ```

- [ ] Assert after `e2e4`:
  - [ ] move succeeded
  - [ ] white pawn is on `e4`
  - [ ] `board.en_passant_target == sq("e3")`
  - [ ] `board.turn == Color.BLACK`

- [ ] Assert after `f5e3`:
  - [ ] move succeeded if the position allows the knight move safely
  - [ ] black knight is on `e3`
  - [ ] white pawn is still on `e4`
  - [ ] `f5` is empty
  - [ ] `board.en_passant_target is None`
  - [ ] `board.turn == Color.WHITE`

### 3.2 Add white knight to black en-passant target mirror test

- [ ] Construct:

  ```text
  White king: e1
  Black king: e8
  Black pawn: e7
  White knight: f4
  Black to move
  ```

- [ ] Execute:

  ```text
  Black: e7e5
  White: f4e6
  ```

- [ ] Assert after `e7e5`:
  - [ ] black pawn is on `e5`
  - [ ] `board.en_passant_target == sq("e6")`
  - [ ] `board.turn == Color.WHITE`

- [ ] Assert after `f4e6`:
  - [ ] white knight is on `e6`
  - [ ] black pawn is still on `e5`
  - [ ] `f4` is empty
  - [ ] `board.en_passant_target is None`
  - [ ] `board.turn == Color.BLACK`

### 3.3 Add a legal en-passant still works test

- [ ] Ensure existing legal en-passant tests still pass.
- [ ] If coverage is unclear, add one direct white en-passant test:

  ```text
  White pawn: e5
  Black pawn: d7
  Black plays d7d5
  White plays e5d6
  Expected: white pawn on d6, black pawn removed from d5
  ```

- [ ] Add one direct black en-passant test if not already present.

---

## Task 4: Fix en-passant execution classification

### 4.1 Inspect current execution path

- [ ] Inspect:

  ```text
  chess_game/chess/board/move_execution.py
  chess_game/chess/board/en_passant.py
  chess_game/chess/board/move_validation.py
  ```

- [ ] Find the helper that decides whether the executor should run en-passant capture logic.
- [ ] Confirm whether it currently checks only `to_square == board.en_passant_target` or otherwise uses loose criteria.

### 4.2 Make en-passant detection strict

- [ ] Update the executor's en-passant detection so it returns `True` only if all of these are true:

  ```text
  moving piece kind == PAWN
  board.en_passant_target is not None
  to_square == board.en_passant_target
  abs(to_col - from_col) == 1
  White: to_row - from_row == -1
  Black: to_row - from_row == +1
  captured square == (from_row, to_col)
  captured piece exists
  captured piece kind == PAWN
  captured piece color != moving piece color
  ```

- [ ] Do not allow knights, bishops, rooks, queens, or kings to trigger en-passant execution.
- [ ] Do not remove the pawn behind the en-passant target unless the strict check passes.

### 4.3 Keep validated legal en-passant working

- [ ] Ensure the legal en-passant validation path still accepts valid white and black en-passant moves.
- [ ] Ensure en-passant still expires after one half-move.
- [ ] Ensure en-passant still rejects moves that expose the moving side's king to check.

### 4.4 Run focused and full tests

- [ ] Run:

  ```bash
  python -m pytest tests/test_en_passant.py tests/test_en_passant_edge_cases.py -q
  ```

- [ ] Run:

  ```bash
  python -m pytest tests -q
  ```

---

## Task 5: Add castling execution misclassification tests

The bug: a non-king move with coordinates like castling can incorrectly execute rook movement.

### 5.1 Add white rook e1g1 test

- [ ] Construct:

  ```text
  White king: a1
  White rook: e1
  White rook: h1
  Black king: a8
  White to move
  ```

- [ ] Attempt:

  ```text
  e1g1
  ```

- [ ] Assert:
  - [ ] move succeeds as a normal rook move if legal in the constructed position
  - [ ] rook from `e1` lands on `g1`
  - [ ] `e1` is empty
  - [ ] rook on `h1` remains on `h1`
  - [ ] `f1` remains empty
  - [ ] no castling rights are incorrectly modified beyond normal rook-move rules, if relevant

### 5.2 Add black rook e8g8 mirror test

- [ ] Construct:

  ```text
  Black king: a8
  Black rook: e8
  Black rook: h8
  White king: a1
  Black to move
  ```

- [ ] Attempt:

  ```text
  e8g8
  ```

- [ ] Assert:
  - [ ] rook from `e8` lands on `g8`
  - [ ] rook on `h8` remains on `h8`
  - [ ] `f8` remains empty

### 5.3 Add queenside-shaped rook move tests

- [ ] Add a white `e1c1` rook-move test where legal:
  - [ ] rook from `e1` lands on `c1`
  - [ ] rook on `a1` remains on `a1`
  - [ ] `d1` remains empty unless occupied by the moving rook path is invalid by setup

- [ ] Add a black `e8c8` rook-move test where legal:
  - [ ] rook from `e8` lands on `c8`
  - [ ] rook on `a8` remains on `a8`
  - [ ] `d8` remains empty unless occupied by the moving rook path is invalid by setup

### 5.4 Add non-king non-rook castling-shape safety test if practical

- [ ] Place another non-king piece on a castling start square.
- [ ] Attempt a castling-shaped move if that piece can legally move that way in a constructed position.
- [ ] Assert no rook movement occurs.
- [ ] If no clean legal geometry exists, document that rook tests cover the actual observed bug.

---

## Task 6: Fix castling execution classification

### 6.1 Inspect current castling execution detection

- [ ] Inspect:

  ```text
  chess_game/chess/board/move_execution.py
  chess_game/chess/board/castling.py
  chess_game/chess/board/move_validation.py
  ```

- [ ] Locate the executor helper equivalent to `_is_castling_move(...)`.
- [ ] Confirm whether it ignores the moving piece kind.

### 6.2 Require the moving piece to be a king

- [ ] Update the executor's castling detection so it is equivalent to:

  ```python
  def _is_castling_move(self, piece, from_square, to_square) -> bool:
      return (
          piece.kind == PieceType.KING
          and self.castling_validator.is_castling_move(from_square, to_square)
      )
  ```

- [ ] Ensure this applies to all four castling coordinate pairs:
  - [ ] `e1g1`
  - [ ] `e1c1`
  - [ ] `e8g8`
  - [ ] `e8c8`

### 6.3 Ensure real castling still works

- [ ] Run existing legal castling tests.
- [ ] Ensure real king castling still moves both king and rook correctly.
- [ ] Ensure castling still rejects:
  - [ ] castling while in check,
  - [ ] castling through check,
  - [ ] castling into check,
  - [ ] blocked path,
  - [ ] moved king,
  - [ ] moved rook,
  - [ ] rook captured from original square.

### 6.4 Run focused and full tests

- [ ] Run:

  ```bash
  python -m pytest tests/test_castling.py tests/test_castling_edge_cases.py -q
  ```

- [ ] Run:

  ```bash
  python -m pytest tests -q
  ```

---

## Task 7: Optional move-kind cleanup

Do this only if the minimal strict-predicate fixes become messy or duplicated.

### 7.1 Decide whether a `MoveKind`/`ValidatedMove` helper is needed

- [ ] If strict special-move predicates are simple and clear, skip this task.
- [ ] If validation/execution remains fragile, add a small internal move classification type.

### 7.2 Possible implementation

- [ ] Add a small enum:

  ```python
  class MoveKind(Enum):
      NORMAL = auto()
      CASTLING = auto()
      EN_PASSANT = auto()
      PROMOTION = auto()
  ```

- [ ] Add a small dataclass:

  ```python
  @dataclass(frozen=True)
  class ValidatedMove:
      from_square: ConstantSquare
      to_square: ConstantSquare
      moving_piece: Piece
      kind: MoveKind
      promotion: PieceType | None = None
  ```

- [ ] Make validation classify the move.
- [ ] Make execution use the classified kind instead of re-detecting special moves from loose coordinates.

### 7.3 Keep this cleanup limited

- [ ] Do not rewrite all move generation.
- [ ] Do not change CLI input format.
- [ ] Do not change the public `Board.make_move()` API unless absolutely necessary.
- [ ] Keep all existing tests passing throughout.

---

## Task 8: Code cleanup after fixes

### 8.1 Remove temporary diagnostics

- [ ] Remove any temporary debug `print()` statements.
- [ ] Do not leave commented-out debug blocks.
- [ ] Use logging only if the project already has a disabled-by-default logging pattern.

### 8.2 Review type imports

- [ ] Ensure any new code imports `PieceType`, `Color`, `ConstantSquare`, or helpers from the correct modules.
- [ ] Avoid circular imports.
- [ ] Avoid weakening types to `Any` unless required by existing project style.

### 8.3 Review tests for coordinate clarity

- [ ] Use `sq("e4")` style helpers for all chess-square setup in new tests.
- [ ] Use `assert_piece(...)` and `assert_empty(...)` where available.
- [ ] Do not introduce stale comments like `row 0 = rank 1`.

---

## Task 9: Manual smoke tests

Run a manual script equivalent to the one below from the repo root.

```python
from chess_game.chess.board import Board
from chess_game.chess.coords import algebraic_to_index as sq
from chess_game.chess.types import Color, PieceType
from chess_game.chess.piece import Piece


def clear(board):
    board.clear_board()
    board.en_passant_target = None
    board.white_can_castle_kingside = False
    board.white_can_castle_queenside = False
    board.black_can_castle_kingside = False
    board.black_can_castle_queenside = False


def put(board, name, color, kind):
    square = sq(name)
    piece = Piece(color=color, kind=kind, square=square)
    board.set_piece(square, piece)
    return piece

# 1. King capture rejected
board = Board()
clear(board)
put(board, "e1", Color.WHITE, PieceType.KING)
put(board, "a1", Color.WHITE, PieceType.ROOK)
put(board, "a8", Color.BLACK, PieceType.KING)
board.turn = Color.WHITE
assert board.make_move(sq("a1"), sq("a8")) is False
assert board.get_piece(sq("a8")).kind == PieceType.KING
assert board.get_piece(sq("a1")).kind == PieceType.ROOK
assert board.turn == Color.WHITE

# 2. Knight to en-passant target does not remove pawn
board = Board()
clear(board)
put(board, "e1", Color.WHITE, PieceType.KING)
put(board, "e8", Color.BLACK, PieceType.KING)
put(board, "e2", Color.WHITE, PieceType.PAWN)
put(board, "f5", Color.BLACK, PieceType.KNIGHT)
board.turn = Color.WHITE
assert board.make_move(sq("e2"), sq("e4")) is True
assert board.en_passant_target == sq("e3")
assert board.make_move(sq("f5"), sq("e3")) is True
assert board.get_piece(sq("e4")).kind == PieceType.PAWN
assert board.get_piece(sq("e3")).kind == PieceType.KNIGHT
assert board.en_passant_target is None

# 3. Rook e1g1 does not castle
board = Board()
clear(board)
put(board, "a1", Color.WHITE, PieceType.KING)
put(board, "e1", Color.WHITE, PieceType.ROOK)
put(board, "h1", Color.WHITE, PieceType.ROOK)
put(board, "a8", Color.BLACK, PieceType.KING)
board.turn = Color.WHITE
assert board.make_move(sq("e1"), sq("g1")) is True
assert board.get_piece(sq("g1")).kind == PieceType.ROOK
assert board.get_piece(sq("h1")).kind == PieceType.ROOK
assert board.get_piece(sq("f1")) is None

print("fix3 smoke ok")
```

- [ ] Save the result in implementation notes.
- [ ] If the script fails, fix the engine or the script if it mismatches real project APIs.

---

## Task 10: Final full acceptance

### 10.1 Full test suite

- [ ] Run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Required result:
  - [ ] zero failures,
  - [ ] test count is at least the previous baseline plus the new regression tests.

### 10.2 Regression checklist

- [ ] Rook cannot capture opponent king.
- [ ] Queen cannot capture opponent king.
- [ ] King cannot capture opponent king / kings cannot be adjacent illegally.
- [ ] `Board.get_legal_moves()` does not include king-capturing moves.
- [ ] `Board.make_move()` never removes an opponent king through a legal move.
- [ ] Knight moving to en-passant target does not remove pawn.
- [ ] Non-pawn movement to en-passant target is treated as normal movement if legal.
- [ ] Legal white en-passant still works.
- [ ] Legal black en-passant still works.
- [ ] En-passant target still expires correctly.
- [ ] Rook `e1g1` does not move rook from `h1`.
- [ ] Rook `e8g8` does not move rook from `h8`.
- [ ] Rook `e1c1` does not move rook from `a1`.
- [ ] Rook `e8c8` does not move rook from `a8`.
- [ ] Real white kingside castling still works.
- [ ] Real white queenside castling still works.
- [ ] Real black kingside castling still works.
- [ ] Real black queenside castling still works.
- [ ] All prior coordinate, promotion, check, checkmate, stalemate, clone, and CLI tests still pass.

### 10.3 Commit guidance

Use small commits if practical:

1. `test: add king capture regression coverage`
2. `fix: reject king captures in move validation`
3. `test: cover en passant target misclassification`
4. `fix: require strict en passant execution criteria`
5. `test: cover castling-shaped non-king moves`
6. `fix: require king piece for castling execution`
7. `docs: add fix3 repair notes`

---

## Completion definition

This TODO is complete when:

- all tasks above are checked off,
- all new regression tests pass,
- the full pytest suite passes,
- manual smoke tests pass,
- no existing rule behavior regresses,
- and the implementation obeys the spec principle:

```text
Special move execution must be based on validated move semantics, not loose coordinate coincidence.
```
