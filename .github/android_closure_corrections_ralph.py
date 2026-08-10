#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md"
SPEC = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_SPEC_2026-08-10.md"
VM = ROOT / "android-harness/android-app/src/main/kotlin/com/ekkus93/chessapp/ChessViewModel.kt"
ARCH_TEST = ROOT / "android-harness/android-app/src/test/kotlin/com/ekkus93/chessapp/ReviewFixArchitectureTest.kt"
SYSTEM_BAR_TEST = ROOT / "android-harness/android-app/src/androidTest/kotlin/com/ekkus93/chessapp/SystemBarAppearanceInstrumentedTest.kt"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(args), flush=True)
    result = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, end="", flush=True)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run("git", *args, check=check)


def replace_exact(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    if old not in text:
        raise RuntimeError(f"expected text not found in {path}: {old[:120]!r}")
    if text.count(old) != 1:
        raise RuntimeError(f"expected exactly one match in {path}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1))


def mark_section(path: Path, start: str, end: str) -> None:
    text = path.read_text()
    a = text.index(start)
    b = text.index(end, a)
    section = text[a:b]
    section = section.replace("- [ ]", "- [x]")
    path.write_text(text[:a] + section + text[b:])


def commit(message: str, *paths: Path) -> str:
    git("add", *[str(p.relative_to(ROOT)) for p in paths])
    diff = git("diff", "--cached", "--check")
    if not git("diff", "--cached", "--quiet", check=False).returncode:
        raise RuntimeError(f"no staged changes for commit {message}")
    git("commit", "-m", message)
    sha = git("rev-parse", "HEAD").stdout.strip()
    git("push", "origin", "HEAD:master")
    print(f"COMMIT {sha} {message}", flush=True)
    return sha


def finalize_instructions() -> None:
    replace_exact(
        SPEC,
        "3. CC-001 through CC-008 land normally, one task per commit (except CC-002, which is explicitly two commits, CC-002A and CC-002B — see §4).",
        "3. CC-001 through CC-008 land normally, one task per commit, except that CC-002A always lands as its own commit and CC-002B lands as a second commit only if CC-002A proves remediation is required — see §4.",
    )
    replace_exact(
        SPEC,
        "If the existing icon-appearance-only test is judged sufficient after this genuine investigation, record that reasoning and the evidence for it explicitly — do not silently leave the task without a positive finding either way.",
        "The existing icon-appearance-only assertions may remain as supporting evidence, but they cannot by themselves satisfy CC-002A. The runtime evidence added in this pass must directly distinguish actual dark product-background rendering from the stock-light-background regression the task is meant to detect.",
    )
    replace_exact(
        TODO,
        "- [ ] If the existing icon-appearance-only check is judged sufficient after this investigation, that reasoning and its evidence recorded explicitly here.",
        "- [ ] Existing icon-appearance-only checks retained only as supporting evidence; CC-002A is not satisfied by those flags alone.",
    )
    commit("docs(android): finalize closure-correction instructions", SPEC, TODO)


def confirm_cc000() -> str:
    # The tracker was already registered by the pre-implementation review updates.
    run("bash", "scripts/task_post_port_review_fix_audit.sh")
    text = TODO.read_text()
    start = text.index("# CC-000: Baseline confirmation")
    end = text.index("# CC-001:", start)
    section = text[start:end]
    # The implementation-start SHA is unknowable until this commit exists; leave only that line pending.
    section = section.replace("- [ ]", "- [x]")
    section = re.sub(
        r"- \[x\] Implementation-start SHA \(captured immediately after CC-000 lands\): `_____________________________`",
        "- [ ] Implementation-start SHA (captured immediately after CC-000 lands): `_____________________________`",
        section,
    )
    TODO.write_text(text[:start] + section + text[end:])
    return commit("docs(android): confirm closure-correction baseline", TODO)


def architecture_test_source() -> str:
    return r'''package com.ekkus93.chessapp

import java.io.File
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ReviewFixArchitectureTest {
    private fun source(name: String): String =
        File(System.getProperty("user.dir"), "src/main/kotlin/com/ekkus93/chessapp/$name").readText()

    private fun productionSources(): Sequence<File> =
        File(System.getProperty("user.dir"), "src/main/kotlin")
            .walkTopDown()
            .filter { it.isFile && it.extension == "kt" }

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
    fun productionPlayerCopyDoesNotExposeArchitectureJargon() {
        val exactInternalOnlySnippets = listOf(
            // check() invariant text is never copied into ChessUiState.errorMessage or another UI sink.
            "check(game === created) { \"native game ownership changed during failed startup cleanup\" }",
            // check() invariant text is never copied into ChessUiState.errorMessage or another UI sink.
            "check(game === current) { \"native game ownership changed during close\" }",
            // Log.e() writes only to logcat during ViewModel leak cleanup; it is not rendered to the player.
            "Log.e(LOG_TAG, \"failed to close native chess game during ViewModel cleanup\", error)",
        )
        val stringLiteral = Regex("\\\"(?:\\\\.|[^\\\"])*\\\"")
        val forbidden = listOf("native", "JNI", "shared layer", "architecture")
        var internalAllowlistMatches = 0

        for (file in productionSources()) {
            var text = file.readText()
            if (file.name == "ChessViewModel.kt") {
                for (snippet in exactInternalOnlySnippets) {
                    val count = text.windowed(snippet.length, 1).count { it == snippet }
                    assertTrue("internal-only allowlist snippet must exist exactly once: $snippet", count == 1)
                    internalAllowlistMatches += count
                    text = text.replace(snippet, "")
                }
            }
            for (literal in stringLiteral.findAll(text).map { it.value }) {
                assertFalse(
                    "${file.name} production string literal exposes architecture jargon: $literal",
                    forbidden.any { term -> literal.contains(term, ignoreCase = true) },
                )
            }
        }
        assertTrue("all three internal-only sinks must be accounted for", internalAllowlistMatches == 3)
    }

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
}
'''


def implement_cc001(cc000_sha: str) -> None:
    replace_exact(
        TODO,
        "- [ ] Implementation-start SHA (captured immediately after CC-000 lands): `_____________________________`",
        f"- [x] Implementation-start SHA (captured immediately after CC-000 lands): `{cc000_sha}`",
    )
    replace_exact(
        VM,
        'errorMessage = "A native game is still active. Retry cleanup before starting another game.",',
        'errorMessage = "A previous game is still active. Retry cleanup before starting another game.",',
    )
    replace_exact(VM, 'append("Initial native snapshot failed: ")', 'append("Initial game snapshot failed: ")')
    ARCH_TEST.write_text(architecture_test_source())

    run("gradle", "-p", "android-harness", ":android-app:testDebugUnitTest", "--no-daemon", "--stacktrace", "--console=plain")

    # Negative sanity check: the structural test must fail if player-visible jargon is reintroduced.
    clean = VM.read_text()
    VM.write_text(clean.replace("A previous game is still active.", "A native game is still active.", 1))
    negative = run(
        "gradle", "-p", "android-harness", ":android-app:testDebugUnitTest",
        "--tests", "com.ekkus93.chessapp.ReviewFixArchitectureTest.productionPlayerCopyDoesNotExposeArchitectureJargon",
        "--no-daemon", "--stacktrace", "--console=plain", check=False,
    )
    VM.write_text(clean)
    if negative.returncode == 0:
        raise RuntimeError("CC-001 negative sanity check unexpectedly passed")
    run(
        "gradle", "-p", "android-harness", ":android-app:testDebugUnitTest",
        "--tests", "com.ekkus93.chessapp.ReviewFixArchitectureTest.productionPlayerCopyDoesNotExposeArchitectureJargon",
        "--no-daemon", "--stacktrace", "--console=plain",
    )

    mark_section(TODO, "# CC-001:", "# CC-002:")
    commit("fix(android): remove remaining player architecture jargon", VM, ARCH_TEST, TODO)


def system_bar_test_source() -> str:
    return r'''package com.ekkus93.chessapp

import android.graphics.Bitmap
import android.os.Build
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.core.graphics.blue
import androidx.core.graphics.green
import androidx.core.graphics.red
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.io.FileOutputStream
import kotlin.math.abs
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class SystemBarAppearanceInstrumentedTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun api35SystemBarsRenderDarkProductBackground() {
        assertEquals("permanent Android CI observation must run on API 35", 35, Build.VERSION.SDK_INT)
        composeRule.waitForIdle()

        val activity = composeRule.activity
        val window = activity.window
        val controller = WindowCompat.getInsetsController(window, window.decorView)
        assertFalse(controller.isAppearanceLightStatusBars)
        assertFalse(controller.isAppearanceLightNavigationBars)

        val insets = requireNotNull(ViewCompat.getRootWindowInsets(window.decorView))
        val statusHeight = insets.getInsets(WindowInsetsCompat.Type.statusBars()).top
        val navigationHeight = insets.getInsets(WindowInsetsCompat.Type.navigationBars()).bottom
        assertTrue("status bar inset must be visible", statusHeight > 0)
        assertTrue("navigation bar inset must be visible", navigationHeight > 0)

        val screenshot = requireNotNull(InstrumentationRegistry.getInstrumentation().uiAutomation.takeScreenshot())
        preserveScreenshot(screenshot)
        val expected = AppBackground.toArgb()
        val statusRatio = matchingRatio(
            screenshot,
            left = screenshot.width / 4,
            top = 0,
            right = screenshot.width * 3 / 4,
            bottom = statusHeight,
            expected = expected,
        )
        val navigationRatio = matchingRatio(
            screenshot,
            left = screenshot.width / 10,
            top = screenshot.height - navigationHeight,
            right = screenshot.width * 4 / 10,
            bottom = screenshot.height,
            expected = expected,
        )
        assertTrue("status bar product-background pixel ratio $statusRatio < 0.70", statusRatio >= 0.70)
        assertTrue("navigation bar product-background pixel ratio $navigationRatio < 0.70", navigationRatio >= 0.70)
    }

    private fun matchingRatio(
        bitmap: Bitmap,
        left: Int,
        top: Int,
        right: Int,
        bottom: Int,
        expected: Int,
    ): Double {
        var matches = 0L
        var total = 0L
        for (y in top.coerceAtLeast(0) until bottom.coerceAtMost(bitmap.height)) {
            for (x in left.coerceAtLeast(0) until right.coerceAtMost(bitmap.width)) {
                val actual = bitmap.getPixel(x, y)
                if (
                    abs(actual.red - expected.red) <= 12 &&
                    abs(actual.green - expected.green) <= 12 &&
                    abs(actual.blue - expected.blue) <= 12
                ) {
                    matches += 1
                }
                total += 1
            }
        }
        require(total > 0) { "system-bar pixel sample must not be empty" }
        return matches.toDouble() / total.toDouble()
    }

    private fun preserveScreenshot(bitmap: Bitmap) {
        val directory = File("/sdcard/Download/RustChessEvidence").apply { mkdirs() }
        FileOutputStream(File(directory, "system-bars-api35.png")).use { output ->
            check(bitmap.compress(Bitmap.CompressFormat.PNG, 100, output))
        }
    }
}
'''


def implement_cc002a() -> None:
    SYSTEM_BAR_TEST.write_text(system_bar_test_source())
    run("gradle", "-p", "android-harness", ":android-app:assembleDebugAndroidTest", "--no-daemon", "--stacktrace", "--console=plain")
    commit("test(android): diagnose API 35 system bar rendering", SYSTEM_BAR_TEST)


def stage1() -> None:
    git("status", "--short")
    finalize_instructions()
    cc000_sha = confirm_cc000()
    implement_cc001(cc000_sha)
    implement_cc002a()
    print("STAGE1_HEAD=" + git("rev-parse", "HEAD").stdout.strip())


if __name__ == "__main__":
    os.chdir(ROOT)
    if len(sys.argv) != 2 or sys.argv[1] != "stage1":
        raise SystemExit("usage: android_closure_corrections_ralph.py stage1")
    stage1()
