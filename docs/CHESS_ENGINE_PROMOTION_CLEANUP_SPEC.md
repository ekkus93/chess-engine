# Chess Engine Promotion Cleanup Spec

## Purpose

This spec defines a focused cleanup pass for the chess engine's promotion-related code and repository hygiene.

The current engine has a strong passing test suite and the major promotion behavior is functionally repaired:

- legal move generation emits queen, rook, bishop, and knight promotion choices;
- invalid public promotion inputs such as raw integers are rejected through `Board.make_move(...)`;
- non-pawn promotion suffixes are rejected;
- AI move ordering preserves promotion identity.

However, the implementation still has maintainability and validator-level correctness issues:

1. Promotion piece lists are duplicated instead of centralized.
2. `PromotionValidator.is_valid_promotion_piece(5)` can still return `True` because `PieceType` is an `IntEnum`.
3. Promotion-rank validation is not color-specific inside the promotion validator.
4. `MoveValidator._get_promotion_piece()` appears stale/dead and still reflects the old queen-only legal-move bug.
5. Generated cache files such as `__pycache__/`, `*.pyc`, and `.pytest_cache/` are present in the repo/archive.

This pass must fix those issues without broadening scope.

## Scope

### In scope

- Centralize allowed promotion pieces in one canonical constant.
- Reuse that canonical promotion list everywhere promotion options are needed.
- Harden promotion-piece validation so only real `PieceType` enum members are accepted.
- Make promotion-rank validation color-specific.
- Remove or repair stale queen-only promotion helper code.
- Add targeted tests for the validator edge cases.
- Remove generated Python/cache artifacts from the repository tree.
- Ensure `.gitignore` prevents these artifacts from returning.
- Run the full test suite.

### Out of scope

Do **not** do any of the following in this cleanup pass:

- redesign the move engine;
- introduce `MoveKind` / `ValidatedMove` unless an existing test exposes a direct need;
- change the canonical coordinate system;
- change public legal-move tuple shape;
- change AI search quality or evaluation behavior;
- add GUI, UCI, PGN, FEN, or networking support;
- rewrite existing tests unrelated to promotion cleanup;
- weaken tests to make the patch pass.

## Current expected baseline

Before making changes, the current expected suite result is approximately:

```bash
python -m pytest tests -q
```

```text
273 passed
```

If the suite is already failing before this cleanup starts, stop and inspect those failures first. Do not mix pre-existing failures with this cleanup patch.

## Canonical coordinate system

Do not alter the coordinate convention:

```text
row 0 = rank 8
row 7 = rank 1
White promotion rank = row 0
Black promotion rank = row 7
```

## Promotion model

### Allowed promotion pieces

The only legal promotion targets are:

```python
PieceType.QUEEN
PieceType.ROOK
PieceType.BISHOP
PieceType.KNIGHT
```

A single canonical constant must define this set/list/tuple. Recommended name:

```python
PROMOTION_PIECES = (
    PieceType.QUEEN,
    PieceType.ROOK,
    PieceType.BISHOP,
    PieceType.KNIGHT,
)
```

Recommended home:

```text
chess_game/chess/board/promotion.py
```

Then import/reuse it from move generation code rather than duplicating the list.

### Type safety requirement

Because `PieceType` is an `IntEnum`, raw integers can compare equal to enum values. The validator must not rely only on membership tests.

This must be rejected:

```python
PromotionValidator(board).is_valid_promotion_piece(5)  # must be False
```

This must also be rejected:

```python
PromotionValidator(board).is_valid_promotion_piece("q")  # must be False
PromotionValidator(board).is_valid_promotion_piece(None)  # must be False for this helper
```

Only actual `PieceType` values from `PROMOTION_PIECES` are valid.

Correct shape:

```python
def is_valid_promotion_piece(self, piece_type: object) -> bool:
    return isinstance(piece_type, PieceType) and piece_type in PROMOTION_PIECES
```

The parameter can remain annotated as `PieceType` if desired, but tests should still verify runtime behavior against bad inputs because this engine is used dynamically.

### Promotion choice validation

`PromotionValidator.is_valid_promotion_choice(piece, end_pos, promotion)` should follow this behavior:

1. If `promotion is None`, return `True`.
   - Direct `make_move(..., promotion=None)` must still allow default queen promotion when a pawn legally reaches the promotion rank.
   - Non-promotion pawn moves and normal non-pawn moves with `promotion=None` must still work.

2. If `promotion is not None`, require all of the following:
   - `promotion` is a real `PieceType` value;
   - `promotion` is one of `PROMOTION_PIECES`;
   - the moving piece is a pawn;
   - the destination is that pawn color's promotion rank.

3. Promotion rank must be color-specific:
   - White pawn: destination row must be `0`.
   - Black pawn: destination row must be `7`.

Do not merely accept `end_pos.row in {0, 7}` inside the validator.

### Default queen promotion

Keep existing public behavior:

- If a pawn legally reaches its promotion rank and `promotion=None`, it promotes to queen by default.
- If a legal underpromotion is explicitly requested with `PieceType.ROOK`, `PieceType.BISHOP`, or `PieceType.KNIGHT`, the resulting piece must have that exact `PieceType`.

### Legal move generation

Do not regress current behavior. `Board.get_legal_moves()` and `Board.get_legal_moves_for_color(...)` must still generate all four promotion choices for quiet and capture promotions.

Legal generated promotion alternatives for a white pawn from `e7` to `e8` must include:

```text
e7e8q
e7e8r
e7e8b
e7e8n
```

The move generation code should reuse the canonical `PROMOTION_PIECES` constant.

## Stale helper cleanup

`MoveValidator._get_promotion_piece()` appears to reflect the old queen-only behavior.

Required behavior:

- If there are no callers, remove the method.
- If there are callers, rewrite it so it cannot reintroduce queen-only legal-move generation.
- After cleanup, search the codebase for the method name and ensure there are no stale references.

Recommended command:

```bash
grep -R "_get_promotion_piece" -n chess_game tests
```

No active production code should depend on a helper that hardcodes queen promotion for move generation.

## Repository hygiene

Generated files must not be included in the repo/archive:

```text
__pycache__/
*.pyc
.pytest_cache/
```

Ensure `.gitignore` includes at least:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
```

Remove existing generated files from the working tree. Do not delete source files.

## Required tests

Add targeted tests for:

- `PromotionValidator.is_valid_promotion_piece(PieceType.QUEEN)` returns `True`.
- `PromotionValidator.is_valid_promotion_piece(PieceType.ROOK)` returns `True`.
- `PromotionValidator.is_valid_promotion_piece(PieceType.BISHOP)` returns `True`.
- `PromotionValidator.is_valid_promotion_piece(PieceType.KNIGHT)` returns `True`.
- `PromotionValidator.is_valid_promotion_piece(PieceType.KING)` returns `False`.
- `PromotionValidator.is_valid_promotion_piece(PieceType.PAWN)` returns `False`.
- `PromotionValidator.is_valid_promotion_piece(PieceType.EMPTY)` returns `False`.
- `PromotionValidator.is_valid_promotion_piece(5)` returns `False`.
- `PromotionValidator.is_valid_promotion_piece("q")` returns `False`.
- `PromotionValidator.is_valid_promotion_piece(None)` returns `False`.
- White pawn with promotion suffix is valid only on row `0`.
- Black pawn with promotion suffix is valid only on row `7`.
- A white pawn cannot pass promotion-choice validation for row `7`.
- A black pawn cannot pass promotion-choice validation for row `0`.
- Existing valid underpromotion behavior still works through `Board.make_move(...)`.
- Existing legal move generation still emits four promotion options.

## Acceptance criteria

This cleanup is complete only when:

- There is exactly one canonical allowed-promotion constant/list used by promotion validation and move generation.
- Raw integers and strings are rejected by `is_valid_promotion_piece(...)`.
- `is_valid_promotion_choice(...)` enforces color-specific promotion ranks.
- Stale queen-only helper code is removed or made harmless.
- Generated cache files are removed from the repo/archive.
- `.gitignore` prevents cache files from returning.
- Full suite passes:

```bash
python -m pytest tests -q
```

Expected final count should be at least the previous `273 passed`, plus any new tests added in this cleanup.
