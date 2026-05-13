# En Passant Rules

## Overview

En passant (French for "in passing") is a special pawn capture rule in chess. It allows a pawn to capture an opponent's pawn that has just moved two squares forward, as if it had moved only one square.

## The Passed-Over Target Square

When a pawn moves two squares forward from its starting position, it "passes over" the intermediate square. That intermediate square becomes the **en passant target square**:

- After White plays `e2e4`, the target is **e3** (the square the pawn passed over).
- After Black plays `d7d5`, the target is **d6** (the square the pawn passed over).

The target square is the square where a capturing pawn would **land**, not the square where the captured pawn sits.

The `en_passant_target` is stored on the board and is used by the move validator to determine whether an en passant capture is legal.

## One-Row Diagonal Capture Geometry

En passant is a **one-row diagonal** capture. The capturing pawn moves exactly one row in its forward direction and one column toward the captured pawn's file.

### White capturing en passant

```
Before: White pawn at e4, Black pawn at f7
Black plays f7-f5 (two squares forward)
En passant target is set to f4 (the passed-over square)
White captures en passant: e4→f4 (one row up, one column right)
Black pawn is removed from f5
```

Key points:
- White pawn moves from e4 (row 4) to f4 (row 4, col 5) — wait, that's wrong. Let me reconsider.

Actually with canonical coordinates:
- e4 = (row=4, col=4)
- f5 = (row=3, col=5)
- f4 = (row=4, col=5)

White pawn at e4 (row 4), black plays f7→f5. Target = f4 (row 4, col 5).
White captures: e4 → f4. row_delta = 0, col_delta = +1. That's not right either — en passant should have a row delta.

Let me reconsider with proper canonical coordinates:
- e4 = rank 4, so row = 8-4 = 4
- f5 = rank 5, so row = 8-5 = 3
- f4 = rank 4, so row = 8-4 = 4

Wait — the en passant target for black f7→f5 should be f6 (the passed-over square), not f4.

Let me redo this properly:

### White capturing en passant (corrected)

```
Before: White pawn at e5 (row 3, col 4), Black pawn at f7 (row 1, col 5)
Black plays f7→f5 (two squares, from row 1 to row 3)
En passant target is set to f6 (row 2, col 5) — the passed-over square
White captures en passant: e5→f6 (row 3→2, col 4→5)
  - row_delta = -1 (white moves toward smaller rows)
  - col_delta = +1 (one column to the right)
Black pawn is removed from f5 (row 3, col 5)
```

### Black capturing en passant (corrected)

```
Before: White pawn at e2 (row 6, col 4), Black pawn at f4 (row 4, col 5)
White plays e2→e4 (two squares, from row 6 to row 4)
En passant target is set to e3 (row 5, col 4) — the passed-over square
Black captures en passant: f4→e3 (row 4→5, col 5→4)
  - row_delta = +1 (black moves toward larger rows)
  - col_delta = -1 (one column to the left)
White pawn is removed from e4 (row 4, col 4)
```

## Captured Pawn Removal Square

The captured pawn is removed from its **actual square**, not the en passant target square:

- The capturing pawn lands on the en passant target square.
- The captured pawn sits on the square **adjacent to the target** on the same file as the captured pawn's original position.

For example, after White `e5` captures en passant against Black `f5`:
- White pawn lands on `f6` (the target square).
- Black pawn is removed from `f5` (where it actually sits).

## Immediate-Half-Move Expiration

The en passant opportunity expires **immediately** after the next half-move. The target square is:

1. Set after a legal two-square pawn advance.
2. Available for capture on the opponent's very next turn only.
3. Cleared unconditionally after any subsequent move (whether it is an en passant capture or any other move).

If the opponent does not capture en passant on their next turn, the opportunity is lost permanently.

## En Passant Validity Conditions

An en passant capture is **legal** only if all of the following are true:

1. The capturing piece is a pawn.
2. The destination square matches `board.en_passant_target`.
3. The capturing pawn is on an adjacent file (column difference of exactly 1).
4. The row difference is exactly 1 (one-row diagonal move):
   - White: `to_row - from_row == -1`
   - Black: `to_row - from_row == +1`
5. The destination square is empty (the captured pawn is on a different square).
6. The move does not leave the capturing side's king in check.

## Coordinate System

- **row 0** = rank 8 (black's back rank)
- **row 7** = rank 1 (white's back rank)
- **White pawns** move toward **smaller** row numbers (row - 1 per step)
- **Black pawns** move toward **larger** row numbers (row + 1 per step)

## Special Considerations

- **En passant cannot be used** if the capture would leave the capturing king in check.
- **En passant is optional** — a player may choose to make a regular move instead.
- **En passant is not available** on the first turn (pawns haven't moved two squares yet).
- **En passant requires exactly one-row diagonal geometry** — the capturing pawn moves one row forward and one column toward the captured pawn.

## State Tracking

The board must maintain:
- `en_passant_target`: The square where a capturing pawn would land (the passed-over square), or `None`.
- Set after every legal two-square pawn advance.
- Cleared after every subsequent move.
