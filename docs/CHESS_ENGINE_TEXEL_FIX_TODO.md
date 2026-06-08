# CHESS_ENGINE_TEXEL_FIX_TODO.md

## Implementation checklist

This TODO is intended for Claude Code to implement against the current chess engine repository.

The patch should focus on correctness, Texel tuning validity, test reliability, and reproducibility.

Do **not** rewrite the engine around make/unmake search in this patch.

---

# Phase 0: Baseline and safety

## 0.1 Confirm baseline commands

- [ ] Run Ruff:
  - [ ] `uv run python -m ruff check chess_game tests`
- [ ] Run mypy:
  - [ ] `uv run python -m mypy chess_game`
- [ ] Run Pylint on Texel package:
  - [ ] `uv run python -m pylint chess_game/texel --score=y`
- [ ] Run fast tests:
  - [ ] `uv run python -m pytest -m "not slow"`
- [ ] If fast tests hang, identify the slow test and mark it slow as part of Phase 4.

## 0.2 Review current files before editing

- [ ] Inspect `chess_game/chess/ai.py`.
- [ ] Inspect `chess_game/chess/ai_quiescence_helpers.py`.
- [ ] Inspect `chess_game/chess/ai_board_utils.py`.
- [ ] Inspect board draw/checkmate APIs under `chess_game/chess/board/`.
- [ ] Inspect `chess_game/texel/loss.py`.
- [ ] Inspect `chess_game/texel/spsa.py`.
- [ ] Inspect `chess_game/texel/tune.py`.
- [ ] Inspect `chess_game/texel/position_db.py`.
- [ ] Inspect `chess_game/texel/collect.py`.
- [ ] Inspect `chess_game/texel/validate.py`.
- [ ] Inspect `chess_game/texel/online_learning.py`.
- [ ] Inspect tests related to AI/search/quiescence/Texel.

---

# Phase 1: Fix production quiescence search

## 1.1 Unify production tactical move selection

- [ ] Find the production quiescence tactical move selector in `chess_game/chess/ai.py`.
- [ ] Find the tested selector in `chess_game/chess/ai_quiescence_helpers.py`.
- [ ] Replace production-specific tactical move filtering with the helper selector.
- [ ] If helper signature needs extra context, update the helper cleanly.
- [ ] Delete or deprecate duplicate private production selector if no longer needed.
- [ ] Ensure production search and tests use the same tactical move-selection behavior.

## 1.2 Ensure pawn captures are considered

- [ ] Remove logic that globally rejects captures of pieces below bishop value.
- [ ] Remove logic that globally rejects captures where captured value is less than attacker value.
- [ ] Ensure pawn captures are eligible for quiescence when relevant.
- [ ] Ensure promotions are always considered tactical.
- [ ] If using SEE or simplified capture heuristics, make them conservative.
- [ ] Add comments explaining why low-value captures cannot be globally ignored.

## 1.3 Fix stand-pat while in check

- [ ] At the start of production `_quiescence()`, check whether side to move is in check.
- [ ] If side to move is in check:
  - [ ] Generate legal check evasions.
  - [ ] If no legal evasions exist, return ply-adjusted mate score.
  - [ ] Search legal evasions.
  - [ ] Do not evaluate stand-pat before escaping check.
- [ ] If side to move is not in check:
  - [ ] Preserve normal stand-pat behavior.
- [ ] Make sure alpha/beta sign conventions match the existing search style.

## 1.4 Add quiescence guards

- [ ] Confirm existing max quiescence depth behavior.
- [ ] Add or preserve a safe quiescence ply limit.
- [ ] Add or preserve search stop/node-budget handling if available.
- [ ] Ensure quiescence cannot recurse indefinitely through checks/captures.

## 1.5 Add production quiescence tests

Create or update tests, preferably in a new file:

```text
tests/test_ai_quiescence_production.py
```

Add tests:

- [ ] Quiescence does not stand pat while in check.
- [ ] Quiescence searches legal evasions while in check.
- [ ] Quiescence returns mate score when side to move is checkmated at quiescence boundary.
- [ ] Production tactical move selection includes pawn captures.
- [ ] Production tactical move selection includes promotions.
- [ ] Public `get_best_move()` or equivalent benefits from corrected quiescence in a simple tactical position.

---

# Phase 2: Centralize terminal/draw/mate scoring

## 2.1 Add or improve terminal-score helper

- [ ] Locate existing `_terminal_score()` or equivalent in `chess_game/chess/ai.py`.
- [ ] Update it to accept `ply` if it does not already.
- [ ] Return `None` when the position is not terminal.
- [ ] Return draw score for stalemate.
- [ ] Return draw score for repetition if board API supports it.
- [ ] Return draw score for fifty-move rule if board API supports it.
- [ ] Return draw score for insufficient material if board API supports it.
- [ ] Return ply-adjusted mate score for checkmate.

## 2.2 Define mate-score constants clearly

- [ ] Ensure there is a single `MATE_SCORE` constant.
- [ ] Ensure there is a single `DRAW_SCORE` constant.
- [ ] Use mate scores similar to:
  - [ ] `-MATE_SCORE + ply` when side to move is mated.
  - [ ] `MATE_SCORE - ply` when scoring a forced mate for the side to move, if applicable.
- [ ] Ensure signs match the engine's minimax/negamax convention.

## 2.3 Use terminal helper consistently

- [ ] Use the terminal helper near the top of main search.
- [ ] Use the terminal helper near the top of quiescence.
- [ ] Use the terminal helper at root if root logic has special terminal handling.
- [ ] Ensure draw handling is consistent across normal search and quiescence.

## 2.4 Add terminal-score tests

Create or update tests, preferably:

```text
tests/test_search_terminal_scores.py
```

Add tests:

- [ ] Checkmate returns mate score.
- [ ] Mate in 1 is preferred over slower mate.
- [ ] Stalemate returns draw score.
- [ ] Repetition returns draw score if supported.
- [ ] Fifty-move rule returns draw score if supported.
- [ ] Insufficient material returns draw score if supported.

---

# Phase 3: Search determinism and reproducibility

## 3.1 Add deterministic search option

- [ ] Locate `BestMoveOptions` or equivalent.
- [ ] Add deterministic tie-breaking support.
- [ ] Add optional RNG seed support if appropriate.
- [ ] Ensure existing casual/random behavior can remain opt-in.
- [ ] Ensure tests can force deterministic behavior.

Suggested fields:

```python
deterministic: bool = False
rng_seed: int | None = None
```

## 3.2 Remove unseeded randomness from tests

- [ ] Search tests for `random`.
- [ ] Where random behavior is needed, pass an explicit seed.
- [ ] Use deterministic mode in engine regression tests.
- [ ] Ensure repeated runs produce the same result.

## 3.3 Apply deterministic behavior to Texel validation/collection

- [ ] Add seed support to collection options if missing.
- [ ] Add seed support to validation options if missing.
- [ ] Ensure random opening-book selection can be seeded.
- [ ] Ensure move tie-breaking in self-play/validation can be seeded.

---

# Phase 4: Fix test reliability

## 4.1 Mark slow tests

- [ ] Run `uv run python -m pytest -m "not slow"`.
- [ ] If any test takes too long or hangs, identify it.
- [ ] Mark depth-heavy/search-heavy integration tests with:
  - [ ] `@pytest.mark.slow`
- [ ] In particular, inspect:
  - [ ] `tests/test_ai_black_improvements1.py::test_depth3_avoids_g7g5_before_castling`
- [ ] Verify fast tests complete without the slow tests.

## 4.2 Remove vacuous assertions

- [ ] Search tests for `or True`.
- [ ] Search tests for assertions that cannot fail.
- [ ] Replace vacuous assertions with meaningful checks.
- [ ] Delete tests that do not assert useful behavior.
- [ ] Specifically inspect any assertion like:
  - [ ] `assert quiet_cycle_penalty(...) > 0 or True`

## 4.3 Keep fast tests fast

- [ ] Avoid adding deep-search tests to the normal suite.
- [ ] Prefer shallow tactical positions.
- [ ] Use deterministic mode.
- [ ] Use time/node/depth limits where available.
- [ ] Mark expensive tests slow.

---

# Phase 5: Texel loss improvements

## 5.1 Add LossOptions

In `chess_game/texel/loss.py`:

- [ ] Add a `LossOptions` dataclass.
- [ ] Include:
  - [ ] `k`
  - [ ] `use_quiescence`
  - [ ] `quiescence_depth_limit`
  - [ ] `quiescence_node_limit` if feasible
  - [ ] `deterministic`
- [ ] Keep backward compatibility with existing `mean_squared_error(..., k=...)` calls.

Suggested shape:

```python
@dataclass(frozen=True)
class LossOptions:
    k: float = DEFAULT_K
    use_quiescence: bool = True
    quiescence_depth_limit: int = 8
    quiescence_node_limit: int | None = None
    deterministic: bool = True
```

## 5.2 Support static and quiescence scoring

- [ ] Add a helper to score a FEN for Texel loss.
- [ ] Static mode:
  - [ ] Use existing static evaluator.
- [ ] Quiescence mode:
  - [ ] Use bounded quiescence, not full search.
- [ ] Ensure quiescence scoring is deterministic.
- [ ] Ensure quiescence scoring cannot run unbounded.

## 5.3 Verify score perspective

- [ ] Determine whether `evaluate_board()` returns White-relative or side-to-move-relative score.
- [ ] Ensure score passed to sigmoid matches the outcome label perspective.
- [ ] If outcome is White-relative:
  - [ ] Convert side-to-move-relative scores to White-relative scores when needed.
- [ ] Add tests for both White-to-move and Black-to-move FENs.

## 5.4 Update mean_squared_error

- [ ] Use `LossOptions`.
- [ ] Preserve old `k=` keyword behavior.
- [ ] Keep current tests passing.
- [ ] Add tests for:
  - [ ] Static loss mode.
  - [ ] Quiescence loss mode.
  - [ ] Non-default `k`.
  - [ ] Score perspective correctness.

---

# Phase 6: Make SPSA optimize the calibrated loss

## 6.1 Change SPSA API safely

Choose one implementation approach:

### Preferred: pass a loss function

- [ ] Update `spsa.optimize()` to accept a callable loss function.
- [ ] The callable should accept `(pairs, weights)` or `(batch, weights)`.
- [ ] Use that callable for plus/minus perturbation loss.
- [ ] Preserve backwards compatibility if possible.

### Alternative: pass LossOptions

- [ ] Add `loss_options` to `SPSAOptions`.
- [ ] Ensure `spsa.optimize()` passes those options to `mean_squared_error()`.

## 6.2 Update tune.py

- [ ] Calibrate `k`.
- [ ] Construct `LossOptions(k=calibrated_k, ...)`.
- [ ] Use the same loss options for:
  - [ ] Initial MSE.
  - [ ] SPSA optimization.
  - [ ] Final MSE.
- [ ] Ensure reporting and optimization use the same objective.

## 6.3 Add SPSA calibrated-k tests

- [ ] Add a test proving non-default `k` is used by optimization.
- [ ] Add a test proving initial/final MSE use the same loss options.
- [ ] Keep existing SPSA tests passing.

---

# Phase 7: PositionDatabase statistics

## 7.1 Replace overwrite behavior with aggregation

In `chess_game/texel/position_db.py`:

- [ ] Add `PositionStats` dataclass:
  - [ ] `total`
  - [ ] `count`
  - [ ] `add()`
  - [ ] `mean`
- [ ] Change internal storage from `dict[str, float]` to `dict[str, PositionStats]`.
- [ ] When adding a duplicate FEN, aggregate instead of overwrite.
- [ ] Export training pairs as `(fen, mean_outcome)` by default.

## 7.2 Backwards-compatible loading

- [ ] Load old JSON format where values are floats.
- [ ] Load new JSON format where values are objects with `total` and `count`.
- [ ] Save in the new format.
- [ ] Document the format.

## 7.3 PositionDatabase tests

Update or create tests in:

```text
tests/test_position_db.py
```

Add tests:

- [ ] Duplicate FEN aggregation.
- [ ] Mean outcome calculation.
- [ ] Old-format JSON load.
- [ ] New-format JSON save/load round trip.
- [ ] Empty database behavior.

---

# Phase 8: Texel collection fixes

## 8.1 Use CollectionOptions.weights

In `chess_game/texel/collect.py`:

- [ ] Locate `CollectionOptions.weights`.
- [ ] Pass it into `get_best_move()` through `BestMoveOptions`.
- [ ] Add test proving custom weights are passed/used.

## 8.2 Add collection seed support

- [ ] Add `seed: int | None = None` to `CollectionOptions` if missing.
- [ ] Use seeded RNG for:
  - [ ] Random opening book choices.
  - [ ] Tie-breaking if applicable.
  - [ ] Any random self-play behavior.
- [ ] Add reproducibility test.

## 8.3 Preserve draw outcomes

- [ ] Detect stalemate as draw.
- [ ] Detect repetition as draw if board API supports it.
- [ ] Detect fifty-move-rule draw if board API supports it.
- [ ] Detect insufficient material as draw if board API supports it.
- [ ] Store draw outcome as `0.5`.

## 8.4 Handle max-move games explicitly

- [ ] Add `max_move_result` option:
  - [ ] `"draw"`
  - [ ] `"discard"`
- [ ] Default to `"draw"` unless existing behavior strongly requires discard.
- [ ] Add tests for both behaviors.

## 8.5 Add collection tests

Create or update:

```text
tests/test_texel_collection.py
```

Add tests:

- [ ] Collection uses configured weights.
- [ ] Collection records checkmate result correctly.
- [ ] Collection records stalemate/draw result as 0.5.
- [ ] Collection handles max-move game according to option.
- [ ] Collection is reproducible with seed.

---

# Phase 9: Texel validation improvements

## 9.1 Add draw-aware score rate

In `chess_game/texel/validate.py`:

- [ ] Keep existing win/draw/loss counts.
- [ ] Add tuned score rate:
  - [ ] `(tuned_wins + 0.5 * draws) / total`
- [ ] Add baseline score rate:
  - [ ] `(baseline_wins + 0.5 * draws) / total`
- [ ] Make sure results are from tuned engine's perspective, not White's perspective.

## 9.2 Add validation seed support

- [ ] Add seed support if missing.
- [ ] Ensure validation matches are reproducible.
- [ ] Ensure color alternation remains deterministic.

## 9.3 Validation tests

Update:

```text
tests/test_validate.py
```

Add tests:

- [ ] All tuned wins gives score rate 1.0.
- [ ] All baseline wins gives tuned score rate 0.0.
- [ ] All draws gives tuned score rate 0.5.
- [ ] Mixed results calculate correctly.
- [ ] Color alternation does not misattribute wins.

---

# Phase 10: Online learning guardrail

## 10.1 Produce candidate weights first

In `chess_game/texel/online_learning.py`:

- [ ] Change online update flow to produce candidate weights.
- [ ] Do not immediately overwrite current weights.
- [ ] Save candidate to temporary/candidate path if needed.

## 10.2 Add validation gate

- [ ] Add options:
  - [ ] `require_validation_improvement: bool = True`
  - [ ] `min_validation_mse_improvement: float = 0.0`
  - [ ] `keep_rejected_candidate: bool = False`
- [ ] Compare baseline validation MSE to candidate validation MSE.
- [ ] Accept candidate only if it passes configured criteria.
- [ ] If no validation data exists and `require_validation_improvement=True`, do not promote automatically.

## 10.3 Add rollback/backup behavior

- [ ] Before promoting candidate, save current weights as backup.
- [ ] Use atomic replace where practical.
- [ ] Invalidate weight cache only after successful promotion.
- [ ] Preserve current weights if candidate is rejected.

## 10.4 Online learning tests

Update:

```text
tests/test_online_learning.py
```

Add tests:

- [ ] Candidate accepted when validation improves.
- [ ] Candidate rejected when validation worsens.
- [ ] Current weights preserved on rejection.
- [ ] Backup created on acceptance.
- [ ] Candidate file behavior respects `keep_rejected_candidate`.
- [ ] Cache invalidated only after accepted promotion.

---

# Phase 11: Perft and move-generation confidence

## 11.1 Check existing perft coverage

- [ ] Search for existing perft tests.
- [ ] If robust perft tests exist, ensure they still pass.
- [ ] If missing or incomplete, add perft helper tests.

## 11.2 Add standard perft tests

Create or update:

```text
tests/test_perft.py
```

Add:

- [ ] Start position depth 1 = 20.
- [ ] Start position depth 2 = 400.
- [ ] Start position depth 3 = 8902.
- [ ] Start position depth 4 = 197281, marked slow if needed.

## 11.3 Add special perft positions

Add positions covering:

- [ ] Castling.
- [ ] En passant.
- [ ] Promotion.
- [ ] Checks.
- [ ] Pins.
- [ ] Check evasions.
- [ ] Discovered checks.

Mark expensive depths as slow.

---

# Phase 12: Documentation

## 12.1 Add Texel tuning docs

Create:

```text
docs/TEXEL_TUNING.md
```

Include:

- [ ] What Texel tuning means in this project.
- [ ] Difference between static loss and quiescence loss.
- [ ] Why calibrated `k` matters.
- [ ] How duplicate positions are aggregated.
- [ ] How to run tuning.
- [ ] How to run validation.
- [ ] How online learning is gated.
- [ ] How to reproduce runs with seeds.

## 12.2 Add search notes

Create or update:

```text
docs/ENGINE_SEARCH_NOTES.md
```

Include:

- [ ] Quiescence behavior.
- [ ] No stand-pat in check.
- [ ] Tactical move selection policy.
- [ ] Terminal/draw/mate scoring.
- [ ] Slow future work: make/unmake search.

## 12.3 Update README

- [ ] Add fast test command:
  - [ ] `uv run python -m pytest -m "not slow"`
- [ ] Add slow test command:
  - [ ] `uv run python -m pytest -m slow`
- [ ] Add lint/type-check commands.
- [ ] Mention Texel tuning docs.

---

# Phase 13: Final validation

## 13.1 Run formatting/lint/type checks

- [ ] `uv run python -m ruff check chess_game tests`
- [ ] `uv run python -m mypy chess_game`
- [ ] `uv run python -m pylint chess_game/texel --score=y`

## 13.2 Run fast tests

- [ ] `uv run python -m pytest -m "not slow"`

## 13.3 Run targeted tests

Run:

```bash
uv run python -m pytest \
  tests/test_ai_quiescence_helpers.py \
  tests/test_ai_search.py \
  tests/test_alpha_beta_pruning.py \
  tests/test_eval_weights.py \
  tests/test_loss.py \
  tests/test_calibrate.py \
  tests/test_position_db.py \
  tests/test_spsa.py \
  tests/test_online_learning.py \
  tests/test_validate.py \
  -q
```

Also run any new tests:

```bash
uv run python -m pytest \
  tests/test_ai_quiescence_production.py \
  tests/test_search_terminal_scores.py \
  tests/test_texel_loss_quiescence.py \
  tests/test_texel_collection.py \
  tests/test_perft.py \
  -q
```

## 13.4 Run slow tests separately

- [ ] `uv run python -m pytest -m slow`

If slow tests are still too slow, document which ones and why.

---

# Phase 14: Completion criteria

Claude Code should consider the patch complete only when all of these are true:

- [ ] Fast tests complete reliably.
- [ ] Slow tests are clearly marked.
- [ ] Ruff passes.
- [ ] Mypy passes.
- [ ] Pylint for `chess_game/texel` passes or remains acceptably high.
- [ ] Production quiescence uses the tested helper path.
- [ ] Production quiescence does not stand pat in check.
- [ ] Pawn captures are not globally excluded from quiescence.
- [ ] Draw states are handled in terminal search scoring.
- [ ] Mate scores are distance-aware.
- [ ] Random search behavior is controllable for deterministic tests.
- [ ] Texel loss supports quiescence scoring.
- [ ] Texel loss has correct score/result perspective.
- [ ] SPSA uses the calibrated `k`.
- [ ] PositionDatabase aggregates duplicate positions.
- [ ] PositionDatabase loads old and new formats.
- [ ] CollectionOptions.weights is used.
- [ ] Collection preserves draw outcomes.
- [ ] Collection has seed support.
- [ ] Validation reports draw-aware score rate.
- [ ] Online learning validates candidates before promotion.
- [ ] Online learning preserves rollback/backup behavior.
- [ ] Vacuous assertions are removed.
- [ ] Documentation is updated.

---

# Notes for implementation

## Be careful with sign conventions

Search, evaluation, and Texel labels may use different perspectives:

- Side-to-move perspective.
- White perspective.
- Root-player perspective.

Before changing loss or mate scoring, identify the current convention and add tests that lock it down.

## Be careful with private tests

Testing private functions is acceptable here only for narrow search correctness bugs. Prefer public API tests where feasible.

## Be careful with performance

Quiescence-based Texel loss can be much slower than static loss. Keep it bounded and configurable. Unit tests may use static loss or very shallow quiescence.

## Do not combine with make/unmake refactor

The clone-heavy search is a real performance issue, but replacing it with make/unmake is a separate high-risk patch. Leave clear TODO comments/docs for future work instead.

