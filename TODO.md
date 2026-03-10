# TODO.md

This file is intentionally strict and explicit so that a weaker coding model can make progress without inventing chess rules.

Read `THE_PLAN.md` first. Follow this TODO in order. Do not skip phases. Do not add AI or GUI work until the rules engine is correct.

---

## Global rules for the model editing this repo

### Rule 1: never mutate the board from `main.py`
All moves must go through a single validated API.

### Rule 2: do not preserve broken behavior for compatibility
If an existing test encodes incorrect chess behavior, fix or replace the test.

### Rule 3: every completed task needs tests
When implementing a rule, add or update tests in the same change.

### Rule 4: use the coordinate convention from `THE_PLAN.md`
- `row 0 = rank 8`
- `row 7 = rank 1`
- `col 0 = file a`
- `col 7 = file h`
- `e2 = (6, 4)`
- white moves "up" the internal array (toward smaller rows)

### Rule 5: do not implement AI yet
Any AI code is blocked until all rules tasks are green.

---

## Phase 0 — Inspect and clean the foundation

### T0.1 Fix packaging/import basics
- [x] Make sure `pytest` can import the package from the repo root.
- [x] Remove duplicate or broken imports in `chess_game/main.py`.
- [x] Ensure all internal imports use a consistent package path, preferably `from chess_game.chess...`.
- [x] Add missing `__init__.py` files if needed.

**Acceptance criteria**
- Running `python -m pytest -q` from the repo root starts test collection without `ModuleNotFoundError`.

### T0.2 Freeze current scope
- [x] Update docs/comments so the immediate goal is a correct rules engine plus CLI.
- [x] Remove or downgrade "AI-powered" marketing language if the engine is not actually AI-capable yet.

**Acceptance criteria**
- README and top-level docs do not imply features that do not exist.

### T0.3 Remove invalid direct-mutation flow from CLI
Current `main.py` directly moves pieces on the board and flips turns without validation. That is wrong.

- [x] Replace raw board mutation in `main.py` with a call to a single engine method.
- [x] The CLI cannot make a move without validation.
- [x] The CLI does not directly assign `board[to] = piece`.
- [x] The CLI does not directly flip the turn.

**Acceptance criteria**
- The CLI cannot make a move without validation.
- The CLI does not directly assign `board[to] = piece`.
- The CLI does not directly flip the turn.

---

## Phase 1 — Define clean core types and conventions

### T1.1 Define `Piece` representation
The current board stores strings like `"Pawn"`, which loses color information.

- [x] Create an explicit piece representation.
- [x] It must encode both color and kind.
- [x] Used dataclass and enums as recommended.

**Recommended shape**
```python
@dataclass(frozen=True)
class Piece:
    color: Color
    kind: PieceType
```

### T1.2 Define square and move helpers

Create helper(s) for algebraic notation conversion.

Create helper(s) for bounds checking.

Create a Move type with optional promotion.

**Must support**
- `e2e4`
- `e7e8q`
- rejection of malformed inputs like `e9e4`, `abc`, `e2-e4`

**Acceptance criteria**
- `algebraic_to_index("e2")` returns `(6, 4)`
- `index_to_algebraic(6, 4)` returns `"e2"`
- `parse_algebraic_move("e2e4")` returns `((6, 4), (4, 4))`
- Canonical board orientation works correctly (row 0 = rank 8)
- Board cells can distinguish white pawn from black pawn.
- Tests can assert piece color and piece kind separately.
- Parsing tests exist and pass.

### T1.3 Rebuild starting position correctly

Ensure white major pieces are on rank 1 and white pawns on rank 2.

Ensure black major pieces are on rank 8 and black pawns on rank 7.

Use the canonical indexing convention.

**Required piece placement**
- White back rank on row 7
- White pawns on row 6
- Black pawns on row 1
- Black back rank on row 0

**Acceptance criteria**
- Tests verify a1, e1, d1, a8, e8, d8, e2, and e7 explicitly.

### T1.4 Add board helper methods

Add helpers for get/set/clear square.

Add a copy/clone method or equivalent immutable update path for simulation.

Add helper to find a king of a given color.

**Acceptance criteria**
- Code no longer depends on magic indexing everywhere.

## Phase 2 — Implement pseudo-legal movement rules

Pseudo-legal means the piece movement pattern is allowed without yet considering whether own king is left in check.

### T2.1 Create piece-specific movement helpers

- [x] Implemented rook, bishop, queen, knight, king, and pawn pseudo-legal move helpers.

 rook pseudo-legal move helper

 bishop pseudo-legal move helper

 queen pseudo-legal move helper

 knight pseudo-legal move helper

 king pseudo-legal move helper

 pawn pseudo-legal move helper

These helpers should answer questions like:

Is the shape correct?

Is the path clear?

Is the destination occupiable?

### T2.2 Implement reusable path-check logic for sliders

- [x] Added reusable straight-line path traversal helper used by rook, bishop, and queen.

 Add a helper for straight-line path traversal.

 Use it for rook, bishop, and queen.

**Acceptance criteria**

Rook, bishop, and queen do not jump over pieces.

Knight still ignores blockers.

### T2.3 Implement rook rules

- [x] Implemented and tested rook pseudo-legal movement rules.

 Allow horizontal/vertical movement only.

 Reject zero-length move.

 Reject blocked paths.

 Reject capture of friendly piece.

**Tests required**

 rook valid horizontal move

 rook valid vertical move

 rook blocked by friendly piece in path

 rook blocked by enemy piece before destination

 rook cannot move diagonally

 rook cannot capture friendly piece

### T2.4 Implement bishop rules

- [x] Implemented and tested bishop pseudo-legal movement rules.

 Allow diagonal movement only.

 Reject blocked diagonals.

 Reject zero-length move.

**Tests required**

 bishop valid diagonal move

 bishop blocked diagonal

 bishop cannot move straight

 bishop cannot capture friendly piece

### T2.5 Implement queen rules

- [x] Implemented and tested queen pseudo-legal movement rules.

 Allow rook-like and bishop-like movement only.

 Reuse tested helpers; do not duplicate logic badly.

**Tests required**

 queen straight move

 queen diagonal move

 queen blocked path

 queen illegal knight-like move

### T2.6 Implement knight rules

- [x] Implemented and tested knight pseudo-legal movement rules.

 Allow exactly (2,1) or (1,2) deltas.

 Knight ignores blockers between start and end.

**Tests required**

 knight valid L-move both orientations

 knight can jump over pieces

 knight illegal straight move

 knight illegal diagonal move

 knight cannot capture friendly piece

### T2.7 Implement king normal move rules

- [x] Implemented and tested king normal one-square pseudo-legal movement rules.

 Allow exactly one square in any direction for normal king moves.

 Reject zero-length move.

 Reject friendly capture.

**Tests required**

 king one-step orthogonal

 king one-step diagonal

 king cannot move two squares except castling path handled separately

### T2.8 Implement pawn rules carefully

- [x] Implemented comprehensive pawn movement rules including all special cases
- [x] Forward movement with one/two-square start options
- [x] Diagonal capturing with proper color validation
- [x] Backward movement rejection
- [x] En passant support and detection
- [x] All pawn-specific blocking conditions

This is where models often fail.

White pawn must do exactly this

 one forward from (r, c) to (r-1, c) if empty

 two forward from starting row 6 to (r-2, c) if both intermediate and destination empty

 capture diagonally to (r-1, c-1) or (r-1, c+1) if occupied by black piece

 never move backward

 never move diagonally into an empty square except en passant

 never move forward into an occupied square

Black pawn must do exactly this

 one forward from (r, c) to (r+1, c) if empty

 two forward from starting row 1 to (r+2, c) if both intermediate and destination empty

 capture diagonally to (r+1, c-1) or (r+1, c+1) if occupied by white piece

 never move backward

 never move diagonally into an empty square except en passant

 never move forward into an occupied square

**Tests required**

 white pawn one-step from e2 to e3

 white pawn two-step from e2 to e4

 white pawn blocked on one-step

 white pawn blocked on two-step intermediate square

 white pawn capture diagonally

 white pawn cannot capture forward

 white pawn cannot move backward

 black pawn one-step from e7 to e6

 black pawn two-step from e7 to e5

 black pawn diagonal capture

 black pawn cannot move backward

**Acceptance criteria**

Pawn direction matches the canonical orientation.

## Phase 3 — Implement legal move validation via king safety

A pseudo-legal move is not enough. Legal chess moves must not leave your own king in check.

### T3.1 Implement attack detection

- [x] Implemented `is_square_attacked(board, square, by_color)` with correct per-piece attack patterns.

 Add a function like is_square_attacked(board, square, by_color).

 It must evaluate whether a square is attacked by enemy pieces.

 Be careful with pawn attack patterns; pawn attacks are not the same as pawn forward moves.

**Tests required**

 rook attack on open file/rank

 bishop attack on open diagonal

 knight attack

 pawn attack squares for white

 pawn attack squares for black

 king adjacent attack

### T3.2 Implement is_in_check(color)

- [x] Implemented `is_in_check(color)` using king lookup plus attack detection.

 Locate the king for that color.

 Use attack detection to determine if the enemy attacks it.

**Tests required**

 simple check by rook

 simple check by bishop

 simple check by knight

 simple check by queen

### T3.3 Reject self-check moves

- [x] Implemented move simulation on a cloned board and rejection of moves that leave own king in check.

 Simulate candidate move on a copy of state.

 Reject move if mover’s king is in check after simulation.

**Tests required**

 pinned piece cannot move exposing king

 king cannot move into check

 blocking a check is allowed

 capturing the checking piece is allowed when it resolves check

**Acceptance criteria**

The engine distinguishes pseudo-legal from legal moves.

## Phase 4 — Special rules
### T4.1 Track castling rights explicitly

- [x] Added explicit castling-right state and updates for king moves, rook moves, and rook captures on original squares.

 Add explicit castling rights to game state.

 Initialize all four rights to true in the starting position.

 Update rights when king moves.

 Update rights when a rook moves from its original square.

 Update rights when a rook is captured on its original square if relevant.

**Acceptance criteria**

Rights never reappear once lost.

### T4.2 Implement castling move validation

- [x] Implemented castling validation and execution for all four castle types with king-safety checks.

 Support white kingside: e1g1

 Support white queenside: e1c1

 Support black kingside: e8g8

 Support black queenside: e8c8

Legal only if

 king has not moved

 relevant rook has not moved

 squares between king and rook are empty

 king is not currently in check

 king does not pass through attacked square

 king does not end on attacked square

**Tests required**

 white kingside castle legal case

 white queenside castle legal case

 black kingside castle legal case

 black queenside castle legal case

 cannot castle while in check

 cannot castle through check

 cannot castle into check

 cannot castle after king moved

 cannot castle after rook moved

 cannot castle if path blocked

### T4.3 Implement en passant state tracking

- [x] Added en_passant_target attribute to Board class
- [x] Set up proper tracking for pawn capture situations
- [x] State cleared after each move appropriately

Add en_passant_target to game state.

 Set it only after a legal two-square pawn advance.

 Clear it after one opponent turn if not used.

### T4.4 Implement en passant legality and capture

- [x] Implemented en passant capture validation
- [x] Proper detection of en passant opportunities
- [x] Capture logic for pawn movement validation
- [x] King safety validation still applies

Allow en passant only on the immediately following move.

 Remove the captured pawn from its actual square, not the destination square.

 Ensure king-safety validation still applies.

**Tests required**

 white en passant legal example

 black en passant legal example

 en passant expires after one turn

 en passant unavailable if last move was not a two-step pawn move

 en passant cannot be used if it leaves own king in check

### T4.5 Implement promotion

- [x] Detection when pawn reaches last rank
- [x] Support for promotion choice in parsed move input
- [x] Default to queen when unspecified
- [x] Proper piece replacement logic

Detect when a pawn reaches the last rank.

 Support promotion choice in parsed move input (q, r, b, n).

 If choice omitted, default to queen.

 Replace pawn with promoted piece.

**Tests required**

 white promotion to queen

 white promotion to knight

 black promotion to queen

 invalid promotion piece rejected

 default promotion is queen when unspecified

## Phase 5 — Game status detection
### T5.1 Generate all legal moves for side to move

- [x] Added legal move enumeration helper with promotion-aware move generation.

 Add a helper that enumerates all legal moves for a color or current side.

 This is needed for checkmate and stalemate.

**Tests required**

 position with multiple legal moves returns expected move count or at least expected move membership

### T5.2 Implement checkmate detection

- [x] Added `is_checkmate(side)` based on in-check + zero legal moves.

 is_checkmate(side) should return true only when side is in check and has zero legal moves.

**Tests required**

 Fool’s Mate or another simple forced mate position

 position in check but with one legal escape is not checkmate

### T5.3 Implement stalemate detection

- [x] Added `is_stalemate(side)` based on not-in-check + zero legal moves.

 is_stalemate(side) should return true only when side is not in check and has zero legal moves.

**Tests required**

 one classic stalemate position

 position with no check but one legal move is not stalemate

### T5.4 Optional later draw-state tasks

Do not implement unless earlier phases are complete.

 fifty-move rule

 threefold repetition

 insufficient material

## Phase 6 — Rewrite the current tests so they stop asserting nonsense

The existing tests are weak and in some cases based on broken assumptions.

### T6.1 Delete or rewrite invalid tests

 Remove tests that manually place pieces in contradictory locations without clearly documenting why.

 Remove tests that assume wrong board orientation.

 Remove tests that set turn just to make a broken move appear valid.

### T6.2 Add fixture helpers for clean board setup

 Create helper(s) to build an empty board.

 Create helper(s) to place only the pieces needed for a targeted rule test.

 Keep kings on the board when testing legal move generation unless the helper explicitly documents otherwise.

### T6.3 Organize test files by subject

Suggested structure:

 tests/test_coords.py

 tests/test_setup.py

 tests/test_piece_moves.py

 tests/test_legality.py

 tests/test_special_moves.py

 tests/test_game_status.py

 tests/test_cli_parsing.py

**Acceptance criteria**

Tests are readable enough that someone unfamiliar with the code can infer the intended rule from them.

## Phase 7 — CLI cleanup
### T7.1 Fix move parsing in main.py

The current parser is wrong because it slices move[2:4] and move[4:6] for a 4-character move string.

 Parse 4-char coordinate moves correctly.

 Parse optional 5th char promotion piece.

 Reject malformed move strings with a good message.

**Examples**

valid: e2e4, g1f3, e7e8q

invalid: e2, e2-e4, hello, e9e4, a1a1

### T7.2 Improve board display

 Display ranks 8 to 1 top to bottom.

 Display files a to h left to right.

 Display distinguishable symbols/codes for white and black pieces.

### T7.3 Improve user feedback

 On illegal move, explain why if practical.

 Show side to move.

 After each move, show whether the next side is in check.

 End the game cleanly on checkmate or stalemate.

## Phase 8 — Documentation cleanup
### T8.1 Update README

 Describe the current real capabilities.

 Explain how to run tests.

 Explain move input format.

 State clearly that correctness comes before AI.

### T8.2 Add developer notes

 Briefly document coordinate conventions.

 Briefly document pseudo-legal vs legal move distinction.

 Briefly document how castling rights and en passant state are stored.

## Phase 9 — Only after all rules tests are green

Do not start this phase until every earlier acceptance criterion is met.

### T9.1 Optional AI baseline

 legal move generation hookup

 material-only evaluation

 shallow minimax

### T9.2 Optional GUI

 render board

 click-to-move

 show legal moves

These are intentionally last.

## Mandatory regression checklist

Before declaring the repo "fixed," verify all of these:

 python -m pytest -q passes

 start position is correct

 white pawn from e2 can play e3 and e4

 black pawn from e7 can play e6 and e5

 rooks/bishops/queens do not jump pieces

 knights can jump pieces

 friendly captures are rejected

 moving opponent piece is rejected

 self-check moves are rejected

 king cannot move into check

 castling works and illegal castling is rejected

 en passant works and expires correctly

 promotion works

 checkmate example works

 stalemate example works

 CLI uses validated engine API only

## Advice to the coding model working on this repo

When in doubt:

add a test,

write the simpler implementation,

simulate the move on a copy,

verify king safety,

avoid clever shortcuts.

The main risk in this repo is quietly wrong chess logic. Optimize for correctness, not speed.