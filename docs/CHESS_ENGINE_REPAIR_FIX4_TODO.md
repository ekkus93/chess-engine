# Chess Engine Repair Fix 4 TODO

## Goal

Fix the remaining confirmed promotion correctness issues in the chess engine.

The current engine has a passing suite and most core rules are repaired, but promotion handling is incomplete:

- `get_legal_moves()` emits only queen promotions.
- Non-pawn moves with promotion suffixes are accepted and the suffix is silently ignored.
- Raw integer promotion values can be accepted and stored as `Piece.kind`.
- AI move ordering/search does not preserve promotion identity when multiple moves share the same start and end square.

This TODO is intentionally focused. Do not broaden this pass into unrelated AI improvements, GUI work, UCI support, or a large move-classification refactor.

---

## Implementation rules

- Treat `CHESS_ENGINE_REPAIR_FIX4_SPEC.md` as the authoritative contract.
- Keep the canonical coordinate system unchanged:
  - `row 0 = rank 8`
  - `row 7 = rank 1`
- Use algebraic test helpers such as `sq("e7")`.
- Do not use raw row/column constants in new tests unless testing coordinate internals.
- Add regression tests before or alongside fixes.
- Do not weaken existing tests.
- Do not remove valid underpromotion support.
- Do not add new features outside promotion correctness.
- After each task group, run:

  ```bash
  python -m pytest tests -q
  ```

---

## Task 0: Establish baseline

### 0.1 Run the current test suite

- [ ] From repo root, run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Confirm the current baseline is passing.

Expected from the latest reviewed repo:

```text
195 passed
```

- [ ] If there are existing failures before making changes, stop and inspect them before starting Fix 4.

### 0.2 Create a repair branch

- [ ] Create a focused branch, for example:

  ```bash
  git checkout -b fix/promotion-move-generation-and-validation
  ```

### 0.3 Add this handoff documentation

- [ ] Copy the spec into:

  ```text
  docs/CHESS_ENGINE_REPAIR_FIX4_SPEC.md
  ```

- [ ] Copy this TODO into:

  ```text
  docs/CHESS_ENGINE_REPAIR_FIX4_TODO.md
  ```

---

## Task 1: Inspect current promotion code paths

### 1.1 Locate promotion validation

- [ ] Inspect the promotion validator module.

Likely file:

```text
chess_game/chess/board/promotion.py
```

- [ ] Identify the method that validates promotion choices.
- [ ] Confirm whether it currently returns `True` for non-pawn pieces with non-`None` promotion values.
- [ ] Confirm whether it currently accepts raw integers because `PieceType` is an `IntEnum`.

### 1.2 Locate legal move generation

- [ ] Inspect move validation/legal move generation.

Likely files:

```text
chess_game/chess/board/move_validation.py
chess_game/chess/board/board.py
```

- [ ] Find the code path that converts pseudo-legal pawn destinations into legal move tuples.
- [ ] Find the helper currently hardcoding queen promotion.

Known suspicious pattern:

```python
if piece.color == Color.WHITE and int(to_square.row) == 0:
    return PieceType.QUEEN
if piece.color == Color.BLACK and int(to_square.row) == 7:
    return PieceType.QUEEN
```

- [ ] Confirm that `get_legal_moves()` emits only queen promotions.

### 1.3 Locate move execution promotion handling

- [ ] Inspect move execution.

Likely file:

```text
chess_game/chess/board/move_execution.py
```

- [ ] Confirm that explicit valid underpromotion execution already works or identify what must be changed.
- [ ] Confirm that execution never stores raw integers or strings as `Piece.kind` after Fix 4.

### 1.4 Locate AI move ordering/search identity

- [ ] Inspect AI code.

Likely file:

```text
chess_game/chess/ai.py
```

- [ ] Find any move ordering key or helper that stores only:
  - `start`
  - `end`

- [ ] Find any search loop that matches ordered moves back to legal moves using only:
  - `start`
  - `end`

- [ ] Mark all places that must include `promotion`.

---

## Task 2: Add promotion move-generation regression tests

Create or update a promotion-focused test file, for example:

```text
tests/test_promotion_move_generation.py
```

Use existing helpers:

```python
sq("e7")
assert_piece(...)
assert_empty(...)
```

If helper names differ, use the existing test-suite style.

### 2.1 Add helper for promotion move extraction

- [ ] Add a local test helper or shared helper that extracts moves by start/end:

  ```python
  def promotions_for(board, start: str, end: str) -> set[PieceType]:
      return {
          promotion
          for move_start, move_end, promotion in board.get_legal_moves()
          if move_start == sq(start) and move_end == sq(end)
      }
  ```

- [ ] Adjust to match the repo's actual legal move tuple/object shape.

### 2.2 White quiet promotion generation

- [ ] Construct a legal position with:
  - White king present.
  - Black king present.
  - White pawn on `e7`.
  - `e8` empty.
  - White to move.

- [ ] Assert legal moves for `e7 -> e8` include exactly:

  ```python
  {
      PieceType.QUEEN,
      PieceType.ROOK,
      PieceType.BISHOP,
      PieceType.KNIGHT,
  }
  ```

- [ ] Assert no invalid promotion pieces appear.

### 2.3 White capture promotion generation

- [ ] Construct a legal position with:
  - White king present.
  - Black king present.
  - White pawn on `e7`.
  - Black piece on `d8` or `f8`.
  - White to move.

- [ ] Assert legal moves for the capture promotion include exactly:

  ```python
  {
      PieceType.QUEEN,
      PieceType.ROOK,
      PieceType.BISHOP,
      PieceType.KNIGHT,
  }
  ```

### 2.4 Black quiet promotion generation

- [ ] Construct a legal position with:
  - White king present.
  - Black king present.
  - Black pawn on `e2`.
  - `e1` empty.
  - Black to move.

- [ ] Assert legal moves for `e2 -> e1` include exactly four promotion choices:
  - queen
  - rook
  - bishop
  - knight

### 2.5 Black capture promotion generation

- [ ] Construct a legal position with:
  - White king present.
  - Black king present.
  - Black pawn on `e2`.
  - White piece on `d1` or `f1`.
  - Black to move.

- [ ] Assert legal moves for the capture promotion include exactly four promotion choices:
  - queen
  - rook
  - bishop
  - knight

### 2.6 No duplicate identical promotion moves

- [ ] Add a test that legal promotion moves do not contain duplicate identical `(start, end, promotion)` entries.

---

## Task 3: Fix legal move generation for all promotion choices

### 3.1 Add canonical promotion choice constant/helper

- [ ] Add or reuse a single canonical allowed-promotion set/list:

  ```python
  PROMOTION_PIECES = (
      PieceType.QUEEN,
      PieceType.ROOK,
      PieceType.BISHOP,
      PieceType.KNIGHT,
  )
  ```

- [ ] Put it in the most appropriate existing module.
- [ ] Avoid duplicating promotion piece lists across multiple modules if practical.

### 3.2 Add helper to detect promotion rank

- [ ] Add or reuse a helper:

  ```python
  def is_promotion_rank(piece: Piece, to_square: ConstantSquare) -> bool:
      if piece.kind != PieceType.PAWN:
          return False
      if piece.color == Color.WHITE:
          return int(to_square.row) == 0
      return int(to_square.row) == 7
  ```

- [ ] Ensure it follows the canonical coordinate system.

### 3.3 Generate four legal moves for promotion destinations

- [ ] In the legal move generation path, when:
  - the moving piece is a pawn,
  - the pseudo-legal destination is a promotion rank,
  - the move is legal after king-safety validation,

  append one legal move per allowed promotion piece.

- [ ] For a legal quiet promotion, generate:

  ```text
  e7e8q
  e7e8r
  e7e8b
  e7e8n
  ```

- [ ] For a legal capture promotion, generate all four capture-promotion alternatives.

- [ ] Do this for both White and Black.

### 3.4 Preserve default queen behavior for direct `make_move(..., promotion=None)`

- [ ] Confirm that direct move execution still promotes to queen by default when a pawn legally reaches promotion rank with `promotion=None`.
- [ ] Do not let default queen behavior affect legal move generation completeness.

### 3.5 Run tests

- [ ] Run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Confirm the new promotion move-generation tests pass.

---

## Task 4: Add promotion input-validation regression tests

Create or update a test file, for example:

```text
tests/test_promotion_validation.py
```

### 4.1 Non-pawn promotion suffix rejected

- [ ] Add tests proving these parsed moves are rejected:

  ```text
  g1f3q
  a1a2q
  e1e2q
  ```

- [ ] For each:
  - Set up a legal position if the starting position blocks the move.
  - Call `board.make_move(move.start, move.end, move.promotion)`.
  - Assert it returns `False`.
  - Assert the piece did not move.
  - Assert `board.turn` did not change.

### 4.2 Pawn promotion suffix on wrong rank rejected

- [ ] Add tests proving these are rejected:

  ```text
  e2e4q
  e7e5q
  ```

- [ ] Assert no board mutation.
- [ ] Assert no turn flip.

### 4.3 Raw integer promotion rejected

- [ ] Construct a legal white promotion position.
- [ ] Call:

  ```python
  board.make_move(sq("e7"), sq("e8"), promotion=5)
  ```

- [ ] Assert the move returns `False`.
- [ ] Assert the pawn remains on `e7`.
- [ ] Assert `e8` remains empty.
- [ ] Assert turn does not change.

### 4.4 Raw string promotion rejected

- [ ] Construct a legal white promotion position.
- [ ] Call:

  ```python
  board.make_move(sq("e7"), sq("e8"), promotion="q")
  ```

- [ ] Assert the move returns `False`.
- [ ] Assert no mutation.

### 4.5 Invalid `PieceType` promotions rejected

- [ ] Construct legal promotion positions.
- [ ] Assert these return `False`:

  ```python
  promotion=PieceType.KING
  promotion=PieceType.PAWN
  promotion=PieceType.EMPTY
  ```

- [ ] Assert no mutation and no turn flip.

### 4.6 Valid underpromotion still accepted

- [ ] Add or verify tests for:

  ```python
  promotion=PieceType.ROOK
  promotion=PieceType.BISHOP
  promotion=PieceType.KNIGHT
  promotion=PieceType.QUEEN
  ```

- [ ] Assert the resulting piece has the exact requested `PieceType`.

---

## Task 5: Fix promotion validation

### 5.1 Reject non-`PieceType` promotion values

- [ ] In the promotion validation path, if `promotion is not None`, require:

  ```python
  isinstance(promotion, PieceType)
  ```

- [ ] Reject raw integers, strings, and arbitrary objects.

Important: if `PieceType` is an `IntEnum`, do not rely only on membership checks.

### 5.2 Reject invalid `PieceType` promotion values

- [ ] If `promotion is not None`, require it to be in the allowed promotion set:

  ```python
  {
      PieceType.QUEEN,
      PieceType.ROOK,
      PieceType.BISHOP,
      PieceType.KNIGHT,
  }
  ```

- [ ] Reject:
  - `PieceType.KING`
  - `PieceType.PAWN`
  - `PieceType.EMPTY`

### 5.3 Reject promotion on non-pawn moves

- [ ] If `promotion is not None`, require the moving piece to be a pawn.
- [ ] If the moving piece is not a pawn, return `False`.
- [ ] Do not move the piece.
- [ ] Do not flip turn.

### 5.4 Reject promotion on wrong-rank pawn moves

- [ ] If `promotion is not None`, require destination to be the correct promotion rank:
  - White: row `0`.
  - Black: row `7`.

- [ ] If destination is not a promotion rank, return `False`.
- [ ] Do not move the pawn.
- [ ] Do not flip turn.

### 5.5 Ensure default queen promotion remains valid

- [ ] If `promotion is None` and a pawn legally reaches promotion rank, allow default queen promotion.
- [ ] If `promotion is None` and a pawn does not reach promotion rank, execute normal pawn move.
- [ ] If `promotion is None` and a non-pawn moves, execute normal non-pawn move.

### 5.6 Ensure board cannot store raw promotion values

- [ ] Inspect promotion execution.
- [ ] Make sure promoted piece construction receives only valid `PieceType` values.
- [ ] Add a defensive assertion or validation if appropriate.

### 5.7 Run tests

- [ ] Run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Confirm all promotion validation tests pass.

---

## Task 6: Update AI move identity to include promotion

### 6.1 Inspect current AI move-ordering key

- [ ] Find `MoveOrderingKey` or equivalent.
- [ ] If it currently stores only:

  ```python
  score
  start
  end
  ```

  update it to also store:

  ```python
  promotion: Optional[PieceType]
  ```

### 6.2 Update ordered move creation

- [ ] Wherever ordered move keys are created from legal moves, include the legal move's promotion value.

Example target structure:

```python
MoveOrderingKey(
    score=score,
    start=start,
    end=end,
    promotion=promotion,
)
```

### 6.3 Update ordered move matching

- [ ] Wherever the AI maps an ordered move key back to an actual legal move, match:

  ```python
  m.start == move_key.start
  m.end == move_key.end
  m.promotion == move_key.promotion
  ```

  or the equivalent tuple fields.

- [ ] Do not match only start/end.

### 6.4 Update search recursion if needed

- [ ] Search all AI code for assumptions that `(start, end)` uniquely identifies a move.
- [ ] Update those assumptions to include `promotion`.

Useful searches:

```bash
grep -R "start ==.*end ==" -n chess_game/chess
grep -R "MoveOrderingKey" -n chess_game/chess
grep -R "promotion" -n chess_game/chess/ai.py
```

### 6.5 Add AI regression test

- [ ] Create a position where a side has multiple legal promotion moves with the same start and end.
- [ ] Verify the AI move ordering/search preserves distinct promotion entries.
- [ ] At minimum, test that `_order_moves()` or equivalent returns keys containing distinct promotion values.
- [ ] If testing private methods is discouraged in the repo, test through the public AI move-selection API and assert it returns a legal move whose promotion field is preserved.

### 6.6 Run tests

- [ ] Run:

  ```bash
  python -m pytest tests -q
  ```

---

## Task 7: Add optional targeted promotion perft/regression test

This task is optional but recommended if the repo has or can easily support a tiny move-count helper.

### 7.1 Add a tiny legal-node counter

- [ ] Add a test-local helper, not necessarily production code:

  ```python
  def count_legal_moves(board: Board) -> int:
      return len(board.get_legal_moves())
  ```

- [ ] Do not add a full perft framework unless it already exists.

### 7.2 Add a promotion multiplicity position

- [ ] Create a position where one side has multiple promotion destinations.
- [ ] Assert that each promotion destination contributes four legal moves, not one.

Example expectation:

```text
one quiet promotion destination = 4 legal moves
one capture promotion destination = 4 legal moves
two promotion destinations = 8 legal moves
```

### 7.3 Avoid brittle full-position counts unless verified

- [ ] Prefer targeted promotion counts over a large full-position perft number unless you cross-check the expected count carefully.
- [ ] Do not paste a large perft expected value without verifying it.

---

## Task 8: Documentation updates

### 8.1 Update docs if promotion behavior is documented

- [ ] Search for promotion docs:

  ```bash
  grep -R "promotion\|promote\|underpromotion" -n README.md docs tests chess_game
  ```

- [ ] Update relevant docs to state:
  - Legal promotion choices are queen, rook, bishop, knight.
  - Default promotion is queen when direct API call omits promotion on a legal promotion move.
  - CLI suffixes are `q`, `r`, `b`, `n`.
  - Promotion suffixes are valid only for pawn moves ending on the promotion rank.

### 8.2 Do not over-document internals

- [ ] Keep docs concise.
- [ ] Do not document private AI implementation details unless an existing architecture doc requires it.

---

## Task 9: Final acceptance checks

### 9.1 Full test suite

- [ ] Run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Required result: all tests pass.

Expected count after this patch should be at least:

```text
195 passed
```

plus newly added tests.

### 9.2 Manual smoke checks

Run a short script or equivalent tests that prove:

- [ ] White quiet promotion legal moves include `q/r/b/n`.
- [ ] Black quiet promotion legal moves include `q/r/b/n`.
- [ ] White capture promotion legal moves include `q/r/b/n`.
- [ ] Black capture promotion legal moves include `q/r/b/n`.
- [ ] `g1f3q` is rejected.
- [ ] `e2e4q` is rejected.
- [ ] `promotion=5` is rejected.
- [ ] `promotion="q"` is rejected.
- [ ] `promotion=PieceType.KING` is rejected.
- [ ] Valid rook/bishop/knight underpromotion still works.
- [ ] AI ordered moves preserve promotion value.

### 9.3 Mutation safety checklist

For each rejected invalid promotion case, confirm:

- [ ] Source piece remains on source square.
- [ ] Destination square remains unchanged.
- [ ] Captured pieces are not removed.
- [ ] Turn does not change.
- [ ] Castling rights do not change.
- [ ] En passant target does not change unexpectedly.

### 9.4 Search for raw promotion leakage

- [ ] Run a quick search or test to ensure no promoted piece has non-`PieceType` kind.
- [ ] Add a defensive test if practical.

---

## Suggested commit breakdown

Use small commits that isolate behavior:

1. `test: add promotion move generation regressions`
2. `fix: generate all legal promotion choices`
3. `test: add invalid promotion input regressions`
4. `fix: harden promotion validation`
5. `fix: preserve promotion identity in ai move ordering`
6. `docs: document fix4 promotion behavior`

If preferred, combine each test commit with its corresponding fix:

1. `fix: generate all legal promotion choices`
2. `fix: harden promotion validation`
3. `fix: preserve promotion identity in ai move ordering`
4. `docs: document promotion behavior`

Do not use one giant commit unless the project workflow requires it.

---

## Final note for implementation agent

This patch is about promotion correctness only.

Do not change unrelated chess rules unless a promotion test exposes a direct dependency.

Do not introduce new AI quality tuning.

Do not refactor the whole move engine.

A successful patch should be small, easy to review, and covered by targeted tests.
