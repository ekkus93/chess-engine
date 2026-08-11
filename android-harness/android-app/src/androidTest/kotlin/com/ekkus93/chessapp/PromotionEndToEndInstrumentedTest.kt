package com.ekkus93.chessapp

import android.os.SystemClock
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performSemanticsAction
import androidx.lifecycle.ViewModelProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class PromotionEndToEndInstrumentedTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun realNormalStartFlowReachesPromotionAndSubmitsChosenPiece() {
        composeRule.onNodeWithTag("setup-screen").fetchSemanticsNode()
        composeRule.onNodeWithTag("depth-control")
            .performSemanticsAction(SemanticsActions.SetProgress) { setProgress -> setProgress(1f) }
        composeRule.waitForIdle()
        composeRule.onNodeWithContentDescription("Engine depth 1").fetchSemanticsNode()
        composeRule.onNodeWithTag("start-game").performClick()

        val viewModel = ViewModelProvider(composeRule.activity)[ChessViewModel::class.java]
        awaitUiState(viewModel) { state ->
            state.engineDepth == 1 && state.snapshot?.humanToMove == true && !state.busy
        }

        // This legal path was discovered by the SC-003 real-JNI bounded search. The test then
        // replays it only through the production UI and high-level ChessGame flow.
        for (move in HUMAN_PATH) {
            playHumanMoveAndAwaitReply(viewModel, move)
        }

        val readyToPromote = awaitUiState(viewModel) { state ->
            state.snapshot?.humanToMove == true &&
                !state.busy &&
                PROMOTION_MOVES.all { move -> move in state.snapshot.legalMoves }
        }
        assertEquals(1, readyToPromote.engineDepth)

        tapSquare("b7")
        tapSquare("a8")

        val choosing = awaitUiState(viewModel) { state ->
            state.promotionMoves.toSet() == PROMOTION_MOVES.toSet()
        }
        assertEquals(PROMOTION_MOVES.toSet(), choosing.promotionMoves.toSet())
        composeRule.waitForIdle()
        composeRule.onNodeWithText("Choose promotion").fetchSemanticsNode()
        composeRule.onNodeWithText("Bishop").performClick()

        // Human moves remain visible for one second before the first engine poll. Capture that
        // authoritative post-promotion snapshot so the promoted piece cannot be obscured by a
        // later legal engine reply.
        val promoted = awaitUiState(viewModel) { state ->
            state.snapshot?.moves?.lastOrNull() == PROMOTION_MOVE &&
                state.snapshot.thinking
        }
        assertTrue(PROMOTION_MOVE in promoted.snapshot!!.moves)
        assertEquals('B', BoardPosition.parse(promoted.snapshot.fen).pieces["a8"])
        assertTrue(promoted.promotionMoves.isEmpty())
    }

    private fun playHumanMoveAndAwaitReply(viewModel: ChessViewModel, move: String) {
        val ready = awaitUiState(viewModel) { state ->
            state.snapshot?.humanToMove == true && !state.busy
        }
        val before = requireNotNull(ready.snapshot)
        assertTrue("expected human move $move to be legal; legal=${before.legalMoves}", move in before.legalMoves)
        val beforeCount = before.moves.size

        tapSquare(move.substring(0, 2))
        tapSquare(move.substring(2, 4))

        val replied = awaitUiState(viewModel) { state ->
            val snapshot = state.snapshot
            snapshot != null &&
                snapshot.humanToMove &&
                !state.busy &&
                snapshot.moves.size >= beforeCount + 2 &&
                snapshot.moves.getOrNull(beforeCount) == move
        }
        assertEquals(move, replied.snapshot!!.moves[beforeCount])
    }

    private fun tapSquare(square: String) {
        composeRule.onNodeWithContentDescription(square, substring = true).performClick()
        composeRule.waitForIdle()
    }

    private fun awaitUiState(
        viewModel: ChessViewModel,
        predicate: (ChessUiState) -> Boolean,
    ): ChessUiState {
        repeat(3_000) {
            val state = viewModel.state.value
            if (predicate(state)) {
                return state
            }
            SystemClock.sleep(10)
        }
        error("Android UI state did not reach the expected condition before the bounded deadline")
    }

    companion object {
        private val HUMAN_PATH = listOf(
            "a2a3",
            "a3a4",
            "a4a5",
            "b2b3",
            "e2e3",
            "a5a6",
            "b3b4",
            "c2c3",
            "g2g3",
            "a6b7",
        )
        private val PROMOTION_MOVES = listOf("b7a8q", "b7a8r", "b7a8b", "b7a8n")
        private const val PROMOTION_MOVE = "b7a8b"
    }
}
