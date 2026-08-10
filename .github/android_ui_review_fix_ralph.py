#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md"
APP = ROOT / "android-harness/android-app"
ATEST = APP / "src/androidTest/kotlin/com/ekkus93/chessapp"
UTEST = APP / "src/test/kotlin"
SAN = ROOT / "crates/chess-core/src/san.rs"
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

# AR-017 SAN coverage: piece capture, disambiguated capture, capture-promotion with check.
insert = r'''

    #[test]
    fn formats_piece_capture() {
        let position = parse_fen("4k3/8/8/4p3/8/5N2/8/4K3 w - - 0 1").expect("valid FEN");
        let mv = parse_uci_move("f3e5").expect("valid move");
        assert_eq!(format_san(&position, mv).expect("SAN"), "Nxe5");
    }

    #[test]
    fn formats_disambiguated_piece_capture() {
        let position = parse_fen("4k3/8/8/8/4p3/2N5/5N2/4K3 w - - 0 1").expect("valid FEN");
        let mv = parse_uci_move("c3e4").expect("valid move");
        assert_eq!(format_san(&position, mv).expect("SAN"), "Ncxe4");
    }

    #[test]
    fn formats_capture_promotion_with_check() {
        let position = parse_fen("k2r4/4P3/8/8/8/8/8/4K3 w - - 0 1").expect("valid FEN");
        let mv = parse_uci_move("e7d8q").expect("valid move");
        assert_eq!(format_san(&position, mv).expect("SAN"), "exd8=Q+");
    }
'''
text = SAN.read_text()
SAN.write_text(text.rstrip()[:-1] + insert + "}\n")
mark("AR-017")
commit("AR-017", "test(core): cover SAN capture edge cases", [TODO, SAN], ["cargo fmt --all -- --check", "cargo test --locked -p chess-core san -- --nocapture"])

# AR-018 fail-closed Kotlin snapshot parser coverage.
parser_dir = UTEST / "com/ekkus93/chessengine"
parser_dir.mkdir(parents=True, exist_ok=True)
parser_test = parser_dir / "ChessGameSnapshotParseTest.kt"
parser_test.write_text(r'''package com.ekkus93.chessengine

import org.junit.Assert.assertThrows
import org.junit.Test

class ChessGameSnapshotParseTest {
    private val validFields = listOf(
        "2",
        "8/8/8/8/8/8/4K3/7k w - - 0 1",
        "",
        "",
        "",
        "white",
        "white",
        "0",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "END",
    )

    private fun encoded(fields: List<String>): String = fields.joinToString("\u001f")

    @Test
    fun rejectsWrongFieldCount() {
        assertThrows(IllegalArgumentException::class.java) {
            ChessGameSnapshot.parse(encoded(validFields.dropLast(1)))
        }
    }

    @Test
    fun rejectsWrongVersion() {
        assertThrows(IllegalArgumentException::class.java) {
            ChessGameSnapshot.parse(encoded(validFields.toMutableList().apply { this[0] = "999" }))
        }
    }

    @Test
    fun rejectsCorruptedTerminator() {
        assertThrows(IllegalArgumentException::class.java) {
            ChessGameSnapshot.parse(encoded(validFields.toMutableList().apply { this[lastIndex] = "BROKEN" }))
        }
    }
}
''')
mark("AR-018")
commit("AR-018", "test(android): cover snapshot parser rejection paths", [TODO, parser_test], ["gradle -p android-harness :android-app:testDebugUnitTest --no-daemon --stacktrace --console=plain"])

# AR-019 static high-level Rust/Kotlin contract parity.
replace(
    JNI_CONTRACT,
    'const KOTLIN_BINDINGS: &str = include_str!("../kotlin/src/main/kotlin/com/ekkus93/chessengine/NativeChessEngineBindings.kt");\n',
    'const KOTLIN_BINDINGS: &str = include_str!("../kotlin/src/main/kotlin/com/ekkus93/chessengine/NativeChessEngineBindings.kt");\nconst APP_BRIDGE: &str = include_str!("../src/app_bridge.rs");\nconst KOTLIN_GAME: &str = include_str!("../kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessGame.kt");\n',
)
extra = r'''

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
    let field_count = fields.lines().filter(|line| line.trim_end().ends_with(',')).count();
    assert_eq!(field_count, 18, "Rust high-level snapshot field count changed");
}
'''
JNI_CONTRACT.write_text(JNI_CONTRACT.read_text().rstrip() + extra + "\n")
mark("AR-019")
commit("AR-019", "test(jni): pin high-level snapshot protocol parity", [TODO, JNI_CONTRACT], ["cargo fmt --all -- --check", "cargo test --locked -p chess-jni --test jni_contract", "cargo test --locked -p chess-jni"])

# AR-020 real API-35 rotation request with non-initial game state preserved.
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
                runCatching { composeRule.onNodeWithContentDescription("e4 pawn").fetchSemanticsNode() }.isSuccess
            }

            device.setOrientationLeft()
            device.waitForIdle()
            composeRule.waitForIdle()

            assertEquals(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT, composeRule.activity.requestedOrientation)
            assertEquals(Configuration.ORIENTATION_PORTRAIT, composeRule.activity.resources.configuration.orientation)
            composeRule.onNodeWithTag("chess-board").assertExists()
            composeRule.onNodeWithContentDescription("e4 pawn").assertExists()
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
    raise RuntimeError("AR-020 runtime rotation-attempt coverage failed in the supported API-35 emulator; refusing to mark blocked/manual without a separate environmental diagnosis")
mark("AR-020")
commit("AR-020", "test(android): verify portrait rotation preserves game state", [TODO, BUILD, rotation_test], [compile_tests(), connected("com.ekkus93.chessapp.PortraitRotationInstrumentedTest")])

print("STAGE3_COMPLETE", subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip())
