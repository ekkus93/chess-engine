package com.ekkus93.chessapp

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
