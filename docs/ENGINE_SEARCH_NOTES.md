# Engine Search Notes

## Architecture overview

The search lives in `chess_game/chess/ai.py` with supporting modules:

| Module | Role |
|--------|------|
| `ai.py` | Main entry points: `get_best_move`, `minimax`, `quiescence` |
| `ai_search_helpers.py` | Iterative deepening, aspiration windows, TT, repetition |
| `ai_move_ordering.py` | Move ordering (killer, history, TT best-move) |
| `ai_quiescence_helpers.py` | Tactical-move selection for quiescence |
| `ai_capture_ordering.py` | MVV-LVA capture ordering |
| `ai_board_utils.py` | `get_legal_moves` wrapper |
| `evaluation.py` | Static evaluator (`evaluate(board, weights)`) |

---

## Coordinate system

- `row 0 = rank 8` (Black's back rank), `row 7 = rank 1` (White's back rank)
- `col 0 = file a`, `col 7 = file h`
- White pawns move toward smaller row numbers; Black pawns toward larger.

---

## Search algorithm

### Iterative deepening with aspiration windows

`_iterative_deepening_best_move` loops from depth 1 to the requested depth.
Each iteration uses an aspiration window centred on the previous iteration's
score.  On a fail-high or fail-low the window is re-opened to ±INF and the
position is re-searched.

### Alpha-beta minimax

`minimax(board, params)` implements negamax-style alpha-beta with:

- **Transposition table** (position-keyed using `position_key()` string representation, with `TTFlag.EXACT / LOWER / UPPER`).
  - **Future work:** Replace string keys with true Zobrist hashing for improved performance.
  - **Mate-score safety:** Mate scores are not stored in the TT until ply-based normalization is implemented (see `MATE_SCORE_MARGIN`).
- **Killer move heuristic** — two killer slots per ply.
- **History heuristic** — quiet moves that caused cut-offs get bonus ordering.
- **Selective extensions** — check extensions and pawn-push extensions.
- **Repetition detection** — threefold repetition draws at any depth.

### Terminal score detection

`_terminal_score(board, legal_moves, ply)` is called before recursing:

1. Fifty-move rule → `DRAW_SCORE (0)`
2. Insufficient material → `DRAW_SCORE`
3. No legal moves + in check → mate score (sign depends on side to move):
   - White mated: `−MATE_SCORE + ply`
   - Black mated: `+MATE_SCORE − ply`
4. No legal moves + not in check → `DRAW_SCORE` (stalemate)

`ply = max(0, len(line_history) − 1)`.  The `+ ply` / `− ply` adjustment
makes the engine prefer delivering checkmate sooner and resisting it longer.

### Score perspective

`evaluate(board, weights)` returns a **White-relative** score:

- Positive → good for White.
- Negative → good for Black.

The minimax tree uses an `is_maximizing` flag — White maximises, Black
minimises.  No perspective flip is applied between the evaluator and the
minimax driver.

---

## Quiescence search

`quiescence(board, alpha, beta, is_maximizing, context, depth_remaining)`
extends tactical leaf nodes.

### Normal path (not in check)

1. Compute *stand-pat* score (static evaluation).
2. Use stand-pat to update alpha/beta bounds.
3. If stand-pat causes a beta cut-off, or `depth_remaining == 0`, return stand-pat.
4. Otherwise expand tactical moves via `select_quiescence_moves` (captures with
   positive/neutral SEE, promotions).

### Check-evasion path (in check)

Stand-pat is **disabled** when the side to move is in check — standing pat on a
check position would accept an illegal state.  Instead:

1. All legal moves are generated.
2. If none exist → checkmate at the quiescence boundary (returns a mate score).
3. Otherwise, all evasions are searched recursively.

This is implemented in `_quiescence_evasion_search`.

### Tactical-move selector

`select_quiescence_moves` (in `ai_quiescence_helpers.py`) uses MVV-LVA to
filter captures.  It includes pawn captures and promotions that were excluded
by older heuristics.

---

## Deterministic mode and seeding

`BestMoveOptions(deterministic=True)` makes the search tie-break lexicographically by
(from_row*8+from_col, to_row*8+to_col, promotion) using primitive square indices
instead of random shuffling. Used in the Texel tuning pipeline for reproducible evaluation.

`BestMoveOptions(rng_seed=N)` seeds the global RNG early, before opening-book
selection, ensuring all random choices (including `random_opening_book`) are controlled.

---

## Key constants

| Constant | Value | Meaning |
|----------|-------|---------|
| `INF` | 10 000 000 | Alpha-beta window bound |
| `MATE_SCORE` | 100 000 | Checkmate base score |
| `DRAW_SCORE` | 0 | Stalemate / draw score |
| `MAX_QUIESCENCE_DEPTH` | 4 | Max plies of quiescence recursion |
| `ASPIRATION_WINDOW` | (varies) | Initial aspiration window half-width |

---

## Adding a new evaluation signal

1. Add a field to `EvalWeights` (in `eval_weights.py`) with a sensible default.
2. Implement the signal in a module under `chess_game/chess/` or the existing
   `evaluation.py`.
3. Call it from `evaluate()` with a `weights.<field>` coefficient.
4. Run `uv run python -m pylint chess_game` to verify 10.00/10 before committing.
5. Optionally re-tune via the Texel pipeline (see `docs/TEXEL_TUNING.md`).

---

## Testing

### Test policy: Fast vs Slow

- **Fast suite** (~100 seconds): Unit tests, smoke tests, and shallow-depth search tests (depth ≤ 2)
  - Run on every code change
  - Test behavior via mocking where practical
  - Catch correctness regressions quickly

- **Slow suite** (~15-20 minutes): Engine-strength regressions at depth 3+
  - Run before releases or major changes
  - Marked with `@pytest.mark.slow`
  - Test full search and evaluation function

**Rule:** Deep search tests (depth > 2) must be marked slow. Fast tests must
complete in <2 seconds each.

### Running tests

```bash
# Fast test suite (excludes @slow markers)
uv run python -m pytest tests/ -q -m "not slow"

# Slow test suite (depth 3+ engine regressions, ~20 minutes)
uv run python -m pytest tests/ -q -m "slow"

# Perft node-count correctness checks
# - Starting position: exact counts (depth 1-4)
# - Special cases: smoke tests only (castling, en passant, promotion, check evasion)
uv run python -m pytest tests/test_perft.py -v -m "not slow"

# Terminal-score branching
uv run python -m pytest tests/test_search_terminal_scores.py -v

# Quiescence correctness
uv run python -m pytest tests/test_ai_quiescence_production.py -v
```

### Perft coverage

**Starting position** (known-exact):
- Depth 1: 20 nodes
- Depth 2: 400 nodes
- Depth 3: 8,902 nodes
- Depth 4: 197,281 nodes (slow)

**Special cases** (smoke tests — verify move generation works):
- Castling: verify move count consistent
- En passant: verify capturing moves exist
- Promotion: verify promotion moves exist
- Check evasion: verify evasion moves exist

**Deferred (future work):**
- Exact counts for pins, discovered checks, complex castling/en passant combinations
- Make/unmake search optimization (replace clone-based move exploration)
- Zobrist hashing (replace string position keys)
- TT mate-score ply-based normalization (allow safe mate score storage)
- Broader exact special perft suite (external database integration)
- Search module decomposition (ai.py is currently ~500+ lines)
