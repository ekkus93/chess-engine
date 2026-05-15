# Lint Fix 2 — Pylint Warning Remediation TODO

## Overview

Fix all remaining pylint warnings across the `chess_game/` package. Current score: **9.56/10**. Target: **10.00/10** (or as close as possible without breaking tests).

Total remaining warnings: **~68 across 12 files**.

Warnings fall into two categories:
- **Fixable** — can be resolved with a code change (docstrings, unused imports, max/min, else-after-return, etc.)
- **Disable-only** — inherent to chess logic or design; require `# pylint: disable=...` with justification

---

## Task 1: Fix `chess_game/chess/move.py` — Missing module docstring

**File:** `chess_game/chess/move.py`
**Warnings:** 1

### Subtasks
- [x] 1.1 Add a module docstring to `move.py` (C0114)

---

## Task 2: Fix `chess_game/chess/board/move_execution.py` — Docstrings, unused args, protected access

**File:** `chess_game/chess/board/move_execution.py`
**Warnings:** 6

### Subtasks
- [ ] 2.1 Add docstring to method at line 26 (C0116)
- [ ] 2.2 Prefix unused args with `_`: `_piece`, `_from_square` at lines 126, 134, 147 (W0613)
- [ ] 2.3 Add `# pylint: disable=protected-access` to line 150 accessing `_square` (W0212)
- [ ] 2.4 Add `# pylint: disable=too-few-public-methods` class-level disable for MoveExecutor (R0903)

---

## Task 3: Fix `chess_game/chess/board/promotion.py` — Missing docstrings, unnecessary else

**File:** `chess_game/chess/board/promotion.py`
**Warnings:** 10

### Subtasks
- [x] 3.1 Add docstrings to all 7 methods missing them (lines 21, 24, 36, 49, 57, 73, 82) (C0116)
- [x] 3.2 Remove unnecessary `else` after `return` at lines 31, 77, 83 (R1705)

---

## Task 4: Fix `chess_game/chess/board/attack_utils.py` — elif-after-return, too-many-returns, import placement

**File:** `chess_game/chess/board/attack_utils.py`
**Warnings:** 3

### Subtasks
- [ ] 4.1 Remove unnecessary `elif` after `return` at line 30 (R1705)
- [ ] 4.2 Move `from chess_game.chess.constants import Color` import to top of file (C0415)
- [ ] 4.3 Add class-level `# pylint: disable=too-many-return-statements` for `piece_attacks_square` (R0911)

---

## Task 5: Fix `chess_game/chess/board/castling.py` — Docstrings, unused import, consider-using-in, elif-after-return, too-many-returns

**File:** `chess_game/chess/board/castling.py`
**Warnings:** 10

### Subtasks
- [x] 5.1 Add docstrings to 4 methods (lines 35, 45, 65, 79) (C0116)
- [x] 5.2 Remove unused `Piece` import from `chess_game.chess.types` (W0611)
- [x] 5.3 Replace `start_pos.row == ROW_1 or start_pos.row == ROW_8` with `start_pos.row in (ROW_1, ROW_8)` at lines 37, 40 (R1714)
- [x] 5.4 Remove unnecessary `elif` after `return` at line 189 (R1705)
- [x] 5.5 Add `# pylint: disable=too-many-return-statements` to methods at lines 93 and 183 (R0911)

---

## Task 6: Fix `chess_game/chess/board/move_validation.py` — Unused import, protected access, too-many-returns/branches/locals/nested, elif-after-return

**File:** `chess_game/chess/board/move_validation.py`
**Warnings:** 9

### Subtasks
- [ ] 6.1 Remove unused `COL_E` import at line 13 (W0611)
- [ ] 6.2 Add `# pylint: disable=protected-access` to lines 145, 148 accessing `_square` (W0212)
- [ ] 6.3 Remove unnecessary `elif` after `return` at line 366 (R1705)
- [ ] 6.4 Add function-level `# pylint: disable=too-many-return-statements` to `_validate_basic_move` (line 38) and `_get_castling_moves` (line 358) (R0911)
- [ ] 6.5 Add function-level `# pylint: disable=too-many-branches` to `_check_all_squares_for_attacks` (line 189) (R0912)
- [ ] 6.6 Add function-level `# pylint: disable=too-many-nested-blocks` to `_would_expose_king_to_check_en_passant` (line 200) (R1702)
- [ ] 6.7 Add function-level `# pylint: disable=too-many-locals` to `_check_all_squares_for_attacks` (line 293) (R0914)

---

## Task 7: Fix `chess_game/chess/board/board.py` — Protected access, else-after-return, too-many-instance-attributes, too-many-returns/branches/public-methods

**File:** `chess_game/chess/board/board.py`
**Warnings:** 12

### Subtasks
- [ ] 7.1 Remove unnecessary `else` after `return` at line 66 (R1705)
- [ ] 7.2 Add class-level `# pylint: disable=too-many-instance-attributes` to Board class (R0902)
- [ ] 7.3 Add class-level `# pylint: disable=too-many-public-methods` to Board class (R0904)
- [ ] 7.3 Add function-level `# pylint: disable=too-many-return-statements` to `get_legal_moves` (line 436) (R0911)
- [ ] 7.4 Add function-level `# pylint: disable=too-many-branches` to method at line 509 (R0912)
- [ ] 7.5 Add `# pylint: disable=protected-access` to lines 51, 117, 365, 398-401 accessing `_square`, `_is_square_attacked`, `_move_validator`, `_move_executor`, `_promotion_validator`, `_en_passant_validator` (W0212)

---

## Task 8: Fix `chess_game/chess/board/en_passant.py` — Too many returns

**File:** `chess_game/chess/board/en_passant.py`
**Warnings:** 1

### Subtasks
- [ ] 8.1 Add function-level `# pylint: disable=too-many-return-statements` to `validate_en_passant_capture` (line 34) (R0911)

---

## Task 9: Fix `chess_game/chess/ai.py` — Too many args/positional-args/locals/branches, max/min builtin

**File:** `chess_game/chess/ai.py`
**Warnings:** 6

### Subtasks
- [ ] 9.1 Replace `if best_score > alpha: alpha = best_score` with `alpha = max(alpha, best_score)` at line 229 (R1731)
- [ ] 9.2 Replace `if best_score < beta: beta = best_score` with `beta = min(beta, best_score)` at line 234 (R1730)
- [ ] 9.3 Add function-level `# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-branches` to minimax function (line 137) (R0913, R0917, R0914, R0912)

---

## Task 10: Fix `chess_game/chess/pieces/piece_movers.py` — Too many returns, too many locals, too few public methods

**File:** `chess_game/chess/pieces/piece_movers.py`
**Warnings:** 3

### Subtasks
- [ ] 10.1 Add class-level `# pylint: disable=too-few-public-methods` to PieceMovers class (R0903)
- [ ] 10.2 Add function-level `# pylint: disable=too-many-return-statements` to `get_valid_moves` (line 22) (R0911)
- [ ] 10.3 Add function-level `# pylint: disable=too-many-locals` to `get_valid_moves` (line 41) (R0914)

---

## Task 11: Fix R0801 — Duplicate code warnings

**Files:** `attack_utils.py` ↔ `move_validation.py`, `en_passant.py` ↔ `move_validation.py`
**Warnings:** 2

### Subtask 11.1: Knight/king attack + _path_is_clear duplication
- [ ] 11.1.1 Investigate whether the `_is_knight_attack`, `_is_king_attack`, and `_path_is_clear` helpers in `move_validation.py` can be consolidated with the equivalents in `attack_utils.py`
- [ ] 11.1.2 If consolidation is feasible, import from `attack_utils.py` in `move_validation.py` and remove local copies
- [ ] 11.1.3 If not feasible, add targeted `# pylint: disable=duplicate-code` to one of the files

### Subtask 11.2: En passant rank check call-site duplication
- [ ] 11.2.1 The `is_valid_ep_rank` call pattern at `en_passant.py:48-56` and `move_validation.py:112-119` is flagged as duplicate
- [ ] 11.2.2 Evaluate wrapping the call+return into a single helper method on `EnPassantValidator` (e.g., `check_ep_rank_valid`)
- [ ] 11.2.3 If wrapping introduces more complexity than it saves, add `# pylint: disable=duplicate-code` to `move_validation.py`

---

## Execution Order

Recommended order (simplest fixes first, building up to complex):

1. **Task 1** — single docstring addition
2. **Task 3** — docstrings + else-after-return (promotion.py)
3. **Task 5** — docstrings, unused import, consider-using-in, elif-after-return (castling.py)
4. **Task 2** — docstrings, unused args, protected access (move_execution.py)
5. **Task 4** — elif-after-return, import placement, too-many-returns (attack_utils.py)
6. **Task 6** — unused import, protected access, elif-after-return, disables (move_validation.py)
7. **Task 8** — too-many-returns disable (en_passant.py)
8. **Task 9** — max/min rewrite + disables (ai.py)
9. **Task 10** — disables (piece_movers.py)
10. **Task 7** — protected access, else-after-return, disables (board.py)
11. **Task 11** — duplicate code investigation (last, may require design decisions)

---

## Verification

After all fixes:
- Run `pylint chess_game/` — target score **10.00/10** (zero warnings)
- Run `mypy chess_game/` — ensure 0 regressions
- Run `black --check chess_game/` — ensure formatting clean
- Run `python -m pytest tests/ -v` — ensure all 189 tests still pass
