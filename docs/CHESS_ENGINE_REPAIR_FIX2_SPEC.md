# Chess Engine Repair Fix 2 Specification

## Purpose

This document defines the second focused repair pass for the chess engine after the large core-rules repair.

The engine is now substantially healthier than the original broken state, and the full existing pytest suite currently passes. However, review found real chess-rule bugs that the test suite does not catch:

1. Queenside castling is incorrectly allowed when `b1` or `b8` is occupied.
2. En passant accepts illegal long diagonal moves when the destination matches `en_passant_target`.
3. Castling logic is duplicated across `CastlingValidator`, `MoveValidator`, and `PieceMovers`.
4. Many tests still use raw row/column constants for real chess positions, making coordinate bugs easier to hide.
5. `BoardState` appears to be stale or semi-orphaned now that `Board` owns state directly.
6. AI evaluation appears to have a piece-square-table orientation issue, although this is lower priority than rules correctness.

This pass must stay focused. Do not add new features. Do not tune AI search. Do not add GUI behavior. Do not change the public API unless required for correctness.

---

## Authoritative invariants

### Coordinate system

The canonical board coordinate system remains:

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

Therefore:

```text
a8 = row 0, col 0
e8 = row 0, col 4
h8 = row 0, col 7
a1 = row 7, col 0
e1 = row 7, col 4
h1 = row 7, col 7
e2 = row 6, col 4
e7 = row 1, col 4
```

All tests that describe real chess positions should prefer algebraic notation helpers such as `sq("e4")` over raw row/column constants.

Raw row/column constants are acceptable only for tests that explicitly test internal coordinate conversion or low-level row/column APIs.

---

## Required fix 1: Queenside castling path validation

### Chess rule

Queenside castling requires all squares between the king and rook to be empty.

For White queenside castling:

```text
King starts: e1
Rook starts: a1
King ends:   c1
Rook ends:   d1

Required empty path squares before castling:
b1, c1, d1
```

For Black queenside castling:

```text
King starts: e8
Rook starts: a8
King ends:   c8
Rook ends:   d8

Required empty path squares before castling:
b8, c8, d8
```

The king attack-path rule is separate:

```text
White queenside attack checks: e1, d1, c1
Black queenside attack checks: e8, d8, c8
```

The `b1` or `b8` square does not need to be attack-free, because the king does not pass through it. It does, however, need to be empty because it is between the rook and king.

### Current bug

The current implementation checks `c1/c8` and `d1/d8`, but does not check `b1/b8`.

This allows illegal castling when a piece is on `b1` or `b8`.

### Required behavior

These positions must be rejected:

```text
White: king e1, rook a1, any piece on b1, black king e8
Move:  e1c1
Result: illegal
```

```text
Black: king e8, rook a8, any piece on b8, white king e1
Move:  e8c8
Result: illegal
```

### Architectural requirement

`CastlingValidator` must be the only authority for castling rules.

`PieceMovers._get_king_moves()` must not independently validate castling. It should produce only normal one-square king moves. Legal move generation may append castling moves by asking `CastlingValidator`.

This prevents duplicated castling bugs.

---

## Required fix 2: En passant geometry validation

### Chess rule

En passant is still a normal one-row diagonal pawn capture shape, except the captured pawn is removed from its adjacent square rather than the destination square.

White en passant geometry:

```text
to_row - from_row == -1
abs(to_col - from_col) == 1
to_square == board.en_passant_target
```

Black en passant geometry:

```text
to_row - from_row == +1
abs(to_col - from_col) == 1
to_square == board.en_passant_target
```

The captured pawn square is:

```text
captured_row = from_row
captured_col = to_col
```

### Current bug

The implementation accepts an en passant move when:

```text
moving piece is pawn
destination equals en_passant_target
source file differs from destination file
```

but does not require the pawn to move exactly one row diagonally.

This illegal move is accepted:

```text
White king: e1
Black king: e8
White pawn: e3
Black pawn: d5
en_passant_target: d6
White to move

Move: e3d6
Current result: legal
Required result: illegal
```

### Required behavior

Reject any en passant attempt where the row delta is not exactly one pawn step in the moving pawn's forward direction.

The validator must reject both:

```text
White e3d6
Black d6e3
```

and any other non-one-row diagonal move, even if the destination equals `en_passant_target`.

---

## Required fix 3: Test coordinate cleanup

The test suite currently passes, but it still contains heavy raw-coordinate usage for real chess positions.

This is dangerous because raw row/column tests can accidentally encode the wrong coordinate convention while still passing.

### Required behavior

Tests that describe chess positions must use helpers such as:

```python
sq("e1")
sq("c1")
sq("b1")
sq("e8")
sq("d6")
```

instead of:

```python
get_square_constant(7, 4)
ConstantSquare(row=ROW_1, col=COL_E)
```

### Priority test files

Clean these first:

```text
tests/test_board_setup.py
tests/test_castling.py
tests/test_en_passant.py
tests/test_en_passant_edge_cases.py
tests/test_promotion.py
tests/test_legal_moves.py
tests/test_check_checkmate_stalemate.py
tests/test_checkmate.py
```

It is acceptable to leave raw coordinate tests in files that directly test coordinate conversion internals.

### Required comments

Fix stale comments that describe old or wrong coordinate mappings.

No comment should say or imply:

```text
row 0 = rank 1
row 7 = rank 8
```

No comment should claim that `ROW_5` maps to row `2` under the current constants.

---

## Required fix 4: Resolve `BoardState`

The current code appears to have shifted state ownership primarily into `Board`, while `BoardState` remains present.

This creates a shadow architecture risk.

### Acceptable option A: Remove stale `BoardState`

If `BoardState` is unused by the actual engine path:

1. Remove the unused `BoardState` class/module.
2. Remove imports that reference it.
3. Remove obsolete tests that only test dead code.
4. Ensure all engine state is clearly owned by `Board`.

### Acceptable option B: Keep and repair `BoardState`

If `BoardState` is intentionally retained:

1. Make `Board` use it consistently.
2. Ensure `BoardState.clone()` deep-copies rows and pieces.
3. Ensure every cloned piece's `_square` points to its actual cloned square.
4. Add direct tests for `BoardState.clone()`.
5. Ensure no duplicate state fields can diverge between `Board` and `BoardState`.

### Preferred choice

Prefer Option A unless there is a clear design reason to retain `BoardState`.

The engine should not keep a parallel state object that is not used by the normal move-validation, execution, and legal-move paths.

---

## Optional fix: AI piece-square-table orientation

This is lower priority than rules correctness.

The current starting position appears to evaluate to a nonzero score. A normal symmetric starting position should evaluate to `0` or very near `0`, unless the engine intentionally includes a side-to-move tempo bonus.

Potential cause:

```python
piece_square_value = table[row][col]
```

is applied equally to both White and Black. If tables are written from White's perspective, Black should use a mirrored row:

```python
eval_row = row if piece.color == Color.WHITE else 7 - row
```

Required if touched:

1. Add a test asserting `evaluate(Board()) == 0` unless there is a documented tempo bonus.
2. Add a test with mirrored positions showing evaluation symmetry.
3. Do not tune search depth, opening books, pruning, or AI strategy in this pass.

---

## Non-goals

Do not do any of the following in this pass:

- Do not add UCI support.
- Do not add PGN support.
- Do not add FEN import/export unless already present and broken.
- Do not tune AI search quality.
- Do not add opening books.
- Do not add GUI features.
- Do not rewrite the entire engine.
- Do not weaken tests.
- Do not silence failing tests by marking them xfail unless a test is clearly obsolete and replaced by a better test.

---

## Required acceptance criteria

The patch is accepted only when all of the following are true:

1. Full test suite passes:

   ```bash
   python -m pytest tests -q
   ```

2. White queenside castling with `b1` occupied is rejected.
3. Black queenside castling with `b8` occupied is rejected.
4. White illegal long en passant such as `e3d6` is rejected.
5. Black illegal long en passant such as `d6e3` is rejected.
6. Legal en passant still works for both colors.
7. Legal castling still works for both colors and both sides.
8. `PieceMovers._get_king_moves()` no longer contains independent castling validation logic.
9. `CastlingValidator` is the only castling rule authority.
10. Real-position tests use algebraic helpers in the priority test files.
11. Stale coordinate comments are removed or corrected.
12. `BoardState` is either removed as stale or made correct, intentional, and tested.
13. No `__pycache__`, `.pytest_cache`, or generated cache files are committed.
