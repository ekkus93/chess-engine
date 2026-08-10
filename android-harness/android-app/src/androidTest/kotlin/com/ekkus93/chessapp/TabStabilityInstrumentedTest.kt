package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class TabStabilityInstrumentedTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun boardAndActionsDoNotMoveAcrossTabSwitch() {
        composeRule.setContent { RustChessTheme { Box(Modifier.requiredSize(360.dp, 640.dp)) {
            GameScreen(gameState(), {}, {}, {}, {})
        } } }
        val board = composeRule.boundsDp("chess-board")
        val actions = composeRule.boundsDp("game-actions")
        composeRule.onNodeWithTag("tab-engine").performClick()
        composeRule.waitForIdle()
        assertBoundsEqual(board, composeRule.boundsDp("chess-board"), "chess-board")
        assertBoundsEqual(actions, composeRule.boundsDp("game-actions"), "game-actions")
    }

    private fun gameState() = ChessUiState(snapshot = ChessGameSnapshot(
        fen = "8/8/8/8/8/8/4K3/7k w - - 0 1", legalMoves = emptyList(), moves = emptyList(), sanMoves = emptyList(),
        humanSide = HumanSide.WHITE, sideToMove = HumanSide.WHITE, thinking = false, outcome = null, statusMessage = null,
        engineDepth = 4, engineScore = "+0.20", engineNodes = 12000, engineNps = 240000, engineElapsed = "50 ms",
        principalVariation = listOf("e2e3"), hashFullPerMille = 2,
    ))
}
