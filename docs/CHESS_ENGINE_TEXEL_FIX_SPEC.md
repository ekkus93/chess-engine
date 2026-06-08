# CHESS_ENGINE_TEXEL_FIX_SPEC.md

## Purpose

This document specifies a focused correctness and reliability patch for the chess engine, with special attention to the engine's Texel-inspired tuning subsystem.

The goal is **not** to rewrite the entire engine. The goal is to fix concrete correctness bugs, remove drift between tested helper code and production code, make Texel tuning statistically more valid, and make the test suite reliable enough for routine development.

The implementation should prioritize:

1. Search correctness.
2. Quiescence search correctness.
3. Texel tuning correctness.
4. Test reliability and determinism.
5. Safe integration with existing architecture.

A future make/unmake board refactor is important, but it should be treated as a later architectural milestone unless explicitly requested.

---

## Current high-level issues

The current codebase is well structured and has strong tests, but the review found several important problems:

1. Production quiescence search is incorrect/incomplete.
2. Production quiescence uses a different tactical-move selector than the tested helper code.
3. Production quiescence ignores pawn captures and other important low-value tactical captures.
4. Quiescence appears to allow stand-pat evaluation while the side to move is in check.
5. Some full non-slow tests are too slow to run routinely.
6. At least one test has a vacuous assertion.
7. Texel loss uses raw static evaluation rather than quiescence-stabilized evaluation.
8. Calibrated Texel sigmoid `k` is reported but not actually used by SPSA optimization.
9. PositionDatabase overwrites duplicate positions instead of preserving outcome statistics.
10. CollectionOptions.weights exists but is not used during game collection.
11. Texel data collection drops or under-represents draw outcomes.
12. Online learning can promote new weights without a validation guardrail.
13. Validation reports win rate in a way that ignores draws as half-points.
14. Search terminal scoring should be centralized and should include draw states.
15. Mate scores should be distance-adjusted.
16. Search/tuning should be reproducible by default when tests require determinism.

---

## Scope

### In scope

This patch should implement:

- Correct production quiescence behavior.
- Unification of production and helper quiescence move selection.
- Tests that cover production behavior, not only helper behavior.
- Marking or redesigning slow tests.
- Removing vacuous assertions.
- Improved terminal/draw/mate scoring in search.
- Texel tuning fixes:
  - use calibrated `k` during optimization,
  - add optional quiescence-based Texel loss,
  - preserve duplicate position outcomes,
  - use configured weights in collection,
  - preserve draw outcomes,
  - report draw-aware validation score,
  - add validation gating for online learning.
- Reproducibility controls for tests and tuning.
- Documentation updates for the Texel subsystem.

### Out of scope for this patch

Do **not** rewrite the engine around make/unmake search in this patch.

Do **not** replace the board representation with bitboards in this patch.

Do **not** attempt to implement a full NNUE-style evaluator in this patch.

Do **not** remove existing public APIs unless absolutely necessary.

Do **not** perform broad stylistic refactors unrelated to correctness or Texel tuning validity.

---

## Implementation principles

### Keep the patch reviewable

Prefer small, targeted changes. Avoid touching unrelated files.

### Prefer production-path tests

If a helper has tests but production code does not use the helper, the tests are insufficient. Production search behavior must be tested through either public APIs or the actual production private functions when necessary.

### Avoid duplicated logic

If quiescence tactical move selection exists in a helper module, production search should use that helper. There should not be two divergent implementations of "interesting tactical move" selection.

### Determinism by default in tests

Any search/tuning behavior that uses randomness must support a seed or deterministic mode.

### Tune safely

Tuned weights should not be promoted automatically unless they pass a validation gate.

### Preserve backwards compatibility

Existing saved weights and position databases should continue to load where practical. If a storage format changes, provide migration support or backwards-compatible parsing.

---

# Part 1: Production quiescence search

## Current problem

Production `_quiescence()` in `chess_game/chess/ai.py` starts with a static stand-pat evaluation and then searches tactical moves. This is only valid when the side to move is **not** in check.

If the side to move is in check, stand-pat is illegal because the player cannot pass while in check. In that situation, quiescence must search legal check evasions or return mate if no evasions exist.

Production quiescence also appears to use its own private tactical-move selection path rather than the tested `ai_quiescence_helpers.py` selector. The production selector filters out captures below bishop value and captures where the captured value is below the attacker value. That excludes pawn captures and many tactically important recaptures.

## Required behavior

### When side to move is in check

Quiescence must:

1. Generate legal check evasions.
2. If there are no legal moves, return a ply-adjusted mate score.
3. Search legal evasions.
4. Not use stand-pat before escaping check.

Conceptual pseudocode:

```python
def _quiescence(board, alpha, beta, context, ply):
    if board.is_in_check(board.turn):
        legal_moves = board.get_legal_moves()
        if not legal_moves:
            return -MATE_SCORE + ply

        best = -INF
        for move in ordered_evasions:
            child = simulate_move(board, move)
            score = -_quiescence(child, -beta, -alpha, context, ply + 1)
            best = max(best, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        return alpha

    stand_pat = evaluate_board(...)
    ...
```

If the engine does not use negamax internally for this function, adapt the signs to the existing minimax convention. The essential rule is: **no stand-pat while in check**.

### When side to move is not in check

Quiescence may use stand-pat:

1. Evaluate static position.
2. If stand-pat >= beta, return beta or stand-pat according to existing fail-hard/fail-soft convention.
3. If stand-pat > alpha, update alpha.
4. Generate tactical moves.
5. Search tactical moves with alpha-beta.
6. Return alpha/best score.

### Tactical move generation

Production quiescence must use the same move-selection logic tested in `chess_game/chess/ai_quiescence_helpers.py`.

If the helper is insufficient, improve the helper and keep production using it.

Tactical moves should include at least:

- Captures.
- Promotions.
- Useful checking moves if the existing helper already supports or can safely support them.
- Pawn captures when tactically relevant.
- Recaptures and low-value captures when SEE or simpler heuristics indicate they should be searched.

Do not exclude all pawn captures.

### Capture filtering

If filtering is needed for performance, use a less brittle approach:

- Include all promotions.
- Include all captures when quiescence depth is small.
- Optionally use static exchange evaluation if available.
- If no SEE exists, use conservative MVV/LVA or "capture value plus promotion/check" logic.
- Do not require captured piece value to be at least bishop value.
- Do not automatically reject a capture merely because captured value < attacker value; recaptures and tactical sequences can still matter.

### Quiescence depth/node guard

Quiescence can explode in tactical positions. Ensure existing limits remain or add safe guards:

- Max quiescence ply.
- Node budget if the search has one.
- Stop flag support if available.
- Move ordering to search forcing moves first.

---

# Part 2: Terminal, draw, and mate scoring

## Current problem

Search terminal scoring appears to handle checkmate/stalemate but not all draw states consistently. Mate scores also appear not to be distance-adjusted.

## Required behavior

Create or improve a centralized search terminal helper.

Example:

```python
def _terminal_score(board: Board, ply: int) -> int | None:
    if board.is_checkmate():
        return -MATE_SCORE + ply
    if board.is_stalemate():
        return DRAW_SCORE
    if board.is_draw_by_repetition():
        return DRAW_SCORE
    if board.is_draw_by_fifty_move_rule():
        return DRAW_SCORE
    if board.has_insufficient_material():
        return DRAW_SCORE
    return None
```

Adapt method names to the actual board API.

Use this helper consistently in:

- Main search.
- Quiescence search.
- Root search where appropriate.

## Mate score requirements

Use mate-distance-aware scores:

- Winning mate sooner should score higher.
- Losing mate later should score higher than losing mate sooner.

Typical convention:

```python
MATE_SCORE = 100_000
mated_score = -MATE_SCORE + ply
mating_score = MATE_SCORE - ply
```

Make sure transposition table storage/retrieval does not break mate distance if TT stores scores across different plies. If current TT does not normalize mate scores, either:

1. Implement mate-score normalization, or
2. Avoid storing/checking mate scores in a way that corrupts distances, and add a TODO comment for a later TT normalization patch.

Do not silently introduce incorrect mate-score reuse.

---

# Part 3: Transposition table and search determinism

## Required behavior

### Preserve TT flag semantics

Existing TT flags should remain:

- EXACT
- LOWERBOUND
- UPPERBOUND

Ensure changes to terminal scoring and quiescence do not break TT storage.

### Deterministic tie-breaking

Search currently appears to use random tie-breaking in at least some situations.

For tests and tuning, add deterministic behavior.

Recommended option:

```python
@dataclass
class BestMoveOptions:
    ...
    rng_seed: int | None = None
    deterministic: bool = False
```

Behavior:

- If `deterministic=True`, tie-breaking should be stable.
- If `rng_seed` is provided, tie-breaking should be reproducible.
- If neither is provided, casual play may keep existing random behavior if desired.

Tests should use deterministic mode.

### Avoid random behavior in Texel validation unless seeded

Validation matches and tuning data collection must accept a seed.

---

# Part 4: Test reliability

## Current problem

At least one non-slow test behaves like a slow integration test and can exceed 120 seconds. There is also at least one vacuous assertion like:

```python
assert quiet_cycle_penalty(...) > 0 or True
```

## Required behavior

### Mark slow tests

Any search-depth test that can exceed a few seconds must be marked:

```python
@pytest.mark.slow
```

Routine test command:

```bash
uv run python -m pytest -m "not slow"
```

must complete quickly and reliably.

### Remove vacuous assertions

Replace assertions like:

```python
assert something or True
```

with meaningful assertions.

If the behavior is not currently guaranteed, either:

1. Rewrite the test to assert the actual intended invariant, or
2. Delete the test.

### Add production quiescence tests

Add tests that prove:

1. Quiescence does not stand pat in check.
2. Quiescence searches legal evasions while in check.
3. Quiescence recognizes checkmate at quiescence boundary.
4. Production quiescence includes pawn captures when relevant.
5. Production `get_best_move()` behavior benefits from the corrected quiescence path in at least one simple tactical position.

Where possible, use public API-level tests. If testing private `_quiescence()` is necessary, keep tests narrow and clearly named.

### Add draw terminal tests for search

Add tests that prove search returns draw score or draw behavior for:

- Stalemate.
- Repetition.
- Fifty-move rule if board API supports it.
- Insufficient material.

### Add mate-distance tests

Add tests that prove the engine prefers mate in 1 over mate in 2/3 when both are available.

---

# Part 5: Texel loss function

## Current problem

`texel/loss.py` uses raw static evaluation:

```python
score = evaluate(board, weights)
predicted = sigmoid(score, k)
```

Classic Texel tuning normally uses a quiescence-stabilized score. Static eval is noisy in tactical positions and can teach bad weights.

## Required behavior

Add configurable evaluation mode for Texel loss.

Recommended API:

```python
@dataclass(frozen=True)
class LossOptions:
    k: float = DEFAULT_K
    use_quiescence: bool = True
    quiescence_depth_limit: int = 8
    quiescence_node_limit: int | None = None
    deterministic: bool = True
```

Update:

```python
mean_squared_error(pairs, weights, *, options: LossOptions | None = None, k: float | None = None)
```

Maintain backwards compatibility if existing tests call `mean_squared_error(pairs, weights, k=...)`.

### Evaluation modes

Support:

1. Static evaluation mode.
2. Quiescence evaluation mode.

Static mode is faster and useful for unit tests.

Quiescence mode is preferred for real tuning.

### Do not accidentally run full search

Texel loss should not call full iterative deepening search for each position. That would be far too slow. It should call static eval or a bounded quiescence eval.

### Sign convention

Ensure the score used by sigmoid is from White's perspective if labels are from White's perspective, or from side-to-move perspective only if labels are transformed accordingly.

This is important.

If `evaluate_board()` returns side-to-move-relative scores, convert to White-relative scores before comparing to outcomes:

```python
score = evaluate_board(board, weights)
if board.turn == "black":
    score = -score
```

Adapt to existing color representation.

Tests should verify this convention.

---

# Part 6: Calibrated `k` must be used by SPSA

## Current problem

`tune.py` calibrates `k`, reports MSE using calibrated `k`, but `spsa.optimize()` appears to call `mean_squared_error()` without passing that calibrated `k`. This means the optimizer and reporting use different losses.

## Required behavior

The optimizer must optimize the same loss that is reported.

Recommended implementation:

### Option A: Pass a loss function

```python
def optimize(initial_weights, pairs, options, loss_fn):
    ...
    loss_plus = loss_fn(batch, weights_plus)
    loss_minus = loss_fn(batch, weights_minus)
```

Then `tune.py` creates:

```python
loss_options = LossOptions(k=calibrated_k, use_quiescence=...)
loss_fn = lambda batch, weights: mean_squared_error(batch, weights, options=loss_options)
```

### Option B: Add loss options to SPSAOptions

```python
@dataclass
class SPSAOptions:
    ...
    loss_options: LossOptions = field(default_factory=LossOptions)
```

Then use those options inside `spsa.optimize()`.

Option A is more flexible and easier to test.

## Tests

Add a test where:

1. A non-default `k` is supplied.
2. The optimizer/loss function receives that exact `k`.
3. Initial/final MSE are computed with the same options used by optimization.

---

# Part 7: Position database statistics

## Current problem

`PositionDatabase` stores a mapping like:

```python
dict[str, float]
```

Duplicate FEN positions overwrite prior outcomes.

That loses information and can bias training.

## Required behavior

Store aggregate statistics per FEN.

Recommended model:

```python
@dataclass
class PositionStats:
    total: float = 0.0
    count: int = 0

    def add(self, outcome: float) -> None:
        self.total += outcome
        self.count += 1

    @property
    def mean(self) -> float:
        return self.total / self.count if self.count else 0.5
```

PositionDatabase should support:

- Adding a single FEN/outcome.
- Adding many positions/outcomes.
- Exporting pairs as `(fen, mean_outcome)` by default.
- Optionally exporting repeated weighted pairs if desired.
- Saving/loading the new format.
- Loading the old format for backwards compatibility.

### Backwards-compatible loading

If existing JSON is:

```json
{
  "fen1": 1.0,
  "fen2": 0.5
}
```

load as:

```python
PositionStats(total=value, count=1)
```

If new JSON is:

```json
{
  "fen1": {"total": 12.5, "count": 20}
}
```

load directly.

### Tests

Add tests for:

1. Duplicate FEN aggregation.
2. Mean outcome calculation.
3. Old-format loading.
4. New-format save/load round trip.

---

# Part 8: Texel collection

## Current problem

`CollectionOptions.weights` exists but is not used when selecting moves.

The collector also appears to preserve only some terminal outcomes and may discard max-move games or fail to capture draw rules.

## Required behavior

### Use configured weights

When `_play_game()` calls `get_best_move()`, pass `options.weights` into `BestMoveOptions`.

Example:

```python
BestMoveOptions(
    weights=options.weights,
    use_opening_book=True,
    random_opening_book=True,
    deterministic=options.deterministic,
    rng_seed=derived_seed,
)
```

Adapt field names to existing code.

### Preserve draw outcomes

Collector should treat recognized draws as `0.5`.

Draws should include:

- Stalemate.
- Repetition.
- Fifty-move rule.
- Insufficient material.
- Other draw helpers supported by Board.

### Max-move games

Do not silently drop all max-move games.

Add explicit option:

```python
@dataclass
class CollectionOptions:
    ...
    max_move_result: Literal["draw", "discard"] = "draw"
```

Default should probably be `"draw"` for tuning stability, unless there is a strong reason to discard.

### Position filtering

For Texel tuning, avoid contaminating data with inappropriate positions.

Recommended filters:

- Skip opening-book positions if possible.
- Skip checkmate positions.
- Skip positions with mate-score labels if full search is used elsewhere.
- Optionally skip positions before a configurable ply threshold.
- Optionally skip positions where side to move is in check if quiescence behavior is not yet robust.

At minimum, make the filtering behavior explicit and tested.

### Seeding

Collection should support a seed so games are reproducible:

```python
CollectionOptions(seed: int | None = None)
```

Random opening book choices and tie-breaking should derive from this seed.

---

# Part 9: Texel validation

## Current problem

Validation win rate appears to count only wins divided by total games. Draws should contribute half-points for engine comparison.

## Required behavior

Keep existing win/draw/loss fields, but add score-rate reporting:

```python
score_rate = (tuned_wins + 0.5 * draws) / total_games
baseline_score_rate = (baseline_wins + 0.5 * draws) / total_games
```

If validation alternates colors, make sure wins are counted from the tuned engine's perspective, not from White's perspective.

### Add confidence information if practical

Optional but useful:

- Elo difference estimate.
- Standard error.
- Number of games.
- Draw rate.

Do not block this patch on Elo math.

### Tests

Add tests for:

- All wins.
- All losses.
- All draws.
- Mixed wins/draws/losses.
- Color alternation if supported.

---

# Part 10: Online learning guardrail

## Current problem

Online learning can save tuned weights after a small SPSA update without a sufficient validation gate.

## Required behavior

Online learning should produce candidate weights first.

Recommended flow:

```text
record completed game
if enough positions:
    load current weights as baseline
    run bounded SPSA update to produce candidate
    evaluate baseline and candidate on validation set
    if candidate passes acceptance criteria:
        save/promote candidate
    else:
        discard candidate
```

### Acceptance criteria

Add configurable criteria:

```python
@dataclass
class OnlineLearningOptions:
    ...
    min_validation_mse_improvement: float = 0.0
    require_validation_improvement: bool = True
    keep_rejected_candidate: bool = False
```

Candidate is accepted if:

```python
candidate_validation_mse <= baseline_validation_mse - min_validation_mse_improvement
```

If no validation set exists, online learning should either:

1. Not promote automatically, or
2. Promote only if an explicit unsafe option is enabled.

Default should be safe.

### Rollback

When promoting weights:

- Keep previous weights as backup.
- Save candidate to a temporary file first.
- Use atomic replace where possible.

Suggested files:

```text
weights.json
weights.previous.json
weights.candidate.json
```

### Tests

Add tests for:

1. Candidate accepted when validation improves.
2. Candidate rejected when validation worsens.
3. Existing weights preserved when candidate rejected.
4. Backup created when candidate accepted.
5. Cache invalidated only after accepted promotion.

---

# Part 11: Perft and move-generation confidence

## Current status

If robust perft tests already exist, keep and possibly expand them. If not, add them.

## Required behavior

Add or confirm perft tests for standard known positions.

Minimum:

```text
startpos depth 1 = 20
startpos depth 2 = 400
startpos depth 3 = 8902
```

If depth 4 is too slow for the current board implementation, mark depth 4 as slow:

```text
startpos depth 4 = 197281
```

Add special positions covering:

- Castling.
- En passant.
- Promotion.
- Checks.
- Pins.
- Discovered checks.
- Check evasions.

Perft should use legal move generation and should not involve evaluation/search.

---

# Part 12: Documentation updates

Update or add documentation explaining:

1. How to run fast tests.
2. How to run slow tests.
3. How Texel tuning works in this project.
4. Difference between static Texel loss and quiescence Texel loss.
5. How validation gates online learning.
6. How to reproduce tuning runs with seeds.
7. Known future performance work: make/unmake search.

Recommended file updates:

```text
README.md
docs/TEXEL_TUNING.md
docs/ENGINE_SEARCH_NOTES.md
```

If docs directory does not exist, create it.

---

# Validation commands

Claude Code should run these before considering the patch complete:

```bash
uv run python -m ruff check chess_game tests
uv run python -m mypy chess_game
uv run python -m pylint chess_game/texel --score=y
uv run python -m pytest -m "not slow"
```

Also run targeted tests:

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

If new tests are added in dedicated files, include them:

```bash
uv run python -m pytest \
  tests/test_ai_quiescence_production.py \
  tests/test_search_terminal_scores.py \
  tests/test_texel_loss_quiescence.py \
  tests/test_texel_collection.py \
  -q
```

Slow tests should be run separately:

```bash
uv run python -m pytest -m slow
```

---

# Acceptance criteria

The patch is complete when:

1. Fast tests complete reliably.
2. Ruff passes.
3. Mypy passes.
4. Pylint for `chess_game/texel` remains clean or acceptably high.
5. Production quiescence no longer stands pat in check.
6. Production quiescence uses the tested tactical move selector.
7. Pawn captures are not globally excluded from quiescence.
8. Terminal search scoring includes draw states.
9. Mate scores are distance-aware.
10. Texel SPSA uses the calibrated `k`.
11. Texel loss supports quiescence-based scoring.
12. PositionDatabase preserves duplicate position statistics.
13. CollectionOptions.weights is actually used.
14. Draw outcomes are preserved by collection.
15. Validation reports draw-aware score rate.
16. Online learning does not automatically promote worse weights by default.
17. Slow tests are marked slow.
18. Vacuous assertions are removed.
19. Documentation describes the new Texel tuning behavior.

---

# Future work, not part of this patch

The next major engine-strength/performance milestone should be:

## Make/unmake search refactor

Current clone-per-node search is simple but slow. A future patch should introduce:

```python
undo = board.make_search_move(move)
score = search(...)
board.unmake_search_move(move, undo)
```

This will require careful handling of:

- Captured pieces.
- Castling rights.
- En passant target.
- Halfmove clock.
- Fullmove number.
- Move history.
- Position history.
- Hashing if/when Zobrist is added.
- Evaluation cache invalidation.

This should be its own spec/TODO because it is large and high-risk.

## Zobrist hashing

If the engine does not already use true Zobrist hashing, add it in a future patch for:

- Faster transposition table keys.
- Repetition detection.
- Opening book lookups.
- Position database deduplication.

## Pseudo-legal move generation

For speed, future search code should use pseudo-legal generation plus legality filtering instead of repeatedly generating fully legal moves where unnecessary.

## Bitboards

A bitboard board representation would improve speed but is a large rewrite. Do not combine it with this patch.

