# CHESS_ENGINE_OPENING_BOOK_TODO.md

## Goal

Add a simple, data-driven opening book to the chess engine.

The book should contain common White openings and Black defenses, including King's Gambit for White. The book must be easy to extend by editing JSON.

Do not bury book logic inside evaluation, minimax, alpha-beta, TT, or move ordering.

---

## Task 0: Establish baseline

### 0.1 Run fast baseline tests

Run:

```bash
python -m pytest tests -q -m "not slow"
```

- [ ] Confirm the fast suite passes before changes.
- [ ] If it does not pass, stop and inspect failures first.

### 0.2 Run rules subset

Run:

```bash
python -m pytest tests/test_board_api.py tests/test_piece_moves.py tests/test_castling.py tests/test_en_passant.py tests/test_promotion.py tests/test_promotion_validation.py tests/test_promotion_move_generation.py tests/test_check_checkmate_stalemate.py tests/test_legal_moves.py -q
```

- [ ] Confirm rules baseline passes.

### 0.3 Add handoff docs

- [ ] Copy the spec into:

  ```text
  docs/CHESS_ENGINE_OPENING_BOOK_SPEC.md
  ```

- [ ] Copy this TODO into:

  ```text
  docs/CHESS_ENGINE_OPENING_BOOK_TODO.md
  ```

---

## Task 1: Inspect current AI entry points and position-key helpers

### 1.1 Locate `get_best_move`

- [ ] Inspect:

  ```text
  chess_game/chess/ai.py
  ```

- [ ] Find the public `get_best_move(...)` signature.
- [ ] Note existing keyword arguments and tests that call it.
- [ ] Do not break existing callers.

### 1.2 Locate move parser and legal move type

- [ ] Find `parse_move_notation(...)`.
- [ ] Confirm it supports coordinate notation:

  ```text
  e2e4
  e7e5
  e7e8q
  ```

- [ ] Confirm the legal move representation:
  - tuple,
  - dataclass,
  - named tuple,
  - or other.

### 1.3 Locate position-key helper

- [ ] Search:

  ```bash
  grep -R "def _position_key\|def position_key\|def _fen_key" -n chess_game
  ```

- [ ] Prefer reusing the same position-key logic used by the transposition table.
- [ ] If helper is private but stable, either:
  - import it with minimal churn, or
  - expose a public wrapper.

### 1.4 Confirm package data approach

- [ ] Inspect `pyproject.toml`.
- [ ] Confirm how JSON package data should be included.
- [ ] If needed, add package-data config so `opening_book.json` is included when installed.

---

## Task 2: Add opening book data file

### 2.1 Create data directory

- [ ] Add:

  ```text
  chess_game/chess/data/
  ```

- [ ] Add `__init__.py` only if the repo/package style requires it.

### 2.2 Create JSON file

- [ ] Add:

  ```text
  chess_game/chess/data/opening_book.json
  ```

### 2.3 Add top-level JSON structure

Use:

```json
{
  "version": 1,
  "selection": "highest_weight",
  "lines": []
}
```

### 2.4 Add 10 White opening lines

Add at least:

- [ ] Italian Game
- [ ] Ruy Lopez
- [ ] Queen's Gambit
- [ ] London System
- [ ] Scotch Game
- [ ] King's Gambit
- [ ] Vienna Game
- [ ] English Opening
- [ ] Reti Opening
- [ ] Catalan Opening

Use coordinate notation only.

### 2.5 Add King's Gambit family lines

Add these additional lines:

- [ ] King's Gambit Accepted: King's Knight Gambit
- [ ] King's Gambit Accepted: Bishop's Gambit
- [ ] King's Gambit Accepted: Classical Defense Setup
- [ ] King's Gambit Accepted: Fischer Defense
- [ ] King's Gambit Declined: Classical
- [ ] King's Gambit Declined: Falkbeer Countergambit

### 2.6 Add 10 Black defense lines

Add at least:

- [ ] Sicilian Defense
- [ ] French Defense
- [ ] Caro-Kann Defense
- [ ] Open Game
- [ ] Scandinavian Defense
- [ ] Pirc Defense
- [ ] Queen's Gambit Declined
- [ ] Slav Defense
- [ ] King's Indian Defense
- [ ] Nimzo-Indian Defense

### 2.7 Validate JSON syntax

Run:

```bash
python -m json.tool chess_game/chess/data/opening_book.json >/dev/null
```

- [ ] Confirm valid JSON.

---

## Task 3: Implement `opening_book.py`

### 3.1 Add module

- [ ] Create:

  ```text
  chess_game/chess/opening_book.py
  ```

### 3.2 Add exception

- [ ] Add:

  ```python
  class OpeningBookError(ValueError):
      pass
  ```

### 3.3 Add dataclasses

- [ ] Add a parsed line dataclass if useful:

  ```python
  @dataclass(frozen=True)
  class OpeningLine:
      name: str
      side: str
      eco: str | None
      moves: tuple[str, ...]
      weight: int
      tags: tuple[str, ...]
  ```

- [ ] Add a book move dataclass:

  ```python
  @dataclass(frozen=True)
  class BookMove:
      move: LegalMove
      name: str
      eco: str | None
      weight: int
      line_index: int
      ply_index: int
      tags: tuple[str, ...]
  ```

- [ ] Adapt type annotations to the repo’s actual legal move type.

### 3.4 Add JSON loader

Implement:

```python
def load_opening_book_data(path: Path | None = None) -> dict:
    ...
```

Requirements:

- [ ] If `path is None`, load bundled JSON using `importlib.resources`.
- [ ] If `path` is provided, load from that file.
- [ ] Raise `OpeningBookError` on invalid JSON/data.

### 3.5 Add parser/validator for raw JSON

Implement:

```python
def parse_opening_lines(data: Mapping[str, object]) -> list[OpeningLine]:
    ...
```

Validation:

- [ ] `version == 1`.
- [ ] `lines` exists and is a list.
- [ ] each line has non-empty `name`.
- [ ] `side` is `"white"`, `"black"`, or `"both"`.
- [ ] `moves` is a non-empty list of strings.
- [ ] `weight` is a positive integer.
- [ ] `eco` is optional string or null.
- [ ] `tags` is optional list of strings.

### 3.6 Add opening book class

Implement:

```python
class OpeningBook:
    @classmethod
    def from_file(cls, path: Path | str) -> "OpeningBook": ...

    @classmethod
    def bundled(cls) -> "OpeningBook": ...

    def find_book_move(self, board: Board) -> LegalMove | None: ...

    def candidates_for(self, board: Board) -> list[BookMove]: ...
```

### 3.7 Build position index

During construction:

- [ ] For each line, start from `Board()`.
- [ ] For each move in the line:
  - [ ] compute `position_key(board)`.
  - [ ] parse the next move string.
  - [ ] verify parsed move is legal in current position.
  - [ ] store a `BookMove` candidate for that current position.
  - [ ] apply the move to the replay board.
- [ ] Include `line_index` and `ply_index`.
- [ ] Preserve promotion identity.

### 3.8 Validate moves during replay

For each move:

- [ ] `parse_move_notation(move_text)` must succeed.
- [ ] The move must appear in legal moves or `board.make_move(...)` must return `True`.
- [ ] Prefer checking legal moves first so errors are clear.
- [ ] If illegal, raise `OpeningBookError` with:
  - line index,
  - line name,
  - ply index,
  - move string,
  - reason.

### 3.9 Legal filtering at lookup time

In `find_book_move(board)`:

- [ ] compute position key.
- [ ] get candidates.
- [ ] filter candidates to current legal moves.
- [ ] compare move identity by:
  - start,
  - end,
  - promotion.
- [ ] return `None` if no legal candidates.

### 3.10 Deterministic highest-weight selection

Sort candidates by:

```text
highest weight first
lowest line_index
lowest ply_index
coordinate move string
```

- [ ] Return the first sorted legal candidate.
- [ ] Do not add weighted randomness in v1.

---

## Task 4: Integrate with `get_best_move`

### 4.1 Add optional parameters

Update `get_best_move(...)` carefully.

Preferred shape:

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

- [ ] Preserve existing parameters.
- [ ] Keep backward compatibility where possible.

### 4.2 Check book before search

At the top of `get_best_move()` after basic depth validation and terminal/no-legal-move handling as appropriate:

- [ ] If `use_opening_book` is true:
  - [ ] use provided `opening_book`, or load bundled book.
  - [ ] call `find_book_move(board)`.
  - [ ] if book move found, return it.

### 4.3 Avoid repeated expensive loading

Do not parse the bundled JSON from disk on every move if avoidable.

Options:

- [ ] module-level cached `OpeningBook.bundled()`,
- [ ] `functools.lru_cache`,
- [ ] caller-provided `opening_book`.

Recommended:

```python
@lru_cache(maxsize=1)
def get_bundled_opening_book() -> OpeningBook:
    return OpeningBook.bundled()
```

### 4.4 Fallback to search

If no book move exists:

- [ ] run existing search unchanged.
- [ ] do not return `None` unless there are no legal moves or search would return `None`.

### 4.5 Tests can disable book

Ensure tests can call:

```python
get_best_move(board, depth=1, use_opening_book=False)
```

so existing search tests are not affected by book choices.

---

## Task 5: Optional CLI/self-play flags

Do this only if easy and low-risk.

### 5.1 Add disable flag

If CLI/self-play uses AI:

- [ ] Add:

  ```text
  --no-opening-book
  ```

- [ ] Pass `use_opening_book=False` to `get_best_move()`.

### 5.2 Add custom book path

Optional:

- [ ] Add:

  ```text
  --opening-book path/to/opening_book.json
  ```

- [ ] Load custom book and pass it to `get_best_move()`.

Do not overbuild command-line integration. Engine/API support and tests are more important.

---

## Task 6: Add opening book tests

Create:

```text
tests/test_opening_book.py
```

### 6.1 Bundled book loads

- [ ] `OpeningBook.bundled()` succeeds.
- [ ] It has at least one indexed position.

### 6.2 Bundled lines are legal

- [ ] Test that all bundled lines validate during load.
- [ ] If load succeeds, this may be implicitly covered.

### 6.3 Starting position returns a White book move

- [ ] From `Board()`, `find_book_move(board)` returns a legal White move.
- [ ] Expected likely move may be `e2e4` or `d2d4` depending weights.
- [ ] Do not make this brittle unless weights specify exact top move.

### 6.4 Black defense after `e2e4`

- [ ] Start from `Board()`.
- [ ] Apply `e2e4`.
- [ ] Assert book move for Black is legal.
- [ ] It may be Sicilian `c7c5` if highest weight.
- [ ] If exact highest weight is deterministic, assert exact move.

### 6.5 King's Gambit root

- [ ] Start from `Board()`.
- [ ] Apply:

  ```text
  e2e4 e7e5
  ```

- [ ] Assert a White book candidate includes:

  ```text
  f2f4
  ```

- [ ] If deterministic highest weight selects another opening at this position, use `candidates_for()` rather than requiring `find_book_move()` to choose King's Gambit.

### 6.6 King's Gambit Accepted continuation

- [ ] Apply:

  ```text
  e2e4 e7e5 f2f4 e5f4
  ```

- [ ] Assert a White book candidate includes:

  ```text
  g1f3
  ```

### 6.7 King's Gambit Declined continuation

- [ ] Apply:

  ```text
  e2e4 e7e5 f2f4 f8c5
  ```

- [ ] Assert a White book candidate includes:

  ```text
  g1f3
  ```

### 6.8 Illegal line raises clear error

- [ ] Build small in-memory data with illegal move, for example:

  ```json
  {
    "version": 1,
    "selection": "highest_weight",
    "lines": [
      {
        "name": "Bad Line",
        "side": "white",
        "moves": ["e2e5"],
        "weight": 1
      }
    ]
  }
  ```

- [ ] Assert `OpeningBookError`.

### 6.9 Unknown position returns `None`

- [ ] Create a position unlikely to be in book.
- [ ] Assert `find_book_move(board) is None`.

### 6.10 Lookup returns only legal moves

- [ ] For several book positions, assert returned move is in `board.get_legal_moves()`.

### 6.11 Integration: `get_best_move` uses book

- [ ] From starting position:

  ```python
  move = get_best_move(Board(), depth=1, use_opening_book=True)
  ```

- [ ] Assert the move matches `OpeningBook.bundled().find_book_move(Board())`.

### 6.12 Integration: disabling book falls back to search

- [ ] Call:

  ```python
  get_best_move(board, depth=1, use_opening_book=False)
  ```

- [ ] Assert it returns a legal move.
- [ ] Do not require it to differ from the book move.

### 6.13 Deterministic tie-breaking

- [ ] Build tiny in-memory book data with two candidates for same position and same weight.
- [ ] Assert selection is stable according to line order / tie-break rule.

### 6.14 Invalid schema tests

Add tests for:

- [ ] missing `lines`,
- [ ] empty moves,
- [ ] invalid side,
- [ ] non-positive weight,
- [ ] non-string move.

---

## Task 7: Documentation

### 7.1 Update README or docs

Add concise docs explaining:

- [ ] Opening book JSON location.
- [ ] Coordinate notation format.
- [ ] How to add a new opening line.
- [ ] How weights work.
- [ ] Deterministic highest-weight selection in v1.
- [ ] Search fallback.
- [ ] How to disable book if API/CLI supports it.

### 7.2 Add example line

Include example:

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

---

## Task 8: Verification

### 8.1 JSON syntax

Run:

```bash
python -m json.tool chess_game/chess/data/opening_book.json >/dev/null
```

- [ ] Passes.

### 8.2 Opening book tests

Run:

```bash
python -m pytest tests/test_opening_book.py -q
```

- [ ] Passes.

### 8.3 Fast suite

Run:

```bash
python -m pytest tests -q -m "not slow"
```

- [ ] Passes.

### 8.4 Rules subset

Run:

```bash
python -m pytest tests/test_board_api.py tests/test_piece_moves.py tests/test_castling.py tests/test_en_passant.py tests/test_promotion.py tests/test_promotion_validation.py tests/test_promotion_move_generation.py tests/test_check_checkmate_stalemate.py tests/test_legal_moves.py -q
```

- [ ] Passes.

### 8.5 Targeted AI tests

Run:

```bash
python -m pytest tests/test_alpha_beta_pruning.py tests/test_ai_quality.py -q
```

- [ ] Passes.

---

## Task 9: Implementation guardrails

Before finishing, verify:

- [ ] No opening-book logic was added to board evaluation.
- [ ] No opening-book logic was added to minimax.
- [ ] No opening-book logic was added to alpha-beta pruning.
- [ ] No opening-book logic was added to TT.
- [ ] No new heuristic modules were added for opening preference.
- [ ] Existing search tests can disable the book with `use_opening_book=False`.
- [ ] Book moves are validated and legal.
- [ ] Unknown positions still fall back to search.

---

## Acceptance checklist

The feature is complete only when:

- [ ] `chess_game/chess/opening_book.py` exists.
- [ ] `chess_game/chess/data/opening_book.json` exists.
- [ ] Book contains at least 10 White openings.
- [ ] Book contains at least 10 Black defenses.
- [ ] Book includes King's Gambit root and King's Gambit family continuations.
- [ ] Book lines validate by replaying legal moves.
- [ ] Book lookup uses position keys.
- [ ] Book lookup filters to legal moves.
- [ ] Selection is deterministic highest-weight.
- [ ] `get_best_move()` checks book before search when enabled.
- [ ] `get_best_move(..., use_opening_book=False)` bypasses book.
- [ ] Tests cover load, validation, lookup, King's Gambit, integration, and fallback.
- [ ] Existing fast test suite passes.
