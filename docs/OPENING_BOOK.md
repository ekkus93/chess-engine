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
- King's Gambit Declined: Classical (`e2e4 e7e5 f2f4 f8c5 g1f3`)
- King's Gambit Declined: Falkbeer Countergambit (`e2e4 e7e5 f2f4 d7d5 e4d5`)

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

## Side-Aware Indexing

The `side` field controls which positions index moves from each line:

- **`side="white"`**: Indexes moves only when it's White to move. Black defenses in these lines are skipped.
- **`side="black"`**: Indexes moves only when it's Black to move. White moves in these lines are applied but not indexed.
- **`side="both"`**: Indexes all plies in the line, regardless of whose turn it is.

This ensures that Black defense lines don't pollute White's opening book and vice versa.

**Example**:
- A `side="black"` Sicilian Defense line has moves `["e2e4", "c7c5", ...]`
  - `e2e4` is applied but NOT indexed (it's White's move)
  - `c7c5` and subsequent Black moves ARE indexed

## Error Handling

The opening book is strict about correctness:

- **Invalid JSON**: `OpeningBookError` is raised with details
- **Non-object top-level JSON**: `OpeningBookError` is raised (`opening_book.json` must be a JSON object)
- **Unsupported format version**: `OpeningBookError` is raised
- **Unsupported selection policy**: `OpeningBookError` is raised (only `"highest_weight"` is supported)
- **Illegal moves**: `OpeningBookError` is raised with the invalid move details
- **Missing or invalid required fields**: `OpeningBookError` is raised with field details

Errors fail loudly and clearly to ensure data integrity. They propagate to the calling layer (typically the CLI) where they can be handled appropriately.

## Unknown Positions and Fallback

When `find_book_move()` is called for a position not in the book:

- `None` is returned
- The AI falls back to regular minimax search
- No silent fallback or default move is performed

This ensures the AI always uses the best available move-selection strategy.

## CLI Usage

### Self-Play with Opening Book

By default, self-play uses the bundled opening book:

```bash
python -m chess_game.self_play --white-depth 3 --black-depth 3
```

### Disable Opening Book

To run self-play without the opening book:

```bash
python -m chess_game.self_play --no-opening-book --white-depth 3 --black-depth 3
```

### Custom Opening Book

To use a custom opening book JSON file:

```bash
python -m chess_game.self_play --opening-book /path/to/my_book.json --white-depth 3 --black-depth 3
```

The custom book is loaded at startup. If the file is invalid or contains illegal moves, the error is reported to stderr and the program exits.

### Combined Flags

If both `--opening-book` and `--no-opening-book` are specified, `--no-opening-book` takes precedence. The custom path is ignored and not loaded.
