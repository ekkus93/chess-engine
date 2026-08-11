package com.ekkus93.chessapp

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
        return Regex("""java\.srcDir\("([^"]+)"\)""")
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
            .flatMap { root -> root.walkTopDown().filter { file -> file.isFile && file.extension == "kt" } }
    }

    @Test
    fun boardAndPieceComposablesDoNotOwnProductColorLiterals() {
        for (name in listOf("ChessPiece.kt", "ChessBoardView.kt")) {
            val text = appSource(name)
            assertFalse("$name must not own Color hex literals", Regex("Color\\(0xFF").containsMatchIn(text))
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
                "Log.e(LOG_TAG, \"failed to close native chess game during ViewModel cleanup\", error)",
            ),
            File(moduleDir, "../../crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessEngine.kt").canonicalFile to listOf(
                // Shared-library filename is an ABI/load contract, not player-facing copy.
                "System.loadLibrary(\"chess_jni\")",
            ),
            File(moduleDir, "../../crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessGame.kt").canonicalFile to listOf(
                // Shared-library filename is an ABI/load contract, not player-facing copy.
                "System.loadLibrary(\"chess_jni\")",
            ),
        )
        val stringLiteral = Regex("\\\"(?:\\\\.|[^\\\"])*\\\"")
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
                    "${file.path} production string literal exposes architecture jargon: $literal",
                    forbidden.any { term -> literal.contains(term, ignoreCase = true) },
                )
            }
        }
        assertEquals("all exact internal-only/ABI sinks must be accounted for", 5, internalAllowlistMatches)
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
