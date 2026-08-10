package com.ekkus93.chessapp

import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class EnginePanelInstrumentedTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun fullMetricsRenderTheirFormattedValues() {
        composeRule.setContent { RustChessTheme { EnginePanel(snapshot(7, "+0.42", 12345, 987654, "1.2 s", listOf("e2e4", "e7e5"))) } }
        for (text in listOf("7", "+0.42", "12k", "988k", "Time 1.2 s", "PV e2e4 e7e5")) {
            composeRule.onNodeWithText(text).assertExists()
        }
    }

    @Test
    fun partialMetricsUseDashInsteadOfFabricatedZeros() {
        composeRule.setContent { RustChessTheme { EnginePanel(snapshot(5, null, null, null, null, emptyList())) } }
        composeRule.onNodeWithText("5").assertExists()
        composeRule.onAllNodesWithText("—").assertCountEquals(3)
        composeRule.onNodeWithText("Time —").assertExists()
        composeRule.onNodeWithText("PV —").assertExists()
    }

    private fun snapshot(depth: Int?, score: String?, nodes: Long?, nps: Long?, elapsed: String?, pv: List<String>) = ChessGameSnapshot(
        fen = "8/8/8/8/8/8/4K3/7k w - - 0 1", legalMoves = emptyList(), moves = emptyList(), sanMoves = emptyList(),
        humanSide = HumanSide.WHITE, sideToMove = HumanSide.WHITE, thinking = false, outcome = null, statusMessage = null,
        engineDepth = depth, engineScore = score, engineNodes = nodes, engineNps = nps, engineElapsed = elapsed,
        principalVariation = pv, hashFullPerMille = null,
    )
}
