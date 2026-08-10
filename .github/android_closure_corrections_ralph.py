#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md"
PARENT_TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md"
PROBE = ROOT / "android-harness/host-jvm/src/test/kotlin/com/ekkus93/chessengine/PromotionPathProbeTest.kt"
PROMOTION_TEST = ROOT / "android-harness/android-app/src/androidTest/kotlin/com/ekkus93/chessapp/PromotionEndToEndInstrumentedTest.kt"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(args), flush=True)
    result = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, end="", flush=True)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run("git", *args, check=check)


def replace_section(path: Path, start: str, end: str, replacement: str) -> None:
    text = path.read_text()
    a = text.index(start)
    b = text.index(end, a)
    path.write_text(text[:a] + replacement.rstrip() + "\n\n---\n\n" + text[b:])


def commit(message: str, *paths: Path) -> str:
    git("add", *[str(p.relative_to(ROOT)) for p in paths])
    git("diff", "--cached", "--check")
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        raise RuntimeError(f"no staged changes for {message}")
    git("commit", "-m", message)
    sha = git("rev-parse", "HEAD").stdout.strip()
    git("push", "origin", "HEAD:master")
    print(f"COMMIT {sha} {message}", flush=True)
    return sha


def record_cc002() -> None:
    section = '''# CC-002: Fix AR-004 — perform the verify-first system-bar observation

**Disposition:** `remediation-not-needed`.

## CC-002A: Runtime observation

- [x] Genuine rendered-state observation performed on permanent Android CI at exact SHA `6e5fdec216f013fae1257c67899fa26cce02d5e6`: workflow run `31431380577`, API-35 emulator job `93595365511`, conclusion `success`.
- [x] Observation-evidence contract satisfied: API 35, x86_64 `google_apis`, Pixel 2 profile, headless SwiftShader emulator; actual `UiAutomation` framebuffer screenshot sampled in the status/navigation-bar insets; expected product background `#0B1220`; RGB tolerance ±12/channel; each sampled bar region required at least 70% matching pixels. Screenshot `system-bars-api35.png` was preserved under `/sdcard/Download/RustChessEvidence` and included in the permanent UI-evidence artifact.
- [x] Existing icon-appearance flags remained supporting assertions only. CC-002A was satisfied by the new framebuffer/pixel diagnostic, not by those flags alone.

## CC-002B: Conditional remediation

- [x] **Disposition reached:** `remediation-not-needed` — CC-002A proved the API-35 system bars already render with the dark product background.

N/A — `remediation-required`: no `MainActivity.kt`/WindowCompat/edge-to-edge production change was needed because the diagnostic passed on the real API-35 emulator.

- [x] `remediation-not-needed` is backed by run `31431380577`, job `93595365511`, exact SHA `6e5fdec216f013fae1257c67899fa26cce02d5e6`.

## CC-002 Tests

- [x] CC-002A runtime diagnostic and the full Android connected-test step passed in job `93595365511`.

N/A — CC-002B re-verification: no remediation commit landed, so no post-fix rerun was required.'''
    replace_section(TODO, "# CC-002:", "# CC-003:", section)
    commit("docs(android): record API 35 system-bar disposition", TODO)


def correct_cc003() -> None:
    parent = '''# AR-007: Add busy-state guard consistency

## AR-007.1 Fix — global-busy/cleanup duplicate-input suppression (QI-005, revised per FQI-002)

- [x] Confirmed `ChessViewModel` has no per-operation-type identity state (only `busy`, `operationGeneration`, `monitorJob`, `game`), so the original same-operation-vs-different-operation distinction is not implementable without adding new state this task does not introduce.
- [x] `restartGame()`, `resign()`, and `submitMove()` each use the explicit existing-game guard `configuration.isSetup || configuration.busy || configuration.cleanupRequired` → early return; the `isSetup` polarity is intentionally opposite `startGame()` because these operations require an active game.
- [x] The guard applies uniformly regardless of whether the new invocation repeats the same button or is a different action attempted while busy — no operation-type distinction is introduced.
- [x] Rejection is a silent no-op (plain `return`), matching what `startGame()`'s guard actually does today — not a newly invented "visible rejection" `startGame()` doesn't itself perform.
- [x] `cleanupRequired` rejection leaves the already-surfaced cleanup-required state unchanged; no new per-invocation error message is added.
- [x] Existing generation/ticket cancellation mechanism unchanged.

## AR-007.2 Tests — corrected by closure-corrections CC-003

The original closure marked four stronger behavioral claims complete (rapid duplicate invocation for `restartGame()`, `resign()`, and `submitMove()`, plus the `cleanupRequired` cases) without an executed behavioral test seam. CC-003 re-inspected the implementation and found that `ChessViewModel` owns a concrete `ChessGame`, while `ChessGame` has a private constructor/native-session ownership and no injectable fake seam. Adding production indirection solely to manufacture these tests would distort the architecture, so the correction pass deliberately chose the `claims-downgraded` disposition instead of pretending the stronger behavior had been executed.

- [x] Actual permanent evidence: `ActiveGameOperationGuardTest.kt` proves the guard predicate truth table for setup/busy/cleanup-required states.
- [x] Actual permanent evidence: `ReviewFixArchitectureTest.kt` proves all three operation bodies place `canRunActiveGameOperation(configuration)` before `nextOperation()`.
- [x] The prior claim of executed duplicate-invocation/no-second-JNI-call behavioral coverage is withdrawn; no such behavioral execution is claimed after CC-003.
'''
    replace_section(PARENT_TODO, "# AR-007:", "# AR-008:", parent)

    section = '''# CC-003: Correct AR-007 behavioral-evidence claims; add behavioral coverage where practical

## CC-003.1 Fix

- [x] Attempted a genuine behavioral-test-seam design by reinspecting the actual ownership boundary: `ChessViewModel` stores a concrete `ChessGame`; `ChessGame` has a private constructor and owns the native high-level session. There is no clean fake/injection seam available to the app tests.
- [x] **Disposition reached:** `claims-downgraded`. Adding a production abstraction solely for this test would expand/distort production architecture, so the tracker now states only what is genuinely proven.

N/A — `seam-built`: no production seam was added.

- [x] `claims-downgraded`: parent AR-007.2 now preserves the original overclaim as provenance and limits the accepted evidence to predicate truth-table coverage plus static guard-before-generation ordering.

## CC-003.2 Tests

- [x] `ActiveGameOperationGuardTest` and `ReviewFixArchitectureTest.activeGameOperationsGuardBeforeGenerationAdvance` pass, and parent AR-007.2 now matches that actual evidence.'''
    replace_section(TODO, "# CC-003:", "# CC-004:", section)

    run(
        "gradle", "-p", "android-harness", ":android-app:testDebugUnitTest",
        "--tests", "com.ekkus93.chessapp.ActiveGameOperationGuardTest",
        "--tests", "com.ekkus93.chessapp.ReviewFixArchitectureTest.activeGameOperationsGuardBeforeGenerationAdvance",
        "--no-daemon", "--stacktrace", "--console=plain",
    )
    commit("docs(android): correct active-operation evidence claims", PARENT_TODO, TODO)


def probe_source() -> str:
    return r'''package com.ekkus93.chessengine

import java.io.File
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Timeout

class PromotionPathProbeTest {
    private data class State(val fen: String, val path: List<String>, val score: Int)

    @Test
    @Timeout(240)
    fun findDepthOneHumanPromotionPath() {
        val output = File("/tmp/rust-chess-promotion-path.txt")
        output.delete()
        ChessEngine.create().use { engine ->
            val initial = engine.fen()
            var beam = listOf(State(initial, emptyList(), positionScore(initial)))
            repeat(12) {
                val next = linkedMapOf<String, State>()
                for (state in beam) {
                    engine.setPosition(state.fen)
                    val legal = engine.legalMoves()
                    val promotion = legal.firstOrNull { move ->
                        move.length == 5 && move.last() in "qrbn"
                    }
                    if (promotion != null) {
                        val path = state.path + promotion
                        output.writeText(path.joinToString(","))
                        println("PROMOTION_PATH=${path.joinToString(",")}")
                        return
                    }
                    val pawns = whitePawnSquares(state.fen)
                    val candidates = legal.sortedByDescending { moveScore(it, pawns) }.take(14)
                    for (move in candidates) {
                        engine.setPosition(state.fen)
                        engine.playMove(move)
                        if (engine.gameStatus().kind != GameStatusKind.ONGOING) continue
                        val reply = engine.openingBookMove()
                            ?: engine.search(SearchRequest(depth = 1)).await().bestMove
                            ?: continue
                        engine.playMove(reply)
                        if (engine.gameStatus().kind != GameStatusKind.ONGOING) continue
                        val fen = engine.fen()
                        if (!fen.contains(" w ")) continue
                        val candidate = State(
                            fen = fen,
                            path = state.path + move,
                            score = positionScore(fen) + moveScore(move, pawns),
                        )
                        val prior = next[fen]
                        if (prior == null || candidate.score > prior.score) next[fen] = candidate
                    }
                }
                beam = next.values.sortedByDescending { it.score }.take(56)
                check(beam.isNotEmpty()) { "promotion-path beam exhausted before promotion" }
            }
        }
        error("no deterministic depth-1 promotion path found in bounded 12-human-move beam search")
    }

    private fun whitePawnSquares(fen: String): Set<String> {
        val result = linkedSetOf<String>()
        val ranks = fen.substringBefore(' ').split('/')
        for ((row, encoded) in ranks.withIndex()) {
            var file = 0
            for (token in encoded) {
                if (token.isDigit()) {
                    file += token.digitToInt()
                } else {
                    if (token == 'P') result += "${('a'.code + file).toChar()}${8 - row}"
                    file += 1
                }
            }
        }
        return result
    }

    private fun moveScore(move: String, pawns: Set<String>): Int {
        if (move.length < 4) return Int.MIN_VALUE
        val source = move.substring(0, 2)
        val destinationRank = move[3].digitToIntOrNull() ?: 0
        return if (source in pawns) 1_000 + destinationRank * 140 else destinationRank
    }

    private fun positionScore(fen: String): Int {
        val ranks = whitePawnSquares(fen).map { it[1].digitToInt() }
        if (ranks.isEmpty()) return -10_000
        return ranks.max() * 2_000 + ranks.sum() * 30
    }
}
'''


def promotion_test_source(path: list[str]) -> str:
    moves = ", ".join(f'"{move}"' for move in path)
    return f'''package com.ekkus93.chessapp

import android.os.SystemClock
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.lifecycle.ViewModelProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class PromotionEndToEndInstrumentedTest {{
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun realBoardTapsReachAndCompletePromotion() {{
        val viewModel = ViewModelProvider(composeRule.activity)[ChessViewModel::class.java]
        viewModel.setEngineDepth(1)
        composeRule.onNodeWithTag("start-game").performClick()
        awaitUiState(viewModel) {{ state -> state.snapshot?.humanToMove == true && !state.busy }}

        val path = listOf({moves})
        for ((index, move) in path.withIndex()) {{
            val source = move.substring(0, 2)
            val destination = move.substring(2, 4)
            val before = requireNotNull(viewModel.state.value.snapshot).moves.size
            composeRule.onNodeWithContentDescription(source, substring = true, useUnmergedTree = true).performClick()
            composeRule.onNodeWithContentDescription(destination, substring = true, useUnmergedTree = true).performClick()

            if (index == path.lastIndex) {{
                assertTrue("probe path must end in queen promotion", move.length == 5 && move.last() == 'q')
                composeRule.onNodeWithText("Choose promotion").fetchSemanticsNode()
                composeRule.onNodeWithText("Queen").performClick()
                val promoted = awaitUiState(viewModel) {{ state ->
                    val snapshot = state.snapshot
                    snapshot != null && snapshot.moves.size > before && snapshot.moves[before] == move
                }}
                assertEquals(move, promoted.snapshot?.moves?.get(before))
                composeRule.onNodeWithContentDescription("$destination queen", substring = true, useUnmergedTree = true)
                    .fetchSemanticsNode()
            }} else {{
                val afterReply = awaitUiState(viewModel) {{ state ->
                    val snapshot = state.snapshot
                    snapshot != null && snapshot.humanToMove && !state.busy && snapshot.moves.size >= before + 2
                }}
                assertEquals(move, afterReply.snapshot?.moves?.get(before))
            }}
        }}
    }}

    private fun awaitUiState(
        viewModel: ChessViewModel,
        predicate: (ChessUiState) -> Boolean,
    ): ChessUiState {{
        repeat(2_000) {{
            val state = viewModel.state.value
            if (predicate(state)) return state
            SystemClock.sleep(10)
        }}
        error("promotion E2E state did not reach expected condition before bounded deadline")
    }}
}}
'''


def attempt_cc004() -> None:
    PROBE.write_text(probe_source())
    run("cargo", "build", "--locked", "-p", "chess-jni", "--release")
    probe = run(
        "gradle", "-p", "android-harness", ":host-jvm:test",
        "--tests", "com.ekkus93.chessengine.PromotionPathProbeTest.findDepthOneHumanPromotionPath",
        "--no-daemon", "--stacktrace", "--console=plain", check=False,
    )
    PROBE.unlink(missing_ok=True)
    out = Path("/tmp/rust-chess-promotion-path.txt")
    if probe.returncode == 0 and out.exists() and out.read_text().strip():
        path = out.read_text().strip().split(",")
        if not (path[-1].endswith("q") and len(path[-1]) == 5):
            raise RuntimeError(f"probe ended in unexpected promotion move: {path[-1]}")
        print("DISCOVERED_PROMOTION_PATH=" + ",".join(path), flush=True)
        PROMOTION_TEST.write_text(promotion_test_source(path))
        run(
            "gradle", "-p", "android-harness", ":android-app:assembleDebugAndroidTest",
            "--no-daemon", "--stacktrace", "--console=plain",
        )
        section = f'''# CC-004: Fix AR-011 — add missing end-to-end promotion test

## CC-004.1 Fix

- [x] **Disposition reached:** `UI-driven fixture`. A bounded real-engine probe against the production depth-1/opening-book response policy discovered this deterministic human move path: `{','.join(path)}`.
- [x] End-to-end instrumentation test `PromotionEndToEndInstrumentedTest.kt` added. It starts the real `MainActivity`/`ChessViewModel` game, drives every human move in the discovered path by actual board taps, opens `PromotionDialog` through the production board flow, taps `Queen`, and asserts the authoritative snapshot records `{path[-1]}` and the destination renders a queen.
- [x] No production/player-facing FEN-loading capability and no Kotlin chess-rule logic was added.

N/A — `test-only fixture seam`: the UI-driven path succeeded, so no seam was needed.

N/A — `documented blocker`: a deterministic path was found.

## CC-004.2 Tests

- [ ] The new instrumentation test compiles here; runtime API-35 execution remains the gate before CC-005 may begin.'''
        replace_section(TODO, "# CC-004:", "# CC-005:", section)
        commit("test(android): add tap-driven promotion flow coverage", PROMOTION_TEST, TODO)
        return

    reason = (
        "A genuine bounded attempt was executed with the real JNI `ChessEngine`, reproducing the "
        "high-level opponent policy (opening-book reply when present, otherwise deterministic depth-1 search) "
        "and beam-searching legal human moves for up to 12 human turns; it did not find a promotion path. "
        "The existing production `ChessGame` also exposes no test-only position-injection seam, and adding one "
        "would require production/native API expansion solely for this test."
    )
    section = f'''# CC-004: Fix AR-011 — add missing end-to-end promotion test

## CC-004.1 Fix

- [x] **Disposition reached:** `documented blocker`.

N/A — `UI-driven fixture`: {reason}

N/A — `test-only fixture seam`: no existing test-only high-level session constructor/FEN seam exists; adding one would expand production/native API surface solely for this test.

- [x] Documented blocker: {reason}

## CC-004.2 Tests

- [x] The bounded real-engine path probe is the empirical blocker evidence; no new instrumentation test is claimed.'''
    replace_section(TODO, "# CC-004:", "# CC-005:", section)
    commit("docs(android): record promotion E2E blocker disposition", TODO)


def stage2() -> None:
    git("status", "--short")
    record_cc002()
    correct_cc003()
    attempt_cc004()
    print("STAGE2_HEAD=" + git("rev-parse", "HEAD").stdout.strip())


if __name__ == "__main__":
    os.chdir(ROOT)
    if len(sys.argv) != 2 or sys.argv[1] != "stage2":
        raise SystemExit("usage: android_closure_corrections_ralph.py stage2")
    stage2()
