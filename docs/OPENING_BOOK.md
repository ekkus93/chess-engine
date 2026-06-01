# Opening Book Guide

## Overview

The chess engine includes a simple, data-driven opening book that provides suggested moves in the opening phase of the game. The book is stored in JSON format and indexed by board position for fast lookup.

## Features

- **Deterministic Selection**: Moves are selected based on weight values in a deterministic manner (highest weight wins, with tie-breaking by line index, ply index, and coordinate notation)
- **Position-Based Lookup**: The book uses full position keys (including piece placement, side to move, castling rights, and en passant target) for accurate matching
- **Legal Move Filtering**: Only legal moves are returned from the book
- **Search Fallback**: If no book move exists for a position, the engine falls back to regular minimax search

## File Location

The bundled opening book is located at:
```
chess_game/chess/data/opening_book.json
```

## JSON Format

The opening book uses the following JSON schema (v1):

```json
{
  "version": 1,
  "selection": "highest_weight",
  "lines": [
    {
      "name": "King's Gambit",
      "side": "white",
      "eco": "C30",
      "moves": ["e2e4", "e7e5", "f2f4"],
      "weight": 70,
      "tags": ["white", "open-game", "gambit", "aggressive"]
    }
  ]
}
```

### Field Descriptions

- **version**: Opening book format version (currently 1)
- **selection**: Selection policy (currently "highest_weight")
- **lines**: List of opening lines
  - **name**: Human-readable name of the opening (required)
  - **side**: "white", "black", or "both" (required)
  - **eco**: ECO classification code (optional)
  - **moves**: List of moves in coordinate notation like "e2e4", "e7e8q" for promotion (required)
  - **weight**: Positive integer weight for selection (higher wins, required)
  - **tags**: List of descriptive tags (optional)

## Move Notation

All moves use coordinate notation:
- Format: source file + source rank + destination file + destination rank
- Examples: `e2e4`, `g1f3`, `e7e8q` (with promotion)
- Promotion suffixes: `q` (queen), `r` (rook), `b` (bishop), `n` (knight)
- Always lowercase

## Adding New Openings

To add a new opening line:

1. Open `chess_game/chess/data/opening_book.json`
2. Add a new object to the `lines` array:

```json
{
  "name": "My Opening",
  "side": "white",
  "eco": "C00",
  "moves": ["e2e4", "e7e6", "d2d4"],
  "weight": 50,
  "tags": ["white", "closed-game"]
}
```

3. Ensure all moves in the line are legal when replayed from the initial position
4. Choose an appropriate weight (higher = more likely to be selected)

## Using the Opening Book

### Programmatic API

```python
from chess_game.chess.opening_book import OpeningBook, get_bundled_opening_book
from chess_game.chess.board import Board

# Load the bundled opening book
book = get_bundled_opening_book()

# Get a book move for the current position
board = Board()
move = book.find_book_move(board)

# Get all candidates for a position
candidates = book.candidates_for(board)

# Get best move with opening book enabled (default)
from chess_game.chess.ai import get_best_move
move = get_best_move(board, depth=3, use_opening_book=True)

# Or disable the book for specific searches
move = get_best_move(board, depth=3, use_opening_book=False)
```

### CLI Usage

The self-play mode respects the opening book by default:

```bash
# Run self-play with opening book enabled (default)
python -m chess_game.self_play --white-depth 3 --black-depth 3

# Disable the opening book
python -m chess_game.self_play --white-depth 3 --black-depth 3 --no-opening-book
```

## Content

The bundled opening book includes:

### White Openings (10+)
- Italian Game
- Ruy Lopez
- Queen's Gambit
- London System
- Scotch Game
- King's Gambit
- Vienna Game
- English Opening
- Reti Opening
- Catalan Opening

### King's Gambit Family (6 continuations)
- King's Gambit Accepted: King's Knight Gambit
- King's Gambit Accepted: Bishop's Gambit
- King's Gambit Accepted: Classical Defense
- King's Gambit Accepted: Fischer Defense
- King's Gambit Declined: Classical
- King's Gambit Declined: Falkbeer Countergambit

### Black Defenses (10+)
- Sicilian Defense
- French Defense
- Caro-Kann Defense
- Open Game
- Scandinavian Defense
- Pirc Defense
- Queen's Gambit Declined
- Slav Defense
- King's Indian Defense
- Nimzo-Indian Defense

## Implementation Notes

- The opening book is loaded and cached on first use via `@lru_cache`
- Book loading fails fast with clear error messages if JSON is invalid or lines are illegal
- Position keys include full board state (pieces, castling rights, en passant) for accurate matching
- Book lookup never returns an illegal move

## Testing

Run the opening book tests:

```bash
python -m pytest tests/test_opening_book.py -v
```

Tests cover:
- Loading and parsing the bundled book
- Legal move validation during load
- Position-based lookup
- Deterministic selection
- Integration with `get_best_move()`
- Content verification (openings, defenses, King's Gambit family)
