# responses3.md – Questions for ChatGPT-5.5 review

Based on:
- CHESS_ENGINE_AI_TT_REPAIR_SPEC.md
- CHESS_ENGINE_AI_TT_REPAIR_TODO.md

High-level understanding:
- Fix minimax terminal handling (no-legal-moves / checkmate / stalemate).
- Fix alpha-beta leaf behavior (raw evaluation, no clamping).
- Implement TT with EXACT / LOWERBOUND / UPPERBOUND.
- Preserve promotion identity (start, end, promotion).
- Validate search depth (raise ValueError for depth < 1).
- Fix self-play promotion suffix formatting using PieceType.
- Add focused regression tests.
- No new features (no iterative deepening addition, no quiescence, no UCI, etc.).
- Do not tune evaluator.

Open questions:

1) Iterative deepening:
- The spec says “Do not add iterative deepening.”
- The current ai.py already uses iterative deepening.
- Should we:
  - Keep iterative deepening as-is?
  - Remove it (strict “no iterative deepening” interpretation)?

2) Shallow clone vs undo-based search:
- Current ai.py uses shallow_clone_board per child.
- The spec does not explicitly require undo-based search.
- Options:
  - Keep shallow_clone_board.
  - Replace with undo-based search to improve performance at depth 5.
- Should we keep shallow_clone_board, or switch to undo-based search as part of this pass?

3) Branching:
- The TODO suggests creating fix/ai-minimax-alpha-beta-tt.
- Should we work on that branch or continue on master?

4) TT key naming:
- The TODO suggests renaming _fen_key() → _position_key() if not a real FEN.
- Should we rename it now?

5) Evaluator tuning:
- The spec says “Do not tune the evaluator.”
- The current code has some promotion bias in move ordering.
- The TODO says we can adjust PROMOTION_ORDER_BONUS for ordering only.
- Is adjusting PROMOTION_ORDER_BONUS allowed, or should we leave evaluation-like weights untouched?

6) Self-play depth:
- The current self-play code supports --white-depth and --black-depth.
- Should we keep this behavior, or simplify to a single depth parameter?

7) TT size limits:
- The current TT is unbounded.
- Should we add a size limit or eviction policy, or leave it unbounded?

8) Test coverage:
- The spec asks for focused regression tests for search correctness.
- Should we create a new file (tests/test_ai_search.py), or add to existing ai-related test files?

9) Documentation:
- The TODO suggests small, reviewable commits.
- Should we track progress in memory.md, or just rely on git history?
