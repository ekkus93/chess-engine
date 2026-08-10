package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.assertExists
import androidx.compose.ui.test.fetchSemanticsNode
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ChessAppLayoutInstrumentedTest {
    @get:Rule
    val composeRule = createComposeRule()

    @Test
    fun compactSetupKeepsEveryControlInsidePortraitViewportWithoutRootScroll() {
        composeRule.setContent {
            RustChessTheme {
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

        assertContained(
            rootTag = "setup-screen",
            childTags = listOf("side-white", "side-black", "depth-control", "start-game"),
        )
        assertNoRootScroll("setup-screen")
    }

    @Test
    fun compactGameKeepsStatusBoardTabsPanelAndActionsFullyVisible() {
        composeRule.setContent {
            RustChessTheme {
                Box(Modifier.requiredSize(360.dp, 640.dp)) {
                    GameScreen(
                        state = gameState(),
                        onSquareTapped = {},
                        onNewGame = {},
                        onRestart = {},
                        onResign = {},
                    )
                }
            }
        }

        assertContained(
            rootTag = "game-screen",
            childTags = listOf(
                "status-region",
                "chess-board",
                "game-tabs",
                "game-tab-body",
                "game-actions",
            ),
        )
        assertNoRootScroll("game-screen")
        assertSquare("chess-board")
    }

    @Test
    fun movesAndEngineTabsReuseTheSameBoundedRegion() {
        composeRule.setContent {
            RustChessTheme {
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

        composeRule.onNodeWithTag("moves-list").assertExists()
        val movesBounds = bounds("game-tab-body")
        composeRule.onNodeWithTag("tab-engine").performClick()
        composeRule.onNodeWithTag("engine-panel").assertExists()
        assertEquals(movesBounds, bounds("game-tab-body"))
        assertContained("game-screen", listOf("game-tab-body", "game-actions"))
    }

    @Test
    fun boardGeometryDoesNotMoveAcrossThinkingAndReplyStates() {
        val state = mutableStateOf(gameState())
        composeRule.setContent {
            RustChessTheme {
                Box(Modifier.requiredSize(360.dp, 640.dp)) {
                    GameScreen(
                        state = state.value,
                        onSquareTapped = {},
                        onNewGame = {},
                        onRestart = {},
                        onResign = {},
                    )
                }
            }
        }

        val idleBoard = bounds("chess-board")
        val idleActions = bounds("game-actions")
        composeRule.runOnUiThread {
            state.value = gameState(
                moves = listOf("e2e4"),
                sanMoves = listOf("e4"),
                thinking = true,
                sideToMove = HumanSide.BLACK,
                status = "You played e2e4",
            )
        }
        composeRule.waitForIdle()
        assertEquals(idleBoard, bounds("chess-board"))
        assertEquals(idleActions, bounds("game-actions"))

        composeRule.runOnUiThread {
            state.value = gameState(
                moves = listOf("e2e4", "c7c5"),
                sanMoves = listOf("e4", "c5"),
                status = "Engine played c7c5",
            )
        }
        composeRule.waitForIdle()
        assertEquals(idleBoard, bounds("chess-board"))
        assertEquals(idleActions, bounds("game-actions"))
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
        thinking: Boolean = false,
        sideToMove: HumanSide = HumanSide.WHITE,
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
            sideToMove = sideToMove,
            thinking = thinking,
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
