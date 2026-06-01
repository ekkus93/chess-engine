# replies4.md

## Opening Book Implementation Clarifications

Here are the answers for Copilot.

I also checked the current repo shape directly where the questions depend on actual code.

---

## 1. Position key implementation

Use the existing **public** helper:

```python
from chess_game.chess.position_utils import position_key
```

Do **not** import private `_position_key()` from `ai.py`.

Current repo already has:

```python
chess_game/chess/position_utils.py

def position_key(board: Board) -> str:
    ...
```

`ai.py` also exposes `position_key(board)`, but the cleaner dependency direction is:

```text
opening_book.py -> position_utils.py
```

not:

```text
opening_book.py -> ai.py
```

That avoids making the opening-book module depend on the AI/search module. Copilot’s question about public vs private position-key usage is exactly right; use the public helper.

---

## 2. Move notation parsing

Yes. `parse_move_notation()` already exists and handles coordinate notation including promotions.

Current file:

```text
chess_game/chess/move.py
```

Current behavior:

```python
parse_move_notation("e2e4")
parse_move_notation("e7e8q")
parse_move_notation("e7e8r")
parse_move_notation("e7e8b")
parse_move_notation("e7e8n")
```

It accepts promotion suffixes:

```text
q, r, b, n
```

and maps them to `PieceType.QUEEN`, `PieceType.ROOK`, `PieceType.BISHOP`, and `PieceType.KNIGHT`.

Still verify it with a small unit test or existing tests before Task 2, but do **not** write a new parser.

---

## 3. Legal move type

Use the dataclass from:

```python
from chess_game.chess.types import LegalMove
```

Current shape:

```python
@dataclass
class LegalMove:
    start: ConstantSquare
    end: ConstantSquare
    promotion: Optional[PieceType] = None
```

There is also an older local alias in `board.py`:

```python
LegalMove = tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]
```

Avoid introducing more tuple-based ambiguity. For new opening-book code, use the dataclass `chess_game.chess.types.LegalMove`.

When validating against `board.get_legal_moves()`, adapt if that API returns tuple-style moves in some paths. Normalize both forms with a tiny helper if needed:

```python
def move_identity(move) -> tuple[ConstantSquare, ConstantSquare, PieceType | None]:
    if isinstance(move, LegalMove):
        return move.start, move.end, move.promotion
    start, end, promotion = move
    return start, end, promotion
```

Book identity must include:

```text
start
end
promotion
```

Do not compare only start/end.

---

## 4. Package data configuration

Yes, update `pyproject.toml` to explicitly include the JSON file.

The current `pyproject.toml` uses setuptools package discovery, but I did not see an existing package-data pattern for JSON files. Add something like:

```toml
[tool.setuptools.package-data]
"chess_game.chess" = ["data/*.json"]
```

Use `importlib.resources`, not `pkgutil`.

Recommended loader:

```python
from importlib import resources

with resources.files("chess_game.chess").joinpath("data/opening_book.json").open(
    "r", encoding="utf-8"
) as f:
    data = json.load(f)
```

This works for installed packages and is the modern approach.

---

## 5. Caching strategy

Use `@lru_cache(maxsize=1)`, not a module-import singleton.

Recommended:

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_bundled_opening_book() -> OpeningBook:
    return OpeningBook.bundled()
```

Reason:

```text
lru_cache avoids repeated JSON parsing.
It delays loading until the book is actually needed.
It avoids import-time failure if some tests import modules without needing the book.
It is easy to clear in tests with get_bundled_opening_book.cache_clear().
```

Do not load the bundled book at module import time.

---

## 6. Default parameters in `get_best_move()`

Use this default:

```python
use_opening_book: bool = True
```

That matches the feature goal: the engine should naturally use the opening book.

But existing AI/search tests should be updated to pass:

```python
use_opening_book=False
```

when they are testing minimax, alpha-beta, TT, evaluation, or search behavior.

So:

```text
Game behavior default: book enabled.
Search/unit-test behavior: explicitly disable the book.
```

This keeps the engine user-facing behavior useful while preserving deterministic search tests.

---

## 7. Coordinate notation casing

Bundled JSON should use **lowercase coordinate notation only**.

The parser lowercases the promotion suffix, but square parsing should not rely on uppercase support unless verified. Keep the data normalized:

```text
e2e4
g1f3
e7e8q
```

Do not put uppercase moves in `opening_book.json`.

For custom files, it is okay to normalize input with:

```python
move_text = move_text.strip().lower()
```

before parsing, but error messages should still mention the original input text if it fails.

---

## 8. King’s Gambit weighting and selection

The deterministic rule is:

```text
For the current position, find all book candidate moves.
Filter to legal candidates.
Pick highest weight.
Tie-break by line_index, then ply_index, then coordinate move string.
```

So yes: after:

```text
e2e4 e7e5
```

if multiple White book candidates exist, the highest-weight move will be selected by `find_book_move()`.

That means King’s Gambit `f2f4` will only be selected at that position if it has the highest weight among candidates for that exact position.

If you want to guarantee a King’s Gambit test, test it with:

```python
candidates_for(board)
```

and assert that `f2f4` is present. Do **not** require `find_book_move()` to choose King’s Gambit unless you deliberately weight King’s Gambit highest for that position.

For transpositions or duplicate candidates, keep candidates separate internally but deterministic. Do not coalesce in v1. If the same exact move appears multiple times for the same position, the highest-weight/earliest-line candidate wins through the normal sort. This is simpler and easier to debug.

---

## 9. Black defense indexing

Yes: Black defenses should be normal lines starting from the initial position.

Example:

```json
{
  "name": "Sicilian Defense",
  "side": "black",
  "moves": ["e2e4", "c7c5"],
  "weight": 100
}
```

Replay logic handles this correctly:

1. Start from initial board.
2. Before `e2e4`, index the initial White-to-move position with candidate `e2e4`.
3. Apply `e2e4`.
4. Before `c7c5`, index the Black-to-move position after `1. e4` with candidate `c7c5`.
5. Apply `c7c5`.

So Sicilian appears only after White has played `e2e4`. Queen’s Gambit Declined appears only after the relevant `d2d4 d7d5 c2c4` position. They are context-dependent by construction.

---

## 10. Error message format

The format is flexible, but it must include the debugging fields.

Use a consistent template like:

```python
raise OpeningBookError(
    f"Invalid opening book move {move_text!r} "
    f"in line {line.name!r} "
    f"(line_index={line_index}, ply_index={ply_index}): {reason}"
)
```

For schema errors before an `OpeningLine` exists:

```python
raise OpeningBookError(
    f"Invalid opening book line at line_index={line_index}: {reason}"
)
```

Do not overbuild a structured error class unless it is useful. A clear `OpeningBookError` string is enough for v1.

---

## Final implementation guidance

Proceed with the spec as written, with these clarifications:

```text
1. Use chess_game.chess.position_utils.position_key.
2. Use existing parse_move_notation(); do not write a new parser.
3. Use chess_game.chess.types.LegalMove for book moves.
4. Include opening_book.json via setuptools package-data.
5. Use importlib.resources for bundled loading.
6. Use @lru_cache(maxsize=1) for bundled book caching.
7. Default get_best_move(..., use_opening_book=True).
8. Update search tests to pass use_opening_book=False.
9. Keep JSON move notation lowercase.
10. For King’s Gambit tests, use candidates_for() unless it is weighted highest.
11. Black defenses are indexed naturally by replaying full lines from the initial board.
12. Use clear OpeningBookError messages with line index, name, ply, move, and reason.
```

This is enough for Copilot to start implementation cleanly.
