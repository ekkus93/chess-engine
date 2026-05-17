# Chess Engine Promotion Cleanup TODO

## Goal

Perform a focused cleanup of promotion validation and repository hygiene after the BIG_FIX1 patch.

The engine currently passes the suite and the main behavior works, but there are still promotion-maintainability and validator-level correctness issues:

- allowed promotion piece lists are duplicated;
- `PromotionValidator.is_valid_promotion_piece(5)` can return `True` because `PieceType` is an `IntEnum`;
- promotion rank validation is not fully color-specific inside the promotion validator;
- stale queen-only helper code still exists in `MoveValidator`;
- generated cache files are still present in the repo/archive.

Do not broaden this patch into new chess features or a move-engine rewrite.

---

## Implementation rules

- Treat `CHESS_ENGINE_PROMOTION_CLEANUP_SPEC.md` as the contract.
- Keep the canonical coordinate system unchanged:

  ```text
  row 0 = rank 8
  row 7 = rank 1
  White promotion rank = row 0
  Black promotion rank = row 7
  ```

- Do not change legal-move tuple shape.
- Do not change public promotion behavior except to reject invalid inputs more consistently.
- Keep default queen promotion for direct `make_move(..., promotion=None)` when a pawn legally reaches the promotion rank.
- Do not weaken existing tests.
- Do not add unrelated AI/GUI/UCI/FEN/PGN work.
- Run the full test suite after each major task group:

  ```bash
  python -m pytest tests -q
  ```

---

## Task 0: Establish baseline

### 0.1 Run the current suite

- [x] From repo root, run:

  ```bash
  python -m pytest tests -q
  ```

- [x] Expected baseline from the latest reviewed repo:

  ```text
  273 passed
  ```

- [x] If the suite is failing before this cleanup starts, stop and inspect the failures before making changes.

### 0.2 Create a focused branch

- [x] Create a branch such as:

  ```bash
  git checkout -b fix/promotion-validator-cleanup
  ```

### 0.3 Add handoff docs

- [x] Copy the spec into:

  ```text
  docs/CHESS_ENGINE_PROMOTION_CLEANUP_SPEC.md
  ```

- [x] Copy this TODO into:

  ```text
  docs/CHESS_ENGINE_PROMOTION_CLEANUP_TODO.md
  ```

---

## Task 1: Inspect current promotion code

### 1.1 Inspect promotion validator

- [x] Open:

  ```text
  chess_game/chess/board/promotion.py
  ```

- [x] Locate:
  - [x] `get_promotion_options(...)`
  - [x] `is_valid_promotion_piece(...)`
  - [x] `is_valid_promotion_choice(...)`
  - [x] promotion-rank helper methods, if present.

- [x] Confirm whether promotion pieces are currently listed inline instead of via one shared constant.

### 1.2 Inspect legal move generation

- [x] Open:

  ```text
  chess_game/chess/board/move_validation.py
  ```

- [x] Locate promotion expansion logic in legal move generation.
- [x] Confirm it generates queen, rook, bishop, and knight.
- [x] Identify where it currently duplicates the promotion piece tuple/list.

### 1.3 Search for stale queen-only helper code

- [x] Run:

  ```bash
  grep -R "_get_promotion_piece" -n chess_game tests
  ```

- [x] Determine whether `MoveValidator._get_promotion_piece()` is used.
- [x] If it is unused, plan to remove it.
- [x] If it is used, plan to rewrite it so it cannot hardcode queen-only legal move generation.

### 1.4 Search all promotion-piece list duplication

- [x] Run:

  ```bash
  grep -R "PieceType.QUEEN" -n chess_game tests | grep -E "PROMOTION|promotion|ROOK|BISHOP|KNIGHT|promotion.py|move_validation.py"
  ```

- [x] Identify production-code sites where the allowed promotion list is duplicated.
- [x] Do not worry about tests that explicitly list expected promotion choices.

---

## Task 2: Add canonical `PROMOTION_PIECES`

### 2.1 Define the constant

- [x] In:

  ```text
  chess_game/chess/board/promotion.py
  ```

  add:

  ```python
  PROMOTION_PIECES = (
      PieceType.QUEEN,
      PieceType.ROOK,
      PieceType.BISHOP,
      PieceType.KNIGHT,
  )
  ```

- [x] Put it near the top of the module after imports.
- [x] Use a tuple to avoid accidental mutation.

### 2.2 Use it in promotion validator

- [x] Update `get_promotion_options(...)` to return or derive from `PROMOTION_PIECES`.

  Acceptable shape:

  ```python
  def get_promotion_options(self, piece: Piece) -> list[PieceType]:
      if piece.kind != PieceType.PAWN:
          return []
      return list(PROMOTION_PIECES)
  ```

- [x] Update `is_valid_promotion_piece(...)` to use `PROMOTION_PIECES`.
- [x] Update `is_valid_promotion_choice(...)` to use `is_valid_promotion_piece(...)` rather than duplicating allowed choices.

### 2.3 Use it in move generation

- [x] In `move_validation.py`, import `PROMOTION_PIECES` from `promotion.py`.
- [x] Replace any local tuple/list of promotion pieces with `PROMOTION_PIECES`.
- [x] Ensure legal move generation still emits all four promotion choices.

### 2.4 Verify no production duplication remains

- [x] Re-run the search from Task 1.4.
- [x] Confirm production code no longer has duplicated allowed-promotion lists.
- [x] It is okay for tests to define an expected set of promotion pieces.

---

## Task 3: Harden `is_valid_promotion_piece(...)`

## Problem

`PieceType` is an `IntEnum`, so raw integers can compare equal to enum values. This means a helper like:

```python
piece_type in [PieceType.QUEEN, PieceType.ROOK]
```

can incorrectly accept `5` if `PieceType.QUEEN == 5`.

### 3.1 Update implementation

- [x] Change `PromotionValidator.is_valid_promotion_piece(...)` so it explicitly requires a real `PieceType` instance.

Recommended implementation:

```python
def is_valid_promotion_piece(self, piece_type: object) -> bool:
    return isinstance(piece_type, PieceType) and piece_type in PROMOTION_PIECES
```

- [x] The parameter type may be broadened from `PieceType` to `object` because this method is intentionally validating runtime inputs.
- [x] Do not rely on membership alone.

### 3.2 Add validator tests

Add tests in an appropriate file, for example:

```text
tests/test_promotion.py
```

or a new focused file:

```text
tests/test_promotion_validation.py
```

- [x] Test these valid values return `True`:
  - [x] `PieceType.QUEEN`
  - [x] `PieceType.ROOK`
  - [x] `PieceType.BISHOP`
  - [x] `PieceType.KNIGHT`

- [x] Test these invalid values return `False`:
  - [x] `PieceType.KING`
  - [x] `PieceType.PAWN`
  - [x] `PieceType.EMPTY`
  - [x] raw integer `5`
  - [x] raw string `"q"`
  - [x] `None`
  - [x] arbitrary object, if desired.

Example:

```python
def test_is_valid_promotion_piece_rejects_raw_int():
    board = Board()
    validator = PromotionValidator(board)
    assert validator.is_valid_promotion_piece(5) is False
```

### 3.3 Run tests

- [x] Run:

  ```bash
  python -m pytest tests -q
  ```

---

## Task 4: Make promotion-rank validation color-specific

## Problem

The promotion choice validator should not merely accept destination rows `{0, 7}`. It should enforce the correct promotion rank for the pawn's color:

```text
White pawn -> row 0 only
Black pawn -> row 7 only
```

### 4.1 Add or reuse a promotion-rank helper

- [x] In `promotion.py`, add or reuse a helper with this behavior:

```python
def is_promotion_rank(self, piece: Piece, end_pos: ConstantSquare) -> bool:
    if piece.kind != PieceType.PAWN:
        return False
    if piece.color == Color.WHITE:
        return int(end_pos.row) == 0
    return int(end_pos.row) == 7
```

- [x] If a helper already exists, verify it behaves exactly this way.

### 4.2 Update `is_valid_promotion_choice(...)`

- [x] Ensure `promotion is None` still returns `True`.
- [x] If `promotion is not None`, require:
  - [x] valid promotion piece using `is_valid_promotion_piece(...)`;
  - [x] moving piece is a pawn;
  - [x] destination is the correct color-specific promotion rank using `is_promotion_rank(...)`.

Recommended behavior:

```python
def is_valid_promotion_choice(self, piece: Piece, end_pos: ConstantSquare, promotion: object | None) -> bool:
    if promotion is None:
        return True
    if not self.is_valid_promotion_piece(promotion):
        return False
    if piece.kind != PieceType.PAWN:
        return False
    return self.is_promotion_rank(piece, end_pos)
```

### 4.3 Add color-specific tests

Add direct validator tests:

- [x] White pawn on/for row `0` with `PieceType.QUEEN` is valid.
- [x] White pawn targeting row `7` with `PieceType.QUEEN` is invalid.
- [x] Black pawn on/for row `7` with `PieceType.QUEEN` is valid.
- [x] Black pawn targeting row `0` with `PieceType.QUEEN` is invalid.

Use algebraic helpers where possible:

```python
white_pawn = create_piece(Color.WHITE, PieceType.PAWN)
black_pawn = create_piece(Color.BLACK, PieceType.PAWN)

assert validator.is_valid_promotion_choice(white_pawn, sq("e8"), PieceType.QUEEN) is True
assert validator.is_valid_promotion_choice(white_pawn, sq("e1"), PieceType.QUEEN) is False
assert validator.is_valid_promotion_choice(black_pawn, sq("e1"), PieceType.QUEEN) is True
assert validator.is_valid_promotion_choice(black_pawn, sq("e8"), PieceType.QUEEN) is False
```

### 4.4 Preserve default queen public behavior

- [x] Confirm existing tests still pass for direct default queen promotion:

```python
board.make_move(sq("e7"), sq("e8"), promotion=None)
```

- [x] Confirm valid explicit underpromotion still works:

```python
board.make_move(sq("e7"), sq("e8"), promotion=PieceType.ROOK)
```

---

## Task 5: Remove or repair stale `_get_promotion_piece()`

### 5.1 Determine usage

- [x] Run:

  ```bash
  grep -R "_get_promotion_piece" -n chess_game tests
  ```

### 5.2 Remove if unused

- [x] If the only result is the method definition itself, delete the method.
- [x] Re-run the test suite.

### 5.3 Repair if used

If there are callers:

- [x] Do not leave a helper that hardcodes queen-only legal move generation.
- [x] Rename or rewrite the helper so its purpose is clear.
- [x] If the helper is only for default queen execution, move that logic to promotion execution or validator code where default behavior belongs.
- [x] Legal move generation must continue to use `PROMOTION_PIECES` and emit all four choices.

### 5.4 Verify no queen-only generation remains

- [x] Search for suspicious patterns:

  ```bash
  grep -R "return PieceType.QUEEN" -n chess_game/chess
  ```

- [x] Any remaining `return PieceType.QUEEN` must be clearly related to default queen promotion during execution, not legal move generation.

---

## Task 6: Add regression tests for legal move generation still using all promotions

This is mostly to ensure the cleanup does not accidentally regress the already-fixed behavior.

### 6.1 Reuse existing tests if present

- [x] Locate existing promotion move generation tests.
- [x] If they already cover all cases below, do not duplicate unnecessarily.

### 6.2 Required behavior to preserve

Ensure tests cover:

- [x] White quiet promotion generates exactly:
  - [x] queen
  - [x] rook
  - [x] bishop
  - [x] knight

- [x] White capture promotion generates exactly the four choices.
- [x] Black quiet promotion generates exactly the four choices.
- [x] Black capture promotion generates exactly the four choices.
- [x] No duplicate identical promotion moves.

### 6.3 Run focused tests

- [x] Run promotion tests, for example:

  ```bash
  python -m pytest tests/test_promotion.py tests/test_promotion_move_generation.py -q
  ```

- [x] Adjust command to match actual test file names.

---

## Task 7: Remove generated cache files and harden `.gitignore`

### 7.1 Inspect generated artifacts

- [x] From repo root, run:

  ```bash
  find . \( -type d -name "__pycache__" -o -type d -name ".pytest_cache" -o -type f -name "*.pyc" \) -print
  ```

### 7.2 Remove generated artifacts

- [x] Remove these from the working tree:

  ```bash
  find . -type d -name "__pycache__" -prune -exec rm -rf {} +
  find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
  find . -type f -name "*.pyc" -delete
  ```

- [x] Do not delete source files.

### 7.3 Update `.gitignore`

- [x] Open `.gitignore`.
- [x] Ensure it contains:

  ```gitignore
  __pycache__/
  *.py[cod]
  .pytest_cache/
  ```

- [x] Add those entries if missing.

### 7.4 Verify cleanup

- [x] Re-run:

  ```bash
  find . \( -type d -name "__pycache__" -o -type d -name ".pytest_cache" -o -type f -name "*.pyc" \) -print
  ```

- [x] It should print nothing from the tracked working tree.

---

## Task 8: Full verification

### 8.1 Run focused promotion tests

- [x] Run:

  ```bash
  python -m pytest tests -q -k promotion
  ```

- [x] All promotion-related tests must pass.

### 8.2 Run Board API tests

- [x] Run:

  ```bash
  python -m pytest tests/test_board_api.py -q
  ```

- [x] All Board API tests must pass.

### 8.3 Run full suite

- [x] Run:

  ```bash
  python -m pytest tests -q
  ```

- [x] Expected result: all tests pass.
- [x] Final count should be at least:

  ```text
  273 passed
  ```

  plus any new tests added by this cleanup.

### 8.4 Search for promotion duplication and cache files

- [x] Confirm production code uses canonical `PROMOTION_PIECES`.
- [x] Confirm no generated cache files remain.

---

## Task 9: Final acceptance checklist

The patch is complete only when all items are true:

- [x] `PROMOTION_PIECES` exists in one canonical production module.
- [x] `get_promotion_options(...)` uses `PROMOTION_PIECES`.
- [x] `is_valid_promotion_piece(...)` uses `PROMOTION_PIECES` and rejects raw integers.
- [x] `is_valid_promotion_piece(5)` returns `False`.
- [x] `is_valid_promotion_piece("q")` returns `False`.
- [x] `is_valid_promotion_piece(PieceType.KING)` returns `False`.
- [x] `is_valid_promotion_piece(PieceType.PAWN)` returns `False`.
- [x] `is_valid_promotion_piece(PieceType.EMPTY)` returns `False`.
- [x] `is_valid_promotion_choice(...)` enforces white row `0` and black row `7`.
- [x] Legal move generation still emits all four promotion choices for both colors and capture/quiet promotions.
- [x] Direct default queen promotion still works.
- [x] Explicit rook/bishop/knight underpromotion still works.
- [x] Stale queen-only `_get_promotion_piece()` code is removed or made harmless.
- [x] `__pycache__/`, `*.pyc`, and `.pytest_cache/` files are removed.
- [x] `.gitignore` covers Python/cache artifacts.
- [x] Full suite passes.

---

## Suggested commit breakdown

Use small commits:

1. `test: cover promotion validator runtime input validation`
2. `fix: centralize promotion pieces and harden validation`
3. `fix: enforce color-specific promotion ranks`
4. `refactor: remove stale queen-only promotion helper`
5. `chore: remove python cache artifacts and update gitignore`

Combining the test and fix commits is also fine:

1. `fix: harden promotion validator cleanup`
2. `chore: remove generated cache artifacts`

Do not use a giant unrelated commit that mixes this cleanup with AI, GUI, or move-engine redesign work.

---

## Final instruction for OpenCode/Copilot

This is a cleanup pass, not a new feature pass.

Make the smallest clean changes that satisfy the spec. Preserve existing behavior unless this TODO explicitly says to tighten invalid-input handling. Full test suite must pass before marking the task complete.
