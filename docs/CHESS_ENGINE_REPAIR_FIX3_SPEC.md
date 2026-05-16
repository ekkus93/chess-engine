# Chess Engine Repair Fix 3 Spec

## Purpose

This document defines the required behavior for the third focused repair pass on the chess engine.

The engine is much healthier than the original version, but the latest review found three remaining rule/execution bugs that can corrupt the board state even though the full pytest suite currently passes:

1. A legal move can capture and remove the opponent king.
2. A non-pawn move to the current en-passant target square can incorrectly execute as en passant and remove a pawn.
3. A non-king move whose coordinates look like castling can incorrectly execute castling rook movement.

This repair pass must fix those bugs, add regression tests, and prevent the execution layer from loosely re-detecting special moves from coordinates alone.

## Scope

### In scope

- Fix king-capture validation.
- Fix en-passant execution classification.
- Fix castling execution classification.
- Add regression tests for the confirmed bugs.
- Add small internal helpers or a small move-classification object if needed.
- Run the full pytest suite and keep all existing tests passing.

### Out of scope

- No GUI work.
- No new AI features.
- No opening books.
- No search-depth tuning.
- No evaluation-table tuning unless a test reveals a direct correctness bug.
- No broad engine rewrite.
- No change to the public CLI unless required by these bug fixes.
- No weakening or deleting tests to make the suite pass.

## Current Known Good State

The latest reviewed version had this test result:

```bash
python -m pytest tests -q
```

```text
189 passed in 2.63s
```

The following previously reported issues were fixed in that version:

- `e2e4` works with the canonical coordinate system.
- Queenside castling rejects occupied `b1`/`b8`.
- Illegal long-diagonal en passant such as `e3d6` is rejected.
- `PieceMovers._get_king_moves()` no longer owns castling generation.
- Starting-position evaluation returned `0` in the reviewed build.

Do not regress any of these.

## Canonical Invariants

These invariants must remain true after this repair pass.

### Coordinate system

The engine uses this canonical internal board mapping:

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

Examples:

```text
e2 = row 6, col 4
e4 = row 4, col 4
e7 = row 1, col 4
e5 = row 3, col 4
e1 = row 7, col 4
e8 = row 0, col 4
```

### King invariant

A valid board may temporarily omit a king in isolated unit tests if the engine deliberately supports kingless test boards, but a legal move must never capture a king.

Required behavior:

- A move whose destination contains an opponent king is illegal.
- `Board.make_move(...)` must return `False` for king-capturing attempts.
- `Board.get_legal_moves(...)` must not include moves whose destination contains the opponent king.
- Move execution must never remove either king from the board as the result of a legal move.
- Checkmate and stalemate must be represented through check/legal-move state, not by king capture.

### En-passant invariant

Only a pawn may execute en passant.

A valid en-passant execution requires all of the following:

```text
moving piece kind == PAWN
destination == board.en_passant_target
abs(to_col - from_col) == 1
White: to_row - from_row == -1
Black: to_row - from_row == +1
captured pawn square == (from_row, to_col)
captured piece exists
captured piece kind == PAWN
captured piece color != moving piece color
```

A non-pawn move to `board.en_passant_target` is just a normal move if otherwise legal. It must not remove the pawn behind the target square.

Examples:

- If White just played `e2e4`, the en-passant target is `e3`.
- If Black has a knight on `f5`, `f5e3` may be a legal knight move, but it is not en passant and must not remove the white pawn on `e4`.
- If Black just played `d7d5`, the en-passant target is `d6`.
- White en passant from `e5d6` removes the black pawn on `d5`.

### Castling invariant

Only a king may execute castling.

A valid castling execution requires all of the following:

```text
moving piece kind == KING
from/to coordinates match one of:
  White kingside:  e1 -> g1
  White queenside: e1 -> c1
  Black kingside:  e8 -> g8
  Black queenside: e8 -> c8
CastlingValidator says the castle is legal
```

A rook, queen, bishop, knight, or pawn moving through castling-shaped coordinates must never trigger castling rook movement.

Examples:

- A white rook on `e1` moving to `g1` is a normal rook move if legal. It must not move the rook on `h1` to `f1`.
- A white queen on `e1` moving to `g1` is not legal queen geometry anyway, but it must not be interpreted as castling.
- A black rook on `e8` moving to `c8` is not black queenside castling.

## Required Design Direction

The minimum acceptable patch is to make the executor's special-move detection strict.

However, the preferred design is to reduce guessing between validation and execution.

### Acceptable minimal design

Keep the current validation/execution flow, but harden the special-move checks:

```python
# Pseudocode only

def _is_castling_move(piece, from_square, to_square):
    return (
        piece.kind == PieceType.KING
        and castling_validator.is_castling_move(from_square, to_square)
    )


def _is_en_passant_capture(piece, from_square, to_square):
    if piece.kind != PieceType.PAWN:
        return False
    if board.en_passant_target is None:
        return False
    if to_square != board.en_passant_target:
        return False
    if abs(int(to_square.col) - int(from_square.col)) != 1:
        return False
    direction = -1 if piece.color == Color.WHITE else 1
    if int(to_square.row) - int(from_square.row) != direction:
        return False
    captured_square = square(from_square.row, to_square.col)
    captured_piece = board.get_piece(captured_square)
    return (
        captured_piece is not None
        and captured_piece.kind == PieceType.PAWN
        and captured_piece.color != piece.color
    )
```

This is acceptable if the tests prove the bugs are fixed and no new duplication is introduced.

### Preferred design

Introduce a small internal classification concept so validation determines the move kind and execution does not infer special moves from coordinates alone.

Example:

```python
class MoveKind(Enum):
    NORMAL = auto()
    CASTLING = auto()
    EN_PASSANT = auto()
    PROMOTION = auto()

@dataclass(frozen=True)
class ValidatedMove:
    from_square: ConstantSquare
    to_square: ConstantSquare
    moving_piece: Piece
    kind: MoveKind
    promotion: PieceType | None = None
```

Then:

```text
Board.make_move()
  asks MoveValidator to validate/classify move
  receives ValidatedMove or None/False
  passes ValidatedMove to MoveExecutor

MoveExecutor
  executes based on ValidatedMove.kind
  does not guess castling/en-passant from coordinates alone
```

Do not perform this refactor if it turns the patch into a large rewrite. The confirmed bugs can be fixed with strict predicates.

## Required Regression Tests

Add tests that fail before the fix and pass after the fix.

### King-capture tests

Required cases:

1. A rook cannot capture the opponent king.
2. A queen cannot capture the opponent king.
3. `Board.get_legal_moves()` must not include a king-capturing move.
4. `Board.make_move()` must not remove the opponent king.
5. The same principle should hold for kings attempting to move onto each other if that case is not already covered by attack detection.

Suggested position:

```text
White king: e1
White rook: a1
Black king: a8
White to move
Attempt: a1a8
Expected: False
Black king remains on a8
```

### En-passant misclassification tests

Required cases:

1. A knight moving to the en-passant target does not remove the pawn behind the target.
2. A bishop/rook/queen moving to the en-passant target, if legal in the constructed position, does not remove the pawn behind the target.
3. Only a pawn making the exact one-row diagonal en-passant capture may execute en passant.
4. Both white-side and black-side examples should be covered where practical.

Suggested white-double-push scenario:

```text
White king: e1
Black king: e8
White pawn: e2
Black knight: f5
White to move

White: e2e4
Black: f5e3

Expected:
- Black knight lands on e3.
- White pawn remains on e4.
- en_passant_target is cleared after Black's move.
```

Suggested black-double-push mirror:

```text
White king: e1
Black king: e8
Black pawn: e7
White knight: f4
Black to move

Black: e7e5
White: f4e6

Expected:
- White knight lands on e6.
- Black pawn remains on e5.
- en_passant_target is cleared after White's move.
```

### Castling misclassification tests

Required cases:

1. A rook move `e1g1` must not move the `h1` rook.
2. A rook move `e8g8` must not move the `h8` rook.
3. A rook move `e1c1` must not move the `a1` rook.
4. A rook move `e8c8` must not move the `a8` rook.
5. A non-king piece on a castling start square must never trigger castling execution.

Suggested white kingside-shaped scenario:

```text
White king: a1
White rook: e1
White rook: h1
Black king: a8
White to move
Attempt: e1g1

Expected:
- Move is legal as a rook move if path is clear and king safety allows it.
- Rook from e1 lands on g1.
- h1 rook remains on h1.
- f1 remains empty.
```

Suggested black kingside-shaped mirror:

```text
Black king: a8
Black rook: e8
Black rook: h8
White king: a1
Black to move
Attempt: e8g8

Expected:
- Rook from e8 lands on g8.
- h8 rook remains on h8.
- f8 remains empty.
```

## Acceptance Criteria

The patch is complete only when all of the following are true:

- Full test suite passes.
- New regression tests fail on the reviewed buggy version and pass after the fix.
- `Board.make_move(sq("a1"), sq("a8"))` cannot capture/remove a black king from the test position described above.
- A non-pawn move to `en_passant_target` never removes an en-passant capturable pawn.
- A non-king move with castling-shaped coordinates never moves a rook as part of castling.
- Existing castling, en-passant, promotion, check, checkmate, stalemate, and coordinate tests still pass.
- No debug `print()` statements are added to engine code.
- No tests are weakened or deleted to pass the suite.

## Manual Smoke Tests

After implementation, run a small manual script equivalent to this from the repo root.

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

## Final Notes

This patch should make the rules engine materially safer without changing its external behavior. The key principle is simple:

> Special move execution must be based on validated move semantics, not loose coordinate coincidence.

