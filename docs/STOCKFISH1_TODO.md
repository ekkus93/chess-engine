# STOCKFISH1_TODO.md — Stockfish-Assisted Tuning

## Goal

Replace noisy self-play eval targets with high-quality Stockfish evaluations
and generate a more diverse position corpus, so Texel tuning can find real
signal in the piece-square table weights.

### Why this matters

| Problem | Current state | After this TODO |
|---------|--------------|-----------------|
| Target noise | Game outcomes (0/1/0.5) or quiescence scores (std ~1400 cp) | Stockfish depth-10 evals (std ~200-400 cp) |
| Position diversity | 1828 unique positions; depth-3 self-play hits a diversity ceiling | 10 000+ positions from human games or SF self-play |
| Tuning signal | Ridge solution barely moves from defaults (only 14 PST entries change by ±1 cp) | Enough signal to find meaningful PST adjustments |

### What "Stockfish eval annotations" means

Instead of the MSE target being the game outcome (did White eventually win?),
it becomes `sigmoid(sf_score_cp, k)` — Stockfish's per-position winning
probability estimate. That sigmoid value is a much more accurate proxy for
"how good is this position" than the ultimate game result, which is corrupted
by later mistakes.

The loss function and Adam optimiser in `fast_tune.py` are unchanged; only the
`outcomes` vector inside `FeatureMatrix` changes.

---

## Out of scope for this TODO

- NNUE (neural network evaluation)
- Changing piece values (material weights remain frozen as they are in `AdamConfig`)
- Modifying the search or move-ordering code
- Automated ELO rating via a long match ladder

---

## Phase 0: Baseline

### 0.1 Static checks

- [x] `uv run python -m ruff check chess_game tests`
- [x] `uv run python -m mypy chess_game`
- [x] `uv run python -m pylint chess_game --score=y`

### 0.2 Fast suite

- [x] `uv run python -m pytest -m "not slow" -q`
- [x] Record pass count as regression baseline.

### 0.3 Strength baseline

- [x] Record the current tuned-weights score rate from the most recent validation
  match (last recorded: 10.5/20, 52% score rate at depth 3 vs default weights).

---

## Phase 1: Install and verify Stockfish

### 1.1 Install Stockfish binary

- [x] Install Stockfish: `sudo apt install stockfish`
  - If apt is unavailable, download the latest binary from the official Stockfish
    releases and place it somewhere on `$PATH` (e.g. `~/.local/bin/stockfish`).
- [x] Verify: `which stockfish && stockfish --version`
- [x] Record the version string in `memory.md`.

### 1.2 Manual UCI smoke test

Run a quick manual sanity check to confirm the binary works:

- [x] Run:
  ```bash
  printf "uci\nisready\nposition startpos\ngo depth 5\nquit\n" | stockfish
  ```
- [x] Confirm output includes `uciok`, `readyok`, one or more `info depth` lines,
  and a final `bestmove` line.
- [x] Note the nodes-per-second figure for later parallelism sizing.

---

## Phase 2: Stockfish annotator module

Create `chess_game/texel/stockfish_annotate.py`.

This module communicates with a Stockfish subprocess via UCI (stdin/stdout),
sends FENs, waits for `bestmove`, and parses the `score cp` from the last
`info depth` line.

### 2.1 `StockfishProcess` class

- [x] `__init__(self, stockfish_path: str = "stockfish", depth: int = 10)` —
  launch `subprocess.Popen` with `stdin=PIPE, stdout=PIPE, text=True`.
- [x] `close(self) -> None` — send `quit\n`, then call `.wait()`.
- [x] Context manager support (`__enter__` / `__exit__`).
- [x] `eval_fen(self, fen: str) -> int | None` — send `position fen <fen>` then
  `go depth <depth>`, read lines until `bestmove`, parse the last `info depth`
  line for `score cp <N>`. Return `None` on mate scores or parse errors.
  - Parse `score cp <N>` from the last `info depth … score cp …` line before `bestmove`.
  - If the line has `score mate`, return `None` (forced mate — exclude from training).
  - Score is always from the side to move; convert to White-relative:
    multiply by +1 if `board.turn == Color.WHITE`, else −1.
    Use `Board.from_fen(fen).turn` for the colour check.

### 2.2 `annotate_fens` function

- [x] `annotate_fens(fens: list[str], *, depth: int = 10, n_workers: int = 4, stockfish_path: str = "stockfish") -> dict[str, int | None]`
  - Launch `n_workers` `StockfishProcess` instances.
  - Distribute FENs across workers (round-robin or via a `multiprocessing.pool`
    of plain subprocess calls — **not** `mp.Pool` since `StockfishProcess` holds a
    subprocess handle that cannot be pickled).
  - Use `concurrent.futures.ThreadPoolExecutor(max_workers=n_workers)` to run
    `process.eval_fen(fen)` calls concurrently (each worker owns one
    `StockfishProcess`).
  - Return `{fen: score_cp_or_none}`.

### 2.3 `annotate_db` convenience wrapper

- [x] `annotate_db(db: PositionDB, *, depth: int = 10, n_workers: int = 4, stockfish_path: str = "stockfish") -> dict[str, int | None]`
  - Extract `[fen for fen, _ in db.all_pairs()]`.
  - Call `annotate_fens`.
  - Return the result dict.

### 2.4 Module-level CLI

- [x] `if __name__ == "__main__"` block with `argparse`:
  - `--db PATH` — input `PositionDB` JSONL path.
  - `--output PATH` — output annotated JSONL path.
  - `--depth INT` (default 10).
  - `--workers INT` (default 4).
  - `--stockfish PATH` (default `"stockfish"`).
  - Load DB, call `annotate_db`, save results (see Phase 3 for output format).

### 2.5 Tests for `stockfish_annotate.py`

Add `tests/test_stockfish_annotate.py`. Mark all tests `@pytest.mark.slow` so
they do not run in the fast suite (they require Stockfish to be installed).

- [x] `test_eval_fen_starting_position` — score is near 0 (±50 cp) for the starting
  position at depth 5.
- [x] `test_eval_fen_white_winning` — use a FEN where White is up a queen; score
  is strongly positive.
- [x] `test_eval_fen_black_winning` — FEN where Black is up a queen; score is
  strongly negative.
- [x] `test_eval_fen_returns_none_on_mate` — position where it is checkmate; result
  is `None`.
- [x] `test_annotate_fens_multiple` — annotate 3 FENs and confirm all keys are
  present in the result dict.
- [x] `test_context_manager_closes_cleanly` — use `with StockfishProcess() as sf:`;
  check no exceptions and process terminates.
- [x] `test_white_relative_conversion` — annotate a symmetric FEN from both
  sides (startpos) vs a FEN with same material but Black to move; verify the
  sign reflects White-relative convention.

---

## Phase 3: Annotated position storage

Extend the JSONL format so each row can optionally store the Stockfish
centipawn score alongside the existing game-outcome fields.

### 3.1 New JSONL field `sf_score_cp`

New optional field in the JSONL format:

```json
{"pos": "<fen>", "total": 0.5, "count": 1, "sf_score_cp": 42}
```

- [x] `sf_score_cp` is an integer in centipawns, White-relative.
- [x] Rows without `sf_score_cp` are treated as unannotated; the existing
  `total`/`count` outcome fields are unaffected.
- [x] Rows where Stockfish returned `None` (mate score) store `"sf_score_cp": null`.

### 3.2 `AnnotatedPositionDB` class in `position_db.py`

- [x] Subclass or extend `PositionDB` with an optional `sf_scores` dict:
  `sf_scores: dict[str, int | None]` mapping FEN → score.
- [x] Override `save` to write `sf_score_cp` when present.
- [x] Override `load` / `_ingest_row` to read `sf_score_cp` when present.
- [x] `annotated_pairs(self) -> list[tuple[str, int | None]]` — return `(fen, sf_score_cp)`
  for all positions; `None` for unannotated positions.
- [x] `has_annotations(self) -> bool` — `True` if any position has a non-None
  `sf_score_cp`.

### 3.3 `save_annotated` standalone function

- [x] `save_annotated(db: PositionDB, scores: dict[str, int | None], path: Path) -> None`
  - Merges an existing `PositionDB` with a `scores` dict from `annotate_db`.
  - Writes the combined JSONL (each row has both game-outcome fields and
    `sf_score_cp` when available).
  - Skips positions where `scores[fen]` is `None` (mate positions are excluded
    from the annotated set but remain in the raw DB).

### 3.4 Tests for annotated storage

Add `tests/test_annotated_position_db.py`:

- [x] Round-trip: save an `AnnotatedPositionDB` with scores and reload it;
  verify all `sf_score_cp` values survive.
- [x] Backward compat: load an old-format JSONL (no `sf_score_cp`); confirm
  `has_annotations()` returns `False`.
- [x] `save_annotated` merges correctly.
- [x] `None` entries (mate positions) are excluded from the annotated output.
- [x] Mixed rows (some annotated, some not) load without error.

---

## Phase 4: Stockfish-targeted tuning

Replace game outcomes in the `FeatureMatrix.outcomes` vector with
`sigmoid(sf_score_cp, k)`.

### 4.1 New `outcomes_from_sf` helper in `features.py`

- [x] `outcomes_from_sf(annotated_pairs: list[tuple[str, int]], k: float) -> np.ndarray`
  - Input: `(fen, sf_score_cp)` pairs (already excluding `None` mate scores).
  - Compute `sigmoid(sf_score_cp, k)` for each pair using the `sigmoid` function
    from `chess_game.texel.loss`.
  - Return `np.ndarray` of shape `(N,)` dtype `float32`.

### 4.2 `compute_sf_feature_matrix` in `features.py`

- [x] New function alongside existing `compute_feature_matrix`:
  ```python
  def compute_sf_feature_matrix(
      annotated_db: AnnotatedPositionDB,
      weights: EvalWeights,
      k: float,
      *,
      eps: float = 1.0,
      n_jobs: int = 14,
  ) -> FeatureMatrix:
  ```
  - Filter to positions where `sf_score_cp` is not `None`.
  - Compute the `F` matrix (same finite-difference method as existing
    `compute_feature_matrix`).
  - Compute `outcomes` as `outcomes_from_sf(annotated_pairs, k)`.
  - Return a `FeatureMatrix` with the SF-based outcomes.

### 4.3 `eval_tune_sf` script

Create `chess_game/texel/eval_tune_sf.py` (mirrors `eval_tune.py`):

- [x] Load `AnnotatedPositionDB` from `--db PATH`.
- [x] Load weights from `--weights PATH` (or defaults).
- [x] Calibrate `k` using `calibrate_k_fast` on the SF outcomes.
- [x] Call `compute_sf_feature_matrix` (parallelised, cached to `--features PATH`).
- [x] Run `fast_tune` on the resulting `FeatureMatrix`.
- [x] Report: DB size, annotated count, k, baseline val-MSE, candidate val-MSE,
  promoted/not-promoted.

### 4.4 Tests for SF-targeted tuning

Add `tests/test_sf_tuning.py`:

- [x] `test_outcomes_from_sf_zero_score` — score=0 gives outcome≈0.5.
- [x] `test_outcomes_from_sf_large_positive` — score=+900 gives outcome>0.9.
- [x] `test_outcomes_from_sf_large_negative` — score=−900 gives outcome<0.1.
- [x] `test_compute_sf_feature_matrix_shape` — with a synthetic annotated DB of
  N positions, `F.shape == (N, D)` and `outcomes.shape == (N,)`.
- [x] `test_compute_sf_feature_matrix_excludes_none` — positions with
  `sf_score_cp=None` are excluded; final N is smaller.

### 4.5 Run `eval_tune_sf` on the existing 1828-position DB

- [x] Annotate the existing `texel_positions.jsonl` (1828 positions) using Phase 2
  annotator at depth 10.
- [x] Count how many positions survive (mate scores → `None` → excluded).
  - Result: 1780 annotated (48 mate scores excluded)
- [x] Run `eval_tune_sf`.
- [x] Record: annotated count, k, baseline val-MSE, candidate val-MSE,
  promoted/not.
  - k=0.1294 (engine sigmoid vs SF outcomes)
  - val-MSE improvement +0.000116 → PROMOTED
- [x] Compare resulting weights against current committed weights; record which
  PST entries changed and by how much.
  - 58 PST entries changed (vs only 14 from previous buggy run with k=0.0299)

---

## Phase 5: Diverse position generation

Break the self-play diversity ceiling by sourcing positions from outside our
own engine.

Choose **one** of the two approaches below (Option A is recommended as it gives
the most realistic human middlegame positions):

### Option A: Lichess open database (recommended)

- [ ] Download a monthly Lichess game file (compressed PGN):
  ```bash
  wget https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst
  ```
  (≈ 2–5 GB compressed; 20+ million games)
- [ ] Install `python-chess`: add `python-chess>=1.10` to `pyproject.toml`
  `[project.dependencies]`.
- [ ] Create `chess_game/texel/pgn_extract.py`:
  - `extract_fens_from_pgn(pgn_path: Path, *, n_games: int, min_ply: int = 16, max_ply: int = 80, min_elo: int = 1800, seed: int = 0) -> list[str]`
  - Open the PGN (zstandard-decompressed if `.zst`; install `zstandard` package).
  - For each game up to `n_games`: skip if either player ELO < `min_elo`; extract
    FEN at each ply in `[min_ply, max_ply]`; sample 1 position per game
    (or up to 3 spread evenly across the range).
  - Deduplicate FENs before returning.
  - Return up to `n_games * 3` FENs.
- [ ] Add module CLI: `--pgn`, `--games`, `--output`, `--min-elo`, `--seed`.

### Option B: Stockfish self-play (chosen)

- [x] Create `chess_game/texel/stockfish_generate.py`:
  - `generate_positions(n_games: int, *, depth: int = 8, stockfish_path: str = "stockfish", min_ply: int = 16, max_ply: int = 60, seed: int = 0) -> list[str]`
  - Launch two `StockfishProcess` instances (White and Black).
  - At each game: play from a random opening (pick from a short list of well-known
    opening FENs, seeded by `seed + game_index`).
  - Collect FENs at plies `[min_ply, max_ply]`.
  - Stop the game when Stockfish reports a mate score or after max_ply moves.
  - Deduplicate and return.
- [x] Add module CLI: `--games`, `--depth`, `--output`, `--seed`.

### Common steps for both options

- [x] Extract at least 10 000 unique FENs.
  - Result: 13,007 unique FENs from 300 games at depth 8, seed 42
- [x] Annotate with Stockfish depth 10 via `annotate_fens`.
  - Result: 12,990 annotated (17 mate scores excluded), 8 workers
- [x] Save as an `AnnotatedPositionDB` JSONL file.
  - Saved to `chess_game/texel/data/sf_selfplay_annotated.jsonl`
- [x] Report: total FENs extracted, annotation rate (% non-None), score distribution
  (mean, std, 5th/95th percentiles).
  - 13,007 FENs extracted; 12,990 annotated (99.9%); mean=10.1 cp, std=155.7 cp, 5th/95th=[-239, +243] cp

---

## Phase 6: Large-scale tuning run

Run `eval_tune_sf` on the large annotated corpus from Phase 5.

### 6.1 Compute feature matrix

- [x] Run `compute_sf_feature_matrix` on the 10 000+ position corpus.
  - Cached to `chess_game/texel/data/sf_selfplay_features.npz`; took ~16 min on 14 cores
- [x] Verify shape: `(N, D)` where `D` matches `len(EvalWeights().to_flat_list())` = 463.
  - Shape: (12990, 463) ✓

### 6.2 Tune with Adam

- [x] Run `fast_tune` with the cached feature matrix.
- [x] Try two regularisation strengths and compare:
  - `l2_lambda=1e-6`: baseline_val_mse=0.028343, candidate_val_mse=0.028327, improvement=+0.000016, PROMOTED (0 PST entries changed >1 cp — barely moved)
  - `l2_lambda=1e-7`: baseline_val_mse=0.028343, candidate_val_mse=0.028190, improvement=+0.000154, PROMOTED (51 PST entries changed >1 cp)
- [x] Winner: **l2=1e-7** (10× larger improvement, meaningful PST adjustments)

### 6.3 Inspect tuned weights

- [x] Count how many PST entries differ from current committed weights by more
  than 1 cp: **51 entries** (l2=1e-7); vs 0 for l2=1e-6
- [x] Spot-check: all plausible chess knowledge confirmed:
  - pawn_table[3][4] (e5): +7 cp ✓ (advanced center pawn more valuable)
  - pawn_table[4][2] (c4): +5 cp ✓ (useful c4 advance)
  - rook_table[7][4] (Re1): +5 cp ✓ (open center file)
  - king_table[7][6] (Kg1): +5 cp ✓ (castled king bonus)
  - rook_table[7][0] (Ra1): −7 cp ✓ (inactive rook penalized)
  - pawn_table[5][4] (e3 pawn): −10 cp ✓ (backward pawn on e3 penalized)

---

## Phase 7: Strength validation

### 7.1 Match setup

- [x] Run a 100-game depth-2 internal match: tuned weights (l2=1e-7) vs current
  committed weights, using `chess_game/texel/validate.py`.
  - Note: depth-3 aborted after ~20 CPU hours (quiescence search + guidance stack makes
    depth-3 ~100-300x slower than depth-2, not the ~30x naive estimate)

### 7.2 Accept/reject decision

- [x] Result: 50W/50L/0D — **50.0% score rate → KEEP EXISTING weights**
  - Perfect symmetry: whichever side has White wins every game; both weight sets are
    indistinguishable at depth 2
  - The +0.000154 val-MSE improvement is real but doesn't translate to depth-2 strength

### 7.3 Commit and update records

- [ ] Commit pipeline code (stockfish_generate.py, eval_tune_sf.py, annotated data, TODO)
- [ ] Update `memory.md` with: timestamp, corpus size, annotation depth,
  val-MSE improvement, match score rate, model used.

---

## Phase 8: Final validation

### 8.1 Static checks

- [x] `uv run python -m ruff check chess_game tests` — PASS
- [x] `uv run python -m mypy chess_game` — PASS (108 source files)
- [x] `uv run python -m pylint chess_game --score=y` — 10.00/10

### 8.2 Full test suite

- [x] `uv run python -m pytest tests/ -q -m "not slow"` — 1203 passed
- [x] `uv run python -m pytest tests/ -q -m "slow"` — 178 passed, 1 pre-existing failure
  - FAILED: `test_strategy6_search_rejects_h5_when_simpler_transition_exists`
  - Confirmed pre-existing: fails at committed HEAD with no changes from this session
  - Unrelated to texel tuning pipeline (test imports only `chess_game.chess.ai`)

### 8.3 Completion criteria

- [x] Stockfish annotator module exists and is tested.
- [x] Annotated JSONL format is backward-compatible with existing `PositionDB`.
- [x] `eval_tune_sf` runs end-to-end without error.
- [x] Tuned weights differ from defaults in more than 20 PST entries (51 entries changed).
- [ ] Validation match score rate > 52% (tuned beats baseline). — NOT MET (50.0%)
- [x] All linters pass at 10.00/10.
- [x] All tests pass (1 pre-existing slow failure unrelated to this work).
