# Rust Chess Android UI/UX Redesign Specification

**Status:** proposed implementation specification

**Companion task plan:** `docs/RUST_ANDROID_UI_UX_REDESIGN_TODO_2026-08-10.md`

**Planning baseline `master`:** `e351ff81fc4dbbd36a99afc142eb1d8dfb237ef9`

**Current Android app:** `android-harness/android-app`

## 1. Purpose

Redesign the existing playable Rust Chess Android application from a functional engineering-oriented UI into a polished, modern, professional chess application while preserving the existing Rust-authoritative game architecture and behavior.

The redesign is deliberately a presentation and UX milestone. It must improve visual quality, information hierarchy, spatial stability, accessibility, and portrait-phone usability without creating a second chess implementation in Kotlin or weakening any existing search, opening-book, lifecycle, or failure semantics.

The most important UX correction is structural: the current game screen is one vertically scrollable page containing the status card, chessboard, game actions, engine diagnostics, and move history. During normal play the user should not need to scroll the entire page to reach controls or information. The redesigned primary screens must fit completely within the portrait viewport. Where data itself is naturally unbounded, such as move history, only the bounded data region may scroll.

This specification uses the actual current Compose implementation and emulator-rendered screens as its baseline. It is not based on aspirational or invented UI.

## 2. Existing-state evidence

### 2.1 Current implementation

At the planning baseline:

- `MainActivity.kt` renders a single `Scaffold` and switches between `SetupScreen` and `GameScreen`.
- `SetupScreen` is a vertically scrollable `Column` with the title, developer-oriented explanatory copy, side-selection chips, engine-depth slider, helper text, and Start button.
- `GameScreen` is a vertically scrollable `Column` containing, in order:
  1. `GameStatusCard`;
  2. `ChessBoard`;
  3. `GameActions`;
  4. `EngineCard`;
  5. `MoveHistoryCard`.
- `ChessBoard` uses Unicode chess glyphs, stock Compose text rendering, and fixed light/dark square colors.
- Move history displays raw UCI coordinate notation.
- The application uses `Theme.Material.Light.NoActionBar` and the default Compose `MaterialTheme` rather than a product-specific design system.
- `AndroidManifest.xml` does not currently lock `MainActivity` to portrait orientation.

Relevant current files include:

```text
android-harness/android-app/src/main/AndroidManifest.xml
android-harness/android-app/src/main/kotlin/com/ekkus93/chessapp/MainActivity.kt
android-harness/android-app/src/main/kotlin/com/ekkus93/chessapp/ChessViewModel.kt
android-harness/android-app/src/main/kotlin/com/ekkus93/chessapp/BoardModel.kt
android-harness/android-app/src/main/res/values/styles.xml
android-harness/android-app/src/androidTest/kotlin/com/ekkus93/chessapp/ChessAppInstrumentedTest.kt
```

### 2.2 Current rendered-screen evidence

The current application was built and rendered on an Android API-35 Pixel 2 emulator. A temporary read-only capture workflow drove the real application and captured the actual setup/game/dialog states.

Final successful capture evidence:

- workflow run: `31363272814`;
- capture SHA: `93d4f08768285003e9fabe842584331fb8ace526`;
- artifact: `9053263983`;
- artifact name: `android-current-ui-gallery-93d4f08768285003e9fabe842584331fb8ace526`.

The capture-only workflow and script were removed afterward. The application source at clean baseline `e351ff81fc4dbbd36a99afc142eb1d8dfb237ef9` is functionally the same application captured by that evidence.

The gallery established the actual before-state:

- setup page with stock Material light presentation;
- White-oriented game page;
- Black-oriented game page;
- lower scrolled region containing engine metrics and move history;
- New Game confirmation dialog;
- Restart confirmation dialog;
- Resign confirmation dialog.

These screenshots are the authoritative visual baseline for this redesign. Do not substitute generated mockups for current-state evidence during implementation review.

## 3. Goals

The redesign must accomplish all of the following:

1. Make the Android application look intentional, polished, contemporary, and production-quality rather than like a development harness.
2. Keep the application portrait-only and design/test only the portrait experience for this milestone.
3. Eliminate whole-page scrolling from the Setup and Game primary screens.
4. Keep all normal game controls and primary information regions fully inside the visible portrait viewport.
5. Make the chessboard the dominant visual element while dynamically shrinking it when necessary to preserve the fixed surrounding UI.
6. Keep the chessboard spatially stable during normal state changes such as human move, engine thinking, engine reply, and status updates.
7. Introduce a cohesive dark product palette, typography hierarchy, spacing system, surface hierarchy, and component treatment.
8. Replace the current stacked Engine and Moves sections with a bounded tabbed information region.
9. Make move history internally scrollable while keeping the entire Moves panel itself visible.
10. Present move history in user-facing Standard Algebraic Notation (SAN) while preserving UCI as the authoritative internal move identity where appropriate.
11. Present engine information as a compact chess-analysis panel rather than a raw diagnostic dump.
12. Keep New Game, Restart, and Resign available without page scrolling.
13. Preserve board orientation from the human player's perspective.
14. Improve visibility of the most recent move and legal move interaction without changing chess legality semantics.
15. Preserve the existing one-second Android post-human-move reveal delay for the engine reply.
16. Preserve the shared Rust opening-book path and all current fail-closed search behavior.
17. Preserve visible native/application errors and retryable lifecycle semantics.
18. Keep accessibility semantics first-class and improve them where the redesign introduces custom components.
19. Add automated layout regression coverage so the app cannot silently drift back to clipped/off-screen primary controls.
20. Preserve API-35 runtime instrumentation and debug-APK publication.

## 4. Non-goals

This milestone does **not**:

- change engine evaluation, search strength, tuning, transposition policy, or opening-book repertoire;
- change the shared TUI or console UX;
- add multiplayer, online play, accounts, cloud sync, leaderboards, puzzles, analysis databases, or engine downloads;
- add saved-game browsing unless separately authorized;
- add Settings, History, About, or other navigation pages merely to make the app look more complete;
- add landscape layouts;
- add tablet-specific two-pane layouts;
- duplicate move legality, check/mate detection, SAN legality/disambiguation, or engine scheduling in Kotlin;
- hide search or JNI failures behind fallback moves or fake UI state;
- silently lower engine depth because a device is slow;
- replace UCI as the internal move identity solely for UI purposes;
- make a broad Android/Gradle/Kotlin toolchain migration unless required by a narrowly justified UI dependency;
- claim release-store readiness, signing, or Play Store publication as part of this visual redesign.

## 5. Product UX invariants

These are acceptance requirements, not visual suggestions.

### 5.1 Portrait-only contract

`MainActivity` must be explicitly portrait-only, expected initially through:

```xml
android:screenOrientation="portrait"
```

or an equivalently explicit and testable platform contract.

The UI should not maintain a parallel landscape composition. Rotation must not move the app into an unsupported landscape layout.

### 5.2 No primary-screen page scrolling

The root Setup screen must not be vertically scrollable.

The root Game screen must not be vertically scrollable.

Scrolling is allowed only inside a bounded region whose container is fully visible, principally the Moves list. A long principal variation may use bounded text wrapping or a deliberately bounded inner region, but it must not make the whole game page scroll.

### 5.3 Minimum supported portrait layout target

The redesign must fit within a **minimum usable portrait content viewport of 360 × 640 dp**, excluding Android system-bar insets handled by Compose/platform layout.

This is a layout acceptance target, not an instruction to hard-code one device size.

At or above that target:

- status/header region is fully visible;
- the complete chessboard is fully visible;
- the complete tab row is fully visible;
- the complete active tab container is fully visible;
- all primary game action controls are fully visible;
- no element requires page scrolling;
- no primary button is partially clipped;
- no text needed to understand current game state is rendered underneath another element.

When space is constrained, shrink the chessboard before clipping fixed UI.

### 5.4 Spatial stability

During a game, the chessboard's screen position and size must not jump because:

- `thinking` changes;
- status text changes;
- engine metrics arrive;
- an engine move is revealed;
- move history grows;
- the selected tab's content changes within its allocated bounds.

Small animations inside fixed bounds are permitted, but layout reflow that moves the board significantly is not.

### 5.5 No deceptive fallback UI

The UI must never display a fabricated/default move, score, status, or engine result when the Rust/JNI layer reports failure or absence.

Missing metrics remain absent or explicitly unavailable.

Search failure remains visible.

A failed native close/restart transition must not visually pretend that the old game was successfully abandoned if ownership remains unresolved.

## 6. Navigation and information architecture

The application remains intentionally simple.

Primary navigation model:

```text
Setup / New Game
       |
       v
     Game
      |
      +-- Moves tab
      |
      +-- Engine tab
```

Modal states:

```text
New Game confirmation
Restart confirmation
Resign confirmation
Promotion choice
Chess engine error
```

There is no drawer, bottom-navigation bar, hamburger menu, Settings page, About page, History page, or Engine page in this milestone.

Moves and Engine are tabs within the fixed Game screen, not separate navigation destinations.

## 7. Visual design system

### 7.1 Design direction

Use a restrained, modern dark chess-tool aesthetic. The board is the visual focal point. Application chrome should recede rather than compete with the board.

Avoid:

- neon gaming aesthetics;
- gradients used merely as decoration;
- faux wood textures;
- oversized shadows;
- casino-style gold;
- excessive rounded cards around every element;
- raw default Material components with no product styling;
- decorative elements that reduce usable board size.

### 7.2 Color palette

Use these design tokens as the initial target palette:

| Token | Hex | Purpose |
|---|---:|---|
| `AppBackground` | `#0B1220` | primary window/background |
| `Surface` | `#121B2B` | cards, tab body, compact panels |
| `SurfaceElevated` | `#18243A` | dialogs, selected/elevated areas |
| `SurfaceMuted` | `#0F172A` | subdued strips / inactive areas |
| `Border` | `#2A3A52` | dividers, outlines |
| `Primary` | `#2DD4BF` | principal accent / selected state |
| `PrimaryStrong` | `#5EEAD4` | high-emphasis accent |
| `OnBackground` | `#F8FAFC` | primary text |
| `OnSurfaceMuted` | `#94A3B8` | secondary text |
| `Success` | `#34D399` | success/positive state |
| `Warning` | `#FBBF24` | warning state |
| `Danger` | `#F87171` | resign/error destructive emphasis |
| `BoardLight` | `#E7D7C4` | light chess square |
| `BoardDark` | `#806A58` | dark chess square |
| `BoardLastMove` | `#D7B85A` | subtle last-move indication/overlay basis |
| `BoardLegalTarget` | `#2DD4BF` | legal-target marker basis |
| `BoardSelection` | `#5EEAD4` | selected-square outline/overlay basis |

Exact alpha values for overlays may be tuned during implementation, but semantic token ownership must remain clear.

Do not scatter literal colors throughout composables. Centralize them in a product theme/design-token layer.

### 7.3 Theme policy

For this milestone, ship one intentional dark product theme.

Do not automatically switch to a stock light theme merely because the system is in light mode. A separate polished light theme can be a future milestone if desired.

System bars should be coordinated with the product background and use readable icon appearance.

### 7.4 Typography

Use a small, deliberate hierarchy rather than large stock Material headings.

Recommended roles:

- product/setup title: approximately 28–32sp, semibold/bold;
- screen/status primary: 18–20sp, semibold;
- section/tab title: 14–16sp, medium/semibold;
- body/control text: 14–16sp;
- secondary metadata: 12–13sp;
- board coordinates: 9–10sp;
- move list: 13–14sp, tabular/monospace only if it improves alignment without hurting readability.

Use system fonts unless a bundled font has a clear product justification. Do not add a network font dependency.

### 7.5 Shape and surface treatment

Prefer subtle 8–12dp corner radii for bounded panels/dialogs and compact 6–8dp radii for controls.

Use borders and surface contrast more than heavy drop shadows.

Avoid nesting multiple cards with large padding where one structured panel suffices.

### 7.6 Iconography

Use coherent vector icons for simple actions where icons save space or improve recognition.

Examples:

- New Game: add/new-board icon plus label;
- Restart: restart/refresh icon plus label;
- Resign: flag icon plus label.

Do not make critical actions icon-only unless the icon has an accessible label and is unambiguous.

Prefer packaged vector drawables/Material icons over Unicode pseudo-icons for application chrome.

## 8. Setup screen specification

### 8.1 Setup information hierarchy

The Setup screen must be a fixed, non-scrolling portrait composition.

Representative structure:

```text
+--------------------------------+
|                                |
|            [mark]              |
|          Rust Chess            |
|   Play against the Rust engine |
|                                |
|  PLAY AS                       |
|  +-----------+ +-----------+   |
|  |   White   | |   Black   |   |
|  +-----------+ +-----------+   |
|                                |
|  ENGINE STRENGTH               |
|  Depth 3             Balanced  |
|  --------o------------------   |
|  1                         12   |
|                                |
|  +--------------------------+  |
|  |        Start Game        |  |
|  +--------------------------+  |
|                                |
+--------------------------------+
```

The mark/logo may initially use a simple bundled chess motif if no final product icon exists, but it must not require image generation to implement.

### 8.2 Player-facing copy

Remove the current developer/architecture paragraph:

> Play against the native Rust engine. Game rules, move validation, and engine turns are controlled by the shared Rust application layer.

That information belongs in developer documentation, not the player setup flow.

Recommended subtitle:

> Play against the Rust chess engine

Keep copy short enough that it does not create compact-height layout problems.

### 8.3 Side selection

Replace the small stock filter-chip appearance with a deliberate two-option segmented control or equally compact selection surface.

Requirements:

- White and Black options are equally sized;
- selected state has clear accent/background contrast;
- selection remains accessible by semantics;
- selection is disabled visibly while game creation is busy;
- no hidden third state.

### 8.4 Engine depth/strength

Depth 1–12 remains the authoritative control for this milestone.

The UI may give the numeric depth a player-friendly descriptor such as:

- 1–2: Easy;
- 3–4: Balanced;
- 5–7: Strong;
- 8–10: Very Strong;
- 11–12: Maximum;

If descriptors are used, they are presentation labels only. They must not silently remap, clamp, or modify the selected depth.

The selected numeric depth must remain visible so engine enthusiasts can see the real setting.

The slider should look intentional and should not expose the current awkward stock tick rendering as the dominant visual feature.

### 8.5 Start action

Use one high-emphasis full-width Start Game button.

When creation is busy:

- keep the button footprint stable;
- disable duplicate activation;
- show bounded progress without moving surrounding controls;
- surface game-creation failure visibly.

## 9. Game screen specification

### 9.1 Fixed portrait composition

The Game screen must not use a root `verticalScroll`.

Representative structure:

```text
+--------------------------------+
| Your move       White · D3     |  compact status/header
| Engine played ...Nf6           |
+--------------------------------+
|                                |
|                                |
|          CHESS BOARD           |
|                                |
|                                |
+--------------------------------+
|      Moves      |    Engine    |  tab selector
+--------------------------------+
|                                |
| fixed tab-content viewport     |
| (only internal list may scroll)|
|                                |
+--------------------------------+
| New Game | Restart | Resign    |  fixed actions
+--------------------------------+
```

The exact implementation may use `BoxWithConstraints`, measured layout, `ConstraintLayout`, or carefully weighted Compose rows/columns, but it must satisfy the viewport invariants rather than relying on one reference device.

### 9.2 Vertical allocation strategy

Fixed/chrome regions should have bounded heights. The board consumes the largest remaining square that preserves all other regions.

Conceptually:

```text
availableContentHeight
  - statusRegion
  - tabSelector
  - tabContentMinimum
  - gameActions
  - verticalSpacing
  = maximumBoardHeight

boardSize = min(availableWidth, maximumBoardHeight)
```

Do not simply use `fillMaxWidth().aspectRatio(1f)` and allow the rest of the content to fall below the screen.

On taller phones, grow the board until width becomes the limit. On compact-height phones, shrink the board.

### 9.3 Status/header region

Replace the large current `GameStatusCard` with a compact fixed-height status region.

It should communicate:

- primary state: `Your move`, `Engine thinking…`, terminal outcome, or equivalent;
- human color;
- configured engine depth;
- short last-action/status text when useful, e.g. `Engine played ...Nf6`.

During thinking, a small spinner/progress treatment may appear inside the fixed region. Do not add/remove enough content to change region height.

Long error text does not belong here; errors remain explicit dialogs or another deliberately bounded visible error surface.

### 9.4 One-second engine reveal behavior

Preserve the existing Android UX rule:

- after a human move is committed, show the human move immediately;
- delay the first Android engine-result poll/reveal by approximately one second;
- allow the Rust engine to compute concurrently during that interval;
- then reveal the accepted engine result;
- subsequent poll cadence may remain fast.

The redesign should make this easier to perceive by combining board last-move highlighting with concise status text.

Do not move the one-second delay into `chess-search` or shared `chess-app`; it remains Android presentation timing.

## 10. Chessboard presentation

### 10.1 Board remains Rust-driven

The board continues to parse authoritative Rust-provided FEN for presentation.

Legal target eligibility continues to come from Rust-provided legal UCI moves.

Kotlin must not introduce a second move generator or chess-rule engine.

### 10.2 Piece artwork

Replace the current Unicode text glyph presentation with a coherent bundled vector chess-piece set if it can be done without licensing ambiguity.

Requirements:

- all 12 piece/color assets come from one consistent set;
- assets are bundled with the application and available offline;
- license/provenance is documented if third-party artwork is used;
- pieces remain readable on both board square colors;
- do not use emoji rendering, whose appearance varies by device/font.

If a suitable licensed piece set is not immediately available, create simple first-party vector assets or retain the current glyphs temporarily behind an explicit TODO rather than quietly downloading arbitrary images at runtime.

### 10.3 Coordinates

Keep rank/file coordinates, but make them subtle and legible.

Orientation rules remain:

- Human White: `a1` bottom-left;
- Human Black: `h8` bottom-left from the user's view, with file/rank labels matching the rotated board.

### 10.4 Selection and legal targets

Do not recolor an entire destination square so strongly that the board becomes visually noisy.

Preferred interaction treatment:

- selected square: accent outline and/or restrained overlay;
- empty legal destination: centered dot;
- occupied legal capture target: ring/outline treatment around the square/piece;
- disabled board while engine owns the turn.

Accessibility semantics must continue to expose square, piece, selected state, and legal-target state.

### 10.5 Last-move highlight

Add a subtle last-move indication for the source and destination squares.

This is a presentation feature and may be derived from the latest authoritative UCI move string without reimplementing chess legality.

Requirements:

- both source and destination are visible;
- highlight is lower priority than active selection/legal-target affordances;
- it works after both human and engine moves;
- it works in both board orientations;
- it remains visible long enough to help the user identify the engine's reply;
- it does not change authoritative game state.

## 11. Moves tab

### 11.1 Bounded container

The Moves tab body is fully visible within the Game screen.

Only the move-list contents scroll vertically when history exceeds the allocated body height.

The tab selector and action controls never scroll away with move history.

### 11.2 SAN presentation requirement

Display player-facing move history in Standard Algebraic Notation, for example:

```text
1. e4       c5
2. Nf3      Nc6
3. Bb5      a6
```

Do not implement SAN legality/disambiguation independently in Kotlin.

Preferred ownership:

1. add/use a Rust notation formatter that can derive SAN from authoritative game history; then
2. expose SAN history through the high-level `ChessGameSnapshot` protocol, alongside or derived from existing UCI history.

UCI history may remain present for internal/testing/debugging compatibility.

SAN generation must correctly cover at least:

- pawn moves;
- piece moves;
- captures;
- disambiguation;
- checks;
- checkmates;
- castling;
- promotions;
- en passant notation behavior expected by SAN.

If the existing Rust core has no SAN helper, implement and test it in an appropriate Rust layer rather than in Compose.

### 11.3 Move list behavior

Use numbered rows with White and Black columns.

Recommended behavior:

- newest move is visually identifiable but not distracting;
- when the user is already at the bottom, a new move auto-scrolls to remain visible;
- if the user manually scrolls up to inspect history, a new move must not aggressively yank the list back to the bottom;
- returning to the Moves tab preserves a sensible current scroll position during the same game;
- New Game/Restart resets the history and scroll state appropriately.

## 12. Engine tab

The Engine tab is for useful chess-engine information, not a raw profiler dump.

Recommended compact fields:

```text
Depth     8
Score     +0.34
Nodes     184,221
NPS       612k
Time      301 ms

PV
Nf3 Nc6 Bb5 a6
```

Requirements:

- display only metrics actually present in the authoritative snapshot;
- keep field positions stable as values update;
- format large node/NPS counts readably without falsifying values;
- score formatting must preserve mate vs centipawn semantics already exposed by Rust;
- PV may wrap inside its bounded area;
- no whole-page scrolling;
- `Hash` is secondary/advanced information and need not occupy prime space.

A compact `Details` row/section may expose hash fullness if desired, but it must remain within the fixed panel and must not create page scrolling.

Opening-book moves may legitimately have limited/no normal search metrics. Present that as an explicit absence such as `Book move` or `No search required` only if the Rust/application snapshot can authoritatively identify a book hit. Do not guess from timing or node count.

## 13. Game action region

`New Game`, `Restart`, and `Resign` must remain fully visible at all times during normal game play.

Use one compact fixed-height action row.

Requirements:

- New Game: normal primary/secondary action;
- Restart: normal secondary action;
- Resign: destructive styling using `Danger` without making the entire screen feel alarming;
- buttons include text labels;
- actions are disabled appropriately while an incompatible operation is busy;
- disabled states remain visually distinguishable;
- button footprints do not change when enabled/disabled.

Do not hide essential game actions in an overflow menu solely to make the layout fit unless later user review explicitly prefers that design.

## 14. Dialogs and modal flows

Restyle all existing dialogs into the same product theme while preserving semantics.

### 14.1 New Game

Keep the existing confirmation meaning:

- title: `Start a new game?`;
- explain that the current game will close and setup choices can change;
- Cancel and New Game actions;
- destructive emphasis is not necessary.

### 14.2 Restart

Keep the existing confirmation meaning:

- title: `Restart this game?`;
- explain current position/history will be discarded;
- Cancel and Restart actions.

### 14.3 Resign

Keep resignation deliberately destructive:

- title: `Resign this game?`;
- explain that resignation immediately ends the game;
- Cancel and Resign actions;
- Resign uses `Danger` emphasis.

### 14.4 Promotion

Promotion remains a modal choice.

Use a compact layout with Queen, Rook, Bishop, Knight choices and clear piece labels/icons.

The move passed back to the view model remains one of the authoritative legal promotion UCI moves supplied by Rust.

### 14.5 Engine/application error

Keep errors fail-visible.

The error dialog must:

- identify that a chess-engine/application error occurred;
- show the real message in a readable bounded area;
- provide an explicit dismissal action where safe;
- not automatically retry search;
- not choose a fallback move;
- not silently reset the game.

## 15. Rust/Kotlin architecture boundary

The redesign must preserve the existing architecture:

```text
Jetpack Compose UI / ChessViewModel
              |
         Kotlin ChessGame
              |
   NativeChessAppBindings (JNI)
              |
          chess-jni
              |
          chess-app
         /         \
   chess-core    chess-search
```

Kotlin remains responsible for:

- presentation state;
- selected square UI state;
- tab selection;
- list scroll state;
- visual formatting that does not require chess rules;
- Android presentation timing such as the one-second engine reveal delay;
- lifecycle orchestration through the existing high-level API.

Rust remains responsible for:

- authoritative game state;
- legal moves;
- applying moves;
- game outcome;
- search scheduling/result acceptance;
- opening-book move selection;
- stale result rejection;
- engine metrics;
- SAN generation/disambiguation if SAN is added.

The UI redesign must not route Android through the UCI console process or historical Python code.

## 16. Opening-book and search behavior preservation

The redesign must preserve the current shared interactive search path where TUI, console, and Android use the shared `chess-app` worker's opening-book-first behavior.

Android-specific presentation changes must not:

- bypass the book;
- introduce a separate Android book;
- choose a UI-side book move;
- treat a book failure as permission to silently search;
- change deterministic book selection;
- alter TUI/console opening-book behavior.

Existing exact Android regression expectations such as the starting White move `e2e4` and Black reply `c7c5` after human `e2e4` must remain green unless the shared opening-book policy is separately changed in another reviewed milestone.

## 17. Failure and lifecycle policy

The UI redesign inherits the existing fail-closed policy.

The following remain prohibited:

- random legal-move fallback;
- first-legal-move fallback;
- silent retry;
- silent depth reduction;
- UCI subprocess fallback;
- Python fallback;
- fake/default snapshot after JNI failure;
- clearing a native owner after destroy failure and pretending cleanup succeeded;
- swallowing reachable-owner close/restart errors;
- stale coroutine state overwriting a newer game generation.

The PhantomReference reaper remains only the documented last-resort cleanup path for an unreachable owner.

## 18. Accessibility requirements

The redesigned app must remain operable and understandable with Android accessibility services.

Requirements include:

- minimum practical touch targets approximately 48dp for primary interactive controls;
- meaningful content descriptions for icon-bearing controls;
- board-square semantics continue to state coordinate and piece;
- selected/legal-target semantics remain available;
- side selection exposes selected state;
- tabs expose selected state and labels;
- destructive action semantics remain clear;
- color is not the only indication of selection, legal target, thinking state, or error;
- text contrast is validated against the actual product palette;
- large system font settings are evaluated at least for common scaling without silently clipping critical controls.

If extreme font scaling cannot fit every secondary metric at the minimum viewport, preserve game controls and core state first and handle secondary analysis information within its bounded tab region rather than making the whole screen scroll.

## 19. Test strategy

### 19.1 Existing tests that must remain green

Preserve current permanent coverage for:

- launcher Activity start;
- high-level `ChessGame` Human White flow;
- shared opening-book reply `e2e4 c7c5`;
- Human Black initial book move `e2e4`;
- one-second post-human-move reveal behavior;
- Rust/JNI lifecycle and contract tests;
- Android lint and JVM tests;
- API-35 instrumentation.

### 19.2 New layout/UI instrumentation coverage

Add Compose UI/instrumentation support if necessary to assert real rendered bounds and semantics.

At minimum add tests proving:

1. Setup root is not a page-scrolling container.
2. Setup title, side selector, depth control, and Start Game are fully inside the portrait content viewport.
3. Game root is not a page-scrolling container.
4. Status, complete board, tab selector, complete active tab body, and complete action row are simultaneously inside the viewport.
5. Moves list itself can scroll when populated while the surrounding Game screen does not move.
6. Switching Moves/Engine tabs does not move/resize the board.
7. Thinking/idle/status changes do not move/resize the board beyond an explicitly tiny tolerance.
8. Human White board orientation is correct.
9. Human Black board orientation is correct.
10. Last-move highlight identifies authoritative source/destination squares.
11. Legal-target selection remains functional.
12. Promotion dialog remains functional.
13. New Game, Restart, and Resign confirmations remain reachable without page scrolling.
14. Resign remains disabled after terminal game state where applicable.
15. Portrait orientation is enforced.

### 19.3 Compact viewport acceptance

Add a deterministic test strategy for the **360 × 640 dp minimum usable content target**.

Acceptable approaches include:

- Compose test-host constraints;
- emulator/device display override in a dedicated UI test;
- a pure measured-layout test around an extracted deterministic layout calculator plus at least one real device assertion.

Do not merely inspect one Pixel 2 screenshot and declare compact-layout coverage complete.

### 19.4 SAN tests

If SAN formatting is newly added in Rust, include focused Rust tests for:

- simple pawn move;
- simple piece move;
- capture;
- ambiguous same-piece move requiring file/rank disambiguation;
- check;
- checkmate;
- kingside castling;
- queenside castling;
- promotion;
- promotion with check/mate where applicable;
- en passant capture representation;
- sequential history formatting from the authoritative game.

Also add Android snapshot/parser tests for the extended protocol if SAN history becomes a new field.

### 19.5 Visual evidence

At final implementation SHA, capture actual emulator screenshots for at least:

- Setup screen;
- Human White game screen;
- Human Black game screen;
- Moves tab with enough moves to demonstrate internal scrolling;
- Engine tab with populated metrics;
- thinking state;
- New Game dialog;
- Restart dialog;
- Resign dialog;
- promotion dialog if a deterministic fixture can reach it;
- error dialog using a controlled test-only failure surface if feasible without adding production fallback behavior.

Screenshots are evidence, not a substitute for assertions.

## 20. Developer workflow and CI

Continue to use the repository-supported entry point:

```bash
bash scripts/dev.sh android
```

Permanent `.github/workflows/android.yml` must continue to validate the application.

If new Compose UI testing dependencies/tasks are required, integrate them into the permanent Android workflow rather than relying on a temporary workflow for final acceptance.

Temporary screenshot/evidence workflows, if used during development, must:

- use `contents: read` only;
- never modify source;
- be removed before final closure unless deliberately promoted as a permanent read-only visual-regression job.

Do not introduce source-modifying CI workflows.

## 21. Documentation updates expected at implementation closure

Update at least:

- `docs/RUST_ANDROID_APP.md`;
- `README.md` if its Android description/screenshots are affected;
- `docs/RUST_DEVELOPER_WORKFLOWS.md` if UI-test commands are added;
- `AGENTS.md` / `CLAUDE.md` only if repository-operating rules genuinely change.

Document:

- portrait-only product policy;
- design-system ownership;
- no-primary-page-scroll invariant;
- Moves/Engine tab model;
- SAN display ownership;
- screenshot/evidence commands if made permanent.

## 22. Acceptance criteria

This redesign is complete only when all of the following are true:

1. The Android app uses the specified cohesive product theme rather than stock Material light defaults.
2. `MainActivity` is explicitly portrait-only.
3. Setup fits within the supported portrait viewport without root scrolling.
4. Game fits within the supported portrait viewport without root scrolling.
5. Status, complete board, tabs, complete tab panel, and all three game actions are simultaneously visible at the minimum layout target.
6. The board dynamically shrinks on compact-height portrait devices rather than pushing controls off-screen.
7. The board does not visibly jump during human/engine turn state transitions.
8. Moves and Engine share one bounded tab region.
9. Only the move-history contents scroll; its panel remains completely visible.
10. Move history is displayed in correct SAN sourced from Rust-authoritative notation logic.
11. Internal UCI move identity and legal-move handling remain intact.
12. The Engine tab presents useful metrics compactly without fabricating unavailable data.
13. Game controls remain permanently accessible without scrolling.
14. Board pieces and interaction affordances look coherent and professional.
15. Last engine/human move is easy to identify visually.
16. One-second Android engine-reveal behavior remains covered and green.
17. Opening-book regression behavior remains covered and green.
18. Human White and Human Black orientation remain correct.
19. Confirmation, promotion, and error dialogs use the same product design language and preserve semantics.
20. Accessibility semantics remain correct for board, tabs, selectors, dialogs, and actions.
21. No silent fallback/retry/fake-state behavior is introduced.
22. Existing Rust/JNI lifecycle behavior remains intact.
23. `bash scripts/dev.sh android` passes on the final source SHA.
24. Permanent Android CI passes on the exact final source SHA.
25. Final actual-emulator screenshots demonstrate the implemented UI and are reviewed against this specification.
26. The implementation TODO contains exact final source SHA, CI run/job IDs, and evidence/artifact IDs before closure.

## 23. Design review principle

When implementation tradeoffs arise, optimize in this order:

1. chess/game correctness and fail-closed behavior;
2. all critical controls/state visible in the portrait viewport;
3. spatial stability during play;
4. accessibility and legibility;
5. board size;
6. visual polish;
7. secondary diagnostic density.

Do not sacrifice correctness or hide controls merely to preserve a larger board. Do not sacrifice the board unnecessarily to display low-value diagnostics. The intended product is a chess app first and an engine telemetry viewer second.
