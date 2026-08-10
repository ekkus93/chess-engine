package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class BlackOrientationInstrumentedTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun compactBlackGameIsContainedAndActuallyBlackOriented() {
        composeRule.setContent { RustChessTheme { Box(Modifier.requiredSize(360.dp, 640.dp)) {
            GameScreen(blackState(), {}, {}, {}, {})
        } } }
        composeRule.assertContained("game-screen", listOf("status-region", "chess-board", "game-tabs", "game-tab-body", "game-actions"))
        composeRule.assertNoRootScroll("game-screen")
        composeRule.assertSquare("chess-board")
        val density = InstrumentationRegistry.getInstrumentation().targetContext.resources.displayMetrics.density
        val board = composeRule.boundsDp("chess-board")
        val a1 = pxRectToDp(composeRule.onNodeWithContentDescription("a1 rook").fetchSemanticsNode().boundsInRoot, density)
        assertTrue("a1 must be above board midpoint for Black orientation", a1.center.y < board.center.y)
    }

    @Test
    fun blackBoardAndActionsStayFixedAcrossThinkingState() {
        val state = mutableStateOf(blackState())
        composeRule.setContent { RustChessTheme { Box(Modifier.requiredSize(360.dp, 640.dp)) {
            GameScreen(state.value, {}, {}, {}, {})
        } } }
        val board = composeRule.boundsDp("chess-board")
        val actions = composeRule.boundsDp("game-actions")
        composeRule.runOnUiThread { state.value = blackState(thinking = true, sideToMove = HumanSide.WHITE) }
        composeRule.waitForIdle()
        assertBoundsEqual(board, composeRule.boundsDp("chess-board"), "black chess-board")
        assertBoundsEqual(actions, composeRule.boundsDp("game-actions"), "black game-actions")
    }

    private fun blackState(thinking: Boolean = false, sideToMove: HumanSide = HumanSide.BLACK) = ChessUiState(
        humanSide = HumanSide.BLACK,
        engineDepth = 3,
        snapshot = ChessGameSnapshot(
            fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
            legalMoves = listOf("g8f6", "b8c6"), moves = emptyList(), sanMoves = emptyList(),
            humanSide = HumanSide.BLACK, sideToMove = sideToMove, thinking = thinking,
            outcome = null, statusMessage = null, engineDepth = 3, engineScore = "+0.10",
            engineNodes = 1000, engineNps = 2000, engineElapsed = "10 ms",
            principalVariation = listOf("g8f6"), hashFullPerMille = 1,
        ),
    )
}
