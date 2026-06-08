# Texel Tuning Guide

## Overview

The engine supports automatic weight tuning using the Texel method: optimise a
sigmoid-based mean-squared-error (MSE) loss over a database of (position, game
outcome) pairs collected from self-play games.

The tunable weights live in `chess_game/chess/eval_weights.py` (`EvalWeights`).
The tuning pipeline lives in `chess_game/texel/`.

---

## Quick-start

```bash
# Collect 500 self-play games at search depth 1 and save to positions.jsonl
uv run python -m chess_game.texel.collect \
    --games 500 --depth 1 \
    --db positions.jsonl --verbose

# Calibrate k, tune weights, save result
uv run python -m chess_game.texel.tune \
    --db positions.jsonl \
    --output chess_game/chess/data/tuned_weights.json \
    --games 0 --verbose

# Validate: play tuned vs default weights for 50 games
uv run python -m chess_game.texel.validate \
    --weights chess_game/chess/data/tuned_weights.json \
    --games 50 --depth 2
```

---

## Pipeline stages

### 1. Collect positions (`collect.py`)

Plays self-play games and stores positions with their game outcome in a
`PositionDB` (JSONL file).

Key options (`CollectionOptions`):

| Field | Default | Description |
|-------|---------|-------------|
| `db_path` | — | Path to the JSONL database |
| `num_games` | 200 | Number of self-play games |
| `depth` | 1 | Search depth per move |
| `weights` | `None` | Weights for self-play (defaults to current tuned weights) |
| `skip_opening_plies` | 10 | Skip first N plies (don't store opening positions) |
| `max_moves` | 200 | Max plies per game before declaring a draw |
| `seed` | `None` | Random seed for reproducibility |
| `max_move_result` | `"draw"` | What to do when `max_moves` is reached: `"draw"` or `"discard"` |

Draw detection covers: checkmate, stalemate, fifty-move rule, insufficient
material, and threefold repetition.

### 2. PositionDB (`position_db.py`)

A JSONL store that aggregates multiple game observations for the same FEN key
into a `PositionStats(total, count)` record.  `all_pairs()` returns the mean
outcome for each position.  `split(validation_fraction=0.20, seed=0)` provides
a deterministic 80/20 train/validation split.

File format (new):
```json
{"pos": "<fen>", "total": 1.5, "count": 2}
```

Old format (`{"pos": "...", "outcome": ...}`) is auto-migrated on load.

### 3. Calibrate k (`loss.py` → `calibrate_and_save_k`)

The sigmoid win probability is:

```
P(White wins) = 1 / (1 + 10^(−k · score / 400))
```

`k` scales the evaluation-to-probability mapping.  It is calibrated by
minimising MSE on the current position set before tuning begins.  The result
is saved to `<db>.k.json` so it can be reused across runs.

### 4. SPSA optimisation (`spsa.py`)

Simultaneous Perturbation Stochastic Approximation — estimates gradients by
perturbing each weight positively and negatively simultaneously.  Parameters:

| Field | Default | Description |
|-------|---------|-------------|
| `max_iterations` | 5000 | SPSA gradient steps |
| `batch_size` | 256 | Positions sampled per step |
| `a` / `c` | 100 / 10 | Learning rate scale / perturbation size |
| `alpha` / `gamma` | 0.602 / 0.101 | SPSA decay exponents |
| `loss_options` | `None` | `LossOptions` from calibration |
| `checkpoint_path` | `None` | Path for checkpoint saves |

### 5. Validate (`validate.py`)

Plays tuned vs baseline (default `EvalWeights`) for `num_games` games (colour
alternated each game).  Reports `ValidationResult`:

- `tuned_wins`, `baseline_wins`, `draws`
- `tuned_win_rate` = wins / total
- `tuned_score_rate` = (wins + 0.5 · draws) / total  ← better small-sample metric

A `seed` parameter makes validation reproducible.

---

## Online learning

After each self-play game in the TUI, `online_learning.record_game_and_update_weights()`
can update the weights incrementally.

It uses an 80/20 train/validation split.  The candidate weights (after a mini
SPSA pass on the training set) are only promoted if they achieve lower MSE on
the **held-out validation set**.  Otherwise the existing weights are kept
unchanged.  A backup is saved as `<weights>.backup.json` before any promotion.

Configure via `OnlineLearningConfig`.

---

## Reproducing a run

Set `seed` on `CollectionOptions` and `ValidationOptions` (or
`run_validation_match(..., seed=42)`) for fully deterministic pipelines.

SPSA itself is stochastic by design; the loss function can be made deterministic
via `LossOptions(deterministic=True)`.

---

## File layout

```
chess_game/texel/
  collect.py        # Self-play collection
  loss.py           # Sigmoid loss, MSE, calibration
  spsa.py           # SPSA optimiser
  tune.py           # End-to-end pipeline
  validate.py       # Match validation
  online_learning.py # Incremental weight updates
  position_db.py    # Aggregated position database
  weights_io.py     # Load/save EvalWeights
```
