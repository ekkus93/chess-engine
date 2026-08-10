package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollToIndex
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ChessAppMoveHistoryStateInstrumentedTest {
    @get:Rule
    val composeRule = createComposeRule()

    @Test
    fun historicalMovePositionSurvivesEngineTabRoundTrip() {
        val sanMoves = List(48) { index -> if (index % 2 == 0) "Nf3" else "Nc6" }
        val uciMoves = List(48) { index -> if (index % 2 == 0) "g1f3" else "b8c6" }
        composeRule.setContent {
            RustChessTheme {
                Box(Modifier.requiredSize(360.dp, 640.dp)) {
                    GameScreen(
                        state = gameState(uciMoves, sanMoves),
                        onSquareTapped = {},
                        onNewGame = {},
                        onRestart = {},
                        onResign = {},
                    )
                }
            }
        }

        composeRule.onNodeWithTag("moves-list").performScrollToIndex(10)
        composeRule.onNodeWithText("11.").fetchSemanticsNode()
        composeRule.onNodeWithTag("tab-engine").performClick()
        composeRule.onNodeWithTag("engine-panel").fetchSemanticsNode()
        composeRule.onNodeWithTag("tab-moves").performClick()
        composeRule.onNodeWithText("11.").fetchSemanticsNode()
    }

    private fun gameState(
        moves: List<String>,
        sanMoves: List<String>,
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
            statusMessage = "Game in progress",
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
