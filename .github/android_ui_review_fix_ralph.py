#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md"
APP = ROOT / "android-harness/android-app"
ATEST = APP / "src/androidTest/kotlin/com/ekkus93/chessapp"
BUILD = APP / "build.gradle.kts"


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


def connected(cls: str) -> str:
    return "gradle -p android-harness :android-app:connectedDebugAndroidTest --no-daemon --stacktrace --console=plain -Pandroid.testInstrumentationRunnerArguments.class=" + cls


def compile_tests() -> str:
    return "gradle -p android-harness :android-app:assembleDebug :android-app:assembleDebugAndroidTest --no-daemon --stacktrace --console=plain"


run("git", "config", "user.name", "Ralph Loop")
run("git", "config", "user.email", "actions@users.noreply.github.com")

replace(
    BUILD,
    '    androidTestImplementation("androidx.compose.ui:ui-test-junit4")\n',
    '    androidTestImplementation("androidx.compose.ui:ui-test-junit4")\n    androidTestImplementation("androidx.test.uiautomator:uiautomator:2.3.0")\n',
)
rotation_test = ATEST / "PortraitRotationInstrumentedTest.kt"
rotation_test.write_text(r'''package com.ekkus93.chessapp

import android.content.pm.ActivityInfo
import android.content.res.Configuration
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.UiDevice
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class PortraitRotationInstrumentedTest {
    @get:Rule val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun rotationRequestKeepsPortraitAndPreservesPlayedMove() {
        val device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        try {
            composeRule.onNodeWithTag("start-game").performClick()
            composeRule.waitUntil(30_000) {
                runCatching { composeRule.onNodeWithContentDescription("e2 pawn").fetchSemanticsNode() }.isSuccess
            }
            composeRule.onNodeWithContentDescription("e2 pawn").performClick()
            composeRule.onNodeWithContentDescription("e4 legal target").performClick()
            composeRule.waitUntil(30_000) {
                runCatching {
                    composeRule.onNodeWithContentDescription("e4 pawn", substring = true).fetchSemanticsNode()
                }.isSuccess
            }

            device.setOrientationLeft()
            device.waitForIdle()
            composeRule.waitForIdle()

            assertEquals(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT, composeRule.activity.requestedOrientation)
            assertEquals(Configuration.ORIENTATION_PORTRAIT, composeRule.activity.resources.configuration.orientation)
            composeRule.onNodeWithTag("chess-board").assertExists()
            composeRule.onNodeWithContentDescription("e4 pawn", substring = true).assertExists()
        } finally {
            device.setOrientationNatural()
            device.waitForIdle()
        }
    }
}
''')
sh(compile_tests())
sh(connected("com.ekkus93.chessapp.PortraitRotationInstrumentedTest"))
mark("AR-020")
run("git", "diff", "--check")
sh(compile_tests())
sh(connected("com.ekkus93.chessapp.PortraitRotationInstrumentedTest"))
run("git", "add", str(TODO.relative_to(ROOT)), str(BUILD.relative_to(ROOT)), str(rotation_test.relative_to(ROOT)))
run("git", "commit", "-m", "test(android): verify portrait rotation preserves game state")
run("git", "push", "origin", "HEAD:master")
print("AR-020", subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), flush=True)
