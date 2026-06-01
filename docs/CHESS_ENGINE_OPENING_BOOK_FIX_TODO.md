# CHESS_ENGINE_OPENING_BOOK_FIX_TODO.md

## Goal

Fix the opening-book implementation issues found in review.

The initial opening-book implementation is mostly good, but it has a critical side-indexing bug and several test/validation weaknesses.

This follow-up must stay focused on opening-book correctness, test strength, and suite runtime. Do not change search, evaluation, alpha-beta, TT, material values, piece-square tables, or move ordering.

---

## Task 0: Establish baseline

### 0.1 Copy handoff docs

- [ ] Copy this TODO into:

  ```text
  docs/CHESS_ENGINE_OPENING_BOOK_FIX_TODO.md
  ```

- [ ] Copy the companion spec into:

  ```text
  docs/CHESS_ENGINE_OPENING_BOOK_FIX_SPEC.md
  ```

### 0.2 Run opening-book tests

Run:

```bash
python -m pytest tests/test_opening_book.py -q --durations=20
```

- [ ] Record result.
- [ ] Record runtime.

Expected from review:

```text
25 passed in about 3 seconds
```

### 0.3 Run rules subset

Run:

```bash
python -m pytest tests/test_board_api.py tests/test_piece_moves.py tests/test_castling.py tests/test_en_passant.py tests/test_promotion.py tests/test_promotion_validation.py tests/test_promotion_move_generation.py tests/test_check_checkmate_stalemate.py tests/test_legal_moves.py -q
```

- [ ] Record result.

Expected from review:

```text
190 passed
```

### 0.4 Run targeted AI tests

Run:

```bash
python -m pytest tests/test_alpha_beta_pruning.py tests/test_ai_quality.py -q --durations=15
```

- [ ] Record result.

### 0.5 Run current non-slow suite

Run:

```bash
python -m pytest tests -q -m "not slow" --durations=25
```

- [ ] Record whether it completes.
- [ ] Record slowest tests.
- [ ] If it times out, continue with Task 8.

---

## Task 1: Fix side-aware opening-book indexing

### 1.1 Inspect current index builder

Open:

```text
chess_game/chess/opening_book.py
```

Find the code that builds the position index, likely inside:

```python
OpeningBook._build_index(...)
```

or equivalent.

Look for logic that indexes every ply of every line regardless of `line.side`.

### 1.2 Add side-aware helper

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

If `board.turn` is a string or other type, adapt accordingly.

### 1.3 Apply helper during replay

During line replay:

- [ ] Always parse the move.
- [ ] Always validate the move.
- [ ] Always apply the move.
- [ ] Only add a `BookMove` candidate to `_position_index` if `_should_index_line_move(line, board)` is true for the current pre-move position.

The pre-move board determines whose book move this is.

### 1.4 Preserve validation

Do not skip validation for moves that are not indexed.

For example, in a Black defense line:

```json
"moves": ["e2e4", "c7c5"]
```

`e2e4` should still be validated/applied, but not indexed for a `side="black"` line.

### 1.5 Add direct tests for side-aware indexing

Add tests proving:

- [ ] Starting-position candidates do not include candidates sourced from `side="black"` lines.
- [ ] After `e2e4`, Black candidates can include Sicilian `c7c5`.
- [ ] After `e2e4`, candidates do not include moves from White-only lines unless the side-to-move and line side match.
- [ ] `side="both"` test data indexes both sides when appropriate.

### 1.6 Verify starting-position source

Add a test that checks the selected starting-position move's candidate metadata.

Example intent:

```python
book_move = book.selected_candidate_for(Board())
assert book_move.name not in BLACK_DEFENSE_NAMES
```

If `find_book_move()` only returns `LegalMove`, use `candidates_for()` and selection helper, or add a test-only/public helper that returns `BookMove` if appropriate.

Do not overexpose internals if not necessary.

---

## Task 2: Remove broad exception swallowing in `get_best_move()`

### 2.1 Locate current integration

Open:

```text
chess_game/chess/ai.py
```

Find the opening-book logic in `get_best_move()`.

Look for broad handling such as:

```python
except Exception:
    pass
```

### 2.2 Remove broad catch

Change the logic to:

```python
if use_opening_book:
    book = opening_book or get_bundled_opening_book()
    book_move = book.find_book_move(board)
    if book_move is not None:
        return book_move
```

### 2.3 Preserve fallback semantics

The engine should fall back to search when:

```text
book lookup succeeds but returns None
```

The engine should not silently fall back when:

```text
bundled JSON is malformed
book validation fails
programming error occurs
```

### 2.4 Add regression test

Add a test using a fake/opening book object that raises an exception from `find_book_move()`.

Expected:

```python
with pytest.raises(ExpectedError):
    get_best_move(board, depth=1, use_opening_book=True, opening_book=bad_book)
```

Use a custom exception or `OpeningBookError`.

---

## Task 3: Strengthen opening-book tests

### 3.1 Add explicit move-application helper

In `tests/test_opening_book.py`, add:

```python
def apply_moves(board: Board, *moves: str) -> None:
    for text in moves:
        move = parse_move_notation(text)
        assert board.make_move(move.start, move.end, move.promotion)
```

Use the repo's actual `parse_move_notation` return shape.

### 3.2 Replace "first legal move" setup

Find tests that currently apply the first legal move instead of explicit notation.

Replace them with:

```python
apply_moves(board, "e2e4")
apply_moves(board, "e2e4", "e7e5")
...
```

### 3.3 Strengthen Black defense test

Test:

```text
after e2e4, c7c5 is present as a Black candidate
```

Suggested:

```python
board = Board()
apply_moves(board, "e2e4")
candidates = book.candidates_for(board)
assert candidate move c7c5 exists
```

### 3.4 Strengthen King's Gambit root test

Test:

```text
after e2e4 e7e5, f2f4 is present as a White candidate
```

Use `candidates_for()` instead of requiring `find_book_move()` to select King's Gambit unless King's Gambit is deliberately the highest weight.

### 3.5 Strengthen King's Gambit Accepted continuation

Test:

```text
after e2e4 e7e5 f2f4 e5f4, g1f3 is present
```

### 3.6 Strengthen King's Gambit Declined Classical continuation

Test:

```text
after e2e4 e7e5 f2f4 f8c5, g1f3 is present
```

### 3.7 Unknown position must return exactly None

Replace any permissive test like:

```python
if move is not None:
    assert hasattr(move, "start")
```

with:

```python
assert book.find_book_move(board) is None
```

Choose a position clearly outside the bundled book.

### 3.8 Candidates must be legal

For several book positions:

- [ ] get `board.get_legal_moves()`.
- [ ] normalize legal move identities.
- [ ] assert every `candidate.move` identity is present in legal moves.

Identity must include:

```text
start
end
promotion
```

### 3.9 Add helper for move-string identity

Add a helper if useful:

```python
def move_to_text(move: LegalMove) -> str:
    ...
```

Include promotion suffix.

Use the repo's existing algebraic/coordinate helpers if available.

---

## Task 4: Add missing schema validation tests and behavior

### 4.1 Non-dict top-level JSON

In `load_opening_book_data()` or parse layer, ensure non-object JSON raises:

```python
OpeningBookError
```

Do not return `{}` for non-dict JSON.

Test with:

```json
[]
```

or:

```json
"not an object"
```

- [x] Validated in `parse_opening_lines()` - checks `isinstance(data, dict)`
- [x] Test added: `test_non_dict_json_raises_error`

### 4.2 Unsupported selection value

Validate:

```text
selection == "highest_weight"
```

Add test:

```json
{
  "version": 1,
  "selection": "weighted_random",
  "lines": []
}
```

Expected:

```python
OpeningBookError
```

- [x] Validation added in `parse_opening_lines()` - checks `selection == "highest_weight"`
- [x] Test added: `test_unsupported_selection_value_raises_error`

### 4.3 Non-string move

Add or strengthen test:

```json
{
  "version": 1,
  "selection": "highest_weight",
  "lines": [
    {
      "name": "Bad Move Type",
      "side": "white",
      "moves": [123],
      "weight": 1
    }
  ]
}
```

Expected:

```python
OpeningBookError
```

- [x] Validation already in `_validate_move()` - checks `isinstance(move_str, str)`
- [x] Test added: `test_non_string_move_raises_error`

### 4.4 Keep existing schema tests passing

Existing tests for:

- [x] missing `lines`,
- [x] empty moves,
- [x] invalid side,
- [x] non-positive weight,
- [x] illegal move,

must still pass.

- [x] All existing validation tests pass

---

## Task 5: Fix deterministic promotion tie-break

### 5.1 Locate candidate sort key

Find sorting logic in:

```text
chess_game/chess/opening_book.py
```

Look for move-string tie-break like:

```python
f"{start_alg}{end_alg}"
```

### 5.2 Include promotion suffix

Update deterministic tie-break string to include promotion.

Pseudo-code:

```python
promotion_suffix = ""
if candidate.move.promotion is not None:
    promotion_suffix = candidate.move.promotion.name.lower()[0]
move_text = f"{start_alg}{end_alg}{promotion_suffix}"
```

Adapt to actual `PieceType` enum.

### 5.3 Add test

Build an in-memory test book with same start/end but different promotion candidates if practical.

If constructing a legal promotion book is cumbersome, directly test the sort-key helper if it is exposed/internal and stable enough.

Do not overbuild this if promotion book-line setup is too complicated, but make sure the production code handles promotion correctly.

---

## Task 6: Resolve optional CLI custom-book path status

### 6.1 Inspect CLI/self-play

Inspect likely entry points:

```text
chess_game/self_play.py
self_play.py
chess_game/cli.py
```

Search:

```bash
grep -R "no-opening-book\|opening-book\|use_opening_book" -n .
```

### 6.2 Choose implementation or deferral

Do one of the following.

#### Option A: Implement `--opening-book`

Add:

```text
--opening-book path/to/opening_book.json
```

Behavior:

- [ ] Load custom book with `OpeningBook.from_file(path)`.
- [ ] Pass loaded book to `get_best_move(..., opening_book=book)`.
- [ ] Works for both White and Black AI if self-play has both sides.
- [ ] If `--no-opening-book` is also supplied, either:
  - reject the combination, or
  - let `--no-opening-book` win.
- [ ] Document chosen behavior.

#### Option B: Mark deferred honestly

If not implementing custom book paths now:

- [ ] Update docs/TODO/memory note to say:

  ```text
  --no-opening-book is implemented.
  --opening-book custom JSON path is intentionally deferred.
  ```

- [ ] Remove any checked claim that custom path support is implemented.

Given this is optional, Option B is acceptable if documented.

---

## Task 7: Fix non-slow suite runtime

### 7.1 Run non-slow suite

Run:

```bash
python -m pytest tests -q -m "not slow" --durations=25
```

If it completes, record result and stop this task.

If it times out, continue.

### 7.2 Inspect slow strategy files

Run targeted timings around likely offenders:

```bash
python -m pytest tests/test_ai_strategy10_regressions.py tests/test_ai_strategy11_regressions.py tests/test_ai_strategy12_regressions.py tests/test_ai_strategy13_regressions.py -q --durations=25
```

Also search for depth-heavy non-slow tests:

```bash
grep -R "depth=3\|depth=4\|depth=5\|get_best_move" -n tests/test_ai_strategy*_regressions.py
```

### 7.3 Mark expensive strategy regression tests slow

At minimum, inspect:

```text
tests/test_ai_strategy13_regressions.py::test_strategy13_black_keeps_forcing_line_over_repetition
```

If it takes multiple seconds or performs complex depth-3+ strategic search, mark it:

```python
@pytest.mark.slow
```

or mark the module slow if it is entirely transcript/strategy regression oriented:

```python
pytestmark = pytest.mark.slow
```

### 7.4 Do not change AI behavior for runtime

This task is marker/classification only.

Do not change:

- minimax,
- alpha-beta,
- TT,
- eval,
- move ordering,
- strategy heuristics,

to make tests faster.

---

## Task 8: Documentation update

### 8.1 Update opening-book docs

Update `docs/OPENING_BOOK.md` or equivalent with:

- [ ] `side="white"` indexes only White-to-move book moves.
- [ ] `side="black"` indexes only Black-to-move book moves.
- [ ] `side="both"` indexes both.
- [ ] Bundled book errors fail loudly.
- [ ] Unknown positions fall back to search.

### 8.2 Update CLI docs/status

Document either:

- [ ] `--opening-book path` usage, if implemented, or
- [ ] custom book path intentionally deferred.

### 8.3 Keep docs concise

Do not paste the full implementation or all test details into README.

---

## Task 9: Final verification

### 9.1 JSON syntax

Run:

```bash
python -m json.tool chess_game/chess/data/opening_book.json >/dev/null
```

- [ ] Passes.

### 9.2 Opening-book tests

Run:

```bash
python -m pytest tests/test_opening_book.py -q --durations=20
```

- [ ] Passes.

### 9.3 Rules subset

Run:

```bash
python -m pytest tests/test_board_api.py tests/test_piece_moves.py tests/test_castling.py tests/test_en_passant.py tests/test_promotion.py tests/test_promotion_validation.py tests/test_promotion_move_generation.py tests/test_check_checkmate_stalemate.py tests/test_legal_moves.py -q
```

- [ ] Passes.

### 9.4 Targeted AI tests

Run:

```bash
python -m pytest tests/test_alpha_beta_pruning.py tests/test_ai_quality.py -q --durations=15
```

- [ ] Passes.

### 9.5 Fast non-slow suite

Run:

```bash
python -m pytest tests -q -m "not slow" --durations=25
```

- [ ] Passes.
- [ ] Completes in practical time.
- [ ] Record runtime and slowest tests.

### 9.6 Optional slow suite

Run if practical:

```bash
python -m pytest tests -q -m "slow" --durations=25
```

- [ ] Record result if run.

---

## Task 10: Guardrail diff review

Before finishing, inspect the diff.

### 10.1 Allowed changes

Expected files:

```text
chess_game/chess/opening_book.py
chess_game/chess/ai.py
tests/test_opening_book.py
tests/test_ai_strategy*_regressions.py
docs/*.md
possibly self_play/CLI file
possibly pyproject.toml only if package-data or docs need correction
```

### 10.2 Disallowed changes unless explicitly justified

Do not change:

```text
evaluation logic
material values
piece-square tables
minimax algorithm
alpha-beta algorithm
TT flag semantics
move ordering scores
board rules
legal move generation
```

### 10.3 Final checklist

- [ ] Side-aware indexing implemented.
- [ ] Black defense lines do not influence White starting book choice.
- [ ] White opening lines do not influence Black defense choices unless `side="both"`.
- [ ] Broad exception swallowing removed from `get_best_move()`.
- [ ] Opening-book tests use explicit move sequences.
- [ ] King's Gambit root and continuations are strongly tested.
- [ ] Unknown position returns exactly `None`.
- [ ] Candidates are verified legal.
- [ ] Unsupported `selection` raises `OpeningBookError`.
- [ ] Non-string move raises `OpeningBookError`.
- [ ] Promotion suffix included in sort tie-break.
- [ ] CLI custom path is implemented or explicitly deferred.
- [ ] Non-slow suite completes.
- [ ] No search/eval/TT behavior changed for this fix.
