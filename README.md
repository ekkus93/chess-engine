# Chess Rules Engine

## What this is

A correct, test-driven chess rules engine with a text-based CLI.

**Correctness comes before features.** There is no AI and no GUI yet — those come after all rules are verifiably green.

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
python -m pytest tests/ -v
```

Quick summary only:

```bash
python -m pytest tests/ -q
```

With coverage:

```bash
python -m pytest tests/ --cov=chess_game
```

> **Note:** `tests/conftest.py` defines a local `record_xml_attribute` fixture intentionally.
> This silences a `PytestExperimentalApiWarning` from auto-loaded third-party plugins at the source.
> Do not remove it unless plugin-loading behaviour is explicitly changed.

## Project structure

```
chess_game/
  chess/
    board.py     # Board state, all move validation, game-status helpers
    coords.py    # Algebraic notation ↔ (row, col) conversion
    move.py      # Move dataclass + coordinate notation parser
    types.py     # Color, PieceType, Piece
  main.py        # CLI entry point
tests/
  conftest.py         # Shared fixtures (empty_board, board_with_kings)
  test_coords.py      # Coordinate conversion and parsing
  test_setup.py       # Starting position, board helpers
  test_piece_moves.py # Pseudo-legal movement rules per piece
  test_legality.py    # Attack detection, check, self-check rejection
  test_special_moves.py # Castling, en passant, promotion
  test_game_status.py # Legal move generation, checkmate, stalemate
  test_cli_parsing.py # Move notation parser
```

## Developer notes

### Coordinate convention

The board is a row-major 8×8 array. Indexing maps chess notation as follows:

| Internal | Algebraic |
|----------|-----------|
| `(0, 0)` | a8 |
| `(0, 7)` | h8 |
| `(7, 0)` | a1 |
| `(7, 7)` | h1 |
| `(6, 4)` | e2 |

- `row 0` = rank 8 (black back rank), `row 7` = rank 1 (white back rank)
- `col 0` = file a, `col 7` = file h
- White pawns move toward **smaller** row numbers (up the array)

### Pseudo-legal vs. legal moves

`Board` exposes per-piece pseudo-legal validators (`is_valid_rook_move`, etc.) that check only shape and path — they do **not** verify whether the mover's king is left in check.

`make_move` and `get_legal_moves` are the only public entry points for executed moves. They simulate each candidate on a clone of the board and reject moves that leave the mover's king in check, making them fully legal.

### Castling rights

Four boolean fields on `Board` track the rights: `white_kingside`, `white_queenside`, `black_kingside`, `black_queenside`. All start `True`. They become permanently `False` when:

- The relevant king moves (both rights for that colour are cleared), or
- The relevant rook moves from its origin square, or
- The relevant rook is captured on its origin square.

Rights never recover once lost.

### En passant state

`Board.en_passant_target` holds the square a capturing pawn would land on (the "ghost" square behind the double-pushed pawn), or `None`. It is set after any legal two-square pawn advance and cleared unconditionally after the next move by either side.
