# CHESS_ENGINE_TEXEL_FIX6_TODO.md

## Implementation checklist

This TODO is for the Fix 6 acceptance-hardening patch.

Keep this patch narrow. Do **not** implement make/unmake search, bitboards, true Zobrist hashing, NNUE, broad search rewrites, or new chess heuristics.

---

# Phase 0: Baseline and current blockers

## 0.1 Run validation with dev dependencies

Use either a synced dev environment:

- [ ] `uv sync --extra dev`

Then:

- [ ] `uv run python -m ruff check chess_game tests`
- [ ] `uv run python -m mypy chess_game`
- [ ] `uv run python -m pylint chess_game/texel --score=y`
- [ ] `uv run python -m pytest -m "not slow" -vv`

Or direct dev-extra commands:

- [ ] `uv run --extra dev python -m ruff check chess_game tests`
- [ ] `uv run --extra dev python -m mypy chess_game`
- [ ] `uv run --extra dev python -m pylint chess_game/texel --score=y`
- [ ] `uv run --extra dev python -m pytest -m "not slow" -vv`

## 0.2 Confirm current fast-suite blocker

- [ ] Run the full fast suite.
- [ ] If it times out, run:
  - [ ] `uv run --extra dev python -m pytest -m "not slow" --ignore=tests/test_test_runtime_markers_integration.py -q`
- [ ] Confirm whether `tests/test_test_runtime_markers_integration.py` is the blocker.
- [ ] Record the fast-suite runtime after the marker file is excluded or fixed.

---

# Phase 1: Fix runtime-marker meta-tests

## 1.1 Choose strategy

Choose one:

- [ ] Mark the whole file slow:
  - [ ] add `pytestmark = pytest.mark.slow` to `tests/test_test_runtime_markers_integration.py`
- [ ] Or rewrite the file as static checks:
  - [ ] no broad pytest subprocess calls,
  - [ ] no full-suite collection subprocesses in the fast suite,
  - [ ] no real engine test subprocesses.

Preferred: mark the whole file slow unless the static rewrite is simple.

## 1.2 If marking slow

- [ ] Import `pytest` if needed.
- [ ] Add:
  - [ ] `pytestmark = pytest.mark.slow`
- [ ] Run:
  - [ ] `uv run --extra dev python -m pytest tests/test_test_runtime_markers_integration.py -m "not slow" -q`
- [ ] Confirm tests are deselected quickly.

## 1.3 If rewriting static

- [ ] Replace broad subprocess calls with file/AST checks.
- [ ] Do not call:
  - [ ] `pytest tests/ --co`
  - [ ] `pytest tests/ -m "not slow" --co`
  - [ ] `pytest tests/ -m slow --co`
  inside fast tests.
- [ ] Run:
  - [ ] `uv run --extra dev python -m pytest tests/test_test_runtime_markers_integration.py -m "not slow" -q`
- [ ] Confirm it completes quickly.

## 1.4 Validate full fast suite

- [ ] Run:
  - [ ] `uv run --extra dev python -m pytest -m "not slow"`
- [ ] Confirm it completes reliably.

---

# Phase 2: Update validation command documentation

## 2.1 README

- [ ] Add or update clean-checkout validation setup:
  - [ ] `uv sync --extra dev`
- [ ] Or document direct commands:
  - [ ] `uv run --extra dev python -m ruff check chess_game tests`
  - [ ] `uv run --extra dev python -m mypy chess_game`
  - [ ] `uv run --extra dev python -m pylint chess_game/texel --score=y`
  - [ ] `uv run --extra dev python -m pytest -m "not slow"`

## 2.2 Other docs

Update any relevant docs that list validation commands:

- [ ] `docs/TEXEL_TUNING.md`, if it lists commands.
- [ ] `docs/ENGINE_SEARCH_NOTES.md`, if it lists commands.
- [ ] Any completion report, if one is created.

## 2.3 Avoid stale commands

- [ ] Do not leave clean-checkout instructions that require unavailable dev tools without first installing dev dependencies.

---

# Phase 3: Rewrite collection tests to prove behavior

## 3.1 Remove or rename config-only behavior tests

In `tests/test_collect.py`:

- [ ] Find tests with behavior names that only assert config fields.
- [ ] Rewrite them to behavior tests, or rename them as config tests.
- [ ] Specifically check for tests asserting only:
  - [ ] `opts.max_move_result == "draw"`
  - [ ] `opts.max_move_result == "discard"`
  - [ ] `opts.weights is custom_weights`
  - [ ] `opts.seed == ...`

## 3.2 Weights propagation through collection path

- [ ] Monkeypatch `chess_game.texel.collect.get_best_move`.
- [ ] Call the real collection path that invokes `get_best_move`, such as `_play_game()` or `collect_games()`.
- [ ] Capture the `BestMoveOptions` passed to `get_best_move`.
- [ ] Configure `CollectionOptions(weights=custom_weights)`.
- [ ] Assert:
  - [ ] captured `BestMoveOptions.weights is custom_weights`.

## 3.3 Max-move draw behavior

- [ ] Use controlled/mocked play that reaches the max move limit.
- [ ] Configure:
  - [ ] `max_move_result="draw"`
- [ ] Assert:
  - [ ] returned/stored outcome is `0.5`.
  - [ ] expected positions are recorded.

## 3.4 Max-move discard behavior

- [ ] Use controlled/mocked play that reaches the max move limit.
- [ ] Configure:
  - [ ] `max_move_result="discard"`
- [ ] Assert:
  - [ ] no positions are stored, or
  - [ ] `_play_game()` returns `None`, depending on current API.

## 3.5 Terminal draw outcome

- [ ] Test terminal draw behavior through the collection path.
- [ ] If using `GameRecord(outcome=0.5)` directly, name the test as a persistence test, not terminal draw detection.
- [ ] Assert outcome `0.5` is stored.

## 3.6 Invalid max_move_result

- [ ] Keep/confirm `ValueError` test for invalid `max_move_result`.

## 3.7 Seed reproducibility

- [ ] Use controlled mocked behavior.
- [ ] Same `CollectionOptions(seed=...)` should produce identical recorded DB/output.
- [ ] Do not use real self-play randomness.

## 3.8 Slow real self-play tests

- [ ] Confirm real self-play collection tests are marked:
  - [ ] `@pytest.mark.slow`

---

# Phase 4: Strengthen PositionDB tests

## 4.1 Duplicate aggregation direct stats

- [ ] Use same FEN with outcomes:
  - [ ] `1.0`
  - [ ] `0.5`
  - [ ] `0.0`
- [ ] Use:
  - [ ] `stats = db.get_stats(fen)`
- [ ] Assert:
  - [ ] `stats is not None`
  - [ ] `stats.count == 3`
  - [ ] `stats.total == pytest.approx(1.5)`
  - [ ] `stats.mean == pytest.approx(0.5)`

## 4.2 Old JSONL duplicate aggregation direct stats

- [ ] Create hand-authored old-format JSONL using `tmp_path`:
  - [ ] `{"pos": "fen", "outcome": 1.0}`
  - [ ] `{"pos": "fen", "outcome": 0.5}`
  - [ ] `{"pos": "fen", "outcome": 0.0}`
- [ ] Load:
  - [ ] `db = PositionDB.load(path)`
- [ ] Use:
  - [ ] `stats = db.get_stats(fen)`
- [ ] Assert:
  - [ ] `stats is not None`
  - [ ] `stats.count == 3`
  - [ ] `stats.total == pytest.approx(1.5)`
  - [ ] `stats.mean == pytest.approx(0.5)`

## 4.3 New JSONL direct load

- [ ] Create hand-authored new-format JSONL using `tmp_path`:
  - [ ] `{"pos": "fen", "total": 3.0, "count": 4}`
- [ ] Load:
  - [ ] `db = PositionDB.load(path)`
- [ ] Use:
  - [ ] `stats = db.get_stats(fen)`
- [ ] Assert:
  - [ ] `stats is not None`
  - [ ] `stats.count == 4`
  - [ ] `stats.total == pytest.approx(3.0)`
  - [ ] `stats.mean == pytest.approx(0.75)`

## 4.4 Round trip

- [ ] Keep a save/load round-trip test.
- [ ] Assert exact `count`, `total`, and `mean` after reload.

## 4.5 Empty DB

- [ ] Keep/confirm empty DB behavior tests.

---

# Phase 5: Strengthen Texel loss k tests

## 5.1 Remove non-proving k tests

In `tests/test_loss.py`:

- [ ] Find tests that only assert MSE values are non-negative.
- [ ] Replace them if they are supposed to prove `k` behavior.
- [ ] Remove any vacuous k-related assertion.

## 5.2 Non-default k changes MSE

- [ ] Use nonzero-eval FEN:
  - [ ] `4k3/8/8/8/8/8/8/4KQ2 w - - 0 1`
- [ ] Create:
  - [ ] `pairs = [(fen_white_up_queen, 0.5)]`
- [ ] Compute:
  - [ ] `mse_default = mean_squared_error(pairs, weights, k=DEFAULT_K)`
  - [ ] `mse_other = mean_squared_error(pairs, weights, k=DEFAULT_K * 2)`
- [ ] Assert:
  - [ ] `mse_default != pytest.approx(mse_other)`

## 5.3 k= compatibility

- [ ] Compute:
  - [ ] `mse_k_kwarg = mean_squared_error(pairs, weights, k=1.5)`
  - [ ] `mse_opts = mean_squared_error(pairs, weights, opts=LossOptions(k=1.5))`
- [ ] Assert:
  - [ ] `mse_k_kwarg == pytest.approx(mse_opts)`

## 5.4 Preserve perspective tests

- [ ] White material advantage positive.
- [ ] Black material advantage negative.
- [ ] Side-to-move does not flip White-relative sign.

---

# Phase 6: Fix opening-book seed tests

## 6.1 Remove vacuous assertions

In `tests/test_opening_book.py`:

- [ ] Remove:
  - [ ] `assert True`
  - [ ] `len(moves_found) >= 1`
  - [ ] any branch that passes without proving seed behavior.

## 6.2 Controlled fake/monkeypatched book

- [ ] Monkeypatch the opening-book path used by `get_best_move()`.
- [ ] Provide multiple legal candidate moves.
- [ ] Avoid relying on real book diversity.

## 6.3 Same-seed test

- [ ] Same seed returns same move.

## 6.4 Different-seed test

- [ ] Choose seeds known to produce different candidates.
- [ ] Assert:
  - [ ] `move_seed_a != move_seed_b`

## 6.5 Global RNG independence

- [ ] Keep or add test proving prior global RNG state does not affect seeded result.
- [ ] If implementation is later changed to local RNG, keep this test valid.

## 6.6 Public path

Prefer testing through:

```python
get_best_move(
    board,
    depth=1,
    book_options=BestMoveOptions(
        use_opening_book=True,
        random_opening_book=True,
        rng_seed=seed,
    ),
)
```

- [ ] If a helper is tested instead, confirm it is used by `get_best_move`.

---

# Phase 7: Perft deferral honesty

## 7.1 Preserve exact start-position perft

- [ ] depth 1 = 20.
- [ ] depth 2 = 400.
- [ ] depth 3 = 8902.
- [ ] depth 4 = 197281 marked slow.

## 7.2 Smoke-test names/comments

- [ ] Special tests that only check `>0` or legal moves exist must be labeled smoke tests.
- [ ] Do not call smoke tests exact perft validation.

## 7.3 Deferred exact special perft

- [ ] Ensure comments/docs state exact known-count special perft positions are future work.

---

# Phase 8: Final validation

## 8.1 Static checks

Run:

- [ ] `uv run --extra dev python -m ruff check chess_game tests`
- [ ] `uv run --extra dev python -m mypy chess_game`
- [ ] `uv run --extra dev python -m pylint chess_game/texel --score=y`

## 8.2 Full fast suite

Run:

- [ ] `uv run --extra dev python -m pytest -m "not slow"`

This must complete.

## 8.3 Targeted tests

Run:

```bash
uv run --extra dev python -m pytest \
  tests/test_ai_quiescence_production.py \
  tests/test_search_terminal_scores.py \
  tests/test_perft.py \
  tests/test_loss.py \
  tests/test_spsa.py \
  tests/test_position_db.py \
  tests/test_collect.py \
  tests/test_online_learning.py \
  tests/test_validate.py \
  tests/test_tune.py \
  tests/test_opening_book.py \
  -m "not slow" -q
```

- [ ] Confirm targeted tests pass.

## 8.4 Slow tests

Run:

- [ ] `uv run --extra dev python -m pytest -m slow`

If too slow:

- [ ] Document runtime limitation.
- [ ] Confirm slow tests are isolated from fast tests.

---

# Phase 9: Completion criteria

This patch is complete only when:

- [ ] Ruff passes with dev dependencies.
- [ ] mypy passes with dev dependencies.
- [ ] Texel Pylint passes or remains acceptably high with dev dependencies.
- [ ] `pytest -m "not slow"` completes reliably with dev dependencies.
- [ ] Runtime-marker meta-tests no longer block the fast suite.
- [ ] Validation docs mention `uv sync --extra dev` or use `uv run --extra dev`.
- [ ] Collection tests prove weights propagation through the actual collection path.
- [ ] Collection tests prove max-move `"draw"` stores `0.5`.
- [ ] Collection tests prove max-move `"discard"` stores no positions.
- [ ] Collection tests prove seed reproducibility.
- [ ] PositionDB old JSONL duplicate aggregation directly checks `count`, `total`, and `mean`.
- [ ] PositionDB new JSONL direct load uses hand-authored JSONL and directly checks stats.
- [ ] Texel loss non-default `k` behavior is directly tested.
- [ ] Texel loss `k=` compatibility is directly tested.
- [ ] Opening-book seed tests contain no vacuous `assert True`.
- [ ] Opening-book different-seed behavior is non-vacuously tested.
- [ ] Special perft smoke tests remain honestly labeled.
- [ ] Targeted tests pass.
- [ ] Slow tests are isolated from fast tests.

---

# Notes for Claude Code

## Start with the fast-suite blocker

The latest evidence points at `tests/test_test_runtime_markers_integration.py`.

## Do not broaden the patch

No engine architecture work.

## Use dev-extra-aware commands

The validation tools are dev dependencies.

## Prefer controlled tests

Use monkeypatches/fakes for collection and opening-book seed behavior.

## Avoid test theater

Behavior tests must prove behavior.
