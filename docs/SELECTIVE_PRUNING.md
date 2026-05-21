# SELECTIVE PRUNING

## Goal

Make deeper search practical by increasing **search selectivity** without breaking correctness, mate finding, or tactical reliability.

This is a deferred roadmap for improving high-depth performance beyond the current depth-5 recovery work.

---

## Core idea

We can prune or reduce **more aggressively as depth increases**, but it must be done **selectively** rather than blindly.

The engine should search:

- the most promising moves at full depth
- weaker or later moves at reduced depth
- obviously unpromising moves less often or not at all near the frontier

The goal is to keep strong tactical coverage where it matters while cutting the huge amount of low-value tree growth at higher depths.

---

## Recommended implementation order

1. Principal Variation Search (PVS)
2. Late Move Reductions (LMR)
3. Careful null-move pruning
4. Futility pruning / razoring
5. Additional depth-aware quiet-move filtering and tuning

---

# Task 1: Add Principal Variation Search (PVS)

## Why

PVS is usually a low-risk speedup once move ordering is decent.

## Plan

- [ ] Search the first move at each node with the full alpha-beta window.
- [ ] Search later moves with a narrow null window first.
- [ ] Re-search with the full window only if the null-window search fails high.
- [ ] Keep the PV path exact; do not accept speculative narrow-window results as final without verification.

## Validation

- [ ] Ensure score parity with current alpha-beta on targeted shallow positions.
- [ ] Confirm mate behavior remains correct.
- [ ] Compare node counts before/after.

---

# Task 2: Add Late Move Reductions (LMR)

## Why

LMR is usually the biggest next performance improvement for deeper searches.

## Plan

- [ ] Keep the first few ordered moves at full depth.
- [ ] Reduce depth for later moves, especially:
  - [ ] quiet moves
  - [ ] non-checking moves
  - [ ] moves late in the ordered list
- [ ] Scale the reduction by:
  - [ ] search depth
  - [ ] move index
  - [ ] whether the move is tactical or quiet

## Safety rules

- [ ] Do not reduce:
  - [ ] forced recaptures unless tested safe
  - [ ] checking moves without explicit validation
  - [ ] promotions
  - [ ] obvious PV candidates
  - [ ] moves in mate-sensitive lines unless proven safe

## Validation

- [ ] Add tests ensuring tactical moves are not suppressed incorrectly.
- [ ] Compare node count and runtime at depths 5+.

---

# Task 3: Add null-move pruning carefully

## Why

Null-move pruning can cut large parts of the tree if the side to move is already clearly fine.

## Plan

- [ ] Add a null-move search with a reduced depth search after a “pass”.
- [ ] If the null-move result still exceeds beta, prune the node.
- [ ] Use a conservative reduction initially.

## Safety rules

- [ ] Avoid or restrict null move in:
  - [ ] zugzwang-prone endgames
  - [ ] low-material endgames
  - [ ] positions where side-to-move has very few legal moves
- [ ] Do not let null-move pruning break exact mate handling.

## Validation

- [ ] Add endgame regression tests specifically for zugzwang-like scenarios.
- [ ] Verify no false mate/stalemate conclusions appear.

---

# Task 4: Add futility pruning and razoring near the frontier

## Why

Near the leaf, many weak moves are not worth full search if static evaluation plus a margin cannot improve alpha.

## Plan

- [ ] Add futility pruning for shallow frontier nodes.
- [ ] Add razoring only if needed after futility is stable.
- [ ] Base margins on:
  - [ ] remaining depth
  - [ ] tactical volatility
  - [ ] move type

## Safety rules

- [ ] Do not futility-prune:
  - [ ] checks
  - [ ] promotions
  - [ ] obvious tactical responses
  - [ ] positions with mate threats unless verified safe

## Validation

- [ ] Re-run tactical regression tests after each margin change.
- [ ] Compare missed tactics before/after.

---

# Task 5: Improve depth-aware quiet-move filtering

## Why

At high depth, many quiet moves are simply not realistic candidates.

## Plan

- [ ] Use move ordering more aggressively for quiet moves.
- [ ] Combine TT move, previous best move, killer moves, and history-like priorities.
- [ ] Search only the best quiet candidates at full depth where justified.
- [ ] Reduce or skip low-value quiet moves late in the move list.

## Validation

- [ ] Ensure strategic quiet improvements are still found in dedicated test positions.
- [ ] Verify endgame conversion does not become erratic.

---

# Task 6: Tune selectivity by depth

## Why

The deeper the node, the more valuable selective pruning becomes.

## Plan

- [ ] Make reductions stronger for:
  - [ ] deeper nodes
  - [ ] later moves
  - [ ] quiet moves with weak ordering score
- [ ] Keep pruning lighter at shallow depths or tactically sharp nodes.

## Warning

- [ ] Do not interpret “more aggressive with depth” as “globally prune harder everywhere.”
- [ ] The safe version is: reduce more for weak late moves, not for principal or tactical moves.

---

# Task 7: Protect correctness and tactical strength

## Risks

Selective pruning can cause:

- missed quiet strategic resources
- tactical blindness
- zugzwang bugs
- incorrect mate handling
- false confidence from reduced nodes

## Required safeguards

- [ ] Keep mate tests and tactical tests running throughout.
- [ ] Add targeted regressions for:
  - [ ] mate in 1
  - [ ] mate in 2 / forced tactical shots
  - [ ] quiet defensive resources
  - [ ] zugzwang-sensitive endings
  - [ ] promotion races

---

# Task 8: Measure every phase

## Metrics to record

- [ ] total nodes
- [ ] cutoffs
- [ ] TT hits
- [ ] depth-5 runtime
- [ ] deeper search runtime where practical
- [ ] tactical regression pass/fail
- [ ] self-play behavior before/after

## Success criteria

- [ ] Depth 6+ becomes materially more practical than today.
- [ ] Tactical quality does not collapse.
- [ ] Endgame and mate correctness remain intact.

---

## Summary

The safest path to stronger high-depth pruning is:

1. **PVS**
2. **LMR**
3. **careful null-move pruning**
4. **futility/razoring**
5. **depth-aware quiet-move selectivity**

The key principle is:

**Be more selective deeper in the tree, but only against weak late moves — not against the lines most likely to contain tactics or the principal variation.**
