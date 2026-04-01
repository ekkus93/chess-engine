# Coordinate System Reference

This document defines the coordinate system used throughout the chess engine. **Read this carefully before working on any code.** Confusion about coordinates is the #1 source of bugs.

---

## The Golden Rule

**The board is an 8×8 array with these mappings:**

| Array Index | Algebraic Notation |
|-------------|-------------------|
| `row 0` | Rank 1 (white's back rank) |
| `row 1` | Rank 2 |
| `row 2` | Rank 3 |
| `row 3` | Rank 4 |
| `row 4` | Rank 5 |
| `row 5` | Rank 6 |
| `row 6` | Rank 7 |
| `row 7` | Rank 8 (black's back rank) |
| `col 0` | File 'a' |
| `col 1` | File 'b' |
| `col 2` | File 'c' |
| `col 3` | File 'd' |
| `col 4` | File 'e' |
| `col 5` | File 'f' |
| `col 6` | File 'g' |
| `col 7` | File 'h' |

**Key insight:** Array row 0 is at the **BOTTOM** (rank 1, where white starts). Array row 7 is at the **TOP** (rank 8, where black starts).

---

## Algebraic to Array Conversion

### Formula

```
algebraic: "e2"
  file 'e' → col 4
  rank 2   → row 1
  Result:  (row=1, col=4)
```

### Code

```python
from chess_game.constants import ROW_2, COL_E

square = algebraic_to_index("e2")
# Returns: ConstantSquare(row=ROW_2, col=COL_E)
# Where ROW_2 has internal value 1, COL_E has internal value 4
```

### Complete Mapping Table

| Algebraic | File | Rank | Array (row, col) | ROW_* Constant | COL_* Constant |
|-----------|------|------|------------------|----------------|----------------|
| a1 | a | 1 | (0, 0) | ROW_1 | COL_A |
| h1 | h | 1 | (0, 7) | ROW_1 | COL_H |
| e1 | e | 1 | (0, 4) | ROW_1 | COL_E |
| a2 | a | 2 | (1, 0) | ROW_2 | COL_A |
| e2 | e | 2 | (1, 4) | ROW_2 | COL_E |
| h2 | h | 2 | (1, 7) | ROW_2 | COL_H |
| ... | ... | ... | ... | ... | ... |
| a8 | a | 8 | (7, 0) | ROW_8 | COL_A |
| e8 | e | 8 | (7, 4) | ROW_8 | COL_E |
| h8 | h | 8 | (7, 7) | ROW_8 | COL_H |

---

## ROW_* Constants - CRITICAL!

The constant names can be **confusing** because they show the **rank**, not the **array index**.

| Constant | Rank | Array Index | Internal Value |
|----------|------|-------------|----------------|
| ROW_0 (alias) | 1 | 0 | 0 |
| ROW_1 | 1 | 0 | 0 |
| ROW_2 | 2 | 1 | 1 |
| ROW_3 | 3 | 2 | 2 |
| ROW_4 | 4 | 3 | 3 |
| ROW_5 | 5 | 4 | 4 |
| ROW_6 | 6 | 5 | 5 |
| ROW_7 | 7 | 6 | 6 |
| ROW_8 | 8 | 7 | 7 |

**Remember:** `ROW_N` means "the constant for rank N", which has array index `N-1`.

**Example:**
```python
# CORRECT:
square = ConstantSquare(row=ROW_2, col=COL_E)  # rank 2, file e

# WRONG:
square = ConstantSquare(row=2, col=5)  # Raises ValueError immediately!

# DON'T DO THIS:
# square = ConstantSquare(row=ROW_7, col=COL_E)  # This is rank 7, NOT e7 from white's perspective!
```

---

## White Pawn Movement

### Starting Position
- White pawns start on **rank 2** (array row 1)
- Example: `e2` = `(ROW_2, COL_E)` = `(row=1, col=4)`

### Direction
- White pawns move toward **rank 1** (array row 0)
- White pawns move toward **smaller row numbers**

### Movement Rules

| Move Type | From (array) | To (array) | Description |
|-----------|--------------|------------|-------------|
| One step | (1, c) | (0, c) | e2→e1 |
| Two step | (1, c) | (-1, c) | e2→e4 (both squares must be empty) |
| Capture | (1, c) | (0, c±1) | e2×d3 or e2×f3 |

### Code Pattern

```python
# White pawn from e2 to e3
start = ConstantSquare(row=ROW_2, col=COL_E)  # (1, 4)
end = ConstantSquare(row=ROW_1, col=COL_E)    # (0, 4)

# Direction is negative in row
row_delta = int(end.row) - int(start.row)  # 0 - 1 = -1
col_delta = int(end.col) - int(start.col)  # 4 - 4 = 0

# White pawn forward = row - 1 (toward rank 1)
# White pawn captures = row - 1, col ± 1
```

---

## Black Pawn Movement

### Starting Position
- Black pawns start on **rank 7** (array row 6)
- Example: `e7` = `(ROW_7, COL_E)` = `(row=6, col=4)`

### Direction
- Black pawns move toward **rank 8** (array row 7)
- Black pawns move toward **larger row numbers**

### Movement Rules

| Move Type | From (array) | To (array) | Description |
|-----------|--------------|------------|-------------|
| One step | (6, c) | (7, c) | e7→e8 |
| Two step | (6, c) | (8, c) | e7→e5 (both squares must be empty) |
| Capture | (6, c) | (7, c±1) | e7×d8 or e7×f8 |

### Code Pattern

```python
# Black pawn from e7 to e6
start = ConstantSquare(row=ROW_7, col=COL_E)  # (6, 4)
end = ConstantSquare(row=ROW_8, col=COL_E)    # (7, 4)

# Direction is positive in row
row_delta = int(end.row) - int(start.row)  # 7 - 6 = +1
col_delta = int(end.col) - int(start.col)  # 4 - 4 = 0

# Black pawn forward = row + 1 (toward rank 8)
# Black pawn captures = row + 1, col ± 1
```

---

## Piece Starting Positions

### White (ranks 1-2)

| Rank | Array Row | Pieces |
|------|-----------|--------|
| Rank 1 | row 0 | R N B Q K B N R |
| Rank 2 | row 1 | P P P P P P P P |

Example:
```python
# White king on e1
white_king = ConstantSquare(row=ROW_1, col=COL_E)  # (0, 4)

# White pawn on e2
white_pawn = ConstantSquare(row=ROW_2, col=COL_E)  # (1, 4)
```

### Black (ranks 7-8)

| Rank | Array Row | Pieces |
|------|-----------|--------|
| Rank 7 | row 6 | P P P P P P P P |
| Rank 8 | row 7 | R N B Q K B N R |

Example:
```python
# Black king on e8
black_king = ConstantSquare(row=ROW_8, col=COL_E)  # (7, 4)

# Black pawn on e7
black_pawn = ConstantSquare(row=ROW_7, col=COL_E)  # (6, 4)
```

---

## Common Pitfalls

### ❌ WRONG: Confusing rank with array index
```python
# This is WRONG:
square = ConstantSquare(row=8, col=4)  # row 8 doesn't exist!
square = ConstantSquare(row=ROW_8, col=COL_E)  # This is rank 8, array row 7

# This is RIGHT:
square = ConstantSquare(row=ROW_8, col=COL_E)  # Correct
```

### ❌ WRONG: Getting white/black direction mixed up
```python
# White pawns move toward ROW_1 (rank 1)
# Black pawns move toward ROW_8 (rank 8)

# WRONG: treating both pawns the same
if piece.color == WHITE and piece.kind == PAWN:
    forward_row = row - 1  # WHITE: correct
else:
    forward_row = row + 1  # BLACK: correct

# But remember: ROW_1 = 0, ROW_8 = 7
# White: row 1 → row 0 (decreasing)
# Black: row 6 → row 7 (increasing)
```

### ❌ WRONG: Using raw integers
```python
# This raises ValueError immediately:
square = ConstantSquare(row=2, col=5)  # ❌ WRONG!

# This is correct:
square = ConstantSquare(row=ROW_2, col=COL_E)  # ✅ CORRECT!
```

### ❌ WRONG: Confusing e1 with e8
```python
# e1 (white's back rank)
e1 = ConstantSquare(row=ROW_1, col=COL_E)  # (0, 4)

# e8 (black's back rank)  
e8 = ConstantSquare(row=ROW_8, col=COL_E)  # (7, 4)

# DON'T mix them up!
```

---

## Direction Cheat Sheet

### White Pieces
- **Forward**: decreasing row (row - 1)
- **Toward**: ROW_1 (rank 1, array row 0)
- **Start**: ROW_2 (pawns), ROW_1 (back rank)

### Black Pieces
- **Forward**: increasing row (row + 1)
- **Toward**: ROW_8 (rank 8, array row 7)
- **Start**: ROW_7 (pawns), ROW_8 (back rank)

### Quick Test
```python
# Is this a white pawn moving forward?
start_row = 1  # ROW_2 (rank 2)
end_row = 0    # ROW_1 (rank 1)
delta = end_row - start_row  # -1 (negative = white forward)

# Is this a black pawn moving forward?
start_row = 6  # ROW_7 (rank 7)
end_row = 7    # ROW_8 (rank 8)
delta = end_row - start_row  # +1 (positive = black forward)
```

---

## Summary

**The board:**
- Array rows 0-7, columns 0-7
- Row 0 = rank 1 (white's side, bottom)
- Row 7 = rank 8 (black's side, top)
- Col 0 = file a, Col 7 = file h

**Constants:**
- Use `ROW_1` through `ROW_8` (not raw integers!)
- Use `COL_A` through `COL_H` (not raw integers!)
- `ROW_N` represents rank N, which has array index `N-1`

**Pawn directions:**
- White: row - 1 (toward ROW_1)
- Black: row + 1 (toward ROW_8)

**Golden rule:** When in doubt, check `tests/test_coords.py` and `tests/test_setup.py` for expected behavior.
