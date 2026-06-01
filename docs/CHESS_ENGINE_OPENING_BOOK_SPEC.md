# CHESS_ENGINE_OPENING_BOOK_SPEC.md

## Purpose

Add a data-driven opening book to the chess engine.

The opening book should contain curated opening lines for White and defensive systems for Black. It should be easy to extend later by editing a JSON data file, not by changing engine code.

The book must be separate from evaluation, minimax, alpha-beta pruning, transposition-table logic, and move ordering. The search engine should remain honest: the opening book is checked before search, and if no book move exists, the engine falls back to the existing AI search.

---

## Goals

1. Add opening-book support for the chess engine.
2. Seed the book with:
   - 10 common White openings.
   - 10 common Black defenses.
   - King’s Gambit as a White opening family.
3. Store openings/defenses in a JSON file.
4. Validate book lines at load time using the engine’s legal move system.
5. Build a position-to-book-move index by replaying book lines from the starting position.
6. Make book move selection deterministic in v1:
   - choose the highest-weight legal book move.
   - use stable tie-breaking for equal weights.
7. Integrate with `get_best_move()` before minimax/search.
8. Preserve existing AI behavior when no book move is available.
9. Add tests for loading, validation, move lookup, integration, and fallback.

---

## Non-goals

Do **not** do any of the following in this pass:

- Do not tune board evaluation.
- Do not change material values.
- Do not change piece-square tables.
- Do not change minimax.
- Do not change alpha-beta pruning.
- Do not change TT semantics.
- Do not add quiescence search.
- Do not add UCI support.
- Do not add PGN import/export unless needed for a tiny helper.
- Do not implement a giant external database.
- Do not add weighted-random book selection in v1.
- Do not make the book depend on move history only.
- Do not hardcode opening logic inside `ai.py`.
- Do not add more strategy-guidance heuristics for openings.

---

## Recommended file layout

Add these files:

```text
chess_game/chess/opening_book.py
chess_game/chess/data/opening_book.json
tests/test_opening_book.py
docs/CHESS_ENGINE_OPENING_BOOK_SPEC.md
docs/CHESS_ENGINE_OPENING_BOOK_TODO.md
```

Optional, only if the repo already has a better data/package pattern:

```text
chess_game/chess/openings/
chess_game/chess/openings/book.py
chess_game/chess/openings/data/opening_book.json
```

Prefer the simplest layout unless the current repo strongly suggests otherwise.

---

## Core design

### Opening book lookup flow

The AI entry point should do:

```text
get_best_move(board, depth, ...)
  1. If opening book is enabled:
       find a legal book move for current board.
       if found, return it.
  2. Otherwise run existing search.
```

Book lookup should be fast and side-aware.

### Opening book should use position keys

Do **not** match by raw move history only.

Instead:

1. Load each opening line.
2. Start from a fresh `Board()`.
3. Before each move in the line:
   - compute the current position key.
   - store the next move as a candidate book move for that position.
4. Apply the move on the replay board.
5. Continue until the line ends.

This creates:

```text
position_key(board) -> candidate book moves
```

This allows transpositions to work later if multiple lines reach the same position.

### Position key

Use the engine’s existing position-key helper if available, preferably the same helper used by the transposition table.

The key must include at least:

```text
piece placement
side to move
castling rights
en passant target
```

It does not need to be full FEN with halfmove/fullmove counters for opening-book lookup.

If the existing helper is private, either:

- safely import it if that is already normal in the codebase, or
- expose a small public helper such as `position_key(board)`.

Do not duplicate inconsistent board-key logic.

---

## JSON data format

Use this v1 schema:

```json
{
  "version": 1,
  "selection": "highest_weight",
  "lines": [
    {
      "name": "Italian Game",
      "side": "white",
      "eco": "C50",
      "moves": ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"],
      "weight": 100,
      "tags": ["open-game", "classical"]
    }
  ]
}
```

### Field meanings

```text
version:
  integer schema version. v1 for initial implementation.

selection:
  default selection mode. v1 should support "highest_weight".

lines:
  list of opening/defense lines.

name:
  human-readable opening/defense name.

side:
  "white", "black", or "both".
  This is descriptive metadata and can also be used for filtering/reporting.
  The actual side to move is determined from the replayed board.

eco:
  optional ECO code string if known.

moves:
  required list of coordinate move strings.
  Use the engine’s existing coordinate notation:
    e2e4
    g1f3
    e7e8q
  Do not use SAN such as Nf3 or O-O in v1.

weight:
  positive integer priority.
  Higher weight wins in deterministic selection.

tags:
  optional list of metadata tags.
```

### Move notation

Use the engine’s existing `parse_move_notation()` coordinate format:

```text
e2e4
e7e5
g1f3
b8c6
e7e8q
```

Do not support SAN in v1:

```text
Nf3
O-O
exd5
Qh5+
```

SAN support can be added later if desired.

---

## Book move candidate model

Internally, represent book candidates with a dataclass or equivalent:

```python
@dataclass(frozen=True)
class BookMove:
    move: LegalMove
    name: str
    eco: str | None
    weight: int
    line_index: int
    ply_index: int
    tags: tuple[str, ...] = ()
```

Use the repo’s actual legal-move tuple/object type. Preserve promotion identity.

Candidate identity must include:

```text
start
end
promotion
```

Do not collapse promotion alternatives by start/end only.

---

## Selection policy v1

Use deterministic highest-weight selection.

Algorithm:

```text
1. Compute position key.
2. Get all candidate book moves for that key.
3. Filter candidates to currently legal moves.
4. If no legal candidates remain, return None.
5. Choose candidate with highest weight.
6. For ties, choose stable deterministic tie-break:
   - lower line_index first,
   - then lower ply_index,
   - then coordinate move string.
```

This gives reproducible tests.

### Future selection policy

Weighted randomness can come later, but not in v1.

Future options:

```text
book_random=True
book_seed=...
selection="weighted_random"
```

Do not add this now unless explicitly requested later.

---

## Validation requirements

The book loader must validate every line.

### Required validation

For each line:

1. `moves` must be a non-empty list.
2. `weight` must be a positive integer.
3. `name` must be non-empty.
4. `side` must be one of:
   - `"white"`
   - `"black"`
   - `"both"`
5. Every move string must parse with `parse_move_notation()`.
6. Every move must be legal when replayed on a fresh `Board()`.
7. Applying the full line must not raise.
8. Duplicate candidate moves for the same position are allowed only if they merge cleanly or remain deterministic.
9. Illegal lines must produce a clear error.

### Invalid data behavior

Prefer fail-fast behavior for bundled book data:

```text
If bundled opening_book.json contains illegal lines, raise OpeningBookError at load/build time.
```

For optional custom book files later, this can become configurable, but v1 should fail loudly.

### Book-move safety at lookup time

Even though lines are validated at load time, lookup must still filter by current legal moves. This prevents stale/corrupt data from returning illegal moves.

---

## Integration with AI

### Preferred API

Add optional parameters to `get_best_move()`:

```python
def get_best_move(
    board: Board,
    depth: int = 3,
    *,
    use_opening_book: bool = True,
    opening_book: OpeningBook | None = None,
    ...
) -> LegalMove | None:
    ...
```

If the current function signature already has many arguments, adapt carefully.

### Default behavior

Recommended default:

```text
use_opening_book=True
```

This makes the engine naturally play book openings.

If tests become difficult, allow tests to pass `use_opening_book=False`.

### Search fallback

If no book move exists:

```text
return normal search result
```

Do not return `None` unless the search would also return `None`.

### Search stats

If the engine has `SearchStats`, book moves should not pretend to be searched nodes.

Optional but recommended:

```text
stats.book_hits += 1
```

Only add this if it fits the current stats design without broad refactoring.

---

## Initial White opening book

Seed at least these 10 White openings.

Use practical short lines, typically 4–8 plies, not giant theory trees.

### 1. Italian Game

```json
{
  "name": "Italian Game",
  "side": "white",
  "eco": "C50",
  "moves": ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"],
  "weight": 100,
  "tags": ["white", "open-game", "classical"]
}
```

### 2. Ruy Lopez

```json
{
  "name": "Ruy Lopez",
  "side": "white",
  "eco": "C60",
  "moves": ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
  "weight": 95,
  "tags": ["white", "open-game", "classical"]
}
```

### 3. Queen's Gambit

```json
{
  "name": "Queen's Gambit",
  "side": "white",
  "eco": "D06",
  "moves": ["d2d4", "d7d5", "c2c4"],
  "weight": 95,
  "tags": ["white", "closed-game", "gambit"]
}
```

### 4. London System

```json
{
  "name": "London System",
  "side": "white",
  "eco": "D02",
  "moves": ["d2d4", "d7d5", "c1f4", "g8f6", "e2e3"],
  "weight": 80,
  "tags": ["white", "system"]
}
```

### 5. Scotch Game

```json
{
  "name": "Scotch Game",
  "side": "white",
  "eco": "C44",
  "moves": ["e2e4", "e7e5", "g1f3", "b8c6", "d2d4"],
  "weight": 75,
  "tags": ["white", "open-game"]
}
```

### 6. King's Gambit

```json
{
  "name": "King's Gambit",
  "side": "white",
  "eco": "C30",
  "moves": ["e2e4", "e7e5", "f2f4"],
  "weight": 70,
  "tags": ["white", "open-game", "gambit", "aggressive"]
}
```

### 7. Vienna Game

```json
{
  "name": "Vienna Game",
  "side": "white",
  "eco": "C25",
  "moves": ["e2e4", "e7e5", "b1c3"],
  "weight": 65,
  "tags": ["white", "open-game"]
}
```

### 8. English Opening

```json
{
  "name": "English Opening",
  "side": "white",
  "eco": "A10",
  "moves": ["c2c4"],
  "weight": 60,
  "tags": ["white", "flank-opening"]
}
```

### 9. Réti / Zukertort Opening

```json
{
  "name": "Reti Opening",
  "side": "white",
  "eco": "A04",
  "moves": ["g1f3", "d7d5", "c2c4"],
  "weight": 55,
  "tags": ["white", "flank-opening"]
}
```

### 10. Catalan Opening

```json
{
  "name": "Catalan Opening",
  "side": "white",
  "eco": "E00",
  "moves": ["d2d4", "g8f6", "c2c4", "e7e6", "g2g3"],
  "weight": 55,
  "tags": ["white", "closed-game", "fianchetto"]
}
```

---

## King's Gambit family additions

Include these as additional White book lines so the engine knows common continuations.

### King's Gambit Accepted: King's Knight Gambit

```json
{
  "name": "King's Gambit Accepted: King's Knight Gambit",
  "side": "white",
  "eco": "C34",
  "moves": ["e2e4", "e7e5", "f2f4", "e5f4", "g1f3"],
  "weight": 80,
  "tags": ["white", "king-gambit", "accepted"]
}
```

### King's Gambit Accepted: Bishop's Gambit

```json
{
  "name": "King's Gambit Accepted: Bishop's Gambit",
  "side": "white",
  "eco": "C33",
  "moves": ["e2e4", "e7e5", "f2f4", "e5f4", "f1c4"],
  "weight": 45,
  "tags": ["white", "king-gambit", "accepted"]
}
```

### King's Gambit Accepted: Classical Defense Setup

```json
{
  "name": "King's Gambit Accepted: Classical Defense Setup",
  "side": "white",
  "eco": "C34",
  "moves": ["e2e4", "e7e5", "f2f4", "e5f4", "g1f3", "g7g5", "f1c4"],
  "weight": 65,
  "tags": ["white", "king-gambit", "accepted"]
}
```

### King's Gambit Accepted: Fischer Defense

```json
{
  "name": "King's Gambit Accepted: Fischer Defense",
  "side": "white",
  "eco": "C34",
  "moves": ["e2e4", "e7e5", "f2f4", "e5f4", "g1f3", "d7d6", "d2d4"],
  "weight": 65,
  "tags": ["white", "king-gambit", "accepted"]
}
```

### King's Gambit Declined: Classical

```json
{
  "name": "King's Gambit Declined: Classical",
  "side": "white",
  "eco": "C30",
  "moves": ["e2e4", "e7e5", "f2f4", "f8c5", "g1f3"],
  "weight": 55,
  "tags": ["white", "king-gambit", "declined"]
}
```

### King's Gambit Declined: Falkbeer Countergambit

```json
{
  "name": "King's Gambit Declined: Falkbeer Countergambit",
  "side": "white",
  "eco": "C31",
  "moves": ["e2e4", "e7e5", "f2f4", "d7d5", "e4d5"],
  "weight": 55,
  "tags": ["white", "king-gambit", "declined"]
}
```

---

## Initial Black defense book

Seed at least these 10 Black defenses.

### 1. Sicilian Defense

```json
{
  "name": "Sicilian Defense",
  "side": "black",
  "eco": "B20",
  "moves": ["e2e4", "c7c5"],
  "weight": 100,
  "tags": ["black", "vs-e4", "asymmetrical"]
}
```

### 2. French Defense

```json
{
  "name": "French Defense",
  "side": "black",
  "eco": "C00",
  "moves": ["e2e4", "e7e6"],
  "weight": 90,
  "tags": ["black", "vs-e4"]
}
```

### 3. Caro-Kann Defense

```json
{
  "name": "Caro-Kann Defense",
  "side": "black",
  "eco": "B10",
  "moves": ["e2e4", "c7c6"],
  "weight": 90,
  "tags": ["black", "vs-e4", "solid"]
}
```

### 4. Open Game / Double King's Pawn

```json
{
  "name": "Open Game",
  "side": "black",
  "eco": "C20",
  "moves": ["e2e4", "e7e5"],
  "weight": 85,
  "tags": ["black", "vs-e4", "classical"]
}
```

### 5. Scandinavian Defense

```json
{
  "name": "Scandinavian Defense",
  "side": "black",
  "eco": "B01",
  "moves": ["e2e4", "d7d5"],
  "weight": 60,
  "tags": ["black", "vs-e4"]
}
```

### 6. Pirc Defense

```json
{
  "name": "Pirc Defense",
  "side": "black",
  "eco": "B07",
  "moves": ["e2e4", "d7d6", "d2d4", "g8f6"],
  "weight": 55,
  "tags": ["black", "vs-e4", "hypermodern"]
}
```

### 7. Queen's Gambit Declined

```json
{
  "name": "Queen's Gambit Declined",
  "side": "black",
  "eco": "D30",
  "moves": ["d2d4", "d7d5", "c2c4", "e7e6"],
  "weight": 95,
  "tags": ["black", "vs-d4", "solid"]
}
```

### 8. Slav Defense

```json
{
  "name": "Slav Defense",
  "side": "black",
  "eco": "D10",
  "moves": ["d2d4", "d7d5", "c2c4", "c7c6"],
  "weight": 90,
  "tags": ["black", "vs-d4", "solid"]
}
```

### 9. King's Indian Defense

```json
{
  "name": "King's Indian Defense",
  "side": "black",
  "eco": "E60",
  "moves": ["d2d4", "g8f6", "c2c4", "g7g6"],
  "weight": 80,
  "tags": ["black", "vs-d4", "hypermodern"]
}
```

### 10. Nimzo-Indian Defense

```json
{
  "name": "Nimzo-Indian Defense",
  "side": "black",
  "eco": "E20",
  "moves": ["d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4"],
  "weight": 85,
  "tags": ["black", "vs-d4", "indian-defense"]
}
```

---

## Testing requirements

Add `tests/test_opening_book.py`.

Tests should cover:

1. Bundled JSON loads successfully.
2. All bundled lines are legal.
3. Starting position returns a White book move.
4. After `e2e4`, Black can return a defense move.
5. After `e2e4 e7e5`, White can return King's Gambit `f2f4` when King's Gambit has highest applicable priority for that position or when testing its specific line lookup.
6. King's Gambit Accepted line returns `g1f3` after:

   ```text
   e2e4 e7e5 f2f4 e5f4
   ```

7. Illegal book line raises a clear `OpeningBookError`.
8. Unknown/non-book position returns `None`.
9. Book move is legal in the current position.
10. `get_best_move(..., use_opening_book=True)` returns a book move when available.
11. `get_best_move(..., use_opening_book=False)` falls back to search.
12. Promotion identity is preserved if a future book line includes promotion.
13. Duplicate candidate/tie-breaking behavior is deterministic.

---

## CLI/self-play integration

If the engine has CLI or self-play entry points that call `get_best_move()`, they may automatically benefit from the default opening book.

If command-line flags are easy, add optional flags:

```text
--no-opening-book
--opening-book path/to/custom.json
```

Do not overbuild this in v1. If CLI integration is messy, limit this pass to engine/API integration and tests.

---

## Error handling

Add a custom exception:

```python
class OpeningBookError(ValueError):
    pass
```

Use it for:

- invalid JSON structure,
- illegal move in a line,
- empty move list,
- invalid weight,
- invalid side,
- parse failure.

Error messages should include:

```text
line name
line index
move string
ply index
reason
```

---

## Documentation

Update README or docs with:

```text
Opening book:
- JSON file location.
- Coordinate move notation.
- How to add a new line.
- How weights work.
- Current selection policy: highest weight.
- Search fallback behavior.
```

Keep docs concise.

---

## Acceptance criteria

This feature is complete when:

1. `opening_book.py` exists and is separate from AI search logic.
2. `opening_book.json` exists and contains at least:
   - 10 White openings,
   - 10 Black defenses,
   - King's Gambit family lines.
3. The bundled book validates successfully.
4. Book lookup uses position keys, not raw move-history-only matching.
5. Book lookup returns only legal moves.
6. `get_best_move()` consults the book before search when enabled.
7. `get_best_move(..., use_opening_book=False)` bypasses the book.
8. Unknown positions fall back to search.
9. Tests cover loading, validation, lookup, King's Gambit, integration, and fallback.
10. Existing rules/search tests still pass.
