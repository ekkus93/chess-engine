# CHESS_ENGINE_FIX8_FAST_SUITE_RUNTIME_SPEC.md

## Purpose

This document specifies a narrow **Fix 8 fast-suite runtime cleanup patch** for the chess engine.

The current engine and Texel work is close. The remaining issue is not primarily chess correctness; it is that the fast test suite is still too slow or too environment-sensitive in constrained sandboxes.

Claude Code reported that the full fast suite passes repeatedly on its machine in roughly 44-46 seconds:

```bash
uv run --extra dev python -m pytest -m "not slow"
```

In a more constrained sandbox, the same command can exceed the external tool timeout before completing. This looks less like a true infinite hang and more like a fast-suite budget problem.

The next patch should make the "fast" suite genuinely fast and robust across environments.

---

## Hard scope boundaries

### In scope

- Reduce runtime of non-slow tests.
- Remove real engine waits from fast TUI tests.
- Replace real engine replies in UI tests with deterministic fakes.
- Mark genuinely integration-heavy UI/TUI tests as slow.
- Preserve fast coverage with cheaper unit-style tests.
- Keep runtime-marker meta-tests out of the fast suite.
- Keep dev-extra validation commands documented.
- Run full validation.

### Out of scope

Do **not** implement:

- make/unmake search,
- bitboards,
- true Zobrist hashing,
- NNUE/neural evaluation,
- broad search rewrites,
- new chess heuristics,
- broad TUI redesign,
- broad opening-book refactors,
- broad Texel changes.

This is a fast-suite runtime patch only.

---

# Current diagnosis

The slowest measured non-slow area is the TUI test group:

```bash
uv run --extra dev python -m pytest \
  tests/test_self_play_runtime.py \
  tests/test_self_play_runtime_integration.py \
  tests/test_tui.py \
  -m "not slow" -q --durations=30
```

Observed result in a constrained environment:

```text
45 passed in 17.85s
```

Slowest examples:

```text
3.73s tests/test_tui.py::TestHumanMoveInput::test_human_move_pawn_lands_on_e4
3.61s tests/test_tui.py::TestHumanMoveInput::test_move_list_shows_both_sides_after_engine_reply
3.50s tests/test_tui.py::TestHumanMoveInput::test_input_cleared_after_valid_move
```

These tests wait for engine replies with code like:

```python
await pilot.pause(delay=3.0)
```

That is not appropriate for fast tests. A fast UI test should not wait multiple seconds for a real engine search when the behavior under test is UI state.

---

# Required final outcome

The patch is complete only when these commands pass:

```bash
uv run --extra dev python -m ruff check chess_game tests
uv run --extra dev python -m mypy chess_game
uv run --extra dev python -m pylint chess_game/texel --score=y
uv run --extra dev python -m pytest -m "not slow"
```

Targeted tests must also pass:

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

Slow tests should be run separately:

```bash
uv run --extra dev python -m pytest -m slow
```

If the slow suite is too slow, document the limitation.

---

# Runtime target

The fast suite should complete comfortably in normal development and constrained automation.

## Required target

- Full fast suite:
  - preferred: under 35 seconds on Claude Code's machine,
  - acceptable: under 45 seconds,
  - hard requirement: reliably completes as one command.

## Per-test target

- Non-slow tests should normally be under 1 second.
- Any non-slow test over 2 seconds must be justified, rewritten, or slow-marked.
- Any non-slow test over 3 seconds should almost certainly be rewritten or marked slow.

---

# Problem 1: TUI tests wait for real engine replies

## Current problem

Several fast TUI tests wait around 3 seconds each for a real engine reply.

Examples:

```python
await pilot.pause(delay=3.0)
```

These tests appear to verify UI behavior such as:

- human move entry,
- move list display after engine reply,
- input clearing after valid move.

Those behaviors should not require a real engine search in the fast suite.

## Required fix

Replace real engine work in fast TUI tests with deterministic fakes.

Preferred options:

1. Monkeypatch the TUI module's `get_best_move` call to return a legal engine reply immediately.
2. Monkeypatch the engine-reply task/helper used by the TUI.
3. Directly post or call the same handler that processes an engine move message.
4. Mark the real-engine end-to-end TUI tests as `@pytest.mark.slow` and add cheap fast tests for UI state transitions.

The preferred solution is option 1 if it is simple.

## Example approach

If `chess_game.tui` imports `get_best_move`, monkeypatch that symbol:

```python
def fake_get_best_move(board, depth, position_counts=None, book_options=None):
    return "e7e5"  # or the actual LegalMove object/string expected by the TUI

monkeypatch.setattr("chess_game.tui.get_best_move", fake_get_best_move)
```

Then replace:

```python
await pilot.pause(delay=3.0)
```

with one of:

```python
await pilot.pause(delay=0.05)
```

or a wait helper that polls until the expected UI state is present:

```python
await wait_until(lambda: len(screen._move_strings) == 2)
```

Use whatever is idiomatic for the existing test harness.

## Acceptance criteria

- Fast TUI tests do not wait 3 seconds for engine replies.
- Tests that require real engine replies are marked slow.
- UI behavior remains covered in the fast suite using deterministic fakes.
- `tests/test_tui.py -m "not slow" --durations=20` shows no avoidable 3-second waits.

---

# Problem 2: Fast tests should not depend on real search depth or engine timing

## Current problem

Some UI/integration tests behave like fast tests but depend on real engine work or timing.

## Required behavior

Fast tests should use:

- deterministic fake engine replies,
- controlled fake board states,
- short polling waits,
- direct handler calls,
- monkeypatched async tasks.

They should not use:

- arbitrary multi-second sleeps,
- real engine search unless extremely cheap,
- real self-play,
- full game loops,
- broad subprocess pytest invocations,
- real timeouts as correctness mechanisms.

## Acceptance criteria

- No non-slow TUI/UI test uses a multi-second arbitrary sleep unless justified.
- Engine-strength or real-search UI tests are slow-marked.
- Fast tests remain deterministic.

---

# Problem 3: Keep runtime-marker meta-tests isolated

## Current status

`tests/test_test_runtime_markers_integration.py` should remain slow-marked.

## Required behavior

The marker meta-test file must not run in:

```bash
uv run --extra dev python -m pytest -m "not slow"
```

It may run in:

```bash
uv run --extra dev python -m pytest tests/test_test_runtime_markers_integration.py -m slow -q
```

## Acceptance criteria

- Runtime-marker meta-tests remain isolated from the fast suite.
- Do not add fake passing tests just to avoid pytest exit code 5 when the file is run alone with `-m "not slow"`.

---

# Problem 4: Confirm Fix 7 substantive test-quality work remains intact

Fix 7 addressed earlier recurring issues. Do not regress them.

## Required checks

Confirm the following remain true:

1. `tests/test_collect.py` contains real behavior tests, not only config assertions.
2. PositionDB old JSONL duplicate aggregation asserts:
   - `count`,
   - `total`,
   - `mean`.
3. PositionDB new JSONL direct load uses hand-authored JSONL and asserts:
   - `count`,
   - `total`,
   - `mean`.
4. Texel loss `k` tests prove:
   - non-default `k` changes MSE,
   - `k=` matches `opts=LossOptions(k=...)`.
5. Opening-book seed tests contain no vacuous executable `assert True`.
6. Opening-book seeded randomness uses local RNG or otherwise does not mutate global RNG in production code.

## Acceptance criteria

- Fix 7 behavior-test improvements are preserved.
- No test-theater regressions are introduced.

---

# Problem 5: Slow-marker policy

## Required policy

A test should be marked slow if it:

- performs real engine search at depth 3 or higher,
- waits on a real engine reply in a UI/TUI test,
- runs real self-play,
- runs broad subprocess pytest collection,
- intentionally tests runtime marker infrastructure,
- depends on multi-second timeouts,
- is an end-to-end integration test rather than a unit-style behavior test.

A test should stay fast if it:

- uses deterministic fake engine replies,
- uses small helper-level behavior,
- uses shallow deterministic move generation,
- avoids arbitrary sleeps,
- completes well under 1 second.

## Acceptance criteria

- Slow tests are honestly marked.
- Fast tests are genuinely fast.

---

# Problem 6: Add fast-suite runtime diagnostics

## Required command

Run and record:

```bash
uv run --extra dev python -m pytest -m "not slow" --durations=50
```

Use this output to identify remaining slow non-slow tests.

## Required action

For any non-slow test over 2 seconds:

- rewrite with fakes/polling, or
- mark slow if it truly requires integration behavior.

For any non-slow test over 3 seconds:

- treat it as a blocker unless strongly justified.

## Acceptance criteria

- The final report includes the slowest non-slow tests.
- No avoidable multi-second TUI waits remain.

---

# Problem 7: Dev-extra documentation remains current

## Required behavior

README/current docs must continue to show one of:

```bash
uv sync --extra dev
```

or:

```bash
uv run --extra dev python -m pytest -m "not slow"
```

Do not worry about every historical TODO/spec file.

## Acceptance criteria

- Current README/current docs explain dev dependency setup.
- Validation commands are reproducible from a clean checkout.

---

# Final validation

Claude Code must run:

```bash
uv run --extra dev python -m ruff check chess_game tests
uv run --extra dev python -m mypy chess_game
uv run --extra dev python -m pylint chess_game/texel --score=y
uv run --extra dev python -m pytest -m "not slow"
uv run --extra dev python -m pytest -m "not slow" --durations=50
```

Then run targeted tests:

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

Then run slow tests separately:

```bash
uv run --extra dev python -m pytest -m slow
```

If the slow suite is too slow, document the limitation.

---

# Acceptance criteria

Fix 8 is complete only when:

1. Ruff passes with dev dependencies.
2. mypy passes with dev dependencies.
3. Texel Pylint passes or remains acceptably high.
4. Full fast suite completes reliably as one command.
5. Full fast suite runtime is reduced or justified.
6. No non-slow TUI test waits several seconds for real engine reply.
7. Real-engine TUI tests are slow-marked or replaced with deterministic fast tests.
8. `tests/test_tui.py -m "not slow" --durations=20` has no avoidable 3-second waits.
9. Runtime-marker meta-tests remain isolated from the fast suite.
10. Fix 7 behavior tests remain intact.
11. Dev-extra validation docs remain current.
12. Targeted tests pass.
13. Slow tests are isolated from fast tests.
14. Any slow-suite runtime limitation is documented honestly.

---

# Notes for Claude Code

## Do not chase unobserved hangs

If the full suite passes repeatedly in your environment, document that and focus on runtime reduction.

## The likely high-value target is TUI test waiting

The 3-second `pilot.pause()` waits are expensive and avoidable.

## Prefer deterministic fakes over sleeps

Fast UI tests should wait for state, not wall-clock time.

## Keep the patch narrow

No chess engine feature work.

## Preserve Fix 7 work

Do not regress the behavior-test improvements.
