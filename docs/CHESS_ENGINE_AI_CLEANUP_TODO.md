# CHESS_ENGINE_AI_CLEANUP_TODO.md

## Goal

Clean up the chess engine AI/search layer after the recent alpha-beta/TT work.

This TODO focuses on:

- making the default test suite fast again,
- removing or exposing the hidden depth-5 opening shortcut,
- fixing a broken node-count test,
- preventing TT root score/move mismatch,
- cleaning up misleading alpha-beta tests,
- removing generated cache files,
- preventing further AI heuristic sprawl in this patch.

Do not broaden this patch into evaluation tuning or new chess features.

---

## Task 0: Establish baseline

### 0.1 Run targeted baseline commands

Run these from the repo root:

```bash
python -m pytest tests/test_board_api.py tests/test_piece_moves.py tests/test_castling.py tests/test_en_passant.py tests/test_promotion.py tests/test_promotion_validation.py tests/test_promotion_move_generation.py tests/test_check_checkmate_stalemate.py tests/test_legal_moves.py -q
```

Expected from review:

```text
190 passed
```

Run:

```bash
python -m pytest tests/test_alpha_beta_pruning.py -q
python -m pytest tests/test_ai_quality.py -q
```

Record current results and durations.

### 0.2 Measure default non-slow runtime

Run:

```bash
python -m pytest tests -q -m "not slow" --durations=25
```

If this times out or takes too long, capture the slowest tests from partial output or run narrower groups with `--durations=25`.

### 0.3 Add this handoff doc

Copy this file into:

```text
docs/CHESS_ENGINE_AI_CLEANUP_TODO.md
```

Copy the companion spec into:

```text
docs/CHESS_ENGINE_AI_CLEANUP_SPEC.md
```

---

## Task 1: Make the default test suite fast

### 1.1 Identify expensive tests

Use:

```bash
python -m pytest tests -q -m "not slow" --durations=50
```

If the full command times out, run candidate files individually:

```bash
python -m pytest tests/test_ai_search.py -q --durations=25
python -m pytest tests/test_ai_endgame1_regressions.py -q --durations=25
python -m pytest tests/test_strategy*.py -q --durations=25
python -m pytest tests/test_*ai*.py -q --durations=25
```

Find non-slow tests that do any of the following:

- depth 4 or depth 5 search,
- complex strategic transcript positions,
- self-play loops,
- expensive exact-move search assertions,
- long minimax/alpha-beta runs.

### 1.2 Mark expensive tests as slow

For expensive tests, add:

```python
import pytest

@pytest.mark.slow
def test_expensive_search_case(...):
    ...
```

or apply a module/class-level marker if the whole file is benchmark-like:

```python
pytestmark = pytest.mark.slow
```

### 1.3 Keep fast correctness tests in the default suite

Do **not** mark all AI tests slow. Keep fast tests for:

- mate-in-one at depth 1,
- terminal handling,
- depth validation,
- TT lookup/storage behavior at shallow depth,
- move ordering helper behavior,
- promotion identity in move ordering,
- alpha-beta vs no-prune at shallow depth.

### 1.4 Verify non-slow suite

Run:

```bash
python -m pytest tests -q -m "not slow" --durations=25
```

Acceptance: it completes in a practical amount of time and reports all passing tests.

---

## Task 2: Remove or expose the hidden depth-5 starting-position shortcut

### 2.1 Locate the shortcut

Search:

```bash
grep -R "_is_initial_position\|_preferred_starting_move\|depth >= 5" -n chess_game tests
```

Known problematic pattern:

```python
if depth >= 5 and _is_initial_position(board):
    return _preferred_starting_move(legal_moves)
```

### 2.2 Preferred fix: remove the shortcut from `get_best_move`

Remove the hidden bypass from `get_best_move()`.

After this change:

```python
get_best_move(Board(), depth=5)
```

must either:

- actually search depth 5, or
- be covered only by slow/manual tests because it is expensive.

### 2.3 Alternative acceptable fix: make opening-book behavior explicit

If you keep the shortcut, it must be explicit and disabled by default:

```python
def get_best_move(board: Board, depth: int, *, use_opening_book: bool = False) -> LegalMove | None:
    ...
```

Only when `use_opening_book=True` may the engine use `_preferred_starting_move(...)`.

Do **not** leave hidden default behavior.

### 2.4 Update tests

If any test expects depth-5 starting search to return instantly, change it.

Tests must not claim real depth-5 search happened if the opening shortcut bypassed search.

---

## Task 3: Fix the broken depth-5 node-count test

### 3.1 Locate node-count tests

Search:

```bash
grep -R "nodes = \[0\]\|node_count\|SearchStats\|depth_5_nodes" -n tests chess_game
```

Known broken pattern:

```python
nodes = [0]
params = make_params_with_nodes(depth=5, is_maximizing=True)
minimax(board, params)
assert nodes[0] < 500_000
```

This is invalid if `nodes` is not the counter used by the search.

### 3.2 Use `SearchStats`

Prefer:

```python
stats = SearchStats()
context = SearchContext(stats=stats, ...)
params = MinimaxParams(..., context=context)
minimax(board, params)
assert stats.nodes < SOME_LIMIT
```

Use the repo's actual context/stats construction helpers.

### 3.3 Mark depth-5 node tests slow

Any real depth-5 node-count test should be marked:

```python
@pytest.mark.slow
```

Do not include real depth-5 search in the default fast suite.

### 3.4 Avoid fake assertions

Delete or rewrite any assertion that always passes because it checks an unconnected counter.

---

## Task 4: Fix TT root score/move mismatch

### 4.1 Inspect root tie-break logic

Search in `chess_game/chess/ai.py`:

```bash
grep -n "_prefer_root_move\|selected_score\|best_score\|_store_tt_cache" chess_game/chess/ai.py
```

Look for logic where:

- `best_score` tracks the highest/lowest minimax score,
- root tie-breaks select a different near-equal move,
- TT stores `best_score` with the tie-break-selected move.

### 4.2 Separate search best move from returned root-selected move

In the search loop, track separate values:

```python
search_best_score: int
search_best_move: LegalMove | None

root_selected_score: int
root_selected_move: LegalMove | None
```

or equivalent names.

Rules:

- `search_best_score` and `search_best_move` must correspond to the same searched child.
- `root_selected_move` may differ only due to root tie-break policy.
- TT stores `search_best_score` and `search_best_move`.
- `get_best_move()` returns `root_selected_move` when root tie-breaks apply.

### 4.3 Store TT entries consistently

Ensure `_store_tt_cache(...)` receives the move that produced the stored score.

If the code stores only once per searched node, keep that. Do not reintroduce duplicate TT stores.

### 4.4 Add a regression test if practical

Construct or mock a small position/helper case where root tie-break selection can choose a near-equal move.

Test the invariant directly if easier:

- TT entry best move corresponds to the stored score source.
- Root-selected move can differ without corrupting TT.

Do not write a brittle exact-move strategic test if a cleaner unit test is possible.

---

## Task 5: Clean up misleading alpha-beta pruning tests

### 5.1 Find misleading tests

Search:

```bash
grep -R "tight.*wide\|wide.*tight\|without_pruning\|no_prune\|alpha_beta" -n tests
```

Known issue:

A test comparing tight-window alpha-beta vs wide-window alpha-beta is not a valid "with pruning vs without pruning" test.

### 5.2 Remove or rename misleading tests

If a test compares:

```text
wide alpha-beta window
vs.
tight alpha-beta window
```

then either:

- rename it to describe aspiration/window behavior accurately, or
- remove it if it no longer provides value.

Do not call it "without pruning."

### 5.3 Keep true no-prune comparison

Keep or add a shallow test comparing:

```text
plain minimax node count
vs.
alpha-beta node count
```

This test should use a small position and shallow depth, usually depth 2.

Acceptance:

```text
alpha_beta_nodes < no_prune_nodes
```

Do not use depth 5 for this test.

---

## Task 6: Keep AI architecture from expanding in this patch

### 6.1 Do not add heuristic modules

Do not add new modules such as:

```text
new_strategy_guidance.py
new_endgame_guidance.py
new_opening_heuristic.py
```

### 6.2 Do not tune evaluation

Do not change:

- material values,
- piece-square tables,
- pawn-structure scores,
- king-safety scores,
- passed-pawn scores,
- mobility scores.

### 6.3 Avoid brittle exact-move strategic tests

Do not add new tests that force a single exact strategic move unless the position has a clear tactical/chess-rule reason.

Prefer tests that assert properties:

```text
move is legal
move does not blunder mate
move preserves material
move finds checkmate
move count is lower with alpha-beta than no-prune
```

---

## Task 7: Remove generated/cache files

### 7.1 Remove generated files

Run:

```bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### 7.2 Verify `.gitignore`

Ensure `.gitignore` includes:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
```

### 7.3 Verify cleanup

Run:

```bash
find . \( -type d -name "__pycache__" -o -type d -name ".pytest_cache" -o -type f -name "*.pyc" \) -print
```

Expected: no output.

---

## Task 8: Fix small test helper issues

### 8.1 Fix or delete backwards `index_to_str`

Search:

```bash
grep -R "def index_to_str" -n tests
```

If present and returning rank before file, fix it:

```python
def index_to_str(square):
    file_char = chr(ord("a") + int(square.col))
    rank = 8 - int(square.row)
    return f"{file_char}{rank}"
```

Or replace it with the existing engine helper:

```python
from chess_game.chess.coords import index_to_algebraic
```

### 8.2 Prefer existing coordinate helpers

Use:

```python
sq("e4")
index_to_algebraic(square)
```

instead of ad-hoc coordinate conversions.

---

## Task 9: Update `memory.md` only if useful

### 9.1 Do not paste long narratives

If updating `memory.md`, keep it short.

Recommended current-state note:

```text
Current AI cleanup state:
- Default rules tests are stable.
- AI/search cleanup focuses on slow tests, hidden depth-5 opening shortcut, node-count test correctness, TT root score/move consistency, and misleading pruning tests.
- Do not add new heuristics/evaluation tuning in this pass.
```

### 9.2 Mark stale old notes

If old memory entries are misleading, add a short top note:

```text
Older entries below are historical and may describe resolved bugs.
```

Do not spend time rewriting the whole file.

---

## Task 10: Verification

### 10.1 Fast default suite

Run:

```bash
python -m pytest tests -q -m "not slow" --durations=25
```

Required:

- passes,
- completes in a practical amount of time,
- slowest tests are reasonable for default CI.

### 10.2 Rules subset

Run:

```bash
python -m pytest tests/test_board_api.py tests/test_piece_moves.py tests/test_castling.py tests/test_en_passant.py tests/test_promotion.py tests/test_promotion_validation.py tests/test_promotion_move_generation.py tests/test_check_checkmate_stalemate.py tests/test_legal_moves.py -q
```

Required: pass.

### 10.3 AI targeted tests

Run:

```bash
python -m pytest tests/test_alpha_beta_pruning.py -q
python -m pytest tests/test_ai_quality.py -q
```

Required: pass.

If `test_ai_quality.py` remains slow but acceptable, document its runtime. If it is too slow for default CI, mark expensive tests inside it as slow.

### 10.4 Slow tests

Run manually when desired:

```bash
python -m pytest tests -q -m "slow" --durations=25
```

These may be expensive. They should not block normal fast iteration unless project policy requires full slow-suite validation.

### 10.5 Final generated-file check

Run:

```bash
find . \( -type d -name "__pycache__" -o -type d -name ".pytest_cache" -o -type f -name "*.pyc" \) -print
```

Required: no output.

---

## Acceptance checklist

The patch is complete only when:

- [ ] `python -m pytest tests -q -m "not slow"` completes and passes.
- [ ] Expensive AI/search/strategy tests are marked `slow`.
- [ ] Hidden depth-5 starting-position shortcut is removed or made explicit and disabled by default.
- [ ] Depth-5 node-count test uses the real search counter or is removed/marked slow.
- [ ] TT stores a best move that corresponds to the stored score.
- [ ] Misleading alpha-beta tests are removed or renamed.
- [ ] A true no-prune vs alpha-beta test remains.
- [ ] No new heuristics or evaluation tuning were added.
- [ ] Generated/cache files are removed from the repo tree.
- [ ] `.gitignore` protects against generated files returning.
