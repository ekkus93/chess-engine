# Chess Engine

## What this is

A correct, test-driven chess rules engine with a minimax AI (alpha-beta pruning),
a Textual TUI, and a text-based CLI fallback.

**Correctness comes before features.**

### Coordinate Convention

- **row 0 = rank 8** (black's back rank), **row 7 = rank 1** (white's back rank)
- **col 0 = file a**, **col 7 = file h**
- White pawns move toward smaller row numbers, black pawns toward larger row numbers
- See `docs/coordinate_system.md` for the complete reference

## Current capabilities

- Full starting position and typed piece model (`Color` × `PieceType`)
- Legal move validation for all piece types including castling, en passant, and promotion
- Game status: check detection, checkmate, stalemate, threefold repetition
- AI: minimax with alpha-beta pruning, quiescence search, piece-square tables, opening book
- **Textual TUI** with human-vs-engine and self-play modes, configurable depth, move list, save to file
- Interactive CLI for simple text-based play
- **Self-improving via Texel tuning** — the engine can learn from self-play games and improve its evaluation weights

## Python environment

This project uses **uv** for environment management. Always prefix commands with `uv run`.

```bash
# Install dependencies (first time or after pyproject.toml changes)
uv sync --extra dev
```

## Running the TUI

```bash
uv run python -m chess_game.tui
```

The TUI opens a mode-selection screen. Choose **Human vs Engine** or **Self-play**,
set the engine depth (1–5), and press **Start Game**.

Move input inside the game: `e2e4`, `g1f3`, `e7e8q` (promotion suffixes: `q r b n`).
Type `resign` in the move field to resign. A **Save Game** button appears after the game ends.

## Running the CLI

```bash
uv run python -m chess_game.main
```

Move input format:

| Example  | Meaning                              |
|----------|--------------------------------------|
| `e2e4`   | Move from e2 to e4                   |
| `g1f3`   | Knight from g1 to f3                 |
| `e7e8q`  | Pawn to e8, promote to queen         |
| `e7e8r`  | Pawn to e8, promote to rook          |
| `e7e8b`  | Pawn to e8, promote to bishop        |
| `e7e8n`  | Pawn to e8, promote to knight        |
| `quit`   | Exit the game                        |

## Running the tests

```bash
# Fast suite (~100 seconds): unit tests, smoke tests, shallow search tests
uv run python -m pytest tests/ -q -m "not slow"

# Slow suite (~15-20 minutes): AI engine-strength regressions at depth 3+
# These tests run full games and are expensive but important for catching
# evaluation degradation from code changes.
uv run python -m pytest tests/ -q -m "slow"

# Full suite (fast + slow)
uv run python -m pytest tests/ -q
```

**Note:** Expensive engine-strength tests are marked `@pytest.mark.slow` and excluded from the
fast suite. Depth 1-2 searches run quickly; depth 3+ searches take minutes per test.

## Self-improving via Texel tuning

The engine can optimize its evaluation weights by learning from self-play game outcomes
using [Texel tuning](https://www.chessprogramming.org/Texel's_Tuning_Method) (gradient-free
SPSA optimization over ~460 tunable parameters).

```bash
# Step 1: Collect positions from self-play games (depth 1, fast)
uv run python -m chess_game.texel.collect --games 500 --depth 1 --db /tmp/positions.jsonl

# Step 2: Tune evaluation weights (5000 SPSA iterations)
uv run python -m chess_game.texel.tune --db /tmp/positions.jsonl \
    --output chess_game/chess/data/tuned_weights.json --iterations 5000 --verbose

# Step 3: Validate tuned vs. baseline (100 games at depth 2)
uv run python -m chess_game.texel.validate \
    --weights chess_game/chess/data/tuned_weights.json --games 100 --depth 2
```

Once `chess_game/chess/data/tuned_weights.json` exists, the engine automatically loads
it on startup. The TUI shows **"Engine: tuned"** vs **"Engine: default"** in the status bar.

## Linting and type checking

```bash
uv run python -m ruff check chess_game tests
uv run python -m mypy chess_game
uv run python -m pylint chess_game          # Target: 10.00/10
```

## Project structure

```
chess_game/
  main.py                  # CLI entry point
  tui.py                   # Textual TUI (human-vs-engine and self-play)
  self_play.py             # Headless self-play runner
  chess/
    __init__.py            # Public API: Board, Move, Piece, Color, PieceType, LegalMove
    types.py               # Piece, CastlingRights, LegalMove dataclasses
    color.py               # Color enum
    coords.py              # Coordinate constants and helpers
    constants.py           # Board size, piece values
    move.py                # Move parsing
    ai.py                  # Main AI: get_best_move, minimax entry
    evaluation.py          # Board position evaluation
    evaluation_tables.py   # Piece-square tables and constants
    ai_search_helpers.py   # Minimax helpers, TT, aspiration windows
    ai_move_ordering.py    # Move ordering for search
    ai_quiescence_helpers.py  # Quiescence search
    ai_capture_ordering.py    # Capture move ordering
    ai_board_utils.py      # Board utilities for AI
    ai_plan_guidance.py    # Plan-based evaluation signals
    ai_repetition_patterns.py # Repetition/draw detection
    opening_book.py        # Opening book lookup
    opening_development.py # Opening development scoring
    opening_move_ordering.py  # Opening-specific move ordering
    opening_guidance.py    # Opening guidance signals
    strategy_utils.py      # Shared strategy helpers
    pawn_structure_evaluation.py  # Pawn structure scoring
    piece_coordination.py  # Piece coordination signals
    threat_awareness.py    # Threat detection and response
    opponent_plans.py      # Opponent plan recognition
    structure_recognition.py     # Positional structure patterns
    conversion_guidance.py       # Winning-side conversion heuristics
    defensive_containment_guidance.py  # Heavy-piece defense vs passers
    defensive_endgame_guidance.py      # Endgame defense
    defensive_priorities.py            # Defensive move prioritization
    anti_drift_guidance.py        # Prevents aimless piece shuffling
    tactical_transition_guidance.py    # Transition move quality
    review_loop_guidance.py       # Transcript-driven practical guidance
    middlegame_practicality_guidance.py
    simple_endgame_guidance.py    # Low-material endgame guidance
    endgame_evaluation.py         # Endgame-specific evaluation
    endgame_choice_guidance.py    # Endgame repetition/cutoff policy
    endgame_emergency_defense.py  # Emergency defense triggers
    low_material_race_guidance.py
    low_material_coordination_guidance.py
    passer_race_guidance.py       # Heavy-piece passed-pawn race scoring
    heavy_piece_endgame_guidance.py
    rook_endgame_guidance.py
    forced_win_guidance.py        # Clearly won position handling
    pawn_race_move_ordering.py
    board/
      board.py             # Board class (top-level interface)
      move_execution.py    # Move execution logic
      move_validation.py   # Legal move validation
      game_state.py        # Check, checkmate, stalemate
      castling.py          # Castling rules and rights
      en_passant.py        # En passant rules
      promotion.py         # Promotion validation
      attack_utils.py      # Square attack detection
      path_validator.py    # Path clearance for sliders
      piece_validation.py  # Piece-specific validation
    pieces/
      piece_movers.py      # Movement rules per piece type
  texel/
    __init__.py
    collect.py      # Self-play data collection (python -m chess_game.texel.collect)
    loss.py         # Sigmoid + MSE loss + K calibration
    spsa.py         # SPSA optimizer
    tune.py         # End-to-end tuning pipeline (python -m chess_game.texel.tune)
    validate.py     # Validation match (python -m chess_game.texel.validate)
    weights_io.py   # Save/load EvalWeights to/from JSON
    position_db.py  # (FEN, outcome) position database
tests/                     # Test suite
docs/                      # Documentation
```
