# Rust Chess Android UI/UX Redesign Implementation TODO

**Companion specification:** `docs/RUST_ANDROID_UI_UX_REDESIGN_SPEC_2026-08-10.md`

**Status:** proposed / not started

**Planning baseline before these documents:** `e351ff81fc4dbbd36a99afc142eb1d8dfb237ef9`

**Specification commit:** `fe9de5b581e8e4a12f1b94186f72d3a3f1fc93ab`

## Ralph-loop operating rules

This checklist is intended to be implemented directly on `master` under the repository workflow.

- Work directly on `master`; do not create a branch or PR unless the user explicitly changes that instruction.
- Re-read `AGENTS.md` and `CLAUDE.md` before implementation.
- Use `bash scripts/dev.sh ...` as the supported developer/validation entry point.
- Keep the Rust workspace authoritative for chess rules, move legality, search, opening-book behavior, game outcomes, and SAN generation/disambiguation.
- Kotlin/Compose owns presentation and Android-specific UX state only.
- Do not change engine evaluation, tuning, strength, search policy, opening-book repertoire, or shared TUI/console behavior as part of this UI milestone.
- Do not mark a checkbox complete merely because code compiles.
- Add focused tests for every behavior moved or changed.
- Do not weaken/delete tests to obtain green validation.
- Do not add first-party lint suppression to bypass warnings.
- Do not add random/first-legal fallback moves, silent retry, silent depth reduction, fake/default snapshots, or alternate engine paths.
- Do not use a UCI subprocess or historical Python engine as an Android fallback.
- Do not clear native ownership after a failed explicit close and pretend cleanup succeeded.
- Preserve the existing one-second Android post-human-move engine reveal behavior.
- Preserve shared opening-book behavior and its current Android regression assertions.
- Keep portrait-only layout as a product requirement; do not add parallel landscape UI work.
- Root Setup and Game screens must not become page-scrollable.
- All critical layout assertions must be automated; screenshots alone are not acceptance evidence.
- Temporary CI/evidence workflows, if used, must be read-only (`contents: read`) and removed before final closure unless explicitly promoted as permanent.
- Never use a CI workflow that modifies source or commits generated changes back to the repository.
- Record exact source SHA, commands, CI run URL/ID, job ID, and relevant artifact/evidence identifiers for major gates.

## Phase 0 — Establish implementation baseline and current-state evidence

- [ ] Record exact starting `master` SHA when implementation begins.
- [ ] Confirm planning baseline `e351ff81fc4dbbd36a99afc142eb1d8dfb237ef9` and list any intervening product commits.
- [ ] Re-read:
  - [ ] `docs/RUST_ANDROID_UI_UX_REDESIGN_SPEC_2026-08-10.md`;
  - [ ] `docs/RUST_ANDROID_APP.md`;
  - [ ] `docs/RUST_WORKSPACE_ARCHITECTURE.md`;
  - [ ] `docs/RUST_DEVELOPER_WORKFLOWS.md`;
  - [ ] `AGENTS.md`;
  - [ ] `CLAUDE.md`.
- [ ] Inspect current:
  - [ ] `MainActivity.kt`;
  - [ ] `ChessViewModel.kt`;
  - [ ] `BoardModel.kt`;
  - [ ] `AndroidManifest.xml`;
  - [ ] `styles.xml`;
  - [ ] Android app Gradle dependencies;
  - [ ] `ChessAppInstrumentedTest.kt`.
- [ ] Record current theme parent and default Compose theme behavior.
- [ ] Confirm `SetupScreen` currently uses root `verticalScroll`.
- [ ] Confirm `GameScreen` currently uses root `verticalScroll`.
- [ ] Confirm current Game screen ordering: status -> board -> actions -> engine -> moves.
- [ ] Confirm current board uses Unicode chess glyphs.
- [ ] Confirm current move list displays raw UCI.
- [ ] Confirm `MainActivity` is not yet explicitly portrait-locked.
- [ ] Confirm current Human White opening-book assertion `e2e4 c7c5`.
- [ ] Confirm current Human Black opening-book assertion `e2e4`.
- [ ] Confirm current one-second post-human-move reveal regression test.

### Phase 0 before-state visual evidence

- [ ] Record final current-state gallery evidence:
  - [ ] run `31363272814`;
  - [ ] capture SHA `93d4f08768285003e9fabe842584331fb8ace526`;
  - [ ] artifact `9053263983`.
- [ ] Review the actual emulator captures for:
  - [ ] Setup screen;
  - [ ] White game screen;
  - [ ] Black game screen;
  - [ ] lower scrolled game content;
  - [ ] New Game dialog;
  - [ ] Restart dialog;
  - [ ] Resign dialog.
- [ ] Do not use generated/aspirational mockups as evidence of the current implementation.

### Phase 0 baseline validation

- [ ] Run `bash scripts/dev.sh android` on the exact implementation starting SHA.
- [ ] Record baseline result and any pre-existing failure before modifying source.
- [ ] Record current permanent Android CI status for the exact implementation starting SHA if available.
- [ ] Confirm repository working tree/source baseline is free of temporary UI capture workflows/scripts.

### Phase 0 acceptance

- [ ] Exact implementation starting SHA recorded.
- [ ] Baseline Android gate result recorded.
- [ ] Current UI architecture and failure/search boundaries documented in implementation notes.
- [ ] No engine/search/book change is included in the implementation plan.

## Phase 1 — Introduce the Android product design-token layer

Create a deliberate product theme instead of scattered literal colors and stock Material defaults.

### Phase 1.1 Color tokens

- [ ] Add centralized Android/Compose color tokens for:
  - [ ] `AppBackground = #0B1220`;
  - [ ] `Surface = #121B2B`;
  - [ ] `SurfaceElevated = #18243A`;
  - [ ] `SurfaceMuted = #0F172A`;
  - [ ] `Border = #2A3A52`;
  - [ ] `Primary = #2DD4BF`;
  - [ ] `PrimaryStrong = #5EEAD4`;
  - [ ] `OnBackground = #F8FAFC`;
  - [ ] `OnSurfaceMuted = #94A3B8`;
  - [ ] `Success = #34D399`;
  - [ ] `Warning = #FBBF24`;
  - [ ] `Danger = #F87171`;
  - [ ] `BoardLight = #E7D7C4`;
  - [ ] `BoardDark = #806A58`;
  - [ ] last-move/legal-target/selection semantic colors.
- [ ] Do not duplicate these literals throughout composables.
- [ ] Use semantic names rather than `Color1`, `Blue500`, or component-specific arbitrary names.

### Phase 1.2 Compose theme

- [ ] Add a dedicated `RustChessTheme` or equivalently explicit product theme.
- [ ] Define an intentional dark `ColorScheme` from the product tokens.
- [ ] Define typography roles appropriate for compact portrait layout.
- [ ] Define shape/radius conventions.
- [ ] Coordinate Android system-bar background/icon appearance with the product theme.
- [ ] Do not silently switch to stock Material light mode when the system is light.
- [ ] Keep this milestone to one polished product theme unless implementation reveals a mandatory platform issue.

### Phase 1.3 Legacy XML theme

- [ ] Update `styles.xml` only as needed to avoid startup flash/theme mismatch and preserve Compose ownership.
- [ ] Ensure launch window/background does not flash a bright stock light surface before Compose renders.
- [ ] Keep NoActionBar behavior unless an explicit Compose top bar replaces it.

### Phase 1.4 Typography/spacing

- [ ] Create reusable spacing constants/tokens where real reuse exists.
- [ ] Avoid oversized stock headline styles that waste board space.
- [ ] Use a compact, consistent typography hierarchy.
- [ ] Keep minimum practical touch targets around 48dp for primary controls.

### Phase 1 tests

- [ ] Add JVM/unit coverage for any pure design-token mapping logic if nontrivial.
- [ ] Add Compose semantics/screenshot evidence showing no stock light theme remains in normal screens/dialogs.
- [ ] Run Android lint after theme changes.

### Phase 1 acceptance

- [ ] Product palette is centralized.
- [ ] Application renders intentionally dark from startup through dialogs.
- [ ] No major composable owns duplicated hard-coded product colors.

## Phase 2 — Enforce portrait-only product behavior

### Phase 2.1 Manifest/platform contract

- [ ] Explicitly lock `MainActivity` to portrait orientation in `AndroidManifest.xml` or an equivalently explicit platform mechanism.
- [ ] Do not create a landscape resource/layout variant.
- [ ] Do not add orientation-specific state forks to `ChessViewModel`.

### Phase 2.2 Runtime behavior

- [ ] Confirm app remains portrait when device/emulator rotation is requested.
- [ ] Confirm game/session state is not reset merely because a rotation request is attempted.

### Phase 2 tests

- [ ] Add instrumentation assertion that Activity requested/supported orientation is portrait.
- [ ] Add emulator/device rotation test if practical in permanent CI.
- [ ] Confirm no landscape screenshot/layout is required by this milestone.

### Phase 2 acceptance

- [ ] Portrait-only behavior is explicit and tested.
- [ ] No parallel landscape layout maintenance burden is introduced.

## Phase 3 — Add measurable fixed-viewport layout infrastructure

The root Setup and Game screens must stop relying on page scrolling.

### Phase 3.1 Minimum viewport contract

- [ ] Treat `360 × 640 dp` usable portrait content as the minimum layout acceptance target.
- [ ] Account for system-bar/window insets rather than hard-coding raw physical pixels.
- [ ] Define which dimensions are fixed/bounded and which are flexible.
- [ ] Document the implemented board-size calculation.

### Phase 3.2 Game board sizing

- [ ] Replace unconditional width-driven board sizing with available-height-aware sizing.
- [ ] Compute board size as the largest square that still preserves:
  - [ ] status/header;
  - [ ] tab selector;
  - [ ] minimum tab-content body;
  - [ ] action row;
  - [ ] required spacing/insets.
- [ ] Cap board size by available width.
- [ ] Shrink board on compact-height phones before clipping controls.
- [ ] Do not use root page scrolling as the escape hatch.

### Phase 3.3 Spatial-stability hooks

- [ ] Add stable test tags/semantics to:
  - [ ] setup root;
  - [ ] game root;
  - [ ] status region;
  - [ ] board;
  - [ ] tab row;
  - [ ] tab body;
  - [ ] action row;
  - [ ] Moves list;
  - [ ] Engine panel.
- [ ] Make board bounds measurable in instrumentation/Compose UI tests.

### Phase 3.4 Root-scroll removal

- [ ] Remove `verticalScroll` from Setup root.
- [ ] Remove `verticalScroll` from Game root.
- [ ] Verify no parent container provides equivalent whole-page scrolling through another modifier/component.

### Phase 3 tests

- [ ] Add real layout-bound assertions for the default API-35 emulator.
- [ ] Add deterministic compact-layout coverage for 360 × 640 dp.
- [ ] Assert all fixed regions are fully contained within the root viewport.
- [ ] Assert board is square.
- [ ] Assert board does not overlap tabs/actions.
- [ ] Assert root Setup is not scrollable.
- [ ] Assert root Game is not scrollable.

### Phase 3 acceptance

- [ ] No primary-screen whole-page scrolling remains.
- [ ] All required regions can be simultaneously visible at compact target.
- [ ] Layout tests fail if a future change pushes actions/tab body off-screen.

## Phase 4 — Redesign the Setup screen

### Phase 4.1 Content cleanup

- [ ] Remove developer-facing architecture paragraph from player UI.
- [ ] Use concise player-facing copy, initially:
  - [ ] title `Rust Chess`;
  - [ ] subtitle `Play against the Rust chess engine` or equivalent concise copy.
- [ ] Do not mention JNI/shared-Rust-layer architecture in setup UI.

### Phase 4.2 Branding/mark

- [ ] Add a restrained chess/product mark if it improves hierarchy without consuming excessive height.
- [ ] Keep asset offline/bundled.
- [ ] Do not use generated decorative imagery as a dependency for implementation.
- [ ] Add content description only if the mark communicates information; decorative marks should not create screen-reader noise.

### Phase 4.3 Side selector

- [ ] Replace stock small filter chips with a deliberate equal-width White/Black segmented control or equivalent.
- [ ] Preserve `HumanSide.WHITE` / `HumanSide.BLACK` exact mapping.
- [ ] Preserve disabled behavior while setup is busy.
- [ ] Add selected-state semantics.

### Phase 4.4 Engine depth

- [ ] Keep authoritative depth range 1–12.
- [ ] Keep numeric depth visible.
- [ ] Restyle slider/control so it does not look like the current raw stock ticked Material slider.
- [ ] If strength descriptors are added, make them pure presentation labels and test exact depth mapping.
- [ ] Never silently clamp a valid selected depth to a different value when starting the game.
- [ ] Preserve existing validation in the high-level owner.

### Phase 4.5 Start Game

- [ ] Add one high-emphasis Start Game action.
- [ ] Keep footprint stable while busy.
- [ ] Prevent duplicate start activation.
- [ ] Keep creation failure visible.

### Phase 4 tests

- [ ] White selection maps to `HumanSide.WHITE`.
- [ ] Black selection maps to `HumanSide.BLACK`.
- [ ] Depth 1 and 12 boundaries remain selectable.
- [ ] Descriptor-to-depth labels are correct if descriptors exist.
- [ ] Start Game is fully visible at 360 × 640 dp.
- [ ] Setup screen has no root scroll semantics.
- [ ] Busy state does not move Start Game or selector controls outside viewport.

### Phase 4 acceptance

- [ ] Setup screen reads as a player-facing chess product, not a developer demo.
- [ ] Entire setup flow is visible without scrolling.

## Phase 5 — Redesign board rendering and interaction affordances

### Phase 5.1 Board palette

- [ ] Replace old board colors with product board tokens.
- [ ] Preserve correct `a1` dark-square parity.
- [ ] Verify both White and Black orientation color parity.

### Phase 5.2 Piece assets

- [ ] Evaluate a coherent vector chess-piece set with acceptable license/provenance.
- [ ] If third-party assets are used:
  - [ ] record source;
  - [ ] record license;
  - [ ] include required attribution/license file;
  - [ ] ensure redistribution is permitted.
- [ ] Prefer one coherent bundled vector set for all 12 pieces.
- [ ] Do not fetch piece images at runtime.
- [ ] Do not mix emoji/device-font rendering styles.
- [ ] If no acceptable set is available, keep current glyph rendering temporarily only with an explicit unchecked follow-up rather than using unlicensed assets.

### Phase 5.3 Coordinates

- [ ] Keep rank/file labels.
- [ ] Reduce visual prominence relative to pieces.
- [ ] Verify labels remain correct after Black rotation.

### Phase 5.4 Selection

- [ ] Implement a restrained selected-square treatment.
- [ ] Avoid obscuring piece visibility.
- [ ] Keep semantic `selected` indication.

### Phase 5.5 Legal move targets

- [ ] Empty legal destination uses a compact dot or equivalent marker.
- [ ] Occupied legal capture destination uses a ring/outline or equivalent marker.
- [ ] Do not rely on color alone.
- [ ] Keep legal target source entirely from Rust-provided legal moves.

### Phase 5.6 Last-move highlight

- [ ] Derive source/destination squares from the most recent authoritative UCI move for presentation only.
- [ ] Highlight source and destination subtly.
- [ ] Apply after human move.
- [ ] Apply after engine move.
- [ ] Preserve highlight through the one-second reveal flow appropriately.
- [ ] Work in White orientation.
- [ ] Work in Black orientation.
- [ ] Define visual precedence among last move, selected square, and legal target.
- [ ] Do not change game state from highlight logic.

### Phase 5 tests

- [ ] Starting board piece positions still parse correctly from FEN.
- [ ] White orientation remains correct.
- [ ] Black orientation remains correct.
- [ ] `a1` is dark.
- [ ] last-move UCI parsing identifies correct source/destination.
- [ ] promotion UCI last move still highlights correct source/destination.
- [ ] legal-target projection tests remain green.
- [ ] tap-to-move behavior remains green.

### Phase 5 acceptance

- [ ] Board looks coherent with the new product visual system.
- [ ] Board remains authoritative-presentation-only; no Kotlin move generator appears.
- [ ] Engine reply is easier to visually identify.

## Phase 6 — Replace large status card with compact stable status region

### Phase 6.1 Status content

- [ ] Display primary state:
  - [ ] `Your move`;
  - [ ] `Engine thinking…`;
  - [ ] terminal outcome;
  - [ ] equivalent explicit engine-turn state where necessary.
- [ ] Display human side compactly.
- [ ] Display configured depth compactly.
- [ ] Display concise last action/status text when useful.

### Phase 6.2 Thinking state

- [ ] Add compact progress/spinner treatment inside fixed bounds.
- [ ] Do not increase/decrease status-region height when thinking toggles.
- [ ] Do not push board downward when progress appears.

### Phase 6.3 One-second reveal integration

- [ ] Preserve immediate human-move snapshot display.
- [ ] Preserve approximately one-second delay before first engine-result poll/reveal.
- [ ] Keep engine computation concurrent during delay.
- [ ] Use status/last-move highlight to make the transition understandable.
- [ ] Keep existing timing regression test green.

### Phase 6 tests

- [ ] Measure board bounds in `Your move` state.
- [ ] Measure board bounds in `thinking` state.
- [ ] Measure board bounds after engine reply.
- [ ] Assert board position/size remains stable within explicit tolerance.
- [ ] Existing one-second regression remains green.

### Phase 6 acceptance

- [ ] Status communicates turn clearly without consuming a large card.
- [ ] Thinking transitions do not cause layout jumps.

## Phase 7 — Introduce fixed Moves / Engine tab region

### Phase 7.1 Tab state

- [ ] Add Android presentation-only tab state, e.g. `GameTab.MOVES` / `GameTab.ENGINE`.
- [ ] Keep tab state out of Rust game/session state.
- [ ] Preserve selected tab through normal move updates.
- [ ] Reset to intended default on New Game/Restart only if explicitly defined.

### Phase 7.2 Tab selector

- [ ] Build compact accessible selector with `Moves` and `Engine`.
- [ ] Selected state is visually clear.
- [ ] Selected state is exposed semantically.
- [ ] Tab row remains fixed regardless of tab content.

### Phase 7.3 Tab body

- [ ] Allocate fixed/bounded body height.
- [ ] Moves and Engine content render inside same bounds.
- [ ] Switching tabs does not resize/move board.
- [ ] Switching tabs does not move action row.

### Phase 7 tests

- [ ] Moves selected semantics are correct.
- [ ] Engine selected semantics are correct.
- [ ] Tab switching changes only body content.
- [ ] Board bounds are equal before/after tab switch.
- [ ] Action-row bounds are equal before/after tab switch.

### Phase 7 acceptance

- [ ] Engine and move history no longer stack vertically below one another.
- [ ] Both are available without whole-screen scrolling.

## Phase 8 — Add Rust-authoritative SAN move-history presentation

Do not implement SAN disambiguation in Kotlin.

### Phase 8.1 Ownership decision

- [ ] Inspect `chess-core` for existing SAN/algebraic notation support.
- [ ] If an existing helper is correct and reusable, use it.
- [ ] Otherwise choose the narrowest appropriate Rust ownership layer for SAN generation.
- [ ] Keep SAN formatter free of Android/JNI dependencies if it is fundamentally chess notation logic.
- [ ] Do not add SAN conversion by replaying approximate rules in Compose.

### Phase 8.2 SAN formatter

If new implementation is required:

- [ ] format pawn quiet moves;
- [ ] format piece quiet moves;
- [ ] format captures;
- [ ] format pawn-file capture notation;
- [ ] format ambiguous piece disambiguation;
- [ ] format kingside castling;
- [ ] format queenside castling;
- [ ] format promotion;
- [ ] format check suffix;
- [ ] format checkmate suffix;
- [ ] handle en passant capture consistently with SAN;
- [ ] use authoritative pre/post move positions as necessary rather than guessing from UCI alone.

### Phase 8.3 Snapshot/JNI protocol

- [ ] Decide whether to expose:
  - [ ] SAN move-history list as an additional versioned snapshot field; or
  - [ ] an equivalent structured move-history field that includes both UCI and SAN.
- [ ] Bump snapshot protocol version if wire shape changes.
- [ ] Keep parser fail-closed on wrong version/field count.
- [ ] Keep existing UCI history available where required for board highlight/tests/internal behavior.
- [ ] Update Rust snapshot encoder tests.
- [ ] Update Kotlin snapshot parser tests.
- [ ] Update host JVM JNI contract tests if protocol expectations change.

### Phase 8.4 SAN Rust tests

- [ ] pawn quiet move.
- [ ] piece quiet move.
- [ ] capture.
- [ ] same-piece file disambiguation.
- [ ] same-piece rank disambiguation where possible.
- [ ] check.
- [ ] checkmate.
- [ ] kingside castling.
- [ ] queenside castling.
- [ ] promotion.
- [ ] promotion plus check/mate as applicable.
- [ ] en passant.
- [ ] sequential move history.
- [ ] no mutation of authoritative game during formatting.

### Phase 8 acceptance

- [ ] Android can display correct SAN without Kotlin chess-rule duplication.
- [ ] UCI remains available for internal move identity/board highlighting.
- [ ] Snapshot versioning remains explicit and tested.

## Phase 9 — Build the bounded Moves tab

### Phase 9.1 Row layout

- [ ] Display numbered rows with White and Black columns.
- [ ] Use SAN strings.
- [ ] Keep columns aligned on narrow portrait screens.
- [ ] Handle an incomplete final move pair cleanly.
- [ ] Visually distinguish newest move subtly.

### Phase 9.2 Internal scrolling

- [ ] Make only move-list contents vertically scrollable.
- [ ] Keep Moves panel/tab body itself fully visible.
- [ ] Keep tab selector fixed.
- [ ] Keep board fixed.
- [ ] Keep actions fixed.

### Phase 9.3 Auto-scroll policy

- [ ] If list is already at/near bottom, keep newest move visible after a new move.
- [ ] If user manually scrolls upward, do not forcibly yank list to bottom on new move.
- [ ] Define threshold deterministically.
- [ ] Preserve sensible scroll state when switching to Engine and back.
- [ ] Reset history/scroll state appropriately on Restart/New Game.

### Phase 9 tests

- [ ] short history fits without internal scrolling.
- [ ] long history scrolls internally.
- [ ] root Game remains stationary while Moves list scrolls.
- [ ] newest move appears when user is at bottom.
- [ ] manual historical position is not forcibly lost when user is scrolled up.
- [ ] SAN rows map correctly to move numbers/colors.

### Phase 9 acceptance

- [ ] User can review arbitrary move history without moving the board or game controls.
- [ ] No raw UCI move list is shown as the primary player-facing history.

## Phase 10 — Redesign the Engine tab

### Phase 10.1 Compact metrics

- [ ] Display available depth.
- [ ] Display score.
- [ ] Display nodes.
- [ ] Display NPS.
- [ ] Display elapsed time.
- [ ] Display PV.
- [ ] Keep hash fullness secondary/optional.
- [ ] Do not fabricate missing values.

### Phase 10.2 Formatting

- [ ] Preserve exact underlying values while formatting them readably.
- [ ] Format large node/NPS values consistently.
- [ ] Preserve mate-vs-centipawn score semantics.
- [ ] Keep PV bounded/wrapped within the tab body.
- [ ] Ensure long PV cannot make root Game scroll.

### Phase 10.3 Opening-book metrics

- [ ] Inspect whether snapshot has authoritative knowledge that a move was a book hit.
- [ ] If not, do not infer `Book move` from zero nodes/timing.
- [ ] If adding explicit book-source metadata is desirable, add it only through shared Rust application state with focused tests.
- [ ] Do not make book-source metadata a prerequisite for the visual redesign if it expands scope excessively.

### Phase 10 tests

- [ ] no-metrics state is intentional/readable.
- [ ] partial-metrics state does not fabricate values.
- [ ] full-metrics state fits bounded tab body.
- [ ] long PV stays bounded.
- [ ] tab switch does not move board.

### Phase 10 acceptance

- [ ] Engine panel feels like useful chess analysis, not a raw debug dump.
- [ ] No whole-screen scrolling is introduced by metrics.

## Phase 11 — Redesign fixed game action region

### Phase 11.1 Action row

- [ ] Place New Game, Restart, Resign in one fixed visible action region.
- [ ] Use compact text labels and coherent vector icons where useful.
- [ ] Keep practical touch targets.
- [ ] Keep button positions stable when disabled/enabled.

### Phase 11.2 Semantics

- [ ] New Game remains confirmation-gated.
- [ ] Restart remains confirmation-gated.
- [ ] Resign remains confirmation-gated.
- [ ] Resign uses `Danger` styling.
- [ ] Resign remains disabled after terminal outcome where appropriate.
- [ ] Busy state disables incompatible actions without moving them.

### Phase 11 tests

- [ ] all three actions simultaneously visible at compact target.
- [ ] New Game opens correct dialog.
- [ ] Restart opens correct dialog.
- [ ] Resign opens correct dialog.
- [ ] disabled-state semantics correct.

### Phase 11 acceptance

- [ ] No game action requires page scrolling or hidden overflow discovery.

## Phase 12 — Restyle all dialogs and modal flows

### Phase 12.1 Confirmation dialogs

- [ ] New Game dialog uses product theme.
- [ ] Restart dialog uses product theme.
- [ ] Resign dialog uses product theme.
- [ ] Preserve existing titles/body meaning.
- [ ] Keep Cancel explicit.
- [ ] Use destructive emphasis only where appropriate.

### Phase 12.2 Promotion dialog

- [ ] Restyle promotion modal.
- [ ] Show Queen/Rook/Bishop/Knight clearly.
- [ ] Use piece icon/label treatment consistent with board assets if practical.
- [ ] Keep actual chosen value an authoritative legal promotion UCI move.
- [ ] Keep Cancel behavior.

### Phase 12.3 Error dialog

- [ ] Restyle `Chess engine error` dialog.
- [ ] Keep real error text visible.
- [ ] Bound long error content appropriately.
- [ ] Do not auto-retry.
- [ ] Do not reset game silently.
- [ ] Do not choose fallback move.

### Phase 12 tests

- [ ] confirmation labels/actions unchanged semantically.
- [ ] promotion order/choice maps to exact authoritative move.
- [ ] error dismissal clears only UI error state intended by current ViewModel.
- [ ] no dialog causes root Game layout state to be lost unexpectedly.

### Phase 12 acceptance

- [ ] Modal states look like part of the same product.
- [ ] Error/failure behavior remains explicit.

## Phase 13 — Accessibility and large-text hardening

### Phase 13.1 Semantics

- [ ] Preserve board square coordinate/piece content descriptions.
- [ ] Preserve selected-square semantics.
- [ ] Preserve legal-target semantics.
- [ ] Add tab selected-state semantics.
- [ ] Add side-selector selected-state semantics.
- [ ] Add meaningful labels to icon-bearing action controls.
- [ ] Avoid redundant decorative image announcements.

### Phase 13.2 Non-color cues

- [ ] Selection not communicated by color alone.
- [ ] Legal move target not communicated by color alone.
- [ ] Error/destructive action not communicated by color alone.
- [ ] Tab selection not communicated by color alone.

### Phase 13.3 Contrast

- [ ] Validate primary text contrast on `AppBackground`.
- [ ] Validate secondary text contrast on `Surface`/`SurfaceMuted`.
- [ ] Validate control labels on accent/danger surfaces.
- [ ] Validate board piece readability on both square colors.
- [ ] Validate legal/selection overlays do not destroy piece contrast.

### Phase 13.4 Font scaling

- [ ] Test default font scale.
- [ ] Test at least one enlarged common font scale.
- [ ] Keep game actions/core turn state visible.
- [ ] Keep board usable.
- [ ] If secondary analysis content needs internal adaptation, keep it inside bounded tab region rather than adding root scrolling.

### Phase 13 acceptance

- [ ] Redesign does not trade accessibility for visual polish.

## Phase 14 — Strengthen Compose/UI instrumentation infrastructure

### Phase 14.1 Dependencies

- [ ] Inspect current Android test dependencies.
- [ ] Add `androidx.compose.ui:ui-test-junit4` / manifest support or equivalent only if needed.
- [ ] Keep dependency versions aligned with current Compose/Kotlin generation.
- [ ] Do not bundle a broad toolchain upgrade with UI tests.

### Phase 14.2 Viewport containment helpers

- [ ] Add reusable test helper for root viewport bounds.
- [ ] Add helper to assert a tagged node is fully contained, not merely partially intersecting/displayed.
- [ ] Add helper to compare board bounds across states.
- [ ] Keep tolerance explicit and small.

### Phase 14.3 Compact-size testing

- [ ] Implement deterministic 360 × 640 dp test strategy.
- [ ] Document why the chosen test genuinely constrains layout to that usable size.
- [ ] Avoid a screenshot-only claim.

### Phase 14 acceptance

- [ ] Layout regressions become test failures rather than subjective discoveries on a phone.

## Phase 15 — End-to-end UI behavior regression suite

Add or expand instrumentation tests for the redesigned UI.

### Phase 15.1 Setup

- [ ] launcher opens Setup.
- [ ] Setup root not scrollable.
- [ ] title visible.
- [ ] side selector fully visible.
- [ ] depth control fully visible.
- [ ] Start Game fully visible.
- [ ] choose White.
- [ ] choose Black.
- [ ] select minimum depth.
- [ ] select maximum depth.

### Phase 15.2 Game shell

- [ ] start Human White game.
- [ ] status fully visible.
- [ ] complete board fully visible.
- [ ] tab selector fully visible.
- [ ] complete tab body fully visible.
- [ ] action row fully visible.
- [ ] root Game not scrollable.

### Phase 15.3 Real play

- [ ] human move via board taps still works.
- [ ] human move appears immediately.
- [ ] one-second engine reveal delay still holds.
- [ ] opening-book reply remains exact where covered.
- [ ] engine reply last-move highlight correct.
- [ ] status returns to human turn.

### Phase 15.4 Black orientation

- [ ] Human Black starts with shared Rust engine White move.
- [ ] Black board orientation correct.
- [ ] status indicates correct human side.
- [ ] all fixed UI remains within viewport.

### Phase 15.5 Tabs

- [ ] Moves tab displays history.
- [ ] Moves list scrolls internally with fixture/long game.
- [ ] Engine tab displays available metrics.
- [ ] switching tabs does not change board bounds.
- [ ] switching tabs does not change action-row bounds.

### Phase 15.6 Dialogs

- [ ] New Game confirmation reachable.
- [ ] Restart confirmation reachable.
- [ ] Resign confirmation reachable.
- [ ] promotion flow tested with deterministic fixture/path.
- [ ] error dialog tested if controlled injection can be done without production fallback hooks.

### Phase 15.7 Spatial stability

- [ ] board bounds stable from idle -> human move -> thinking -> engine reply.
- [ ] board bounds stable across status-message changes.
- [ ] board bounds stable across Moves/Engine tab switch.
- [ ] action row remains fully visible in all those states.

### Phase 15 acceptance

- [ ] All core UX invariants have automated runtime coverage.

## Phase 16 — Anti-fallback and architecture audit

Perform an explicit source review before declaring UI completion.

### Phase 16.1 Kotlin/Compose audit

- [ ] Search for random/first-legal move fallback.
- [ ] Search for UI-side opening-book move choice.
- [ ] Search for UI-side chess legality logic.
- [ ] Search for UI-side SAN disambiguation logic.
- [ ] Search for silent `try/catch` that suppresses reachable-owner native failures.
- [ ] Search for default/fake snapshots after JNI failure.
- [ ] Search for silent depth clamping outside intended user slider conversion.
- [ ] Search for automatic search retries.
- [ ] Search for stale coroutine updates lacking generation protection.
- [ ] Confirm one-second delay remains presentation-only.

### Phase 16.2 Rust/JNI audit

- [ ] Confirm shared opening-book-first worker still authoritative.
- [ ] Confirm book errors remain fail-visible rather than silent search fallback.
- [ ] Confirm search fallback rejection remains intact.
- [ ] Confirm JNI snapshot version validation remains strict.
- [ ] Confirm destroy failure remains retryable while owner reachable.
- [ ] Confirm SAN additions, if any, cannot mutate authoritative game state unexpectedly.

### Phase 16.3 Cross-frontend audit

- [ ] TUI opening-book behavior unaffected.
- [ ] Console opening-book behavior unaffected.
- [ ] Android UI redesign does not introduce dependencies from `chess-core`/`chess-search` to Android.
- [ ] Android does not route through UCI.

### Phase 16 acceptance

- [ ] No unsafe/silent fallback introduced by UI polish.
- [ ] Rust/Kotlin ownership boundary remains clean.

## Phase 17 — Full local validation

Run supported gates on exact implementation source SHA.

- [ ] `cargo fmt --all -- --check` through supported developer workflow where applicable.
- [ ] strict workspace Clippy through supported developer workflow.
- [ ] Rust tests affected by SAN/snapshot changes.
- [ ] host JVM JNI contract.
- [ ] Android app JVM/unit tests.
- [ ] Android lint.
- [ ] Android APK/test APK build.
- [ ] API-35 instrumentation.
- [ ] `bash scripts/dev.sh android`.
- [ ] `bash scripts/dev.sh fast` if repository policy expects it for cross-workspace changes.
- [ ] Record exact commands and results.

### Phase 17 acceptance

- [ ] No local/focused failure remains unexplained.
- [ ] No warnings are hidden by suppression.

## Phase 18 — Permanent CI integration

### Phase 18.1 Workflow

- [ ] Update `.github/workflows/android.yml` only as required for new UI tests/dependencies.
- [ ] Keep permanent API-35 emulator runtime coverage.
- [ ] Keep host JNI coverage.
- [ ] Keep lint/unit-test jobs.
- [ ] Keep ARM64/x86_64 JNI packaging checks.
- [ ] Keep debug APK artifact publication.
- [ ] Add compact-layout/UI assertions to permanent CI rather than leaving them temporary.

### Phase 18.2 CI safety

- [ ] Workflow permissions remain least-privilege.
- [ ] No workflow source modifications.
- [ ] No CI-generated commits.
- [ ] Temporary capture workflow/script removed before final closure unless promoted intentionally.

### Phase 18 acceptance

- [ ] Exact final source SHA is validated by permanent Android CI.
- [ ] All required permanent jobs are green.

## Phase 19 — Final actual-emulator visual evidence

Capture real application pixels at the final implementation SHA.

### Phase 19.1 Required captures

- [ ] Setup screen.
- [ ] Human White game, initial/idle.
- [ ] Human White after a human move during one-second pause.
- [ ] Human White after engine reply.
- [ ] Human Black game.
- [ ] Moves tab with multiple rows.
- [ ] Moves tab with internal scroll demonstrated.
- [ ] Engine tab with populated metrics.
- [ ] Engine-thinking state.
- [ ] New Game dialog.
- [ ] Restart dialog.
- [ ] Resign dialog.
- [ ] Promotion dialog if deterministic fixture/path available.
- [ ] Error dialog if controlled safe test path available.

### Phase 19.2 Evidence quality

- [ ] Screenshots come from actual APK/emulator/device, not generated mockups.
- [ ] Capture exact source SHA.
- [ ] Record workflow run/job if captured in CI.
- [ ] Record artifact ID/name/digest.
- [ ] Verify screenshots manually before citing them.
- [ ] Ensure no screenshot is accidentally a setup spinner/transient wrong state.

### Phase 19.3 Before/after review

- [ ] Compare final captures to baseline artifact `9053263983`.
- [ ] Verify root-scroll problem is visibly eliminated.
- [ ] Verify board remains dominant.
- [ ] Verify no primary control is partially off-screen.
- [ ] Verify dark product palette is consistent.
- [ ] Verify Moves/Engine tab region is fully visible.

### Phase 19 acceptance

- [ ] Actual visual evidence matches the implemented product and this spec.

## Phase 20 — Physical-device UX check

Emulator assertions are authoritative for automated layout, but a real phone review is still valuable for touch/legibility.

- [ ] Install exact green APK on a representative physical Android phone if available.
- [ ] Verify portrait lock.
- [ ] Verify setup fits without scrolling.
- [ ] Verify game fits without scrolling.
- [ ] Verify board touch targets feel usable.
- [ ] Verify selected/legal/last-move states are easy to distinguish.
- [ ] Verify one-second engine reply delay feels natural.
- [ ] Verify Moves list internal scrolling feels natural.
- [ ] Verify Engine tab remains readable.
- [ ] Verify dialogs are comfortably tappable.
- [ ] Record any subjective UX follow-up separately rather than weakening automated acceptance.

### Phase 20 acceptance

- [ ] No device-only blocker discovered, or any blocker is fixed/revalidated before closure.

## Phase 21 — Documentation update

- [ ] Update `docs/RUST_ANDROID_APP.md` with:
  - [ ] portrait-only policy;
  - [ ] product theme overview;
  - [ ] no-primary-page-scroll invariant;
  - [ ] game layout structure;
  - [ ] Moves/Engine tabs;
  - [ ] SAN display ownership;
  - [ ] piece asset/license provenance;
  - [ ] UI test commands.
- [ ] Update `README.md` Android section if screenshots/description are stale.
- [ ] Update `docs/RUST_DEVELOPER_WORKFLOWS.md` for new permanent UI-test command(s).
- [ ] Update architecture docs only if SAN/snapshot ownership changes warrant it.
- [ ] Do not modify `AGENTS.md`/`CLAUDE.md` unless operating rules actually changed.

### Phase 21 acceptance

- [ ] Documentation describes shipped implementation, not aspirational UI.

## Phase 22 — Final repository validation and evidence closure

### Phase 22.1 Exact final SHA

- [ ] Record final clean product/documentation `master` SHA.
- [ ] Confirm no temporary capture workflow/script remains.
- [ ] Confirm no generated APK/JNI binaries are accidentally committed.
- [ ] Confirm Cargo/Gradle lock/config files have only intentional changes.

### Phase 22.2 Final permanent CI

- [ ] Permanent Android workflow green on exact final SHA.
- [ ] Record Android workflow run ID/URL.
- [ ] Record API-35 emulator job ID.
- [ ] Record host JNI job ID.
- [ ] Record lint/unit-test job ID.
- [ ] Record APK artifact ID/name/digest.
- [ ] If Rust/core snapshot/SAN changes trigger general repository CI, require it green on the exact final SHA too.
- [ ] Record general CI run/job evidence as applicable.

### Phase 22.3 Final anti-fallback declaration

- [ ] Confirm no random move fallback.
- [ ] Confirm no first-legal fallback.
- [ ] Confirm no silent search retry.
- [ ] Confirm no silent depth reduction.
- [ ] Confirm no Python fallback.
- [ ] Confirm no UCI subprocess fallback.
- [ ] Confirm no UI-side opening-book choice.
- [ ] Confirm no UI-side chess legality implementation.
- [ ] Confirm no UI-side SAN rule implementation.
- [ ] Confirm reachable-owner cleanup failures remain visible/retryable.

### Phase 22.4 Closure evidence block

Record here before marking complete:

```text
Implementation start SHA:
Final source SHA:
Final documentation SHA:

bash scripts/dev.sh android:
bash scripts/dev.sh fast (if required):

Permanent Android CI run:
Android API-35 job:
Host JNI job:
Android lint/unit job:
APK artifact:
APK SHA-256:

General repository CI run (if required):
General CI key job(s):

Final screenshot/evidence run:
Final screenshot artifact:
Physical-device result:
```

### Phase 22 acceptance

- [ ] Exact final SHA is clean and reproducibly green.
- [ ] Evidence block is complete.
- [ ] No task is marked complete based solely on subjective visual review.

## Final program acceptance checklist

Do not close this TODO until every applicable item below is true.

### Product presentation

- [ ] App uses intentional dark product palette.
- [ ] Setup looks production-quality rather than like a developer demo.
- [ ] Game looks production-quality rather than like a stacked diagnostic form.
- [ ] Piece rendering is coherent and professionally licensed/first-party.
- [ ] Dialogs share the same product language.

### Portrait/layout contract

- [ ] Activity is portrait-only.
- [ ] Setup root does not scroll.
- [ ] Game root does not scroll.
- [ ] Complete board visible.
- [ ] Complete status region visible.
- [ ] Complete tab row visible.
- [ ] Complete tab body visible.
- [ ] Complete action row visible.
- [ ] All are simultaneously visible at minimum supported viewport.
- [ ] Board shrinks rather than pushing UI off-screen.
- [ ] Board remains spatially stable during play.

### Game UX

- [ ] Human White interaction works.
- [ ] Human Black interaction works.
- [ ] Board orientation correct for both sides.
- [ ] Selected square clear.
- [ ] Legal targets clear.
- [ ] Last move clear.
- [ ] one-second engine reveal preserved.
- [ ] New Game always reachable.
- [ ] Restart always reachable.
- [ ] Resign always reachable.

### Moves/Engine information

- [ ] Moves/Engine tabs share one bounded region.
- [ ] Move history uses correct SAN.
- [ ] UCI remains authoritative/internal where needed.
- [ ] Moves list scrolls internally only.
- [ ] User historical scroll is not aggressively stolen.
- [ ] Engine metrics are compact/readable.
- [ ] Missing engine metrics are not fabricated.
- [ ] Long PV cannot create root scrolling.

### Correctness and architecture

- [ ] Rust remains authoritative for chess rules.
- [ ] Rust remains authoritative for search.
- [ ] Rust remains authoritative for opening book.
- [ ] SAN rule/disambiguation logic remains Rust-side.
- [ ] Kotlin remains presentation/lifecycle orchestration only.
- [ ] No alternate engine path added.
- [ ] No silent fallback added.
- [ ] Snapshot protocol changes are versioned and tested.
- [ ] Lifecycle/cleanup behavior remains fail-visible.

### Accessibility

- [ ] Core controls have practical touch targets.
- [ ] Board semantics preserved.
- [ ] Tab/selector semantics present.
- [ ] Color is not sole state indicator.
- [ ] Contrast reviewed.
- [ ] Enlarged font scale reviewed.

### Validation/evidence

- [ ] Existing opening-book tests green.
- [ ] Existing one-second reveal test green.
- [ ] New compact-layout tests green.
- [ ] New root-no-scroll tests green.
- [ ] New spatial-stability tests green.
- [ ] SAN tests green.
- [ ] `bash scripts/dev.sh android` green.
- [ ] Permanent Android CI green on exact final SHA.
- [ ] General CI green if cross-workspace Rust changes require it.
- [ ] Final real-emulator screenshots captured and reviewed.
- [ ] Final APK artifact recorded.
- [ ] Physical-device check completed if available.

## Ralph-loop stop condition

Stop only when:

1. every applicable checkbox is complete with evidence;
2. exact final source/documentation SHA is recorded;
3. permanent required CI is green on that exact SHA;
4. the app demonstrably satisfies the portrait/no-root-scroll layout contract on automated compact-layout coverage;
5. actual emulator screenshots show the implemented UI rather than generated mockups;
6. no dangerous fallback, silent failure, or presentation-side chess implementation has been introduced.

If any of those conditions is false, the redesign is not complete.
