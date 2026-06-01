# replies6.md

## Answers to Copilot clarification questions

Here are the answers for Copilot.

---

## 1. `get_best_move()` API cleanup

Remove the opening-book `**kwargs` compatibility path.

Make `use_opening_book` and `opening_book` explicit keyword-only parameters:

```python
def get_best_move(
    board: Board,
    depth: int,
    stats: Optional[SearchStats] = None,
    position_counts: Optional[dict[str, int]] = None,
    *,
    use_opening_book: bool = True,
    opening_book: Optional[OpeningBook] = None,
) -> Optional[LegalMove]:
    ...
```

Do **not** keep:

```python
kwargs.pop("use_opening_book", ...)
kwargs.pop("opening_book", ...)
```

If there are unrelated future keyword options, add them explicitly later when needed. Avoid vague `**kwargs` unless there is a real current caller that requires it.

---

## 2. Generated artifact cleanup

Remove all `tmp/` content from the repo by default.

Do **not** preserve or move any `tmp/` audit files unless they are required by tests or explicitly referenced by documentation. The current assumption is that they are generated strategy/audit output and should not be source-controlled.

Add or verify `.gitignore` includes:

```gitignore
tmp/
*.log
.coverage
htmlcov/
__pycache__/
*.py[cod]
.pytest_cache/
```

---

## 3. Recursion-limit changes

Audit them, then remove or reduce if safe.

Preferred order:

1. Try removing `sys.setrecursionlimit(...)`.
2. Run targeted AI/search/self-play tests.
3. If tests pass, leave it removed.
4. If removal fails, reduce to the smallest reasonable value that passes.
5. If it must stay high, add a short comment explaining why.

Do **not** keep huge values like `50000` without justification.

---

## 4. Slow-test classification scope

No special fast-test exceptions for multi-second strategic/transcript tests.

If a test regularly takes multiple seconds and is not a core correctness test, mark it `slow`.

Keep non-slow only for things like:

```text
rules tests
opening-book tests
shallow AI correctness
mate-in-one depth 1
terminal-state handling
small helper/unit tests
shallow alpha-beta/no-prune tests
```

Depth-4/5, transcript-style, self-play, and multi-second strategic tests should be `slow`.

---

## 5. Pytest config cleanup

Remove global verbose defaults like:

```toml
addopts = "-v"
```

unless there is a very strong documented reason to keep them.

The default config should not fight commands like:

```bash
python -m pytest tests -q -m "not slow"
```

Keep the `slow` marker declaration. Do not add warning suppressions or broad ignores.

---

## 6. Task 0 copy-doc subtasks

Yes. If the docs already exist in the repo, mark Task 0 copy-doc subtasks complete.

Do not duplicate or rename them. Just verify these files exist:

```text
docs/CHESS_ENGINE_AI_TEST_RUNTIME_REPO_HYGIENE_SPEC.md
docs/CHESS_ENGINE_AI_TEST_RUNTIME_REPO_HYGIENE_TODO.md
```

Then mark the copy-doc subtasks done.

---

## Final locked guidance

```text
1. Remove opening-book **kwargs compatibility; use explicit keyword-only parameters.
2. Remove tmp/ generated artifacts by default.
3. Remove/reduce recursion-limit calls if safe; otherwise document why they remain.
4. Mark multi-second strategic/transcript tests slow; no special exceptions.
5. Remove global pytest -v defaults unless strongly justified.
6. Mark Task 0 doc-copy subtasks complete if files already exist.
```

These decisions answer the six clarification items Copilot raised.
