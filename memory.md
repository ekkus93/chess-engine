# Chess Engine Project Memory

## Current Status: Phase 9 Complete - AI Module with Type Checking Fixes

### Session ID: 531fe519-d26a-4d2c-a870-ffa34f44987f
### Date: 2026-04-19 (09:53 AM)
### Claude Code Session ID: 531fe519-d26a-4d2c-a870-ffa34f44987f

---

## Recent Work (Phase 9)

**Linter & Type Checking Fix:** Ran ruff and mypy on all files. Fixed multiple issues:

1. **chess_game/chess/ai.py**:
   - Removed unused `Protocol` import from typing
   - Changed type hints from custom `Square` to `tuple[int, int]`
   - Replaced float infinity with integer bounds for alpha-beta pruning
   - Cleaned up duplicate variable definitions and unused imports
   - Fixed union attribute access patterns

2. **chess_game/chess/evaluation.py**:
   - Removed unused `Piece` import from types module

3. **chess_game/main.py**:
   - Removed unused `get_best_move` and `evaluate` imports

4. **tests/**:
   - Removed unused table constants from conftest.py
   - Fixed import order in test_ai.py
   - Added proper move ordering test instead of skeleton with unused vars

**Final Results:**
- ✅ ruff lint: All checks passed on chess_game and tests
- ✅ mypy: No issues found in any source files
- ✅ pytest: 104 tests passed in 0.19s

---

## Project State Summary

### Implementation Complete:
- **Phase 1-3**: Basic chess engine with board representation, move legality rules (checkmate, stalemate, castling, en passant)
- **Phase 4-5**: Game status detection and CLI interface
- **Phase 6-8**: Move parsing and test organization
- **Phase 9**: AI module with minimax, alpha-beta pruning, and piece-square tables

### Files Structure:
```
chess_game/
├── chess/
│   ├── __init__.py
│   ├── board.py      # Board state and move validation
│   ├── types.py      # Color, PieceType enums, Piece dataclass
│   ├── move.py       # Move parsing from algebraic notation
│   ├── evaluation.py # Material values + piece-square tables (not used in final code)
│   └── ai.py         # Minimax with alpha-beta pruning, move ordering
├── main.py           # CLI entry point (no AI integration yet)
└── pyproject.toml    # Project configuration

tests/
├── test_ai.py        # Tests for AI module (20 tests)
├── test_board.py     # Board state and legality tests (34 tests)
├── test_coords.py    # Coordinate conversion tests
├── test_game_status.py # Checkmate/stalemate detection tests
├── test_legality.py  # Piece move legality tests
├── test_piece_moves.py # All piece movement rules (65 tests)
├── test_special_moves.py # Castling, promotion, en passant (12 tests)
└── conftest.py       # Pytest fixtures

pyproject.toml        # Project dependencies and settings
README.md             # Documentation with phases listed
```

### Known Gaps:
1. CLI does not integrate AI yet (`--ai` / `--ai-depth` flags missing in main.py)
2. Piece-square tables implemented but not used (evaluations use only material balance)
3. Transposition table present but currently disabled

---

## Architecture Notes

### Evaluation Module:
- Uses material values: pawn=100, knight=320, bishop=320, rook=500, queen=900
- Piece-square tables exist for pawn/knight/bishop/rook/queen/king but currently unused
- Scores are integer-based (no floats)

### AI Module:
- `evaluate(board)` - Material + positional bias scoring
- `_order_moves()` - Captures > promotions > pawn pushes > normal moves
- Minimax with alpha-beta pruning, depth parameter in plies
- Optional transposition table for position caching

### Test Coverage:
- 104 total tests across all modules
- All board, legality, and game status tests complete
- AI module fully tested (20 tests covering evaluation, move ordering, pruning)

---

## Fix 2 Session (Castling, En Passant, Cleanup)

**Session Date:** 2026-05 (pick up from here later)
**Branch:** `master` (up to date on `origin/master` — all Fix 2 changes merged via `ort` strategy)
**Remote branch `fix2/castling-en-passant-cleanup` deleted from GitHub**

### What Was Done (Fix 2)

- **Task 0 (Baseline):** Established baseline, created branch, added spec/TODO to repo
- **Task 1 (Regression Tests):** Added `test_castling_edge_cases.py` (10 tests) and `test_en_passant_edge_cases.py` (15 tests) — all passing
- **Task 2 (Queenside Castling):** Added `b1`/`b8` check to `CastlingValidator._is_path_clear()` for queenside
- **Task 4 (En Passant Geometry):** Added row-delta check in `EnPassantValidator.validate()` to reject non-one-row diagonal moves
- **Task 6 (Stale Comments):** Full-project search clean — no stale coordinate comments remain
- **Task 7 (BoardState):** Option A chosen — `BoardState` removed from engine code; `test_board_state.py` renamed to `test_board_edge_cases.py`
- **Task 8 (AI Evaluation):** Applied `row = 7 - row` fix for Black in `chess_game/chess/ai.py:84`; starting position evaluates to `0`
- **Task 9.1 (Cache Files):** Removed `__pycache__`, `.pytest_cache` from repo
- **Task 5 (Partial):** Converted `test_en_passant_edge_cases.py` to `sq()` notation (all 15 tests passing)

### What Remains

- **Task 3 (NOT DONE):** Remove castling logic from `PieceMovers._get_king_moves()` (lines 337-356 in `piece_movers.py`), add it in `MoveValidator.get_legal_moves()` so `CastlingValidator` is the sole authority
- **Task 5 (IN PROGRESS):** Convert remaining priority test files to `sq()` notation — ~314 raw coords remain:
  - `test_castling.py` (82), `test_en_passant.py` (66), `test_promotion.py` (63), `test_checkmate.py` (59), `test_check_checkmate_stalemate.py` (45), `test_clone.py` (40), `test_board_setup.py` (19)
- **Task 8.3 (NOT DONE):** Add AI evaluation symmetry tests (starting position = 0, mirrored position symmetric)
- **Task 9.2 (NOT DONE):** Update `.gitignore` — missing: `*.py[cod]`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/`, `venv/`
- **Task 10 (BLOCKED):** Final acceptance blocked on Tasks 3, 5, 8.3, 9.2

### Current Quality Gate Results

| Check | Result |
|-------|--------|
| **Tests** | ✅ 176/176 passed |
| **pylint** | 9.47/10 (only duplicate-code warnings, no errors) |
| **mypy** | 24 pre-existing errors (`ConstantSquare \| None` access, `RowConstant`/`ColConstant` arg types) |
| **black** | Not installed on this system |

### Key Files

- `docs/CHESS_ENGINE_REPAIR_FIX2_TODO.md` — Authoritative task list and status
- `docs/CHESS_ENGINE_REPAIR_FIX2_SPEC.md` — Task specifications
- `chess_game/chess/pieces/piece_movers.py` — Lines 337-356 have castling logic to remove (Task 3)
- `chess_game/chess/board/move_validation.py` — Where castling moves should be added (Task 3)
- `chess_game/chess/board/castling.py` — `CastlingValidator` — sole castling authority once Task 3 done
- `chess_game/chess/ai.py` — Line 84 has `row = 7 - row` fix; needs symmetry tests (Task 8.3)
- `tests/helpers.py` — Contains `sq()`, `assert_piece()`, `assert_empty()` helpers
- `.gitignore` — Missing cache directory entries (Task 9.2)

### Important Notes

- Coordinate system: row 0 = rank 8, row 7 = rank 1; col 0 = file a
- Manual conversion preferred over subagent (subagent previously introduced bugs in `test_en_passant_edge_cases.py`)
- `black` formatter not installed; use `pylint` for linting
- `.gitignore` currently only has `__pycache__/` — needs all cache entries added
- mpy errors are pre-existing and unrelated to Fix 2 work

---

*Memory last updated: 2026-05-14*
