# En Passant Rules

## Overview

En passant (French for "in passing") is a special pawn capture rule in chess. It allows a pawn to capture an opponent's pawn that has just moved two squares forward, as if it had moved only one square.

## When En Passant Can Occur

An en passant capture is possible **only** under these conditions:

1. **A pawn has just moved two squares forward from its starting position**
   - White pawn: from ROW_2 (rank 2) to ROW_4 (rank 4)
   - Black pawn: from ROW_7 (rank 8) to ROW_5 (rank 6)
   - The move must be a single turn, not a series of moves

2. **The opponent has a pawn on an adjacent file** that can capture the pawn that just moved

3. **The capture must happen immediately** - on the very next turn

## How the Capture Works

The capturing pawn moves **diagnostically** to the square that the opponent's pawn **passed over**. The captured pawn is removed from the board as if it had only moved one square.

### White Capturing Black

```
Before: White pawn at e4, Black pawn at f7
Black moves f7-f5 (two squares)
White captures en passant: e4 captures f5 (to e5)
Black pawn is removed from f5
```

### Black Capturing White

```
Before: White pawn at e2, Black pawn at f7
White moves e2-e4 (two squares)
Black captures en passant: f7 captures e4 (to e5)
White pawn is removed from e4
```

## The En Passant Target Square

- The en passant target is the **midpoint square** between the pawn's starting and ending squares
- For a two-square pawn move, this is the square the pawn "jumped over"
- This square remains set as the en passant target until:
  - A pawn captures it en passant
  - Any other move is made by either side

## En Passant Validity Conditions

An en passant capture is **valid** only if:

1. The capturing piece is a pawn
2. The destination square matches the en passant target
3. The capturing pawn is on an adjacent file (column difference of 1)
4. The row difference is exactly 1 (diagonal move)
5. The destination square appears empty (the pawn is in transit, not yet landed)
6. The move does not leave the capturing side's king in check
7. The move does not leave the capturing side's king pinned

## En Passant Expiration

The en passant target is **cleared** (set to None) after:

1. A pawn capture (en passant or regular)
2. A pawn promotion
3. A castling move
4. A king move
5. A queen move
6. A rook move
7. A bishop move
8. A knight move
9. **Any move that is not a pawn two-square push**

## Coordinate System

- **ROW_1** = rank 1 = array row 0 (white's back rank)
- **ROW_8** = rank 8 = array row 7 (black's back rank)
- **White pawns** move toward **increasing** row numbers (toward ROW_8)
- **Black pawns** move toward **decreasing** row numbers (toward ROW_1)

## Special Considerations

- **En passant cannot be used** if the capture would leave the capturing king in check
- **En passant cannot be used** if the capturing piece is pinned
- **En passant is optional** - a player may choose to make a regular move instead
- **En passant is not available** on the first turn (pawns haven't moved two squares yet)

## State Tracking

The board must maintain:
- `en_passant_target`: The square where an en passant capture can occur
- This must be updated after every pawn two-square move
- This must be cleared after every other type of move