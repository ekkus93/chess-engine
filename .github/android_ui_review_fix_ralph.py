#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md"
APP = ROOT / "android-harness/android-app"
ATEST = APP / "src/androidTest/kotlin/com/ekkus93/chessapp"
JNI_CONTRACT = ROOT / "crates/chess-jni/tests/jni_contract.rs"
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


def compile_tests() -> str:
    return "gradle -p android-harness :android-app:assembleDebug :android-app:assembleDebugAndroidTest --no-daemon --stacktrace --console=plain"


run("git", "config", "user.name", "Ralph Loop")
run("git", "config", "user.email", "actions@users.noreply.github.com")

# AR-019: static high-level Rust/Kotlin snapshot contract parity.
replace(
    JNI_CONTRACT,
    'const RUST_EXPORTS: &str = include_str!("../src/lib.rs");\n',
    'const RUST_EXPORTS: &str = include_str!("../src/lib.rs");\n'
    'const APP_BRIDGE: &str = include_str!("../src/app_bridge.rs");\n'
    'const KOTLIN_GAME: &str =\n'
    '    include_str!("../kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessGame.kt");\n',
)
JNI_CONTRACT.write_text(JNI_CONTRACT.read_text().rstrip() + r'''

#[test]
fn high_level_snapshot_contract_matches_between_rust_and_kotlin() {
    assert!(KOTLIN_GAME.contains("private const val FIELD_COUNT = 18"));
    assert!(KOTLIN_GAME.contains("private const val VERSION = \"2\""));
    assert!(APP_BRIDGE.contains("const SNAPSHOT_VERSION: &str = \"2\";"));

    let fields = APP_BRIDGE
        .split("let fields = [")
        .nth(1)
        .expect("snapshot field array")
        .split("];")
        .next()
        .expect("snapshot field array end");
    let field_count = fields
        .lines()
        .filter(|line| line.trim_end().ends_with(','))
        .count();
    assert_eq!(field_count, 18, "Rust high-level snapshot field count changed");
}
''' + "\n")
sh("cargo fmt --all")
mark("AR-019")
commit(
    "AR-019",
    "test(jni): pin high-level snapshot protocol parity",
    [TODO, JNI_CONTRACT],
    ["cargo fmt --all -- --check", "cargo test --locked -p chess-jni --test jni_contract", "cargo test --locked -p chess-jni"],
)

# AR-020: real API-35 rotation request with a non-initial played position preserved.
replace(
    BUILD,
    '    androidTestImplementation("androidx.compose.ui:ui-test-junit4:1.7.8")\n',
    '    androidTestImplementation("androidx.compose.ui:ui-test-junit4:1.7.8")\n    androidTestImplementation("androidx.test.uiautomator:uiautomator:2.3.0")\n',
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
rotation = sh(connected("com.ekkus93.chessapp.PortraitRotationInstrumentedTest"), check=False)
if rotation.returncode != 0:
    raise RuntimeError(
        "AR-020 runtime rotation-attempt coverage failed in the supported API-35 emulator; "
        "refusing to mark it blocked/manual without a distinct environmental diagnosis"
    )
mark("AR-020")
commit(
    "AR-020",
    "test(android): verify portrait rotation preserves game state",
    [TODO, BUILD, rotation_test],
    [compile_tests(), connected("com.ekkus93.chessapp.PortraitRotationInstrumentedTest")],
)

print("STAGE3_FINAL_COMPLETE", subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip())
