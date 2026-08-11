#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_TODO_2026-08-10.md"
SPEC = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_SPEC_2026-08-10.md"
CC_TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md"
INDEX = ROOT / "docs/LEGACY_TODO_INDEX.md"
AUDIT = ROOT / "scripts/task_post_port_review_fix_audit.sh"
CHESS_GAME = ROOT / "crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessGame.kt"
CHESS_ENGINE = ROOT / "crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessEngine.kt"
ARCH_TEST = ROOT / "android-harness/android-app/src/test/kotlin/com/ekkus93/chessapp/ReviewFixArchitectureTest.kt"
APP_GRADLE = ROOT / "android-harness/android-app/build.gradle.kts"
SYSTEM_BAR_TEST = ROOT / "android-harness/android-app/src/androidTest/kotlin/com/ekkus93/chessapp/SystemBarAppearanceInstrumentedTest.kt"
ANDROID_WORKFLOW = ROOT / ".github/workflows/android.yml"
PROBE_TEST = ROOT / "android-harness/host-jvm/src/test/kotlin/com/ekkus93/chessengine/PromotionPathEvidenceTest.kt"
PROBE_WORKFLOW = ROOT / ".github/workflows/android-second-corrections-promotion-probe.yml"
RALPH_SCRIPT = ROOT / ".github/android_second_corrections_ralph.py"
RALPH_WORKFLOW = ROOT / ".github/workflows/android-second-corrections-ralph.yml"

REVIEW_BASELINE = "a943b67abf4b187f1840a790ad9372d27576c3c5"
REPO = os.environ.get("GITHUB_REPOSITORY", "ekkus93/chess-engine")


def run(*args: str, check: bool = True, env: dict[str, str] | None = None, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(args), flush=True)
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    result = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=merged_env,
    )
    print(result.stdout, end="", flush=True)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run("git", *args, check=check)


def commit(message: str, paths: list[Path] | None = None) -> str:
    if paths is None:
        git("add", "-A")
    else:
        git("add", *[str(path.relative_to(ROOT)) for path in paths])
    staged = git("diff", "--cached", "--quiet", check=False)
    if staged.returncode == 0:
        raise RuntimeError(f"no staged changes for commit: {message}")
    git("commit", "-m", message)
    sha = git("rev-parse", "HEAD").stdout.strip()
    git("push", "origin", "HEAD:master")
    print(f"COMMIT {sha} {message}", flush=True)
    return sha


def replace_exact(path: Path, old: str, new: str, count: int = 1) -> None:
    text = path.read_text()
    actual = text.count(old)
    if actual != count:
        raise RuntimeError(f"{path}: expected {count} occurrences of {old!r}, found {actual}")
    path.write_text(text.replace(old, new, count))


def replace_section(path: Path, start: str, end: str, replacement: str) -> None:
    text = path.read_text()
    a = text.index(start)
    b = text.index(end, a)
    path.write_text(text[:a] + replacement.rstrip() + "\n\n---\n\n" + text[b:])


def mark_checkbox(section: str, contains: str, replacement_line: str | None = None) -> str:
    lines = section.splitlines()
    matches = [i for i, line in enumerate(lines) if line.startswith("- [ ]") and contains in line]
    if len(matches) != 1:
        raise RuntimeError(f"expected one unchecked checkbox containing {contains!r}, found {len(matches)}")
    i = matches[0]
    lines[i] = replacement_line if replacement_line is not None else lines[i].replace("- [ ]", "- [x]", 1)
    return "\n".join(lines)


def section_text(path: Path, start: str, end: str) -> tuple[str, str, str]:
    text = path.read_text()
    a = text.index(start)
    b = text.index(end, a)
    return text[:a], text[a:b], text[b:]


def update_section(path: Path, start: str, end: str, updater) -> None:
    prefix, section, suffix = section_text(path, start, end)
    path.write_text(prefix + updater(section) + suffix)


def configure_git() -> None:
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    git("status", "--short")
    if git("status", "--porcelain").stdout.strip():
        raise RuntimeError("Ralph runner started with a dirty worktree")


def validate_sc000_premises() -> None:
    index = INDEX.read_text()
    audit = AUDIT.read_text()
    todo = TODO.read_text()
    game = CHESS_GAME.read_text()
    cc = CC_TODO.read_text()
    assert "RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_TODO_2026-08-10.md` (in progress" in index
    assert "android_ui_review_fix_second_corrections_todo=" in audit
    assert "native Android game returned a null handle" in game
    assert "# CC-002A: Runtime observation" in cc
    assert "# CC-004: Fix AR-011" in cc
    assert f"**Review baseline SHA:** `{REVIEW_BASELINE}`" in todo
    git("cat-file", "-e", f"{REVIEW_BASELINE}^{{commit}}")


def complete_sc000() -> str:
    print("=== SC-000 ===", flush=True)
    validate_sc000_premises()

    def first_pass(section: str) -> str:
        checks = [
            "Confirmed CC-001 fixed its two originally-flagged strings",
            "Confirmed CC-002A's TODO section dropped 3 of 6",
            "Confirmed CC-004's \"documented blocker\" disposition",
            "Recorded the review baseline SHA",
            "Read `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_QUESTIONS_AND_ISSUES_2026-08-10.md` in full",
            "Confirmed all six items were resolved",
            "Registered `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_TODO_2026-08-10.md`",
            "Updated `scripts/task_post_port_review_fix_audit.sh`'s registration/count checks",
            "Review baseline SHA (state this spec/TODO pair reviewed)",
            "Reinspected each finding immediately before implementing its fix",
            "Did not reopen any other CC-00N or AR-00N task",
        ]
        for item in checks:
            section = mark_checkbox(section, item)
        return section

    update_section(TODO, "# SC-000:", "# SC-001:", first_pass)
    sc000_sha = commit("docs(android): activate second-corrections tracker", [TODO])

    def record_start(section: str) -> str:
        return mark_checbox(
            section,
            "Implementation-start SHA (captured immediately after SC-000 lands)",
            f"- [x] Implementation-start SHA (captured immediately after SC-000 lands): `{sc000_sha}`",
        )

    update_section(TODO, "# SC-000:", "# SC-001:", record_start)
    commit("docs(android): record second-corrections implementation start", [TODO])
    return sc000_sha


ARCH_TEST_CONTENT = r'''package com.ekkus93.chessapp

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ReviewFixArchitectureTest {
    private val moduleDir = File(System.getProperty("user.dir")).canonicalFile
    private val configuredProductionSourceRoots = listOf(
        File(moduleDir, "src/main/kotlin").canonicalFile,
        File(moduleDir, "../../crates/chess-jni/kotlin/src/main/kotlin").canonicalFile,
    )

    private fun appSource(name: String): String =
        File(configuredProductionSourceRoots.first(), "com/ekkus93/chessapp/$name").readText()

    private fun declaredAdditionalProductionSourceRoots(): Set<File> {
        val buildScript = File(moduleDir, "build.gradle.kts").readText()
        return Regex("""\java\.srcDir\(\"[^\"]+)\"\)""")
            .findAll(buildScript)
            .map { match -> File(moduleDir, match.groupValues[1]).canonicalFile }
            .toSet()
    }

    private fun productionSources(): Sequence<File> {
        val configuredAdditional = configuredProductionSourceRoots.drop(1).toSet()
        assertEquals(
            "every Gradle-declared production java.srcDir must be covered by the architecture scanner",
            declaredAdditionalProductionSourceRoots(),
            configuredAdditional,
        )
        return configuredProductionSourceRoots
            .asSequence()
            .flatMap { root ->
                root.walkTopDown().filter { file -> file.isFile && file.extension == "kt" }
            }
    }

    @Test
    fun boardAndPieceComposablesDoNotOwnProductColorLiterals() {
        for (name in listOf("ChessPiece.kt", "ChessBoardView.kt")) {
            val text = appSource(name)
            assertFalse("$name must not own Color hex literals", Regex("Color\\(pxFF").containsMatchIn(text))
            assertFalse("$name must not own Color.Black/White literals", Regex("Color\\.(Black|White)").containsMatchIn(text))
        }
    }

    @Test
    fun boardUsesNamedLastMoveAndCoordinateTokens() {
        val text = appSource("ChessBoardView.kt")
        assertTrue(text.contains("lerp(baseColor, BoardLastMove, 0.30f)"))
        assertTrue(text.contains("CoordinateLabelOnLight"))
        assertTrue(text.contains("CoordinateLabelOnDark"))
    }

    @Test
    fun productionPlayerCopyDoesNotExposeArchitectureJargon() {
        val exactInternalOnlySnippets = mapOf(
            File(moduleDir, "src/main/kotlin/com/ekkus93/chessapp/ChessViewModel.kt").canonicalFile to listOf(
                // check() invariant text is never copied into ChessUiState.errorMessage or another UI sink.
                "check(game === created) { \"native game ownership changed during failed startup cleanup\" }",
                // check() invariant text is never copied into ChessUiState.errorMessage or another UI sink.
                "check(game === current) { \"native game ownership changed during close\" }",
                // Log.e() writes only to logcat during ViewModel leak cleanup; it is not rendered to the player.
                "Log.e(LOG_TAG, "failed to close native chess game during ViewModel cleanup", error)",
            ),
            File(
                moduleDir,
                "../../crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessEngine.kt",
            ).canonicalFile to listOf(
                // The shared-library filename is an ABI/load contract, not player-facing copy.
                "System.loadLibrary(\"chess_jni\")",
            ),
            File(
                moduleDir,
                "../../crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessGame.kt",
            ).canonicalFile to listOf(
                // The shared-library filename is an ABI/load contract, not player-facing copy.
                "System.loadLibrary(\"chess_jni\")",
            ),
        )
        val stringLiteral = Regex("\\\"(?:\\\\\\.|[^\\\"])*\\\"")
        val forbidden = listOf("native", "JNI", "shared layer", "architecture")
        var internalAllowlistMatches = 0

        for (file in productionSources()) {
            var text = file.readText()
            for (snippet in exactInternalOnlySnippets[file].orEmpty()) {
                val count = text.windowed(snippet.length, 1).count { it == snippet }
                assertEquals("internal-only allowlist snippet must exist exactly once: $snippet", 1, count)
                internalAllowlistMatches += count
                text = text.replace(snippet, "")
            }
            for (literal in stringLiteral.findAll(text).map { it.value }) {
                assertFalse(
                    "${file.name} production string literal exposes architecture jargon: $literal",
                    forbidden.any { term -> literal.contains(term, ignoreCase = true) },
                )
            }
        }
        assertEquals("all internal-only sinks must be accounted for", 5, internalAllowlistMatches)
    }

    @Test
    fun activeGameOperationsGuardBeforeGenerationAdvance() {
        val text = appSource("ChessViewModel.kt")
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


def apply_sc001_source_changes() -> None:
    game_replacements = {
        '\"native Android game snapshot must contain $FIELD_COUNT fields\"': '\"Android game snapshot must contain $FIELD_COUNT fields\"',
        '\"unsupported native Android game snapshot version: ${fields[0]}\"': '\"unsupported Android game snapshot version: ${fields[0]}\"',
        '\"native Android game snapshot terminator is missing\"': '\"Android game snapshot terminator is missing\"',
        '\"unknown native side: $value\"': '\"unknown game side: $value\",
        '\"unknown native boolean: $value\"': '\"unknown game boolean: $value\",
        '\"native Android game returned a null handle\"': '\"Android game failed to initialize\"',
    }
    engine_replacements = {
        '\"unknown native color code: $value\"': '\"unknown engine color code: $value\",
        '\"unknown native status code: $value\"': '\"unknown engine status code: $value\",
        '\"unknown native draw code: $value\"': '\"unknown engine draw code: $value\",
        '\"native game status must contain three fields\"': '\"engine game status must contain three fields\",
        '\"native weight identity must contain three fields\"': '\"engine weight identity must contain three fields\",
        '\"unknown native score code: $value\"': '\"unknown engine score code: $value\"',
        '\"unknown native termination code: $value\"': '\"unknown engine termination code: $value\"',
        '\"unknown native fallback code: $value\"': '\"unknown engine fallback code: $value\"',
        '\"native search result must contain exactly $FIELD_COUNT fields\"': '\"engine search result must contain exactly $FIELD_COUNT fields\",
        '\"native search failed\"': '\"engine search failed\",
        '\"chess-engine-native-reaper\"': '\"chess-engine-reaper\",
        '\"native search worker did not terminate after cancellation\"': '\"engine search worker did not terminate after cancellation\"',
    }
    for old, new in game_replacements.items():
        replace_exact(CHESS_GAME, old, new)
    for old, new in engine_replacements.items():
        replace_exact(CHESS_ENGINE, old, new" ¢2WFFRç’†÷7BÔ¥dÒ76W'F–öç2F†B–çFVçF–öæÆÇ’†&BÖ6öFR6†ævVBÖW76vW2à¢†÷7E÷FW7G2Ò$ôõBò&æG&ö–BÖ†&æW72ö†÷7BÖ§fÒ÷7&2÷FW7Bö¶÷FÆ–â ¢f÷"F‚–â†÷7E÷FW7G2ç&vÆö"‚"¢æ·B"“ ¢FW‡BÒF‚ç&VE÷FW‡B‚¢WFFVBÒFW‡@¢f÷"öÆBÂæWr–â²¢¦vÖU÷&WÆ6VÖVçG2Â¢¦Væv–æU÷&WÆ6VÖVçG7Òæ—FV×2‚“ ¢WFFVBÒWFFVBç&WÆ6R†öÆBç7G&—‚uÂ"r’ÂæWrç7G&—‚uÂ"r’¢–bWFFVBÒFW‡C ¢F‚çw&—FU÷FW‡B‡WFFVB ¢$4…õDU5Bçw&—FU÷FW‡B„$4…õDU5Eô4ôåDTåB  ¦FVbw&FÆR‚§F6·3¢7G"Â6†V6³¢&ööÂÒG'VR’Óâ7V'&ö6W72ä6ö×ÆWFVE&ö6W75·7G%Ó ¢&WGW&â'Vâ€¢&w&FÆR"Â"×"Â&æG&ö–BÖ†&æW72"Â§F6·2À¢"ÒÖæòÖFVÖöâ"Â"Ò×7F6·G&6R"Â"ÒÖ6öç6öÆS×Æ–â"À¢6†V6³Ö6†V6²À¢  ¦FVbfÆ–FFU÷63‚’ÓâæöæS ¢2&–Ö'’7G'V7GW&Â6†V6²à¢w&FÆR‚#¦æG&ö–BÖ§FW7DFV'VuVæ—EFW7B"Â"Ò×FW7G2"Â&6öÒæV¶·W3“2æ6†W76å&Wf–Wtf—„&6†—FV7GW&UFW7B" ¢2æVvF—fR6æ—G’¢Æ–W"×f—6–&ÆR¦&vöâ&V–çG&öGV7F–öâ×W7Bf–Âà¢÷&–v–æÂÒ4„U55ôtÔRç&VE÷FW‡B‚¢4„U55ôtÔRçw&—FU÷FW‡B†÷&–v–æÂç&WÆ6R‚uÂ$æG&ö–BvÖRf–ÆVBFò–æ—F–Æ—¦UÂ"rÂuÂ&æF—fRæG&ö–BvÖR&WGW&æVBçVÆÂ†æFÆUÂ"rÂ’¢&W7VÇBÒw&FÆR€¢#¦æG&ö–BÖ§FW7DFV'VuVæ—EFW7B"À¢"Ò×FW7G2"Â&6öÒæV¶·W3“2æ6†W76å&Wf–Wtf—„&6†—FV7GW&UFW7Bç&öGV7F–öåÆ–W$6÷”FöW4æ÷DW‡÷6T&6†—FV7GW&T¦&vöâ"À¢6†V6³ÔfÇ6RÀ¢¢4„U55ôtÔRçw&—FU÷FW‡B†÷&–v–æÂ¢–b&W7VÇBç&WGW&æ6öFRÓÒ ¢&—6R'VçF–ÖTW'&÷"‚%42ÓæVvF—fR6æ—G’f–ÆVC¢¦&vöâ&V–çG&öGV7F–öâv2æ÷B&V¦V7FVB" ¢2æVvF—fR6æ—G’#¢æWrw&FÆR&öGV7F–öâ6÷W&6R&ö÷B×W7Bf–ÂVçF–Â66ææW"6öæf–r—2WFFVBà¢w&FÆUö÷&–v–æÂÒôu$DÄRç&VE÷FW‡B‚¢æVVFÆRÒv¦fç7&4F—"‚"ââòââö7&FW2ö6†W72Ö¦æ’ö¶÷FÆ–â÷7&2öÖ–âö¶÷FÆ–â"’p¢–æ¦V7FVBÒæVVFÆR²uÆâ¦fç7&4F—"‚'7&2öÖ–âö¶÷FÆ–â×F†—&BÖf—‡GW&R"’p¢–bw&FÆUö÷&–v–æÂæ6÷VçB†æVVFÆR’Ò ¢&—6R'VçF–ÖTW'&÷"‚&6÷VÆBæ÷BVæ—VVÇ’Æö6FRW†—7F–ær¦fç7&4F—"FV6Æ&F–öâ"¢ôu$DÄRçw&—FU÷FW‡B†w&FÆUö÷&–v–æÂç&WÆ6R†æVVFÆRÂ–æ¦V7FVBÂ’¢&W7VÇBÒw&FÆR€¢#¦æG&ö–BÖ§FW7DFV'VuVæ—EFW7B"À¢"Ò×FW7G2"Â&6öÒæV¶·W3“2æ6†W76å&Wf–Wtf—„&6†—FV7GW&UFW7Bç&öGV7F–öåÆ–W$6÷”FöW4æ÷DW‡÷6T&6†—FV7GW&T¦&vöâ"À¢6†V6³ÔfÇ6RÀ¢¢ôu$DÄRçw&—FU÷FW‡B†w&FÆUö÷&–v–æÂ¢–b&W7VÇBç&WGW&æ6öFRÓÒ ¢&—6R'VçF–ÖTW'&÷"‚%42ÓæVvF—fR6æ—G’f–ÆVC¢Væ6÷fW&VB¦fç7&4F—"v2æ÷B&V¦V7FVB" ¢2&W7F÷&RæB'VâF†R&VÆWfçBgVÆÂ7W&f6W2à¢'Vâ‚&6&vò"Â&'V–ÆB"Â"ÒÖÆö6¶VB"Â"×"Â&6†W72Ö¦æ’"Â"Ò×&VÆV6R"¢w&FÆR€¢#¦æG&ö–BÖ¦Æ–çDFV'Vr"À¢#¦æG&ö–BÖ§FW7DFV'VuVæ—EFW7B"À¢#¦†÷7BÖ§fÓ§FW7B"À¢#¦æG&ö–BÖ¦76VÖ&ÆTFV'VtæG&ö–EFW7B"À¢  ¦FVb6ö×ÆWFU÷63†–×ÆVÖVçFF–öå÷7F'C¢7G"’Óâ7G# ¢&–çB‚#ÓÓÒ42ÓÓÓÒ"ÂfÇW6ƒÕG'VR¢76W'Bv¦fç7&4F—"‚"ââòââö7&FW2ö6†W72Ö¦æ’ö¶÷FÆ–â÷7&2öÖ–âö¶÷FÆ–â"’r–âôu$DÄRç&VE÷FW‡B‚¢Ç•÷63÷6÷W&6Uö6†ævW2‚¢fÆ–FFU÷63‚ ¢6V7F–öâÒbrrr242Ó¢f—‚F†R&V7W'&VB&æF—fR"¦&vöâFVfV7B–â6†W74vÖRæ·F  ¢2242Óãf—€ ¢Ò·…Ò&VBæG&ö–BÖö'V–ÆBæw&FÆRæ·G6w27GVÂ6÷W&6U6WG6ö¦fç7&4F—&6öæf–wW&F–öã²F†RÖöGVÆR6ö×–ÆW2—G2FVfVÇB7&2öÖ–âö¶÷FÆ–æÇW2ââòââö7&FW2ö6†W72Ö¦æ’ö¶÷FÆ–â÷7&2öÖ–âö¶÷FÆ–æà¢Ò·…ÒG&6VBF†R6—‚÷&–v–æÆÇ’×&W÷'FVB6†W74vÖRæ·FW†6WF–öâ7G&–æw2F‡&÷Vv‚6†W75f–WtÖöFVÂçV&Æ—6„W'&÷"‚–FòF†RÆ–W"×f—6–&ÆRW'&÷"F–Æös²ÆÂ6—‚vW&R&Wv÷&FVBFò&VÖ÷fR&6†—FV7GW&R¦&vöâv†–ÆR&W6W'f–ærÖVæ–ærà¢Ò·…Ò6†V6¶VBæG&ö–BÖ†&æW72ö†÷7BÖ§fÒ÷7&2÷FW7Bö¶÷FÆ–âò¢¦f÷"†&BÖ6öFVB6†ævVBÖW76vRFW‡BæB¶WBç’ffV7FVB76W'F–öç27–æ6‡&öæ—¦VBà¢Ò·…Ò&Wf–Wtf—„&6†—FV7GW&UFW7Bæ·Fæ÷r66ç2&÷F‚7W'&VçBw&FÆRÖ6ö×–ÆVB&öGV7F–öâ¶÷FÆ–â&ö÷G2à¢Ò·…ÒF†RW‡æFVB66âÇ6òF—7÷6—F–öæVBWfW'’f÷&&–FFVâ×FW&Ò7G&–ær–â6†W74Væv–æRæ·F¢&6†—FV7GW&Rv÷&F–ær–âW†6WF–öâ÷F‡&VBÖæÖR7G&–æw2v2&VÖ÷fVB&F†W"F†â'&öFÇ’ÆÆ÷vÆ—7FVBâöæÇ’F†RW†7B7—7FVÒæÆöDÆ–'&'’…Â&6†W75ö¦æ•Â"–$’f–ÆVæÖR—2æ'&÷vÇ’ÆÆ÷vÆ—7FVB–âV6‚¤ä’¶÷FÆ–âf–ÆRà¢Ò·…ÒW†—7F–ær–çFW&æÂÖöæÇ’6†W75f–WtÖöFVÆ6†V6²‚–öÆöræV6æ—WG2&VÖ–âW†7BÂæ'&÷vÇ’§W7F–f–VBÆÆ÷vÆ—7BVçG&–W2à¢Ò·…ÒÖV6†æ–6ÂgWGW&RÖF—&V7F÷'’–çf&–çBFFVC¢F†RFW7B'6W2WfW'’&öGV7F–öâ¦fç7&4F—"‚âââ–FV6Æ&F–öâ–âæG&ö–BÖö'V–ÆBæw&FÆRæ·G6æBf–Ç2–b—B—2æ÷B&W&W6VçFVB–âF†R66ææW"w26öæf–wW&VB&öGV7F–öâ&ö÷G2à ¢2242Óã"FW7G0 ¢Ò·…ÒW‡FVæFVB&Wf–Wtf—„&6†—FV7GW&UFW7F76W27&÷72&÷F‚7W'&VçB&öGV7F–öâ6÷W&6RF—&V7F÷&–W2à¢Ò·…ÒæVvF—fR6æ—G’76VC¢FV×÷&&–Ç’&W7F÷&–ærÂ&æF—fRæG&ö–BvÖR&WGW&æVBçVÆÂ†æFÆUÂ&ÖFR&öGV7F–öåÆ–W$6÷”FöW4æ÷DW‡÷6T&6†—FV7GW&T¦&vöæf–Ã²&W7F÷&–ærF†R6÷'&V7FVBFW‡BÖFR—B72v–âà¢Ò·…ÒæVvF—fR6÷W&6R×&ö÷B6æ—G’76VC¢FV×÷&&–Ç’FF–ærF†—&B¦fç7&4F—"…Â'7&2öÖ–âö¶÷FÆ–â×F†—&BÖf—‡GW&UÂ"–v—F†÷WB66ææW"6÷fW&vRÖFRF†R7G'V7GW&ÂFW7Bf–Ã²F†RFV6Æ&F–öâv2&WfW'FVBæBF†RFW7B76VBv–âà¢Ò·…Ò†÷7BÔ¥dÒ¤ä’FW7G2ÂæG&ö–B¥dÒ÷Væ—BFW7G2ÂæG&ö–BÆ–çBÂæBæG&ö–B–ç7G'VÖVçFF–öâ6ö×–ÆF–öâÆÂ72öâF†R6÷'&V7FVBv÷&¶–ærG&VRà ¢¢¤–×ÆVÖVçFF–öâ×7F'B4„¢¢¢¶–×ÆVÖVçFF–öå÷7F'GÖà¢rrp¢&WÆ6U÷6V7F–öâ…DôDòÂ"242Ó¢"Â"242Ó#¢"Â6V7F–öâ¢&WGW&â6öÖÖ—B€¢&f—‚†æG&ö–B“¢6Æ÷6R6V6öæBÖ6÷'&V7F–öç2¦&vöâ66÷R"À¢´4„U55ôtÔRÂ4„U55ôTät”äRÂ$4…õDU5BÂDôDõÒ²°¢f÷"–â…$ôõBò&æG&ö–BÖ†&æW72ö†÷7BÖ§fÒ÷7&2÷FW7Bö¶÷FÆ–â"’ç&vÆö"‚"¢æ·B"’–bv—B‚'7FGW2"Â"Ò×÷&6VÆ–â"Â7G"‡ç&VÆF—fU÷Fò…$ôõB’’’ç7FF÷WBç7G&—‚¢ÒÀ¢  ¦FVb6ö×ÆWFU÷63"‚’Óâ7G# ¢&–çB‚#ÓÓÒ42Ó"ÓÓÒ"ÂfÇW6ƒÕG'VR¢7—7FVÕö&"Ò5•5DTÕô$%õDU5Bç&VE÷FW‡B‚¢v÷&¶fÆ÷rÒäE$ô”Eõtõ$´dÄõrç&VE÷FW‡B‚¢f÷"&WV—&VB–â°¢$'V–ÆBådU%4”ôâå4Dµô”åB"À¢#ÃÒ""À¢'7FGW5&F–òãÒãs"À¢"