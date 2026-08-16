package com.ekkus93.chessapp

import android.os.SystemClock
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.lifecycle.ViewModelProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.ekkus93.chessengine.HumanSide
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ChessAppVisualFlowEvidenceInstrumentedTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun captureRealWhiteAndBlackProductFlow() {
        composeRule.waitForIdle()
        captureVisualEvidence("setup")

        composeRule.onNodeWithTag("start-game").performClick()
        val viewModel = ViewModelProvider(composeRule.activity)[ChessViewModel::class.java]
        awaitUiState(viewModel) { state ->
            state.snapshot?.humanToMove == true && state.snapshot.moves.isEmpty() && !state.busy
        }
        composeRule.waitForIdle()
        captureVisualEvidence("white-idle")

        composeRule.onNodeWithContentDescription("e2 pawn").performClick()
        composeRule.onNodeWithContentDescription("e4 legal target").performClick()
        awaitUiState(viewModel) { state ->
            state.snapshot?.moves == listOf("e2e4") && state.snapshot.thinking
        }
        composeRule.waitForIdle()
        captureVisualEvidence("white-thinking")

        awaitUiState(viewModel) { state ->
            val snapshot = state.snapshot ?: return@awaitUiState false
            snapshot.moves.size == 2 && snapshot.moves.first() == "e2e4" && snapshot.humanToMove
        }
        composeRule.waitForIdle()
        captureVisualEvidence("white-engine-reply")

        captureDialog("New game", "new-game-dialog")
        captureDialog("Restart", "restart-dialog")
        captureDialog("Resign", "resign-dialog")

        viewModel.returnToSetup()
        awaitUiState(viewModel) { state -> state.isSetup && !state.busy }
        composeRule.waitForIdle()
        composeRule.onNodeWithTag("side-black").performClick()
        composeRule.onNodeWithTag("start-game").performClick()
        awaitUiState(viewModel) { state ->
            state.snapshot?.humanSide == HumanSide.BLACK &&
                state.snapshot.moves.size == 1 &&
                state.snapshot.humanToMove &&
                !state.busy
        }
        composeRule.waitForIdle()
        captureVisualEvidence("black-game")
    }

    private fun captureDialog(actionLabel: String, evidenceName: String) {
        composeRule.onNodeWithText(actionLabel).performClick()
        composeRule.waitForIdle()
        captureVisualEvidence(evidenceName)
        composeRule.onNodeWithText("Cancel").performClick()
        composeRule.waitForIdle()
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
        error("Android UI state did not reach the expected visual evidence condition")
    }
}
