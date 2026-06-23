# UCI1_TODO.md — Universal Chess Interface Implementation

## Scope

Implement the UCI protocol so the engine can be used with chess GUIs (Arena, cutechess,
Lichess bot API, etc.). The implementation lives in a single new module
`chess_game/uci.py` and a new entry point. Core search and eval code is not changed
except where explicitly noted.

### Out of scope for this TODO

- GUI frontend
- NNUE
- Pondering (searching on opponent's time)
- Multi-PV output (`setoption name MultiPV`)
- Full principal-variation tracking (beyond best move at each depth)

---

## UCI protocol reference (what must be supported)

```
GUI → Engine  |  Engine → GUI
--------------+-----------------
uci           |  id name <name>
              |  id author <author>
              |  uciok
isready       |  readyok
ucinewgame    |  (reset state)
position …    |  (setup board)
go …          |  info depth N score cp X nodes N time N pv <move>
              |  bestmove <move>
stop          |  bestmove <move>
quit          |  (exit)
```

---

## Phase 0: Baseline validation

### 0.1 Static checks

- [x] `uv run python -m ruff check chess_game tests`
- [x] `uv run python -m mypy chess_game`
- [x] `uv run python -m pylint chess_game --score=y`

### 0.2 Fast suite

- [x] `uv run python -m pytest -m "not slow" -q`
- [x] Record pass count as the baseline to protect against regressions.

---

## Phase 1: Move formatting utility

**Why first:** Every other phase emits moves in UCI notation. This is a pure utility
with no external dependencies.

### 1.1 `legal_move_to_uci(move: LegalMove) -> str`

Add a helper in `chess_game/uci.py`:

- [x] Convert `move.start` → 2-char algebraic via `index_to_algebraic(move.start)`.
- [x] Convert `move.end` → 2-char algebraic via `index_to_algebraic(move.end)`.
- [x] Append promotion character when `move.promotion` is not `None`:
  - `PieceType.QUEEN` → `"q"`
  - `PieceType.ROOK`  → `"r"`
  - `PieceType.BISHOP` → `"b"`
  - `PieceType.KNIGHT` → `"n"`
- [x] Return the concatenated string, e.g. `"e2e4"`, `"e7e8q"`.

### 1.2 Tests for `legal_move_to_uci`

Add `tests/test_uci.py`:

- [x] Normal move: `LegalMove(start=(6,4), end=(4,4))` → `"e2e4"`.
- [x] Promotion to queen: start=(1,4), end=(0,4), promotion=QUEEN → `"e7e8q"`.
- [x] Promotion to knight: promotion=KNIGHT → suffix `"n"`.
- [x] Promotion to rook: promotion=ROOK → suffix `"r"`.
- [x] Promotion to bishop: promotion=BISHOP → suffix `"b"`.
- [x] No promotion field → no suffix.
- [x] Corner squares: a1, h8.

---

## Phase 2: UCI state class

The state that persists between commands.

### 2.1 Define `UciState` dataclass in `chess_game/uci.py`

- [x] `board: Board` — current position (default: `Board()` for starting position).
- [x] `position_counts: dict[str, int]` — for threefold-repetition detection across
  the replayed move history (mirrors what `record_position` tracks in the CLI).
- [x] `debug: bool = False` — when True, engine may emit `info string …` diagnostics.

### 2.2 `reset(state: UciState) -> None`

- [x] Set `state.board = Board()`.
- [x] Clear `state.position_counts`.

---

## Phase 3: Individual command handlers

Each handler is a plain function that takes `(state: UciState, tokens: list[str])`
and writes to `sys.stdout`. Using `flush=True` on every print is mandatory — GUIs
read line-by-line and block if stdout is buffered.

### 3.1 `handle_uci(state, tokens)`

- [x] Print `id name ChessEngine`.
- [x] Print `id author <your name>`.
- [x] Print `uciok`.
- [x] (No options for now; add `setoption` handlers in future TODO.)

### 3.2 `handle_isready(state, tokens)`

- [x] Print `readyok`.

### 3.3 `handle_ucinewgame(state, tokens)`

- [x] Call `reset(state)` — clears board back to starting position and resets
  position counts.

### 3.4 `handle_quit(state, tokens)`

- [x] Call `sys.exit(0)`.

### 3.5 `handle_debug(state, tokens)`

- [x] Parse `tokens[1]` as `"on"` or `"off"`.
- [x] Set `state.debug` accordingly.
- [x] No output required; ignore unknown values silently.

### 3.6 Tests for command handlers

In `tests/test_uci.py`, using `capsys` to capture stdout:

- [x] `handle_uci` emits `id name`, `id author`, `uciok` (in that order).
- [x] `handle_isready` emits `readyok`.
- [x] `handle_ucinewgame` resets state (board back to starting position).
- [x] `handle_quit` calls `sys.exit`.
- [x] `handle_debug on` sets `state.debug = True`.
- [x] `handle_debug off` sets `state.debug = False`.

---

## Phase 4: `position` command

### 4.1 Parsing rules

The `position` command takes one of two forms:

```
position startpos [moves e2e4 e7e5 ...]
position fen <fen_string> [moves e2e4 e7e5 ...]
```

The `moves` keyword and subsequent tokens are optional.

### 4.2 `handle_position(state, tokens)`

- [x] If `tokens[1] == "startpos"`:
  - [ ] Set `state.board = Board()`.
  - [ ] Set `state.position_counts = {}`.
  - [ ] Record starting position: call `record_position(state.board, state.position_counts)`.
  - [ ] Locate `"moves"` keyword in remaining tokens; collect subsequent tokens as move strings.
- [x] If `tokens[1] == "fen"`:
  - [ ] Collect FEN tokens until `"moves"` keyword or end of tokens.
    - FEN is always 6 space-separated fields; collect exactly 6 tokens (or fewer if
      moves follows immediately).
  - [ ] Join collected FEN tokens with spaces and call `Board.from_fen(fen_str)`.
  - [ ] Set `state.position_counts = {}`.
  - [ ] Record the starting FEN position in position counts.
  - [ ] Locate `"moves"` keyword and collect subsequent tokens.
- [x] Replay each move string:
  - [ ] Call `parse_move_notation(move_str)` → `Move`.
  - [ ] Call `state.board.make_move(move.start, move.end, promotion=move.promotion)`.
  - [ ] If `make_move` returns `False`, print `info string illegal move <move_str>`
    (only when `state.debug`) and stop replaying.
  - [ ] After each successful move, call `record_position(state.board, state.position_counts)`.
- [x] Ignore unknown subcommands silently.

### 4.3 Tests for `handle_position`

- [x] `position startpos` → board matches initial `Board()`.
- [x] `position startpos moves e2e4` → board has White pawn on e4, it is Black's turn.
- [x] `position startpos moves e2e4 e7e5 g1f3` → knight on f3, Black's turn, three positions recorded.
- [x] `position fen <starting_fen>` → same as startpos.
- [x] `position fen <custom_fen>` → board matches custom position.
- [x] `position fen <fen> moves e2e4` → move replayed on top of FEN position.
- [x] FEN with all 6 fields (including halfmove clock and fullmove number) loads correctly.
- [x] Illegal move in replay is handled gracefully (no crash).

---

## Phase 5: `go` command (depth-based, blocking)

This phase implements `go depth N` — the simplest `go` form. Search is synchronous
(blocking); `stop` is not yet supported. This is sufficient for most offline GUI
connections.

### 5.1 Expose per-depth score from iterative deepening

`get_best_move()` currently returns only `Optional[LegalMove]` with no score. UCI
needs the score for `info` output.

**Decision:** Do not modify `get_best_move`'s signature. Instead, call
`search_root_depth` (already public, `chess_game/chess/ai.py:553`) directly from the
UCI `go` handler, implementing our own iterative deepening loop. This avoids
changing any existing API.

The UCI handler will need to import:

```python
from chess_game.chess.ai import search_root_depth, get_legal_moves
from chess_game.chess.ai_search_types import SearchContext, SearchStats, BestMoveOptions
from chess_game.chess.opening_book import get_bundled_opening_book
```

### 5.2 `_uci_search(board, depth, position_counts, state) -> Optional[LegalMove]`

Private helper called by `handle_go`. It:

- [x] Checks opening book first:
  - [ ] Call `get_bundled_opening_book().find_book_move(state.board)`.
  - [ ] If a book move is returned, immediately print `bestmove <uci>` and return.
- [x] Builds `SearchStats()` and `SearchContext(transposition_table={}, stats=stats, killer_moves=[], position_counts=position_counts, ...)`.
- [x] Runs iterative deepening loop `for current_depth in range(1, depth + 1)`:
  - [ ] Records `t0 = time.monotonic()` before the loop starts.
  - [ ] Calls `score, move = search_root_depth(board, current_depth, is_maximizing, previous_score, context)`.
  - [ ] After each depth, emits:
    ```
    info depth <current_depth> score cp <score> nodes <stats.nodes> time <elapsed_ms> pv <move_uci>
    ```
    - `elapsed_ms = int((time.monotonic() - t0) * 1000)`
    - `score` is from White's perspective (already is, since search returns White-centric score).
    - `pv <move_uci>` is the best move found at this depth (single move only for now).
    - Skip `pv` if `move is None`.
  - [ ] Updates `previous_score = score` and `best_move = move`.
- [x] Returns `best_move`.

### 5.3 `handle_go(state, tokens)`

- [x] Parse `tokens` for subcommands. Supported subcommands in this phase:
  - `depth N` — search to depth N (integer ≥ 1).
- [x] Default depth when not specified: `3` (matches existing CLI default).
- [x] Call `_uci_search(state.board, depth, state.position_counts, state)`.
- [x] Print `bestmove <uci>` where `<uci>` is `legal_move_to_uci(move)`.
- [x] If no move returned (game over position), print `bestmove (none)`.
- [x] All output must use `flush=True`.

### 5.4 Tests for `go depth N`

- [x] `go depth 1` on starting position emits `bestmove` with a legal move.
- [x] `go depth 2` emits `info depth 1 …` then `info depth 2 …` then `bestmove`.
- [x] `bestmove` response contains a valid UCI move string (4 or 5 chars).
- [x] `go depth 1` in a checkmate position emits `bestmove (none)`.
- [x] `go depth 1` in a stalemate position emits `bestmove (none)`.
- [x] Score in `info` line is an integer (centipawns).
- [x] `nodes` in `info` line is a non-negative integer.

---

## Phase 6: Time-limited search (`go movetime`)

### 6.1 Threading model

`get_best_move` and `search_root_depth` are synchronous. To honour `movetime` or
`stop`, the search must run on a background thread.

- [x] Add a module-level `_stop_event: threading.Event` in `chess_game/uci.py`.
- [x] `handle_go` launches `_uci_search` on a `threading.Thread(daemon=True)`.
- [x] The thread sets a `_search_done` event when complete.
- [x] `handle_stop` sets `_stop_event`; the search thread must check it.

**Hooking into the search to observe the stop flag:**

`search_root_depth` does not check an external stop flag. The cleanest option without
modifying the search: after each depth iteration in `_uci_search`, check
`_stop_event.is_set()` and break. This is coarse (each depth must complete) but
correct and requires zero changes to the existing search.

- [x] After completing each depth in the iterative deepening loop, check
  `_stop_event.is_set()`. If set, break and emit `bestmove` with the current best.

### 6.2 `go movetime N`

- [x] Parse `movetime N` (N in milliseconds).
- [x] Start search thread.
- [x] Start a timer thread that calls `handle_stop` after N ms.
- [x] Wait for search thread to complete.

### 6.3 `handle_stop(state, tokens=None)`

- [x] Set `_stop_event`.
- [x] Wait briefly for search thread to emit `bestmove` (join with short timeout).
- [x] If called while no search is running, ignore silently.

### 6.4 `go infinite`

- [x] Start search thread at a high depth (e.g., `depth=99`).
- [x] The thread runs until `_stop_event` is set.
- [x] Honour `stop` command to terminate.

### 6.5 Tests for time-limited search

- [x] `go movetime 500` returns `bestmove` within ~1 second.
- [x] `go movetime 500` emits at least one `info depth` line.
- [x] `stop` after `go infinite` causes `bestmove` to be emitted.
- [x] Multiple sequential `go` + `stop` cycles work without deadlock.

---

## Phase 7: Classical time controls (`go wtime btime`)

### 7.1 Time allocation

Parse the following `go` subcommands:

- [x] `wtime N` — White's remaining time in ms.
- [x] `btime N` — Black's remaining time in ms.
- [x] `winc N` — White's increment per move in ms (0 if not provided).
- [x] `binc N` — Black's increment per move in ms (0 if not provided).
- [x] `movestogo N` — moves remaining until next time control (optional, often absent).

### 7.2 `_allocate_time(wtime, btime, winc, binc, movestogo, color) -> int`

Return milliseconds to allocate for this move.

- [x] Select the relevant side's time and increment based on `color`.
- [x] If `movestogo` is provided: `allocated = time_remaining / movestogo + increment`.
- [x] If `movestogo` is absent (sudden death): `allocated = time_remaining / 30 + increment`.
- [x] Floor at 100 ms to avoid zero or negative allocations.
- [x] Cap at `time_remaining * 0.8` to avoid flagging.

### 7.3 `_time_to_depth(allocated_ms) -> int`

Map allocated time to a search depth (coarse approximation):

- [x] < 500 ms → depth 2
- [x] < 2000 ms → depth 3
- [x] < 8000 ms → depth 4
- [x] ≥ 8000 ms → depth 5

This table should be a module constant so it can be adjusted easily.

### 7.4 `handle_go` integration

- [x] If `wtime`/`btime` are present in tokens, call `_allocate_time`, then
  `_time_to_depth` to select depth, then run timed search with the computed depth.
- [x] `movetime` takes priority over `wtime`/`btime` if both are present.
- [x] `depth` takes priority over everything.

### 7.5 Tests for time allocation

- [x] `_allocate_time(60000, 60000, 0, 0, None, WHITE)` returns ~2000 ms.
- [x] `_allocate_time(60000, 60000, 1000, 1000, None, BLACK)` returns ~3000 ms.
- [x] `_allocate_time(5000, 5000, 0, 0, None, WHITE)` returns ≥ 100 ms (no crash on low time).
- [x] `_allocate_time(60000, 60000, 0, 0, 20, WHITE)` returns ~3000 ms.
- [x] `_time_to_depth(300)` returns 2.
- [x] `_time_to_depth(1000)` returns 3.
- [x] `_time_to_depth(5000)` returns 4.
- [x] `_time_to_depth(10000)` returns 5.

---

## Phase 8: UCI entry point

### 8.1 `uci_loop(input_stream=sys.stdin, output_stream=sys.stdout)`

The main dispatch loop in `chess_game/uci.py`:

- [x] Redirect `sys.stdout` to `output_stream` if provided (simplifies testing).
- [x] Create `UciState()`.
- [x] Clears `_stop_event` on startup.
- [x] Loop: `for line in input_stream: tokens = line.strip().split()`.
- [x] Skip empty lines.
- [x] Dispatch on `tokens[0]`:
  - `"uci"` → `handle_uci`
  - `"isready"` → `handle_isready`
  - `"ucinewgame"` → `handle_ucinewgame`
  - `"position"` → `handle_position`
  - `"go"` → `handle_go`
  - `"stop"` → `handle_stop`
  - `"debug"` → `handle_debug`
  - `"quit"` → `handle_quit`
  - anything else → ignore silently (required by UCI spec).
- [x] Catch and log exceptions per command without crashing the loop; emit
  `info string error: <message>` when `state.debug` is True.

### 8.2 `__main__` block

- [x] `chess_game/uci.py` must be runnable as `uv run python -m chess_game.uci`.
- [x] `if __name__ == "__main__": uci_loop()`.

### 8.3 Console script entry point

In `pyproject.toml`, add under `[project.scripts]`:

```toml
chess-uci = "chess_game.uci:uci_loop"
```

- [x] After adding, verify `uv run chess-uci` starts and responds to `uci\n`.

### 8.4 Tests for `uci_loop`

- [x] Full handshake: feed `"uci\n"` → output contains `uciok`.
- [x] Feed `"isready\n"` → output contains `readyok`.
- [x] Feed `"uci\nisready\nquit\n"` → clean exit.
- [x] Unknown command (e.g. `"xyzzy"`) → no crash, no output.
- [x] Loop handles multiple sequential commands correctly.

---

## Phase 9: Integration smoke test

### 9.1 Manual verification commands

Run these after completing Phase 8:

```bash
echo -e "uci\nisready\nposition startpos moves e2e4 e7e5\ngo depth 3\nquit" \
  | uv run python -m chess_game.uci
```

Expected output contains:
- [x] `id name ChessEngine`
- [x] `uciok`
- [x] `readyok`
- [x] At least one `info depth` line
- [x] `bestmove <move>` where `<move>` is a legal UCI move string

```bash
echo -e "uci\nisready\nposition fen rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1\ngo depth 2\nquit" \
  | uv run python -m chess_game.uci
```

- [x] Board set up correctly (Black to move after 1.e4).
- [x] `bestmove` is a legal Black move.

### 9.2 cutechess / Arena compatibility (optional manual check)

If `cutechess-cli` is available:

```bash
cutechess-cli -engine cmd="uv run python -m chess_game.uci" -engine cmd="stockfish" \
  -each proto=uci tc=10+0.1 -games 1
```

- [x] Engine completes the game without protocol errors.

---

## Phase 10: Linting and full test suite

### 10.1 Static checks

- [x] `uv run python -m ruff check chess_game tests`
- [x] `uv run python -m mypy chess_game`
- [x] `uv run python -m pylint chess_game --score=y` — must remain 10.00/10

### 10.2 Full fast suite

- [x] `uv run python -m pytest -m "not slow" -q` — all existing tests still pass.

### 10.3 New UCI tests

- [x] `uv run python -m pytest tests/test_uci.py -v`

---

## Completion criteria

This implementation is complete only when:

- [x] `python -m chess_game.uci` starts and responds to the UCI handshake.
- [x] `position startpos moves …` correctly replays a game.
- [x] `position fen … moves …` correctly loads a FEN and replays moves.
- [x] `go depth N` emits `info depth` lines and `bestmove`.
- [x] `go movetime N` respects the time limit (±1 depth overshoot is acceptable).
- [x] `go wtime … btime …` allocates reasonable time and responds with `bestmove`.
- [x] `stop` causes a running search to emit `bestmove` and terminate cleanly.
- [x] Unknown commands are silently ignored (required by spec).
- [x] Ruff, mypy, and pylint all pass.
- [x] All pre-existing fast tests still pass.
- [x] `tests/test_uci.py` covers all handlers.

---

## Files created / modified

| File | Change |
|------|--------|
| `chess_game/uci.py` | New — UCI protocol implementation |
| `tests/test_uci.py` | New — UCI tests |
| `pyproject.toml` | Add `chess-uci` console script |

No changes to `chess_game/chess/ai.py` or any other engine file are required.
