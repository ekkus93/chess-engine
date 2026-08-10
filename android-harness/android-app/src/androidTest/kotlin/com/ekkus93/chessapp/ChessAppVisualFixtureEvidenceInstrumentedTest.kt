package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.captureToImage
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onRoot
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
class ChessAppVisualFixtureEvidenceInstrumentedTest {
    @get:Rule
    val composeRule = createComposeRule()

    @Test
    fun captureMovesInternalScrollAndPopulatedEnginePanel() {
        val sanMoves = realisticHistory()
        val uciMoves = List(sanMoves.size) { ply -> if (ply % 2 == 0) "g1f3" else "b8c6" }
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

        composeRule.waitForIdle()
        capture("moves-multiple")
        composeRule.onNodeWithTag("moves-list").performScrollToIndex(12)
        composeRule.waitForIdle()
        capture("moves-scrolled")
        composeRule.onNodeWithTag("tab-engine").performClick()
        composeRule.waitForIdle()
        capture("engine-metrics")
    }

    @Test
    fun capturePromotionDialog() {
        composeRule.setContent {
            RustChessTheme {
                PromotionDialog(
                    moves = listOf("a7a8q", "a7a8r", "a7a8b", "a7a8n"),
                    onChoose = {},
                    onCancel = {},
                )
            }
        }
        composeRule.waitForIdle()
        capture("promotion-dialog")
    }

    @Test
    fun captureBoundedErrorDialog() {
        composeRule.setContent {
            RustChessTheme {
                ChessEngineErrorDialog(
                    message = "The native chess engine reported a deterministic test failure. " +
                        "The real error remains visible and no retry, alternate move, or fallback path is used.",
                    onDismiss = {},
                )
            }
        }
        composeRule.waitForIdle()
        capture("error-dialog")
    }

    private fun capture(name: String) {
        saveVisualEvidence(name, composeRule.onRoot().captureToImage())
    }

    private fun gameState(
        moves: List<String>,
        sanMoves: List<String>,
    ): ChessUiState = ChessUiState(
        humanSide = HumanSide.WHITE,
        engineDepth = 8,
        snapshot = ChessGameSnapshot(
            fen = "r1bq1rk1/2p2ppp/p1np1n2/1p2p3/3PP3/1B3N2/PP3PPP/RNBQ1RK1 w - - 0 9",
            legalMoves = listOf("d4d5", "b3f7", "f3g5"),
            moves = moves,
            sanMoves = sanMoves,
            humanSide = HumanSide.WHITE,
            sideToMove = HumanSide.WHITE,
            thinking = false,
            outcome = null,
            statusMessage = "Your move",
            engineDepth = 8,
            engineScore = "+0.42",
            engineNodes = 1_284_220,
            engineNps = 438_000,
            engineElapsed = "2.9 s",
            principalVariation = listOf("d4d5", "c6e7", "b1c3", "f6g6", "c1e3"),
            hashFullPerMille = 84,
        ),
    )

    private fun realisticHistory(): List<String> = listOf(
        "e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6",
        "O-O", "Be7", "Re1", "b5", "Bb3", "d6", "c3", "O-O",
        "h3", "Nb8", "d4", "Nbd7", "c4", "c6", "Nc3", "Qc7",
        "Be3", "Bb7", "Rc1", "Rfe8", "a3", "Bf8", "Ba2", "h6",
        "b4", "exd4", "Nxd4", "Ne5", "cxb5", "axb5", "f4", "Nc4",
        "Bxc4", "bxc4", "Bf2", "Rxa3", "e5", "dxe5", "fxe5", "Ng4",
    )
}
