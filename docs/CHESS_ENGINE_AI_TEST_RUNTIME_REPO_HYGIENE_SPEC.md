# CHESS_ENGINE_AI_TEST_RUNTIME_REPO_HYGIENE_SPEC.md

## Purpose

This spec defines a focused cleanup pass for the broader AI/test-runtime and repo-hygiene issues that remain after the opening-book work.

The chess engine is now playing well, and the opening-book feature is functionally complete. This pass is **not** about making the engine stronger. It is about making the project easier to maintain, test, review, and extend.

The cleanup should address:

1. AI/test-runtime reliability.
2. Slow-test classification.
3. Public AI API clarity.
4. Repository hygiene.
5. Generated artifact cleanup.
6. Minor obvious code cleanup.
7. Verification command consistency.

---

## Current known issues

From the latest review:

1. The full non-slow suite did not reliably complete as one command in the review environment:

   ```bash
   python -m pytest tests -q -m "not slow" --durations=25
   ```

   Copilot reported it completing in about 18 seconds, but that could not be reproduced in review.

2. `pyproject.toml` appears to use verbose pytest defaults, such as:

   ```toml
   addopts = "-v"
   ```

   This may conflict with attempts to run quiet/fast test commands using `-q`.

3. `get_best_move()` accepts opening-book options through `**kwargs` instead of explicit keyword-only parameters.

4. `opening_book.py` has a harmless but sloppy duplicate line:

   ```python
   pos_key = position_key(board)
   pos_key = position_key(board)
   ```

5. The repo zip includes `tmp/` audit files, likely generated strategy outputs.

6. The repo has historically accumulated generated artifacts such as:

   ```text
   __pycache__/
   .pytest_cache/
   *.pyc
   tmp/
   audit output files
   ```

7. `sys.setrecursionlimit(...)` values remain high:

   ```text
   chess_game/chess/ai.py: 50000
   chess_game/self_play.py: 5000
   ```

   This is not necessarily part of this patch unless it is safe to reduce/remove, but it should be audited.

---

## Non-goals

Do **not** do any of the following in this pass:

- Do not tune evaluation.
- Do not change material values.
- Do not change piece-square tables.
- Do not change move-ordering scores.
- Do not change alpha-beta pruning semantics.
- Do not change transposition-table semantics.
- Do not change minimax behavior.
- Do not add new chess heuristics.
- Do not add new opening-book lines.
- Do not change the opening-book selection policy.
- Do not add quiescence search.
- Do not add UCI support.
- Do not rewrite the engine architecture.
- Do not weaken tests to make them pass faster.
- Do not mark all AI tests slow just to get a fast default suite.

This pass is about test classification, project hygiene, API clarity, and low-risk cleanup.

---

## Required cleanup areas

## 1. Make the non-slow suite reproducible

The default fast suite must be reproducible from a clean shell:

```bash
python -m pytest tests -q -m "not slow" --durations=25
```

The result should include:

```text
pass/fail status
runtime
selected/deselected counts
slowest tests
```

If the command does not complete reliably, identify which non-slow tests are too expensive or hanging.

### Rules

- Depth 4/5 AI tests should be slow.
- Complex transcript-style strategy tests should be slow.
- Multi-second strategic search tests should usually be slow.
- Small tactical correctness tests should stay non-slow.
- Rules tests should stay non-slow.
- Opening-book tests should stay non-slow if they remain fast.

---

## 2. Review pytest configuration

Inspect:

```text
pyproject.toml
pytest.ini
setup.cfg
tox.ini
```

Look for pytest config such as:

```toml
addopts = "-v"
```

If verbose mode is globally forced, update it so quiet commands are not undermined.

Preferred:

```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow/extended",
]
```

Avoid global `-v` unless there is a strong reason.

Do not hide warnings or suppress failures.

---

## 3. Clean up `get_best_move()` public API

The opening-book options should be explicit keyword-only parameters, not hidden inside `**kwargs`.

Preferred signature shape:

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

If existing callers need compatibility with additional keyword options, keep only the truly required ones. Do not leave opening-book parameters buried in `kwargs`.

All existing tests and callers must continue to work.

Search tests that need pure search should explicitly use:

```python
get_best_move(board, depth=..., use_opening_book=False)
```

---

## 4. Remove trivial duplicate/cleanup issues

Remove obvious redundant lines, especially:

```python
pos_key = position_key(board)
pos_key = position_key(board)
```

in `opening_book.py`.

This is not a behavior change; it is clarity cleanup.

---

## 5. Repo hygiene and generated artifacts

The committed/uploaded repo should not contain generated runtime artifacts unless intentionally documented.

Remove or ignore:

```text
__pycache__/
.pytest_cache/
*.pyc
tmp/
*.log
strategy audit output files
coverage output
```

Recommended `.gitignore` additions:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
tmp/
*.log
```

If some `tmp/` files are intentionally checked in as reference artifacts, move them to a documented directory such as:

```text
docs/audits/
tests/fixtures/
```

and explain why they are source-controlled.

Default recommendation: remove `tmp/` generated audit files from the repo.

---

## 6. Audit recursion-limit changes

Inspect:

```python
sys.setrecursionlimit(...)
```

Current known locations:

```text
chess_game/chess/ai.py
chess_game/self_play.py
```

Do not change this blindly if tests depend on it.

Preferred process:

1. Document why the recursion-limit increase exists.
2. Try removing or reducing it in a branch.
3. Run tests.
4. If safe, remove or lower it.
5. If not safe, leave it but add a short comment explaining why.

This is a cleanup item, not a required correctness fix.

---

## 7. Test file classification and structure

Review AI test files for consistency.

Likely categories:

```text
Fast default:
  rules tests
  opening-book tests
  shallow AI correctness
  helper/unit tests
  mate-in-one depth 1
  shallow alpha-beta/no-prune tests

Slow:
  transcript strategy regressions
  multi-second strategic searches
  self-play loops
  depth 4/5 searches
  large node-count tests
```

Prefer marking individual expensive tests slow. If a whole file is transcript/regression/strategy heavy, module-level `pytestmark = pytest.mark.slow` is acceptable.

---

## 8. Verification output discipline

When marking TODO items complete, include actual command output summaries.

For final verification, record:

```bash
python -m pytest tests/test_opening_book.py -q --durations=20
python -m pytest tests/test_alpha_beta_pruning.py tests/test_ai_quality.py -q --durations=15
python -m pytest tests/test_board_api.py tests/test_piece_moves.py tests/test_castling.py tests/test_en_passant.py tests/test_promotion.py tests/test_promotion_validation.py tests/test_promotion_move_generation.py tests/test_check_checkmate_stalemate.py tests/test_legal_moves.py -q
python -m pytest tests -q -m "not slow" --durations=25
python -m pytest tests --collect-only -q -m "not slow"
python -m pytest tests --collect-only -q -m "slow"
```

If any command cannot complete, say so and capture the last visible test file/test.

---

## Acceptance criteria

This cleanup is complete when:

1. `get_best_move()` has explicit opening-book keyword parameters.
2. Existing callers/tests are updated for the explicit signature.
3. The duplicate `position_key(board)` line is removed.
4. Pytest config no longer forces noisy/contradictory defaults such as global `-v` unless justified.
5. The non-slow suite completes reproducibly or the remaining blocker is identified and documented.
6. Multi-second strategy/transcript tests are marked `slow`.
7. Fast correctness tests remain non-slow.
8. `tmp/` generated audit files are removed or intentionally relocated/documented.
9. `.gitignore` excludes generated artifacts.
10. `__pycache__`, `.pytest_cache`, `*.pyc`, and similar artifacts are absent.
11. `sys.setrecursionlimit(...)` uses are either removed, reduced, or documented with justification.
12. Opening-book tests still pass.
13. Rules subset still passes.
14. Targeted AI tests still pass.
15. No minimax/alpha-beta/TT/evaluation/move-ordering behavior is changed.
