# DEPTH5 FIX

## Goal

Restore strong search performance so `get_best_move(board, depth=5)` completes within the project target while preserving correctness.

This pass is about **depth-5 search recovery**, not broad feature work.

---

## Problem summary

Current state:

- Depth 3 self-play works, but move quality is still shallow.
- Depth 5 is the intended strength target, but current runtime is far too slow.
- Search quality improvements already added some extra cost, especially around evaluation and quiescence.

This plan focuses on getting the engine back to a practical depth-5 search first, then validating that move quality improves from deeper search.

---

## Rules for this pass

- Do not weaken legality or rules correctness.
- Do not hide lint warnings or test failures.
- Prefer structural fixes over ad hoc shortcuts.
- Keep the public API stable where possible.
- Use measurement before and after each major change.
- After each major phase, run:

  ```bash
  python -m pytest tests -q
  pylint chess_game
  ```

---

# Task 0: Re-establish the baseline

## 0.1 Record the current slowdown

- [x] Run:

  ```bash
  python -m pytest tests/test_ai_search.py::test_depth_5_search_completes -q
  ```

- [x] Record:
  - [x] elapsed runtime
  - [x] pass/fail
  - [x] whether a move was returned

## 0.2 Record search-node baseline

- [x] Run the existing node-count depth benchmark if available.
- [x] If needed, add a temporary local measurement script or test helper using existing `SearchStats`.
- [x] Record:
  - [x] total nodes
  - [x] cutoffs
  - [x] TT hits
  - [x] quiescence nodes
  - [x] fail-high / fail-low retries

## 0.3 Record self-play baseline

- [x] Run at least one depth-3 self-play game and save the transcript.
- [x] Note:
  - [x] move count
  - [x] result
  - [x] obvious tactical blunders
  - [x] repetition behavior

---

# Task 1: Add targeted performance diagnostics

## 1.1 Expand search diagnostics

- [x] Ensure `SearchStats` reports:
  - [x] total nodes
  - [x] cutoffs
  - [x] TT hits
  - [x] quiescence nodes
  - [x] root re-search count
  - [x] fail-high retries
  - [x] fail-low retries

## 1.2 Add timing hooks for root search

- [x] Add lightweight timing around each iterative-deepening pass.
- [x] Record per-depth timing for:
  - [x] depth 1
  - [x] depth 2
  - [x] depth 3
  - [x] depth 4
  - [x] depth 5

- [x] Keep these diagnostics optional or test-only if they should not always print.

## 1.3 Add quiescence visibility

- [x] Measure:
  - [x] how often quiescence is entered
  - [x] average tactical move count
  - [x] worst-case tactical branching

- [x] Identify whether quiescence is the dominant slowdown or only part of it.

---

# Task 2: Fix the biggest search-cost drivers first

## 2.1 Identify top hotspots

- [x] Confirm whether runtime is dominated by:
  - [x] board cloning
  - [x] legal move generation
  - [x] ordering work
  - [x] evaluation cost
  - [x] quiescence recursion
  - [x] TT key construction

## 2.2 Measure by phase, not by guess

- [x] Add temporary instrumentation or use profiling to compare time spent in:
  - [x] `board.clone()`
  - [x] `board.get_legal_moves()`
  - [x] `evaluate()`
  - [x] `quiescence()`
  - [x] `_order_moves()`
  - [x] `position_key()`

## 2.3 Rank the fixes

- [x] Write down the top 2-3 costs before changing anything major.
- [x] Tackle the highest-cost item first.

---

# Task 3: Reduce quiescence cost without losing the benefit

## Problem

Quiescence likely improves tactical sanity, but it currently looks too expensive for depth 5.

## 3.1 Narrow the move set

- [x] Restrict quiescence to the most meaningful continuations only:
  - [x] promotions
  - [x] favorable captures
  - [x] recaptures, if cleanly detectable

- [x] Exclude low-value noisy captures unless clearly necessary.

## 3.2 Reduce branching

- [x] Limit the number of tactical moves considered per node.
- [x] Verify move ordering is applied before that cap.
- [x] Prefer “best few tactical moves” over “all tactical moves”.

## 3.3 Tighten depth bound

- [x] Revisit maximum quiescence depth.
- [x] Use the shallowest setting that still fixes obvious horizon blunders.
- [x] Add regression tests so tactical quality does not silently collapse.

## 3.4 Add stand-pat guard improvements

- [x] Improve early cutoff behavior in quiescence.
- [x] Avoid exploring tactical lines when stand-pat already clearly settles the node.

## 3.5 Validate tactical retention

- [x] Re-run tactical tests after each quiescence reduction.
- [x] Ensure the engine still:
  - [x] avoids obvious hanging-piece blunders better than pure static search
  - [x] handles simple recapture sequences sensibly

---

# Task 4: Make evaluation cheaper

## Problem

A stronger evaluator helps, but if it is too expensive it reduces effective search depth.

## 4.1 Profile evaluation components

- [x] Measure cost of each evaluation component:
  - [x] material
  - [x] piece-square tables
  - [x] mobility
  - [x] pawn structure
  - [x] king safety
  - [x] rook activity
  - [x] bishop pair
  - [x] development heuristics

## 4.2 Remove low-value expensive work

- [x] Identify heuristics that cost a lot but contribute little strength.
- [x] Simplify or disable those first.

## 4.3 Avoid repeated full-board scans

- [x] Consolidate repeated board traversals where possible.
- [x] Reuse piece lists or shared intermediate data inside one evaluation call.
- [x] Avoid recomputing the same file/pawn/king information multiple times.

## 4.4 Revisit mobility cost

- [x] Confirm whether mobility scoring is too expensive.
- [x] If necessary:
  - [x] restrict mobility to selected piece types
  - [x] reduce how often it is counted
  - [x] use a cheaper approximation

## 4.5 Revisit king-safety cost

- [x] Confirm whether king-safety helpers are worth their current cost.
- [x] Simplify expensive scans if they do not move evaluation quality enough.

---

# Task 5: Improve move ordering for more pruning

## Problem

The cheapest way to “speed up” alpha-beta is often to prune more.

## 5.1 Strengthen root move ordering

- [x] Ensure iterative deepening reuses the previous best move first.
- [x] Ensure TT best move is prioritized at the root and internal nodes.

## 5.2 Improve tactical ordering

- [x] Keep MVV/LVA for captures.
- [x] Verify promotions are scored correctly.
- [x] Ensure killer moves are only used where helpful.

## 5.3 Avoid expensive ordering work

- [x] Make sure move ordering itself is not becoming a hotspot.
- [x] If expensive scoring is done per move, simplify it.

## 5.4 Validate pruning impact

- [x] Compare before/after:
  - [x] total nodes
  - [x] cutoffs
  - [x] depth-5 runtime

---

# Task 6: Improve transposition-table effectiveness

## Problem

If TT works but hit rate is low, the search still wastes time.

## 6.1 Measure TT usefulness

- [x] Record:
  - [x] TT hit rate
  - [x] reused exact scores
  - [x] reused bounds
  - [x] average depth of TT entries used

## 6.2 Verify key cost vs value

- [x] Measure how much time `position_key()` takes.
- [x] If string key generation is too expensive, evaluate a cheaper representation.

## 6.3 Improve reuse

- [x] Ensure the TT move is reused for ordering whenever available.
- [x] Ensure iterative deepening actually benefits from retained TT state.

## 6.4 Keep semantics correct

- [x] Do not weaken correctness of:
  - [x] exact entries
  - [x] lower-bound entries
  - [x] upper-bound entries
  - [x] depth replacement rules

---

# Task 7: Reduce board-copy overhead

## Problem

Clone-per-child search may still be a major cost center.

## 7.1 Measure clone cost explicitly

- [x] Quantify how much total time is spent in `board.clone()`.
- [x] Confirm whether clone cost is a primary blocker or secondary one.

## 7.2 Make clone cheaper if possible

- [x] Remove unnecessary copying inside search clones.
- [x] Reuse existing board clone paths instead of redundant search-only copies.
- [x] Avoid copying data not needed for search correctness.

## 7.3 Evaluate future path

- [x] If clone remains the dominant cost after simpler fixes:
  - [x] create a follow-up plan for apply/undo search
  - [x] do not start a risky undo rewrite in the middle of this pass unless clearly necessary

---

# Task 8: Tighten iterative deepening and aspiration behavior

## Problem

Root re-searches can become expensive if the aspiration policy is too aggressive.

## 8.1 Measure retry frequency

- [x] Count:
  - [x] fail-high retries
  - [x] fail-low retries
  - [x] full-window reruns

## 8.2 Tune aspiration window size

- [x] If reruns are too frequent, widen the initial window.
- [x] If reruns are rare but pruning remains good, keep the cheaper setting.

## 8.3 Avoid wasted root work

- [x] Ensure the fallback path does not re-run more than necessary.
- [x] Ensure root search accepts only final exact results.

---

# Task 9: Add performance-focused tests and benchmarks

## 9.1 Preserve current correctness

- [x] Keep all current AI correctness tests passing:
  - [x] mate tests
  - [x] TT tests
  - [x] promotion identity tests
  - [x] board non-mutation tests

## 9.2 Add benchmark-style tests

- [x] Add tests or scripts for:
  - [x] depth-3 runtime
  - [x] depth-4 runtime
  - [x] depth-5 runtime
  - [x] node-count comparisons

## 9.3 Protect tactical quality

- [x] Add regression tests that ensure performance fixes do not reintroduce:
  - [x] obvious hanging-piece blunders
  - [x] missing simple recaptures
  - [x] broken mate-in-one behavior

---

# Task 10: Re-run self-play after speed recovery

## 10.1 Validate depth-3 remains stable

- [x] Run fresh depth-3 vs depth-3 self-play.
- [x] Confirm:
  - [x] legal moves only
  - [x] no import/runtime regressions
  - [x] no false repetition behavior

## 10.2 Test stronger depth

- [ ] Once depth 5 is practical, run:

  ```bash
  python -m chess_game.self_play --white-depth 5 --black-depth 5
  ```

- [ ] Save at least one transcript under `tmp/`.

## 10.3 Review playing quality

- [ ] Compare depth-3 and depth-5 games for:
  - [ ] fewer blunders
  - [ ] stronger king safety
  - [ ] better tactical conversion
  - [ ] less meaningless shuffling

---

# Task 11: Final acceptance

## 11.1 Performance target

- [x] `tests/test_ai_search.py::test_depth_5_search_completes` passes
- [x] `tests/test_ai_search.py::test_depth_5_nodes_within_reasonable_limit` passes

## 11.2 Correctness target

- [x] Full test suite passes
- [x] Pylint passes without hidden warnings

## 11.3 Quality target

- [x] Depth-3 self-play remains stable
- [ ] Depth-5 play is visibly stronger than depth 3
- [x] No regression in mate/stalemate/repetition correctness

---

## Recommended execution order

1. Task 0 - baseline
2. Task 1 - diagnostics
3. Task 2 - hotspot ranking
4. Task 3 - quiescence reduction
5. Task 4 - evaluator cost reduction
6. Task 5 - move ordering improvements
7. Task 6 - TT effectiveness
8. Task 7 - clone-cost review
9. Task 8 - aspiration tuning
10. Task 9 - benchmark protection
11. Task 10 - self-play validation
12. Task 11 - final acceptance

---

## Notes

- The fastest path to stronger play is usually:
  1. recover depth
  2. keep tactical stability
  3. then tune evaluation further

- If depth-5 still cannot be recovered after Tasks 3-8, the next serious follow-up should be a dedicated **apply/undo search refactor** rather than piling on more evaluator changes.
