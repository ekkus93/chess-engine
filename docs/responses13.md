# FIX8 (Fast-Suite Runtime) — Questions and Issues

## Overview

I have read both CHESS_ENGINE_FIX8_FAST_SUITE_RUNTIME_SPEC.md and
CHESS_ENGINE_FIX8_FAST_SUITE_RUNTIME_TODO.md. This is a narrow fast-suite
runtime patch: make the "fast" suite genuinely fast by removing real engine
waits from fast TUI tests. No chess-engine feature work.

Before raising questions I did read-only verification (grep + a durations run).
The diagnosis in the spec holds up precisely.

---

## Verification of the FIX8 diagnosis (read-only)

### The three 3-second waits are the entire problem

`grep` across all of `tests/` for multi-second waits finds exactly three, all in
`tests/test_tui.py`:

```
tests/test_tui.py:206:  await pilot.pause(delay=3.0)
tests/test_tui.py:234:  await pilot.pause(delay=3.0)
tests/test_tui.py:248:  await pilot.pause(delay=3.0)
```

No other test in the suite sleeps >= 2s.

### Local timing confirms it

`uv run --extra dev python -m pytest tests/test_tui.py -m "not slow" --durations=10`:

```
3.79s test_human_move_pawn_lands_on_e4
3.62s test_move_list_shows_both_sides_after_engine_reply
3.58s test_input_cleared_after_valid_move
(next slowest ~0.69s)
31 passed in 18.19s
```

Each of the three costs ~3.6-3.8s — MORE than the fixed 3.0s delay, because the
real depth-1 engine runs in the `@work(thread=True)` worker on top of the wait.
~11s of test_tui.py's 18s is these three tests. This is a fixed wall-clock cost
on every machine, which is exactly why a constrained sandbox exceeds its
external timeout (consistent with the Problem 1 / H1 analysis in memory.md).

### The fix pattern already exists in the repo

`tests/test_self_play_runtime.py` and `tests/test_self_play_runtime_integration.py`
already monkeypatch the engine:

```python
monkeypatch.setattr(self_play, "get_best_move", fake_get_best_move)
```

The TUI path is analogous: `chess_game/tui.py` imports `get_best_move` at module
level (line 33) and calls it inside a `@work(thread=True)` worker `_run_engine`
(line 558) that posts `EngineMoveMessage`, handled by `_on_engine_move`. So the
monkeypatch target is `chess_game.tui.get_best_move`, returning a `LegalMove`.

### Two of the three tests do not need the engine at all

- `test_human_move_pawn_lands_on_e4` asserts a White pawn is on e4.
- `test_input_cleared_after_valid_move` asserts the input field is empty.

Both are true immediately after the human move is submitted, before any engine
reply. The 3s wait is pure waste for these two.

Only `test_move_list_shows_both_sides_after_engine_reply` needs a reply, and it
only asserts `len(_move_strings) >= 2` and `_move_strings[0] == "e2e4"` — so any
*legal* fake reply suffices (it does not check which engine move).

---

## Questions

### 1. Per-test approach

Proposed:

- `test_human_move_pawn_lands_on_e4`: replace `delay=3.0` with a short
  `await pilot.pause()`; keep the human-side assertion. No fake needed.
- `test_input_cleared_after_valid_move`: same — short pause, no fake needed.
- `test_move_list_shows_both_sides_after_engine_reply`: monkeypatch
  `chess_game.tui.get_best_move` to return a legal move instantly, then poll for
  `len(_move_strings) >= 2`.

Result: all three stay **fast**; none slow-marked; UI coverage preserved.

**Question:** Agree with keeping all three fast, or do you also want a
real-engine end-to-end TUI test retained but `@pytest.mark.slow` for integration
coverage?

### 2. Fake reply move

I plan to use a "first legal move" fake (compute `get_legal_moves(board)[0]`),
which guarantees a legal Black reply regardless of position, rather than a
hardcoded `e7e5`.

**Question:** Acceptable? Or do you prefer a fixed, readable `e7e5`-style reply?

### 3. Wait-for-state helper

The TODO suggests a `wait_until(predicate, timeout=...)` helper that polls for
state instead of sleeping. I propose adding a small async helper to
`tests/test_tui.py` for the engine-reply test, and using plain `await
pilot.pause()` for the two human-side tests.

**Question:** Prefer the `wait_until` polling helper (waits for state), or a
fixed short `await pilot.pause(delay=0.05)`? I lean toward `wait_until` for the
engine-reply test per the spec's "wait for state, not wall-clock" guidance.

### 4. Runtime target

Removing ~11s takes the full fast suite from ~44s to ~33s, hitting the spec's
"preferred under 35 seconds" target with this single change. `grep` shows no
other multi-second offenders, so I do not expect further hunting is needed
beyond confirming with `--durations=50`.

**Question:** Confirm that this one change (plus the durations check) is the
expected scope, and you do not want me to chase sub-second optimizations.

### 5. Adjacent observation (not FIX8 scope) — production signal.alarm

`chess_game/self_play.py` uses a real `signal.alarm` timeout, exercised by
`tests/test_self_play_runtime.py::test_get_best_move_with_timeout_returns_none_on_alarm_timeout`.
My FIX7 "no signal usage" finding was specifically about the *test* files; the
production self-play path does use `signal.alarm`. It is fast and out of FIX8
scope, but I am flagging it since signal/alarm came up in the Problem 1
discussion (signal-handler leakage was one of the original suspects).

**Question:** Leave it entirely alone for FIX8 (my default), or do you want a
quick read-only check that the alarm is always disarmed in a `finally` so it
cannot leak across tests?

---

## Assumptions I am making

1. The patch is test-only; no production code changes (the engine/TUI logic is
   correct, only the tests are slow).
2. All three TUI tests can remain fast once the real-engine wait is removed; no
   new slow tests are required.
3. Monkeypatching `chess_game.tui.get_best_move` is reliable across the
   `@work(thread=True)` worker (it resolves the module global at call time, so
   the thread picks up the fake).
4. FIX7 behavior tests (collection, PositionDB, loss k, opening-book) must
   remain intact — I will re-run them to confirm no regression.
5. No breaking changes to public APIs, TUI behavior, or dev-extra docs.

---

## Proposed implementation order (pending your answers)

1. Phase 0: baseline static checks + `--durations=50` to record the starting
   slowest non-slow tests.
2. Phase 1: fix the three TUI tests (short pause for the two human-side tests;
   fake engine + `wait_until` for the engine-reply test).
3. Phase 2: confirm runtime-marker meta-tests still excluded from fast suite.
4. Phase 3: re-verify FIX7 behavior tests intact.
5. Phase 4: re-run `--durations=50`; confirm no non-slow test > 2s remains.
6. Phase 5: confirm dev-extra docs current (no churn).
7. Phase 6: final validation (ruff, mypy, pylint, fast suite, targeted, slow).

No code changed.
