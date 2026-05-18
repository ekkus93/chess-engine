# AGENTS.md

## Purpose

This repository is a correct, test-driven chess rules engine with a small CLI.
All changes must preserve correctness, consistency, and test coverage.

Primary design document: `docs/THE_PLAN.md`. When in doubt, follow that file.

## Key Design Rules

- Single source of truth:
  - All move legality is enforced in one place (the Board’s API).
  - No duplicate rules in main.py or elsewhere.
- No direct board mutation from UI:
  - main.py must never mutate board, turn, castling rights, or en_passant directly.
  - All changes must go through Board’s official apply-move interface.
- Separate pseudo-legal from legal:
  - Pseudo-legal: geometry and piece-specific rules.
  - Legal: additionally, must not leave the moving side’s king in check.
- Encode piece color:
  - Every square holds (color, piece_type), never a bare string like "Pawn".

## Coordinate Convention

Must be respected everywhere:

- row 0 = rank 8
- row 7 = rank 1
- col 0 = file a, col 7 = file h
- White pawns move toward smaller row indices.
- Black pawns move toward larger row indices.

Reference: `THE_PLAN.md` and `docs/coordinate_system.md`.

## Project Structure

- `chess_game/`
  - `chess/`
    - `types.py`, `color.py`, `coords.py`, `constants.py`, `move.py`
    - `ai.py`, `evaluation.py`
    - `board/`
      - `board.py` (top-level interface)
      - `move_execution.py`, `move_validation.py`
      - `game_state.py`, `castling.py`, `en_passant.py`
      - `promotion.py`, `attack_utils.py`, `path_validator.py`, `piece_validation.py`
    - `pieces/`
      - `piece_movers.py` (movement rules per piece type)
  - `main.py` (CLI; no direct board mutation)
- `tests/`
  - 227 tests; must continue to pass.
- `docs/`
  - `THE_PLAN.md` (authoritative for behavior/architecture)
  - `coordinate_system.md`

## Build, Test, Lint

- Run all tests:
  - `python -m pytest tests/ -q`
- Verbose:
  - `python -m pytest tests/ -v`
- Coverage:
  - `python -m pytest tests/ --cov=chess_game`
- Lint (if used):
  - `pylint chess_game/`
- Format:
  - `black chess_game/`
- Type check:
  - `mypy chess_game/`
- All changes must keep existing tests passing (unless intentionally updating them).

## Coding Guidelines

- Imports:
  - Use absolute imports: `from chess_game.chess.board import Board`
  - Group: stdlib, third-party, local.
- Naming:
  - Classes: PascalCase
  - Functions/variables: snake_case
  - Constants: UPPER_CASE
- Types:
  - Use explicit type hints.
  - Prefer clarity over cleverness.
- Structure:
  - Keep functions short and focused.
  - No global mutable state.
  - No duplicate rules across files.

## Testing Rules

- Must test real chess positions, not artificial nonsense.
- Must cover:
  - Normal moves, edge cases, invalid inputs
  - Special rules: castling, en passant, promotion, check, checkmate, stalemate
- Never allow “passing” tests based on impossible positions.
- If you change rules or behavior:
  - Add or adjust tests that explicitly capture the new behavior.

## Constraints for Changes

When modifying code:

- Do not change coordinate conventions unless:
  - You update THE_PLAN.md, docs, tests, and all code consistently.
- Do not introduce:
  - Direct board mutation in main.py
  - Multiple conflicting move-validation paths
- Always ensure:
  - `pytest tests/ -q` still passes.
  - The CLI (`python -m chess_game.main`) starts and accepts moves.

## Memory file
- You have access to a persistent memory file, memory.md, that stores context about the project, previous interactions, and user preferences.
- Use this memory to inform your decisions, remember user preferences, and maintain continuity across sessions. 
- Before sending back a response, update memory.md with any new relevant information learned during the interaction. Make sure to timestamp and format entries clearly.
- Include the GitHub Copilot model used for the entry in the heading line so memory history records both time and model (for example: `## 2024-06-01T12:00:00Z - GPT-5.4 - User prefers concise responses`).
- **NEVER fabricate or guess timestamps.** Always obtain the current time by running `date -u +"%Y-%m-%dT%H:%M:%SZ"` in the terminal immediately before writing the entry. If the entry describes a specific commit, use `git log -1 --format="%aI" <hash>` for that commit's actual timestamp.
- For each entry, add an ISO 8601 timestamp and a brief description of the information added. For example:
```markdown

## 2024-06-01T12:00:00Z - GPT-5.4 - User prefers concise responses
- User has expressed a preference for concise, to-the-point answers without unnecessary elaboration.
```


