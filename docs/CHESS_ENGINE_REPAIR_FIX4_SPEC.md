# Chess Engine Repair Fix 4 Specification

## Purpose

This document defines the required behavior for the next focused chess-engine repair pass.

The current engine is substantially healthier than the original version. The coordinate system, basic move validation, castling, en passant, king-capture rejection, test helper usage, and AI evaluation orientation have all been repaired.

The remaining confirmed correctness issue is promotion handling:

1. `get_legal_moves()` generates only queen promotions.
2. Promotion suffixes are accepted on non-pawn moves and silently ignored.
3. Raw integer promotion values can be accepted and stored as `Piece.kind`.
4. AI move ordering/search currently does not preserve promotion identity when multiple legal moves share the same start and end square.

This Fix 4 pass must correct those promotion-related issues without broadening scope into unrelated AI features, GUI work, new chess features, or a large engine rewrite.

---

## Scope

### In scope

- Legal move generation for all valid promotion choices.
- Promotion validation for CLI/API moves.
- Type safety for the `promotion` argument.
- AI move ordering/search preservation of promotion identity.
- Regression tests proving promotion move completeness and promotion input validation.
- Documentation updates only where needed to reflect corrected promotion behavior.

### Out of scope

- New AI features.
- Opening books.
- UCI protocol support.
- GUI work.
- New game modes.
- Full perft framework, unless a very small targeted helper is useful for regression coverage.
- Large `MoveKind` / `ValidatedMove` refactor unless absolutely necessary.
- Rewriting unrelated move-validation code that already works.

---

## Current baseline

Before making changes, the repository should pass:

```bash
python -m pytest tests -q
```

Expected baseline from the latest reviewed version:

```text
195 passed
```

If the count differs slightly because tests were added or renamed, continue only if the existing suite is passing before Fix 4 work begins.

---

## Promotion rules contract

### Legal promotion pieces

When a pawn promotes, the only valid promotion pieces are:

- `PieceType.QUEEN`
- `PieceType.ROOK`
- `PieceType.BISHOP`
- `PieceType.KNIGHT`

The following are invalid:

- `PieceType.KING`
- `PieceType.PAWN`
- `PieceType.EMPTY`
- raw integers such as `5`
- strings such as `"q"`
- any non-`PieceType` object

The public CLI/parser may convert suffixes like `q`, `r`, `b`, `n` into `PieceType` values. After parsing, engine internals should receive only `PieceType` values or `None`.

---

## Promotion rank contract

The canonical coordinate system remains:

```text
row 0 = rank 8
row 7 = rank 1
```

Promotion ranks are:

```text
White promotes on row 0 / rank 8.
Black promotes on row 7 / rank 1.
```

A pawn may only promote if the underlying pawn move is legal.

Examples:

```text
White e7e8q is a legal quiet promotion if e8 is empty and the move does not leave White in check.
White e7d8q is a legal capture promotion only if d8 contains an enemy piece and the move does not leave White in check.
Black e2e1q is a legal quiet promotion if e1 is empty and the move does not leave Black in check.
Black e2d1q is a legal capture promotion only if d1 contains an enemy piece and the move does not leave Black in check.
```

Promotion must not bypass normal pawn movement rules.

---

## Default promotion behavior

The engine currently supports default queen promotion when a pawn reaches the promotion rank with `promotion=None`.

This behavior may remain, but it must be applied only when:

1. the moving piece is a pawn,
2. the destination is that pawn's valid promotion rank,
3. the underlying pawn movement is legal,
4. the move does not leave the moving side's king in check.

Default queen promotion must not make non-pawn moves with `promotion=None` special.

---

## Legal move generation contract

`Board.get_legal_moves()` and any underlying `MoveValidator.get_legal_moves(...)` path must generate all legal promotion choices.

When a pawn has a legal quiet promotion, legal moves must include four moves with the same start and end but different promotion values:

```text
QUEEN
ROOK
BISHOP
KNIGHT
```

When a pawn has a legal capture promotion, legal moves must also include four moves with the same start and end but different promotion values:

```text
QUEEN
ROOK
BISHOP
KNIGHT
```

Legal move generation must not return only queen promotion.

Legal move generation must not return invalid promotion pieces.

Legal move generation must preserve promotion values in the returned move representation.

---

## Move execution contract

`Board.make_move(start, end, promotion)` must reject invalid promotion requests.

### Non-pawn promotion suffixes

If `promotion is not None` and the moving piece is not a pawn, the move must be rejected.

Examples that must return `False`:

```text
g1f3q
e1e2q
a1a2q
```

The piece must not move.

The turn must not change.

The board state must not be mutated.

### Wrong-rank promotion suffixes

If `promotion is not None` and the moving pawn does not end on its promotion rank, the move must be rejected.

Examples that must return `False`:

```text
e2e4q
e7e5q
```

The pawn must not move.

The turn must not change.

The board state must not be mutated.

### Invalid promotion type

If `promotion` is not an instance of `PieceType`, reject it.

Examples that must return `False`:

```python
board.make_move(sq("e7"), sq("e8"), promotion=5)
board.make_move(sq("e7"), sq("e8"), promotion="q")
board.make_move(sq("e7"), sq("e8"), promotion=object())
```

The board must never contain a `Piece` whose `kind` is a raw integer or string.

### Invalid `PieceType`

If `promotion` is a `PieceType` but not one of queen/rook/bishop/knight, reject it.

Examples that must return `False`:

```python
board.make_move(sq("e7"), sq("e8"), promotion=PieceType.KING)
board.make_move(sq("e7"), sq("e8"), promotion=PieceType.PAWN)
board.make_move(sq("e7"), sq("e8"), promotion=PieceType.EMPTY)
```

---

## Parser contract

`parse_move_notation(...)` may continue to parse promotion suffixes syntactically.

Accepted suffixes:

```text
q, r, b, n
Q, R, B, N if currently supported or easy to support consistently
```

Invalid suffixes must raise `ValueError`.

Parser acceptance does not mean the move is legal. The engine must still reject parsed promotion suffixes on non-pawn moves and wrong-rank pawn moves.

Example:

```python
move = parse_move_notation("g1f3q")
assert move.promotion == PieceType.QUEEN
assert board.make_move(move.start, move.end, move.promotion) is False
```

---

## AI/search contract

AI move generation must preserve promotion identity.

If four legal moves share the same start and end square but differ by promotion piece, the AI must treat them as four distinct moves.

Any move-ordering key, cached move descriptor, or search loop helper that currently stores only:

```text
start
end
```

must be updated to include:

```text
promotion
```

When matching an ordered move back to a legal move, match all three:

```text
start
end
promotion
```

not just start and end.

This is required because legal promotion alternatives are semantically different moves.

---

## Testing contract

Tests must be written using existing algebraic helpers such as:

```python
sq("e7")
assert_piece(...)
assert_empty(...)
```

Avoid raw row/column constants in tests unless the test is explicitly about internal coordinate conversion.

At minimum, add tests for:

1. White quiet promotion move generation includes queen, rook, bishop, and knight.
2. White capture promotion move generation includes queen, rook, bishop, and knight.
3. Black quiet promotion move generation includes queen, rook, bishop, and knight.
4. Black capture promotion move generation includes queen, rook, bishop, and knight.
5. Explicit underpromotion executes correctly for all allowed pieces.
6. Non-pawn moves with promotion suffixes are rejected.
7. Pawns with promotion suffixes on non-promotion ranks are rejected.
8. Raw integer promotion values are rejected.
9. Raw string promotion values are rejected.
10. `PieceType.KING`, `PieceType.PAWN`, and `PieceType.EMPTY` promotions are rejected.
11. Failed promotion validation does not mutate board state or flip turn.
12. AI move ordering/search preserves promotion identity.

Optional but useful:

- A targeted perft-style regression position where promotion multiplicity changes the node count.
- A test proving `get_legal_moves()` returns no duplicate identical promotion moves.

---

## Acceptance criteria

The patch is complete when:

1. The full test suite passes:

   ```bash
   python -m pytest tests -q
   ```

2. Legal move generation returns all four promotion choices for both colors and both quiet/capture promotions.

3. Explicit underpromotion works through `Board.make_move(...)`.

4. Non-pawn promotion suffixes are rejected.

5. Wrong-rank pawn promotion suffixes are rejected.

6. Raw integer/string promotion values are rejected.

7. Invalid `PieceType` promotion values are rejected.

8. The board never stores a raw integer/string as `Piece.kind`.

9. AI move ordering/search preserves the `promotion` field.

10. The patch does not introduce unrelated AI, GUI, or architecture changes.

---

## Recommended implementation approach

Prefer a small, focused patch.

Do not introduce a large `MoveKind` or `ValidatedMove` refactor for this pass unless promotion correctness cannot be achieved cleanly without it.

Recommended structure:

1. Add failing regression tests first.
2. Fix promotion validation.
3. Fix legal move generation to emit all promotion choices.
4. Fix AI move ordering/search to include promotion identity.
5. Run the full suite.
6. Update docs if needed.

---

## Known risk areas

### `IntEnum` equality

If `PieceType` is an `IntEnum`, raw integers may compare equal to enum members.

Therefore, membership checks are not enough:

```python
promotion in {PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT}
```

may accidentally accept raw integers.

Always check:

```python
isinstance(promotion, PieceType)
```

before membership.

### AI move identity

When promotion choices are added to `get_legal_moves()`, any code that assumes `(start, end)` uniquely identifies a move becomes incorrect.

Search, move ordering, transposition move hints, and best-move selection must include promotion.

### Default queen promotion

Default queen promotion should not hide invalid explicit promotion suffixes.

These are different:

```text
e7e8 with promotion=None      -> default queen promotion may be allowed
e2e4q with promotion=QUEEN    -> must be rejected
g1f3q with promotion=QUEEN    -> must be rejected
```
