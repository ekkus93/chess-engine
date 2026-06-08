# CHESS_ENGINE_TEXEL_FIX2_TODO.md

## Implementation checklist

This TODO is for the second follow-up patch to finish the incomplete Texel/search/test-reliability work.

The patch should be focused. Do **not** rewrite the engine around make/unmake search, bitboards, Zobrist hashing, NNUE, or broad search architecture changes.

---

# Phase 0: Baseline verification

## 0.1 Run baseline commands

- [ ] Run Ruff:
  - [ ] `uv run python -m ruff check chess_game tests`
- [ ] Run mypy:
  - [ ] `uv run python -m mypy chess_game`
- [ ] Run Pylint on Texel package:
  - [ ] `uv run python -m pylint chess_game/texel --score=y`
- [ ] Run fast tests:
  - [ ] `uv run python -m pytest -m "not slow"`

## 0.2 Record current failures

- [ ] Record whether `pytest -m "not slow"` completes.
- [ ] If it hangs, identify the exact test where it hangs.
- [ ] Confirm whether these are still slow:
  - [ ] `tests/test_ai_repetition_integration.py::test_repetition_sensitive_position_counts_change_root_choice`
  - [ ] `tests/test_ai_strategy15_regressions.py::TestQuiescenceDepth::test_quiescence_resolves_capture_chain`
- [ ] Confirm `deterministic=True` currently crashes before fixing it.

---

# Phase 1: Fix deterministic mode crash

## 1.1 Locate deterministic tie-break code

- [ ] Inspect `BestMoveOptions`.
- [ ] Inspect move ordering and tie-breaking code in `chess_game/chess/ai.py`.
- [ ] Locate `_move_sort_key()` or equivalent.
- [ ] Confirm it currently returns non-orderable square objects.

## 1.2 Replace sort key with primitive values

- [ ] Change `_move_sort_key()` to return only primitive comparable values.
- [ ] Use one of:
  - [ ] numeric square indices,
  - [ ] algebraic square strings,
  - [ ] UCI move strings if available.
- [ ] Include promotion as a string.
- [ ] Do not return `ConstantSquare` objects.

Suggested shape:

```python
def _move_sort_key(move: Move | LegalMove) -> tuple[int, int, str]:
    return (
        int(move.start.row) * 8 + int(move.start.col),
        int(move.end.row) * 8 + int(move.end.col),
        move.promotion.name if move.promotion else "",
    )
```

Adapt field names to actual code.

## 1.3 Add deterministic tests

Add or update tests:

- [ ] `get_best_move(Board(), depth=1, deterministic=True)` does not crash.
- [ ] Repeated deterministic calls return the same move.
- [ ] Deterministic equal-score tie-breaking is stable.
- [ ] Seeded random mode is reproducible if supported.
- [ ] Tests do not rely on unseeded randomness.

---

# Phase 2: Make fast test suite complete

## 2.1 Identify slow non-slow tests

- [ ] Run:
  - [ ] `uv run python -m pytest -m "not slow" -vv`
- [ ] Identify the first hanging/very slow test.
- [ ] Repeat until all non-slow tests complete.

Known candidates:

- [ ] `tests/test_ai_repetition_integration.py::test_repetition_sensitive_position_counts_change_root_choice`
- [ ] `tests/test_ai_strategy15_regressions.py::TestQuiescenceDepth::test_quiescence_resolves_capture_chain`

## 2.2 Mark or rewrite slow tests

For each slow test:

- [ ] If it is an engine-strength/depth-heavy integration test, mark it:
  - [ ] `@pytest.mark.slow`
- [ ] If it can be converted into a fast unit test, rewrite it with:
  - [ ] lower depth,
  - [ ] narrower position,
  - [ ] deterministic mode,
  - [ ] direct helper-level assertion,
  - [ ] no full expensive search where avoidable.

## 2.3 Confirm fast suite

- [ ] Run:
  - [ ] `uv run python -m pytest -m "not slow"`
- [ ] Confirm it completes.
- [ ] Record runtime.

---

# Phase 3: Implement safe TT mate-score behavior

## 3.1 Add mate-score helper

In the search/TT module:

- [ ] Add a helper:
  - [ ] `_is_mate_score(score: int) -> bool`
- [ ] Use a margin:
  - [ ] `MATE_SCORE_MARGIN = 1_000` or similar.
- [ ] Return true for scores close to `MATE_SCORE` or `-MATE_SCORE`.

Suggested:

```python
MATE_SCORE_MARGIN = 1_000

def _is_mate_score(score: int) -> bool:
    return abs(score) >= MATE_SCORE - MATE_SCORE_MARGIN
```

## 3.2 Skip TT storage for mate scores

- [ ] Locate `_store_tt_cache()` or equivalent.
- [ ] Before creating/storing a TT entry:
  - [ ] if `_is_mate_score(score)`, return without storing.
- [ ] Keep storing normal non-mate scores.
- [ ] Add a TODO comment:
  - [ ] full TT mate-score normalization is future work.

## 3.3 Ensure TT retrieval does not use old mate entries

If old mate entries can exist in memory:

- [ ] Add a defensive check in `_check_tt_cache()`.
- [ ] If a TT entry score is a mate score:
  - [ ] ignore the entry for cutoff/use,
  - [ ] optionally use its best move only if safe,
  - [ ] prefer simplest behavior: ignore the entry.

## 3.4 Add tests

Add tests:

- [ ] `_is_mate_score(MATE_SCORE)` is true.
- [ ] `_is_mate_score(MATE_SCORE - 1)` is true.
- [ ] `_is_mate_score(-MATE_SCORE + 1)` is true.
- [ ] `_is_mate_score(500)` is false.
- [ ] `_store_tt_cache()` skips mate scores.
- [ ] `_store_tt_cache()` stores normal scores.
- [ ] TT lookup ignores any mate-score entries if such entries are manually inserted.

---

# Phase 4: Complete terminal/draw handling

## 4.1 Inspect draw APIs

Inspect board/game-state APIs for:

- [ ] checkmate,
- [ ] stalemate,
- [ ] fifty-move rule,
- [ ] seventy-five move rule,
- [ ] insufficient material,
- [ ] dead position,
- [ ] repetition,
- [ ] fivefold repetition.

## 4.2 Update terminal helper

- [ ] Locate `_terminal_score()` or equivalent.
- [ ] Ensure it accepts `ply`.
- [ ] Return `None` for non-terminal positions.
- [ ] Return draw score for every supported draw state.
- [ ] Return ply-adjusted mate score for checkmate.

Include where available:

- [ ] fifty-move rule,
- [ ] seventy-five move rule,
- [ ] insufficient material,
- [ ] dead position,
- [ ] fivefold repetition,
- [ ] stalemate.

## 4.3 Use terminal helper consistently

- [ ] Main search calls terminal helper near the top.
- [ ] Quiescence calls terminal helper near the top where practical.
- [ ] Root logic handles terminal states if needed.
- [ ] Repetition handling remains correct if it depends on search context.

## 4.4 Add tests

Add/update tests:

- [ ] checkmate returns mate score.
- [ ] stalemate returns draw score.
- [ ] fifty-move rule returns draw score.
- [ ] insufficient material returns draw score.
- [ ] seventy-five move rule returns draw score if API supports it.
- [ ] dead position returns draw score if API supports it.
- [ ] fivefold repetition returns draw score if API supports it.
- [ ] quiescence returns draw score for terminal draw state where practical.

---

# Phase 5: Fix RNG seed behavior before opening book

## 5.1 Move seed initialization

- [ ] Locate `get_best_move()`.
- [ ] Find where `options.rng_seed` is applied.
- [ ] Move seed/RNG setup before opening-book lookup.
- [ ] Ensure `random_opening_book=True` is controlled by the seed.

## 5.2 Prefer local RNG if feasible

If low-risk:

- [ ] Create a local `random.Random(options.rng_seed)` instance.
- [ ] Pass it into opening-book random selection.
- [ ] Avoid global `random.seed()`.

If too invasive:

- [ ] Use the minimal fix by seeding before opening-book selection.
- [ ] Document that a future patch should replace global RNG with local RNG plumbing.

## 5.3 Add tests

Add tests:

- [ ] Same seed gives same random opening-book move.
- [ ] Different seeds can produce different moves if multiple book moves exist.
- [ ] Seeded collection is reproducible in a small/mocked scenario.

---

# Phase 6: Strengthen Texel loss behavior and tests

## 6.1 Verify evaluator perspective

- [ ] Confirm whether `evaluate()` / `evaluate_board()` is White-relative or side-to-move-relative.
- [ ] Do not add sign flip unless needed.
- [ ] Add comments/tests locking down the convention.

## 6.2 Strengthen `_score_position()` tests

Add tests:

- [ ] White material advantage gives positive score.
- [ ] Black material advantage gives negative score.
- [ ] Sign is independent of side to move for equivalent material positions.
- [ ] Static mode works.
- [ ] Quiescence mode works with shallow bounded depth.
- [ ] Non-default `k` changes loss.
- [ ] `mean_squared_error(..., k=...)` compatibility still works.

## 6.3 Optional node limit

- [ ] If practical, add `quiescence_node_limit: int | None` to `LossOptions`.
- [ ] Enforce it in quiescence loss scoring.
- [ ] Add test for bounded behavior.

If not practical:

- [ ] Document that quiescence loss is depth-bounded only for now.

---

# Phase 7: Finish validation metrics

## 7.1 Add baseline score rate

In `chess_game/texel/validate.py`:

- [ ] Add `baseline_score_rate`.
- [ ] Ensure zero games returns `0.0`.
- [ ] Formula:
  - [ ] `(baseline_wins + 0.5 * draws) / total_games`

## 7.2 Update reporting

- [ ] Update CLI/reporting to display tuned score rate.
- [ ] Update CLI/reporting to display baseline score rate if appropriate.
- [ ] Keep win rate available, but do not rely only on win rate.
- [ ] If pass/fail logic exists, prefer score rate over pure win rate.

## 7.3 Add validation tests

Add tests:

- [ ] all tuned wins gives tuned score rate `1.0`.
- [ ] all baseline wins gives tuned score rate `0.0`.
- [ ] all draws gives tuned score rate `0.5` and baseline score rate `0.5`.
- [ ] mixed results calculate correctly.
- [ ] zero games handles cleanly.
- [ ] color alternation does not misattribute wins if validation alternates colors.

---

# Phase 8: Finish online-learning guardrail

## 8.1 Extend OnlineLearningConfig

Add:

- [ ] `require_validation_improvement: bool = True`
- [ ] `min_validation_mse_improvement: float = 0.0`
- [ ] `keep_rejected_candidate: bool = False`
- [ ] `validation_fraction: float = 0.20`
- [ ] `validation_seed: int = 0`

Remove or replace hardcoded validation constants where possible.

## 8.2 Implement candidate promotion flow

- [ ] Generate candidate weights first.
- [ ] Do not overwrite active weights before validation.
- [ ] Split train/validation using config.
- [ ] If validation set too small and validation improvement is required:
  - [ ] do not promote active weights.
- [ ] Compare:
  - [ ] `candidate_val_mse <= baseline_val_mse - min_validation_mse_improvement`
- [ ] Promote only if accepted.

## 8.3 Candidate/backup behavior

Implement either file-based or explicitly in-memory candidate behavior.

Preferred file-based behavior:

- [ ] Write candidate to `weights.candidate.json`.
- [ ] On acceptance:
  - [ ] copy active weights to `weights.previous.json` if active weights exist,
  - [ ] atomically replace active weights,
  - [ ] invalidate cache,
  - [ ] remove candidate unless configured to keep it.
- [ ] On rejection:
  - [ ] preserve active weights,
  - [ ] remove candidate unless `keep_rejected_candidate=True`.

If in-memory only:

- [ ] Document that candidate is not persisted unless accepted.
- [ ] Still implement tests proving rejected candidates do not overwrite active weights.

## 8.4 Add online-learning tests

Add tests:

- [ ] candidate accepted when validation improves enough.
- [ ] candidate rejected when validation worsens.
- [ ] candidate rejected when improvement is below threshold.
- [ ] current active weights preserved on rejection.
- [ ] backup created on acceptance when active weights exist.
- [ ] cache invalidated only after accepted promotion.
- [ ] rejected candidate file behavior respects `keep_rejected_candidate`.
- [ ] too-small validation set does not promote by default.
- [ ] unsafe/no-validation promotion requires explicit config if supported.

---

# Phase 9: Strengthen PositionDB tests

## 9.1 Fix stale comments

- [ ] Search for comments saying “last outcome wins.”
- [ ] Replace with aggregation/mean-outcome wording.

## 9.2 Add duplicate aggregation tests

- [ ] Add same FEN with outcomes `1.0`, `0.5`, `0.0`.
- [ ] Verify count is `3`.
- [ ] Verify total is `1.5`.
- [ ] Verify mean is `0.5`.

## 9.3 Add old JSONL compatibility tests

- [ ] Create temp file with old lines:
  - [ ] `{"pos": "...", "outcome": 1.0}`
- [ ] Load database.
- [ ] Verify stats total/count.
- [ ] Add duplicate old-format lines.
- [ ] Verify aggregation.

## 9.4 Add new JSONL compatibility tests

- [ ] Create temp file with new lines:
  - [ ] `{"pos": "...", "total": 3.0, "count": 4}`
- [ ] Load database.
- [ ] Verify stats.
- [ ] Save and reload.
- [ ] Verify round trip.

## 9.5 Add empty DB tests

- [ ] Empty DB length/export behavior.
- [ ] Empty DB save/load if applicable.

---

# Phase 10: Strengthen collection tests and validation

## 10.1 Validate max_move_result

- [ ] Add validation for `max_move_result`.
- [ ] Accept only:
  - [ ] `"draw"`
  - [ ] `"discard"`
- [ ] Raise `ValueError` for invalid values.

## 10.2 Add fast collection unit tests

Use monkeypatch/mocks where needed. Avoid expensive self-play in fast tests.

Add tests:

- [ ] `CollectionOptions.weights` is passed into `BestMoveOptions`.
- [ ] Draw outcomes are stored as `0.5`.
- [ ] Max-move `"draw"` stores draw outcome.
- [ ] Max-move `"discard"` stores no positions.
- [ ] Invalid `max_move_result` raises `ValueError`.
- [ ] `CollectionOptions(seed=...)` is reproducible.
- [ ] No tests contain assertions like `assert len(db) >= 0`.

## 10.3 Review slow collection tests

- [ ] Keep expensive collection/self-play tests marked slow.
- [ ] Ensure fast collection tests are meaningful and quick.

---

# Phase 11: Add or explicitly defer special perft cases

## 11.1 Keep start-position perft

Ensure these remain:

- [ ] depth 1 = 20.
- [ ] depth 2 = 400.
- [ ] depth 3 = 8902.
- [ ] depth 4 = 197281 marked slow.

## 11.2 Add fast special perft cases

Add at least shallow tests for:

- [ ] castling,
- [ ] en passant,
- [ ] promotion,
- [ ] check evasions.

Use known perft positions where possible.

## 11.3 Defer remaining cases if needed

If not adding all special cases now, document future cases:

- [ ] pins,
- [ ] discovered checks,
- [ ] complex castling/en passant interactions.

---

# Phase 12: Fix documentation

## 12.1 Correct TT terminology

- [ ] Search docs for “Zobrist”.
- [ ] If docs claim current TT is Zobrist-keyed, correct it.
- [ ] Use:
  - [ ] “position-keyed transposition table”
  - [ ] or “string-keyed transposition table using `position_key()`.”
- [ ] Add future-work note for true Zobrist hashing.

## 12.2 Update search docs

Update `docs/ENGINE_SEARCH_NOTES.md`:

- [ ] deterministic mode behavior,
- [ ] TT mate-score limitation,
- [ ] future mate-score normalization,
- [ ] current string-keyed TT,
- [ ] future Zobrist hashing.

## 12.3 Update Texel docs

Update `docs/TEXEL_TUNING.md`:

- [ ] validation split behavior,
- [ ] online-learning promotion gate,
- [ ] candidate acceptance/rejection,
- [ ] seed reproducibility,
- [ ] score-rate metrics.

## 12.4 Update README if needed

- [ ] Fast test command.
- [ ] Slow test command.
- [ ] Lint/type-check commands.
- [ ] Documentation links.

---

# Phase 13: Final validation

## 13.1 Static checks

Run:

- [ ] `uv run python -m ruff check chess_game tests`
- [ ] `uv run python -m mypy chess_game`
- [ ] `uv run python -m pylint chess_game/texel --score=y`

## 13.2 Fast tests

Run:

- [ ] `uv run python -m pytest -m "not slow"`

This must complete.

## 13.3 Targeted tests

Run:

```bash
uv run python -m pytest \
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
  -m "not slow" -q
```

- [ ] Confirm targeted tests pass.

## 13.4 Slow tests

Run:

- [ ] `uv run python -m pytest -m slow`

If slow tests are too slow:

- [ ] Document which tests are slow.
- [ ] Confirm they are marked slow.
- [ ] Do not let them contaminate the fast suite.

---

# Phase 14: Completion criteria

This patch is complete only when:

- [ ] `deterministic=True` no longer crashes.
- [ ] Deterministic mode returns stable repeated results.
- [ ] `pytest -m "not slow"` completes.
- [ ] Known slow tests are marked slow or rewritten.
- [ ] TT mate scores are skipped or ignored until normalization exists.
- [ ] TT mate-score normalization remains documented as future work.
- [ ] Terminal helper covers all practical draw states exposed by current APIs.
- [ ] Quiescence still does not stand pat in check.
- [ ] `rng_seed` controls opening-book randomness.
- [ ] Texel loss tests prove score perspective behavior.
- [ ] Texel loss tests prove non-default `k` behavior.
- [ ] `ValidationResult` has `tuned_score_rate`.
- [ ] `ValidationResult` has `baseline_score_rate`.
- [ ] Reporting includes draw-aware score rate.
- [ ] Online learning has configurable validation gate options.
- [ ] Online learning accept/reject/backup/cache behavior is tested.
- [ ] PositionDB duplicate aggregation is tested.
- [ ] PositionDB old/new JSONL compatibility is tested.
- [ ] Collection weights/draw/max-move/seed behavior is tested.
- [ ] Invalid `max_move_result` is rejected.
- [ ] At least basic special perft positions are added or explicitly deferred.
- [ ] Docs no longer say the current TT is Zobrist-keyed.
- [ ] Ruff passes.
- [ ] Mypy passes.
- [ ] Pylint for Texel passes or remains acceptably high.
- [ ] Fast tests and targeted tests pass.

---

# Notes for implementation

## Keep the patch small

Do not refactor the entire engine. Fix the blockers directly.

## Avoid expensive tests in the fast suite

Expensive full-engine search tests belong in the slow suite.

## Do not hide failures with weak assertions

Do not add assertions like:

```python
assert len(db) >= 0
```

Every new test should prove a meaningful invariant.

## Use deterministic tests

Wherever search/randomness is involved, use:

```python
BestMoveOptions(deterministic=True)
```

or an explicit seed.

## Preserve compatibility

Existing saved PositionDB files and existing CLI usage should continue to work.

## Future work

Leave clear future-work notes for:

- make/unmake search,
- Zobrist hashing,
- TT mate-score normalization,
- broader perft suite,
- search module decomposition.
