# CHESS_ENGINE_TEXEL_FIX2_SPEC.md

## Purpose

This document specifies the second follow-up patch for the chess engine's Texel/search correctness work.

The previous patch made meaningful progress, especially around production quiescence, Texel loss scaffolding, PositionDB aggregation, and basic validation gating. However, review of the latest code found that the implementation is **not complete** and contains several blocking issues.

This Fix 2 patch should finish the incomplete work from `CHESS_ENGINE_TEXEL_FIX_TODO.md` without broad rewrites.

Primary goals:

1. Fix the `deterministic=True` crash.
2. Make the fast test suite actually finish with `pytest -m "not slow"`.
3. Implement safe transposition-table handling for mate scores until proper normalization exists.
4. Finish incomplete terminal/draw handling.
5. Finish deterministic seed behavior, especially opening-book randomness.
6. Finish Texel validation metrics and online-learning guardrails.
7. Strengthen tests around PositionDB, collection, validation, online learning, Texel loss, and perft.
8. Correct inaccurate documentation.

---

## Hard scope boundaries

### In scope

- Search correctness fixes.
- Deterministic mode fix.
- Test reliability fixes.
- Safe TT mate-score behavior.
- Terminal/draw handling for already-supported board APIs.
- Texel metrics and guardrail completion.
- Reproducibility fixes.
- Targeted tests.
- Documentation corrections.

### Out of scope

Do **not** implement these in this patch:

- make/unmake search refactor,
- bitboard board rewrite,
- Zobrist hashing,
- NNUE or neural evaluator,
- large `ai.py` architectural split,
- new engine-strength heuristics unrelated to the blockers,
- broad formatting-only refactors.

Those are future milestones.

---

# Current blocking issues

The latest review found the following blockers.

## Blocker 1: `deterministic=True` crashes

Calling:

```python
get_best_move(
    Board(),
    depth=1,
    book_options=BestMoveOptions(use_opening_book=False, deterministic=True),
)
```

raises:

```text
TypeError: '<' not supported between instances of 'ConstantSquare' and 'ConstantSquare'
```

Cause: deterministic tie-break comparison uses a tuple containing `move.start` and `move.end`, which are `ConstantSquare` objects and not orderable.

The sort key must use primitive comparable values.

---

## Blocker 2: Fast test suite still does not complete

The command:

```bash
uv run python -m pytest -m "not slow"
```

still times out.

At least these tests are slow/hanging and currently not properly isolated:

```text
tests/test_ai_repetition_integration.py::test_repetition_sensitive_position_counts_change_root_choice
tests/test_ai_strategy15_regressions.py::TestQuiescenceDepth::test_quiescence_resolves_capture_chain
```

The Fix 2 patch must make the non-slow test suite complete reliably.

---

## Blocker 3: TT mate-score safety was not actually implemented

The prior decision was:

- Do not implement full TT mate-score normalization yet.
- Until normalization exists, avoid storing or using mate scores in the transposition table.

The latest code added a TODO comment, but still stores all TT scores, including mate scores.

This is not safe.

---

## Blocker 4: Terminal/draw handling remains incomplete

The code handles some draw cases, but board/game-state APIs also support additional draw states such as:

- seventy-five move rule,
- dead position,
- fivefold repetition.

These should be included where the board API already supports them.

Quiescence should also use the centralized terminal/draw helper where practical.

---

## Blocker 5: Random seed is applied too late for opening-book randomness

`get_best_move()` applies `rng_seed` after opening-book selection. If `random_opening_book=True`, the random book move happens before the seed is applied.

This breaks reproducibility in Texel collection and any tests relying on seeded book selection.

---

## Blocker 6: Validation metrics are incomplete

`ValidationResult` has `tuned_score_rate`, but is missing `baseline_score_rate`.

CLI/reporting still emphasizes win rate instead of draw-aware score rate.

---

## Blocker 7: Online learning guardrail is only partial

The online-learning code has a hardcoded validation split and a hardcoded improvement gate, but missing required configuration:

```python
require_validation_improvement: bool = True
min_validation_mse_improvement: float = 0.0
keep_rejected_candidate: bool = False
```

Tests for accept/reject/backup/cache behavior are incomplete.

---

## Blocker 8: PositionDB tests are incomplete/stale

Implementation mostly aggregates duplicates, but tests do not strongly verify:

- duplicate aggregation,
- old JSONL load,
- new JSONL load,
- old duplicate aggregation,
- empty DB behavior.

There is also a stale comment saying “last outcome wins,” which is now wrong.

---

## Blocker 9: Collection tests are weak

Collection has seed/weights/max-move/draw support, but tests are too weak and contain assertions that cannot fail, such as:

```python
assert len(db) >= 0
```

The tests must prove actual behavior.

---

## Blocker 10: Special perft coverage is incomplete

Start-position perft exists, but special perft positions for castling/en passant/promotion/checks/pins/check evasions/discovered checks were not added.

Either add these positions or explicitly document that deeper special perft coverage is deferred to a later move-generation patch. Prefer adding at least a small fast subset.

---

## Blocker 11: Documentation says TT is Zobrist-keyed

The docs say the transposition table is Zobrist-keyed. This is inaccurate. The current code uses a string position key, not true Zobrist hashing.

Docs must be corrected to say “position-keyed” or “string-keyed.”

---

# Detailed requirements

## 1. Deterministic mode

### Required behavior

When `BestMoveOptions(deterministic=True)` is used:

- no random shuffle,
- no random tie-break,
- no comparison of non-orderable objects,
- equal-score moves are resolved by a stable primitive key,
- the same position/depth/options produce the same move on repeated calls.

### Stable key

Implement a helper that returns only primitive comparable values.

Acceptable examples:

```python
def _move_sort_key(move: Move | LegalMove) -> tuple[int, int, str]:
    return (
        int(move.start.row) * 8 + int(move.start.col),
        int(move.end.row) * 8 + int(move.end.col),
        move.promotion.name if move.promotion else "",
    )
```

or:

```python
def _move_sort_key(move: Move | LegalMove) -> tuple[str, str, str]:
    return (
        square_to_algebraic(move.start),
        square_to_algebraic(move.end),
        move.promotion.name if move.promotion else "",
    )
```

Do not return `ConstantSquare` objects in the sort key.

### Tests

Add tests proving:

1. Deterministic depth-1 search from start position does not crash.
2. Repeated deterministic calls return the same move.
3. Equal-score tie-breaking uses stable ordering.
4. Seeded random mode remains reproducible if supported.
5. Casual random mode remains allowed if existing behavior expects it.

---

## 2. Fast test suite reliability

### Required behavior

This command must complete:

```bash
uv run python -m pytest -m "not slow"
```

It should not hang on depth-heavy integration tests.

### Strategy

For each slow/hanging non-slow test:

- either mark it `@pytest.mark.slow`,
- or rewrite it into a bounded fast unit/regression test.

Known candidates to inspect:

```text
tests/test_ai_repetition_integration.py::test_repetition_sensitive_position_counts_change_root_choice
tests/test_ai_strategy15_regressions.py::TestQuiescenceDepth::test_quiescence_resolves_capture_chain
```

Also search for other depth-3+ engine tests that call `get_best_move()` without being marked slow.

### Rule of thumb

Fast tests should avoid:

- expensive depth-3 full-engine integration searches,
- unbounded repetition-sensitive root searches,
- positions with many legal moves at depth 3+,
- tests that depend on search strength rather than a narrow invariant.

Use slow tests for expensive engine-strength regressions.

### Tests

No special test needed beyond the validation command. The proof is that the fast suite completes.

---

## 3. Safe TT mate-score handling

### Background

The previous agreed decision was not to implement full TT mate-score normalization in this patch.

Therefore, until normalization is implemented, the engine must avoid corrupting mate distances through TT storage/retrieval.

### Required behavior

Add helper:

```python
def _is_mate_score(score: int) -> bool:
    return abs(score) >= MATE_SCORE - MATE_SCORE_MARGIN
```

Use a small margin large enough to cover ply adjustments. Example:

```python
MATE_SCORE_MARGIN = 1_000
```

Then choose one safe behavior.

Preferred for this patch:

```python
def _store_tt_cache(..., score: int, ...):
    if _is_mate_score(score):
        return
    ...
```

Alternative acceptable behavior:

- allow storage,
- but never allow TT cutoff/use for mate scores unless normalized.

The preferred version is simpler: **do not store mate scores in TT**.

### Required comment

Keep a clear TODO:

```python
# TODO: Implement mate-score normalization on TT store/retrieve.
# Until then, mate scores are not stored in TT because mate distance is ply-relative.
```

### Tests

Add tests proving:

1. `_is_mate_score(MATE_SCORE)` is true.
2. `_is_mate_score(MATE_SCORE - 1)` is true.
3. A normal evaluation score is false.
4. `_store_tt_cache()` skips mate scores.
5. `_store_tt_cache()` still stores normal scores.

---

## 4. Terminal and draw handling

### Required behavior

The centralized terminal helper should cover every draw state already exposed by the board/game-state API.

At minimum, include support for:

- checkmate,
- stalemate,
- fifty-move rule,
- seventy-five move rule if available,
- insufficient material,
- dead position if available,
- fivefold repetition if available,
- repetition draw if already represented by search context/position counts.

### Quiescence

At the top of quiescence, call the terminal helper where possible.

Important nuance: quiescence check-evasion behavior remains correct:

- if side to move is in check and there are no legal evasions, return ply-adjusted mate score,
- if side to move is in check and legal evasions exist, search all legal evasions,
- no stand-pat in check.

### Tests

Add or strengthen tests for:

1. checkmate terminal score,
2. stalemate draw score,
3. fifty-move rule draw,
4. insufficient-material draw,
5. seventy-five move rule if API supports it,
6. dead position if API supports it,
7. fivefold repetition if API supports it,
8. quiescence returns draw score for terminal draw states where applicable.

If constructing some states is awkward, add targeted helper-level tests using existing board APIs.

---

## 5. Seed and randomness behavior

### Required behavior

If `BestMoveOptions.rng_seed` is provided, the seed must affect all random choices in `get_best_move()`, including opening-book randomness.

Current bug: seed is applied after opening-book selection.

### Minimal fix

Move seed setup before opening-book lookup:

```python
if options.rng_seed is not None:
    random.seed(options.rng_seed)

if options.use_opening_book:
    ...
```

### Better fix

Prefer a local RNG object:

```python
rng = random.Random(options.rng_seed) if options.rng_seed is not None else random
```

Then pass `rng` into code paths that need randomness.

If opening-book API cannot accept an RNG yet, either:

- add an RNG parameter to opening-book random selection, or
- use the minimal global-seed fix and document it.

### Tests

Add tests proving:

1. Seeded random opening-book selection is reproducible.
2. Different seeds can produce different book move sequences when multiple book moves exist.
3. `CollectionOptions(seed=...)` produces reproducible collected positions/outcomes in a mocked or small deterministic collection test.

---

## 6. Texel loss test strengthening

### Current status

`LossOptions` exists, but tests are weak around score perspective and quiescence/static behavior.

### Required behavior

Do not add a sign flip unless the current evaluator is side-to-move-relative. In the latest code, the evaluator appears to be documented as White-relative. Lock this down with tests.

### Tests

Add tests proving:

1. `_score_position()` returns a positive score when White has a clear material advantage.
2. `_score_position()` returns a negative score when Black has a clear material advantage.
3. The sign is independent of side to move for equivalent material positions.
4. Static loss mode works.
5. Quiescence loss mode works with a shallow bounded depth.
6. Non-default `k` affects the computed loss.
7. Existing `mean_squared_error(..., k=...)` compatibility still works.

### Optional improvement

Add `quiescence_node_limit: int | None` to `LossOptions` if it can be implemented cleanly. If not, explicitly document that quiescence is bounded by depth only in this patch.

---

## 7. Texel validation metrics

### Required behavior

Add `baseline_score_rate`.

Current desired model:

```python
@property
def tuned_score_rate(self) -> float:
    if self.total_games == 0:
        return 0.0
    return (self.tuned_wins + 0.5 * self.draws) / self.total_games

@property
def baseline_score_rate(self) -> float:
    if self.total_games == 0:
        return 0.0
    return (self.baseline_wins + 0.5 * self.draws) / self.total_games
```

### Reporting

Update CLI/reporting to show score rate, not only win rate.

Example:

```text
Validation: tuned score rate 62.5%, tuned win rate 40.0%, draw rate 45.0%
```

Acceptance logic should prefer score rate over pure win rate when deciding whether a validation result is favorable.

### Tests

Add tests for:

1. all tuned wins,
2. all baseline wins,
3. all draws,
4. mixed wins/draws/losses,
5. zero games,
6. color alternation does not misattribute wins.

---

## 8. Online learning guardrail

### Required configuration

Extend `OnlineLearningConfig` with:

```python
require_validation_improvement: bool = True
min_validation_mse_improvement: float = 0.0
keep_rejected_candidate: bool = False
validation_fraction: float = 0.20
validation_seed: int = 0
```

If a current constant exists for validation fraction/seed, move it into config.

### Required behavior

Online learning flow:

```text
record game positions
if enough positions:
    split PositionDB into train/validation using config
    if validation set too small and require_validation_improvement:
        do not promote active weights
    train candidate weights on train split
    compare baseline/candidate on validation split
    accept only if:
        candidate_val_mse <= baseline_val_mse - min_validation_mse_improvement
    if accepted:
        backup current active weights
        atomically promote candidate
        invalidate cache
    if rejected:
        preserve active weights
        optionally keep rejected candidate if configured
```

### Candidate file behavior

Preferred behavior:

- Write candidate to `weights.candidate.json`.
- If accepted:
  - copy active weights to `weights.previous.json`,
  - atomically replace active weights with candidate,
  - remove candidate unless configured otherwise.
- If rejected:
  - active weights unchanged,
  - remove candidate unless `keep_rejected_candidate=True`.

If the implementation keeps candidates only in memory, document that explicitly and still satisfy the acceptance/rejection tests.

### Tests

Add tests proving:

1. Candidate accepted when validation improves enough.
2. Candidate rejected when validation worsens.
3. Candidate rejected when improvement is smaller than `min_validation_mse_improvement`.
4. Current weights are preserved on rejection.
5. Backup is created on acceptance when existing active weights exist.
6. Cache invalidates only after accepted promotion.
7. Candidate file behavior respects `keep_rejected_candidate`.
8. If validation data is too small and `require_validation_improvement=True`, active weights are not overwritten.
9. If unsafe promotion is explicitly allowed, behavior is explicit and tested.

---

## 9. PositionDB tests and comments

### Required behavior

Implementation already mostly supports aggregated `PositionStats`. Strengthen tests and fix stale comments.

### Tests

Add or update tests for:

1. Duplicate FEN aggregation:
   - add same FEN with 1.0, 0.5, 0.0,
   - verify `count == 3`,
   - verify `total == 1.5`,
   - verify `mean == 0.5`.

2. Old JSONL load:
   - file lines like `{"pos": "...", "outcome": 1.0}`,
   - verify converted to `PositionStats(total=1.0, count=1)`.

3. Old JSONL duplicate aggregation:
   - duplicate old-format lines,
   - verify aggregation.

4. New JSONL load:
   - file lines like `{"pos": "...", "total": 3.0, "count": 4}`,
   - verify loaded directly.

5. New JSONL round trip:
   - save DB,
   - load DB,
   - verify stats preserved.

6. Empty database:
   - verify length/export behavior.

### Comments

Remove or update any stale comment saying “last outcome wins.” New behavior is aggregate/mean outcome.

---

## 10. Collection tests and behavior

### Required behavior

Collection behavior should be testable without running expensive full self-play.

Add fast unit tests using monkeypatching/mocking where appropriate.

### Tests

Add tests for:

1. `CollectionOptions.weights` is passed to `BestMoveOptions`.
2. Draw outcomes are stored as `0.5`.
3. Max-move result `"draw"` stores 0.5.
4. Max-move result `"discard"` stores no positions.
5. Invalid `max_move_result` raises `ValueError` or is rejected early.
6. `CollectionOptions(seed=...)` is reproducible.
7. No assertion like `assert len(db) >= 0` remains.

### Behavior

Validate `max_move_result`:

```python
if options.max_move_result not in {"draw", "discard"}:
    raise ValueError("max_move_result must be 'draw' or 'discard'")
```

---

## 11. Perft coverage

### Required behavior

Start-position perft should remain:

```text
depth 1 = 20
depth 2 = 400
depth 3 = 8902
depth 4 = 197281  # slow
```

Add at least a small fast subset of special perft positions, preferably from known standard perft suites.

Minimum special cases to cover in this patch:

1. castling,
2. en passant,
3. promotion,
4. check evasions.

If adding all seven special categories is too much for this patch, document the remaining deferred categories:

- pins,
- discovered checks,
- complex castling/en passant combinations.

### Tests

Use shallow depths for fast tests.

Mark expensive depths slow.

---

## 12. Documentation corrections

### Required fixes

Correct documentation that says the transposition table is Zobrist-keyed.

Use one of:

```text
position-keyed transposition table
```

or:

```text
string-keyed transposition table using the current position_key() representation
```

Add note:

```text
Future work: replace string position keys with true Zobrist hashing.
```

### Documentation updates

Update:

```text
docs/ENGINE_SEARCH_NOTES.md
docs/TEXEL_TUNING.md
README.md
```

as needed.

Include:

- fast test command,
- slow test command,
- deterministic search mode behavior,
- online-learning validation gate behavior,
- current TT mate-score limitation,
- future TT mate-score normalization TODO,
- future Zobrist hashing TODO.

---

# Validation commands

Claude Code must run these before declaring completion:

```bash
uv run python -m ruff check chess_game tests
uv run python -m mypy chess_game
uv run python -m pylint chess_game/texel --score=y
uv run python -m pytest -m "not slow"
```

Then run targeted tests:

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

Run slow tests separately:

```bash
uv run python -m pytest -m slow
```

If slow tests are too slow for normal development, document which tests are slow and why.

---

# Acceptance criteria

This patch is complete only when all of the following are true:

1. `deterministic=True` no longer crashes.
2. Deterministic mode returns stable repeated results.
3. `uv run python -m pytest -m "not slow"` completes.
4. Known unmarked slow tests are marked slow or rewritten.
5. TT mate scores are not stored/used unsafely.
6. Mate-score TT normalization remains documented as future work.
7. Terminal/draw helper covers all draw states exposed by current board APIs where practical.
8. Quiescence uses terminal/draw handling where practical and still does not stand pat in check.
9. `rng_seed` affects opening-book randomness.
10. Texel loss tests prove score perspective and non-default `k` behavior.
11. `ValidationResult` includes both `tuned_score_rate` and `baseline_score_rate`.
12. Validation/reporting uses draw-aware score rate.
13. Online learning has configurable validation gate options.
14. Online learning tests cover accept/reject/backup/cache/candidate behavior.
15. PositionDB tests verify old/new JSONL and duplicate aggregation.
16. Collection tests verify weights, draws, max-move behavior, seed reproducibility, and invalid options.
17. At least basic special perft positions are added or explicitly deferred with rationale.
18. Docs no longer claim the TT is Zobrist-keyed.
19. Ruff passes.
20. Mypy passes.
21. Pylint for `chess_game/texel` passes or remains acceptably high.
22. Slow tests are clearly isolated from the fast suite.

---

# Notes for Claude Code

## Avoid broad rewrites

Do not refactor the entire search engine. This is a focused fix patch.

## Prefer direct regression tests

For every bug fixed, add a small direct test. Avoid adding expensive depth-heavy tests to the fast suite.

## Keep compatibility

Do not break existing CLI commands or saved PositionDB files.

## Be precise with terminology

Do not call the current TT Zobrist-keyed unless true Zobrist hashing is implemented.

## Keep future work explicit

Future work should include:

- make/unmake search,
- true Zobrist hashing,
- TT mate-score normalization,
- broader special-position perft suite,
- possible `ai.py` decomposition.
