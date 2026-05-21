## Goal
- Fix remaining structural pylint warnings (Task 6: move_validation.py). Target: 10.00/10 pylint score.

## Constraints & Preferences
- Address tasks sequentially, updating TODO file after each.
- Run `pylint` and `pytest` after each phase; fix all warnings structurally (no pragmas).
- Commit and push to `origin/master` only when lint and tests pass.
- Keep public API stable where possible.

## Progress
### Done
- Task 1: Consolidated castling rights into `CastlingRights` dataclass; consolidated validators into `BoardValidators`.
- Task 2: Refactored `Board` public methods; extracted `game_state.py` and `PieceMoveChecker`.
- Task 3: Refactored `make_move` in `board.py` to reduce return statements (committed `e036195`).
- Task 4: Refactored `ai.py` — bundled params into `MinimaxParams` dataclass, extracted helpers; pylint 10.00/10 (committed `200435f`). Extracted castling-rights helpers to `castling.py`.
- Task 5: Refactored `ai.py` minimax — `MinimaxParams`, extracted TT and search helpers (committed `200435f`).
- Task 7: Refactored `attack_utils.py` — replaced if/elif chain in `piece_attacks_square` with `_ATTACK_CHECKERS` dispatch dict and wrapper functions.
- Task 8: Refactored `en_passant.py` — consolidated multiple return statements in `validate_en_passant_capture` into compound conditions and early returns.
- Task 9: Refactored `piece_movers.py` — `_MOVEMENT_GETTERS` dispatch dict, public `.square` API, `_pawn_direction()` helper.
- `piece_validation.py`: Fixed protected-access warnings — all 6 methods delegate through `board.is_valid_move()`.
- `board.py`: Consolidated validator instances into `BoardValidators` dataclass (`self._validators`).
- `board.py`: Simplified `_update_castling_rights` by extracting helpers into `castling.py`.
- `types.py`: Added `BoardValidators` dataclass.
- `tests/test_clone.py`: Updated to use `cloned._validators.*` instead of `cloned._move_validator`, etc.
- All committed in `c2af063`, pushed to `origin/master`.

### In Progress
- Task 6: `move_validation.py` — `too-many-return-statements` in `_get_pseudo_legal_moves` (8/6), `too-many-locals` in `_is_legal_move_for_piece` (16/15), `too-many-return-statements` in `_get_piece_pseudo_legal_moves` (7/6).

### Blocked
- None

## Key Decisions
- Structural refactors over pylint pragmas.
- Execution order: Tasks 1→2→3+4→5→7→8→9 completed. Task 6 remains.
- Used `MinimaxParams` dataclass to bundle minimax parameters.
- Used dispatch dicts (`_ATTACK_CHECKERS`, `_MOVEMENT_GETTERS`) to eliminate if/elif chains.
- Consolidated Board validators into `BoardValidators` dataclass.
- Extracted castling-rights update helpers to `castling.py`.
- Exposed `is_valid_move()` on `Board` for public API access.

## Next Steps
- Task 6: Refactor `move_validation.py`:
  - `_get_pseudo_legal_moves`: extract per-piece move generation into helpers, single return.
  - `_is_legal_move_for_piece`: extract board clone + move attempt, extract check verification.
  - `_get_piece_pseudo_legal_moves`: dispatch via dict, single return.
- Run `pylint` and `pytest` after Task 6.
- Update `docs/LINT_FIX3_TODO.md` status.
- Commit & push to `origin/master`.
- Address remaining `duplicate-code` warnings (move_validation.py attack geometry, en_passant.py).

## Critical Context
- Latest commit: `c2af063` ("Tasks 5-9: refactor board validators, attack_utils, en_passant, piece_movers, piece_validation")
- All 189 tests pass. Pylint rated 9.31/10.
- Remaining warnings after latest commit:
  - `move_validation.py:405:420`: duplicate-code (`_is_knight_attack` / `_is_king_attack` share row/col diff pattern)
  - `move_validation.py:111:118` vs `en_passant.py:49:57`: duplicate-code (en passant rank validation)
  - Task 6 warnings not yet addressed: `too-many-return-statements`, `too-many-locals` in `move_validation.py`

## Relevant Files
- `docs/LINT_FIX3_TODO.md`: Task tracker; Tasks 1-9 marked DONE.
- `chess_game/chess/board/board.py`: Uses `BoardValidators` dataclass. Public `is_valid_move()` method.
- `chess_game/chess/board/move_validation.py`: Target for Task 6 (returns/locals). Contains `_is_knight_attack`, `_is_king_attack` duplicate-code warnings.
- `chess_game/chess/board/attack_utils.py`: Uses `_ATTACK_CHECKERS` dispatch dict with wrapper functions.
- `chess_game/chess/board/en_passant.py`: Consolidated returns. Has duplicate-code with `move_validation.py:111-118`.
- `chess_game/chess/pieces/piece_movers.py`: Uses `_MOVEMENT_GETTERS` dispatch dict, public `.square` API, `_pawn_direction()` helper.
- `chess_game/chess/board/piece_validation.py`: 6 methods delegate to `_check_piece_move` → `board.is_valid_move()`.
- `chess_game/chess/types.py`: Contains `Piece`, `CastlingRights`, `BoardValidators`, `LegalMove` dataclasses.
- `chess_game/chess/board/castling.py`: Contains castling-rights helper functions.
- `chess_game/chess/board/game_state.py`: Holds `is_in_check`, `is_checkmate`, `is_stalemate`.
- `tests/test_clone.py`: Updated to use `_validators.*` attribute access.

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


