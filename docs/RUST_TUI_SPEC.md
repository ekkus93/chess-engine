# Rust Chess TUI Specification

Status: proposed implementation specification

## 1. Purpose

Add a native Rust terminal user interface for playing with and exercising the authoritative Rust chess engine.

The new application is `crates/chess-tui`. It is a human-facing frontend, not a new chess implementation. The historical Python Textual application in `chess_game/tui.py` and `chess_game/tui_game.py` is the behavioral and UX reference. The Rust workspace on `master` remains authoritative for chess rules, position state, search, evaluation, repetition, and engine policy.

The primary goals are:

- let a human play against the Rust engine entirely in a terminal;
- support engine-vs-engine self-play for interactive observation;
- expose useful search information while the engine thinks;
- provide a convenient manual integration harness for `chess-core` and `chess-search`;
- preserve the useful interaction model of the Python TUI without retaining Python as a runtime dependency;
- avoid duplicating chess rules, search, evaluation, or UCI protocol logic in the UI.

## 2. Non-goals

This milestone does not:

- change search strength, evaluation weights, search policy, opening-book policy, or promotion state;
- revive the retired Python engine as production code;
- invoke Python from Rust;
- implement a network chess client or server;
- provide a graphical desktop UI;
- make the TUI a stable library/API boundary;
- silently fall back to another engine if the Rust engine fails;
- introduce online learning or automatic weight mutation. The Python TUI's historical self-play learning behavior is deliberately not carried forward.

## 3. Architectural decision

### 3.1 Do not spawn the UCI executable

Although the user-facing requirement is a TUI using the Rust UCI-era engine, `chess-tui` must not normally launch `chess-uci` as a subprocess and parse its stdout.

Both applications live in the same Rust workspace. A subprocess would add process lifecycle, pipe buffering, protocol parsing, cancellation, and failure-recovery complexity without adding useful isolation.

The intended dependency direction is:

```text
                       +-----------------------+
                       | chess-uci             |
                       | stdin/stdout adapter  |
                       +-----------+-----------+
                                   |
                                   v
+-----------+      +---------------------------+      +--------------+
| chess-tui | ---> | shared engine/search APIs | ---> | chess-search |
| Ratatui   |      | + chess-core Game state  |      +------+-------+
+-----------+      +---------------------------+             |
                                                               v
                                                        +------------+
                                                        | chess-core |
                                                        +------------+
```

`chess-uci` remains the external UCI process adapter. `chess-tui` is another presentation adapter over the same authoritative Rust engine components.

If implementation reveals UCI-owned worker/session functionality that is genuinely presentation-neutral, extract the smallest reusable abstraction rather than copying it. Do not make `chess-core` depend on UCI or UI code, and do not make `chess-search` depend on UCI, TUI, filesystem, JNI, or FFI code.

### 3.2 Crate dependencies

`chess-tui` should depend directly on:

- `chess-core` for `Game`, positions, legal move validation, UCI move representation, side to move, terminal state, and repetition/history semantics;
- `chess-search` for iterative deepening, limits, cancellation, search progress, score, PV, and transposition support;
- `chess-book` only if opening-book use is explicitly enabled through the same explicit policy used by the Rust engine;
- `ratatui` for terminal widgets/layout;
- `crossterm` for terminal input/backend handling.

A small shared adapter module/crate may be introduced only when it removes real duplication between `chess-uci` and `chess-tui`. Do not create an abstraction merely to satisfy the diagram above.

## 4. Historical Python behavior to preserve

The Python Textual TUI currently provides a useful reference for:

- a main menu;
- Human vs Engine and Self-play modes;
- White/Black selection for the human;
- configurable engine depth;
- separate White/Black depth in self-play;
- terminal board rendering with coordinates and distinct White/Black pieces;
- move history;
- explicit thinking state;
- check/game-over status;
- human move entry using coordinate/UCI-style notation such as `e2e4`;
- promotion suffixes such as `e7e8q`;
- resignation with confirmation;
- self-play pause/resume and single-step;
- post-game save and return-to-menu actions.

The Rust version should preserve these capabilities where they remain appropriate, but it need not reproduce Textual widget structure, CSS, colors, exact strings, or historical implementation quirks.

## 5. User workflows

### 5.1 Startup/main menu

Running the TUI opens a main menu rather than immediately starting a search.

The menu supports:

1. Human vs Engine
2. Self-play

For Human vs Engine, configure:

- human color: White or Black;
- engine search depth for the initial milestone.

For Self-play, configure:

- White search depth;
- Black search depth.

Defaults should be conservative and responsive. The historical default depth of 3 is acceptable initially.

### 5.2 Human vs Engine

The application creates a fresh authoritative `Game` in the starting position.

If the human is White, input is enabled immediately. If the human is Black, the engine begins the first search.

Human moves are entered as UCI coordinate moves:

```text
e2e4
g1f3
e7e8q
```

The UI parses through the Rust core's move representation and validates against the current authoritative game state. Illegal or malformed moves are rejected visibly and do not mutate state.

After a valid human move:

1. apply the move transactionally;
2. update history/display;
3. detect terminal state;
4. if the game continues, start the engine search asynchronously;
5. keep the UI event loop responsive;
6. apply the engine's returned legal move only if it belongs to the still-current game/search generation.

### 5.3 Self-play

Both sides use the Rust engine.

Self-play begins automatically and supports:

- Pause: stop automatic scheduling after the current search has safely stopped or completed;
- Resume: continue automatic play;
- Step: when paused, search and apply exactly one engine move;
- return to menu after game completion.

Pausing must not corrupt engine state. If the search layer supports cancellation, pause/exit should request cancellation and wait for clean ownership transfer rather than abandoning mutable state.

### 5.4 Game over

Recognize terminal outcomes using Rust-core authoritative state, including at least:

- checkmate;
- stalemate;
- draw conditions represented by the core, including repetition and move-count rules where implemented;
- insufficient-material draw where represented by the core;
- human resignation.

The TUI displays the result prominently and stops scheduling searches.

Post-game actions:

- save game;
- return to main menu;
- quit.

## 6. Screen layout

The exact responsive layout may evolve, but the default wide-terminal game screen should resemble:

```text
+---------------------------------------------------------------+
| Chess Engine                         Human vs Engine / Depth 3 |
+--------------------------------------+------------------------+
|                                      | Moves                  |
|      a   b   c   d   e   f   g   h   |  1. e2e4   e7e5       |
|    +---+---+---+---+---+---+---+---+ |  2. g1f3   ...        |
|  8 | r | n | b | q | k | b | n | r | |                        |
|    +---+---+---+---+---+---+---+---+ | Engine                 |
|  7 | p | p | p | p | p | p | p | p | | depth  5              |
|    +---+---+---+---+---+---+---+---+ | score  +0.24           |
|  ...                                 | nodes  128,430         |
|    +---+---+---+---+---+---+---+---+ | nps    410k            |
|  1 | R | N | B | Q | K | B | N | R | | time   313 ms         |
|    +---+---+---+---+---+---+---+---+ | pv e7e5 g1f3 ...       |
|      a   b   c   d   e   f   g   h   |                        |
+--------------------------------------+------------------------+
| Your turn (White)                                             |
| Move: e2e4_                                                   |
+---------------------------------------------------------------+
| Enter move | r resign | n new game | m menu | q quit          |
+---------------------------------------------------------------+
```

For narrower terminals, panels may stack vertically. The app must not panic on resize or on terminals smaller than the preferred dimensions. A clear minimum-size message is acceptable when useful rendering is impossible.

## 7. Board rendering

Initial implementation may use ASCII/Unicode text rather than graphical chess glyphs.

Requirements:

- files `a` through `h` and ranks `1` through `8` are visible;
- White and Black are visually distinguishable without relying solely on color;
- White uses uppercase piece letters and Black lowercase, matching the historical TUI;
- knight is `N`/`n`;
- board orientation follows the human side in Human vs Engine mode: White at bottom for a White human, Black at bottom for a Black human;
- self-play defaults to White at bottom;
- terminal color is enhancement only; monochrome terminals remain usable;
- last move and/or selected input squares may be highlighted when straightforward, but this is not required for first acceptance.

## 8. Input and key bindings

Minimum game bindings:

- typed UCI move + Enter: submit human move;
- `r`: request resignation when not editing move text;
- `n`: new game, with confirmation if a game is active;
- `m` or Esc: return to menu, with confirmation if abandoning an active game;
- `q`: quit, with confirmation if abandoning an active game;
- self-play: Space toggles pause/resume;
- self-play while paused: `s` or an explicit Step control advances one ply.

The implementation must make text-entry focus unambiguous so that shortcut keys do not accidentally fire while a move is being typed.

## 9. Engine search integration

### 9.1 Asynchronous search

Search must never execute on the terminal event/render thread.

Use an owned worker thread or equivalent bounded Rust concurrency mechanism. There must be at most one active search per game session unless the search implementation itself explicitly owns parallelism.

Each search request includes an immutable/safely-owned snapshot of the required game/search state and a monotonically increasing generation/request identifier.

A completion event must be ignored if its generation no longer matches the active game. This prevents stale results from a cancelled search, old game, or menu transition from being applied.

### 9.2 Search limits

The first milestone exposes fixed depth because it maps cleanly to the Python reference. Internally, use the existing `SearchLimits` infrastructure rather than inventing TUI-only stopping logic.

A later extension may expose:

- move time;
- node limit;
- clock controls;
- hash size;
- check-extension option;
- explicit opening-book selection.

Those are not required for initial acceptance.

### 9.3 Progress reporting

When the existing search observer/progress APIs make the information available, display:

- current/completed depth;
- evaluation score, including mate score formatting;
- nodes;
- nodes per second;
- elapsed search time;
- principal variation;
- hash fullness if readily available.

Progress is informational. Missing optional progress fields must display as unavailable rather than fabricated defaults.

### 9.4 Search failures

Search errors must be visible. Never silently:

- substitute a random legal move;
- substitute the first legal move;
- reduce depth and retry without telling the user;
- restart with different search policy;
- switch to the historical Python engine;
- swallow a worker panic/error and leave the UI appearing to think forever.

On search failure, stop the thinking state, preserve the last valid game state, display the error, and allow the user to return to the menu or retry explicitly where safe.

## 10. Opening book

The Rust engine's explicit opening-book policy remains authoritative.

The TUI must not perform implicit filesystem discovery. If no explicit book is configured, play without a book. If book support is included in the first implementation, it must use an explicit path/configuration and expose failure rather than silently switching data sources.

Randomized opening-book behavior from the historical Python TUI is not a requirement.

## 11. Game state and move history

`chess-core::Game` is the authoritative game/session state. Do not maintain a second rules model in the TUI.

The UI may maintain presentation-only history derived from successfully applied moves. Prefer storing structured `UciMove` values and formatting them for display rather than treating strings as authoritative state.

Repetition and terminal detection must use core-owned history semantics rather than a TUI-local repetition algorithm.

## 12. Save format

Initial save support should be deliberately simple and deterministic.

A saved text game contains:

- date/time where appropriate;
- mode;
- human color or self-play configuration;
- configured search limits;
- ordered UCI move list;
- final result/reason.

Do not call the format PGN unless valid PGN is actually implemented. A later milestone may add SAN/PGN export using a tested Rust implementation.

Saving must report filesystem errors to the user. A failed write must never change the UI to `Saved`.

## 13. Terminal lifecycle and cleanup

The application must restore the terminal on all normal error paths.

Requirements:

- raw mode/alternate-screen setup and teardown are scoped safely;
- quitting during a search requests cancellation where supported;
- worker ownership is resolved before process exit where practical;
- panic hooks or RAII guards restore terminal state;
- no background worker is allowed to continue mutating shared application state after a game is destroyed.

## 14. Error handling policy

The TUI follows the repository's correctness-first, fail-closed posture.

User-correctable input errors are displayed in the UI. Internal invariant failures and engine/search failures are not reclassified as legal game outcomes.

No `unwrap()`/`expect()` is acceptable on user input, terminal size/events, filesystem writes, or engine responses unless an invariant is locally proven and documented. Workspace Clippy/warnings policy remains in force.

## 15. Tests

### 15.1 Unit tests

Cover at least:

- board orientation and rendering;
- move-history formatting;
- UCI move input parsing/validation integration;
- promotion input;
- menu/config state transitions;
- game-over state transitions;
- self-play pause/resume/step state machine;
- stale search-generation rejection;
- search-error transition;
- save serialization independent of filesystem I/O.

### 15.2 Integration tests

Headless tests should exercise the application/session controller without requiring a real terminal where possible:

- human White: `e2e4`, engine response, correct side to move;
- human Black: engine searches first;
- illegal move leaves `Game` unchanged;
- engine completion from an obsolete game generation is ignored;
- self-play step applies exactly one ply;
- game-over prevents another search from being scheduled;
- resignation produces the correct winner;
- save failure remains visible and is not reported as success.

### 15.3 Engine parity/invariants

The TUI must not require new chess-rule golden data. Existing core/search tests remain authoritative. TUI integration tests should assert that moves accepted/applied by the UI are the same moves accepted/applied through the public Rust core APIs.

## 16. Developer workflow

Add a supported developer entry point, preferably:

```bash
bash scripts/dev.sh tui
```

and direct Cargo execution:

```bash
cargo run -p chess-tui
```

The crate participates in normal workspace formatting, `cargo check`, strict Clippy, tests, and rustdoc/build gates.

## 17. Documentation

Update the README workspace list and common commands when implementation lands. Document:

- how to launch the TUI;
- controls;
- supported modes;
- search settings;
- save behavior;
- relationship between `chess-tui`, `chess-uci`, `chess-search`, and `chess-core`.

## 18. Acceptance criteria

The milestone is complete when all of the following are true:

1. `crates/chess-tui` is a Rust workspace member and builds on the repository's supported Rust toolchain.
2. `cargo run -p chess-tui` opens a usable terminal menu.
3. A human can play a complete legal game as White or Black against the authoritative Rust engine.
4. Human move validation and terminal outcomes come from Rust core state, not duplicated UI rules.
5. Engine search runs off the UI thread and the interface remains responsive.
6. Search progress is displayed where provided by existing search APIs.
7. Self-play supports automatic play, pause/resume, and one-ply step.
8. Resignation and game-over states stop future search scheduling.
9. Stale/cancelled search results cannot mutate a new or abandoned game.
10. Engine/search/save errors are visible and no silent fallback move is used.
11. The terminal is restored after normal quit and handled error paths.
12. Game saving accurately reports success/failure.
13. No Python process or Python engine module is required at runtime.
14. No search/evaluation/tuning/promotion behavior is changed by this milestone.
15. Workspace format, check, strict Clippy, tests, and relevant CI gates pass on the exact implementation SHA.

## 19. Future extensions

Explicitly deferred possibilities include:

- SAN and real PGN import/export;
- clocks and configurable time controls;
- analysis-only mode for arbitrary FEN positions;
- interactive legal-move highlighting/cursor movement;
- engine option editor;
- explicit opening-book picker;
- load/resume saved games;
- copy FEN/PV to clipboard;
- multiple PV display;
- richer Unicode board themes.

These should be added only after the basic TUI is stable and tested.