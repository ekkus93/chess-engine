#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
TODO = Path("docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md")
APP = Path("android-harness/android-app")
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
        raise RuntimeError(f"{path}: replacement target missing: {old[:120]!r}")
    path.write_text(text.replace(old, new, count))


def mark_section(task: str):
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
    run("git", "add", *[str(path) for path in paths])
    run("git", "commit", "-m", message)
    run("git", "push", "origin", "HEAD:master")
    print(task, subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(), flush=True)


def unit():
    return "gradle -p android-harness :android-app:testDebugUnitTest --no-daemon --stacktrace --console=plain"


def compile_tests():
    return "gradle -p android-harness :android-app:assembleDebug :android-app:assembleDebugAndroidTest --no-daemon --stacktrace --console=plain"


def connected(cls: str):
    return "gradle -p android-harness :android-app:connectedDebugAndroidTest --no-daemon --stacktrace --console=plain -Pandroid.testInstrumentationRunnerArguments.class=" + cls


run("git", "config", "user.name", "Ralph Loop")
run("git", "config", "user.email", "actions@users.noreply.github.com")

# AR-003: fix copy and overwrite the structural test class cleanly. The first runner's
# failed working-tree append never landed; AR-002 remains the exact resume point.
replace(MAIN / "SetupScreen.kt", '"Native cleanup must succeed before another game can start."', '"Cleanup must finish before another game can start."')
replace(MAIN / "SetupScreen.kt", '"Play against the native Rust chess engine."', '"Play against the Rust chess engine."')
(UTEST / "ReviewFixArchitectureTest.kt").write_text(r'''package com.ekkus93.chessapp

import java.io.File
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ReviewFixArchitectureTest {
    private fun source(name: String): String =
        File(System.getProperty("user.dir"), "src/main/kotlin/com/ekkus93/chessapp/$name").readText()

    @Test
    fun boardAndPieceComposablesDoNotOwnProductColorLiterals() {
        for (name in listOf("ChessPiece.kt", "ChessBoardView.kt")) {
            val text = source(name)
            assertFalse("$name must not own Color hex literals", Regex("Color\\(0xFF").containsMatchIn(text))
            assertFalse("$name must not own Color.Black/White literals", Regex("Color\\.(Black|White)").containsMatchIn(text))
        }
    }

    @Test
    fun boardUsesNamedLastMoveAndCoordinateTokens() {
        val text = source("ChessBoardView.kt")
        assertTrue(text.contains("lerp(baseColor, BoardLastMove, 0.30f)"))
        assertTrue(text.contains("CoordinateLabelOnLight"))
        assertTrue(text.contains("CoordinateLabelOnDark"))
    }

    @Test
    fun setupPlayerCopyDoesNotExposeNativeArchitectureJargon() {
        val text = source("SetupScreen.kt")
        val stringLiterals = Regex("\\\"(?:\\\\.|[^\\\"])*\\\"").findAll(text).map { it.value }.toList()
        assertFalse(stringLiterals.any { it.contains("native", ignoreCase = true) })
        assertFalse(stringLiterals.any { it.contains("JNI", ignoreCase = true) })
    }
}
''')
mark_section("AR-003")
commit("AR-003", "fix(android): remove architecture jargon from setup copy", [TODO, MAIN / "SetupScreen.kt", UTEST / "ReviewFixArchitectureTest.kt"], [unit(), compile_tests()])

# AR-004 verify first on API 35. Only add production flags if the observable runtime state fails.
system_test = ATEST / "SystemBarAppearanceInstrumentedTest.kt"
system_test.write_text(r'''package com.ekkus93.chessapp

import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.core.view.WindowCompat
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertFalse
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class SystemBarAppearanceInstrumentedTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun api35SystemBarsUseDarkIconAppearance() {
        composeRule.runOnIdle {
            val window = composeRule.activity.window
            val controller = WindowCompat.getInsetsController(window, window.decorView)
            assertFalse(controller.isAppearanceLightStatusBars)
            assertFalse(controller.isAppearanceLightNavigationBars)
        }
    }
}
''')
sh(compile_tests())
probe = sh(connected("com.ekkus93.chessapp.SystemBarAppearanceInstrumentedTest"), check=False)
main_changed = False
if probe.returncode != 0:
    replace(MAIN / "MainActivity.kt", "import androidx.lifecycle.viewmodel.compose.viewModel\n", "import androidx.lifecycle.viewmodel.compose.viewModel\nimport androidx.core.view.WindowCompat\n")
    replace(MAIN / "MainActivity.kt", "        super.onCreate(savedInstanceState)\n        setContent {\n", "        super.onCreate(savedInstanceState)\n        WindowCompat.getInsetsController(window, window.decorView).apply {\n            isAppearanceLightStatusBars = false\n            isAppearanceLightNavigationBars = false\n        }\n        setContent {\n")
    main_changed = True
    sh(compile_tests())
    sh(connected("com.ekkus93.chessapp.SystemBarAppearanceInstrumentedTest"))
else:
    print("AR-004 runtime probe passed before production modification; no window-management code added.")
mark_section("AR-004")
paths = [TODO, system_test] + ([MAIN / "MainActivity.kt"] if main_changed else [])
commit("AR-004", "fix(android): verify API 35 system bar appearance", paths, [compile_tests(), connected("com.ekkus93.chessapp.SystemBarAppearanceInstrumentedTest")])

# AR-005 documentation.
replace(MAIN / "GameScreen.kt", "        val nonBoardHeight = statusHeight + tabHeight + actionHeight + minimumPanelHeight + gap * 4\n        val boardSize = minOf(\n", "        val nonBoardHeight = statusHeight + tabHeight + actionHeight + minimumPanelHeight + gap * 4\n        // Use the largest square bounded by viewport width and by remaining height after fixed\n        // status/tab/action regions, the minimum panel, and gaps; the board shrinks first.\n        val boardSize = minOf(\n")
doc = Path("docs/RUST_ANDROID_APP.md")
if "### Board sizing" not in doc.read_text():
    doc.write_text(doc.read_text().rstrip() + "\n\n### Board sizing\n\nThe playable Compose shell computes `boardSize` as the minimum of available width and available height after subtracting the fixed `statusHeight`, `tabHeight`, `actionHeight`, `minimumPanelHeight`, and four inter-region gaps. This is a shrink-before-clip policy: the board gives up size before the status, tabs, bounded panel, or action row can be clipped.\n")
mark_section("AR-005")
commit("AR-005", "docs(android): document board sizing policy", [TODO, MAIN / "GameScreen.kt", doc], ["grep -Fq 'the board shrinks first' android-harness/android-app/src/main/kotlin/com/ekkus93/chessapp/GameScreen.kt && grep -Fq 'shrink-before-clip' docs/RUST_ANDROID_APP.md"])

# AR-006 replace timing dependence with explicit follow mode updated only while scrolling.
panels = MAIN / "GamePanels.kt"
replace(panels, "import androidx.compose.runtime.LaunchedEffect\nimport androidx.compose.runtime.remember\n", "import androidx.compose.runtime.LaunchedEffect\nimport androidx.compose.runtime.getValue\nimport androidx.compose.runtime.mutableStateOf\nimport androidx.compose.runtime.remember\nimport androidx.compose.runtime.setValue\nimport androidx.compose.runtime.snapshotFlow\n")
replace(panels, '''    val rows = remember(sanMoves) { moveRows(sanMoves) }
    LaunchedEffect(rows.size) {
        if (rows.isEmpty()) {
            return@LaunchedEffect
        }
        val layout = listState.layoutInfo
        val lastVisible = layout.visibleItemsInfo.lastOrNull()?.index
        val wasNearBottom = layout.totalItemsCount == 0 ||
            lastVisible == null || lastVisible >= layout.totalItemsCount - 2
        if (wasNearBottom) {
            listState.animateScrollToItem(rows.lastIndex)
        }
    }
''', '''    val rows = remember(sanMoves) { moveRows(sanMoves) }
    var followLatest by remember(listState) { mutableStateOf(true) }
    LaunchedEffect(listState) {
        snapshotFlow {
            val layout = listState.layoutInfo
            val lastVisible = layout.visibleItemsInfo.lastOrNull()?.index
            val nearBottom = layout.totalItemsCount == 0 ||
                lastVisible == null || lastVisible >= layout.totalItemsCount - 2
            listState.isScrollInProgress to nearBottom
        }.collect { (scrolling, nearBottom) ->
            // Layout growth alone cannot change follow mode; only an actual scroll does.
            if (scrolling) {
                followLatest = nearBottom
            }
        }
    }
    LaunchedEffect(rows.size, followLatest) {
        if (rows.isNotEmpty() && followLatest) {
            listState.animateScrollToItem(rows.lastIndex)
        }
    }
''')
mark_section("AR-006")
commit("AR-006", "fix(android): remove move-list effect ordering dependency", [TODO, panels], [compile_tests(), connected("com.ekkus93.chessapp.MoveHistoryAutoScrollInstrumentedTest")])

# AR-007 global active-game guard consistency.
vm = MAIN / "ChessViewModel.kt"
replace(vm, "    fun restartGame() {\n        val current = game ?: return\n", "    fun restartGame() {\n        val configuration = mutableState.value\n        if (!canRunActiveGameOperation(configuration)) return\n        val current = game ?: return\n")
replace(vm, "    fun resign() {\n        val current = game ?: return\n        val snapshot = mutableState.value.snapshot ?: return\n", "    fun resign() {\n        val configuration = mutableState.value\n        if (!canRunActiveGameOperation(configuration)) return\n        val current = game ?: return\n        val snapshot = configuration.snapshot ?: return\n")
replace(vm, "    private fun submitMove(move: String) {\n        val current = game ?: return\n", "    private fun submitMove(move: String) {\n        val configuration = mutableState.value\n        if (!canRunActiveGameOperation(configuration)) return\n        val current = game ?: return\n")
replace(vm, "private fun displayMessage(error: RuntimeException): String =\n", "internal fun canRunActiveGameOperation(state: ChessUiState): Boolean =\n    !state.isSetup && !state.busy && !state.cleanupRequired\n\nprivate fun displayMessage(error: RuntimeException): String =\n")
(UTEST / "ActiveGameOperationGuardTest.kt").write_text(r'''package com.ekkus93.chessapp

import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ActiveGameOperationGuardTest {
    private fun activeState(busy: Boolean = false, cleanupRequired: Boolean = false) = ChessUiState(
        snapshot = ChessGameSnapshot(
            fen = "8/8/8/8/8/8/4K3/7k w - - 0 1",
            legalMoves = emptyList(), moves = emptyList(), sanMoves = emptyList(),
            humanSide = HumanSide.WHITE, sideToMove = HumanSide.WHITE, thinking = false,
            outcome = null, statusMessage = null, engineDepth = null, engineScore = null,
            engineNodes = null, engineNps = null, engineElapsed = null,
            principalVariation = emptyList(), hashFullPerMille = null,
        ),
        busy = busy,
        cleanupRequired = cleanupRequired,
    )

    @Test
    fun onlyIdleActiveGameMayRunOperation() {
        assertTrue(canRunActiveGameOperation(activeState()))
        assertFalse(canRunActiveGameOperation(ChessUiState()))
        assertFalse(canRunActiveGameOperation(activeState(busy = true)))
        assertFalse(canRunActiveGameOperation(activeState(cleanupRequired = true)))
    }
}
''')
# Extend the structural class by full rewrite to avoid fragile nested insertion.
arch = UTEST / "ReviewFixArchitectureTest.kt"
text = arch.read_text()
insert = r'''
    @Test
    fun activeGameOperationsGuardBeforeGenerationAdvance() {
        val text = source("ChessViewModel.kt")
        for (signature in listOf("fun restartGame()", "fun resign()", "private fun submitMove(move: String)")) {
            val start = text.indexOf(signature)
            assertTrue(start >= 0)
            val end = text.indexOf("nextOperation()", start)
            val guard = text.indexOf("canRunActiveGameOperation(configuration)", start)
            assertTrue("$signature must guard before nextOperation", guard >= 0 && end >= 0 && guard < end)
        }
    }
'''
arch.write_text(text.rstrip()[:-1] + insert + "}\n")
mark_section("AR-007")
commit("AR-007", "fix(android): guard active-game operations while busy", [TODO, vm, UTEST / "ActiveGameOperationGuardTest.kt", arch], [unit(), compile_tests()])

print("STAGE1_RESUME_COMPLETE", subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
