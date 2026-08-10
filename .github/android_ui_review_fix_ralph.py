#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md"
APP = ROOT / "android-harness/android-app"
MAIN = APP / "src/main/kotlin/com/ekkus93/chessapp"
ATEST = APP / "src/androidTest/kotlin/com/ekkus93/chessapp"
UTEST = APP / "src/test/kotlin/com/ekkus93/chessapp"


def run(*args: str, check: bool = True):
    print("+", " ".join(args), flush=True)
    return subprocess.run(args, cwd=ROOT, text=True, check=check)


def sh(command: str, check: bool = True):
    print("+", command, flush=True)
    return subprocess.run(["bash", "-lc", command], cwd=ROOT, text=True, check=check)


def replace(path: Path, old: str, new: str, count: int = 1):
    text = path.read_text()
    if text.count(old) < count:
        raise RuntimeError(f"{path}: target missing: {old[:160]!r}")
    path.write_text(text.replace(old, new, count))


def mark(task: str):
    text = TODO.read_text()
    start = text.index(f"# {task}:")
    end = text.find("\n# AR-", start + 1)
    if end < 0:
        end = len(text)
    TODO.write_text(text[:start] + text[start:end].replace("- [ ]", "- [x]") + text[end:])


def commit(task: str, message: str, paths: list[Path], checks: list[str]):
    run("git", "diff", "--check")
    for command in checks:
        sh(command)
    run("git", "add", *[str(p.relative_to(ROOT)) for p in paths])
    run("git", "commit", "-m", message)
    run("git", "push", "origin", "HEAD:master")
    print(task, subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), flush=True)


def connected(cls: str) -> str:
    return "gradle -p android-harness :android-app:connectedDebugAndroidTest --no-daemon --stacktrace --console=plain -Pandroid.testInstrumentationRunnerArguments.class=" + cls


def unit() -> str:
    return "gradle -p android-harness :android-app:testDebugUnitTest --no-daemon --stacktrace --console=plain"


def compile_tests() -> str:
    return "gradle -p android-harness :android-app:assembleDebug :android-app:assembleDebugAndroidTest --no-daemon --stacktrace --console=plain"


run("git", "config", "user.name", "Ralph Loop")
run("git", "config", "user.email", "actions@users.noreply.github.com")

# AR-012: error dialog rendering/dismiss callback. assertExists is a SemanticsNodeInteraction
# member in this Compose version, not a top-level import.
error_test = ATEST / "ErrorDialogInstrumentedTest.kt"
error_test.write_text(r'''package com.ekkus93.chessapp

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ErrorDialogInstrumentedTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun errorMessageRendersAndDismissesOnlyThroughCallback() {
        var dismissed = false
        val message = "Deterministic engine failure 8472"
        composeRule.setContent { RustChessTheme { ChessEngineErrorDialog(message) { dismissed = true } } }
        composeRule.onNodeWithText(message).assertExists()
        composeRule.onNodeWithText("OK").performClick()
        composeRule.runOnIdle { assertTrue(dismissed) }
    }
}
''')
mark("AR-012")
commit("AR-012", "test(android): exercise engine error dialog dismissal", [TODO, error_test], [compile_tests(), connected("com.ekkus93.chessapp.ErrorDialogInstrumentedTest")])

# AR-013 engine metrics content, including honest placeholders for absent metrics.
metrics_test = ATEST / "EnginePanelInstrumentedTest.kt"
metrics_test.write_text(r'''package com.ekkus93.chessapp

import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class EnginePanelInstrumentedTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun fullMetricsRenderTheirFormattedValues() {
        composeRule.setContent { RustChessTheme { EnginePanel(snapshot(7, "+0.42", 12345, 987654, "1.2 s", listOf("e2e4", "e7e5"))) } }
        for (text in listOf("7", "+0.42", "12k", "988k", "Time 1.2 s", "PV e2e4 e7e5")) {
            composeRule.onNodeWithText(text).assertExists()
        }
    }

    @Test
    fun partialMetricsUseDashInsteadOfFabricatedZeros() {
        composeRule.setContent { RustChessTheme { EnginePanel(snapshot(5, null, null, null, null, emptyList())) } }
        composeRule.onNodeWithText("5").assertExists()
        composeRule.onAllNodesWithText("—").assertCountEquals(3)
        composeRule.onNodeWithText("Time —").assertExists()
        composeRule.onNodeWithText("PV —").assertExists()
    }

    private fun snapshot(depth: Int?, score: String?, nodes: Long?, nps: Long?, elapsed: String?, pv: List<String>) = ChessGameSnapshot(
        fen = "8/8/8/8/8/8/4K3/7k w - - 0 1", legalMoves = emptyList(), moves = emptyList(), sanMoves = emptyList(),
        humanSide = HumanSide.WHITE, sideToMove = HumanSide.WHITE, thinking = false, outcome = null, statusMessage = null,
        engineDepth = depth, engineScore = score, engineNodes = nodes, engineNps = nps, engineElapsed = elapsed,
        principalVariation = pv, hashFullPerMille = null,
    )
}
''')
mark("AR-013")
commit("AR-013", "test(android): validate rendered engine metrics", [TODO, metrics_test], [compile_tests(), connected("com.ekkus93.chessapp.EnginePanelInstrumentedTest")])

# AR-014 setup-title semantic tag and containment.
setup = MAIN / "SetupScreen.kt"
replace(setup, '''            Text(
                text = "Rust Chess",
                style = MaterialTheme.typography.headlineLarge,
                color = OnBackground,
            )
''', '''            Text(
                text = "Rust Chess",
                modifier = Modifier.testTag("setup-title"),
                style = MaterialTheme.typography.headlineLarge,
                color = OnBackground,
            )
''')
layout_test = ATEST / "ChessAppLayoutInstrumentedTest.kt"
adaptive_test = ATEST / "ChessAppAdaptiveLayoutInstrumentedTest.kt"
for path in (layout_test, adaptive_test):
    replace(path, 'listOf("side-white", "side-black", "depth-control", "start-game")', 'listOf("setup-title", "side-white", "side-black", "depth-control", "start-game")')
setup_title_test = ATEST / "SetupTitleInstrumentedTest.kt"
setup_title_test.write_text(r'''package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class SetupTitleInstrumentedTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun titleIsTaggedVisibleAndContained() {
        composeRule.setContent { RustChessTheme { Box(Modifier.requiredSize(360.dp, 640.dp)) { SetupScreen(ChessUiState(), {}, {}, {}) } } }
        composeRule.onNodeWithTag("setup-title").assertTextEquals("Rust Chess")
        composeRule.assertContained("setup-screen", listOf("setup-title"))
    }
}
''')
mark("AR-014")
commit("AR-014", "test(android): tag and contain setup title", [TODO, setup, layout_test, adaptive_test, setup_title_test], [compile_tests(), connected("com.ekkus93.chessapp.SetupTitleInstrumentedTest"), connected("com.ekkus93.chessapp.ChessAppLayoutInstrumentedTest")])

# AR-015 busy/game-over state must change semantics, not geometry.
panels = MAIN / "GamePanels.kt"
replace(panels, '''            modifier = Modifier
                .weight(1f)
                .fillMaxSize(),
            contentPadding = PaddingValues(horizontal = 6.dp),
            shape = MaterialTheme.shapes.small,
            border = BorderStroke(1.dp, Danger.copy(alpha = 0.65f)),
''', '''            modifier = Modifier
                .weight(1f)
                .fillMaxSize()
                .testTag("action-resign"),
            contentPadding = PaddingValues(horizontal = 6.dp),
            shape = MaterialTheme.shapes.small,
            border = BorderStroke(1.dp, Danger.copy(alpha = 0.65f)),
''')
busy_test = ATEST / "BusyLayoutInstrumentedTest.kt"
busy_test.write_text(r'''package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class BusyLayoutInstrumentedTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun setupBusyStateDisablesWithoutMovingControls() {
        val state = mutableStateOf(ChessUiState())
        composeRule.setContent { RustChessTheme { Box(Modifier.requiredSize(360.dp, 640.dp)) { SetupScreen(state.value, {}, {}, {}) } } }
        val tags = listOf("side-white", "side-black", "depth-control", "start-game")
        val before = tags.associateWith { composeRule.boundsDp(it) }
        composeRule.runOnUiThread { state.value = state.value.copy(busy = true) }
        composeRule.waitForIdle()
        tags.forEach { assertBoundsEqual(before.getValue(it), composeRule.boundsDp(it), it) }
        tags.forEach { composeRule.onNodeWithTag(it).assertIsNotEnabled() }
    }

    @Test
    fun gameBusyAndGameOverDisableResignWithoutMovingActions() {
        val state = mutableStateOf(gameState())
        composeRule.setContent { RustChessTheme { Box(Modifier.requiredSize(360.dp, 640.dp)) { GameScreen(state.value, {}, {}, {}, {}) } } }
        val before = composeRule.boundsDp("game-actions")
        composeRule.runOnUiThread { state.value = state.value.copy(busy = true) }
        composeRule.waitForIdle()
        assertBoundsEqual(before, composeRule.boundsDp("game-actions"), "busy game-actions")
        composeRule.onNodeWithTag("action-resign").assertIsNotEnabled()
        composeRule.runOnUiThread { state.value = gameState(outcome = "White wins") }
        composeRule.waitForIdle()
        assertBoundsEqual(before, composeRule.boundsDp("game-actions"), "game-over game-actions")
        composeRule.onNodeWithTag("action-resign").assertIsNotEnabled()
    }

    private fun gameState(outcome: String? = null) = ChessUiState(snapshot = ChessGameSnapshot(
        fen = "8/8/8/8/8/8/4K3/7k w - - 0 1", legalMoves = emptyList(), moves = emptyList(), sanMoves = emptyList(),
        humanSide = HumanSide.WHITE, sideToMove = HumanSide.WHITE, thinking = false, outcome = outcome, statusMessage = null,
        engineDepth = null, engineScore = null, engineNodes = null, engineNps = null, engineElapsed = null,
        principalVariation = emptyList(), hashFullPerMille = null,
    ))
}
''')
mark("AR-015")
commit("AR-015", "test(android): pin busy-state layout and actions", [TODO, panels, busy_test], [compile_tests(), connected("com.ekkus93.chessapp.BusyLayoutInstrumentedTest")])

# AR-016 contrast gate. The existing translucent teal legal-target marker does not
# reach 3:1 against all required board treatments, so use the semantic dark foreground.
theme = MAIN / "Theme.kt"
replace(theme, "internal val BoardLegalTarget = Color(0xCC2DD4BF)\n", "internal val BoardLegalTarget = AppBackground\n")
contrast_test = UTEST / "ThemeContrastTest.kt"
contrast_test.write_text(r'''package com.ekkus93.chessapp

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.lerp
import kotlin.math.max
import kotlin.math.min
import org.junit.Assert.assertTrue
import org.junit.Test

class ThemeContrastTest {
    private fun linear(c: Float): Double =
        if (c <= 0.04045f) c.toDouble() / 12.92 else Math.pow((c.toDouble() + 0.055) / 1.055, 2.4)

    private fun luminance(c: Color): Double =
        0.2126 * linear(c.red) + 0.7152 * linear(c.green) + 0.0722 * linear(c.blue)

    private fun contrast(a: Color, b: Color): Double {
        val l1 = luminance(a)
        val l2 = luminance(b)
        return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
    }

    private fun composite(fg: Color, bg: Color): Color {
        val a = fg.alpha + bg.alpha * (1f - fg.alpha)
        if (a == 0f) return Color.Transparent
        fun channel(f: Float, b: Float): Float = (f * fg.alpha + b * bg.alpha * (1f - fg.alpha)) / a
        return Color(channel(fg.red, bg.red), channel(fg.green, bg.green), channel(fg.blue, bg.blue), a)
    }

    private fun requireRatio(label: String, fg: Color, bg: Color, minimum: Double) {
        val value = contrast(fg, bg)
        assertTrue("$label contrast $value < $minimum", value >= minimum)
    }

    private fun pieceBoundary(label: String, fill: Color, stroke: Color, bg: Color) {
        val value = max(contrast(fill, bg), contrast(stroke, bg))
        assertTrue("$label silhouette boundary contrast $value < 3", value >= 3.0)
    }

    @Test
    fun textAndControlPairsMeetAa() {
        requireRatio("OnBackground/AppBackground", OnBackground, AppBackground, 4.5)
        requireRatio("OnSurfaceMuted/Surface", OnSurfaceMuted, Surface, 4.5)
        requireRatio("OnSurfaceMuted/SurfaceMuted", OnSurfaceMuted, SurfaceMuted, 4.5)
        requireRatio("primary label", AppBackground, Primary, 4.5)
        requireRatio("strong primary label", AppBackground, PrimaryStrong, 4.5)
        requireRatio("danger label", AppBackground, Danger, 4.5)
        requireRatio("coordinate on light", CoordinateLabelOnLight, BoardLight, 4.5)
        requireRatio("coordinate on dark", CoordinateLabelOnDark, BoardDark, 4.5)
    }

    @Test
    fun piecesAndLegalTargetsRemainRecognizableAcrossBoardTreatments() {
        for ((squareName, base) in listOf("light" to BoardLight, "dark" to BoardDark)) {
            val backgrounds = listOf(
                "base" to base,
                "last" to lerp(base, BoardLastMove, 0.30f),
                "selected" to composite(BoardSelected, base),
                "last+selected" to composite(BoardSelected, lerp(base, BoardLastMove, 0.30f)),
            )
            for ((treatment, bg) in backgrounds) {
                pieceBoundary("light piece/$squareName/$treatment", PieceLightFill, PieceLightStroke, bg)
                pieceBoundary("dark piece/$squareName/$treatment", PieceDarkFill, PieceDarkStroke, bg)
                val marker = composite(BoardLegalTarget, bg)
                requireRatio("legal target/$squareName/$treatment", marker, bg, 3.0)
            }
        }
    }
}
''')
replace(TODO, "- [ ] Any failing combination's token value adjusted in `Theme.kt`; before/after values recorded here.", "- [x] Failing legal-target marker combinations were corrected by changing `BoardLegalTarget` from `Color(0xCC2DD4BF)` to opaque `AppBackground`; the automated matrix validates the resulting marker on all exercised board treatments.")
mark("AR-016")
commit("AR-016", "test(android): enforce UI contrast matrix", [TODO, theme, contrast_test], [unit(), compile_tests()])

print("STAGE2_RESUME_COMPLETE", subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip())
