package com.ekkus93.chessapp

import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ActiveGameOperationGuardTest {
    private fun activeState(busy: Boolean = false, cleanupRequired: Boolean = false) = ChessUiState(
        snapshot = ChessGameSnapshot(
            fen = "8/8/8/8/8/8/4K3/7k w - - 0 1",
            legalMoves = emptyList(), moves = emptyList(), sanMoves = emptyList(),
            humanSide = HumanSide.WHITE, sideToMove = HumanSide.WHITE, thinking = false,
            outcome = null, statusMessage = null, engineDepth = null, engineScore = null,
            engineNodes = null, engineNps = null, engineElapsed = null,
            principalVariation = emptyList(), hashFullPerMille = null,
        ),
        busy = busy,
        cleanupRequired = cleanupRequired,
    )

    @Test
    fun onlyIdleActiveGameMayRunOperation() {
        assertTrue(canRunActiveGameOperation(activeState()))
        assertFalse(canRunActiveGameOperation(ChessUiState()))
        assertFalse(canRunActiveGameOperation(activeState(busy = true)))
        assertFalse(canRunActiveGameOperation(activeState(cleanupRequired = true)))
    }
}
