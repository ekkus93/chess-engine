# CHESS_ENGINE_AI_TEST_RUNTIME_REPO_HYGIENE_TODO.md

## Goal

Clean up the broader AI/test-runtime and repo-hygiene issues that remain after the opening-book work.

This pass should make the project easier to test, review, and maintain. It should not change chess strength, evaluation, minimax, alpha-beta, TT, or move ordering behavior.

---

## Task 0: Add handoff docs and establish baseline

### 0.1 Copy docs

- [ ] Copy this TODO into:

  ```text
  docs/CHESS_ENGINE_AI_TEST_RUNTIME_REPO_HYGIENE_TODO.md
  ```

- [ ] Copy the companion spec into:

  ```text
  docs/CHESS_ENGINE_AI_TEST_RUNTIME_REPO_HYGIENE_SPEC.md
  ```

### 0.2 Run targeted baseline tests

Run:

```bash
python -m pytest tests/test_opening_book.py -q --durations=20
python -m pytest tests/test_alpha_beta_pruning.py tests/test_ai_quality.py -q --durations=15
```

- [ ] Record results.
- [ ] Record runtimes.

### 0.3 Run rules subset

Run:

```bash
python -m pytest tests/test_board_api.py tests/test_piece_moves.py tests/test_castling.py tests/test_en_passant.py tests/test_promotion.py tests/test_promotion_validation.py tests/test_promotion_move_generation.py tests/test_check_checkmate_stalemate.py tests/test_legal_moves.py -q
```

- [ ] Record result.
- [ ] Record runtime.

### 0.4 Run non-slow suite

Run:

```bash
python -m pytest tests -q -m "not slow" --durations=25
```

- [ ] Record whether it completes.
- [ ] Record selected/deselected counts.
- [ ] Record runtime.
- [ ] Record slowest tests.
- [ ] If it times out, record the last visible test/file before timeout.

---

## Task 1: Review pytest configuration

### 1.1 Inspect config files

Inspect:

```text
pyproject.toml
pytest.ini
setup.cfg
tox.ini
```

Search:

```bash
grep -R "addopts\|markers\|filterwarnings" -n pyproject.toml pytest.ini setup.cfg tox.ini 2>/dev/null
```

### 1.2 Remove contradictory global verbosity

If pytest config contains:

```toml
addopts = "-v"
```

or equivalent, remove it unless there is a strong reason to force verbose output globally.

Preferred config should not fight this command:

```bash
python -m pytest tests -q -m "not slow"
```

### 1.3 Keep slow marker declared

Ensure the slow marker is declared:

```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow/extended",
]
```

Adapt to the repo's existing config style.

### 1.4 Do not hide warnings/failures

Do not add warning suppressions or failure-hiding config.

- [ ] No new broad `filterwarnings = ignore`.
- [ ] No new `xfail_strict = false` if not already present.
- [ ] No new test skipping to hide failures.

---

## Task 2: Make `get_best_move()` opening-book API explicit

### 2.1 Inspect current signature

Open:

```text
chess_game/chess/ai.py
```

Find:

```python
def get_best_move(...):
```

Current issue from review:

```python
def get_best_move(..., **kwargs: object):
    use_opening_book_obj = kwargs.pop("use_opening_book", True)
    opening_book_obj = kwargs.pop("opening_book", None)
```

### 2.2 Add explicit keyword-only parameters

Preferred shape:

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

If there are other legitimate keyword-only parameters, include them explicitly.

### 2.3 Remove opening-book parsing from `kwargs`

Remove:

```python
kwargs.pop("use_opening_book", ...)
kwargs.pop("opening_book", ...)
```

for opening-book behavior.

### 2.4 Update call sites

Search:

```bash
grep -R "get_best_move(" -n chess_game tests
```

Update any call sites as needed.

Search-specific tests should use:

```python
use_opening_book=False
```

### 2.5 Type/lint check

Run relevant tests after this refactor.

- [ ] No existing caller is broken.
- [ ] Opening book still works by default.
- [ ] Search tests can still disable the book.

---

## Task 3: Remove trivial duplicate code in opening book

### 3.1 Locate duplicate position key line

Open:

```text
chess_game/chess/opening_book.py
```

Find duplicate code like:

```python
pos_key = position_key(board)
pos_key = position_key(board)
```

### 3.2 Remove duplicate

- [ ] Remove the redundant line.
- [ ] Run `tests/test_opening_book.py`.

This should be a no-behavior-change cleanup.

---

## Task 4: Clean repo generated artifacts

### 4.1 Identify generated files

Run:

```bash
find . \( -type d -name "__pycache__" -o -type d -name ".pytest_cache" -o -type f -name "*.pyc" -o -type d -name "tmp" \) -print
```

Also inspect:

```bash
find tmp -maxdepth 2 -type f 2>/dev/null | sort
```

### 4.2 Remove standard generated files

Remove:

```bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### 4.3 Decide what to do with `tmp/`

If `tmp/` contains generated audit output, remove it from the repo.

Preferred:

```bash
rm -rf tmp
```

If any files are intentionally valuable reference artifacts, move them to a documented location such as:

```text
docs/audits/
tests/fixtures/
```

and explain why they are source-controlled.

Do not leave untracked/generated strategy audit output in `tmp/`.

### 4.4 Update `.gitignore`

Ensure `.gitignore` contains:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
tmp/
*.log
```

Add only entries that make sense for this repo.

### 4.5 Verify cleanup

Run:

```bash
find . \( -type d -name "__pycache__" -o -type d -name ".pytest_cache" -o -type f -name "*.pyc" \) -print
```

Expected: no output.

If `tmp/` is intentionally retained, document why. Otherwise:

```bash
test ! -d tmp
```

---

## Task 5: Audit slow-test classification

### 5.1 Collect test inventory

Run:

```bash
python -m pytest tests --collect-only -q -m "not slow" > /tmp/not_slow_tests.txt
python -m pytest tests --collect-only -q -m "slow" > /tmp/slow_tests.txt
```

Record counts.

### 5.2 Profile non-slow tests

Run:

```bash
python -m pytest tests -q -m "not slow" --durations=50
```

If this times out, run likely groups:

```bash
python -m pytest tests/test_ai_strategy*_regressions.py -q -m "not slow" --durations=50
python -m pytest tests/test_ai_search.py -q -m "not slow" --durations=50
python -m pytest tests/test_alpha_beta_pruning.py -q -m "not slow" --durations=50
```

### 5.3 Mark expensive strategy/transcript tests slow

Mark tests slow if they are:

- [ ] multi-second strategy regressions,
- [ ] transcript-derived exact-move tests,
- [ ] depth 4/5 searches,
- [ ] self-play loops,
- [ ] large node-count tests.

Use:

```python
@pytest.mark.slow
```

or module-level:

```python
pytestmark = pytest.mark.slow
```

only when the whole file is extended/strategy-regression oriented.

### 5.4 Preserve fast AI correctness tests

Do not mark these slow unless genuinely expensive:

- [ ] mate-in-one depth 1,
- [ ] terminal state handling,
- [ ] depth validation,
- [ ] TT helper/unit tests,
- [ ] move-ordering helper tests,
- [ ] opening-book tests,
- [ ] shallow alpha-beta/no-prune comparison tests.

---

## Task 6: Audit recursion-limit usage

### 6.1 Locate recursion-limit calls

Run:

```bash
grep -R "setrecursionlimit" -n chess_game tests
```

Known locations from review:

```text
chess_game/chess/ai.py
chess_game/self_play.py
```

### 6.2 Decide per location

For each call:

- [ ] Determine why it exists.
- [ ] Try removing or reducing it if safe.
- [ ] Run targeted tests.
- [ ] If keeping it, add a short comment explaining why.

Do not destabilize the engine for this cleanup.

### 6.3 Acceptance

One of the following must be true:

- [ ] Recursion-limit change removed.
- [ ] Recursion-limit value reduced to a reasonable documented value.
- [ ] Existing value kept with a clear comment explaining why.

---

## Task 7: Re-run verification

### 7.1 Opening-book tests

Run:

```bash
python -m pytest tests/test_opening_book.py -q --durations=20
```

- [ ] Passes.

### 7.2 Rules subset

Run:

```bash
python -m pytest tests/test_board_api.py tests/test_piece_moves.py tests/test_castling.py tests/test_en_passant.py tests/test_promotion.py tests/test_promotion_validation.py tests/test_promotion_move_generation.py tests/test_check_checkmate_stalemate.py tests/test_legal_moves.py -q
```

- [ ] Passes.

### 7.3 Targeted AI tests

Run:

```bash
python -m pytest tests/test_alpha_beta_pruning.py tests/test_ai_quality.py -q --durations=15
```

- [ ] Passes.

### 7.4 Full non-slow suite

Run from a clean shell:

```bash
python -m pytest tests -q -m "not slow" --durations=25
```

- [ ] Passes.
- [ ] Completes in practical time.
- [ ] Record selected/deselected counts.
- [ ] Record runtime.
- [ ] Record slowest tests.

If it still does not complete, document the exact last visible test/file and the timeout duration.

### 7.5 Optional slow suite

Run if practical:

```bash
python -m pytest tests -q -m "slow" --durations=25
```

- [ ] Record result if run.
- [ ] It is acceptable for this to be slower than the default suite.

---

## Task 8: Guardrail diff review

### 8.1 Expected changed files

Likely:

```text
chess_game/chess/ai.py
chess_game/chess/opening_book.py
tests/*.py
pyproject.toml or pytest config
.gitignore
docs/*.md
```

Possibly:

```text
chess_game/self_play.py
```

only if recursion-limit/comment/API cleanup requires it.

### 8.2 Disallowed behavior changes

Confirm no changes to:

- [ ] minimax semantics,
- [ ] alpha-beta semantics,
- [ ] TT flag semantics,
- [ ] evaluation scores,
- [ ] material values,
- [ ] piece-square tables,
- [ ] move-ordering scoring,
- [ ] legal move generation,
- [ ] board rules.

### 8.3 Final checklist

- [ ] `get_best_move()` has explicit opening-book keyword parameters.
- [ ] Duplicate `position_key(board)` line removed.
- [ ] Pytest config does not force noisy/contradictory global verbosity.
- [ ] Slow marker remains declared.
- [ ] Generated files removed.
- [ ] `.gitignore` excludes generated artifacts.
- [ ] `tmp/` is removed or intentionally relocated/documented.
- [ ] Slow tests are classified consistently.
- [ ] Recursion-limit usage is removed, reduced, or documented.
- [ ] Opening-book tests pass.
- [ ] Rules subset passes.
- [ ] Targeted AI tests pass.
- [ ] Non-slow suite result is captured.
- [ ] No chess search/eval behavior changed.
