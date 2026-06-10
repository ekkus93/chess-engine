# replies13.md

# Replies to Claude Code on FIX8 Fast-Suite Runtime

Claude Code’s proposed Fix 8 direction is correct. The diagnosis in `responses13(1).md` is solid: the three `await pilot.pause(delay=3.0)` calls in `tests/test_tui.py` are the high-value target, and this should stay a **test-only fast-suite cleanup**.

---

## 1. Per-test approach

I agree with keeping all three tests fast.

Use this plan:

- `test_human_move_pawn_lands_on_e4`: replace the 3-second pause with a short `await pilot.pause()` or a small state wait. No fake engine needed.
- `test_input_cleared_after_valid_move`: same. This is a human-input/UI-state assertion, not an engine-reply assertion.
- `test_move_list_shows_both_sides_after_engine_reply`: monkeypatch `chess_game.tui.get_best_move` to return immediately, then wait/poll until `_move_strings` has both sides.

No new slow real-engine TUI test is required for Fix 8. The purpose of this patch is to make the fast suite fast. If later you want end-to-end TUI/real-engine coverage, add it as a separate slow integration test, but do not block this patch on that.

---

## 2. Fake reply move

Use the “first legal move” fake.

That is better than hardcoding `e7e5`, because it is robust to current board state, move format, and future setup changes:

```python
def fake_get_best_move(board, depth, position_counts=None, book_options=None):
    return get_legal_moves(board)[0]
```

Adjust the signature to match how `chess_game.tui.get_best_move` is called. The important thing is that it returns the same type the TUI expects, probably `LegalMove`.

A hardcoded `e7e5` is more readable, but it is also more brittle. The first-legal-move fake is acceptable and preferred here.

---

## 3. Wait-for-state helper

Use a `wait_until` polling helper for the engine-reply test.

For the two human-side tests, a plain short `await pilot.pause()` is fine if the assertion becomes true immediately after the submitted input is processed.

For the engine-reply test, use state polling. That avoids replacing a 3-second sleep with a smaller but still arbitrary sleep.

Suggested helper:

```python
async def wait_until(predicate, *, timeout: float = 0.5, interval: float = 0.01) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        await asyncio.sleep(interval)
    raise AssertionError("condition was not met before timeout")
```

Then:

```python
await wait_until(lambda: len(screen._move_strings) >= 2)
```

Use existing project idioms if there is already a helper.

---

## 4. Runtime target / scope

Confirmed: this one change plus a `--durations=50` verification is the expected scope.

Do not chase sub-second optimizations. The target is to remove the obvious fixed 9–11 second wall-clock cost and make the fast suite more resilient in constrained environments.

After the patch, run:

```bash
uv run --extra dev python -m pytest tests/test_tui.py -m "not slow" -q --durations=20
uv run --extra dev python -m pytest -m "not slow" --durations=50
```

If no non-slow test is over 2 seconds, stop. If a few tests are slightly over 2 seconds but clearly justified and the full suite is comfortably under the target, document them rather than starting a broad optimization pass.

---

## 5. Production `signal.alarm` in `self_play.py`

Leave it alone for Fix 8.

A quick read-only check is fine:

- confirm alarms are disarmed in `finally`,
- confirm previous signal handlers are restored if the code replaces them,
- confirm tests monkeypatching timeout behavior do not leak state.

But do not refactor production self-play timeout handling in this patch unless you find an actual leak or failing test. The current Fix 8 target is TUI test runtime.

---

## Final guidance

Claude Code’s proposed implementation order is good:

1. Baseline with static checks and `--durations=50`.
2. Fix the three TUI tests.
3. Confirm runtime-marker tests remain excluded from fast suite.
4. Re-run Fix 7 targeted behavior tests.
5. Re-run `--durations=50`.
6. Confirm dev-extra docs current.
7. Final validation.

The patch should remain test-only unless the fake-engine path reveals a tiny import/signature adjustment is needed.
