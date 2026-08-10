# Rust Android UI/UX Redesign Closure Evidence — 2026-08-10

**Program:** portrait Android UI/UX redesign  
**Planning baseline:** `e351ff81fc4dbbd36a99afc142eb1d8dfb237ef9`  
**Specification commit:** `fe9de5b581e8e4a12f1b94186f72d3a3f1fc93ab`  
**Implementation-start SHA:** `d98c241837a6bd99a77fb9990ac8efc8c82852fc`  
**Final product/evidence source SHA:** `a93c282699f380d604b214e0950372fd88e33585`  
**Branch:** `master`

## Disposition

The automated Android UI/UX redesign program is complete on the product/evidence source SHA above. The application is a portrait-only, fixed-viewport dark Compose UI over the existing Rust-authoritative game/session architecture. The redesign did not add a Kotlin chess engine, UI-side opening-book policy, alternate move source, or search retry path.

A physical-phone subjective UX pass was not performed from this execution environment because no representative Android device was attached. That manual check remains a follow-up and is not represented as automated evidence or silently treated as passed.

## Shipped product behavior

The redesigned Android application provides:

- dark first-party product theme and dark launch/system-bar treatment;
- portrait-only launcher policy;
- fixed game viewport with no primary/root page scrolling;
- one square board that remains spatially stable across idle, thinking, engine reply, tab changes, and status changes;
- first-party vector chess piece artwork drawn by Compose rather than text glyphs or third-party piece images;
- White/Black orientation, coordinates, selected-square outline, legal-target dot/ring, and last-move highlighting;
- compact stable turn/status region;
- presentation-only `Moves` / `Engine` tab state with selected-state semantics and non-color checkmark cues;
- Rust-generated SAN as player-facing move history while UCI remains authoritative for move identity/control/highlighting;
- internally scrollable move history with deterministic follow-bottom / preserve-manual-history behavior;
- bounded engine metrics for depth, score, nodes, NPS, elapsed time, PV, and available secondary data without fabricated values;
- fixed New Game / Restart / Resign action row;
- themed confirmation, promotion, and error dialogs;
- explicit retryable native-cleanup state if startup snapshot acquisition and cleanup both fail;
- the existing approximately one-second human-move visibility interval before the first engine-result poll/reveal.

## Architecture and ownership evidence

### Rust owns chess behavior

`chess-core` owns rules and SAN formatting. The redesign added SAN formatting there rather than replaying or approximating chess rules in Kotlin. SAN coverage includes quiet moves, captures, disambiguation, castling, promotion, check/checkmate, en passant, sequential history, and non-mutation of the authoritative game position.

`chess-app` remains the shared interactive application/session layer. `SearchWorker` remains opening-book-first and exact-result-only for gameplay. Book/search/channel failures remain typed failures; they do not fall through to a random, first-legal, lower-depth, or alternate move source.

### JNI snapshot contract

The high-level Android snapshot protocol was versioned to carry SAN history in addition to the existing authoritative UCI history. UCI remains available for exact move identity, legal-move projection, board interaction, and last-move highlighting. Rust encoder, Kotlin parser, and host-JVM contract coverage were updated together.

### Kotlin remains presentation/controller glue

Compose parses FEN for drawing and projects selectable sources/targets from the Rust-provided legal-move list. Kotlin does not implement move generation, legality, SAN disambiguation, opening-book selection, or engine-turn scheduling. JNI calls remain off the Android main thread.

### Lifecycle fail-closed hardening

Explicit `ChessGame.close()` remains authoritative. Native destroy keeps the opaque handle registered until cleanup succeeds, and Kotlin keeps its handle until native destruction succeeds. During the redesign audit an additional startup edge was fixed: if initial snapshot acquisition fails and the immediate explicit close also fails, the ViewModel now retains the reachable native owner, sets `cleanupRequired`, disables new game configuration, surfaces both failures, and exposes an explicit `Retry cleanup` action. No silent cleanup retry is performed.

The PhantomReference reaper remains only a last-resort leak backstop after an owner is already unreachable; it is not a gameplay or reachable-owner failure fallback.

## Automated UI/runtime coverage

Permanent API-35 instrumentation covers, among other contracts:

- 360 × 640 dp Setup containment and no root scroll;
- 360 × 640 dp Game containment, square board, and no root scroll;
- stable board/action geometry across idle, thinking, engine reply, and tab changes;
- enlarged text (`fontScale = 1.3`) containment;
- White and Black selection semantics;
- exact depth bounds 1 and 12 plus strict presentation descriptors;
- selected tab and selected board-square semantics;
- explicit cleanup-required retry UI;
- long-history internal scrolling;
- follow-bottom behavior when already at the bottom;
- preservation of a manually selected historical scroll position;
- Rust SAN rows and move numbering;
- exact promotion ordering and exact authoritative UCI promotion values;
- launcher startup;
- real board-tap Human White play;
- immediate human-move visibility and the one-second reveal delay;
- exact built-in opening-book reply `e2e4 c7c5` for Human White coverage;
- exact built-in first move `e2e4` for Human Black coverage;
- New Game, Restart, Resign, Promotion, and Error modal rendering/evidence.

## Permanent Android CI evidence

**Workflow:** `Android JNI`  
**Run:** `31383610431`  
**Run URL:** `https://github.com/ekkus93/chess-engine/actions/runs/31383610431`  
**Source SHA:** `a93c282699f380d604b214e0950372fd88e33585`  
**Overall:** success

Jobs:

- `Android API 35 JNI and app smoke` — job `93439083192` — success;
- `Host JVM JNI contract` — job `93439083194` — success;
- `Android/Kotlin lint and unit tests` — job `93439083164` — success.

The emulator job passed dual-ABI JNI staging/symbol checks, app/test-APK compilation, the historical JNI lifecycle/performance suite, all playable-app instrumentation, and all evidence/APK artifact publication steps.

## Final actual-emulator visual evidence

**Visual artifact:** `rust-chess-android-ui-evidence-a93c282699f380d604b214e0950372fd88e33585`  
**Artifact ID:** `9060954512`  
**Artifact digest:** `sha256:eede39982290206a150f0848b323f587f65776b196be4bad8ee14eba2768d575`

The artifact contains exactly 13 real API-35 device-framebuffer PNGs plus a relative-path `SHA256SUMS.txt`. The extracted manifest was verified with `sha256sum -c SHA256SUMS.txt`; all entries passed and no expected state image had a duplicate digest.

Screenshot hashes:

```text
ea067b3364f0c26fcf62f465ea566fd9c29f4062d8bace0d14d40483490034f5  black-game.png
131529ae3fe1df1356475d86630b59da2e39a683329d86908ef8a0f072df5851  engine-metrics.png
fd1e1e9b135acf665d32bc7e0b053fc6ab48b50110f147c569b0379c24e64b70  error-dialog.png
2db83b5bd7081c1bd7141c25d0119f4119773bdd47a0fe59d522de19796b0692  moves-multiple.png
c7cbb233ee14f4a74c3dead041b9820b4b52f05b0b60bc94cac0f4e1a90a9d2c  moves-scrolled.png
54f839e51f14d2af69a9edadbd831dd734234dc9520d133c245493388fc2d617  new-game-dialog.png
c8446961d3fb9e4033a8a1b01c7b502027ef907c4e26c327a0991c9aa5557ce5  promotion-dialog.png
feb1c15f5e15a37d4c7278971cb62c124c352bcd6716eb36db9818d976b1f907  resign-dialog.png
4992f2384f822a3e349016220a8e97e62ea07be687ecc382f8c27181afd7064d  restart-dialog.png
109e0e365d731a4077b17dbc957db39b3e5f3b222db50e4d1e5a63491e2c6501  setup.png
82d24a658a1bc80d5c324a84229aaf9e40f368ed910e9c2d8da7fe6cfb6a5f7c  white-engine-reply.png
f962f7bd1b65d67ba11539325ed4e5a5ec22a6bfd7ae3194f1b116965ad50223  white-idle.png
70d7c5a03012e522f7509bade1e16843cd543c6e63eb47f14a6bcb91e7934492  white-thinking.png
```

Manual pixel review confirmed:

- Setup is fully rendered in the dark product theme; it is not a launch spinner/blank frame.
- Human White idle shows the complete fixed shell.
- Human White thinking shows `e4` already applied while the status reads `Engine thinking…`.
- Engine reply shows `e4 c5`, returns to `Your move`, and highlights the exact latest move.
- Human Black shows the board reversed for Black after the shared Rust engine's `e2e4` opening move.
- `moves-multiple.png` and `moves-scrolled.png` visibly show different history ranges, demonstrating evidence of internal history navigation while board/actions remain fixed.
- Engine metrics remain inside the bounded tab body.
- New Game, Restart, and Resign dialogs are readable, themed, and keep explicit Cancel actions; Resign has destructive emphasis.
- Promotion offers Queen/Rook/Bishop/Knight clearly.
- Error text remains visible in the themed error dialog and does not claim retry/fallback success.
- No primary control is clipped or pushed off-screen in the reviewed captures.

### Baseline comparison

Before-state artifact `9053263983` (capture SHA `93d4f08768285003e9fabe842584331fb8ace526`) showed the prior light/default presentation. Engine and Moves content were stacked below the board and required a separate `game-white-lower.png` capture to view lower controls/content.

The final evidence shows the root-scroll problem visibly eliminated: compact status, board, tabs, bounded tab body, and New Game/Restart/Resign are simultaneously present in one portrait viewport. The board remains visually dominant and the dark product palette is consistent across primary screens and dialogs.

## APK evidence

**Artifact:** `rust-chess-android-debug-a93c282699f380d604b214e0950372fd88e33585`  
**Artifact ID:** `9060955018`  
**Artifact digest:** `sha256:fc1f3094d0d14a87385ab02cf555c41d7caa1c2d07fa48adbfa5be90c830dfd9`

## Performance evidence

**Artifact:** `task24-android-performance-a93c282699f380d604b214e0950372fd88e33585`  
**Artifact ID:** `9060954166`  
**Artifact digest:** `sha256:072e95ec4270b1892ace88306ffcfa99beaee6554b957761dd7a43929868624e`

Performance remains an independent gate/evidence stream and is not used to hide correctness failures.

## General Rust CI

Because the redesign added Rust SAN/snapshot work, the complete permanent repository CI also ran on the exact product/evidence source SHA.

**Workflow:** `CI`  
**Run:** `31383610397`  
**Run URL:** `https://github.com/ekkus93/chess-engine/actions/runs/31383610397`  
**Source SHA:** `a93c282699f380d604b214e0950372fd88e33585`  
**Overall:** success

Jobs:

- `Rust workspace quality` — job `93439080444` — success;
- `Linux ARM64 workspace build` — job `93439080479` — success.

The x86 workspace job passed repository authority audits, committed-lockfile/workspace metadata checks, rustfmt, workspace check, strict Clippy, complete workspace tests, console PTY acceptance, authoritative release perft, rustdoc, debug/release workspace builds, UCI smoke, and the pinned differential corpus/seeded-playout oracle. The ARM64 job passed workspace metadata, debug/release builds, and test compilation.

## Anti-fallback declaration

Source review and permanent tests confirm the redesign introduced none of the following:

- random legal-move fallback;
- first-legal-move fallback;
- silent search retry;
- silent depth reduction;
- UI-side opening-book choice;
- UI-side chess legality implementation;
- UI-side SAN rule/disambiguation implementation;
- Python gameplay fallback;
- UCI subprocess gameplay fallback;
- silent reachable-owner cleanup abandonment.

## Manual-only / not represented as passed

- A representative physical-phone UX pass was not performed in this execution environment.
- The literal local commands `bash scripts/dev.sh android` and `bash scripts/dev.sh fast` were not run from this connector-only execution environment; their covered correctness/build/test responsibilities were exercised by permanent GitHub Actions on the exact source SHA. The tracker must not claim those literal local invocations occurred.

These omissions do not weaken or rewrite automated evidence. They are recorded as manual/local execution follow-ups rather than silently inferred successes.
