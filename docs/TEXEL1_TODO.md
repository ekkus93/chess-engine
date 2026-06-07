# TEXEL1: Texel Tuning for Self-Improving Evaluation

## Goal

Implement Texel tuning so the chess engine can automatically optimize its evaluation
weights by learning from self-play game outcomes. After each tuning run, the engine
should measurably outperform the previous set of weights when the two versions are
pitted against each other.

## Background

Texel tuning works by:
1. Collecting (position, game_outcome) pairs from self-play games
2. For each position, computing a "predicted outcome" from the static evaluation using a sigmoid
3. Minimizing mean squared error between predicted and actual outcomes
4. Using SPSA (gradient-free optimization) to adjust evaluation weights toward lower error

The tunable parameters live in `chess_game/chess/evaluation_tables.py` — roughly 60
scalar constants, 6 piece-square tables (384 values), and 5 material values (~450
parameters total). The biggest engineering challenge is refactoring the evaluator to
accept injectable weights rather than reading module-level constants directly.

---

## Phase 1: Define the `EvalWeights` dataclass

### 1.1 Create `chess_game/chess/eval_weights.py`
- [ ] Define a `EvalWeights` dataclass containing every tunable parameter currently
      in `evaluation_tables.py`:
  - [ ] `material: dict[PieceType, int]` — piece values (PAWN, KNIGHT, BISHOP, ROOK, QUEEN)
  - [ ] `pawn_table: list[list[int]]` — 8×8
  - [ ] `knight_table: list[list[int]]` — 8×8
  - [ ] `bishop_table: list[list[int]]` — 8×8
  - [ ] `rook_table: list[list[int]]` — 8×8
  - [ ] `queen_table: list[list[int]]` — 8×8
  - [ ] `king_table: list[list[int]]` — 8×8
  - [ ] One field per scalar constant in `evaluation_tables.py`
        (e.g. `isolated_pawn_penalty`, `bishop_pair_bonus`, `castled_king_bonus`, etc.)
  - [ ] `passed_pawn_bonus_by_progress: dict[int, int]` — 7 values (ranks 0–6)
  - [ ] `mobility_weights: dict[PieceType, int]` — KNIGHT, BISHOP
- [ ] Add a `@classmethod default() -> EvalWeights` that constructs an instance from
      the current hardcoded values in `evaluation_tables.py` (this is the baseline)
- [ ] Add a `to_dict() -> dict` method for JSON serialization
- [ ] Add a `@classmethod from_dict(d: dict) -> EvalWeights` for JSON deserialization
- [ ] Add a `to_flat_list() -> list[float]` method that flattens all tunable values
      into a single list (needed by the SPSA optimizer)
- [ ] Add a `@classmethod from_flat_list(values: list[float], reference: EvalWeights) -> EvalWeights`
      that reconstructs an `EvalWeights` from a flat list using the reference for structure
- [ ] Keep `KING` out of `material` tuning (it's a sentinel value, not a real weight)
- [ ] Keep non-tunable structural constants (`CENTER_FILES`, `EXTENDED_CENTER_FILES`,
      `CENTRAL_SQUARES`, `MATING_MATERIAL_BASE`, threshold constants) in
      `evaluation_tables.py` — they are logic, not weights

### 1.2 Unit tests for `EvalWeights`
- [ ] `test_default_round_trips_through_dict` — `EvalWeights.default()` → `to_dict()` →
      `from_dict()` produces identical weights
- [ ] `test_default_round_trips_through_flat_list` — flat list round-trip is lossless
- [ ] `test_flat_list_length_is_stable` — length of flat list matches expected count
      (document the count as a constant in `eval_weights.py`)
- [ ] `test_from_flat_list_rejects_wrong_length` — raises `ValueError` on wrong size

---

## Phase 2: Refactor the evaluator to accept `EvalWeights`

This is the largest phase. The evaluator currently reads constants directly from
`evaluation_tables.py`. Every sub-evaluator function needs to accept weights as a
parameter instead.

### 2.1 Refactor `evaluation.py`
- [ ] Change `evaluate(board: Board) -> int` signature to
      `evaluate(board: Board, weights: EvalWeights | None = None) -> int`
      — when `None`, use `EvalWeights.default()` (backward-compatible)
- [ ] Change `get_evaluation_breakdown` similarly
- [ ] Thread `weights` through every call to every sub-evaluator function inside
      `get_evaluation_breakdown`
- [ ] Replace all direct references to imported `evaluation_tables` constants with
      accesses on the `weights` object (e.g. `BISHOP_PAIR_BONUS` → `weights.bishop_pair_bonus`)
- [ ] Replace `MATERIAL_VALUES` dict usages with `weights.material`
- [ ] Replace piece-square table lookups with `weights.*_table`

### 2.2 Refactor `pawn_structure_evaluation.py`
- [ ] Add `weights: EvalWeights` parameter to `evaluate_pawn_structure()`
- [ ] Replace all `evaluation_tables` constant references with `weights.*` accesses
- [ ] Update all call sites in `evaluation.py`

### 2.3 Refactor `endgame_evaluation.py`
- [ ] Add `weights: EvalWeights` parameter to each public function
- [ ] Replace `evaluation_tables` constant references with `weights.*` accesses
- [ ] Update all call sites in `evaluation.py`

### 2.4 Refactor `opening_development.py`
- [ ] Add `weights: EvalWeights` parameter to affected functions
- [ ] Replace `EARLY_QUEEN_MOVE_PENALTY`, `EARLY_ROOK_MOVE_PENALTY`, etc. with
      `weights.*` accesses
- [ ] Update all call sites in `evaluation.py`

### 2.5 Audit remaining sub-evaluators
- [ ] Check each of the following for direct `evaluation_tables` imports and
      refactor as needed:
  - [ ] `middlegame_practicality_guidance.py` (`MATERIAL_VALUES`, `STARTING_NON_PAWN_MATERIAL`)
  - [ ] `conversion_guidance.py` (`MATERIAL_VALUES`)
  - [ ] `strategy_utils.py` (`MATERIAL_VALUES`)
  - [ ] `ai_search_helpers.py` (`MATERIAL_VALUES`, `STARTING_NON_PAWN_MATERIAL`)
  - [ ] `ai_move_ordering.py` (`MATERIAL_VALUES`)
  - [ ] `ai.py` (`VOLUNTARY_REPETITION_PENALTY`, `REPETITION_PROGRESS_THRESHOLD`,
        `REPETITION_PROGRESS_ONLY_THRESHOLD`)
- [ ] For files used only inside the search (not the evaluator hot-path), it is
      acceptable to keep reading from `evaluation_tables` constants for now —
      document which files were deliberately left un-refactored and why

### 2.6 Verify backward compatibility
- [ ] `evaluate(board)` with no weights argument must return the same score as before
- [ ] All existing evaluation tests must pass unchanged
- [ ] Pylint 10.00/10, mypy clean, ruff clean after this phase

---

## Phase 3: Position database

### 3.1 Create `chess_game/texel/position_db.py`
- [ ] Define a `GameRecord` dataclass:
  - [ ] `positions: list[str]` — position keys (one per ply, from `position_key()`)
  - [ ] `outcome: float` — 1.0 = White wins, 0.5 = draw, 0.0 = Black wins
- [ ] Define `PositionDB` class:
  - [ ] Internal storage: `list[tuple[str, float]]` — (position_key, outcome) pairs,
        deduplicated by position key (keep the last-seen outcome for repeated positions)
  - [ ] `add_game(record: GameRecord) -> None`
  - [ ] `save(path: Path) -> None` — write as newline-delimited JSON (one record per line)
  - [ ] `@classmethod load(path: Path) -> PositionDB`
  - [ ] `__len__() -> int`
  - [ ] `sample(n: int) -> list[tuple[str, float]]` — random sample without replacement
        (for mini-batch tuning)
  - [ ] `all_pairs() -> list[tuple[str, float]]`
- [ ] Create `chess_game/texel/` package with `__init__.py`

### 3.2 Unit tests for `PositionDB`
- [ ] `test_add_game_stores_correct_outcome`
- [ ] `test_save_and_load_round_trip`
- [ ] `test_len_returns_unique_position_count`
- [ ] `test_sample_respects_size`
- [ ] `test_empty_db_save_load`

---

## Phase 4: Self-play data collection

### 4.1 Create `chess_game/texel/collect.py`
- [ ] Define `CollectionOptions` dataclass:
  - [ ] `num_games: int = 200`
  - [ ] `depth: int = 1` — use depth 1 or 2 for data collection (fast)
  - [ ] `db_path: Path` — where to write/append the database
  - [ ] `weights: EvalWeights | None = None` — if provided, use custom weights for collection
  - [ ] `verbose: bool = False`
- [ ] Implement `collect_games(options: CollectionOptions) -> PositionDB`:
  - [ ] For each game, run a modified self-play loop (based on `_run_self_play_internal`)
        that records every position key seen during the game
  - [ ] Determine outcome from `terminal_message()`:
    - [ ] "Checkmate! White wins" → 1.0
    - [ ] "Checkmate! Black wins" → 0.0
    - [ ] Stalemate / threefold repetition / fifty-move rule → 0.5
    - [ ] Reached max moves without terminal → skip game (don't add to DB)
  - [ ] Skip opening-book positions (first N plies where book move was played) to
        avoid polluting the DB with positions the engine doesn't evaluate
  - [ ] Append completed `GameRecord` to the `PositionDB`
  - [ ] Optionally print progress every 10 games if `verbose=True`
- [ ] Add `__main__` entry point: `python -m chess_game.texel.collect`
  - [ ] CLI args: `--games N`, `--depth D`, `--db PATH`, `--verbose`

### 4.2 Unit tests for data collection
- [ ] `test_collect_games_produces_nonempty_db` — 5 games at depth 1 returns a DB with entries
- [ ] `test_collect_games_outcomes_are_valid` — all outcomes are 0.0, 0.5, or 1.0
- [ ] `test_collect_games_appends_to_existing_db` — running twice accumulates entries
- [ ] `test_collect_skips_incomplete_games` — a game that hits max_moves is excluded

---

## Phase 5: Loss function

### 5.1 Create `chess_game/texel/loss.py`
- [ ] Implement `sigmoid(score: float, k: float = 1.13) -> float`:
  ```python
  return 1.0 / (1.0 + 10 ** (-k * score / 400))
  ```
  The `k` constant scales centipawn scores to win probabilities. Start with 1.13
  (a commonly used value) and calibrate in Phase 8.
- [ ] Implement `mean_squared_error(pairs: list[tuple[str, float]], weights: EvalWeights,
      board_cache: dict[str, Board] | None = None) -> float`:
  - [ ] For each (position_key, outcome) pair, reconstruct the board from the position
        key and call `evaluate(board, weights)`
  - [ ] Compute `predicted = sigmoid(score)`
  - [ ] Return `mean((outcome - predicted) ** 2)` over all pairs
- [ ] Implement `calibrate_k(pairs: list[tuple[str, float]], weights: EvalWeights) -> float`:
  - [ ] Minimize MSE over `k` using a simple grid search or scipy minimize
  - [ ] Returns the best `k` value for these weights and data

**Note on board reconstruction**: `position_key()` produces a compact key from the
board state. To reconstruct a board, we need to either store the full FEN string in
the DB or store position keys alongside enough state to reconstruct the board.
Choose one approach during implementation:
- [ ] **Option A (simpler)**: Store FEN strings in the DB instead of position keys.
      Use `board.to_fen()` (add this method if it doesn't exist) and
      `Board.from_fen(fen)` (add this too). Enables full board reconstruction from DB.
- [ ] **Option B (leaner)**: Store boards in memory during the tuning session by
      running eval on live boards during collection, not reconstructing from DB.
      Trades memory for implementation simplicity.
- [ ] Decide between A and B and document the choice in a comment in `collect.py`

### 5.2 Unit tests for loss function
- [ ] `test_sigmoid_at_zero_returns_half` — `sigmoid(0) == 0.5`
- [ ] `test_sigmoid_large_positive_near_one` — `sigmoid(10000) > 0.99`
- [ ] `test_sigmoid_large_negative_near_zero` — `sigmoid(-10000) < 0.01`
- [ ] `test_mse_perfect_prediction_is_zero` — if every prediction matches outcome, MSE = 0
- [ ] `test_mse_worst_prediction_is_point_25` — outcome=1.0, prediction=0.5 → error=0.25
- [ ] `test_mse_decreases_with_better_weights` — construct a position where we know the
      correct sign of a weight change, verify MSE goes down

---

## Phase 6: SPSA optimizer

### 6.1 Create `chess_game/texel/spsa.py`
- [ ] Define `SPSAOptions` dataclass:
  - [ ] `max_iterations: int = 5000`
  - [ ] `initial_step_size: float = 5.0` — `a` in SPSA
  - [ ] `step_decay: float = 0.602` — `alpha` in SPSA (standard value)
  - [ ] `perturbation_size: float = 1.0` — `c` (perturbation magnitude)
  - [ ] `perturbation_decay: float = 0.101` — `gamma` (standard value)
  - [ ] `stability_constant: int = 100` — `A` (prevents too-large steps early on)
  - [ ] `batch_size: int | None = None` — if set, use a random batch per iteration;
        if None, use the full dataset
  - [ ] `checkpoint_every: int = 500` — save weights to disk every N iterations
  - [ ] `checkpoint_path: Path | None = None`
  - [ ] `verbose: bool = True`
- [ ] Implement `optimize(weights: EvalWeights, db: PositionDB,
      options: SPSAOptions) -> EvalWeights`:
  - [ ] Flatten weights to a numpy array or plain list using `to_flat_list()`
  - [ ] For each iteration `k`:
    - [ ] Compute step sizes: `a_k = a / (k + 1 + A) ** alpha`,
          `c_k = c / (k + 1) ** gamma`
    - [ ] Sample a random ±1 Bernoulli perturbation vector `delta` (same length as weights)
    - [ ] Evaluate `loss(w + c_k * delta)` and `loss(w - c_k * delta)`
      - [ ] Use `batch_size` sample if set, else full DB
    - [ ] Gradient estimate: `g_k = (loss_plus - loss_minus) / (2 * c_k * delta)`
    - [ ] Update: `w = w - a_k * g_k`
    - [ ] Clip weights to reasonable bounds (e.g. material values > 0, table values
          within [-100, 100]) to prevent runaway values
    - [ ] Every `checkpoint_every` iterations, reconstruct `EvalWeights` and save to disk
    - [ ] Log progress: iteration, current MSE, step size if `verbose`
  - [ ] Return final `EvalWeights.from_flat_list(w)`
- [ ] Define `_clip_weights(w: list[float], reference: EvalWeights) -> list[float]`
      — applies per-parameter bounds

### 6.2 Unit tests for SPSA
- [ ] `test_spsa_reduces_mse_on_trivial_problem` — one-parameter quadratic: optimizer
      converges toward the minimum
- [ ] `test_spsa_checkpoint_written` — checkpoint file exists after `checkpoint_every`
      iterations
- [ ] `test_spsa_returns_eval_weights_instance` — return type is `EvalWeights`
- [ ] `test_clip_weights_keeps_material_positive` — material values never go below 1

---

## Phase 7: Weight persistence and loading

### 7.1 Create `chess_game/texel/weights_io.py`
- [ ] Implement `save_weights(weights: EvalWeights, path: Path) -> None`
  - [ ] Serialize via `weights.to_dict()` and write as pretty-printed JSON
- [ ] Implement `load_weights(path: Path) -> EvalWeights`
  - [ ] Deserialize via `EvalWeights.from_dict()`
  - [ ] Raise `FileNotFoundError` if path doesn't exist
  - [ ] Raise `ValueError` with a clear message if JSON is malformed or missing fields
- [ ] Implement `load_weights_or_default(path: Path | None) -> EvalWeights`
  - [ ] If `path` is None or doesn't exist, return `EvalWeights.default()`
  - [ ] Otherwise call `load_weights(path)`

### 7.2 Integrate weight loading into `get_best_move`
- [ ] Add `weights: EvalWeights | None = None` parameter to `get_best_move()` in `ai.py`
- [ ] Thread `weights` through to `evaluate()` calls inside the minimax search
- [ ] When `weights` is None, fall back to `EvalWeights.default()`
- [ ] Update `BestMoveOptions` or create a separate mechanism — keep the API clean

### 7.3 Add default weight path convention
- [ ] Define `TUNED_WEIGHTS_PATH = Path("chess_game/chess/data/tuned_weights.json")`
      in a central location
- [ ] In `get_best_move`, auto-load tuned weights from this path if it exists and no
      explicit weights are provided (lazy-loaded and cached)
- [ ] Document this behavior in a module-level docstring

### 7.4 Unit tests for weight I/O
- [ ] `test_save_and_load_round_trip`
- [ ] `test_load_nonexistent_raises`
- [ ] `test_load_malformed_json_raises`
- [ ] `test_load_or_default_returns_default_when_no_file`
- [ ] `test_auto_load_tuned_weights_if_file_exists` (integration test)

---

## Phase 8: Calibration of the K constant

### 8.1 Add K calibration script
- [ ] In `chess_game/texel/loss.py`, implement `calibrate_and_save_k(db: PositionDB,
      weights: EvalWeights, path: Path) -> float`:
  - [ ] Run `calibrate_k()` on the collected dataset
  - [ ] Save the result to a small JSON file at `path`
  - [ ] Return the calibrated K
- [ ] Add CLI entry point: `python -m chess_game.texel.calibrate`
  - [ ] Args: `--db PATH`, `--weights PATH`, `--output PATH`
- [ ] Document: K should be calibrated once on a fresh dataset with the default
      weights before the first tuning run, then held fixed during tuning

### 8.2 Unit tests for K calibration
- [ ] `test_calibrate_k_returns_positive_float`
- [ ] `test_calibrate_k_reduces_mse_vs_default_k`

---

## Phase 9: End-to-end tuning runner

### 9.1 Create `chess_game/texel/tune.py`
- [ ] Implement the full tuning pipeline as `run_tuning(config: TuningConfig) -> EvalWeights`:
  - [ ] `TuningConfig` dataclass:
    - [ ] `collection_games: int = 500`
    - [ ] `collection_depth: int = 1`
    - [ ] `db_path: Path`
    - [ ] `output_weights_path: Path`
    - [ ] `initial_weights_path: Path | None = None`
    - [ ] `spsa_options: SPSAOptions`
    - [ ] `calibrate_k: bool = True`
    - [ ] `verbose: bool = True`
  - [ ] Step 1: Load or collect position database
  - [ ] Step 2: Load initial weights (`initial_weights_path` or default)
  - [ ] Step 3: Calibrate K if `calibrate_k` is True
  - [ ] Step 4: Run SPSA optimizer
  - [ ] Step 5: Save final weights to `output_weights_path`
  - [ ] Step 6: Print a summary (initial MSE, final MSE, improvement %)
  - [ ] Return final weights
- [ ] Add `__main__` CLI: `python -m chess_game.texel.tune`
  - [ ] Args: `--games N`, `--depth D`, `--db PATH`, `--output PATH`,
        `--initial-weights PATH`, `--iterations N`, `--verbose`
  - [ ] Example invocation printed in module docstring

### 9.2 Unit tests for tuning runner
- [ ] `test_run_tuning_produces_weights_file` — integration test: 20 games, 10 iterations,
      verify output file exists and loads cleanly
- [ ] `test_run_tuning_mse_does_not_increase` — MSE after tuning ≤ MSE before tuning
      (on the same dataset)

---

## Phase 10: Validation — tuned vs. baseline match

### 10.1 Create `chess_game/texel/validate.py`
- [ ] Implement `run_validation_match(tuned_path: Path, num_games: int = 100,
      depth: int = 2) -> ValidationResult`:
  - [ ] `ValidationResult` dataclass: `tuned_wins`, `baseline_wins`, `draws`,
        `tuned_win_rate: float`
  - [ ] For each game, alternate which side uses tuned vs. baseline weights
        (tuned plays White in even games, Black in odd games) to cancel out
        any first-mover advantage
  - [ ] Use `get_best_move(..., weights=tuned_weights)` vs.
        `get_best_move(..., weights=EvalWeights.default())`
  - [ ] Print a results table if verbose
- [ ] Add `__main__` CLI: `python -m chess_game.texel.validate`
  - [ ] Args: `--weights PATH`, `--games N`, `--depth D`
- [ ] Document: a tuned_win_rate > 55% over 100 games is considered a meaningful improvement

### 10.2 Unit tests for validation
- [ ] `test_validation_result_game_count_sums_correctly`
- [ ] `test_validation_alternates_sides` — verify tuned weights appear on both colors
- [ ] `test_identical_weights_win_rate_near_50_percent` (slow) — tuned = baseline
      should produce ~50% win rate

---

## Phase 11: Integration with TUI self-play

### 11.1 Surface tuned weights in the TUI
- [ ] In `tui.py`, when starting a self-play game, auto-load tuned weights from
      `TUNED_WEIGHTS_PATH` if the file exists
- [ ] Display a small indicator in the TUI status bar if tuned weights are active
      (e.g. "Engine: tuned weights" vs "Engine: default weights")

### 11.2 Add a "Run Tuning" option to the TUI (stretch goal)
- [ ] In the self-play config panel, add a "Improve from self-play" checkbox
- [ ] When checked, after the self-play game finishes, run a mini tuning pass
      (e.g. 50 games, 500 SPSA iterations) in a background worker thread
- [ ] Show progress in the TUI (a progress bar or "Tuning... X/500 iterations")
- [ ] On completion, save tuned weights and reload them for the next game
- [ ] This is a stretch goal — implement the CLI pipeline first

---

## Phase 12: Documentation and cleanup

### 12.1 Update `README.md`
- [ ] Add "Self-improving via Texel tuning" section explaining the workflow:
  1. Collect positions: `python -m chess_game.texel.collect --games 500 --db data/positions.jsonl`
  2. Tune weights: `python -m chess_game.texel.tune --db data/positions.jsonl --output data/tuned_weights.json`
  3. Validate: `python -m chess_game.texel.validate --weights data/tuned_weights.json`

### 12.2 Update `memory.md`
- [ ] Add entry recording the TEXEL1 implementation with timestamp and model

### 12.3 Final quality gate
- [ ] `uv run python -m ruff check chess_game tests` — clean
- [ ] `uv run python -m mypy chess_game` — no errors
- [ ] `uv run python -m pylint chess_game` — 10.00/10
- [ ] `uv run python -m pytest tests/ -q -m "not slow"` — all pass
- [ ] `uv run python -m pytest tests/ -q` — all pass (including slow suite)
- [ ] Commit and push to GitHub
- [ ] Tag as `v0.3`

---

## Phase ordering and dependencies

```
Phase 1 (EvalWeights dataclass)
    ↓
Phase 2 (refactor evaluator)       ← biggest risk, do first
    ↓
Phase 3 (PositionDB)               ← independent of Phase 2
    ↓
Phase 4 (data collection)          ← depends on Phase 2 + 3
    ↓
Phase 5 (loss function)            ← depends on Phase 2 + 3
    ↓
Phase 6 (SPSA optimizer)           ← depends on Phase 5
    ↓
Phase 7 (weight I/O + ai.py)       ← depends on Phase 1
    ↓
Phase 8 (K calibration)            ← depends on Phase 5
    ↓
Phase 9 (end-to-end runner)        ← depends on Phases 4–8
    ↓
Phase 10 (validation match)        ← depends on Phase 7 + 9
    ↓
Phase 11 (TUI integration)         ← depends on Phase 7
    ↓
Phase 12 (docs + final gate)
```

Phases 3 and 7 can be developed in parallel with Phase 2 since they have no
dependency on the refactored evaluator internals.

---

## Key risks and mitigations

| Risk | Mitigation |
|------|-----------|
| Refactoring evaluator breaks existing test suite | Do Phase 2 first; all existing tests must pass before moving on |
| Board reconstruction from position keys is expensive or lossy | Use FEN strings in the DB (Option A in Phase 5) |
| SPSA diverges or explodes | Clip weights to bounds; start with small step sizes; checkpoint frequently |
| Data collection at depth 1 produces games too random to be informative | Collect at depth 2 if time permits; use a large dataset to average out noise |
| Tuned weights perform worse than baseline | Validation match (Phase 10) catches this; keep baseline weights as fallback |
| Too many games needed for convergence | 500–2000 games at depth 1–2 is sufficient for a first pass; quality improves with more data |
