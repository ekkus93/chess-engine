# Rust Chess Console Application Specification

Status: proposed implementation specification

Companion task plan: `docs/RUST_CONSOLE_TODO.md`

Baseline `master` when this specification was authored: `0964371d93b5a54c340769acf2909b86b47da7a6`.

## 1. Purpose

Add a native Rust, human-facing console application for the authoritative Rust chess engine.

The new executable is `crates/chess-console`. It is deliberately different from both existing terminal-facing programs:

- `chess-uci` is a machine-facing Universal Chess Interface process adapter;
- `chess-tui` is a full-screen Ratatui/Crossterm terminal UI;
- `chess-console` will be a simple interactive command/prompt application that reads human commands and prints ordinary text output.

The console application must use the same Rust rules and search implementation as the TUI and UCI engine. It must not introduce a second chess implementation, launch the historical Python engine, or hide search failures behind emergency moves.

This milestone also introduces a small shared Rust application-support crate, `chess-app`, so that `chess-tui` and `chess-console` can share gameplay/session/search lifecycle code instead of independently reimplementing subtle state machines.

## 2. Goals

The milestone should provide all of the following:

1. A human can launch a normal console program and play against the Rust engine.
2. The human can choose White or Black and a fixed engine depth.
3. The board is printed as ordinary ASCII text with coordinates and deterministic orientation.
4. Human moves use UCI coordinate notation such as `e2e4` and `e7e8q`.
5. Invalid and illegal moves fail visibly and transactionally.
6. Engine thinking runs outside the console command-processing path and exposes useful search information.
7. A self-play mode supports automatic play plus pause/resume/one-ply step semantics.
8. Console commands expose board, move history, status, engine information, resignation, save, new game/menu, help, and quit actions.
9. Active searches are cancelled/joined safely when a game is abandoned or the process exits through a supported path.
10. Search failures preserve the last valid game state and are never converted into random/first-legal fallback moves.
11. The completed TUI retains its current behavior after shared code is extracted.
12. No production/runtime Python dependency is introduced.

## 3. Non-goals

This milestone does not:

- change engine strength, evaluation weights, search policy, transposition policy, opening-book policy, or tuning-candidate activation state;
- implement a new chess rules engine;
- turn `chess-uci` into a human console UI;
- spawn `chess-uci` and parse UCI text internally;
- revive the historical Python console or TUI as runtime code;
- add online learning or automatic weight mutation;
- add a GUI, web server, network chess protocol, multiplayer service, or remote engine transport;
- require SAN or PGN input;
- claim a save file is PGN unless valid PGN support is separately implemented and tested;
- silently discover books, weights, configuration, or save destinations from conventional filesystem paths;
- make broad search/evaluation refactors merely because shared frontend code is being reorganized.

## 4. Existing state and architectural motivation

At the baseline SHA, the active workspace already contains:

- `chess-core` for rules, game state, notation, history, hashing, and legal move semantics;
- `chess-search` for evaluation, iterative deepening, transposition state, limits, diagnostics, and cancellation;
- `chess-uci` for the external UCI process protocol;
- `chess-tui` for the full-screen native terminal UI.

The TUI already contains substantial presentation-neutral behavior that a console application would otherwise have to duplicate. In particular, current TUI code owns:

- `GameConfig`;
- `GameOutcome`;
- `GameSession`;
- game generation and search request IDs;
- legal human move resolution through `chess-core`;
- human-vs-engine turn scheduling;
- self-play scheduling/pause/resume/step;
- terminal-state detection;
- stale search result rejection;
- typed search progress/completion/cancellation/failure events;
- the bounded search worker and cancellation path;
- strict rejection of search fallback moves;
- pure board, move-history, outcome, and search-metric text formatting.

Those behaviors are valuable beyond Ratatui. Duplicating them in `chess-console` would create two sources of truth for cancellation, generation handling, fallback rejection, and game/session state. That is exactly the class of duplication this project should avoid.

At the same time, current TUI state also includes presentation-specific concepts that must *not* be pushed into a supposedly generic application crate, including:

- `MenuState` and menu cursor selection;
- `AppScreen`;
- Ratatui confirmation overlays;
- save-path text editing overlays;
- the move-entry text buffer;
- terminal layout decisions;
- Ratatui/Crossterm lifecycle state;
- TUI shortcut/focus behavior.

The extraction therefore must be selective rather than moving `chess-tui` wholesale into another crate.

## 5. Target workspace architecture

### 5.1 New crates

Add two workspace members:

```text
crates/chess-app
crates/chess-console
```

`chess-app` is a safe Rust library for shared interactive-frontend application/session behavior.

`chess-console` is a safe Rust binary for human-facing line/command interaction.

Both should use workspace package metadata and workspace lint configuration and should use `#![forbid(unsafe_code)]`.

### 5.2 Dependency direction

The intended workspace slice is:

```text
                         +-------------------+
                         | chess-uci         |
                         | UCI protocol      |
                         +---------+---------+
                                   |
                                   +------------------+
                                                      |
+-------------------+       +-------------------+     v
| chess-tui         | ----> | chess-app         | --> chess-search
| Ratatui/Crossterm |       | shared app layer  |       |
+-------------------+       +---------+---------+       v
                                      |             chess-core
+-------------------+                 |
| chess-console     | ----------------+
| human console     |
+-------------------+
```

More precisely:

- `chess-app` may depend directly on `chess-core` and `chess-search`;
- `chess-tui` may depend on `chess-app` and directly on `chess-core`/`chess-search` only where presentation code genuinely needs their public value types;
- `chess-console` should primarily depend on `chess-app`, with direct `chess-core`/`chess-search` dependencies only when a non-reexported public value type is genuinely needed;
- `chess-uci` remains independent of `chess-app` unless a future, separately reviewed task demonstrates a real benefit;
- `chess-core` and `chess-search` must never depend on `chess-app`, `chess-tui`, `chess-console`, UCI, filesystem, or terminal code.

`chess-app` is an outward application-support layer, not a new engine layer.

### 5.3 Do not route the console through UCI

`chess-console` must not normally launch `chess-uci` as a subprocess.

Doing so would introduce unnecessary process management, pipe buffering, UCI serialization/parsing, cancellation races, and another place where protocol failures could be misclassified. Since all components are in one Rust workspace, the console should call shared Rust application/search APIs in-process.

The UCI executable remains available for external chess GUIs and protocol clients and is not modified merely to support this console application.

## 6. `chess-app` ownership contract

### 6.1 Shared gameplay/session controller

Extract the presentation-neutral subset of the current TUI application state into a controller such as `GameController` or an equivalently explicit name.

The shared controller owns:

- optional current `GameSession`;
- generation IDs for replacing/restarting games;
- search request IDs;
- pending `SearchRequest` state;
- legal human move submission;
- current game terminal-state refresh;
- human-vs-engine engine scheduling;
- self-play automatic scheduling policy;
- self-play pause/resume/step state;
- resignation outcome;
- stale `EngineEvent` rejection;
- application of exact completed engine moves only after current-position legality verification;
- visible/shared status text where useful to both frontends.

The shared `GameSession` should own only session/game concepts useful to multiple interactive frontends, such as:

- authoritative `chess_core::Game`;
- `GameConfig`;
- generation;
- active search ticket;
- thinking state;
- self-play auto state;
- outcome;
- engine metrics;
- shared status/error message if retained.

The following should remain frontend-specific rather than being carried into `chess-app::GameSession` merely because they exist in the TUI today:

- TUI move-input editing buffer;
- TUI screen/menu selection state;
- TUI overlay state;
- TUI pending overwrite dialog path;
- TUI `should_quit` state;
- terminal layout state.

If current TUI tests reveal another field is purely presentation state, keep it in `chess-tui`.

### 6.2 Shared search worker

Move the current interactive search worker into `chess-app` with semantics preserved.

Shared types should include, or be equivalent to:

- `SearchTicket`;
- `SearchRequest`;
- `SearchMetrics`;
- `EngineEvent`;
- `SearchWorker`;
- `SearchWorkerError`.

The worker must continue to:

- create a bounded owned search thread;
- use existing `chess-search::SearchLimits` and cancellation support;
- search a safely owned/snapshotted game state;
- report typed progress;
- report typed exact completion;
- report cancellation separately from failure;
- report channel/thread/search errors visibly to the frontend boundary;
- join on explicit shutdown/cancellation paths;
- reject emergency/fallback search results as playable moves.

Presentation-specific names in thread names or error text such as `chess-tui-search` or `TUI rejected the search fallback` must become neutral shared-application wording without weakening the policy.

### 6.3 Fallback policy is part of the shared interactive contract

For `chess-app` interactive frontends, a move is playable only when it comes from the exact completed iterative-deepening result accepted by the existing TUI policy.

The shared worker/controller must never silently:

- use a random legal move;
- use the first legal move;
- play a `SearchResult` fallback/emergency move;
- lower depth and retry;
- switch search algorithm or search limits;
- switch to Python;
- reuse an obsolete best move after cancellation;
- convert a worker panic/channel failure into a legal chess move.

This is a correctness boundary, not merely a TUI preference.

This extraction must not unintentionally change `chess-uci` policy. UCI behavior remains governed by its own existing tests and specification.

### 6.4 Shared pure text helpers

The current TUI has pure formatting functions that are useful to both terminal frontends. Extract the presentation-library-independent subset into a module such as `chess_app::text`.

Good candidates include:

- board orientation enum;
- orientation from `GameConfig`;
- ASCII board lines;
- piece symbol formatting;
- move-history formatting;
- turn/check/draw-claim status text;
- outcome formatting;
- score formatting;
- search metrics formatting;
- color and draw-reason names.

Do *not* move Ratatui layout calculations, terminal minimum sizes, widgets, styles, colors, rectangles, or Crossterm behavior into `chess-app`.

The console may use a slightly more compact textual presentation, but shared helpers should be preferred when they prevent semantic drift in board orientation, score/mate formatting, or outcome wording.

### 6.5 Save primitives

Both frontends need explicit, fail-visible, atomic save behavior.

The shared layer may own neutral primitives such as:

- a structured save record/snapshot derived from a game session;
- deterministic field ordering;
- atomic same-directory temporary-file write and rename;
- common validation/error propagation.

However, the extraction must not silently change the already-shipped TUI save bytes merely to make the banner generic. The existing TUI `v1` serialization header should remain byte-compatible unless a deliberate version migration is separately documented and tested.

A practical design is:

- `chess-app` owns `SaveRecord`/equivalent and `write_game_atomic`;
- `chess-tui` keeps a thin serializer wrapper that preserves `Chess Engine Rust TUI save v1`;
- `chess-console` has a corresponding deterministic console serializer, for example `Chess Engine Rust Console save v1`.

Neither format is called PGN.

## 7. TUI refactor compatibility requirements

The shared-layer extraction is not allowed to regress the completed TUI.

Before console-specific behavior is considered complete:

- all existing `chess-tui` unit/integration tests must remain green;
- all existing TUI hardening tests must remain green;
- the real PTY acceptance suite must remain green;
- Human/White and Human/Black behavior must remain unchanged;
- self-play pause/resume/step behavior must remain unchanged;
- save success/failure and overwrite confirmation behavior must remain unchanged;
- quit/new-game/menu cancellation behavior must remain unchanged;
- terminal resize and terminal restoration behavior must remain unchanged;
- no TUI-visible search fallback may appear;
- the refactor must not introduce a `chess-tui -> chess-uci` dependency.

Move tests into `chess-app` where they are testing shared controller/worker behavior, but retain enough TUI integration coverage to prove the wiring is still correct.

Do not mark a moved test as equivalent merely because the underlying unit test is green; the TUI-facing integration boundary still requires regression coverage.

## 8. Console interaction model

### 8.1 General style

`chess-console` is intentionally an ordinary scrolling console application.

It should:

- print normal text to stdout/stderr;
- avoid Ratatui widgets and the alternate screen;
- avoid requiring terminal colors for correctness;
- keep prompts understandable on monochrome terminals;
- work with normal keyboard input;
- keep the board and history readable in captured logs;
- avoid clearing prior output, because scrollback is useful for debugging and play review.

ANSI color may be added later as an optional enhancement, but initial correctness must not depend on it.

### 8.2 Startup menu

A representative startup flow is:

```text
Rust Chess Console

1. Human vs Engine
2. Self-play
3. Quit

Select [1]:
```

For Human vs Engine:

```text
Play as:
1. White
2. Black
Select [1]:

Engine depth [3]:
```

For Self-play:

```text
White engine depth [3]:
Black engine depth [3]:
```

Input validation must be explicit. Empty input accepts the displayed default. Invalid numeric/range input does not silently clamp to a different value; it reports the accepted range and prompts again.

The first milestone uses the same supported fixed-depth range as the shared interactive application policy unless the implementation discovers a strong reason to expose a narrower console range.

### 8.3 Board rendering

At game start and after each applied move, print the board with file/rank labels.

White-at-bottom example:

```text
    a   b   c   d   e   f   g   h
  +---+---+---+---+---+---+---+---+
8 | r | n | b | q | k | b | n | r |
  +---+---+---+---+---+---+---+---+
7 | p | p | p | p | p | p | p | p |
  +---+---+---+---+---+---+---+---+
6 |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+
5 |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+
4 |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+
3 |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+
2 | P | P | P | P | P | P | P | P |
  +---+---+---+---+---+---+---+---+
1 | R | N | B | Q | K | B | N | R |
  +---+---+---+---+---+---+---+---+
    a   b   c   d   e   f   g   h
```

Requirements:

- White pieces are uppercase;
- Black pieces are lowercase;
- knights are `N`/`n`;
- Human vs Engine orientation follows the human color;
- Self-play defaults to White at bottom;
- rendering must not depend on color support;
- the board output must be deterministic and testable as pure text.

### 8.4 Human move input

The console accepts bare UCI coordinate moves when a human move is legal:

```text
move> e2e4
move> g1f3
move> e7e8q
```

It may also accept an explicit `move e2e4` form for consistency with the command grammar.

Move handling must use `chess-core::UciMove` and current legal moves, not a console-local chess parser.

A malformed or illegal move:

- prints a clear error;
- does not change the position;
- does not append move history;
- does not schedule an engine search;
- does not clear a prior valid result incorrectly.

### 8.5 Engine thinking output

When the engine searches, print useful progress without flooding the console.

Representative output:

```text
Engine thinking at depth 5...
info depth 1 score +0.18 nodes 24 nps 12000 time 2ms pv e7e5
info depth 2 score +0.10 nodes 310 nps 103333 time 3ms pv e7e5 g1f3
info depth 5 score +0.22 nodes 82419 nps 265867 time 310ms pv e7e5 g1f3 b8c6
Engine plays: e7e5
```

Progress may be one line per completed search iteration or otherwise rate-limited using existing observer information. Do not invent zero values for unavailable metrics. Missing values should appear as `-` or be omitted consistently.

Mate scores must use the same semantic formatting as the TUI/shared helper.

The final move line must only be printed after the exact completed move has passed shared generation and legality checks and has actually been applied.

### 8.6 Game status

After each move, print the resulting turn/status information, including:

- side to move;
- check indication;
- terminal outcome;
- available draw claims where represented by the existing core/application behavior.

Terminal results stop future search scheduling.

## 9. Console command grammar

During a game, support at least:

```text
<uci>                 submit a human move when allowed
move <uci>            explicit move form
board                 print the current board
moves                 print numbered move history
status                print turn/check/result/status
engine                print last known engine metrics
help                   print context-sensitive commands
resign                 request human resignation
save <path>            save the current game explicitly
new                    start a new game using current configuration
menu                   abandon current game and return to startup menu
quit                   exit the console application
```

Self-play additionally supports:

```text
pause                  stop automatic scheduling safely
resume                 resume automatic scheduling
step                    while paused, search/apply exactly one ply
```

The parser should be deterministic, case-insensitive for command words, and whitespace-tolerant. UCI square/move syntax remains governed by the core notation parser.

Unknown commands are errors, not ignored no-ops.

Commands that are invalid in the current mode must explain why. For example, `resign` in self-play should report that resignation is a Human vs Engine action rather than silently doing nothing.

## 10. Confirmation behavior

Destructive/abandoning commands must not be accidental.

At minimum:

- `resign` while a human game is active requires confirmation;
- `new` while a game is active requires confirmation;
- `menu` while a game is active requires confirmation;
- `quit` while a game is active requires confirmation;
- overwriting an existing save file requires confirmation.

Representative prompt:

```text
Abandon the current game and quit? [y/N]:
```

Only an explicit affirmative response confirms. Empty input or unrecognized input should default to no or reprompt; it must not silently choose the destructive path.

If an active engine search is associated with the game, cancellation/join happens only after the destructive action has been confirmed.

## 11. Search and console event-loop behavior

### 11.1 The console must remain able to observe search progress

The main application boundary must be able to process both console input and `EngineEvent` values without mutating game state from multiple threads.

The authoritative `GameController` remains owned by one application thread. Background search code sends typed events; it never directly mutates the controller.

### 11.2 Input architecture must be explicit and testable

A line-oriented console is simpler than a TUI, but self-play pause/quit commands and clean cancellation mean the implementation must deliberately decide how input and search events are multiplexed.

Acceptable designs include an interruptible/nonblocking input abstraction or a small input event worker feeding a channel, provided ownership and shutdown are explicit.

Requirements:

- no background input worker may own or mutate `GameController`;
- input events must be typed before reaching the controller/command dispatcher;
- a blocked input reader must not be disguised as a cleanly joined thread if it cannot actually be joined;
- if a process-lifetime input reader is used, that lifecycle decision must be explicit in code/docs/tests and must own no resources requiring cleanup beyond stdin access;
- engine search workers must still be cancelled/joined deterministically;
- no detached engine worker is acceptable;
- no raw-terminal mode should be introduced unless it is actually necessary and has scoped restoration equivalent to the TUI's correctness posture;
- any new dependency used for console input must support the repository MSRV and be justified by the required lifecycle behavior.

Before implementation commits to an input approach, add a focused test or prototype proving that self-play can receive a pause/quit command without corrupting or racing game state.

### 11.3 Search scheduling boundary

`GameController` may create a pending search request, but the console runtime owns the actual `SearchWorker` instance and event receiver, analogous to the TUI runtime boundary.

There must be at most one console-owned active search for the current game session.

A stale completion after restart/menu/quit is ignored by generation/request identity and must not mutate the new/current game.

## 12. Human vs Engine workflow

### 12.1 Human as White

1. Create a fresh `Game` with the selected configuration.
2. Print board and status.
3. Prompt for a move/command.
4. Apply a valid human move transactionally.
5. Print the updated board/status.
6. If terminal, stop.
7. Otherwise start the engine search.
8. Print progress as available.
9. Apply the exact current search result through the shared controller.
10. Print `Engine plays: <uci>` and the updated board/status.
11. Return to the human prompt.

### 12.2 Human as Black

1. Create a fresh game.
2. Print board/status.
3. Schedule the White engine search immediately.
4. Apply and print the exact engine move.
5. Prompt the human as Black.

The console must never prompt a human move while the human side is not to move.

## 13. Self-play workflow

Self-play uses the same shared state machine as the TUI.

On start:

- auto-play is enabled;
- White search is scheduled;
- exact White result is applied;
- Black search follows automatically;
- play continues until terminal or paused.

Commands:

- `pause`: request that automatic play stop safely; cancellation semantics should remain aligned with the shared controller/TUI behavior;
- `resume`: continue from the authoritative current game;
- `step`: while paused, schedule exactly one ply and remain paused afterward;
- `board`, `moves`, `status`, `engine`, `save`, `menu`, `quit`, and `help` remain available where meaningful.

Game-over stops all automatic scheduling.

No self-play console mode writes tuning/evaluation candidate files or mutates engine weights.

## 14. Save behavior

Saving is explicit only.

Example:

```text
chess> save games/2026-08-09.txt
Saved to games/2026-08-09.txt
```

Requirements:

- no auto-save;
- no implicit default directory discovery;
- save path comes from the user command/prompt;
- existing destination requires confirmation;
- serialization is deterministic;
- ordered UCI moves come from authoritative game history;
- mode/configuration and result/reason are included;
- filesystem errors are printed visibly;
- success is printed only after the atomic write has completed;
- failed writes do not mark the game saved;
- same-directory temporary write + atomic rename behavior is reused where possible;
- no format is called PGN unless actual PGN support is added separately.

## 15. EOF, errors, and process-exit behavior

### 15.1 End of stdin

EOF is not an ignorable empty command.

If stdin closes:

- print a concise reason where output is still possible;
- request cancellation of an active search;
- join the engine worker;
- exit deterministically.

Because confirmation is impossible after stdin has closed, EOF is treated as an explicit inability to continue interaction rather than waiting forever for confirmation.

### 15.2 Search failure

On a shared search `Failed` event:

- clear thinking/active-search state through the shared controller;
- keep the last valid game position unchanged;
- print the failure prominently;
- do not schedule a replacement move automatically;
- allow the user to inspect status and choose an explicit next action where safe.

### 15.3 Worker failure

Thread panic, channel closure, invalid search limits, TT construction failure, or another worker error is not a chess result and not a legal move source.

The console must surface the failure and move to a stable non-thinking state or controlled shutdown.

### 15.4 User input errors

Malformed menu selections, invalid depths, unknown commands, malformed moves, illegal moves, invalid save paths, and declined confirmations are user-correctable and should not crash the process.

Do not use `unwrap()`/`expect()` on user input, filesystem operations, channel receives, or engine results unless a local invariant is genuinely proven and documented.

## 16. Tests

### 16.1 `chess-app` extraction tests

Shared tests must cover at least:

- default/valid config depth behavior;
- Human/White waits for input;
- Human/Black schedules White engine search;
- Self-play schedules White search;
- new game changes generation;
- legal human move applies transactionally;
- malformed/illegal human move preserves state;
- promotion identity is preserved;
- current exact engine completion applies once;
- stale completion does not mutate state;
- engine-returned illegal move is rejected visibly;
- cancellation clears thinking state safely;
- search failure clears thinking state visibly;
- resignation winner is correct;
- terminal game schedules no new search;
- pause/resume/step semantics;
- exact fallback rejection;
- worker cancellation emits no playable completion;
- search worker joins cleanly;
- shared board/history/outcome/metric formatting;
- atomic save primitive success/failure behavior.

### 16.2 TUI regression tests

After extraction, retain and run:

- current TUI unit tests;
- current TUI hardening tests;
- current TUI integration tests;
- current real PTY acceptance suite;
- terminal restoration tests;
- save success/failure tests;
- resize tests;
- quit-while-searching cancellation tests.

The extraction is incomplete if tests merely moved to `chess-app` while the TUI wiring is no longer exercised.

### 16.3 Console parser/unit tests

Cover:

- startup/menu selections;
- empty-default selections;
- invalid depth and range handling;
- bare UCI vs `move <uci>` parsing;
- command case/whitespace normalization;
- unknown command error;
- mode-invalid command error;
- confirmation yes/no handling;
- explicit save path parsing;
- EOF event handling;
- deterministic board/history/status output.

### 16.4 Console integration tests

Prefer a testable input/output abstraction for most coverage, plus at least one real-process smoke path.

Exercise:

- Human White: start, `e2e4`, receive exact legal engine reply, return to human turn;
- Human Black: engine makes the first legal move, then human prompt is enabled;
- illegal move does not change board/history;
- `board`, `moves`, `status`, and `engine` produce meaningful output;
- resignation confirmation produces the opponent winner;
- save success writes expected bytes;
- save failure is visible;
- existing-file overwrite requires confirmation;
- self-play pause prevents automatic next-ply scheduling;
- self-play step applies exactly one ply and remains paused;
- resume restarts automatic scheduling;
- quit/menu/new while searching cannot apply a stale move afterward;
- EOF while searching cancels/joins cleanly;
- a search failure never produces a random/first-legal fallback move.

### 16.5 Workspace regression gates

Existing core/search/UCI/FFI/JNI/tooling correctness gates remain independent and green.

No console test is allowed to replace perft, differential, robustness, ABI/JNI, performance, or strength validation.

## 17. Developer workflow

Add supported developer commands to `scripts/dev.sh`, following the repository rule that `scripts/dev.sh` is the supported local entry point.

At minimum:

```bash
bash scripts/dev.sh console
```

should run the new console application.

If focused test helpers are useful, add explicit discoverable commands such as:

```bash
bash scripts/dev.sh console-test
```

only if they provide value beyond the normal `fast` workflow.

Direct Cargo commands may be documented for understanding, but repository development/validation instructions should use `scripts/dev.sh`.

The new crates participate in:

- formatting;
- workspace check;
- strict Clippy;
- workspace tests;
- locked dependency resolution;
- MSRV validation where applicable;
- artifact/strength audits where existing workflow requires them.

## 18. Documentation updates required when implementation lands

Update at least:

- root `Cargo.toml` workspace members;
- `docs/RUST_WORKSPACE_ARCHITECTURE.md`;
- `docs/RUST_DEVELOPER_WORKFLOWS.md`;
- `README.md` workspace/application overview;
- `README.md` common launch commands;
- `CLAUDE.md`/`AGENTS.md` command or architecture lists if they would otherwise become stale;
- the companion `docs/RUST_CONSOLE_TODO.md` with exact evidence.

Document clearly that:

- `chess-uci` is machine-facing;
- `chess-tui` is full-screen terminal UI;
- `chess-console` is human-facing scrolling console UI;
- both interactive frontends share `chess-app`;
- Python is reference-only and is not a runtime dependency.

## 19. Forbidden implementation shortcuts and silent failures

The implementation is explicitly rejected if it introduces any of the following without a separately reviewed specification change:

- random legal move fallback after engine failure;
- first legal move fallback after engine failure;
- playing a search emergency/fallback result when no exact completed iteration exists;
- silent depth reduction;
- silent retry with different search policy;
- Python engine fallback;
- UCI subprocess fallback;
- implicit opening-book discovery;
- implicit save-path discovery;
- swallowing a worker panic/channel error;
- leaving `thinking=true` after a failed worker;
- applying stale search completion to a restarted/new game;
- detached engine search workers;
- silent command ignores;
- destructive commands that default to yes;
- save success reported before the final write/rename succeeds;
- weakening existing TUI tests merely to make the shared-layer extraction pass;
- changing evaluation/search behavior as incidental frontend cleanup.

## 20. Acceptance criteria

The milestone is complete only when all of the following are true on the exact intended final source SHA:

1. `chess-app` and `chess-console` are workspace members and build on the supported toolchain/MSRV policy.
2. `chess-app` owns the shared interactive game/search lifecycle rather than duplicating it in TUI and console.
3. `chess-tui` uses the shared layer and retains its existing automated/PTY behavior.
4. `bash scripts/dev.sh console` launches a usable human-facing scrolling console application.
5. Human White can play a legal game flow against the authoritative engine.
6. Human Black receives an engine first move and can then play normally.
7. Human move legality and terminal outcomes come from `chess-core`.
8. Engine moves come only from exact accepted search completion and are revalidated against the current game.
9. Search progress/failure/cancellation is visible and typed.
10. Self-play supports automatic play, pause, resume, and exactly-one-ply step.
11. Board, moves, status, engine, help, resignation, save, new/menu, and quit commands work with explicit errors/confirmations.
12. Save writes are deterministic, explicit, atomic where supported by the existing implementation, and fail visibly.
13. EOF and supported shutdown paths cancel/join active engine search cleanly.
14. No random/first-legal/Python/UCI-subprocess/silent-depth fallback exists.
15. Existing UCI behavior and tests remain green.
16. Existing core/search correctness and robustness gates remain green.
17. No engine strength/evaluation/tuning activation change is bundled into this frontend milestone.
18. Permanent CI is green on the exact final SHA and the TODO records the run/job/evidence identifiers required by repository policy.

## 21. Implementation sequencing rule

Implementation should proceed in this order:

1. establish baseline evidence;
2. create `chess-app`;
3. extract worker/controller/text/save primitives with behavior-preserving tests;
4. refactor `chess-tui` to consume the shared layer;
5. prove TUI regression gates, including PTY acceptance;
6. create `chess-console`;
7. implement console workflows and tests;
8. update docs/developer commands;
9. run final exact-SHA validation and permanent CI;
10. close the TODO only from recorded evidence.

Do not develop an independent console controller first and promise to deduplicate it later. The shared boundary is part of this milestone's correctness design.