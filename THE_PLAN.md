# THE_PLAN.md

## Mission
Turn this repository into a **correct, test-driven chess rules engine** with a small CLI front-end.

The immediate goal is **not** a strong AI, a GUI, or fancy notation support. The immediate goal is to build a chess program that:

1. Represents the board and pieces correctly.
2. Generates and validates legal chess moves correctly.
3. Applies moves without corrupting game state.
4. Correctly detects check, checkmate, stalemate, and draw-related states that we explicitly support.
5. Has a test suite strict enough that a weaker coding model cannot "sort of" implement the rules incorrectly.

This repo currently has major correctness problems:

- Board orientation is inconsistent.
- Piece color is not encoded in board cells.
- `main.py` bypasses validation and mutates the board directly.
- Tests encode illegal assumptions and do not reflect real chess rules.
- There is no clear distinction between:
  - pseudo-legal moves (piece can move that way geometrically), and
  - legal moves (the move does not leave own king in check).

This document defines the target architecture and the implementation order.

---

## Scope for the first correct version

### In scope
- Standard 8x8 chess board
- Standard starting position
- Two-player local play through CLI
- Full legal move validation for:
  - pawn
  - knight
  - bishop
  - rook
  - queen
  - king
- Special rules:
  - castling
  - en passant
  - promotion
- Game-state detection:
  - check
  - checkmate
  - stalemate
- Move parsing for coordinate notation like `e2e4` and `e7e8q`
- Test-driven development with strong unit and integration coverage

### Explicitly out of scope for the first correct version
These items should not be worked on until the rules engine is stable and well-tested:

- Strong AI / minimax / alpha-beta
- GUI
- Networking / multiplayer
- PGN import/export beyond maybe a future phase
- Opening books
- Move clocks for FIDE draw rules unless explicitly added later
- Threefold repetition unless explicitly added later

The project should become **boring and correct** before it becomes ambitious.

---

## Non-negotiable design principles

### 1. Single source of truth for rules
There must be exactly one canonical place where move legality is decided. The CLI must call that logic. Tests must target that logic. No alternate move code paths.

### 2. No direct board mutation from the UI layer
`main.py` must never perform:
- direct piece moves,
- direct turn flips,
- direct capture handling.

All mutation must go through a method such as:
- `Game.apply_move(move)` or
- `Board.apply_move(move)`

that validates the move and updates state atomically.

### 3. Separate pseudo-legal from legal move validation
Every piece needs geometry/path rules. Then a second layer must reject moves that leave the moving side’s king in check.

This distinction is essential.

### 4. Encode piece color in the data model
A board cell cannot just contain `"Pawn"` or `"Rook"`.
That loses essential information.

Each occupied square must encode at least:
- piece type
- color

Examples:
- dataclass `Piece(color="white", kind="pawn")`
- or compact codes like `"wP"`, `"bK"`

A structured representation is preferred.

### 5. Write tests before or with each rules feature
A weak model will invent broken chess logic unless the tests lock behavior down. Every rule change must come with tests.

### 6. Prefer clarity over cleverness
Do not over-optimize. Correctness and maintainability matter more than speed.

---

## Canonical coordinate and board conventions

These conventions must be used everywhere in code, docs, and tests.

### Files and ranks
- Files: `a b c d e f g h`
- Ranks: `1 2 3 4 5 6 7 8`

### Internal board indexing
Use zero-based indexing:
- row `0` = rank `8`
- row `7` = rank `1`
- col `0` = file `a`
- col `7` = file `h`

Examples:
- `a8 -> (0, 0)`
- `e8 -> (0, 4)`
- `a1 -> (7, 0)`
- `e2 -> (6, 4)`

### Side orientation
- White starts on ranks 1 and 2.
- Black starts on ranks 7 and 8.
- White pawns move toward smaller row indices.
- Black pawns move toward larger row indices.

Therefore:
- white pawn forward step = `row - 1`
- black pawn forward step = `row + 1`

This must be treated as a hard invariant.

---

## Formal rules specification

This section exists because the model working on this repo has already shown that it does not reliably know chess rules.

### General move legality rules
A move is legal only if all of the following are true:

1. Start square is on the board.
2. End square is on the board.
3. Start square contains a piece.
4. The piece belongs to the side whose turn it is.
5. End square does not contain a friendly piece.
6. The piece’s movement pattern allows the move.
7. Sliding pieces do not jump over blocking pieces.
8. Any special rule requirements are satisfied.
9. After the move is applied, the moving side’s king is **not** in check.

### Rook
A rook moves any number of squares horizontally or vertically.

Legal geometric conditions:
- same row, different column; or
- same column, different row.

Path rule:
- every square strictly between start and end must be empty.

Capture rule:
- may capture an enemy piece on the destination square.
- may not capture a friendly piece.

### Bishop
A bishop moves any number of squares diagonally.

Legal geometric condition:
- `abs(row_delta) == abs(col_delta)` and move is non-zero.

Path rule:
- every intermediate diagonal square must be empty.

### Queen
A queen moves like a rook or bishop.

Legal geometric condition:
- rook-valid OR bishop-valid.

Path rule:
- same as the underlying movement type.

### Knight
A knight moves in an L-shape:
- 2 in one axis and 1 in the other.

Legal geometric condition:
- `(abs(row_delta), abs(col_delta)) in {(2, 1), (1, 2)}`

Path rule:
- knights ignore blocking pieces between start and end.

### King
A king normally moves one square in any direction.

Legal geometric condition for normal move:
- `max(abs(row_delta), abs(col_delta)) == 1`

Additional legality:
- king may not move into check.

### Pawn
Pawns are directional and asymmetric.

#### White pawn
- forward one: `row - 1`, same column, destination empty
- forward two from starting rank only: from rank 2 (`row == 6`) to rank 4 (`row == 4`), same column, both intermediate and destination squares empty
- capture diagonally: `row - 1` and `col +/- 1`, destination occupied by black piece
- en passant: special case described below
- promotion: when arriving on rank 8 (`row == 0`)

#### Black pawn
- forward one: `row + 1`, same column, destination empty
- forward two from starting rank only: from rank 7 (`row == 1`) to rank 5 (`row == 3`), same column, both intermediate and destination squares empty
- capture diagonally: `row + 1` and `col +/- 1`, destination occupied by white piece
- en passant: special case described below
- promotion: when arriving on rank 1 (`row == 7`)

#### Pawn restrictions
- pawns do not move diagonally unless capturing or en passant.
- pawns do not capture straight ahead.
- pawns may not move forward into an occupied square.
- two-square advance is only legal from the starting rank and only if unobstructed.

### Castling
Castling is a king move with a rook move coupled to it.

#### Kingside castling
- White: king `e1 -> g1`, rook `h1 -> f1`
- Black: king `e8 -> g8`, rook `h8 -> f8`

#### Queenside castling
- White: king `e1 -> c1`, rook `a1 -> d1`
- Black: king `e8 -> c8`, rook `a8 -> d8`

#### Castling is legal only if all are true
1. The king has not moved before.
2. The involved rook has not moved before.
3. All squares between king and rook are empty.
4. The king is not currently in check.
5. The king does not pass through a square under attack.
6. The king does not end on a square under attack.

Important:
- It is allowed for the rook to pass through attacked squares.
- Only the king’s start, transit, and destination safety matters.

### En passant
En passant is only available immediately after an opposing pawn makes a two-square move and lands adjacent to one of your pawns.

Example:
- White pawn on `e5`
- Black plays `d7d5`
- White may play `e5d6` as en passant on the next move only

Implementation rule:
- Store an `en_passant_target` square after a legal two-square pawn move.
- That target is the square the capturing pawn would move into.
- If not used immediately on the opponent’s very next turn, it expires.

### Promotion
When a pawn reaches the back rank, it must promote.

- White promotes on rank 8 (`row == 0`)
- Black promotes on rank 1 (`row == 7`)

For the first correct version:
- Support promotion to queen, rook, bishop, or knight.
- If notation does not specify, default to queen.
- Never allow promotion to king or pawn.

### Check
A side is in check if its king is currently attacked by any enemy piece.

### Checkmate
Checkmate means:
1. Side to move is in check.
2. Side to move has no legal move.

### Stalemate
Stalemate means:
1. Side to move is **not** in check.
2. Side to move has no legal move.

---

## Proposed architecture

The current `Board` class mixes too many responsibilities. The project should move toward a small rules engine with explicit state.

### Recommended modules

```text
chess_game/
  chess/
    __init__.py
    types.py           # enums, dataclasses, shared types
    coords.py          # algebraic <-> index conversion
    piece.py           # Piece representation
    move.py            # Move dataclass / parsing support
    board.py           # board storage and low-level square access
    rules.py           # pseudo-legal movement rules per piece
    game.py            # turn, castling rights, en passant, status, apply_move
    status.py          # check/checkmate/stalemate helpers
  main.py              # CLI only; never mutates board directly
tests/
  ...

A simpler alternative is acceptable if it preserves clean responsibilities.

Core data structures
Piece

Suggested shape:

@dataclass(frozen=True)
class Piece:
    color: Color
    kind: PieceType
Move

Suggested shape:

@dataclass(frozen=True)
class Move:
    start: Square
    end: Square
    promotion: PieceType | None = None
Game state

At minimum:

board

side_to_move

castling rights

en_passant_target

halfmove_clock (optional now, useful later)

fullmove_number (optional now, useful later)

Castling rights

Store explicitly, for example:

white_kingside: bool

white_queenside: bool

black_kingside: bool

black_queenside: bool

Do not try to infer this from piece positions alone.

Validation pipeline

Every attempted move should go through this pipeline.

Step 1: Parse input

Convert e2e4 or e7e8q into a Move object.
Reject malformed input early.

Step 2: Structural validation

squares in bounds

start square occupied

moving correct color

destination not occupied by friendly piece

move is not zero-length

Step 3: Pseudo-legal validation

Ask piece-specific logic whether the move shape and board geometry are allowed.
This includes:

sliding path checks

pawn directional rules

castling geometry

en passant geometry

promotion requirements

Step 4: King safety validation

Apply the move on a temporary copy of state and verify the moving side’s king is not in check afterward.

Step 5: Commit

If legal, mutate real game state and update:

board

side_to_move

castling rights

en_passant_target

promotion result

status

This pipeline must be deterministic and testable.

Required invariants

These are conditions that should always be true for a valid game state.

Board is 8x8.

Every occupied square contains a valid piece object/code.

Exactly one white king exists.

Exactly one black king exists.

side_to_move is either white or black.

A legal move never leaves the mover’s king in check.

Castling rights only disappear; they do not reappear.

en_passant_target is either None or a valid square consistent with the immediately previous move.

Promotion never results in a pawn remaining on the promotion rank after move completion.

UI code does not modify board state except through the official move application API.

Testing strategy

The tests must guide the implementation and prevent regressions.

Test layers
Layer 1: coordinate tests

algebraic to index conversion

index to algebraic conversion

invalid input rejection

Layer 2: piece geometry tests

rook geometry and blocking

bishop geometry and blocking

queen geometry and blocking

knight jumps

king one-step movement

pawn forward/capture/two-step rules

Layer 3: legality tests

cannot move opponent piece

cannot capture own piece

cannot move while leaving own king in check

pinned piece examples

king cannot move into check

Layer 4: special move tests

castling allowed when all rules satisfied

castling forbidden if king moved

castling forbidden if rook moved

castling forbidden through check

en passant available exactly one move

promotion with explicit piece

promotion default queen

Layer 5: game outcome tests

check detection

checkmate examples

stalemate examples

Layer 6: CLI/API tests

parse good input

reject bad input

CLI uses official move API rather than raw board mutation

Important testing rule

Tests must represent real chess positions. Do not write tests that "pass" by putting impossible piece states on the board unless the test is explicitly about a low-level helper and documents that fact.

Implementation phases
Phase 0: stabilize the foundation

Fix imports and packaging so tests run.

Freeze board/index conventions.

Replace ambiguous string-only pieces with color-aware representation.

Remove raw mutation from main.py.

Phase 1: board + move primitives

Implement square conversion helpers.

Implement Piece, Move, and board access helpers.

Rebuild starting position correctly.

Phase 2: pseudo-legal move rules

Implement piece-specific move geometry.

Implement path blocking for sliding pieces.

Implement pawn directional rules.

Phase 3: legal move rules

Add king location lookup.

Add attack detection.

Add self-check rejection.

Phase 4: special rules

Castling

En passant

Promotion

Phase 5: status detection

check

checkmate

stalemate

Phase 6: CLI cleanup

robust input loop

clear error messages

board display using canonical orientation

optional resignation/quit commands

Phase 7: only after correctness

AI

GUI

notation improvements

serialization

Definition of done

The first correct milestone is complete only when all of the following are true:

pytest passes.

Tests cover normal moves, illegal moves, and special moves.

main.py never mutates board state directly.

A king cannot be left in check after a legal move.

Castling, en passant, and promotion work.

Checkmate and stalemate are detected in at least representative test positions.

The docs and tests agree on coordinate conventions.

No test relies on the old incorrect board orientation assumptions.

Anti-goals and failure modes to avoid

These are common ways a weak model will break the project.

Do not

treat all pawns as identical without color

infer move legality from turn only

let main.py bypass the engine

flip the board orientation in one file but not another

accept a move because the destination square is empty while ignoring path blocking

allow castling while in check

allow castling through attacked squares

forget to clear/update en passant state

let promotion silently leave a pawn on the last rank

write tests that assert illegal chess behavior

If uncertain

Prefer adding a helper, a docstring, and a test instead of writing "smart" code.