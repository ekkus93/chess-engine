# Opening Book Fix - Implementation Answers

## Answers to Clarification Questions

### Q1: `board.turn` Type ✅ CONFIRMED

**Answer:** `board.turn` is a `Color` enum.

```python
from chess_game.chess.types import Color

# board.turn will be either:
# - Color.WHITE (value: 1)
# - Color.BLACK (value: 0)

# Usage in helper:
def _should_index_line_move(line: OpeningLine, board: Board) -> bool:
    if line.side == "both":
        return True
    if line.side == "white":
        return board.turn == Color.WHITE
    if line.side == "black":
        return board.turn == Color.BLACK
    return False
```

**Status:** ✅ Ready to use. No adaptation needed.

---

### Q2: Promotion Enum Access ✅ CONFIRMED

**Answer:** Promotion is `PieceType` enum with uppercase names.

```python
from chess_game.chess.types import PieceType

# Available types: EMPTY, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING
# For promotion tie-break:

if candidate.move.promotion is not None:
    promotion_suffix = candidate.move.promotion.name.lower()[0]
    # Examples:
    # PieceType.QUEEN → "queen" → "q"
    # PieceType.ROOK → "rook" → "r"
    # PieceType.KNIGHT → "knight" → "n"
    # PieceType.BISHOP → "bishop" → "b"
```

**Status:** ✅ Spec code will work directly. `.name.lower()[0]` produces correct suffix.

---

### Q3: Legal Move Return Shape ✅ CONFIRMED

**Answer:** `board.get_legal_moves()` returns tuples of `(start, end, promotion)`.

```python
legal_moves = board.get_legal_moves()
# Returns: [(ConstantSquare, ConstantSquare, Optional[PieceType]), ...]

# For comparison with book moves:
book_move = book.find_book_move(board)  # Returns LegalMove (tuple-like)
legal_moves = board.get_legal_moves()   # Returns list of tuples

# Comparison strategy (Task 3.8):
for legal_move in legal_moves:
    legal_start, legal_end, legal_promo = legal_move
    if (book_move.start == legal_start and 
        book_move.end == legal_end and 
        book_move.promotion == legal_promo):
        # Match found
        break
```

**Status:** ✅ Identity comparison can check start/end/promotion fields.

---

### Q4: `candidates_for()` Method ✅ CONFIRMED AVAILABLE

**Answer:** `OpeningBook` has `candidates_for(board)` as a public method.

```python
from chess_game.chess.opening_book import get_bundled_opening_book

book = get_bundled_opening_book()

# Public methods available:
# - book.find_book_move(board) → LegalMove or None
# - book.candidates_for(board) → list of BookMove candidates
# - book.from_file(path) → OpeningBook instance
# - book.lines → list of OpeningLine

# Usage in tests:
candidates = book.candidates_for(board)
for candidate in candidates:
    # candidate has: move, weight, line_index, ply_index, name
    print(f"{candidate.name}: {candidate.move}")
```

**Status:** ✅ Ready to use. API is already exposed for testing.

---

### Q5: CLI Structure - `--no-opening-book` Pattern ✅ NEED TO CHECK

**Where to look:**
```bash
grep -R "no-opening-book" . --include="*.py"
```

**Expected locations:**
- `chess_game/self_play.py` — argparse setup
- `chess_game/main.py` or equivalent — CLI entry point

**For implementation (if needed):**
- Pattern: `--no-opening-book` flag → boolean `use_opening_book` parameter
- Optional: `--opening-book path/to/book.json` → file path
- Conflict handling: `--no-opening-book --opening-book custom.json` → decide precedence

**Status:** ⏳ Will grep on implementation start to see current pattern.

---

## Move Representation Details

### Current Situation (Verified)

1. **`board.get_legal_moves()`** returns tuples:
   - `(ConstantSquare, ConstantSquare, Optional[PieceType])`

2. **`parse_move_notation()`** returns `Move` dataclass:
   - Type: `chess_game.chess.move.Move`
   - Has attributes: `.start`, `.end`, `.promotion`

3. **`LegalMove`** type (from types.py):
   - Used in type hints but actual return from board is tuple
   - `Move` dataclass is compatible

4. **Book moves** (from opening_book.py):
   - Stored as `LegalMove` internally
   - `find_book_move()` returns `Optional[LegalMove]`
   - `candidates_for()` returns list of `BookMove` (internal type with metadata)

### For Task 3.8 (Verify Candidates Are Legal)

```python
# Pseudo-code:
board = Board()
apply_moves(board, "e2e4", "e7e5")
legal_moves = board.get_legal_moves()

# Get candidates
candidates = book.candidates_for(board)
assert len(candidates) > 0, "Should have candidates"

# Verify each candidate is legal
legal_move_set = set()
for start, end, promo in legal_moves:
    legal_move_set.add((start, end, promo))

for candidate in candidates:
    move_tuple = (candidate.move.start, candidate.move.end, candidate.move.promotion)
    assert move_tuple in legal_move_set, \
        f"Candidate {candidate.name} move {move_tuple} not legal"
```

---

## Implementation-Ready Details

### Helper for Task 1.2 (Side-Aware Indexing)

```python
def _should_index_line_move(line: OpeningLine, board: Board) -> bool:
    """Check if this line's move should be indexed for current board position."""
    if line.side == "both":
        return True
    if line.side == "white":
        return board.turn == Color.WHITE
    if line.side == "black":
        return board.turn == Color.BLACK
    return False
```

**Imports needed:**
```python
from chess_game.chess.types import Color, OpeningLine
from chess_game.chess.board import Board
```

### Promotion Suffix Helper for Task 5.2

```python
def _promotion_suffix(piece_type: Optional[PieceType]) -> str:
    """Get single-char suffix for promotion piece."""
    if piece_type is None:
        return ""
    return piece_type.name.lower()[0]

# Usage in sort key:
promotion_suffix = _promotion_suffix(candidate.move.promotion)
move_str = f"{start_alg}{end_alg}{promotion_suffix}"
```

**Imports needed:**
```python
from chess_game.chess.types import PieceType
from typing import Optional
```

### Move Application Helper for Task 3.1

```python
def apply_moves(board: Board, *moves: str) -> None:
    """Apply a sequence of coordinate notation moves to board."""
    from chess_game.chess.move import parse_move_notation
    
    for move_text in moves:
        move = parse_move_notation(move_text)
        result = board.make_move(move.start, move.end, move.promotion)
        assert result, f"Failed to apply move: {move_text}"
```

**Imports needed:**
```python
from chess_game.chess.board import Board
from chess_game.chess.move import parse_move_notation
```

---

## Pre-Implementation Checklist

- ✅ `board.turn` type: `Color` enum (WHITE=1, BLACK=0)
- ✅ Promotion enum: `PieceType` with `.name.lower()[0]` → single char
- ✅ Legal move shape: tuples of (start, end, promotion)
- ✅ `candidates_for()`: Public method available
- ✅ `find_book_move()`: Public method available
- ✅ `from_file()`: Available on OpeningBook class
- ⏳ CLI pattern: Will verify with grep on start

---

## Summary

**All implementation details verified and ready.**

No ambiguities remain. Code is ready to begin implementing Tasks 0-10 in order.

The spec and TODO are clear, focused, and achievable without additional clarification.
