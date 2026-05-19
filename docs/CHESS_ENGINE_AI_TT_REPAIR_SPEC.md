# CHESS_ENGINE_AI_TT_REPAIR_SPEC.md

## Purpose

This spec defines the required repair for the chess engine AI search layer.

The core chess rules engine is now in relatively good shape. The current focus is **not** to rewrite move generation or tune chess evaluation. The current focus is to make the AI search mechanically correct:

- minimax terminal handling,
- alpha-beta pruning behavior,
- transposition table correctness,
- promotion-aware move identity,
- depth validation,
- self-play promotion formatting.

Copilot must treat this document as the authoritative contract for the AI/TT repair pass.

---

## Scope

### In scope

Implement and verify:

1. Correct minimax terminal handling.
2. Correct alpha-beta leaf handling.
3. Full transposition table support with exact/lower/upper bound flags.
4. Promotion-aware best-move identity in move ordering and TT entries.
5. Search-depth validation.
6. Self-play promotion suffix formatting.
7. Focused regression tests for search correctness.

### Out of scope

Do **not** do any of the following in this pass unless a required test exposes a direct dependency:

- Do not tune the evaluator.
- Do not add opening books.
- Do not add iterative deepening.
- Do not add quiescence search.
- Do not add time controls.
- Do not add UCI/XBoard protocol.
- Do not change legal move generation semantics except where needed to preserve move identity.
- Do not refactor the whole move engine.
- Do not alter the canonical coordinate system.

Evaluation improvements can come later. First make minimax, alpha-beta, and TT correctness solid.

---

## Current known problem summary

The current AI layer has several search-correctness issues:

1. `minimax()` checks `depth == 0` before checking for checkmate/stalemate.
   - This causes mate-at-horizon failures.
   - A mate-in-one can be missed at search depth 1.

2. Leaf evaluation is clamped to the alpha-beta window.
   - Alpha-beta bounds should prune, not mutate exact static evaluation values.
   - Depth-zero leaves should return raw `evaluate(board)`.

3. The transposition table stores scores without bound type.
   - Alpha-beta TT entries are not always exact.
   - A cutoff node must be stored as a lower or upper bound, not reused as exact.

4. TT and move ordering must preserve promotion identity.
   - `(start, end)` is not enough.
   - Promotion alternatives such as `e7e8q`, `e7e8r`, `e7e8b`, `e7e8n` are distinct legal moves.

5. Invalid depth values are not clearly rejected.
   - `get_best_move(depth < 1)` must raise a clear `ValueError`.

6. Self-play promotion formatting relies on string conversion of `PieceType`.
   - Since `PieceType` is an `IntEnum`, `str(PieceType.ROOK)` may not produce `"rook"`.
   - Promotion suffix formatting must use `PieceType` keys directly.

---

## Required search semantics

### Evaluation perspective

`evaluate(board)` returns:

- positive score: advantage for White,
- negative score: advantage for Black.

Minimax must preserve this convention.

When `board.turn == Color.WHITE`, search should maximize the score.

When `board.turn == Color.BLACK`, search should minimize the score.

If the existing code uses `is_maximizing`, it must remain consistent with this rule.

---

## Required terminal handling

Terminal state detection must occur **before** the `depth == 0` cutoff.

Correct order inside `minimax()`:

1. Generate legal moves for `board.turn`.
2. If there are no legal moves:
   - if side to move is in check, return a checkmate score,
   - otherwise return stalemate score `0`.
3. If `depth == 0`, return raw `evaluate(board)`.
4. Search child moves with alpha-beta pruning.

This is required so a mate-in-one is found at depth 1.

### Checkmate scoring

Use a large mate score, for example:

```python
MATE_SCORE = 100_000
```

Required convention:

- If White has delivered mate and Black is side to move with no legal moves, score must be positive.
- If Black has delivered mate and White is side to move with no legal moves, score must be negative.

Equivalent implementation:

```python
if no_legal_moves and board.is_in_check(board.turn):
    if board.turn == Color.WHITE:
        # White to move is checkmated, good for Black.
        return -MATE_SCORE + ply_from_root
    else:
        # Black to move is checkmated, good for White.
        return MATE_SCORE - ply_from_root
```

If the code does not currently track `ply_from_root`, it may initially return `-MATE_SCORE` / `MATE_SCORE`. Prefer adding ply-distance adjustment if simple, because it makes the AI prefer faster mates and delay being mated.

### Stalemate scoring

Stalemate score is exactly:

```python
0
```

Do not evaluate stalemate by material.

---

## Required alpha-beta behavior

At depth-zero leaves:

```python
return evaluate(board), None
```

Do **not** clamp the returned score to `[alpha, beta]`.

Alpha-beta uses `alpha` and `beta` to decide pruning. It must not convert exact static evaluations into bound values at leaf nodes.

---

## Required transposition table design

Implement a real alpha-beta transposition table.

### Required TT flag enum

Add a flag enum, preferably in `chess_game/chess/ai.py` or a dedicated AI support module:

```python
from enum import Enum

class TTFlag(Enum):
    EXACT = "exact"
    LOWERBOUND = "lowerbound"
    UPPERBOUND = "upperbound"
```

String values are acceptable if the repo style prefers them, but an enum is preferred.

### Required TT entry dataclass

Add:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class TTEntry:
    depth: int
    score: int
    best_move: Optional[LegalMove]
    flag: TTFlag
```

If the repo represents legal moves as tuples rather than a `LegalMove` class, use the repo's current move type. The TT entry must preserve:

- start square,
- end square,
- promotion piece.

### Required TT key

The TT key must include all state relevant to legal moves and evaluation:

- board placement,
- side to move,
- castling rights,
- en passant target.

The current `_fen_key()` or equivalent is acceptable only if it includes those fields.

Do not call the key a full FEN unless it is actually a valid FEN string. A pseudo-FEN/key string is fine if named accordingly.

### Required TT lookup semantics

At the start of `minimax()`, after terminal/depth handling requirements are respected appropriately, lookup the key.

A TT entry can be used only if:

```python
entry.depth >= current_depth
```

Then apply alpha-beta TT semantics:

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

Important: LOWERBOUND and UPPERBOUND entries adjust the window. They are not exact values unless they cause a cutoff.

### Required TT store semantics

Before searching a node, save the original alpha:

```python
alpha_orig = alpha
```

After search completes, compute the TT flag:

```python
if best_score <= alpha_orig:
    flag = TTFlag.UPPERBOUND
elif best_score >= beta:
    flag = TTFlag.LOWERBOUND
else:
    flag = TTFlag.EXACT
```

Important: use the original beta for this comparison. If the code mutates `beta`, save `beta_orig` too.

A safer pattern:

```python
alpha_orig = alpha
beta_orig = beta

# search...

if best_score <= alpha_orig:
    flag = TTFlag.UPPERBOUND
elif best_score >= beta_orig:
    flag = TTFlag.LOWERBOUND
else:
    flag = TTFlag.EXACT
```

Store:

```python
transposition_table[key] = TTEntry(
    depth=current_depth,
    score=best_score,
    best_move=best_move,
    flag=flag,
)
```

### Required TT safety

- A shallower entry must not replace a deeper entry unless there is a clear reason.
- Simple rule: only overwrite if no entry exists or new entry depth is greater than or equal to old entry depth.
- TT must not mutate the board.
- TT best moves must include promotion identity.

---

## Required move identity

Move identity must include:

- start square,
- end square,
- promotion piece.

This applies to:

- legal move objects/tuples,
- move ordering keys,
- TT best moves,
- mapping ordered moves back to legal moves,
- tests.

Do not match moves by `(start, end)` only.

---

## Required move ordering cleanup

Move ordering must not treat any move to rank 1 or rank 8 as promotion.

Bad pattern:

```python
promoted_to = end.row in (ROW_1, ROW_8) and board.get_piece(start) is not None
```

Correct approach:

```python
promotion_bonus = 0
if move.promotion is not None:
    promotion_bonus = value_for_promoted_piece(move.promotion)
```

Promotion ordering should prefer:

```text
queen > rook > bishop/knight
```

Do not add complex evaluation tuning in this pass.

---

## Required depth validation

`get_best_move(board, depth)` must reject invalid depths:

```python
if depth < 1:
    raise ValueError("depth must be >= 1")
```

Self-play argument parsing must also reject invalid depth values or fail with a clear message.

Do not treat depth 0 as "no legal move."

---

## Required self-play promotion formatting

Promotion suffix formatting must use `PieceType` directly:

```python
PROMOTION_SUFFIXES = {
    PieceType.QUEEN: "q",
    PieceType.ROOK: "r",
    PieceType.BISHOP: "b",
    PieceType.KNIGHT: "n",
}
```

If `promotion is None`, append no suffix.

Do not rely on:

```python
str(promotion).lower()
```

---

## Required tests

Add tests for:

1. Mate-in-one found at depth 1.
2. Terminal checkmate at horizon is scored as mate, not material.
3. Stalemate returns no best move.
4. Depth validation rejects `depth=0` and negative depth.
5. Leaf evaluation returns raw evaluation, not clamped score.
6. TT stores and reuses exact entries correctly.
7. TT uses lower-bound and upper-bound flags correctly.
8. TT preserves promotion identity.
9. Move ordering preserves promotion identity.
10. Self-play promotion suffix formatting handles rook/bishop/knight/queen correctly.

Tests may inspect private helpers if the current test suite already does so and there is no clean public API. Prefer public behavior tests where practical.

---

## Acceptance criteria

The patch is complete only when:

- Full suite passes with `python -m pytest tests -q`.
- Mate-in-one is found at depth 1.
- Stalemate returns no move.
- Depth zero and negative depth raise `ValueError`.
- Leaf nodes return raw evaluation.
- TT entries include depth, score, best move, and exact/lower/upper flag.
- TT lookup applies correct alpha-beta bound semantics.
- TT best moves preserve promotion identity.
- Move ordering preserves promotion identity.
- Self-play formats underpromotion suffixes correctly.
- No evaluator tuning or unrelated features are included.
