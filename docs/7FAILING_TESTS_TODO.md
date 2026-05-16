# 7 Failing Tests - TODO List

## Overview

Seven tests in `tests/test_board_api.py` are currently failing. Each test maps to a specific bug in the chess engine. This document tracks all fixes needed, organized by test, with detailed subtasks.

---

## 1. `test_find_king_after_king_moves`

**Symptom**: After moving a king (e.g., e1→f1), `board.find_king(Color.WHITE)` still returns the old square (e1) instead of the new square (f1).

**Root Cause**: King position is not updated when the king moves. The `Piece._square` is updated via `piece.square = to_square` in `move_execution.py:157`, but the board's internal king tracking (`_white_king_pos`, `_black_king_pos`) is not updated to follow the piece.

### Subtasks
- [ ] 1.1. Locate `_white_king_pos` / `_black_king_pos` in `board.py` and understand how they are initialized.
- [ ] 1.2. Find where king position is set during board creation/setup.
- [ ] 1.3. Modify `move_execution.py` `_move_piece` (or add a board method) to update `_white_king_pos` / `_black_king_pos` when a king moves.
- [ ] 1.4. Verify `find_king()` reads from these tracked positions.
- [ ] 1.5. Run `test_find_king_after_king_moves` to confirm fix.

---

## 2. `test_find_king_cloned_board_preserves_positions`

**Symptom**: After cloning a board where the king has moved, `cloned_board.find_king()` returns incorrect positions.

**Root Cause**: The board's `__copy__` / clone method does not preserve `_white_king_pos` / `_black_king_pos` (or the underlying mechanism is broken per fix #1).

### Subtasks
- [ ] 2.1. Locate the `__copy__` or clone method in `board.py`.
- [ ] 2.2. Verify that king position fields are copied to the new board instance.
- [ ] 2.3. Fix copy logic if king positions are not transferred.
- [ ] 2.4. This fix may resolve automatically once fix #1 is applied — verify after fix #1.
- [ ] 2.5. Run `test_find_king_cloned_board_preserves_positions` to confirm fix.

---

## 3. `test_legal_moves_for_color_pinned_piece_no_illegal_moves`

**Symptom**: A pinned piece (e.g., e2 pawn pinned by a rook on e8) still generates legal moves. The test expects the pinned piece to have zero legal moves.

**Root Cause**: The `_filter_legal_moves` method in `board.py` does not correctly filter out moves from pinned pieces. The pin detection logic or the filtering step is missing or broken.

### Subtasks
- [ ] 3.1. Locate `_filter_legal_moves` in `board.py` and understand its current logic.
- [ ] 3.2. Locate pin detection logic (likely in `attack_utils.py` or `move_validation.py`).
- [ ] 3.3. Understand how pins are detected — check if `_is_square_pinned` or equivalent exists.
- [ ] 3.4. Ensure `_filter_legal_moves` calls pin check for each generated move.
- [ ] 3.5. If pin filtering is missing entirely, implement it: for each move, simulate it and check if it exposes the king to check.
- [ ] 3.6. Run `test_legal_moves_for_color_pinned_piece_no_illegal_moves` to confirm fix.

---

## 4. `test_legal_moves_for_color_castling_moves_appear`

**Symptom**: In a position where castling should be legal (e.g., fresh board after white plays e2-e4), the castling moves (O-O / O-O-O) do not appear in `get_legal_moves_for_color(White)`.

**Root Cause**: Castling moves are not being generated in the move generation pipeline. The `get_legal_moves_for_color` method may not include castling moves from the king's square, or `PieceMovers` for the king does not include castling targets.

### Subtasks
- [ ] 4.1. Locate `get_legal_moves_for_color` in `board.py` and trace how moves are collected.
- [ ] 4.2. Check if `PieceMovers` for the king includes castling squares (c1/g1 for white, c8/g8 for black).
- [ ] 4.3. If castling squares are not in the king's legal squares, add them (or handle castling separately in `get_legal_moves_for_color`).
- [ ] 4.4. Verify `MoveValidator.is_valid_move` passes castling moves via `CastlingValidator`.
- [ ] 4.5. Run `test_legal_moves_for_color_castling_moves_appear` to confirm fix.

---

## 5. `test_legal_moves_for_color_en_passant_appears`

**Symptom**: After a double pawn push (e.g., b2-b4), the en passant capture (axb3 or cxb3) does not appear in `get_legal_moves_for_color(White)`.

**Root Cause**: En passant target square is set correctly, but en passant moves are not generated in the pawn's legal squares. The `PieceMovers` for pawns may not include en passant logic, or the en passant row/destination calculation is wrong.

### Subtasks
- [ ] 5.1. Read `piece_movers.py` pawn move generation — locate where capture squares are computed.
- [ ] 5.2. Check if en passant capture squares are added to the pawn's legal squares list.
- [ ] 5.3. If missing, add en passant logic: when `board.en_passant_target` is set and is on the pawn's capture rank, include it as a legal square.
- [ ] 5.4. Verify the en passant row calculation (White captures on row 3/`ROW_C`, Black captures on row 5/`ROW_E`).
- [ ] 5.5. Verify the destination square for en passant is the target square itself (not the captured piece's square).
- [ ] 5.6. Run `test_legal_moves_for_color_en_passant_appears` to confirm fix.

---

## 6. `test_legal_moves_for_color_promotion_moves_appear`

**Symptom**: When a pawn reaches the last rank, promotion moves (to queen, rook, bishop, knight) do not appear in `get_legal_moves_for_color`.

**Root Cause**: Promotion moves are not generated during move generation. The `PieceMovers` for pawns may not handle promotion squares, or `get_legal_moves_for_color` does not expand promotion moves into multiple entries (one per piece type).

### Subtasks
- [ ] 6.1. Read `board.py` `get_legal_moves_for_color` — check if promotion expansion happens there.
- [ ] 6.2. Read `piece_movers.py` pawn logic — check if pawns on rank 2/7 still generate moves to rank 1/8.
- [ ] 6.3. If promotion squares are not in pawn's legal squares, add them.
- [ ] 6.4. If promotion squares are present but not expanded, add promotion expansion in `get_legal_moves_for_color` (generate one move per promotion piece type: Q, R, B, N).
- [ ] 6.5. Run `test_legal_moves_for_color_promotion_moves_appear` to confirm fix.

---

## 7. `test_legal_moves_for_color_checkmate_has_no_moves`

**Symptom**: In a checkmate position, `get_legal_moves_for_color` returns 2 moves (king to d8 and f8) instead of 0.

**Root Cause**: The checkmate position's setup may be incorrect, OR the king's move generation includes squares that would still leave it in check (pin/check filtering issue for the king specifically).

### Subtasks
- [ ] 7.1. Read the test setup for `test_legal_moves_for_color_checkmate_has_no_moves` carefully.
- [ ] 7.2. Verify the position actually creates checkmate (all king squares covered, no captures, no blocks).
- [ ] 7.3. If the setup is wrong, fix the piece placement in the test.
- [ ] 7.4. If the setup is correct, this is the same root cause as fix #3 (pin/check filtering is broken).
- [ ] 7.5. This test may resolve automatically once fix #3 (pin filtering) is applied — verify after fix #3.
- [ ] 7.6. Run `test_legal_moves_for_color_checkmate_has_no_moves` to confirm fix.

---

## Dependency Graph

```
Fix #3 (pin filtering) → may also fix #7 (checkmate)
Fix #1 (king tracking) → may also fix #2 (cloned board king positions)
Fix #4 (castling), #5 (en passant), #6 (promotion) are independent
```

## Execution Order (Recommended)

1. Fix #1 — King tracking (foundational, affects #2)
2. Fix #2 — Cloned board king positions (verify after #1)
3. Fix #3 — Pin filtering (foundational, affects #7)
4. Fix #7 — Checkmate (verify after #3)
5. Fix #4 — Castling move generation
6. Fix #5 — En passant move generation
7. Fix #6 — Promotion move generation

## Verification

After all fixes:
- Run `python -m pytest tests/test_board_api.py -v` — all 7 tests should pass
- Run `python -m pytest tests/ -v` — full test suite should pass
- Run `pylint chess_game/` — score should remain near 10/10
