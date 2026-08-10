package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertIsNotSelected
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performSemanticsAction
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ChessAppSemanticsInstrumentedTest {
    @get:Rule
    val composeRule = createComposeRule()

    @Test
    fun sideSelectionAndDepthBoundsMapExactlyToPresentationState() {
        val state = mutableStateOf(ChessUiState())
        composeRule.setContent {
            RustChessTheme {
                Box(Modifier.requiredSize(360.dp, 640.dp)) {
                    SetupScreen(
                        state = state.value,
                        onSideChanged = { state.value = state.value.copy(humanSide = it) },
                        onDepthChanged = { state.value = state.value.copy(engineDepth = it) },
                        onStart = {},
                    )
                }
            }
        }

        composeRule.onNodeWithTag("side-white").assertIsSelected()
        composeRule.onNodeWithTag("side-black").assertIsNotSelected().performClick()
        composeRule.waitForIdle()
        composeRule.onNodeWithTag("side-black").assertIsSelected()
        composeRule.runOnIdle { assertEquals(HumanSide.BLACK, state.value.humanSide) }

        composeRule.onNodeWithTag("depth-control")
            .performSemanticsAction(SemanticsActions.SetProgress) { setProgress -> setProgress(1f) }
        composeRule.waitForIdle()
        composeRule.onNodeWithContentDescription("Engine depth 1").fetchSemanticsNode()
        composeRule.runOnIdle { assertEquals(1, state.value.engineDepth) }

        composeRule.onNodeWithTag("depth-control")
            .performSemanticsAction(SemanticsActions.SetProgress) { setProgress -> setProgress(12f) }
        composeRule.waitForIdle()
        composeRule.onNodeWithContentDescription("Engine depth 12").fetchSemanticsNode()
        composeRule.runOnIdle { assertEquals(12, state.value.engineDepth) }
    }

    @Test
    fun cleanupRequiredShowsExplicitRetryAndLocksConfiguration() {
        var cleanupRetried = false
        composeRule.setContent {
            RustChessTheme {
                Box(Modifier.requiredSize(360.dp, 640.dp)) {
                    SetupScreen(
                        state = ChessUiState(cleanupRequired = true),
                        onSideChanged = {},
                        onDepthChanged = {},
                        onStart = {},
                        onRetryCleanup = { cleanupRetried = true },
                    )
                }
            }
        }

        composeRule.onNodeWithTag("start-game").assertDoesNotExist()
        composeRule.onNodeWithTag("side-white").assertIsNotEnabled()
        composeRule.onNodeWithTag("side-black").assertIsNotEnabled()
        composeRule.onNodeWithTag("depth-control").assertIsNotEnabled()
        composeRule.onNodeWithTag("retry-cleanup").performClick()
        composeRule.runOnIdle { assertTrue(cleanupRetried) }
    }

    @Test
    fun tabsAndBoardSelectionExposeSelectedSemantics() {
        composeRule.setContent {
            RustChessTheme {
                Box(Modifier.requiredSize(360.dp, 640.dp)) {
                    GameScreen(
                        state = gameState(selectedSquare = "e2"),
                        onSquareTapped = {},
                        onNewGame = {},
                        onRestart = {},
                        onResign = {},
                    )
                }
            }
        }

        composeRule.onNodeWithTag("tab-moves").assertIsSelected()
        composeRule.onNodeWithTag("tab-engine").assertIsNotSelected().performClick()
        composeRule.waitForIdle()
        composeRule.onNodeWithTag("tab-engine").assertIsSelected()
        composeRule.onNodeWithContentDescription("e2 pawn selected").assertIsSelected()
    }

    private fun gameState(selectedSquare: String): ChessUiState = ChessUiState(
        humanSide = HumanSide.WHITE,
        engineDepth = 3,
        selectedSquare = selectedSquare,
        snapshot = ChessGameSnapshot(
            fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            legalMoves = listOf("e2e3", "e2e4"),
            moves = emptyList(),
            sanMoves = emptyList(),
            humanSide = HumanSide.WHITE,
            sideToMove = HumanSide.WHITE,
            thinking = false,
            outcome = null,
            statusMessage = "Your move",
            engineDepth = null,
            engineScore = null,
            engineNodes = null,
            engineNps = null,
            engineElapsed = null,
            principalVariation = emptyList(),
            hashFullPerMille = null,
        ),
    )
}
