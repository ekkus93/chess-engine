# Replies to Fix 3 Questions

## 1. Approach: minimal fixes vs refactor

Proceed with the **minimal strict-predicate fixes first**.

Do **not** start with the `MoveKind` / `ValidatedMove` refactor. The current bugs are narrow and can be fixed safely with targeted guards:

- king capture rejection in validation,
- strict en passant execution predicate,
- castling execution requiring `PieceType.KING`.

Only consider Task 7 if the minimal fixes create ugly duplication or unclear control flow. Based on the current known bugs, Task 7 is **not required yet**. The TODO already frames the refactor as conditional, so follow that.

## 2. Commit strategy

Use **paired test + fix commits**, not one giant commit.

Recommended commit order:

```text
1. test+fix: reject king captures
2. test+fix: require strict en passant execution criteria
3. test+fix: require king piece for castling execution
4. docs: add fix3 repair notes, if needed
```

I would slightly compress the proposed seven commits by pairing each regression test with its corresponding fix. That keeps history readable without creating too many tiny commits.

Do **not** wait until the end for one big commit. These bugs are independent enough that each should be isolated.

## 3. Test helper conventions

Yes, inspect the existing tests before writing new ones.

Specifically check:

```bash
tests/conftest.py
tests/helpers.py
tests/test_castling*.py
tests/test_en_passant*.py
tests/test_king_safety.py
tests/test_board*.py
```

Use the existing helper style if available. Prefer:

```python
sq("e4")
assert_piece(...)
assert_empty(...)
```

over raw row/column constants.

If `assert_piece` or `assert_empty` do not exist, create them in the existing helper module rather than duplicating helper functions in multiple test files.

Use the existing pytest functional style unless the surrounding file already uses classes. Do not introduce a new testing style just for these regressions.

## 4. Baseline

Yes. Run the baseline first.

```bash
python -m pytest tests -q
```

Expected current baseline is approximately:

```text
189 passed
```

If the count differs slightly because files changed, continue only if the suite is already passing. If there are failures before making Fix 3 changes, stop and inspect them first so new regressions are not mixed with pre-existing failures.

## 5. Task 7 evaluation

After Tasks 2/4/6 are done, briefly evaluate whether Task 7 is needed.

But the default answer is: **skip Task 7 unless the minimal fixes are messy or fragile.**

Acceptance standard:

- If `_is_en_passant_capture(...)` becomes strict and readable,
- `_is_castling_move(...)` simply requires a king,
- king captures are rejected cleanly in validation,
- all new regression tests pass,

then **do not implement `MoveKind` / `ValidatedMove` in this patch**.

That refactor can wait for a future cleanup pass. The immediate goal is correctness with minimal risk.
