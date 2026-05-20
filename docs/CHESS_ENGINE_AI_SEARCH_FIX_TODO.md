# Chess Engine AI Search Fix TODO

## Goal

Fix the AI search layer so minimax, alpha-beta pruning, and the transposition table are correct and measurable.

This TODO is based on the latest diagnosis:

- Alpha-beta is not completely disabled.
- The unsafe aspiration-window implementation is causing incorrect move selection.
- Depth 5 is slow because search is expensive, not necessarily because alpha-beta never prunes.
- The transposition table needs correct keying, flag semantics, and move identity.

Do not tune the evaluator in this pass.

---

## Implementation rules

- Treat `CHESS_ENGINE_AI_SEARCH_FIX_SPEC.md` as the authoritative contract.
- Keep the existing board/rules engine behavior unchanged unless an AI test exposes a direct dependency bug.
- Keep clone-per-child search for now.
- Do not switch to undo-based search.
- Do not add quiescence search.
- Do not add UCI support.
- Do not tune material values or piece-square tables.
- Do not add new AI features beyond search correctness, TT correctness, move ordering, and instrumentation.
- Keep default unit tests fast; depth 5 belongs in benchmarks/slow tests, not normal CI.
- After each major task group, run:

  ```bash
  python -m pytest tests -q
  ```

---

# Task 0: Establish baseline

## 0.1 Run current tests

- [ ] From repo root, run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Record the current result in implementation notes.
- [ ] If the suite already fails, inspect the failures before starting.
- [ ] Do not mix pre-existing failures with this patch.

## 0.2 Create a focused branch

- [ ] Prefer:

  ```bash
  git checkout -b fix/ai-search-alpha-beta-tt
  ```

- [ ] If project workflow is currently direct-to-master, continuing on master is acceptable, but keep this patch focused.

## 0.3 Add handoff docs

- [ ] Copy this TODO to:

  ```text
  docs/CHESS_ENGINE_AI_SEARCH_FIX_TODO.md
  ```

- [ ] Copy the companion spec to:

  ```text
  docs/CHESS_ENGINE_AI_SEARCH_FIX_SPEC.md
  ```

---

# Task 1: Inspect current AI/search code

## 1.1 Inspect `ai.py`

- [ ] Open:

  ```text
  chess_game/chess/ai.py
  ```

- [ ] Locate:
  - [ ] `get_best_move(...)`
  - [ ] `minimax(...)`
  - [ ] `_search_move_loop(...)`
  - [ ] `_position_key(...)` or `_fen_key(...)`
  - [ ] `TTEntry`
  - [ ] `TTFlag`
  - [ ] `MoveOrderingKey`
  - [ ] `_order_moves(...)`

## 1.2 Inspect self-play code

- [ ] Open likely file:

  ```text
  chess_game/self_play.py
  ```

  or:

  ```text
  self_play.py
  ```

- [ ] Locate:
  - [ ] depth argument parsing,
  - [ ] `--white-depth`,
  - [ ] `--black-depth`,
  - [ ] move formatting,
  - [ ] promotion suffix formatting.

## 1.3 Inspect current tests

- [ ] Open:

  ```text
  tests/test_ai_search.py
  ```

  if it exists.

- [ ] Locate any depth-5 tests.
- [ ] Locate mate-in-one tests.
- [ ] Locate TT tests.
- [ ] Locate alpha-beta node-count tests.

---

# Task 2: Remove unsafe aspiration-window behavior

## Problem

Current search likely does something equivalent to:

```python
score = 0
for d in range(1, depth + 1):
    alpha = score - 50
    beta = score + 50
    score, move = minimax(board, depth=d, alpha=alpha, beta=beta)
```

This is unsafe without fail-high/fail-low re-search. It can return a lower/upper bound as if it were an exact best move.

## Subtasks

- [ ] In `get_best_move(...)`, remove narrow alpha/beta windows.
- [ ] Use full-width bounds for each completed iterative-deepening pass:

  ```python
  INF = 10_000_000
  alpha = -INF
  beta = INF
  ```

- [ ] Keep existing iterative deepening if present:

  ```python
  best_move = None
  best_score = 0
  for current_depth in range(1, depth + 1):
      best_score, best_move = minimax(... depth=current_depth, alpha=-INF, beta=INF ...)
  return best_move
  ```

- [ ] Do not reintroduce aspiration windows in this patch.
- [ ] If aspiration-window helper constants/functions exist and are now unused, remove them.
- [ ] Add a code comment if helpful:

  ```python
  # Use full-width search for correctness. Aspiration windows require fail-high/fail-low re-search.
  ```

## Acceptance

- [ ] `get_best_move(depth=1)` must not cut off at the root simply because the first move exceeds a tiny beta window.
- [ ] Mate-in-one test in Task 7 must pass.

---

# Task 3: Fix minimax terminal handling and leaf behavior

## Problem

Terminal positions must be checked before the `depth == 0` cutoff. Otherwise checkmate at the search horizon is treated as an ordinary static evaluation.

Leaf evaluation must return raw `evaluate(board)`, not a value clamped to alpha/beta.

## Subtasks

### 3.1 Reorder terminal checks

- [ ] In `minimax(...)`, generate legal moves before the depth cutoff or otherwise detect terminal states first.
- [ ] Required flow:

  ```python
  legal_moves = get_legal_moves(board)

  if not legal_moves:
      if board._is_in_check(board.turn):
          return checkmate_score_for_side_to_move(board), None
      return 0, None

  if params.depth == 0:
      return evaluate(board), None
  ```

- [ ] Use public board methods if available. If current code uses `_is_in_check`, keep existing style unless there is a clean public alternative.

### 3.2 Use correct checkmate score sign

- [ ] Since evaluation is positive for White and negative for Black:
  - [ ] If White to move has no legal moves and is in check, return a large negative score.
  - [ ] If Black to move has no legal moves and is in check, return a large positive score.
  - [ ] If stalemate, return `0`.

Example:

```python
if board.turn == Color.WHITE:
    return -MATE_SCORE, None
return MATE_SCORE, None
```

- [ ] Optional: include depth distance to prefer faster mate. Keep it simple and documented.

### 3.3 Remove leaf score clamping

- [ ] Replace any depth-zero logic like:

  ```python
  return max(alpha, min(score, beta)), None
  ```

  with:

  ```python
  return evaluate(board), None
  ```

## Acceptance

- [ ] A mate-in-one is found at depth 1.
- [ ] A terminal checkmate node at horizon scores as mate, not as static material.
- [ ] Leaf scores are not modified by alpha/beta.

---

# Task 4: Validate search depth

## Problem

Depth less than 1 is not a useful best-move search and can cause misleading behavior or runaway recursion.

## Subtasks

- [ ] In `get_best_move(board, depth)`, add:

  ```python
  if depth < 1:
      raise ValueError("depth must be >= 1")
  ```

- [ ] If `minimax(...)` is public/internal and can receive negative depth directly, guard it too:

  ```python
  if params.depth < 0:
      raise ValueError("depth must be >= 0")
  ```

- [ ] In self-play, validate both `--white-depth` and `--black-depth`:

  ```text
  white_depth >= 1
  black_depth >= 1
  ```

- [ ] If invalid, fail fast with a clear error.

## Tests

- [ ] `get_best_move(board, depth=0)` raises `ValueError`.
- [ ] `get_best_move(board, depth=-1)` raises `ValueError`.
- [ ] Self-play argument validation rejects invalid depths if directly testable.

---

# Task 5: Repair transposition-table keying

## Problem

If the current table key appends depth, such as:

```python
key = _position_key(board) + f":d{params.depth}"
```

then deeper entries cannot be reused at shallower depths. This defeats much of the purpose of storing `depth` in `TTEntry`.

## Subtasks

- [ ] Rename `_fen_key(...)` to `_position_key(...)` if the key is not full FEN.
- [ ] Ensure key includes:
  - [ ] piece placement,
  - [ ] side to move,
  - [ ] castling rights,
  - [ ] en passant target.

- [ ] Do **not** append depth to the key.
- [ ] Store search depth only in `TTEntry.depth`.

## Tests

- [ ] Add a test that the same board position has the same `_position_key(...)` regardless of requested search depth.
- [ ] Add a test that different side-to-move values produce different keys.
- [ ] Add a test that different castling rights produce different keys if practical.
- [ ] Add a test that different en-passant targets produce different keys if practical.

---

# Task 6: Implement correct TT entry semantics

## 6.1 Define TT flag enum

- [ ] Ensure `TTFlag` exists:

  ```python
  class TTFlag(Enum):
      EXACT = "exact"
      LOWERBOUND = "lowerbound"
      UPPERBOUND = "upperbound"
  ```

## 6.2 Define TT entry

- [ ] Ensure `TTEntry` includes:

  ```python
  @dataclass(frozen=True)
  class TTEntry:
      depth: int
      score: int
      best_move: LegalMove | None
      flag: TTFlag
  ```

- [ ] If current move type is tuple-based, use the repo's actual legal move type.
- [ ] Ensure `best_move` includes promotion identity.

## 6.3 Probe semantics

- [ ] In TT lookup, ignore entries with insufficient depth:

  ```python
  if entry.depth < params.depth:
      return None
  ```

- [ ] EXACT entries may return immediately.
- [ ] LOWERBOUND entries may return only if:

  ```python
  entry.score >= beta
  ```

- [ ] UPPERBOUND entries may return only if:

  ```python
  entry.score <= alpha
  ```

- [ ] Non-cutoff LOWERBOUND/UPPERBOUND entries may be ignored in this pass.

## 6.4 Store semantics

- [ ] Preserve original alpha/beta before searching a node:

  ```python
  alpha_orig = params.alpha
  beta_orig = params.beta
  ```

- [ ] After search:

  ```python
  if best_score <= alpha_orig:
      flag = TTFlag.UPPERBOUND
  elif best_score >= beta_orig:
      flag = TTFlag.LOWERBOUND
  else:
      flag = TTFlag.EXACT
  ```

- [ ] Store exactly once per searched node.
- [ ] Remove duplicate TT stores.

## Tests

- [ ] Test EXACT entry lookup returns score/move when depth is sufficient.
- [ ] Test insufficient-depth TT entry is ignored.
- [ ] Test LOWERBOUND returns only when it cuts off.
- [ ] Test UPPERBOUND returns only when it cuts off.
- [ ] Test TT stores one entry per searched node/key, not duplicate conflicting entries.

---

# Task 7: Use TT best move for move ordering

## Problem

Even if a TT entry cannot be used directly to return a score, its stored best move can improve move ordering and pruning.

## Subtasks

- [ ] Modify `_order_moves(...)` to accept an optional TT best move.
- [ ] If the TT best move is legal in the current position, score/order it first.
- [ ] Match TT best move using:
  - [ ] start,
  - [ ] end,
  - [ ] promotion.

- [ ] Do not match by start/end only.

## Tests

- [ ] Create legal promotion moves with the same start/end and different promotion pieces.
- [ ] Store/construct a TT best move for a specific underpromotion.
- [ ] Assert `_order_moves(...)` places that exact promotion move first.
- [ ] Assert queen/rook/bishop/knight promotion identities do not collapse into one move.

---

# Task 8: Clean and improve move ordering without evaluation tuning

## Problem

Good move ordering is necessary for alpha-beta performance. This pass may improve ordering but must not change board evaluation.

## Subtasks

- [ ] Remove bogus promotion ordering based only on destination rank, such as:

  ```python
  promoted_to = end.row in (ROW_1, ROW_8)
  ```

- [ ] Use:

  ```python
  move.promotion is not None
  ```

  or equivalent tuple field.

- [ ] Order promotions by promotion piece value:
  - [ ] queen highest,
  - [ ] rook next,
  - [ ] bishop/knight lower.

- [ ] Order captures before quiet moves.
- [ ] If simple, use MVV-LVA:
  - [ ] more valuable captured piece scores higher,
  - [ ] less valuable attacking piece scores higher among equal captures.

- [ ] Preserve existing reasonable ordering heuristics if they are correct.
- [ ] Remove duplicate/dead code such as duplicate type aliases or unused `_promotion_bonus()` if present.

## Tests

- [ ] Add a small unit test for move ordering where:
  - [ ] TT best move comes first,
  - [ ] captures outrank quiet moves,
  - [ ] queen promotion outranks rook/bishop/knight promotion.

---

# Task 9: Add node-count instrumentation

## Problem

The engine needs a way to measure whether alpha-beta actually prunes compared with plain minimax.

## Subtasks

- [ ] Add a lightweight `SearchStats` dataclass, for example:

  ```python
  @dataclass
  class SearchStats:
      nodes: int = 0
      cutoffs: int = 0
      tt_hits: int = 0
  ```

- [ ] Add `stats: SearchStats | None` to `MinimaxParams` or another clean path.
- [ ] Increment `stats.nodes` once per visited node.
- [ ] Increment `stats.cutoffs` when alpha-beta breaks due to cutoff.
- [ ] Increment `stats.tt_hits` when TT lookup returns a usable entry.

## Acceptance

- [ ] Stats are optional and do not affect search behavior.
- [ ] Existing callers need not pass stats.
- [ ] Tests can pass stats to compare node counts.

---

# Task 10: Add no-prune reference minimax for tests

## Problem

Comparing wide alpha-beta to narrow alpha-beta does not prove pruning. A no-prune reference is needed for shallow tests.

## Subtasks

- [ ] Add a no-prune minimax helper in test code or a clearly test-only utility.
- [ ] It must:
  - [ ] use same terminal handling,
  - [ ] use same evaluator,
  - [ ] recurse through all legal moves,
  - [ ] not perform alpha-beta cutoffs,
  - [ ] count nodes.

- [ ] Keep depth shallow, preferably depth 2 from the starting position.
- [ ] Do not use this no-prune search in production `get_best_move()`.

## Tests

- [ ] From starting position at depth 2:

  ```text
  alpha_beta_nodes < no_prune_nodes
  ```

- [ ] Do not require exact node numbers unless they are stable.
- [ ] Avoid depth 5 in this test.

---

# Task 11: Fix mate-in-one and terminal search tests

## Required mate-in-one position

Use a simple position such as:

```text
White king: g6
White queen: f7
Black king: h8
White to move
```

## Subtasks

- [ ] Build the board with existing helpers:

  ```python
  board = Board()
  board.clear_board()
  board.set_piece(sq("g6"), create_piece(Color.WHITE, PieceType.KING))
  board.set_piece(sq("f7"), create_piece(Color.WHITE, PieceType.QUEEN))
  board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
  board.turn = Color.WHITE
  ```

- [ ] Assert `get_best_move(board, depth=1)` returns a legal move.
- [ ] Apply the returned move to a clone.
- [ ] Assert Black is checkmated after the move.

Example:

```python
move = get_best_move(board, depth=1)
assert move is not None
clone = board.clone()
assert clone.make_move(move.start, move.end, move.promotion) is True
assert clone._is_checkmate(Color.BLACK) is True
```

## Direct minimax agreement test

- [ ] Call direct minimax with full window on the same position.
- [ ] Assert direct minimax returns a checkmating move.
- [ ] Assert `get_best_move()` also returns a checkmating move.
- [ ] Do not require the exact same mate move if multiple mates exist.

## Stalemate terminal test

- [ ] Add a known stalemate position.
- [ ] Assert search returns score 0 and no move if side to move has no legal moves and is not in check.

---

# Task 12: Fix self-play promotion formatting and depth validation

## 12.1 Promotion suffix formatting

- [ ] Locate self-play move formatting helper.
- [ ] Replace any logic like:

  ```python
  promo_key = str(promotion).lower()
  ```

  with direct `PieceType` mapping:

  ```python
  promo_map = {
      PieceType.QUEEN: "q",
      PieceType.ROOK: "r",
      PieceType.BISHOP: "b",
      PieceType.KNIGHT: "n",
  }
  ```

- [ ] Assert underpromotions format correctly:
  - [ ] rook -> `r`,
  - [ ] bishop -> `b`,
  - [ ] knight -> `n`,
  - [ ] queen -> `q`.

## 12.2 Depth validation

- [ ] Keep existing `--white-depth` and `--black-depth` options.
- [ ] Validate both are `>= 1`.
- [ ] Do not replace them with a single depth option.

## Tests

- [ ] Add unit tests for self-play formatting if helper is importable.
- [ ] Add tests for invalid depth parsing/validation if practical.

---

# Task 13: Remove or quarantine unsafe undo helpers

## Problem

Current or previous code may contain unused helpers such as:

```text
apply_move_for_search
unapply_move_for_search
```

These were observed to be unsafe in earlier inspection:

- restore logic used the moved piece's current square incorrectly,
- en-passant captured key names mismatched,
- destination piece restoration was incomplete,
- promotion restoration was incomplete,
- en-passant target calculation was wrong.

## Subtasks

- [ ] Search:

  ```bash
  grep -R "apply_move_for_search\|unapply_move_for_search" -n chess_game tests
  ```

- [ ] If these functions are unused, delete them.
- [ ] If deletion is too disruptive, move them under a clearly named experimental/debug area and add comments that they are not used by current search.
- [ ] Do not switch the current search to use them.

## Acceptance

- [ ] Active AI search uses clone-per-child or the existing safe path.
- [ ] No broken undo helper is used by `get_best_move()` or `minimax()`.

---

# Task 14: Move depth-5 tests out of default fast suite

## Problem

Depth-5 tests can be too slow and brittle for ordinary unit runs.

## Subtasks

- [ ] Search for depth-5 tests:

  ```bash
  grep -R "depth=5\|depth 5\|Depth 5" -n tests
  ```

- [ ] For each depth-5 test, choose one:
  - [ ] reduce depth to 2 or 3 if it is a correctness test,
  - [ ] mark as slow with pytest marker,
  - [ ] move to a benchmark/manual test file.

- [ ] If using pytest markers, update pytest config if needed.

## Acceptance

- [ ] `python -m pytest tests -q` should not depend on depth-5 completing quickly.
- [ ] A manual/slow benchmark may still exist for depth 5.

---

# Task 15: Final verification

## 15.1 Focused AI tests

- [ ] Run:

  ```bash
  python -m pytest tests/test_ai_search.py -q
  ```

- [ ] All AI search tests pass.

## 15.2 Full suite

- [ ] Run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Full suite passes.

## 15.3 Manual smoke checks

Run or encode equivalent tests for:

- [ ] Mate-in-one found at depth 1.
- [ ] Starting position depth 2 alpha-beta visits fewer nodes than no-prune minimax.
- [ ] `get_best_move(depth=0)` raises `ValueError`.
- [ ] TT key does not include depth.
- [ ] TT best move preserves promotion identity.
- [ ] Self-play formats rook/bishop/knight promotion suffixes correctly.

---

# Task 16: Suggested commit breakdown

Use small reviewable commits:

1. `fix: remove unsafe aspiration windows from ai search`
2. `fix: handle terminal nodes before depth cutoff`
3. `fix: implement correct transposition table semantics`
4. `fix: use tt best move and promotion-aware move ordering`
5. `test: add ai search mate and pruning regressions`
6. `fix: validate search depths and self-play promotion formatting`
7. `test: move depth-five search out of fast unit suite`
8. `cleanup: remove unsafe unused undo search helpers`

If project workflow prefers fewer commits, combine tests with the corresponding fixes. Do not use one giant commit unless required.

---

# Final acceptance checklist

The patch is complete only when:

- [ ] `get_best_move()` no longer uses unsafe aspiration windows.
- [ ] Full-width alpha-beta is used by default.
- [ ] Terminal nodes are checked before `depth == 0` leaf evaluation.
- [ ] Leaf evaluation returns raw `evaluate(board)`.
- [ ] Mate-in-one is found at depth 1.
- [ ] `depth < 1` is rejected for best-move search.
- [ ] TT key excludes depth.
- [ ] TT entry stores depth.
- [ ] TT flags are correct: `EXACT`, `LOWERBOUND`, `UPPERBOUND`.
- [ ] TT stores exactly once per searched node.
- [ ] TT best move ordering uses promotion-aware identity.
- [ ] Alpha-beta pruning is measured against a no-prune reference.
- [ ] Move ordering uses TT best move, captures, and promotions without changing evaluation.
- [ ] Self-play promotion formatting uses `PieceType`, not `str(PieceType)`.
- [ ] Depth-5 tests are not part of default fast unit tests unless proven fast/stable.
- [ ] Broken unused undo helpers are removed or quarantined.
- [ ] Full suite passes:

  ```bash
  python -m pytest tests -q
  ```
