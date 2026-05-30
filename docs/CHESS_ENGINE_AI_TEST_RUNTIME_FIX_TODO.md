# CHESS_ENGINE_AI_TEST_RUNTIME_FIX_TODO.md

## Goal

Finish the AI test-runtime cleanup.

The previous AI cleanup improved several real issues, but the default non-slow test suite is still not reliably fast/runnable. The goal of this pass is to correctly classify expensive AI/search/strategy tests as `slow`, preserve fast AI correctness coverage, and make the default test command practical again.

This is a test-infrastructure cleanup pass, not a chess-strength or search-engine rewrite.

---

## Task 0: Establish current baseline

### 0.1 Add handoff docs

- [x] Copy this TODO into:

  ```text
  docs/CHESS_ENGINE_AI_TEST_RUNTIME_FIX_TODO.md
  ```

- [x] Copy the companion spec into:

  ```text
  docs/CHESS_ENGINE_AI_TEST_RUNTIME_FIX_SPEC.md
  ```

### 0.2 Run rules subset

Run:

```bash
python -m pytest tests/test_board_api.py tests/test_piece_moves.py tests/test_castling.py tests/test_en_passant.py tests/test_promotion.py tests/test_promotion_validation.py tests/test_promotion_move_generation.py tests/test_check_checkmate_stalemate.py tests/test_legal_moves.py -q
```

Expected from latest review:

```text
190 passed
```

- [x] Record result and runtime.

### 0.3 Run targeted AI suites

Run:

```bash
python -m pytest tests/test_alpha_beta_pruning.py -q --durations=10
python -m pytest tests/test_ai_quality.py -q --durations=15
```

Expected from latest review:

```text
test_alpha_beta_pruning.py: 6 passed, roughly 13s
test_ai_quality.py: 52 passed, roughly 11s
```

- [x] Record result and runtime.

### 0.4 Run current non-slow suite

Run:

```bash
python -m pytest tests -q -m "not slow" --durations=25
```

- [x] Record whether it completes.
- [x] Record runtime.
- [x] Record slowest tests from `--durations=25`.
- [x] If it times out, run narrower files as described in Task 1.

---

## Task 1: Identify remaining expensive non-slow tests

### 1.1 Run likely offender files individually

Run:

```bash
python -m pytest tests/test_ai_endgame1_regressions.py -q --durations=25
python -m pytest tests/test_ai_search.py -q --durations=25
python -m pytest tests/test_ai_strategy5_regressions.py -q --durations=25
```

- [x] Record runtimes.
- [x] Record tests taking more than approximately 1 second.
- [x] Record tests using depth 3+ search.
- [x] Record tests using transcript-style exact move assertions.

### 1.2 Search for depth-heavy tests

Run:

```bash
grep -R "depth=3\|depth=4\|depth=5\|white_depth\|black_depth\|get_best_move" -n tests
```

Review matches in AI/search/strategy tests.

- [x] Identify depth-4/depth-5 tests.
- [x] Identify depth-3 tests on complex positions.
- [x] Identify self-play tests.
- [x] Identify exact-move strategic regression tests.

### 1.3 Search current slow markings

Run:

```bash
grep -R "pytest.mark.slow\|pytestmark = pytest.mark.slow" -n tests
```

- [x] Confirm which AI files are already marked slow.
- [x] Identify inconsistent files of the same category that are not marked slow.

---

## Task 2: Mark `test_ai_endgame1_regressions.py` slow or split it

### 2.1 Inspect file

Open:

```text
tests/test_ai_endgame1_regressions.py
```

Look for:

- depth-3 `get_best_move(...)`,
- complex endgame strategic positions,
- exact move assertions,
- tests taking multiple seconds.

### 2.2 Preferred fix: mark module slow

If the whole file is transcript/strategy/endgame-regression oriented, add at top:

```python
import pytest

pytestmark = pytest.mark.slow
```

This is likely the right fix.

### 2.3 Alternative fix: split fast and slow tests

If the file contains a few genuinely cheap unit tests, keep those non-slow and mark only expensive tests:

```python
@pytest.mark.slow
def test_expensive_endgame_search(...):
    ...
```

Do not spend too much time micro-splitting. Module-level slow is acceptable for transcript-style strategic regression files.

### 2.4 Verify

Run:

```bash
python -m pytest tests/test_ai_endgame1_regressions.py -q -m "not slow"
python -m pytest tests/test_ai_endgame1_regressions.py -q -m "slow" --durations=10
```

Expected:

- non-slow should be empty or fast,
- slow should run the endgame regressions.

---

## Task 3: Review and mark expensive tests in `test_ai_search.py`

### 3.1 Identify expensive tests

Run:

```bash
python -m pytest tests/test_ai_search.py -q --durations=25
```

Look especially for tests like:

```text
test_search_sees_prophylactic_line_is_best
test_search_prefers_clean_simplifying_line_over_repeated_checking
test_search_rejects_material_win_that_opens_fatal_counterplay
```

These are strategic/depth-search tests and may be too slow for default CI.

### 3.2 Keep fast correctness tests non-slow

Do **not** mark these slow if they are fast:

- mate-in-one at depth 1,
- terminal-state handling,
- `depth < 1` validation,
- TT unit behavior,
- move-ordering helper tests,
- promotion identity tests,
- shallow alpha-beta correctness tests.

### 3.3 Mark expensive strategic tests slow

For each expensive strategic end-to-end search test, add:

```python
@pytest.mark.slow
```

Use this rule:

```text
If it calls get_best_move(depth=3) on a complex tactical/strategic position and takes multiple seconds, mark slow.
```

### 3.4 Consider rewriting if a cheaper test is possible

If a test is trying to verify a helper-level behavior, rewrite it to call the helper directly rather than doing full depth-3 search.

Examples:

- If testing move ordering, call `_order_moves(...)` directly.
- If testing TT flags, call `_check_tt_cache(...)` / `_store_tt_cache(...)` or a shallow minimax.
- If testing terminal handling, use depth 1.

Do not rewrite strategic tests into brittle mocks unless needed. Marking slow is acceptable.

### 3.5 Verify

Run:

```bash
python -m pytest tests/test_ai_search.py -q -m "not slow" --durations=20
python -m pytest tests/test_ai_search.py -q -m "slow" --durations=20
```

Non-slow must finish quickly.

---

## Task 4: Review `test_ai_strategy5_regressions.py`

### 4.1 Inspect file

Open:

```text
tests/test_ai_strategy5_regressions.py
```

Look for:

- full `get_best_move(...)` calls,
- depth 3+,
- transcript-derived strategic expectations,
- multi-second tests.

### 4.2 Mark slow if needed

If the file is primarily strategic/transcript regression tests, add:

```python
import pytest

pytestmark = pytest.mark.slow
```

If only a few tests are expensive, mark those tests individually.

### 4.3 Verify

Run:

```bash
python -m pytest tests/test_ai_strategy5_regressions.py -q -m "not slow" --durations=20
python -m pytest tests/test_ai_strategy5_regressions.py -q -m "slow" --durations=20
```

---

## Task 5: Review other AI strategy/regression files for consistency

### 5.1 List AI/regression files

Run:

```bash
ls tests/test_ai* tests/test_strategy* 2>/dev/null
```

Review whether these files are consistently categorized.

### 5.2 Mark comparable files consistently

If files like these are slow:

```text
tests/test_ai_strategy6_regressions.py
tests/test_ai_strategy7_regressions.py
tests/test_ai_review_loop.py
```

then comparable transcript/depth-heavy files should also be slow.

### 5.3 Avoid marking basic AI unit tests slow

Keep these non-slow if reasonably fast:

```text
tests/test_ai_quality.py
tests/test_alpha_beta_pruning.py
small tests in tests/test_ai_search.py
```

If one or two tests inside these files are slow, mark only those tests slow.

---

## Task 6: Clean up weak or misleading pruning/window tests only if needed

### 6.1 Locate tight-vs-wide window tests

Run:

```bash
grep -R "tight.*window\|wide.*window\|without_pruning\|no_prune" -n tests
```

### 6.2 Preserve true alpha-beta vs no-prune tests

Keep tests that compare:

```text
plain minimax node count
vs.
alpha-beta node count
```

at shallow depth.

### 6.3 Optional cleanup

If a tight-window vs wide-window test is slow or confusing:

- [x] rename it to clearly describe aspiration/window behavior, or
- [x] mark it slow, or
- [x] remove it if redundant.

Do not spend much time here unless it affects runtime or clarity.

---

## Task 7: Verify hidden depth-5 shortcut is still gone

Run:

```bash
grep -R "_is_initial_position\|_preferred_starting_move\|depth >= 5" -n chess_game tests
```

- [x] Confirm no hidden `get_best_move()` shortcut was reintroduced.
- [x] If any match exists, inspect it.
- [x] Do not re-add the old starting-position shortcut.

---

## Task 8: Verify no search/evaluation behavior was changed

### 8.1 Check git diff

Review the patch.

Expected changed files should mostly be:

```text
tests/*.py
docs/*.md
memory.md
possibly pytest configuration
```

Engine files should not normally change in this pass.

### 8.2 Confirm no evaluation/search tuning

Make sure this pass did not change:

- material values,
- piece-square tables,
- minimax logic,
- alpha-beta logic,
- TT semantics,
- move ordering scores,
- strategy guidance modules.

If a code change outside tests/docs was necessary, document why.

---

## Task 9: Update `memory.md` briefly if useful

### 9.1 Add a short current-state note

If `memory.md` is used by Copilot/OpenCode, add a short note near the top:

```text
Current AI test-runtime cleanup state:
- Rules engine remains stable.
- Expensive AI/strategy transcript tests are marked slow.
- Default command is python -m pytest tests -q -m "not slow".
- Slow/extended command is python -m pytest tests -q -m "slow".
- Do not re-add hidden depth-5 opening shortcut.
- Do not tune evaluation in this pass.
```

### 9.2 Mark old entries historical

If the file has old misleading notes, add:

```text
Older entries below are historical and may describe resolved bugs.
```

Do not rewrite the entire file.

---

## Task 10: Final verification

### 10.1 Fast default suite

Run:

```bash
python -m pytest tests -q -m "not slow" --durations=25
```

Required:

- [x] passes,
- [x] completes in a practical time,
- [x] preferably under 2 minutes,
- [x] hard target under 3 minutes.

Record result and top slowest tests.

### 10.2 Rules subset

Run:

```bash
python -m pytest tests/test_board_api.py tests/test_piece_moves.py tests/test_castling.py tests/test_en_passant.py tests/test_promotion.py tests/test_promotion_validation.py tests/test_promotion_move_generation.py tests/test_check_checkmate_stalemate.py tests/test_legal_moves.py -q
```

Required:

- [x] passes.

### 10.3 Targeted AI suites

Run:

```bash
python -m pytest tests/test_alpha_beta_pruning.py -q --durations=10
python -m pytest tests/test_ai_quality.py -q --durations=15
```

Required:

- [x] pass.
- [x] If these remain in the default non-slow suite, their runtime must be acceptable.

### 10.4 Slow suite

Run when practical:

```bash
python -m pytest tests -q -m "slow" --durations=25
```

Required:

- [x] record result,
- [x] record runtime,
- [x] slow suite may be expensive but should be runnable manually.

### 10.5 Marker consistency check

Run:

```bash
python -m pytest tests --collect-only -q -m "slow"
python -m pytest tests --collect-only -q -m "not slow"
```

Confirm slow and non-slow split looks sane.

---

## Acceptance checklist

The patch is complete only when:

- [x] `tests/test_ai_endgame1_regressions.py` has been marked slow or split appropriately.
- [x] Expensive tests in `tests/test_ai_search.py` have been marked slow or rewritten cheaply.
- [x] `tests/test_ai_strategy5_regressions.py` has been reviewed and marked slow if appropriate.
- [x] Comparable strategy/transcript regression files are classified consistently.
- [x] Fast AI correctness tests remain non-slow.
- [x] `python -m pytest tests -q -m "not slow" --durations=25` passes and completes under the target runtime.
- [x] Slow tests are available via `python -m pytest tests -q -m "slow"`.
- [x] Hidden depth-5 starting-position shortcut was not reintroduced.
- [x] No evaluation/search/TT behavior was changed for runtime reasons.
- [x] `memory.md` is updated only briefly, if at all.
