# TEXEL_FIX7_STATUS

Honest status for the Fix 7 test-reliability/test-quality patch. Each item is
marked complete only where a real test or validation command proves it.

## Verified by new behavior tests

- **Opening-book RNG is local, not global** — `get_best_move()` no longer calls
  `random.seed()`; it builds a local `random.Random(rng_seed)` threaded into
  book selection and tie-breaking.
  - `tests/test_opening_book.py::TestOpeningBookSeedReproducibility::test_seeded_call_does_not_mutate_global_rng`
- **Collection weights propagation through the real path** — captures the
  `BestMoveOptions` actually passed by `_play_game()`.
  - `tests/test_collect.py::test_play_game_propagates_weights_to_get_best_move`
- **Max-move draw** stores outcome `0.5` (at `_play_game` and `collect_games`).
  - `test_play_game_max_move_draw_returns_half`, `test_collect_games_draw_stores_half_outcomes`
- **Max-move discard** stores nothing / returns `None`.
  - `test_play_game_max_move_discard_returns_none`, `test_collect_games_discard_stores_nothing`
- **Seed reproducibility** — same `CollectionOptions.seed` reproduces identical
  recorded data; the fake chooser keys off the seed-derived per-move rng_seed so
  the result genuinely depends on the seed.
  - `test_collect_games_same_seed_reproducible`
- **PositionDB old JSONL duplicate aggregation** — hand-authored file; asserts
  `get_stats()` `count`/`total`/`mean`.
  - `tests/test_position_db.py::TestPositionDB::test_old_jsonl_duplicate_aggregation`
- **PositionDB new JSONL direct load** — hand-authored `{total, count}` (count 4
  on a single line); asserts `count`/`total`/`mean` without using `save()`.
  - `test_new_jsonl_direct_load_raw_stats`
- **Texel loss non-default `k` changes MSE** — on a one-pawn-edge position
  (the spec's queen-up FEN saturates the sigmoid; rationale in the test docstring).
  - `tests/test_loss.py::TestTexelLossKParameter::test_non_default_k_changes_mse`
- **Texel loss `k=` matches `opts=LossOptions(k=)`**.
  - `test_k_kwarg_matches_loss_options`
- **Opening-book same-seed and different-seed selection** with a controlled
  multi-candidate fake book (replaces a prior `assert True`).
  - `test_same_seed_selects_same_move_with_fake_book`, `test_different_seeds_can_select_different_moves`

## Already passing / revalidated

- Ruff (`--extra dev`).
- mypy (`--extra dev`).
- Pylint `chess_game/texel` and full `chess_game`: 10.00/10.
- Full fast suite as **one command**: `1031 passed, 169 deselected` in ~46s.
  Verified repeatedly (3x in Phase 0 at ~43.5s, again in final validation).
- Targeted test set: `154 passed, 11 deselected`.
- Runtime-marker meta-tests isolated: deselected from `-m "not slow"` (0.02s),
  pass under `-m slow` (15 passed).
- Perft: exact start-position counts (20/400/8902/197281, depth-4 slow);
  special positions are honestly labeled `test_perft_smoke_*`.

## Problem 1 (full-suite timeout): not reproduced

The Fix 7 spec reported the one-command fast suite timing out in a constrained
sandbox. It was **not reproduced** here: the suite completes reliably as one
command (~44-46s) across repeated runs. The localized RNG fix (above) removes a
real global-state contamination vector regardless.

## Investigated, no change needed

- **Signal/alarm leakage**: `grep -rn "signal.alarm\|signal.signal" tests`
  found no usages, so there was nothing to contain.

## Deferred (documented future work)

- Exact known-count special perft positions (castling/en-passant/promotion/
  check-evasion) remain smoke tests; exact counts deferred.
- Slow suite full runtime is long (depth-3+ engine-strength regressions, ~15-20
  min). It is isolated from the fast suite and run separately; not executed in
  full here.
