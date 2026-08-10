package com.ekkus93.chessapp

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
