# CHESS_ENGINE_FIX8_FAST_SUITE_RUNTIME_TODO.md

## Implementation checklist

This TODO is for the Fix 8 fast-suite runtime cleanup patch.

Keep this patch narrow. Do **not** implement make/unmake search, bitboards, true Zobrist hashing, NNUE, broad search rewrites, new chess heuristics, or broad UI redesign.

---

# Phase 0: Baseline validation and timing

## 0.1 Run static checks

- [ ] `uv run --extra dev python -m ruff check chess_game tests`
- [ ] `uv run --extra dev python -m mypy chess_game`
- [ ] `uv run --extra dev python -m pylint chess_game/texel --score=y`

## 0.2 Run full fast suite

- [ ] `uv run --extra dev python -m pytest -m "not slow" -q`
- [ ] Record:
  - [ ] pass/fail,
  - [ ] number of passed tests,
  - [ ] number of deselected tests,
  - [ ] wall-clock runtime.

## 0.3 Run runtime diagnostics

- [ ] `uv run --extra dev python -m pytest -m "not slow" --durations=50`
- [ ] Save the slowest-test list.
- [ ] Identify any non-slow test over 2 seconds.
- [ ] Identify any non-slow test over 3 seconds.

## 0.4 Run focused TUI timing

- [ ] `uv run --extra dev python -m pytest tests/test_tui.py -m "not slow" -q --durations=20`
- [ ] Record slowest TUI tests.
- [ ] Search for long sleeps:
  - [ ] `grep -R "pause(delay=3\\|pause(delay=2\\|sleep(3\\|sleep(2" tests/test_tui.py tests`

---

# Phase 1: Remove real engine waits from fast TUI tests

## 1.1 Inspect TUI engine call path

- [ ] Find where `tests/test_tui.py` triggers an engine reply.
- [ ] Identify whether `chess_game.tui.get_best_move` or another imported symbol should be monkeypatched.
- [ ] Identify the expected return type:
  - [ ] UCI string,
  - [ ] `LegalMove`,
  - [ ] internal move object,
  - [ ] other.

## 1.2 Add deterministic fake engine reply

- [ ] Add helper/fake in `tests/test_tui.py`, for example:
  - [ ] fake black reply after `e2e4`,
  - [ ] fake reply returns immediately,
  - [ ] fake uses a legal move format accepted by the TUI.
- [ ] Monkeypatch the TUI engine call path:
  - [ ] `monkeypatch.setattr("chess_game.tui.get_best_move", fake_get_best_move)`
  - [ ] or the correct symbol used by the current implementation.

## 1.3 Replace arbitrary 3-second waits

For each fast TUI test that uses a long wait:

- [ ] Replace `await pilot.pause(delay=3.0)` with a short wait or state wait.
- [ ] Prefer waiting for expected state:
  - [ ] move list has expected length,
  - [ ] input is cleared,
  - [ ] board piece is at expected square,
  - [ ] engine reply has been applied.
- [ ] If no wait helper exists, add a small local polling helper.

Example helper shape:

```python
async def wait_until(predicate, *, timeout: float = 0.5, interval: float = 0.01) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        await asyncio.sleep(interval)
    raise AssertionError("condition was not met before timeout")
```

Use existing project/test idioms if available.

## 1.4 Mark real-engine TUI tests slow

If a TUI test intentionally verifies real engine integration:

- [ ] Mark it `@pytest.mark.slow`.
- [ ] Add a fast replacement that verifies UI behavior with fake engine reply.
- [ ] Keep test names honest.

---

# Phase 2: Confirm runtime-marker meta-tests stay out of fast suite

## 2.1 Check marker file

- [ ] Confirm `tests/test_test_runtime_markers_integration.py` has:
  - [ ] `pytestmark = pytest.mark.slow`

## 2.2 Validate slow-marker behavior

- [ ] Run:
  - [ ] `uv run --extra dev python -m pytest tests/test_test_runtime_markers_integration.py -m slow -q`
- [ ] Confirm it passes.

## 2.3 Confirm full fast exclusion

- [ ] Run:
  - [ ] `uv run --extra dev python -m pytest -m "not slow" --collect-only -q`
- [ ] Confirm marker meta-tests are not selected.

---

# Phase 3: Preserve Fix 7 behavior-test improvements

## 3.1 Collection tests

In `tests/test_collect.py`:

- [ ] Confirm behavior tests still exercise production paths.
- [ ] Confirm weights propagation is tested through actual collection path.
- [ ] Confirm max-move `"draw"` stores or returns outcome `0.5`.
- [ ] Confirm max-move `"discard"` returns `None` or stores no positions.
- [ ] Confirm seed reproducibility uses controlled behavior.
- [ ] Confirm pure config tests are named as config tests, not behavior tests.

## 3.2 PositionDB tests

In `tests/test_position_db.py`:

- [ ] Confirm old JSONL duplicate aggregation uses hand-authored JSONL.
- [ ] Confirm old JSONL duplicate aggregation asserts:
  - [ ] `stats.count == 3`
  - [ ] `stats.total == pytest.approx(1.5)`
  - [ ] `stats.mean == pytest.approx(0.5)`
- [ ] Confirm new JSONL direct load uses hand-authored JSONL:
  - [ ] `{"pos": "fen", "total": 3.0, "count": 4}`
- [ ] Confirm new JSONL direct load asserts:
  - [ ] `stats.count == 4`
  - [ ] `stats.total == pytest.approx(3.0)`
  - [ ] `stats.mean == pytest.approx(0.75)`

## 3.3 Loss k tests

In `tests/test_loss.py`:

- [ ] Confirm non-default `k` changes MSE using nonzero-eval FEN.
- [ ] Confirm `k=` and `opts=LossOptions(k=...)` are both called.
- [ ] Confirm the two APIs produce matching MSE.
- [ ] Confirm no `k` test only asserts non-negative MSE.

## 3.4 Opening-book seed tests

In `tests/test_opening_book.py`:

- [ ] Confirm no executable `assert True` remains.
- [ ] Confirm same-seed behavior is tested.
- [ ] Confirm different-seed behavior is tested with a controlled fake/multiple candidate setup.
- [ ] Confirm global RNG is not mutated by seeded book selection.

---

# Phase 4: Fast-suite slow-marker policy cleanup

## 4.1 Identify slow non-slow tests

From `--durations=50`:

- [ ] List every non-slow test over 2 seconds.
- [ ] For each, decide:
  - [ ] rewrite,
  - [ ] mark slow,
  - [ ] justify as acceptable.

## 4.2 Rewrite preferred cases

Prefer rewriting if the test:

- [ ] waits for real engine work but only verifies UI state,
- [ ] sleeps for fixed wall-clock time,
- [ ] uses real self-play where a fake would work,
- [ ] uses broad integration behavior for a unit assertion.

## 4.3 Slow-mark appropriate cases

Mark slow if the test genuinely verifies:

- [ ] real engine integration,
- [ ] real self-play,
- [ ] broad TUI integration,
- [ ] runtime marker infrastructure,
- [ ] depth-heavy search behavior.

---

# Phase 5: Dev-extra docs

## 5.1 README/current docs

- [ ] Confirm README/current docs mention:
  - [ ] `uv sync --extra dev`
  - [ ] or `uv run --extra dev python -m ...`

## 5.2 Avoid historical cleanup churn

- [ ] Do not edit old TODO/spec files just because they contain old commands.
- [ ] Only update current docs if stale.

---

# Phase 6: Final validation

## 6.1 Static checks

- [ ] `uv run --extra dev python -m ruff check chess_game tests`
- [ ] `uv run --extra dev python -m mypy chess_game`
- [ ] `uv run --extra dev python -m pylint chess_game/texel --score=y`

## 6.2 Full fast suite

- [ ] `uv run --extra dev python -m pytest -m "not slow"`
- [ ] Record:
  - [ ] passed count,
  - [ ] deselected count,
  - [ ] runtime.

## 6.3 Runtime diagnostics

- [ ] `uv run --extra dev python -m pytest -m "not slow" --durations=50`
- [ ] Record slowest non-slow tests.
- [ ] Confirm no avoidable multi-second TUI waits remain.

## 6.4 Targeted tests

Run:

```bash
uv run --extra dev python -m pytest \
  tests/test_tui.py \
  tests/test_self_play_runtime.py \
  tests/test_self_play_runtime_integration.py \
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

## 6.5 Slow tests

- [ ] `uv run --extra dev python -m pytest -m slow`
- [ ] If too slow, document limitation.
- [ ] Confirm slow tests remain isolated from fast tests.

---

# Phase 7: Completion criteria

This patch is complete only when:

- [ ] Ruff passes with dev dependencies.
- [ ] mypy passes with dev dependencies.
- [ ] Texel Pylint passes or remains acceptably high.
- [ ] Full fast suite completes reliably as one command.
- [ ] Full fast suite runtime is reduced or justified.
- [ ] No non-slow TUI test waits several seconds for real engine reply.
- [ ] Real-engine TUI tests are slow-marked or replaced with deterministic fast tests.
- [ ] `tests/test_tui.py -m "not slow" --durations=20` has no avoidable 3-second waits.
- [ ] Runtime-marker meta-tests remain isolated from the fast suite.
- [ ] Fix 7 behavior tests remain intact.
- [ ] Dev-extra validation docs remain current.
- [ ] Targeted tests pass.
- [ ] Slow tests are isolated from fast tests.
- [ ] Any slow-suite runtime limitation is documented honestly.

---

# Notes for Claude Code

## Primary goal

Make the fast suite fast enough, not just technically green on one machine.

## Highest-value target

Remove real engine waits from fast TUI tests.

## Do not add sleeps

Prefer state polling and deterministic fakes.

## Keep the patch narrow

No chess feature work.

## Preserve prior hardening

Do not regress collection, PositionDB, loss, or opening-book behavior tests.
