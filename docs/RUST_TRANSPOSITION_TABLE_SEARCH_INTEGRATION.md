# Rust Transposition-Table Search Integration

The overall Task 15 gate connects the fixed-capacity transposition table to production negamax alpha-beta without changing legal-move, terminal, draw, mate-distance, cancellation, or restoration semantics.

## Public entry points

The existing `alpha_beta_search` and `alpha_beta_search_with_cancellation` convenience functions allocate one fresh bounded table using `DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES`, currently 1 MiB.

Callers that want reuse across searches provide a fixed table through:

- `alpha_beta_search_with_transposition_table`;
- `alpha_beta_search_with_cancellation_and_transposition_table`.

A caller-owned table retains entries, advances generation once per valid search, and resets only diagnostic counters. It never resizes and has no map fallback.

## Node sequence

For every non-quiescence node, production search:

1. checks cancellation;
2. generates legal moves and resolves checkmate, stalemate, dead position, repetition, and move-count draws before consulting cached scores;
3. probes by the complete position key, required depth, current ply, and alpha-beta window;
4. accepts exact or bound cutoffs only through the verified probe contract;
5. uses a verified TT move as the highest ordering hint at non-root nodes when no score cutoff is available;
6. searches and restores every active child exactly;
7. classifies the completed fail-soft result as exact, lower, or upper against the original window;
8. normalizes the score at the current ply and stores it only when history-independent reuse is safe.

Depth-zero nodes continue through correctness-first quiescence and are not stored as ordinary alpha-beta entries.

## Reversible-history safety

The position Zobrist key intentionally excludes the halfmove clock and prior repetition path. A score is therefore stored or reused only when `halfmove_clock == 0`, immediately after an irreversible pawn move or capture has reset the relevant repetition and fifty-move history boundary.

At nodes with a nonzero halfmove clock, the probe uses `SuppressedForRepetition`. A verified move may still order already-generated legal moves, but the cached score cannot cut off and the newly searched path-dependent score is not stored. Terminal and draw resolution always happens before probing.

## Root determinism

The root ignores ordering-only TT moves. A root shortcut is accepted only for an exact entry whose stored best move is present in the current legal-token list. This preserves the established deterministic best-move contract when equal root scores exist and prevents corrupt or stale move payloads from bypassing legal search.

Exact entries created below the root omit their best move. Their scores remain reusable internally, but a later search rooted at that position must search legal moves to establish the canonical root move. Exact root entries retain the canonical move and support a one-node warm-table return.

## Bounds and restoration

Completed node scores are stored as:

- upper bounds when the result is at or below the original alpha;
- lower bounds when the result is at or above beta;
- exact values otherwise.

No entry is stored for cancellation, rule failure, history failure, score-conversion failure, terminal/draw resolution, or incomplete child restoration.

## Deterministic usefulness witnesses

The gate includes two independent node-reduction witnesses:

- a fixed narrow-window production-node test where an insufficient-depth TT entry contributes only its move and visits fewer nodes without changing score or best move;
- a caller-owned warm-table test where the second identical full-window search returns the same exact score and canonical best move in one node.

Additional regressions prove reversible-history score suppression, root hint suppression, illegal exact-root move rejection, fixed table capacity, and exact position/history/Zobrist restoration.
