# Opening Book Fix - Spec & TODO Review

## Status: Ready for Implementation
All requirements are clear and well-specified. No blockers identified.

---

## Summary of Changes Needed

### Critical Issues (Must Fix)

1. **Side-aware Book Indexing** — CRITICAL
   - Current implementation indexes all plies regardless of `side` field
   - Black defense lines incorrectly influence White's starting position choice
   - Need to add `_should_index_line_move()` helper that respects:
     - `side="white"`: only index when `board.turn == WHITE`
     - `side="black"`: only index when `board.turn == BLACK`
     - `side="both"`: index both sides
   - Continue validating all moves even if not indexed

2. **Remove Broad Exception Swallowing** — IMPORTANT
   - Current: catches `Exception` and silently falls back
   - Problem: hides broken bundled book, JSON errors, illegal moves, programming errors
   - Fix: Only catch exceptions at CLI layer for custom user-supplied books
   - Bundled book errors should fail loudly

3. **Strengthen Opening Book Tests** — IMPORTANT
   - Replace "first legal move" approach with explicit `apply_moves(board, "e2e4", ...)`
   - Add strong tests for:
     - Starting position uses White/both lines only, not Black defense lines
     - After `e2e4`, Black can play `c7c5` (Sicilian)
     - After `e2e4 e7e5`, White can play `f2f4` (King's Gambit)
     - After `e2e4 e7e5 f2f4 e5f4`, White can play `g1f3`
     - After `e2e4 e7e5 f2f4 f8c5`, White can play `g1f3`
     - Unknown positions return exactly `None` (not permissive checks)
     - All candidates are legal moves

---

### Important Issues (Strong Validation)

4. **Schema Validation Improvements**
   - Validate `selection == "highest_weight"` (fail on unsupported values)
   - Non-dict JSON should raise `OpeningBookError`, not return `{}`
   - Add tests for:
     - Non-string moves → `OpeningBookError`
     - Unsupported selection values → `OpeningBookError`

5. **Deterministic Sort Tie-Break with Promotion**
   - Include promotion suffix in move-string tie-break
   - Example: `e7e8q` not just `e7e8`
   - Future-proofing for promotion lines in the book

6. **Non-slow Suite Runtime**
   - Current suite may be too slow due to expensive AI strategy regression tests
   - Minimum action: mark obviously expensive tests with `@pytest.mark.slow`
   - Known candidate: `test_strategy13_black_keeps_forcing_line_over_repetition`

---

### Optional (Choose One Path)

7. **CLI Custom Book Path**
   - **Option A**: Implement `--opening-book path/to/custom.json`
   - **Option B**: Mark as "intentionally deferred" (acceptable given it's optional)
   - Current TODO marked it complete but it's not actually implemented
   - Must resolve the discrepancy (either do it or document deferral)

---

### Documentation & Verification

8. **Update Documentation**
   - `docs/OPENING_BOOK.md`: Add side-aware behavior explanation
   - CLI docs: Document `--opening-book` status

9. **Final Verification Tasks**
   - Task 9 in TODO covers all checks needed
   - JSON syntax validation
   - Opening book tests (all 25)
   - Rules subset (190 tests)
   - Targeted AI tests
   - Non-slow suite completion

---

## Questions & Clarifications

### Q1: `board.turn` Type
**Spec mentions:** "If `board.turn` is a string or other type, adapt accordingly."

**Current codebase status:** Need to verify whether `board.turn` is:
- `Color` enum (likely)
- String (`"white"` / `"black"`)
- Other

**Action:** Brief inspection of board.py will confirm. This doesn't block implementation but needs to be checked when implementing 1.2.

### Q2: Promotion Enum Access
**Spec shows:** `candidate.move.promotion.name.lower()[0]`

**Current codebase status:** Need to verify:
- Is `PieceType` the promotion enum?
- Does it have `.name` attribute that's appropriate?
- Are promotion values like `QUEEN`, `ROOK`, etc. or `Q`, `R`?

**Action:** Check types.py and move.py. Should be straightforward but needs verification.

### Q3: `get_legal_moves()` Return Shape
**For move-identity verification (Task 3.8):**

The spec assumes `board.get_legal_moves()` returns moves with comparable identity.

**Current codebase status:** Confirmed it returns tuples: `(start, end, promotion)`

**Action:** Already known from previous session. Proceed confidently.

### Q4: `candidates_for()` Method
**Spec references:** `book.candidates_for(board)` to get list of `BookMove` candidates

**Current status:** Need to verify if this method exists or needs to be created/exposed

**Action:** Check opening_book.py. If not public, either:
- Expose it as public API for testing
- Use internal `_position_index` for tests (less clean)
- Add test-only helper

### Q5: CLI Structure
**For Task 6 (optional `--opening-book` support):**

Need to understand:
- Where self-play CLI argument parsing happens
- How `--no-opening-book` is currently handled
- Pattern for adding file-path arguments

**Action:** grep for `no-opening-book` will show current pattern. Straightforward to extend.

---

## What's NOT Changing (Guardrails)

Per the spec and confirmed:

- ✅ Minimax algorithm
- ✅ Alpha-beta pruning
- ✅ Transposition table semantics
- ✅ Static evaluation
- ✅ Material values
- ✅ Piece-square tables
- ✅ Move ordering scores
- ✅ Board rules / legal move generation

This is a **data-layer fix**, not a search/eval refactor.

---

## Implementation Order (Recommended)

1. **Task 0**: Establish baseline (quick verification)
2. **Task 1**: Side-aware indexing (core fix)
3. **Task 2**: Remove exception swallowing (safety)
4. **Task 3**: Strengthen tests (validation)
5. **Task 4**: Schema validation (robustness)
6. **Task 5**: Promotion tie-break (minor polish)
7. **Task 6**: CLI custom path (optional, last)
8. **Task 7**: Runtime marking (if needed)
9. **Task 8**: Doc updates
10. **Task 9**: Final verification
11. **Task 10**: Diff review

---

## Confidence Level

**HIGH** — Spec is clear, focused, well-defined, and non-intrusive.

No ambiguities that would block implementation.
Minor clarifications above are knowledge checks, not showstoppers.

Ready to begin implementation on your signal.
