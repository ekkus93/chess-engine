# CHESS_ENGINE_OPENING_BOOK_FINAL_FIX_SPEC.md

## Purpose

This spec defines the final focused polish pass for the chess engine opening-book implementation.

The opening book is mostly working: it is data-driven, side-aware indexing is implemented, book lookup is separated from search/evaluation, package data works, and targeted opening-book tests pass.

The remaining issues are small but important:

1. A King's Gambit Declined Classical line stops too early and does not provide the intended White continuation.
2. The Falkbeer Countergambit line also stops early and should be extended if keeping it as a White opening-family continuation.
3. Several opening-book tests are still too permissive and do not assert required book candidates exactly.
4. `load_opening_book_data()` still returns `{}` for non-dict JSON instead of raising `OpeningBookError` immediately.
5. CLI behavior for `--no-opening-book --opening-book badpath` does not match the documented precedence.
6. The non-slow test suite must be re-verified and the terminal result captured.

This is a **small final cleanup patch**. Do not change chess search behavior.

---

## Non-goals

Do **not** do any of the following in this pass:

- Do not change minimax.
- Do not change alpha-beta pruning.
- Do not change transposition-table semantics.
- Do not change evaluation.
- Do not change material values.
- Do not change piece-square tables.
- Do not change move-ordering scores.
- Do not add new opening-book selection policies.
- Do not add weighted randomness.
- Do not add PGN/SAN parsing.
- Do not add new opening families beyond the specific line completions below.
- Do not rewrite the opening-book architecture.
- Do not weaken tests to make them pass.
- Do not reintroduce broad exception swallowing around bundled opening-book lookup.

Expected code areas are:

```text
chess_game/chess/data/opening_book.json
chess_game/chess/opening_book.py
chess_game/self_play.py
tests/test_opening_book.py
docs/OPENING_BOOK.md
docs/CHESS_ENGINE_OPENING_BOOK_FINAL_FIX_SPEC.md
docs/CHESS_ENGINE_OPENING_BOOK_FINAL_FIX_TODO.md
```

Possibly touched only if necessary:

```text
tests/test_self_play.py
tests/test_cli*.py
```

---

## Required fix 1: Complete King's Gambit Declined Classical

The bundled JSON currently has a King's Gambit Declined Classical line equivalent to:

```text
e2e4 e7e5 f2f4 f8c5
```

That leaves the White-to-move position after `...Bc5` with no book candidate.

Update it to include the intended White continuation:

```text
e2e4 e7e5 f2f4 f8c5 g1f3
```

The exact JSON line should end with:

```json
"moves": ["e2e4", "e7e5", "f2f4", "f8c5", "g1f3"]
```

After replaying:

```text
e2e4 e7e5 f2f4 f8c5
```

`OpeningBook.bundled().candidates_for(board)` must include:

```text
g1f3
```

---

## Required fix 2: Extend Falkbeer Countergambit if kept as a White continuation

The bundled JSON currently has a Falkbeer Countergambit line equivalent to:

```text
e2e4 e7e5 f2f4 d7d5
```

If the line is included as part of the White King's Gambit family, extend it with the common White capture:

```text
e4d5
```

Preferred final line:

```json
"moves": ["e2e4", "e7e5", "f2f4", "d7d5", "e4d5"]
```

If there is a reason not to include this continuation, document it clearly. The preferred fix is to add `e4d5`.

---

## Required fix 3: Strengthen opening-book tests

Opening-book tests must assert exact required behavior.

Do not use patterns like:

```python
if len(candidates) > 0:
    assert any(hasattr(c, "move") for c in candidates)
```

That pattern allows a required candidate to be absent while the test still passes.

### Required helper

Use or add a helper like:

```python
def apply_moves(board: Board, *moves: str) -> None:
    for text in moves:
        move = parse_move_notation(text)
        assert board.make_move(move.start, move.end, move.promotion)
```

Use explicit move strings in every opening-line setup.

### Required move-text helper

Use or add a helper like:

```python
def move_to_text(move: LegalMove) -> str:
    start = index_to_algebraic(move.start)
    end = index_to_algebraic(move.end)
    promotion = ""
    if move.promotion is not None:
        promotion = move.promotion.name.lower()[0]
    return f"{start}{end}{promotion}"
```

Adapt to the repo's actual imports/types.

### Required assertions

Tests must assert all of the following:

1. After:

   ```text
   e2e4
   ```

   Black candidates include:

   ```text
   c7c5
   ```

2. After:

   ```text
   e2e4 e7e5
   ```

   White candidates include:

   ```text
   f2f4
   ```

3. After:

   ```text
   e2e4 e7e5 f2f4 e5f4
   ```

   White candidates include:

   ```text
   g1f3
   ```

4. After:

   ```text
   e2e4 e7e5 f2f4 f8c5
   ```

   White candidates include:

   ```text
   g1f3
   ```

5. If Falkbeer continuation is added, after:

   ```text
   e2e4 e7e5 f2f4 d7d5
   ```

   White candidates include:

   ```text
   e4d5
   ```

6. Unknown/non-book position returns exactly:

   ```python
   None
   ```

   Do not accept arbitrary legal moves in the unknown-position test.

7. Every candidate returned by `candidates_for(board)` for sampled positions is legal in the current board position.

Move identity must include:

```text
start
end
promotion
```

---

## Required fix 4: Non-dict JSON loader behavior

`load_opening_book_data()` must raise `OpeningBookError` immediately if the loaded JSON is not an object/dict.

Bad behavior:

```python
data = json.load(f)
return data if isinstance(data, dict) else {}
```

Correct behavior:

```python
data = json.load(f)
if not isinstance(data, dict):
    raise OpeningBookError("Opening book data must be a JSON object")
return data
```

Apply this to both:

```text
bundled JSON loading
custom file path loading
```

### Required tests

Add tests using temp files, not only direct `parse_opening_lines(...)` calls:

1. JSON array:

   ```json
   []
   ```

   must raise `OpeningBookError` from `load_opening_book_data(path)` or `OpeningBook.from_file(path)`.

2. JSON string:

   ```json
   "not an object"
   ```

   must raise `OpeningBookError`.

The test must catch the loader path, not only the parser path.

---

## Required fix 5: CLI `--no-opening-book` precedence

Documentation currently says that if both flags are supplied:

```text
--no-opening-book
--opening-book path/to/book.json
```

then `--no-opening-book` wins.

The implementation must match that behavior.

### Required behavior

If `--no-opening-book` is present:

1. Do not load the custom opening-book file.
2. Ignore `--opening-book`, even if the path is invalid.
3. Run self-play/search with `use_opening_book=False`.

This command should not fail due to the bad path:

```bash
python -m chess_game.self_play --no-opening-book --opening-book /no/such/file --max-moves 1
```

It should proceed with the opening book disabled.

### Acceptable alternative

Instead of `--no-opening-book` winning, it is acceptable to reject the combination explicitly with a clear error:

```text
--opening-book cannot be used together with --no-opening-book
```

However, because the current docs claim `--no-opening-book` wins, the preferred fix is to implement that documented behavior.

### Required test

Add or update a CLI/self-play test proving that `--no-opening-book` prevents loading a bad custom book path.

---

## Required fix 6: Re-verify non-slow suite

Run:

```bash
python -m pytest tests -q -m "not slow" --durations=25
```

Capture:

```text
pass/fail status
runtime
slowest tests
selected/deselected counts
```

If it does not complete in a practical time, identify the slowest non-slow tests and mark appropriate strategy/transcript tests as `slow`.

Do not change AI behavior for runtime.

---

## Documentation requirements

Update `docs/OPENING_BOOK.md` if needed:

1. Document the completed King's Gambit Declined Classical continuation.
2. Document Falkbeer continuation if added.
3. Confirm that `--no-opening-book` wins over `--opening-book`.
4. State that non-object JSON raises `OpeningBookError`.
5. Keep docs concise.

---

## Acceptance criteria

This patch is complete only when:

1. King's Gambit Declined Classical includes `g1f3`.
2. Falkbeer Countergambit includes `e4d5`, or its omission is explicitly documented.
3. Tests assert `c7c5` after `e2e4`.
4. Tests assert `f2f4` after `e2e4 e7e5`.
5. Tests assert `g1f3` after `e2e4 e7e5 f2f4 e5f4`.
6. Tests assert `g1f3` after `e2e4 e7e5 f2f4 f8c5`.
7. Tests assert `e4d5` after `e2e4 e7e5 f2f4 d7d5` if Falkbeer is extended.
8. Required-candidate tests do not use permissive `if candidates` guards.
9. Unknown-position lookup returns exactly `None`.
10. Candidate legality is checked by actual legal-move identity.
11. `load_opening_book_data()` raises `OpeningBookError` for JSON arrays/strings.
12. Tests cover non-dict JSON through the loader/file path.
13. `--no-opening-book --opening-book /bad/path` does not load the bad path if docs say no-book wins.
14. `tests/test_opening_book.py` passes.
15. Rules subset passes.
16. Targeted AI tests pass.
17. Non-slow suite completes or remaining slow tests are classified appropriately.
18. No minimax/alpha-beta/TT/evaluation/move-ordering behavior is changed.
