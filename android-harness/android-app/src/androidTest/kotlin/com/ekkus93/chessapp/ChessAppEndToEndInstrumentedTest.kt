package com.ekkus93.chessapp

import android.content.pm.ActivityInfo
import android.os.SystemClock
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.lifecycle.ViewModelProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ChessAppEndToEndInstrumentedTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun realActivityRunsRedesignedWhiteGameThroughRustBookAndDialogs() {
        assertEquals(
            ActivityInfo.SCREEN_ORIENTATION_PORTRAIT,
            composeRule.activity.requestedOrientation,
        )
        composeRule.onNodeWithTag("setup-screen").fetchSemanticsNode()
        composeRule.onNodeWithTag("start-game").performClick()

        val viewModel = ViewModelProvider(composeRule.activity)[ChessViewModel::class.java]
        awaitUiState(viewModel) { state ->
            state.snapshot?.humanToMove == true && !state.busy
        }
        composeRule.waitForIdle()
        composeRule.onNodeWithTag("game-screen").fetchSemanticsNode()
        composeRule.onNodeWithTag("chess-board").fetchSemanticsNode()
        composeRule.onNodeWithTag("game-actions").fetchSemanticsNode()

        composeRule.onNodeWithContentDescription("e2 pawn").performClick()
        composeRule.onNodeWithContentDescription("e4 legal target").performClick()

        val afterHuman = awaitUiState(viewModel) { state ->
            state.snapshot?.moves == listOf("e2e4") && state.snapshot?.thinking == true
        }
        assertEquals(listOf("e4"), afterHuman.snapshot?.sanMoves)
        composeRule.waitForIdle()
        composeRule.onNodeWithText("Engine thinking…").fetchSemanticsNode()

        val afterEngine = awaitUiState(viewModel) { state ->
            state.snapshot?.moves == listOf("e2e4", "c7c5")
        }
        assertEquals(listOf("e4", "c5"), afterEngine.snapshot?.sanMoves)
        composeRule.waitForIdle()
        composeRule.onNodeWithText("e4").fetchSemanticsNode()
        composeRule.onNodeWithText("c5").fetchSemanticsNode()
        composeRule.onNodeWithContentDescription("e4 pawn last move").fetchSemanticsNode()
        composeRule.onNodeWithContentDescription("c5 pawn last move").fetchSemanticsNode()

        composeRule.onNodeWithTag("tab-engine").performClick()
        composeRule.onNodeWithTag("engine-panel").fetchSemanticsNode()
        composeRule.onNodeWithTag("game-actions").fetchSemanticsNode()
        composeRule.onNodeWithTag("tab-moves").performClick()
        composeRule.onNodeWithTag("moves-list").fetchSemanticsNode()

        composeRule.onNodeWithText("New game").performClick()
        composeRule.onNodeWithText("Start a new game?").fetchSemanticsNode()
        composeRule.onNodeWithText("Cancel").performClick()

        composeRule.onNodeWithText("Restart").performClick()
        composeRule.onNodeWithText("Restart this game?").fetchSemanticsNode()
        composeRule.onNodeWithText("Cancel").performClick()

        composeRule.onNodeWithText("Resign").performClick()
        composeRule.onNodeWithText("Resign this game?").fetchSemanticsNode()
        composeRule.onNodeWithText("Cancel").performClick()
    }

    private fun awaitUiState(
        viewModel: ChessViewModel,
        predicate: (ChessUiState) -> Boolean,
    ): ChessUiState {
        repeat(1_200) {
            val state = viewModel.state.value
            if (predicate(state)) {
                return state
            }
            SystemClock.sleep(10)
        }
        error("Android UI state did not reach the expected condition before the bounded deadline")
    }
}
