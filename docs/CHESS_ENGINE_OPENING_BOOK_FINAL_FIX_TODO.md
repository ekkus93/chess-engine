# CHESS_ENGINE_OPENING_BOOK_FINAL_FIX_TODO.md

## Goal

Finish the final small opening-book polish items.

The opening book is mostly complete. This patch fixes remaining line-data, test-strength, loader, CLI-precedence, and verification issues.

This is not a search-engine patch. Do not change minimax, alpha-beta, TT, evaluation, material values, piece-square tables, or move ordering.

---

## Task 0: Baseline and handoff docs

### 0.1 Copy docs

- [ ] Copy this TODO into:

  ```text
  docs/CHESS_ENGINE_OPENING_BOOK_FINAL_FIX_TODO.md
  ```

- [ ] Copy the companion spec into:

  ```text
  docs/CHESS_ENGINE_OPENING_BOOK_FINAL_FIX_SPEC.md
  ```

### 0.2 Run current opening-book tests

Run:

```bash
python -m pytest tests/test_opening_book.py -q --durations=20
```

- [ ] Record result.
- [ ] Record runtime.

### 0.3 Run JSON syntax check

Run:

```bash
python -m json.tool chess_game/chess/data/opening_book.json >/dev/null
```

- [ ] Confirm it passes.

---

## Task 1: Fix King's Gambit Declined Classical line

### 1.1 Locate line

Open:

```text
chess_game/chess/data/opening_book.json
```

Find:

```text
King's Gambit Declined: Classical
```

### 1.2 Add White continuation

Change the moves from:

```json
["e2e4", "e7e5", "f2f4", "f8c5"]
```

to:

```json
["e2e4", "e7e5", "f2f4", "f8c5", "g1f3"]
```

### 1.3 Verify legality manually through tests

The final position before `g1f3` is:

```text
e2e4 e7e5 f2f4 f8c5
```

White to move. `g1f3` must be legal.

- [ ] Confirm bundled book validates after this JSON change.

---

## Task 2: Extend Falkbeer Countergambit line

### 2.1 Locate line

Find:

```text
King's Gambit Declined: Falkbeer Countergambit
```

### 2.2 Add White continuation

Preferred change:

```json
["e2e4", "e7e5", "f2f4", "d7d5", "e4d5"]
```

### 2.3 If not adding continuation, document why

If you choose not to add `e4d5`, update docs with a clear reason.

Preferred outcome:

- [ ] Add `e4d5`.

---

## Task 3: Strengthen opening-book candidate tests

### 3.1 Add or verify explicit apply helper

In:

```text
tests/test_opening_book.py
```

ensure there is a helper equivalent to:

```python
def apply_moves(board: Board, *moves: str) -> None:
    for text in moves:
        move = parse_move_notation(text)
        assert board.make_move(move.start, move.end, move.promotion)
```

- [ ] All opening-position tests must use explicit moves.
- [ ] Do not use first-legal-move setup for specific openings.

### 3.2 Add or verify move-to-text helper

Add/verify a helper that converts `LegalMove` to coordinate text including promotion suffix:

```python
def move_to_text(move: LegalMove) -> str:
    ...
```

Examples:

```text
e2e4
g1f3
e7e8q
```

### 3.3 Strengthen Black defense test

Add or update a test:

```text
after e2e4, candidates include c7c5
```

Implementation intent:

```python
board = Board()
apply_moves(board, "e2e4")
candidate_texts = {move_to_text(c.move) for c in book.candidates_for(board)}
assert "c7c5" in candidate_texts
```

- [ ] Test fails if `c7c5` is absent.

### 3.4 Strengthen King's Gambit root test

Add or update a test:

```text
after e2e4 e7e5, candidates include f2f4
```

- [ ] Test fails if `f2f4` is absent.

### 3.5 Strengthen King's Gambit Accepted test

Add or update a test:

```text
after e2e4 e7e5 f2f4 e5f4, candidates include g1f3
```

- [ ] Test fails if `g1f3` is absent.

### 3.6 Strengthen King's Gambit Declined Classical test

Add or update a test:

```text
after e2e4 e7e5 f2f4 f8c5, candidates include g1f3
```

- [ ] Test fails if `g1f3` is absent.
- [ ] Remove any `if len(candidates) > 0:` guard from this test.

### 3.7 Add Falkbeer continuation test

If Task 2 adds `e4d5`, add or update a test:

```text
after e2e4 e7e5 f2f4 d7d5, candidates include e4d5
```

- [ ] Test fails if `e4d5` is absent.

### 3.8 Remove permissive required-candidate guards

Search:

```bash
grep -R "if len(candidates) > 0\|if candidates" -n tests/test_opening_book.py
```

For tests that require candidates, remove permissive guards.

Acceptable:

```python
assert candidates
```

followed by exact required candidate assertions.

Not acceptable:

```python
if candidates:
    assert ...
```

when the candidate is required.

---

## Task 4: Strengthen unknown-position and legality tests

### 4.1 Unknown position returns exactly None

Find the unknown-position test.

It must assert:

```python
assert book.find_book_move(board) is None
```

Do not accept arbitrary legal moves.

### 4.2 Use a truly non-book position

Set up a position that should not occur in the bundled book.

Example approach:

```text
a2a3 h7h6 a3a4 h6h5
```

or another awkward sequence outside the book.

- [ ] Confirm `find_book_move(board) is None`.

### 4.3 Candidates are legal

For sampled book positions, verify:

1. Compute legal move identities from `board.get_legal_moves()`.
2. Compute candidate move identities from `book.candidates_for(board)`.
3. Assert every candidate identity is present in legal identities.

Identity must include:

```text
start
end
promotion
```

- [ ] Starting position checked.
- [ ] After `e2e4` checked.
- [ ] After `e2e4 e7e5` checked.
- [ ] After one King's Gambit accepted position checked.

---

## Task 5: Fix non-dict JSON loader behavior

### 5.1 Locate loader

Open:

```text
chess_game/chess/opening_book.py
```

Find:

```python
load_opening_book_data(...)
```

Look for:

```python
return data if isinstance(data, dict) else {}
```

### 5.2 Raise immediately for non-dict JSON

Change both bundled and custom-path loading to:

```python
data = json.load(f)
if not isinstance(data, dict):
    raise OpeningBookError("Opening book data must be a JSON object")
return data
```

Make sure `OpeningBookError` is already defined before use.

### 5.3 Add temp-file tests

Add tests that exercise the loader/file path, not only `parse_opening_lines(...)`.

Test JSON array:

```python
path.write_text("[]", encoding="utf-8")
with pytest.raises(OpeningBookError):
    load_opening_book_data(path)
```

or:

```python
with pytest.raises(OpeningBookError):
    OpeningBook.from_file(path)
```

Test JSON string:

```python
path.write_text('"not an object"', encoding="utf-8")
with pytest.raises(OpeningBookError):
    load_opening_book_data(path)
```

- [ ] Both tests pass.

---

## Task 6: Fix CLI flag precedence

### 6.1 Inspect self-play CLI

Open:

```text
chess_game/self_play.py
```

Find the code handling:

```text
--no-opening-book
--opening-book
```

### 6.2 Implement documented precedence

Docs say `--no-opening-book` wins.

Implement:

```python
opening_book = None
if not args.no_opening_book and args.opening_book:
    opening_book = OpeningBook.from_file(args.opening_book)
```

Then pass:

```python
use_opening_book=not args.no_opening_book
opening_book=opening_book
```

The key requirement:

```text
If --no-opening-book is present, do not load args.opening_book at all.
```

### 6.3 Add CLI/self-play test

Add a test that proves bad custom path is ignored when `--no-opening-book` is present.

Equivalent command:

```bash
python -m chess_game.self_play --no-opening-book --opening-book /no/such/file --max-moves 1
```

Expected:

- [ ] Does not fail due to missing `/no/such/file`.
- [ ] Runs with opening book disabled.

If there is an existing CLI test helper, use it. If CLI tests are not present, add a minimal subprocess or function-level test.

### 6.4 Update docs if needed

`docs/OPENING_BOOK.md` should state:

```text
If both --no-opening-book and --opening-book are provided, --no-opening-book wins and the custom file is not loaded.
```

---

## Task 7: Documentation update

Update:

```text
docs/OPENING_BOOK.md
```

as needed.

### 7.1 King's Gambit docs

- [ ] Mention King's Gambit Declined Classical includes `g1f3`.
- [ ] Mention Falkbeer includes `e4d5` if added.

### 7.2 Loader behavior docs

- [ ] State that JSON must be a top-level object.
- [ ] State that non-object JSON raises `OpeningBookError`.

### 7.3 CLI docs

- [ ] Confirm `--no-opening-book` disables the book.
- [ ] Confirm `--opening-book PATH` loads a custom JSON book.
- [ ] Confirm combined flag behavior.

Keep the docs concise.

---

## Task 8: Verification

### 8.1 JSON syntax

Run:

```bash
python -m json.tool chess_game/chess/data/opening_book.json >/dev/null
```

- [ ] Passes.

### 8.2 Opening-book tests

Run:

```bash
python -m pytest tests/test_opening_book.py -q --durations=20
```

- [ ] Passes.
- [ ] Record runtime.

### 8.3 Rules subset

Run:

```bash
python -m pytest tests/test_board_api.py tests/test_piece_moves.py tests/test_castling.py tests/test_en_passant.py tests/test_promotion.py tests/test_promotion_validation.py tests/test_promotion_move_generation.py tests/test_check_checkmate_stalemate.py tests/test_legal_moves.py -q
```

- [ ] Passes.

### 8.4 Targeted AI tests

Run:

```bash
python -m pytest tests/test_alpha_beta_pruning.py tests/test_ai_quality.py -q --durations=15
```

- [ ] Passes.

### 8.5 Fast non-slow suite

Run:

```bash
python -m pytest tests -q -m "not slow" --durations=25
```

- [ ] Passes or failure is understood.
- [ ] Record selected/deselected counts.
- [ ] Record runtime.
- [ ] Record slowest tests.

If this command does not complete in a practical time, identify slow non-slow strategy tests and mark appropriate ones `slow`.

Do not change AI behavior for runtime.

### 8.6 CLI smoke test

Run:

```bash
python -m chess_game.self_play --no-opening-book --opening-book /no/such/file --max-moves 1
```

- [ ] Does not fail because of missing custom book path.
- [ ] Uses opening book disabled behavior.

---

## Task 9: Guardrail diff review

Before finishing, inspect the diff.

### 9.1 Expected changed files

Likely:

```text
chess_game/chess/data/opening_book.json
chess_game/chess/opening_book.py
chess_game/self_play.py
tests/test_opening_book.py
docs/OPENING_BOOK.md
docs/CHESS_ENGINE_OPENING_BOOK_FINAL_FIX_SPEC.md
docs/CHESS_ENGINE_OPENING_BOOK_FINAL_FIX_TODO.md
```

Possibly:

```text
tests/test_self_play.py
tests/test_cli*.py
```

### 9.2 Files/logic that should not change

Do not change:

```text
minimax
alpha-beta
transposition table semantics
static evaluation
material values
piece-square tables
move ordering scores
board rules
legal move generation
```

### 9.3 Final checklist

- [ ] King's Gambit Declined Classical includes `g1f3`.
- [ ] Falkbeer includes `e4d5` or omission is documented.
- [ ] Required candidate tests assert exact moves.
- [ ] No permissive `if candidates` guard hides required missing moves.
- [ ] Unknown position returns exactly `None`.
- [ ] Candidate legality is checked by actual legal move identity.
- [ ] Non-dict JSON raises `OpeningBookError` in loader/file-path path.
- [ ] CLI `--no-opening-book` prevents loading invalid custom path.
- [ ] Documentation matches implementation.
- [ ] Opening-book tests pass.
- [ ] Rules subset passes.
- [ ] Targeted AI tests pass.
- [ ] Non-slow suite result is captured.
- [ ] No search/eval/TT behavior changed.
