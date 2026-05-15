# LINT FIX3 TODO

All 189 tests pass, mypy is clean. Remaining issues are structural pylint warnings.

---

## Task 1: `chess_game/chess/board/board.py` — too-many-instance-attributes (11/7) ✅ DONE

### Subtask 1.1: Consolidate castling rights into a dataclass ✅ DONE
- Create a `CastlingRights` dataclass with `white_kingside`, `white_queenside`, `black_kingside`, `black_queenside`
- Replace the 4 individual attributes on Board with a single `castling_rights: CastlingRights`
- Update all references in board.py, castling.py, en_passant.py, and any test files

### Subtask 1.2: Consolidate validator instances ✅ DONE
- Evaluate whether `_move_validator`, `_move_executor`, `_promotion_validator`, `_en_passant_validator` can be lazily instantiated or stored as a single `_validators` container
- Or alternatively, add `# pylint: disable=too-many-instance-attributes` with a docstring justification

---

## Task 2: `chess_game/chess/board/board.py` — too-many-public-methods (26/20) ✅ DONE

### Subtask 2.1: Group piece-specific validators into a mixin or delegate class ✅ DONE
- Move `is_valid_rook_move`, `is_valid_bishop_move`, `is_valid_queen_move`, `is_valid_knight_move`, `is_valid_king_move`, `is_valid_pawn_move` into a `PieceMoveValidator` class that holds a Board reference
- Board delegates to this class, or these become module-level functions

### Subtask 2.2: Group check/checkmate/stalemate methods ✅ DONE
- Move `is_in_check`, `is_checkmate`, `is_stalemate` into a `GameStateException` class or module-level functions

### Subtask 2.3: Privatize methods and update callers ✅ DONE
- Prefix delegated methods with underscore to reduce public method count
- Update main.py, tests, and other callers to use module-level functions from game_state

---

## Task 3: `chess_game/chess/board/board.py` — too-many-return-statements (7/6) on `make_move` ✅ DONE

### Subtask 3.1: Extract validation checks into a single `_is_move_valid` method
- Move all the pre-execution validation (piece check, promotion, castling, en passant, move legality) into `_is_move_valid`
- `make_move` then becomes: validate → execute → update rights → switch turn → return True

### Subtask 3.2: Use early return guard clauses consistently
- Ensure all validation paths return False at the top of `_is_move_valid`, leaving a single True at the bottom

---

## Task 4: `chess_game/chess/board/board.py` — too-many-branches (14/12) on `_update_castling_rights` ✅ DONE

### Subtask 4.1: Extract king-move castling loss
- Move the "king moves → lose both rights" logic into `_clear_castling_for_color(color)`

### Subtask 4.2: Extract rook-move castling loss
- Move the "rook leaves home square" logic into `_clear_rook_castling(start_pos, color)`

### Subtask 4.3: Extract rook-capture castling loss
- Move the "rook captured on starting square" logic into `_clear_castling_for_captured_rook(end_pos)`

---

## Task 5: `chess_game/chess/ai.py` — minimax function refactoring ✅ DONE

### Subtask 5.1: too-many-arguments (6/5) & too-many-positional-arguments (6/5)
- Create a `MinimaxParams` dataclass: `board`, `depth`, `alpha`, `beta`, `maximizing_player`, `depth_limit`
- Replace individual parameters with `params: MinimaxParams`

### Subtask 5.2: too-many-locals (19/15)
- Extract move generation + scoring into helper methods: `_generate_and_score_moves(board, depth, ...)`
- Reduce locals in the main function body

### Subtask 5.3: too-many-branches (16/12)
- Extract checkmate/stalemate detection into `_evaluate_terminal_state(board, color)`
- Extract move cloning + evaluation loop into `_evaluate_move(cloned, move, ...)`

---

## Task 6: `chess_game/chess/board/move_validation.py` — too-many-return-statements & too-many-locals

### Subtask 6.1: `_get_pseudo_legal_moves` — too-many-return-statements (8/6)
- Build a list of candidate moves across all pieces, then return once at the end
- Or extract per-piece move generation into helpers: `_get_piece_moves(piece, square)`, returning a list

### Subtask 6.2: `_is_legal_move_for_piece` — too-many-locals (16/15)
- Extract board clone + move attempt into `_try_move_on_clone(board, from_sq, to_sq, promotion)`
- Extract check verification into `_would_leave_own_king_in_check(cloned, moving_color)`

### Subtask 6.3: `_get_piece_pseudo_legal_moves` — too-many-return-statements (7/6)
- Dispatch piece types via a dictionary mapping `PieceType -> handler_function`
- Single return at the end of the method

---

## Task 7: `chess_game/chess/board/attack_utils.py` — too-many-return-statements (7/6) ✅ DONE

### Subtask 7.1: `is_square_attacked` consolidation
- Extract per-attacker-type checks into helpers: `_check_pawn_attacks`, `_check_knight_attacks`, `_check_sliding_attacks`, `_check_king_attacks`
- Main function collects results and returns once

---

## Task 8: `chess_game/chess/board/en_passant.py` — too-many-return-statements (9/6) ✅ DONE

### Subtask 8.1: `validate_en_passant_capture` consolidation
- Extract individual guard checks into `_validate_en_passant_pawn`, `_validate_en_passant_target`, `_validate_en_passant_geometry`
- Main function calls guards, returns once at the end

---

## Task 9: `chess_game/chess/pieces/piece_movers.py` — too-many-return-statements, too-many-locals, too-few-public-methods ✅ DONE

### Subtask 9.1: `PieceMovers` — too-few-public-methods (1/2)
- Either add a second public method or convert to a module with standalone functions
- Alternatively add `# pylint: disable=too-few-public-methods` if it serves as a namespace

### Subtask 9.2: `get_pawn_moves` — too-many-return-statements (8/6)
- Collect moves in a list across forward, diagonal, and double-push branches
- Return the list once at the end

### Subtask 9.3: `_get_sliding_moves` — too-many-locals (19/15)
- Extract direction iteration into `_iterate_directions(start, directions)`
- Extract per-step square logic into `_step_along_ray(current, dr, dc)`

---

## Execution Order

1. Task 1 (board.py attributes) — foundational, affects other tasks
2. Task 2 (board.py methods) — depends on Task 1
3. Task 3 + Task 4 (board.py make_move / castling) — can run in parallel
4. Task 5 (ai.py minimax) — independent
5. Task 6 (move_validation.py) — independent
6. Task 7 (attack_utils.py) — independent
7. Task 8 (en_passant.py) — independent
8. Task 9 (piece_movers.py) — independent

After each task: run `python -m pytest tests/ -v` and `mypy chess_game/` to verify.
