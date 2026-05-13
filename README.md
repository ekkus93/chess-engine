# Chess Rules Engine

## What this is

A correct, test-driven chess rules engine with a text-based CLI.

**Correctness comes before features.** AI and GUI are not yet implemented and are not part of the current scope — they come after all rules are verifiably green.

### Coordinate Convention

The engine uses a canonical coordinate system:
- **row 0 = rank 8** (black's back rank)
- **row 7 = rank 1** (white's back rank)
- **col 0 = file a**, **col 7 = file h**
- White pawns move toward smaller row numbers, black pawns toward larger row numbers
- See `docs/coordinate_system.md` for the complete reference

## Current capabilities

- Full starting position and typed piece model (`Color` × `PieceType`)
- Pseudo-legal movement rules for all six piece types
- Legal move validation: moves that leave the mover's king in check are rejected
- Castling (all four variants) with rights tracking
- En passant with expiry after one turn
- Pawn promotion with default-to-queen when no choice is supplied
- Game status: `is_in_check`, `is_checkmate`, `is_stalemate`, `get_legal_moves`
- Interactive CLI (`main.py`) that runs a full game loop

## Running the CLI

```bash
python -m chess_game.main
```

Move input format:

| Example | Meaning |
|---------|---------|
| `e2e4` | Move from e2 to e4 |
| `g1f3` | Knight from g1 to f3 |
| `e7e8q` | Pawn to e8, promote to queen |
| `e7e8r` | Pawn to e8, promote to rook |
| `quit` | Exit the game |

Invalid or illegal moves print an error and prompt again. The board is displayed after every legal move. Check, checkmate, and stalemate are announced automatically.

## Running the tests

```bash
python -m pytest tests/ -q
```

Verbose output:

```bash
python -m pytest tests/ -v
```

With coverage:

```bash
python -m pytest tests/ --cov=chess_game
```

> **Note:** `tests/conftest.py` defines a local `record_xml_attribute` fixture intentionally.
> This silences a `PytestExperimentalApiWarning` from auto-loaded third-party plugins at the source.
> Do not remove it unless plugins are updated.

## Project structure

```
chess_game/          # Source code
  chess/
    board.py         # Board class and move logic
    piece.py         # Piece model
    coords.py        # Coordinate constants and helpers
    types.py         # Enums (Color, PieceType)
    move.py          # Move parsing
  main.py            # CLI entry point
tests/               # Test suite
docs/                # Documentation
```
