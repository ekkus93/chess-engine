#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

TODO = Path("docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md")
SPEC = Path("docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SPEC_2026-08-10.md")
INDEX = Path("docs/LEGACY_TODO_INDEX.md")
AUDIT = Path("scripts/task_post_port_review_fix_audit.sh")
APP = Path("android-harness/android-app")
MAIN = APP / "src/main/kotlin/com/ekkus93/chessapp"
ATEST = APP / "src/androidTest/kotlin/com/ekkus93/chessapp"
UTEST = APP / "src/test/kotlin/com/ekkus93/chessapp"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(args), flush=True)
    return subprocess.run(args, cwd=ROOT, text=True, check=check)


def sh(command: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", command, flush=True)
    return subprocess.run(["bash", "-lc", command], cwd=ROOT, text=True, check=check)


def replace(path: Path, old: str, new: str, count: int = 1) -> None:
    text = path.read_text()
    actual = text.count(old)
    if actual < count:
        raise RuntimeError(f"{path}: expected at least {count} copies of replacement target, found {actual}: {old[:120]!r}")
    path.write_text(text.replace(old, new, count))


def regex_replace(path: Path, pattern: str, repl: str, count: int = 1, flags: int = 0) -> None:
    text = path.read_text()
    updated, actual = re.subn(pattern, repl, text, count=count, flags=flags)
    if actual != count:
        raise RuntimeError(f"{path}: expected {count} regex replacement(s), got {actual}: {pattern}")
    path.write_text(updated)


def append_before(path: Path, marker: str, insertion: str) -> None:
    replace(path, marker, insertion + marker)


def mark_section(task: str) -> None:
    text = TODO.read_text()
    start = text.index(f"# {task}:")
    next_header = text.find("\n# AR-", start + 1)
    end = len(text) if next_header == -1 else next_header
    section = text[start:end].replace("- [ ]", "- [x]")
    TODO.write_text(text[:start] + section + text[end:])


def commit(task: str, message: str, paths: list[Path], checks: list[str]) -> str:
    run("git", "diff", "--check")
    for command in checks:
        sh(command)
    run("git", "add", *[str(path) for path in paths])
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if staged.returncode == 0:
        raise RuntimeError(f"{task}: no staged changes")
    run("git", "commit", "-m", message)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    run("git", "push", "origin", "HEAD:master")
    print(f"{task} committed {sha}", flush=True)
    return sha


def connected(test_class: str) -> str:
    return (
        "gradle -p android-harness :android-app:connectedDebugAndroidTest --no-daemon --stacktrace --console=plain "
        f"-Pandroid.testInstrumentationRunnerArguments.class={test_class}"
    )


def unit() -> str:
    return "gradle -p android-harness :android-app:testDebugUnitTest --no-daemon --stacktrace --console=plain"


def compile_android_tests() -> str:
    return "gradle -p android-harness :android-app:assembleDebug :android-app:assembleDebugAndroidTest --no-daemon --stacktrace --console=plain"


run("git", "config", "user.name", "Ralph Loop")
run("git", "config", "user.email", "actions@users.noreply.github.com")
run("git", "status", "--short")

# ---------------------------------------------------------------------------
# AR-000 — baseline confirmation + implementation-time plan corrections.
# ---------------------------------------------------------------------------
replace(
    TODO,
    "**Status:** proposed / not started",
    "**Status:** In progress — AR-000 baseline confirmed; implementation underway",
)

# Make the permanent authority audit actually scope bounded-review-fix membership
# to the classification section instead of accepting a match in the historical list.
old_audit = '''for bounded_review_fix_tracker in \\
    'docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md' \\
    'docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md' \\
    'docs/RUST_TUI_REVIEW_FIX_TODO_2026-08-09.md' \\
    'docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md'; do
    grep -Fq "\\`$bounded_review_fix_tracker\\`" "$legacy_index" || {
        echo "bounded review-fix tracker not listed under its classification: $bounded_review_fix_tracker" >&2
        exit 1
    }
done
'''
new_audit = '''bounded_review_fix_section="$(awk '
    /^## Bounded review-fix trackers$/ { in_section = 1; next }
    /^## Exhaustive classification rule$/ { in_section = 0 }
    in_section { print }
' "$legacy_index")"
for bounded_review_fix_tracker in \\
    'docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md' \\
    'docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md' \\
    'docs/RUST_TUI_REVIEW_FIX_TODO_2026-08-09.md' \\
    'docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md'; do
    grep -Fq "\\`$bounded_review_fix_tracker\\`" <<<"$bounded_review_fix_section" || {
        echo "bounded review-fix tracker not listed under its classification: $bounded_review_fix_tracker" >&2
        exit 1
    }
done
'''
replace(AUDIT, old_audit, new_audit)

# Clarify the existing-game guard polarity discovered during implementation.
replace(
    SPEC,
    "Add to `restartGame()`, `resign()`, and `submitMove()` the exact same precondition guard `startGame()` already uses — `if (!configuration.isSetup || configuration.busy || configuration.cleanupRequired) { return }` adapted to each function's actual applicable preconditions — returning early without performing the operation, without any second engine/native/JNI/cleanup call, and without any state mutation, whenever `busy` or `cleanupRequired` is true.",
    "Add an explicit existing-game precondition to `restartGame()`, `resign()`, and `submitMove()`: `if (configuration.isSetup || configuration.busy || configuration.cleanupRequired) { return }`, followed by each function's existing operation-specific checks. The `isSetup` polarity is intentionally the opposite of `startGame()` because these three operations require an active game. Return early without performing the operation, without any second engine/native/JNI/cleanup call, and without any state mutation whenever setup is active, `busy` is true, or `cleanupRequired` is true.",
)
replace(
    TODO,
    "`restartGame()`, `resign()`, and `submitMove()` each add the same precondition guard `startGame()` already uses (`busy`/`cleanupRequired` → early return), adapted to each function's applicable preconditions.",
    "`restartGame()`, `resign()`, and `submitMove()` each use the explicit existing-game guard `configuration.isSetup || configuration.busy || configuration.cleanupRequired` → early return; the `isSetup` polarity is intentionally opposite `startGame()` because these operations require an active game.",
)

# Coordinate labels need two semantic colors: no single foreground can satisfy
# 4.5:1 against both current board backgrounds because the backgrounds themselves
# are only ~3.6:1 apart.
replace(
    SPEC,
    "Add a `CoordinateLabel` (or equivalently named) token to `Theme.kt` for the rank/file label color, replacing the raw `Color.Black.copy(alpha = ...)` literal in `ChessBoardView.kt`.",
    "Add semantic coordinate-label tokens for both board-square contexts (for example `CoordinateLabelOnLight` and `CoordinateLabelOnDark`) to `Theme.kt`, replacing the raw `Color.Black.copy(alpha = ...)` literal in `ChessBoardView.kt`. A single fixed token is not required because it cannot meet the AR-016 normal-text threshold against both current square colors.",
)
replace(
    TODO,
    "`CoordinateLabel` (or equivalently named) token added to `Theme.kt`; `ChessBoardView.kt`'s rank/file labels reference it instead of `Color.Black.copy(...)`.",
    "Semantic coordinate-label tokens for light and dark board squares added to `Theme.kt`; `ChessBoardView.kt`'s rank/file labels select the appropriate token instead of `Color.Black.copy(...)`.",
)
replace(
    SPEC,
    "- `CoordinateLabel` (from AR-002) on both `BoardLight` and `BoardDark`.",
    "- The coordinate-label token selected for `BoardLight` on `BoardLight`, and the token selected for `BoardDark` on `BoardDark`.",
)
replace(
    TODO,
    "Coordinate-label contrast covered on both `BoardLight` and `BoardDark`.",
    "Coordinate-label contrast covered with the actual light-square and dark-square label tokens on their respective square colors.",
)

# Legal-target markers are circles/rings, not full-square background overlays.
replace(
    SPEC,
    "For overlays: cover last-move highlight (`BoardLastMove`, per AR-002's rewiring), the selected-square treatment, and the legal-move-target marker, computed as the actual alpha-composited effective background color (overlay color/alpha blended onto the underlying square color) rather than the raw overlay token compared to the raw foreground token in isolation, applying the same composite-boundary model described above.",
    "For full-square treatments, cover the last-move highlight (`BoardLastMove`, per AR-002's rewiring) and selected-square treatment by computing the actual effective background after compositing/lerping. The legal-move target is different: `ChessBoardView.kt` renders a filled circle on an empty target and a ring on an occupied capture target, behind any piece. Test the effective target circle/ring color against every applicable effective square background at the 3:1 graphical-object threshold, and independently apply the composite piece-silhouette test to pieces on those backgrounds. Do not model the target marker as if it covered the entire square behind the piece.",
)
replace(
    TODO,
    "Last-move, selected-square, and legal-target overlay contrast covered using the actual alpha-composited effective background color and the same composite-boundary model, not the raw overlay token compared in isolation.",
    "Last-move and selected-square full-background contrast uses actual composited/lerped backgrounds; legal-target filled-circle/ring contrast is tested as a graphical marker against each applicable effective square background, separately from piece-silhouette contrast.",
)

# AR-000 is a documentation/audit baseline task. Leave only the self-referential
# implementation-start SHA item open; AR-001 records the AR-000 commit SHA as its parent.
text = TODO.read_text()
start = text.index("# AR-000:")
end = text.index("\n# AR-001:", start)
section = text[start:end]
section = section.replace("- [ ]", "- [x]")
section = section.replace(
    "- [x] Implementation-start SHA (exact `master` state immediately before AR-001 begins, captured after this spec/TODO pair and its pre-implementation corrections have landed): `_____________________________`",
    "- [ ] Implementation-start SHA (exact `master` state immediately before AR-001 begins, captured after this spec/TODO pair and its pre-implementation corrections have landed): `_____________________________`",
)
section = section.replace(
    "- [x] Confirmed these two values are not conflated anywhere in this document or the closure-evidence document.",
    "- [ ] Confirmed these two values are not conflated anywhere in this document or the closure-evidence document.",
)
TODO.write_text(text[:start] + section + text[end:])

ar000_sha = commit(
    "AR-000",
    "docs(android): begin UI review-fix implementation",
    [TODO, SPEC, AUDIT],
    ["bash scripts/task_post_port_review_fix_audit.sh"],
)

# ---------------------------------------------------------------------------
# AR-001 — newest-move highlight.
# ---------------------------------------------------------------------------
replace(
    MAIN / "Theme.kt",
    "internal val Danger = Color(0xFFF87171)\n",
    "internal val Danger = Color(0xFFF87171)\ninternal val MoveLatest = PrimaryStrong\n",
)
replace(
    MAIN / "GamePanels.kt",
    "import androidx.compose.ui.text.font.FontFamily\n",
    "import androidx.compose.ui.text.font.FontFamily\nimport androidx.compose.ui.text.font.FontWeight\n",
)
replace(
    MAIN / "GamePanels.kt",
    "            val row = rows[index]\n            Row(\n",
    "            val row = rows[index]\n            val isNewestRow = index == rows.lastIndex\n            val newestIsWhite = isNewestRow && sanMoves.size % 2 == 1\n            val newestIsBlack = isNewestRow && sanMoves.size % 2 == 0 && row.black != null\n            Row(\n",
)
replace(
    MAIN / "GamePanels.kt",
    '''                Text(\n                    text = row.white,\n                    modifier = Modifier.weight(1f),\n                    style = MaterialTheme.typography.bodyMedium,\n                    fontFamily = FontFamily.Monospace,\n                    color = OnBackground,\n''',
    '''                Text(\n                    text = row.white,\n                    modifier = Modifier\n                        .weight(1f)\n                        .then(if (newestIsWhite) Modifier.testTag("latest-move") else Modifier),\n                    style = MaterialTheme.typography.bodyMedium,\n                    fontFamily = FontFamily.Monospace,\n                    fontWeight = if (newestIsWhite) FontWeight.SemiBold else FontWeight.Normal,\n                    color = if (newestIsWhite) MoveLatest else OnBackground,\n''',
)
replace(
    MAIN / "GamePanels.kt",
    '''                Text(\n                    text = row.black.orEmpty(),\n                    modifier = Modifier.weight(1f),\n                    style = MaterialTheme.typography.bodyMedium,\n                    fontFamily = FontFamily.Monospace,\n                    color = if (row.black == null) OnSurfaceMuted else OnBackground,\n''',
    '''                Text(\n                    text = row.black.orEmpty(),\n                    modifier = Modifier\n                        .weight(1f)\n                        .then(if (newestIsBlack) Modifier.testTag("latest-move") else Modifier),\n                    style = MaterialTheme.typography.bodyMedium,\n                    fontFamily = FontFamily.Monospace,\n                    fontWeight = if (newestIsBlack) FontWeight.SemiBold else FontWeight.Normal,\n                    color = when {\n                        newestIsBlack -> MoveLatest\n                        row.black == null -> OnSurfaceMuted\n                        else -> OnBackground\n                    },\n''',
)

review_test = ATEST / "ReviewFixInstrumentedTest.kt"
review_test.write_text('''package com.ekkus93.chessapp\n\nimport androidx.compose.foundation.layout.Box\nimport androidx.compose.foundation.layout.requiredSize\nimport androidx.compose.foundation.lazy.LazyListState\nimport androidx.compose.runtime.mutableStateOf\nimport androidx.compose.ui.Modifier\nimport androidx.compose.ui.test.assertCountEquals\nimport androidx.compose.ui.test.assertTextEquals\nimport androidx.compose.ui.test.junit4.createComposeRule\nimport androidx.compose.ui.test.onAllNodesWithTag\nimport androidx.compose.ui.test.onNodeWithTag\nimport androidx.compose.ui.unit.dp\nimport androidx.test.ext.junit.runners.AndroidJUnit4\nimport org.junit.Rule\nimport org.junit.Test\nimport org.junit.runner.RunWith\n\n@RunWith(AndroidJUnit4::class)\nclass ReviewFixInstrumentedTest {\n    @get:Rule\n    val composeRule = createComposeRule()\n\n    @Test\n    fun newestMoveMarkerTargetsOnlyLatestPly() {\n        composeRule.setContent {\n            RustChessTheme {\n                Box(Modifier.requiredSize(360.dp, 160.dp)) {\n                    MoveHistoryPanel(listOf("e4", "c5", "Nf3"), LazyListState())\n                }\n            }\n        }\n        composeRule.onAllNodesWithTag("latest-move").assertCountEquals(1)\n        composeRule.onNodeWithTag("latest-move").assertTextEquals("Nf3")\n    }\n\n    @Test\n    fun appendingMoveTransfersNewestMarker() {\n        val moves = mutableStateOf(listOf("e4", "c5", "Nf3"))\n        composeRule.setContent {\n            RustChessTheme {\n                Box(Modifier.requiredSize(360.dp, 160.dp)) {\n                    MoveHistoryPanel(moves.value, LazyListState())\n                }\n            }\n        }\n        composeRule.onNodeWithTag("latest-move").assertTextEquals("Nf3")\n        composeRule.runOnUiThread { moves.value = moves.value + "Nc6" }\n        composeRule.waitForIdle()\n        composeRule.onAllNodesWithTag("latest-move").assertCountEquals(1)\n        composeRule.onNodeWithTag("latest-move").assertTextEquals("Nc6")\n    }\n\n    @Test\n    fun emptyHistoryHasNoNewestMarker() {\n        composeRule.setContent {\n            RustChessTheme {\n                Box(Modifier.requiredSize(360.dp, 160.dp)) {\n                    MoveHistoryPanel(emptyList(), LazyListState())\n                }\n            }\n        }\n        composeRule.onAllNodesWithTag("latest-move").assertCountEquals(0)\n    }\n}\n''')

# Record the exact AR-000 commit as implementation start in the first implementation commit.
replace(
    TODO,
    "- [ ] Implementation-start SHA (exact `master` state immediately before AR-001 begins, captured after this spec/TODO pair and its pre-implementation corrections have landed): `_____________________________`",
    f"- [x] Implementation-start SHA (exact `master` state immediately before AR-001 begins, captured after this spec/TODO pair and its pre-implementation corrections have landed): `{ar000_sha}`",
)
replace(
    TODO,
    "- [ ] Confirmed these two values are not conflated anywhere in this document or the closure-evidence document.",
    "- [x] Confirmed these two values are not conflated anywhere in this document or the closure-evidence document.",
)
mark_section("AR-001")
commit(
    "AR-001",
    "fix(android): distinguish newest move in history",
    [TODO, MAIN / "Theme.kt", MAIN / "GamePanels.kt", review_test],
    [compile_android_tests(), connected("com.ekkus93.chessapp.ReviewFixInstrumentedTest")],
)

# ---------------------------------------------------------------------------
# AR-002 — theme token centralization.
# ---------------------------------------------------------------------------
replace(
    MAIN / "Theme.kt",
    "internal val BoardLegalTarget = Color(0xCC2DD4BF)\n",
    "internal val BoardLegalTarget = Color(0xCC2DD4BF)\n"
    "internal val PieceLightFill = Color(0xFFF7F3EA)\n"
    "internal val PieceDarkFill = Color(0xFF172033)\n"
    "internal val PieceLightStroke = Color(0xFF26364D)\n"
    "internal val PieceDarkStroke = Color(0xFFE8EEF7)\n"
    "internal val CoordinateLabelOnLight = AppBackground\n"
    "internal val CoordinateLabelOnDark = OnBackground\n",
)
replace(
    MAIN / "ChessPiece.kt",
    "import androidx.compose.ui.graphics.Color\n",
    "import androidx.compose.ui.graphics.Color\n",
)
replace(
    MAIN / "ChessPiece.kt",
    "    val fill = if (isWhite) Color(0xFFF7F3EA) else Color(0xFF172033)\n    val stroke = if (isWhite) Color(0xFF26364D) else Color(0xFFE8EEF7)\n",
    "    val fill = if (isWhite) PieceLightFill else PieceDarkFill\n    val stroke = if (isWhite) PieceLightStroke else PieceDarkStroke\n",
)
replace(
    MAIN / "ChessBoardView.kt",
    "import androidx.compose.ui.graphics.Color\n",
    "",
)
replace(
    MAIN / "ChessBoardView.kt",
    ".background(\n                                if (isLastMove) lerp(baseColor, PrimaryStrong, 0.30f) else baseColor,\n                            )",
    ".background(\n                                if (isLastMove) lerp(baseColor, BoardLastMove, 0.30f) else baseColor,\n                            )",
)
replace(
    MAIN / "Theme.kt",
    "internal val BoardLastMove = Color(0x665EEAD4)\n",
    "internal val BoardLastMove = PrimaryStrong\n",
)
replace(
    MAIN / "ChessBoardView.kt",
    "color = Color.Black.copy(alpha = 0.58f),",
    "color = if (baseColor == BoardLight) CoordinateLabelOnLight else CoordinateLabelOnDark,",
    count=2,
)

arch_test = UTEST / "ReviewFixArchitectureTest.kt"
arch_test.write_text('''package com.ekkus93.chessapp\n\nimport java.io.File\nimport org.junit.Assert.assertFalse\nimport org.junit.Assert.assertTrue\nimport org.junit.Test\n\nclass ReviewFixArchitectureTest {\n    private fun source(name: String): String =\n        File(System.getProperty("user.dir"), "src/main/kotlin/com/ekkus93/chessapp/$name")\n            .readText()\n\n    @Test\n    fun boardAndPieceComposablesDoNotOwnProductColorLiterals() {\n        for (name in listOf("ChessPiece.kt", "ChessBoardView.kt")) {\n            val text = source(name)\n            assertFalse("$name must not own Color hex literals", Regex("Color\\\\(0xFF").containsMatchIn(text))\n            assertFalse("$name must not own Color.Black/White literals", Regex("Color\\\\.(Black|White)").containsMatchIn(text))\n        }\n    }\n\n    @Test\n    fun boardUsesNamedLastMoveAndCoordinateTokens() {\n        val text = source("ChessBoardView.kt")\n        assertTrue(text.contains("lerp(baseColor, BoardLastMove, 0.30f)"))\n        assertTrue(text.contains("CoordinateLabelOnLight"))\n        assertTrue(text.contains("CoordinateLabelOnDark"))\n    }\n}\n''')
mark_section("AR-002")
commit(
    "AR-002",
    "refactor(android): centralize board and piece colors",
    [TODO, MAIN / "Theme.kt", MAIN / "ChessPiece.kt", MAIN / "ChessBoardView.kt", arch_test],
    [unit(), compile_android_tests()],
)

# ---------------------------------------------------------------------------
# AR-003 — player-facing copy.
# ---------------------------------------------------------------------------
replace(
    MAIN / "SetupScreen.kt",
    '"Native cleanup must succeed before another game can start."',
    '"Cleanup must finish before another game can start."',
)
replace(
    MAIN / "SetupScreen.kt",
    '"Play against the native Rust chess engine."',
    '"Play against the Rust chess engine."',
)
append_before(
    arch_test,
    "}\n",
    '''    @Test\n    fun setupPlayerCopyDoesNotExposeNativeArchitectureJargon() {\n        val text = source("SetupScreen.kt")\n        val stringLiterals = Regex("\\\"(?:\\\\.|[^\\\"])*\\\"").findAll(text).map { it.value }.toList()\n        assertFalse(stringLiterals.any { it.contains("native", ignoreCase = true) })\n        assertFalse(stringLiterals.any { it.contains("JNI", ignoreCase = true) })\n    }\n\n''',
)
mark_section("AR-003")
commit(
    "AR-003",
    "fix(android): remove architecture jargon from setup copy",
    [TODO, MAIN / "SetupScreen.kt", arch_test],
    [unit(), compile_android_tests()],
)

# ---------------------------------------------------------------------------
# AR-004 — verify system-bar appearance first; patch only if the runtime test fails.
# ---------------------------------------------------------------------------
main_activity_test = ATEST / "SystemBarAppearanceInstrumentedTest.kt"
main_activity_test.write_text('''package com.ekkus93.chessapp\n\nimport androidx.compose.ui.test.junit4.createAndroidComposeRule\nimport androidx.core.view.WindowCompat\nimport androidx.test.ext.junit.runners.AndroidJUnit4\nimport org.junit.Assert.assertFalse\nimport org.junit.Rule\nimport org.junit.Test\nimport org.junit.runner.RunWith\n\n@RunWith(AndroidJUnit4::class)\nclass SystemBarAppearanceInstrumentedTest {\n    @get:Rule\n    val composeRule = createAndroidComposeRule<MainActivity>()\n\n    @Test\n    fun api35SystemBarsUseDarkIconAppearance() {\n        composeRule.runOnIdle {\n            val window = composeRule.activity.window\n            val controller = WindowCompat.getInsetsController(window, window.decorView)\n            assertFalse("status bar must not request light icons", controller.isAppearanceLightStatusBars)\n            assertFalse("navigation bar must not request light icons", controller.isAppearanceLightNavigationBars)\n        }\n    }\n}\n''')
first = sh(connected("com.ekkus93.chessapp.SystemBarAppearanceInstrumentedTest"), check=False)
changed_main = False
if first.returncode != 0:
    replace(
        MAIN / "MainActivity.kt",
        "import androidx.lifecycle.viewmodel.compose.viewModel\n",
        "import androidx.lifecycle.viewmodel.compose.viewModel\nimport androidx.core.view.WindowCompat\n",
    )
    replace(
        MAIN / "MainActivity.kt",
        "        super.onCreate(savedInstanceState)\n        setContent {\n",
        "        super.onCreate(savedInstanceState)\n        WindowCompat.getInsetsController(window, window.decorView).apply {\n            isAppearanceLightStatusBars = false\n            isAppearanceLightNavigationBars = false\n        }\n        setContent {\n",
    )
    changed_main = True
    sh(connected("com.ekkus93.chessapp.SystemBarAppearanceInstrumentedTest"))
else:
    print("AR-004 verify-first observation: current API-35 runtime already reports dark system-bar icon appearance; no production window code added.")
mark_section("AR-004")
paths = [TODO, main_activity_test]
if changed_main:
    paths.append(MAIN / "MainActivity.kt")
commit(
    "AR-004",
    "test(android): verify API 35 system bar appearance" if not changed_main else "fix(android): enforce API 35 system bar appearance",
    paths,
    [compile_android_tests(), connected("com.ekkus93.chessapp.SystemBarAppearanceInstrumentedTest")],
)

# ---------------------------------------------------------------------------
# AR-005 — board-size documentation.
# ---------------------------------------------------------------------------
replace(
    MAIN / "GameScreen.kt",
    "        val nonBoardHeight = statusHeight + tabHeight + actionHeight + minimumPanelHeight + gap * 4\n        val boardSize = minOf(\n",
    "        val nonBoardHeight = statusHeight + tabHeight + actionHeight + minimumPanelHeight + gap * 4\n        // Use the largest square bounded by the viewport width and by the remaining height after\n        // the fixed status/tab/action regions, minimum panel, and gaps; the board shrinks first.\n        val boardSize = minOf(\n",
)
rust_android_doc = Path("docs/RUST_ANDROID_APP.md")
doc_text = rust_android_doc.read_text()
anchor = "##"
# Add a compact, implementation-specific layout paragraph near the first layout mention if present,
# otherwise append it; exact behavior is verified against GameScreen.kt above.
paragraph = "\n### Board sizing\n\nThe playable Compose shell computes `boardSize` as the minimum of available width and available height after subtracting the fixed `statusHeight`, `tabHeight`, `actionHeight`, `minimumPanelHeight`, and four inter-region gaps. This implements a shrink-before-clip policy: the chessboard gives up size before the status, tabs, bounded panel, or action row can be clipped.\n"
if "### Board sizing" not in doc_text:
    rust_android_doc.write_text(doc_text.rstrip() + "\n" + paragraph)
mark_section("AR-005")
commit(
    "AR-005",
    "docs(android): document board sizing policy",
    [TODO, MAIN / "GameScreen.kt", rust_android_doc],
    ["grep -Fq 'the board shrinks first' android-harness/android-app/src/main/kotlin/com/ekkus93/chessapp/GameScreen.kt && grep -Fq 'shrink-before-clip' docs/RUST_ANDROID_APP.md"],
)

# ---------------------------------------------------------------------------
# AR-006 — remove auto-scroll ordering dependency.
# ---------------------------------------------------------------------------
replace(
    MAIN / "GamePanels.kt",
    "import androidx.compose.runtime.LaunchedEffect\nimport androidx.compose.runtime.remember\n",
    "import androidx.compose.runtime.LaunchedEffect\nimport androidx.compose.runtime.getValue\nimport androidx.compose.runtime.mutableStateOf\nimport androidx.compose.runtime.remember\nimport androidx.compose.runtime.setValue\nimport androidx.compose.runtime.snapshotFlow\n",
)
replace(
    MAIN / "GamePanels.kt",
    '''    val rows = remember(sanMoves) { moveRows(sanMoves) }\n    LaunchedEffect(rows.size) {\n        if (rows.isEmpty()) {\n            return@LaunchedEffect\n        }\n        val layout = listState.layoutInfo\n        val lastVisible = layout.visibleItemsInfo.lastOrNull()?.index\n        val wasNearBottom = layout.totalItemsCount == 0 ||\n            lastVisible == null || lastVisible >= layout.totalItemsCount - 2\n        if (wasNearBottom) {\n            listState.animateScrollToItem(rows.lastIndex)\n        }\n    }\n''',
    '''    val rows = remember(sanMoves) { moveRows(sanMoves) }\n    var followLatest by remember(listState) { mutableStateOf(true) }\n    LaunchedEffect(listState) {\n        snapshotFlow {\n            val layout = listState.layoutInfo\n            val lastVisible = layout.visibleItemsInfo.lastOrNull()?.index\n            val nearBottom = layout.totalItemsCount == 0 ||\n                lastVisible == null || lastVisible >= layout.totalItemsCount - 2\n            listState.isScrollInProgress to nearBottom\n        }.collect { (scrolling, nearBottom) ->\n            // Only direct/programmatic scrolling changes follow mode; a new layout alone cannot\n            // race this decision before the rows-size effect runs.\n            if (scrolling) {\n                followLatest = nearBottom\n            }\n        }\n    }\n    LaunchedEffect(rows.size, followLatest) {\n        if (rows.isNotEmpty() && followLatest) {\n            listState.animateScrollToItem(rows.lastIndex)\n        }\n    }\n''',
)
mark_section("AR-006")
commit(
    "AR-006",
    "fix(android): remove move-list effect ordering dependency",
    [TODO, MAIN / "GamePanels.kt"],
    [compile_android_tests(), connected("com.ekkus93.chessapp.MoveHistoryAutoScrollInstrumentedTest")],
)

# ---------------------------------------------------------------------------
# AR-007 — global busy/cleanup guard consistency.
# ---------------------------------------------------------------------------
view_model = MAIN / "ChessViewModel.kt"
replace(
    view_model,
    "    fun restartGame() {\n        val current = game ?: return\n",
    "    fun restartGame() {\n        val configuration = mutableState.value\n        if (!canRunActiveGameOperation(configuration)) {\n            return\n        }\n        val current = game ?: return\n",
)
replace(
    view_model,
    "    fun resign() {\n        val current = game ?: return\n        val snapshot = mutableState.value.snapshot ?: return\n",
    "    fun resign() {\n        val configuration = mutableState.value\n        if (!canRunActiveGameOperation(configuration)) {\n            return\n        }\n        val current = game ?: return\n        val snapshot = configuration.snapshot ?: return\n",
)
replace(
    view_model,
    "    private fun submitMove(move: String) {\n        val current = game ?: return\n",
    "    private fun submitMove(move: String) {\n        val configuration = mutableState.value\n        if (!canRunActiveGameOperation(configuration)) {\n            return\n        }\n        val current = game ?: return\n",
)
append_before(
    view_model,
    "private fun displayMessage(error: RuntimeException): String =\n",
    "internal fun canRunActiveGameOperation(state: ChessUiState): Boolean =\n    !state.isSetup && !state.busy && !state.cleanupRequired\n\n",
)

# Add unit coverage for the guard and structural proof that all three call it before nextOperation().
append_before(
    arch_test,
    "}\n",
    '''    @Test\n    fun activeGameOperationsGuardBeforeGenerationAdvance() {\n        val text = source("ChessViewModel.kt")\n        for (signature in listOf("fun restartGame()", "fun resign()", "private fun submitMove(move: String)")) {\n            val start = text.indexOf(signature)\n            assertTrue("missing $signature", start >= 0)\n            val nextFunction = text.indexOf("\\n    fun ", start + signature.length).let { if (it < 0) text.length else it }\n            val body = text.substring(start, nextFunction)\n            val guard = body.indexOf("canRunActiveGameOperation(configuration)")\n            val generation = body.indexOf("nextOperation()")\n            assertTrue("$signature must guard before nextOperation", guard >= 0 && generation >= 0 && guard < generation)\n        }\n    }\n\n''',
)

guard_test = UTEST / "ActiveGameOperationGuardTest.kt"
guard_test.write_text('''package com.ekkus93.chessapp\n\nimport com.ekkus93.chessengine.ChessGameSnapshot\nimport com.ekkus93.chessengine.HumanSide\nimport org.junit.Assert.assertFalse\nimport org.junit.Assert.assertTrue\nimport org.junit.Test\n\nclass ActiveGameOperationGuardTest {\n    private fun activeState(busy: Boolean = false, cleanupRequired: Boolean = false) = ChessUiState(\n        snapshot = ChessGameSnapshot(\n            fen = "8/8/8/8/8/8/4K3/7k w - - 0 1",\n            legalMoves = emptyList(),\n            moves = emptyList(),\n            sanMoves = emptyList(),\n            humanSide = HumanSide.WHITE,\n            sideToMove = HumanSide.WHITE,\n            thinking = false,\n            outcome = null,\n            statusMessage = null,\n            engineDepth = null,\n            engineScore = null,\n            engineNodes = null,\n            engineNps = null,\n            engineElapsed = null,\n            principalVariation = emptyList(),\n            hashFullPerMille = null,\n        ),\n        busy = busy,\n        cleanupRequired = cleanupRequired,\n    )\n\n    @Test\n    fun onlyIdleActiveGameMayRunAnActiveGameOperation() {\n        assertTrue(canRunActiveGameOperation(activeState()))\n        assertFalse(canRunActiveGameOperation(ChessUiState()))\n        assertFalse(canRunActiveGameOperation(activeState(busy = true)))\n        assertFalse(canRunActiveGameOperation(activeState(cleanupRequired = true)))\n    }\n}\n''')
mark_section("AR-007")
commit(
    "AR-007",
    "fix(android): guard active-game operations while busy",
    [TODO, view_model, arch_test, guard_test],
    [unit(), compile_android_tests()],
)

print("STAGE1_COMPLETE", subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
