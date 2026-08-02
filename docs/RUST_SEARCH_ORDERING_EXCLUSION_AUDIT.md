# Rust Search and Ordering Exclusion Audit

**Task:** 14.5  
**Branch:** `rust-engine`  
**Scope:** production Rust search, quiescence, and move-ordering code

## Purpose

Task 14 deliberately keeps the Rust search architecture free of the narrow scenario-specific patches accumulated by the Python implementation. Move ordering may change the order in which exact search examines legal moves, but it may not become a second evaluator or alter the searched result.

The permanent CI command is:

```bash
python3 scripts/task_14_5_exclusion_audit.py
```

The audit fails the build when any exclusion below is no longer mechanically supported.

## Exclusion matrix

| Exclusion | Enforced boundary | Behavioral evidence |
|---|---|---|
| No transcript review-loop ordering | Production `chess-search` source is scanned for transcript/review-loop scoring, bonus, penalty, guidance, and ordering identifiers. | Ordering tests remain expressed only in chess/search terms and do not load transcript state. |
| No anti-drift scenario scoring | Production source is scanned for anti-drift, drift-scenario, and scenario-score identifiers. | Full-window reference and alpha-beta searches retain identical score semantics on curated fixtures. |
| No root heuristic may override a better exact score | Root alpha-beta uses the complete mate-domain window. Best replacement is strictly `score > previous`; ordering keys are absent from result selection. | `uniquely_best_tactical_move_matches_the_independent_root_score_oracle` proves the selected root move is the unique maximum exact score. `quiet_ordering_preserves_full_window_result_deterministically` proves quiet ordering preserves the full-window result. |
| No large strategic evaluation duplicated inside ordering | `MoveOrderKey` is restricted to TT/PV hooks, tactical category/material terms, killer/history values, and the encoded tie-break. The orderer may query only `Position::piece_at` and `Position::side_to_move`. Strategic evaluator identifiers are forbidden in production ordering code. | Tactical and quiet narrow-window witnesses reduce nodes without changing the searched score or best move. |

## Permitted ordering information

The bounded orderer may use only:

1. a future transposition-table move hook;
2. a future previous-iteration PV move hook;
3. promotion piece value;
4. MVV-LVA capture value, including en-passant pawn-victim semantics;
5. two killer moves per ply;
6. bounded side/source/destination history;
7. stable packed-move identity as the final quiet tie-break.

The local tactical `piece_value` table is intentionally small and is not a strategic evaluator. It classifies promotions, victims, and attackers only. Pawn structure, mobility, king safety, space, piece-square tables, game phase, and other evaluation terms remain exclusively in the evaluator.

## Exact-score boundary

Ordering controls traversal only. Production root selection follows these rules:

- the root is searched with the complete supported score window;
- a move replaces the current best only when its searched score is strictly greater;
- equal scores retain the first deterministic best move;
- no ordering key, history value, killer rank, transcript state, scenario score, or post-search heuristic participates in best-move replacement;
- every ordering benchmark must preserve score and best-move semantics while demonstrating node reduction only where a fixed witness supports it.

## Audit maintenance

Changes to the ordering key, permitted `Position` queries, or exact-root selection require an intentional update to this document and the audit script. Task 15 may activate the TT move hook, and Task 16 may activate previous-PV ordering, but neither task may weaken the exact-score boundary or add strategic/scenario scoring to ordering.
