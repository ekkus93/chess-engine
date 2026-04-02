# REFACTOR_BOARD_TODO.md

## Executive Summary

`chess_game/chess/board.py` (1109 lines, 44 methods) is a monolithic "god class" that violates the Single Responsibility Principle. This has led to:
- 18 failing unit tests (black pawn moves, promotion, en passant)
- Hard to test individual components
- Difficult to fix bugs without breaking other functionality
- Poor maintainability

**Goal**: Refactor into modular, testable components that can be verified independently.

---

## Current State Analysis

### Metrics
- **Lines of Code**: 1109
- **Methods**: 44
- **Average Lines per Method**: 25.2
- **Cyclomatic Complexity**: High (single class handles everything)

### Code Smells
1. **God Class**: Board class does data management, move validation, move execution, special rules, AND UI (display method)
2. **Long Method**: Multiple methods exceed 50 lines
3. **Tight Coupling**: No interfaces or abstractions
4. **Mixed Responsibilities**: Validation logic mixed with execution logic
5. **No Separation of Concerns**: All chess logic in one file

### Current Test Failures (18 failing)
All in `tests/test_special_moves.py`:

| Test | Category | Issue |
|------|----------|-------|
| test_black_en_passant_legal_example | Black pawn 2-step | Coordinate bug (ROW_7 vs ROW_8) |
| test_en_passant_expires_after_one_turn | En passant expiration | Coord system issue |
| test_en_passant_cannot_be_used_if_it_leaves_own_king_in_check | En passant + check | Coord system issue |
| test_white_promotion_to_queen | White promotion | Promotion logic bug |
| test_white_promotion_to_knight | White promotion | Promotion logic bug |
| test_default_promotion_is_queen_when_unspecified | Default promotion | Promotion logic bug |
| test_parse_move_notation_supports_promotion_choice | Promotion parsing | Promotion logic bug |
| test_en_passant_white_captures_black_pawn | En passant capture | Coord system issue |
| test_en_passant_expires_after_non_pawn_move | En passant expiration | Coord system issue |
| test_en_passant_cannot_capture_own_pawn | En passant validation | Coord system issue |
| test_en_passant_expires_after_white_move | En passant expiration | Coord system issue |
| test_promotion_to_rook | Promotion | Promotion logic bug |
| test_promotion_to_bishop | Promotion | Promotion logic bug |
| test_promotion_to_knight | Promotion | Promotion logic bug |
| test_promotion_from_rank_7_forced | Promotion validation | Promotion logic bug |
| test_checkmate_with_promotion | Checkmate + promotion | Coord + promotion bug |
| test_edge_rank_pawn_promotion_scenarios | Edge case promotion | Promotion logic bug |
| test_multiple_en_passant_in_game | Multiple en passant | Coord system issue |

### Root Cause Analysis
- **Primary Bug**: Line 537 checks `start_row == int(ROW_7)` for black pawn 2-step moves, but black pawns start on rank 8 (ROW_8)
- **Secondary Issues**: Coordinate system confusion between rank numbers and array indices
- **Tertiary Issues**: Promotion logic doesn't handle all edge cases

---

## Refactoring Goals

1. **Reduce Complexity**: Split 1109 lines into ~1000 lines across 8-10 focused files
2. **Improve Testability**: Each component testable in isolation
3. **Fix Bugs Systematically**: Isolate bugs to specific modules
4. **Maintain Backward Compatibility**: Preserve public API for existing tests
5. **Follow SOLID Principles**:
   - Single Responsibility
   - Open/Closed
   - Liskov Substitution
   - Interface Segregation
   - Dependency Inversion

---

## Proposed File Structure

```
chess_game/
├── chess/
│   ├── __init__.py
│   ├── board/
│   │   ├── __init__.py
│   │   ├── board.py                    # Main Board class (~200 lines)
│   │   ├── board_state.py              # Data structure (~100 lines)
│   │   ├── move_validation.py          # Validation logic (~250 lines)
│   │   ├── move_execution.py           # Move execution (~150 lines)
│   │   ├── castling.py                 # Castling logic (~100 lines)
│   │   └── en_passant.py               # En passant logic (~80 lines)
│   ├── pieces/
│   │   ├── __init__.py
│   │   ├── piece.py                    # Piece data class (~50 lines)
│   │   └── piece_movers.py             # Per-piece validation (~200 lines)
│   └── constants/
│       ├── __init__.py
│       └── constants.py                # ROW_1, ROW_8, COL_A, etc.
├── tests/
│   ├── test_board.py                   # Board integration tests
│   ├── test_board_state.py             # Data structure tests
│   ├── test_move_validation.py         # Validation tests
│   ├── test_move_execution.py          # Execution tests
│   ├── test_castling.py                # Castling tests
│   ├── test_en_passant.py              # En passant tests
│   └── test_pieces.py                  # Piece tests
└── docs/
    ├── REFACTOR_BOARD_TODO.md          # This file
    ├── REFACTOR_PROGRESS.md            # Track progress
    └── coordinate_system.md            # Reference
```

---

## Phase-by-Phase Plan

### Phase 1: Extract Data Structures (Week 1)
**Goal**: Create pure data classes without behavior

**Files to Create:**
- `chess_game/chess/board/board_state.py`

**Tasks:**
- [ ] Create `BoardState` data class
  - 8x8 board array (List[List[Optional[Piece]]])
  - turn: Color
  - en_passant_target: Optional[Square]
  - castling_rights: Dict[str, bool] (white_kingside, white_queenside, black_kingside, black_queenside)
- [ ] Create `CastlingRights` data class
- [ ] Extract all data access methods from Board
  - `get_piece()`
  - `set_piece()`
  - `clear_square()`
  - `is_empty()`
  - `get_color_at()`
  - `get_piece_type_at()`
- [ ] Move `is_in_check()`, `is_checkmate()`, `is_stalemate()` to BoardState
- [ ] Tests needed:
  - [ ] Test BoardState initialization
  - [ ] Test piece access methods
  - [ ] Test board state immutability
  - [ ] Test turn switching
  - [ ] Test en passant target
  - [ ] Test castling rights

**Acceptance Criteria:**
- BoardState is a pure data class (no methods except setters)
- Board class has ~50% fewer lines
- All existing tests still pass

---

### Phase 2: Extract Move Validation (Week 2)
**Goal**: Separate validation logic from Board class

**Files to Create:**
- `chess_game/chess/board/move_validation.py`
- `chess_game/chess/board/path_validator.py`
- `chess_game/chess/pieces/piece_movers.py`

**Tasks:**
- [ ] Create `PathValidator` class
  - `_path_is_clear()` method
  - `_is_piece_between()` helper
- [ ] Create `PieceValidator` class
  - `validate_rook_move()`
  - `validate_bishop_move()`
  - `validate_queen_move()`
  - `validate_knight_move()`
  - `validate_king_move()`
  - `validate_pawn_move()` (CRITICAL - contains the bug)
- [ ] Extract `_is_castling_move()` to `castling.py`
- [ ] Extract `_can_castle()` to `castling.py`
- [ ] Extract `_is_piece_pinned()` to `move_validation.py`
- [ ] Tests needed:
  - [ ] Test path validation for all directions
  - [ ] Test piece-specific validation
  - [ ] Test pawn forward moves (white & black)
  - [ ] Test pawn 2-step moves (white & black) - **FIX THE BUG HERE**
  - [ ] Test pawn captures
  - [ ] Test promotion detection

**Acceptance Criteria:**
- PathValidator works independently of Board
- PieceValidators can be tested in isolation
- Black pawn 2-step bug is fixed

---

### Phase 3: Extract Move Execution (Week 3)
**Goal**: Separate move execution from validation

**Files to Create:**
- `chess_game/chess/board/move_execution.py`

**Tasks:**
- [ ] Create `MoveExecutor` class
  - `_apply_move_unchecked()`
  - En passant capture logic
  - Castling rook movement
  - Pawn promotion
- [ ] Extract `_clear_castling_right_for_captured_rook()` to `castling.py`
- [ ] Extract `_update_castling_rights_for_move()` to `castling.py`
- [ ] Tests needed:
  - [ ] Test basic move execution
  - [ ] Test en passant capture execution
  - [ ] Test castling execution
  - [ ] Test promotion execution
  - [ ] Test castling rights updates

**Acceptance Criteria:**
- MoveExecutor applies moves without validation
- Castling rights correctly updated
- En passant target cleared

---

### Phase 4: Extract Special Rules (Week 4)
**Goal**: Create domain-specific rule engines

**Files to Create:**
- `chess_game/chess/board/castling.py`
- `chess_game/chess/board/en_passant.py`
- `chess_game/chess/board/promotion.py`

**Tasks:**
- [ ] Create `CastlingValidator` class
  - `_rook_at_original_square()`
  - `_is_castling_move()`
  - `_can_castle()`
  - Castling path validation
- [ ] Create `EnPassantValidator` class
  - `set_en_passant_target()`
  - `validate_en_passant_capture()`
  - En passant expiration logic
- [ ] Create `PromotionValidator` class
  - `_promotion_options_for_move()`
  - `_is_valid_promotion_choice()`
  - Promotion rank detection
- [ ] Tests needed:
  - [ ] Test castling validation
  - [ ] Test en passant validation
  - [ ] Test promotion validation

**Acceptance Criteria:**
- All special rules in dedicated classes
- Can be tested independently
- Black pawn en passant bug fixed

---

### Phase 5: Refactor Main Board Class (Week 5)
**Goal**: Board becomes orchestrator/coordinator

**Tasks:**
- [ ] Board class now only has:
  - `__init__()` - Initialize components
  - `get_legal_moves()` - Orchestrate move discovery
  - `make_move()` - Orchestrate move execution
  - `is_in_check()`, `is_checkmate()`, `is_stalemate()` - Game state
  - `clone()` - Deep copy
- [ ] Remove all validation logic (delegated)
- [ ] Remove all execution logic (delegated)
- [ ] Remove all special rule logic (delegated)
- [ ] Keep only coordination/orchestration code
- [ ] Tests needed:
  - [ ] Test Board integration
  - [ ] Test all special cases work together

**Acceptance Criteria:**
- Board class is ~200 lines (from 1109)
- Board only calls other classes, doesn't contain logic
- All 18 failing tests pass

---

### Phase 6: Create Comprehensive Test Suite (Week 6)
**Goal**: Full test coverage for all components

**Files to Create:**
- `tests/test_board_state.py` - Data structure tests
- `tests/test_path_validator.py` - Path validation tests
- `tests/test_piece_movers.py` - Piece movement tests
- `tests/test_castling.py` - Castling tests
- `tests/test_en_passant.py` - En passant tests
- `tests/test_promotion.py` - Promotion tests
- `tests/test_move_execution.py` - Execution tests
- `tests/test_board_integration.py` - Integration tests

**Tasks:**
- [ ] Write 100+ unit tests total
- [ ] Each component has dedicated test file
- [ ] Edge cases covered
- [ ] Black pawn bugs fixed and verified
- [ ] All 18 previously failing tests pass

**Acceptance Criteria:**
- 95%+ code coverage
- All tests pass
- No test duplication

---

### Phase 7: Fix Identified Bugs (Week 7)
**Goal**: Systematically fix all 18 failing tests

**Known Bugs:**
1. **Line 537**: `start_row == int(ROW_7)` should be `start_row == int(ROW_8)` for black 2-step
2. **Coordinate confusion**: ROW_7 = rank 7 = array row 6, ROW_8 = rank 8 = array row 7
3. **Promotion rank detection**: May not handle all edge cases
4. **En passant validation**: May use incorrect coordinates

**Tasks:**
- [ ] Fix black pawn 2-step validation (castling.py or piece_movers.py)
- [ ] Fix promotion rank detection (promotion.py)
- [ ] Fix en passant target setting (en_passant.py)
- [ ] Fix any other coordinate bugs found
- [ ] Verify all 18 tests pass

**Acceptance Criteria:**
- All 18 tests pass
- No new bugs introduced
- Tests are stable

---

### Phase 8: Verification & Cleanup (Week 8)
**Goal**: Final verification and cleanup

**Tasks:**
- [ ] Run full test suite
- [ ] Remove any unused code
- [ ] Update documentation
- [ ] Add docstrings to all new classes
- [ ] Run linters (pylint, black, mypy)
- [ ] Performance testing
- [ ] Documentation review

**Acceptance Criteria:**
- All tests pass
- Code is linted
- Documentation is complete
- Ready for production

---

## Testing Strategy

### Per-Phase Testing
1. **Unit Tests**: Test each class in isolation
2. **Integration Tests**: Test component interactions
3. **Regression Tests**: Ensure existing tests still pass
4. **Edge Case Tests**: Boundary conditions, error cases

### Testing Tools
- `pytest` - Main testing framework
- `pytest-cov` - Code coverage
- `black` - Code formatting
- `mypy` - Type checking
- `pylint` - Static analysis

### Test Naming Convention
```python
test_<component>_<feature>_<scenario>()
# Examples:
# test_board_state_initialization()
# test_piece_movers_black_pawn_two_step_from_start()
# test_castling_black_kingside_valid()
# test_en_passant_white_captures_black_pawn()
```

---

## Risk Assessment

### High Risks
1. **Breaking Changes**: Existing tests may fail during refactoring
   - **Mitigation**: Preserve public API, add integration tests

2. **Logic Errors**: Refactoring may introduce subtle bugs
   - **Mitigation**: Test each phase thoroughly before moving on

3. **Performance**: More objects = more overhead
   - **Mitigation**: Benchmark after refactoring

### Medium Risks
1. **Time Overruns**: Refactoring takes longer than expected
   - **Mitigation**: Build incrementally, verify each phase

2. **Missing Test Coverage**: Edge cases not covered
   - **Mitigation**: Write tests before implementation (TDD)

### Low Risks
1. **Code Complexity**: New architecture may be confusing
   - **Mitigation**: Clear documentation, consistent naming

2. **File Organization**: Choosing wrong structure
   - **Mitigation**: Follow established Python patterns

---

## Success Metrics

### Code Quality
- [ ] Board.py reduced from 1109 to <300 lines
- [ ] Cyclomatic complexity reduced by 50%+
- [ ] No method exceeds 50 lines
- [ ] All modules have < 300 lines

### Test Coverage
- [ ] 95%+ code coverage
- [ ] 100+ unit tests
- [ ] All 18 previously failing tests pass
- [ ] No test duplication

### Maintainability
- [ ] Single Responsibility Principle followed
- [ ] Each module has clear purpose
- [ ] Easy to add new features
- [ ] Easy to fix bugs

---

## Dependencies

### External
- Python 3.10+
- pytest >= 7.0
- pytest-cov >= 4.0
- black >= 23.0
- mypy >= 1.0
- pylint >= 2.0

### Internal
- `docs/coordinate_system.md` - Reference for coordinate system
- `docs/en_passant.md` - En passant rules
- `docs/init_board_position.md` - Starting position reference

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1 | Week 1 | Data structures, ~50% smaller Board class |
| 2 | Week 2 | Move validation, black pawn bug fixed |
| 3 | Week 3 | Move execution, castling rights |
| 4 | Week 4 | Special rules engines |
| 5 | Week 5 | Board as orchestrator, ~200 lines |
| 6 | Week 6 | Comprehensive test suite |
| 7 | Week 7 | All 18 bugs fixed |
| 8 | Week 8 | Final verification, cleanup |

**Total Estimated Time**: 8 weeks

---

## Rollback Plan

If a phase fails:
1. Don't proceed to next phase
2. Debug current phase thoroughly
3. If needed, revert to last good state
4. Document what went wrong
5. Adjust approach for next attempt

---

## Next Steps

1. **Start Phase 1**: Extract data structures
2. **Create tests** before implementing new code
3. **Verify** each phase before moving on
4. **Track progress** in `docs/REFACTOR_PROGRESS.md`

---

## Links

- **Main file to refactor**: `chess_game/chess/board.py` (1109 lines)
- **Failing tests**: `tests/test_special_moves.py` (18 tests)
- **Coordinate reference**: `docs/coordinate_system.md`
- **En passant rules**: `docs/en_passant.md`
- **Board initialization**: `docs/init_board_position.md`

---

**Last Updated**: 2026-04-01
**Status**: Ready to begin Phase 1