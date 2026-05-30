# Chess Rules Engine

## What this is

A correct, test-driven chess rules engine with a text-based CLI.

**Correctness comes before features.** A minimax-based AI with alpha-beta pruning is implemented and functional. GUI is not yet implemented.

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
- Pawn promotion with all four choices (queen, rook, bishop, knight); defaults to queen when no suffix is supplied
- Game status: check detection, checkmate, stalemate
- AI: minimax with alpha-beta pruning, piece-square tables, move ordering (`get_best_move`)
- Public API: `get_legal_moves`
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
| `e7e8b` | Pawn to e8, promote to bishop |
| `e7e8n` | Pawn to e8, promote to knight |
| `quit` | Exit the game |

Promotion suffixes (`q`, `r`, `b`, `n`) are only valid for pawn moves that end on the promotion rank (rank 8 for White, rank 1 for Black).

Invalid or illegal moves print an error and prompt again. The board is displayed after every legal move. Check, checkmate, and stalemate are announced automatically.

## Running the tests

```bash
python -m pytest tests/ -q -m "not slow"
```

Verbose output:

```bash
python -m pytest tests/ -v -m "not slow"
```

Run the slow suite separately:

```bash
python -m pytest tests/ -q -m "slow"
```

With coverage:

```bash
python -m pytest tests/ --cov=chess_game
```

> **Note:** `tests/conftest.py` defines a local `record_xml_attribute` fixture intentionally.
> This silences a `PytestExperimentalApiWarning` from auto-loaded third-party plugins at the source.
> Do not remove it unless plugins are updated.

## Linting and type checking

```bash
python -m ruff check chess_game tests
python -m mypy chess_game
python -m pylint chess_game
```

CI runs the same lint sequence before the test suite.

## Project structure

```
chess_game/          # Source code
  chess/
    __init__.py      # Package init
    types.py         # PieceType enum
    color.py         # Color enum
    coords.py        # Coordinate constants and helpers
    constants.py     # Board size, piece values
    move.py          # Move parsing
    ai.py            # AI move ordering and search
    evaluation.py    # Board position evaluation
    board/
      __init__.py    # Package init
      board.py       # Board class (top-level interface)
      move_execution.py    # Move execution logic
      move_validation.py   # Legal move validation
      game_state.py        # Check, checkmate, stalemate
      castling.py          # Castling rules and rights
      en_passant.py        # En passant rules
      promotion.py         # Promotion validation
      attack_utils.py      # Square attack detection
      path_validator.py    # Path clearance for sliders
      piece_validation.py  # Piece-specific validation
    pieces/
      __init__.py    # Package init
      piece_movers.py # Movement rules per piece type
  main.py            # CLI entry point
tests/               # Test suite
docs/                # Documentation
```
