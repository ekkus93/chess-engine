# CHESS_ENGINE_OPENING_BOOK_FIX_SPEC.md

## Purpose

This spec defines a focused follow-up fix pass for the chess engine opening-book implementation.

The initial opening-book feature is mostly implemented: it has a separate `opening_book.py` module, a bundled JSON book, package-data configuration, `get_best_move()` integration, King's Gambit lines, and a dedicated test file.

However, the latest review found several correctness and verification issues that must be fixed before the opening-book TODO can be considered complete.

This is a targeted polish/bugfix pass. It must not become a search rewrite or chess-strength tuning pass.

---

## Main confirmed issues

### 1. Side-agnostic book indexing

The current book index appears to store every ply of every line regardless of the line's `side`.

That causes Black defense lines to influence White's opening choice.

Example problem:

```json
{
  "name": "Sicilian Defense",
  "side": "black",
  "moves": ["e2e4", "c7c5"],
  "weight": 100
}
```

If every ply is indexed, this line contributes `e2e4` as a candidate in the initial White-to-move position. That is conceptually wrong: the Sicilian Defense should contribute Black's move `c7c5` after White has played `e2e4`, not White's first move.

The same problem can happen in reverse: White opening lines can influence Black's replies.

### 2. Broad exception swallowing in `get_best_move()`

The current integration catches broad exceptions around opening-book lookup and silently falls back to search.

That hides broken bundled book data, invalid JSON, illegal book moves, package-data problems, or programming errors.

For bundled data, fail fast. Fallback to search only when no legal book move exists.

### 3. Weak opening-book tests

Some tests appear to use "first legal move" instead of explicitly applying intended moves such as `e2e4` and `e7e5`. This makes King's Gambit and Black defense tests less meaningful.

Some tests assert only that returned objects have attributes rather than verifying actual legal-move membership or expected book behavior.

### 4. Optional CLI custom book path marked complete but not actually implemented

The TODO marked `--opening-book path/to/opening_book.json` complete, but the implementation appears to only support `--no-opening-book`.

Because the custom path task was optional, either implement it or mark it intentionally deferred. Do not leave it checked as complete if not implemented.

### 5. Minor schema and deterministic-sort polish

The implementation should validate:

```text
selection == "highest_weight"
```

The deterministic tie-break move string should include promotion suffix, not just start/end.

### 6. Non-slow test suite still does not reliably complete

The opening-book tests themselves pass quickly, but the broader non-slow suite still timed out in review. The problem appears to be newer AI strategy regression tests, not opening-book tests.

This pass should mark obviously expensive AI strategy regression tests as `slow` so the default command is runnable again.

---

## Non-goals

Do **not** do any of the following in this pass:

- Do not change minimax.
- Do not change alpha-beta pruning.
- Do not change transposition-table semantics.
- Do not change static evaluation.
- Do not change material values.
- Do not change piece-square tables.
- Do not change move ordering scores.
- Do not add new chess heuristics.
- Do not add new opening preferences outside the data-driven book.
- Do not add weighted-random book selection.
- Do not add PGN/SAN parsing.
- Do not add UCI support.
- Do not reintroduce a hidden depth-5 opening shortcut.
- Do not hide test failures by weakening assertions.

---

## Required behavior

## 1. Side-aware indexing

The opening book must respect the `side` field when deciding which plies to index.

### Required semantics

```text
side == "white":
  index only positions where White is to move.

side == "black":
  index only positions where Black is to move.

side == "both":
  index both White-to-move and Black-to-move positions.
```

### Example

Given:

```json
{
  "name": "Sicilian Defense",
  "side": "black",
  "moves": ["e2e4", "c7c5"],
  "weight": 100
}
```

The index should **not** store `e2e4` as a starting-position White book move for this line.

It **should** store `c7c5` as a Black book move after `e2e4`.

### Recommended helper

Add a helper such as:

```python
def _should_index_line_move(line: OpeningLine, board: Board) -> bool:
    if line.side == "both":
        return True
    if line.side == "white":
        return board.turn == Color.WHITE
    if line.side == "black":
        return board.turn == Color.BLACK
    return False
```

Use the repo's actual color enum/type.

During replay, always validate and apply every move in every line, but only add a candidate to the index if `_should_index_line_move(...)` returns true.

---

## 2. Error handling in `get_best_move()`

Do not catch broad exceptions around bundled opening-book lookup.

Bad:

```python
try:
    book = opening_book or get_bundled_opening_book()
    book_move = book.find_book_move(board)
    if book_move is not None:
        return book_move
except Exception:
    pass
```

Preferred:

```python
if use_opening_book:
    book = opening_book or get_bundled_opening_book()
    book_move = book.find_book_move(board)
    if book_move is not None:
        return book_move
```

If no book move exists, fall back to search.

If the bundled book is broken, raise the actual error.

If a CLI wants to be resilient to custom user-supplied book files, catch `OpeningBookError` in the CLI layer and print a clear message. Do not hide it in the core AI function.

---

## 3. Strong opening-book tests

Tests must explicitly set up positions.

Use a helper like:

```python
def apply_moves(board: Board, *moves: str) -> None:
    for text in moves:
        move = parse_move_notation(text)
        assert board.make_move(move.start, move.end, move.promotion)
```

Do not use "first legal move" to simulate specific opening lines.

### Required test cases

Add or strengthen tests for:

1. Starting position returns a White book move from a White or both-side line, not from a Black defense line.
2. After `e2e4`, Black has a legal defense candidate, such as Sicilian `c7c5`.
3. After `e2e4 e7e5`, King's Gambit candidate `f2f4` exists.
4. After `e2e4 e7e5 f2f4 e5f4`, King's Gambit Accepted candidate `g1f3` exists.
5. After `e2e4 e7e5 f2f4 f8c5`, King's Gambit Declined Classical candidate `g1f3` exists.
6. Unknown/non-book position returns exactly `None`.
7. `candidates_for(board)` returns only candidates whose moves are legal in the current position.
8. `find_book_move(board)` returns only a legal move.
9. Non-string move schema validation raises `OpeningBookError`.
10. Unsupported `selection` value raises `OpeningBookError`.
11. Deterministic tie-breaking includes promotion suffix.

---

## 4. CLI custom book path status

The original TODO made `--opening-book path/to/opening_book.json` optional.

This follow-up pass must do one of the following:

### Option A: Implement it

Add a CLI argument:

```text
--opening-book path/to/opening_book.json
```

It should:

1. Load that custom book file.
2. Validate it.
3. Pass the resulting `OpeningBook` instance to `get_best_move(...)`.
4. Work together with `--no-opening-book`.

Expected semantics:

```text
--no-opening-book:
  disable book completely.

--opening-book custom.json:
  use custom book.

both flags together:
  either reject as invalid or let --no-opening-book win.
  Document the chosen behavior.
```

### Option B: Defer it honestly

If CLI custom path support is not implemented, update the TODO/docs/memory note to say:

```text
--opening-book custom path intentionally deferred.
--no-opening-book is implemented.
```

Do not leave the optional item checked as implemented if it is not implemented.

---

## 5. Schema validation

The parser must validate:

```text
version == 1
selection == "highest_weight"
lines is a list
name is non-empty string
side is "white", "black", or "both"
moves is a non-empty list of strings
weight is a positive integer
eco is optional string/null
tags is optional list of strings
```

If top-level JSON is not an object, raise `OpeningBookError`.

Do not return `{}` for non-dict JSON.

Bad:

```python
return data if isinstance(data, dict) else {}
```

Preferred:

```python
if not isinstance(data, dict):
    raise OpeningBookError("Opening book data must be a JSON object")
```

---

## 6. Deterministic sort must preserve promotion identity

If using coordinate string as a tie-break, include the promotion suffix.

Bad:

```python
move_str = f"{start_alg}{end_alg}"
```

Better:

```python
promotion_suffix = ""
if candidate.move.promotion is not None:
    promotion_suffix = candidate.move.promotion.name.lower()[0]
move_str = f"{start_alg}{end_alg}{promotion_suffix}"
```

Use the repo's actual promotion enum names.

This is mostly future-proofing because the bundled book may not currently contain promotion lines, but the book model must not collapse promotion alternatives.

---

## 7. Test-runtime cleanup

The opening-book tests pass, but the broader non-slow suite still appears too slow.

At minimum, inspect and mark slow any multi-second AI strategy regression tests.

Known likely candidate from review:

```text
tests/test_ai_strategy13_regressions.py::test_strategy13_black_keeps_forcing_line_over_repetition
```

Apply the existing slow-test policy:

```text
Depth 4/5 tests:
  slow

Complex depth-3 strategic tests:
  slow

Transcript-style exact-move regressions:
  slow

Self-play search loops:
  slow
```

This should be a marker/classification change only. Do not change AI behavior for runtime reasons.

---

## Acceptance criteria

This follow-up is complete when:

1. Black defense lines no longer affect White's starting-position book choice.
2. White opening lines no longer affect Black's defensive choices unless `side == "both"`.
3. Opening-book lookup still validates and replays all lines correctly.
4. `get_best_move()` no longer swallows broad opening-book exceptions.
5. Broken bundled book data fails loudly.
6. No-book positions fall back to normal search.
7. Tests explicitly apply intended opening moves.
8. King's Gambit root and continuations are strongly tested.
9. Unknown positions return exactly `None`.
10. Candidates are verified to be legal moves.
11. Non-string moves and unsupported `selection` values raise `OpeningBookError`.
12. Deterministic sort includes promotion suffix.
13. CLI custom path is either implemented or explicitly documented as deferred.
14. `tests/test_opening_book.py` passes.
15. Rules subset passes.
16. Targeted AI tests pass.
17. `python -m pytest tests -q -m "not slow" --durations=25` completes in a practical time.
18. No minimax/alpha-beta/TT/evaluation behavior is changed for this fix.
