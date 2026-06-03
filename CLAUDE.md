# Chess Engine — Project Context

## What this is

A correct, test-driven chess rules engine with a minimax AI (alpha-beta pruning) and text-based CLI.

**Correctness comes before features.** GUI is not yet implemented.

## Coordinate Convention

- **row 0 = rank 8** (black's back rank), **row 7 = rank 1** (white's back rank)
- **col 0 = file a**, **col 7 = file h**
- White pawns move toward smaller row numbers, black pawns toward larger row numbers

## Project Structure

```
chess_game/
  main.py                  # CLI entry point
  chess/
    __init__.py            # Public API: Board, Move, Piece, Color, PieceType, LegalMove
    types.py               # Piece, CastlingRights, BoardValidators, LegalMove dataclasses
    color.py               # Color enum
    coords.py              # Coordinate constants and helpers
    constants.py           # Board size, piece values
    move.py                # Move parsing
    ai.py                  # Main AI: get_best_move, minimax entry
    evaluation.py          # Board position evaluation
    ai_search_helpers.py   # Minimax helpers, TT, aspiration windows, selective extensions
    ai_move_ordering.py    # Move ordering for search
    ai_quiescence_helpers.py  # Quiescence search
    ai_capture_ordering.py   # Capture move ordering
    ai_repetition_patterns.py # Reposition detection for draws
    ai_board_utils.py      # Board utilities for AI
    ai_plan_guidance.py    # Plan-based evaluation signals
    strategy_utils.py      # Shared strategy helpers
    opening_book.py        # Opening book lookup
    opening_development.py # Opening development scoring
    opening_move_ordering.py # Opening-specific move ordering
    opening_guidance.py    # Opening guidance signals
    conversion_guidance.py # Winning-side conversion heuristics
    defensive_containment_guidance.py  # Heavy-piece defense vs passers
    defensive_endgame_guidance.py      # Endgame defense
    defensive_priorities.py             # Defensive move prioritization
    threat_awareness.py      # Threat detection and response
    anti_drift_guidance.py   # Prevents aimless piece shuffling
    tactical_transition_guidance.py # Transition move quality
    review_loop_guidance.py  # Transcript-driven practical guidance
    simple_endgame_guidance.py   # Low-material endgame guidance
    endgame_evaluation.py        # Endgame-specific evaluation
    endgame_choice_guidance.py   # Endgame repetition/cutoff policy
    endgame_emergency_defense.py # Emergency defense triggers
    low_material_race_guidance.py    # Low-material passed-pawn races
    low_material_coordination_guidance.py # Bishop/king sparse endings
    passer_race_guidance.py      # Heavy-piece passed-pawn race scoring
    heavy_piece_endgame_guidance.py  # Queen/rook ending guidance
    rook_endgame_guidance.py           # Rook-specific endgame
    forced_win_guidance.py             # Clearly won position handling
    pawn_race_move_ordering.py         # Pawn race ordering
    pawn_structure_evaluation.py       # Pawn structure scoring
    piece_coordination.py              # Piece coordination signals
    opponent_plans.py                  # Opponent plan recognition
    structure_recognition.py           # Positional structure patterns
    middlegame_practicality_guidance.py # Middlegame practicality
    evaluation_tables.py       # Piece-square tables
    board/
      board.py              # Board class (top-level interface)
      move_execution.py     # Move execution logic
      move_validation.py    # Legal move validation
      game_state.py         # Check, checkmate, stalemate
      castling.py           # Castling rules and rights
      en_passant.py         # En passant rules
      promotion.py          # Promotion validation
      attack_utils.py       # Square attack detection
      path_validator.py     # Path clearance for sliders
      piece_validation.py   # Piece-specific validation
    pieces/
      piece_movers.py       # Movement rules per piece type
tests/                       # Test suite
docs/                        # Documentation
```

## Python Environment

This project uses **uv** for environment management. A `.venv` (Python 3.11) is already created.
Always prefix commands with `uv run` — do **not** use the system or mambaforge Python directly.

## Running the CLI

```bash
uv run python -m chess_game.main
```

Move input: `e2e4`, `g1f3`, `e7e8q` (promotion suffixes: `q`, `r`, `b`, `n`).

## Running Tests

```bash
uv run python -m pytest tests/ -q -m "not slow"   # Fast suite
uv run python -m pytest tests/ -q -m "slow"       # Slow AI regressions
uv run python -m pytest tests/ -q                 # Full suite
```

## Linting

```bash
uv run python -m ruff check chess_game tests
uv run python -m mypy chess_game
uv run python -m pylint chess_game               # Target: 10.00/10
```

## Key Conventions

- **Structural fixes over pragmas.** Never use pylint disable comments to silence warnings — refactor the code instead.
- **Test-driven.** Add tests before or alongside implementation changes.
- **Pylint 10.00/10 is the gate.** Every change must pass `ruff`, `mypy`, `pylint`, and the full test suite before committing.
- **Keep public API stable.** `Board`, `Move`, `Piece`, `Color`, `PieceType`, `LegalMove` are the stable interface.
- **Coordinate system:** row 0 = rank 8, col 0 = file a. See `docs/coordinate_system.md` for details.
- **Memory file:** `memory.md` tracks project history. Update it with new relevant information, timestamped, including model used.

## Development Workflow

1. Address tasks sequentially when following a TODO tracker in `docs/`.
2. Run `ruff`, `mypy`, `pylint`, and `pytest` after each change.
3. Commit only when all checks pass.
4. Update TODO files to reflect progress.
5. Update `memory.md` with timestamps and model used.

## Relevant Files

- `pyproject.toml`: Dependencies, tool config (ruff, mypy, pytest markers)
- `mypy.ini`: Mypy configuration
- `memory.md`: Persistent project memory — always consulted at session start
