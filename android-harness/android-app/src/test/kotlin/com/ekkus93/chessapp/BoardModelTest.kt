package com.ekkus93.chessapp

import com.ekkus93.chessengine.HumanSide
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class BoardModelTest {
    @Test
    fun startingFenParsesExpectedPieces() {
        val board = BoardPosition.parse(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        )
        assertEquals('K', board.pieces["e1"])
        assertEquals('k', board.pieces["e8"])
        assertEquals('P', board.pieces["a2"])
        assertEquals('p', board.pieces["h7"])
        assertEquals(32, board.pieces.size)
    }

    @Test
    fun orientationMatchesHumanSide() {
        assertEquals(('a'..'h').toList(), visibleFiles(HumanSide.WHITE))
        assertEquals((8 downTo 1).toList(), visibleRanks(HumanSide.WHITE))
        assertEquals(('h' downTo 'a').toList(), visibleFiles(HumanSide.BLACK))
        assertEquals((1..8).toList(), visibleRanks(HumanSide.BLACK))
    }

    @Test
    fun legalSourceAndTargetProjectionUsesRustMoveListOnly() {
        val legal = listOf("e2e3", "e2e4", "g1f3")
        assertEquals(setOf("e2", "g1"), selectableSources(legal))
        assertEquals(setOf("e3", "e4"), legalTargets(legal, "e2"))
        assertEquals(listOf("e2e4"), candidateMoves(legal, "e2", "e4"))
        assertTrue(legalTargets(legal, "a1").isEmpty())
    }

    @Test
    fun promotionCandidatesRemainExplicit() {
        val legal = listOf("a7a8q", "a7a8r", "a7a8b", "a7a8n")
        assertEquals(legal, candidateMoves(legal, "a7", "a8"))
    }
}
