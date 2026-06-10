# FIX8_FAST_SUITE_STATUS

Honest status for the Fix 8 fast-suite runtime patch (test-only; no engine/TUI
production code changed).

## Outcome

Full fast suite (`uv run --extra dev python -m pytest -m "not slow"`):

    Before: 1031 passed, 169 deselected in ~45.0s
    After:  1031 passed, 169 deselected in ~35-36s

The reduction is the removal of three fixed 3-second wall-clock waits in the TUI
tests (~11s of real cost on every machine, the likely cause of constrained-
sandbox timeouts). Result is at the spec's "preferred under 35s" line and well
under the "acceptable under 45s" hard target.

## What changed (tests/test_tui.py only)

The three `TestHumanMoveInput` tests used `await pilot.pause(delay=3.0)` to wait
for a real depth-1 engine reply in the `@work(thread=True)` worker.

- `test_human_move_pawn_lands_on_e4` — asserts a White pawn on e4 (a human-side
  state true immediately after the move). Replaced the 3s wait with
  `await pilot.pause()`; no fake engine needed.
- `test_input_cleared_after_valid_move` — asserts the input is cleared on
  submission. Same short pause.
- `test_move_list_shows_both_sides_after_engine_reply` — genuinely needs a
  reply. Monkeypatches `chess_game.tui.get_best_move` with an instant
  first-legal-move fake and waits for state via a new `wait_until()` poll
  helper (no arbitrary sleep). Stress-tested 5/5 runs ~0.74s, no flakiness.

Per-test timing: the three dropped from ~3.6s each to 0.57-0.79s.
`tests/test_tui.py` total: 18.2s -> 9.6s.

All three remain fast; none slow-marked. No new slow real-engine TUI test was
added (the spec said not to block this patch on end-to-end coverage).

## Remaining non-slow tests over 2 seconds (documented, not changed)

Per the Fix 8 reply guidance (do not chase sub-second optimizations; document
justified slightly-over-2s tests when the suite is comfortably under target):

- `tests/test_ai_search.py::test_tt_does_not_overwrite_deeper_entry` — ~2.4s.
  Real search at **depth 2**; a transposition-table correctness invariant.
- `tests/test_ai_search.py::test_alpha_beta_tight_window_visits_no_more_nodes_than_wide_window`
  — ~2.3s. Runs two **depth-3** minimax searches on a mate-in-one position to
  assert an alpha-beta node-count pruning invariant.
- `tests/test_opening_book_search_integration.py::test_book_to_offbook_transition_keeps_repetition_aware_search`
  — ~2.0s. Book/search integration invariant.

Honest flag: the alpha-beta test does depth-3 real search, which by the strict
Problem-5 slow-marker policy ("real engine search at depth 3 or higher") could
be slow-marked. It was left fast because (a) it is a search-correctness
invariant rather than an engine-strength regression, (b) the full suite already
meets the runtime target, and (c) Fix 8's reply guidance was explicitly to
document such cases rather than start a broad slow-marking pass. If the reviewer
prefers, slow-marking it is a one-line change; flagged here for that decision.

## Verified intact / revalidated

- Ruff, mypy clean; pylint `chess_game/texel` 10.00/10.
- Full fast suite reliable as one command (~35-36s, 1031 passed).
- Targeted test set: 199 passed, 11 deselected.
- Runtime-marker meta-tests: 0 selected in `-m "not slow"` (slow-marked).
- Fix 7 behavior tests intact: collection/PositionDB/loss-k/opening-book —
  85 passed; specific tests present (weights propagation, new-JSONL direct load,
  non-default-k MSE, different-seed fake-book). No executable `assert True`
  remains in opening-book tests (the only match is a docstring reference).
- README dev-extra workflow current.

## Investigated, no change needed

- Production `chess_game/self_play.py` uses a real `signal.alarm` timeout
  (exercised by `test_get_best_move_with_timeout_returns_none_on_alarm_timeout`).
  Out of Fix 8 scope and left unchanged; no test-state leak observed (fast suite
  stable across repeated full runs).

## Deferred / limitation

- Slow suite (~15-20 min, depth-3+ engine-strength regressions) remains isolated
  from the fast suite and was not run in full here; run separately with
  `uv run --extra dev python -m pytest -m slow`.
