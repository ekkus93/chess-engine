# CHESS_ENGINE_AI_TT_REPAIR_TODO.md

## Goal

Repair the chess engine AI search implementation so minimax, alpha-beta pruning, transposition table lookup/storage, promotion-aware move identity, and self-play promotion formatting are correct.

This is a focused AI/search correctness pass. Do not broaden this into evaluator tuning or unrelated engine refactoring.

---

## Implementation rules

- Treat `CHESS_ENGINE_AI_TT_REPAIR_SPEC.md` as the authoritative contract.
- Keep the existing legal move API stable unless a test forces a small compatibility change.
- Do not change the canonical coordinate system.
- Do not tune the board evaluator in this pass.
- Do not add opening books, iterative deepening, quiescence search, UCI, GUI work, or time controls.
- Preserve promotion identity everywhere a move is stored, ordered, cached, or compared.
- Add tests before or alongside fixes.
- After each major task group, run:

  ```bash
  python -m pytest tests -q
  ```

---

# Task 0: Establish baseline and add repair docs

## 0.1 Run baseline tests

- [ ] From repo root, run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Expected latest reviewed baseline:

  ```text
  314 passed
  ```

- [ ] If there are failures before starting, stop and inspect them first.

## 0.2 Create a focused branch

- [ ] Create a branch such as:

  ```bash
  git checkout -b fix/ai-minimax-alpha-beta-tt
  ```

- [ ] If the project workflow is currently direct-on-master, keep the patch small and clearly scoped.

## 0.3 Add handoff docs

- [ ] Copy the spec into:

  ```text
  docs/CHESS_ENGINE_AI_TT_REPAIR_SPEC.md
  ```

- [ ] Copy this TODO into:

  ```text
  docs/CHESS_ENGINE_AI_TT_REPAIR_TODO.md
  ```

---

# Task 1: Inspect current AI/search implementation

## 1.1 Read current AI code

- [ ] Inspect:

  ```text
  chess_game/chess/ai.py
  ```

- [ ] Locate:
  - [ ] `get_best_move`
  - [ ] `minimax`
  - [ ] `_order_moves`
  - [ ] `MoveOrderingKey`
  - [ ] `_fen_key` or equivalent TT key generator
  - [ ] transposition table usage
  - [ ] any duplicate/dead aliases such as duplicate `LegalMoveKey`

## 1.2 Read self-play code

- [ ] Inspect:

  ```text
  chess_game/self_play.py
  ```

- [ ] Locate:
  - [ ] depth argument handling,
  - [ ] `_move_to_algebraic` or equivalent,
  - [ ] promotion suffix formatting.

## 1.3 Confirm current known issues

- [ ] Confirm `minimax()` checks `depth == 0` before terminal/no-legal-move handling.
- [ ] Confirm leaf scores are clamped to alpha/beta.
- [ ] Confirm TT entries lack exact/lower/upper bound flags.
- [ ] Confirm any move matching by `(start, end)` only.
- [ ] Confirm self-play promotion formatting does not use `PieceType` keys directly.

---

# Task 2: Add mate-at-horizon regression tests

Create or update a test file, for example:

```text
tests/test_ai_search.py
```

Use existing test helpers such as:

```python
sq("e4")
assert_piece(...)
assert_empty(...)
```

## 2.1 Add move string helper

- [ ] Add a local helper if not already available:

  ```python
  from chess_game.chess.coords import index_to_algebraic

  def move_to_str(move):
      start, end, promotion = move
      suffix = "" if promotion is None else promotion.name[0].lower()
      return index_to_algebraic(start) + index_to_algebraic(end) + suffix
  ```

- [ ] Adjust to the repo's actual move representation if needed.

## 2.2 Mate-in-one at depth 1

- [ ] Construct this position:

  ```text
  White king: g6
  White queen: f7
  Black king: h8
  White to move
  ```

  Example:

  ```python
  board = Board()
  board.clear_board()
  board.set_piece(sq("g6"), create_piece(Color.WHITE, PieceType.KING))
  board.set_piece(sq("f7"), create_piece(Color.WHITE, PieceType.QUEEN))
  board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
  board.turn = Color.WHITE
  ```

- [ ] Call:

  ```python
  move = get_best_move(board, depth=1)
  ```

- [ ] Assert the move is one of the actual checkmating moves.

  Acceptable expected moves include the set discovered from current legal move generation if they truly leave Black checkmated. Likely examples:

  ```text
  f7f8
  f7g7
  f7h7
  f7e8
  ```

- [ ] After applying the chosen move to a clone, assert:

  ```python
  clone.is_checkmate(Color.BLACK) is True
  ```

  or use the repo's current public/private checkmate method.

## 2.3 Black mate-in-one at depth 1

- [ ] Add a symmetric or equivalent black-to-move mate-in-one position.
- [ ] Assert `get_best_move(board, depth=1)` returns a move that checkmates White.

## 2.4 Ensure old bad move is not selected

- [ ] For the white mate-in-one position, assert the AI does **not** choose a non-mating queen move such as `f7f4` if that remains legal.

---

# Task 3: Fix minimax terminal handling

## 3.1 Reorder minimax checks

- [ ] In `minimax()`, move terminal no-legal-move detection before the `depth == 0` leaf cutoff.

Required structure:

```python
legal_moves = get_legal_moves(board)

if not legal_moves:
    if board.is_in_check(board.turn):
        return mate_score_for_side_to_move(...), None
    return 0, None

if depth == 0:
    return evaluate(board), None
```

- [ ] Use the repo's actual helper names for check detection. If only `_is_in_check` exists, use the current project style consistently.

## 3.2 Add mate score constants

- [ ] Add:

  ```python
  MATE_SCORE = 100_000
  ```

- [ ] If practical, add ply-distance adjustment:
  - [ ] faster mate preferred,
  - [ ] slower loss preferred.

Example:

```python
if board.turn == Color.WHITE:
    return -MATE_SCORE + ply_from_root, None
return MATE_SCORE - ply_from_root, None
```

- [ ] If adding `ply_from_root` is too invasive, use plain `MATE_SCORE`/`-MATE_SCORE` for this pass and document the simplification.

## 3.3 Preserve evaluation perspective

- [ ] Ensure positive score still means good for White.
- [ ] Ensure White maximizes and Black minimizes.

## 3.4 Run tests

- [ ] Run:

  ```bash
  python -m pytest tests/test_ai_search.py -q
  ```

- [ ] Run full suite:

  ```bash
  python -m pytest tests -q
  ```

---

# Task 4: Fix leaf evaluation behavior

## 4.1 Remove leaf score clamping

- [ ] Find code similar to:

  ```python
  return (
      max(params.alpha, min(score, params.beta))
      if params.is_maximizing
      else min(params.beta, max(score, params.alpha)),
      None,
  )
  ```

- [ ] Replace it with:

  ```python
  return evaluate(board), None
  ```

  or equivalent using the existing `score` variable.

## 4.2 Add regression test for raw leaf score

- [ ] Add a test that calls `minimax()` directly if existing tests already inspect it.
- [ ] Construct a board with a known nonzero evaluation.
- [ ] Call `minimax()` at depth 0 with a narrow alpha/beta window that does not contain the raw score.
- [ ] Assert returned score equals `evaluate(board)`, not alpha or beta.

Example intent:

```python
raw = evaluate(board)
score, _ = minimax(board, depth=0, alpha=-1, beta=1, ...)
assert score == raw
```

- [ ] Adjust for the current `minimax()` signature.

---

# Task 5: Implement TT data structures

## 5.1 Add TT flag enum

- [ ] In `chess_game/chess/ai.py` or a small AI support module, add:

  ```python
  from enum import Enum

  class TTFlag(Enum):
      EXACT = "exact"
      LOWERBOUND = "lowerbound"
      UPPERBOUND = "upperbound"
  ```

## 5.2 Add TT entry dataclass

- [ ] Add:

  ```python
  @dataclass(frozen=True)
  class TTEntry:
      depth: int
      score: int
      best_move: LegalMove | None
      flag: TTFlag
  ```

- [ ] If Python version requires `Optional[LegalMove]`, use that style.

## 5.3 Define TT table type alias

- [ ] Add a type alias such as:

  ```python
  TranspositionTable = dict[str, TTEntry]
  ```

- [ ] Use the actual key type if not string.

## 5.4 Preserve promotion in stored moves

- [ ] Ensure `best_move` is the full legal move object/tuple including promotion.
- [ ] Do not store only `(start, end)`.

---

# Task 6: Verify and harden TT key generation

## 6.1 Inspect current key

- [ ] Inspect `_fen_key(board)` or equivalent.
- [ ] Confirm it includes:
  - [ ] board placement,
  - [ ] side to move,
  - [ ] castling rights,
  - [ ] en passant target.

## 6.2 Add key tests

- [ ] Add tests proving TT keys differ when only side to move differs.
- [ ] Add tests proving TT keys differ when castling rights differ.
- [ ] Add tests proving TT keys differ when en passant target differs.
- [ ] Add tests proving TT keys differ when board placement differs.

## 6.3 Rename if needed

- [ ] If `_fen_key()` is not a valid full FEN string, either:
  - [ ] keep the private name if existing tests expect it, or
  - [ ] rename to `_position_key()` and update callers.
- [ ] Do not spend time on full FEN compliance unless already trivial.

---

# Task 7: Implement TT lookup semantics

## 7.1 Save alpha/beta originals

- [ ] At each `minimax()` node before TT lookup/search:

  ```python
  alpha_orig = alpha
  beta_orig = beta
  ```

- [ ] Adapt to current parameter object if alpha/beta live in `SearchParams`.

## 7.2 Lookup only sufficiently deep entries

- [ ] On lookup:

  ```python
  entry = transposition_table.get(key)
  if entry is not None and entry.depth >= depth:
      ...
  ```

- [ ] Ignore shallower entries for direct reuse.

## 7.3 Apply TT flag semantics

- [ ] Implement:

  ```python
  if entry.flag == TTFlag.EXACT:
      return entry.score, entry.best_move

  if entry.flag == TTFlag.LOWERBOUND:
      alpha = max(alpha, entry.score)
  elif entry.flag == TTFlag.UPPERBOUND:
      beta = min(beta, entry.score)

  if alpha >= beta:
      return entry.score, entry.best_move
  ```

- [ ] Ensure LOWERBOUND/UPPERBOUND entries do not get returned as exact unless they cause cutoff.

## 7.4 Add TT lookup tests

- [ ] Add focused tests for:
  - [ ] exact entry reuse,
  - [ ] lower-bound entry raising alpha,
  - [ ] upper-bound entry lowering beta,
  - [ ] shallow entry ignored when depth is insufficient.

Testing private internals is acceptable if there is no clean public hook.

---

# Task 8: Implement TT store semantics

## 8.1 Determine flag after search

- [ ] After a node is searched, compute flag using original alpha/beta:

  ```python
  if best_score <= alpha_orig:
      flag = TTFlag.UPPERBOUND
  elif best_score >= beta_orig:
      flag = TTFlag.LOWERBOUND
  else:
      flag = TTFlag.EXACT
  ```

- [ ] Use `beta_orig`, not a mutated beta.

## 8.2 Store entry

- [ ] Store:

  ```python
  TTEntry(
      depth=depth,
      score=best_score,
      best_move=best_move,
      flag=flag,
  )
  ```

## 8.3 Replacement policy

- [ ] Only overwrite existing entry if:
  - [ ] no entry exists, or
  - [ ] new depth is greater than or equal to old depth.

## 8.4 Do not store invalid moves

- [ ] If `best_move` is not `None`, it must be a legal move from the current position and include promotion identity.
- [ ] Never store a `(start, end)` pair without promotion.

## 8.5 Add TT store tests

- [ ] Add tests proving:
  - [ ] exact entries are stored with `TTFlag.EXACT`,
  - [ ] cutoff entries are stored as lower/upper bound as appropriate,
  - [ ] deeper entries replace shallower entries,
  - [ ] shallower entries do not replace deeper entries.

---

# Task 9: Preserve promotion identity in search and TT

## 9.1 Inspect move ordering key

- [ ] Confirm `MoveOrderingKey` includes:

  ```python
  promotion: PieceType | None
  ```

- [ ] If not, add it.

## 9.2 Ordered move creation

- [ ] When creating ordered move keys, include `move.promotion`.

## 9.3 Ordered move matching

- [ ] When matching an ordered key back to a legal move, match all three:

  ```python
  m.start == move_key.start
  and m.end == move_key.end
  and m.promotion == move_key.promotion
  ```

## 9.4 TT best move preservation

- [ ] Ensure TT stores the full legal move with promotion.
- [ ] Ensure TT returns the same promotion value.

## 9.5 Add promotion identity tests

- [ ] Construct a position with a pawn promotion where all four promotions are legal.
- [ ] Assert `_order_moves()` returns distinct entries for:
  - [ ] queen promotion,
  - [ ] rook promotion,
  - [ ] bishop promotion,
  - [ ] knight promotion.

- [ ] Add a TT test where the stored/returned best move is an underpromotion, such as rook or knight, and verify promotion identity is preserved.

---

# Task 10: Clean move ordering

## 10.1 Fix promotion bonus logic

- [ ] Replace any logic that treats rank-1/rank-8 moves as promotion.

Bad pattern:

```python
promoted_to = end.row in (ROW_1, ROW_8) and board.get_piece(start) is not None
```

- [ ] Use:

  ```python
  if move.promotion is not None:
      ...
  ```

## 10.2 Prefer higher-value promotions

- [ ] Use a small ordering bonus by promotion piece:

  ```python
  PROMOTION_ORDER_BONUS = {
      PieceType.QUEEN: 900,
      PieceType.ROOK: 500,
      PieceType.BISHOP: 330,
      PieceType.KNIGHT: 320,
  }
  ```

- [ ] This is move ordering only, not board evaluation tuning.

## 10.3 Remove duplicate/dead code

- [ ] Remove duplicate aliases such as repeated `LegalMoveKey`.
- [ ] Remove unused `_promotion_bonus()` if it has no callers.
- [ ] Remove dead `if not scored_moves:` branch if truly unreachable.

## 10.4 Run tests

- [ ] Run AI tests and full suite.

---

# Task 11: Validate search depth

## 11.1 Add `get_best_move` depth guard

- [ ] In `get_best_move(board, depth)`, add:

  ```python
  if depth < 1:
      raise ValueError("depth must be >= 1")
  ```

## 11.2 Add tests

- [ ] Assert `get_best_move(board, depth=0)` raises `ValueError`.
- [ ] Assert `get_best_move(board, depth=-1)` raises `ValueError`.

## 11.3 Update self-play depth handling

- [ ] In `self_play.py`, reject invalid depth values before search starts.
- [ ] If using argparse, enforce `depth >= 1` after parsing and raise/exit with a clear message.

## 11.4 Add self-play depth test if practical

- [ ] If self-play has testable argument parsing, add a test for invalid depth.
- [ ] If not practical, document manual verification.

---

# Task 12: Fix self-play promotion formatting

## 12.1 Replace string-based promotion suffix logic

- [ ] Find code similar to:

  ```python
  promo_key = str(promotion).lower()
  base += promo_map.get(promo_key, "q")
  ```

- [ ] Replace with:

  ```python
  PROMOTION_SUFFIXES = {
      PieceType.QUEEN: "q",
      PieceType.ROOK: "r",
      PieceType.BISHOP: "b",
      PieceType.KNIGHT: "n",
  }

  if promotion is not None:
      base += PROMOTION_SUFFIXES[promotion]
  ```

## 12.2 Add tests

- [ ] Test `_move_to_algebraic((sq("e7"), sq("e8"), PieceType.QUEEN)) == "e7e8q"`.
- [ ] Test rook promotion suffix `"r"`.
- [ ] Test bishop promotion suffix `"b"`.
- [ ] Test knight promotion suffix `"n"`.
- [ ] Test no suffix when promotion is `None`.

---

# Task 13: Add public AI behavior tests

## 13.1 Stalemate returns no move

- [ ] Construct known stalemate:

  ```text
  Black king: h8
  White king: f7
  White queen: g6
  Black to move
  ```

- [ ] Assert:

  ```python
  get_best_move(board, depth=1) is None
  ```

## 13.2 Checkmate side to move returns no move

- [ ] Construct known checkmate:

  ```text
  Black king: h8
  White king: f6
  White queen: g7
  Black to move
  ```

- [ ] Assert:

  ```python
  get_best_move(board, depth=1) is None
  ```

## 13.3 AI does not mutate original board

- [ ] Construct a normal legal position.
- [ ] Save board representation/key before search.
- [ ] Call `get_best_move(board, depth=2)`.
- [ ] Assert board representation/key is unchanged.

---

# Task 14: Manual smoke script

After implementation, run or encode as tests:

```python
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq
from chess_game.chess.ai import get_best_move

board = Board()
board.clear_board()
board.set_piece(sq("g6"), create_piece(Color.WHITE, PieceType.KING))
board.set_piece(sq("f7"), create_piece(Color.WHITE, PieceType.QUEEN))
board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
board.turn = Color.WHITE

move = get_best_move(board, depth=1)
clone = board.clone()
assert move is not None
assert clone.make_move(move[0], move[1], move[2]) is True
assert clone.is_checkmate(Color.BLACK)
print("mate-in-one smoke ok")
```

- [ ] Run this manually or convert it into a test.

---

# Task 15: Final verification

## 15.1 Focused tests

- [ ] Run:

  ```bash
  python -m pytest tests/test_ai*.py -q
  ```

- [ ] Also run self-play tests if present:

  ```bash
  python -m pytest tests/test_self_play*.py -q
  ```

## 15.2 Full suite

- [ ] Run:

  ```bash
  python -m pytest tests -q
  ```

- [ ] Required result: all tests pass.

## 15.3 Manual checks

- [ ] Confirm mate-in-one is found at depth 1.
- [ ] Confirm leaf score is raw evaluation.
- [ ] Confirm TT entries include flags.
- [ ] Confirm TT lookup respects exact/lower/upper semantics.
- [ ] Confirm promotion identity is preserved in move ordering and TT.
- [ ] Confirm invalid depth raises `ValueError`.
- [ ] Confirm self-play underpromotion formatting is correct.

---

# Suggested commit breakdown

Use small, reviewable commits:

1. `test: add ai mate-at-horizon regressions`
2. `fix: check terminal states before minimax depth cutoff`
3. `fix: return raw evaluation at minimax leaves`
4. `fix: implement flagged transposition table entries`
5. `fix: preserve promotion identity in ai tt and move ordering`
6. `fix: validate search depth`
7. `fix: format self-play promotions by piece type`
8. `test: add ai tt and self-play regression coverage`

Combining test+fix commits is acceptable if that is the project workflow. Do not use one huge commit unless required.
