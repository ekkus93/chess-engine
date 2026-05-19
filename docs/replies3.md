# replies3.md — Answers for Copilot on AI/TT Repair

These answers address the questions in `responses3.md` about the AI/minimax/alpha-beta/transposition-table repair pass based on:

- `CHESS_ENGINE_AI_TT_REPAIR_SPEC.md`
- `CHESS_ENGINE_AI_TT_REPAIR_TODO.md`

The high-level summary is correct: this pass is about fixing minimax terminal handling, alpha-beta leaf behavior, TT correctness, promotion-aware move identity, depth validation, self-play promotion formatting, and focused regression tests.

Do **not** add new search features. Do **not** tune evaluation.

---

## 1. Iterative deepening

**Keep the existing iterative deepening if it is already in `ai.py`. Do not remove it.**

The instruction “do not add iterative deepening” means: do not introduce iterative deepening as a new feature if it is not already there. Since the current code already uses it, preserve it unless it directly blocks correctness.

Required behavior:

```text
get_best_move(board, depth=N)
  may internally search 1..N
  must return the best move from the completed depth-N search
  must still use correct terminal handling and TT semantics
```

Do not use this pass to redesign time management or add clocks.

---

## 2. Shallow clone vs undo-based search

**Keep the current clone-per-child search. Do not switch to undo-based search in this pass.**

Undo-based search is faster, but it is also more error-prone. This project just spent several rounds fixing board mutation bugs. A clone-based search is slower but safer and easier to validate.

Use this rule:

```text
Correctness first. Performance later.
```

Only replace `shallow_clone_board` if it is provably causing incorrect search results. Otherwise, keep it.

---

## 3. Branching

Prefer creating the branch:

```bash
git checkout -b fix/ai-minimax-alpha-beta-tt
```

If the project has been working directly on `master`, continuing on `master` is acceptable, but this patch must stay focused. Do not mix in unrelated engine, GUI, or evaluation changes.

---

## 4. TT key naming

**Yes, rename `_fen_key()` to `_position_key()` now**, unless that causes a lot of churn.

Reason: if the key is not full legal FEN, calling it FEN is misleading. A TT key must include at least:

```text
board placement
side to move
castling rights
en passant target
```

If it does not include halfmove/fullmove counters, that is fine for search identity, but then it should not be called a full FEN key.

Use a compatibility wrapper only if needed:

```python
def _fen_key(board: Board) -> str:
    return _position_key(board)
```

But preferably update internal callers to `_position_key`.

---

## 5. Evaluator tuning / promotion ordering bonus

Do **not** tune the evaluator.

It is okay to adjust **move ordering** constants if needed for correctness/readability, because move ordering does not change the final minimax value when alpha-beta is correct. But keep it conservative.

Allowed:

```text
Use move.promotion is not None for promotion ordering.
Prefer queen promotion before rook/bishop/knight in ordering.
Remove bogus promotion detection based only on reaching row 0/7.
```

Not allowed in this pass:

```text
Changing material values.
Changing piece-square tables.
Adding mobility, king safety, pawn-structure scoring, passed-pawn scoring, etc.
```

So yes, `PROMOTION_ORDER_BONUS` may be adjusted **only as move ordering**, not evaluation tuning.

---

## 6. Self-play depth

**Keep `--white-depth` and `--black-depth`.**

Do not simplify to a single depth parameter. The existing interface is useful for testing uneven-strength self-play, and changing it is unrelated to the TT repair.

Add validation for both:

```text
white_depth >= 1
black_depth >= 1
```

If either is invalid, fail fast with a clear error.

---

## 7. TT size limits

For this pass, **leave the TT unbounded** unless the existing code already has a size mechanism.

A correct bounded TT requires a replacement policy, and that is a separate design choice. First implement correct TT semantics:

```text
EXACT
LOWERBOUND
UPPERBOUND
depth-aware lookup
promotion-aware best move
safe alpha/beta window handling
```

Once correctness is established, a later patch can add max entries / LRU / depth-preferred replacement.

---

## 8. Test coverage file

Create a new file:

```text
tests/test_ai_search.py
```

Keep the tests focused on search behavior:

```text
mate-in-one found at depth 1
terminal states handled before depth cutoff
leaf evaluation is raw, not alpha/beta-clamped
TT exact/lower/upper flags behave correctly
promotion identity is preserved in search/TT/move ordering
depth < 1 raises ValueError
self-play promotion suffix formatting uses PieceType
```

Use existing test helpers like `sq(...)`, `assert_piece(...)`, and `assert_empty(...)`.

Do not bury these tests in a broad board-rules file.

---

## 9. Documentation / `memory.md`

Use git history as the primary record.

Update `memory.md` only if the project convention requires it or if it is actively used by Copilot/OpenCode as working memory. If updated, keep it short and current:

```text
AI/TT repair:
- Fixed terminal handling before depth cutoff.
- Implemented TTEntry with EXACT/LOWERBOUND/UPPERBOUND.
- Preserved promotion identity in TT/move ordering.
- Added tests in tests/test_ai_search.py.
- Full suite: N passed.
```

Do not paste a long narrative into `memory.md`.

Also remove or clearly mark stale old claims if they are confusing Copilot.

---

## Final instruction to Copilot

Implement this as a correctness patch:

```text
1. Keep existing iterative deepening.
2. Keep clone-based child search.
3. Fix terminal handling before depth cutoff.
4. Return raw evaluate(board) at depth 0.
5. Implement TTEntry with depth, score, best_move, and flag.
6. Use EXACT / LOWERBOUND / UPPERBOUND correctly.
7. Rename _fen_key to _position_key if practical.
8. Preserve promotion in all move identity paths.
9. Validate depth >= 1.
10. Keep white-depth / black-depth in self-play.
11. Fix self-play promotion suffix formatting.
12. Add tests in tests/test_ai_search.py.
13. Do not tune the evaluator.
```

This should be enough to proceed cleanly.
