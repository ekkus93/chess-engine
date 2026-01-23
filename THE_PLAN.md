# Chess Program Plan

## Overview
- Python CLI application.
- Separate game logic from UI for future UI swaps.
- Player chooses color and alpha‑beta depth before starting.
- Full chess rules enforced (en‑passant, castling, stalemate, check, check‑mate, etc.).
- Computer uses an alpha‑beta pruning search.

## High‑Level Architecture
1. **Core engine** (`chess_engine/`)
   - `Board` representation and state.
   - Move generation, legality checks, and rule enforcement.
   - Game state transitions and termination detection.
   - Evaluation function for the search.
   - Alpha‑beta search implementation.
2. **CLI UI** (`cli/`)
   - Prompt player for color and depth.
   - Render board in ASCII.
   - Read player moves (SAN or algebraic).
   - Display results, game status, and prompts.
3. **Entry point** (`main.py`)
   - Orchestrates engine and UI.

## Key Modules & Files
- `chess_engine/board.py` – Board state, piece placement.
- `chess_engine/move.py` – Move representation, parsing.
- `chess_engine/engine.py` – Game logic, turn management.
- `chess_engine/search.py` – Alpha‑beta algorithm.
- `cli/ui.py` – Rendering and input handling.
- `tests/` – Unit tests for board rules, move legality, search.

## Future Extensibility
- Swap CLI with GUI or web front‑end by implementing a new UI module that consumes the same engine API.
- Replace or tweak the evaluation function or search depth limits.
- Add features: time controls, PGN import/export, network play.

## Development Milestones
1. **Board representation** – basic board, piece types.
2. **Move generation** – all legal moves, including special rules.
3. **Game flow** – alternating turns, check/check‑mate detection.
4. **Alpha‑beta search** – depth‑controlled search, evaluation.
5. **CLI UI** – interactive loop, display board, handle input.
6. **Testing** – unit tests for all components.

## Notes
- Use Python 3.11+.
- Avoid external chess libraries to keep the logic explicit.
- Keep data structures immutable where possible for easier reasoning.
- Ensure the UI is minimal; focus on correctness in the engine.

---

Feel free to review and suggest changes.
