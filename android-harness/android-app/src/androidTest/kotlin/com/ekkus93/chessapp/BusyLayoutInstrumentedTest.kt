package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class BusyLayoutInstrumentedTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun setupBusyStateDisablesWithoutMovingControls() {
        val state = mutableStateOf(ChessUiState())
        composeRule.setContent { RustChessTheme { Box(Modifier.requiredSize(360.dp, 640.dp)) { SetupScreen(state.value, {}, {}, {}) } } }
        val tags = listOf("side-white", "side-black", "depth-control", "start-game")
        val before = tags.associateWith { composeRule.boundsDp(it) }
        composeRule.runOnUiThread { state.value = state.value.copy(busy = true) }
        composeRule.waitForIdle()
        tags.forEach { assertBoundsEqual(before.getValue(it), composeRule.boundsDp(it), it) }
        tags.forEach { composeRule.onNodeWithTag(it).assertIsNotEnabled() }
    }

    @Test
    fun gameBusyAndGameOverDisableResignWithoutMovingActions() {
        val state = mutableStateOf(gameState())
        composeRule.setContent { RustChessTheme { Box(Modifier.requiredSize(360.dp, 640.dp)) { GameScreen(state.value, {}, {}, {}, {}) } } }
        val before = composeRule.boundsDp("game-actions")
        composeRule.runOnUiThread { state.value = state.value.copy(busy = true) }
        composeRule.waitForIdle()
        assertBoundsEqual(before, composeRule.boundsDp("game-actions"), "busy game-actions")
        composeRule.onNodeWithTag("action-resign").assertIsNotEnabled()
        composeRule.runOnUiThread { state.value = gameState(outcome = "White wins") }
        composeRule.waitForIdle()
        assertBoundsEqual(before, composeRule.boundsDp("game-actions"), "game-over game-actions")
        composeRule.onNodeWithTag("action-resign").assertIsNotEnabled()
    }

    private fun gameState(outcome: String? = null) = ChessUiState(snapshot = ChessGameSnapshot(
        fen = "8/8/8/8/8/8/4K3/7k w - - 0 1", legalMoves = emptyList(), moves = emptyList(), sanMoves = emptyList(),
        humanSide = HumanSide.WHITE, sideToMove = HumanSide.WHITE, thinking = false, outcome = outcome, statusMessage = null,
        engineDepth = null, engineScore = null, engineNodes = null, engineNps = null, engineElapsed = null,
        principalVariation = emptyList(), hashFullPerMille = null,
    ))
}
