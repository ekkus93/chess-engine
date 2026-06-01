# replies5.md

## Answers to Copilot clarification questions

Here are the answers for Copilot.

---

## 1. CLI precedence policy lock

Use **`--no-opening-book` wins** as the final behavior.

Do **not** reject combined flags. The docs already say no-book-wins, so make implementation match docs:

```python
opening_book = None

if not args.no_opening_book and args.opening_book:
    opening_book = OpeningBook.from_file(args.opening_book)

use_opening_book = not args.no_opening_book
```

This command should **not** try to load the bad path:

```bash
python -m chess_game.self_play --no-opening-book --opening-book /bad/path --max-moves 1
```

It should run with the opening book disabled.

---

## 2. Falkbeer continuation requirement

Treat `e4d5` as **required** for final acceptance.

The line should be:

```json
"moves": ["e2e4", "e7e5", "f2f4", "d7d5", "e4d5"]
```

The earlier “omission-with-doc-justification” escape hatch is no longer needed. Add the continuation and test it.

---

## 3. Strength of required-candidate assertions

“Required candidate must be included” is sufficient.

Do **not** assert exact candidate-set equality. The book is extensible, and exact set equality would make tests brittle when new openings/defenses are added later.

Use inclusion assertions:

```python
assert "f2f4" in candidate_texts
assert "g1f3" in candidate_texts
assert "c7c5" in candidate_texts
```

That is the right balance: strong enough to catch missing required lines, flexible enough to allow future book growth.

---

## 4. Loader error contract

Pin the exception type and a message fragment, not the exact full message.

Good:

```python
with pytest.raises(OpeningBookError, match="JSON object"):
    load_opening_book_data(path)
```

Avoid brittle full-string matching. The exact message can evolve, but it must clearly communicate that the top-level JSON must be an object/dict.

---

## 5. CLI testing style preference

Prefer a **function-level or monkeypatch test** if the self-play CLI is structured so that this is clean.

The test should prove that when both flags are supplied:

```text
--no-opening-book
--opening-book /bad/path
```

the custom path is not loaded.

A good unit-style test would monkeypatch `OpeningBook.from_file` to raise if called, then verify it is **not called** when `no_opening_book=True`.

A subprocess smoke test is acceptable as a secondary check, but it is slower and more brittle. Use subprocess only if the CLI argument flow is hard to test directly.

---

## 6. Task 0 copy-doc subtasks

Yes. If the final-fix spec/TODO files are already present in the repo, mark the Task 0 copy-doc subtasks complete.

Do not duplicate the files or create alternate names. Just verify these exist:

```text
docs/CHESS_ENGINE_OPENING_BOOK_FINAL_FIX_SPEC.md
docs/CHESS_ENGINE_OPENING_BOOK_FINAL_FIX_TODO.md
```

Then mark them complete.

---

## Final locked guidance

Proceed with these decisions:

```text
1. --no-opening-book wins over --opening-book.
2. Falkbeer e4d5 is required.
3. Candidate inclusion assertions are sufficient; do not require exact set equality.
4. Loader tests should assert OpeningBookError plus a stable message fragment.
5. Prefer function-level/monkeypatch CLI tests over subprocess tests.
6. Mark Task 0 copy-doc subtasks complete if the files already exist.
```

These answers address the six clarification items Copilot raised.
