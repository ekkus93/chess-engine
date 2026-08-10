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

# ---------------------------------------------------------------------------
# AR-008 shared dp-normalized layout support.
# ---------------------------------------------------------------------------
layout_support = ATEST / "LayoutTestSupport.kt"
layout_support.write_text(r'''package com.ekkus93.chessapp

import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.junit4.ComposeContentTestRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import kotlin.math.abs

internal const val BOUNDS_TOLERANCE_DP = 0.5f

internal fun pxRectToDp(rect: Rect, density: Float): Rect {
    require(density > 0f)
    return Rect(rect.left / density, rect.top / density, rect.right / density, rect.bottom / density)
}

internal fun boundsApproximatelyEqual(a: Rect, b: Rect, toleranceDp: Float = BOUNDS_TOLERANCE_DP): Boolean =
    abs(a.left - b.left) <= toleranceDp &&
        abs(a.top - b.top) <= toleranceDp &&
        abs(a.right - b.right) <= toleranceDp &&
        abs(a.bottom - b.bottom) <= toleranceDp

internal fun ComposeContentTestRule.boundsDp(tag: String): Rect {
    val density = InstrumentationRegistry.getInstrumentation().targetContext.resources.displayMetrics.density
    return pxRectToDp(onNodeWithTag(tag).fetchSemanticsNode().boundsInRoot, density)
}

internal fun ComposeContentTestRule.assertContained(rootTag: String, childTags: List<String>) {
    val root = boundsDp(rootTag)
    childTags.forEach { tag ->
        val child = boundsDp(tag)
        assertTrue("$tag left edge escaped $rootTag", child.left + BOUNDS_TOLERANCE_DP >= root.left)
        assertTrue("$tag top edge escaped $rootTag", child.top + BOUNDS_TOLERANCE_DP >= root.top)
        assertTrue("$tag right edge escaped $rootTag", child.right - BOUNDS_TOLERANCE_DP <= root.right)
        assertTrue("$tag bottom edge escaped $rootTag", child.bottom - BOUNDS_TOLERANCE_DP <= root.bottom)
        assertTrue("$tag must have positive width", child.width > 0f)
        assertTrue("$tag must have positive height", child.height > 0f)
    }
}

internal fun ComposeContentTestRule.assertNoRootScroll(tag: String) {
    val node = onNodeWithTag(tag).fetchSemanticsNode()
    assertFalse("$tag must not expose a root scroll action", node.config.contains(SemanticsActions.ScrollBy))
}

internal fun ComposeContentTestRule.assertSquare(tag: String) {
    val value = boundsDp(tag)
    assertTrue("$tag must remain square", abs(value.width - value.height) <= BOUNDS_TOLERANCE_DP)
}

internal fun assertBoundsEqual(expected: Rect, actual: Rect, label: String) {
    assertTrue("$label bounds changed: expected=$expected actual=$actual", boundsApproximatelyEqual(expected, actual))
}
''')

layout_test = ATEST / "ChessAppLayoutInstrumentedTest.kt"
text = layout_test.read_text()
# remove duplicated helper block
start = text.index("    private fun assertContained(")
end = text.index("    private fun gameState(", start)
text = text[:start] + text[end:]
text = text.replace("import androidx.compose.ui.geometry.Rect\n", "")
text = text.replace("import androidx.compose.ui.semantics.SemanticsActions\n", "")
text = text.replace("import org.junit.Assert.assertEquals\n", "")
text = text.replace("import org.junit.Assert.assertFalse\n", "")
text = text.replace("import org.junit.Assert.assertTrue\n", "")
text = text.replace("assertContained(", "composeRule.assertContained(")
text = text.replace("assertNoRootScroll(", "composeRule.assertNoRootScroll(")
text = text.replace("assertSquare(", "composeRule.assertSquare(")
text = text.replace("bounds(\"game-tab-body\")", "composeRule.boundsDp(\"game-tab-body\")")
text = text.replace("bounds(\"chess-board\")", "composeRule.boundsDp(\"chess-board\")")
text = text.replace("bounds(\"game-actions\")", "composeRule.boundsDp(\"game-actions\")")
text = text.replace("assertEquals(movesBounds, composeRule.boundsDp(\"game-tab-body\"))", "assertBoundsEqual(movesBounds, composeRule.boundsDp(\"game-tab-body\"), \"game-tab-body\")")
text = text.replace("assertEquals(idleBoard, composeRule.boundsDp(\"chess-board\"))", "assertBoundsEqual(idleBoard, composeRule.boundsDp(\"chess-board\"), \"chess-board\")")
text = text.replace("assertEquals(idleActions, composeRule.boundsDp(\"game-actions\"))", "assertBoundsEqual(idleActions, composeRule.boundsDp(\"game-actions\"), \"game-actions\")")
layout_test.write_text(text)

adaptive_test = ATEST / "ChessAppAdaptiveLayoutInstrumentedTest.kt"
text = adaptive_test.read_text()
start = text.index("    private fun assertContained(")
end = text.index("    private fun gameState(", start)
text = text[:start] + text[end:]
text = text.replace("import androidx.compose.ui.geometry.Rect\n", "")
text = text.replace("import org.junit.Assert.assertFalse\n", "")
text = text.replace("assertContained(", "composeRule.assertContained(")
text = text.replace("assertNoRootScroll(", "composeRule.assertNoRootScroll(")
text = text.replace("assertSquare(", "composeRule.assertSquare(")
adaptive_test.write_text(text)

support_test = ATEST / "LayoutTestSupportInstrumentedTest.kt"
support_test.write_text(r'''package com.ekkus93.chessapp

import androidx.compose.ui.geometry.Rect
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class LayoutTestSupportInstrumentedTest {
    @Test
    fun toleranceIsExplicitAndBounded() {
        val base = Rect(0f, 0f, 100f, 100f)
        assertTrue(boundsApproximatelyEqual(base, Rect(0.25f, 0.25f, 100.25f, 100.25f)))
        assertFalse(boundsApproximatelyEqual(base, Rect(0.75f, 0f, 100f, 100f)))
    }

    @Test
    fun pxNormalizationPreservesDpMeaningAtNonUnitDensity() {
        assertEquals(Rect(0f, 0f, 10f, 5f), pxRectToDp(Rect(0f, 0f, 20f, 10f), 2f))
    }
}
''')
mark("AR-008")
commit("AR-008", "test(android): share density-aware layout assertions", [TODO, layout_support, layout_test, adaptive_test, support_test], [compile_tests(), connected("com.ekkus93.chessapp.LayoutTestSupportInstrumentedTest"), connected("com.ekkus93.chessapp.ChessAppLayoutInstrumentedTest"), connected("com.ekkus93.chessapp.ChessAppAdaptiveLayoutInstrumentedTest")])

# ---------------------------------------------------------------------------
# Shared black/game fixture source for AR-009/010 and later focused coverage.
# ---------------------------------------------------------------------------
black_test = ATEST / "BlackOrientationInstrumentedTest.kt"
black_test.write_text(r'''package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class BlackOrientationInstrumentedTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun compactBlackGameIsContainedAndActuallyBlackOriented() {
        composeRule.setContent { RustChessTheme { Box(Modifier.requiredSize(360.dp, 640.dp)) {
            GameScreen(blackState(), {}, {}, {}, {})
        } } }
        composeRule.assertContained("game-screen", listOf("status-region", "chess-board", "game-tabs", "game-tab-body", "game-actions"))
        composeRule.assertNoRootScroll("game-screen")
        composeRule.assertSquare("chess-board")
        val density = InstrumentationRegistry.getInstrumentation().targetContext.resources.displayMetrics.density
        val board = composeRule.boundsDp("chess-board")
        val a1 = pxRectToDp(composeRule.onNodeWithContentDescription("a1 rook").fetchSemanticsNode().boundsInRoot, density)
        assertTrue("a1 must be above board midpoint for Black orientation", a1.center.y < board.center.y)
    }

    @Test
    fun blackBoardAndActionsStayFixedAcrossThinkingState() {
        val state = mutableStateOf(blackState())
        composeRule.setContent { RustChessTheme { Box(Modifier.requiredSize(360.dp, 640.dp)) {
            GameScreen(state.value, {}, {}, {}, {})
        } } }
        val board = composeRule.boundsDp("chess-board")
        val actions = composeRule.boundsDp("game-actions")
        composeRule.runOnUiThread { state.value = blackState(thinking = true, sideToMove = HumanSide.WHITE) }
        composeRule.waitForIdle()
        assertBoundsEqual(board, composeRule.boundsDp("chess-board"), "black chess-board")
        assertBoundsEqual(actions, composeRule.boundsDp("game-actions"), "black game-actions")
    }

    private fun blackState(thinking: Boolean = false, sideToMove: HumanSide = HumanSide.BLACK) = ChessUiState(
        humanSide = HumanSide.BLACK,
        engineDepth = 3,
        snapshot = ChessGameSnapshot(
            fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
            legalMoves = listOf("g8f6", "b8c6"), moves = emptyList(), sanMoves = emptyList(),
            humanSide = HumanSide.BLACK, sideToMove = sideToMove, thinking = thinking,
            outcome = null, statusMessage = null, engineDepth = 3, engineScore = "+0.10",
            engineNodes = 1000, engineNps = 2000, engineElapsed = "10 ms",
            principalVariation = listOf("g8f6"), hashFullPerMille = 1,
        ),
    )
}
''')
mark("AR-009")
commit("AR-009", "test(android): cover Black-oriented layout stability", [TODO, black_test], [compile_tests(), connected("com.ekkus93.chessapp.BlackOrientationInstrumentedTest")])

# AR-010 tab switch must not move board/actions.
tab_test = ATEST / "TabStabilityInstrumentedTest.kt"
tab_test.write_text(r'''package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class TabStabilityInstrumentedTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun boardAndActionsDoNotMoveAcrossTabSwitch() {
        composeRule.setContent { RustChessTheme { Box(Modifier.requiredSize(360.dp, 640.dp)) {
            GameScreen(gameState(), {}, {}, {}, {})
        } } }
        val board = composeRule.boundsDp("chess-board")
        val actions = composeRule.boundsDp("game-actions")
        composeRule.onNodeWithTag("tab-engine").performClick()
        composeRule.waitForIdle()
        assertBoundsEqual(board, composeRule.boundsDp("chess-board"), "chess-board")
        assertBoundsEqual(actions, composeRule.boundsDp("game-actions"), "game-actions")
    }

    private fun gameState() = ChessUiState(snapshot = ChessGameSnapshot(
        fen = "8/8/8/8/8/8/4K3/7k w - - 0 1", legalMoves = emptyList(), moves = emptyList(), sanMoves = emptyList(),
        humanSide = HumanSide.WHITE, sideToMove = HumanSide.WHITE, thinking = false, outcome = null, statusMessage = null,
        engineDepth = 4, engineScore = "+0.20", engineNodes = 12000, engineNps = 240000, engineElapsed = "50 ms",
        principalVariation = listOf("e2e3"), hashFullPerMille = 2,
    ))
}
''')
mark("AR-010")
commit("AR-010", "test(android): pin board and action bounds across tabs", [TODO, tab_test], [compile_tests(), connected("com.ekkus93.chessapp.TabStabilityInstrumentedTest")])

# AR-011 promotion callbacks.
promotion_test = ATEST / "PromotionDialogInstrumentedTest.kt"
promotion_test.write_text(r'''package com.ekkus93.chessapp

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class PromotionDialogInstrumentedTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun allPromotionButtonsReturnAuthoritativeMove() {
        var chosen: String? = null
        val moves = listOf("e7e8q", "e7e8r", "e7e8b", "e7e8n")
        composeRule.setContent { RustChessTheme { PromotionDialog(moves, { chosen = it }, {}) } }
        for ((label, expected) in listOf("Queen" to "e7e8q", "Rook" to "e7e8r", "Bishop" to "e7e8b", "Knight" to "e7e8n")) {
            composeRule.onNodeWithText(label).performClick()
            composeRule.runOnIdle { assertEquals(expected, chosen) }
        }
    }
}
''')
mark("AR-011")
commit("AR-011", "test(android): exercise promotion dialog callbacks", [TODO, promotion_test], [compile_tests(), connected("com.ekkus93.chessapp.PromotionDialogInstrumentedTest")])

# AR-012 error dialog dismissal.
error_test = ATEST / "ErrorDialogInstrumentedTest.kt"
error_test.write_text(r'''package com.ekkus93.chessapp

import androidx.compose.ui.test.assertExists
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

# AR-013 metrics content, including honest absence placeholders.
metrics_test = ATEST / "EnginePanelInstrumentedTest.kt"
metrics_test.write_text(r'''package com.ekkus93.chessapp

import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertExists
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

# AR-014 setup title tag/containment.
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
    @Test fun titleIsTaggedVisibleAndContained() {
        composeRule.setContent { RustChessTheme { Box(Modifier.requiredSize(360.dp, 640.dp)) { SetupScreen(ChessUiState(), {}, {}, {}) } } }
        composeRule.onNodeWithTag("setup-title").assertTextEquals("Rust Chess")
        composeRule.assertContained("setup-screen", listOf("setup-title"))
    }
}
''')
mark("AR-014")
commit("AR-014", "test(android): tag and contain setup title", [TODO, setup, layout_test, adaptive_test, setup_title_test], [compile_tests(), connected("com.ekkus93.chessapp.SetupTitleInstrumentedTest"), connected("com.ekkus93.chessapp.ChessAppLayoutInstrumentedTest")])

# AR-015 busy-state bounds and disabled semantics.
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

# AR-016 automated contrast validation. The existing teal target marker fails 3:1 on
# some board treatments, so make the marker semantic dark foreground before enforcing the gate.
theme = MAIN / "Theme.kt"
replace(theme, "internal val BoardLegalTarget = Color(0xCC2DD4BF)\n", "internal val BoardLegalTarget = AppBackground\n")
contrast_test = UTEST / "ThemeContrastTest.kt"
contrast_test.write_text(r'''package com.ekkus93.chessapp

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.lerp
import kotlin.math.max
import org.junit.Assert.assertTrue
import org.junit.Test

class ThemeContrastTest {
    private fun linear(c: Float): Double = if (c <= 0.04045f) c / 12.92 else Math.pow((c + 0.055) / 1.055, 2.4)
    private fun luminance(c: Color): Double = 0.2126 * linear(c.red) + 0.7152 * linear(c.green) + 0.0722 * linear(c.blue)
    private fun contrast(a: Color, b: Color): Double {
        val l1 = luminance(a); val l2 = luminance(b)
        return (max(l1, l2) + 0.05) / (kotlin.math.min(l1, l2) + 0.05)
    }
    private fun composite(fg: Color, bg: Color): Color {
        val a = fg.alpha + bg.alpha * (1f - fg.alpha)
        if (a == 0f) return Color.Transparent
        fun channel(f: Float, b: Float) = (f * fg.alpha + b * bg.alpha * (1f - fg.alpha)) / a
        return Color(channel(fg.red, bg.red), channel(fg.green, bg.green), channel(fg.blue, bg.blue), a)
    }
    private fun requireRatio(label: String, fg: Color, bg: Color, minimum: Double) {
        val value = contrast(fg, bg)
        assertTrue("$label contrast $value < $minimum", value >= minimum)
    }
    private fun pieceBoundary(label: String, fill: Color, stroke: Color, bg: Color) {
        val value = max(contrast(fill, bg), contrast(stroke, bg))
        assertTrue("$label composite silhouette boundary contrast $value < 3", value >= 3.0)
    }

    @Test
    fun textAndControlTokenPairsMeetAa() {
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
    fun piecesRemainRecognizableAcrossBoardTreatments() {
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
# Record the concrete adjustment rather than hiding it behind a generic checked box.
replace(TODO, "- [ ] Any failing combination's token value adjusted in `Theme.kt`; before/after values recorded here.", "- [x] Failing legal-target marker combinations were corrected by changing `BoardLegalTarget` from `Color(0xCC2DD4BF)` to opaque `AppBackground`; the automated matrix below validates the resulting marker on all exercised board treatments.")
mark("AR-016")
commit("AR-016", "test(android): enforce UI contrast matrix", [TODO, theme, contrast_test], [unit(), compile_tests()])

print("STAGE2_COMPLETE", subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip())
