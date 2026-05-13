# Coordinate System Reference

This document defines the coordinate system used throughout the chess engine. **Read this carefully before working on any code.** Confusion about coordinates is the #1 source of bugs.

---

## The Golden Rule

**The board is an 8×8 array with these mappings:**

| Array Index | Algebraic Notation |
|-------------|-------------------|
| `row 0` | Rank 8 (black's back rank) |
| `row 1` | Rank 7 |
| `row 2` | Rank 6 |
| `row 3` | Rank 5 |
| `row 4` | Rank 4 |
| `row 5` | Rank 3 |
| `row 6` | Rank 2 |
| `row 7` | Rank 1 (white's back rank) |
| `col 0` | File 'a' |
| `col 1` | File 'b' |
| `col 2` | File 'c' |
| `col 3` | File 'd' |
| `col 4` | File 'e' |
| `col 5` | File 'f' |
| `col 6` | File 'g' |
| `col 7` | File 'h' |

**Key insight:** Array row 0 is at the **TOP** (rank 8, where black starts). Array row 7 is at the **BOTTOM** (rank 1, where white starts).

---

## Algebraic to Array Conversion

### Formula

```
algebraic: "e2"
  file 'e' → col 4
  rank 2   → row = 8 - 2 = 6
  Result:  (row=6, col=4)
```

### Code

```python
from chess_game.chess.coords import algebraic_to_index

square = algebraic_to_index("e2")
# Returns ConstantSquare(row=ROW_2, col=COL_E)
# Where ROW_2 has internal value 6, COL_E has internal value 4
```

### Complete Mapping Table

| Algebraic | File | Rank | Array (row, col) | ROW_* Constant | COL_* Constant |
|-----------|------|------|------------------|----------------|----------------|
| a8 | a | 8 | (0, 0) | ROW_8 | COL_A |
| h8 | h | 8 | (0, 7) | ROW_8 | COL_H |
| e8 | e | 8 | (0, 4) | ROW_8 | COL_E |
| e7 | e | 7 | (1, 4) | ROW_7 | COL_E |
| e2 | e | 2 | (6, 4) | ROW_2 | COL_E |
| e1 | e | 1 | (7, 4) | ROW_1 | COL_E |
| a1 | a | 1 | (7, 0) | ROW_1 | COL_A |
| h1 | h | 1 | (7, 7) | ROW_1 | COL_H |

---

## ROW_* Constants

The constant names encode the **rank**, not the array index.

| Constant | Rank | Array Index | Internal Value |
|----------|------|-------------|----------------|
| ROW_8 | 8 | 0 | 0 |
| ROW_7 | 7 | 1 | 1 |
| ROW_6 | 6 | 2 | 2 |
| ROW_5 | 5 | 3 | 3 |
| ROW_4 | 4 | 4 | 4 |
| ROW_3 | 3 | 5 | 5 |
| ROW_2 | 2 | 6 | 6 |
| ROW_1 | 1 | 7 | 7 |

**Remember:** `ROW_N` means "the constant for rank N", which has array index `8 - N`.

**Example:**
```python
# CORRECT:
square = ConstantSquare(row=ROW_2, col=COL_E)  # rank 2, file e → (6, 4)

# WRONG:
square = ConstantSquare(row=2, col=5)  # Raises ValueError immediately!
```

---

## White Pawn Movement

### Starting Position
- White pawns start on **rank 2** (array row 6)
- Example: `e2` = `(ROW_2, COL_E)` = `(row=6, col=4)`

### Direction
- White pawns move toward **rank 8** (array row 0)
- White pawns move toward **smaller row numbers** (row - 1)

### Movement Rules

| Move Type | From (array) | To (array) | Description |
|-----------|--------------|------------|-------------|
| One step | (6, c) | (5, c) | e2→e3 |
| Two step | (6, c) | (4, c) | e2→e4 (both squares must be empty) |
| Capture | (r, c) | (r-1, c±1) | diagonal capture |

### Code Pattern

```python
# White pawn from e2 to e3
start = ConstantSquare(row=ROW_2, col=COL_E)  # (6, 4)
end = ConstantSquare(row=ROW_3, col=COL_E)    # (5, 4)

# Direction is negative in row
row_delta = int(end.row) - int(start.row)  # 5 - 6 = -1
col_delta = int(end.col) - int(start.col)  # 4 - 4 = 0

# White pawn forward = row - 1 (toward rank 8)
# White pawn captures = row - 1, col ± 1
```

---

## Black Pawn Movement

### Starting Position
- Black pawns start on **rank 7** (array row 1)
- Example: `e7` = `(ROW_7, COL_E)` = `(row=1, col=4)`

### Direction
- Black pawns move toward **rank 1** (array row 7)
- Black pawns move toward **larger row numbers** (row + 1)

### Movement Rules

| Move Type | From (array) | To (array) | Description |
|-----------|--------------|------------|-------------|
| One step | (1, c) | (2, c) | e7→e6 |
| Two step | (1, c) | (3, c) | e7→e5 (both squares must be empty) |
| Capture | (r, c) | (r+1, c±1) | diagonal capture |

### Code Pattern

```python
# Black pawn from e7 to e6
start = ConstantSquare(row=ROW_7, col=COL_E)  # (1, 4)
end = ConstantSquare(row=ROW_6, col=COL_E)    # (2, 4)

# Direction is positive in row
row_delta = int(end.row) - int(start.row)  # 2 - 1 = +1
col_delta = int(end.col) - int(start.col)  # 4 - 4 = 0

# Black pawn forward = row + 1 (toward rank 1)
# Black pawn captures = row + 1, col ± 1
```

---

## Piece Starting Positions

### White (ranks 1-2)

| Rank | Array Row | Pieces |
|------|-----------|--------|
| Rank 1 | row 7 | R N B Q K B N R |
| Rank 2 | row 6 | P P P P P P P P |

Example:
```python
# White king on e1
white_king = ConstantSquare(row=ROW_1, col=COL_E)  # (7, 4)

# White pawn on e2
white_pawn = ConstantSquare(row=ROW_2, col=COL_E)  # (6, 4)
```

### Black (ranks 7-8)

| Rank | Array Row | Pieces |
|------|-----------|--------|
| Rank 7 | row 1 | P P P P P P P P |
| Rank 8 | row 0 | R N B Q K B N R |

Example:
```python
# Black king on e8
black_king = ConstantSquare(row=ROW_8, col=COL_E)  # (0, 4)

# Black pawn on e7
black_pawn = ConstantSquare(row=ROW_7, col=COL_E)  # (1, 4)
```

---

## Common Pitfalls

### Don't confuse rank with array index
```python
# row 0 = rank 8, row 7 = rank 1
# ROW_N has array index (8 - N)
```

### Don't mix up white/black pawn direction
```python
# White pawns: row - 1 (toward rank 8, row 0)
# Black pawns: row + 1 (toward rank 1, row 7)
```

### Always use ROW_* and COL_* constants, never raw integers
```python
# WRONG:
square = ConstantSquare(row=6, col=4)

# CORRECT:
square = ConstantSquare(row=ROW_2, col=COL_E)
```

### Don't confuse e1 with e8
```python
# e1 (white's back rank)
e1 = ConstantSquare(row=ROW_1, col=COL_E)  # (7, 4)

# e8 (black's back rank)
e8 = ConstantSquare(row=ROW_8, col=COL_E)  # (0, 4)
```

---

## Quick Reference

### White Pieces
- **Forward**: decreasing row (row - 1)
- **Toward**: rank 8 (row 0)
- **Start**: rank 2 (row 6) for pawns, rank 1 (row 7) for back rank

### Black Pieces
- **Forward**: increasing row (row + 1)
- **Toward**: rank 1 (row 7)
- **Start**: rank 7 (row 1) for pawns, rank 8 (row 0) for back rank

### Quick Test
```python
# White pawn e2→e3: row 6 → row 5 (delta = -1)
# Black pawn e7→e6: row 1 → row 2 (delta = +1)
```

---

## Summary

**The board:**
- Array rows 0-7, columns 0-7
- Row 0 = rank 8 (black's side, top)
- Row 7 = rank 1 (white's side, bottom)
- Col 0 = file a, Col 7 = file h

**Constants:**
- Use `ROW_1` through `ROW_8` (not raw integers!)
- Use `COL_A` through `COL_H` (not raw integers!)
- `ROW_N` represents rank N, which has array index `8 - N`

**Pawn directions:**
- White: row - 1 (toward rank 8)
- Black: row + 1 (toward rank 1)

**Golden rule:** When in doubt, check `tests/test_coords.py` and `tests/test_setup.py` for expected behavior.
