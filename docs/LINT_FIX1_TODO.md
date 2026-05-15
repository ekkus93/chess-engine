# Lint Fix 1 — mypy Error Remediation TODO

## Overview

Fix all 23 mypy type errors across 7 files in `chess_game/`. The errors fall into 6 distinct categories, each requiring a different fix strategy.

---

## Task 1: Fix `RowType` / `ColType` type alias annotations in `constants.py`

**File:** `chess_game/chess/constants.py` (lines 290-291)
**Errors:** 2 — `Cannot assign multiple types to name without explicit type[...] annotation`

### Subtasks
- [x] 1.1 Import `TypeAlias` from `typing` (Python 3.10+) or use `typing_extensions`
- [x] 1.2 Change `RowType = int` to `RowType: TypeAlias = int`
- [x] 1.3 Change `ColType = int` to `ColType: TypeAlias = int`

---

## Task 2: Fix `ConstantSquare | None` attribute access in `piece_movers.py`

**File:** `chess_game/chess/pieces/piece_movers.py`
**Errors:** 12 — accessing `.row` / `.col` on a value typed `ConstantSquare | None`

### Root Cause
The method `get_valid_moves` calls `board.get_piece(square)` which returns `Optional[Piece]`. The `Piece._square` attribute is typed as `ConstantSquare | None`, so accessing `piece._square.row` or `piece._square.col` triggers a mypy error when `piece._square` could be `None`.

### Affected Lines
- Lines 45, 46 (bishop moves)
- Lines 120, 121 (knight moves)
- Lines 152, 153 (pawn moves)
- Lines 188, 189 (rook moves)
- Lines 289, 296 (queen moves — two separate locations)
- Lines 318, 319 (king moves)

### Subtasks
- [x] 2.1 Add a null-check guard before each access: `if piece._square is None: return []` (or similar early-return / assertion)
- [x] 2.2 Alternatively, add an assertion `assert piece._square is not None` at the start of `get_valid_moves`, since pieces on the board should always have a valid square
- [x] 2.3 Apply the same fix pattern consistently across all 6 piece types (bishop, knight, pawn, rook, queen, king)

---

## Task 3: Fix `ConstantSquare | None` attribute access in `move_validation.py`

**File:** `chess_game/chess/board/move_validation.py`
**Errors:** 2 — accessing `.row` on a value typed `ConstantSquare | None`

### Affected Lines
- Line 146: `king_row = int(piece._square.row)` inside `_get_castling_moves`
- Line 311: `captured_row = int(self.board.en_passant_target.row) - direction` inside `_would_expose_king_to_check_en_passant`

### Subtasks
- [x] 3.1 Line 146: Add null check on `piece._square` before accessing `.row` (e.g., `if piece._square is None: return []`)
- [x] 3.2 Line 311: The `en_passant_target` is already guarded at line 170 (`if self.board.en_passant_target is None: return False`), but the guard is in `_validate_en_passant`, not `_would_expose_king_to_check_en_passant`. Add the same guard at the start of `_would_expose_king_to_check_en_passant`.

---

## Task 4: Fix `ConstantSquare | None` attribute access in `move_execution.py`

**File:** `chess_game/chess/board/move_execution.py`
**Error:** 1 — accessing `.row` on a value typed `ConstantSquare | None`

### Affected Lines
- Line 138: `capture_row = int(ep_target.row) - direction` inside `_execute_en_passant_capture` — `ep_target` is `self.board.en_passant_target` which is `ConstantSquare | None`

### Subtasks
- [x] 4.1 Add null check on `self.board.en_passant_target` at the start of `_execute_en_passant_capture` (e.g., `assert self.board.en_passant_target is not None`)

---

## Task 5: Fix "returning Any" from typed function in `castling.py`

**File:** `chess_game/chess/board/castling.py`
**Errors:** 2 — `Returning Any from function declared as bool`

### Affected Lines
- Line 36: `return start_pos.row == 0 or start_pos.row == 7`
- Line 39: `return start_pos.row == 0 or start_pos.row == 7`

### Root Cause
Comparing `start_pos.row` (a `RowConstant`) with `int` literals (`0`, `7`) produces `Any` because the `==` operator on `RowConstant` vs `int` may not resolve to `bool` under mypy. The fix is to compare against the row constants instead of raw integers.

### Subtasks
- [x] 5.1 Import `ROW_1`, `ROW_8` (or the relevant row constants) at the top of the file if not already imported — verify they are already imported from `constants`
- [x] 5.2 Line 36: Replace `start_pos.row == 0 or start_pos.row == 7` with `start_pos.row == ROW_1 or start_pos.row == ROW_8`
- [x] 5.3 Line 39: Same replacement as 5.2

---

## Task 6: Fix `int` vs `RowConstant` / `ColConstant` type mismatch in `test_util.py`

**File:** `chess_game/test_util.py`
**Errors:** 4 — passing `int` where `RowConstant` / `ColConstant` expected

### Affected Lines
- Line 19: `ConstantSquare(row=0, col=4)` — `0` is `int`, needs `RowConstant`; `4` is `int`, needs `ColConstant`
- Line 23: `ConstantSquare(row=7, col=4)` — same issue

### Subtasks
- [x] 6.1 Import `get_row_constant` and `get_col_constant` from `chess_game.chess.constants`
- [x] 6.2 Line 19: Change `ConstantSquare(row=0, col=4)` to `ConstantSquare(row=get_row_constant(0), col=get_col_constant(4))`
- [x] 6.3 Line 23: Change `ConstantSquare(row=7, col=4)` to `ConstantSquare(row=get_row_constant(7), col=get_col_constant(4))`
- [x] 6.4 Line 34: `ConstantSquare(row=square[0], col=square[1])` — apply same fix proactively: `ConstantSquare(row=get_row_constant(square[0]), col=get_col_constant(square[1]))`

---

## Task 7: Fix `str | None` vs `str` type mismatch in `ai.py`

**File:** `chess_game/chess/ai.py` (line 163)
**Error:** 1 — `Argument 1 to "get" of "dict" has incompatible type "str | None"; expected "str"`

### Root Cause
Line 159: `key = _fen_key(board) if transposition_table is not None else None` — `key` is `str | None`.
Line 163: `transposition_table.get(key)` — `dict.get()` expects a `str` key, but `key` is `str | None`.

### Subtasks
- [x] 7.1 Change line 163 to guard against `None`: `cached = transposition_table.get(key) if key is not None else None`
- [x] 7.2 Verify the fix resolves the mypy error

---

## Execution Order

Recommended order to address tasks (by dependency):

1. **Task 1** (`constants.py`) — simple annotation fix, no downstream impact
2. **Task 5** (`castling.py`) — simple constant comparison fix
3. **Task 2** (`piece_movers.py`) — 12 errors, but all share the same fix pattern
4. **Task 3** (`move_validation.py`) — depends on Task 2 fix pattern
5. **Task 4** (`move_execution.py`) — depends on Task 2 fix pattern
6. **Task 6** (`test_util.py`) — simple constant wrapping
7. **Task 7** (`ai.py`) — single error, investigate last

After completing all tasks, run `mypy chess_game/` to verify zero errors.

---

## Verification

After all fixes:
- Run `mypy chess_game/` — expect 0 errors
- Run `python -m pytest tests/ -v` — ensure no regressions
- Run `python -m pytest tests/ --cov=chess_game` — verify coverage unchanged
