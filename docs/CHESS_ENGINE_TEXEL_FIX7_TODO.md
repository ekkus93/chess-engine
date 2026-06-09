# CHESS_ENGINE_TEXEL_FIX7_TODO.md

## Implementation checklist

This TODO is for the Fix 7 final test-reliability patch.

Keep this patch narrow. Do **not** implement make/unmake search, bitboards, true Zobrist hashing, NNUE, broad search rewrites, or new chess heuristics.

---

# Phase 0: Baseline validation

## 0.1 Run static checks

- [ ] `uv run --extra dev python -m ruff check chess_game tests`
- [ ] `uv run --extra dev python -m mypy chess_game`
- [ ] `uv run --extra dev python -m pylint chess_game/texel --score=y`

## 0.2 Run full fast suite

- [ ] `uv run --extra dev python -m pytest -m "not slow" -vv`
- [ ] Record whether it completes.
- [ ] If it times out, record the last visible test and approximate elapsed time.

## 0.3 Confirm chunk behavior

If the full suite times out:

- [ ] Run collection:
  - [ ] `uv run --extra dev python -m pytest --collect-only -q -m "not slow"`
- [ ] Split the collected tests into chunks if needed.
- [ ] Confirm whether chunks pass while full suite times out.
- [ ] Record any suspected interaction pair/group.

---

# Phase 1: Fix full-suite reliability

## 1.1 Keep runtime-marker meta-tests isolated

- [ ] Confirm `tests/test_test_runtime_markers_integration.py` has:
  - [ ] `pytestmark = pytest.mark.slow`
- [ ] Confirm it does not run under:
  - [ ] `uv run --extra dev python -m pytest -m "not slow"`
- [ ] Confirm it passes under:
  - [ ] `uv run --extra dev python -m pytest tests/test_test_runtime_markers_integration.py -m slow -q`

## 1.2 Investigate signal/alarm leakage

Search:

```bash
grep -R "signal.alarm\\|signal.signal" tests
```

For each relevant test:

- [ ] Store previous signal handler.
- [ ] Restore previous signal handler in `finally` or fixture teardown.
- [ ] Call `signal.alarm(0)` in cleanup.
- [ ] Avoid leaving active alarms after a test.

## 1.3 Investigate global RNG leakage

Search:

```bash
grep -R "random.seed" chess_game tests
```

For relevant production/test paths:

- [ ] Prefer local `random.Random(seed)` where low-risk.
- [ ] If global RNG must be used, restore state in tests:
  - [ ] `state = random.getstate()`
  - [ ] `try: ... finally: random.setstate(state)`
- [ ] Pay special attention to opening-book seed tests and self-play tests.

## 1.4 Investigate subprocess/background leaks

Search for:

```bash
grep -R "subprocess\\|Popen\\|Thread\\|asyncio\\|Textual" tests chess_game
```

For relevant tests:

- [ ] Ensure subprocesses are waited for or killed.
- [ ] Ensure pipes are consumed or closed.
- [ ] Ensure background threads/tasks are stopped.
- [ ] Ensure TUI/event-loop tests clean up.

## 1.5 Investigate monkeypatch/mock leakage

Search for manual patches:

```bash
grep -R "\\.start()" tests
grep -R "mock.patch" tests
```

- [ ] Prefer `monkeypatch` or context-managed `mock.patch`.
- [ ] Ensure started patches are stopped.
- [ ] Ensure module globals are restored.

## 1.6 Validate full fast suite

- [ ] Run:
  - [ ] `uv run --extra dev python -m pytest -m "not slow"`
- [ ] Confirm it completes reliably as one command.

---

# Phase 2: Rewrite collection tests to prove behavior

## 2.1 Remove or rename config-only behavior tests

In `tests/test_collect.py`:

- [ ] Find behavior-named tests that only assert config fields.
- [ ] Rewrite them to behavior tests, or rename them as config tests.
- [ ] Specifically check for:
  - [ ] `assert opts.max_move_result == "draw"`
  - [ ] `assert opts.max_move_result == "discard"`
  - [ ] `assert opts.weights is custom_weights`
  - [ ] `assert opts.seed == ...`

## 2.2 Weights propagation through actual path

- [ ] Monkeypatch `chess_game.texel.collect.get_best_move`.
- [ ] Call `_play_game()` or `collect_games()`, whichever actually invokes `get_best_move`.
- [ ] Capture `BestMoveOptions`.
- [ ] Configure custom weights through `CollectionOptions(weights=custom_weights)`.
- [ ] Assert captured options use the same weights:
  - [ ] `captured_options.weights is custom_weights`

## 2.3 Max-move draw behavior

- [ ] Use controlled legal move sequence or monkeypatched move generation.
- [ ] Set `max_moves` low enough to hit the limit.
- [ ] Configure `max_move_result="draw"`.
- [ ] Assert:
  - [ ] returned/stored outcome is `0.5`;
  - [ ] expected positions are recorded.

## 2.4 Max-move discard behavior

- [ ] Use controlled play that hits max move limit.
- [ ] Configure `max_move_result="discard"`.
- [ ] Assert:
  - [ ] `_play_game()` returns `None`, or
  - [ ] `collect_games()` stores no positions, depending on current API.

## 2.5 Terminal draw outcome

- [ ] Test terminal draw handling through collection path.
- [ ] If testing `GameRecord(outcome=0.5)` persistence only, name the test accordingly.
- [ ] Assert draw outcome `0.5` is stored.

## 2.6 Seed reproducibility

- [ ] Use controlled mocked behavior.
- [ ] Same `CollectionOptions(seed=...)` produces identical recorded output.
- [ ] Do not rely on real self-play randomness.

## 2.7 Slow real self-play

- [ ] Ensure real self-play collection tests remain marked slow.

---

# Phase 3: Strengthen PositionDB tests

## 3.1 Duplicate aggregation direct stats

- [ ] Add same FEN with outcomes:
  - [ ] `1.0`
  - [ ] `0.5`
  - [ ] `0.0`
- [ ] Assert via `get_stats()`:
  - [ ] `stats is not None`
  - [ ] `stats.count == 3`
  - [ ] `stats.total == pytest.approx(1.5)`
  - [ ] `stats.mean == pytest.approx(0.5)`

## 3.2 Old JSONL duplicate aggregation direct stats

- [ ] Create hand-authored old-format JSONL with `tmp_path`:
  - [ ] `{"pos": "fen", "outcome": 1.0}`
  - [ ] `{"pos": "fen", "outcome": 0.5}`
  - [ ] `{"pos": "fen", "outcome": 0.0}`
- [ ] Load with `PositionDB.load(path)`.
- [ ] Assert via `get_stats()`:
  - [ ] `stats is not None`
  - [ ] `stats.count == 3`
  - [ ] `stats.total == pytest.approx(1.5)`
  - [ ] `stats.mean == pytest.approx(0.5)`

## 3.3 New JSONL direct load

- [ ] Create hand-authored new-format JSONL with `tmp_path`:
  - [ ] `{"pos": "fen", "total": 3.0, "count": 4}`
- [ ] Load with `PositionDB.load(path)`.
- [ ] Assert via `get_stats()`:
  - [ ] `stats is not None`
  - [ ] `stats.count == 4`
  - [ ] `stats.total == pytest.approx(3.0)`
  - [ ] `stats.mean == pytest.approx(0.75)`

## 3.4 Round-trip preservation

- [ ] Keep round-trip test.
- [ ] Assert exact `count`, `total`, and `mean`.

## 3.5 Empty DB

- [ ] Keep empty DB test.

---

# Phase 4: Strengthen Texel loss k tests

## 4.1 Remove non-proving tests

In `tests/test_loss.py`:

- [ ] Remove/replace `k` tests that only assert MSE is non-negative.
- [ ] Remove any vacuous `k` assertion.

## 4.2 Non-default k changes MSE

- [ ] Use nonzero-eval FEN:
  - [ ] `4k3/8/8/8/8/8/8/4KQ2 w - - 0 1`
- [ ] Pair with draw outcome:
  - [ ] `pairs = [(fen_white_up_queen, 0.5)]`
- [ ] Compute:
  - [ ] `mse_default = mean_squared_error(pairs, weights, k=DEFAULT_K)`
  - [ ] `mse_other = mean_squared_error(pairs, weights, k=DEFAULT_K * 2)`
- [ ] Assert:
  - [ ] `mse_default != pytest.approx(mse_other)`

## 4.3 k= compatibility

- [ ] Compute both:
  - [ ] `mean_squared_error(pairs, weights, k=1.5)`
  - [ ] `mean_squared_error(pairs, weights, opts=LossOptions(k=1.5))`
- [ ] Assert they match:
  - [ ] `mse_k_kwarg == pytest.approx(mse_opts)`

## 4.4 Preserve perspective tests

- [ ] White material advantage positive.
- [ ] Black material advantage negative.
- [ ] Side-to-move does not flip White-relative sign.

---

# Phase 5: Fix opening-book seed tests

## 5.1 Remove vacuous assertions

In `tests/test_opening_book.py`:

- [ ] Remove:
  - [ ] `assert True`
  - [ ] `"Seed mechanism is working"`
  - [ ] branches that pass without proving seed behavior.

## 5.2 Controlled fake book/path

- [ ] Monkeypatch the opening-book path used by `get_best_move()`.
- [ ] Provide multiple legal candidate moves.
- [ ] Do not rely on real bundled book diversity.

## 5.3 Same-seed behavior

- [ ] Assert same seed returns same move.

## 5.4 Different-seed behavior

- [ ] Choose seeds known to select different moves.
- [ ] Assert:
  - [ ] `move_seed_a != move_seed_b`

## 5.5 Global RNG containment

- [ ] Ensure tests restore global RNG state if global RNG is used.
- [ ] Prefer local RNG in production if this is a small localized fix.
- [ ] Confirm opening-book seeded tests do not cause full-suite state leakage.

---

# Phase 6: Dev-extra docs and perft honesty

## 6.1 Dev-extra docs

- [ ] Keep README/current docs showing:
  - [ ] `uv sync --extra dev`, or
  - [ ] `uv run --extra dev python -m ...`
- [ ] Do not worry about every historical TODO/spec file.

## 6.2 Perft honesty

- [ ] Preserve exact start-position perft counts.
- [ ] Ensure special move-generation/perft-like tests that only check legal moves or `> 0` are labeled smoke tests.
- [ ] Keep exact special perft as documented future work.

---

# Phase 7: Final validation

## 7.1 Static checks

Run:

- [ ] `uv run --extra dev python -m ruff check chess_game tests`
- [ ] `uv run --extra dev python -m mypy chess_game`
- [ ] `uv run --extra dev python -m pylint chess_game/texel --score=y`

## 7.2 Full fast suite

Run:

- [ ] `uv run --extra dev python -m pytest -m "not slow"`

This must complete as one command.

## 7.3 Targeted tests

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

## 7.4 Slow tests

Run:

- [ ] `uv run --extra dev python -m pytest -m slow`

If too slow:

- [ ] Document runtime limitation.
- [ ] Confirm slow tests are isolated from fast tests.

---

# Phase 8: Completion criteria

This patch is complete only when:

- [ ] Ruff passes with dev dependencies.
- [ ] mypy passes with dev dependencies.
- [ ] Texel Pylint passes or remains acceptably high.
- [ ] Full fast suite completes reliably as one command.
- [ ] Runtime-marker meta-tests remain isolated from the fast suite.
- [ ] Any full-suite state leak is fixed or contained.
- [ ] Collection tests prove weights propagation through actual collection path.
- [ ] Collection tests prove max-move `"draw"` stores `0.5`.
- [ ] Collection tests prove max-move `"discard"` stores no positions.
- [ ] Collection tests prove seed reproducibility.
- [ ] PositionDB old JSONL duplicate aggregation directly checks `count`, `total`, and `mean`.
- [ ] PositionDB new JSONL direct load uses hand-authored JSONL and directly checks stats.
- [ ] Texel loss non-default `k` behavior is directly tested.
- [ ] Texel loss `k=` compatibility is directly tested.
- [ ] Opening-book seed tests contain no vacuous `assert True`.
- [ ] Opening-book different-seed behavior is non-vacuously tested.
- [ ] Dev-extra validation docs remain current.
- [ ] Special perft smoke tests remain honestly labeled.
- [ ] Targeted tests pass.
- [ ] Slow tests are isolated from fast tests.

---

# Notes for Claude Code

## Fix full-suite reliability first

Do not stop at chunked passing runs. The one-command fast suite must pass.

## Keep this narrow

No engine architecture work.

## Watch global state

Global RNG, signal handlers, subprocesses, and background tasks are the likely full-suite interaction points.

## Avoid test theater

Behavior tests must exercise the behavior they claim to test.

## Preserve compatibility

Do not break PositionDB JSONL, CLI usage, or public Texel APIs.
