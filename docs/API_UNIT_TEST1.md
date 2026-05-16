# API Unit Test Plan — Batch 1

## Untested Board API Methods

| # | Method | Signature |
|---|--------|-----------|
| 1 | `is_valid_position` | `(square: ConstantSquare) -> bool` |
| 2 | `is_same_color` | `(square1: ConstantSquare, square2: ConstantSquare) -> bool` |
| 3 | `is_opponent` | `(square1: ConstantSquare, square2: ConstantSquare) -> bool` |
| 4 | `is_empty` | `(square: ConstantSquare) -> bool` |
| 5 | `find_king` | `(color: Color) -> Optional[ConstantSquare]` |
| 6 | `get_legal_moves_for_color` | `(color: Color) -> List[LegalMove]` |

---

## 1. `is_valid_position`

Validates that a `ConstantSquare` falls within the 8×8 board bounds.

### Tasks

- [ ] Test valid corner squares (a1, a8, h1, h8) return `True`
- [ ] Test valid center squares (e4, d5) return `True`
- [ ] Test out-of-bounds column index (< 0 or >= 8) returns `False`
- [ ] Test out-of-bounds row index (< 0 or >= 8) returns `False`
- [ ] Test negative row and column indices return `False`

---

## 2. `is_same_color`

Checks whether the pieces on two squares share the same color.

### Tasks

- [ ] Test two white pieces on different squares return `True`
- [ ] Test two black pieces on different squares return `True`
- [ ] Test one white and one black piece return `False`
- [ ] Test same square returns `True`
- [ ] Test one occupied and one empty square returns `False`
- [ ] Test both squares empty returns `False`

---

## 3. `is_opponent`

Checks whether the pieces on two squares have opposing colors.

### Tasks

- [ ] Test white vs black piece returns `True`
- [ ] Test black vs white piece returns `True`
- [ ] Test two white pieces return `False`
- [ ] Test two black pieces return `False`
- [ ] Test one occupied and one empty square returns `False`
- [ ] Test both squares empty returns `False`
- [ ] Test same square returns `False`

---

## 4. `is_empty`

Checks whether a square has no piece.

### Tasks

- [ ] Test default board empty squares (e.g., e2, e7) return `True`
- [ ] Test occupied squares (e.g., e1 has king) return `False`
- [ ] Test square after `clear_square` returns `True`
- [ ] Test square after `set_piece` returns `False`
- [ ] Test corner squares on default board (a1 has rook → `False`, a8 has rook → `False`)

---

## 5. `find_king`

Locates the king square for a given color.

### Tasks

- [ ] Test default board white king found at e1
- [ ] Test default board black king found at e8
- [ ] Test after king moves, new position is returned
- [ ] Test after king captured (impossible in chess, but edge case) returns `None`
- [ ] Test both colors independently return correct squares
- [ ] Test cloned board preserves king positions

---

## 6. `get_legal_moves_for_color`

Returns all legal moves for a given color.

### Tasks

- [ ] Test default board white has expected number of legal moves (20)
- [ ] Test default board black has expected number of legal moves (20)
- [ ] Test after a move, only the next side's moves are returned
- [ ] Test pinned pieces do not produce illegal moves in the list
- [ ] Test castling moves appear when conditions are met
- [ ] Test en passant move appears when available
- [ ] Test promotion moves appear when pawn reaches rank
- [ ] Test checkmate position returns empty list for side in checkmate
- [ ] Test stalemate position returns empty list for side in stalemate

---

## File Structure

All tests go in `tests/test_board_api.py`.

### Task Summary

| Method | Tests |
|--------|-------|
| `is_valid_position` | 5 |
| `is_same_color` | 6 |
| `is_opponent` | 7 |
| `is_empty` | 5 |
| `find_king` | 6 |
| `get_legal_moves_for_color` | 9 |
| **Total** | **38** |
