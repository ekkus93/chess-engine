# Initial Chess Board Position

This document describes the standard initial position of all pieces in chess.

## Piece Placement

### Rank 1 (White's Back Rank)
```
Rook | Knight | Bishop | Queen | King | Bishop | Knight | Rook
```
- **Rook** on a1 (file a, rank 1)
- **Knight** on b1 (file b, rank 1)
- **Bishop** on c1 (file c, rank 1)
- **Queen** on d1 (file d, rank 1) - *Queen on her own color (white square)*
- **King** on e1 (file e, rank 1)
- **Bishop** on f1 (file f, rank 1)
- **Knight** on g1 (file g, rank 1)
- **Rook** on h1 (file h, rank 1)

### Rank 2 (White Pawns)
- **Pawns** on a2, b2, c2, d2, e2, f2, g2, h2

### Ranks 3-6 (Empty)
- No pieces

### Rank 7 (Black Pawns)
- **Pawns** on a7, b7, c7, d7, e7, f7, g7, h7

### Rank 8 (Black's Back Rank)
```
Rook | Knight | Bishop | Queen | King | Bishop | Knight | Rook
```
- **Rook** on a8 (file a, rank 8)
- **Knight** on b8 (file b, rank 8)
- **Bishop** on c8 (file c, rank 8)
- **Queen** on d8 (file d, rank 8) - *Queen on her own color (black square)*
- **King** on e8 (file e, rank 8)
- **Bishop** on f8 (file f, rank 8)
- **Knight** on g8 (file g, rank 8)
- **Rook** on h8 (file h, rank 8)

## Visual Representation

```
  a b c d e f g h
8 R N B Q K B N R 8
7 P P P P P P P P 7
6 . . . . . . . . 6
5 . . . . . . . . 5
4 . . . . . . . . 4
3 . . . . . . . . 3
2 p p p p p p p p 2
1 r n b q k b n r 1
  a b c d e f g h
```

## Key Rules

1. **Pawns** occupy the rank immediately in front of each player
2. **Major pieces** (Rooks, Knights, Bishops, Queen, King) occupy the back rank
3. **Queen** is placed on her own color square (d1 for white, d8 for black)
4. **King** is always in the center file (e-file)
5. The board is symmetric for both sides

## Coordinate System

- **Files** (columns): a, b, c, d, e, f, g, h
- **Ranks** (rows): 1, 2, 3, 4, 5, 6, 7, 8
- White starts at the bottom (ranks 1-2)
- Black starts at the top (ranks 7-8)
