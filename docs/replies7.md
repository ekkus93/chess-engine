# replies7.md

# Replies to Claude Code questions on CHESS_ENGINE_TEXEL_FIX_SPEC.md

These are the implementation decisions and clarifications for Claude Code.

The two main architecture decisions are:

1. Use **Option A** for validation data in this patch: a deterministic held-out split from the current position database.
2. Do **not** implement full transposition-table mate-score normalization yet. Use the safer lower-risk approach for this patch.

---

# Answers for Claude Code

## Q1: Texel loss score perspective

Yes, that is exactly the bug.

If `evaluate(board, weights)` returns a **side-to-move-relative** score, but Texel labels are **White-relative**, then Black-to-move positions are currently sign-inverted for training. A positive score for Black is being interpreted as good for White.

Use this fix:

```python
score = evaluate(board, weights)

if board.turn == Color.BLACK:
    score = -score

predicted = sigmoid(score, k)
```

After this conversion, `score > 0` means “good for White,” and `score < 0` means “good for Black,” matching labels where:

```text
1.0 = White win
0.5 = draw
0.0 = Black win
```

Add a regression test with the same material imbalance in two FENs: one White-to-move and one Black-to-move. The White-relative score should have the same sign after conversion.

---

## Q2: Online learning validation data

Use **Option A for this patch**: a deterministic held-out split from the same position database.

Option B, a separate rolling validation DB, is cleaner long-term, but it is extra infrastructure. For this patch, do the simpler safe version:

```text
Position DB
    ↓ deterministic shuffle/split
80% training
20% validation
```

Requirements:

- Use a seed.
- Split by FEN, not by raw row, so duplicates do not leak between train and validation.
- Keep the validation split fixed during a single tuning run.
- Do not train SPSA on validation positions.
- Report both training MSE and validation MSE.

Suggested defaults:

```python
validation_fraction = 0.20
validation_seed = 0
min_validation_positions = 50
```

If the DB is too small to split safely, online learning should **not auto-promote** candidate weights unless an explicit unsafe override is set.

Long-term TODO: add a separate rolling validation database.

---

## Q3: Quiescence while in check

Search **all legal check evasions**.

When the side to move is in check, quiescence should not restrict itself to captures/checks. Legal evasions can be:

- king moves,
- captures of the checking piece,
- blocking moves,
- special cases such as castling not being legal out of check, etc.

So the intended behavior is:

```python
if board.is_in_check(board.turn):
    legal_moves = board.get_legal_moves()

    if not legal_moves:
        return -MATE_SCORE + ply

    for move in ordered_legal_evasions:
        search(move)
```

This is more expensive, but it is the correct behavior. A quiet blocking move can be the only legal or best evasion, so filtering to only captures/checks would be wrong.

---

## Q4: Mate-score distance and transposition table

Use **Option 2 for this patch**.

Do **not** implement full TT mate-score normalization in this patch. That is easy to get subtly wrong and should be its own focused patch.

For now:

1. Make terminal mate scores distance-aware inside search:

```python
-MATE_SCORE + ply
```

2. Avoid storing mate scores in the TT, or avoid using TT mate scores for cutoffs unless normalization is implemented.

3. Add a clear TODO comment:

```python
# TODO: Implement mate-score normalization for TT storage/retrieval.
# Mate scores are currently not stored/used from TT to avoid corrupting
# mate distance across different search plies.
```

That is lower risk and fits the current patch scope.

---

## Q5: Deterministic mode

For `deterministic=True`, use **fixed ordering**, not seeded shuffle.

Concretely:

- Do not call `random.shuffle`.
- Do not use random tie-breaking.
- Preserve generated move order, then apply deterministic ordering heuristics.
- For equal scores, break ties by a stable move key.

Example stable key:

```python
def move_sort_key(move: Move) -> tuple:
    return (
        str(move.from_square),
        str(move.to_square),
        str(move.promotion) if move.promotion else "",
    )
```

or, if moves already have a stable UCI string:

```python
move.uci()
```

Recommended behavior:

```text
deterministic=True:
    fixed order, no randomness

rng_seed is not None:
    seeded RNG allowed and reproducible

default casual mode:
    current random behavior may remain if desired
```

Tests should use `deterministic=True`, not seeded shuffle, unless the test is specifically about reproducible randomness.

---

## Q6: PositionDB format

Yes, implement backwards compatibility for the actual old format Claude found: **newline-delimited JSON**, not a single JSON object.

Old format:

```json
{"pos": "fen1", "outcome": 1.0}
{"pos": "fen2", "outcome": 0.5}
```

New preferred JSONL format:

```json
{"pos": "fen1", "total": 12.5, "count": 20}
{"pos": "fen2", "total": 3.0, "count": 4}
```

Backwards-compatible loader should accept:

```python
{"pos": fen, "outcome": outcome}
```

and convert it to:

```python
PositionStats(total=outcome, count=1)
```

If easy, the loader may also support the object-map format from the spec, but the required compatibility target is the existing JSONL format.

When duplicate old-format lines appear, aggregate them:

```python
stats[fen].total += outcome
stats[fen].count += 1
```

---

## Q7: Perft depth 4

Mark depth 4 as `@pytest.mark.slow`.

Do not omit it entirely. It is useful as a correctness check, but it should not be part of the fast suite while the engine still uses clone-per-move board simulation.

Use:

```python
@pytest.mark.slow
def test_startpos_perft_depth4():
    assert perft(Board.starting_position(), 4) == 197281
```

Fast suite should include:

```text
depth 1 = 20
depth 2 = 400
depth 3 = 8902
```

Depth 4 belongs in:

```bash
uv run python -m pytest -m slow
```

---

## Q8: Online learning validation gate for CLI `--learn`

Yes, the validation gate should apply to **all code paths that promote/save learned weights**, including CLI batch runs.

The rule should be:

```text
No candidate weights become active weights unless they pass validation.
```

For this patch, use the same **Option A held-out validation split** from Q2.

However, do not necessarily validate and promote after every single game if that is too slow. Better behavior:

```text
--learn records games/positions
candidate update is generated when threshold is reached
candidate is validated before promotion
only accepted candidates replace active weights
```

If the current architecture triggers SPSA after each game, it can still validate after each game for now, but the implementation should make promotion cadence configurable.

Suggested CLI/config options:

```text
--learn
--learn-promote-every N
--validation-fraction 0.20
--validation-seed 0
--unsafe-promote-without-validation false
```

Default behavior should be safe:

```text
require validation improvement = true
unsafe promotion = false
```

If there are not enough validation positions, save candidate weights separately or discard them, but do not overwrite active weights.

---

# Final implementation decisions

| Question | Decision |
|---|---|
| Q1 score perspective | Confirmed bug. Convert side-to-move score to White-relative before sigmoid. |
| Q2 validation data | Use deterministic 80/20 held-out split from current PositionDB for this patch. |
| Q3 quiescence in check | Search all legal check evasions. No stand-pat. |
| Q4 TT mate scores | Use safer Option 2: do not store/use mate scores in TT until normalization is implemented. |
| Q5 deterministic mode | Fixed stable ordering; no shuffle; stable tie-break key. |
| Q6 PositionDB format | Existing format is JSONL. Implement old JSONL → aggregate stats migration. |
| Q7 perft depth 4 | Keep it, but mark it slow. |
| Q8 CLI `--learn` | Validation gate applies to all weight promotion paths, including CLI batch learning. |

The most important instruction: **candidate weights should never replace active weights by default unless validation MSE improves.**
