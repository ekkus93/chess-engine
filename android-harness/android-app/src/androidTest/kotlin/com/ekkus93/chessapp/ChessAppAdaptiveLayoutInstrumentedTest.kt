package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ChessAppAdaptiveLayoutInstrumentedTest {
    @get:Rule
    val composeRule = createComposeRule()

    @Test
    fun longMoveHistoryScrollsInternallyWhileGameShellRemainsFixed() {
        val sanMoves = List(48) { index -> if (index % 2 == 0) "Nf3" else "Nc6" }
        val uciMoves = List(48) { index -> if (index % 2 == 0) "g1f3" else "b8c6" }
        composeRule.setContent {
            RustChessTheme {
                Box(Modifier.requiredSize(360.dp, 640.dp)) {
                    GameScreen(
                        state = gameState(moves = uciMoves, sanMoves = sanMoves),
                        onSquareTapped = {},
                        onNewGame = {},
                        onRestart = {},
                        onResign = {},
                    )
                }
            }
        }

        assertNoRootScroll("game-screen")
        assertContained("game-screen", listOf("chess-board", "game-tab-body", "game-actions"))
        val movesNode = composeRule.onNodeWithTag("moves-list").fetchSemanticsNode()
        assertTrue(
            "long move history must expose internal scrolling",
            movesNode.config.contains(SemanticsActions.ScrollBy),
        )
    }

    @Test
    fun enlargedTextKeepsCompactSetupAndCoreGameRegionsContained() {
        composeRule.setContent {
            RustChessTheme {
                val density = LocalDensity.current
                CompositionLocalProvider(
                    LocalDensity provides Density(density.density, fontScale = 1.3f),
                ) {
                    Box(Modifier.requiredSize(360.dp, 640.dp)) {
                        SetupScreen(
                            state = ChessUiState(),
                            onSideChanged = {},
                            onDepthChanged = {},
                            onStart = {},
                        )
                    }
                }
            }
        }
        assertContained(
            "setup-screen",
            listOf("side-white", "side-black", "depth-control", "start-game"),
        )
        assertNoRootScroll("setup-screen")

        composeRule.setContent {
            RustChessTheme {
                val density = LocalDensity.current
                CompositionLocalProvider(
                    LocalDensity provides Density(density.density, fontScale = 1.3f),
                ) {
                    Box(Modifier.requiredSize(360.dp, 640.dp)) {
                        GameScreen(
                            state = gameState(
                                moves = listOf("e2e4", "c7c5"),
                                sanMoves = listOf("e4", "c5"),
                                status = "Engine played c7c5",
                            ),
                            onSquareTapped = {},
                            onNewGame = {},
                            onRestart = {},
                            onResign = {},
                        )
                    }
                }
            }
        }
        assertContained(
            "game-screen",
            listOf("status-region", "chess-board", "game-tabs", "game-tab-body", "game-actions"),
        )
        assertNoRootScroll("game-screen")
        assertSquare("chess-board")
    }

    private fun assertContained(rootTag: String, childTags: List<String>) {
        val root = bounds(rootTag)
        childTags.forEach { tag ->
            val child = bounds(tag)
            assertTrue("$tag left edge escaped $rootTag", child.left >= root.left)
            assertTrue("$tag top edge escaped $rootTag", child.top >= root.top)
            assertTrue("$tag right edge escaped $rootTag", child.right <= root.right)
            assertTrue("$tag bottom edge escaped $rootTag", child.bottom <= root.bottom)
            assertTrue("$tag must have positive width", child.width > 0f)
            assertTrue("$tag must have positive height", child.height > 0f)
        }
    }

    private fun assertNoRootScroll(tag: String) {
        val node = composeRule.onNodeWithTag(tag).fetchSemanticsNode()
        assertFalse(
            "$tag must not expose a root scroll action",
            node.config.contains(SemanticsActions.ScrollBy),
        )
    }

    private fun assertSquare(tag: String) {
        val value = bounds(tag)
        assertTrue("$tag must remain square", kotlin.math.abs(value.width - value.height) < 1f)
    }

    private fun bounds(tag: String): Rect =
        composeRule.onNodeWithTag(tag).fetchSemanticsNode().boundsInRoot

    private fun gameState(
        moves: List<String> = emptyList(),
        sanMoves: List<String> = emptyList(),
        status: String? = null,
    ): ChessUiState = ChessUiState(
        humanSide = HumanSide.WHITE,
        engineDepth = 3,
        snapshot = ChessGameSnapshot(
            fen = "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            legalMoves = listOf("g1f3", "b1c3", "d2d4"),
            moves = moves,
            sanMoves = sanMoves,
            humanSide = HumanSide.WHITE,
            sideToMove = HumanSide.WHITE,
            thinking = false,
            outcome = null,
            statusMessage = status,
            engineDepth = 3,
            engineScore = "+0.18",
            engineNodes = 18_420,
            engineNps = 241_000,
            engineElapsed = "76 ms",
            principalVariation = listOf("g1f3", "b8c6", "f1b5"),
            hashFullPerMille = 12,
        ),
    )
}
